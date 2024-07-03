import ast
import typing as t
from functools import cached_property

from pyprotostuben.protobuf.builder.message import MessageASTBuilder, FieldInfo
from pyprotostuben.python.info import TypeInfo


class ImmutableMessageASTBuilder(MessageASTBuilder):
    @cached_property
    def protobuf_field_repeated_ref(self) -> TypeInfo:
        return TypeInfo.build(self.inner.typing_module, "Sequence")

    @cached_property
    def protobuf_map_entry_ref(self) -> TypeInfo:
        return TypeInfo.build(self.inner.typing_module, "Mapping")

    def build_protobuf_message_init_stub(self, fields: t.Sequence[FieldInfo]) -> ast.stmt:
        return self.inner.build_init_stub(
            [
                self.inner.build_kw_arg(
                    name=field.name,
                    annotation=self.inner.build_optional_ref(field.annotation)
                    if field.optional or field.oneof_group is not None
                    else field.annotation,
                    default=field.default
                    if field.default is not None
                    else self.inner.build_none_ref()
                    if field.optional or field.oneof_group is not None
                    else None,
                )
                for field in fields
            ]
        )

    def build_protobuf_message_field_stubs(self, fields: t.Sequence[FieldInfo]) -> t.Sequence[ast.stmt]:
        return [
            self.inner.build_property_stub(
                name=field.name,
                returns=field.annotation,
            )
            for field in fields
        ]
