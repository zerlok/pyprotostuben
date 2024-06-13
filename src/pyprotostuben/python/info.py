from typing_extensions import Self
import functools as ft
import typing as t
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class NamespaceInfo:
    parent: t.Optional["NamespaceInfo"]
    name: str

    @classmethod
    def build(cls, *parts: str) -> Self:
        top, *tail = parts

        info = cls(None, top)
        for name in tail:
            info = cls(info, name)

        return info

    @classmethod
    def build_or_none(cls, *parts: str) -> t.Optional[Self]:
        return cls.build(*parts) if parts else None

    @ft.cached_property
    def parts(self) -> t.Sequence[str]:
        return *(self.parent.parts if self.parent is not None else ()), self.name

    @ft.cached_property
    def qualname(self) -> str:
        return ".".join(self.parts)


@dataclass(frozen=True)
class PackageInfo(NamespaceInfo):
    parent: t.Optional["PackageInfo"]

    # @classmethod
    # def build(cls, *parts: str) -> "PackageInfo":
    #     top, *tail = parts
    #
    #     info = cls(None, top)
    #     for name in tail:
    #         info = cls(info, name)
    #
    #     return info
    #
    # @classmethod
    # def build_or_none(cls, *parts: str) -> t.Optional["PackageInfo"]:
    #     return cls.build(*parts) if parts else None

    @ft.cached_property
    def directory(self) -> Path:
        return Path(*self.parts)


@dataclass(frozen=True)
class ModuleInfo(NamespaceInfo):
    parent: t.Optional[PackageInfo]

    @classmethod
    def build(cls, *parts: str) -> "ModuleInfo":
        *package_parts, name = parts
        return cls(PackageInfo.build_or_none(*package_parts), name)

    @classmethod
    def build_or_none(cls, *parts: str) -> t.Optional["ModuleInfo"]:
        return cls.build(*parts) if parts else None

    @property
    def package(self) -> t.Optional[PackageInfo]:
        return self.parent

    @ft.cached_property
    def file(self) -> Path:
        return ((self.package.directory / self.name) if self.package is not None else Path(self.name)).with_suffix(
            ".py"
        )

    @ft.cached_property
    def stub_file(self) -> Path:
        return self.file.with_suffix(".pyi")


@dataclass(frozen=True)
class TypeInfo(NamespaceInfo):
    parent: t.Union[ModuleInfo, "TypeInfo"]

    # @classmethod
    # def build(
    #     cls,
    #     parent: t.Union[ModuleInfo, "TypeInfo", t.Sequence[str]],
    #     *namespace: str,
    # ) -> "TypeInfo":
    #     if isinstance(parent, (ModuleInfo, TypeInfo)):
    #         clean_parent = parent
    #
    #     else:
    #         clean_parent = ModuleInfo.build(*parent)
    #
    #     top, *tail = namespace
    #     info = cls(clean_parent, top)
    #
    #     for name in tail:
    #         info = cls(info, name)
    #
    #     return info

    @classmethod
    def create(cls, module: ModuleInfo, *parts: str) -> "TypeInfo":
        top, *tail = parts
        info = cls(module, top)

        for name in tail:
            info = cls(info, name)

        return info

    @property
    def package(self) -> t.Optional[PackageInfo]:
        return self.module.package

    @ft.cached_property
    def module(self) -> ModuleInfo:
        curr: t.Union[ModuleInfo, TypeInfo] = self

        while True:
            if isinstance(curr, ModuleInfo):
                return curr

            curr = curr.parent

    @ft.cached_property
    def namespace(self) -> NamespaceInfo:
        return NamespaceInfo.build(*self.parts[len(self.module.parts) :])
