import typing as t

from google.protobuf.descriptor_pb2 import (
    FieldDescriptorProto,
    DescriptorProto,
    EnumDescriptorProto,
    MethodDescriptorProto,
    ServiceDescriptorProto,
)

from pyprotostuben.logging import LoggerMixin
from pyprotostuben.python.info import TypeInfo, ModuleInfo, NamespaceInfo
from pyprotostuben.python.types.resolver.abc import TypeResolver


class ModuleDependencyResolver(TypeResolver[NamespaceInfo], LoggerMixin):
    def __init__(
        self,
        inner: TypeResolver[TypeInfo],
        module: ModuleInfo,
        deps: t.Set[ModuleInfo],
    ) -> None:
        self.__inner = inner
        self.__module = module
        self.__deps = deps

    def resolve_bytes(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_bytes())

    def resolve_bool(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_bool())

    def resolve_int(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_int())

    def resolve_float(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_float())

    def resolve_str(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_str())

    def resolve_final(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_final())

    def resolve_no_return(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_no_return())

    def resolve_overload(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_overload())

    def resolve_literal(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_literal())

    def resolve_property(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_property())

    def resolve_abstract_meta(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_abstract_meta())

    def resolve_abstract_method(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_abstract_method())

    def resolve_optional(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_optional())

    def resolve_sequence(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_sequence())

    def resolve_mapping(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_mapping())

    def resolve_async_iterator(self) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_async_iterator())

    def resolve_protobuf_enum_base(self, proto: EnumDescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_protobuf_enum_base(proto))

    def resolve_protobuf_message_base(self, proto: DescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_protobuf_message_base(proto))

    def resolve_protobuf_field(self, proto: FieldDescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_protobuf_field(proto))

    def resolve_grpc_server(self, proto: ServiceDescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_grpc_server(proto))

    def resolve_grpc_channel(self, proto: ServiceDescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_grpc_channel(proto))

    def resolve_grpc_servicer_context(self, proto: MethodDescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_grpc_servicer_context(proto))

    def resolve_grpc_stub_timeout(self, proto: MethodDescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_grpc_stub_timeout(proto))

    def resolve_grpc_stub_metadata_type(self, proto: MethodDescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_grpc_stub_metadata_type(proto))

    def resolve_grpc_stub_credentials(self, proto: MethodDescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_grpc_stub_credentials(proto))

    def resolve_grpc_stub_wait_for_ready(self, proto: MethodDescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_grpc_stub_wait_for_ready(proto))

    def resolve_grpc_stub_compression(self, proto: MethodDescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_grpc_stub_compression(proto))

    def resolve_grpc_stub_unary_unary_call(self, proto: MethodDescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_grpc_stub_unary_unary_call(proto))

    def resolve_grpc_stub_unary_stream_call(self, proto: MethodDescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_grpc_stub_unary_stream_call(proto))

    def resolve_grpc_stub_stream_unary_call(self, proto: MethodDescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_grpc_stub_stream_unary_call(proto))

    def resolve_grpc_stub_stream_stream_call(self, proto: MethodDescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_grpc_stub_stream_stream_call(proto))

    def resolve_grpc_method_input(self, proto: MethodDescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_grpc_method_input(proto))

    def resolve_grpc_method_output(self, proto: MethodDescriptorProto) -> NamespaceInfo:
        return self.__resolve(self.__inner.resolve_grpc_method_output(proto))

    def __resolve(self, type_: TypeInfo) -> NamespaceInfo:
        if type_.module == self.__module:
            ns = type_.namespace

        else:
            self.__deps.add(type_.module)
            ns = type_

        self._log.debug("resolved", type_=type_, ns=ns)

        return ns
