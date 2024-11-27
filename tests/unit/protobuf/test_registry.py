import typing as t

import pytest
from google.protobuf.descriptor_pb2 import FieldDescriptorProto

from pyprotostuben.protobuf.registry import (
    EnumInfo,
    MapEntryInfo,
    MapEntryPlaceholder,
    MessageInfo,
    ProtoInfo,
    ScalarInfo,
    TypeNotFoundError,
    TypeRegistry,
)
from pyprotostuben.python.info import ModuleInfo


@pytest.mark.parametrize(
    ("field", "user_types", "expected_info"),
    [
        pytest.param(
            FieldDescriptorProto(
                type=FieldDescriptorProto.Type.TYPE_BOOL,
            ),
            {},
            ScalarInfo.build(ModuleInfo(None, "builtins"), "bool"),
        ),
        pytest.param(
            FieldDescriptorProto(
                type=FieldDescriptorProto.Type.TYPE_INT32,
            ),
            {},
            ScalarInfo.build(ModuleInfo(None, "builtins"), "int"),
        ),
        pytest.param(
            FieldDescriptorProto(
                type=FieldDescriptorProto.Type.TYPE_UINT64,
            ),
            {},
            ScalarInfo.build(ModuleInfo(None, "builtins"), "int"),
        ),
        pytest.param(
            FieldDescriptorProto(
                type=FieldDescriptorProto.Type.TYPE_FLOAT,
            ),
            {},
            ScalarInfo.build(ModuleInfo(None, "builtins"), "float"),
        ),
        pytest.param(
            FieldDescriptorProto(
                type=FieldDescriptorProto.Type.TYPE_DOUBLE,
            ),
            {},
            ScalarInfo.build(ModuleInfo(None, "builtins"), "float"),
        ),
        pytest.param(
            FieldDescriptorProto(
                type=FieldDescriptorProto.Type.TYPE_STRING,
            ),
            {},
            ScalarInfo.build(ModuleInfo(None, "builtins"), "str"),
        ),
        pytest.param(
            FieldDescriptorProto(
                type=FieldDescriptorProto.Type.TYPE_MESSAGE,
                type_name="my-first-type",
            ),
            {
                "my-first-type": MessageInfo.build(ModuleInfo(None, "my_module"), "First"),
            },
            MessageInfo.build(ModuleInfo(None, "my_module"), "First"),
        ),
    ],
)
def test_resolve_proto_field_ok(
    type_registry: TypeRegistry,
    field: FieldDescriptorProto,
    expected_info: ProtoInfo,
) -> None:
    assert type_registry.resolve_proto_field(field) == expected_info


@pytest.mark.parametrize(
    ("field", "expected_error"),
    [
        pytest.param(
            FieldDescriptorProto(
                type=FieldDescriptorProto.Type.TYPE_MESSAGE,
                type_name="unknown",
            ),
            TypeNotFoundError,
        ),
    ],
)
def test_resolve_proto_field_error(
    type_registry: TypeRegistry,
    field: FieldDescriptorProto,
    expected_error: type[Exception],
) -> None:
    with pytest.raises(expected_error):
        type_registry.resolve_proto_field(field)


@pytest.mark.parametrize(
    ("ref", "user_types", "expected_info"),
    [
        pytest.param(
            "foo.Foo",
            {
                "foo.Foo": MessageInfo.build(ModuleInfo(None, "foo"), "Foo"),
            },
            MessageInfo.build(ModuleInfo(None, "foo"), "Foo"),
        ),
        pytest.param(
            "foo.Bar",
            {
                "foo.Foo": MessageInfo.build(ModuleInfo(None, "foo"), "Foo"),
                "foo.Bar": MessageInfo.build(ModuleInfo(None, "foo"), "Bar"),
            },
            MessageInfo.build(ModuleInfo(None, "foo"), "Bar"),
        ),
    ],
)
def test_resolve_proto_message_ok(
    type_registry: TypeRegistry,
    ref: str,
    expected_info: MessageInfo,
) -> None:
    assert type_registry.resolve_proto_message(ref) == expected_info


