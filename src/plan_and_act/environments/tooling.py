from __future__ import annotations

import json

from plan_and_act.core.schemas import ExecutorAction
from plan_and_act.environments.base import EnvironmentAdapter, EnvironmentStepResult
from plan_and_act.tools.base import ToolRegistry
from plan_and_act.tracing.collector import TraceCollector


class ToolCallingEnvironment(EnvironmentAdapter):
    """Generic tool-calling environment for non-browser agent domains."""

    name = "tool_calling"

    def __init__(
        self,
        registry: ToolRegistry,
        *,
        default_tool: str | None = None,
        action_type_tool_map: dict[str, str] | None = None,
        tracer: TraceCollector | None = None,
    ) -> None:
        self.registry = registry
        self.default_tool = default_tool
        self.action_type_tool_map = action_type_tool_map or {}
        self.tracer = tracer

    def reset(self, *, goal: str) -> str:
        registered = sorted(self.registry.tools.keys())
        return f"Tool environment initialized for goal: {goal}. Registered tools={registered}"

    def _resolve_tool_name(self, action: ExecutorAction) -> str | None:
        if action.target.startswith("tool:"):
            return action.target.split(":", 1)[1].strip() or None
        mapped = self.action_type_tool_map.get(action.action_type)
        if mapped:
            return mapped
        return self.default_tool

    def step(self, *, action: ExecutorAction, step_count: int) -> EnvironmentStepResult:
        if action.action_type == "exit":
            return EnvironmentStepResult(
                observation=f"Step {step_count}: Exit action requested.",
                done=True,
                success=True,
                final_answer=action.final_answer,
            )

        tool_name = self._resolve_tool_name(action)
        if not tool_name:
            if self.tracer:
                self.tracer.log_event(
                    event_type="tool_call_end",
                    step=step_count,
                    payload={
                        "tool_name": "",
                        "ok": False,
                        "error": "no_tool_selected",
                        "action_type": action.action_type,
                        "target": action.target,
                        "arguments": action.arguments,
                    },
                )
            return EnvironmentStepResult(
                observation=(
                    f"Step {step_count}: No tool selected for action_type='{action.action_type}'. "
                    f"Set target='tool:<name>' or configure a default tool."
                ),
            )

        if self.tracer:
            self.tracer.log_event(
                event_type="tool_call_start",
                step=step_count,
                payload={
                    "tool_name": tool_name,
                    "action_type": action.action_type,
                    "target": action.target,
                    "arguments": action.arguments,
                },
            )
        result = self.registry.call(tool_name, action.arguments)
        if self.tracer:
            self.tracer.log_event(
                event_type="tool_call_end",
                step=step_count,
                payload={
                    "tool_name": tool_name,
                    "ok": bool(result.get("ok", False)),
                    "result": result,
                },
            )
        observation = (
            f"Step {step_count}: Tool[{tool_name}] returned: {json.dumps(result, ensure_ascii=True)}"
        )
        notes: list[str] = [] if result.get("ok", False) else [f"Tool call failed: {result.get('error', 'unknown')}."]
        return EnvironmentStepResult(observation=observation, notes=notes)
