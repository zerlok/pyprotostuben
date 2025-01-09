import abc
import typing as t

from pyprotostuben.python.visitor.model import ContainerContext, EnumContext, ScalarContext, StructureContext

T_contra = t.TypeVar("T_contra", contravariant=True)


class TypeVisitor(t.Generic[T_contra], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def visit_scalar(self, context: ScalarContext, meta: T_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_enum(self, context: EnumContext, meta: T_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_container(self, context: ContainerContext, meta: T_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def visit_structure(self, context: StructureContext, meta: T_contra) -> None:
        raise NotImplementedError


class TypeVisitorDecorator(t.Generic[T_contra], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def enter_scalar(self, context: ScalarContext, meta: T_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_scalar(self, context: ScalarContext, meta: T_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_enum(self, context: EnumContext, meta: T_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_enum(self, context: EnumContext, meta: T_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_container(self, context: ContainerContext, meta: T_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_container(self, context: ContainerContext, meta: T_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def enter_structure(self, context: StructureContext, meta: T_contra) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def leave_structure(self, context: StructureContext, meta: T_contra) -> None:
        raise NotImplementedError
