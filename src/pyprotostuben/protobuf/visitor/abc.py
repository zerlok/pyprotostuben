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

T_contra = t.TypeVar("T_contra", contravariant=True)


class ProtoVisitor(t.Generic[T_contra], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def visit_file_descriptor_proto(self, context: FileDescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_enum_descriptor_proto(self, context: EnumDescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_descriptor_proto(self, context: DescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_oneof_descriptor_proto(self, context: OneofDescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_field_descriptor_proto(self, context: FieldDescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_service_descriptor_proto(self, context: ServiceDescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_method_descriptor_proto(self, context: MethodDescriptorContext[T_contra]) -> None:
        raise NotImplementedError
