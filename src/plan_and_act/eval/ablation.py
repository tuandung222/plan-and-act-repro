from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AblationStage:
    name: str
    planner_enabled: bool
    synthetic_data_enabled: bool
    dynamic_replanning: bool
    cot_enabled: bool


DEFAULT_ABLATION_STAGES = [
    AblationStage("no_planner", False, False, False, False),
    AblationStage("static_planner", True, False, False, False),
    AblationStage("synthetic_data", True, True, False, False),
    AblationStage("dynamic_replanning", True, True, True, False),
    AblationStage("cot", True, True, True, True),
]
