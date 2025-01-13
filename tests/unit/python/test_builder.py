import ast
import inspect
import typing as t

import pytest
from _pytest.mark import ParameterSet

from pyprotostuben.python.builder2 import ModuleASTBuilder, module, package, render
from tests.conftest import parse_ast


def to_module_param(func: t.Callable[[], ModuleASTBuilder]) -> ParameterSet:
    expected_code = inspect.getdoc(func)
    assert expected_code is not None
    return pytest.param(func(), parse_ast(expected_code), id=func.__name__)


@to_module_param
def build_empty_module() -> ModuleASTBuilder:
    """"""
    with module("simple") as mod:
        return mod


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

        bars: typing.Optional[builtins.list[Bar]]

        def __init__(self, my_bar: Foo.Bar) -> None:
            self.__my_bar = my_bar

        def do_stuff(self, x: builtins.int) -> builtins.str:
            self.__some = Foo.Bar(x=x)
            x_str = builtins.str(x)
            return y.__str__()

        @abc.abstractmethod
        def do_buzz(self) -> builtins.object:
            raise NotImplementedError
    """

    with (
        module("simple") as mod,
        mod.class_def("Foo") as foo,
    ):
        with mod.class_def("Bar").dataclass() as bar:
            mod.field_def("spam", int)

        mod.field_def("bars", bar.ref().list().optional())

        with foo.init_self_attrs_def({"my_bar": bar}):
            pass

        with foo.method_def("do_stuff").pos_arg("x", int).returns(str):
            mod.assign_stmt(mod.attr("self", "__some"), bar.ref().init().kwarg("x", mod.attr("x")))
            mod.assign_stmt("x_str", mod.call(str, [mod.attr("x")]))
            mod.return_stmt(mod.attr("y").attr("__str__").call())

        with foo.method_def("do_buzz").abstract().returns(object).not_implemented():
            pass

        return mod


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
        def do_stuff(self, spam: builtins.str) -> typing.Iterator[builtins.str]:
            ...
    """

    with (
        package("simple") as pkg,
        pkg.module("foo") as foo,
        foo.class_def("Foo") as foo_class,
        foo_class.method_def("do_stuff")
        .pos_arg("spam", str)
        .returns(foo.type_(str).context_manager())
        .abstract()
        .not_implemented(),
    ):
        pass

    with (
        pkg.module("bar") as bar,
        bar.class_def("Bar").inherits(foo_class) as _,
        _.method_def("do_stuff").pos_arg("spam", str).returns(str).context_manager().override().stub(),
    ):
        return bar


@pytest.mark.parametrize(
    ("builder", "expected"),
    [
        build_empty_module,
        build_simple_module,
        build_bar_impl_module,
    ],
)
def test_module_build(builder: ModuleASTBuilder, expected: ast.Module) -> None:
    assert render(builder) == render(expected)
