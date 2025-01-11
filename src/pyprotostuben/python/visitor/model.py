import typing as t
from dataclasses import dataclass


class _Empty:
    __slots__ = ()

    def __str__(self) -> str:
        return "<EMPTY>"

    __repr__ = __str__


_EMPTY: t.Final[_Empty] = _Empty()


@dataclass(frozen=True, kw_only=True)
class _BaseContext:
    type_: object


@dataclass(frozen=True, kw_only=True)
class ScalarContext(_BaseContext):
    pass


@dataclass(frozen=True, kw_only=True)
class EnumValueContext(_BaseContext):
    name: t.Optional[str]
    value: object
    description: t.Optional[str] = None


@dataclass(frozen=True, kw_only=True)
class EnumContext(_BaseContext):
    name: t.Optional[str]
    values: t.Sequence[EnumValueContext]
    description: t.Optional[str] = None


@dataclass(frozen=True, kw_only=True)
class ContainerContext(_BaseContext):
    origin: type[object]
    inners: t.Sequence[type[object]]


@dataclass(frozen=True, kw_only=True)
class StructureFieldContext(_BaseContext):
    name: str
    annotation: type[object]
    default_value: object = _EMPTY
    description: t.Optional[str] = None


@dataclass(frozen=True, kw_only=True)
class StructureContext(_BaseContext):
    name: str
    fields: t.Sequence[StructureFieldContext]
    description: t.Optional[str] = None


def empty() -> object:
    return _EMPTY


def is_empty(obj: object) -> bool:
    return obj is _EMPTY
