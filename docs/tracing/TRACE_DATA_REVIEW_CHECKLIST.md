# Trace Data Code Review Checklist

Use this checklist when reviewing tracing code for training-data readiness.

Navigation:
- Mindset guide: [`TRACE_DATA_REVIEW_MINDSET.md`](TRACE_DATA_REVIEW_MINDSET.md)
- Worked walkthrough: [`TRACE_TO_SFT_CODE_REVIEW_WALKTHROUGH.md`](TRACE_TO_SFT_CODE_REVIEW_WALKTHROUGH.md)

## P0 (must fix before training)

1. Parse failures are silent.
- Verify parse errors from model output are surfaced.
- Code: [`src/plan_and_act/utils/llm.py`](../../src/plan_and_act/utils/llm.py)

2. Schema validation missing at role boundary.
- Planner/executor/replanner outputs must pass typed validation.
- Code: [`src/plan_and_act/core/schemas.py`](../../src/plan_and_act/core/schemas.py)

3. Missing provenance keys in raw traces.
- `run_id`, `event_type`, `step`, timestamps required.
- Code: [`src/plan_and_act/tracing/schemas.py`](../../src/plan_and_act/tracing/schemas.py)

4. Train/test leakage not controlled.
- Confirm split strategy preserves source-level isolation.

5. Episode failure reasons not captured.
- Must log stop reason and model/runtime errors.
- Code: [`src/plan_and_act/eval/runner.py`](../../src/plan_and_act/eval/runner.py)

## P1 (high-value correctness)

1. Event coverage incomplete for one role.
- Ensure planner_input/output, executor_input/output, replanner_input/output are present.
- Code: [`src/plan_and_act/graph/workflow.py`](../../src/plan_and_act/graph/workflow.py)

2. Tool execution context too shallow.
- Include tool name, arguments shape, success/failure signal.
- Code: [`src/plan_and_act/environments/tooling.py`](../../src/plan_and_act/environments/tooling.py)

3. Session metadata missing experiment-critical fields.
- Model stack, runtime config, environment info should be persisted.
- Code: [`src/plan_and_act/tracing/collector.py`](../../src/plan_and_act/tracing/collector.py)

4. Dataset checks only verify key existence.
- Add logical consistency checks and duplicates checks.
- Code: [`src/plan_and_act/training/dataset_checks.py`](../../src/plan_and_act/training/dataset_checks.py)

## P2 (diagnostics and maintainability)

1. No schema/version tag for trace format.
2. Missing latency/token usage fields for error analysis.
3. Hard-to-replay event order.
4. No utility scripts for trace integrity checks.

## Quick review routine (30-60 minutes)

1. Run one traced episode.

```bash
./scripts/run_episode_with_trace.sh
```

2. Inspect latest trace folder.

```bash
ls -lt data/raw/traces | head
```

3. Validate `session.json` fields.
- `run_id`, `status`, `goal`, `model_stack`, `runtime_config`, `summary`.

4. Validate `events.jsonl` sequence.
- Must show a coherent planner -> executor -> environment -> replanner/end flow.

5. Sample-convert a few events into SFT rows and run checks.

```python
from plan_and_act.training.dataset_checks import validate_dataset

rows = [
    {"input": "planner prompt snapshot", "output": "{\"goal\": \"...\", \"steps\": []}"}
]
print(validate_dataset(rows))
```

6. File findings by severity (P0/P1/P2), with exact file paths and line anchors.

## Review-comment template

Use this template for each finding:

1. Problem
- What is incorrect or risky.

2. Why it matters for training
- How it can poison/shift the dataset.

3. Evidence
- File path and specific code location.

4. Fix direction
- Minimal patch recommendation.

Example:
- Problem: executor failures are not encoded as structured labels.
- Why: failure-conditioned training and augmentation cannot separate tool vs planner errors.
- Evidence: `src/plan_and_act/graph/workflow.py` logs notes but no explicit failure taxonomy field.
- Fix: add `failure_type` enum in event payload and downstream dataset mapping.

