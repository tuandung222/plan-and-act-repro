from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import typer
from dotenv import load_dotenv
from rich import print

from plan_and_act.agents.executor import ExecutorAgent
from plan_and_act.agents.planner import PlannerAgent
from plan_and_act.agents.replanner import ReplannerAgent
from plan_and_act.core.schemas import EpisodeArtifact
from plan_and_act.core.state import build_initial_state
from plan_and_act.core.types import ModelConfig, RuntimeConfig
from plan_and_act.environments.factory import build_environment
from plan_and_act.eval.metrics import compute_episode_metrics
from plan_and_act.graph.workflow import build_workflow
from plan_and_act.prompts.templates import PromptTemplates
from plan_and_act.tracing import TraceCollector, TraceConfig
from plan_and_act.tools.factory import build_default_tool_registry
from plan_and_act.utils.io import load_yaml, write_json
from plan_and_act.utils.seeding import set_seed

app = typer.Typer(no_args_is_help=True)


@app.callback()
def main() -> None:
    """Run Plan-and-Act experiments and evaluations."""


def _load_runtime_config(path: str) -> RuntimeConfig:
    return RuntimeConfig.model_validate(load_yaml(path))


def _load_model_configs(path: str) -> dict[str, ModelConfig]:
    data = load_yaml(path)
    return {
        "planner": ModelConfig.model_validate(data.get("planner", {})),
        "executor": ModelConfig.model_validate(data.get("executor", {})),
        "replanner": ModelConfig.model_validate(data.get("replanner", {})),
    }


def _load_trace_config(path: str) -> TraceConfig:
    return TraceConfig.model_validate(load_yaml(path))


@app.command("run-episode")
def run_episode(
    goal: str = typer.Option(..., help="User goal/instruction."),
    base_config: str = typer.Option("configs/base.yaml", help="Path to base runtime config."),
    model_config: str = typer.Option("configs/models.yaml", help="Path to model config."),
    trace_config: str = typer.Option("configs/tracing.yaml", help="Path to tracing config."),
    trace: bool = typer.Option(False, help="Enable runtime trace logging for this run."),
    environment: str = typer.Option("simulator", help="Environment adapter: simulator|tool"),
    dynamic_replanning: bool = typer.Option(True, help="Enable replanning after each action."),
    use_cot: bool = typer.Option(False, help="Enable CoT hints in prompts."),
) -> None:
    load_dotenv()
    runtime_cfg = _load_runtime_config(base_config)
    model_cfgs = _load_model_configs(model_config)
    trace_cfg = _load_trace_config(trace_config)
    if trace:
        trace_cfg.enabled = True

    runtime_cfg = runtime_cfg.model_copy(
        update={
            "dynamic_replanning": dynamic_replanning,
            "use_cot": use_cot,
        }
    )

    set_seed(runtime_cfg.seed)

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    tracer = TraceCollector(config=trace_cfg, run_id=run_id)
    env_adapter = build_environment(environment, tracer=tracer)

    prompts = PromptTemplates(config_dir="configs/prompts")
    planner = PlannerAgent(model_cfgs["planner"], prompts, tracer=tracer)
    executor = ExecutorAgent(model_cfgs["executor"], prompts, tracer=tracer)
    replanner = ReplannerAgent(model_cfgs["replanner"], prompts, tracer=tracer)
    tracer.start_session(
        goal=goal,
        environment={"kind": environment, "name": env_adapter.name},
        model_stack={
            "planner": model_cfgs["planner"].model_dump(),
            "executor": model_cfgs["executor"].model_dump(),
            "replanner": model_cfgs["replanner"].model_dump(),
        },
        runtime_config=runtime_cfg.model_dump(),
    )

    workflow = build_workflow(planner, executor, replanner, env_adapter, tracer)

    initial_state = build_initial_state(
        goal=goal,
        max_steps=runtime_cfg.max_steps,
        dynamic_replanning=runtime_cfg.dynamic_replanning,
        use_cot=runtime_cfg.use_cot,
        observation=env_adapter.reset(goal=goal),
    )

    try:
        final_state: dict[str, Any] = workflow.invoke(initial_state)
    except Exception as exc:
        tracer.log_event(
            event_type="episode_error",
            step=initial_state["step_count"],
            payload={"error_type": type(exc).__name__, "error_message": str(exc)},
        )
        tracer.close(
            status="failed",
            summary={"error_type": type(exc).__name__, "error_message": str(exc)},
        )
        raise

    metrics = compute_episode_metrics(final_state)
    tracer.log_event(
        event_type="episode_end",
        step=int(final_state.get("step_count", 0)),
        payload={
            "success": bool(final_state.get("success", False)),
            "final_answer": str(final_state.get("final_answer", "")),
            "metrics": metrics,
        },
    )
    tracer.close(
        status="completed",
        summary={
            "success": bool(final_state.get("success", False)),
            "step_count": int(final_state.get("step_count", 0)),
            "metrics": metrics,
        },
    )

    artifact = EpisodeArtifact(
        run_id=run_id,
        goal=goal,
        success=bool(final_state.get("success", False)),
        step_count=int(final_state.get("step_count", 0)),
        final_answer=str(final_state.get("final_answer", "")),
        action_history=list(final_state.get("action_history", [])),
        notes=list(final_state.get("notes", [])),
    )

    if runtime_cfg.save_artifacts:
        out_dir = Path(runtime_cfg.artifact_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        write_json(out_dir / f"episode_{run_id}.json", {
            "config": runtime_cfg.model_dump(),
            "model": {
                "planner": model_cfgs["planner"].model_dump(),
                "executor": model_cfgs["executor"].model_dump(),
                "replanner": model_cfgs["replanner"].model_dump(),
            },
            "environment": {
                "name": env_adapter.name,
                "kind": environment,
            },
            "metrics": metrics,
            "final_state": final_state,
            "artifact": artifact.model_dump(),
        })

    print("[bold green]Episode finished[/bold green]")
    print({
        "success": artifact.success,
        "step_count": artifact.step_count,
        "final_answer": artifact.final_answer,
        "metrics": metrics,
        "environment": env_adapter.name,
        "trace_enabled": trace_cfg.enabled,
        "trace_run_id": run_id if trace_cfg.enabled else "",
        "used_openai_key": bool(os.getenv("OPENAI_API_KEY", "").strip()),
    })


@app.command("demo-tools")
def demo_tools(
    query: str = typer.Option(
        "latest langgraph release notes",
        help="Web search query for the no-key web_search tool.",
    ),
    url: str = typer.Option(
        "https://docs.python.org/3/library/ast.html",
        help="URL for the no-key fetch_url tool.",
    ),
    expression: str = typer.Option(
        "sqrt(144) + 2**8 - 3",
        help="Expression for the no-key calculator tool.",
    ),
) -> None:
    registry = build_default_tool_registry()

    search_result = registry.call(
        "web_search",
        {
            "query": query,
            "max_results": 5,
        },
    )
    fetch_result = registry.call(
        "fetch_url",
        {
            "url": url,
            "max_chars": 500,
        },
    )
    calc_result = registry.call(
        "calculator",
        {
            "expression": expression,
        },
    )

    print("[bold green]Real tool demo finished (no model API key required)[/bold green]")
    print(
        {
            "search": search_result,
            "fetch": {
                "ok": fetch_result.get("ok"),
                "url": fetch_result.get("url"),
                "status": fetch_result.get("status"),
                "title": fetch_result.get("title"),
                "content_preview": fetch_result.get("content_preview"),
            },
            "calculator": calc_result,
        }
    )


def run_cli() -> None:
    app()


if __name__ == "__main__":
    run_cli()
