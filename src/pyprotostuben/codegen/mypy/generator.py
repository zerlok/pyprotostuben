import abc
import typing as t
from dataclasses import dataclass

from pyprotostuben.codegen.module_ast import ModuleAstContext
from pyprotostuben.codegen.mypy.builder import Pb2AstBuilder, Pb2GrpcAstBuilder
from pyprotostuben.codegen.mypy.model import (
    EnumInfo,
    EnumValueInfo,
    ExtensionInfo,
    FieldInfo,
    MessageInfo,
    MethodInfo,
    ScopeInfo,
    ServiceInfo,
)
from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.location import build_docstring
from pyprotostuben.protobuf.registry import MapEntryInfo, TypeRegistry
from pyprotostuben.protobuf.visitor.abc import ProtoVisitorDecorator
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
from pyprotostuben.python.info import ModuleInfo


@dataclass()
class MypyStubContext(ModuleAstContext, ScopeInfo):
    _pb2_module: t.Optional[ModuleInfo] = None
    _pb2_builder: t.Optional[Pb2AstBuilder] = None
    _pb2_grpc_module: t.Optional[ModuleInfo] = None
    _pb2_grpc_builder: t.Optional[Pb2GrpcAstBuilder] = None

    @property
    def pb2_module(self) -> ModuleInfo:
        if self._pb2_module is None:
            raise ValueError
        return self._pb2_module

    @property
    def pb2_builder(self) -> Pb2AstBuilder:
        if self._pb2_builder is None:
            raise ValueError
        return self._pb2_builder

    @property
    def pb2_grpc_module(self) -> ModuleInfo:
        if self._pb2_grpc_module is None:
            raise ValueError
        return self._pb2_grpc_module

    @property
    def pb2_grpc_builder(self) -> Pb2GrpcAstBuilder:
        if self._pb2_grpc_builder is None:
            raise ValueError
        return self._pb2_grpc_builder


