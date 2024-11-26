import typing as t

from google.protobuf.descriptor_pb2 import (
    FileDescriptorProto,
)

from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.visitor.abc import ProtoVisitor
from pyprotostuben.protobuf.visitor.decorator import ProtoVisitorDecorator
from pyprotostuben.protobuf.visitor.model import (
    DescriptorContext,
    EnumDescriptorContext,
    EnumValueDescriptorContext,
    ExtensionDescriptorContext,
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
        proto = context.proto

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
        proto = context.proto

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_enum_descriptor_proto(context)

        self.__walk_enum_values(context)

        for nested in reversed(self.__nested):
            nested.leave_enum_descriptor_proto(context)

        log.info("visited")

    def visit_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[T_contra]) -> None:
        proto = context.proto

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_enum_value_descriptor_proto(context)

        for nested in reversed(self.__nested):
            nested.leave_enum_value_descriptor_proto(context)

        log.info("visited")

    def visit_descriptor_proto(self, context: DescriptorContext[T_contra]) -> None:
        proto = context.proto

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
        proto = context.proto

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_oneof_descriptor_proto(context)

        for nested in reversed(self.__nested):
            nested.leave_oneof_descriptor_proto(context)

        log.info("visited")

    def visit_field_descriptor_proto(self, context: FieldDescriptorContext[T_contra]) -> None:
        proto = context.proto

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_field_descriptor_proto(context)

        for nested in reversed(self.__nested):
            nested.leave_field_descriptor_proto(context)

        log.info("visited")

    def visit_service_descriptor_proto(self, context: ServiceDescriptorContext[T_contra]) -> None:
        proto = context.proto

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_service_descriptor_proto(context)

        self.__walk_methods(context)

        for nested in reversed(self.__nested):
            nested.leave_service_descriptor_proto(context)

        log.info("visited")

    def visit_method_descriptor_proto(self, context: MethodDescriptorContext[T_contra]) -> None:
        proto = context.proto

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_method_descriptor_proto(context)

        for nested in reversed(self.__nested):
            nested.leave_method_descriptor_proto(context)

        log.info("visited")

    def visit_extension_descriptor_proto(self, context: ExtensionDescriptorContext[T_contra]) -> None:
        proto = context.proto

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_extension_descriptor_proto(context)

        for nested in reversed(self.__nested):
            nested.leave_extension_descriptor_proto(context)

        log.info("visited")

    def walk(self, *files: FileDescriptorProto, meta: t.Optional[T_contra] = None) -> None:
        for file in files:
            self.visit_file_descriptor_proto(
                FileDescriptorContext(
                    _meta=meta,
                    proto=file,
                    path=[],
                )
            )

    def __walk_enums(self, context: t.Union[FileDescriptorContext[T_contra], DescriptorContext[T_contra]]) -> None:
        for i, enum_type in enumerate(context.proto.enum_type):
            self.visit_enum_descriptor_proto(
                EnumDescriptorContext(
                    _meta=context.meta,
                    parent=context,
                    proto=enum_type,
                    path=(*context.path, context.proto.ENUM_TYPE_FIELD_NUMBER, i),
                )
            )

    def __walk_enum_values(self, context: EnumDescriptorContext[T_contra]) -> None:
        for i, value in enumerate(context.proto.value):
            self.visit_enum_value_descriptor_proto(
                EnumValueDescriptorContext(
                    _meta=context.meta,
                    parent=context,
                    proto=value,
                    path=(*context.path, context.proto.VALUE_FIELD_NUMBER, i),
                )
            )

    def __walk_message_types(self, context: FileDescriptorContext[T_contra]) -> None:
        for i, message_type in enumerate(context.proto.message_type):
            self.visit_descriptor_proto(
                DescriptorContext(
                    _meta=context.meta,
                    parent=context,
                    proto=message_type,
                    path=(*context.path, context.proto.MESSAGE_TYPE_FIELD_NUMBER, i),
                )
            )

    def __walk_nested_types(self, context: DescriptorContext[T_contra]) -> None:
        for i, nested_type in enumerate(context.proto.nested_type):
            self.visit_descriptor_proto(
                DescriptorContext(
                    _meta=context.meta,
                    parent=context,
                    proto=nested_type,
                    path=(*context.path, context.proto.NESTED_TYPE_FIELD_NUMBER, i),
                )
            )

    def __walk_oneofs(self, context: DescriptorContext[T_contra]) -> None:
        for i, oneof in enumerate(context.proto.oneof_decl):
            self.visit_oneof_descriptor_proto(
                OneofDescriptorContext(
                    _meta=context.meta,
                    parent=context,
                    proto=oneof,
                    path=(*context.path, context.proto.ONEOF_DECL_FIELD_NUMBER, i),
                )
            )

    def __walk_fields(self, context: DescriptorContext[T_contra]) -> None:
        for i, field in enumerate(context.proto.field):
            self.visit_field_descriptor_proto(
                FieldDescriptorContext(
                    _meta=context.meta,
                    parent=context,
                    proto=field,
                    path=(*context.path, context.proto.FIELD_FIELD_NUMBER, i),
                )
            )

    def __walk_services(self, context: FileDescriptorContext[T_contra]) -> None:
        for i, service in enumerate(context.proto.service):
            self.visit_service_descriptor_proto(
                ServiceDescriptorContext(
                    _meta=context.meta,
                    parent=context,
                    proto=service,
                    path=(*context.path, context.proto.SERVICE_FIELD_NUMBER, i),
                )
            )

    def __walk_methods(self, context: ServiceDescriptorContext[T_contra]) -> None:
        for i, method in enumerate(context.proto.method):
            self.visit_method_descriptor_proto(
                MethodDescriptorContext(
                    _meta=context.meta,
                    parent=context,
                    proto=method,
                    path=(*context.path, context.proto.METHOD_FIELD_NUMBER, i),
                )
            )

    def __walk_extensions(self, context: t.Union[FileDescriptorContext[T_contra], DescriptorContext[T_contra]]) -> None:
        for i, ext in enumerate(context.proto.extension):
            self.visit_extension_descriptor_proto(
                ExtensionDescriptorContext(
                    _meta=context.meta,
                    parent=context,
                    proto=ext,
                    path=(*context.path, context.proto.EXTENSION_FIELD_NUMBER, i),
                )
            )
