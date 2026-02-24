from __future__ import annotations

from typing import Any


def compute_episode_metrics(state: dict[str, Any]) -> dict[str, Any]:
    step_count = int(state.get("step_count", 0))
    success = bool(state.get("success", False))
    action_history = state.get("action_history", [])
    replans = sum(1 for n in state.get("notes", []) if "Replanned" in n)

    return {
        "task_success": success,
        "step_count": step_count,
        "actions_taken": len(action_history),
        "replans": replans,
    }
