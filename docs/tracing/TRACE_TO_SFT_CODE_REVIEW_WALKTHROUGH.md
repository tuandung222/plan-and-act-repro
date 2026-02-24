# Trace-to-SFT Code Review Walkthrough

This is a practical, repo-specific walkthrough to review tracing code and infer training-data readiness.

Navigation:
- Mindset: [`TRACE_DATA_REVIEW_MINDSET.md`](TRACE_DATA_REVIEW_MINDSET.md)
- Checklist: [`TRACE_DATA_REVIEW_CHECKLIST.md`](TRACE_DATA_REVIEW_CHECKLIST.md)
- Trace plan: [`TRAINING_DATA_TRACING_PLAN.md`](../plans/TRAINING_DATA_TRACING_PLAN.md)

## 1) Build one real trace

Run:

```bash
./scripts/run_episode_with_trace.sh
```

This writes:
- `data/raw/traces/<run_id>/session.json`
- `data/raw/traces/<run_id>/events.jsonl`

## 2) Review session-level contract

Open `session.json` and verify:
1. `run_id` is unique and stable.
2. `status` updates from `running` -> terminal status.
3. `goal`, `environment`, `model_stack`, `runtime_config` are present.
4. `summary.event_count` matches events written.

Source code to verify behavior:
- Session start/close: [`src/plan_and_act/tracing/collector.py`](../../src/plan_and_act/tracing/collector.py)
- Session schema: [`src/plan_and_act/tracing/schemas.py`](../../src/plan_and_act/tracing/schemas.py)
- Writer: [`src/plan_and_act/tracing/writer.py`](../../src/plan_and_act/tracing/writer.py)

## 3) Review event sequence correctness

Expected event families:
1. `planner_input`
2. `planner_output`
3. `executor_input`
4. `executor_output`
5. `environment_step`
6. optional `replanner_input`/`replanner_output`
7. `episode_end` or `episode_error`

Where emitted:
- [`src/plan_and_act/graph/workflow.py`](../../src/plan_and_act/graph/workflow.py)
- [`src/plan_and_act/eval/runner.py`](../../src/plan_and_act/eval/runner.py)

High-value checks:
1. `step` monotonicity is sensible.
2. `planner_output.steps` aligns with later `executor_input.current_step`.
3. `executor_output.action` is reflected in `environment_step`.
4. Terminal events are always present.

## 4) Review model-output reliability path

Question to ask:
- If model output is messy text, how does system prevent bad data from entering trace/dataset?

Current path:
1. `LLMClient.chat_json` parses text to dict with fallbacks.
2. Role-specific Pydantic validation enforces structure.

Code:
- Parse logic: [`src/plan_and_act/utils/llm.py`](../../src/plan_and_act/utils/llm.py)
- Schemas: [`src/plan_and_act/core/schemas.py`](../../src/plan_and_act/core/schemas.py)
- Planner validation point: [`src/plan_and_act/agents/planner.py`](../../src/plan_and_act/agents/planner.py)

## 5) Review trace suitability for SFT construction

Current dataset builders are intentionally minimal:
- Builder: [`src/plan_and_act/training/build_sft_data.py`](../../src/plan_and_act/training/build_sft_data.py)
- Checks: [`src/plan_and_act/training/dataset_checks.py`](../../src/plan_and_act/training/dataset_checks.py)

Review question:
- Can we reconstruct `input` and `output` pairs for each role from traces without ambiguity?

If not, add fields/events before scaling data generation.

## 6) Mini extraction example from events

Use this snippet to prototype planner SFT rows from one trace:

```python
import json
from pathlib import Path

run_dir = Path("data/raw/traces/<run_id>")
events = [
    json.loads(line)
    for line in (run_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
    if line.strip()
]

planner_inputs = [e for e in events if e["event_type"] == "planner_input"]
planner_outputs = [e for e in events if e["event_type"] == "planner_output"]

rows = []
for pin, pout in zip(planner_inputs, planner_outputs):
    rows.append(
        {
            "input": json.dumps(pin["payload"], ensure_ascii=False),
            "output": json.dumps({"steps": pout["payload"].get("steps", [])}, ensure_ascii=False),
        }
    )

print("planner rows:", len(rows))
print(rows[0] if rows else "no rows")
```

This is only for review/prototyping. Production conversion should use explicit lineage metadata.

## 7) What findings usually appear first

In similar projects, the first meaningful findings are:
1. Missing failure taxonomy labels in events.
2. No split/leakage controls in trace-to-dataset stage.
3. Sparse provenance from SFT row back to raw trace.
4. Inconsistent event payload fields across versions.

## 8) How to apply this to future projects

Portable process:
1. Identify role boundaries and output schemas.
2. Instrument boundary events only.
3. Prove one episode can be reconstructed end-to-end.
4. Prototype SFT conversion on a small sample.
5. Add dataset integrity checks before scale-up.

Use this file as a repeatable review protocol for any agent framework.

