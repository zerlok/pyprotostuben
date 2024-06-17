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
from pyprotostuben.protobuf.registry import TypeRegistry, ProtoInfo
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
)
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

        modules: t.Dict[Path, ast.Module] = {}

        visit(DFSWalkingProtoVisitor(ModuleASTGenerator(self.__registry, modules)), file.descriptor)
        log.debug("proto visited", modules=modules)

        for path, module_ast in modules.items():
            module_content = ast.unparse(module_ast)
            log.info("module generated", path=path)

            yield file, path, module_content


class ModuleASTGenerator(ProtoVisitorDecorator, LoggerMixin):
    def __init__(self, registry: TypeRegistry, modules: t.MutableMapping[Path, ast.Module]) -> None:
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
            self.__modules[file.pb2_message.stub_file] = ast.Module(body=info.nested, type_ignores=[])

        servicer_body = self.__servicer_body.pop()
        if servicer_body:
            self.__modules[file.pb2_grpc.stub_file] = ast.Module(body=servicer_body, type_ignores=[])

        stub_body = self.__stub_body.pop()
        if stub_body:
            self.__modules[file.pb2_grpc.stub_file] = ast.Module(body=stub_body, type_ignores=[])

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
                    build_method_stub(
                        name="HasField",
                        args=[
                            FuncArgInfo.create_pos(
                                name="field_name",
                                annotation=build_generic_ref(build_attr("typing", "Literal"), *info.has_field_args)
                                if info.has_field_args
                                else build_attr("typing", "NoReturn"),
                            )
                        ],
                        returns=build_attr("builtins", "bool"),
                    ),
                    *self.__build_which_oneof_methods(info),
                ],
            )
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
        self.__stub_body.put(
            [
                build_init_stub(
                    [
                        FuncArgInfo.create_pos("channel", build_attr("grpc", "aio", "Channel")),
                    ]
                ),
            ],
        )

    def leave_service_descriptor_proto(self, proto: ServiceDescriptorProto) -> None:
        servicer_body = self.__build_servicer_class(proto, self.__servicer_body.pop())
        self.__servicer_body.get_last().append(servicer_body)

        stub_body = self.__build_stub_class(proto, self.__stub_body.pop())
        self.__stub_body.get_last().append(stub_body)

    def __build_servicer_class(self, proto: ServiceDescriptorProto, body: t.Sequence[ast.stmt]) -> ast.stmt:
        return build_class_def(
            name=f"{proto.name}Servicer",
            body=body,
        )

    def __build_stub_class(self, proto: ServiceDescriptorProto, body: t.Sequence[ast.stmt]) -> ast.stmt:
        return build_class_def(
            name=f"{proto.name}Stub",
            body=body,
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
        output_expr = self.__registry.resolve_type_ref(proto.output_type)

        return build_method_stub(
            name=proto.name,
            decorators=[build_attr("abc", "abstractmethod")],
            args=[
                FuncArgInfo.create_pos("request", input_expr),
                FuncArgInfo.create_pos(
                    "context",
                    build_generic_ref(
                        build_attr("grpc", "aio", "ServicerContext"),
                        input_expr,
                        output_expr,
                    ),
                ),
            ],
            returns=output_expr,
            is_async=True,
        )

    def __build_stub_method(self, proto: MethodDescriptorProto) -> ast.stmt:
        input_expr = self.__registry.resolve_type_ref(proto.input_type)
        output_expr = self.__registry.resolve_type_ref(proto.output_type)

        return build_method_stub(
            name=proto.name,
            args=[
                FuncArgInfo.create_pos("request", input_expr),
            ],
            returns=output_expr,
            is_async=True,
        )
