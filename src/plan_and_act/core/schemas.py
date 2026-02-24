from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from plan_and_act.core.types import ActionType


class PlanStep(BaseModel):
    step_id: int = Field(ge=1)
    intent: str = Field(min_length=1)
    success_criteria: str = ""


class PlannerOutput(BaseModel):
    goal: str
    steps: list[PlanStep]


class ExecutorAction(BaseModel):
    action_type: ActionType
    target: str = ""
    arguments: dict[str, Any] = Field(default_factory=dict)
    rationale: str = ""
    is_final: bool = False
    final_answer: str = ""


class EpisodeArtifact(BaseModel):
    run_id: str
    goal: str
    success: bool
    step_count: int
    final_answer: str
    action_history: list[dict[str, Any]]
    notes: list[str]
