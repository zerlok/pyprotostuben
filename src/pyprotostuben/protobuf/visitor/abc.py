import abc
import typing as t

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


class ProtoVisitor(t.Generic[T_contra], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def visit_file(self, context: FileContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_enum(self, context: EnumContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_enum_value(self, context: EnumValueContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_descriptor(self, context: DescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_oneof(self, context: OneofContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_field(self, context: FieldContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_service(self, context: ServiceContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_method(self, context: MethodContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_extension(self, context: ExtensionContext[T_contra]) -> None:
        raise NotImplementedError


class ProtoVisitorDecorator(t.Generic[T_contra], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def enter_file(self, context: FileContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_file(self, context: FileContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_enum(self, context: EnumContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_enum(self, context: EnumContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_enum_value(self, context: EnumValueContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_enum_value(self, context: EnumValueContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_descriptor(self, context: DescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_descriptor(self, context: DescriptorContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_oneof(self, context: OneofContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_oneof(self, context: OneofContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_field(self, context: FieldContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_field(self, context: FieldContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_service(self, context: ServiceContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_service(self, context: ServiceContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_method(self, context: MethodContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_method(self, context: MethodContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_extension(self, context: ExtensionContext[T_contra]) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_extension(self, context: ExtensionContext[T_contra]) -> None:
        raise NotImplementedError
