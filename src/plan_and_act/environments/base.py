from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from plan_and_act.core.schemas import ExecutorAction


@dataclass
class EnvironmentStepResult:
    observation: str
    done: bool = False
    success: bool = False
    final_answer: str = ""
    notes: list[str] = field(default_factory=list)


class EnvironmentAdapter(Protocol):
    name: str

    def reset(self, *, goal: str) -> str:
        """Initialize environment state and return initial observation."""

    def step(self, *, action: ExecutorAction, step_count: int) -> EnvironmentStepResult:
        """Execute one action in the environment and return resulting transition."""
