import inspect
import typing as t
from dataclasses import dataclass
from pathlib import Path

from pyprotostuben.python.info import TypeInfo


@dataclass(frozen=True, kw_only=True)
class BaseMethodInfo:
    name: str
    doc: t.Optional[str]


@dataclass(frozen=True, kw_only=True)
class UnaryUnaryMethodInfo(BaseMethodInfo):
    params: t.Sequence[inspect.Parameter]
    returns: type[object] | None


@dataclass(frozen=True, kw_only=True)
class StreamStreamMethodInfo(BaseMethodInfo):
    input_: inspect.Parameter
    output: type[object] | None


MethodInfo: t.TypeAlias = t.Union[UnaryUnaryMethodInfo, StreamStreamMethodInfo]


@dataclass(frozen=True, kw_only=True)
class EntrypointInfo:
    name: str
    type_: TypeInfo
    methods: t.Sequence[MethodInfo]
    doc: t.Optional[str]


@dataclass(frozen=True, kw_only=True)
class EntrypointOptions:
    name: t.Optional[str] = None
    version: t.Optional[str] = None


@dataclass(frozen=True, kw_only=True)
class GeneratorContext:
    entrypoints: t.Sequence[EntrypointInfo]
    source: Path
    output: Path
    package: t.Optional[str]


@dataclass(frozen=True, kw_only=True)
class GeneratedFile:
    path: Path
    content: str
