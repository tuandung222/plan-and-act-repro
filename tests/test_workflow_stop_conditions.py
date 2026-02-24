from __future__ import annotations

from plan_and_act.core.schemas import ExecutorAction, PlannerOutput
from plan_and_act.core.state import build_initial_state
from plan_and_act.environments.simulator import GenericSimulatorEnvironment
from plan_and_act.graph.workflow import build_workflow


class EmptyPlanner:
    def plan(self, **kwargs) -> PlannerOutput:
        return PlannerOutput(goal=kwargs["goal"], steps=[])


class NoopReplanner:
    def replan(self, **kwargs) -> PlannerOutput:
        return PlannerOutput(goal=kwargs["goal"], steps=[])


class NonFinalExecutor:
    def act(self, **kwargs) -> ExecutorAction:
        return ExecutorAction(
            action_type="click",
            target="any",
            arguments={},
            rationale="non-final",
            is_final=False,
        )


def test_plan_exhaustion_stops_when_dynamic_replanning_disabled() -> None:
    workflow = build_workflow(
        planner=EmptyPlanner(),
        executor=NonFinalExecutor(),
        replanner=NoopReplanner(),
        environment=GenericSimulatorEnvironment(),
    )

    init = build_initial_state(
        goal="any-goal",
        max_steps=5,
        dynamic_replanning=False,
        use_cot=False,
        observation="init",
    )

    final_state = workflow.invoke(init)
    assert final_state["done"] is True
    assert final_state["success"] is False
    assert "plan exhausted" in final_state["final_answer"].lower()
