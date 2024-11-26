import typing as t

from google.protobuf.descriptor_pb2 import SourceCodeInfo


def get_comment_blocks(location: t.Optional[SourceCodeInfo.Location]) -> t.Sequence[str]:
    if location is None:
        return []

    blocks: list[str] = []
    blocks.extend(comment.strip() for comment in location.leading_detached_comments)

    if location.HasField("leading_comments"):
        blocks.append(location.leading_comments.strip())

    if location.HasField("trailing_comments"):
        blocks.append(location.trailing_comments.strip())

    return blocks


def build_docstring(location: t.Optional[SourceCodeInfo.Location]) -> t.Optional[str]:
    return "\n\n".join(get_comment_blocks(location))
