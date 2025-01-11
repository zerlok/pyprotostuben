import ast
import typing as t
from dataclasses import dataclass, field, replace

import pytest

from pyprotostuben.codegen.model import DataclassModelFactory, ModelDefBuilder, ModelFactory, PydanticModelFactory
from pyprotostuben.python.builder import ModuleASTBuilder, TypeRef
from pyprotostuben.python.info import ModuleInfo, PackageInfo, TypeInfo
from tests.conftest import parse_ast
from tests.stub.structs import ChatRoom, User


@dataclass(frozen=True, kw_only=True)
class CreateCase:
    expected: ast.AST
    name: str
    fields: t.Mapping[str, TypeRef]
    defaults: t.Mapping[str, object] = field(default_factory=dict)
    nested: t.Sequence[ast.stmt] = field(default_factory=list)
    doc: t.Optional[str] = None


@pytest.mark.parametrize(
    ["case", "model_factory_type"],
    [
        pytest.param(
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
            PydanticModelFactory,
        ),
        pytest.param(
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
            DataclassModelFactory,
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
    ["model_factory_type", "model_module_info", "types", "orig_type", "model_type_ref"],
    [
        pytest.param(
            PydanticModelFactory,
            ModuleInfo(None, "model"),
            [str],
            str,
            TypeInfo.from_type(str),
        ),
        pytest.param(
            PydanticModelFactory,
            ModuleInfo(None, "model"),
            [User],
            User,
            TypeInfo.build(ModuleInfo(None, "model"), "User"),
        ),
        # TODO: fix enum case
        # pytest.param(
        #     PydanticModelFactory,
        #     [User],
        #     UserStatus,
        #     TypeInfo.build(None, "User"),
        # ),
    ],
)
def test_model_def_builder_resolve_returns_expected_type_info(
    stub_package_info: PackageInfo,
    types: t.Collection[type[object]],
    orig_type: type[object],
    model_type_ref: TypeInfo,
    model_def_builder: ModelDefBuilder,
) -> None:
    model_def_builder.update(types)

    assert model_def_builder.resolve(orig_type) == model_type_ref


@pytest.mark.parametrize(
    ["model_factory_type", "model_module_info", "target_var", "source_var", "type_", "mode", "expected"],
    [
        pytest.param(
            PydanticModelFactory,
            ModuleInfo(None, "model"),
            "my_target_var",
            "my_source_var",
            str,
            "model",
            parse_ast("""
            my_target_var = my_source_var
            """),
        ),
        pytest.param(
            PydanticModelFactory,
            ModuleInfo(None, "model"),
            "my_target_var",
            "my_source_var",
            str,
            "original",
            parse_ast("""
            my_target_var = my_source_var
            """),
        ),
        pytest.param(
            PydanticModelFactory,
            ModuleInfo(None, "model"),
            "user_model",
            "user_data",
            User,
            "model",
            parse_ast("""
            import model
            
            user_model = model.User(
                id=user_data.id,
                username=user_data.username,
                created_at=user_data.created_at,
                status=user_data.status.name,
            )
            """),
        ),
        pytest.param(
            PydanticModelFactory,
            ModuleInfo(None, "model"),
            "result_list",
            "list_data",
            list[User],
            "model",
            parse_ast("""
            import model
            
            result_list = [
                model.User(
                    id=list_data_item.id,
                    username=list_data_item.username,
                    created_at=list_data_item.created_at,
                    status=list_data_item.status.name,
                )
                for list_data_item in list_data
            ]
            """),
        ),
        pytest.param(
            PydanticModelFactory,
            ModuleInfo(None, "model"),
            "room",
            "data",
            ChatRoom,
            "model",
            parse_ast("""
            import model
            
            room = model.ChatRoom(
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
        ),
        pytest.param(
            PydanticModelFactory,
            ModuleInfo(None, "model"),
            "result_value",
            "pydantic_value",
            ChatRoom,
            "original",
            parse_ast("""
            import tests.stub.structs
            
            result_value = tests.stub.structs.ChatRoom(
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
        ),
    ],
)
def test_model_def_builder_assign_stmt_returns_expected_stmt(
    target_var: str,
    source_var: str,
    type_: type[object],
    mode: t.Literal["original", "model"],
    expected: ast.AST,
    model_def_builder: ModelDefBuilder,
    other_module_builder: ModuleASTBuilder,
) -> None:
    model_def_builder.update([type_])

    other_module_builder.append(
        model_def_builder.assign_stmt(target_var, source_var, type_, mode, other_module_builder)
    )

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
