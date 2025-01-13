import inspect
import typing as t
from itertools import chain

from pyprotostuben.codegen.model import ModelDefBuilder, PydanticModelFactory
from pyprotostuben.codegen.servicify.abc import ServicifyCodeGenerator
from pyprotostuben.codegen.servicify.model import EntrypointInfo, GeneratedFile, GeneratorContext, MethodInfo
from pyprotostuben.python.builder2 import (
    AttrASTBuilder,
    Expr,
    FuncScopeASTBuilder,
    PackageASTBuilder,
    TypeRef,
    package,
    render,
)
from pyprotostuben.python.info import ModuleInfo, TypeInfo
from pyprotostuben.string_case import camel2snake, snake2camel


class ModelRegistry:
    def __init__(self, builder: ModelDefBuilder) -> None:
        self.__builder = builder
        self.__requests = dict[tuple[str, str], TypeRef]()
        self.__responses = dict[tuple[str, str], TypeRef]()

    def request_ref(self, entrypoint: EntrypointInfo, method: MethodInfo) -> TypeRef:
        return self.__requests[(entrypoint.name, method.name)]

    def response_ref(self, entrypoint: EntrypointInfo, method: MethodInfo) -> t.Optional[TypeRef]:
        return self.__responses.get((entrypoint.name, method.name))

    def request_param_unpack_expr(
        self,
        source: AttrASTBuilder,
        param: inspect.Parameter,
        builder: FuncScopeASTBuilder,
    ) -> Expr:
        return self.__builder.assign_expr(source.attr(param.name), param.annotation, "original", builder)

    def response_payload_pack_expr(
        self,
        source: AttrASTBuilder,
        annotation: type[object],
        builder: FuncScopeASTBuilder,
    ) -> Expr:
        return self.__builder.assign_expr(source, annotation, "model", builder)

    def register_request(
        self,
        entrypoint: EntrypointInfo,
        method: MethodInfo,
        fields: t.Mapping[str, type[object]],
        doc: t.Optional[str],
    ) -> None:
        model_ref = self.__builder.create(self.__create_model_name(entrypoint, method, "Request"), fields, doc)
        self.__requests[(entrypoint.name, method.name)] = model_ref

    def register_response(
        self,
        entrypoint: EntrypointInfo,
        method: MethodInfo,
        fields: t.Mapping[str, type[object]],
        doc: t.Optional[str],
    ) -> None:
        model_ref = self.__builder.create(self.__create_model_name(entrypoint, method, "Response"), fields, doc)
        self.__responses[(entrypoint.name, method.name)] = model_ref

    def __create_model_name(
        self,
        entrypoint: EntrypointInfo,
        method: MethodInfo,
        suffix: str,
    ) -> str:
        return "".join(snake2camel(s) for s in (entrypoint.name, method.name, suffix))


