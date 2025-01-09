import inspect
import typing as t
from dataclasses import dataclass
from pathlib import Path

from pyprotostuben.python.info import TypeInfo


@dataclass(frozen=True, kw_only=True)
class MethodInfo:
    name: str
    params: t.Sequence[inspect.Parameter]
    returns: type[object] | None
    doc: t.Optional[str]


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
