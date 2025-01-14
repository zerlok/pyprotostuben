import abc
import enum
import inspect
import typing as t
import uuid
from dataclasses import MISSING, is_dataclass
from dataclasses import fields as get_dataclass_fields
from datetime import date, datetime, time, timedelta

from pyprotostuben.logging import LoggerMixin
from pyprotostuben.python.visitor.abc import TypeVisitor, TypeVisitorDecorator
from pyprotostuben.python.visitor.model import (
    ContainerContext,
    EnumContext,
    EnumValueContext,
    ScalarContext,
    StructureContext,
    StructureFieldContext,
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
    def extract_scalar(self, obj: object) -> t.Optional[ScalarContext]:
        if obj is None or obj is type(None):
            return ScalarContext(type_=type(None))

        if obj is Ellipsis:
            return ScalarContext(type_=type(Ellipsis))

        if isinstance(obj, type) and issubclass(
            obj, (bytes, bytearray, bool, int, float, complex, str, time, date, datetime, timedelta, uuid.UUID)
        ):
            return ScalarContext(type_=obj)

        if obj is t.Any:
            return ScalarContext(type_=object)

        return None

    def extract_enum(self, obj: object) -> t.Optional[EnumContext]:
        if t.get_origin(obj) is t.Literal:
            return EnumContext(
                type_=t.cast(type[object], obj),
                name=None,
                values=tuple(
                    EnumValueContext(
                        type_=type(value),
                        name=value,
                        value=value,
                    )
                    for value in t.get_args(obj)
                ),
            )

        if isinstance(obj, type) and issubclass(obj, enum.Enum):
            return EnumContext(
                type_=obj,
                name=obj.__name__,
                values=tuple(
                    EnumValueContext(
                        type_=obj,
                        name=el.name,
                        value=el.value,
                    )
                    for el in obj
                ),
                description=get_enum_doc(obj),
            )

        return None

    def extract_container(self, obj: object) -> t.Optional[ContainerContext]:
        if isinstance(obj, type) and isinstance(obj, t.NewType):
            return ContainerContext(
                type_=obj,
                origin=obj.__supertype__,
                inners=(),
            )

        if (origin := t.get_origin(obj)) is not None and origin not in {t.Literal, t.Generic}:
            inners = t.get_args(obj)

            if (
                getattr(obj, "__module__", None) == t.Optional.__module__
                and getattr(obj, "__name__", None) == t.Optional.__name__  # type: ignore[attr-defined]
            ):
                origin = t.Optional
                inners = inners[:1]

            return ContainerContext(
                type_=t.cast(type[object], obj),
                origin=origin,
                inners=inners,
            )

        return None

    def extract_structure(self, obj: object) -> t.Optional[StructureContext]:
        if not isinstance(obj, type):
            return None

        if is_dataclass(obj):
            fields = list[StructureFieldContext]()

            for field in get_dataclass_fields(obj):
                # TODO: handle str case (forward ref)
                if isinstance(field.type, str):
                    raise TypeError(field.type, field, obj)

                fields.append(
                    StructureFieldContext(
                        type_=field.type,
                        name=field.name,
                        annotation=field.type,
                        default_value=field.default if field.default is not MISSING else empty(),
                    )
                )

            return StructureContext(
                type_=obj,
                name=obj.__name__,
                fields=tuple(fields),
                description=get_dataclass_doc(obj),
            )

        # TODO: support more structured types, e.g. attrs or simple python classes with properties

        return None


def get_enum_doc(type_: type[enum.Enum]) -> t.Optional[str]:
    doc = inspect.getdoc(type_)

    # Python enums provides base enum class documentation if custom docstring is not set in custom enum definition.
    # Don't use it as docstring.
    return doc if doc != inspect.getdoc(enum.Enum) else None


def get_dataclass_doc(dc: type[object]) -> t.Optional[str]:
    doc = inspect.getdoc(dc)
    if doc is None:
        return None

    # skip `self`
    params = list(inspect.signature(dc.__init__).parameters.values())[1:]
    init_signature_doc = f"{dc.__name__}{inspect.Signature(params)}"

    # Python dataclasses provides init constructor signature documentation if custom docstring is not set in class
    # definition. Don't use it as docstring (e.g. don't expose internal implementation to API level).
    return doc if doc != init_signature_doc else None


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

        for value in context.values:
            self.visit_enum_value(value, meta)

        for nested in reversed(self.__nested):
            nested.leave_enum(context, meta)

        log.info("visited")

    def visit_enum_value(self, context: EnumValueContext, meta: T_contra) -> None:
        log = self._log.bind_details(context=context)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_enum_value(context, meta)

        for nested in reversed(self.__nested):
            nested.leave_enum_value(context, meta)

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
            self.visit_structure_field(field, meta)

        for nested in reversed(self.__nested):
            nested.leave_structure(context, meta)

        log.info("visited")

    def visit_structure_field(self, context: StructureFieldContext, meta: T_contra) -> None:
        log = self._log.bind_details(context=context)
        log.debug("entered")

        for nested in self.__nested:
            nested.enter_structure_field(context, meta)

        self.walk(context.annotation, meta)

        for nested in reversed(self.__nested):
            nested.leave_structure_field(context, meta)

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
