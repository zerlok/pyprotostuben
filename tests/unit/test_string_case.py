import pytest

from pyprotostuben.string_case import camel2snake, snake2camel


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(
            "",
            "",
        ),
        pytest.param(
            "hello-world",
            "hello-world",
        ),
        pytest.param(
            "hello_world",
            "hello_world",
        ),
        pytest.param(
            "HelloWorld",
            "hello_world",
        ),
        pytest.param(
            "ABCMeta",
            "abc_meta",
        ),
        pytest.param(
            "FooBarBaz",
            "foo_bar_baz",
        ),
        pytest.param(
            "__FooBarBaz",
            "__foo_bar_baz",
        ),
    ],
)
def test_camel2snake_ok(value: str, expected: str) -> None:
    assert camel2snake(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(
            "",
            "",
        ),
        pytest.param(
            "hello_world",
            "HelloWorld",
        ),
        pytest.param(
            "HelloWorld",
            "HelloWorld",
        ),
        pytest.param(
            "abc_meta",
            "AbcMeta",
        ),
        pytest.param(
            "foo_bar_baz",
            "FooBarBaz",
        ),
        pytest.param(
            "__foo_bar_baz",
            "__FooBarBaz",
        ),
    ],
)
def test_snake2camel_ok(value: str, expected: str) -> None:
    assert snake2camel(value) == expected
