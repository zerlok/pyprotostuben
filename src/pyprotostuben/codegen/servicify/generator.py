import ast
import inspect
import itertools
import typing as t
from dataclasses import dataclass
from pathlib import Path

from pyprotostuben.codegen.servicify.entrypoint import EntrypointInfo, MethodInfo
from pyprotostuben.python.ast_builder import ASTBuilder, ModuleDependencyResolver
from pyprotostuben.python.info import ModuleInfo, PackageInfo, TypeInfo
from pyprotostuben.string_case import camel2snake, snake2camel


@dataclass(frozen=True, kw_only=True)
class GeneratorContext:
    entrypoints: t.Sequence[EntrypointInfo]
    output: Path


@dataclass(frozen=True, kw_only=True)
class GeneratedFile:
    path: Path
    content: str


class ServicifyCodeGenerator:
    def generate(self, context: GeneratorContext) -> t.Iterable[GeneratedFile]:
        package = PackageInfo(None, "fastapi")

        model_file, models_map = self.__build_models(context, package)
        yield model_file
        yield self.__build_app(context, package, models_map)

    def __build_models(
        self,
        context: GeneratorContext,
        package: PackageInfo,
    ) -> tuple[GeneratedFile, t.Mapping[MethodInfo, tuple[TypeInfo, TypeInfo]]]:
        info = ModuleInfo(package, "model")
        builder = self.__get_builder(info)

        model_map = {
            method: (
                TypeInfo(module=info, ns=[f"{entrypoint.ns[0]}{snake2camel(method.name.title())}Request"]),
                TypeInfo(module=info, ns=[f"{entrypoint.ns[0]}{snake2camel(method.name.title())}Response"]),
            )
            for entrypoint in context.entrypoints
            for method in entrypoint.methods
        }

        body = list(
            itertools.chain.from_iterable(
                (
                    builder.build_class_def(
                        name=model_map[method][0].ns[0],
                        bases=[TypeInfo.from_str("pydantic:BaseModel")],
                        body=[
                            builder.build_attr_stub(
                                name=param.name,
                                annotation=TypeInfo.from_type(param.annotation),
                            )
                            for param in method.signature.parameters.values()
                            if param.annotation is not inspect.Parameter.empty
                        ],
                    ),
                    builder.build_class_def(
                        name=model_map[method][1].ns[0],
                        bases=[
                            builder.build_generic_ref(
                                TypeInfo.from_str("pydantic:RootModel"),
                                TypeInfo.from_type(method.signature.return_annotation),
                            ),
                        ],
                        body=[builder.build_pass_stmt()],
                    ),
                )
                for entrypoint in context.entrypoints
                for method in entrypoint.methods
            )
        )

        return self.__build_module(context, info, builder.build_module(body=body)), model_map

    def __build_app(
        self,
        context: GeneratorContext,
        package: PackageInfo,
        models_map: t.Mapping[MethodInfo, tuple[TypeInfo, TypeInfo]],
    ) -> GeneratedFile:
        info = ModuleInfo(package, "app")
        builder = self.__get_builder(info)

        body = [
            builder.build_attr_assign("app", value=builder.build_call(func=TypeInfo.from_str("fastapi:FastAPI"))),
            *(
                builder.build_func_def(
                    name=f"{camel2snake(method.name)}_{camel2snake(entrypoint.ns[0])}",
                    decorators=[
                        builder.build_call(
                            func=builder.build_name("app", "post"),
                            args=[builder.build_const("/".join(["", *entrypoint.module.parts, method.name]))],
                        ),
                    ],
                    args=[
                        builder.build_pos_arg(
                            name="request",
                            annotation=TypeInfo.from_str("fastapi:Request"),
                        ),
                    ],
                    body=[
                        builder.build_attr_assign(
                            "request_payload",
                            value=builder.build_call(
                                func=ast.Attribute(
                                    value=builder.build_ref(models_map[method][0]),
                                    attr="model_validate_json",
                                ),
                                args=[builder.build_call(func=builder.build_name("request", "read"), is_async=True)],
                                kwargs={"by_alias": builder.build_const(True)},
                            ),
                        ),
                        builder.build_attr_assign(
                            "response_payload",
                            value=builder.build_call(
                                func=builder.build_name("request", "state", entrypoint.ns[0], method.name),
                                kwargs={
                                    param.name: builder.build_name("request_payload", param.name)
                                    for param in method.signature.parameters.values()
                                    if param.annotation is not inspect.Parameter.empty
                                },
                            ),
                        ),
                        builder.build_return_stmt(
                            value=builder.build_call(
                                func=ast.Attribute(
                                    value=builder.build_ref(models_map[method][1]),
                                    attr="model_validate",
                                ),
                                args=[builder.build_name("response_payload")],
                                kwargs={"by_alias": builder.build_const(True)},
                            ),
                        ),
                    ],
                    returns=models_map[method][1],
                    is_async=True,
                )
                for entrypoint in context.entrypoints
                for method in entrypoint.methods
            ),
        ]

        return self.__build_module(context, info, builder.build_module(body=body))

    def __build_module(self, context: GeneratorContext, info: ModuleInfo, body: ast.Module) -> GeneratedFile:
        return GeneratedFile(path=context.output.joinpath(info.file), content=ast.unparse(body))

    def __get_builder(self, info: ModuleInfo) -> ASTBuilder:
        return ASTBuilder(ModuleDependencyResolver(info))
