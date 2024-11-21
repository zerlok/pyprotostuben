from contextlib import ExitStack

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest, CodeGeneratorResponse
from google.protobuf.descriptor_pb2 import GeneratedCodeInfo

from pyprotostuben.codegen.abc import ProtocPlugin, ProtoFileGenerator
from pyprotostuben.codegen.brokrpc.generator import BrokRPCContext, BrokRPCModuleGenerator
from pyprotostuben.codegen.model import GeneratedItem
from pyprotostuben.codegen.module_ast import ModuleASTBasedProtoFileGenerator
from pyprotostuben.logging import LoggerMixin
from pyprotostuben.pool.abc import Pool
from pyprotostuben.pool.process import MultiProcessPool, SingleProcessPool
from pyprotostuben.protobuf.builder.resolver import ProtoDependencyResolver
from pyprotostuben.protobuf.context import CodeGeneratorContext, ContextBuilder
from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.parser import CodeGeneratorParameters
from pyprotostuben.python.ast_builder import ASTBuilder
from pyprotostuben.python.info import ModuleInfo
from pyprotostuben.stack import MutableStack


class BrokRPCProtocPlugin(ProtocPlugin, LoggerMixin):
    def run(self, request: CodeGeneratorRequest) -> CodeGeneratorResponse:
        log = self._log.bind_details(request_file_to_generate=request.file_to_generate)
        log.debug("request received")

        with ExitStack() as cm_stack:
            context = ContextBuilder.build(request)
            gen = self.__create_generator(context)
            pool = self.__create_pool(context.params, cm_stack)

            resp = CodeGeneratorResponse(
                supported_features=CodeGeneratorResponse.Feature.FEATURE_PROTO3_OPTIONAL,
                file=(self.__build_file(item) for items in pool.run(gen.run, context.files) for item in items),
            )

        log.info("request handled")

        return resp

    def __create_generator(self, context: CodeGeneratorContext) -> ProtoFileGenerator:
        return ModuleASTBasedProtoFileGenerator(
            context_factory=_MultiProcessFuncs.create_visitor_context,
            visitor=BrokRPCModuleGenerator(registry=context.registry),
        )

    def __create_pool(self, params: CodeGeneratorParameters, cm_stack: ExitStack) -> Pool:
        return (
            SingleProcessPool()
            if params.has_flag("no-parallel") or params.has_flag("debug")
            else cm_stack.enter_context(MultiProcessPool.setup())
        )

    def __build_file(self, item: GeneratedItem) -> CodeGeneratorResponse.File:
        return CodeGeneratorResponse.File(
            name=str(item.path),
            generated_code_info=GeneratedCodeInfo(
                annotation=[GeneratedCodeInfo.Annotation(source_file=str(item.source.proto_path))],
            ),
            content=item.content,
        )


class _MultiProcessFuncs:
    """
    A set of picklable functions that can be passed to `MultiProcessPool`.

    For more info: https://docs.python.org/3/library/multiprocessing.html#programming-guidelines
    """

    @staticmethod
    def create_visitor_context(file: ProtoFile) -> BrokRPCContext:
        deps = set[ModuleInfo]()
        module = ModuleInfo(file.pb2_package, f"{file.name}_brokrpc")

        return BrokRPCContext(
            file=file,
            modules={},
            deps=deps,
            module=module,
            builder=ASTBuilder(ProtoDependencyResolver(module, deps)),
            scopes=MutableStack(),
        )
