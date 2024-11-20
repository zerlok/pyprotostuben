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

T_co = t.TypeVar("T_co", covariant=True)


class ProtoVisitorDecorator(t.Generic[T_co], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def enter_file_descriptor_proto(self, context: FileDescriptorContext[T_co]) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_file_descriptor_proto(self, context: FileDescriptorContext[T_co]) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_enum_descriptor_proto(self, context: EnumDescriptorContext[T_co]) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_enum_descriptor_proto(self, context: EnumDescriptorContext[T_co]) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T_co]) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T_co]) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_descriptor_proto(self, context: DescriptorContext[T_co]) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_descriptor_proto(self, context: DescriptorContext[T_co]) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_oneof_descriptor_proto(self, context: OneofDescriptorContext[T_co]) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_oneof_descriptor_proto(self, context: OneofDescriptorContext[T_co]) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_field_descriptor_proto(self, context: FieldDescriptorContext[T_co]) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_field_descriptor_proto(self, context: FieldDescriptorContext[T_co]) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_service_descriptor_proto(self, context: ServiceDescriptorContext[T_co]) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_service_descriptor_proto(self, context: ServiceDescriptorContext[T_co]) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_method_descriptor_proto(self, context: MethodDescriptorContext[T_co]) -> T_co:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_method_descriptor_proto(self, context: MethodDescriptorContext[T_co]) -> T_co:
        raise NotImplementedError


class EnterProtoVisitorDecorator(ProtoVisitorDecorator[T_co]):
    def __init__(self, *nested: ProtoVisitor[T_co]) -> None:
        self.__nested = nested

    def enter_file_descriptor_proto(self, context: FileDescriptorContext[T_co]) -> T_co:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_file_descriptor_proto(replace(context, meta=meta))

        return meta

    def leave_file_descriptor_proto(self, context: FileDescriptorContext[T_co]) -> T_co:
        return context.meta

    def enter_enum_descriptor_proto(self, context: EnumDescriptorContext[T_co]) -> T_co:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_enum_descriptor_proto(replace(context, meta=meta))

        return meta

    def leave_enum_descriptor_proto(self, context: EnumDescriptorContext[T_co]) -> T_co:
        return context.meta

    def enter_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T_co]) -> T_co:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_enum_value_descriptor_proto(replace(context, meta=meta))

        return meta

    def leave_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T_co]) -> T_co:
        return context.meta

    def enter_descriptor_proto(self, context: DescriptorContext[T_co]) -> T_co:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_descriptor_proto(replace(context, meta=meta))

        return meta

    def leave_descriptor_proto(self, context: DescriptorContext[T_co]) -> T_co:
        return context.meta

    def enter_oneof_descriptor_proto(self, context: OneofDescriptorContext[T_co]) -> T_co:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_oneof_descriptor_proto(replace(context, meta=meta))

        return meta

    def leave_oneof_descriptor_proto(self, context: OneofDescriptorContext[T_co]) -> T_co:
        return context.meta

    def enter_field_descriptor_proto(self, context: FieldDescriptorContext[T_co]) -> T_co:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_field_descriptor_proto(replace(context, meta=meta))

        return meta

    def leave_field_descriptor_proto(self, context: FieldDescriptorContext[T_co]) -> T_co:
        return context.meta

    def enter_service_descriptor_proto(self, context: ServiceDescriptorContext[T_co]) -> T_co:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_service_descriptor_proto(replace(context, meta=meta))

        return meta

    def leave_service_descriptor_proto(self, context: ServiceDescriptorContext[T_co]) -> T_co:
        return context.meta

    def enter_method_descriptor_proto(self, context: MethodDescriptorContext[T_co]) -> T_co:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_method_descriptor_proto(replace(context, meta=meta))

        return meta

    def leave_method_descriptor_proto(self, context: MethodDescriptorContext[T_co]) -> T_co:
        return context.meta


class LeaveProtoVisitorDecorator(ProtoVisitorDecorator[T_co]):
    def __init__(self, *nested: ProtoVisitor[T_co]) -> None:
        self.__nested = nested

    def enter_file_descriptor_proto(self, context: FileDescriptorContext[T_co]) -> T_co:
        return context.meta

    def leave_file_descriptor_proto(self, context: FileDescriptorContext[T_co]) -> T_co:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_file_descriptor_proto(replace(context, meta=meta))

        return meta

    def enter_enum_descriptor_proto(self, context: EnumDescriptorContext[T_co]) -> T_co:
        return context.meta

    def leave_enum_descriptor_proto(self, context: EnumDescriptorContext[T_co]) -> T_co:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_enum_descriptor_proto(replace(context, meta=meta))

        return meta

    def enter_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T_co]) -> T_co:
        return context.meta

    def leave_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T_co]) -> T_co:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_enum_value_descriptor_proto(replace(context, meta=meta))

        return meta

    def enter_descriptor_proto(self, context: DescriptorContext[T_co]) -> T_co:
        return context.meta

    def leave_descriptor_proto(self, context: DescriptorContext[T_co]) -> T_co:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_descriptor_proto(replace(context, meta=meta))

        return meta

    def enter_oneof_descriptor_proto(self, context: OneofDescriptorContext[T_co]) -> T_co:
        return context.meta

    def leave_oneof_descriptor_proto(self, context: OneofDescriptorContext[T_co]) -> T_co:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_oneof_descriptor_proto(replace(context, meta=meta))

        return meta

    def enter_field_descriptor_proto(self, context: FieldDescriptorContext[T_co]) -> T_co:
        return context.meta

    def leave_field_descriptor_proto(self, context: FieldDescriptorContext[T_co]) -> T_co:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_field_descriptor_proto(replace(context, meta=meta))

        return meta

    def enter_service_descriptor_proto(self, context: ServiceDescriptorContext[T_co]) -> T_co:
        return context.meta

    def leave_service_descriptor_proto(self, context: ServiceDescriptorContext[T_co]) -> T_co:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_service_descriptor_proto(replace(context, meta=meta))

        return meta

    def enter_method_descriptor_proto(self, context: MethodDescriptorContext[T_co]) -> T_co:
        return context.meta

    def leave_method_descriptor_proto(self, context: MethodDescriptorContext[T_co]) -> T_co:
        meta = context.meta

        for nested in self.__nested:
            meta = nested.visit_method_descriptor_proto(replace(context, meta=meta))

        return meta
