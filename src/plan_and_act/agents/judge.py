from __future__ import annotations

from typing import Any


class JudgeAgent:
    """Simple placeholder judge for synthetic-data filtering stages."""

    def classify_trajectory(self, trajectory: list[dict[str, Any]]) -> bool:
        if not trajectory:
            return False
        last_action = trajectory[-1]
        return bool(last_action.get("is_final") or last_action.get("action_type") == "exit")
