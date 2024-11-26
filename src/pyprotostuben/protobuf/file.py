import functools as ft
import typing as t
from pathlib import Path

from google.protobuf.descriptor_pb2 import FileDescriptorProto

from pyprotostuben.python.info import ModuleInfo, PackageInfo


class ProtoFile:
    def __init__(self, proto: FileDescriptorProto) -> None:
        self.__proto = proto

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}: {self.proto_path}>"

    __repr__ = __str__

    @property
    def proto(self) -> FileDescriptorProto:
        return self.__proto

    @ft.cached_property
    def name(self) -> str:
        return self.proto_path.stem

    @ft.cached_property
    def proto_path(self) -> Path:
        return Path(self.__proto.name)

    @ft.cached_property
    def pb2_package(self) -> t.Optional[PackageInfo]:
        package_parts = self.proto_path.parent.parts
        if not package_parts:
            return None

        return PackageInfo.build(*package_parts)

    @ft.cached_property
    def pb2_module(self) -> ModuleInfo:
        return ModuleInfo(self.pb2_package, f"{self.name}_pb2")
