import enum
import typing as t
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


@dataclass(frozen=True, kw_only=True)
class SuperUser(User):
    super_created_at: datetime


@dataclass(frozen=True, kw_only=True)
class HostInfo:
    domain: str
    user: t.Optional[SuperUser]


@dataclass(frozen=True, kw_only=True)
class ChatRoom:
    name: str
    host: HostInfo
    users: list[User]
    tags: t.Collection[str]


class Rectangle:
    def __init__(self, height: int, width: int) -> None:
        self.height = height
        self.width = width
