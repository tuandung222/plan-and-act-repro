from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from plan_and_act.core.schemas import ExecutorAction
from plan_and_act.environments.factory import build_environment
from plan_and_act.environments.simulator import GenericSimulatorEnvironment
from plan_and_act.environments.tooling import ToolCallingEnvironment
from plan_and_act.tools.base import ToolRegistry
from plan_and_act.tracing import TraceCollector, TraceConfig


@dataclass
class EchoTool:
    name: str = "echo"

    def run(self, arguments: dict) -> dict:
        return {"ok": True, "echo": arguments}


def test_factory_builds_supported_environments() -> None:
    simulator = build_environment("simulator")
    tool = build_environment("tool")

    assert simulator.name == "generic_simulator"
    assert tool.name == "tool_calling"


def test_tool_environment_executes_registered_tool() -> None:
    env = ToolCallingEnvironment(
        ToolRegistry({"echo": EchoTool()}),
        default_tool="echo",
    )

    obs0 = env.reset(goal="Test generic tool domain")
    assert "Registered tools" in obs0

    result = env.step(
        action=ExecutorAction(
            action_type="search",
            target="",
            arguments={"query": "hello"},
        ),
        step_count=1,
    )

    assert "Tool[echo]" in result.observation
    assert result.done is False
    assert result.success is False


def test_tool_environment_exit_action_finishes_episode() -> None:
    env = build_environment("tool")
    result = env.step(
        action=ExecutorAction(
            action_type="exit",
            is_final=True,
            final_answer="done",
        ),
        step_count=2,
    )

    assert result.done is True
    assert result.success is True
    assert result.final_answer == "done"


def test_tool_environment_maps_search_action_to_web_search_tool() -> None:
    env = build_environment("tool")
    env.reset(goal="Search something")
    result = env.step(
        action=ExecutorAction(
            action_type="search",
            target="",
            arguments={"query": "plan and act llm agents", "max_results": 1},
        ),
        step_count=1,
    )

    assert "Tool[web_search]" in result.observation


def test_simulator_environment_action_branches() -> None:
    env = GenericSimulatorEnvironment()
    assert "Environment initialized" in env.reset(goal="x")

    search = env.step(
        action=ExecutorAction(action_type="search", target="s", arguments={"q": "x"}),
        step_count=1,
    )
    click = env.step(
        action=ExecutorAction(action_type="click", target="btn", arguments={}),
        step_count=2,
    )
    typed = env.step(
        action=ExecutorAction(action_type="type", target="input", arguments={"text": "abc"}),
        step_count=3,
    )
    ended = env.step(
        action=ExecutorAction(action_type="exit", is_final=True, final_answer="done"),
        step_count=4,
    )

    assert "Search executed" in search.observation
    assert "Click executed" in click.observation
    assert "Type executed" in typed.observation
    assert ended.done is True
    assert ended.final_answer == "done"


def test_tool_environment_emits_structured_tool_call_events(tmp_path: Path) -> None:
    tracer = TraceCollector(
        config=TraceConfig(enabled=True, base_dir=str(tmp_path)),
        run_id="tool_trace",
    )
    tracer.start_session(
        goal="trace tools",
        environment={"kind": "tool", "name": "tool_calling"},
        model_stack={},
        runtime_config={},
    )
    env = ToolCallingEnvironment(
        ToolRegistry({"echo": EchoTool()}),
        default_tool="echo",
        tracer=tracer,
    )

    env.reset(goal="emit tool events")
    _ = env.step(
        action=ExecutorAction(
            action_type="search",
            target="",
            arguments={"query": "hello"},
        ),
        step_count=1,
    )
    tracer.close(status="completed", summary={})

    events_path = tmp_path / "tool_trace" / "events.jsonl"
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    event_types = [event["event_type"] for event in events]

    assert "tool_call_start" in event_types
    assert "tool_call_end" in event_types
