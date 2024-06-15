from dataclasses import dataclass

from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.registry import TypeRegistry


@dataclass(frozen=True)
class FileContext:
    type_registry: TypeRegistry
    file: ProtoFile
