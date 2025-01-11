import ast
import typing as t
from dataclasses import dataclass, field, replace

import pytest

from pyprotostuben.codegen.model import DataclassModelFactory, ModelDefBuilder, ModelFactory, PydanticModelFactory
from pyprotostuben.python.builder import ModuleASTBuilder, TypeRef
from pyprotostuben.python.info import ModuleInfo, PackageInfo, TypeInfo
from tests.conftest import parse_ast
from tests.stub.structs import ChatRoom, User, UserStatus


@dataclass(frozen=True, kw_only=True)
class CreateCase:
    expected: ast.AST
    name: str
    fields: t.Mapping[str, TypeRef]
    defaults: t.Mapping[str, object] = field(default_factory=dict)
    nested: t.Sequence[ast.stmt] = field(default_factory=list)
    doc: t.Optional[str] = None


@pytest.mark.parametrize(
    ("model_factory_type", "case"),
    [
        pytest.param(
            PydanticModelFactory,
            CreateCase(
                expected=parse_ast("""
                import builtins
                import model
                import pydantic

                class Foo(pydantic.BaseModel):
                    spam: builtins.int
                    eggs: model.EggBucket
                """),
                name="Foo",
                fields={
                    "spam": TypeInfo.from_type(int),
                    "eggs": TypeInfo.build(ModuleInfo(None, "model"), "EggBucket"),
                },
            ),
            id="pydantic model factory",
        ),
        pytest.param(
            DataclassModelFactory,
            CreateCase(
                expected=parse_ast("""
                import builtins
                import dataclasses
                import model

                @dataclasses.dataclass(frozen=True, kw_only=True)
                class Foo:
                    spam: builtins.str
                    eggs: model.EggBucket
                """),
                name="Foo",
                fields={
                    "spam": TypeInfo.from_type(str),
                    "eggs": TypeInfo.build(ModuleInfo(None, "model"), "EggBucket"),
                },
            ),
            id="dataclass model factory",
        ),
    ],
)
def test_model_def_builder_create_returns_expected_class_def(
    model_module_builder: ModuleASTBuilder,
    case: CreateCase,
    model_def_builder: ModelDefBuilder,
) -> None:
    model_module_builder.append(
        model_def_builder.create(
            name=case.name,
            fields=case.fields,
            defaults=case.defaults,
            nested=case.nested,
            doc=case.doc,
        )
    )

    assert ast.unparse(model_module_builder.build()) == ast.unparse(case.expected)


@pytest.mark.parametrize(
    ("model_factory_type", "model_module_info", "types", "orig_type", "expected_type_info"),
    [
        pytest.param(
            PydanticModelFactory,
            ModuleInfo(None, "model"),
            [str],
            str,
            TypeInfo.from_type(str),
            id="str",
        ),
        pytest.param(
            PydanticModelFactory,
            ModuleInfo(None, "model"),
            [User],
            User,
            TypeInfo.build(ModuleInfo(None, "model"), "User"),
            id="user model",
        ),
    ],
)
def test_model_def_builder_resolve_returns_expected_type_info(
    types: t.Collection[type[object]],
    orig_type: type[object],
    expected_type_info: TypeInfo,
    model_def_builder: ModelDefBuilder,
) -> None:
    model_def_builder.update(types)

    assert model_def_builder.resolve(orig_type) == expected_type_info


@pytest.mark.parametrize(
    ("model_factory_type", "model_module_info", "types", "orig_type", "expected_expr"),
    [
        pytest.param(
            PydanticModelFactory,
            ModuleInfo(None, "model"),
            [UserStatus],
            UserStatus,
            parse_ast("""typing.Literal["UNVERIFIED", "VERIFIED", "BANNED"]"""),
            id="user status",
        ),
    ],
)
def test_model_def_builder_resolve_returns_expected_expr(
    types: t.Collection[type[object]],
    orig_type: type[object],
    expected_expr: ast.expr,
    model_def_builder: ModelDefBuilder,
) -> None:
    model_def_builder.update(types)

    resolved = model_def_builder.resolve(orig_type)
    assert isinstance(resolved, ast.expr)
    assert ast.unparse(resolved) == ast.unparse(expected_expr)


