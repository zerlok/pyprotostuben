import abc
import typing as t

from google.protobuf.descriptor_pb2 import (
    DescriptorProto,
    EnumDescriptorProto,
    EnumValueDescriptorProto,
    FieldDescriptorProto,
    FileDescriptorProto,
    MethodDescriptorProto,
    OneofDescriptorProto,
    ServiceDescriptorProto,
)

Proto = t.Union[
    FileDescriptorProto,
    EnumDescriptorProto,
    EnumValueDescriptorProto,
    DescriptorProto,
    OneofDescriptorProto,
    FieldDescriptorProto,
    ServiceDescriptorProto,
    MethodDescriptorProto,
]


class ProtoVisitor(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def visit_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_descriptor_proto(self, proto: DescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        raise NotImplementedError


def visit(visitor: ProtoVisitor, *protos: Proto) -> None:
    for proto in protos:
        if isinstance(proto, FileDescriptorProto):
            visitor.visit_file_descriptor_proto(proto)
        elif isinstance(proto, EnumDescriptorProto):
            visitor.visit_enum_descriptor_proto(proto)
        elif isinstance(proto, EnumValueDescriptorProto):
            visitor.visit_enum_value_descriptor_proto(proto)
        elif isinstance(proto, DescriptorProto):
            visitor.visit_descriptor_proto(proto)
        elif isinstance(proto, OneofDescriptorProto):
            visitor.visit_oneof_descriptor_proto(proto)
        elif isinstance(proto, FieldDescriptorProto):
            visitor.visit_field_descriptor_proto(proto)
        elif isinstance(proto, ServiceDescriptorProto):
            visitor.visit_service_descriptor_proto(proto)
        elif isinstance(proto, MethodDescriptorProto):
            visitor.visit_method_descriptor_proto(proto)
        else:
            t.assert_never(proto)
