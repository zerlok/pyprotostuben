import json
import subprocess
import typing as t
from dataclasses import dataclass
from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest
from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest, CodeGeneratorResponse
from pyprotostuben.codegen.abc import ProtocPlugin
from pyprotostuben.codegen.mypy.plugin import MypyStubProtocPlugin

CASES_DIR = Path(__file__).parent / "cases"
CASES = [
    pytest.param(path, id=str(path.relative_to(CASES_DIR)))
    for path in sorted(CASES_DIR.iterdir())
    if path.is_dir() and path.stem != "__pycache__" and (path / "proto").is_dir()
]


@dataclass(frozen=True)
class Case:
    generator: ProtocPlugin
    request: CodeGeneratorRequest
    gen_expected_files: t.Sequence[CodeGeneratorResponse.File]


@pytest.fixture(params=CASES)
def case(request: SubRequest, tmp_path: Path) -> Case:
    case_dir: Path = request.param
    proto_dir = case_dir / "proto"
    expected_gen_dir = case_dir / "expected_gen"

    gen_request = _read_request(proto_dir, tmp_path)
    gen_request.parameter = "no-parallel"  # for easier debug

    return Case(
        generator=MypyStubProtocPlugin(),
        request=gen_request,
        gen_expected_files=[
            CodeGeneratorResponse.File(
                name=str(path.relative_to(expected_gen_dir)),
                content=_load_content(path),
            )
            for path in expected_gen_dir.iterdir()
        ],
    )


def _read_request(proto_dir: Path, tmp_path: Path) -> CodeGeneratorRequest:
    echo_result = subprocess.run(
        [  # noqa: S603,S607
            "protoc",
            f"-I{proto_dir}",
            f"--echo_out={tmp_path}",
            *(str(proto) for proto in proto_dir.rglob("*.proto")),
        ],
        stderr=subprocess.PIPE,
        encoding="utf-8",
        check=False,
    )

    if echo_result.returncode != 0:
        pytest.fail(echo_result.stderr)

    with (tmp_path / "request.json").open("r") as echo_out:
        return CodeGeneratorRequest(**json.load(echo_out))


def _load_content(path: Path) -> str:
    with path.open("r") as fd:
        return fd.read()
