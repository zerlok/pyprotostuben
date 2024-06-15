import builtins
import google.protobuf.message
import typing

class Message3(google.protobuf.message.Message):

    def __init__(self, *, i32: builtins.int) -> None:...

    @builtins.property
    def i32(self) -> builtins.int:...

    def HasField(self, field_name: typing.NoReturn) -> typing.NoReturn:...

    def WhichOneof(self, oneof_group: typing.NoReturn) -> typing.NoReturn:...