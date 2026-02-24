from __future__ import annotations

from plan_and_act.core.state import PlanActState


def route_after_executor(state: PlanActState) -> str:
    if state["done"]:
        return "end"
    if state["dynamic_replanning"] and state["needs_replan"]:
        return "replan"
    return "continue"
