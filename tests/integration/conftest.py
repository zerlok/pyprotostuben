import importlib
import inspect
from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest

from tests.integration.case import Case, CaseProvider


@pytest.fixture(
    params=[
        pytest.param(obj, id=f"group={path.name}; name={name}")
        for path in sorted(
            path
            for path in (Path(__file__).parent / "cases").iterdir()
            if path.stem != "__pycache__" and (path / "case.py").is_file()
        )
        for name, obj in inspect.getmembers(importlib.import_module(f"tests.integration.cases.{path.name}.case"))
        if isinstance(obj, CaseProvider)
    ]
)
def case(request: SubRequest, tmp_path: Path) -> Case:
    case_provider: CaseProvider = request.param
    return case_provider.provide(tmp_path)
