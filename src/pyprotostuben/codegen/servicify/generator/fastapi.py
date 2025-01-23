import inspect
import typing as t

from pyprotostuben.codegen.model import ModelASTBuilder, PydanticModelFactory
from pyprotostuben.codegen.servicify.abc import ServicifyCodeGenerator
from pyprotostuben.codegen.servicify.model import (
    EntrypointInfo,
    GeneratedFile,
    GeneratorContext,
    MethodInfo,
    StreamStreamMethodInfo,
    UnaryUnaryMethodInfo,
)
from pyprotostuben.python.builder2 import (
    AttrASTBuilder,
    ClassBodyASTBuilder,
    Expr,
    FuncBodyASTBuilder,
    ModuleASTBuilder,
    PackageASTBuilder,
    ScopeASTBuilder,
    TypeInfoProvider,
    TypeRef,
    package,
    render,
)
from pyprotostuben.python.info import ModuleInfo, TypeInfo
from pyprotostuben.string_case import camel2snake, snake2camel


class FastAPITypeRegistry:
    def __init__(self, context: GeneratorContext, builder: ModuleASTBuilder) -> None:
        self.__builder = ModelASTBuilder(builder, PydanticModelFactory())
        self.__builder.update(set(self.__iter_types(context)))

        self.__requests = dict[tuple[str, str], TypeInfoProvider]()
        self.__responses = dict[tuple[str, str], TypeInfoProvider]()

    def get_request(self, entrypoint: EntrypointInfo, method: MethodInfo) -> TypeInfoProvider:
        return self.__requests[(entrypoint.name, method.name)]

    def get_response(self, entrypoint: EntrypointInfo, method: MethodInfo) -> t.Optional[TypeInfoProvider]:
        return self.__responses.get((entrypoint.name, method.name))

    def request_param_unpack_expr(
        self,
        source: AttrASTBuilder,
        param: inspect.Parameter,
        builder: FuncBodyASTBuilder,
    ) -> Expr:
        return self.__builder.assign_expr(source.attr(param.name), param.annotation, "original", builder)

    def response_payload_pack_expr(
        self,
        source: AttrASTBuilder,
        annotation: type[object],
        builder: FuncBodyASTBuilder,
    ) -> Expr:
        return self.__builder.assign_expr(source, annotation, "model", builder)

    def register_request(
        self,
        entrypoint: EntrypointInfo,
        method: MethodInfo,
        fields: t.Mapping[str, type[object]],
        doc: t.Optional[str],
    ) -> None:
        model_ref = self.__builder.create_def(self.__create_model_name(entrypoint, method, "Request"), fields, doc)
        # TODO: remove assert
        assert isinstance(model_ref, TypeInfoProvider)
        self.__requests[(entrypoint.name, method.name)] = model_ref

    def register_response(
        self,
        entrypoint: EntrypointInfo,
        method: MethodInfo,
        fields: t.Mapping[str, type[object]],
        doc: t.Optional[str],
    ) -> None:
        model_ref = self.__builder.create_def(self.__create_model_name(entrypoint, method, "Response"), fields, doc)
        # TODO: remove assert
        assert isinstance(model_ref, TypeInfoProvider)
        self.__responses[(entrypoint.name, method.name)] = model_ref

    def __create_model_name(
        self,
        entrypoint: EntrypointInfo,
        method: MethodInfo,
        suffix: str,
    ) -> str:
        return "".join(snake2camel(s) for s in (entrypoint.name, method.name, suffix))

    @staticmethod
    def __iter_types(context: GeneratorContext) -> t.Iterable[type[object]]:
        for entrypoint in context.entrypoints:
            for method in entrypoint.methods:
                if isinstance(method, UnaryUnaryMethodInfo):
                    for param in method.params:
                        yield param.annotation

                    if method.returns is not None:
                        yield method.returns

                elif isinstance(method, StreamStreamMethodInfo):
                    yield method.input_.annotation
                    if method.output is not None:
                        yield method.output

                else:
                    t.assert_never(method)


