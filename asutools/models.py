from dataclasses import dataclass, field, asdict
from typing import Literal, Optional

ToolType = Literal["python", "java", "shell", "gui", "url"]
EnvType = Literal["python", "venv", "conda", "java"]


@dataclass
class Environment:
    id: str
    name: str
    type: EnvType
    path: str
    version: str = ""
    source: Literal["auto", "user"] = "auto"
    tags: list[str] = field(default_factory=list)
    javafx: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Tool:
    id: str
    name: str
    type: ToolType
    path: str
    category: str = ""
    env_id: Optional[str] = None
    args: str = ""
    tags: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Category:
    id: str
    name: str
    order: int = 0

    def to_dict(self) -> dict:
        return asdict(self)
