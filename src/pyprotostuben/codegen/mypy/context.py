import ast
import typing as t
from dataclasses import dataclass, field

from pyprotostuben.protobuf.builder.grpc import GRPCASTBuilder, MethodInfo
from pyprotostuben.protobuf.builder.message import FieldInfo, MessageASTBuilder
from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.python.info import ModuleInfo


@dataclass()
class MessageContext:
    file: ProtoFile
    module: ModuleInfo
    builder: MessageASTBuilder
    nested: t.MutableSequence[ast.stmt] = field(default_factory=list)
    fields: t.MutableSequence[FieldInfo] = field(default_factory=list)
    oneof_groups: t.MutableSequence[str] = field(default_factory=list)

    def sub(self) -> "MessageContext":
        return MessageContext(
            file=self.file,
            module=self.module,
            builder=self.builder,
        )


@dataclass()
class GRPCContext:
    file: ProtoFile
    module: ModuleInfo
    builder: GRPCASTBuilder
    nested: t.MutableSequence[ast.stmt] = field(default_factory=list)
    methods: t.MutableSequence[MethodInfo] = field(default_factory=list)

    def sub(self) -> "GRPCContext":
        return GRPCContext(
            file=self.file,
            module=self.module,
            builder=self.builder,
        )
