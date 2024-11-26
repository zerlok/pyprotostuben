import re
import typing as t
from functools import cache


@cache
def _get_camel2snake_pattern() -> t.Pattern[str]:
    return re.compile(r"(?<!^)(?=[A-Z])")


def camel2snake(value: str) -> str:
    return _get_camel2snake_pattern().sub("_", value).lower()


def snake2camel(value: str) -> str:
    return "".join(part.title() if part else "_" for part in value.split("_"))
