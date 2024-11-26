from contextlib import ExitStack
from itertools import chain

from google.protobuf.compiler.plugin_pb2 import CodeGeneratorRequest, CodeGeneratorResponse

from pyprotostuben.codegen.abc import ProtocPlugin, ProtoFileGenerator
from pyprotostuben.codegen.brokrpc.generator import BrokRPCContext, BrokRPCModuleGenerator
from pyprotostuben.codegen.module_ast import ModuleAstProtoFileGenerator
from pyprotostuben.logging import LoggerMixin
from pyprotostuben.pool.abc import Pool
from pyprotostuben.pool.process import MultiProcessPool, SingleProcessPool
from pyprotostuben.protobuf.context import CodeGeneratorContext, ContextBuilder
from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.parser import CodeGeneratorParameters


class BrokRPCProtocPlugin(ProtocPlugin, LoggerMixin):
    def run(self, request: CodeGeneratorRequest) -> CodeGeneratorResponse:
        log = self._log.bind_details(request_file_to_generate=request.file_to_generate)
        log.debug("request received")

        with ExitStack() as cm_stack:
            context = ContextBuilder().build(request)
            gen = self.__create_generator(context)
            pool = self.__create_pool(context.params, cm_stack)

            resp = CodeGeneratorResponse(
                supported_features=CodeGeneratorResponse.Feature.FEATURE_PROTO3_OPTIONAL,
                file=chain.from_iterable(pool.run(gen.run, context.files)),
            )

        log.info("request handled")

        return resp

    def __create_generator(self, context: CodeGeneratorContext) -> ProtoFileGenerator:
        return ModuleAstProtoFileGenerator(
            context_factory=_MultiProcessFuncs.create_visitor_context,
            visitor=BrokRPCModuleGenerator(registry=context.registry),
        )

    def __create_pool(self, params: CodeGeneratorParameters, cm_stack: ExitStack) -> Pool:
        return (
            SingleProcessPool()
            if params.has_flag("no-parallel") or params.has_flag("debug")
            else cm_stack.enter_context(MultiProcessPool.setup())
        )


class _MultiProcessFuncs:
    """
    A set of picklable functions that can be passed to `MultiProcessPool`.

    For more info: https://docs.python.org/3/library/multiprocessing.html#programming-guidelines
    """

    @staticmethod
    def create_visitor_context(_: ProtoFile) -> BrokRPCContext:
        return BrokRPCContext()
