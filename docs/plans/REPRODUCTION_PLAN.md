# Reproduction Plan - Plan-and-Act (arXiv:2503.09572v3)

Navigation:
- Reading hub: [`../READING_GUIDE.md`](../READING_GUIDE.md)
- Project README: [`../../README.md`](../../README.md)
- Paper review: [`../analysis/PLAN_AND_ACT_REVIEW.md`](../analysis/PLAN_AND_ACT_REVIEW.md)
- Notebook demo: [`../../notebooks/01_plan_and_act_real_tool_demo.ipynb`](../../notebooks/01_plan_and_act_real_tool_demo.ipynb)

## 1. Reproduction Objectives

This plan defines three reproducibility targets with increasing rigor.

### Level A - Functional Reproduction

Goal:
1. Deliver a complete `Planner -> Executor -> Replanner` runtime.
2. Run end-to-end episodes with deterministic control flow and typed I/O contracts.

Success criteria:
1. Repeatable episode execution with stable stop conditions.
2. Trace logs and artifacts generated for each run.

### Level B - Method Reproduction

Goal:
Recreate the key method blocks from the paper:
1. Synthetic trajectory generation.
2. Grounded plan generation.
3. Plan expansion.
4. Targeted augmentation.
5. Dynamic replanning.
6. CoT-aware variants.

Success criteria:
1. All method blocks exist as executable modules or scripts.
2. Each block has explicit inputs, outputs, and validation checks.

### Level C - Performance Reproduction (Trend-Oriented)

Goal:
Reproduce the **ablation trend shape** from the paper.

Important constraint:
Absolute parity with reported SOTA numbers is not guaranteed due to differences in model stack, teacher pipelines, and benchmark environment drift.

Success criteria:
1. Directional gains are consistent with method additions.
2. Evaluation artifacts are complete and auditable.

## 2. Framework Decision

Selected framework: **LangGraph** (with LangChain ecosystem support).

Rationale:
1. Explicit graph semantics for long-horizon orchestration.
2. Deterministic transition control and stop-condition management.
3. Strong fit for modular multi-role agent design.
4. Clear state machine mental model for AI researchers and agent architects.

Design policy:
Even when reproducing a web-agent paper, implementation should remain **domain-agnostic**. Browser/web is one adapter, not the entire architecture.

## 3. Technical Stack

### 3.1 Model layer

Primary target model in this workspace:
1. `gpt-4` via `OPENAI_API_KEY`

Operational rules:
1. No hard-coded credentials.
2. Credentials loaded from environment only.
3. Prompt/model selection from config, not source edits.

### 3.2 Core libraries

1. `python>=3.11`
2. `langgraph`, `langchain`, `openai`, `pydantic`, `typer`
3. `pyyaml`, `orjson`, `python-dotenv`, `tenacity`, `rich`
4. Optional benchmark/runtime tooling as needed (`playwright`, data science stack)

### 3.3 Experiment tracking

Recommended:
1. Use one primary tracker (`mlflow` or `wandb`).
2. Persist config hash, model versions, prompt versions, seed, and metric snapshots.

## 4. Repository Design Standards

This repository should remain readable for AI researchers, data scientists, and agent architects.

Mandatory standards:
1. Schema-first boundaries with strict typing.
2. Config-driven runtime behavior.
3. Side-effect isolation between runtime, data generation, and training export.
4. Clear module ownership (`agents`, `graph`, `environments`, `tools`, `tracing`, `training`).
5. Tests for parser behavior, state transitions, and stop conditions.

## 5. Current and Target Structure

```text
plan_and_act_repro/
  README.md
  pyproject.toml
  configs/
    base.yaml
    models.yaml
    tracing.yaml
    prompts/
      planner.yaml
      executor.yaml
      replanner.yaml
      cot.yaml
  src/plan_and_act/
    core/
    agents/
    graph/
    environments/
    tools/
    tracing/
    data/
    training/
    eval/
    prompts/
    utils/
  scripts/
  data/
  artifacts/
  notebooks/
  tests/
  docs/
```

## 6. Implementation Roadmap

### Phase 1 - Runtime Baseline (3-4 days)

Scope:
1. Bootstrap project skeleton and configuration layer.
2. Implement minimal LangGraph workflow.
3. Define Pydantic schemas for plan/action/state.
4. Add simulator environment for deterministic smoke tests.

Deliverables:
1. End-to-end baseline run command.
2. Initial test suite for schema and transition sanity.

