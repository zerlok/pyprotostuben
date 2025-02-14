import builtins
import google.protobuf.message
import typing

class GreetRequest(google.protobuf.message.Message):
    """the greet request"""

    def __init__(self, *, name: builtins.str) -> None:...

    @builtins.property
    def name(self) -> builtins.str:...

    def HasField(self, field_name: typing.NoReturn) -> typing.NoReturn:...

    def WhichOneof(self, oneof_group: typing.NoReturn) -> typing.NoReturn:...

class GreetResponse(google.protobuf.message.Message):
    """the greet response"""

    def __init__(self, *, text: builtins.str) -> None:...

    @builtins.property
    def text(self) -> builtins.str:...

    def HasField(self, field_name: typing.NoReturn) -> typing.NoReturn:...

    def WhichOneof(self, oneof_group: typing.NoReturn) -> typing.NoReturn:...