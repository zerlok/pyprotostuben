import typing
import typing as t

from google.protobuf.descriptor import (
    Descriptor,
    EnumDescriptor,
    FieldDescriptor,
    FileDescriptor,
    MethodDescriptor,
    ServiceDescriptor,
)

C = t.TypeVar("C")
T = t.TypeVar("T")


@typing.final
class ExtensionDescriptor(t.Generic[C, T], FieldDescriptor):
    """Generic FieldDescriptor, designed for `get_extension` method."""


def get_extension(
    source: FileDescriptor | EnumDescriptor | Descriptor | FieldDescriptor | ServiceDescriptor | MethodDescriptor,
    ext: ExtensionDescriptor[t.Any, T],
) -> t.Optional[T]:
    """Get extension from the source options, type safe."""

    opts = source.GetOptions()
    # TODO: find a way to get `_ExtensionFieldDescriptor` type which is expected in `HasExtension`.
    if not opts.HasExtension(t.cast(t.Any, ext)):
        return None

    return t.cast(T, opts.Extensions[t.cast(t.Any, ext)])
