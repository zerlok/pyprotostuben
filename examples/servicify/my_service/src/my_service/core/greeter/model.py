import typing as t
import uuid
from dataclasses import dataclass
from datetime import datetime

UserId = t.NewType("UserId", int)


@dataclass(frozen=True, kw_only=True)
class SessionInfo:
    id_: uuid.UUID
    started_at: datetime
    finished_at: datetime


@dataclass(frozen=True, kw_only=True)
class UserInfo:
    id_: UserId
    name: str
    visits: list[SessionInfo]
