import ast
import typing as t
from contextlib import ExitStack
from pathlib import Path

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest, CodeGeneratorResponse
from google.protobuf.descriptor_pb2 import GeneratedCodeInfo

from pyprotostuben.codegen.abc import CodeGenerator
from pyprotostuben.codegen.builder import ASTBuilder
from pyprotostuben.codegen.mypy.builder import ModuleStubBuilder
from pyprotostuben.codegen.mypy.context import CodeGeneratorContext, FileContext
from pyprotostuben.codegen.mypy.info import ScopeInfo, ScopeProtoVisitorDecorator
from pyprotostuben.codegen.parser import ParameterParser
from pyprotostuben.codegen.render import render
from pyprotostuben.logging import LoggerMixin, Logger
from pyprotostuben.pool.abc import Pool
from pyprotostuben.pool.process import SingleProcessPool, MultiProcessPool
from pyprotostuben.protobuf.context import ContextBuilder
from pyprotostuben.protobuf.visitor.abc import visit
from pyprotostuben.protobuf.visitor.decorator import LeaveProtoVisitorDecorator
from pyprotostuben.protobuf.visitor.dfs import DFSWalkingProtoVisitor
from pyprotostuben.protobuf.visitor.info import NamespaceInfoVisitor
from pyprotostuben.python.info import NamespaceInfo
from pyprotostuben.stack import MutableStack


# TODO: support such options (disabled by default):
#  1. mutable message (allow field modifications after instantiation)
#  2. non strict (allow `None` value for non-optional fields)
class MypyStubCodeGenerator(CodeGenerator, LoggerMixin):
    def run(self, request: CodeGeneratorRequest) -> CodeGeneratorResponse:
        log = self._log.bind_details(request_file_to_generate=request.file_to_generate)
        log.debug("request received")

        with ExitStack() as cm_stack:
            context = self.__build_context(request)

            pool = self.__create_pool(context, cm_stack)
            log.debug("pool created", pool=pool)

            resp = CodeGeneratorResponse(
                file=list(self.__build_mypy_stubs(context, pool, log)),
                supported_features=CodeGeneratorResponse.Feature.FEATURE_PROTO3_OPTIONAL,
            )

        log.info("request handled")

        return resp

    def __build_context(self, request: CodeGeneratorRequest) -> CodeGeneratorContext:
        ctx = ContextBuilder.build(request.proto_file)

        parser = ParameterParser()
        params = parser.parse(request.parameter)

        return CodeGeneratorContext(ctx.files, ctx.type_registry, params, request)

    def __create_pool(self, context: CodeGeneratorContext, cm_stack: ExitStack) -> Pool:
        return (
            SingleProcessPool()
            if context.params.has_flag("no-parallel") or context.params.has_flag("debug")
            else cm_stack.enter_context(MultiProcessPool.setup())
        )

    def __build_mypy_stubs(
        self,
        context: CodeGeneratorContext,
        pool: Pool,
        log: Logger,
    ) -> t.Iterable[CodeGeneratorResponse.File]:
        generated_results = pool.run(
            func=_build_mypy_stub_for_single_file,
            args=(FileContext(context.type_registry, context.files[file]) for file in context.request.file_to_generate),
        )

        for file_ctx, modules in generated_results:
            log.debug("mypy stub modules ready", file_ctx=file_ctx)

            info = GeneratedCodeInfo(
                annotation=[
                    GeneratedCodeInfo.Annotation(source_file=str(file_ctx.file.proto_path)),
                ],
            )

            for path, content in modules.items():
                yield CodeGeneratorResponse.File(
                    name=str(path),
                    generated_code_info=info,
                    content=content,
                )


def _build_mypy_stub_for_single_file(context: FileContext) -> t.Tuple[FileContext, t.Mapping[Path, str]]:
    file = context.file

    ast_builder = ASTBuilder()
    namespaces: MutableStack[NamespaceInfo] = MutableStack()
    scopes: MutableStack[ScopeInfo] = MutableStack()
    modules: t.Dict[Path, ast.Module] = {}

    visit(
        DFSWalkingProtoVisitor(
            NamespaceInfoVisitor(namespaces),
            ScopeProtoVisitorDecorator(scopes),
            LeaveProtoVisitorDecorator(
                ModuleStubBuilder(
                    type_registry=context.type_registry,
                    ast_builder=ast_builder,
                    files=MutableStack([file]),
                    namespaces=namespaces,
                    scopes=scopes,
                    modules=modules,
                )
            ),
        ),
        file.descriptor,
    )

    return context, {path: render(module_ast) for path, module_ast in modules.items()}