class FastAPIServicifyCodeGenerator(ServicifyCodeGenerator):
    def generate(self, context: GeneratorContext) -> t.Sequence[GeneratedFile]:
        with package(context.package or "api") as pkg:
            with pkg.init():
                pass

            registry = self.__build_model_module(context, pkg)
            self.__build_server_module(context, pkg, registry)
            self.__build_client_module(context, pkg, registry)

        return [
            GeneratedFile(
                path=context.output.joinpath(module.file),
                content=render(body),
            )
            for module, body in pkg.build().items()
        ]

    def __build_model_module(
        self,
        context: GeneratorContext,
        pkg: PackageASTBuilder,
    ) -> FastAPITypeRegistry:
        with pkg.module("model") as mod:
            registry = FastAPITypeRegistry(context, mod)

            for entrypoint in context.entrypoints:
                for method in entrypoint.methods:
                    if isinstance(method, UnaryUnaryMethodInfo):
                        registry.register_request(
                            entrypoint=entrypoint,
                            method=method,
                            fields={param.name: param.annotation for param in method.params},
                            doc=f"Request model for `{entrypoint.name}.{method.name}` entrypoint method",
                        )

                        if method.returns is not None:
                            registry.register_response(
                                entrypoint=entrypoint,
                                method=method,
                                fields={"payload": method.returns},
                                doc=f"Response model for `{entrypoint.name}.{method.name}` entrypoint method",
                            )

                    elif isinstance(method, StreamStreamMethodInfo):
                        registry.register_request(
                            entrypoint=entrypoint,
                            method=method,
                            fields={method.input_.name: method.input_.annotation},
                            doc=f"Request model for `{entrypoint.name}.{method.name}` entrypoint method",
                        )

                        if method.output is not None:
                            registry.register_response(
                                entrypoint=entrypoint,
                                method=method,
                                fields={"payload": method.output},
                                doc=f"Response model for `{entrypoint.name}.{method.name}` entrypoint method",
                            )

                    else:
                        t.assert_never(method)

        return registry

    def __build_server_module(
        self,
        context: GeneratorContext,
        pkg: PackageASTBuilder,
        registry: FastAPITypeRegistry,
    ) -> None:
        with pkg.module("server") as _:
            for entrypoint in context.entrypoints:
                with _.class_def(f"{snake2camel(entrypoint.name)}Handler") as handler_def:
                    with handler_def.init_self_attrs_def({"impl": entrypoint.type_}):
                        pass

                    for method in entrypoint.methods:
                        self.__build_server_handler_method(handler_def, registry, entrypoint, method)

                self.__build_server_entrypoint_router(_, entrypoint, handler_def)

    def __build_server_router_method(self, builder: ScopeASTBuilder, method: MethodInfo) -> None:
        _ = builder

        if isinstance(method, UnaryUnaryMethodInfo):
            _.append(
                _.attr("router", "post")
                .call()
                .kwarg("path", _.const(f"/{method.name}"))
                .kwarg("description", _.const(method.doc) if method.doc is not None else _.none())
                .call()
                .arg(_.attr("entrypoint", method.name))
            )

        elif isinstance(method, StreamStreamMethodInfo):
            _.append(
                _.attr("router", "websocket")
                .call()
                .kwarg("path", _.const(f"/{method.name}"))
                .call()
                .arg(_.attr("entrypoint", method.name))
            )

        else:
            t.assert_never(method)

    def __build_server_handler_method(
        self,
        _: ClassBodyASTBuilder,
        registry: FastAPITypeRegistry,
        entrypoint: EntrypointInfo,
        method: MethodInfo,
    ) -> None:
        if isinstance(method, UnaryUnaryMethodInfo):
            self.__build_server_handler_method_unary_unary(_, registry, entrypoint, method)

        elif isinstance(method, StreamStreamMethodInfo):
            self.__build_server_handler_method_stream_stream(_, registry, entrypoint, method)

        else:
            t.assert_never(method)

    def __build_server_handler_method_unary_unary(
        self,
        _: ClassBodyASTBuilder,
        registry: FastAPITypeRegistry,
        entrypoint: EntrypointInfo,
        method: UnaryUnaryMethodInfo,
    ) -> None:
        request_ref = registry.get_request(entrypoint, method)
        response_ref = registry.get_response(entrypoint, method)

        with (
            _.method_def(method.name)
            .arg("request", request_ref)
            .returns(response_ref or _.none())
            .async_() as method_def
        ):
            for param in method.params:
                _.assign_stmt(
                    target=f"input_{param.name}",
                    value=registry.request_param_unpack_expr(_.attr("request"), param, method_def),
                )

            impl_call = method_def.self_attr("impl", method.name).call(
                kwargs={param.name: _.attr(f"input_{param.name}") for param in method.params}
            )

            if method.returns is not None and response_ref is not None:
                _.assign_stmt("output", impl_call)
                _.assign_stmt(
                    "response",
                    _.call(response_ref).kwarg(
                        "payload",
                        registry.response_payload_pack_expr(_.attr("output"), method.returns, method_def),
                    ),
                )
                _.return_stmt(_.attr("response"))

            else:
                _.append(impl_call)

    def __build_server_handler_method_stream_stream(
        self,
        _: ClassBodyASTBuilder,
        registry: FastAPITypeRegistry,
        entrypoint: EntrypointInfo,
        method: StreamStreamMethodInfo,
    ) -> None:
        request_ref = registry.get_request(entrypoint, method)
        response_ref = registry.get_response(entrypoint, method)

        if method.output is None:
            detail = "invalid method"
            raise ValueError(detail, method)

        if response_ref is None:
            detail = "invalid method"
            raise ValueError(detail, method)

        with (
            _.method_def(method.name)
            .arg("websocket", TypeInfo.build(ModuleInfo(None, "fastapi"), "WebSocket"))
            .returns(_.none())
            .async_() as method_def
        ):
            with (
                method_def.func_def("receive_inputs")
                .returns(_.iterator_type(method.input_.annotation, is_async=True))
                .async_()
            ):
                with _.for_stmt("request_text", _.attr("websocket", "iter_text").call()).async_():
                    _.assign_stmt(
                        target="request",
                        value=self.__build_model_load_expr(_, request_ref, "request_text"),
                    )
                    _.yield_stmt(registry.request_param_unpack_expr(_.attr("request"), method.input_, method_def))

            with _.try_stmt() as try_stmt:
                with try_stmt.body():
                    _.append(_.attr("websocket", "accept").call().await_())

                    with _.for_stmt(
                        target="output",
                        items=method_def.self_attr("impl", method.name).call().arg(_.attr("receive_inputs").call()),
                    ).async_():
                        _.assign_stmt(
                            target="response",
                            value=_.call(response_ref).kwarg(
                                "payload",
                                registry.response_payload_pack_expr(_.attr("output"), method.output, method_def),
                            ),
                        )
                        _.append(
                            _.attr("websocket", "send_text")
                            .call()
                            .arg(self.__build_model_dump_expr(_, "response"))
                            .await_()
                        )

                with try_stmt.except_(TypeInfo.build(ModuleInfo(None, "fastapi"), "WebSocketDisconnect")):
                    pass

    def __build_server_entrypoint_router(
        self,
        _: ModuleASTBuilder,
        entrypoint: EntrypointInfo,
        handler_def: TypeRef,
    ) -> None:
        fastapi_router_ref = TypeInfo.build(ModuleInfo(None, "fastapi"), "APIRouter")

        with (
            _.func_def(f"create_{camel2snake(entrypoint.name)}_router")
            .arg("entrypoint", handler_def)
            .returns(fastapi_router_ref)
        ):
            _.assign_stmt(
                "router",
                value=_.call(fastapi_router_ref)
                .kwarg("prefix", _.const(f"/{camel2snake(entrypoint.name)}"))
                .kwarg("tags", _.const([entrypoint.name])),
            )

            for method in entrypoint.methods:
                self.__build_server_router_method(_, method)

            _.return_stmt(_.attr("router"))

    def __build_client_module(
        self,
        context: GeneratorContext,
        pkg: PackageASTBuilder,
        registry: FastAPITypeRegistry,
    ) -> None:
        client_impl_ref = TypeInfo.build(ModuleInfo(None, "httpx"), "AsyncClient")

        with pkg.module("client") as _:
            for entrypoint in context.entrypoints:
                with _.class_def(f"{snake2camel(entrypoint.name)}AsyncClient") as client_def:
                    with client_def.init_self_attrs_def({"impl": client_impl_ref}):
                        pass

                    for method in entrypoint.methods:
                        if isinstance(method, UnaryUnaryMethodInfo):
                            self.__build_client_method_unary_unary(client_def, registry, entrypoint, method)

                        elif isinstance(method, StreamStreamMethodInfo):
                            self.__build_client_method_stream_stream(client_def, registry, entrypoint, method)

                        else:
                            t.assert_never(method)

    def __build_client_method_unary_unary(
        self,
        _: ClassBodyASTBuilder,
        registry: FastAPITypeRegistry,
        entrypoint: EntrypointInfo,
        method: UnaryUnaryMethodInfo,
    ) -> None:
        response_def = registry.get_response(entrypoint, method)
        with (
            _.method_def(method.name)
            .arg("request", registry.get_request(entrypoint, method))
            .returns(response_def or _.const(None))
            .async_() as method_def
        ):
            request_call_expr = (
                method_def.self_attr("impl", "post")
                .call()
                .kwarg("url", _.const(f"/{camel2snake(entrypoint.name)}/{method.name}"))
                .kwarg("json", self.__build_model_dump_expr(_, "request", intermediate=True))
                .await_()
            )

            if method.returns is not None and response_def is not None:
                _.assign_stmt("raw_response", request_call_expr)
                _.assign_stmt(
                    target="response",
                    value=self.__build_model_load_expr(_, response_def, _.attr("raw_response", "read").call()),
                )
                _.return_stmt(_.attr("response"))

            else:
                _.append(request_call_expr)

    def __build_client_method_stream_stream(
        self,
        _: ClassBodyASTBuilder,
        registry: FastAPITypeRegistry,
        entrypoint: EntrypointInfo,
        method: StreamStreamMethodInfo,
    ) -> None:
        ws_connect_ref = TypeInfo.build(ModuleInfo(None, "httpx_ws"), "aconnect_ws")
        ws_session_ref = TypeInfo.build(ModuleInfo(None, "httpx_ws"), "AsyncWebSocketSession")
        ws_error_refs = [
            TypeInfo.build(ModuleInfo(None, "httpx_ws"), "WebSocketNetworkError"),
            TypeInfo.build(ModuleInfo(None, "httpx_ws"), "WebSocketDisconnect"),
        ]
        task_group_ref = TypeInfo.build(ModuleInfo(None, "asyncio"), "TaskGroup")

        request_def = registry.get_request(entrypoint, method)
        response_def = registry.get_response(entrypoint, method)

        if method.output is None:
            detail = "invalid method"
            raise ValueError(detail, method)

        if response_def is None:
            detail = "invalid method"
            raise ValueError(detail, method)

        with (
            _.method_def(method.name)
            .arg("requests", request_def.ref().iterator(is_async=True))
            .returns(response_def.ref().iterator(is_async=True))
            .async_() as method_def
        ):
            with _.func_def("send_requests").arg("ws", ws_session_ref).returns(_.none()).async_():
                with _.try_stmt() as try_stmt:
                    with try_stmt.body():
                        with _.for_stmt("request", _.attr("requests")).async_():
                            _.append(
                                _.attr("ws", "send_text")
                                .call()
                                .arg(self.__build_model_dump_expr(_, "request"))
                                .await_()
                            )

                    with try_stmt.finally_():
                        _.append(_.attr("ws", "close").call().await_())

            with (
                _.with_stmt()
                .async_()
                .enter(
                    cm=_.call(ws_connect_ref)
                    .kwarg("url", _.const(f"/{camel2snake(entrypoint.name)}/{method.name}"))
                    .kwarg("client", method_def.self_attr("impl")),
                    name="ws",
                )
                .enter(_.call(task_group_ref), "tasks")
            ):
                _.assign_stmt(
                    target="sender",
                    value=_.attr("tasks", "create_task").call().arg(_.attr("send_requests").call().arg(_.attr("ws"))),
                )

                with _.while_stmt(_.not_(_.attr("sender", "done").call())):
                    with _.try_stmt() as try_stmt:
                        with try_stmt.body():
                            _.assign_stmt(
                                target="raw_response",
                                value=_.attr("ws", "receive_text").call().await_(),
                            )

                        with try_stmt.except_(*ws_error_refs, name="err"):
                            with _.if_stmt(_.attr("sender", "done").call()) as if_stmt, if_stmt.body():
                                _.break_stmt()

                            _.raise_stmt(_.attr("err"))

                        with try_stmt.else_():
                            _.assign_stmt(
                                target="response",
                                value=self.__build_model_load_expr(_, response_def, "raw_response"),
                            )
                            _.yield_stmt(_.attr("response"))

    def __build_model_load_expr(self, builder: ScopeASTBuilder, model: TypeRef, source: t.Union[str, Expr]) -> Expr:
        return (
            builder.attr(model, "model_validate_json")
            .call()
            .arg(builder.attr(source) if isinstance(source, str) else source)
        )

    def __build_model_dump_expr(
        self,
        builder: ScopeASTBuilder,
        source: str,
        *,
        intermediate: bool = False,
    ) -> Expr:
        return (
            builder.attr(source, "model_dump_json" if not intermediate else "model_dump")
            .call(kwargs={"mode": builder.const("json")} if intermediate else None)
            .kwarg("by_alias", builder.const(value=True))
            .kwarg("exclude_none", builder.const(value=True))
        )
