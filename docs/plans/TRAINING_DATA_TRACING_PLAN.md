# Training-Data Tracing Implementation Plan (Paper-Aligned)

Navigation:
- Reading hub: [`../READING_GUIDE.md`](../READING_GUIDE.md)
- Reproduction roadmap: [`REPRODUCTION_PLAN.md`](REPRODUCTION_PLAN.md)
- Architecture guide: [`../architecture/AGENT_FRAMEWORK_ARCHITECTURE.md`](../architecture/AGENT_FRAMEWORK_ARCHITECTURE.md)
- Code root: [`../../src/plan_and_act/`](../../src/plan_and_act/)

## 1. Objective

This document defines how to implement **trace collection as a training-data pipeline** aligned with Plan-and-Act methodology.

Target outputs:
1. Action trajectory traces.
2. Grounded-plan annotations (plan-step to action-span mapping).
3. Replanning training samples.
4. CoT-oriented training samples (where policy permits).
5. Failure taxonomy traces for targeted augmentation.

End goal:
Produce auditable datasets for:
1. Planner SFT.
2. Executor SFT.
3. Replanner SFT.
4. Optional CoT-enhanced variants.

## 2. What Must Be Traced (Paper-Aligned Coverage)

### 2.1 Action trajectory generation

Capture:
1. Seed query and synthetic query provenance.
2. Full step timeline (observation, action, tool result, transition).
3. Pass/fail judgments and reason codes.

### 2.2 Grounded plan generation

Capture:
1. Source trajectory ID.
2. Plan text and structure.
3. Step-to-action index alignment.

### 2.3 Synthetic plan expansion

Capture:
1. Seed query-plan pair ID.
2. Expanded pair ID.
3. Transformation metadata and generator version.

### 2.4 Dynamic replanning

Capture:
1. Pre-replan state slice.
2. Observation at replan time.
3. New plan and rationale metadata.

### 2.5 CoT traces

Capture (subject to policy and security constraints):
1. Planner reasoning trace metadata.
2. Executor reasoning trace metadata.
3. Replanner reasoning trace metadata.

### 2.6 Failure taxonomy and targeted augmentation

Capture:
1. Failure class label.
2. Trigger conditions.
3. Link from failure class to generated targeted samples.

## 3. Canonical Trace Schemas

## 3.1 Session-level trace

Path:
`data/raw/traces/<run_id>/session.json`

Example:

```json
{
  "schema_version": "1.0",
  "run_id": "20260224T120000Z",
  "goal": "...",
  "environment": {
    "kind": "tool",
    "name": "tool_calling"
  },
  "model_stack": {
    "planner": {"provider": "openai", "model": "gpt-4"},
    "executor": {"provider": "openai", "model": "gpt-4"},
    "replanner": {"provider": "openai", "model": "gpt-4"}
  },
  "runtime_config": {
    "max_steps": 8,
    "dynamic_replanning": true,
    "use_cot": false
  },
  "started_at": "...",
  "finished_at": "...",
  "status": "completed",
  "summary": {
    "event_count": 42
  }
}
```

## 3.2 Event-level trace (JSONL)

Path:
`data/raw/traces/<run_id>/events.jsonl`

Each line should contain:

```json
{
  "schema_version": "1.0",
  "run_id": "...",
  "event_type": "executor_output",
  "step": 3,
  "timestamp": "...",
  "payload": {},
  "meta": {
    "latency_ms": 123.4,
    "prompt_tokens": 120,
    "completion_tokens": 45
  }
}
```

Required event families:
1. `planner_input`, `planner_output`
2. `executor_input`, `executor_output`
3. `environment_step`
4. `tool_call_start`, `tool_call_end` (if applicable)
5. `replanner_input`, `replanner_output` (if applicable)
6. `episode_end` or `episode_error`

## 3.3 Normalized trajectory record

Path:
`data/interim/trajectories/<split>.jsonl`

```json
{
  "trajectory_id": "traj_001",
  "query": "...",
  "steps": [
    {
      "obs_before": "...",
      "action": {},
      "tool_result": {},
      "obs_after": "...",
      "done": false
    }
  ],
  "final_answer": "...",
  "success": true,
  "judge_score": 1.0,
  "provenance": {
    "run_id": "..."
  }
}
```

