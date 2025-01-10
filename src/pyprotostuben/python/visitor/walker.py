import abc
import enum
import inspect
import typing as t
import uuid
from dataclasses import MISSING, is_dataclass
from dataclasses import fields as get_dataclass_fields
from datetime import date, datetime, time, timedelta
from functools import lru_cache

from pyprotostuben.logging import LoggerMixin
from pyprotostuben.python.visitor.abc import TypeVisitor, TypeVisitorDecorator
from pyprotostuben.python.visitor.model import (
    ContainerContext,
    EnumContext,
    ScalarContext,
    StructureContext,
    empty,
)

T_contra = t.TypeVar("T_contra", contravariant=True)


class TypeWalkerTrait(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def extract_scalar(self, obj: object) -> t.Optional[ScalarContext]:
        raise NotImplementedError

    @abc.abstractmethod
    def extract_enum(self, obj: object) -> t.Optional[EnumContext]:
        raise NotImplementedError

    @abc.abstractmethod
    def extract_container(self, obj: object) -> t.Optional[ContainerContext]:
        raise NotImplementedError

    @abc.abstractmethod
    def extract_structure(self, obj: object) -> t.Optional[StructureContext]:
        raise NotImplementedError


class DefaultTypeWalkerTrait(TypeWalkerTrait):
    @lru_cache
    def extract_scalar(self, obj: object) -> t.Optional[ScalarContext]:
        if obj is None or obj is type(None):
            return ScalarContext(type_=type(None))

        if obj is Ellipsis:
            return ScalarContext(type_=type(Ellipsis))

        if obj is t.Any or (
            isinstance(obj, type)
            and issubclass(
                obj, (bytes, bytearray, bool, int, float, complex, str, time, date, datetime, timedelta, uuid.UUID)
            )
        ):
            return ScalarContext(type_=obj)

        return None

    @lru_cache
    def extract_enum(self, obj: object) -> t.Optional[EnumContext]:
        if t.get_origin(obj) is t.Literal:
            return EnumContext(
                type_=obj,
                name=None,
                values=tuple(EnumContext.ValueInfo(name=value, value=value) for value in t.get_args(obj)),
            )

        if isinstance(obj, type) and issubclass(obj, enum.Enum):
            return EnumContext(
                type_=obj,
                name=obj.__name__,
                values=tuple(EnumContext.ValueInfo(name=el.name, value=el.value) for el in obj),
            )

        return None

    @lru_cache
    def extract_container(self, obj: object) -> t.Optional[ContainerContext]:
        if isinstance(obj, t.NewType):
            return ContainerContext(
                type_=obj,
                origin=obj.__supertype__,
                inners=(),
            )

        if (origin := t.get_origin(obj)) is not None and origin not in {t.Literal, t.Generic}:
            return ContainerContext(
                type_=obj,
                origin=origin,
                inners=t.get_args(obj),
            )

        return None

    @lru_cache
    def extract_structure(self, obj: object) -> t.Optional[StructureContext]:
        if not isinstance(obj, type):
            return None

        if is_dataclass(obj):
            return StructureContext(
                type_=obj,
                name=obj.__name__,
                fields=tuple(
                    StructureContext.FieldInfo(
                        name=field.name,
                        annotation=field.type,  # TODO: handle str case
                        default_value=field.default if field.default is not MISSING else empty(),
                    )
                    for field in get_dataclass_fields(obj)
                ),
            )

        return StructureContext(
            type_=obj,
            name=obj.__name__,
            fields=tuple(
                StructureContext.FieldInfo(
                    name=name,
                    annotation=member,
                )
                for name, member in inspect.getmembers_static(obj)
                if not name.startswith("_") and not inspect.isfunction(obj)
            ),
        )


class TypeWalker(TypeVisitor[T_contra], LoggerMixin):
    def __init__(
        self,
        trait: TypeWalkerTrait,
        *nested: TypeVisitorDecorator[T_contra],
    ) -> None:
        self.__trait = trait
        self.__nested = nested

    def visit_scalar(self, context: ScalarContext, meta: T_contra) -> None:
        log = self._log.bind_details(context=context)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_scalar(context, meta)

        for nested in reversed(self.__nested):
            nested.leave_scalar(context, meta)

        log.info("visited")

    def visit_enum(self, context: EnumContext, meta: T_contra) -> None:
        log = self._log.bind_details(context=context)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_enum(context, meta)

        for nested in reversed(self.__nested):
            nested.leave_enum(context, meta)

        log.info("visited")

    def visit_container(self, context: ContainerContext, meta: T_contra) -> None:
        log = self._log.bind_details(context=context)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_container(context, meta)

        for inner in context.inners:
            self.walk(inner, meta)

        for nested in reversed(self.__nested):
            nested.leave_container(context, meta)

        log.info("visited")

    def visit_structure(self, context: StructureContext, meta: T_contra) -> None:
        log = self._log.bind_details(context=context)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_structure(context, meta)

        for field in context.fields:
            self.walk(field.annotation, meta)

        for nested in reversed(self.__nested):
            nested.leave_structure(context, meta)

        log.info("visited")

    def walk(self, type_: t.Optional[type[object]], meta: T_contra) -> None:
        if (scalar_ctx := self.__trait.extract_scalar(type_)) is not None:
            self.visit_scalar(scalar_ctx, meta)

        elif (enum_ctx := self.__trait.extract_enum(type_)) is not None:
            self.visit_enum(enum_ctx, meta)

        elif (container_ctx := self.__trait.extract_container(type_)) is not None:
            self.visit_container(container_ctx, meta)

        elif (struct_ctx := self.__trait.extract_structure(type_)) is not None:
            self.visit_structure(struct_ctx, meta)

        else:
            details = "unsupported type"
            raise TypeError(details, type_, meta)
