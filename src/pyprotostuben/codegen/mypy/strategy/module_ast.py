import ast
import itertools as it
import typing as t
from pathlib import Path

from google.protobuf.descriptor_pb2 import (
    FileDescriptorProto,
    EnumDescriptorProto,
    EnumValueDescriptorProto,
    DescriptorProto,
    OneofDescriptorProto,
    FieldDescriptorProto,
    ServiceDescriptorProto,
    MethodDescriptorProto,
)

from pyprotostuben.codegen.mypy.builder import ModuleASTBuilder
from pyprotostuben.codegen.mypy.info import (
    ScopeInfo,
    EnumInfo,
    OneofInfo,
    FieldInfo,
    CodeBlock,
    ScopeProtoVisitorDecorator,
    ServicerInfo,
    StubInfo,
)
from pyprotostuben.codegen.mypy.strategy.abc import Strategy
from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.registry import TypeRegistry
from pyprotostuben.protobuf.visitor.abc import ProtoVisitor, visit
from pyprotostuben.protobuf.visitor.decorator import LeaveProtoVisitorDecorator
from pyprotostuben.protobuf.visitor.dfs import DFSWalkingProtoVisitor
from pyprotostuben.protobuf.visitor.info import NamespaceInfoVisitor
from pyprotostuben.python.builder import build_enum_class_def
from pyprotostuben.python.info import NamespaceInfo
from pyprotostuben.python.types.resolver.dependency import ModuleDependencyResolver
from pyprotostuben.stack import Stack, MutableStack


class ModuleASTGeneratorStrategy(Strategy, LoggerMixin):
    def __init__(self, type_registry: TypeRegistry) -> None:
        self.__type_registry = type_registry

    def run(self, file: ProtoFile) -> t.Iterable[t.Tuple[ProtoFile, Path, str]]:
        log = self._log.bind_details(file_name=file.name)
        log.debug("file received")

        namespaces: MutableStack[NamespaceInfo] = MutableStack()
        scopes: MutableStack[ScopeInfo] = MutableStack()
        modules: t.Dict[Path, ast.Module] = {}

        visitor = DFSWalkingProtoVisitor(
            NamespaceInfoVisitor(namespaces),
            ScopeProtoVisitorDecorator(scopes),
            LeaveProtoVisitorDecorator(
                ModuleASTGenerator(
                    type_registry=self.__type_registry,
                    files=MutableStack([file]),
                    namespaces=namespaces,
                    scopes=scopes,
                    modules=modules,
                )
            ),
        )
        visit(visitor, file.descriptor)
        log.debug("proto visited", modules=modules)

        for path, module_ast in modules.items():
            module_content = ast.unparse(module_ast)
            log.info("module generated", path=path)

            yield file, path, module_content


