from dataclasses import dataclass
from pathlib import Path

from pyprotostuben.protobuf.file import ProtoFile


@dataclass(frozen=True)
class GeneratedItem:
    source: ProtoFile
    path: Path
    content: str
