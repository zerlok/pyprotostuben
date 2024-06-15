import builtins
import complex_pb2
import google.protobuf.message
import typing

class MessageWithExternalDependency(google.protobuf.message.Message):

    def __init__(self, *, extmsg2: typing.Sequence[complex_pb2.Message2]) -> None:...

    @builtins.property
    def extmsg2(self) -> typing.Sequence[complex_pb2.Message2]:...

    def HasField(self, field_name: typing.NoReturn) -> typing.NoReturn:...

    def WhichOneof(self, oneof_group: typing.NoReturn) -> typing.NoReturn:...