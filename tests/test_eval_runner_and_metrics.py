from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from plan_and_act.eval import runner
from plan_and_act.eval.metrics import compute_episode_metrics
from plan_and_act.graph.transitions import route_after_executor


def test_compute_episode_metrics_counts_replans() -> None:
    metrics = compute_episode_metrics(
        {
            "step_count": 4,
            "success": True,
            "action_history": [{}, {}, {}],
            "notes": ["Replanned based on latest observation.", "Other note", "Replanned again"],
        }
    )

    assert metrics == {
        "task_success": True,
        "step_count": 4,
        "actions_taken": 3,
        "replans": 2,
    }


def test_route_after_executor_all_branches() -> None:
    assert route_after_executor({"done": True, "dynamic_replanning": True, "needs_replan": True}) == "end"
    assert route_after_executor({"done": False, "dynamic_replanning": True, "needs_replan": True}) == "replan"
    assert route_after_executor({"done": False, "dynamic_replanning": False, "needs_replan": True}) == "continue"


def test_runner_config_loaders(tmp_path: Path) -> None:
    runtime_cfg = tmp_path / "runtime.yaml"
    runtime_cfg.write_text(
        yaml.safe_dump(
            {
                "seed": 7,
                "max_steps": 3,
                "dynamic_replanning": False,
                "use_cot": True,
                "save_artifacts": False,
            }
        ),
        encoding="utf-8",
    )
    model_cfg = tmp_path / "models.yaml"
    model_cfg.write_text(
        yaml.safe_dump(
            {
                "planner": {"provider": "heuristic"},
                "executor": {"provider": "heuristic"},
                "replanner": {"provider": "heuristic"},
            }
        ),
        encoding="utf-8",
    )
    trace_cfg = tmp_path / "trace.yaml"
    trace_cfg.write_text(
        yaml.safe_dump(
            {
                "enabled": False,
                "base_dir": str(tmp_path / "traces"),
                "flush_every": 1,
            }
        ),
        encoding="utf-8",
    )

    rt = runner._load_runtime_config(str(runtime_cfg))
    models = runner._load_model_configs(str(model_cfg))
    tr = runner._load_trace_config(str(trace_cfg))

    assert rt.seed == 7
    assert rt.max_steps == 3
    assert models["planner"].provider == "heuristic"
    assert tr.base_dir.endswith("traces")


def test_run_episode_trace_override_writes_trace(tmp_path: Path, monkeypatch) -> None:
    base_cfg = tmp_path / "base.yaml"
    base_cfg.write_text(
        yaml.safe_dump(
            {
                "seed": 1,
                "max_steps": 2,
                "dynamic_replanning": False,
                "use_cot": False,
                "save_artifacts": False,
                "artifact_dir": str(tmp_path / "artifacts"),
            }
        ),
        encoding="utf-8",
    )
    model_cfg = tmp_path / "models.yaml"
    model_cfg.write_text(
        yaml.safe_dump(
            {
                "planner": {"provider": "heuristic"},
                "executor": {"provider": "heuristic"},
                "replanner": {"provider": "heuristic"},
            }
        ),
        encoding="utf-8",
    )
    trace_cfg = tmp_path / "trace.yaml"
    trace_dir = tmp_path / "traces"
    trace_cfg.write_text(
        yaml.safe_dump({"enabled": False, "base_dir": str(trace_dir), "flush_every": 1}),
        encoding="utf-8",
    )

    project_root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(project_root)
    monkeypatch.setattr(runner, "load_dotenv", lambda: None)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    runner.run_episode(
        goal="Test trace override",
        base_config=str(base_cfg),
        model_config=str(model_cfg),
        trace_config=str(trace_cfg),
        trace=True,
        environment="simulator",
        dynamic_replanning=False,
        use_cot=False,
    )

    run_dirs = [p for p in trace_dir.iterdir() if p.is_dir()]
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]
    session = json.loads((run_dir / "session.json").read_text(encoding="utf-8"))
    events = [json.loads(line) for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines() if line]

    assert session["status"] == "completed"
    assert session["summary"]["event_count"] == len(events)
    assert any(event["event_type"] == "episode_end" for event in events)


def test_demo_tools_uses_registry_outputs(monkeypatch) -> None:
    class FakeRegistry:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict[str, Any]]] = []

        def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
            self.calls.append((name, arguments))
            return {"ok": True, "name": name, "arguments": arguments}

    fake_registry = FakeRegistry()
    printed: list[Any] = []

    monkeypatch.setattr(runner, "build_default_tool_registry", lambda: fake_registry)
    monkeypatch.setattr(runner, "print", lambda payload: printed.append(payload))

    runner.demo_tools(query="q", url="https://example.com", expression="2+2")

    called_tools = [name for name, _ in fake_registry.calls]
    assert called_tools == ["web_search", "fetch_url", "calculator"]
    assert printed, "Expected demo_tools to print output payload"
