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

from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.visitor.abc import ProtoVisitor
from pyprotostuben.protobuf.visitor.decorator import ProtoVisitorDecorator


class DFSWalkingProtoVisitor(ProtoVisitor, LoggerMixin):
    def __init__(self, *nested: ProtoVisitorDecorator) -> None:
        self.__nested = nested

    def visit_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_file_descriptor_proto(proto)

        for enum_type in proto.enum_type:
            self.visit_enum_descriptor_proto(enum_type)
        for message_type in proto.message_type:
            self.visit_descriptor_proto(message_type)
        for service in proto.service:
            self.visit_service_descriptor_proto(service)
        for ext in proto.extension:
            self.visit_field_descriptor_proto(ext)

        for nested in reversed(self.__nested):
            nested.leave_file_descriptor_proto(proto)

        log.info("visited")

    def visit_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_enum_descriptor_proto(proto)

        for value in proto.value:
            self.visit_enum_value_descriptor_proto(value)

        for nested in reversed(self.__nested):
            nested.leave_enum_descriptor_proto(proto)

        log.info("visited")

    def visit_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_enum_value_descriptor_proto(proto)

        for nested in reversed(self.__nested):
            nested.leave_enum_value_descriptor_proto(proto)

        log.info("visited")

    def visit_descriptor_proto(self, proto: DescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_descriptor_proto(proto)

        for enum_type in proto.enum_type:
            self.visit_enum_descriptor_proto(enum_type)
        for nested_type in proto.nested_type:
            self.visit_descriptor_proto(nested_type)
        for oneof in proto.oneof_decl:
            self.visit_oneof_descriptor_proto(oneof)
        for field in proto.field:
            self.visit_field_descriptor_proto(field)
        for ext in proto.extension:
            self.visit_field_descriptor_proto(ext)

        for nested in reversed(self.__nested):
            nested.leave_descriptor_proto(proto)

        log.info("visited")

    def visit_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_oneof_descriptor_proto(proto)

        for nested in reversed(self.__nested):
            nested.leave_oneof_descriptor_proto(proto)

        log.info("visited")

    def visit_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_field_descriptor_proto(proto)

        for nested in reversed(self.__nested):
            nested.leave_field_descriptor_proto(proto)

        log.info("visited")

    def visit_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_service_descriptor_proto(proto)

        for method in proto.method:
            self.visit_method_descriptor_proto(method)

        for nested in reversed(self.__nested):
            nested.leave_service_descriptor_proto(proto)

        log.info("visited")

    def visit_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_method_descriptor_proto(proto)

        for nested in reversed(self.__nested):
            nested.leave_method_descriptor_proto(proto)

        log.info("visited")