class MypyStubTrait(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def create_pb2_module(self, file: ProtoFile) -> ModuleInfo:
        raise NotImplementedError

    @abc.abstractmethod
    def create_pb2_builder(self, module: ModuleInfo) -> Pb2AstBuilder:
        raise NotImplementedError

    @abc.abstractmethod
    def create_pb2_grpc_module(self, file: ProtoFile) -> ModuleInfo:
        raise NotImplementedError

    @abc.abstractmethod
    def create_pb2_grpc_builder(self, module: ModuleInfo) -> Pb2GrpcAstBuilder:
        raise NotImplementedError


class MypyStubAstGenerator(ProtoVisitorDecorator[MypyStubContext], LoggerMixin):
    def __init__(self, registry: TypeRegistry, trait: MypyStubTrait) -> None:
        self.__registry = registry
        self.__trait = trait

    def enter_file(self, context: FileContext[MypyStubContext]) -> None:
        context.meta = self.__create_root_context(context)

    def leave_file(self, context: FileContext[MypyStubContext]) -> None:
        scope = context.meta

        pb2_module_ast = scope.pb2_builder.build_module(scope)
        pb2_grpc_module_ast = scope.pb2_grpc_builder.build_module(scope)

        context.meta.generated_modules.update(
            {
                scope.pb2_module.stub_file: pb2_module_ast,
                scope.pb2_grpc_module.stub_file: pb2_grpc_module_ast,
            }
        )

    def enter_enum(self, context: EnumContext[MypyStubContext]) -> None:
        context.meta = self.__create_sub_context(context)

    def leave_enum(self, context: EnumContext[MypyStubContext]) -> None:
        scope = context.meta
        parent = context.parent.meta
        builder = scope.pb2_builder

        parent.enums.append(
            EnumInfo(
                body=[
                    builder.build_enum_def(
                        path=self.__get_class_path(context),
                        doc=build_docstring(context.location),
                        scope=scope,
                    )
                ],
            ),
        )

    def enter_enum_value(self, _: EnumValueContext[MypyStubContext]) -> None:
        pass

    def leave_enum_value(self, context: EnumValueContext[MypyStubContext]) -> None:
        proto = context.proto
        parent = context.meta
        builder = parent.pb2_builder

        parent.enum_values.append(
            EnumValueInfo(
                name=proto.name,
                value=proto.number,
                body=builder.build_enum_value_def(
                    name=proto.name,
                    doc=build_docstring(context.location),
                    value=proto.number,
                ),
            ),
        )

    def enter_descriptor(self, context: DescriptorContext[MypyStubContext]) -> None:
        context.meta = self.__create_sub_context(context)

    def leave_descriptor(self, context: DescriptorContext[MypyStubContext]) -> None:
        proto = context.proto
        if proto.options.map_entry:
            return

        scope = context.meta
        parent = context.parent.meta
        builder = scope.pb2_builder

        parent.messages.append(
            MessageInfo(
                body=[
                    builder.build_message_def(
                        path=self.__get_class_path(context),
                        doc=build_docstring(context.location),
                        scope=scope,
                    ),
                ],
            )
        )

    def enter_oneof(self, _: OneofContext[MypyStubContext]) -> None:
        pass

    def leave_oneof(self, context: OneofContext[MypyStubContext]) -> None:
        proto = context.proto
        parent = context.meta

        parent.oneof_groups.append(proto.name)

    def enter_field(self, _: FieldContext[MypyStubContext]) -> None:
        pass

    def leave_field(self, context: FieldContext[MypyStubContext]) -> None:
        proto = context.proto
        parent = context.meta
        builder = context.meta.pb2_builder

        info = self.__registry.resolve_proto_field(proto)
        is_optional = proto.proto3_optional

        annotation = builder.build_type_ref(info)
        if not isinstance(info, MapEntryInfo) and proto.label == proto.Label.LABEL_REPEATED:
            annotation = builder.build_repeated_ref(annotation)

        parent.fields.append(
            FieldInfo(
                name=proto.name,
                annotation=annotation,
                doc=build_docstring(context.location),
                optional=is_optional,
                # TODO: support proto.default_value
                default=None,
                oneof_group=parent.oneof_groups[proto.oneof_index]
                if not is_optional and proto.HasField("oneof_index")
                else None,
            )
        )

    def enter_service(self, context: ServiceContext[MypyStubContext]) -> None:
        context.meta = self.__create_sub_context(context)

    def leave_service(self, context: ServiceContext[MypyStubContext]) -> None:
        name = context.proto.name
        scope = context.meta
        parent = context.parent.meta
        builder = scope.pb2_grpc_builder

        doc = build_docstring(context.location)

        parent.services.append(
            ServiceInfo(
                name=name,
                servicer=builder.build_servicer_def(name, doc, scope),
                registrator=builder.build_servicer_registrator_def(name),
                stub=builder.build_stub_def(name, doc, scope),
            )
        )

    def enter_method(self, context: MethodContext[MypyStubContext]) -> None:
        pass

    def leave_method(self, context: MethodContext[MypyStubContext]) -> None:
        proto = context.proto
        parent = context.meta

        parent.methods.append(
            MethodInfo(
                name=proto.name,
                doc=build_docstring(context.location),
                server_input=self.__registry.resolve_proto_method_client_input(proto),
                server_input_streaming=proto.client_streaming,
                server_output=self.__registry.resolve_proto_method_server_output(proto),
                server_output_streaming=proto.server_streaming,
            ),
        )

    def enter_extension(self, context: ExtensionContext[MypyStubContext]) -> None:
        pass

    def leave_extension(self, context: ExtensionContext[MypyStubContext]) -> None:
        proto = context.proto
        parent = context.meta
        builder = context.meta.pb2_builder

        if not proto.HasField("extendee"):
            return

        info = self.__registry.resolve_proto_field(proto)

        annotation = builder.build_type_ref(info)
        if not isinstance(info, MapEntryInfo) and proto.label == proto.Label.LABEL_REPEATED:
            annotation = builder.build_repeated_ref(annotation)

        parent.extensions.append(
            ExtensionInfo(
                name=proto.name,
                annotation=annotation,
                doc=build_docstring(context.location),
                # TODO: support proto.default_value
                default=None,
                extended=self.__registry.resolve_proto_message(proto.extendee),
            )
        )

    def __create_root_context(self, context: FileContext[MypyStubContext]) -> MypyStubContext:
        pb2_module = self.__trait.create_pb2_module(context.file)
        pb2_grpc_module = self.__trait.create_pb2_grpc_module(context.file)

        return MypyStubContext(
            generated_modules=context.meta.generated_modules,
            _pb2_module=pb2_module,
            _pb2_builder=self.__trait.create_pb2_builder(pb2_module),
            _pb2_grpc_module=pb2_grpc_module,
            _pb2_grpc_builder=self.__trait.create_pb2_grpc_builder(pb2_grpc_module),
            enums=[],
            enum_values=[],
            messages=[],
            oneof_groups=[],
            fields=[],
            services=[],
            methods=[],
        )

    def __create_sub_context(
        self,
        context: t.Union[
            EnumContext[MypyStubContext],
            DescriptorContext[MypyStubContext],
            ServiceContext[MypyStubContext],
        ],
    ) -> MypyStubContext:
        return MypyStubContext(
            generated_modules=context.meta.generated_modules,
            _pb2_module=context.meta.pb2_module,
            _pb2_builder=context.meta.pb2_builder,
            _pb2_grpc_module=context.meta.pb2_grpc_module,
            _pb2_grpc_builder=context.meta.pb2_grpc_builder,
            enums=[],
            enum_values=[],
            messages=[],
            oneof_groups=[],
            fields=[],
            services=[],
            methods=[],
        )

    def __get_class_path(
        self,
        context: t.Union[EnumContext[MypyStubContext], DescriptorContext[MypyStubContext]],
    ) -> t.Sequence[str]:
        # skip first part (root = file descriptor)
        return [part.proto.name for part in context.parts[1:]]
