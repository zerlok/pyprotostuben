import builtins
import google.protobuf.message
import typing

class Spam(google.protobuf.message.Message):

    def __init__(self, *, eggs: builtins.str, pizza: typing.Sequence[builtins.int], apple: typing.Optional[builtins.str]=None) -> None:...

    @builtins.property
    def eggs(self) -> builtins.str:...

    @builtins.property
    def pizza(self) -> typing.Sequence[builtins.int]:...

    @builtins.property
    def apple(self) -> builtins.str:...

    def HasField(self, field_name: typing.Literal['apple']) -> bool:...

    def WhichOneof(self, oneof_group: typing.NoReturn) -> typing.NoReturn:...