from functools import cached_property

from pyprotostuben.protobuf.builder.grpc import GRPCASTBuilder
from pyprotostuben.python.info import ModuleInfo, PackageInfo, TypeInfo


class GRPCAioASTBuilder(GRPCASTBuilder):
    @cached_property
    def grpc_streaming_generic(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(None, "typing"), "AsyncIterator")

    @property
    def is_grpc_servicer_async(self) -> bool:
        return True

    @property
    def is_grpc_stub_async(self) -> bool:
        return True

    @cached_property
    def grpc_server_ref(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(PackageInfo(None, "grpc"), "aio"), "Server")

    @cached_property
    def grpc_servicer_context_ref(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(PackageInfo(None, "grpc"), "aio"), "ServicerContext")

    @cached_property
    def grpc_channel_ref(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(PackageInfo(None, "grpc"), "aio"), "Channel")

    @cached_property
    def grpc_metadata_ref(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(PackageInfo(None, "grpc"), "aio"), "MetadataType")

    @cached_property
    def grpc_unary_unary_call_ref(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(PackageInfo(None, "grpc"), "aio"), "UnaryUnaryCall")

    @cached_property
    def grpc_unary_stream_call_ref(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(PackageInfo(None, "grpc"), "aio"), "UnaryStreamCall")

    @cached_property
    def grpc_stream_unary_call_ref(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(PackageInfo(None, "grpc"), "aio"), "StreamUnaryCall")

    @cached_property
    def grpc_stream_stream_call_ref(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(PackageInfo(None, "grpc"), "aio"), "StreamStreamCall")
