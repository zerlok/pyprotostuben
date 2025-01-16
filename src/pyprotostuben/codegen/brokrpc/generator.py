import ast
import sys
import typing as t
from dataclasses import dataclass, field
from functools import cached_property
from itertools import chain

# NOTE: brokrpc supports python 3.12 or higher
if sys.version_info >= (3, 12):
    from brokrpc.spec.v1.amqp_pb2 import ExchangeOptions as AmqpExchangeOptions
    from brokrpc.spec.v1.amqp_pb2 import ExchangeType as AmqpExchangeType
    from brokrpc.spec.v1.amqp_pb2 import QueueOptions as AmqpQueueOptions

    # TODO: find a better way to load only used extension modules in file descriptor.
    #  https://github.com/protocolbuffers/protobuf/issues/12049#issuecomment-1444187517
    # NOTE: Extension modules must be preloaded, so protoc plugins can use it. Extensions are parsed with
    # `CodeGeneratorRequest` protobuf message and  passed to protoc plugin.
    from brokrpc.spec.v1.amqp_pb2 import exchange as amqp_pb2_exchange_ext
    from brokrpc.spec.v1.amqp_pb2 import queue as amqp_pb2_queue_ext
    from brokrpc.spec.v1.consumer_pb2 import Void as AmqpConsumerVoid

else:
    AmqpExchangeType = t.Any
    AmqpExchangeOptions = t.Any
    AmqpQueueOptions = t.Any
    amqp_pb2_exchange_ext = t.Any
    amqp_pb2_queue_ext = t.Any
    AmqpConsumerVoid = t.Any

from pyprotostuben.codegen.module_ast import ModuleAstContext
from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.extension import get_extension
from pyprotostuben.protobuf.location import build_docstring
from pyprotostuben.protobuf.registry import MessageInfo, TypeRegistry
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
from pyprotostuben.python.ast_builder import ASTBuilder, FuncArgInfo, ModuleDependencyResolver, TypeRef
from pyprotostuben.python.info import ModuleInfo, PackageInfo, TypeInfo
from pyprotostuben.string_case import camel2snake


@dataclass(frozen=True)
class _BaseMethodInfo:
    name: str
    qualname: str
    doc: t.Optional[str]
    server_input: TypeRef
    server_input_streaming: bool
    amqp_queue_options: t.Optional[AmqpQueueOptions]


@dataclass(frozen=True)
class VoidMethodInfo(_BaseMethodInfo):
    pass


@dataclass(frozen=True)
class ReplyingMethodInfo(_BaseMethodInfo):
    server_output: TypeRef
    server_output_streaming: bool


