import typing as t
from dataclasses import replace

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

T = t.TypeVar("T")


class Walker(ProtoVisitor[T], LoggerMixin):
    def __init__(self, *nested: ProtoVisitorDecorator[T]) -> None:
        self.__nested = nested

    def visit_file_descriptor_proto(self, context: FileDescriptorContext[T]) -> T:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        meta = context.meta

        for nested in self.__nested:
            meta = nested.enter_file_descriptor_proto(replace(context, meta=meta))

        meta = self.__walk_enums(replace(context, meta=meta))
        meta = self.__walk_message_types(replace(context, meta=meta))
        meta = self.__walk_services(replace(context, meta=meta))
        meta = self.__walk_extensions(replace(context, meta=meta))

        for nested in reversed(self.__nested):
            meta = nested.leave_file_descriptor_proto(replace(context, meta=meta))

        log.info("visited")

        return meta

    def visit_enum_descriptor_proto(self, context: EnumDescriptorContext[T]) -> T:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        meta = context.meta

        for nested in self.__nested:
            meta = nested.enter_enum_descriptor_proto(replace(context, meta=meta))

        meta = self.__walk_enum_values(replace(context, meta=meta))

        for nested in reversed(self.__nested):
            meta = nested.leave_enum_descriptor_proto(replace(context, meta=meta))

        log.info("visited")

        return meta

    def visit_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T]) -> T:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        meta = context.meta

        for nested in self.__nested:
            meta = nested.enter_enum_value_descriptor_proto(replace(context, meta=meta))

        for nested in reversed(self.__nested):
            meta = nested.leave_enum_value_descriptor_proto(replace(context, meta=meta))

        log.info("visited")

        return meta

    def visit_descriptor_proto(self, context: DescriptorContext[T]) -> T:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        meta = context.meta

        for nested in self.__nested:
            meta = nested.enter_descriptor_proto(replace(context, meta=meta))

        meta = self.__walk_enums(replace(context, meta=meta))
        meta = self.__walk_nested_types(replace(context, meta=meta))
        meta = self.__walk_oneofs(replace(context, meta=meta))
        meta = self.__walk_fields(replace(context, meta=meta))
        meta = self.__walk_extensions(replace(context, meta=meta))

        for nested in reversed(self.__nested):
            meta = nested.leave_descriptor_proto(replace(context, meta=meta))

        log.info("visited")

        return meta

    def visit_oneof_descriptor_proto(self, context: OneofDescriptorContext[T]) -> T:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        meta = context.meta

        for nested in self.__nested:
            meta = nested.enter_oneof_descriptor_proto(replace(context, meta=meta))

        for nested in reversed(self.__nested):
            meta = nested.leave_oneof_descriptor_proto(replace(context, meta=meta))

        log.info("visited")

        return meta

    def visit_field_descriptor_proto(self, context: FieldDescriptorContext[T]) -> T:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        meta = context.meta

        for nested in self.__nested:
            meta = nested.enter_field_descriptor_proto(replace(context, meta=meta))

        for nested in reversed(self.__nested):
            meta = nested.leave_field_descriptor_proto(replace(context, meta=meta))

        log.info("visited")

        return meta

    def visit_service_descriptor_proto(self, context: ServiceDescriptorContext[T]) -> T:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        meta = context.meta

        for nested in self.__nested:
            meta = nested.enter_service_descriptor_proto(replace(context, meta=meta))

        meta = self.__walk_methods(replace(context, meta=meta))

        for nested in reversed(self.__nested):
            meta = nested.leave_service_descriptor_proto(replace(context, meta=meta))

        log.info("visited")

        return meta

    def visit_method_descriptor_proto(self, context: MethodDescriptorContext[T]) -> T:
        proto = context.item

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        meta = context.meta

        for nested in self.__nested:
            meta = nested.enter_method_descriptor_proto(replace(context, meta=meta))

        for nested in reversed(self.__nested):
            meta = nested.leave_method_descriptor_proto(replace(context, meta=meta))

        log.info("visited")

        return meta

    def walk(self, meta: T, *files: FileDescriptorProto) -> T:
        for file in files:
            meta = self.visit_file_descriptor_proto(
                FileDescriptorContext(
                    meta=meta,
                    item=file,
                    path=[],
                )
            )

        return meta

    def __walk_enums(self, context: BaseContext[T, FileDescriptorProto | DescriptorProto]) -> T:
        meta = context.meta

        for i, enum_type in enumerate(context.item.enum_type):
            meta = self.visit_enum_descriptor_proto(
                EnumDescriptorContext(
                    meta=meta,
                    parent_context=context,
                    item=enum_type,
                    path=(*context.path, context.item.ENUM_TYPE_FIELD_NUMBER, i),
                )
            )

        return meta

    def __walk_enum_values(self, context: BaseContext[T, EnumDescriptorProto]) -> T:
        meta = context.meta

        for i, value in enumerate(context.item.value):
            meta = self.visit_enum_value_descriptor_proto(
                EnumValueDescriptorContext(
                    meta=meta,
                    parent_context=context,
                    item=value,
                    path=(*context.path, context.item.VALUE_FIELD_NUMBER, i),
                )
            )

        return meta

    def __walk_message_types(self, context: BaseContext[T, FileDescriptorProto]) -> T:
        meta = context.meta

        for i, message_type in enumerate(context.item.message_type):
            meta = self.visit_descriptor_proto(
                DescriptorContext(
                    meta=meta,
                    parent_context=context,
                    item=message_type,
                    path=(*context.path, context.item.MESSAGE_TYPE_FIELD_NUMBER, i),
                )
            )

        return meta

    def __walk_nested_types(self, context: BaseContext[T, DescriptorProto]) -> T:
        meta = context.meta

        for i, nested_type in enumerate(context.item.nested_type):
            meta = self.visit_descriptor_proto(
                DescriptorContext(
                    meta=meta,
                    parent_context=context,
                    item=nested_type,
                    path=(*context.path, context.item.NESTED_TYPE_FIELD_NUMBER, i),
                )
            )

        return meta

    def __walk_oneofs(self, context: BaseContext[T, DescriptorProto]) -> T:
        meta = context.meta

        for i, oneof in enumerate(context.item.oneof_decl):
            meta = self.visit_oneof_descriptor_proto(
                OneofDescriptorContext(
                    meta=meta,
                    parent_context=context,
                    item=oneof,
                    path=(*context.path, context.item.ONEOF_DECL_FIELD_NUMBER, i),
                )
            )

        return meta

    def __walk_fields(self, context: BaseContext[T, DescriptorProto]) -> T:
        meta = context.meta

        for i, field in enumerate(context.item.field):
            meta = self.visit_field_descriptor_proto(
                FieldDescriptorContext(
                    meta=meta,
                    parent_context=context,
                    item=field,
                    path=(*context.path, context.item.FIELD_FIELD_NUMBER, i),
                )
            )

        return meta

    def __walk_services(self, context: BaseContext[T, FileDescriptorProto]) -> T:
        meta = context.meta

        for i, service in enumerate(context.item.service):
            meta = self.visit_service_descriptor_proto(
                ServiceDescriptorContext(
                    meta=meta,
                    parent_context=context,
                    item=service,
                    path=(*context.path, context.item.SERVICE_FIELD_NUMBER, i),
                )
            )

        return meta

    def __walk_methods(self, context: BaseContext[T, ServiceDescriptorProto]) -> T:
        meta = context.meta

        for i, method in enumerate(context.item.method):
            meta = self.visit_method_descriptor_proto(
                MethodDescriptorContext(
                    meta=meta,
                    parent_context=context,
                    item=method,
                    path=(*context.path, context.item.METHOD_FIELD_NUMBER, i),
                )
            )

        return meta

    def __walk_extensions(self, context: BaseContext[T, FileDescriptorProto | DescriptorProto]) -> T:
        meta = context.meta

        for i, ext in enumerate(context.item.extension):
            meta = self.visit_field_descriptor_proto(
                FieldDescriptorContext(
                    meta=meta,
                    parent_context=context,
                    item=ext,
                    path=(*context.path, context.item.EXTENSION_FIELD_NUMBER, i),
                )
            )

        return meta
