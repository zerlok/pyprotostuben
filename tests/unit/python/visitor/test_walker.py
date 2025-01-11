import typing as t
from datetime import datetime
from unittest.mock import ANY, MagicMock, call, create_autospec

import pytest

from pyprotostuben.python.visitor.abc import TypeVisitorDecorator
from pyprotostuben.python.visitor.model import (
    ContainerContext,
    EnumContext,
    EnumValueContext,
    ScalarContext,
    StructureContext,
    StructureFieldContext,
)
from pyprotostuben.python.visitor.walker import DefaultTypeWalkerTrait, TypeWalker, TypeWalkerTrait
from tests.stub.structs import User, UserStatus

T = t.TypeVar("T")


@pytest.mark.parametrize(
    ("type_", "expected_calls"),
    [
        pytest.param(
            None,
            [
                call.enter_scalar(ScalarContext(type_=type(None)), ANY),
                call.leave_scalar(ScalarContext(type_=type(None)), ANY),
            ],
            id="None",
        ),
        pytest.param(
            int,
            [
                call.enter_scalar(ScalarContext(type_=int), ANY),
                call.leave_scalar(ScalarContext(type_=int), ANY),
            ],
            id="int",
        ),
        pytest.param(
            str,
            [
                call.enter_scalar(ScalarContext(type_=str), ANY),
                call.leave_scalar(ScalarContext(type_=str), ANY),
            ],
            id="str",
        ),
        pytest.param(
            list[str],
            [
                call.enter_container(ContainerContext(type_=list[str], origin=list, inners=(str,)), ANY),
                call.enter_scalar(ScalarContext(type_=str), ANY),
                call.leave_scalar(ScalarContext(type_=str), ANY),
                call.leave_container(ContainerContext(type_=list[str], origin=list, inners=(str,)), ANY),
            ],
            id="list[str]",
        ),
        pytest.param(
            t.Optional[list[list[str]]],
            [
                call.enter_container(
                    ContainerContext(
                        type_=t.cast(type[object], t.Optional[list[list[str]]]),
                        origin=t.cast(type[object], t.Union),
                        inners=(
                            list[list[str]],
                            type(None),
                        ),
                    ),
                    ANY,
                ),
                call.enter_container(ContainerContext(type_=list[list[str]], origin=list, inners=(list[str],)), ANY),
                call.enter_container(ContainerContext(type_=list[str], origin=list, inners=(str,)), ANY),
                call.enter_scalar(ScalarContext(type_=str), ANY),
                call.leave_scalar(ScalarContext(type_=str), ANY),
                call.leave_container(ContainerContext(type_=list[str], origin=list, inners=(str,)), ANY),
                call.leave_container(ContainerContext(type_=list[list[str]], origin=list, inners=(list[str],)), ANY),
                call.enter_scalar(ScalarContext(type_=type(None)), ANY),
                call.leave_scalar(ScalarContext(type_=type(None)), ANY),
                call.leave_container(
                    ContainerContext(
                        type_=t.cast(type[object], t.Optional[list[list[str]]]),
                        origin=t.cast(type[object], t.Union),
                        inners=(
                            list[list[str]],
                            type(None),
                        ),
                    ),
                    ANY,
                ),
            ],
            id="t.Optional[list[list[str]]]",
        ),
        pytest.param(
            tuple[list[int], list[str]],
            [
                call.enter_container(
                    ContainerContext(type_=tuple[list[int], list[str]], origin=tuple, inners=(list[int], list[str])),
                    ANY,
                ),
                call.enter_container(ContainerContext(type_=list[int], origin=list, inners=(int,)), ANY),
                call.enter_scalar(ScalarContext(type_=int), ANY),
                call.leave_scalar(ScalarContext(type_=int), ANY),
                call.leave_container(ContainerContext(type_=list[int], origin=list, inners=(int,)), ANY),
                call.enter_container(ContainerContext(type_=list[str], origin=list, inners=(str,)), ANY),
                call.enter_scalar(ScalarContext(type_=str), ANY),
                call.leave_scalar(ScalarContext(type_=str), ANY),
                call.leave_container(ContainerContext(type_=list[str], origin=list, inners=(str,)), ANY),
                call.leave_container(
                    ContainerContext(type_=tuple[list[int], list[str]], origin=tuple, inners=(list[int], list[str])),
                    ANY,
                ),
            ],
            id="tuple[list[int], list[str]]",
        ),
        pytest.param(
            t.Literal["foo", "bar"],
            [
                call.enter_enum(
                    EnumContext(
                        type_=t.cast(type[object], t.Literal["foo", "bar"]),
                        name=None,
                        values=(
                            EnumValueContext(type_=str, name="foo", value="foo"),
                            EnumValueContext(type_=str, name="bar", value="bar"),
                        ),
                    ),
                    ANY,
                ),
                call.enter_enum_value(EnumValueContext(type_=str, name="foo", value="foo"), ANY),
                call.leave_enum_value(EnumValueContext(type_=str, name="foo", value="foo"), ANY),
                call.enter_enum_value(EnumValueContext(type_=str, name="bar", value="bar"), ANY),
                call.leave_enum_value(EnumValueContext(type_=str, name="bar", value="bar"), ANY),
                call.leave_enum(
                    EnumContext(
                        type_=t.cast(type[object], t.Literal["foo", "bar"]),
                        name=None,
                        values=(
                            EnumValueContext(type_=str, name="foo", value="foo"),
                            EnumValueContext(type_=str, name="bar", value="bar"),
                        ),
                    ),
                    ANY,
                ),
            ],
            id="Literal[foo, bar]",
        ),
        pytest.param(
            UserStatus,
            [
                call.enter_enum(
                    EnumContext(
                        type_=UserStatus,
                        name="UserStatus",
                        values=(
                            EnumValueContext(type_=UserStatus, name="UNVERIFIED", value=1),
                            EnumValueContext(type_=UserStatus, name="VERIFIED", value=2),
                            EnumValueContext(type_=UserStatus, name="BANNED", value=3),
                        ),
                    ),
                    ANY,
                ),
                call.enter_enum_value(EnumValueContext(type_=UserStatus, name="UNVERIFIED", value=1), ANY),
                call.leave_enum_value(EnumValueContext(type_=UserStatus, name="UNVERIFIED", value=1), ANY),
                call.enter_enum_value(EnumValueContext(type_=UserStatus, name="VERIFIED", value=2), ANY),
                call.leave_enum_value(EnumValueContext(type_=UserStatus, name="VERIFIED", value=2), ANY),
                call.enter_enum_value(EnumValueContext(type_=UserStatus, name="BANNED", value=3), ANY),
                call.leave_enum_value(EnumValueContext(type_=UserStatus, name="BANNED", value=3), ANY),
                call.leave_enum(
                    EnumContext(
                        type_=UserStatus,
                        name="UserStatus",
                        values=(
                            EnumValueContext(type_=UserStatus, name="UNVERIFIED", value=1),
                            EnumValueContext(type_=UserStatus, name="VERIFIED", value=2),
                            EnumValueContext(type_=UserStatus, name="BANNED", value=3),
                        ),
                    ),
                    ANY,
                ),
            ],
            id="UserStatus",
        ),
        pytest.param(
            User,
            [
                call.enter_structure(
                    StructureContext(
                        type_=User,
                        name="User",
                        fields=(
                            StructureFieldContext(type_=int, name="id", annotation=int),
                            StructureFieldContext(type_=str, name="username", annotation=str),
                            StructureFieldContext(type_=datetime, name="created_at", annotation=datetime),
                            StructureFieldContext(type_=UserStatus, name="status", annotation=UserStatus),
                        ),
                    ),
                    ANY,
                ),
                call.enter_structure_field(StructureFieldContext(type_=int, name="id", annotation=int), ANY),
                call.enter_scalar(ScalarContext(type_=int), ANY),
                call.leave_scalar(ScalarContext(type_=int), ANY),
                call.leave_structure_field(StructureFieldContext(type_=int, name="id", annotation=int), ANY),
                call.enter_structure_field(StructureFieldContext(type_=str, name="username", annotation=str), ANY),
                call.enter_scalar(ScalarContext(type_=str), ANY),
                call.leave_scalar(ScalarContext(type_=str), ANY),
                call.leave_structure_field(StructureFieldContext(type_=str, name="username", annotation=str), ANY),
                call.enter_structure_field(
                    StructureFieldContext(type_=datetime, name="created_at", annotation=datetime), ANY
                ),
                call.enter_scalar(ScalarContext(type_=datetime), ANY),
                call.leave_scalar(ScalarContext(type_=datetime), ANY),
                call.leave_structure_field(
                    StructureFieldContext(type_=datetime, name="created_at", annotation=datetime), ANY
                ),
                call.enter_structure_field(
                    StructureFieldContext(type_=UserStatus, name="status", annotation=UserStatus), ANY
                ),
                call.enter_enum(
                    EnumContext(
                        type_=UserStatus,
                        name="UserStatus",
                        values=(
                            EnumValueContext(type_=UserStatus, name="UNVERIFIED", value=1),
                            EnumValueContext(type_=UserStatus, name="VERIFIED", value=2),
                            EnumValueContext(type_=UserStatus, name="BANNED", value=3),
                        ),
                    ),
                    ANY,
                ),
                call.enter_enum_value(EnumValueContext(type_=UserStatus, name="UNVERIFIED", value=1), ANY),
                call.leave_enum_value(EnumValueContext(type_=UserStatus, name="UNVERIFIED", value=1), ANY),
                call.enter_enum_value(EnumValueContext(type_=UserStatus, name="VERIFIED", value=2), ANY),
                call.leave_enum_value(EnumValueContext(type_=UserStatus, name="VERIFIED", value=2), ANY),
                call.enter_enum_value(EnumValueContext(type_=UserStatus, name="BANNED", value=3), ANY),
                call.leave_enum_value(EnumValueContext(type_=UserStatus, name="BANNED", value=3), ANY),
                call.leave_enum(
                    EnumContext(
                        type_=UserStatus,
                        name="UserStatus",
                        values=(
                            EnumValueContext(type_=UserStatus, name="UNVERIFIED", value=1),
                            EnumValueContext(type_=UserStatus, name="VERIFIED", value=2),
                            EnumValueContext(type_=UserStatus, name="BANNED", value=3),
                        ),
                    ),
                    ANY,
                ),
                call.leave_structure_field(
                    StructureFieldContext(type_=UserStatus, name="status", annotation=UserStatus), ANY
                ),
                call.leave_structure(
                    StructureContext(
                        type_=User,
                        name="User",
                        fields=(
                            StructureFieldContext(type_=int, name="id", annotation=int),
                            StructureFieldContext(type_=str, name="username", annotation=str),
                            StructureFieldContext(type_=datetime, name="created_at", annotation=datetime),
                            StructureFieldContext(type_=UserStatus, name="status", annotation=UserStatus),
                        ),
                    ),
                    ANY,
                ),
            ],
            id="User",
        ),
    ],
)
def test_type_walker_nested_method_calls_ok(
    type_walker: TypeWalker[T],
    context: T,
    type_: t.Optional[type[object]],
    nested: MagicMock,
    expected_calls: t.Sequence[MagicMock],
) -> None:
    type_walker.walk(type_, context)

    assert nested.method_calls == expected_calls


@pytest.mark.parametrize(
    "type_",
    [
        pytest.param(
            int,
            id="int",
        ),
        pytest.param(
            tuple[list[int], list[str]],
            id="tuple[list[int], list[str]]",
        ),
        pytest.param(
            User,
            id="User",
        ),
        pytest.param(
            UserStatus,
            id="UserStatus",
        ),
    ],
)
def test_type_walker_propagates_same_context(
    type_walker: TypeWalker[T],
    context: T,
    type_: t.Optional[type[object]],
    nested: MagicMock,
) -> None:
    type_walker.walk(type_, context)

    assert {mc.args[-1] for mc in nested.method_calls} == {context}


@pytest.fixture
def trait() -> TypeWalkerTrait:
    return DefaultTypeWalkerTrait()


@pytest.fixture
def type_walker(trait: TypeWalkerTrait, nested: TypeVisitorDecorator[T]) -> TypeWalker[T]:
    return TypeWalker(trait, nested)


@pytest.fixture
def nested() -> TypeVisitorDecorator[object]:
    return t.cast(TypeVisitorDecorator[object], create_autospec(TypeVisitorDecorator))


@pytest.fixture
def context() -> object:
    return object()
