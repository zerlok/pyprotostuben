import typing as t

from google.protobuf.descriptor_pb2 import (
    FileDescriptorProto,
)

from pyprotostuben.logging import LoggerMixin
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


class Walker(ProtoVisitor[T_contra], LoggerMixin):
    def __init__(self, *nested: ProtoVisitorDecorator[T_contra]) -> None:
        self.__nested = nested

    def visit_file(self, context: FileContext[T_contra]) -> None:
        proto = context.proto

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_file(context)

        self.__walk_enums(context)
        self.__walk_message_types(context)
        self.__walk_services(context)
        self.__walk_extensions(context)

        for nested in reversed(self.__nested):
            nested.leave_file(context)

        log.info("visited")

    def visit_enum(self, context: EnumContext[T_contra]) -> None:
        proto = context.proto

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_enum(context)

        self.__walk_enum_values(context)

        for nested in reversed(self.__nested):
            nested.leave_enum(context)

        log.info("visited")

    def visit_enum_value(self, context: EnumValueContext[T_contra]) -> None:
        proto = context.proto

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_enum_value(context)

        for nested in reversed(self.__nested):
            nested.leave_enum_value(context)

        log.info("visited")

    def visit_descriptor(self, context: DescriptorContext[T_contra]) -> None:
        proto = context.proto

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_descriptor(context)

        self.__walk_enums(context)
        self.__walk_nested_types(context)
        self.__walk_oneofs(context)
        self.__walk_fields(context)
        self.__walk_extensions(context)

        for nested in reversed(self.__nested):
            nested.leave_descriptor(context)

        log.info("visited")

    def visit_oneof(self, context: OneofContext[T_contra]) -> None:
        proto = context.proto

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_oneof(context)

        for nested in reversed(self.__nested):
            nested.leave_oneof(context)

        log.info("visited")

    def visit_field(self, context: FieldContext[T_contra]) -> None:
        proto = context.proto

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_field(context)

        for nested in reversed(self.__nested):
            nested.leave_field(context)

        log.info("visited")

    def visit_service(self, context: ServiceContext[T_contra]) -> None:
        proto = context.proto

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_service(context)

        self.__walk_methods(context)

        for nested in reversed(self.__nested):
            nested.leave_service(context)

        log.info("visited")

    def visit_method(self, context: MethodContext[T_contra]) -> None:
        proto = context.proto

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_method(context)

        for nested in reversed(self.__nested):
            nested.leave_method(context)

        log.info("visited")

    def visit_extension(self, context: ExtensionContext[T_contra]) -> None:
        proto = context.proto

        log = self._log.bind_details(proto_name=proto.name)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_extension(context)

        for nested in reversed(self.__nested):
            nested.leave_extension(context)

        log.info("visited")

    def walk(self, *files: FileDescriptorProto, meta: t.Optional[T_contra] = None) -> None:
        for file in files:
            self.visit_file(
                FileContext(
                    _meta=meta,
                    proto=file,
                    path=[],
                )
            )

    def __walk_enums(self, context: t.Union[FileContext[T_contra], DescriptorContext[T_contra]]) -> None:
        for i, enum_type in enumerate(context.proto.enum_type):
            self.visit_enum(
                EnumContext(
                    _meta=context.meta,
                    parent=context,
                    proto=enum_type,
                    path=(*context.path, context.proto.ENUM_TYPE_FIELD_NUMBER, i),
                )
            )

    def __walk_enum_values(self, context: EnumContext[T_contra]) -> None:
        for i, value in enumerate(context.proto.value):
            self.visit_enum_value(
                EnumValueContext(
                    _meta=context.meta,
                    parent=context,
                    proto=value,
                    path=(*context.path, context.proto.VALUE_FIELD_NUMBER, i),
                )
            )

    def __walk_message_types(self, context: FileContext[T_contra]) -> None:
        for i, message_type in enumerate(context.proto.message_type):
            self.visit_descriptor(
                DescriptorContext(
                    _meta=context.meta,
                    parent=context,
                    proto=message_type,
                    path=(*context.path, context.proto.MESSAGE_TYPE_FIELD_NUMBER, i),
                )
            )

    def __walk_nested_types(self, context: DescriptorContext[T_contra]) -> None:
        for i, nested_type in enumerate(context.proto.nested_type):
            self.visit_descriptor(
                DescriptorContext(
                    _meta=context.meta,
                    parent=context,
                    proto=nested_type,
                    path=(*context.path, context.proto.NESTED_TYPE_FIELD_NUMBER, i),
                )
            )

    def __walk_oneofs(self, context: DescriptorContext[T_contra]) -> None:
        for i, oneof in enumerate(context.proto.oneof_decl):
            self.visit_oneof(
                OneofContext(
                    _meta=context.meta,
                    parent=context,
                    proto=oneof,
                    path=(*context.path, context.proto.ONEOF_DECL_FIELD_NUMBER, i),
                )
            )

    def __walk_fields(self, context: DescriptorContext[T_contra]) -> None:
        for i, field in enumerate(context.proto.field):
            self.visit_field(
                FieldContext(
                    _meta=context.meta,
                    parent=context,
                    proto=field,
                    path=(*context.path, context.proto.FIELD_FIELD_NUMBER, i),
                )
            )

    def __walk_services(self, context: FileContext[T_contra]) -> None:
        for i, service in enumerate(context.proto.service):
            self.visit_service(
                ServiceContext(
                    _meta=context.meta,
                    parent=context,
                    proto=service,
                    path=(*context.path, context.proto.SERVICE_FIELD_NUMBER, i),
                )
            )

    def __walk_methods(self, context: ServiceContext[T_contra]) -> None:
        for i, method in enumerate(context.proto.method):
            self.visit_method(
                MethodContext(
                    _meta=context.meta,
                    parent=context,
                    proto=method,
                    path=(*context.path, context.proto.METHOD_FIELD_NUMBER, i),
                )
            )

    def __walk_extensions(self, context: t.Union[FileContext[T_contra], DescriptorContext[T_contra]]) -> None:
        for i, ext in enumerate(context.proto.extension):
            self.visit_extension(
                ExtensionContext(
                    _meta=context.meta,
                    parent=context,
                    proto=ext,
                    path=(*context.path, context.proto.EXTENSION_FIELD_NUMBER, i),
                )
            )
