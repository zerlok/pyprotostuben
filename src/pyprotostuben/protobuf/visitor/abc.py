import abc

from pyprotostuben.protobuf.visitor.model import (
    DescriptorContext,
    EnumDescriptorContext,
    EnumValueDescriptorContext,
    FieldDescriptorContext,
    FileDescriptorContext,
    MethodDescriptorContext,
    OneofDescriptorContext,
    ServiceDescriptorContext,
)


class ProtoVisitor(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def visit_file_descriptor_proto(self, context: FileDescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_enum_descriptor_proto(self, context: EnumDescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_descriptor_proto(self, context: DescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_oneof_descriptor_proto(self, context: OneofDescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_field_descriptor_proto(self, context: FieldDescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_service_descriptor_proto(self, context: ServiceDescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_method_descriptor_proto(self, context: MethodDescriptorContext) -> None:
        raise NotImplementedError
