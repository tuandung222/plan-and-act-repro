from __future__ import annotations

from typing import Any

from plan_and_act.core.schemas import PlanStep, PlannerOutput
from plan_and_act.core.types import ModelConfig
from plan_and_act.prompts.templates import PromptTemplates
from plan_and_act.tracing.collector import TraceCollector
from plan_and_act.utils.llm import LLMClient


class ReplannerAgent:
    def __init__(
        self,
        model_config: ModelConfig,
        prompts: PromptTemplates,
        tracer: TraceCollector | None = None,
    ) -> None:
        self.model_config = model_config
        self.prompts = prompts
        self.tracer = tracer
        self.llm = LLMClient(trace_hook=self._llm_trace_hook if tracer else None)

    def _llm_trace_hook(self, payload: dict[str, Any]) -> None:
        if self.tracer is None:
            return
        raw_step = payload.get("step", -1)
        step = raw_step if isinstance(raw_step, int) else -1
        self.tracer.log_event(event_type="llm_call", step=step, payload=payload)

    def replan(
        self,
        *,
        goal: str,
        previous_plan: list[dict[str, Any]],
        action_history: list[dict[str, Any]],
        observation: str,
        use_cot: bool,
        step: int = -1,
    ) -> PlannerOutput:
        if self.model_config.provider == "openai" and self.llm.enabled:
            return self._replan_with_openai(
                goal=goal,
                previous_plan=previous_plan,
                action_history=action_history,
                observation=observation,
                use_cot=use_cot,
                step=step,
            )
        return self._replan_heuristic(goal, observation)

    def _replan_with_openai(
        self,
        *,
        goal: str,
        previous_plan: list[dict[str, Any]],
        action_history: list[dict[str, Any]],
        observation: str,
        use_cot: bool,
        step: int,
    ) -> PlannerOutput:
        replanner_cfg = self.prompts.replanner
        cot_hint = self.prompts.cot.get("instruction", "") if use_cot else ""
        system_prompt = (
            replanner_cfg["system"]
            + "\nOutput JSON schema: {\"goal\": str, \"steps\": [{\"step_id\": int, \"intent\": str, \"success_criteria\": str}]}"
            + ("\n" + cot_hint if cot_hint else "")
        )
        user_prompt = self.prompts.format_user(
            replanner_cfg["user_template"],
            {
                "goal": goal,
                "plan": previous_plan,
                "action_history": action_history,
                "observation": observation,
            },
        )
        payload = self.llm.chat_json(
            model=self.model_config.model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=self.model_config.temperature,
            trace_context={"component": "replanner", "step": step},
        )
        return PlannerOutput.model_validate(payload)

    @staticmethod
    def _replan_heuristic(goal: str, observation: str) -> PlannerOutput:
        steps = [
            PlanStep(
                step_id=1,
                intent="Use latest observation context and finalize the user goal",
                success_criteria="Final answer produced",
            )
        ]
        return PlannerOutput(goal=f"{goal}", steps=steps)
