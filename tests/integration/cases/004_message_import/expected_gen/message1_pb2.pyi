import builtins
import google.protobuf.message
import typing

class Message1(google.protobuf.message.Message):

    def __init__(self, *, s: builtins.str) -> None:...

    @builtins.property
    def s(self) -> builtins.str:...

    def HasField(self, field_name: typing.NoReturn) -> typing.NoReturn:...

    def WhichOneof(self, oneof_group: typing.NoReturn) -> typing.NoReturn:...