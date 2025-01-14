import ast
import typing as t
from dataclasses import dataclass, field

import pytest

from pyprotostuben.codegen.model import DataclassModelFactory, ModelASTBuilder, ModelFactory, PydanticModelFactory
from pyprotostuben.python.builder2 import Expr, ModuleASTBuilder, package, render
from pyprotostuben.python.info import PackageInfo
from tests.conftest import parse_module_ast
from tests.stub.structs import ChatRoom, User


@dataclass(frozen=True, kw_only=True)
class BaseCase:
    model_factory_type: t.Union[type[DataclassModelFactory], type[PydanticModelFactory]] = PydanticModelFactory
    model_module_name: str = "model"


@dataclass(frozen=True, kw_only=True)
class CreateCase(BaseCase):
    name: str
    fields: t.Mapping[str, type[object]]
    defaults: t.Mapping[str, object] = field(default_factory=dict)
    doc: t.Optional[str] = None
    expected: ast.Module


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(
            CreateCase(
                model_factory_type=PydanticModelFactory,
                name="Foo",
                fields={
                    "spam": int,
                    "eggs": User,
                },
                expected=parse_module_ast("""
                    import builtins
                    import datetime
                    import pydantic
                    import typing

                    class User(pydantic.BaseModel):
                        id: builtins.int
                        username: builtins.str
                        created_at: datetime.datetime
                        status: typing.Literal["UNVERIFIED", "VERIFIED", "BANNED"]

                    class Foo(pydantic.BaseModel):
                        spam: builtins.int
                        eggs: User
                """),
            ),
            id="pydantic model factory",
        ),
        pytest.param(
            CreateCase(
                model_factory_type=DataclassModelFactory,
                name="Foo",
                fields={
                    "spam": str,
                    "eggs": User,
                },
                expected=parse_module_ast("""
                    import builtins
                    import dataclasses
                    import datetime
                    import typing

                    @dataclasses.dataclass(frozen=True, kw_only=True)
                    class User:
                        id: builtins.int
                        username: builtins.str
                        created_at: datetime.datetime
                        status: typing.Literal['UNVERIFIED', 'VERIFIED', 'BANNED']

                    @dataclasses.dataclass(frozen=True, kw_only=True)
                    class Foo:
                        spam: builtins.str
                        eggs: User
                """),
            ),
            id="dataclass model factory",
        ),
    ],
)
def test_model_ast_builder_create_returns_expected_class_def(
    model_module_builder: ModuleASTBuilder,
    model_ast_builder: ModelASTBuilder,
    case: CreateCase,
) -> None:
    model_ast_builder.update(case.fields.values())
    model_ast_builder.create_def(name=case.name, fields=case.fields, doc=case.doc)

    assert render(model_module_builder) == render(case.expected)


@dataclass(frozen=True, kw_only=True)
class AssignExprCase(BaseCase):
    source: Expr
    target: type[object]
    mode: t.Literal["original", "model"]
    expected: ast.Module


