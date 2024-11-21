import abc
import typing as t

from pyprotostuben.protobuf.visitor.abc import ProtoVisitor
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


class ProtoVisitorDecorator(t.Generic[T_contra], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def enter_file_descriptor_proto(self, context: FileDescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_file_descriptor_proto(self, context: FileDescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_enum_descriptor_proto(self, context: EnumDescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_enum_descriptor_proto(self, context: EnumDescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_descriptor_proto(self, context: DescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_descriptor_proto(self, context: DescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_oneof_descriptor_proto(self, context: OneofDescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_oneof_descriptor_proto(self, context: OneofDescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_field_descriptor_proto(self, context: FieldDescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_field_descriptor_proto(self, context: FieldDescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_service_descriptor_proto(self, context: ServiceDescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_service_descriptor_proto(self, context: ServiceDescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_method_descriptor_proto(self, context: MethodDescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_method_descriptor_proto(self, context: MethodDescriptorContext[T_contra]) -> None:
        raise NotImplementedError


class EnterProtoVisitorDecorator(ProtoVisitorDecorator[T_contra]):
    def __init__(self, *nested: ProtoVisitor[T_contra]) -> None:
        self.__nested = nested

    def enter_file_descriptor_proto(self, context: FileDescriptorContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_file_descriptor_proto(context)

    def leave_file_descriptor_proto(self, context: FileDescriptorContext[T_contra]) -> None:
        pass

    def enter_enum_descriptor_proto(self, context: EnumDescriptorContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_enum_descriptor_proto(context)

    def leave_enum_descriptor_proto(self, context: EnumDescriptorContext[T_contra]) -> None:
        pass

    def enter_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_enum_value_descriptor_proto(context)

    def leave_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T_contra]) -> None:
        pass

    def enter_descriptor_proto(self, context: DescriptorContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_descriptor_proto(context)

    def leave_descriptor_proto(self, context: DescriptorContext[T_contra]) -> None:
        pass

    def enter_oneof_descriptor_proto(self, context: OneofDescriptorContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_oneof_descriptor_proto(context)

    def leave_oneof_descriptor_proto(self, context: OneofDescriptorContext[T_contra]) -> None:
        pass

    def enter_field_descriptor_proto(self, context: FieldDescriptorContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_field_descriptor_proto(context)

    def leave_field_descriptor_proto(self, context: FieldDescriptorContext[T_contra]) -> None:
        pass

    def enter_service_descriptor_proto(self, context: ServiceDescriptorContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_service_descriptor_proto(context)

    def leave_service_descriptor_proto(self, context: ServiceDescriptorContext[T_contra]) -> None:
        pass

    def enter_method_descriptor_proto(self, context: MethodDescriptorContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_method_descriptor_proto(context)

    def leave_method_descriptor_proto(self, context: MethodDescriptorContext[T_contra]) -> None:
        pass


class LeaveProtoVisitorDecorator(ProtoVisitorDecorator[T_contra]):
    def __init__(self, *nested: ProtoVisitor[T_contra]) -> None:
        self.__nested = nested

    def enter_file_descriptor_proto(self, context: FileDescriptorContext[T_contra]) -> None:
        pass

    def leave_file_descriptor_proto(self, context: FileDescriptorContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_file_descriptor_proto(context)

    def enter_enum_descriptor_proto(self, context: EnumDescriptorContext[T_contra]) -> None:
        pass

    def leave_enum_descriptor_proto(self, context: EnumDescriptorContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_enum_descriptor_proto(context)

    def enter_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T_contra]) -> None:
        pass

    def leave_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_enum_value_descriptor_proto(context)

    def enter_descriptor_proto(self, context: DescriptorContext[T_contra]) -> None:
        pass

    def leave_descriptor_proto(self, context: DescriptorContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_descriptor_proto(context)

    def enter_oneof_descriptor_proto(self, context: OneofDescriptorContext[T_contra]) -> None:
        pass

    def leave_oneof_descriptor_proto(self, context: OneofDescriptorContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_oneof_descriptor_proto(context)

    def enter_field_descriptor_proto(self, context: FieldDescriptorContext[T_contra]) -> None:
        pass

    def leave_field_descriptor_proto(self, context: FieldDescriptorContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_field_descriptor_proto(context)

    def enter_service_descriptor_proto(self, context: ServiceDescriptorContext[T_contra]) -> None:
        pass

    def leave_service_descriptor_proto(self, context: ServiceDescriptorContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_service_descriptor_proto(context)

    def enter_method_descriptor_proto(self, context: MethodDescriptorContext[T_contra]) -> None:
        pass

    def leave_method_descriptor_proto(self, context: MethodDescriptorContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_method_descriptor_proto(context)
