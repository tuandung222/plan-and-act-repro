from plan_and_act.agents.executor import ExecutorAgent
from plan_and_act.core.schemas import PlanStep
from plan_and_act.core.types import ModelConfig
from plan_and_act.prompts.templates import PromptTemplates


def test_executor_action_schema() -> None:
    prompts = PromptTemplates(config_dir="configs/prompts")
    agent = ExecutorAgent(ModelConfig(provider="heuristic"), prompts)
    action = agent.act(
        goal="Find postal code",
        current_step=PlanStep(step_id=1, intent="Search the location", success_criteria="result visible"),
        observation="home",
        step_index=0,
        total_steps=2,
        use_cot=False,
    )
    assert action.action_type in {"click", "type", "search", "exit"}
