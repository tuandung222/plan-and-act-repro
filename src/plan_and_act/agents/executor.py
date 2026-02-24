from __future__ import annotations

from typing import Any

from plan_and_act.core.schemas import ExecutorAction, PlanStep
from plan_and_act.core.types import ModelConfig
from plan_and_act.prompts.templates import PromptTemplates
from plan_and_act.tracing.collector import TraceCollector
from plan_and_act.utils.llm import LLMClient


class ExecutorAgent:
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

    def act(
        self,
        *,
        goal: str,
        current_step: PlanStep,
        observation: str,
        step_index: int,
        total_steps: int,
        use_cot: bool,
        step: int = -1,
    ) -> ExecutorAction:
        if self.model_config.provider == "openai" and self.llm.enabled:
            return self._act_with_openai(
                goal=goal,
                current_step=current_step,
                observation=observation,
                use_cot=use_cot,
                step=step,
            )
        return self._act_heuristic(goal, current_step, step_index, total_steps)

    def _act_with_openai(
        self,
        *,
        goal: str,
        current_step: PlanStep,
        observation: str,
        use_cot: bool,
        step: int,
    ) -> ExecutorAction:
        executor_cfg = self.prompts.executor
        cot_hint = self.prompts.cot.get("instruction", "") if use_cot else ""
        system_prompt = (
            executor_cfg["system"]
            + "\nOutput JSON schema: {\"action_type\": \"click|type|search|exit\", \"target\": str, \"arguments\": object, \"rationale\": str, \"is_final\": bool, \"final_answer\": str}"
            + ("\n" + cot_hint if cot_hint else "")
        )
        user_prompt = self.prompts.format_user(
            executor_cfg["user_template"],
            {
                "goal": goal,
                "current_step": current_step.model_dump(),
                "observation": observation,
            },
        )
        payload = self.llm.chat_json(
            model=self.model_config.model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=self.model_config.temperature,
            trace_context={"component": "executor", "step": step},
        )
        return ExecutorAction.model_validate(payload)

    @staticmethod
    def _act_heuristic(
        goal: str,
        current_step: PlanStep,
        step_index: int,
        total_steps: int,
    ) -> ExecutorAction:
        intent = current_step.intent.lower()
        is_final_step = step_index >= (total_steps - 1)

        if is_final_step:
            return ExecutorAction(
                action_type="exit",
                target="",
                arguments={},
                rationale="Final step reached, ending episode.",
                is_final=True,
                final_answer=f"Completed goal: {goal}",
            )

        if "search" in intent or "identify" in intent:
            return ExecutorAction(
                action_type="search",
                target="search_box",
                arguments={"query": goal},
                rationale="Use search to gather necessary information.",
            )

        if "type" in intent:
            return ExecutorAction(
                action_type="type",
                target="input_field",
                arguments={"text": goal},
                rationale="Input required text.",
            )

        return ExecutorAction(
            action_type="click",
            target="primary_cta",
            arguments={},
            rationale="Proceed with a relevant click action.",
        )
