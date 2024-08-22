import abc

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

from pyprotostuben.protobuf.visitor.abc import ProtoVisitor


class ProtoVisitorDecorator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def enter_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_descriptor_proto(self, proto: DescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_descriptor_proto(self, proto: DescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        raise NotImplementedError


class EnterProtoVisitorDecorator(ProtoVisitorDecorator):
    def __init__(self, *nested: ProtoVisitor) -> None:
        self.__nested = nested

    def enter_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        for nested in self.__nested:
            nested.visit_file_descriptor_proto(proto)

    def leave_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        pass

    def enter_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        for nested in self.__nested:
            nested.visit_enum_descriptor_proto(proto)

    def leave_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        pass

    def enter_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        for nested in self.__nested:
            nested.visit_enum_value_descriptor_proto(proto)

    def leave_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        pass

    def enter_descriptor_proto(self, proto: DescriptorProto) -> None:
        for nested in self.__nested:
            nested.visit_descriptor_proto(proto)

    def leave_descriptor_proto(self, proto: DescriptorProto) -> None:
        pass

    def enter_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        for nested in self.__nested:
            nested.visit_oneof_descriptor_proto(proto)

    def leave_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        pass

    def enter_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        for nested in self.__nested:
            nested.visit_field_descriptor_proto(proto)

    def leave_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        pass

    def enter_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        for nested in self.__nested:
            nested.visit_service_descriptor_proto(proto)

    def leave_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        pass

    def enter_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        for nested in self.__nested:
            nested.visit_method_descriptor_proto(proto)

    def leave_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        pass


class LeaveProtoVisitorDecorator(ProtoVisitorDecorator):
    def __init__(self, *nested: ProtoVisitor) -> None:
        self.__nested = nested

    def enter_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        pass

    def leave_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        for nested in self.__nested:
            nested.visit_file_descriptor_proto(proto)

    def enter_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        pass

    def leave_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        for nested in self.__nested:
            nested.visit_enum_descriptor_proto(proto)

    def enter_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        pass

    def leave_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        for nested in self.__nested:
            nested.visit_enum_value_descriptor_proto(proto)

    def enter_descriptor_proto(self, proto: DescriptorProto) -> None:
        pass

    def leave_descriptor_proto(self, proto: DescriptorProto) -> None:
        for nested in self.__nested:
            nested.visit_descriptor_proto(proto)

    def enter_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        pass

    def leave_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        for nested in self.__nested:
            nested.visit_oneof_descriptor_proto(proto)

    def enter_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        pass

    def leave_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        for nested in self.__nested:
            nested.visit_field_descriptor_proto(proto)

    def enter_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        pass

    def leave_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        for nested in self.__nested:
            nested.visit_service_descriptor_proto(proto)

    def enter_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        pass

    def leave_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        for nested in self.__nested:
            nested.visit_method_descriptor_proto(proto)
