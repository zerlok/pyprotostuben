import abc
import importlib
import json
import subprocess
import typing as t
from dataclasses import dataclass
from pathlib import Path

import pytest
from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest, CodeGeneratorResponse
from pyprotostuben.codegen.abc import ProtocPlugin


@dataclass(frozen=True)
class Case:
    generator: ProtocPlugin
    request: CodeGeneratorRequest
    gen_expected_files: t.Sequence[CodeGeneratorResponse.File]


class CaseProvider(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def provide(self, tmp_path: Path) -> Case:
        raise NotImplementedError


class SimpleCaseProvider(CaseProvider):
    def __init__(
        self,
        filename: str,
        plugin: ProtocPlugin,
        proto_source: t.Optional[str] = None,
        proto_paths: t.Optional[t.Sequence[str]] = None,
        expected_gen_source: t.Optional[str] = None,
        expected_gen_paths: t.Optional[t.Sequence[str]] = None,
    ) -> None:
        self.__case_dir = Path(filename).parent
        self.__plugin = plugin

        self.__proto_source = self.__case_dir / (proto_source or "proto")
        self.__expected_gen_source = self.__case_dir / (expected_gen_source or "expected_gen")

        assert self.__proto_source.exists(), f"not found: {self.__proto_source}"
        assert self.__expected_gen_source.exists(), f"not found: {self.__expected_gen_source}"

        self.__proto_paths = (
            [self.__proto_source / path for path in proto_paths]
            if proto_paths is not None
            else list(self.__proto_source.iterdir())
        )
        self.__expected_gen_paths = (
            [self.__expected_gen_source / path for path in expected_gen_paths]
            if expected_gen_paths is not None
            else list(self.__expected_gen_source.iterdir())
        )

    def provide(self, tmp_path: Path) -> Case:
        gen_request = read_request(self.__proto_source, self.__proto_paths, tmp_path)
        gen_request.parameter = "no-parallel"  # for easier debug

        return Case(
            generator=self.__plugin,
            request=gen_request,
            gen_expected_files=[
                load_expected_gen(self.__expected_gen_source, path) for path in self.__expected_gen_paths
            ],
        )


def read_request(proto_source: Path, proto_paths: t.Iterable[Path], tmp_path: Path) -> CodeGeneratorRequest:
    echo_result = subprocess.run(
        [  # noqa: S603,S607
            "protoc",
            f"-I{proto_source}",
            f"--echo_out={tmp_path}",
            *(str(proto) for proto in proto_paths),
        ],
        stderr=subprocess.PIPE,
        encoding="utf-8",
        check=False,
    )

    if echo_result.returncode != 0:
        pytest.fail(echo_result.stderr)

    with (tmp_path / "request.json").open("r") as echo_out:
        return CodeGeneratorRequest(**json.load(echo_out))


def load_expected_gen(source: Path, path: Path) -> CodeGeneratorResponse.File:
    with path.open("r") as fd:
        return CodeGeneratorResponse.File(
            name=str(path.relative_to(source)),
            content=fd.read(),
        )


def build_plugin_case(
    plugin: ProtocPlugin,
    proto_source: Path,
    proto_paths: t.Iterable[Path],
    expected_gen_source: Path,
    expected_gen_paths: t.Iterable[Path],
    tmp_path: Path,
) -> Case:
    gen_request = read_request(proto_source, proto_paths, tmp_path)
    gen_request.parameter = "no-parallel"  # for easier debug

    return Case(
        generator=plugin,
        request=gen_request,
        gen_expected_files=[load_expected_gen(expected_gen_source, path) for path in expected_gen_paths],
    )
