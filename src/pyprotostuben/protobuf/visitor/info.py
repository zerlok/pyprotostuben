import typing as t

from google.protobuf.descriptor_pb2 import (
    FileDescriptorProto,
    EnumDescriptorProto,
    EnumValueDescriptorProto,
    DescriptorProto,
    OneofDescriptorProto,
    FieldDescriptorProto,
    ServiceDescriptorProto,
    MethodDescriptorProto,
)

from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.visitor.decorator import ProtoVisitorDecorator
from pyprotostuben.python.info import TypeInfo, ModuleInfo, NamespaceInfo
from pyprotostuben.stack import MutableStack


class NamespaceInfoVisitorDecorator(ProtoVisitorDecorator, LoggerMixin):
    def __init__(self, stack: MutableStack[NamespaceInfo]) -> None:
        self.__stack = stack

    def enter_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)

        file = ProtoFile(proto)
        self.__stack.put(ModuleInfo(file.pb2_package, file.proto_path.stem))

        log.info("entered")

    def leave_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)

        self.__stack.pop()

        log.info("left")

    def enter_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)

        self.__stack.put(TypeInfo(self.__get_type_parent(), proto.name))

        log.info("entered")

    def leave_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)

        self.__stack.pop()

        log.info("left")

    def enter_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)

        log.info("entered")

    def leave_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)

        log.info("left")

    def enter_descriptor_proto(self, proto: DescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)

        self.__stack.put(TypeInfo(self.__get_type_parent(), proto.name))

        log.info("entered")

    def leave_descriptor_proto(self, proto: DescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)

        self.__stack.pop()

        log.info("left")

    def enter_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)

        log.info("entered")

    def leave_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)

        log.info("left")

    def enter_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)

        log.info("entered")

    def leave_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)

        log.info("left")

    def enter_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)

        self.__stack.put(TypeInfo(self.__get_type_parent(), proto.name))

        log.info("entered")

    def leave_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)

        self.__stack.pop()

        log.info("left")

    def enter_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)

        log.info("entered")

    def leave_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)

        log.info("left")

    def __get_type_parent(self) -> t.Union[ModuleInfo, TypeInfo]:
        parent = self.__stack.get_last()
        if not isinstance(parent, (ModuleInfo, TypeInfo)):
            raise ValueError("invalid type parent", parent)

        return parent