## 3.4 Grounded-plan record

Path:
`data/interim/grounded_plans/<split>.jsonl`

```json
{
  "trajectory_id": "traj_001",
  "query": "...",
  "plan": [
    {
      "step_id": 1,
      "intent": "...",
      "success_criteria": "...",
      "action_indices": [0, 1]
    }
  ],
  "source": {
    "teacher_model": "...",
    "generator_version": "..."
  }
}
```

## 3.5 SFT record outputs

Recommended paths:
1. `data/processed/sft/planner_sft.jsonl`
2. `data/processed/sft/executor_sft.jsonl`
3. `data/processed/sft/replanner_sft.jsonl`
4. `data/processed/sft/planner_cot_sft.jsonl` (optional)
5. `data/processed/sft/executor_cot_sft.jsonl` (optional)

## 4. Trace Hook Points in Current Codebase

### 4.1 LLM boundary hooks

Files:
1. [`../../src/plan_and_act/utils/llm.py`](../../src/plan_and_act/utils/llm.py)
2. [`../../src/plan_and_act/agents/planner.py`](../../src/plan_and_act/agents/planner.py)
3. [`../../src/plan_and_act/agents/executor.py`](../../src/plan_and_act/agents/executor.py)
4. [`../../src/plan_and_act/agents/replanner.py`](../../src/plan_and_act/agents/replanner.py)

Log requirements:
1. Prompt input (with secret redaction).
2. Raw model output.
3. Parsed JSON output.
4. Parse failures and error reasons.
5. Latency and token usage if available.

### 4.2 Graph node hooks

Files:
1. [`../../src/plan_and_act/graph/workflow.py`](../../src/plan_and_act/graph/workflow.py)
2. [`../../src/plan_and_act/eval/runner.py`](../../src/plan_and_act/eval/runner.py)

Log requirements:
1. Planner node input/output.
2. Executor node input/action/output transition.
3. Replanner node input/output.
4. Episode terminal summary and failure reasons.

### 4.3 Tool and environment hooks

Files:
1. [`../../src/plan_and_act/environments/tooling.py`](../../src/plan_and_act/environments/tooling.py)
2. [`../../src/plan_and_act/tools/base.py`](../../src/plan_and_act/tools/base.py)

Log requirements:
1. Tool selection decision.
2. Tool name, arguments shape, result, error.
3. Environment observation transition before/after step.

### 4.4 Data-pipeline hooks

Files:
1. [`../../src/plan_and_act/data/trajectory_gen.py`](../../src/plan_and_act/data/trajectory_gen.py)
2. [`../../src/plan_and_act/data/grounded_plan_gen.py`](../../src/plan_and_act/data/grounded_plan_gen.py)
3. [`../../src/plan_and_act/data/plan_expansion.py`](../../src/plan_and_act/data/plan_expansion.py)
4. [`../../src/plan_and_act/data/targeted_augmentation.py`](../../src/plan_and_act/data/targeted_augmentation.py)
5. [`../../src/plan_and_act/training/build_sft_data.py`](../../src/plan_and_act/training/build_sft_data.py)

Log requirements:
1. Source IDs and lineage links.
2. Filtering decisions and quality-gate reasons.
3. Export counts and schema-validation summaries.

## 5. Phase Plan

### Phase A - Tracing Infrastructure (2-3 days)

Deliverables:
1. Stable schemas in `tracing/schemas.py`.
2. Session/event writer in `tracing/writer.py`.
3. Runtime collector in `tracing/collector.py`.
4. Config toggles via `configs/tracing.yaml`.

Acceptance criteria:
1. Every traced run writes `session.json` and `events.jsonl`.
2. Trace overhead remains acceptable for local experimentation.

### Phase B - Runtime Instrumentation (2-4 days)

Deliverables:
1. Full planner/executor/replanner event coverage.
2. Tool-call start/end events with structured payloads.
3. LLM parse-error and usage metadata captured.

