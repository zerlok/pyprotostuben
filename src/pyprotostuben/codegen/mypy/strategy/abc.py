import abc
import typing as t
from pathlib import Path

from pyprotostuben.protobuf.file import ProtoFile


class Strategy(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def run(self, file: ProtoFile) -> t.Iterable[t.Tuple[ProtoFile, Path, str]]:
        raise NotImplementedError()
