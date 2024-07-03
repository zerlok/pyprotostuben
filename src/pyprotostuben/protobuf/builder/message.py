import ast
import typing as t
from collections import defaultdict
from dataclasses import dataclass
from functools import cached_property

from pyprotostuben.protobuf.registry import ProtoInfo, MapEntryInfo
from pyprotostuben.python.ast_builder import ASTBuilder, TypeRef
from pyprotostuben.python.info import ModuleInfo, PackageInfo, TypeInfo


@dataclass(frozen=True)
class FieldInfo:
    name: str
    annotation: ast.expr
    optional: bool
    default: t.Optional[ast.expr]
    oneof_group: t.Optional[str]


class MessageASTBuilder:
    def __init__(self, inner: ASTBuilder) -> None:
        self.inner = inner

    @cached_property
    def protobuf_message_ref(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(PackageInfo(PackageInfo(None, "google"), "protobuf"), "message"), "Message")

    @cached_property
    def protobuf_enum_ref(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(None, "enum"), "IntEnum")

    @cached_property
    def protobuf_field_repeated_ref(self) -> TypeInfo:
        return TypeInfo.build(self.inner.typing_module, "MutableSequence")

    @cached_property
    def protobuf_map_entry_ref(self) -> TypeInfo:
        return TypeInfo.build(self.inner.typing_module, "MutableMapping")

    def build_protobuf_message_module(self, deps: t.Collection[ModuleInfo], body: t.Sequence[ast.stmt]) -> ast.Module:
        return self.inner.build_module(deps, body) if body else self.inner.build_module([], [])

    def build_protobuf_message_def(
        self,
        name: str,
        fields: t.Sequence[FieldInfo],
        nested: t.Sequence[ast.stmt],
    ) -> ast.stmt:
        return self.inner.build_class_def(
            name=name,
            bases=[self.protobuf_message_ref],
            body=[
                *nested,
                self.build_protobuf_message_init_stub(fields),
                *self.build_protobuf_message_field_stubs(fields),
                self.build_protobuf_message_has_field_method_stub(fields),
                *self.build_which_oneof_method_stubs(fields),
            ],
        )

    def build_protobuf_type_ref(self, info: ProtoInfo) -> ast.expr:
        if isinstance(info, MapEntryInfo):
            return self.inner.build_generic_ref(self.protobuf_map_entry_ref, info.key, info.value)

        return self.inner.build_ref(info)

    def build_protobuf_repeated_ref(self, info: ProtoInfo, inner: TypeRef) -> ast.expr:
        return self.inner.build_generic_ref(self.protobuf_field_repeated_ref, inner)

    def build_protobuf_enum_def(
        self,
        name: str,
        nested: t.Sequence[ast.stmt],
    ) -> ast.ClassDef:
        return self.inner.build_class_def(
            name=name,
            bases=[self.protobuf_enum_ref],
            body=nested,
        )

    def build_protobuf_enum_value_def(self, name: str, value: object) -> ast.stmt:
        return ast.Assign(
            targets=[ast.Name(id=name)],
            value=ast.Constant(value=value),
            lineno=None,
        )

    def build_protobuf_message_init_stub(self, fields: t.Sequence[FieldInfo]) -> ast.stmt:
        return self.inner.build_init_stub(
            [
                self.inner.build_kw_arg(
                    name=field.name,
                    annotation=self.inner.build_optional_ref(field.annotation),
                    default=field.default if field.default is not None else self.inner.build_none_ref(),
                )
                for field in fields
            ]
        )

    def build_protobuf_message_field_stubs(self, fields: t.Sequence[FieldInfo]) -> t.Sequence[ast.stmt]:
        return [
            self.inner.build_attr_stub(
                name=field.name,
                annotation=field.annotation,
                default=field.default,
            )
            for field in fields
        ]

    def build_protobuf_message_has_field_method_stub(self, fields: t.Sequence[FieldInfo]) -> ast.stmt:
        optional_field_names = [ast.Constant(value=field.name) for field in fields if field.optional]

        return self.inner.build_method_stub(
            name="HasField",
            args=[
                self.inner.build_pos_arg(
                    name="field_name",
                    annotation=self.inner.build_literal_ref(*optional_field_names),
                )
            ],
            returns=self.inner.build_bool_ref() if optional_field_names else self.inner.build_no_return_ref(),
        )

    def build_which_oneof_method_stubs(self, fields: t.Sequence[FieldInfo]) -> t.Sequence[ast.stmt]:
        oneofs: t.DefaultDict[str, t.List[ast.expr]] = defaultdict(list)
        for field in fields:
            if field.oneof_group is not None:
                oneofs[field.oneof_group].append(ast.Constant(value=field.name))

        if not oneofs:
            return [
                self.inner.build_method_stub(
                    name="WhichOneof",
                    args=[
                        self.inner.build_pos_arg(
                            name="oneof_group",
                            annotation=self.inner.build_no_return_ref(),
                        ),
                    ],
                    returns=self.inner.build_no_return_ref(),
                ),
            ]

        return [
            self.inner.build_method_stub(
                name="WhichOneof",
                decorators=[self.inner.build_overload_ref()] if len(oneofs) > 1 else None,
                args=[
                    self.inner.build_pos_arg(
                        name="oneof_group",
                        annotation=self.inner.build_literal_ref(ast.Constant(value=name)),
                    ),
                ],
                returns=self.inner.build_optional_ref(self.inner.build_literal_ref(*items)),
            )
            for name, items in oneofs.items()
        ]
