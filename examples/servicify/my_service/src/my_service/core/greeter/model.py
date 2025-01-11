import typing as t
import uuid
from dataclasses import dataclass
from datetime import datetime

UserId = t.NewType("UserId", int)


@dataclass(frozen=True, kw_only=True)
class SessionInfo:
    """Period of time user spent on the site."""

    id_: uuid.UUID
    started_at: datetime
    finished_at: datetime


@dataclass(frozen=True, kw_only=True)
class WithName:
    name: str


@dataclass(frozen=True, kw_only=True)
class UserInfo(WithName):
    id_: UserId
    visits: list[SessionInfo]
