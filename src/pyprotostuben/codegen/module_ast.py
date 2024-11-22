import ast
import typing as t
from dataclasses import dataclass
from pathlib import Path

from pyprotostuben.codegen.abc import ProtoFileGenerator
from pyprotostuben.codegen.model import GeneratedItem
from pyprotostuben.logging import Logger, LoggerMixin
from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.visitor.decorator import ProtoVisitorDecorator
from pyprotostuben.protobuf.visitor.walker import Walker


@dataclass()
class ModuleASTContext:
    file: ProtoFile
    modules: t.MutableMapping[Path, ast.Module]


T = t.TypeVar("T", bound=ModuleASTContext)


class ModuleASTBasedProtoFileGenerator(t.Generic[T], ProtoFileGenerator, LoggerMixin):
    def __init__(self, context_factory: t.Callable[[ProtoFile], T], visitor: ProtoVisitorDecorator[T]) -> None:
        self.__context_factory = context_factory
        self.__walker = Walker(visitor)

    def run(self, file: ProtoFile) -> t.Sequence[GeneratedItem]:
        log = self._log.bind_details(file_name=file.name)
        log.debug("file received")

        context = self.__context_factory(file)
        self.__walker.walk(context, file.descriptor)
        log.debug("proto visited", context=context)

        return list(self.__gen_modules(context, log))

    def __gen_modules(self, context: ModuleASTContext, log: Logger) -> t.Iterable[GeneratedItem]:
        for path, module_ast in context.modules.items():
            if not module_ast.body:
                continue

            module_content = ast.unparse(module_ast)
            module = GeneratedItem(context.file, path, module_content)

            log.info("module generated", module=module)

            yield module
