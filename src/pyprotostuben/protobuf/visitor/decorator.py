import typing as t

from pyprotostuben.protobuf.visitor.abc import ProtoVisitor, ProtoVisitorDecorator
from pyprotostuben.protobuf.visitor.model import (
    DescriptorContext,
    EnumContext,
    EnumValueContext,
    ExtensionContext,
    FieldContext,
    FileContext,
    MethodContext,
    OneofContext,
    ServiceContext,
)

T_contra = t.TypeVar("T_contra", contravariant=True)


class EnterProtoVisitorDecorator(ProtoVisitorDecorator[T_contra]):
    def __init__(self, *nested: ProtoVisitor[T_contra]) -> None:
        self.__nested = nested

    def enter_file(self, context: FileContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_file(context)

    def leave_file(self, context: FileContext[T_contra]) -> None:
        pass

    def enter_enum(self, context: EnumContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_enum(context)

    def leave_enum(self, context: EnumContext[T_contra]) -> None:
        pass

    def enter_enum_value(self, context: EnumValueContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_enum_value(context)

    def leave_enum_value(self, context: EnumValueContext[T_contra]) -> None:
        pass

    def enter_descriptor(self, context: DescriptorContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_descriptor(context)

    def leave_descriptor(self, context: DescriptorContext[T_contra]) -> None:
        pass

    def enter_oneof(self, context: OneofContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_oneof(context)

    def leave_oneof(self, context: OneofContext[T_contra]) -> None:
        pass

    def enter_field(self, context: FieldContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_field(context)

    def leave_field(self, context: FieldContext[T_contra]) -> None:
        pass

    def enter_service(self, context: ServiceContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_service(context)

    def leave_service(self, context: ServiceContext[T_contra]) -> None:
        pass

    def enter_method(self, context: MethodContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_method(context)

    def leave_method(self, context: MethodContext[T_contra]) -> None:
        pass

    def enter_extension(self, context: ExtensionContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_extension(context)

    def leave_extension(self, context: ExtensionContext[T_contra]) -> None:
        pass


class LeaveProtoVisitorDecorator(ProtoVisitorDecorator[T_contra]):
    def __init__(self, *nested: ProtoVisitor[T_contra]) -> None:
        self.__nested = nested

    def enter_file(self, context: FileContext[T_contra]) -> None:
        pass

    def leave_file(self, context: FileContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_file(context)

    def enter_enum(self, context: EnumContext[T_contra]) -> None:
        pass

    def leave_enum(self, context: EnumContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_enum(context)

    def enter_enum_value(self, context: EnumValueContext[T_contra]) -> None:
        pass

    def leave_enum_value(self, context: EnumValueContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_enum_value(context)

    def enter_descriptor(self, context: DescriptorContext[T_contra]) -> None:
        pass

    def leave_descriptor(self, context: DescriptorContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_descriptor(context)

    def enter_oneof(self, context: OneofContext[T_contra]) -> None:
        pass

    def leave_oneof(self, context: OneofContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_oneof(context)

    def enter_field(self, context: FieldContext[T_contra]) -> None:
        pass

    def leave_field(self, context: FieldContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_field(context)

    def enter_service(self, context: ServiceContext[T_contra]) -> None:
        pass

    def leave_service(self, context: ServiceContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_service(context)

    def enter_method(self, context: MethodContext[T_contra]) -> None:
        pass

    def leave_method(self, context: MethodContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_method(context)

    def enter_extension(self, context: ExtensionContext[T_contra]) -> None:
        pass

    def leave_extension(self, context: ExtensionContext[T_contra]) -> None:
        for nested in self.__nested:
            nested.visit_extension(context)
