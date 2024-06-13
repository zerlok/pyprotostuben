import ast

from google.protobuf.descriptor_pb2 import FieldDescriptorProto, DescriptorProto, EnumDescriptorProto

from pyprotostuben.codegen.builder import ASTBuilder
from pyprotostuben.protobuf.types.resolver.abc import TypeResolver
from pyprotostuben.python.info import NamespaceInfo


class ASTTypeResolver(TypeResolver[ast.expr]):
    def __init__(self, inner: TypeResolver[NamespaceInfo], ast_builder: ASTBuilder) -> None:
        self.__inner = inner
        self.__ast = ast_builder

    def resolve_final(self) -> ast.expr:
        return self.__build_expr(self.__inner.resolve_final())

    def resolve_no_return(self) -> ast.expr:
        return self.__build_expr(self.__inner.resolve_no_return())

    def resolve_overload(self) -> ast.expr:
        return self.__build_expr(self.__inner.resolve_overload())

    def resolve_literal(self) -> ast.expr:
        return self.__build_expr(self.__inner.resolve_literal())

    def resolve_property(self) -> ast.expr:
        return self.__build_expr(self.__inner.resolve_property())

    def resolve_optional(self) -> ast.expr:
        return self.__build_expr(self.__inner.resolve_optional())

    def resolve_sequence(self) -> ast.expr:
        return self.__build_expr(self.__inner.resolve_sequence())

    def resolve_mapping(self) -> ast.expr:
        return self.__build_expr(self.__inner.resolve_mapping())

    def resolve_protobuf_enum_base(self, proto: EnumDescriptorProto) -> ast.expr:
        return self.__build_expr(self.__inner.resolve_protobuf_enum_base(proto))

    def resolve_protobuf_message_base(self, proto: DescriptorProto) -> ast.expr:
        return self.__build_expr(self.__inner.resolve_protobuf_message_base(proto))

    def resolve_protobuf_field(self, proto: FieldDescriptorProto) -> ast.expr:
        expr = self.__build_expr(self.__inner.resolve_protobuf_field(proto))
        if proto.label == FieldDescriptorProto.Label.LABEL_REPEATED:
            expr = self.__ast.build_generic_instance_expr(self.resolve_sequence(), expr)

        return expr

    def __build_expr(self, info: NamespaceInfo) -> ast.expr:
        return self.__ast.build_attr_expr(*info.parts)
