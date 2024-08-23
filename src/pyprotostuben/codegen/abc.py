import abc
import typing as t
from pathlib import Path

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest, CodeGeneratorResponse

from pyprotostuben.protobuf.file import ProtoFile


class ProtocPlugin(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def run(self, request: CodeGeneratorRequest) -> CodeGeneratorResponse:
        raise NotImplementedError


class ProtoFileGenerator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def run(self, file: ProtoFile) -> t.Sequence[t.Tuple[ProtoFile, Path, str]]:
        raise NotImplementedError
