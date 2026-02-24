from __future__ import annotations

from plan_and_act.environments.base import EnvironmentAdapter
from plan_and_act.environments.simulator import GenericSimulatorEnvironment
from plan_and_act.environments.tooling import ToolCallingEnvironment
from plan_and_act.tools.factory import build_default_tool_registry
from plan_and_act.tracing.collector import TraceCollector


def build_environment(kind: str, tracer: TraceCollector | None = None) -> EnvironmentAdapter:
    normalized = kind.strip().lower()

    if normalized == "simulator":
        return GenericSimulatorEnvironment()

    if normalized == "tool":
        registry = build_default_tool_registry()
        return ToolCallingEnvironment(
            registry,
            default_tool="web_search",
            action_type_tool_map={
                "search": "web_search",
            },
            tracer=tracer,
        )

    raise ValueError(f"Unsupported environment kind: '{kind}'. Expected one of: simulator, tool")
