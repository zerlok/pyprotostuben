import builtins
import google.protobuf.message
import google.protobuf.timestamp_pb2
import message1_pb2
import message2_pb2
import message3_pb2
import typing

class MessageImport(google.protobuf.message.Message):

    def __init__(self, *, m1: message1_pb2.Message1, m2: message2_pb2.Message2, m3: message3_pb2.Message3, ts: google.protobuf.timestamp_pb2.Timestamp) -> None:...

    @builtins.property
    def m1(self) -> message1_pb2.Message1:...

    @builtins.property
    def m2(self) -> message2_pb2.Message2:...

    @builtins.property
    def m3(self) -> message3_pb2.Message3:...

    @builtins.property
    def ts(self) -> google.protobuf.timestamp_pb2.Timestamp:...

    def HasField(self, field_name: typing.NoReturn) -> typing.NoReturn:...

    def WhichOneof(self, oneof_group: typing.NoReturn) -> typing.NoReturn:...