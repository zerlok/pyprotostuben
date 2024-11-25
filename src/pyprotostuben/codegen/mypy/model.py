import ast
import typing as t
from dataclasses import dataclass

from pyprotostuben.python.ast_builder import TypeRef


@dataclass()
class EnumInfo:
    body: t.Sequence[ast.stmt]


@dataclass()
class EnumValueInfo:
    body: t.Sequence[ast.stmt]


@dataclass()
class MessageInfo:
    body: t.Sequence[ast.stmt]


@dataclass()
class FieldInfo:
    name: str
    doc: t.Optional[str]
    annotation: ast.expr
    optional: bool
    default: t.Optional[ast.expr]
    oneof_group: t.Optional[str]


@dataclass()
class ServiceInfo:
    servicer: t.Sequence[ast.stmt]
    registrator: t.Sequence[ast.stmt]
    stub: t.Sequence[ast.stmt]


@dataclass()
class MethodInfo:
    name: str
    doc: t.Optional[str]
    server_input: TypeRef
    server_input_streaming: bool
    server_output: TypeRef
    server_output_streaming: bool


@dataclass()
class ScopeInfo:
    enums: t.MutableSequence[EnumInfo]
    enum_values: t.MutableSequence[EnumValueInfo]
    messages: t.MutableSequence[MessageInfo]
    oneof_groups: t.MutableSequence[str]
    fields: t.MutableSequence[FieldInfo]
    services: t.MutableSequence[ServiceInfo]
    methods: t.MutableSequence[MethodInfo]
