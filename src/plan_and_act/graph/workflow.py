from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from plan_and_act.agents.executor import ExecutorAgent
from plan_and_act.agents.planner import PlannerAgent
from plan_and_act.agents.replanner import ReplannerAgent
from plan_and_act.core.schemas import PlanStep
from plan_and_act.core.state import PlanActState
from plan_and_act.environments.base import EnvironmentAdapter
from plan_and_act.environments.simulator import GenericSimulatorEnvironment
from plan_and_act.graph.transitions import route_after_executor
from plan_and_act.tracing.collector import TraceCollector


def planner_node(
    state: PlanActState,
    planner: PlannerAgent,
    tracer: TraceCollector | None = None,
) -> dict[str, Any]:
    if tracer:
        tracer.log_event(
            event_type="planner_input",
            step=state["step_count"],
            payload={
                "goal": state["goal"],
                "observation": state["observation"],
                "action_history": state["action_history"],
            },
        )
    output = planner.plan(
        goal=state["goal"],
        observation=state["observation"],
        action_history=state["action_history"],
        use_cot=state["use_cot"],
        step=state["step_count"],
    )
    if tracer:
        tracer.log_event(
            event_type="planner_output",
            step=state["step_count"],
            payload={"steps": [step.model_dump() for step in output.steps]},
        )
    return {
        "plan": [step.model_dump() for step in output.steps],
        "current_step_idx": 0,
        "needs_replan": False,
    }


def executor_node(
    state: PlanActState,
    executor: ExecutorAgent,
    environment: EnvironmentAdapter,
    tracer: TraceCollector | None = None,
) -> dict[str, Any]:
    if state["done"]:
        return {}

    step_count = state["step_count"]
    max_steps = state["max_steps"]
    current_idx = state["current_step_idx"]
    plan = state["plan"]

    if step_count >= max_steps:
        if tracer:
            tracer.log_event(
                event_type="episode_stop",
                step=step_count,
                payload={"reason": "max_steps_reached", "max_steps": max_steps},
            )
        return {
            "done": True,
            "success": False,
            "final_answer": "Stopped: max steps reached.",
            "notes": state["notes"] + ["Reached max step budget."],
        }

    if not plan or current_idx >= len(plan):
        if not state["dynamic_replanning"]:
            if tracer:
                tracer.log_event(
                    event_type="episode_stop",
                    step=step_count,
                    payload={"reason": "plan_exhausted_without_replanning"},
                )
            return {
                "done": True,
                "success": False,
                "final_answer": "Stopped: plan exhausted while dynamic replanning is disabled.",
                "notes": state["notes"] + ["Plan exhausted and replanning is disabled."],
            }
        if tracer:
            tracer.log_event(
                event_type="executor_needs_replan",
                step=step_count,
                payload={"reason": "plan_exhausted"},
            )
        return {
            "needs_replan": True,
            "notes": state["notes"] + ["No remaining plan steps; requesting replanning."],
        }

    current_step = PlanStep.model_validate(plan[current_idx])
    if tracer:
        tracer.log_event(
            event_type="executor_input",
            step=step_count,
            payload={
                "current_step_idx": current_idx,
                "current_step": current_step.model_dump(),
                "observation": state["observation"],
            },
        )
    action = executor.act(
        goal=state["goal"],
        current_step=current_step,
        observation=state["observation"],
        step_index=current_idx,
        total_steps=len(plan),
        use_cot=state["use_cot"],
        step=step_count,
    )

    new_step_count = step_count + 1
    new_action_history = state["action_history"] + [action.model_dump()]
    if tracer:
        tracer.log_event(
            event_type="executor_output",
            step=new_step_count,
            payload={"action": action.model_dump()},
        )
    env_result = environment.step(action=action, step_count=new_step_count)
    if tracer:
        tracer.log_event(
            event_type="environment_step",
            step=new_step_count,
            payload={
                "observation": env_result.observation,
                "done": env_result.done,
                "success": env_result.success,
                "final_answer": env_result.final_answer,
                "notes": env_result.notes,
            },
        )
    new_observation = env_result.observation

    done = bool(action.is_final or env_result.done)
    success = bool(action.is_final or env_result.success)
    final_answer = action.final_answer or env_result.final_answer or state["final_answer"]

    needs_replan = bool(state["dynamic_replanning"] and not done)
    notes = state["notes"] + env_result.notes

    return {
        "latest_action": action.model_dump(),
        "action_history": new_action_history,
        "observation": new_observation,
        "step_count": new_step_count,
        "current_step_idx": current_idx + 1,
        "done": done,
        "success": success,
        "final_answer": final_answer,
        "needs_replan": needs_replan,
        "notes": notes,
    }


def replanner_node(
    state: PlanActState,
    replanner: ReplannerAgent,
    tracer: TraceCollector | None = None,
) -> dict[str, Any]:
    if tracer:
        tracer.log_event(
            event_type="replanner_input",
            step=state["step_count"],
            payload={
                "previous_plan_length": len(state["plan"]),
                "previous_plan": state["plan"],
                "action_history": state["action_history"],
                "observation": state["observation"],
            },
        )
    output = replanner.replan(
        goal=state["goal"],
        previous_plan=state["plan"],
        action_history=state["action_history"],
        observation=state["observation"],
        use_cot=state["use_cot"],
        step=state["step_count"],
    )
    if tracer:
        tracer.log_event(
            event_type="replanner_output",
            step=state["step_count"],
            payload={"steps": [step.model_dump() for step in output.steps]},
        )
    return {
        "plan": [step.model_dump() for step in output.steps],
        "current_step_idx": 0,
        "needs_replan": False,
        "notes": state["notes"] + ["Replanned based on latest observation."],
    }


def build_workflow(
    planner: PlannerAgent,
    executor: ExecutorAgent,
    replanner: ReplannerAgent,
    environment: EnvironmentAdapter | None = None,
    tracer: TraceCollector | None = None,
):
    environment_adapter = environment or GenericSimulatorEnvironment()
    trace_collector = tracer
    graph = StateGraph(PlanActState)

    graph.add_node("planner", lambda s: planner_node(s, planner, trace_collector))
    graph.add_node("executor", lambda s: executor_node(s, executor, environment_adapter, trace_collector))
    graph.add_node("replanner", lambda s: replanner_node(s, replanner, trace_collector))

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "executor")

    graph.add_conditional_edges(
        "executor",
        route_after_executor,
        {
            "end": END,
            "replan": "replanner",
            "continue": "executor",
        },
    )
    graph.add_edge("replanner", "executor")

    return graph.compile()
