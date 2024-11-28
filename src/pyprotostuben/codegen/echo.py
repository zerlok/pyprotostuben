import typing as t
from pathlib import Path

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest, CodeGeneratorResponse
from google.protobuf.json_format import MessageToJson

from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.parser import ParameterParser


class RequestEchoProtocPlugin(LoggerMixin):
    def run(self, input_: t.IO[bytes], output: t.IO[bytes]) -> None:
        input_content = input_.read()
        request = CodeGeneratorRequest.FromString(input_content)

        log = self._log.bind_details(request_file_to_generate=request.file_to_generate)
        log.debug("request received")

        parser = ParameterParser()
        params = parser.parse(request.parameter)

        format_ = params.get_raw_by_name("format", "raw")
        dest = Path(params.get_raw_by_name("dest", "request.bin"))

        content: bytes
        if format_ == "raw":
            content = input_content

        elif format_ == "binary":
            content = request.SerializeToString()

        elif format_ == "json":
            content = MessageToJson(request, preserving_proto_field_name=True, sort_keys=True).encode()

        else:
            msg = "unsupported format"
            raise ValueError(msg, format_)

        with dest.open("wb") as fd:
            fd.write(content)

        log.info("request handled", dest=dest)

        output.write(
            CodeGeneratorResponse(
                supported_features=CodeGeneratorResponse.Feature.FEATURE_PROTO3_OPTIONAL,
            ).SerializeToString()
        )
