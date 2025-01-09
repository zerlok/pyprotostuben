import typing as t
from datetime import datetime
from unittest.mock import ANY, MagicMock, call, create_autospec

import pytest

from pyprotostuben.python.visitor.abc import TypeVisitorDecorator
from pyprotostuben.python.visitor.model import ContainerContext, EnumContext, ScalarContext, StructureContext
from pyprotostuben.python.visitor.walker import DefaultTypeWalkerTrait, TypeWalker, TypeWalkerTrait
from tests.stub.structs import User, UserStatus

T = t.TypeVar("T")


@pytest.mark.parametrize(
    ["type_", "expected_calls"],
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
                        type_=t.Literal["foo", "bar"],
                        name=None,
                        values=(
                            EnumContext.ValueInfo(name="foo", value="foo"),
                            EnumContext.ValueInfo(name="bar", value="bar"),
                        ),
                    ),
                    ANY,
                ),
                call.leave_enum(
                    EnumContext(
                        type_=t.Literal["foo", "bar"],
                        name=None,
                        values=(
                            EnumContext.ValueInfo(name="foo", value="foo"),
                            EnumContext.ValueInfo(name="bar", value="bar"),
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
                            EnumContext.ValueInfo(name="UNVERIFIED", value=1),
                            EnumContext.ValueInfo(name="VERIFIED", value=2),
                            EnumContext.ValueInfo(name="BANNED", value=3),
                        ),
                    ),
                    ANY,
                ),
                call.leave_enum(
                    EnumContext(
                        type_=UserStatus,
                        name="UserStatus",
                        values=(
                            EnumContext.ValueInfo(name="UNVERIFIED", value=1),
                            EnumContext.ValueInfo(name="VERIFIED", value=2),
                            EnumContext.ValueInfo(name="BANNED", value=3),
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
                            StructureContext.FieldInfo(name="id", annotation=int),
                            StructureContext.FieldInfo(name="username", annotation=str),
                            StructureContext.FieldInfo(name="created_at", annotation=datetime),
                            StructureContext.FieldInfo(name="status", annotation=UserStatus),
                        ),
                    ),
                    ANY,
                ),
                call.enter_scalar(ScalarContext(type_=int), ANY),
                call.leave_scalar(ScalarContext(type_=int), ANY),
                call.enter_scalar(ScalarContext(type_=str), ANY),
                call.leave_scalar(ScalarContext(type_=str), ANY),
                call.enter_scalar(ScalarContext(type_=datetime), ANY),
                call.leave_scalar(ScalarContext(type_=datetime), ANY),
                call.enter_enum(
                    EnumContext(
                        type_=UserStatus,
                        name="UserStatus",
                        values=(
                            EnumContext.ValueInfo(name="UNVERIFIED", value=1),
                            EnumContext.ValueInfo(name="VERIFIED", value=2),
                            EnumContext.ValueInfo(name="BANNED", value=3),
                        ),
                    ),
                    ANY,
                ),
                call.leave_enum(
                    EnumContext(
                        type_=UserStatus,
                        name="UserStatus",
                        values=(
                            EnumContext.ValueInfo(name="UNVERIFIED", value=1),
                            EnumContext.ValueInfo(name="VERIFIED", value=2),
                            EnumContext.ValueInfo(name="BANNED", value=3),
                        ),
                    ),
                    ANY,
                ),
                call.leave_structure(
                    StructureContext(
                        type_=User,
                        name="User",
                        fields=(
                            StructureContext.FieldInfo(name="id", annotation=int),
                            StructureContext.FieldInfo(name="username", annotation=str),
                            StructureContext.FieldInfo(name="created_at", annotation=datetime),
                            StructureContext.FieldInfo(name="status", annotation=UserStatus),
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

    assert set(mc.args[-1] for mc in nested.method_calls) == {context}


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