# TODO: try to reuse this code in protobuf brokrpc generator. Use some kind of factory to inject custom module naming
#  (protobuf message types & serializer_module).
class FastAPIServicifyCodeGenerator(ServicifyCodeGenerator):
    def generate(self, context: GeneratorContext) -> t.Sequence[GeneratedFile]:
        with package(context.package or "api") as pkg:
            with pkg.init():
                pass

            models = self.__build_model_module(context, pkg)
            self.__build_abc_module(context, pkg, models)
            self.__build_server_module(context, pkg, models)
            self.__build_client_module(context, pkg, models)

        return [
            GeneratedFile(
                path=context.output.joinpath(module.file),
                content=render(body),
            )
            for module, body in pkg.build().items()
        ]

    def __build_abc_module(
        self,
        context: GeneratorContext,
        pkg: PackageASTBuilder,
        models: ModelRegistry,
    ) -> None:
        with pkg.module("abc") as mod:
            for entrypoint in context.entrypoints:
                with mod.class_def(entrypoint.name).docstring(entrypoint.doc).abstract() as entrypoint_def:
                    for method in entrypoint.methods:
                        with (
                            entrypoint_def.method_def(method.name)
                            .pos_arg("request", models.request_ref(entrypoint, method))
                            .returns(models.response_ref(entrypoint, method))
                            .async_()
                            .abstract()
                            .not_implemented()
                        ):
                            pass

    def __build_model_module(
        self,
        context: GeneratorContext,
        pkg: PackageASTBuilder,
    ) -> ModelRegistry:
        with pkg.module("model") as mod:
            models = ModelDefBuilder(mod, PydanticModelFactory())
            models.update(
                set(
                    chain.from_iterable(
                        chain(
                            (param.annotation for param in method.params),
                            (method.returns,) if method.returns is not None else (),
                        )
                        for entrypoint in context.entrypoints
                        for method in entrypoint.methods
                    )
                )
            )

            registry = ModelRegistry(models)

            for entrypoint in context.entrypoints:
                for method in entrypoint.methods:
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

        return registry

    def __build_server_module(self, context: GeneratorContext, pkg: PackageASTBuilder, models: ModelRegistry) -> None:
        abc_ref = ModuleInfo(pkg.info, "abc")
        fastapi_router_ref = TypeInfo.build(ModuleInfo(None, "fastapi"), "APIRouter")

        with pkg.module("server") as mod:
            for entrypoint in context.entrypoints:
                with (
                    mod.func_def(f"create_{camel2snake(entrypoint.name)}_router")
                    .pos_arg(
                        name="entrypoint",
                        annotation=TypeInfo.build(ModuleInfo(pkg.info, "abc"), snake2camel(entrypoint.name)),
                    )
                    .returns(fastapi_router_ref) as router_def
                ):
                    router_def.assign_stmt(
                        "router",
                        value=router_def.call(fastapi_router_ref)
                        .kwarg("prefix", router_def.const(f"/{camel2snake(entrypoint.name)}"))
                        .kwarg("tags", router_def.const([entrypoint.name])),
                    )

                    for method in entrypoint.methods:
                        router_def.append(
                            router_def.attr("router", "post")
                            .call()
                            .kwarg("path", router_def.const(f"/{method.name}"))
                            .kwarg(
                                "description",
                                router_def.const(method.doc) if method.doc is not None else router_def.none(),
                            )
                            .call()
                            .arg(mod.attr("entrypoint", method.name))
                        )

                    router_def.return_stmt(router_def.attr("router"))

                with mod.class_def(f"{snake2camel(entrypoint.name)}Handler").inherits(
                    TypeInfo.build(abc_ref, snake2camel(entrypoint.name))
                ) as handler_def:
                    with handler_def.init_self_attrs_def({"impl": entrypoint.type_}):
                        pass

                    for method in entrypoint.methods:
                        with (
                            handler_def.method_def(method.name)
                            .pos_arg("request", models.request_ref(entrypoint, method))
                            .returns(models.response_ref(entrypoint, method) or handler_def.none())
                            .async_()
                            .override() as method_def
                        ):
                            for param in method.params:
                                method_def.assign_stmt(
                                    f"input_{param.name}",
                                    value=models.request_param_unpack_expr(
                                        source=mod.attr("request"),
                                        param=param,
                                        builder=method_def,
                                    ),
                                )

                            impl_call = method_def.self_attr("impl", method.name).call(
                                kwargs={param.name: method_def.attr(f"input_{param.name}") for param in method.params}
                            )

                            if method.returns is not None:
                                method_def.assign_stmt("output", impl_call)
                                method_def.assign_stmt(
                                    "response",
                                    method_def.call(models.response_ref(entrypoint, method)).kwarg(
                                        "payload",
                                        models.response_payload_pack_expr(
                                            method_def.attr("output"), method.returns, method_def
                                        ),
                                    ),
                                )
                                method_def.return_stmt(method_def.attr("response"))

                            else:
                                method_def.append(impl_call)

    def __build_client_module(self, context: GeneratorContext, pkg: PackageASTBuilder, models: ModelRegistry) -> None:
        abc_ref = ModuleInfo(pkg.info, "abc")
        client_impl_ref = TypeInfo.build(ModuleInfo(None, "httpx"), "AsyncClient")

        with pkg.module("client") as mod:
            for entrypoint in context.entrypoints:
                client_name = f"{snake2camel(entrypoint.name)}AsyncClient"

                with mod.class_def(client_name).inherits(
                    TypeInfo.build(abc_ref, snake2camel(entrypoint.name))
                ) as client_def:
                    with client_def.init_self_attrs_def({"impl": client_impl_ref}):
                        pass

                    for method in entrypoint.methods:
                        with (
                            client_def.method_def(method.name)
                            .pos_arg("request", models.request_ref(entrypoint, method))
                            .returns(models.response_ref(entrypoint, method) or client_def.const(None))
                            .async_()
                            .override() as _
                        ):
                            request_call_expr = (
                                _.self_attr("impl", "post")
                                .call()
                                .kwarg("url", client_def.const(f"/{camel2snake(entrypoint.name)}/{method.name}"))
                                .kwarg(
                                    "json",
                                    _.attr("request", "model_dump")
                                    .call()
                                    .kwarg("mode", mod.const("json"))
                                    .kwarg("by_alias", mod.const(value=True))
                                    .kwarg("exclude_none", mod.const(value=True)),
                                )
                                .await_()
                            )

                            if method.returns is not None:
                                _.assign_stmt("raw_response", request_call_expr)
                                _.assign_stmt(
                                    "response",
                                    value=_.attr(models.response_ref(entrypoint, method), "model_validate_json")
                                    .call()
                                    .arg(_.attr("raw_response", "read").call()),
                                )
                                _.return_stmt(_.attr("response"))

                            else:
                                _.append(request_call_expr)

    def __build_model_name(
        self,
        entrypoint: EntrypointInfo,
        method: MethodInfo,
        suffix: str,
    ) -> str:
        return "".join(snake2camel(s) for s in (entrypoint.name, method.name, suffix))
