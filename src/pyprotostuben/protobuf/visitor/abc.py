import abc
import typing as t

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

T = t.TypeVar("T")


class ProtoVisitor(t.Generic[T], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def visit_file_descriptor_proto(self, context: FileDescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_enum_descriptor_proto(self, context: EnumDescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_descriptor_proto(self, context: DescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_oneof_descriptor_proto(self, context: OneofDescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_field_descriptor_proto(self, context: FieldDescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_service_descriptor_proto(self, context: ServiceDescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_method_descriptor_proto(self, context: MethodDescriptorContext[T]) -> T:
        raise NotImplementedError
