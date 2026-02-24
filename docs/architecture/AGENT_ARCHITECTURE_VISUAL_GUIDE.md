# Agent Architecture Visual Guide

This document explains the **current** architecture of this repository with diagrams that render in GitHub and most IDE Markdown previews.

Navigation:
- Overview guide: [`AGENT_FRAMEWORK_ARCHITECTURE.md`](AGENT_FRAMEWORK_ARCHITECTURE.md)
- Planning/orchestration deep dive: [`PLANNING_ORCHESTRATION_DEEP_DIVE.md`](PLANNING_ORCHESTRATION_DEEP_DIVE.md)
- Trace plan for training data: [`TRAINING_DATA_TRACING_PLAN.md`](../plans/TRAINING_DATA_TRACING_PLAN.md)

## 1) One-page architecture summary

The system is a Plan-and-Act agent with explicit modules:
1. `Planner` produces multi-step plans.
2. `Executor` converts one step into one action.
3. `Environment` executes actions (simulator/tool domain).
4. `Replanner` updates plan from latest observations.
5. `LangGraph` orchestrates transitions.
6. `TraceCollector` records session + event timeline for analysis and training-data pipelines.

Core code:
- Workflow graph: [`src/plan_and_act/graph/workflow.py`](../../src/plan_and_act/graph/workflow.py)
- Runner entrypoint: [`src/plan_and_act/eval/runner.py`](../../src/plan_and_act/eval/runner.py)
- Agent modules: [`src/plan_and_act/agents/`](../../src/plan_and_act/agents/)
- Environment adapters: [`src/plan_and_act/environments/`](../../src/plan_and_act/environments/)
- Tracing infra: [`src/plan_and_act/tracing/`](../../src/plan_and_act/tracing/)

## 2) Layered architecture (logical view)

```mermaid
flowchart TB
    subgraph UX["CLI / Notebook Layer"]
        CLI["plan-act-run CLI"]
        NB["Jupyter notebooks"]
    end

    subgraph ORCH["Orchestration Layer"]
        WF["LangGraph workflow"]
        TRANS["Transition policy"]
        STATE["PlanActState"]
    end

    subgraph AGENTS["Agent Decision Layer"]
        PLAN["PlannerAgent"]
        EXEC["ExecutorAgent"]
        REPLAN["ReplannerAgent"]
        LLM["LLMClient + schema parsing"]
    end

    subgraph ENV["Environment Layer"]
        SIM["GenericSimulatorEnvironment"]
        TOOLENV["ToolCallingEnvironment"]
    end

    subgraph TOOLS["Tool Capability Layer"]
        WEB["WebSearchTool / FetchURLTool"]
        CALC["CalculatorTool"]
        GH["GitHubTopContributorTool"]
    end

    subgraph TRACE["Tracing Layer"]
        COL["TraceCollector"]
        WRITER["TraceWriter"]
        ART["session.json + events.jsonl"]
    end

    CLI --> WF
    NB --> WF
    WF --> PLAN
    WF --> EXEC
    WF --> REPLAN
    PLAN --> LLM
    EXEC --> LLM
    REPLAN --> LLM
    WF --> SIM
    WF --> TOOLENV
    TOOLENV --> WEB
    TOOLENV --> CALC
    TOOLENV --> GH
    WF --> COL
    TOOLENV --> COL
    PLAN --> COL
    EXEC --> COL
    REPLAN --> COL
    COL --> WRITER --> ART
```

## 3) Runtime control flow (state-machine view)

```mermaid
flowchart LR
    START["START"] --> P["planner_node"]
    P --> E["executor_node"]
    E -->|done| END["END"]
    E -->|needs_replan and dynamic_replanning| R["replanner_node"]
    E -->|continue| E
    R --> E
```

Where implemented:
- Graph wiring: [`src/plan_and_act/graph/workflow.py`](../../src/plan_and_act/graph/workflow.py)
- Route policy: [`src/plan_and_act/graph/transitions.py`](../../src/plan_and_act/graph/transitions.py)

## 4) Sequence diagram (single run)

```mermaid
sequenceDiagram
    participant User
    participant Runner as "eval.runner"
    participant Graph as "LangGraph workflow"
    participant Planner
    participant Executor
    participant Replanner
    participant Env as "EnvironmentAdapter"
    participant Tools as "ToolRegistry"
    participant Tracer as "TraceCollector"

    User->>Runner: run-episode(goal, config)
    Runner->>Tracer: start_session(...)
    Runner->>Graph: invoke(initial_state)

    Graph->>Tracer: planner_input
    Graph->>Planner: plan(goal, observation, action_history)
    Planner->>Tracer: llm_call(component=planner)
    Planner-->>Graph: PlannerOutput(steps)
    Graph->>Tracer: planner_output

    loop Until done or max_steps
        Graph->>Tracer: executor_input
        Graph->>Executor: act(current_step, observation)
        Executor->>Tracer: llm_call(component=executor)
        Executor-->>Graph: ExecutorAction
        Graph->>Tracer: executor_output

        Graph->>Env: step(action, step_count)
        opt Tool environment
            Env->>Tracer: tool_call_start
            Env->>Tools: call(tool_name, arguments)
            Tools-->>Env: tool_result
            Env->>Tracer: tool_call_end
        end
        Env-->>Graph: EnvironmentStepResult
        Graph->>Tracer: environment_step

        alt needs_replan
            Graph->>Tracer: replanner_input
            Graph->>Replanner: replan(previous_plan, action_history, observation)
            Replanner->>Tracer: llm_call(component=replanner)
            Replanner-->>Graph: PlannerOutput(new_steps)
            Graph->>Tracer: replanner_output
        else done
            Graph->>Tracer: episode_end
        end
    end

    Runner->>Tracer: close(status, summary)
```

