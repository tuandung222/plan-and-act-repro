from __future__ import annotations

from plan_and_act.agents.judge import JudgeAgent
from plan_and_act.data.grounded_plan_gen import generate_grounded_plans
from plan_and_act.data.plan_expansion import expand_plans
from plan_and_act.data.targeted_augmentation import infer_failure_patterns
from plan_and_act.data.trajectory_gen import generate_synthetic_trajectories
from plan_and_act.training.build_sft_data import build_sft_dataset
from plan_and_act.training.dataset_checks import validate_dataset


def test_generate_synthetic_trajectories_shape() -> None:
    trajectories = generate_synthetic_trajectories(["q1", "q2"])

    assert len(trajectories) == 2
    assert trajectories[0]["trajectory_id"] == "traj_1"
    assert trajectories[0]["actions"][-1]["is_final"] is True


def test_generate_grounded_plans_from_trajectories() -> None:
    trajectories = generate_synthetic_trajectories(["q1"])
    grounded = generate_grounded_plans(trajectories)

    assert len(grounded) == 1
    assert grounded[0]["query"] == "q1"
    assert grounded[0]["plan"][0]["action_indices"] == [0]


def test_expand_plans_target_size_and_empty_seed() -> None:
    assert expand_plans([], 5) == []

    expanded = expand_plans([{"query": "base", "plan": [{"step_id": 1}]}], target_size=3)
    assert len(expanded) == 3
    assert expanded[1]["query"].endswith("(variant 2)")


def test_infer_failure_patterns_counts_unknown() -> None:
    result = infer_failure_patterns(
        [
            {"failure_type": "tool"},
            {"failure_type": "tool"},
            {"failure_type": "planner"},
            {},
        ]
    )

    assert result == {"tool": 2, "planner": 1, "unknown": 1}


def test_judge_agent_classifies_terminal_trajectory() -> None:
    judge = JudgeAgent()

    assert judge.classify_trajectory([]) is False
    assert judge.classify_trajectory([{"action_type": "click"}]) is False
    assert judge.classify_trajectory([{"action_type": "exit"}]) is True
    assert judge.classify_trajectory([{"is_final": True}]) is True


def test_build_sft_and_validate_dataset() -> None:
    records = [{"input": "in", "output": "out"}]
    rows = build_sft_dataset(records)
    assert rows == [{"messages": [{"role": "user", "content": "in"}, {"role": "assistant", "content": "out"}]}]

    errors = validate_dataset(records)
    assert errors == []
    assert validate_dataset([{"input": "only"}]) == ["row[0] missing keys: ['output']"]
