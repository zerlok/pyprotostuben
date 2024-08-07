import builtins
import google.protobuf.message
import typing

class STD(google.protobuf.message.Message):

    def __init__(self, *, b1: builtins.bool, i32: builtins.int, f: builtins.float, str: builtins.str, int_seq: typing.Sequence[builtins.int], str_seq: typing.Sequence[builtins.str], opt_str: typing.Optional[builtins.str]=None, i64_to_float: typing.Mapping[builtins.int, builtins.float], str_to_bool: typing.Mapping[builtins.str, builtins.bool]) -> None:...

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

    def HasField(self, field_name: typing.Literal['opt_str']) -> builtins.bool:...

    def WhichOneof(self, oneof_group: typing.NoReturn) -> typing.NoReturn:...