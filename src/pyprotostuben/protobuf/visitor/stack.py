from google.protobuf.descriptor_pb2 import (
    MethodDescriptorProto,
    ServiceDescriptorProto,
    FieldDescriptorProto,
    OneofDescriptorProto,
    DescriptorProto,
    EnumValueDescriptorProto,
    EnumDescriptorProto,
    FileDescriptorProto,
)

from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.visitor.abc import Proto
from pyprotostuben.protobuf.visitor.decorator import ProtoVisitorDecorator
from pyprotostuben.stack import MutableStack


class ProtoStackVisitorDecorator(ProtoVisitorDecorator):
    """Puts proto into stack on enter and pops it on leave."""

    def __init__(self, stack: MutableStack[Proto]) -> None:
        self.__stack = stack

    def enter_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        self.__stack.put(proto)

    def leave_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        self.__stack.pop()

    def enter_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        self.__stack.put(proto)

    def leave_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        self.__stack.pop()

    def enter_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        self.__stack.put(proto)

    def leave_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        self.__stack.pop()

    def enter_descriptor_proto(self, proto: DescriptorProto) -> None:
        self.__stack.put(proto)

    def leave_descriptor_proto(self, proto: DescriptorProto) -> None:
        self.__stack.pop()

    def enter_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        self.__stack.put(proto)

    def leave_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        self.__stack.pop()

    def enter_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        self.__stack.put(proto)

    def leave_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        self.__stack.pop()

    def enter_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        self.__stack.put(proto)

    def leave_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        self.__stack.pop()

    def enter_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        self.__stack.put(proto)

    def leave_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        self.__stack.pop()


class ProtoFileStackVisitorDecorator(ProtoVisitorDecorator):
    def __init__(self, stack: MutableStack[ProtoFile]) -> None:
        self.__stack = stack

    def enter_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        self.__stack.put(ProtoFile(proto))

    def leave_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        self.__stack.pop()

    def enter_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        pass

    def leave_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        pass

    def enter_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        pass

    def leave_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        pass

    def enter_descriptor_proto(self, proto: DescriptorProto) -> None:
        pass

    def leave_descriptor_proto(self, proto: DescriptorProto) -> None:
        pass

    def enter_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        pass

    def leave_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        pass

    def enter_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        pass

    def leave_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        pass

    def enter_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        pass

    def leave_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        pass

    def enter_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        pass

    def leave_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        pass
