from dataclasses import dataclass

# UserId = t.NewType("UserId", int)


@dataclass(frozen=True, kw_only=True)
class UserInfo:
    id_: int
    name: str
