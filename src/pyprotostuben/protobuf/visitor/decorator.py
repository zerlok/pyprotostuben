import abc
import typing as t
from dataclasses import replace

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

T = t.TypeVar("T")


class ProtoVisitorDecorator(t.Generic[T], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def enter_file_descriptor_proto(self, context: FileDescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_file_descriptor_proto(self, context: FileDescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_enum_descriptor_proto(self, context: EnumDescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_enum_descriptor_proto(self, context: EnumDescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_descriptor_proto(self, context: DescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_descriptor_proto(self, context: DescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_oneof_descriptor_proto(self, context: OneofDescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_oneof_descriptor_proto(self, context: OneofDescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_field_descriptor_proto(self, context: FieldDescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_field_descriptor_proto(self, context: FieldDescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_service_descriptor_proto(self, context: ServiceDescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_service_descriptor_proto(self, context: ServiceDescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_method_descriptor_proto(self, context: MethodDescriptorContext[T]) -> T:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_method_descriptor_proto(self, context: MethodDescriptorContext[T]) -> T:
        raise NotImplementedError


class EnterProtoVisitorDecorator(ProtoVisitorDecorator[T]):
    def __init__(self, *nested: ProtoVisitor[T]) -> None:
        self.__nested = nested

    def enter_file_descriptor_proto(self, context: FileDescriptorContext[T]) -> T:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_file_descriptor_proto(replace(context, meta=meta))

        return meta

    def leave_file_descriptor_proto(self, context: FileDescriptorContext[T]) -> T:
        return context.meta

    def enter_enum_descriptor_proto(self, context: EnumDescriptorContext[T]) -> T:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_enum_descriptor_proto(replace(context, meta=meta))

        return meta

    def leave_enum_descriptor_proto(self, context: EnumDescriptorContext[T]) -> T:
        return context.meta

    def enter_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T]) -> T:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_enum_value_descriptor_proto(replace(context, meta=meta))

        return meta

    def leave_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T]) -> T:
        return context.meta

    def enter_descriptor_proto(self, context: DescriptorContext[T]) -> T:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_descriptor_proto(replace(context, meta=meta))

        return meta

    def leave_descriptor_proto(self, context: DescriptorContext[T]) -> T:
        return context.meta

    def enter_oneof_descriptor_proto(self, context: OneofDescriptorContext[T]) -> T:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_oneof_descriptor_proto(replace(context, meta=meta))

        return meta

    def leave_oneof_descriptor_proto(self, context: OneofDescriptorContext[T]) -> T:
        return context.meta

    def enter_field_descriptor_proto(self, context: FieldDescriptorContext[T]) -> T:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_field_descriptor_proto(replace(context, meta=meta))

        return meta

    def leave_field_descriptor_proto(self, context: FieldDescriptorContext[T]) -> T:
        return context.meta

    def enter_service_descriptor_proto(self, context: ServiceDescriptorContext[T]) -> T:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_service_descriptor_proto(replace(context, meta=meta))

        return meta

    def leave_service_descriptor_proto(self, context: ServiceDescriptorContext[T]) -> T:
        return context.meta

    def enter_method_descriptor_proto(self, context: MethodDescriptorContext[T]) -> T:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_method_descriptor_proto(replace(context, meta=meta))

        return meta

    def leave_method_descriptor_proto(self, context: MethodDescriptorContext[T]) -> T:
        return context.meta


class LeaveProtoVisitorDecorator(ProtoVisitorDecorator[T]):
    def __init__(self, *nested: ProtoVisitor[T]) -> None:
        self.__nested = nested

    def enter_file_descriptor_proto(self, context: FileDescriptorContext[T]) -> T:
        return context.meta

    def leave_file_descriptor_proto(self, context: FileDescriptorContext[T]) -> T:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_file_descriptor_proto(replace(context, meta=meta))

        return meta

    def enter_enum_descriptor_proto(self, context: EnumDescriptorContext[T]) -> T:
        return context.meta

    def leave_enum_descriptor_proto(self, context: EnumDescriptorContext[T]) -> T:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_enum_descriptor_proto(replace(context, meta=meta))

        return meta

    def enter_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T]) -> T:
        return context.meta

    def leave_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T]) -> T:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_enum_value_descriptor_proto(replace(context, meta=meta))

        return meta

    def enter_descriptor_proto(self, context: DescriptorContext[T]) -> T:
        return context.meta

    def leave_descriptor_proto(self, context: DescriptorContext[T]) -> T:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_descriptor_proto(replace(context, meta=meta))

        return meta

    def enter_oneof_descriptor_proto(self, context: OneofDescriptorContext[T]) -> T:
        return context.meta

    def leave_oneof_descriptor_proto(self, context: OneofDescriptorContext[T]) -> T:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_oneof_descriptor_proto(replace(context, meta=meta))

        return meta

    def enter_field_descriptor_proto(self, context: FieldDescriptorContext[T]) -> T:
        return context.meta

    def leave_field_descriptor_proto(self, context: FieldDescriptorContext[T]) -> T:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_field_descriptor_proto(replace(context, meta=meta))

        return meta

    def enter_service_descriptor_proto(self, context: ServiceDescriptorContext[T]) -> T:
        return context.meta

    def leave_service_descriptor_proto(self, context: ServiceDescriptorContext[T]) -> T:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_service_descriptor_proto(replace(context, meta=meta))

        return meta

    def enter_method_descriptor_proto(self, context: MethodDescriptorContext[T]) -> T:
        return context.meta

    def leave_method_descriptor_proto(self, context: MethodDescriptorContext[T]) -> T:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_method_descriptor_proto(replace(context, meta=meta))

        return meta
