import inspect
import typing as t
from dataclasses import dataclass
from pathlib import Path

from pyprotostuben.python.info import ModuleInfo, TypeInfo


@dataclass(frozen=True, kw_only=True)
class MethodInfo:
    name: str
    signature: inspect.Signature
    doc: t.Optional[str]


@dataclass(frozen=True, kw_only=True)
class GroupInfo:
    info: TypeInfo
    methods: t.Sequence[MethodInfo]

    @property
    def name(self) -> str:
        return self.info.ns[0]


@dataclass(frozen=True, kw_only=True)
class EntrypointInfo:
    module: ModuleInfo
    groups: t.Sequence[GroupInfo]

    @property
    def name(self) -> str:
        return self.module.name


@dataclass(frozen=True, kw_only=True)
class GeneratorContext:
    entrypoints: t.Sequence[EntrypointInfo]
    output: Path
    package: t.Optional[str]

    def iter_methods(self) -> t.Iterable[tuple[EntrypointInfo, GroupInfo, MethodInfo]]:
        for entrypoint in self.entrypoints:
            for group in entrypoint.groups:
                for method in group.methods:
                    yield entrypoint, group, method


@dataclass(frozen=True, kw_only=True)
class GeneratedFile:
    path: Path
    content: str
