from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class Tool(Protocol):
    name: str

    def run(self, arguments: dict[str, Any]) -> dict[str, Any]:
        """Run tool with structured arguments."""


@dataclass
class ToolRegistry:
    tools: dict[str, Tool]

    def has(self, name: str) -> bool:
        return name in self.tools

    def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in self.tools:
            return {"ok": False, "error": f"Tool '{name}' is not registered"}
        return self.tools[name].run(arguments)
