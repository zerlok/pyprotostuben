import ast
import typing as t
from dataclasses import dataclass, field
from pathlib import Path

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorResponse
from google.protobuf.descriptor_pb2 import GeneratedCodeInfo

from pyprotostuben.codegen.abc import ProtoFileGenerator
from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.visitor.abc import ProtoVisitorDecorator
from pyprotostuben.protobuf.visitor.walker import Walker


@dataclass()
class ModuleAstContext:
    generated_modules: t.MutableMapping[Path, ast.Module] = field(default_factory=dict)


T = t.TypeVar("T", bound=ModuleAstContext)


class ModuleAstProtoFileGenerator(t.Generic[T], ProtoFileGenerator, LoggerMixin):
    def __init__(self, context_factory: t.Callable[[ProtoFile], T], visitor: ProtoVisitorDecorator[T]) -> None:
        self.__context_factory = context_factory
        self.__walker = Walker(visitor)

    def run(self, file: ProtoFile) -> t.Sequence[CodeGeneratorResponse.File]:
        log = self._log.bind_details(file_name=file.name)
        log.debug("proto file received")

        context = self.__context_factory(file)
        self.__walker.walk(file.proto, meta=context)
        log.debug("proto file visited", context=context)

        info = GeneratedCodeInfo(
            annotation=[
                GeneratedCodeInfo.Annotation(
                    source_file=str(file.proto_path),
                ),
            ],
        )
        files = [
            CodeGeneratorResponse.File(
                name=str(path),
                content=ast.unparse(module_ast),
                generated_code_info=info,
            )
            for path, module_ast in context.generated_modules.items()
            if module_ast.body
        ]

        log.info("modules generated", files_len=len(files))

        return files
