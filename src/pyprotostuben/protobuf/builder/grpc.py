import ast
import typing as t
from dataclasses import dataclass
from functools import cached_property

from pyprotostuben.protobuf.registry import MessageInfo
from pyprotostuben.python.ast_builder import ASTBuilder
from pyprotostuben.python.info import ModuleInfo, PackageInfo, TypeInfo


@dataclass(frozen=True)
class MethodInfo:
    name: str
    client_input: ast.expr
    client_streaming: bool
    server_output: ast.expr
    server_streaming: bool


class GRPCASTBuilder:
    def __init__(
        self,
        inner: ASTBuilder,
        *,
        is_sync: bool,
        skip_servicer: bool,
        skip_stub: bool,
    ) -> None:
        self.inner = inner
        self.__is_sync = is_sync
        self.__skip_servicer = skip_servicer
        self.__skip_stub = skip_stub

        self.__base_grpc_module = (
            ModuleInfo(None, "grpc") if self.__is_sync else ModuleInfo(PackageInfo(None, "grpc"), "aio")
        )

    @cached_property
    def grpc_streaming_generic(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(None, "typing"), "Iterator" if self.__is_sync else "AsyncIterator")

    @cached_property
    def grpc_server_ref(self) -> TypeInfo:
        return TypeInfo.build(self.__base_grpc_module, "Server")

    @cached_property
    def grpc_servicer_context_ref(self) -> TypeInfo:
        return TypeInfo.build(self.__base_grpc_module, "ServicerContext")

    @cached_property
    def grpc_channel_ref(self) -> TypeInfo:
        return TypeInfo.build(self.__base_grpc_module, "Channel")

    @cached_property
    def grpc_metadata_ref(self) -> TypeInfo:
        return TypeInfo.build(self.__base_grpc_module, "MetadataType")

    @cached_property
    def grpc_call_credentials_ref(self) -> TypeInfo:
        # always grpc module
        return TypeInfo.build(ModuleInfo(None, "grpc"), "CallCredentials")

    @cached_property
    def grpc_compression_ref(self) -> TypeInfo:
        # always grpc module
        return TypeInfo.build(ModuleInfo(None, "grpc"), "Compression")

    @cached_property
    def grpc_unary_unary_call_ref(self) -> TypeInfo:
        return TypeInfo.build(self.__base_grpc_module, "UnaryUnaryCall")

    @cached_property
    def grpc_unary_stream_call_ref(self) -> TypeInfo:
        return TypeInfo.build(self.__base_grpc_module, "UnaryStreamCall")

    @cached_property
    def grpc_stream_unary_call_ref(self) -> TypeInfo:
        return TypeInfo.build(self.__base_grpc_module, "StreamUnaryCall")

    @cached_property
    def grpc_stream_stream_call_ref(self) -> TypeInfo:
        return TypeInfo.build(self.__base_grpc_module, "StreamStreamCall")

    def build_grpc_module(self, deps: t.Collection[ModuleInfo], body: t.Sequence[ast.stmt]) -> ast.Module:
        return self.inner.build_module(deps, body) if body else self.inner.build_module([], [])

    def build_grpc_servicer_defs(self, name: str, methods: t.Sequence[MethodInfo]) -> t.Sequence[ast.stmt]:
        if self.__skip_servicer:
            return []

        return [
            self.inner.build_abstract_class_def(
                name=name,
                body=[self.build_grpc_servicer_method_def(info) for info in methods],
            ),
            self.build_grpc_servicer_registrator_def(name, ast.Name(id=name)),
        ]

    def build_grpc_stub_defs(self, name: str, methods: t.Sequence[MethodInfo]) -> t.Sequence[ast.stmt]:
        if self.__skip_stub:
            return []

        return [
            self.inner.build_class_def(
                name=name,
                body=[
                    self.build_grpc_stub_init_def(),
                    *(self.build_grpc_stub_method_def(info) for info in methods),
                ],
            ),
        ]

    def build_grpc_message_ref(self, info: MessageInfo) -> ast.expr:
        return self.inner.build_ref(info)

    def build_grpc_streaming_ref(self, inner: ast.expr) -> ast.expr:
        return self.inner.build_generic_ref(self.grpc_streaming_generic, inner)

    def build_grpc_servicer_method_def(self, info: MethodInfo) -> ast.stmt:
        request, response = self.build_grpc_servicer_method_request_response_refs(info)

        return self.inner.build_abstract_method_stub(
            name=info.name,
            args=[
                self.inner.build_pos_arg(
                    name="request",
                    annotation=request,
                ),
                self.inner.build_pos_arg(
                    name="context",
                    annotation=self.inner.build_generic_ref(
                        self.grpc_servicer_context_ref,
                        info.client_input,
                        info.server_output,
                    ),
                ),
            ],
            returns=response,
            is_async=not self.__is_sync,
        )

    def build_grpc_servicer_method_request_response_refs(self, info: MethodInfo) -> t.Tuple[ast.expr, ast.expr]:
        if not info.client_streaming and not info.server_streaming:
            return (
                info.client_input,
                info.server_output,
            )

        if not info.client_streaming and info.server_streaming:
            return (
                info.client_input,
                self.build_grpc_streaming_ref(info.server_output),
            )

        if info.client_streaming and not info.server_streaming:
            return (
                self.build_grpc_streaming_ref(info.client_input),
                info.server_output,
            )

        if info.client_streaming and info.server_streaming:
            return (
                self.build_grpc_streaming_ref(info.client_input),
                self.build_grpc_streaming_ref(info.server_output),
            )

        msg = "invalid method streaming options"
        raise ValueError(msg, info)

    def build_grpc_servicer_registrator_def(self, name: str, servicer: ast.expr) -> ast.stmt:
        return self.inner.build_func_stub(
            name=f"add_{name}_to_server",
            args=[
                self.inner.build_pos_arg(
                    name="servicer",
                    annotation=servicer,
                ),
                self.inner.build_pos_arg(
                    name="server",
                    annotation=self.grpc_server_ref,
                ),
            ],
            returns=self.inner.build_none_ref(),
        )

    def build_grpc_stub_init_def(self) -> ast.stmt:
        return self.inner.build_init_stub(
            args=[
                self.inner.build_pos_arg(
                    name="channel",
                    annotation=self.grpc_channel_ref,
                ),
            ],
        )

    def build_grpc_stub_method_def(self, info: MethodInfo) -> ast.stmt:
        request, response = self.build_grpc_stub_method_request_response_refs(info)

        return self.inner.build_method_stub(
            name=info.name,
            args=[
                self.inner.build_pos_arg("request", request),
                self.inner.build_kw_arg(
                    name="timeout",
                    annotation=self.inner.build_optional_ref(self.inner.build_float_ref()),
                    default=self.inner.build_none_ref(),
                ),
                self.inner.build_kw_arg(
                    name="metadata",
                    annotation=self.inner.build_optional_ref(self.grpc_metadata_ref),
                    default=self.inner.build_none_ref(),
                ),
                self.inner.build_kw_arg(
                    name="credentials",
                    annotation=self.inner.build_optional_ref(self.grpc_call_credentials_ref),
                    default=self.inner.build_none_ref(),
                ),
                self.inner.build_kw_arg(
                    name="wait_for_ready",
                    annotation=self.inner.build_optional_ref(self.inner.build_bool_ref()),
                    default=self.inner.build_none_ref(),
                ),
                self.inner.build_kw_arg(
                    name="compression",
                    annotation=self.inner.build_optional_ref(self.grpc_compression_ref),
                    default=self.inner.build_none_ref(),
                ),
            ],
            returns=response,
        )

    def build_grpc_stub_method_request_response_refs(self, info: MethodInfo) -> t.Tuple[ast.expr, ast.expr]:
        if not info.client_streaming and not info.server_streaming:
            return (
                info.client_input,
                self.inner.build_generic_ref(self.grpc_unary_unary_call_ref, info.client_input, info.server_output),
            )

        if not info.client_streaming and info.server_streaming:
            return (
                info.client_input,
                self.inner.build_generic_ref(self.grpc_unary_stream_call_ref, info.client_input, info.server_output),
            )

        if info.client_streaming and not info.server_streaming:
            return (
                self.build_grpc_streaming_ref(info.client_input),
                self.inner.build_generic_ref(self.grpc_stream_unary_call_ref, info.client_input, info.server_output),
            )

        if info.client_streaming and info.server_streaming:
            return (
                self.build_grpc_streaming_ref(info.client_input),
                self.inner.build_generic_ref(self.grpc_stream_stream_call_ref, info.client_input, info.server_output),
            )

        msg = "invalid method streaming options"
        raise ValueError(msg, info)
