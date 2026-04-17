from dataclasses import dataclass


@dataclass
class User:
    id: int
    full_name: str
    username: str
    role_name: str
    location: str | None
    is_active: int