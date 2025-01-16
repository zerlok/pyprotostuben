import abc
import typing as t

from pyprotostuben.codegen.servicify.model import GeneratedFile, GeneratorContext


class ServicifyCodeGenerator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def generate(self, context: GeneratorContext) -> t.Sequence[GeneratedFile]:
        raise NotImplementedError
