from __future__ import annotations

from typing import Any, TypedDict


class PlanActState(TypedDict):
    goal: str
    observation: str
    plan: list[dict[str, Any]]
    current_step_idx: int
    action_history: list[dict[str, Any]]
    latest_action: dict[str, Any]
    step_count: int
    max_steps: int
    dynamic_replanning: bool
    needs_replan: bool
    done: bool
    success: bool
    final_answer: str
    use_cot: bool
    notes: list[str]


def build_initial_state(
    goal: str,
    max_steps: int,
    dynamic_replanning: bool,
    use_cot: bool,
    observation: str = "Environment initialized.",
) -> PlanActState:
    return {
        "goal": goal,
        "observation": observation,
        "plan": [],
        "current_step_idx": 0,
        "action_history": [],
        "latest_action": {},
        "step_count": 0,
        "max_steps": max_steps,
        "dynamic_replanning": dynamic_replanning,
        "needs_replan": False,
        "done": False,
        "success": False,
        "final_answer": "",
        "use_cot": use_cot,
        "notes": [],
    }
