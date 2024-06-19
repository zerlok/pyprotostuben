import ast
import typing as t
from dataclasses import dataclass, field
from pathlib import Path

from google.protobuf.descriptor_pb2 import (
    FieldDescriptorProto,
    EnumDescriptorProto,
    DescriptorProto,
    MethodDescriptorProto,
    ServiceDescriptorProto,
    OneofDescriptorProto,
    EnumValueDescriptorProto,
    FileDescriptorProto,
)

from pyprotostuben.codegen.mypy.strategy.abc import Strategy
from pyprotostuben.logging import LoggerMixin
from pyprotostuben.protobuf.file import ProtoFile
from pyprotostuben.protobuf.registry import TypeRegistry
from pyprotostuben.protobuf.visitor.abc import visit
from pyprotostuben.protobuf.visitor.decorator import ProtoVisitorDecorator
from pyprotostuben.protobuf.visitor.dfs import DFSWalkingProtoVisitor
from pyprotostuben.python.builder import (
    build_attr,
    build_class_def,
    build_method_stub,
    build_init_stub,
    FuncArgInfo,
    build_generic_ref,
    build_func_stub,
)
from pyprotostuben.python.info import ModuleInfo
from pyprotostuben.stack import MutableStack


@dataclass()
class MessageInfo:
    nested: t.MutableSequence[ast.stmt] = field(default_factory=list)
    init_args: t.MutableSequence[FuncArgInfo] = field(default_factory=list)
    properties: t.MutableSequence[ast.stmt] = field(default_factory=list)
    has_field_args: t.MutableSequence[ast.expr] = field(default_factory=list)
    oneof_groups: t.MutableSequence[ast.expr] = field(default_factory=list)
    oneof_items: t.Dict[int, t.MutableSequence[ast.expr]] = field(default_factory=dict)


class ModuleASTGeneratorStrategy(Strategy, LoggerMixin):
    def __init__(self, registry: TypeRegistry) -> None:
        self.__registry = registry

    def run(self, file: ProtoFile) -> t.Iterable[t.Tuple[ProtoFile, Path, str]]:
        log = self._log.bind_details(file_name=file.name)
        log.debug("file received")

        modules: t.Dict[ModuleInfo, ast.Module] = {}

        visit(DFSWalkingProtoVisitor(ModuleASTGenerator(self.__registry, modules)), file.descriptor)
        log.debug("proto visited", modules=modules)

        for module_info, module_ast in modules.items():
            import_fixer = ModuleImportFixer()
            fixed_module_ast = import_fixer.fix(module_info, module_ast)

            module_content = ast.unparse(fixed_module_ast)
            log.info("module generated", module_info=module_info)

            yield file, module_info.stub_file, module_content


class ModuleImportFixer(ast.NodeVisitor):
    class RefProvider(ast.NodeVisitor):
        def __init__(self) -> None:
            self.__result: t.MutableSequence[str] = []

        def visit_Attribute(self, node: ast.Attribute) -> None:
            self.visit(node.value)
            self.__result.append(node.attr)

        def visit_Name(self, node: ast.Name) -> None:
            self.__result.append(node.id)

        def provide(self, node: ast.expr) -> t.Tuple[str, ...]:
            self.visit(node)
            return tuple(self.__result)

    def __init__(self) -> None:
        self.__ns: MutableStack[str] = MutableStack()
        self.__deps: t.Set[t.Tuple[str, ...]] = set()

    def visit_Attribute(self, node: ast.Attribute) -> None:
        module_ref = self.RefProvider().provide(node.value)
        self.__deps.add(module_ref)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        self.visit(node.slice)
        self.visit(node.value)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.visit(node.args)
        if node.returns is not None:
            self.visit(node.returns)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.visit(node.args)
        if node.returns is not None:
            self.visit(node.returns)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.visit_body(node.bases)
        self.visit_body(node.keywords)

        self.__ns.put(node.name)
        self.visit_body(node.body)
        self.__ns.pop()

    def visit_body(self, body: t.Sequence[ast.AST]) -> None:
        for node in body:
            self.visit(node)

    def fix(self, module: ModuleInfo, node: ast.Module) -> ast.Module:
        self.visit(node)
        module_imports = [ast.Import(names=[ast.alias(name=".".join(dep))]) for dep in sorted(self.__deps)]
        return ast.Module(body=[*module_imports, *node.body], type_ignores=node.type_ignores)


