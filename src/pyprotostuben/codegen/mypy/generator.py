import abc
import typing as t
from dataclasses import dataclass

from pyprotostuben.codegen.module_ast import ModuleAstContext
from pyprotostuben.codegen.mypy.builder import Pb2AstBuilder, Pb2GrpcAstBuilder
from pyprotostuben.codegen.mypy.model import (
    EnumInfo,
    EnumValueInfo,
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
from pyprotostuben.protobuf.visitor.decorator import ProtoVisitorDecorator
from pyprotostuben.protobuf.visitor.model import (
    DescriptorContext,
    EnumDescriptorContext,
    EnumValueDescriptorContext,
    FieldDescriptorContext,
    FileDescriptorContext,
    MethodDescriptorContext,
    OneofDescriptorContext,
    ServiceDescriptorContext,
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


# TODO: consider use of inline type dicts, see: https://mypy.readthedocs.io/en/stable/typed_dict.html#inline-typeddict-types
class MypyStubAstGenerator(ProtoVisitorDecorator[MypyStubContext], LoggerMixin):
    def __init__(self, registry: TypeRegistry, trait: MypyStubTrait) -> None:
        self.__registry = registry
        self.__trait = trait

    def enter_file_descriptor_proto(self, context: FileDescriptorContext[MypyStubContext]) -> None:
        context.meta = self.__create_root_context(context)

    def leave_file_descriptor_proto(self, context: FileDescriptorContext[MypyStubContext]) -> None:
        scope = context.meta

        pb2_module_ast = scope.pb2_builder.build_module(scope)
        pb2_grpc_module_ast = scope.pb2_grpc_builder.build_module(scope)

        context.meta.generated_modules.update(
            {
                scope.pb2_module.stub_file: pb2_module_ast,
                scope.pb2_grpc_module.stub_file: pb2_grpc_module_ast,
            }
        )

    def enter_enum_descriptor_proto(self, context: EnumDescriptorContext[MypyStubContext]) -> None:
        context.meta = self.__create_sub_context(context.meta)

    def leave_enum_descriptor_proto(self, context: EnumDescriptorContext[MypyStubContext]) -> None:
        proto = context.proto
        scope = context.meta
        parent = context.parent.meta
        builder = scope.pb2_builder

        parent.enums.append(
            EnumInfo(
                body=[
                    builder.build_enum_def(
                        name=proto.name,
                        doc=build_docstring(context.location),
                        scope=scope,
                    )
                ],
            ),
        )

    def enter_enum_value_descriptor_proto(self, _: EnumValueDescriptorContext[MypyStubContext]) -> None:
        pass

    def leave_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[MypyStubContext]) -> None:
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

    def enter_descriptor_proto(self, context: DescriptorContext[MypyStubContext]) -> None:
        context.meta = self.__create_sub_context(context.meta)

    def leave_descriptor_proto(self, context: DescriptorContext[MypyStubContext]) -> None:
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
                        name=proto.name,
                        doc=build_docstring(context.location),
                        scope=scope,
                    ),
                ],
            )
        )

    def enter_oneof_descriptor_proto(self, _: OneofDescriptorContext[MypyStubContext]) -> None:
        pass

    def leave_oneof_descriptor_proto(self, context: OneofDescriptorContext[MypyStubContext]) -> None:
        proto = context.proto
        parent = context.meta

        parent.oneof_groups.append(proto.name)

    def enter_field_descriptor_proto(self, _: FieldDescriptorContext[MypyStubContext]) -> None:
        pass

    def leave_field_descriptor_proto(self, context: FieldDescriptorContext[MypyStubContext]) -> None:
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

        # TODO: support extensions
        # if proto.HasField("extendee"):
        #     (proto)

    def enter_service_descriptor_proto(self, context: ServiceDescriptorContext[MypyStubContext]) -> None:
        context.meta = self.__create_sub_context(context.meta)

    def leave_service_descriptor_proto(self, context: ServiceDescriptorContext[MypyStubContext]) -> None:
        name = context.proto.name
        scope = context.meta
        parent = context.parent.meta
        builder = scope.pb2_grpc_builder

        doc = build_docstring(context.location)

        parent.services.append(
            ServiceInfo(
                servicer=builder.build_servicer_def(name, doc, scope),
                registrator=builder.build_servicer_registrator_def(name),
                stub=builder.build_stub_def(name, doc, scope),
            )
        )

    def enter_method_descriptor_proto(self, context: MethodDescriptorContext[MypyStubContext]) -> None:
        pass

    def leave_method_descriptor_proto(self, context: MethodDescriptorContext[MypyStubContext]) -> None:
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

    def __create_root_context(self, context: FileDescriptorContext[MypyStubContext]) -> MypyStubContext:
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

    def __create_sub_context(self, context: MypyStubContext) -> MypyStubContext:
        return MypyStubContext(
            generated_modules=context.generated_modules,
            _pb2_module=context.pb2_module,
            _pb2_builder=context.pb2_builder,
            _pb2_grpc_module=context.pb2_grpc_module,
            _pb2_grpc_builder=context.pb2_grpc_builder,
            enums=[],
            enum_values=[],
            messages=[],
            oneof_groups=[],
            fields=[],
            services=[],
            methods=[],
        )
