import sys
import typing as t

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest, CodeGeneratorResponse

from pyprotostuben.codegen.abc import ProtocPlugin
from pyprotostuben.logging import Logger


def run_codegen(
    gen: ProtocPlugin,
    input_: t.IO[bytes] = sys.stdin.buffer,
    output: t.IO[bytes] = sys.stdout.buffer,
) -> None:
    log = Logger.get(__name__)

    request = CodeGeneratorRequest.FromString(input_.read())

    log.debug("started", gen=gen)
    try:
        response = gen.run(request)

    except Exception as err:
        log.exception("generator error occurred", exc_info=err)

        response = CodeGeneratorResponse(
            error=repr(err),
        )

    log.debug("finished", gen=gen)

    output.write(response.SerializeToString())

    log.info("run", gen=gen)