@pytest.mark.parametrize(
    ("ref", "user_types", "expected_error"),
    [
        pytest.param(
            "unknown",
            {},
            TypeNotFoundError,
        ),
        pytest.param(
            "foo",
            {"bar": MessageInfo.build(ModuleInfo(None, "bar"), "Bar")},
            TypeNotFoundError,
        ),
    ],
)
def test_resolve_proto_message_error(
    type_registry: TypeRegistry,
    ref: str,
    expected_error: type[Exception],
) -> None:
    with pytest.raises(expected_error):
        type_registry.resolve_proto_message(ref)


@pytest.mark.parametrize(
    ("ref", "user_types", "map_entries", "expected_info"),
    [
        pytest.param(
            "foo.Map",
            {},
            {
                "foo.Map": MapEntryPlaceholder(
                    ModuleInfo(None, "foo"),
                    FieldDescriptorProto(
                        type=FieldDescriptorProto.Type.TYPE_INT32,
                    ),
                    FieldDescriptorProto(
                        type=FieldDescriptorProto.Type.TYPE_STRING,
                    ),
                ),
            },
            MapEntryInfo(
                module=ModuleInfo(None, "foo"),
                key=ScalarInfo.build(ModuleInfo(None, "builtins"), "int"),
                value=ScalarInfo.build(ModuleInfo(None, "builtins"), "str"),
            ),
        ),
        pytest.param(
            "foo.Map",
            {
                "spam.Egg": MessageInfo.build(ModuleInfo(None, "spam"), "Egg"),
            },
            {
                "foo.Map": MapEntryPlaceholder(
                    ModuleInfo(None, "foo"),
                    FieldDescriptorProto(
                        type=FieldDescriptorProto.Type.TYPE_STRING,
                    ),
                    FieldDescriptorProto(
                        type=FieldDescriptorProto.Type.TYPE_MESSAGE,
                        type_name="spam.Egg",
                    ),
                ),
            },
            MapEntryInfo(
                module=ModuleInfo(None, "foo"),
                key=ScalarInfo.build(ModuleInfo(None, "builtins"), "str"),
                value=MessageInfo.build(ModuleInfo(None, "spam"), "Egg"),
            ),
        ),
    ],
)
def test_resolve_proto_map_entry_ok(
    type_registry: TypeRegistry,
    ref: str,
    expected_info: MapEntryInfo,
) -> None:
    assert type_registry.resolve_proto_map_entry(ref) == expected_info


@pytest.mark.parametrize(
    ("ref", "map_entries", "expected_error"),
    [
        pytest.param(
            "unknown",
            {},
            TypeNotFoundError,
        ),
        pytest.param(
            "bar.Bar",
            {
                "foo.Foo": MapEntryPlaceholder(
                    ModuleInfo(None, "foo"),
                    FieldDescriptorProto(
                        type=FieldDescriptorProto.Type.TYPE_INT32,
                    ),
                    FieldDescriptorProto(
                        type=FieldDescriptorProto.Type.TYPE_STRING,
                    ),
                ),
            },
            TypeNotFoundError,
        ),
    ],
)
def test_resolve_proto_map_entry_error(
    type_registry: TypeRegistry,
    ref: str,
    expected_error: type[Exception],
) -> None:
    with pytest.raises(expected_error):
        type_registry.resolve_proto_map_entry(ref)


@pytest.fixture
def type_registry(
    user_types: t.Mapping[str, t.Union[EnumInfo, MessageInfo]],
    map_entries: t.Mapping[str, MapEntryPlaceholder],
) -> TypeRegistry:
    return TypeRegistry(user_types, map_entries)


@pytest.fixture
def user_types() -> t.Mapping[str, t.Union[EnumInfo, MessageInfo]]:
    return {}


@pytest.fixture
def map_entries() -> t.Mapping[str, MapEntryPlaceholder]:
    return {}
