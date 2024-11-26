import typing as t
from dataclasses import dataclass, field

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest
from google.protobuf.descriptor_pb2 import FieldDescriptorProto

from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.parser import CodeGeneratorParameters, ParameterParser
from pyprotostuben.protobuf.registry import (
    EnumInfo,
    MapEntryPlaceholder,
    MessageInfo,
    TypeRegistry,
)
from pyprotostuben.protobuf.visitor.abc import ProtoVisitor
from pyprotostuben.protobuf.visitor.decorator import LeaveProtoVisitorDecorator
from pyprotostuben.protobuf.visitor.model import (
    DescriptorContext,
    EnumContext,
    EnumValueContext,
    ExtensionContext,
    FieldContext,
    FileContext,
    MethodContext,
    OneofContext,
    ServiceContext,
)
from pyprotostuben.protobuf.visitor.walker import Walker
from pyprotostuben.python.info import ModuleInfo


@dataclass(frozen=True)
class CodeGeneratorContext:
    request: CodeGeneratorRequest
    params: CodeGeneratorParameters
    files: t.Sequence[ProtoFile]
    registry: TypeRegistry


@dataclass()
class BuildContext:
    files: dict[str, ProtoFile] = field(default_factory=dict)
    types: dict[str, t.Union[EnumInfo, MessageInfo]] = field(default_factory=dict)
    map_entries: dict[str, MapEntryPlaceholder] = field(default_factory=dict)


class ContextBuilder(ProtoVisitor[BuildContext], LoggerMixin):
    def visit_file(self, context: FileContext[BuildContext]) -> None:
        self.__register_file(context)
        self._log.debug("visited", file=context.file)

    def visit_enum(self, context: EnumContext[BuildContext]) -> None:
        self.__register_enum(context)

    def visit_enum_value(self, _: EnumValueContext[BuildContext]) -> None:
        pass

    def visit_descriptor(self, context: DescriptorContext[BuildContext]) -> None:
        proto = context.proto

        if proto.options.map_entry:
            self.__register_map_entry(
                context,
                self.__find_field_by_name(proto.field, "key"),
                self.__find_field_by_name(proto.field, "value"),
            )

        else:
            self.__register_message(context)

    def visit_oneof(self, _: OneofContext[BuildContext]) -> None:
        pass

    def visit_field(self, _: FieldContext[BuildContext]) -> None:
        pass

    def visit_service(self, _: ServiceContext[BuildContext]) -> None:
        pass

    def visit_method(self, _: MethodContext[BuildContext]) -> None:
        pass

    def visit_extension(self, context: ExtensionContext[BuildContext]) -> None:
        pass

    # TODO: speed up with multiprocessing by files
    def build(self, request: CodeGeneratorRequest) -> CodeGeneratorContext:
        parser = ParameterParser()
        walker = Walker(LeaveProtoVisitorDecorator(self))

        context = BuildContext()

        # TODO: consider `request.source_file_descriptors` usage to keep options
        walker.walk(*request.proto_file, meta=context)

        return CodeGeneratorContext(
            request=request,
            params=parser.parse(request.parameter),
            files=[context.files[name] for name in request.file_to_generate],
            registry=TypeRegistry(context.types, context.map_entries),
        )

    def __register_file(self, context: FileContext[BuildContext]) -> None:
        context.meta.files[context.proto.name] = context.file

    def __register_enum(self, context: EnumContext[BuildContext]) -> None:
        qualname, module, ns = self.__build_type(context.root, context)
        type_ = context.meta.types[qualname] = EnumInfo(module, ns)

        self._log.info("registered", qualname=qualname, type_=type_)

    def __register_message(
        self,
        context: t.Union[FileContext[BuildContext], DescriptorContext[BuildContext]],
    ) -> None:
        qualname, module, ns = self.__build_type(
            root=context.root if isinstance(context, DescriptorContext) else context,
            context=context,
        )
        type_ = context.meta.types[qualname] = MessageInfo(module, ns)

        self._log.info("registered", qualname=qualname, type_=type_)

    def __register_map_entry(
        self,
        context: DescriptorContext[BuildContext],
        key: FieldDescriptorProto,
        value: FieldDescriptorProto,
    ) -> None:
        qualname, module, _ = self.__build_type(context.root, context)
        placeholder = context.meta.map_entries[qualname] = MapEntryPlaceholder(module, key, value)

        self._log.info("registered", qualname=qualname, placeholder=placeholder)

    def __build_type(
        self,
        root: FileContext[BuildContext],
        context: t.Union[
            FileContext[BuildContext],
            EnumContext[BuildContext],
            DescriptorContext[BuildContext],
        ],
    ) -> tuple[str, ModuleInfo, t.Sequence[str]]:
        ns = [part.proto.name for part in context.parts[1:]]
        proto_path = ".".join(ns)

        qualname = f".{root.proto.package}.{proto_path}"
        module = root.file.pb2_module

        return qualname, module, ns

    def __find_field_by_name(self, fields: t.Sequence[FieldDescriptorProto], name: str) -> FieldDescriptorProto:
        for proto in fields:
            if proto.name == name:
                return proto

        msg = "field not found"
        raise ValueError(msg, name, fields)
