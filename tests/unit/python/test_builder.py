import ast
import inspect
import typing as t

import pytest

from pyprotostuben.python.builder2 import ASTBuilder, ModuleASTBuilder, module, package, render
from tests.conftest import parse_ast


def to_module_param(func: t.Callable[[], ModuleASTBuilder]):
    return pytest.param(func(), parse_ast(inspect.getdoc(func)), id=func.__name__)


@to_module_param
def build_empty_module() -> ModuleASTBuilder:
    """"""
    with module("simple") as _:
        return _


@to_module_param
def build_simple_module() -> ModuleASTBuilder:
    """
    import abc
    import builtins
    import dataclasses
    import typing

    class Foo:

        @dataclasses.dataclass(frozen=False, kw_only=False)
        class Bar:
            spam: builtins.int

        bars: typing.Optional[builtins.list[Foo.Bar]]

        def __init__(my_bar: Foo.Bar) -> None:
            self.__my_bar = my_bar

        def do_stuff(x: builtins.int) -> builtins.str:
            self.__some = Foo.Bar(x=x)
            x_str = builtins.str(x)
            return y.__str__()

        @abc.abstractmethod
        def do_buzz() -> builtins.object:
            raise NotImplementedError
    """

    with module("simple") as _:
        with _.class_def("Foo") as foo:
            with _.dataclass_def("Bar") as bar:
                _.field_def("spam", int)

            _.field_def("bars", bar.ref().list().optional())

            with foo.init_self_attrs_def({"my_bar": bar}):
                pass

            with foo.method_def("do_stuff").pos_arg("x", int).returns(str):
                _.assign_stmt(_.attr("self", "__some"), bar.ref().init().kwarg("x", _.attr("x")))
                _.assign_stmt("x_str", _.call(str, [_.attr("x")]))
                _.return_stmt(_.attr("y").attr("__str__").call())

            with foo.method_def("do_buzz").abstract().returns(object).not_implemented():
                pass

        return _


@to_module_param
def build_bar_impl_module() -> ModuleASTBuilder:
    """
    import builtins
    import contextlib
    import simple.foo
    import typing

    class Bar(simple.foo.Foo):
        @typing.override
        @contextlib.contextmanager
        def do_stuff(spam: builtins.str) -> typing.Iterator[builtins.str]:
            ...
    """

    with package("simple") as pkg:
        with pkg.module("foo") as foo:
            with foo.class_def("Foo") as foo_class:
                with (
                    foo_class.method_def("do_stuff")
                    .pos_arg("spam", str)
                    .returns(foo.type_ref(str).context_manager())
                    .abstract()
                    .not_implemented()
                ):
                    pass

        with pkg.module("bar") as bar:
            with bar.class_def("Bar").inherits(foo_class) as _:
                with _.method_def("do_stuff").pos_arg("spam", str).returns(str).context_manager().override().stub():
                    pass

            return bar


@pytest.mark.parametrize(
    ("builder", "expected"),
    [
        build_empty_module,
        build_simple_module,
        build_bar_impl_module,
    ],
)
def test_module_build(builder: ASTBuilder, expected: ast.AST) -> None:
    assert render(builder) == render(expected)
