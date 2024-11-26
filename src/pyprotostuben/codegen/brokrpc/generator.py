import ast
import typing as t
from dataclasses import dataclass, field
from functools import cached_property
from itertools import chain

from pyprotostuben.codegen.module_ast import ModuleAstContext
from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.location import build_docstring
from pyprotostuben.protobuf.registry import TypeRegistry
from pyprotostuben.protobuf.visitor.abc import ProtoVisitorDecorator
from pyprotostuben.protobuf.visitor.decorator import T_contra
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
from pyprotostuben.python.ast_builder import ASTBuilder, ModuleDependencyResolver, TypeRef
from pyprotostuben.python.info import ModuleInfo, PackageInfo, TypeInfo
from pyprotostuben.string_case import camel2snake


@dataclass(frozen=True)
class MethodInfo:
    name: str
    qualname: str
    doc: t.Optional[str]
    server_input: TypeRef
    server_input_streaming: bool
    server_output: TypeRef
    server_output_streaming: bool


@dataclass(frozen=True)
class ServiceInfo:
    service: ast.stmt
    service_registrator: ast.stmt
    client: ast.stmt
    client_factory: ast.stmt


@dataclass()
class BrokRPCContext(ModuleAstContext):
    _module: t.Optional[ModuleInfo] = None
    _builder: t.Optional[ASTBuilder] = None
    services: t.MutableSequence[ServiceInfo] = field(default_factory=list)
    methods: t.MutableSequence[MethodInfo] = field(default_factory=list)

    @property
    def module(self) -> ModuleInfo:
        if self._module is None:
            raise ValueError
        return self._module

    @property
    def builder(self) -> ASTBuilder:
        if self._builder is None:
            raise ValueError
        return self._builder