class ModuleASTGenerator(ProtoVisitorDecorator, LoggerMixin):
    def __init__(self, registry: TypeRegistry, modules: t.MutableMapping[ModuleInfo, ast.Module]) -> None:
        self.__registry = registry
        self.__modules = modules
        self.__messages: MutableStack[MessageInfo] = MutableStack()
        self.__enum_body: MutableStack[t.MutableSequence[ast.stmt]] = MutableStack()
        self.__servicer_body: MutableStack[t.MutableSequence[ast.stmt]] = MutableStack()
        self.__stub_body: MutableStack[t.MutableSequence[ast.stmt]] = MutableStack()

    def enter_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        self.__messages.put(MessageInfo())
        self.__servicer_body.put([])
        self.__stub_body.put([])

    def leave_file_descriptor_proto(self, proto: FileDescriptorProto) -> None:
        file = ProtoFile(proto)

        info = self.__messages.pop()
        if info:
            self.__modules[file.pb2_message] = ast.Module(body=info.nested, type_ignores=[])

        servicer_body = self.__servicer_body.pop()
        stub_body = self.__stub_body.pop()
        if servicer_body and stub_body:
            self.__modules[file.pb2_grpc] = ast.Module(body=[*servicer_body, *stub_body], type_ignores=[])

    def enter_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        self.__enum_body.put([])

    def leave_enum_descriptor_proto(self, proto: EnumDescriptorProto) -> None:
        body = self.__enum_body.pop()
        info = self.__messages.get_last()

        info.nested.append(
            build_class_def(
                name=proto.name,
                bases=[build_attr("enum", "IntEnum")],
                body=body,
            )
        )

    def enter_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        pass

    def leave_enum_value_descriptor_proto(self, proto: EnumValueDescriptorProto) -> None:
        self.__enum_body.get_last().append(
            ast.Assign(targets=[ast.Name(id=proto.name)], value=ast.Constant(value=proto.number), lineno=None)
        )

    def enter_descriptor_proto(self, proto: DescriptorProto) -> None:
        self.__messages.put(MessageInfo())

    def leave_descriptor_proto(self, proto: DescriptorProto) -> None:
        info = self.__messages.pop()

        if proto.options.map_entry:
            return

        self.__messages.get_last().nested.append(
            build_class_def(
                name=proto.name,
                bases=[build_attr("google", "protobuf", "message", "Message")],
                body=[
                    *info.nested,
                    build_init_stub(info.init_args),
                    *info.properties,
                    self.__build_has_field_method(info),
                    *self.__build_which_oneof_methods(info),
                ],
            )
        )

    def __build_has_field_method(self, info: MessageInfo) -> ast.stmt:
        return build_method_stub(
            name="HasField",
            args=[
                FuncArgInfo.create_pos(
                    name="field_name",
                    annotation=build_generic_ref(build_attr("typing", "Literal"), *info.has_field_args)
                    if info.has_field_args
                    else build_attr("typing", "NoReturn"),
                )
            ],
            returns=build_attr("builtins", "bool") if info.has_field_args else build_attr("typing", "NoReturn"),
        )

    def __build_which_oneof_methods(self, info: MessageInfo) -> t.Sequence[ast.stmt]:
        valid_oneofs = [
            (group_expr, info.oneof_items[group_index])
            for group_index, group_expr in enumerate(info.oneof_groups)
            if info.oneof_items[group_index]
        ]

        if not valid_oneofs:
            return [
                build_method_stub(
                    name="WhichOneof",
                    args=[
                        FuncArgInfo.create_pos(
                            name="oneof_group",
                            annotation=build_attr("typing", "NoReturn"),
                        ),
                    ],
                    returns=build_attr("typing", "NoReturn"),
                ),
            ]

        return [
            build_method_stub(
                name="WhichOneof",
                decorators=[build_attr("typing", "overload")] if len(valid_oneofs) > 1 else None,
                args=[
                    FuncArgInfo.create_pos(
                        name="oneof_group",
                        annotation=build_generic_ref(build_attr("typing", "Literal"), name),
                    ),
                ],
                returns=build_generic_ref(build_attr("typing", "Literal"), *items),
            )
            for name, items in valid_oneofs
        ]

    def enter_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        pass

    def leave_oneof_descriptor_proto(self, proto: OneofDescriptorProto) -> None:
        info = self.__messages.get_last()
        info.oneof_items[len(info.oneof_groups)] = []
        info.oneof_groups.append(ast.Constant(value=proto.name))

    def enter_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        pass

    def leave_field_descriptor_proto(self, proto: FieldDescriptorProto) -> None:
        info = self.__messages.get_last()
        annotation = self.__registry.resolve_field_type(proto)

        info.init_args.append(
            FuncArgInfo.create_kw(
                name=proto.name,
                annotation=build_generic_ref(build_attr("typing", "Optional"), annotation)
                if proto.proto3_optional
                else annotation,
                default=ast.Constant(value=None) if proto.proto3_optional else None,
            )
        )

        info.properties.append(
            build_method_stub(
                name=proto.name,
                decorators=[build_attr("builtins", "property")],
                returns=annotation,
            )
        )

        if proto.proto3_optional:
            info.has_field_args.append(ast.Constant(value=proto.name))

        if not proto.proto3_optional and proto.HasField("oneof_index"):
            info.oneof_items[proto.oneof_index].append(ast.Constant(value=proto.name))

    def enter_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        self.__servicer_body.put([])
        self.__stub_body.put([])

    def leave_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        servicer_body = self.__build_servicer_class(proto, self.__servicer_body.pop())
        servicer_registrator = self.__build_servicer_registrator(proto)
        self.__servicer_body.get_last().extend((servicer_body, servicer_registrator))

        stub_body = self.__build_stub_class(proto, self.__stub_body.pop())
        self.__stub_body.get_last().append(stub_body)

    def __build_servicer_class(self, proto: ServiceDescriptorProto, body: t.Sequence[ast.stmt]) -> ast.stmt:
        return build_class_def(
            name=f"{proto.name}Servicer",
            keywords={"metaclass": build_attr("abc", "ABCMeta")},
            body=body,
        )

    def __build_servicer_registrator(self, proto: ServiceDescriptorProto) -> ast.stmt:
        return build_func_stub(
            name=f"add_{proto.name}Servicer_to_server",
            args=[
                FuncArgInfo.create_pos("servicer", build_attr(f"{proto.name}Servicer")),
                FuncArgInfo.create_pos("server", build_attr("grpc", "aio", "Server")),
            ],
            returns=ast.Constant(value=None),
        )

    def __build_stub_class(self, proto: ServiceDescriptorProto, body: t.Sequence[ast.stmt]) -> ast.stmt:
        return build_class_def(
            name=f"{proto.name}Stub",
            body=[
                build_init_stub(
                    [
                        FuncArgInfo.create_pos("channel", build_attr("grpc", "aio", "Channel")),
                    ]
                ),
                *body,
            ],
        )

    def enter_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        pass

    def leave_method_descriptor_proto(self, proto: MethodDescriptorProto) -> None:
        servicer_body = self.__build_servicer_method(proto)
        self.__servicer_body.get_last().append(servicer_body)

        stub_body = self.__build_stub_method(proto)
        self.__stub_body.get_last().append(stub_body)

    def __build_servicer_method(self, proto: MethodDescriptorProto) -> ast.stmt:
        input_expr = self.__registry.resolve_type_ref(proto.input_type)
        request_expr = input_expr
        if proto.client_streaming:
            request_expr = build_generic_ref(build_attr("typing", "AsyncIterator"), request_expr)

        output_expr = self.__registry.resolve_type_ref(proto.output_type)
        response_expr = output_expr
        if proto.server_streaming:
            response_expr = build_generic_ref(build_attr("typing", "AsyncIterator"), response_expr)

        return build_method_stub(
            name=proto.name,
            decorators=[build_attr("abc", "abstractmethod")],
            args=[
                FuncArgInfo.create_pos("request", request_expr),
                FuncArgInfo.create_pos(
                    "context",
                    build_generic_ref(
                        build_attr("grpc", "aio", "ServicerContext"),
                        input_expr,
                        output_expr,
                    ),
                ),
            ],
            returns=response_expr,
            is_async=True,
        )

    def __build_stub_method(self, proto: MethodDescriptorProto) -> ast.stmt:
        request_expr, response_expr = self.__build_stub_method_request_response_expr(proto)

        return build_method_stub(
            name=proto.name,
            args=[
                FuncArgInfo.create_pos("request", request_expr),
                FuncArgInfo.create_kw(
                    "timeout",
                    build_generic_ref(build_attr("typing", "Optional"), build_attr("builtins", "float")),
                    ast.Constant(value=None),
                ),
                FuncArgInfo.create_kw(
                    "metadata",
                    build_generic_ref(build_attr("typing", "Optional"), build_attr("grpc", "aio", "MetadataType")),
                    ast.Constant(value=None),
                ),
                FuncArgInfo.create_kw(
                    "credentials",
                    build_generic_ref(build_attr("typing", "Optional"), build_attr("grpc", "CallCredentials")),
                    ast.Constant(value=None),
                ),
                FuncArgInfo.create_kw(
                    "wait_for_ready",
                    build_generic_ref(build_attr("typing", "Optional"), build_attr("builtins", "bool")),
                    ast.Constant(value=None),
                ),
                FuncArgInfo.create_kw(
                    "compression",
                    build_generic_ref(build_attr("typing", "Optional"), build_attr("grpc", "Compression")),
                    ast.Constant(value=None),
                ),
            ],
            returns=response_expr,
            is_async=True,
        )

    def __build_stub_method_request_response_expr(self, proto: MethodDescriptorProto) -> t.Tuple[ast.expr, ast.expr]:
        input_expr = self.__registry.resolve_type_ref(proto.input_type)
        output_expr = self.__registry.resolve_type_ref(proto.output_type)

        if not proto.client_streaming and not proto.server_streaming:
            return (
                input_expr,
                build_generic_ref(
                    build_attr("grpc", "aio", "UnaryUnaryCall"),
                    input_expr,
                    output_expr,
                ),
            )

        elif not proto.client_streaming and proto.server_streaming:
            return (
                input_expr,
                build_generic_ref(
                    build_attr("grpc", "aio", "UnaryStreamCall"),
                    input_expr,
                    output_expr,
                ),
            )

        elif proto.client_streaming and not proto.server_streaming:
            return (
                build_generic_ref(build_attr("typing", "AsyncIterator"), input_expr),
                build_generic_ref(
                    build_attr("grpc", "aio", "StreamUnaryCall"),
                    input_expr,
                    output_expr,
                ),
            )

        elif proto.client_streaming and proto.server_streaming:
            return (
                build_generic_ref(build_attr("typing", "AsyncIterator"), input_expr),
                build_generic_ref(
                    build_attr("grpc", "aio", "StreamStreamCall"),
                    input_expr,
                    output_expr,
                ),
            )

        else:
            raise ValueError("invalid streaming options", proto)
