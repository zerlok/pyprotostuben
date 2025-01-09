import enum
from dataclasses import dataclass
from datetime import datetime


class UserStatus(enum.Enum):
    UNVERIFIED = enum.auto()
    VERIFIED = enum.auto()
    BANNED = enum.auto()


@dataclass(frozen=True, kw_only=True)
class User:
    id: int
    username: str
    created_at: datetime
    status: UserStatus


class Rectangle:
    def __init__(self, height: int, width: int) -> None:
        self.height = height
        self.width = width
