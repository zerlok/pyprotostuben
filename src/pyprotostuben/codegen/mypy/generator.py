import typing as t
from dataclasses import dataclass, replace

from google.protobuf.descriptor_pb2 import (
    FieldDescriptorProto,
)

from pyprotostuben.codegen.module_ast import ModuleASTContext
from pyprotostuben.codegen.mypy.context import GRPCContext, MessageContext
from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.builder.grpc import MethodInfo
from pyprotostuben.protobuf.builder.message import FieldInfo
from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.registry import MapEntryInfo, TypeRegistry
from pyprotostuben.protobuf.visitor.decorator import ProtoVisitorDecorator
from pyprotostuben.protobuf.visitor.model import (
    DescriptorContext,
    EnumDescriptorContext,
    EnumValueDescriptorContext,
    FieldDescriptorContext,
    FileDescriptorContext,
    MethodDescriptorContext,
    OneofDescriptorContext,
    ServiceDescriptorContext,
)
from pyprotostuben.stack import MutableStack


@dataclass(frozen=True)
class MypyStubContext(ModuleASTContext):
    messages: MutableStack[MessageContext]
    grpcs: MutableStack[GRPCContext]


class MypyStubASTGenerator(ProtoVisitorDecorator[MypyStubContext], LoggerMixin):
    def __init__(
        self,
        registry: TypeRegistry,
        message_context_factory: t.Callable[[ProtoFile], MessageContext],
        grpc_context_factory: t.Callable[[ProtoFile], GRPCContext],
    ) -> None:
        self.__registry = registry
        self.__message_context_factory = message_context_factory
        self.__grpc_context_factory = grpc_context_factory

    def enter_file_descriptor_proto(self, context: FileDescriptorContext[MypyStubContext]) -> MypyStubContext:
        context.meta.messages.put(self.__message_context_factory(context.file))
        context.meta.grpcs.put(self.__grpc_context_factory(context.file))

        return context.meta

    def leave_file_descriptor_proto(self, context: FileDescriptorContext[MypyStubContext]) -> MypyStubContext:
        message = context.meta.messages.pop()
        grpc = context.meta.grpcs.pop()

        modules = {
            message.module.stub_file: message.builder.build_protobuf_message_module(
                message.external_modules,
                message.nested,
            ),
            grpc.module.stub_file: grpc.builder.build_grpc_module(
                grpc.external_modules,
                grpc.nested,
            ),
        }

        return replace(context.meta, modules={**context.meta.modules, **modules})

    def enter_enum_descriptor_proto(self, context: EnumDescriptorContext[MypyStubContext]) -> MypyStubContext:
        parent = context.meta.messages.get_last()

        context.meta.messages.put(parent.sub())

        return context.meta

    def leave_enum_descriptor_proto(self, context: EnumDescriptorContext[MypyStubContext]) -> MypyStubContext:
        message = context.meta.messages.pop()
        parent = context.meta.messages.get_last()
        builder = message.builder

        parent.nested.append(builder.build_protobuf_enum_def(context.item.name, message.nested))

        return context.meta

    def enter_enum_value_descriptor_proto(
        self,
        context: EnumValueDescriptorContext[MypyStubContext],
    ) -> MypyStubContext:
        return context.meta

    def leave_enum_value_descriptor_proto(
        self, context: EnumValueDescriptorContext[MypyStubContext]
    ) -> MypyStubContext:
        parent = context.meta.messages.get_last()
        builder = parent.builder

        parent.nested.append(builder.build_protobuf_enum_value_def(context.item.name, context.item.number))

        return context.meta

    def enter_descriptor_proto(self, context: DescriptorContext[MypyStubContext]) -> MypyStubContext:
        parent = context.meta.messages.get_last()

        context.meta.messages.put(parent.sub())

        return context.meta

    def leave_descriptor_proto(self, context: DescriptorContext[MypyStubContext]) -> MypyStubContext:
        message = context.meta.messages.pop()

        if context.item.options.map_entry:
            return context.meta

        parent = context.meta.messages.get_last()
        builder = message.builder

        parent.nested.append(
            builder.build_protobuf_message_def(
                name=context.item.name,
                fields=message.fields,
                nested=message.nested,
            ),
        )

        return context.meta

    def enter_oneof_descriptor_proto(self, context: OneofDescriptorContext[MypyStubContext]) -> MypyStubContext:
        return context.meta

    def leave_oneof_descriptor_proto(self, context: OneofDescriptorContext[MypyStubContext]) -> MypyStubContext:
        info = context.meta.messages.get_last()
        info.oneof_groups.append(context.item.name)

        return context.meta

    def enter_field_descriptor_proto(self, context: FieldDescriptorContext[MypyStubContext]) -> MypyStubContext:
        return context.meta

    def leave_field_descriptor_proto(self, context: FieldDescriptorContext[MypyStubContext]) -> MypyStubContext:
        is_optional = context.item.proto3_optional
        message = context.meta.messages.get_last()
        builder = message.builder

        info = self.__registry.resolve_proto_field(context.item)

        annotation = builder.build_protobuf_type_ref(info)
        if not isinstance(info, MapEntryInfo) and context.item.label == FieldDescriptorProto.Label.LABEL_REPEATED:
            annotation = builder.build_protobuf_repeated_ref(annotation)

        message.fields.append(
            FieldInfo(
                name=context.item.name,
                annotation=annotation,
                optional=is_optional,
                default=None,
                # TODO: support proto.default_value
                oneof_group=message.oneof_groups[context.item.oneof_index]
                if not is_optional and context.item.HasField("oneof_index")
                else None,
            ),
        )

        return context.meta

    def enter_service_descriptor_proto(self, context: ServiceDescriptorContext[MypyStubContext]) -> MypyStubContext:
        parent = context.meta.grpcs.get_last()

        context.meta.grpcs.put(parent.sub())

        return context.meta

    def leave_service_descriptor_proto(self, context: ServiceDescriptorContext[MypyStubContext]) -> MypyStubContext:
        grpc = context.meta.grpcs.pop()
        parent = context.meta.grpcs.get_last()
        builder = grpc.builder

        parent.nested.extend(builder.build_grpc_servicer_defs(f"{context.item.name}Servicer", grpc.methods))
        parent.nested.extend(builder.build_grpc_stub_defs(f"{context.item.name}Stub", grpc.methods))

        return context.meta

    def enter_method_descriptor_proto(self, context: MethodDescriptorContext[MypyStubContext]) -> MypyStubContext:
        return context.meta

    def leave_method_descriptor_proto(self, context: MethodDescriptorContext[MypyStubContext]) -> MypyStubContext:
        grpc = context.meta.grpcs.get_last()
        builder = grpc.builder

        grpc.methods.append(
            MethodInfo(
                name=context.item.name,
                client_input=builder.build_grpc_message_ref(
                    self.__registry.resolve_proto_method_client_input(context.item)
                ),
                client_streaming=context.item.client_streaming,
                server_output=builder.build_grpc_message_ref(
                    self.__registry.resolve_proto_method_server_output(context.item)
                ),
                server_streaming=context.item.server_streaming,
            ),
        )

        return context.meta