## 5) Data contracts between modules

```mermaid
flowchart TB
    GOAL["Goal + Observation"] --> POUT["PlannerOutput"]
    POUT --> PSTATE["state.plan[]"]
    PSTATE --> EIN["Executor input current_step"]
    EIN --> EOUT["ExecutorAction"]
    EOUT --> ENVOUT["EnvironmentStepResult"]
    ENVOUT --> OBS["New observation"]
    OBS --> RIN["Replanner input"]
    RIN --> ROUT["PlannerOutput updated"]
    ROUT --> PSTATE
```

Schemas:
- Planner/Action models: [`src/plan_and_act/core/schemas.py`](../../src/plan_and_act/core/schemas.py)
- Runtime state: [`src/plan_and_act/core/state.py`](../../src/plan_and_act/core/state.py)
- Type constraints: [`src/plan_and_act/core/types.py`](../../src/plan_and_act/core/types.py)

## 6) Tracing architecture and storage

```mermaid
flowchart TB
    subgraph EMIT["Event Emitters"]
        N1["planner_node / executor_node / replanner_node"]
        N2["LLMClient trace hooks"]
        N3["ToolCallingEnvironment"]
        N4["Runner lifecycle"]
    end

    subgraph TRACE["Tracing Core"]
        C["TraceCollector"]
        S["TraceSession model"]
        E["TraceEvent model"]
        W["TraceWriter"]
    end

    subgraph FILES["Artifacts"]
        F1["data/raw/traces/<run_id>/session.json"]
        F2["data/raw/traces/<run_id>/events.jsonl"]
    end

    N1 --> C
    N2 --> C
    N3 --> C
    N4 --> C
    C --> S
    C --> E
    C --> W
    W --> F1
    W --> F2
```

Tracing code:
- Collector: [`src/plan_and_act/tracing/collector.py`](../../src/plan_and_act/tracing/collector.py)
- Schemas: [`src/plan_and_act/tracing/schemas.py`](../../src/plan_and_act/tracing/schemas.py)
- Writer: [`src/plan_and_act/tracing/writer.py`](../../src/plan_and_act/tracing/writer.py)

## 7) What architecture style is this?

Current style:
1. **Plan-and-Act orchestration** at graph level.
2. **ReAct-like action generation** at executor level (structured action from observation).
3. **Code-controlled runtime policy** for transitions, stop conditions, and replanning.
4. **Not CodeAct** (no generate-code-then-execute loop).

## 8) Strengths of current architecture

1. Strong modular boundaries: planner/executor/replanner/environment/tools are replaceable.
2. Explicit control flow: transitions are inspectable and testable.
3. Good observability baseline: trace session + event timeline + LLM call traces.
4. Domain-agnostic runtime: browser is only one possible adapter, not mandatory.

## 9) Current bottlenecks and extension points

Bottlenecks:
1. Planner is not fully tool-aware by explicit tool manifest in prompt.
2. Trace-to-SFT conversion is still minimal in current builders.
3. Dataset quality gates are still lightweight compared to production training standards.

Extension points:
1. Add tool-aware planning prompt templates.
2. Add richer role-specific SFT exporters with lineage.
3. Add stricter dataset validators and leakage checks.
4. Add browser adapter without changing graph orchestration core.

## 10) Practical file map

1. Orchestration:
- [`src/plan_and_act/graph/workflow.py`](../../src/plan_and_act/graph/workflow.py)
- [`src/plan_and_act/graph/transitions.py`](../../src/plan_and_act/graph/transitions.py)

2. Agents:
- [`src/plan_and_act/agents/planner.py`](../../src/plan_and_act/agents/planner.py)
- [`src/plan_and_act/agents/executor.py`](../../src/plan_and_act/agents/executor.py)
- [`src/plan_and_act/agents/replanner.py`](../../src/plan_and_act/agents/replanner.py)

3. Environment + tools:
- [`src/plan_and_act/environments/tooling.py`](../../src/plan_and_act/environments/tooling.py)
- [`src/plan_and_act/tools/factory.py`](../../src/plan_and_act/tools/factory.py)
- [`src/plan_and_act/tools/web.py`](../../src/plan_and_act/tools/web.py)
- [`src/plan_and_act/tools/calc.py`](../../src/plan_and_act/tools/calc.py)
- [`src/plan_and_act/tools/github.py`](../../src/plan_and_act/tools/github.py)

4. Tracing:
- [`src/plan_and_act/tracing/collector.py`](../../src/plan_and_act/tracing/collector.py)
- [`src/plan_and_act/tracing/schemas.py`](../../src/plan_and_act/tracing/schemas.py)
- [`src/plan_and_act/tracing/writer.py`](../../src/plan_and_act/tracing/writer.py)

## 11) Rendering tips (IDE and browser)

1. GitHub renders Mermaid blocks natively.
2. In IDE, use Markdown preview with Mermaid enabled.
3. If Mermaid is disabled in IDE preview, open the file in GitHub for final visual rendering.

