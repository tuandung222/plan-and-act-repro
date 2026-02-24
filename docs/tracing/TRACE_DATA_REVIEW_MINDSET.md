# Trace Data Review Mindset (LLM Scientist Perspective)

This guide explains how to review tracing code when the end goal is training data quality, not only runtime debugging.

Navigation:
- Trace implementation plan: [`TRAINING_DATA_TRACING_PLAN.md`](../plans/TRAINING_DATA_TRACING_PLAN.md)
- Tracing deep dive: [`PLANNING_ORCHESTRATION_DEEP_DIVE.md`](../architecture/PLANNING_ORCHESTRATION_DEEP_DIVE.md)
- Practical checklist: [`TRACE_DATA_REVIEW_CHECKLIST.md`](TRACE_DATA_REVIEW_CHECKLIST.md)
- Worked walkthrough: [`TRACE_TO_SFT_CODE_REVIEW_WALKTHROUGH.md`](TRACE_TO_SFT_CODE_REVIEW_WALKTHROUGH.md)

## 1) Core mindset

Treat tracing as a **data product pipeline**, not a logging utility.

For each trace field, ask:
1. Will this field help train or evaluate a model later?
2. Can this field be trusted and reproduced?
3. Can we trace this field back to source decisions?

If answer is "no", the field is noise.

## 2) Mental model: contracts across boundaries

Use this contract chain:

1. Prompt contract
- Inputs to planner/executor/replanner prompts must be explicit and versioned.

2. Model-output contract
- LLM returns text.
- `LLMClient` must parse robustly and surface parse failures.
- Code: [`src/plan_and_act/utils/llm.py`](../../src/plan_and_act/utils/llm.py)

3. Schema contract
- Parsed payload must pass strict Pydantic validation.
- Code: [`src/plan_and_act/core/schemas.py`](../../src/plan_and_act/core/schemas.py)

4. State-transition contract
- Valid outputs must produce deterministic state transitions.
- Code: [`src/plan_and_act/graph/workflow.py`](../../src/plan_and_act/graph/workflow.py)

5. Trace-event contract
- Important decisions must be represented as structured events.
- Code: [`src/plan_and_act/tracing/collector.py`](../../src/plan_and_act/tracing/collector.py)
- Event/session schema: [`src/plan_and_act/tracing/schemas.py`](../../src/plan_and_act/tracing/schemas.py)

6. Dataset contract
- Raw traces must convert into SFT-ready records with schema checks.
- Code: [`src/plan_and_act/training/build_sft_data.py`](../../src/plan_and_act/training/build_sft_data.py)
- Checks: [`src/plan_and_act/training/dataset_checks.py`](../../src/plan_and_act/training/dataset_checks.py)

## 3) Review strategy I use in practice

### Pass 1: Architecture and control flow

Goal: identify where truth is created.

Read in this order:
1. [`src/plan_and_act/eval/runner.py`](../../src/plan_and_act/eval/runner.py)
2. [`src/plan_and_act/graph/workflow.py`](../../src/plan_and_act/graph/workflow.py)
3. [`src/plan_and_act/tracing/collector.py`](../../src/plan_and_act/tracing/collector.py)

Expected outcome:
- You know exactly where each trace event is emitted and why.

### Pass 2: Data contract strictness

Goal: detect silent corruption paths.

Check:
1. Is parse failure explicit or silently ignored?
2. Does schema reject invalid structure early?
3. Are event fields typed enough for downstream usage?

### Pass 3: Training usefulness

Goal: verify traces are sufficient to train planner/executor/replanner.

Check:
1. Planner samples: prompt context + plan output are captured.
2. Executor samples: current step + observation + action are captured.
3. Replanner samples: previous plan + history + new plan are captured.
4. Failure samples: explicit error reason exists.

### Pass 4: Reproducibility and lineage

Goal: support audit and future experiments.

Check:
1. Each run has stable `run_id`.
2. Session contains model stack and runtime config.
3. Event sequence can reconstruct episode timeline.
4. Data export keeps pointers to source trace/run.

### Pass 5: Risk and leakage

Goal: prevent invalid training conclusions.

Check:
1. Train/test leakage via shared source traces.
2. Missing provenance in transformed datasets.
3. Selective logging bias (only successful episodes logged).
4. Prompt/response truncation bias in logs.

## 4) What "good" looks like

A good tracing system for training has:
1. Deterministic schemas.
2. Event completeness for every critical boundary.
3. Explicit errors and stop reasons.
4. Provenance from SFT row back to raw run.
5. Quality gates in CI for dataset integrity.

## 5) Common anti-patterns

1. "Just log everything" mindset.
- Creates large, low-signal traces.

2. Stringly-typed events without schema.
- Breaks downstream builders silently.

3. No parse-failure accounting.
- You lose error distribution visibility.

4. Logging only final answer.
- Useless for planner/executor fine-tuning.

5. No split/lineage metadata.
- High leakage risk.

## 6) How to transfer this mindset to other projects

Use this reusable template:

1. Define role outputs as strict schemas.
2. Instrument boundary events, not internal noise.
3. Require conversion pipeline: raw trace -> normalized records -> trainable rows.
4. Add dataset checks before any training run.
5. Add audit scripts to trace any row back to source run.

This works for browser agents, API agents, desktop agents, and data-pipeline agents.

## 7) Repo-specific current status

Strengths:
1. Runtime tracing infra exists and is integrated in graph nodes.
2. Session/event schemas are structured.
3. Notebook trace monitoring exists.

Current gaps to prioritize:
1. Lineage metadata from SFT row back to run/event is still thin.
2. Dataset checks are minimal (currently only key presence).
3. Tool-call-specific events can be richer for training diagnostics.

