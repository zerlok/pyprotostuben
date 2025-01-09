from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class UserInfo:
    id_: int
    name: str
