import typing as t
from pathlib import Path

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest, CodeGeneratorResponse
from google.protobuf.json_format import MessageToJson

from pyprotostuben.codegen.abc import ProtocPlugin
from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.parser import ParameterParser


class RequestEchoProtocPlugin(ProtocPlugin, LoggerMixin):
    def run(self, request: CodeGeneratorRequest) -> CodeGeneratorResponse:
        log = self._log.bind_details(request_file_to_generate=request.file_to_generate)
        log.debug("request received")

        parser = ParameterParser()
        params = parser.parse(request.parameter)

        format_ = params.get_raw_by_name("format", "json")
        dest = Path(params.get_raw_by_name("dest", "request.json"))

        content: t.Union[bytes, str]
        if format_ == "binary":
            content = request.SerializeToString()

        elif format_ == "json":
            content = MessageToJson(request, preserving_proto_field_name=True, sort_keys=True)

        else:
            msg = "unsupported format"
            raise ValueError(msg, format_)

        log.info("request handled", dest=dest)

        return CodeGeneratorResponse(
            supported_features=CodeGeneratorResponse.Feature.FEATURE_PROTO3_OPTIONAL,
            file=[CodeGeneratorResponse.File(name=str(dest), content=t.cast(str, content))],
        )
