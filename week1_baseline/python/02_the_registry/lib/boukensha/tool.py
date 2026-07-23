from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    block: Callable[..., Any]

    def __str__(self) -> str:
        return f"#<Tool name={self.name} description={self.description[:41]} params={list(self.parameters.keys())}>"
