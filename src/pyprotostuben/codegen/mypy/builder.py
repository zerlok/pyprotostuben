import ast
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

from pyprotostuben.codegen.builder import ASTBuilder, ArgInfo
from pyprotostuben.codegen.mypy.info import FieldInfo, OneofInfo, ScopeInfo, EnumInfo
from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.types.registry import TypeRegistry
from pyprotostuben.protobuf.types.resolver.ast import ASTTypeResolver
from pyprotostuben.protobuf.types.resolver.dependency import ModuleDependencyResolver
from pyprotostuben.protobuf.visitor.abc import ProtoVisitor
from pyprotostuben.python.info import ModuleInfo, NamespaceInfo
from pyprotostuben.stack import Stack


class ModuleStubBuilder(ProtoVisitor):
    def __init__(
        self,
        type_registry: TypeRegistry,
        ast_builder: ASTBuilder,
        files: Stack[ProtoFile],
        namespaces: Stack[NamespaceInfo],
        scopes: Stack[ScopeInfo],
        modules: t.Dict[Path, ast.Module],
    ) -> None:
        self.__type_registry = type_registry
        self.__ast = ast_builder
        self.__files = files
        self.__namespaces = namespaces
        self.__scopes = scopes
        self.__modules = modules

    @property
    def file(self) -> ProtoFile:
        return self.__files.get_last()

    @property
    def current_scope(self) -> ScopeInfo:
        return self.__scopes[-1]

    @property
    def parent_scope(self) -> ScopeInfo:
        return self.__scopes[-2]

    def get_resolver(self, module: ModuleInfo) -> ASTTypeResolver:
        return ASTTypeResolver(
            ModuleDependencyResolver(self.__type_registry, module, self.current_scope.dependencies),
            self.__ast,
        )

    def visit_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        scope = self.current_scope
        message = scope.message
        servicer = scope.servicer
        stub = scope.stub

        if message.body:
            self.__modules[self.file.pb2_message.stub_file] = self.__ast.build_module(
                *self.__build_imports(scope.dependencies),
                *message.body,
            )

        if servicer.body and stub.body:
            self.__modules[self.file.pb2_grpc.stub_file] = self.__ast.build_module(
                *self.__build_imports(scope.dependencies),
                *servicer.body,
                *stub.body,
            )

    def visit_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        self.parent_scope.message.body.append(
            self.__ast.build_enum_def(
                name=proto.name,
                base=self.get_resolver(self.file.pb2_message).resolve_protobuf_enum_base(proto),
                items=[(enum.name, enum.value) for enum in self.current_scope.message.enums],
            )
        )

    def visit_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        self.parent_scope.message.enums.append(EnumInfo(proto.name, proto.number))

    def visit_descriptor_proto(self, proto: DescriptorProto) -> None:
        # TODO: solve MapEntry: `map<KeyType, ValueType> field_name`
        #  proto.options.map_entry

        resolver = self.get_resolver(self.file.pb2_message)

        scope = self.current_scope
        message = scope.message
        fields = message.fields

        parent_scope = self.parent_scope
        parent_message = parent_scope.message
        parent_body = parent_message.body

        # if proto.options.map_entry:
        #     key_field, value_field = message.fields  # type: FieldInfo
        #     parent_body.append(
        #         self.__ast.build_class_def(
        #             name=proto.name,
        #             bases=[
        #                 self.__ast.build_generic_instance_expr(
        #                     resolver.resolve_mapping(), key_field.annotation, value_field.annotation
        #                 )
        #             ],
        #         )
        #     )
        #     return

        has_field_args = [self.__ast.const(field.name) for field in fields if field.optional]
        oneofs = [oneof for oneof in message.oneofs if oneof.items]

        parent_body.append(
            self.__ast.build_class_def(
                name=proto.name,
                bases=[resolver.resolve_protobuf_message_base(proto)],
                body=[
                    *message.body,
                    self.__ast.build_init_stub(
                        args=[
                            ArgInfo(
                                name=field.name,
                                kind=ArgInfo.Kind.KW_ONLY,
                                annotation=self.__ast.build_generic_instance_expr(
                                    resolver.resolve_optional(), field.annotation
                                )
                                if field.optional or field.oneof
                                else field.annotation,
                                default=self.__ast.build_none_expr() if field.optional or field.oneof else None,
                            )
                            for field in fields
                        ],
                    ),
                    *(
                        self.__ast.build_instance_method_stub(
                            name=field.name,
                            decorators=[resolver.resolve_property()],
                            returns=field.annotation,
                        )
                        for field in fields
                    ),
                    self.__ast.build_instance_method_stub(
                        name="HasField",
                        args=[
                            ArgInfo(
                                name="field_name",
                                annotation=(
                                    self.__ast.build_generic_instance_expr(
                                        resolver.resolve_literal(),
                                        *has_field_args,
                                    )
                                    if has_field_args
                                    else resolver.resolve_no_return()
                                ),
                            ),
                        ],
                        returns=(self.__ast.build_bool_expr() if has_field_args else resolver.resolve_no_return()),
                    ),
                    *(
                        (
                            self.__ast.build_instance_method_stub(
                                name="WhichOneof",
                                decorators=[resolver.resolve_overload()] if len(message.oneofs) > 1 else None,
                                args=[
                                    ArgInfo(
                                        name="oneof_group",
                                        annotation=self.__ast.build_generic_instance_expr(
                                            resolver.resolve_literal(),
                                            self.__ast.const(oneof.name),
                                        ),
                                    ),
                                ],
                                returns=self.__ast.build_generic_instance_expr(
                                    resolver.resolve_optional(),
                                    self.__ast.build_generic_instance_expr(
                                        resolver.resolve_literal(),
                                        *(self.__ast.const(item) for item in oneof.items),
                                    ),
                                ),
                            )
                            for oneof in oneofs
                        )
                        if oneofs
                        else (
                            self.__ast.build_instance_method_stub(
                                name="WhichOneof",
                                args=[ArgInfo(name="oneof_group", annotation=resolver.resolve_no_return())],
                                returns=resolver.resolve_no_return(),
                            ),
                        )
                    ),
                ],
            )
        )

    def visit_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        self.parent_scope.message.oneofs.append(OneofInfo(name=proto.name, items=[]))

    def visit_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        message = self.parent_scope.message

        name = proto.name
        is_multi = proto.label == FieldDescriptorProto.Label.LABEL_REPEATED
        is_optional = proto.proto3_optional
        is_oneof = not is_optional and proto.HasField("oneof_index")

        annotation = self.get_resolver(self.file.pb2_message).resolve_protobuf_field(proto)

        message.fields.append(
            FieldInfo(
                name=name,
                annotation=annotation,
                multi=is_multi,
                optional=is_optional,
                oneof=is_oneof,
                # TODO: support default fields: proto.default_value
            )
        )

        if is_oneof:
            message.oneofs[proto.oneof_index].items.append(name)

    def visit_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        resolver = self.get_resolver(self.file.pb2_grpc)

        servicer_name = f"{proto.name}Servicer"

        self.parent_scope.servicer.body.append(
            self.__ast.build_class_def(
                name=servicer_name,
                keywords={
                    "metaclass": resolver.resolve_abstract_meta(),
                },
                body=[
                    *self.current_scope.servicer.body,
                ],
            )
        )
        self.parent_scope.servicer.body.append(
            self.__ast.build_func_stub(
                name=f"add_{servicer_name}_to_server",
                args=[
                    ArgInfo(name="servicer", annotation=self.__ast.build_attr_expr(servicer_name)),
                    ArgInfo(name="server", annotation=self.__ast.build_attr_expr(servicer_name)),
                ],
                returns=self.__ast.build_none_expr(),
            )
        )
        self.parent_scope.stub.body.append(
            self.__ast.build_class_def(
                name=f"{proto.name}Stub",
                body=[
                    self.__ast.build_init_stub(args=[ArgInfo(name="channel", annotation=resolver.resolve_no_return())]),
                    *self.current_scope.stub.body,
                ],
            )
        )

    def visit_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        resolver = self.get_resolver(self.file.pb2_grpc)

        input_type = resolver.resolve_grpc_method_input(proto)
        output_type = resolver.resolve_grpc_method_output(proto)

        self.parent_scope.servicer.body.append(
            self.__ast.build_instance_method_stub(
                name=proto.name,
                decorators=[resolver.resolve_abstract_method()],
                args=[
                    ArgInfo(name="request", annotation=input_type),
                    ArgInfo(name="context", annotation=resolver.resolve_grpc_servicer_context(proto)),
                ],
                returns=output_type,
                is_async=True,
            )
        )
        self.parent_scope.stub.body.append(
            self.__ast.build_instance_method_stub(
                name=proto.name,
                args=[
                    ArgInfo(name="request", annotation=input_type),
                ],
                returns=output_type,
                is_async=True,
            )
        )

    def __build_imports(self, dependencies: t.Collection[ModuleInfo]) -> t.Iterable[ast.stmt]:
        for module in sorted(dependencies, key=lambda x: x.qualname):
            yield self.__ast.build_import(module)
