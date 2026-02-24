# Agent Framework Architecture Guide

This document explains the implementation architecture in this repository, why each design choice was made, and how to reuse the same framework to reproduce other agent papers.

## 1. Design Goals

The framework is intentionally designed for **general-purpose agents**, not only browser/web agents.

Primary goals:
1. **Domain-agnostic runtime**: planning/execution loop does not hard-code browser assumptions.
2. **Composable components**: planner, executor, replanner, environment, tools are replaceable.
3. **Research-friendly experimentation**: config-driven runs, deterministic fallbacks, testable boundaries.
4. **Incremental reproducibility**: easy to start with baseline and add paper-specific modules phase-by-phase.
5. **Production-minded structure**: typed schemas, explicit contracts, controlled side effects.

## 2. High-Level Architecture

Core interaction loop:
1. Planner generates structured high-level steps.
2. Executor converts current step into a concrete action.
3. Environment executes that action and returns observation transition.
4. Replanner optionally updates plan based on new context.
5. Loop continues until success/failure/stop condition.

Conceptual boundaries:
- `Agent logic`: planner/executor/replanner decisions.
- `Environment logic`: how actions affect world state.
- `Tool logic`: concrete capabilities (search/fetch/calc/github/etc.).
- `Workflow logic`: orchestration and stop/replan transitions.

## 3. Source Structure and Responsibilities

### 3.1 Core contracts
- `src/plan_and_act/core/types.py`
- `src/plan_and_act/core/schemas.py`
- `src/plan_and_act/core/state.py`

Why:
- Keep all cross-module contracts centralized.
- Prevent hidden shape drift in plan/action/state objects.
- Make tests and refactors safer.

### 3.2 Agents
- `src/plan_and_act/agents/planner.py`
- `src/plan_and_act/agents/executor.py`
- `src/plan_and_act/agents/replanner.py`
- `src/plan_and_act/agents/judge.py`

Why:
- Isolate decision policies from environment implementation.
- Allow replacing one agent at a time (prompt-only, finetuned, rule-based, RL).

### 3.3 Workflow orchestration
- `src/plan_and_act/graph/workflow.py`
- `src/plan_and_act/graph/transitions.py`

Why:
- A graph-based orchestrator models long-horizon control flow clearly.
- Replanning is represented as explicit transition logic, not hidden conditionals spread across files.

### 3.4 Environments (domain adapters)
- `src/plan_and_act/environments/base.py`
- `src/plan_and_act/environments/simulator.py`
- `src/plan_and_act/environments/tooling.py`
- `src/plan_and_act/environments/factory.py`

Why:
- `EnvironmentAdapter` lets the same workflow run in different domains.
- Browser, API, desktop GUI, simulator, and tool-calling can share one control loop.

### 3.5 Tools (capabilities)
- `src/plan_and_act/tools/base.py`
- `src/plan_and_act/tools/factory.py`
- `src/plan_and_act/tools/web.py`
- `src/plan_and_act/tools/calc.py`
- `src/plan_and_act/tools/github.py`

Why:
- Tool implementations are independent modules with stable `run(arguments)` interface.
- Enables compositional capability growth without rewriting planner/executor code.

### 3.6 Evaluation and runtime entrypoints
- `src/plan_and_act/eval/runner.py`
- `src/plan_and_act/eval/metrics.py`
- `src/plan_and_act/eval/ablation.py`

Why:
- Single operational CLI for reproducible runs.
- Metrics decoupled from model/environment specifics.

### 3.7 Data and training pipelines
- `src/plan_and_act/data/*`
- `src/plan_and_act/training/*`

Why:
- Keep synthetic data and SFT preparation isolated from online runtime.
- Easier to reproduce paper data pipelines and run ablations.

## 4. Why This Is General-Purpose (Not Web-Locked)

The runtime is generalized by two interfaces:

1. `EnvironmentAdapter`
- `reset(goal) -> observation`
- `step(action, step_count) -> EnvironmentStepResult`

2. `Tool`
- `run(arguments) -> dict`

