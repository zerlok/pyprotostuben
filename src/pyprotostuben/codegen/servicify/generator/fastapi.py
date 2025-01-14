import inspect
import typing as t
from itertools import chain

from pyprotostuben.codegen.model import ModelASTBuilder, PydanticModelFactory
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


class FastAPITypeRegistry:
    def __init__(self, builder: ModelASTBuilder) -> None:
        self.__builder = builder
        self.__interfaces = dict[str, TypeRef]()
        self.__requests = dict[tuple[str, str], TypeRef]()
        self.__responses = dict[tuple[str, str], TypeRef]()

    def interface_ref(self, entrypoint: EntrypointInfo) -> TypeRef:
        return self.__interfaces[entrypoint.name]

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

    def register_interface(self, entrypoint: EntrypointInfo, ref: TypeRef) -> None:
        self.__interfaces[entrypoint.name] = ref

    def register_request(
        self,
        entrypoint: EntrypointInfo,
        method: MethodInfo,
        fields: t.Mapping[str, type[object]],
        doc: t.Optional[str],
    ) -> None:
        model_ref = self.__builder.create_def(self.__create_model_name(entrypoint, method, "Request"), fields, doc)
        self.__requests[(entrypoint.name, method.name)] = model_ref

    def register_response(
        self,
        entrypoint: EntrypointInfo,
        method: MethodInfo,
        fields: t.Mapping[str, type[object]],
        doc: t.Optional[str],
    ) -> None:
        model_ref = self.__builder.create_def(self.__create_model_name(entrypoint, method, "Response"), fields, doc)
        self.__responses[(entrypoint.name, method.name)] = model_ref

    def __create_model_name(
        self,
        entrypoint: EntrypointInfo,
        method: MethodInfo,
        suffix: str,
    ) -> str:
        return "".join(snake2camel(s) for s in (entrypoint.name, method.name, suffix))


class FastAPIServicifyCodeGenerator(ServicifyCodeGenerator):
    def generate(self, context: GeneratorContext) -> t.Sequence[GeneratedFile]:
        with package(context.package or "api") as pkg:
            with pkg.init():
                pass

            registry = self.__build_model_module(context, pkg)
            self.__build_abc_module(context, pkg, registry)
            self.__build_server_module(context, pkg, registry)
            self.__build_client_module(context, pkg, registry)

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
        registry: FastAPITypeRegistry,
    ) -> None:
        with pkg.module("abc") as _:
            for entrypoint in context.entrypoints:
                with _.class_def(entrypoint.name).docstring(entrypoint.doc).abstract() as entrypoint_def:
                    registry.register_interface(entrypoint, entrypoint_def)

                    for method in entrypoint.methods:
                        with (
                            entrypoint_def.method_def(method.name)
                            .pos_arg("request", registry.request_ref(entrypoint, method))
                            .returns(registry.response_ref(entrypoint, method))
                            .async_()
                            .abstract()
                            .not_implemented()
                        ):
                            pass

    def __build_model_module(
        self,
        context: GeneratorContext,
        pkg: PackageASTBuilder,
    ) -> FastAPITypeRegistry:
        with pkg.module("model") as mod:
            models = ModelASTBuilder(mod, PydanticModelFactory())
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

            registry = FastAPITypeRegistry(models)

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

    def __build_server_module(
        self,
        context: GeneratorContext,
        pkg: PackageASTBuilder,
        registry: FastAPITypeRegistry,
    ) -> None:
        fastapi_router_ref = TypeInfo.build(ModuleInfo(None, "fastapi"), "APIRouter")

        with pkg.module("server") as _:
            for entrypoint in context.entrypoints:
                with (
                    _.func_def(f"create_{camel2snake(entrypoint.name)}_router")
                    .pos_arg("entrypoint", registry.interface_ref(entrypoint))
                    .returns(fastapi_router_ref)
                ):
                    _.assign_stmt(
                        "router",
                        value=_.call(fastapi_router_ref)
                        .kwarg("prefix", _.const(f"/{camel2snake(entrypoint.name)}"))
                        .kwarg("tags", _.const([entrypoint.name])),
                    )

                    for method in entrypoint.methods:
                        _.append(
                            _.attr("router", "post")
                            .call()
                            .kwarg("path", _.const(f"/{method.name}"))
                            .kwarg("description", _.const(method.doc) if method.doc is not None else _.none())
                            .call()
                            .arg(_.attr("entrypoint", method.name))
                        )

                    _.return_stmt(_.attr("router"))

                with _.class_def(f"{snake2camel(entrypoint.name)}Handler").inherits(
                    registry.interface_ref(entrypoint)
                ) as handler_def:
                    with handler_def.init_self_attrs_def({"impl": entrypoint.type_}):
                        pass

                    for method in entrypoint.methods:
                        response_ref = registry.response_ref(entrypoint, method)

                        with (
                            handler_def.method_def(method.name)
                            .pos_arg("request", registry.request_ref(entrypoint, method))
                            .returns(response_ref or _.none())
                            .async_()
                            .override() as method_def
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
                                        registry.response_payload_pack_expr(
                                            _.attr("output"), method.returns, method_def
                                        ),
                                    ),
                                )
                                _.return_stmt(_.attr("response"))

                            else:
                                _.append(impl_call)

    def __build_client_module(
        self, context: GeneratorContext, pkg: PackageASTBuilder, models: FastAPITypeRegistry
    ) -> None:
        abc_ref = ModuleInfo(pkg.info, "abc")
        client_impl_ref = TypeInfo.build(ModuleInfo(None, "httpx"), "AsyncClient")

        with pkg.module("client") as _:
            for entrypoint in context.entrypoints:
                with _.class_def(f"{snake2camel(entrypoint.name)}AsyncClient").inherits(
                    TypeInfo.build(abc_ref, snake2camel(entrypoint.name))
                ) as client_def:
                    with client_def.init_self_attrs_def({"impl": client_impl_ref}):
                        pass

                    for method in entrypoint.methods:
                        with (
                            client_def.method_def(method.name)
                            .pos_arg("request", models.request_ref(entrypoint, method))
                            .returns(models.response_ref(entrypoint, method) or _.const(None))
                            .async_()
                            .override() as method_def
                        ):
                            request_call_expr = (
                                method_def.self_attr("impl", "post")
                                .call()
                                .kwarg("url", client_def.const(f"/{camel2snake(entrypoint.name)}/{method.name}"))
                                .kwarg(
                                    "json",
                                    _.attr("request", "model_dump")
                                    .call()
                                    .kwarg("mode", _.const("json"))
                                    .kwarg("by_alias", _.const(value=True))
                                    .kwarg("exclude_none", _.const(value=True)),
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
