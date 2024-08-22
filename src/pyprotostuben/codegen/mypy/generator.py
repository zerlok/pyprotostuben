import ast
import typing as t
from pathlib import Path

from google.protobuf.descriptor_pb2 import (
    DescriptorProto,
    EnumDescriptorProto,
    EnumValueDescriptorProto,
    FieldDescriptorProto,
    FileDescriptorProto,
    MethodDescriptorProto,
    OneofDescriptorProto,
    ServiceDescriptorProto,
)

from pyprotostuben.codegen.module_ast import ModuleASTProtoVisitorDecoratorFactory
from pyprotostuben.codegen.mypy.context import GRPCContext, MessageContext
from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.builder.grpc import GRPCASTBuilder, MethodInfo
from pyprotostuben.protobuf.builder.message import FieldInfo, MessageASTBuilder
from pyprotostuben.protobuf.builder.resolver import ProtoDependencyResolver
from pyprotostuben.protobuf.context import CodeGeneratorContext
from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.registry import MapEntryInfo, TypeRegistry
from pyprotostuben.protobuf.visitor.decorator import ProtoVisitorDecorator
from pyprotostuben.python.ast_builder import ASTBuilder
from pyprotostuben.python.info import ModuleInfo
from pyprotostuben.stack import MutableStack


class MypyStubASTGeneratorFactory(ModuleASTProtoVisitorDecoratorFactory):
    def __init__(
        self,
        context: CodeGeneratorContext,
    ) -> None:
        self.__context = context

    def create_proto_visitor_decorator(self, modules: t.MutableMapping[Path, ast.Module]) -> ProtoVisitorDecorator:
        return MypyStubASTGenerator(
            registry=self.__context.registry,
            factory=self,
            modules=modules,
        )

    def create_file_message_context(self, file: ProtoFile) -> MessageContext:
        deps: t.Set[ModuleInfo] = set()
        module = file.pb2_message

        return MessageContext(
            file=file,
            module=module,
            external_modules=deps,
            builder=self.__create_message_ast_builder(module, deps),
        )

    def create_file_grpc_context(self, file: ProtoFile) -> GRPCContext:
        deps: t.Set[ModuleInfo] = set()
        module = file.pb2_grpc

        return GRPCContext(
            file=file,
            module=module,
            external_modules=deps,
            builder=self.__create_grpc_ast_builder(module, deps),
        )

    def __create_message_ast_builder(self, module: ModuleInfo, deps: t.Set[ModuleInfo]) -> MessageASTBuilder:
        inner = ASTBuilder(ProtoDependencyResolver(module, deps))

        return MessageASTBuilder(
            inner,
            mutable=self.__context.params.has_flag("message-mutable"),
            all_init_args_optional=self.__context.params.has_flag("message-all-init-args-optional"),
        )

    def __create_grpc_ast_builder(self, module: ModuleInfo, deps: t.Set[ModuleInfo]) -> GRPCASTBuilder:
        inner = ASTBuilder(ProtoDependencyResolver(module, deps))

        return GRPCASTBuilder(
            inner,
            is_sync=self.__context.params.has_flag("grpc-sync"),
            skip_servicer=self.__context.params.has_flag("grpc-skip-servicer"),
            skip_stub=self.__context.params.has_flag("grpc-skip-stub"),
        )


class MypyStubASTGenerator(ProtoVisitorDecorator, LoggerMixin):
    def __init__(
        self,
        registry: TypeRegistry,
        factory: MypyStubASTGeneratorFactory,
        modules: t.MutableMapping[Path, ast.Module],
    ) -> None:
        self.__registry = registry
        self.__factory = factory
        self.__modules = modules
        self.__messages: MutableStack[MessageContext] = MutableStack()
        self.__grpcs: MutableStack[GRPCContext] = MutableStack()

    def enter_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        file = ProtoFile(proto)

        self.__messages.put(self.__factory.create_file_message_context(file))
        self.__grpcs.put(self.__factory.create_file_grpc_context(file))

    def leave_file_descriptor_proto(self, _: FileDescriptorProto) -> None:
        message = self.__messages.pop()
        grpc = self.__grpcs.pop()

        self.__modules[message.module.stub_file] = message.builder.build_protobuf_message_module(
            message.external_modules,
            message.nested,
        )
        self.__modules[grpc.module.stub_file] = grpc.builder.build_grpc_module(
            grpc.external_modules,
            grpc.nested,
        )

    def enter_enum_descriptor_proto(self, _: EnumDescriptorProto) -> None:
        parent = self.__messages.get_last()

        self.__messages.put(parent.sub())

    def leave_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        message = self.__messages.pop()
        parent = self.__messages.get_last()
        builder = message.builder

        parent.nested.append(builder.build_protobuf_enum_def(proto.name, message.nested))

    def enter_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        pass

    def leave_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        parent = self.__messages.get_last()
        builder = parent.builder

        parent.nested.append(builder.build_protobuf_enum_value_def(proto.name, proto.number))

    def enter_descriptor_proto(self, _: DescriptorProto) -> None:
        parent = self.__messages.get_last()

        self.__messages.put(parent.sub())

    def leave_descriptor_proto(self, proto: DescriptorProto) -> None:
        message = self.__messages.pop()

        if proto.options.map_entry:
            return

        parent = self.__messages.get_last()
        builder = message.builder

        parent.nested.append(
            builder.build_protobuf_message_def(
                name=proto.name,
                fields=message.fields,
                nested=message.nested,
            ),
        )

    def enter_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        pass

    def leave_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        info = self.__messages.get_last()
        info.oneof_groups.append(proto.name)

    def enter_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        pass

    def leave_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        is_optional = proto.proto3_optional
        message = self.__messages.get_last()
        builder = message.builder

        info = self.__registry.resolve_proto_field(proto)

        annotation = builder.build_protobuf_type_ref(info)
        if not isinstance(info, MapEntryInfo) and proto.label == FieldDescriptorProto.Label.LABEL_REPEATED:
            annotation = builder.build_protobuf_repeated_ref(annotation)

        message.fields.append(
            FieldInfo(
                name=proto.name,
                annotation=annotation,
                optional=is_optional,
                default=None,
                # TODO: support proto.default_value
                oneof_group=message.oneof_groups[proto.oneof_index]
                if not is_optional and proto.HasField("oneof_index")
                else None,
            ),
        )

    def enter_service_descriptor_proto(self, _: ServiceDescriptorProto) -> None:
        parent = self.__grpcs.get_last()

        self.__grpcs.put(parent.sub())

    def leave_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        grpc = self.__grpcs.pop()
        parent = self.__grpcs.get_last()
        builder = grpc.builder

        parent.nested.extend(builder.build_grpc_servicer_defs(f"{proto.name}Servicer", grpc.methods))
        parent.nested.extend(builder.build_grpc_stub_defs(f"{proto.name}Stub", grpc.methods))

    def enter_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        pass

    def leave_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        grpc = self.__grpcs.get_last()
        builder = grpc.builder

        grpc.methods.append(
            MethodInfo(
                name=proto.name,
                client_input=builder.build_grpc_message_ref(self.__registry.resolve_proto_method_client_input(proto)),
                client_streaming=proto.client_streaming,
                server_output=builder.build_grpc_message_ref(self.__registry.resolve_proto_method_server_output(proto)),
                server_streaming=proto.server_streaming,
            ),
        )