@pytest.mark.parametrize(
    ("model_factory_type", "model_module_info", "source", "type_", "mode", "expected"),
    [
        pytest.param(
            PydanticModelFactory,
            ModuleInfo(None, "model"),
            ast.Name(id="my_source_var"),
            str,
            "model",
            parse_ast("my_source_var"),
            id="str scalar model",
        ),
        pytest.param(
            PydanticModelFactory,
            ModuleInfo(None, "model"),
            ast.Attribute(value=ast.Attribute(value=ast.Name(id="my"), attr="source"), attr="var"),
            str,
            "model",
            ast.Attribute(value=ast.Attribute(value=ast.Name(id="my"), attr="source"), attr="var"),
            id="nested attribute",
        ),
        pytest.param(
            PydanticModelFactory,
            ModuleInfo(None, "model"),
            ast.Name(id="my_source_var"),
            str,
            "original",
            parse_ast("my_source_var"),
            id="str scalar original",
        ),
        pytest.param(
            PydanticModelFactory,
            ModuleInfo(None, "model"),
            "user_data",
            User,
            "model",
            parse_ast("""
            import model

            model.User(
                id=user_data.id,
                username=user_data.username,
                created_at=user_data.created_at,
                status=user_data.status.name,
            )
            """),
            id="user model",
        ),
        pytest.param(
            PydanticModelFactory,
            ModuleInfo(None, "model"),
            ast.Name(id="maybe_user"),
            t.Optional[User],
            "model",
            parse_ast("""
            import model

            model.User(
                id=maybe_user.id,
                username=maybe_user.username,
                created_at=maybe_user.created_at,
                status=maybe_user.status.name,
            ) if maybe_user is not None else None
            """),
        ),
        pytest.param(
            PydanticModelFactory,
            ModuleInfo(None, "model"),
            ast.Name(id="users"),
            list[User],
            "model",
            parse_ast("""
            import model

            [
                model.User(
                    id=users_item.id,
                    username=users_item.username,
                    created_at=users_item.created_at,
                    status=users_item.status.name,
                )
                for users_item in users
            ]
            """),
            id="list user model",
        ),
        pytest.param(
            PydanticModelFactory,
            ModuleInfo(None, "pydantic_models"),
            ast.Name(id="user_map"),
            dict[int, User],
            "model",
            parse_ast("""
            import pydantic_models

            {
                user_map_key: pydantic_models.User(
                    id=user_map_value.id,
                    username=user_map_value.username,
                    created_at=user_map_value.created_at,
                    status=user_map_value.status.name,
                )
                for user_map_key, user_map_value in user_map.items()
            }
            """),
            id="dict user model",
        ),
        pytest.param(
            PydanticModelFactory,
            ModuleInfo(None, "model"),
            ast.Name(id="data"),
            ChatRoom,
            "model",
            parse_ast("""
            import model

            model.ChatRoom(
                name=data.name,
                host=model.HostInfo(
                    domain=data.host.domain,
                    user=model.SuperUser(
                        id=data.host.user.id,
                        username=data.host.user.username,
                        created_at=data.host.user.created_at,
                        status=data.host.user.status.name,
                        super_created_at=data.host.user.super_created_at,
                    )
                ),
                users=[
                    model.User(
                        id=data_users_item.id,
                        username=data_users_item.username,
                        created_at=data_users_item.created_at,
                        status=data_users_item.status.name,
                    )
                    for data_users_item in data.users
                ],
            )
            """),
            id="chat room model",
        ),
        pytest.param(
            PydanticModelFactory,
            ModuleInfo(None, "model"),
            ast.Name(id="pydantic_value"),
            ChatRoom,
            "original",
            parse_ast("""
            import tests.stub.structs

            tests.stub.structs.ChatRoom(
                name=pydantic_value.name,
                host=tests.stub.structs.HostInfo(
                    domain=pydantic_value.host.domain,
                    user=tests.stub.structs.SuperUser(
                        id=pydantic_value.host.user.id,
                        username=pydantic_value.host.user.username,
                        created_at=pydantic_value.host.user.created_at,
                        status=pydantic_value.host.user.status.name,
                        super_created_at=pydantic_value.host.user.super_created_at,
                    )
                ),
                users=[
                    tests.stub.structs.User(
                        id=pydantic_value_users_item.id,
                        username=pydantic_value_users_item.username,
                        created_at=pydantic_value_users_item.created_at,
                        status=pydantic_value_users_item.status.name,
                    )
                    for pydantic_value_users_item in pydantic_value.users
                ],
            )
            """),
            id="chat room original",
        ),
    ],
)
def test_model_def_builder_assign_stmt_returns_expected_stmt(
    source: ast.expr,
    type_: type[object],
    mode: t.Literal["original", "model"],
    expected: ast.AST,
    model_def_builder: ModelDefBuilder,
    other_module_builder: ModuleASTBuilder,
) -> None:
    model_def_builder.update([type_])

    other_module_builder.append(ast.Expr(model_def_builder.assign_expr(source, type_, mode, other_module_builder)))

    assert ast.unparse(other_module_builder.build()) == ast.unparse(expected)


@pytest.fixture
def model_def_builder(model_factory: ModelFactory) -> ModelDefBuilder:
    return ModelDefBuilder(model_factory)


@pytest.fixture
def model_module_info(stub_package_info: PackageInfo) -> ModuleInfo:
    return ModuleInfo(stub_package_info, "model")


@pytest.fixture
def model_module_builder(model_module_info: ModuleInfo) -> ModuleASTBuilder:
    return ModuleASTBuilder(model_module_info)


@pytest.fixture
def other_module_builder(model_module_info: ModuleInfo) -> ModuleASTBuilder:
    return ModuleASTBuilder(replace(model_module_info, name="other"))


@pytest.fixture
def model_factory_type() -> t.Optional[t.Callable[[ModuleASTBuilder], ModelFactory]]:
    return None


@pytest.fixture
def model_factory(
    model_factory_type: t.Optional[t.Callable[[ModuleASTBuilder], ModelFactory]],
    model_module_builder: ModuleASTBuilder,
) -> ModelFactory:
    assert model_factory_type is not None
    return model_factory_type(model_module_builder)
