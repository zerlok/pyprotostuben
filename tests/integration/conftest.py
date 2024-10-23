import typing as t
import importlib
from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest

from tests.integration.case import Case, CaseProvider

CASES_DIR = Path(__file__).parent / "cases"
CASE_PATHS = sorted(path for path in CASES_DIR.iterdir() if (path / "case.py").is_file())


@pytest.fixture(
    params=[
        pytest.param(obj, id=f"{path.name}/{name}")
        for path in CASE_PATHS
        for name, obj in importlib.import_module(f"tests.integration.cases.{path.name}.case").__dict__.items()
        if isinstance(obj, CaseProvider)
    ]
)
def case(request: SubRequest, tmp_path: Path) -> Case:
    case_provider: CaseProvider = request.param
    return case_provider.provide(tmp_path)
