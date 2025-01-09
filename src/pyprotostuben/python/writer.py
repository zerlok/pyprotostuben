import ast
import typing as t
from pathlib import Path

from pyprotostuben.python.info import ModuleInfo


class Writer:
    def __init__(self, dest: t.Optional[Path] = None) -> None:
        self.__dest = dest

    def write(self, info: ModuleInfo, content: ast.Module, kind: t.Literal["regular", "stub"] = "regular") -> Path:
        path = info.file if kind == "regular" else info.stub_file
        if self.__dest is not None:
            path = self.__dest.joinpath(path)

        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as fd:
            fd.write(ast.unparse(content))

        return path
