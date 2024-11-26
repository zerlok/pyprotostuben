import ast
import typing as t
from collections import defaultdict
from functools import cached_property
from itertools import chain

from pyprotostuben.codegen.mypy.model import MethodInfo, ScopeInfo
from pyprotostuben.protobuf.registry import MapEntryInfo, ProtoInfo
from pyprotostuben.python.ast_builder import ASTBuilder, TypeRef
from pyprotostuben.python.info import ModuleInfo, TypeInfo


class Pb2AstBuilder:
    def __init__(
        self,
        inner: ASTBuilder,
        *,
        mutable: bool,
        all_init_args_optional: bool,
        include_descriptors: bool,
    ) -> None:
        self.__inner = inner
        self.__mutable = mutable
        self.__all_init_args_optional = all_init_args_optional
        self.__include_descriptors = include_descriptors

    def build_enum_def(self, path: t.Sequence[str], doc: t.Optional[str], scope: ScopeInfo) -> ast.stmt:
        # TODO: actual type is not fully compatible with IntEnum.
        #  See: https://github.com/nipunn1313/mypy-protobuf/issues/484
        return self.__inner.build_class_def(
            name=path[-1],
            bases=[self.__protobuf_enum_ref],
            doc=doc,
            # TODO: add EnumDescriptor & base enum wrapper methods: Name, Value, ValueType, items, keys, values
            body=list(chain.from_iterable(value.body for value in scope.enum_values)),
        )

    def build_enum_value_def(self, name: str, doc: t.Optional[str], value: object) -> t.Sequence[ast.stmt]:
        # TODO: actual type is not fully compatible with IntEnum.
        #  See: https://github.com/nipunn1313/mypy-protobuf/issues/484
        result = [
            self.__inner.build_attr_assign(
                name,
                value=self.__inner.build_const(value),
            ),
        ]

        if doc:
            result.append(self.__inner.build_docstring(doc))

        return result

    def build_message_def(self, path: t.Sequence[str], doc: t.Optional[str], scope: ScopeInfo) -> ast.stmt:
        return self.__inner.build_class_def(
            name=path[-1],
            bases=[self.__protobuf_message_ref],
            doc=doc,
            body=list(
                chain(
                    self.__build_message_nested_body(scope),
                    (self.__build_message_init_stub(scope),),
                    self.__build_message_field_stubs(scope),
                    (self.__build_protobuf_message_has_field_method_stub(scope),),
                    self.__build_which_oneof_method_stubs(scope),
                    self.__build_extensions(scope),
                    self.__build_descriptor_annotation(self.__protobuf_message_descriptor_ref),
                )
            ),
        )

    def build_module(self, scope: ScopeInfo) -> ast.Module:
        body = list(
            chain(
                chain.from_iterable(enum.body for enum in scope.enums),
                chain.from_iterable(message.body for message in scope.messages),
                self.__build_extensions(scope),
                self.__build_descriptor_annotation(self.__protobuf_file_descriptor_ref),
            )
        )

        return self.__inner.build_module(None, body)

    def build_type_ref(self, info: ProtoInfo) -> ast.expr:
        if isinstance(info, MapEntryInfo):
            return self.build_map_entry_ref(info.key, info.value)

        return self.__inner.build_ref(info)

    def build_map_entry_ref(self, key: TypeRef, value: TypeRef) -> ast.expr:
        return self.__inner.build_generic_ref(self.__protobuf_map_entry_ref, key, value)

    def build_repeated_ref(self, inner: TypeRef) -> ast.expr:
        return self.__inner.build_generic_ref(self.__protobuf_field_repeated_ref, inner)

    def __build_descriptor_annotation(self, base: TypeRef) -> t.Sequence[ast.stmt]:
        if not self.__include_descriptors:
            return []

        return [
            self.__inner.build_attr_stub(
                name="DESCRIPTOR",
                annotation=base,
            ),
        ]

    def __build_message_nested_body(self, scope: ScopeInfo) -> t.Iterable[ast.stmt]:
        return chain(
            chain.from_iterable(enum.body for enum in scope.enums),
            chain.from_iterable(message.body for message in scope.messages),
        )

    def __build_message_init_stub(self, scope: ScopeInfo) -> ast.stmt:
        return self.__inner.build_init_stub(
            [
                self.__inner.build_kw_arg(
                    name=field.name,
                    annotation=self.__inner.build_optional_ref(field.annotation)
                    if self.__all_init_args_optional or field.optional or field.oneof_group is not None
                    else field.annotation,
                    default=field.default
                    if field.default is not None
                    else self.__inner.build_none_ref()
                    if self.__all_init_args_optional or field.optional or field.oneof_group is not None
                    else None,
                )
                for field in scope.fields
            ],
        )

    def __build_message_field_stubs(self, scope: ScopeInfo) -> t.Iterable[ast.stmt]:
        return chain.from_iterable(
            (
                self.__inner.build_property_getter_stub(name=field.name, annotation=field.annotation, doc=field.doc),
                self.__inner.build_property_setter_stub(name=field.name, annotation=field.annotation),
            )
            if self.__mutable
            else (self.__inner.build_property_getter_stub(name=field.name, annotation=field.annotation, doc=field.doc),)
            for field in scope.fields
        )

    def __build_protobuf_message_has_field_method_stub(self, scope: ScopeInfo) -> ast.stmt:
        optional_field_names = [self.__inner.build_const(field.name) for field in scope.fields if field.optional]

        return self.__inner.build_method_stub(
            name="HasField",
            args=[
                self.__inner.build_pos_arg(
                    name="field_name",
                    annotation=self.__inner.build_literal_ref(*optional_field_names),
                ),
            ],
            returns=self.__inner.build_bool_ref() if optional_field_names else self.__inner.build_no_return_ref(),
        )

    def __build_which_oneof_method_stubs(self, scope: ScopeInfo) -> t.Iterable[ast.stmt]:
        oneofs = defaultdict[str, list[ast.expr]](list)
        for field in scope.fields:
            if field.oneof_group is not None:
                oneofs[field.oneof_group].append(self.__inner.build_const(field.name))

        if not oneofs:
            return (
                self.__inner.build_method_stub(
                    name="WhichOneof",
                    args=[
                        self.__inner.build_pos_arg(
                            name="oneof_group",
                            annotation=self.__inner.build_no_return_ref(),
                        ),
                    ],
                    returns=self.__inner.build_no_return_ref(),
                ),
            )

        return (
            self.__inner.build_method_stub(
                name="WhichOneof",
                decorators=[self.__inner.build_overload_ref()] if len(oneofs) > 1 else None,
                args=[
                    self.__inner.build_pos_arg(
                        name="oneof_group",
                        annotation=self.__inner.build_literal_ref(ast.Constant(value=name)),
                    ),
                ],
                returns=self.__inner.build_optional_ref(self.__inner.build_literal_ref(*items)),
            )
            for name, items in oneofs.items()
        )

    def __build_extensions(self, scope: ScopeInfo) -> t.Sequence[ast.stmt]:
        return [
            self.__inner.build_attr_stub(
                name=extension.name,
                annotation=self.__inner.build_generic_ref(
                    self.__protobuf_extension_descriptor_ref,
                    extension.extended,
                    extension.annotation,
                ),
                default=extension.default,
                is_final=True,
            )
            for extension in scope.extensions
        ]

    @cached_property
    def __protobuf_message_ref(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo.from_str("google.protobuf.message"), "Message")

    @cached_property
    def __protobuf_enum_ref(self) -> TypeInfo:
        # TODO: consider enum type wrapper usage `google.protobuf.internal.enum_type_wrapper.EnumTypeWrapper`
        return TypeInfo.build(ModuleInfo(None, "enum"), "IntEnum")

    @cached_property
    def __protobuf_field_repeated_ref(self) -> TypeInfo:
        return TypeInfo.build(self.__inner.typing_module, "MutableSequence" if self.__mutable else "Sequence")

    @cached_property
    def __protobuf_map_entry_ref(self) -> TypeInfo:
        return TypeInfo.build(self.__inner.typing_module, "MutableMapping" if self.__mutable else "Mapping")

    @cached_property
    def __protobuf_descriptor_module(self) -> ModuleInfo:
        return ModuleInfo.from_str("google.protobuf.descriptor")

    @cached_property
    def __protobuf_message_descriptor_ref(self) -> TypeInfo:
        return TypeInfo.build(self.__protobuf_descriptor_module, "Descriptor")

    @cached_property
    def __protobuf_file_descriptor_ref(self) -> TypeInfo:
        return TypeInfo.build(self.__protobuf_descriptor_module, "FileDescriptor")

    @cached_property
    def __protobuf_extension_descriptor_ref(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo.from_str("pyprotostuben.protobuf.extension"), "ExtensionDescriptor")


