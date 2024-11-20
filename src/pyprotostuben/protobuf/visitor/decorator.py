import abc

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


class ProtoVisitorDecorator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def enter_file_descriptor_proto(self, context: FileDescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_file_descriptor_proto(self, context: FileDescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_enum_descriptor_proto(self, context: EnumDescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_enum_descriptor_proto(self, context: EnumDescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_descriptor_proto(self, context: DescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_descriptor_proto(self, context: DescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_oneof_descriptor_proto(self, context: OneofDescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_oneof_descriptor_proto(self, context: OneofDescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_field_descriptor_proto(self, context: FieldDescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_field_descriptor_proto(self, context: FieldDescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_service_descriptor_proto(self, context: ServiceDescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_service_descriptor_proto(self, context: ServiceDescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_method_descriptor_proto(self, context: MethodDescriptorContext) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_method_descriptor_proto(self, context: MethodDescriptorContext) -> None:
        raise NotImplementedError


class EnterProtoVisitorDecorator(ProtoVisitorDecorator):
    def __init__(self, *nested: ProtoVisitor) -> None:
        self.__nested = nested

    def enter_file_descriptor_proto(self, context: FileDescriptorContext) -> None:
        for nested in self.__nested:
            nested.visit_file_descriptor_proto(context)

    def leave_file_descriptor_proto(self, context: FileDescriptorContext) -> None:
        pass

    def enter_enum_descriptor_proto(self, context: EnumDescriptorContext) -> None:
        for nested in self.__nested:
            nested.visit_enum_descriptor_proto(context)

    def leave_enum_descriptor_proto(self, context: EnumDescriptorContext) -> None:
        pass

    def enter_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext) -> None:
        for nested in self.__nested:
            nested.visit_enum_value_descriptor_proto(context)

    def leave_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext) -> None:
        pass

    def enter_descriptor_proto(self, context: DescriptorContext) -> None:
        for nested in self.__nested:
            nested.visit_descriptor_proto(context)

    def leave_descriptor_proto(self, context: DescriptorContext) -> None:
        pass

    def enter_oneof_descriptor_proto(self, context: OneofDescriptorContext) -> None:
        for nested in self.__nested:
            nested.visit_oneof_descriptor_proto(context)

    def leave_oneof_descriptor_proto(self, context: OneofDescriptorContext) -> None:
        pass

    def enter_field_descriptor_proto(self, context: FieldDescriptorContext) -> None:
        for nested in self.__nested:
            nested.visit_field_descriptor_proto(context)

    def leave_field_descriptor_proto(self, context: FieldDescriptorContext) -> None:
        pass

    def enter_service_descriptor_proto(self, context: ServiceDescriptorContext) -> None:
        for nested in self.__nested:
            nested.visit_service_descriptor_proto(context)

    def leave_service_descriptor_proto(self, context: ServiceDescriptorContext) -> None:
        pass

    def enter_method_descriptor_proto(self, context: MethodDescriptorContext) -> None:
        for nested in self.__nested:
            nested.visit_method_descriptor_proto(context)

    def leave_method_descriptor_proto(self, context: MethodDescriptorContext) -> None:
        pass


class LeaveProtoVisitorDecorator(ProtoVisitorDecorator):
    def __init__(self, *nested: ProtoVisitor) -> None:
        self.__nested = nested

    def enter_file_descriptor_proto(self, context: FileDescriptorContext) -> None:
        pass

    def leave_file_descriptor_proto(self, context: FileDescriptorContext) -> None:
        for nested in self.__nested:
            nested.visit_file_descriptor_proto(context)

    def enter_enum_descriptor_proto(self, context: EnumDescriptorContext) -> None:
        pass

    def leave_enum_descriptor_proto(self, context: EnumDescriptorContext) -> None:
        for nested in self.__nested:
            nested.visit_enum_descriptor_proto(context)

    def enter_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext) -> None:
        pass

    def leave_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext) -> None:
        for nested in self.__nested:
            nested.visit_enum_value_descriptor_proto(context)

    def enter_descriptor_proto(self, context: DescriptorContext) -> None:
        pass

    def leave_descriptor_proto(self, context: DescriptorContext) -> None:
        for nested in self.__nested:
            nested.visit_descriptor_proto(context)

    def enter_oneof_descriptor_proto(self, context: OneofDescriptorContext) -> None:
        pass

    def leave_oneof_descriptor_proto(self, context: OneofDescriptorContext) -> None:
        for nested in self.__nested:
            nested.visit_oneof_descriptor_proto(context)

    def enter_field_descriptor_proto(self, context: FieldDescriptorContext) -> None:
        pass

    def leave_field_descriptor_proto(self, context: FieldDescriptorContext) -> None:
        for nested in self.__nested:
            nested.visit_field_descriptor_proto(context)

    def enter_service_descriptor_proto(self, context: ServiceDescriptorContext) -> None:
        pass

    def leave_service_descriptor_proto(self, context: ServiceDescriptorContext) -> None:
        for nested in self.__nested:
            nested.visit_service_descriptor_proto(context)

    def enter_method_descriptor_proto(self, context: MethodDescriptorContext) -> None:
        pass

    def leave_method_descriptor_proto(self, context: MethodDescriptorContext) -> None:
        for nested in self.__nested:
            nested.visit_method_descriptor_proto(context)