Acceptance criteria:
1. Event sequence supports deterministic replay analysis.
2. Error paths are represented explicitly, not silently dropped.

### Phase C - Dataset Builders (3-5 days)

Deliverables:
1. `scripts/trace_to_trajectories.py`
2. `scripts/trajectories_to_grounded_plans.py`
3. `scripts/build_sft_from_traces.py`
4. Data cards for generated outputs.

Acceptance criteria:
1. Planner/executor/replanner SFT exports are generated.
2. Dataset checks pass on structure and consistency.

### Phase D - Paper-Specific Augmentation (4-6 days)

Deliverables:
1. Failure classifier and taxonomy mapping.
2. Targeted augmentation generator.
3. CoT data-generation pipeline (policy-aware).

Acceptance criteria:
1. Dataset variants for each ablation stage are available.
2. Variant lineage is traceable and auditable.

### Phase E - Reproducibility and Audit (1-2 days)

Deliverables:
1. Run manifest (`run_manifest.json`) with config/model hashes.
2. Sample lineage graph (`sample_id -> ancestors`).
3. Integrity checker (`scripts/audit_trace_integrity.py`).

Acceptance criteria:
1. Any SFT sample can be traced back to raw events.
2. Integrity checker reports no critical contract violations.

## 6. Data Directory Convention

```text
data/
  raw/
    traces/
      <run_id>/
        session.json
        events.jsonl
  interim/
    trajectories/
    grounded_plans/
  processed/
    sft/
  synthetic/
    expanded_plans/
    targeted_plans/
```

## 7. Quality Gates (Mandatory)

1. Schema validation gate.
- Reject missing or malformed required fields.

2. Logical consistency gate.
- Validate step ordering, action-index ranges, and terminal flags.

3. Deduplication gate.
- Remove duplicate or near-duplicate query-plan pairs.

4. Leakage gate.
- Prevent test-derived lineage from entering training split.

5. Parse robustness gate.
- Track and cap parse-failure rate by role/component.

## 8. Mapping Trace Events to Training Tasks

### 8.1 Planner SFT

Input:
1. Goal, observation context, action history summary.

Output:
1. Structured `PlannerOutput` steps.

Event anchors:
1. `planner_input`
2. `planner_output`
3. `llm_call` for prompt/output metadata

### 8.2 Executor SFT

Input:
1. Goal, current step, current observation.

Output:
1. Structured `ExecutorAction`.

Event anchors:
1. `executor_input`
2. `executor_output`
3. `environment_step`

### 8.3 Replanner SFT

Input:
1. Previous plan, action history, latest observation.

Output:
1. Updated structured plan.

Event anchors:
1. `replanner_input`
2. `replanner_output`

### 8.4 CoT variants

Input/output:
1. Same role boundaries as above with optional reasoning traces.

Policy note:
CoT storage must respect provider policy and internal governance requirements.

## 9. Review and Governance Checklist

Before using traced data for training, confirm:
1. Event coverage is complete for all enabled modules.
2. Session summaries and event counts are consistent.
3. Error and parse-failure paths are represented explicitly.
4. Dataset lineage is queryable and reproducible.
5. Redaction policy is active for sensitive fields.

Supporting docs:
1. [`../tracing/TRACE_DATA_REVIEW_MINDSET.md`](../tracing/TRACE_DATA_REVIEW_MINDSET.md)
2. [`../tracing/TRACE_DATA_REVIEW_CHECKLIST.md`](../tracing/TRACE_DATA_REVIEW_CHECKLIST.md)
3. [`../tracing/TRACE_TO_SFT_CODE_REVIEW_WALKTHROUGH.md`](../tracing/TRACE_TO_SFT_CODE_REVIEW_WALKTHROUGH.md)

## 10. Expected Outcome

When this plan is implemented fully, the repository should provide:
1. A trace pipeline suitable for runtime debugging and model training.
2. Strong data contracts that reduce silent corruption.
3. Clear provenance for planner/executor/replanner SFT samples.
4. A repeatable methodology for reproducing other agent papers with similar data-centric requirements.
