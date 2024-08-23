import abc
import ast
import typing as t
from pathlib import Path

from pyprotostuben.codegen.abc import ProtoFileGenerator
from pyprotostuben.logging import Logger, LoggerMixin
from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.visitor.abc import visit
from pyprotostuben.protobuf.visitor.decorator import ProtoVisitorDecorator
from pyprotostuben.protobuf.visitor.dfs import DFSWalkingProtoVisitor


class ModuleASTProtoVisitorDecoratorFactory(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def create_proto_visitor_decorator(self, modules: t.MutableMapping[Path, ast.Module]) -> ProtoVisitorDecorator:
        raise NotImplementedError


class ModuleASTBasedProtoFileGenerator(ProtoFileGenerator, LoggerMixin):
    def __init__(self, factory: ModuleASTProtoVisitorDecoratorFactory) -> None:
        self.__factory = factory

    def run(self, file: ProtoFile) -> t.Sequence[t.Tuple[ProtoFile, Path, str]]:
        log = self._log.bind_details(file_name=file.name)
        log.debug("file received")

        modules: t.Dict[Path, ast.Module] = {}

        generator = self.__factory.create_proto_visitor_decorator(modules)
        log = log.bind_details(generator=generator)

        visit(DFSWalkingProtoVisitor(generator), file.descriptor)
        log.debug("proto visited", modules=modules)

        return list(self.__gen_modules(file, modules, log))

    def __gen_modules(
        self,
        file: ProtoFile,
        modules: t.Mapping[Path, ast.Module],
        log: Logger,
    ) -> t.Iterable[t.Tuple[ProtoFile, Path, str]]:
        for path, module_ast in modules.items():
            if not module_ast.body:
                continue

            module_content = ast.unparse(module_ast)
            log.info("module generated", path=path)

            yield file, path, module_content
