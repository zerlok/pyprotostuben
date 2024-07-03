import typing as t

from pyprotostuben.python.ast_builder import DependencyResolver
from pyprotostuben.python.info import ModuleInfo, TypeInfo


class ProtoDependencyResolver(DependencyResolver):
    def __init__(self, module: ModuleInfo, deps: t.MutableSet[ModuleInfo]) -> None:
        self.__module = module
        self.__deps = deps

    def resolve(self, info: TypeInfo) -> TypeInfo:
        if info.module == self.__module:
            return TypeInfo(None, info.ns)

        if info.module is not None:
            self.__deps.add(info.module)

        return info
