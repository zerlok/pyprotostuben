import ast
import typing as t
from dataclasses import dataclass, field

from pyprotostuben.python.ast_builder import TypeRef


@dataclass()
class EnumInfo:
    body: t.Sequence[ast.stmt]


@dataclass()
class EnumValueInfo:
    name: str
    value: int
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
    name: str
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
class ExtensionInfo:
    name: str
    doc: t.Optional[str]
    annotation: ast.expr
    default: t.Optional[ast.expr]
    extended: TypeRef


@dataclass()
class ScopeInfo:
    enums: t.MutableSequence[EnumInfo] = field(default_factory=list)
    enum_values: t.MutableSequence[EnumValueInfo] = field(default_factory=list)
    messages: t.MutableSequence[MessageInfo] = field(default_factory=list)
    oneof_groups: t.MutableSequence[str] = field(default_factory=list)
    fields: t.MutableSequence[FieldInfo] = field(default_factory=list)
    services: t.MutableSequence[ServiceInfo] = field(default_factory=list)
    methods: t.MutableSequence[MethodInfo] = field(default_factory=list)
    extensions: t.MutableSequence[ExtensionInfo] = field(default_factory=list)