class ModuleASTGenerator(ProtoVisitor):
    def __init__(
        self,
        type_registry: TypeRegistry,
        files: Stack[ProtoFile],
        namespaces: Stack[NamespaceInfo],
        scopes: Stack[ScopeInfo],
        modules: t.Dict[Path, ast.Module],
    ) -> None:
        self.__type_registry = type_registry
        self.__files = files
        self.__namespaces = namespaces
        self.__scopes = scopes
        self.__modules = modules

    @property
    def file(self) -> ProtoFile:
        return self.__files.get_last()

    @property
    def root_scope(self) -> ScopeInfo:
        return self.__scopes[0]

    @property
    def current_scope(self) -> ScopeInfo:
        return self.__scopes[-1]

    @property
    def parent_scope(self) -> ScopeInfo:
        return self.__scopes[-2]

    def create_message_builder(self) -> "ModuleASTBuilder":
        return ModuleASTBuilder(
            ModuleDependencyResolver(self.__type_registry, self.file.pb2_message, self.root_scope.message.dependencies),
        )

    def create_grpc_servicer_builder(self) -> "ModuleASTBuilder":
        return ModuleASTBuilder(
            ModuleDependencyResolver(
                self.__type_registry, self.file.pb2_grpc, self.root_scope.grpc.servicer.dependencies
            ),
        )

    def create_grpc_stub_builder(self) -> "ModuleASTBuilder":
        return ModuleASTBuilder(
            ModuleDependencyResolver(self.__type_registry, self.file.pb2_grpc, self.root_scope.grpc.stub.dependencies),
        )

    def visit_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        message = self.current_scope.message
        grpc = self.current_scope.grpc

        if message.body:
            self.__modules[self.file.pb2_message.stub_file] = self.__build_module(message)

        if grpc.servicer.body and grpc.stub.body:
            self.__modules[self.file.pb2_grpc.stub_file] = self.__build_module(grpc.servicer, grpc.stub)

    def visit_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        enum_class_def = build_enum_class_def(
            name=proto.name,
            base=self.create_message_builder().build_enum_ref(proto),
            items=[(enum.name, enum.value) for enum in self.current_scope.message.enums],
        )

        self.parent_scope.message.body.append(enum_class_def)

    def visit_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        self.parent_scope.message.enums.append(EnumInfo(proto.name, proto.number))

    def visit_descriptor_proto(self, proto: DescriptorProto) -> None:
        # TODO: solve MapEntry: `map<KeyType, ValueType> field_name`
        #  proto.options.map_entry

        builder = self.create_message_builder()
        message = self.current_scope.message

        message_def = builder.build_message_def(
            proto=proto,
            body=[
                *message.body,
                builder.build_message_init_def(message.fields),
                *builder.build_message_field_defs(message.fields),
                builder.build_message_method_has_field_def(message.fields),
                *builder.build_message_method_which_oneof_defs(message.oneofs),
            ],
        )

        self.parent_scope.message.body.append(message_def)

    def visit_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        self.parent_scope.message.oneofs.append(OneofInfo(name=proto.name))

    def visit_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        name = proto.name
        is_multi = proto.label == FieldDescriptorProto.Label.LABEL_REPEATED
        is_optional = proto.proto3_optional
        is_oneof = not is_optional and proto.HasField("oneof_index")

        builder = self.create_message_builder()

        ref = builder.build_field_ref(proto)
        if is_multi:
            ref = builder.build_sequence_ref(ref)

        self.parent_scope.message.fields.append(
            FieldInfo(
                name=name,
                annotation=ref,
                multi=is_multi,
                optional=is_optional,
                oneof=is_oneof,
                # TODO: support default fields: proto.default_value
            )
        )

        if is_oneof:
            self.parent_scope.message.oneofs[proto.oneof_index].items.append(name)

    def visit_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        grpc = self.current_scope.grpc
        self.__build_service_servicer(proto, grpc.servicer)
        self.__build_service_stub(proto, grpc.stub)

    def __build_service_servicer(self, proto: ServiceDescriptorProto, info: ServicerInfo) -> None:
        if not info.body:
            return

        builder = self.create_grpc_servicer_builder()
        servicer_class_def = builder.build_servicer_def(proto, [])
        servicer_registrator_def = builder.build_servicer_registrator_def(proto)

        self.parent_scope.grpc.servicer.body.extend([servicer_class_def, servicer_registrator_def])

    def __build_service_stub(self, proto: ServiceDescriptorProto, info: StubInfo) -> None:
        if not info.body:
            return

        builder = self.create_grpc_stub_builder()
        stub_class_def = builder.build_stub_def(
            proto=proto,
            body=[
                builder.build_stub_init_def(proto),
                *self.current_scope.grpc.stub.body,
            ],
        )

        self.parent_scope.grpc.stub.body.append(stub_class_def)

    def visit_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        # self.__build_method_servicer(proto)
        # self.__build_method_stub(proto)
        pass

    # def __build_method_servicer(self, proto: MethodDescriptorProto) -> None:
    #     builder = self.create_grpc_servicer_builder()
    #     method_def = builder.build_method_stub(
    #         name=proto.name,
    #         decorators=[builder.resolve_abstract_method()],
    #         args=[
    #             FuncArgInfo(name="request", annotation=input_type),
    #             FuncArgInfo(name="context", annotation=resolver.resolve_grpc_servicer_context(proto)),
    #         ],
    #         returns=output_type,
    #         is_async=True,
    #     )
    #     self.parent_scope.grpc.body.append()
    #
    # def __build_method_stub(self, proto: MethodDescriptorProto) -> None:
    #     self.parent_scope.stub.body.append(
    #         self.__ast.build_method_stub(
    #             name=proto.name,
    #             args=[
    #                 FuncArgInfo(name="request", annotation=input_type),
    #             ],
    #             returns=output_type,
    #             is_async=True,
    #         )
    #     )

    def __build_module(self, *blocks: CodeBlock) -> ast.Module:
        dependencies = sorted(it.chain.from_iterable(block.dependencies for block in blocks), key=lambda m: m.qualname)
        body = list(
            it.chain(
                (ast.Import(names=[ast.alias(name=module.qualname)]) for module in dependencies),
                it.chain.from_iterable(block.body for block in blocks),
            )
        )

        return ast.Module(body=body, type_ignores=[])
