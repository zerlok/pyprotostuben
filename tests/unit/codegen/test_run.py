import io
import typing as t
from unittest.mock import create_autospec

import pytest
from _pytest.fixtures import SubRequest
from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest, CodeGeneratorResponse
from google.protobuf.descriptor_pb2 import FileDescriptorProto

from pyprotostuben.codegen.abc import ProtocPlugin
from pyprotostuben.codegen.run import run_codegen


class CustomPluginFailure(Exception):
    pass


@pytest.mark.parametrize(
    ["codegen_request", "codegen_error", "codegen_response"],
    [
        pytest.param(
            CodeGeneratorRequest(
                file_to_generate=["test.proto"],
                proto_file=[
                    FileDescriptorProto(
                        name="test.proto",
                        package="test",
                    )
                ],
            ),
            None,
            CodeGeneratorResponse(
                file=[
                    CodeGeneratorResponse.File(
                        name="test-file",
                        content="test-content",
                    ),
                ]
            ),
        ),
        pytest.param(
            CodeGeneratorRequest(),
            CustomPluginFailure(),
            CodeGeneratorResponse(error="CustomPluginFailure()"),
        ),
    ],
    indirect=True,
)
def test_run_codegen_forwars_plugin_request_and_response_to_streams(
    plugin: ProtocPlugin,
    codegen_request: t.Optional[CodeGeneratorRequest],
    codegen_response: t.Optional[CodeGeneratorResponse],
    codegen_input: t.IO[bytes],
    codegen_output: t.IO[bytes],
) -> None:
    run_codegen(plugin, codegen_input, codegen_output)

    plugin.run.assert_called_once_with(codegen_request)
    assert read_response(codegen_output) == codegen_response


def read_response(stream: t.IO[bytes]) -> t.Optional[CodeGeneratorResponse]:
    stream.seek(0, io.SEEK_SET)
    return CodeGeneratorResponse.FromString(stream.read())


@pytest.fixture
def codegen_request(request: SubRequest) -> t.Optional[CodeGeneratorRequest]:
    value = getattr(request, "param", None)
    assert value is None or isinstance(value, CodeGeneratorRequest)
    return value


@pytest.fixture
def codegen_error(request: SubRequest) -> t.Optional[Exception]:
    value = getattr(request, "param", None)
    assert value is None or isinstance(value, Exception)
    return value


@pytest.fixture
def codegen_response(request: SubRequest) -> t.Optional[CodeGeneratorResponse]:
    value = getattr(request, "param", None)
    assert value is None or isinstance(value, CodeGeneratorResponse)
    return value


@pytest.fixture
def codegen_input(codegen_request: t.Optional[CodeGeneratorRequest]) -> t.Iterator[t.IO[bytes]]:
    with io.BytesIO() as stream:
        if codegen_request is not None:
            stream.write(codegen_request.SerializeToString())
            stream.seek(0, io.SEEK_SET)

        yield stream


@pytest.fixture
def codegen_output() -> t.Iterator[t.IO[bytes]]:
    with io.BytesIO() as stream:
        yield stream


@pytest.fixture
def plugin(codegen_error: t.Optional[Exception], codegen_response: t.Optional[CodeGeneratorResponse]) -> ProtocPlugin:
    mock = create_autospec(ProtocPlugin)

    if codegen_error is not None:
        mock.run.side_effect = codegen_error

    elif codegen_response is not None:
        mock.run.return_value = codegen_response

    return mock
