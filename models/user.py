# Student Name: Shune Pyae Pyae (Evelyn) Aung
# Student ID: 24028257
# Module: UFCF8S-30-2 Advanced Software Development

from dataclasses import dataclass


@dataclass
class User:
    id: int
    full_name: str
    username: str
    role_name: str
    location: str | None
    is_active: int