Exit criteria:
1. One-command run succeeds deterministically.
2. Stop conditions are enforced and tested.

### Phase 2 - Static Plan-and-Act (4-6 days)

Scope:
1. Planner emits structured multi-step plans.
2. Executor consumes current plan step and emits one action.
3. Add basic evaluation harness and run reporting.

Deliverables:
1. Baseline report comparing no-planner vs static planner.
2. Trace visibility for planner/executor I/O.

Exit criteria:
1. Static-plan episodes are reproducible.
2. Output schemas are stable under test.

### Phase 3 - Data-Centric Pipeline (7-10 days)

Scope:
1. Synthetic trajectory generation.
2. Grounded plan extraction with plan-step/action-span mapping.
3. Synthetic plan expansion.
4. Targeted augmentation from failure taxonomy.

Deliverables:
1. Versioned synthetic datasets.
2. Data cards and quality-gate summaries.

Exit criteria:
1. Datasets pass structural and logical consistency checks.
2. Provenance is traceable from generated sample to source seed.

### Phase 4 - Dynamic Replanning and CoT (5-7 days)

Scope:
1. Replanning loop integration and trigger policy.
2. CoT-aware prompt/data variants.
3. Full ablation suite matching paper methodology.

Deliverables:
1. Ablation table and trend plots.
2. Cost/latency/performance analysis.

Exit criteria:
1. Trend gains align with method increments.
2. Runtime remains bounded with explicit guardrails.

### Phase 5 - Packaging and Reproducibility Audit (2-3 days)

Scope:
1. Final report and reproducibility checklist.
2. Scripted one-command workflows for key experiments.
3. Artifact manifest and integrity checks.

Deliverables:
1. `artifacts/reports/final_reproduction_report.md`
2. Reproducible command matrix for baseline + ablations.

Exit criteria:
1. Another researcher can reproduce key experiments from docs and scripts.

## 7. Prompt and Schema Contracts

### Planner output contract

```json
{
  "goal": "string",
  "steps": [
    {
      "step_id": 1,
      "intent": "string",
      "success_criteria": "string"
    }
  ]
}
```

### Executor output contract

```json
{
  "action_type": "click|type|search|exit",
  "target": "string",
  "arguments": {},
  "rationale": "string",
  "is_final": false,
  "final_answer": "string"
}
```

### Replanner input contract

Should include:
1. Original goal.
2. Previous plan.
3. Action history.
4. Latest observation.
5. Optional failure hint/reason.

## 8. Evaluation and Metrics

Primary metric:
1. Task success rate.

Secondary metrics:
1. Plan validity rate.
2. Action grounding quality.
3. Replanning efficiency:
- replans per episode
- token usage
- latency
4. Failure taxonomy distribution:
- planning error
- grounding error
- observation misinterpretation
- loop/stuck behavior

## 9. Risk Register and Mitigations

1. API cost escalation.
- Mitigation: strict budgets, caching where valid, smaller pilot runs first.

2. Benchmark instability.
- Mitigation: fixed seeds, config snapshots, run manifests.

3. Synthetic data drift.
- Mitigation: quality gates, deduplication, contradiction checks.

4. Prompt overfitting.
- Mitigation: fixed held-out validation tasks and website splits.

5. Hidden runtime loops.
- Mitigation: explicit max-step stop conditions and tested transition logic.

## 10. Coding and Research Standards

1. Type hints and schema validation at boundaries.
2. No hidden business logic in notebooks.
3. Config-first runtime and prompt management.
4. Small, testable modules with explicit ownership.
5. Every major change has a focused ablation or targeted test.

## 11. Experiment Governance

1. Every run must have a unique `run_id`.
2. Record commit hash and config hash.
3. Store model and prompt versions.
4. Keep command reproducibility for every table/plot.
5. Draw conclusions only from logged and auditable artifacts.

## 12. Security and Secret Hygiene

1. Never commit API keys, `.env`, or secret-bearing notebook outputs.
2. Rotate exposed keys immediately.
3. Apply trace redaction for key-like patterns in prompts/responses.

## 13. Final Recommendation

For a clean and scalable reproduction of Plan-and-Act:
1. Use LangGraph orchestration with schema-first boundaries.
2. Prioritize planner-data quality before model-size escalation.
3. Treat tracing as a first-class data pipeline, not just runtime logging.
4. Evaluate by ablation trends and failure taxonomy, not only final headline scores.
