import builtins
import enum
import google.protobuf.descriptor
import google.protobuf.message
import typing

class MyEnum(enum.IntEnum):
    MY_ENUM_VAL_ZERO = 0
    MY_ENUM_VAL_ONE = 1
    MY_ENUM_VAL_TWO = 2

class Container(google.protobuf.message.Message):

    def __init__(self, *, b1: builtins.bool, i32: builtins.int, f: builtins.float, str: builtins.str, int_seq: typing.Sequence[builtins.int], str_seq: typing.Sequence[builtins.str], opt_str: typing.Optional[builtins.str]=None, i64_to_float: typing.Mapping[builtins.int, builtins.float], str_to_bool: typing.Mapping[builtins.str, builtins.bool], nested: Nested, nested_seq: typing.Sequence[Nested], str_to_nested: typing.Mapping[builtins.str, Nested]) -> None:...

    @builtins.property
    def b1(self) -> builtins.bool:...

    @builtins.property
    def i32(self) -> builtins.int:...

    @builtins.property
    def f(self) -> builtins.float:...

    @builtins.property
    def str(self) -> builtins.str:...

    @builtins.property
    def int_seq(self) -> typing.Sequence[builtins.int]:...

    @builtins.property
    def str_seq(self) -> typing.Sequence[builtins.str]:...

    @builtins.property
    def opt_str(self) -> builtins.str:...

    @builtins.property
    def i64_to_float(self) -> typing.Mapping[builtins.int, builtins.float]:...

    @builtins.property
    def str_to_bool(self) -> typing.Mapping[builtins.str, builtins.bool]:...

    @builtins.property
    def nested(self) -> Nested:...

    @builtins.property
    def nested_seq(self) -> typing.Sequence[Nested]:...

    @builtins.property
    def str_to_nested(self) -> typing.Mapping[builtins.str, Nested]:...

    def HasField(self, field_name: typing.Literal['opt_str']) -> builtins.bool:...

    def WhichOneof(self, oneof_group: typing.NoReturn) -> typing.NoReturn:...
    DESCRIPTOR: google.protobuf.descriptor.Descriptor

class Nested(google.protobuf.message.Message):

    def __init__(self, *, b: typing.Optional[builtins.bool]=None, i: typing.Optional[builtins.int]=None, s: typing.Optional[builtins.str]=None) -> None:...

    @builtins.property
    def b(self) -> builtins.bool:...

    @builtins.property
    def i(self) -> builtins.int:...

    @builtins.property
    def s(self) -> builtins.str:...

    def HasField(self, field_name: typing.NoReturn) -> typing.NoReturn:...

    def WhichOneof(self, oneof_group: typing.Literal['value']) -> typing.Optional[typing.Literal['b', 'i', 's']]:...
    DESCRIPTOR: google.protobuf.descriptor.Descriptor
DESCRIPTOR: google.protobuf.descriptor.FileDescriptor