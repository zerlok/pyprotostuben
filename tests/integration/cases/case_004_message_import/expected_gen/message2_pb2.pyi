import builtins
import google.protobuf.message
import message1_pb2
import typing

class Message2(google.protobuf.message.Message):

    def __init__(self, *, m1: message1_pb2.Message1) -> None:...

    @builtins.property
    def m1(self) -> message1_pb2.Message1:...

    def HasField(self, field_name: typing.NoReturn) -> typing.NoReturn:...

    def WhichOneof(self, oneof_group: typing.NoReturn) -> typing.NoReturn:...