import functools as ft
import typing as t
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class NamespaceInfo:
    parent: t.Optional["NamespaceInfo"]
    name: str

    @ft.cached_property
    def parts(self) -> t.Sequence[str]:
        return *(self.parent.parts if self.parent is not None else ()), self.name

    @ft.cached_property
    def qualname(self) -> str:
        return ".".join(self.parts)


@dataclass(frozen=True)
class PackageInfo(NamespaceInfo):
    parent: t.Optional["PackageInfo"]

    @classmethod
    def build(cls, *parts: str) -> "PackageInfo":
        top, *tail = parts

        info = cls(None, top)
        for name in tail:
            info = cls(info, name)

        return info

    @classmethod
    def build_or_none(cls, *parts: str) -> t.Optional["PackageInfo"]:
        return cls.build(*parts) if parts else None

    @ft.cached_property
    def directory(self) -> Path:
        return Path(*self.parts)


@dataclass(frozen=True)
class ModuleInfo(NamespaceInfo):
    parent: t.Optional[PackageInfo]

    @classmethod
    def from_str(cls, ref: str) -> "ModuleInfo":
        *other, last = ref.split(".")
        return ModuleInfo(PackageInfo.build_or_none(*other), last)

    @property
    def package(self) -> t.Optional[PackageInfo]:
        return self.parent

    @ft.cached_property
    def file(self) -> Path:
        return ((self.package.directory / self.name) if self.package is not None else Path(self.name)).with_suffix(
            ".py",
        )

    @ft.cached_property
    def stub_file(self) -> Path:
        return self.file.with_suffix(".pyi")


@dataclass(frozen=True)
class TypeInfo:
    module: t.Optional[ModuleInfo]
    ns: t.Sequence[str]

    @classmethod
    def build(cls, module: t.Optional[ModuleInfo], *ns: str) -> "TypeInfo":
        return cls(module, ns)
