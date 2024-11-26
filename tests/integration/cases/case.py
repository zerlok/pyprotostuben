import abc
import json
import shutil
import subprocess
import typing as t
from collections import OrderedDict
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import pytest
import yaml
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


class DirCaseProvider(CaseProvider):
    # NOTE: case provider constructor has many settings, no need to add extra class.
    def __init__(  # noqa: PLR0913
        self,
        *,
        filename: str,
        plugin: ProtocPlugin,
        deps: t.Optional[t.Sequence[str]] = None,
        parameter: t.Optional[str] = None,
        proto_source: t.Optional[str] = None,
        proto_paths: t.Optional[t.Sequence[str]] = None,
        expected_gen_source: t.Optional[str] = None,
        expected_gen_paths: t.Optional[t.Sequence[str]] = None,
    ) -> None:
        self.__case_dir = Path(filename).parent
        self.__plugin = plugin
        self.__deps = deps
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
        dest = tmp_path / "request"
        dest.mkdir()

        request = read_request_buf(
            source=self.__proto_source,
            dest=dest,
            deps=self.__deps,
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


def read_request_protoc(
    source: Path,
    dest: Path,
    protos: t.Iterable[Path],
) -> CodeGeneratorRequest:
    protoc = shutil.which("protoc")
    if not protoc:
        pytest.fail("can't find protoc")

    # NOTE: need to execute `protoc` that can be installed in local virtual env to get protoc plugin request to pass it
    # to `CodeGeneratorPlugin` in tests.
    echo_result = subprocess.run(  # noqa: S603
        [
            protoc,
            f"-I{source}",
            f"--echo_out={dest}",
            *(str(proto) for proto in protos),
        ],
        stderr=subprocess.PIPE,
        encoding="utf-8",
        check=False,
    )

    if echo_result.returncode != 0:
        pytest.fail(echo_result.stderr)

    with (dest / "request.json").open("r") as echo_out:
        return CodeGeneratorRequest(**json.load(echo_out))


def read_request_buf(
    source: Path,
    dest: Path,
    deps: t.Optional[t.Sequence[str]],
    protos: t.Sequence[Path],
) -> CodeGeneratorRequest:
    buf = shutil.which("buf")
    if not buf:
        pytest.fail("can't find buf")

    create_buf_config(dest, deps)
    create_buf_gen_config(dest)

    with link_to_protos(source, dest, protos):
        # NOTE: need to execute `buf` that can be installed in local virtual env to get buf plugin request to pass it
        # to `CodeGeneratorPlugin` in tests. Before execution need to download deps before `buf generate`
        run_cmd(dest, buf, "dep", "update")
        run_cmd(dest, buf, "generate")

    with (dest / "request.json").open("r") as request_fd:
        return CodeGeneratorRequest(**json.load(request_fd))


def run_cmd(cwd: Path, *args: str) -> None:
    gen_result = subprocess.run(
        args=args,
        cwd=cwd,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        check=False,
    )

    if gen_result.returncode != 0:
        pytest.fail(gen_result.stderr)


def create_buf_gen_config(dest: Path) -> Path:
    buf_gen_config = dest / "buf.gen.yaml"
    with buf_gen_config.open("w") as fd:
        yaml.dump(
            {
                "version": "v2",
                "plugins": [{"local": "protoc-gen-echo", "out": ".", "strategy": "all"}],
            },
            fd,
        )

    return buf_gen_config


def create_buf_config(dest: Path, deps: t.Optional[t.Sequence[str]]) -> Path:
    buf_config = dest / "buf.yaml"

    with buf_config.open("w") as fd:
        yaml.dump(
            {
                "version": "v2",
                "modules": [{"path": "."}],
                "deps": list(deps or ()),
            },
            fd,
        )

    return buf_config


@contextmanager
def link_to_protos(source: Path, dest: Path, protos: t.Sequence[Path]) -> t.Iterator[t.Sequence[Path]]:
    proto_links = OrderedDict([(proto, dest.joinpath(proto.relative_to(source))) for proto in protos])
    try:
        for proto, link in proto_links.items():
            link.symlink_to(proto)

        yield list(proto_links.values())

    finally:
        for link in proto_links.values():
            link.unlink(missing_ok=True)


def load_codegen_response_file_content(source: Path, path: Path) -> CodeGeneratorResponse.File:
    return CodeGeneratorResponse.File(
        name=str(path.relative_to(source)),
        content=path.read_text(),
    )
