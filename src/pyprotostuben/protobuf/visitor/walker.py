from google.protobuf.descriptor_pb2 import (
    DescriptorProto,
    EnumDescriptorProto,
    FileDescriptorProto,
    ServiceDescriptorProto,
)

from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.visitor.abc import ProtoVisitor
from pyprotostuben.protobuf.visitor.decorator import ProtoVisitorDecorator
from pyprotostuben.protobuf.visitor.model import (
    BaseContext,
    DescriptorContext,
    EnumDescriptorContext,
    EnumValueDescriptorContext,
    FieldDescriptorContext,
    FileDescriptorContext,
    MethodDescriptorContext,
    OneofDescriptorContext,
    ServiceDescriptorContext,
)


class Walker(ProtoVisitor, LoggerMixin):
    def __init__(self, *nested: ProtoVisitorDecorator) -> None:
        self.__nested = nested

    def visit_file_descriptor_proto(self, context: FileDescriptorContext) -> None:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_file_descriptor_proto(context)

        self.__walk_enums(context)
        self.__walk_message_types(context)
        self.__walk_services(context)
        self.__walk_extensions(context)

        for nested in reversed(self.__nested):
            nested.leave_file_descriptor_proto(context)

        log.info("visited")

    def visit_enum_descriptor_proto(self, context: EnumDescriptorContext) -> None:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_enum_descriptor_proto(context)

        self.__walk_enum_values(context)

        for nested in reversed(self.__nested):
            nested.leave_enum_descriptor_proto(context)

        log.info("visited")

    def visit_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext) -> None:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_enum_value_descriptor_proto(context)

        for nested in reversed(self.__nested):
            nested.leave_enum_value_descriptor_proto(context)

        log.info("visited")

    def visit_descriptor_proto(self, context: DescriptorContext) -> None:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_descriptor_proto(context)

        self.__walk_enums(context)
        self.__walk_nested_types(context)
        self.__walk_oneofs(context)
        self.__walk_fields(context)
        self.__walk_extensions(context)

        for nested in reversed(self.__nested):
            nested.leave_descriptor_proto(context)

        log.info("visited")

    def visit_oneof_descriptor_proto(self, context: OneofDescriptorContext) -> None:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_oneof_descriptor_proto(context)

        for nested in reversed(self.__nested):
            nested.leave_oneof_descriptor_proto(context)

        log.info("visited")

    def visit_field_descriptor_proto(self, context: FieldDescriptorContext) -> None:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_field_descriptor_proto(context)

        for nested in reversed(self.__nested):
            nested.leave_field_descriptor_proto(context)

        log.info("visited")

    def visit_service_descriptor_proto(self, context: ServiceDescriptorContext) -> None:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_service_descriptor_proto(context)

        self.__walk_methods(context)

        for nested in reversed(self.__nested):
            nested.leave_service_descriptor_proto(context)

        log.info("visited")

    def visit_method_descriptor_proto(self, context: MethodDescriptorContext) -> None:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_method_descriptor_proto(context)

        for nested in reversed(self.__nested):
            nested.leave_method_descriptor_proto(context)

        log.info("visited")

    def walk(self, *files: FileDescriptorProto) -> None:
        for file in files:
            context = FileDescriptorContext(
                item=file,
                path=[],
            )
            self.visit_file_descriptor_proto(context)

    def __walk_enums(self, context: BaseContext[FileDescriptorProto | DescriptorProto]) -> None:
        for i, enum_type in enumerate(context.item.enum_type):
            self.visit_enum_descriptor_proto(
                EnumDescriptorContext(
                    parent_context=context,
                    item=enum_type,
                    path=(*context.path, context.item.ENUM_TYPE_FIELD_NUMBER, i),
                )
            )

    def __walk_enum_values(self, context: BaseContext[EnumDescriptorProto]) -> None:
        for i, value in enumerate(context.item.value):
            self.visit_enum_value_descriptor_proto(
                EnumValueDescriptorContext(
                    parent_context=context,
                    item=value,
                    path=(*context.path, context.item.VALUE_FIELD_NUMBER, i),
                )
            )

    def __walk_message_types(self, context: BaseContext[FileDescriptorProto]) -> None:
        for i, message_type in enumerate(context.item.message_type):
            self.visit_descriptor_proto(
                DescriptorContext(
                    parent_context=context,
                    item=message_type,
                    path=(*context.path, context.item.MESSAGE_TYPE_FIELD_NUMBER, i),
                )
            )

    def __walk_nested_types(self, context: BaseContext[DescriptorProto]) -> None:
        for i, nested_type in enumerate(context.item.nested_type):
            self.visit_descriptor_proto(
                DescriptorContext(
                    parent_context=context,
                    item=nested_type,
                    path=(*context.path, context.item.NESTED_TYPE_FIELD_NUMBER, i),
                )
            )

    def __walk_oneofs(self, context: BaseContext[DescriptorProto]) -> None:
        for i, oneof in enumerate(context.item.oneof_decl):
            self.visit_oneof_descriptor_proto(
                OneofDescriptorContext(
                    parent_context=context,
                    item=oneof,
                    path=(*context.path, context.item.ONEOF_DECL_FIELD_NUMBER, i),
                )
            )

    def __walk_fields(self, context: BaseContext[DescriptorProto]) -> None:
        for i, field in enumerate(context.item.field):
            self.visit_field_descriptor_proto(
                FieldDescriptorContext(
                    parent_context=context,
                    item=field,
                    path=(*context.path, context.item.FIELD_FIELD_NUMBER, i),
                )
            )

    def __walk_services(self, context: BaseContext[FileDescriptorProto]) -> None:
        for i, service in enumerate(context.item.service):
            self.visit_service_descriptor_proto(
                ServiceDescriptorContext(
                    parent_context=context,
                    item=service,
                    path=(*context.path, context.item.SERVICE_FIELD_NUMBER, i),
                )
            )

    def __walk_methods(self, context: BaseContext[ServiceDescriptorProto]) -> None:
        for i, method in enumerate(context.item.method):
            self.visit_method_descriptor_proto(
                MethodDescriptorContext(
                    parent_context=context,
                    item=method,
                    path=(*context.path, context.item.METHOD_FIELD_NUMBER, i),
                )
            )

    def __walk_extensions(self, context: BaseContext[FileDescriptorProto | DescriptorProto]) -> None:
        for i, ext in enumerate(context.item.extension):
            self.visit_field_descriptor_proto(
                FieldDescriptorContext(
                    parent_context=context,
                    item=ext,
                    path=(*context.path, context.item.EXTENSION_FIELD_NUMBER, i),
                )
            )