class BrokRPCModuleGenerator(ProtoVisitorDecorator[BrokRPCContext], LoggerMixin):
    def __init__(self, registry: TypeRegistry) -> None:
        self.__registry = registry

    def enter_file(self, context: FileContext[BrokRPCContext]) -> None:
        context.meta = self.__create_root_context(context)

    def leave_file(self, context: FileContext[BrokRPCContext]) -> None:
        scope = context.meta

        if scope.services:
            context.meta.generated_modules.update(
                {
                    context.meta.module.file: context.meta.builder.build_module(
                        doc=f"Source: {context.file.proto_path}",
                        body=list(
                            chain.from_iterable(
                                (
                                    service.service,
                                    service.service_registrator,
                                    service.client,
                                    service.client_factory,
                                )
                                for service in scope.services
                            )
                        ),
                    ),
                }
            )

    def enter_enum(self, context: EnumContext[BrokRPCContext]) -> None:
        pass

    def leave_enum(self, context: EnumContext[BrokRPCContext]) -> None:
        pass

    def enter_enum_value(self, context: EnumValueContext[BrokRPCContext]) -> None:
        pass

    def leave_enum_value(self, context: EnumValueContext[BrokRPCContext]) -> None:
        pass

    def enter_descriptor(self, context: DescriptorContext[BrokRPCContext]) -> None:
        pass

    def leave_descriptor(self, context: DescriptorContext[BrokRPCContext]) -> None:
        pass

    def enter_oneof(self, context: OneofContext[BrokRPCContext]) -> None:
        pass

    def leave_oneof(self, context: OneofContext[BrokRPCContext]) -> None:
        pass

    def enter_field(self, context: FieldContext[BrokRPCContext]) -> None:
        pass

    def leave_field(self, context: FieldContext[BrokRPCContext]) -> None:
        pass

    def enter_service(self, context: ServiceContext[BrokRPCContext]) -> None:
        context.meta = self.__create_sub_context(context.meta)

    def leave_service(self, context: ServiceContext[BrokRPCContext]) -> None:
        proto = context.proto
        scope = context.meta
        parent = context.parent.meta

        service_class_name = f"{proto.name}Service"
        client_class_name = f"{proto.name}Client"

        parent.services.append(
            ServiceInfo(
                service=self.__build_service_def(context, service_class_name, scope.methods),
                service_registrator=self.__build_service_registrator_def(context, service_class_name, scope.methods),
                client=self.__build_client_def(context, client_class_name, scope.methods),
                client_factory=self.__build_client_factory_def(context, client_class_name, scope.methods),
            ),
        )

    def enter_method(self, context: MethodContext[BrokRPCContext]) -> None:
        pass

    def leave_method(self, context: MethodContext[BrokRPCContext]) -> None:
        proto = context.proto
        parent = context.meta

        parent.methods.append(
            MethodInfo(
                name=camel2snake(proto.name),
                qualname=f"/{context.root.proto.package}/{context.parent.proto.name}/{proto.name}",
                doc=build_docstring(context.location),
                server_input=self.__registry.resolve_proto_method_client_input(proto),
                server_input_streaming=proto.client_streaming,
                server_output=self.__registry.resolve_proto_method_server_output(proto),
                server_output_streaming=proto.server_streaming,
            )
        )

    def enter_extension(self, context: ExtensionContext[T_contra]) -> None:
        pass

    def leave_extension(self, context: ExtensionContext[T_contra]) -> None:
        pass

    def __create_root_context(self, context: FileContext[BrokRPCContext]) -> BrokRPCContext:
        file = context.file
        module = ModuleInfo(file.pb2_package, f"{file.name}_brokrpc")

        return BrokRPCContext(
            generated_modules=context.meta.generated_modules,
            _module=module,
            _builder=ASTBuilder(ModuleDependencyResolver(module)),
        )

    def __create_sub_context(self, context: BrokRPCContext) -> BrokRPCContext:
        return BrokRPCContext(
            generated_modules=context.generated_modules,
            _module=context.module,
            _builder=context.builder,
        )

    def __build_service_def(
        self,
        context: ServiceContext[BrokRPCContext],
        name: str,
        methods: t.Sequence[MethodInfo],
    ) -> ast.stmt:
        builder = context.meta.builder

        return builder.build_abstract_class_def(
            name=name,
            doc=build_docstring(context.location),
            body=[
                builder.build_abstract_method_def(
                    name=method.name,
                    args=[
                        builder.build_pos_arg(
                            name="request",
                            annotation=builder.build_generic_ref(self.__brokrpc_request, method.server_input),
                        )
                    ],
                    returns=method.server_output,
                    is_async=True,
                    doc=method.doc,
                )
                for method in methods
            ],
        )

    def __build_service_registrator_def(
        self,
        context: ServiceContext[BrokRPCContext],
        name: str,
        methods: t.Sequence[MethodInfo],
    ) -> ast.stmt:
        builder = context.meta.builder

        return builder.build_func_def(
            name=f"add_{camel2snake(name)}_to_server",
            args=[
                builder.build_pos_arg(
                    name="service",
                    annotation=builder.build_name(name),
                ),
                builder.build_pos_arg(
                    name="server",
                    annotation=builder.build_ref(self.__brokrpc_server),
                ),
            ],
            returns=builder.build_none_ref(),
            body=[
                builder.build_call_stmt(
                    func=builder.build_name("server", "register_unary_unary_handler"),
                    kwargs={
                        "func": builder.build_name("service", method.name),
                        "routing_key": builder.build_const(method.qualname),
                        "serializer": self.__build_serializer(builder, method),
                    },
                )
                for method in methods
            ],
        )

    def __build_client_def(
        self,
        context: ServiceContext[BrokRPCContext],
        name: str,
        methods: t.Sequence[MethodInfo],
    ) -> ast.stmt:
        builder = context.meta.builder

        return builder.build_class_def(
            name=name,
            doc=build_docstring(context.location),
            body=(
                self.__build_client_init(builder, methods),
                *(self.__build_client_call(builder, method) for method in methods),
            ),
        )

    def __build_client_init(self, builder: ASTBuilder, methods: t.Sequence[MethodInfo]) -> ast.stmt:
        return builder.build_init_def(
            args=[
                builder.build_pos_arg(
                    name=method.name,
                    annotation=builder.build_generic_ref(
                        self.__brokrpc_caller,
                        method.server_input,
                        method.server_output,
                    ),
                )
                for method in methods
            ],
            body=[
                builder.build_attr_assign(
                    "self",
                    f"__{method.name}",
                    value=builder.build_name(method.name),
                )
                for method in methods
            ],
        )

    def __build_client_call(self, builder: ASTBuilder, method: MethodInfo) -> ast.stmt:
        return builder.build_method_def(
            name=method.name,
            args=[
                builder.build_pos_arg(
                    name="request",
                    annotation=method.server_input,
                ),
            ],
            returns=builder.build_generic_ref(self.__brokrpc_response, method.server_output),
            doc=method.doc,
            body=[
                builder.build_return_stmt(
                    builder.build_call(
                        func=builder.build_name("self", f"__{method.name}", "invoke"),
                        args=[builder.build_name("request")],
                        is_async=True,
                    )
                ),
            ],
            is_async=True,
        )

    def __build_client_factory_def(
        self,
        context: ServiceContext[BrokRPCContext],
        name: str,
        methods: t.Sequence[MethodInfo],
    ) -> ast.stmt:
        builder = context.meta.builder

        return builder.build_func_def(
            name="create_client",
            args=[
                builder.build_pos_arg(
                    name="client",
                    annotation=builder.build_ref(self.__brokrpc_client),
                ),
            ],
            returns=builder.build_name(name),
            is_async=True,
            is_context_manager=True,
            body=[
                builder.build_with_stmt(
                    is_async=True,
                    items=[
                        (
                            method.name,
                            self.__build_client_caller_factory(context, method),
                        )
                        for method in methods
                    ],
                    body=[
                        builder.build_yield_stmt(
                            builder.build_call(
                                func=builder.build_name(name),
                                kwargs={method.name: builder.build_name(method.name) for method in methods},
                            )
                        )
                    ],
                ),
            ],
        )

    def __build_client_caller_factory(
        self,
        context: ServiceContext[BrokRPCContext],
        method: MethodInfo,
    ) -> ast.expr:
        builder = context.meta.builder

        return builder.build_call(
            func=builder.build_name("client", "unary_unary_caller"),
            kwargs={
                "routing_key": builder.build_const(method.qualname),
                "serializer": self.__build_serializer(builder, method),
            },
        )

    def __build_serializer(self, builder: ASTBuilder, method: MethodInfo) -> ast.expr:
        return builder.build_call(
            func=builder.build_ref(self.__brokrpc_serializer),
            args=[
                method.server_input,
                method.server_output,
            ],
        )

    @cached_property
    def __brokrpc(self) -> PackageInfo:
        return PackageInfo(None, "brokrpc")

    @cached_property
    def __brokrpc_rpc(self) -> PackageInfo:
        return PackageInfo(self.__brokrpc, "rpc")

    @cached_property
    def __brokrpc_server(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(self.__brokrpc_rpc, "server"), "Server")

    @cached_property
    def __brokrpc_client(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(self.__brokrpc_rpc, "client"), "Client")

    @cached_property
    def __brokrpc_caller(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(self.__brokrpc_rpc, "abc"), "Caller")

    @cached_property
    def __brokrpc_request(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(self.__brokrpc_rpc, "model"), "Request")

    @cached_property
    def __brokrpc_response(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(self.__brokrpc_rpc, "model"), "Response")

    @cached_property
    def __brokrpc_serializer(self) -> TypeInfo:
        return TypeInfo.build(
            ModuleInfo(PackageInfo(self.__brokrpc, "serializer"), "protobuf"), "RPCProtobufSerializer"
        )
