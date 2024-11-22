import typing as t

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

T_contra = t.TypeVar("T_contra", contravariant=True)


class Walker(ProtoVisitor[T_contra], LoggerMixin):
    def __init__(self, *nested: ProtoVisitorDecorator[T_contra]) -> None:
        self.__nested = nested

    def visit_file_descriptor_proto(self, context: FileDescriptorContext[T_contra]) -> None:
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

    def visit_enum_descriptor_proto(self, context: EnumDescriptorContext[T_contra]) -> None:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_enum_descriptor_proto(context)

        self.__walk_enum_values(context)

        for nested in reversed(self.__nested):
            nested.leave_enum_descriptor_proto(context)

        log.info("visited")

    def visit_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T_contra]) -> None:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_enum_value_descriptor_proto(context)

        for nested in reversed(self.__nested):
            nested.leave_enum_value_descriptor_proto(context)

        log.info("visited")

    def visit_descriptor_proto(self, context: DescriptorContext[T_contra]) -> None:
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

    def visit_oneof_descriptor_proto(self, context: OneofDescriptorContext[T_contra]) -> None:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_oneof_descriptor_proto(context)

        for nested in reversed(self.__nested):
            nested.leave_oneof_descriptor_proto(context)

        log.info("visited")

    def visit_field_descriptor_proto(self, context: FieldDescriptorContext[T_contra]) -> None:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_field_descriptor_proto(context)

        for nested in reversed(self.__nested):
            nested.leave_field_descriptor_proto(context)

        log.info("visited")

    def visit_service_descriptor_proto(self, context: ServiceDescriptorContext[T_contra]) -> None:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_service_descriptor_proto(context)

        self.__walk_methods(context)

        for nested in reversed(self.__nested):
            nested.leave_service_descriptor_proto(context)

        log.info("visited")

    def visit_method_descriptor_proto(self, context: MethodDescriptorContext[T_contra]) -> None:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_method_descriptor_proto(context)

        for nested in reversed(self.__nested):
            nested.leave_method_descriptor_proto(context)

        log.info("visited")

    def walk(self, meta: T_contra, *files: FileDescriptorProto) -> None:
        for file in files:
            self.visit_file_descriptor_proto(
                FileDescriptorContext(
                    meta=meta,
                    item=file,
                    path=[],
                )
            )

    def __walk_enums(self, context: BaseContext[T_contra, t.Union[FileDescriptorProto, DescriptorProto]]) -> None:
        for i, enum_type in enumerate(context.item.enum_type):
            self.visit_enum_descriptor_proto(
                EnumDescriptorContext(
                    meta=context.meta,
                    parent_context=context,
                    item=enum_type,
                    path=(*context.path, context.item.ENUM_TYPE_FIELD_NUMBER, i),
                )
            )

    def __walk_enum_values(self, context: BaseContext[T_contra, EnumDescriptorProto]) -> None:
        for i, value in enumerate(context.item.value):
            self.visit_enum_value_descriptor_proto(
                EnumValueDescriptorContext(
                    meta=context.meta,
                    parent_context=context,
                    item=value,
                    path=(*context.path, context.item.VALUE_FIELD_NUMBER, i),
                )
            )

    def __walk_message_types(self, context: BaseContext[T_contra, FileDescriptorProto]) -> None:
        for i, message_type in enumerate(context.item.message_type):
            self.visit_descriptor_proto(
                DescriptorContext(
                    meta=context.meta,
                    parent_context=context,
                    item=message_type,
                    path=(*context.path, context.item.MESSAGE_TYPE_FIELD_NUMBER, i),
                )
            )

    def __walk_nested_types(self, context: BaseContext[T_contra, DescriptorProto]) -> None:
        for i, nested_type in enumerate(context.item.nested_type):
            self.visit_descriptor_proto(
                DescriptorContext(
                    meta=context.meta,
                    parent_context=context,
                    item=nested_type,
                    path=(*context.path, context.item.NESTED_TYPE_FIELD_NUMBER, i),
                )
            )

    def __walk_oneofs(self, context: BaseContext[T_contra, DescriptorProto]) -> None:
        for i, oneof in enumerate(context.item.oneof_decl):
            self.visit_oneof_descriptor_proto(
                OneofDescriptorContext(
                    meta=context.meta,
                    parent_context=context,
                    item=oneof,
                    path=(*context.path, context.item.ONEOF_DECL_FIELD_NUMBER, i),
                )
            )

    def __walk_fields(self, context: BaseContext[T_contra, DescriptorProto]) -> None:
        for i, field in enumerate(context.item.field):
            self.visit_field_descriptor_proto(
                FieldDescriptorContext(
                    meta=context.meta,
                    parent_context=context,
                    item=field,
                    path=(*context.path, context.item.FIELD_FIELD_NUMBER, i),
                )
            )

    def __walk_services(self, context: BaseContext[T_contra, FileDescriptorProto]) -> None:
        for i, service in enumerate(context.item.service):
            self.visit_service_descriptor_proto(
                ServiceDescriptorContext(
                    meta=context.meta,
                    parent_context=context,
                    item=service,
                    path=(*context.path, context.item.SERVICE_FIELD_NUMBER, i),
                )
            )

    def __walk_methods(self, context: BaseContext[T_contra, ServiceDescriptorProto]) -> None:
        for i, method in enumerate(context.item.method):
            self.visit_method_descriptor_proto(
                MethodDescriptorContext(
                    meta=context.meta,
                    parent_context=context,
                    item=method,
                    path=(*context.path, context.item.METHOD_FIELD_NUMBER, i),
                )
            )

    def __walk_extensions(self, context: BaseContext[T_contra, t.Union[FileDescriptorProto, DescriptorProto]]) -> None:
        for i, ext in enumerate(context.item.extension):
            self.visit_field_descriptor_proto(
                FieldDescriptorContext(
                    meta=context.meta,
                    parent_context=context,
                    item=ext,
                    path=(*context.path, context.item.EXTENSION_FIELD_NUMBER, i),
                )
            )
