import ast
import enum
import itertools
import typing as t
from dataclasses import dataclass

from pyprotostuben.codegen.servicify.abc import ServicifyCodeGenerator
from pyprotostuben.codegen.servicify.model import EntrypointInfo, GeneratedFile, GeneratorContext, MethodInfo
from pyprotostuben.python.builder import ModuleASTBuilder, PackageASTBuilder
from pyprotostuben.python.info import ModuleInfo, PackageInfo, TypeInfo
from pyprotostuben.string_case import camel2snake, snake2camel


class GenTrait:
    def get_interface_type(self, entrypoint: EntrypointInfo) -> TypeInfo:
        return TypeInfo.build(ModuleInfo(None, "abc"), snake2camel(entrypoint.name.title()))

    def get_type(self, package: str, module: str, name: str) -> TypeInfo:
        return TypeInfo.build(
            ModuleInfo(PackageInfo.build(*self.get_root_pkg().parts, package, self.__entrypoint.name), module),
            name,
        )

    # def get_server_model_type(self, method: MethodInfo, suffix: str) -> TypeInfo:
    #     return self._get_type_info("server", "model", f"{method.name}{suffix}")
    #
    # def get_server_serializer_type(self, method: MethodInfo, suffix: str) -> TypeInfo:
    #     return self._get_type_info("server", "serializer", f"{method.name}{suffix}")
    #
    # def get_server_impl_type(self) -> TypeInfo:
    #     return self._get_type_info("server", "entrypoint", f"{self.__entrypoint.name}Impl")
    #
    # def get_client_model_type(self, method: MethodInfo, suffix: str) -> TypeInfo:
    #     return self._get_type_info("client", "model", f"{method.name}{suffix}")
    #
    # def get_client_serializer_type(self, method: MethodInfo, suffix: str) -> TypeInfo:
    #     return self._get_type_info("client", "serializer", f"{method.name}{suffix}")
    #
    # def get_client_impl_type(self) -> TypeInfo:
    #     return self._get_type_info("client", "entrypoint", f"{self.__entrypoint.name}Impl")


@dataclass(frozen=True, kw_only=True)
class _BaseBrokRPCMethodSpec:
    entrypoint: EntrypointInfo
    method: MethodInfo
    # trait: GenTrait

    @property
    def parts(self) -> t.Sequence[str]:
        type_ = self.entrypoint.type_
        module = type_.module
        return *(module.parts if module is not None else ()), *type_.ns, self.method.name


@dataclass(frozen=True, kw_only=True)
class BrokRPCConsumerMethodSpec(_BaseBrokRPCMethodSpec):
    pass


@dataclass(frozen=True, kw_only=True)
class BrokRPCRequestResponseMethodSpec(_BaseBrokRPCMethodSpec):
    class Kind(enum.Enum):
        UNARY_UNARY = enum.auto()
        STREAM_UNARY = enum.auto()
        UNARY_STREAM = enum.auto()
        STREAM_STREAM = enum.auto()

    kind: Kind


BrokRPCMethodSpec = t.Union[BrokRPCConsumerMethodSpec, BrokRPCRequestResponseMethodSpec]


@dataclass(frozen=True, kw_only=True)
class BrokRPCEntrypointSpec:
    entrypoint: EntrypointInfo
    methods: t.Sequence[BrokRPCMethodSpec]


