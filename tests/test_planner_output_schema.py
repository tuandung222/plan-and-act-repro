from plan_and_act.agents.planner import PlannerAgent
from plan_and_act.core.types import ModelConfig
from plan_and_act.prompts.templates import PromptTemplates


def test_planner_output_schema() -> None:
    prompts = PromptTemplates(config_dir="configs/prompts")
    agent = PlannerAgent(ModelConfig(provider="heuristic"), prompts)
    out = agent.plan(
        goal="Book a flight to NYC",
        observation="home page",
        action_history=[],
        use_cot=False,
    )
    assert out.goal
    assert len(out.steps) >= 1
    assert out.steps[0].step_id >= 1
