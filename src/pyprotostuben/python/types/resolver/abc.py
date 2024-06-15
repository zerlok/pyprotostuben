import abc
import typing as t

from google.protobuf.descriptor_pb2 import (
    FieldDescriptorProto,
    DescriptorProto,
    EnumDescriptorProto,
    MethodDescriptorProto,
    ServiceDescriptorProto,
)

T_co = t.TypeVar("T_co")


class TypeResolver(t.Generic[T_co], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def resolve_bytes(self) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_bool(self) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_int(self) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_float(self) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_str(self) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_final(self) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_no_return(self) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_overload(self) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_literal(self) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_property(self) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_abstract_meta(self) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_abstract_method(self) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_optional(self) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_sequence(self) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_mapping(self) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_async_iterator(self) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_protobuf_enum_base(self, proto: EnumDescriptorProto) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_protobuf_message_base(self, proto: DescriptorProto) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_protobuf_field(self, proto: FieldDescriptorProto) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_grpc_server(self, proto: ServiceDescriptorProto) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_grpc_channel(self, proto: ServiceDescriptorProto) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_grpc_servicer_context(self, proto: MethodDescriptorProto) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_grpc_stub_timeout(self, proto: MethodDescriptorProto) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_grpc_stub_metadata_type(self, proto: MethodDescriptorProto) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_grpc_stub_credentials(self, proto: MethodDescriptorProto) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_grpc_stub_wait_for_ready(self, proto: MethodDescriptorProto) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_grpc_stub_compression(self, proto: MethodDescriptorProto) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_grpc_stub_unary_unary_call(self, proto: MethodDescriptorProto) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_grpc_stub_unary_stream_call(self, proto: MethodDescriptorProto) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_grpc_stub_stream_unary_call(self, proto: MethodDescriptorProto) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_grpc_stub_stream_stream_call(self, proto: MethodDescriptorProto) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_grpc_method_input(self, proto: MethodDescriptorProto) -> T_co:
        raise NotImplementedError()

    @abc.abstractmethod
    def resolve_grpc_method_output(self, proto: MethodDescriptorProto) -> T_co:
        raise NotImplementedError()