# TODO: try to reuse this code in protobuf brokrpc generator. Use some kind of factory to inject custom module naming
#  (protobuf message types & serializer_module).
class BrokRPCServicifyCodeGenerator(ServicifyCodeGenerator):
    def generate(self, context: GeneratorContext) -> t.Sequence[GeneratedFile]:
        builder = PackageASTBuilder(PackageInfo(None, context.package or "api"))
        specs: t.Sequence[BrokRPCEntrypointSpec] = list(self.__build_entrypoint_specs(context))

        self.__build_abc_module(GenTrait(), builder, specs)

        return [
            GeneratedFile(
                path=context.output.joinpath(module.file),
                content=ast.unparse(body),
            )
            for module, body in builder.build()
        ]

        # # TODO: repeat domain project root_pkg structure
        # return [
        #     *(
        #         self.__gen_package(context, pkg)
        #         for pkg in (
        #             # mod_manager.get_root_pkg(),
        #             # mod_manager.get_server_pkg(),
        #             # mod_manager.get_client_pkg(),
        #         )
        #     ),
        #     *self.__build_serializer_modules(context, specs),
        #     *self.__build_server_modules(context, specs),
        #     *self.__build_client_modules(context, specs),
        # ]

    def __build_entrypoint_specs(self, context: GeneratorContext) -> t.Iterable[BrokRPCEntrypointSpec]:
        for entrypoint in context.entrypoints:
            if not entrypoint.methods:
                continue

            yield BrokRPCEntrypointSpec(
                entrypoint=entrypoint,
                methods=tuple(self.__build_method_spec(context, entrypoint, method) for method in entrypoint.methods),
            )

    def __build_method_spec(
        self,
        context: GeneratorContext,
        entrypoint: EntrypointInfo,
        method: MethodInfo,
    ) -> BrokRPCMethodSpec:
        # trait = GenTrait(context, entrypoint)

        if method.returns is None:
            return BrokRPCConsumerMethodSpec(
                entrypoint=entrypoint,
                method=method,
                # trait=trait,
            )

        else:
            return BrokRPCRequestResponseMethodSpec(
                entrypoint=entrypoint,
                method=method,
                # TODO: support all kinds
                kind=BrokRPCRequestResponseMethodSpec.Kind.UNARY_UNARY,
                # trait=trait,
            )

    def __build_abc_module(
        self,
        trait: GenTrait,
        pkg_builder: PackageASTBuilder,
        specs: t.Sequence[BrokRPCEntrypointSpec],
    ) -> None:
        trait.get_interface_type()

        builder = pkg_builder.module(ModuleInfo(None, "abc"))

        builder.build(
            body=[
                builder.abstract_class_def(
                    name=spec.entrypoint.name,
                    body=[
                        builder.abstract_method_def(
                            name=method.method.name,
                            args=[
                                builder.pos_arg(
                                    name="event" if isinstance(method, BrokRPCConsumerMethodSpec) else "request",
                                    annotation=builder.int_ref(),
                                )
                            ],
                            returns=trait.get_type("wtf", "model", method.method.name),
                            is_async=True,
                        )
                        for method in spec.methods
                    ],
                )
                for spec in specs
            ],
        )

    # TODO: separate server & client serializer_module
    def __build_serializer_module(
        self,
        context: GeneratorContext,
        info: ModuleInfo,
        specs: t.Sequence[BrokRPCMethodSpec],
    ) -> GeneratedFile:
        builder = self.__get_builder(info)

        body = builder.build(
            body=list(itertools.chain.from_iterable(self.__build_method_serializers(spec, builder) for spec in specs))
        )

        return self.__gen_module(context, info, body)

    def __build_server_module(
        self,
        context: GeneratorContext,
        info: ModuleInfo,
        specs: t.Sequence[BrokRPCEntrypointSpec],
    ) -> GeneratedFile:
        builder = self.__get_builder(info)

        body = builder.build(
            body=list(
                itertools.chain.from_iterable(
                    (
                        builder.func_def(
                            name=f"register_{camel2snake(spec.name.title())}",
                            args=[
                                builder.pos_arg(
                                    name="entrypoint",
                                    annotation=builder.attr(spec.name),
                                ),
                                builder.pos_arg(
                                    name="server",
                                    annotation=builder.ref(TypeInfo.from_str("brokrpc.rpc.server:Server")),
                                ),
                            ],
                            returns=builder.none_ref(),
                            body=[
                                self.__build_server_method_register_stmt(method, builder)
                                for group, methods in spec.groups.items()
                                for method in methods
                            ],
                        ),
                    )
                    for spec in specs
                )
            ),
        )

        return self.__gen_module(context, info, body)

    def __build_client_module(
        self,
        context: GeneratorContext,
        info: ModuleInfo,
        specs: t.Sequence[BrokRPCEntrypointSpec],
    ) -> GeneratedFile:
        builder = self.__get_builder(info)

        body = builder.build(
            body=[self.__build_client_class(spec, builder) for spec in specs],
        )

        return self.__gen_module(context, info, body)

    def __build_method_serializers(self, spec: BrokRPCMethodSpec, builder: ModuleASTBuilder) -> t.Iterable[ast.stmt]:
        return (
            builder.class_def(
                name=spec.request_name,
                bases=[TypeInfo.from_str("brokrpc.rpc.abc:RPCSerializer")],
                body=[
                    builder.attr_stub(
                        name=param.name,
                        annotation=TypeInfo.from_type(param.annotation),
                    )
                    for param in spec.request_params
                ],
            ),
            builder.class_def(
                name=spec.response_name,
                bases=[TypeInfo.from_str("brokrpc.rpc.abc:RPCSerializer")],
                body=[builder.pass_stmt()],
            ),
        )

    def __build_server_method_register_stmt(self, spec: BrokRPCMethodSpec, builder: ModuleASTBuilder) -> ast.stmt:
        registrator: str

        if isinstance(spec, BrokRPCConsumerMethodSpec):
            registrator = "register_consumer"

        elif isinstance(spec, BrokRPCRequestResponseMethodSpec):
            if spec.kind is BrokRPCRequestResponseMethodSpec.Kind.UNARY_UNARY:
                registrator = "register_unary_unary_handler"

            elif spec.kind is BrokRPCRequestResponseMethodSpec.Kind.STREAM_UNARY:
                registrator = "register_stream_unary_handler"

            elif spec.kind is BrokRPCRequestResponseMethodSpec.Kind.UNARY_STREAM:
                registrator = "register_unary_stream_handler"

            elif spec.kind is BrokRPCRequestResponseMethodSpec.Kind.STREAM_STREAM:
                registrator = "register_stream_stream_handler"

            else:
                t.assert_never(spec.kind)

        else:
            t.assert_never(spec.kind)

        return builder.call_stmt(
            func=builder.attr("server", registrator),
            kwargs={
                "func": builder.attr("entrypoint", spec.method.name),
                "routing_key": builder.const("/".join(spec.parts)),
                "serializer": builder.ref(spec.server_serializer),
            },
        )

    def __build_client_class(self, spec: BrokRPCEntrypointSpec, builder: ModuleASTBuilder) -> ast.stmt:
        name = f"{snake2camel(spec.name.title())}Client"

        return builder.class_def(
            name=name,
            body=[
                builder.class_method_def(
                    name="create",
                    args=[
                        builder.pos_arg(
                            name="client",
                            annotation=builder.ref(TypeInfo.from_str("brokrpc.rpc.client:Client")),
                        ),
                    ],
                    returns=builder.const(name),
                    is_async=True,
                    is_context_manager=True,
                    body=[
                        builder.with_stmt(
                            items=[
                                (
                                    spec.name,
                                    self.__build_client_method_caller_register_stmt(method, builder),
                                )
                                for group, methods in spec.groups.items()
                                for method in methods
                            ],
                            body=[
                                builder.yield_stmt(
                                    value=builder.call(
                                        func=builder.attr("cls"),
                                        kwargs={
                                            method.name: builder.attr(method.name)
                                            for group, methods in spec.groups.items()
                                            for method in methods
                                        },
                                    )
                                ),
                            ],
                            is_async=True,
                        ),
                    ],
                ),
                builder.init_attrs_def(
                    args=[
                        builder.pos_arg(
                            name=spec.name,
                            annotation=self.__build_client_method_caller_type(method, builder),
                        )
                        for group, methods in spec.groups.items()
                        for method in methods
                    ],
                ),
                *(
                    self.__build_client_method_caller_def(method, builder)
                    for group, methods in spec.groups.items()
                    for method in methods
                ),
            ],
        )

    def __build_client_method_caller_register_stmt(
        self, spec: BrokRPCMethodSpec, builder: ModuleASTBuilder
    ) -> ast.expr:
        registrator: str

        if isinstance(spec, BrokRPCConsumerMethodSpec):
            registrator = "publisher"

        elif isinstance(spec, BrokRPCRequestResponseMethodSpec):
            if spec.kind is BrokRPCRequestResponseMethodSpec.Kind.UNARY_UNARY:
                registrator = "unary_unary_caller"

            elif spec.kind is BrokRPCRequestResponseMethodSpec.Kind.STREAM_UNARY:
                registrator = "stream_unary_caller"

            elif spec.kind is BrokRPCRequestResponseMethodSpec.Kind.UNARY_STREAM:
                registrator = "unary_stream_caller"

            elif spec.kind is BrokRPCRequestResponseMethodSpec.Kind.STREAM_STREAM:
                registrator = "stream_stream_caller"

            else:
                t.assert_never(spec.kind)

        else:
            t.assert_never(spec.kind)

        return builder.call(
            func=builder.attr("client", registrator),
            kwargs={
                "routing_key": builder.const("/".join(spec.parts)),
                "serializer": builder.ref(spec.client_serializer),
            },
        )

    def __build_client_method_caller_type(self, spec: BrokRPCMethodSpec, builder: ModuleASTBuilder) -> ast.expr:
        if isinstance(spec, BrokRPCConsumerMethodSpec):
            return builder.generic_ref(
                TypeInfo.from_str("brokrpc.abc:Publisher"), builder.attr(spec.name), builder.none_ref()
            )

        elif isinstance(spec, BrokRPCRequestResponseMethodSpec):
            return builder.generic_ref(
                TypeInfo.from_str("brokrpc.rpc.abc:Caller"),
                builder.attr(spec.request_name),
                builder.attr(spec.response_name),
            )

        else:
            t.assert_never(spec.kind)

    def __build_client_method_caller_def(self, spec: BrokRPCMethodSpec, builder: ModuleASTBuilder) -> ast.stmt:
        if isinstance(spec, BrokRPCConsumerMethodSpec):
            return builder.method_def(
                name=spec.name,
                args=[builder.pos_arg(name="event", annotation=spec.input_info)],
                body=[
                    builder.call_stmt(
                        func=builder.attr("self", f"__{spec.name}", "publish"),
                        args=[builder.attr("event")],
                        is_async=True,
                    ),
                ],
                returns=builder.none_ref(),
                is_async=True,
            )

        elif isinstance(spec, BrokRPCRequestResponseMethodSpec):
            return builder.method_def(
                name=spec.name,
                args=[builder.pos_arg(name="request", annotation=spec.request_info)],
                body=[
                    builder.return_stmt(
                        value=builder.call(
                            func=builder.attr("self", f"__{spec.name}", "invoke"),
                            args=[builder.attr("request")],
                            is_async=True,
                        ),
                    )
                ],
                returns=spec.response_info,
                is_async=True,
            )

        else:
            t.assert_never(spec.kind)