class Pb2GrpcAstBuilder:
    def __init__(
        self,
        inner: ASTBuilder,
        *,
        is_sync: bool,
        skip_servicer: bool,
        skip_stub: bool,
    ) -> None:
        self.__inner = inner
        self.__is_sync = is_sync
        self.__skip_servicer = skip_servicer
        self.__skip_stub = skip_stub

    def build_servicer_def(self, name: str, doc: t.Optional[str], scope: ScopeInfo) -> t.Sequence[ast.stmt]:
        if self.__skip_servicer:
            return []

        return [
            self.__inner.build_abstract_class_def(
                name=f"{name}Servicer",
                doc=doc,
                body=[self.__build_servicer_method_def(method) for method in scope.methods],
            ),
        ]

    def build_servicer_registrator_def(self, name: str) -> t.Sequence[ast.stmt]:
        if self.__skip_servicer:
            return []

        return [
            self.__inner.build_func_stub(
                name=f"add_{name}Servicer_to_server",
                args=[
                    self.__inner.build_pos_arg(
                        name="servicer",
                        annotation=self.__inner.build_name(f"{name}Servicer"),
                    ),
                    self.__inner.build_pos_arg(
                        name="server",
                        annotation=self.__grpc_server_ref,
                    ),
                ],
                returns=self.__inner.build_none_ref(),
            )
        ]

    def build_stub_def(self, name: str, doc: t.Optional[str], scope: ScopeInfo) -> t.Sequence[ast.stmt]:
        if self.__skip_stub:
            return []

        return [
            self.__inner.build_class_def(
                name=f"{name}Stub",
                doc=doc,
                body=list(
                    chain(
                        (self.__build_stub_init_def(),),
                        (self.__build_stub_method_def(info) for info in scope.methods),
                    )
                ),
            ),
        ]

    def build_module(self, scope: ScopeInfo) -> ast.Module:
        body = list(
            chain.from_iterable(
                chain(service.servicer, service.registrator, service.stub) for service in scope.services
            )
        )
        return self.__inner.build_module(None, body)

    @cached_property
    def __grpc_streaming_generic(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(None, "typing"), "Iterator" if self.__is_sync else "AsyncIterator")

    @cached_property
    def __grpc_module(self) -> ModuleInfo:
        return ModuleInfo(None, "grpc") if self.__is_sync else ModuleInfo.from_str("grpc.aio")

    @cached_property
    def __grpc_server_ref(self) -> TypeInfo:
        return TypeInfo.build(self.__grpc_module, "Server")

    @cached_property
    def __grpc_servicer_context_ref(self) -> TypeInfo:
        return TypeInfo.build(self.__grpc_module, "ServicerContext")

    @cached_property
    def __grpc_channel_ref(self) -> TypeInfo:
        return TypeInfo.build(self.__grpc_module, "Channel")

    @cached_property
    def __grpc_metadata_ref(self) -> TypeInfo:
        return TypeInfo.build(self.__grpc_module, "MetadataType")

    @cached_property
    def __grpc_call_credentials_ref(self) -> TypeInfo:
        # always grpc module
        return TypeInfo.build(ModuleInfo(None, "grpc"), "CallCredentials")

    @cached_property
    def __grpc_compression_ref(self) -> TypeInfo:
        # always grpc module
        return TypeInfo.build(ModuleInfo(None, "grpc"), "Compression")

    @cached_property
    def __grpc_unary_unary_call_ref(self) -> TypeInfo:
        return TypeInfo.build(self.__grpc_module, "UnaryUnaryCall")

    @cached_property
    def __grpc_unary_stream_call_ref(self) -> TypeInfo:
        return TypeInfo.build(self.__grpc_module, "UnaryStreamCall")

    @cached_property
    def __grpc_stream_unary_call_ref(self) -> TypeInfo:
        return TypeInfo.build(self.__grpc_module, "StreamUnaryCall")

    @cached_property
    def __grpc_stream_stream_call_ref(self) -> TypeInfo:
        return TypeInfo.build(self.__grpc_module, "StreamStreamCall")

    def __build_servicer_method_def(self, method: MethodInfo) -> ast.stmt:
        request, response = self.__build_servicer_method_inout_refs(method)

        return self.__inner.build_abstract_method_stub(
            name=method.name,
            args=[
                self.__inner.build_pos_arg(
                    name="request",
                    annotation=request,
                ),
                self.__inner.build_pos_arg(
                    name="context",
                    annotation=self.__inner.build_generic_ref(
                        self.__grpc_servicer_context_ref,
                        method.server_input,
                        method.server_output,
                    ),
                ),
            ],
            returns=response,
            doc=method.doc,
            is_async=not self.__is_sync,
        )

    def __build_stub_init_def(self) -> ast.stmt:
        return self.__inner.build_init_stub(
            args=[
                self.__inner.build_pos_arg(
                    name="channel",
                    annotation=self.__grpc_channel_ref,
                ),
            ],
        )

    def __build_stub_method_def(self, info: MethodInfo) -> ast.stmt:
        request, response = self.__build_stub_method_inout_refs(info)

        return self.__inner.build_method_stub(
            name=info.name,
            args=[
                self.__inner.build_pos_arg("request", request),
                self.__inner.build_kw_arg(
                    name="timeout",
                    annotation=self.__inner.build_optional_ref(self.__inner.build_float_ref()),
                    default=self.__inner.build_none_ref(),
                ),
                self.__inner.build_kw_arg(
                    name="metadata",
                    annotation=self.__inner.build_optional_ref(self.__grpc_metadata_ref),
                    default=self.__inner.build_none_ref(),
                ),
                self.__inner.build_kw_arg(
                    name="credentials",
                    annotation=self.__inner.build_optional_ref(self.__grpc_call_credentials_ref),
                    default=self.__inner.build_none_ref(),
                ),
                self.__inner.build_kw_arg(
                    name="wait_for_ready",
                    annotation=self.__inner.build_optional_ref(self.__inner.build_bool_ref()),
                    default=self.__inner.build_none_ref(),
                ),
                self.__inner.build_kw_arg(
                    name="compression",
                    annotation=self.__inner.build_optional_ref(self.__grpc_compression_ref),
                    default=self.__inner.build_none_ref(),
                ),
            ],
            returns=response,
            doc=info.doc,
        )

    def __build_servicer_method_inout_refs(self, info: MethodInfo) -> tuple[ast.expr, ast.expr]:
        if not info.server_input_streaming and not info.server_output_streaming:
            return (
                self.__build_message_ref(info.server_input),
                self.__build_message_ref(info.server_output),
            )

        if not info.server_input_streaming and info.server_output_streaming:
            return (
                self.__build_message_ref(info.server_input),
                self.__build_streaming_ref(info.server_output),
            )

        if info.server_input_streaming and not info.server_output_streaming:
            return (
                self.__build_streaming_ref(info.server_input),
                self.__build_message_ref(info.server_output),
            )

        if info.server_input_streaming and info.server_output_streaming:
            return (
                self.__build_streaming_ref(info.server_input),
                self.__build_streaming_ref(info.server_output),
            )

        msg = "invalid method streaming options"
        raise ValueError(msg, info)

    def __build_stub_method_inout_refs(self, info: MethodInfo) -> tuple[ast.expr, ast.expr]:
        if not info.server_input_streaming and not info.server_output_streaming:
            return (
                self.__build_message_ref(info.server_input),
                self.__inner.build_generic_ref(
                    self.__grpc_unary_unary_call_ref,
                    info.server_input,
                    info.server_output,
                ),
            )

        if not info.server_input_streaming and info.server_output_streaming:
            return (
                self.__build_message_ref(info.server_input),
                self.__inner.build_generic_ref(
                    self.__grpc_unary_stream_call_ref,
                    info.server_input,
                    info.server_output,
                ),
            )

        if info.server_input_streaming and not info.server_output_streaming:
            return (
                self.__build_streaming_ref(info.server_input),
                self.__inner.build_generic_ref(
                    self.__grpc_stream_unary_call_ref,
                    info.server_input,
                    info.server_output,
                ),
            )

        if info.server_input_streaming and info.server_output_streaming:
            return (
                self.__build_streaming_ref(info.server_input),
                self.__inner.build_generic_ref(
                    self.__grpc_stream_stream_call_ref,
                    info.server_input,
                    info.server_output,
                ),
            )

        msg = "invalid method streaming options"
        raise ValueError(msg, info)

    def __build_message_ref(self, ref: TypeRef) -> ast.expr:
        return self.__inner.build_ref(ref)

    def __build_streaming_ref(self, inner: TypeRef) -> ast.expr:
        return self.__inner.build_generic_ref(self.__grpc_streaming_generic, inner)
