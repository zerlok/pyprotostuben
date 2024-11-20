import builtins
import enum
import google.protobuf.message
import typing

class MyEnum(enum.IntEnum):
    """this is a comment to enum"""
    MY_ENUM_VAL_ZERO = 0
    MY_ENUM_VAL_FIRST = 1
    MY_ENUM_VAL_SECOND = 2
    MY_ENUM_VAL_THIRD = 3

class Msg1(google.protobuf.message.Message):
    """this is a leading comment to Msg1

this is a trailing comment to Msg1"""

    def __init__(self, *, field1: builtins.int, field2: builtins.str) -> None:...

    @builtins.property
    def field1(self) -> builtins.int:...

    @builtins.property
    def field2(self) -> builtins.str:...

    def HasField(self, field_name: typing.NoReturn) -> typing.NoReturn:...

    def WhichOneof(self, oneof_group: typing.NoReturn) -> typing.NoReturn:...

class Msg2(google.protobuf.message.Message):
    """this is a leading comment to Msg2"""

    def __init__(self, *, name: builtins.str) -> None:...

    @builtins.property
    def name(self) -> builtins.str:...

    def HasField(self, field_name: typing.NoReturn) -> typing.NoReturn:...

    def WhichOneof(self, oneof_group: typing.NoReturn) -> typing.NoReturn:...

class Msg3(google.protobuf.message.Message):
    """this is a multiline
 comment

 to
 Msg3"""

    def __init__(self) -> None:...

    def HasField(self, field_name: typing.NoReturn) -> typing.NoReturn:...

    def WhichOneof(self, oneof_group: typing.NoReturn) -> typing.NoReturn:...