@pytest.mark.parametrize(
    "case",
    [
        pytest.param(
            AssignExprCase(
                source=ast.Name(id="my_source_var"),
                target=str,
                mode="model",
                expected=parse_module_ast("my_source_var"),
            ),
            id="str scalar model",
        ),
        pytest.param(
            AssignExprCase(
                source=ast.Attribute(value=ast.Attribute(value=ast.Name(id="my"), attr="source"), attr="var"),
                target=str,
                mode="model",
                expected=parse_module_ast("my.source.var"),
            ),
            id="nested attribute",
        ),
        pytest.param(
            AssignExprCase(
                source=ast.Name(id="my_source_var"),
                target=str,
                mode="original",
                expected=parse_module_ast("my_source_var"),
            ),
            id="str scalar original",
        ),
        pytest.param(
            AssignExprCase(
                source=ast.Name(id="user_data"),
                target=User,
                mode="model",
                expected=parse_module_ast("""
                    import tests.integration.test_model.model

                    tests.integration.test_model.model.User(
                        id=user_data.id,
                        username=user_data.username,
                        created_at=user_data.created_at,
                        status=user_data.status.name,
                    )
                """),
            ),
            id="user model",
        ),
        pytest.param(
            AssignExprCase(
                source=ast.Name(id="maybe_user"),
                target=t.Optional[User],  # type: ignore[arg-type]
                mode="model",
                expected=parse_module_ast("""
                    import tests.integration.test_model.model

                    tests.integration.test_model.model.User(
                        id=maybe_user.id,
                        username=maybe_user.username,
                        created_at=maybe_user.created_at,
                        status=maybe_user.status.name,
                    ) if maybe_user is not None else None
                """),
            ),
            id="optional user model",
        ),
        pytest.param(
            AssignExprCase(
                source=ast.Name(id="users"),
                target=list[User],
                mode="model",
                expected=parse_module_ast("""
                    import tests.integration.test_model.model

                    [
                        tests.integration.test_model.model.User(
                            id=users_item.id,
                            username=users_item.username,
                            created_at=users_item.created_at,
                            status=users_item.status.name,
                        )
                        for users_item in users
                    ]
                """),
            ),
            id="list user model",
        ),
        pytest.param(
            AssignExprCase(
                source=ast.Name(id="users"),
                target=dict[str, User],
                mode="model",
                expected=parse_module_ast("""
                    import tests.integration.test_model.model

                    {
                        users_key: tests.integration.test_model.model.User(
                            id=users_value.id,
                            username=users_value.username,
                            created_at=users_value.created_at,
                            status=users_value.status.name,
                        )
                        for users_key, users_value in users.items()
                    }
                """),
            ),
            id="dict user model",
        ),
        pytest.param(
            AssignExprCase(
                source=ast.Name(id="data"),
                target=ChatRoom,
                mode="model",
                expected=parse_module_ast("""
                import tests.integration.test_model.model

                tests.integration.test_model.model.ChatRoom(
                    name=data.name,
                    host=tests.integration.test_model.model.HostInfo(
                        domain=data.host.domain,
                        user=tests.integration.test_model.model.SuperUser(
                            id=data.host.user.id,
                            username=data.host.user.username,
                            created_at=data.host.user.created_at,
                            status=data.host.user.status.name,
                            super_created_at=data.host.user.super_created_at,
                        ) if data.host.user is not None else None,
                    ),
                    users=[
                        tests.integration.test_model.model.User(
                            id=data_users_item.id,
                            username=data_users_item.username,
                            created_at=data_users_item.created_at,
                            status=data_users_item.status.name,
                        )
                        for data_users_item in data.users
                    ],
                    tags={data_tags_item for data_tags_item in data.tags},
                )
                """),
            ),
            id="chat room model",
        ),
        pytest.param(
            AssignExprCase(
                source=ast.Name(id="orig"),
                target=ChatRoom,
                mode="original",
                expected=parse_module_ast("""
                import tests.stub.structs

                tests.stub.structs.ChatRoom(
                    name=orig.name,
                    host=tests.stub.structs.HostInfo(
                        domain=orig.host.domain,
                        user=tests.stub.structs.SuperUser(
                            id=orig.host.user.id,
                            username=orig.host.user.username,
                            created_at=orig.host.user.created_at,
                            status=orig.host.user.status.name,
                            super_created_at=orig.host.user.super_created_at,
                        ) if orig.host.user is not None else None,
                    ),
                    users=[
                        tests.stub.structs.User(
                            id=orig_users_item.id,
                            username=orig_users_item.username,
                            created_at=orig_users_item.created_at,
                            status=orig_users_item.status.name,
                        )
                        for orig_users_item in orig.users
                    ],
                    tags={orig_tags_item for orig_tags_item in orig.tags},
                )
                """),
            ),
            id="chat room original",
        ),
    ],
)
def test_model_ast_builder_assign_stmt_returns_expected_stmt(
    model_ast_builder: ModelASTBuilder,
    other_module_builder: ModuleASTBuilder,
    case: AssignExprCase,
) -> None:
    model_ast_builder.update([case.target])

    other_module_builder.append(
        model_ast_builder.assign_expr(case.source, case.target, case.mode, other_module_builder)
    )

    assert render(other_module_builder) == render(case.expected)


@pytest.fixture
def model_ast_builder(model_module_builder: ModuleASTBuilder, model_factory: ModelFactory) -> ModelASTBuilder:
    return ModelASTBuilder(model_module_builder, model_factory)


@pytest.fixture
def model_module_builder(stub_package_info: PackageInfo, case: BaseCase) -> t.Iterator[ModuleASTBuilder]:
    with package(stub_package_info) as pkg, pkg.module(case.model_module_name) as mod:
        yield mod


@pytest.fixture
def other_module_builder(stub_package_info: PackageInfo) -> t.Iterator[ModuleASTBuilder]:
    with package(stub_package_info) as pkg, pkg.module("other") as mod:
        yield mod


@pytest.fixture
def model_factory(case: BaseCase) -> ModelFactory:
    return case.model_factory_type()
