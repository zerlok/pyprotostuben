import abc
import os
import shutil
import subprocess
import typing as t
from dataclasses import dataclass
from importlib import import_module
from itertools import chain
from pathlib import Path

import pytest
from _pytest.mark import Mark
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

    @abc.abstractmethod
    def get_name(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_marks(self) -> t.Sequence[Mark]:
        raise NotImplementedError


class DirCaseProvider(CaseProvider):
    # NOTE: case provider constructor has many settings, no need to add extra class.
    def __init__(  # noqa: PLR0913
        self,
        *,
        filename: str,
        plugin: ProtocPlugin,
        marks: t.Optional[t.Sequence[Mark]] = None,
        deps: t.Optional[t.Sequence[str]] = None,
        deps_dir: t.Optional[Path] = None,
        parameter: t.Optional[str] = None,
        proto_source: t.Optional[str] = None,
        proto_paths: t.Optional[t.Sequence[str]] = None,
        expected_gen_source: t.Optional[str] = None,
        expected_gen_paths: t.Optional[t.Sequence[str]] = None,
    ) -> None:
        self.__case_dir = Path(filename).parent
        self.__plugin = plugin
        self.__marks = marks
        self.__deps = deps
        self.__deps_dir = deps_dir
        self.__parameter = parameter

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
            else [path for path in self.__expected_gen_source.iterdir() if path.name != "__init__.py"]
        )

    def provide(self, tmp_path: Path) -> Case:
        request = read_request_protoc(
            source=self.__proto_source,
            working_dir=tmp_path,
            deps=self.__deps,
            deps_dir=self.__deps_dir if self.__deps_dir is not None else tmp_path / "deps",
            protos=self.__proto_paths,
        )

        if self.__parameter is not None:
            request.parameter = self.__parameter

        return Case(
            generator=self.__plugin,
            request=request,
            gen_expected_files=[
                load_codegen_response_file_content(self.__expected_gen_source, path)
                for path in self.__expected_gen_paths
            ],
        )

    def get_name(self) -> str:
        return self.__case_dir.stem

    def get_marks(self) -> t.Sequence[Mark]:
        return self.__marks or ()


# TODO: find a way to run `buf generate`
def read_request_protoc(
    source: Path,
    working_dir: Path,
    deps: t.Optional[t.Sequence[str]],
    deps_dir: Path,
    protos: t.Sequence[Path],
) -> CodeGeneratorRequest:
    protoc = shutil.which("protoc")
    if not protoc:
        pytest.fail("can't find protoc")

    buf = shutil.which("buf")
    if not buf:
        pytest.fail("can't find buf")

    request_bin_path = working_dir / "request.bin"
    request_bin_path.unlink(missing_ok=True)

    if not deps_dir.exists():
        deps_dir.mkdir(parents=True, exist_ok=True)
        for dep in deps or ():
            run_cmd(working_dir, buf, "export", dep, "--output", str(deps_dir))

    run_cmd(working_dir, protoc, f"-I{source}", f"-I{deps_dir}", "--echo_out=.", *(str(proto) for proto in protos))

    return CodeGeneratorRequest.FromString(request_bin_path.read_bytes())


def run_cmd(working_dir: Path, *args: str) -> None:
    cmd_result = subprocess.run(
        args=args,
        cwd=working_dir,
        env={
            # NOTE: this fixes `pluggy` coverage combine during pytest teardown.
            "COVERAGE_PROCESS_START": "1",
            # NOTE: forward values of PATH & PYTHONPATH so `protoc` can find local project plugins.
            "PATH": os.getenv("PATH", ""),
            "PYTHONPATH": os.getenv("PYTHONPATH", ""),
        },
        stderr=subprocess.PIPE,
        encoding="utf-8",
        check=False,
    )

    if cmd_result.returncode != 0:
        pytest.fail(_trim_lines(cmd_result.stderr))


def _trim_lines(value: str) -> str:
    threshold = 16
    lines = value.split("\n")

    if len(lines) <= threshold * 2:
        return value

    return "\n".join(
        chain(lines[:threshold], (f"... (skipped {len(lines) - threshold * 2} lines)",), lines[-threshold:])
    )


def load_codegen_response_file_content(source: Path, path: Path) -> CodeGeneratorResponse.File:
    return CodeGeneratorResponse.File(
        name=str(path.relative_to(source)),
        content=path.read_text(),
    )


def skip_if_module_not_found(qualname: str) -> Mark:
    try:
        import_module(qualname)

    except ImportError:
        found = False

    else:
        found = True

    return pytest.mark.skipif(not found, reason=f"module not found: {qualname}")
