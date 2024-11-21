import typing as t

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest, CodeGeneratorResponse

from pyprotostuben.codegen.abc import ProtocPlugin


class CustomPluginError(Exception):
    pass


class ProtocPluginStub(ProtocPlugin):
    def __init__(self, side_effect: t.Optional[Exception], return_value: t.Optional[CodeGeneratorResponse]) -> None:
        self.requests: t.List[CodeGeneratorRequest] = []
        self.__side_effect = side_effect
        self.__return_value = return_value

    def run(self, request: CodeGeneratorRequest) -> CodeGeneratorResponse:
        self.requests.append(request)

        if self.__side_effect is not None:
            raise self.__side_effect

        if self.__return_value is not None:
            return self.__return_value

        raise ValueError(self.__side_effect, self.__return_value)
