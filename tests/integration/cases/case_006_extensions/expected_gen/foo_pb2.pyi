import builtins
import google.protobuf.descriptor_pb2
import google.protobuf.message
import pyprotostuben.protobuf.extension
import typing

class FooMsg(google.protobuf.message.Message):

    def __init__(self, *, field1: builtins.int, field2: builtins.str) -> None:...

    @builtins.property
    def field1(self) -> builtins.int:...

    @builtins.property
    def field2(self) -> builtins.str:...

    def HasField(self, field_name: typing.NoReturn) -> typing.NoReturn:...

    def WhichOneof(self, oneof_group: typing.NoReturn) -> typing.NoReturn:...
foo_service_option: typing.Final[pyprotostuben.protobuf.extension.ExtensionDescriptor[google.protobuf.descriptor_pb2.ServiceOptions, FooMsg]]
foo_method_option: typing.Final[pyprotostuben.protobuf.extension.ExtensionDescriptor[google.protobuf.descriptor_pb2.MethodOptions, FooMsg]]