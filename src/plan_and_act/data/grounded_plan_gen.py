from __future__ import annotations

from typing import Any


def generate_grounded_plans(trajectories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Phase-3 placeholder: reverse-engineer high-level plans from trajectories."""
    grounded: list[dict[str, Any]] = []
    for item in trajectories:
        grounded.append(
            {
                "query": item["query"],
                "plan": [
                    {
                        "step_id": 1,
                        "intent": "Search for the required information",
                        "success_criteria": "Relevant results are visible",
                        "action_indices": [0],
                    },
                    {
                        "step_id": 2,
                        "intent": "Return the final answer",
                        "success_criteria": "User receives final response",
                        "action_indices": [1],
                    },
                ],
            }
        )
    return grounded
