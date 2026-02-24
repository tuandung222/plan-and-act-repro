from __future__ import annotations

from plan_and_act.core.schemas import ExecutorAction
from plan_and_act.environments.base import EnvironmentAdapter, EnvironmentStepResult


class GenericSimulatorEnvironment(EnvironmentAdapter):
    """Domain-agnostic deterministic simulator for fast local validation."""

    name = "generic_simulator"

    def reset(self, *, goal: str) -> str:
        return f"Environment initialized for goal: {goal}"

    def step(self, *, action: ExecutorAction, step_count: int) -> EnvironmentStepResult:
        if action.action_type == "search":
            observation = f"Step {step_count}: Search executed with arguments={action.arguments}."
            return EnvironmentStepResult(observation=observation)

        if action.action_type == "click":
            observation = f"Step {step_count}: Click executed on target='{action.target}'."
            return EnvironmentStepResult(observation=observation)

        if action.action_type == "type":
            observation = f"Step {step_count}: Type executed on target='{action.target}' with arguments={action.arguments}."
            return EnvironmentStepResult(observation=observation)

        if action.action_type == "exit":
            observation = f"Step {step_count}: Exit action requested."
            return EnvironmentStepResult(
                observation=observation,
                done=True,
                success=True,
                final_answer=action.final_answer,
            )

        return EnvironmentStepResult(observation=f"Step {step_count}: Observation updated.")
