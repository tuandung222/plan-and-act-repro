from __future__ import annotations

from typing import Any


def expand_plans(seed_plan_pairs: list[dict[str, Any]], target_size: int) -> list[dict[str, Any]]:
    """Phase-3 placeholder: expand query-plan pairs for planner training."""
    if not seed_plan_pairs:
        return []

    expanded: list[dict[str, Any]] = []
    i = 0
    while len(expanded) < target_size:
        source = seed_plan_pairs[i % len(seed_plan_pairs)]
        expanded.append(
            {
                "query": f"{source['query']} (variant {len(expanded) + 1})",
                "plan": source["plan"],
            }
        )
        i += 1
    return expanded
