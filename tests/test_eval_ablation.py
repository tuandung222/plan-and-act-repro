from __future__ import annotations

from plan_and_act.eval.ablation import DEFAULT_ABLATION_STAGES, AblationStage


def test_default_ablation_stages_order_and_flags() -> None:
    assert [stage.name for stage in DEFAULT_ABLATION_STAGES] == [
        "no_planner",
        "static_planner",
        "synthetic_data",
        "dynamic_replanning",
        "cot",
    ]

    assert DEFAULT_ABLATION_STAGES[0] == AblationStage("no_planner", False, False, False, False)
    assert DEFAULT_ABLATION_STAGES[-1].cot_enabled is True
