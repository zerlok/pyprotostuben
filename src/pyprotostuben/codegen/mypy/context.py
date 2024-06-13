from dataclasses import dataclass

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest

from pyprotostuben.codegen.parser import Parameters
from pyprotostuben.protobuf.context import Context
from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.types.registry import TypeRegistry


@dataclass(frozen=True)
class CodeGeneratorContext(Context):
    params: Parameters
    request: CodeGeneratorRequest


@dataclass(frozen=True)
class FileContext:
    type_registry: TypeRegistry
    file: ProtoFile
