from plan_and_act.agents.executor import ExecutorAgent
from plan_and_act.agents.planner import PlannerAgent
from plan_and_act.agents.replanner import ReplannerAgent
from plan_and_act.core.state import build_initial_state
from plan_and_act.core.types import ModelConfig
from plan_and_act.graph.workflow import build_workflow
from plan_and_act.prompts.templates import PromptTemplates


def test_dynamic_replanning_executes_and_stops() -> None:
    prompts = PromptTemplates(config_dir="configs/prompts")
    planner = PlannerAgent(ModelConfig(provider="heuristic"), prompts)
    executor = ExecutorAgent(ModelConfig(provider="heuristic"), prompts)
    replanner = ReplannerAgent(ModelConfig(provider="heuristic"), prompts)

    workflow = build_workflow(planner, executor, replanner)
    initial = build_initial_state(
        goal="Follow top contributor",
        max_steps=6,
        dynamic_replanning=True,
        use_cot=False,
    )

    final_state = workflow.invoke(initial)

    assert final_state["step_count"] <= 6
    assert len(final_state["action_history"]) >= 1
    assert final_state["done"] is True
