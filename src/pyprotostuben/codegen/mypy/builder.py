import ast
import typing as t

from google.protobuf.descriptor_pb2 import (
    EnumDescriptorProto,
    DescriptorProto,
    FieldDescriptorProto,
    ServiceDescriptorProto,
)

from pyprotostuben.codegen.mypy.info import FieldInfo, OneofInfo
from pyprotostuben.python.builder import (
    build_ref,
    build_generic_ref,
    FuncArgInfo,
    build_init_stub,
    build_method_stub,
    build_class_def,
    build_func_stub,
)
from pyprotostuben.python.info import NamespaceInfo
from pyprotostuben.python.types.resolver.abc import TypeResolver


class ModuleASTBuilder:
    def __init__(self, resolver: TypeResolver[NamespaceInfo]) -> None:
        self.__resolver = resolver

    def build_message_init_def(self, fields: t.Sequence[FieldInfo]) -> ast.stmt:
        return build_init_stub(
            [
                FuncArgInfo(
                    name=field.name,
                    kind=FuncArgInfo.Kind.KW_ONLY,
                    annotation=self.build_optional_ref(field.annotation)
                    if field.optional or field.oneof
                    else field.annotation,
                    default=ast.Constant(value=None) if field.optional or field.oneof else None,
                )
                for field in fields
            ],
        )

    def build_message_field_defs(self, fields: t.Sequence[FieldInfo]) -> t.Sequence[ast.stmt]:
        return [
            build_method_stub(
                name=field.name,
                decorators=[build_ref(self.__resolver.resolve_property())],
                returns=field.annotation,
            )
            for field in fields
        ]

    def build_message_method_has_field_def(self, fields: t.Sequence[FieldInfo]) -> ast.stmt:
        has_field_args = [field.name for field in fields if field.optional]

        return build_method_stub(
            name="HasField",
            args=[
                FuncArgInfo(
                    name="field_name",
                    annotation=(
                        self.build_literal_ref(*has_field_args) if has_field_args else self.build_no_return_ref()
                    ),
                ),
            ],
            returns=ast.Name(id="bool") if has_field_args else self.build_no_return_ref(),
        )

    def build_message_method_which_oneof_defs(self, oneofs: t.Sequence[OneofInfo]) -> t.Sequence[ast.stmt]:
        if not oneofs:
            return [
                build_method_stub(
                    name="WhichOneof",
                    args=[FuncArgInfo(name="oneof_group", annotation=self.build_no_return_ref())],
                    returns=self.build_no_return_ref(),
                ),
            ]

        return [
            build_method_stub(
                name="WhichOneof",
                decorators=[build_ref(self.__resolver.resolve_overload())] if len(oneofs) > 1 else None,
                args=[
                    FuncArgInfo(
                        name="oneof_group",
                        annotation=self.build_literal_ref(oneof.name) if oneof.items else self.build_no_return_ref(),
                    )
                ],
                returns=self.build_optional_ref(self.build_literal_ref(*oneof.items))
                if oneof.items
                else self.build_no_return_ref(),
            )
            for oneof in oneofs
        ]

    def build_message_def(self, proto: DescriptorProto, body: t.Sequence[ast.stmt]) -> ast.stmt:
        return build_class_def(
            name=proto.name,
            bases=[build_ref(self.__resolver.resolve_protobuf_message_base(proto))],
            body=body,
        )

    def build_field_ref(self, proto: FieldDescriptorProto) -> ast.expr:
        return build_ref(self.__resolver.resolve_protobuf_field(proto))

    def build_no_return_ref(self) -> ast.expr:
        return build_ref(self.__resolver.resolve_no_return())

    def build_optional_ref(self, inner: ast.expr) -> ast.expr:
        return build_generic_ref(build_ref(self.__resolver.resolve_optional()), inner)

    def build_sequence_ref(self, inner: ast.expr) -> ast.expr:
        return build_generic_ref(build_ref(self.__resolver.resolve_sequence()), inner)

    def build_literal_ref(self, *args: str) -> ast.expr:
        return build_generic_ref(
            build_ref(self.__resolver.resolve_literal()), *(ast.Constant(value=arg) for arg in args)
        )

    def build_enum_ref(self, proto: EnumDescriptorProto) -> ast.expr:
        return build_ref(self.__resolver.resolve_protobuf_enum_base(proto))

    def build_stub_init_def(self, proto: ServiceDescriptorProto) -> ast.stmt:
        return build_init_stub(
            [FuncArgInfo(name="channel", annotation=build_ref(self.__resolver.resolve_grpc_channel(proto)))]
        )

    def build_servicer_def(self, proto: ServiceDescriptorProto, body: t.Sequence[ast.stmt]) -> ast.stmt:
        return build_class_def(
            name=self.build_servicer_name(proto),
            keywords={
                "metaclass": build_ref(self.__resolver.resolve_abstract_meta()),
            },
            body=body,
        )

    def build_servicer_registrator_def(self, proto: ServiceDescriptorProto) -> ast.stmt:
        servicer_name = self.build_servicer_name(proto)

        return build_func_stub(
            name=f"add_{servicer_name}_to_server",
            args=[
                FuncArgInfo(name="servicer", annotation=ast.Name(id=servicer_name)),
                FuncArgInfo(name="server", annotation=build_ref(self.__resolver.resolve_grpc_server(proto))),
            ],
            returns=ast.Constant(value=None),
        )

    def build_stub_def(self, proto: ServiceDescriptorProto, body: t.Sequence[ast.stmt]) -> ast.stmt:
        return build_class_def(
            name=f"{proto.name}Stub",
            body=body,
        )

    def build_servicer_name(self, proto: ServiceDescriptorProto) -> str:
        return f"{proto.name}Servicer"

    def build_stub_name(self, proto: ServiceDescriptorProto) -> str:
        return f"{proto.name}Stub"
