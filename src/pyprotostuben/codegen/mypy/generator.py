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
class MypyStubContext(ModuleAstContext):
    @dataclass()
    class Pb2(ScopeInfo):
        module: ModuleInfo
        builder: Pb2AstBuilder

    @dataclass()
    class Pb2Grpc(ScopeInfo):
        module: ModuleInfo
        builder: Pb2GrpcAstBuilder

    _pb2: t.Optional[Pb2]
    _pb2_grpc: t.Optional[Pb2Grpc]

    @property
    def pb2(self) -> Pb2:
        if self._pb2 is None:
            raise ValueError
        return self._pb2

    @property
    def pb2_grpc(self) -> Pb2Grpc:
        if self._pb2_grpc is None:
            raise ValueError
        return self._pb2_grpc


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
        pb2 = context.meta.pb2
        pb2_grpc = context.meta.pb2_grpc

        pb2_module_ast = pb2.builder.build_module(pb2)
        pb2_grpc_module_ast = pb2_grpc.builder.build_module(pb2_grpc)

        context.meta.generated_modules.update(
            {
                pb2.module.stub_file: pb2_module_ast,
                pb2_grpc.module.stub_file: pb2_grpc_module_ast,
            }
        )

    def enter_enum_descriptor_proto(self, context: EnumDescriptorContext[MypyStubContext]) -> None:
        context.meta = self.__create_sub_context(context.meta)

    def leave_enum_descriptor_proto(self, context: EnumDescriptorContext[MypyStubContext]) -> None:
        context.parent.meta.pb2.enums.append(
            EnumInfo(
                body=[
                    context.meta.pb2.builder.build_enum_def(
                        name=context.proto.name,
                        doc=build_docstring(context.location),
                        scope=context.meta.pb2,
                    )
                ],
            ),
        )

    def enter_enum_value_descriptor_proto(self, _: EnumValueDescriptorContext[MypyStubContext]) -> None:
        pass

    def leave_enum_value_descriptor_proto(self, context: EnumValueDescriptorContext[MypyStubContext]) -> None:
        proto = context.proto
        parent = context.meta.pb2

        parent.enum_values.append(
            EnumValueInfo(
                name=proto.name,
                value=proto.number,
                body=parent.builder.build_enum_value_def(
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

        parent = context.parent.meta.pb2
        parent.messages.append(
            MessageInfo(
                body=[
                    parent.builder.build_message_def(
                        name=proto.name,
                        doc=build_docstring(context.location),
                        scope=context.meta.pb2,
                    ),
                ],
            )
        )

    def enter_oneof_descriptor_proto(self, _: OneofDescriptorContext[MypyStubContext]) -> None:
        pass

    def leave_oneof_descriptor_proto(self, context: OneofDescriptorContext[MypyStubContext]) -> None:
        proto = context.proto
        parent = context.meta.pb2

        parent.oneof_groups.append(proto.name)

    def enter_field_descriptor_proto(self, _: FieldDescriptorContext[MypyStubContext]) -> None:
        pass

    def leave_field_descriptor_proto(self, context: FieldDescriptorContext[MypyStubContext]) -> None:
        proto = context.proto
        parent = context.meta.pb2
        builder = parent.builder

        info = self.__registry.resolve_proto_field(context.proto)
        is_optional = proto.proto3_optional

        annotation = builder.build_type_ref(info)
        if not isinstance(info, MapEntryInfo) and context.proto.label == context.proto.Label.LABEL_REPEATED:
            annotation = builder.build_repeated_ref(annotation)

        parent.fields.append(
            FieldInfo(
                name=proto.name,
                annotation=annotation,
                # descriptor=builder.__inner.build_class_def(
                #     name="_Descriptor",
                #     bases=[builder.__inner.build_ref(TypeInfo.from_type(FieldDescriptor))],
                #     body=[
                #         builder.__inner.build_attr_stub(
                #             name="name",
                #             annotation=builder.__inner.build_str_ref(),
                #         ),
                #     ],
                # ),
                doc=build_docstring(context.location),
                optional=is_optional,
                default=None,
                # TODO: support proto.default_value
                oneof_group=parent.oneof_groups[context.proto.oneof_index]
                if not is_optional and context.proto.HasField("oneof_index")
                else None,
            )
        )

        # if context.proto.HasField("extendee"):
        #     (context.proto)

    def enter_service_descriptor_proto(self, context: ServiceDescriptorContext[MypyStubContext]) -> None:
        context.meta = self.__create_sub_context(context.meta)

    def leave_service_descriptor_proto(self, context: ServiceDescriptorContext[MypyStubContext]) -> None:
        name = context.proto.name
        scope = context.meta.pb2_grpc
        parent = context.parent.meta.pb2_grpc
        builder = parent.builder

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
        context.meta.pb2_grpc.methods.append(
            MethodInfo(
                name=context.proto.name,
                doc=build_docstring(context.location),
                server_input=self.__registry.resolve_proto_method_client_input(context.proto),
                server_input_streaming=context.proto.client_streaming,
                server_output=self.__registry.resolve_proto_method_server_output(context.proto),
                server_output_streaming=context.proto.server_streaming,
            ),
        )

    def __create_root_context(self, context: FileDescriptorContext[MypyStubContext]) -> MypyStubContext:
        pb2_module = self.__trait.create_pb2_module(context.file)
        pb2_grpc_module = self.__trait.create_pb2_grpc_module(context.file)

        return MypyStubContext(
            generated_modules=context.meta.generated_modules,
            _pb2=MypyStubContext.Pb2(
                module=pb2_module,
                builder=self.__trait.create_pb2_builder(pb2_module),
                enums=[],
                enum_values=[],
                messages=[],
                oneof_groups=[],
                fields=[],
                services=[],
                methods=[],
            ),
            _pb2_grpc=MypyStubContext.Pb2Grpc(
                module=pb2_grpc_module,
                builder=self.__trait.create_pb2_grpc_builder(pb2_grpc_module),
                enums=[],
                enum_values=[],
                messages=[],
                oneof_groups=[],
                fields=[],
                services=[],
                methods=[],
            ),
        )

    def __create_sub_context(self, context: MypyStubContext) -> MypyStubContext:
        return MypyStubContext(
            generated_modules=context.generated_modules,
            _pb2=MypyStubContext.Pb2(
                module=context.pb2.module,
                builder=context.pb2.builder,
                enums=[],
                enum_values=[],
                messages=[],
                oneof_groups=[],
                fields=[],
                services=[],
                methods=[],
            ),
            _pb2_grpc=MypyStubContext.Pb2Grpc(
                module=context.pb2_grpc.module,
                builder=context.pb2_grpc.builder,
                enums=[],
                enum_values=[],
                messages=[],
                oneof_groups=[],
                fields=[],
                services=[],
                methods=[],
            ),
        )

    # def __build_extension_field(
    #     self,
    #     builder: ASTBuilder,
    #     field: FieldInfo,
    # ) -> ast.stmt:
    #     return builder.build_attr_stub(
    #         name=field.name,
    #         annotation=builder.build_generic_ref(
    #             TypeInfo.build(ModuleInfo.from_obj(extension), "ExtensionDescriptor"),
    #             field.annotation,
    #         ),
    #     )

    # def __build_service_descriptors(
    #     self,
    #     context: FileDescriptorContext[MypyStubContext],
    #     grpc: GRPCContext,
    # ) -> t.Sequence[ast.stmt]:
    #     builder = grpc.builder.__inner
    #
    #     return [
    #         builder.build_class_def(
    #             name=service.name,
    #             bases=[builder.build_ref(TypeInfo.from_type(ServiceDescriptor))],
    #             body=[
    #                 *(
    #                     builder.build_class_def(
    #                         name=method.name,
    #                         bases=[builder.build_ref(TypeInfo.from_type(MethodDescriptor))],
    #                         body=[
    #                             builder.build_attr_stub(
    #                                 name="name",
    #                                 annotation=builder.build_str_ref(),
    #                             ),
    #                             builder.build_attr_stub(
    #                                 name="full_name",
    #                                 annotation=builder.build_str_ref(),
    #                             ),
    #                             builder.build_attr_stub(
    #                                 name="index",
    #                                 annotation=builder.build_int_ref(),
    #                             ),
    #                             builder.build_attr_stub(
    #                                 name="containing_service",
    #                                 annotation=builder.build_int_ref(),
    #                             ),
    #                             builder.build_attr_stub(
    #                                 name="input_type",
    #                                 annotation=builder.build_int_ref(),
    #                             ),
    #                             builder.build_attr_stub(
    #                                 name="output_type",
    #                                 annotation=builder.build_int_ref(),
    #                             ),
    #                             builder.build_attr_stub(
    #                                 name="client_streaming",
    #                                 annotation=builder.build_int_ref(),
    #                             ),
    #                             builder.build_attr_stub(
    #                                 name="server_streaming",
    #                                 annotation=builder.build_int_ref(),
    #                             ),
    #                         ],
    #                         is_final=True,
    #                     )
    #                     for method in service.method
    #                 ),
    #                 builder.build_typed_dict_def(
    #                     name="_MethodsByName",
    #                     items={method.name: builder.build_name(method.name) for method in service.method},
    #                     is_final=True,
    #                 ),
    #             ],
    #             is_final=True,
    #         )
    #         for service in context.proto.service
    #     ]
    #
    # def __build_file_descriptor(
    #     self,
    #     context: FileDescriptorContext[MypyStubContext],
    #     message: MessageContext,
    #     # grpc: GRPCContext,
    # ) -> t.Sequence[ast.stmt]:
    #     builder = message.builder.__inner
    #
    #     return [
    #         builder.build_class_def(
    #             name="_FileDescriptor",
    #             bases=[
    #                 builder.build_ref(TypeInfo.from_type(FileDescriptor)),
    #             ],
    #             body=[
    #                 *(
    #                     builder.build_typed_dict_def(
    #                         name="_EnumTypesByName",
    #                         items={
    #                             enum_type.name: builder.build_type_ref(builder.build_name(enum_type.name))
    #                             for enum_type in context.proto.enum_type
    #                         },
    #                         is_final=True,
    #                     ),
    #                     builder.build_typed_dict_def(
    #                         name="_MessageTypesByName",
    #                         items={
    #                             message_type.name: builder.build_type_ref(builder.build_name(message_type.name))
    #                             for message_type in context.proto.message_type
    #                         },
    #                         is_final=True,
    #                     ),
    #                     builder.build_typed_dict_def(
    #                         name="_ServicesByName",
    #                         items={
    #                             service.name: builder.build_type_ref(builder.build_name(service.name))
    #                             for service in context.proto.service
    #                         },
    #                         is_final=True,
    #                     ),
    #                     # builder.build_typed_dict_def(
    #                     #     name="_ExtensionsByName",
    #                     #     items={field.name: ... for field in message.fields},
    #                     #     is_final=True,
    #                     # ),
    #                 ),
    #                 builder.build_attr_stub(
    #                     name="name",
    #                     annotation=builder.build_str_ref(),
    #                 ),
    #                 builder.build_attr_stub(
    #                     name="package",
    #                     annotation=builder.build_str_ref(),
    #                 ),
    #                 builder.build_attr_stub(
    #                     name="enum_types_by_name",
    #                     annotation=builder.build_name("_EnumTypesByName"),
    #                 ),
    #                 builder.build_attr_stub(
    #                     name="message_types_by_name",
    #                     annotation=builder.build_name("_MessageTypesByName"),
    #                 ),
    #                 builder.build_attr_stub(
    #                     name="services_by_name",
    #                     annotation=builder.build_name("_ServicesByName"),
    #                 ),
    #                 builder.build_attr_stub(
    #                     name="extensions_by_name",
    #                     annotation=builder.build_name("_ExtensionsByName"),
    #                 ),
    #             ],
    #             is_final=True,
    #         ),
    #         builder.build_attr_stub(
    #             name="DESCRIPTOR",
    #             annotation=builder.build_name("_FileDescriptor"),
    #             is_final=True,
    #         ),
    #     ]
