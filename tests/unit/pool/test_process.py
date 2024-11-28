import os
import time
import typing as t
from collections import Counter
from datetime import timedelta

import pytest

from pyprotostuben.pool.process import MultiProcessPool


@pytest.mark.parametrize(
    ("values", "expected_results"),
    [
        pytest.param([], []),
        pytest.param([42], ["42"]),
        pytest.param(list(range(3)), [str(i) for i in range(3)]),
        pytest.param(list(range(100)), [str(i) for i in range(100)]),
    ],
)
def test_multi_process_pool_can_be_run(
    pool: MultiProcessPool,
    values: t.Collection[object],
    expected_results: t.Collection[str],
) -> None:
    assert Counter(pool.run(str, values)) == Counter(expected_results)


@pytest.mark.parametrize(
    "delays",
    [
        pytest.param(
            [timedelta(milliseconds=i * 20) for i in reversed(range(os.cpu_count() or 0))],
        ),
    ],
)
def test_multi_process_pool_return_results_as_ready(
    pool: MultiProcessPool,
    delays: t.Sequence[timedelta],
) -> None:
    assert list(pool.run(calc_stuff, delays)) == sorted(delays)


@pytest.fixture
def pool() -> t.Iterator[MultiProcessPool]:
    with MultiProcessPool.setup() as pool:
        yield pool


def calc_stuff(delay: timedelta) -> timedelta:
    time.sleep(delay.total_seconds())  # simulate long CPU bound task
    return delay