MethodInfo = t.Union[VoidMethodInfo, ReplyingMethodInfo]


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

        amqp_exchange_options = get_extension(proto, amqp_pb2_exchange_ext)
        service_name = proto.name
        client_name = f"{service_name}Client"

        parent.services.append(
            ServiceInfo(
                service=self.__build_service_def(context, service_name, scope.methods),
                service_registrator=self.__build_service_registrator_def(
                    context=context,
                    service_name=service_name,
                    amqp_exchange_options=amqp_exchange_options,
                    methods=scope.methods,
                ),
                client=self.__build_client_def(context, client_name, scope.methods),
                client_factory=self.__build_client_factory_def(
                    context=context,
                    service_name=service_name,
                    client_name=client_name,
                    amqp_exchange_options=amqp_exchange_options,
                    methods=scope.methods,
                ),
            ),
        )

    def enter_method(self, context: MethodContext[BrokRPCContext]) -> None:
        pass

    def leave_method(self, context: MethodContext[BrokRPCContext]) -> None:
        proto = context.proto
        parent = context.meta

        name = camel2snake(proto.name)
        qualname = f"/{context.root.proto.package}/{context.parent.name}/{proto.name}"
        doc = build_docstring(context.location)
        server_input = self.__registry.resolve_proto_method_client_input(proto)
        server_output = self.__registry.resolve_proto_method_server_output(proto)
        amqp_queue_options = get_extension(proto, amqp_pb2_queue_ext)

        method: MethodInfo
        if server_output == self.__brokrpc_consumer_void:
            method = VoidMethodInfo(
                name=name,
                qualname=qualname,
                doc=doc,
                server_input=server_input,
                server_input_streaming=proto.client_streaming,
                amqp_queue_options=amqp_queue_options,
            )

        else:
            method = ReplyingMethodInfo(
                name=name,
                qualname=qualname,
                doc=doc,
                server_input=server_input,
                server_input_streaming=proto.client_streaming,
                server_output=server_output,
                server_output_streaming=proto.server_streaming,
                amqp_queue_options=amqp_queue_options,
            )

        parent.methods.append(method)

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
        service_name: str,
        methods: t.Sequence[MethodInfo],
    ) -> ast.stmt:
        builder = context.meta.builder

        return builder.build_abstract_class_def(
            name=service_name,
            doc=build_docstring(context.location),
            body=[self.__build_service_method_def(builder, method) for method in methods],
        )

    def __build_service_method_def(self, builder: ASTBuilder, method: MethodInfo) -> ast.stmt:
        if isinstance(method, VoidMethodInfo):
            return builder.build_abstract_method_def(
                name=method.name,
                args=[
                    builder.build_pos_arg(
                        name="message",
                        annotation=builder.build_generic_ref(self.__brokrpc_message, method.server_input),
                    ),
                ],
                returns=self.__brokrpc_consumer_result,
                is_async=True,
                doc=method.doc,
            )

        elif isinstance(method, ReplyingMethodInfo):
            return builder.build_abstract_method_def(
                name=method.name,
                args=[
                    builder.build_pos_arg(
                        name="request",
                        annotation=builder.build_generic_ref(self.__brokrpc_request, method.server_input),
                    ),
                ],
                returns=method.server_output,
                is_async=True,
                doc=method.doc,
            )

        else:
            t.assert_never(method)

    def __build_service_registrator_def(
        self,
        context: ServiceContext[BrokRPCContext],
        service_name: str,
        amqp_exchange_options: t.Optional[AmqpExchangeOptions],
        methods: t.Sequence[MethodInfo],
    ) -> ast.stmt:
        builder = context.meta.builder

        return builder.build_func_def(
            name=f"add_{camel2snake(service_name)}_to_server",
            args=[
                builder.build_pos_arg(
                    name="service",
                    annotation=builder.build_name(service_name),
                ),
                builder.build_pos_arg(
                    name="server",
                    annotation=builder.build_ref(self.__brokrpc_server),
                ),
            ],
            returns=builder.build_none_ref(),
            body=[
                self.__build_service_registrator_method_call(builder, method, amqp_exchange_options)
                for method in methods
            ],
        )

    def __build_service_registrator_method_call(
        self,
        builder: ASTBuilder,
        method: MethodInfo,
        amqp_exchange_options: t.Optional[AmqpExchangeOptions],
    ) -> ast.stmt:
        func = builder.build_name("service", method.name)
        routing_key = builder.build_const(method.qualname)
        serializer = self.__build_serializer(builder, method)
        exchange = self.__build_exchange_options(builder, amqp_exchange_options)
        queue = self.__build_queue_options(builder, method.qualname, method.amqp_queue_options)

        if isinstance(method, VoidMethodInfo):
            return builder.build_call_stmt(
                func=builder.build_name("server", "register_consumer"),
                kwargs={
                    "func": func,
                    "routing_key": routing_key,
                    "serializer": serializer,
                    "exchange": exchange,
                    "queue": queue,
                },
            )

        elif isinstance(method, ReplyingMethodInfo):
            return builder.build_call_stmt(
                func=builder.build_name("server", "register_unary_unary_handler"),
                kwargs={
                    "func": func,
                    "routing_key": routing_key,
                    "serializer": serializer,
                    "exchange": exchange,
                    "queue": queue,
                },
            )

        else:
            t.assert_never(method)

    def __build_client_def(
        self,
        context: ServiceContext[BrokRPCContext],
        client_name: str,
        methods: t.Sequence[MethodInfo],
    ) -> ast.stmt:
        builder = context.meta.builder

        return builder.build_class_def(
            name=client_name,
            doc=build_docstring(context.location),
            body=(
                self.__build_client_init(builder, methods),
                *(self.__build_client_method_def(builder, method) for method in methods),
            ),
        )

    def __build_client_init(self, builder: ASTBuilder, methods: t.Sequence[MethodInfo]) -> ast.stmt:
        return builder.build_init_def(
            args=[self.__build_client_init_arg(builder, method) for method in methods],
            body=[
                builder.build_attr_assign(
                    "self",
                    f"__{method.name}",
                    value=builder.build_name(method.name),
                )
                for method in methods
            ],
        )

    def __build_client_init_arg(self, builder: ASTBuilder, method: MethodInfo) -> FuncArgInfo:
        if isinstance(method, VoidMethodInfo):
            return builder.build_pos_arg(
                name=method.name,
                annotation=builder.build_generic_ref(
                    self.__brokrpc_publisher,
                    method.server_input,
                    self.__brokrpc_publisher_result,
                ),
            )

        elif isinstance(method, ReplyingMethodInfo):
            return builder.build_pos_arg(
                name=method.name,
                annotation=builder.build_generic_ref(
                    self.__brokrpc_caller,
                    method.server_input,
                    method.server_output,
                ),
            )

        else:
            t.assert_never(method)

    def __build_client_method_def(self, builder: ASTBuilder, method: MethodInfo) -> ast.stmt:
        if isinstance(method, VoidMethodInfo):
            return builder.build_method_def(
                name=method.name,
                args=[
                    builder.build_pos_arg(
                        name="message",
                        annotation=method.server_input,
                    ),
                ],
                returns=builder.build_none_ref(),
                doc=method.doc,
                body=[
                    builder.build_call_stmt(
                        func=builder.build_name("self", f"__{method.name}", "publish"),
                        args=[builder.build_name("message")],
                        is_async=True,
                    ),
                ],
                is_async=True,
            )

        elif isinstance(method, ReplyingMethodInfo):
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

        else:
            t.assert_never(method)

    def __build_client_factory_def(
        self,
        context: ServiceContext[BrokRPCContext],
        service_name: str,
        client_name: str,
        amqp_exchange_options: t.Optional[AmqpExchangeOptions],
        methods: t.Sequence[MethodInfo],
    ) -> ast.stmt:
        builder = context.meta.builder

        return builder.build_func_def(
            name=f"create_{camel2snake(service_name)}_client",
            args=[
                builder.build_pos_arg(
                    name="client",
                    annotation=builder.build_ref(self.__brokrpc_client),
                ),
            ],
            returns=builder.build_name(client_name),
            is_async=True,
            is_context_manager=True,
            body=[
                builder.build_with_stmt(
                    is_async=True,
                    items=[
                        (
                            method.name,
                            self.__build_client_caller_factory(context, amqp_exchange_options, method),
                        )
                        for method in methods
                    ],
                    body=[
                        builder.build_yield_stmt(
                            builder.build_call(
                                func=builder.build_name(client_name),
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
        amqp_exchange_options: t.Optional[AmqpExchangeOptions],
        method: MethodInfo,
    ) -> ast.expr:
        builder = context.meta.builder

        routing_key = builder.build_const(method.qualname)
        serializer = self.__build_serializer(builder, method)
        exchange = self.__build_exchange_options(builder, amqp_exchange_options)

        if isinstance(method, VoidMethodInfo):
            return builder.build_call(
                func=builder.build_name("client", "publisher"),
                kwargs={
                    "routing_key": routing_key,
                    "serializer": serializer,
                    "exchange": exchange,
                },
            )

        elif isinstance(method, ReplyingMethodInfo):
            return builder.build_call(
                func=builder.build_name("client", "unary_unary_caller"),
                kwargs={
                    "routing_key": routing_key,
                    "serializer": serializer,
                    "exchange": exchange,
                },
            )

        else:
            t.assert_never(method)

    def __build_serializer(self, builder: ASTBuilder, method: MethodInfo) -> ast.expr:
        if isinstance(method, VoidMethodInfo):
            return builder.build_call(
                func=builder.build_ref(self.__brokrpc_serializer),
                args=[method.server_input],
            )

        elif isinstance(method, ReplyingMethodInfo):
            return builder.build_call(
                func=builder.build_ref(self.__brokrpc_rpc_serializer),
                args=[method.server_input, method.server_output],
            )

        else:
            t.assert_never(method)

    def __build_exchange_options(
        self,
        builder: ASTBuilder,
        amqp_exchange_options: t.Optional[AmqpExchangeOptions],
    ) -> ast.expr:
        if amqp_exchange_options is None:
            return builder.build_none_ref()

        return builder.build_call(
            func=builder.build_ref(self.__brokrpc_exchange_options),
            kwargs={
                "name": builder.build_const(
                    amqp_exchange_options.name if amqp_exchange_options.HasField("name") else None
                ),
                "type": builder.build_const(
                    self.__brokrpc_exchange_type_map[amqp_exchange_options.type]
                    if amqp_exchange_options.HasField("type")
                    else None
                ),
                "durable": builder.build_const(
                    amqp_exchange_options.durable if amqp_exchange_options.HasField("durable") else None
                ),
                "auto_delete": builder.build_const(
                    amqp_exchange_options.auto_delete if amqp_exchange_options.HasField("auto_delete") else None
                ),
            },
        )

    def __build_queue_options(
        self,
        builder: ASTBuilder,
        method_qualname: str,
        amqp_queue_options: t.Optional[AmqpQueueOptions],
    ) -> ast.expr:
        return builder.build_call(
            func=builder.build_ref(self.__brokrpc_queue_options),
            kwargs={
                "name": builder.build_const(
                    amqp_queue_options.name
                    if amqp_queue_options is not None and amqp_queue_options.HasField("name")
                    else method_qualname
                ),
                "durable": builder.build_const(
                    amqp_queue_options.durable
                    if amqp_queue_options is not None and amqp_queue_options.HasField("durable")
                    else None
                ),
                "exclusive": builder.build_const(
                    amqp_queue_options.exclusive
                    if amqp_queue_options is not None and amqp_queue_options.HasField("exclusive")
                    else None
                ),
                "auto_delete": builder.build_const(
                    amqp_queue_options.auto_delete
                    if amqp_queue_options is not None and amqp_queue_options.HasField("auto_delete")
                    else None
                ),
            },
        )

    @cached_property
    def __brokrpc(self) -> PackageInfo:
        return PackageInfo(None, "brokrpc")

    @cached_property
    def __brokrpc_rpc(self) -> PackageInfo:
        return PackageInfo(self.__brokrpc, "rpc")

    @cached_property
    def __brokrpc_consumer(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(self.__brokrpc, "abc"), "Consumer")

    @cached_property
    def __brokrpc_consumer_result(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(self.__brokrpc, "model"), "ConsumerResult")

    @cached_property
    def __brokrpc_publisher(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(self.__brokrpc, "abc"), "Publisher")

    @cached_property
    def __brokrpc_publisher_result(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(self.__brokrpc, "model"), "PublisherResult")

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
    def __brokrpc_message(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(self.__brokrpc, "message"), "Message")

    @cached_property
    def __brokrpc_request(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(self.__brokrpc_rpc, "model"), "Request")

    @cached_property
    def __brokrpc_response(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(self.__brokrpc_rpc, "model"), "Response")

    @cached_property
    def __brokrpc_serializer(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(PackageInfo(self.__brokrpc, "serializer"), "protobuf"), "ProtobufSerializer")

    @cached_property
    def __brokrpc_rpc_serializer(self) -> TypeInfo:
        return TypeInfo.build(
            ModuleInfo(PackageInfo(self.__brokrpc, "serializer"), "protobuf"), "RPCProtobufSerializer"
        )

    @cached_property
    def __brokrpc_exchange_options(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(self.__brokrpc, "options"), "ExchangeOptions")

    @cached_property
    def __brokrpc_queue_options(self) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(self.__brokrpc, "options"), "QueueOptions")

    @cached_property
    def __brokrpc_exchange_type_map(self) -> t.Mapping[int, t.Optional[str]]:
        return {
            AmqpExchangeType.EXCHANGE_TYPE_UNSPECIFIED: None,
            AmqpExchangeType.EXCHANGE_TYPE_DIRECT: "direct",
            AmqpExchangeType.EXCHANGE_TYPE_FANOUT: "fanout",
            AmqpExchangeType.EXCHANGE_TYPE_TOPIC: "topic",
            AmqpExchangeType.EXCHANGE_TYPE_HEADER: "header",
        }

    @cached_property
    def __brokrpc_consumer_void(self) -> MessageInfo:
        return MessageInfo.from_type(AmqpConsumerVoid)
