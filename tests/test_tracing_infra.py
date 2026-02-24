from __future__ import annotations

import json
from pathlib import Path

from plan_and_act.tracing import TraceCollector, TraceConfig
from plan_and_act.tracing.schemas import TRACE_EVENT_VERSION, TRACE_SCHEMA_VERSION, TraceEvent, TraceSession


def test_trace_collector_writes_session_and_events(tmp_path: Path) -> None:
    cfg = TraceConfig(enabled=True, base_dir=str(tmp_path), flush_every=1)
    collector = TraceCollector(config=cfg, run_id="run_test")

    collector.start_session(
        goal="trace-goal",
        environment={"kind": "tool", "name": "tool_calling"},
        model_stack={"planner": {"model": "gpt-4"}},
        runtime_config={"max_steps": 4},
    )
    collector.log_event(
        event_type="planner_input",
        step=0,
        payload={"goal": "trace-goal"},
    )
    collector.log_event(
        event_type="planner_output",
        step=0,
        payload={"steps": [{"step_id": 1, "intent": "x", "success_criteria": "y"}]},
    )
    collector.close(status="completed", summary={"success": True})

    run_dir = tmp_path / "run_test"
    assert run_dir.exists()

    session_path = run_dir / "session.json"
    events_path = run_dir / "events.jsonl"
    assert session_path.exists()
    assert events_path.exists()

    session = json.loads(session_path.read_text(encoding="utf-8"))
    assert session["status"] == "completed"
    assert session["goal"] == "trace-goal"
    assert session["schema_version"] == TRACE_SCHEMA_VERSION
    assert session["summary"]["event_count"] == 2

    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(events) == 2
    assert events[0]["schema_version"] == TRACE_SCHEMA_VERSION
    assert events[0]["event_version"] == TRACE_EVENT_VERSION
    assert events[0]["event_type"] == "planner_input"
    assert events[1]["event_type"] == "planner_output"


def test_trace_schema_backward_compatible_defaults() -> None:
    old_session = {
        "run_id": "legacy",
        "goal": "legacy goal",
    }
    parsed_session = TraceSession.model_validate(old_session)
    assert parsed_session.schema_version == TRACE_SCHEMA_VERSION

    old_event = {
        "run_id": "legacy",
        "step": 0,
        "event_type": "planner_input",
        "payload": {"goal": "legacy goal"},
    }
    parsed_event = TraceEvent.model_validate(old_event)
    assert parsed_event.schema_version == TRACE_SCHEMA_VERSION
    assert parsed_event.event_version == TRACE_EVENT_VERSION
