import ast
import typing as t

from google.protobuf.descriptor_pb2 import (
    EnumDescriptorProto,
    DescriptorProto,
    FieldDescriptorProto,
    ServiceDescriptorProto,
    MethodDescriptorProto,
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

    def build_message_has_field_def(self, fields: t.Sequence[FieldInfo]) -> ast.stmt:
        has_field_args = [field.name for field in fields if field.optional]

        return build_method_stub(
            name="HasField",
            args=[
                FuncArgInfo.create_pos(
                    name="field_name",
                    annotation=(
                        self.build_literal_ref(*has_field_args) if has_field_args else self.build_no_return_ref()
                    ),
                ),
            ],
            returns=build_ref(self.__resolver.resolve_bool()) if has_field_args else self.build_no_return_ref(),
        )

    def build_message_which_oneof_defs(self, oneofs: t.Sequence[OneofInfo]) -> t.Sequence[ast.stmt]:
        valid_oneofs = [oneof for oneof in oneofs if oneof.items]

        if not valid_oneofs:
            return [
                build_method_stub(
                    name="WhichOneof",
                    args=[FuncArgInfo.create_pos(name="oneof_group", annotation=self.build_no_return_ref())],
                    returns=self.build_no_return_ref(),
                ),
            ]

        return [
            build_method_stub(
                name="WhichOneof",
                decorators=[build_ref(self.__resolver.resolve_overload())] if len(valid_oneofs) > 1 else None,
                args=[
                    FuncArgInfo.create_pos(
                        name="oneof_group",
                        annotation=self.build_literal_ref(oneof.name) if oneof.items else self.build_no_return_ref(),
                    )
                ],
                returns=self.build_optional_ref(self.build_literal_ref(*oneof.items))
                if oneof.items
                else self.build_no_return_ref(),
            )
            for oneof in valid_oneofs
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
            [FuncArgInfo.create_pos(name="channel", annotation=build_ref(self.__resolver.resolve_grpc_channel(proto)))]
        )

    def build_servicer_def(self, proto: ServiceDescriptorProto, body: t.Sequence[ast.stmt]) -> ast.stmt:
        return build_class_def(
            name=self.build_servicer_name(proto),
            keywords={
                "metaclass": build_ref(self.__resolver.resolve_abstract_meta()),
            },
            body=body,
        )

    def build_servicer_method_def(self, proto: MethodDescriptorProto) -> ast.stmt:
        context, request_ref, response_ref = self.build_servicer_method_request_response_ref(proto)

        return build_method_stub(
            name=proto.name,
            decorators=[build_ref(self.__resolver.resolve_abstract_method())],
            args=[
                FuncArgInfo.create_pos(name="request", annotation=request_ref),
                FuncArgInfo.create_pos(
                    name="context",
                    annotation=context,
                ),
            ],
            returns=response_ref,
            is_async=True,
        )

    def build_servicer_method_request_response_ref(
        self,
        proto: MethodDescriptorProto,
    ) -> t.Tuple[ast.expr, ast.expr, ast.expr]:
        input_ref = build_ref(self.__resolver.resolve_grpc_method_input(proto))
        output_ref = build_ref(self.__resolver.resolve_grpc_method_output(proto))
        context_ref = build_generic_ref(
            build_ref(self.__resolver.resolve_grpc_servicer_context(proto)),
            input_ref,
            output_ref,
        )

        request_ref = input_ref
        if proto.client_streaming:
            request_ref = build_generic_ref(build_ref(self.__resolver.resolve_async_iterator()), request_ref)

        response_ref = output_ref
        if proto.server_streaming:
            response_ref = build_generic_ref(build_ref(self.__resolver.resolve_async_iterator()), response_ref)

        return context_ref, request_ref, response_ref

    def build_servicer_registrator_def(self, proto: ServiceDescriptorProto) -> ast.stmt:
        servicer_name = self.build_servicer_name(proto)

        return build_func_stub(
            name=f"add_{servicer_name}_to_server",
            args=[
                FuncArgInfo.create_pos(name="servicer", annotation=ast.Name(id=servicer_name)),
                FuncArgInfo.create_pos(name="server", annotation=build_ref(self.__resolver.resolve_grpc_server(proto))),
            ],
            returns=self.build_none(),
        )

    def build_stub_def(self, proto: ServiceDescriptorProto, body: t.Sequence[ast.stmt]) -> ast.stmt:
        return build_class_def(
            name=f"{proto.name}Stub",
            body=body,
        )

    def build_stub_method_def(self, proto: MethodDescriptorProto) -> ast.stmt:
        request_ref, response_ref = self.build_stub_method_request_response_ref(proto)

        return build_method_stub(
            name=proto.name,
            args=[
                FuncArgInfo.create_pos(
                    name="request",
                    annotation=request_ref,
                ),
                self.build_optional_arg(
                    name="timeout",
                    annotation=build_ref(self.__resolver.resolve_grpc_stub_timeout(proto)),
                ),
                self.build_optional_arg(
                    name="metadata",
                    annotation=build_ref(self.__resolver.resolve_grpc_stub_metadata_type(proto)),
                ),
                self.build_optional_arg(
                    name="credentials",
                    annotation=build_ref(self.__resolver.resolve_grpc_stub_credentials(proto)),
                ),
                self.build_optional_arg(
                    name="wait_for_ready",
                    annotation=build_ref(self.__resolver.resolve_grpc_stub_wait_for_ready(proto)),
                ),
                self.build_optional_arg(
                    name="compression",
                    annotation=build_ref(self.__resolver.resolve_grpc_stub_compression(proto)),
                ),
            ],
            returns=response_ref,
            is_async=True,
        )

    def build_stub_method_request_response_ref(self, proto: MethodDescriptorProto) -> t.Tuple[ast.expr, ast.expr]:
        input_ref = build_ref(self.__resolver.resolve_grpc_method_input(proto))
        output_ref = build_ref(self.__resolver.resolve_grpc_method_output(proto))

        if not proto.client_streaming and not proto.server_streaming:
            return (
                input_ref,
                build_generic_ref(
                    build_ref(self.__resolver.resolve_grpc_stub_unary_unary_call(proto)),
                    input_ref,
                    output_ref,
                ),
            )

        elif not proto.client_streaming and proto.server_streaming:
            return (
                input_ref,
                build_generic_ref(
                    build_ref(self.__resolver.resolve_grpc_stub_unary_stream_call(proto)),
                    input_ref,
                    output_ref,
                ),
            )

        elif proto.client_streaming and not proto.server_streaming:
            return (
                build_generic_ref(build_ref(self.__resolver.resolve_async_iterator()), input_ref),
                build_generic_ref(
                    build_ref(self.__resolver.resolve_grpc_stub_stream_unary_call(proto)),
                    input_ref,
                    output_ref,
                ),
            )

        elif proto.client_streaming and proto.server_streaming:
            return (
                build_generic_ref(build_ref(self.__resolver.resolve_async_iterator()), input_ref),
                build_generic_ref(
                    build_ref(self.__resolver.resolve_grpc_stub_stream_stream_call(proto)),
                    input_ref,
                    output_ref,
                ),
            )

        else:
            raise ValueError("invalid streaming options", proto)

    def build_none(self) -> ast.expr:
        return ast.Constant(value=None)

    def build_optional_arg(self, name: str, annotation: ast.expr) -> FuncArgInfo:
        return FuncArgInfo.create_kw(
            name=name,
            annotation=self.build_optional_ref(annotation),
            default=self.build_none(),
        )

    def build_servicer_name(self, proto: ServiceDescriptorProto) -> str:
        return f"{proto.name}Servicer"

    def build_stub_name(self, proto: ServiceDescriptorProto) -> str:
        return f"{proto.name}Stub"