Because workflow depends on interfaces, not concrete domains:
- Browser domain: environment can call Playwright or WebArena adapter.
- API domain: environment can call API tools.
- Data analysis domain: environment can execute python/sql tools.
- RPA domain: environment can call desktop automation tools.

## 5. Real Tools Without Model API Key

Included no-key tools:
1. `web_search` via DuckDuckGo HTML endpoint
2. `fetch_url` via direct URL fetch + content extraction
3. `calculator` via safe AST evaluator

Run real tool demo:
```bash
plan-act-run demo-tools \
  --query "plan and act llm agents" \
  --url "https://arxiv.org/abs/2503.09572v3" \
  --expression "(42 * 13) / 7 + sqrt(81)"
```

This command does not require model API key because it directly runs tools.

## 6. Why The Stop Conditions Look Strict

In long-horizon agent graphs, a common failure mode is silent infinite loops.

Implemented guardrails:
1. Global max step budget
2. Explicit plan-exhaustion stop when replanning is disabled
3. Exit-action completion

These constraints make experiments auditable and prevent hidden runaway costs.

## 7. How to Reproduce Other Papers with This Framework

Use this migration template:

1. Keep `core/` contracts stable.
2. Replace or extend `agents/` according to paper method.
3. Add domain-specific `environment` adapter.
4. Add required tools in `tools/`.
5. Implement paper data generation in `data/`.
6. Implement training pipeline changes in `training/`.
7. Add ablation stages in `eval/ablation.py`.
8. Add focused tests for every new boundary.

## 8. Minimal Implementation Checklist for a New Paper

1. Define task success metrics first.
2. Define agent I/O schemas before writing prompts.
3. Implement environment adapter with deterministic smoke mode.
4. Add at least one real tool integration.
5. Add stop-condition tests and schema tests.
6. Add one end-to-end run command for reproducibility.
7. Add one ablation command/script for trend verification.

## 9. Framework Design Principles (Reusable)

1. **Schema-first**
- Every boundary is typed and validated.

2. **Config-first**
- Prompts, model choices, and runtime settings are externalized.

3. **Adapter-first**
- Environment and tools are pluggable interfaces.

4. **Graph-first orchestration**
- Complex execution paths are explicit and inspectable.

5. **Test-first on boundaries**
- Validate contracts, stop logic, and parser behavior early.

## 10. Practical Anti-Patterns to Avoid

1. Coupling tool calls directly inside planner/executor internals.
2. Embedding domain-specific assumptions in core state schema.
3. Hiding stop conditions inside prompt text instead of runtime logic.
4. Mixing data generation/training code with online serving path.
5. Relying on notebooks as the only executable artifact.

## 11. How to Think About "Agent Framework Quality"

A good framework is not just high benchmark score. It should also be:
1. **Composable**: easy to swap components.
2. **Inspectable**: clear traces and state transitions.
3. **Reproducible**: deterministic baseline path + config snapshots.
4. **Extensible**: new tools/environments do not require architecture rewrites.
5. **Fail-safe**: bounded loops, explicit error notes, predictable exits.

## 12. Recommended Next Steps in This Repo

1. Add browser adapter (`WebArenaEnvironmentAdapter` or Playwright adapter).
2. Add tool-selection policy (instead of default mapping) for richer domains.
3. Add trace viewer for run artifacts.
4. Add dataset versioning metadata for synthetic pipeline outputs.
5. Add benchmark harness wrappers for standardized result tables.

## 13. Cross Links

- Reading guide: [`READING_GUIDE.md`](../READING_GUIDE.md)
- Reproduction plan: [`REPRODUCTION_PLAN.md`](../plans/REPRODUCTION_PLAN.md)
- Technical review: [`PLAN_AND_ACT_REVIEW.md`](../analysis/PLAN_AND_ACT_REVIEW.md)
- Project README: [`README.md`](../../README.md)
- Notebook demo: [`notebooks/01_plan_and_act_real_tool_demo.ipynb`](../../notebooks/01_plan_and_act_real_tool_demo.ipynb)
