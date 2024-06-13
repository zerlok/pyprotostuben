import abc

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest, CodeGeneratorResponse


class CodeGenerator(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def run(self, request: CodeGeneratorRequest) -> CodeGeneratorResponse:
        raise NotImplementedError
