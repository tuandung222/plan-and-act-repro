from __future__ import annotations

from typing import Any


def generate_synthetic_trajectories(seed_queries: list[str]) -> list[dict[str, Any]]:
    """Phase-3 placeholder: generate synthetic trajectories from seed queries."""
    trajectories: list[dict[str, Any]] = []
    for idx, query in enumerate(seed_queries, start=1):
        trajectories.append(
            {
                "trajectory_id": f"traj_{idx}",
                "query": query,
                "actions": [
                    {"action_type": "search", "target": "search_box", "arguments": {"query": query}},
                    {"action_type": "exit", "is_final": True, "final_answer": "placeholder"},
                ],
            }
        )
    return trajectories
