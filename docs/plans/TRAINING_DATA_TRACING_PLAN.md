# Training Data Tracing Implementation Plan (Paper-Aligned)

Navigation:
- Reading hub: [`READING_GUIDE.md`](../READING_GUIDE.md)
- Reproduction roadmap: [`REPRODUCTION_PLAN.md`](REPRODUCTION_PLAN.md)
- Architecture guide: [`AGENT_FRAMEWORK_ARCHITECTURE.md`](../architecture/AGENT_FRAMEWORK_ARCHITECTURE.md)
- Code root: [`src/plan_and_act/`](../../src/plan_and_act/)

## 1) Mục tiêu

Mục tiêu tài liệu này là lên kế hoạch hiện thực **data tracing phục vụ training** giống paper Plan-and-Act, gồm:
1. Tracing action trajectories
2. Tracing grounded-plan annotations (plan step <-> action span)
3. Tracing replanning samples
4. Tracing CoT training samples
5. Tracing failure taxonomy + targeted augmentation

Mục tiêu cuối cùng: sinh được bộ dữ liệu chuẩn để train:
- Planner SFT
- Executor SFT
- Replanner SFT
- (Optional) CoT-enhanced SFT

## 2) Bám sát paper: cần trace những gì

Theo pipeline paper (Section 4.x + 3.3 + 3.4), ta cần trace các lớp dữ liệu sau:

1. **Action Trajectory Generation (4.1)**
- Query seed
- Synthetic query
- Full trajectory (obs/action/tool result/reward)
- Pass/fail của judge/ORM

2. **Grounded Plan Generation (4.2)**
- Trajectory đã pass
- Plan được annotate
- Mapping step -> action indices

3. **Synthetic Plan Expansion (4.3)**
- Seed query-plan pairs
- Expanded query-plan pairs
- Provenance: generated-from seed nào

4. **Dynamic Replanning Data (4.2.1 + 3.3)**
- Prefix trajectory + previous plan
- Observation tại thời điểm replan
- Replanned steps

5. **CoT Traces (4.2.2 + 3.4)**
- Planner CoT traces
- Executor CoT traces
- Optional replanner CoT traces

6. **Failure Classification + Targeted Augmentation (4.3)**
- Failure label taxonomy
- Link từ failure -> selected seeds -> generated targeted data

## 3) Thiết kế trace schema (chuẩn hóa trước khi code)

## 3.1 Session-level trace
File: `data/raw/traces/<run_id>/session.json`

```json
{
  "run_id": "20260219T...Z",
  "goal": "...",
  "environment": "tool|simulator|webarena",
  "model_stack": {
    "planner": "gpt-4",
    "executor": "gpt-4",
    "replanner": "gpt-4"
  },
  "config_hash": "...",
  "git_commit": "...",
  "started_at": "...",
  "finished_at": "..."
}
```

## 3.2 Step-level event trace (JSONL)
File: `data/raw/traces/<run_id>/events.jsonl`

Mỗi event 1 dòng JSON, có `event_type`:
- `planner_input`
- `planner_output`
- `executor_input`
- `executor_output`
- `tool_call`
- `environment_step`
- `judge_result`
- `replanner_input`
- `replanner_output`
- `episode_end`

Event format tối thiểu:
```json
{
  "run_id": "...",
  "step": 3,
  "event_type": "executor_output",
  "timestamp": "...",
  "payload": {...},
  "meta": {
    "latency_ms": 123,
    "tokens_prompt": 0,
    "tokens_completion": 0
  }
}
```

## 3.3 Normalized trajectory record
File: `data/interim/trajectories/<split>.jsonl`

```json
{
  "trajectory_id": "traj_...",
  "query": "...",
  "steps": [
    {
      "obs_before": "...",
      "action": {...},
      "tool_result": {...},
      "obs_after": "...",
      "done": false
    }
  ],
  "final_answer": "...",
  "success": true,
  "judge_score": 1.0,
  "provenance": {...}
}
```

## 3.4 Grounded-plan record
File: `data/interim/grounded_plans/<split>.jsonl`

```json
{
  "trajectory_id": "...",
  "query": "...",
  "plan": [
    {
      "step_id": 1,
      "intent": "...",
      "success_criteria": "...",
      "action_indices": [0, 1]
    }
  ],
  "source": "teacher_model_name"
}
```

## 3.5 SFT records
Files:
- `data/processed/sft/planner_sft.jsonl`
- `data/processed/sft/executor_sft.jsonl`
- `data/processed/sft/replanner_sft.jsonl`
- `data/processed/sft/planner_cot_sft.jsonl` (optional)
- `data/processed/sft/executor_cot_sft.jsonl` (optional)

## 4) Điểm hook tracing trong code hiện tại

## 4.1 LLM tracing
File cần chỉnh:
- `src/plan_and_act/utils/llm.py`

Hook:
1. Trước call model: log `model`, `temperature`, prompt id/hash, input payload hash
2. Sau call model: log raw output, parse status, latency, token usage
3. Khi parse lỗi JSON: log raw output + exception để debug training-data noise

## 4.2 Graph/node tracing
Files:
- `src/plan_and_act/graph/workflow.py`
- `src/plan_and_act/eval/runner.py`

Hook:
1. `planner_node`: input snapshot + output plan
2. `executor_node`: current step + action output + env transition
3. `replanner_node`: context trước/sau replan
4. kết thúc episode: success/failure + stop reason

## 4.3 Tool/environment tracing
Files:
- `src/plan_and_act/environments/tooling.py`
- `src/plan_and_act/tools/base.py`

Hook:
1. Tool name, arguments, result, error
2. Action->tool routing decision (`action_type_tool_map` hay `target=tool:*`)
3. Environment observation transitions

## 4.4 Data pipeline tracing
Files:
- `src/plan_and_act/data/trajectory_gen.py`
- `src/plan_and_act/data/grounded_plan_gen.py`
- `src/plan_and_act/data/plan_expansion.py`
- `src/plan_and_act/data/targeted_augmentation.py`
- `src/plan_and_act/training/build_sft_data.py`

Hook:
1. provenance của mỗi sample
2. source record ids
3. filtering decisions (pass/fail + reason)
4. final export counts per dataset

## 5) Kế hoạch triển khai theo phase (thực thi)

## Phase A - Tracing Infrastructure (2-3 ngày)

Deliverables:
1. `src/plan_and_act/tracing/` module mới:
- `schemas.py` (event/session schemas)
- `writer.py` (JSON/JSONL writer)
- `collector.py` (runtime collector)
2. `configs/tracing.yaml`
3. bật/tắt tracing bằng config

Acceptance criteria:
- Mỗi run sinh được `session.json` + `events.jsonl`
- Overhead tracing < 10% runtime local

## Phase B - Runtime Hooking (2-4 ngày)

Deliverables:
1. Hook vào planner/executor/replanner nodes
2. Hook vào tool calls và environment transitions
3. Hook vào LLM client (latency + parse failure + token usage nếu có)

Acceptance criteria:
- 1 episode có trace end-to-end đầy đủ event sequence
- replay timeline đọc được theo step

## Phase C - Dataset Builders (3-5 ngày)

Deliverables:
1. `scripts/trace_to_trajectories.py`
2. `scripts/trajectories_to_grounded_plans.py`
3. `scripts/build_sft_from_traces.py`
4. data cards cho mỗi output dataset

Acceptance criteria:
- Build được 3 bộ SFT: planner/executor/replanner
- Dataset checks pass (schema + completeness)

## Phase D - Paper-specific Augmentation (4-6 ngày)

Deliverables:
1. failure classifier + taxonomy mapping
2. targeted plan augmentation pipeline
3. CoT trace generation pipeline

Acceptance criteria:
- Có dataset version cho:
  - base
  - +synthetic traj
  - +plan expansion
  - +targeted
  - +replanning
  - +CoT

## Phase E - Reproducibility & Audit (1-2 ngày)

Deliverables:
1. manifest theo run (`run_manifest.json`)
2. dataset provenance graph (`sample_id -> ancestors`)
3. script `scripts/audit_trace_integrity.py`

Acceptance criteria:
- Từ một sample SFT bất kỳ truy ngược được lineage

## 6) Quy ước thư mục dữ liệu đề xuất

```text
data/
  raw/
    traces/
      <run_id>/
        session.json
        events.jsonl
  interim/
    trajectories/
      train.jsonl
      val.jsonl
    grounded_plans/
      train.jsonl
      val.jsonl
  processed/
    sft/
      planner_sft.jsonl
      executor_sft.jsonl
      replanner_sft.jsonl
      planner_cot_sft.jsonl
      executor_cot_sft.jsonl
  synthetic/
    expanded_plans/
    targeted_plans/
```

## 7) Data quality gates (bắt buộc)

1. Schema validation gate
- reject sample nếu thiếu field quan trọng

2. Logical consistency gate
- action_indices phải nằm trong range trajectory steps
- done/success transition không mâu thuẫn

3. Dedup gate
- hash-based near-duplicate removal cho query-plan pair

4. Leakage gate
- không cho sample test xuất hiện trong train provenance

5. Parse robustness gate
- tỷ lệ raw model outputs parse fail < threshold

## 8) Mapping trace -> training tasks

1. Planner SFT
Input: goal + observation summary + history
Output: structured plan steps

2. Executor SFT
Input: goal + current_step + current_observation
Output: action JSON

3. Replanner SFT
Input: goal + previous_plan + action_history + latest_observation
Output: updated plan

4. CoT variants
Input giống trên
Output: reasoning + final JSON (hoặc hidden reasoning policy tùy model policy)

## 9) Testing plan cho tracing pipeline

Unit tests cần thêm:
1. trace schema validation
2. trace writer append/flush correctness
3. action_indices grounding validator
4. dataset builder mapping correctness

Integration tests cần thêm:
1. run 1 episode -> sinh traces -> build SFT thành công
2. run tool environment -> trace đủ `tool_call` events
3. replay timeline từ events.jsonl không lỗi

## 10) Command plan (khi bắt đầu code)

Đề xuất scripts mới:
1. `scripts/run_episode_with_trace.sh`
2. `scripts/build_training_data_from_traces.sh`
3. `scripts/audit_trace_integrity.sh`

Luồng chuẩn:
```bash
./scripts/run_episode_with_trace.sh
./scripts/build_training_data_from_traces.sh
./scripts/audit_trace_integrity.sh
pytest -q
```

## 11) Khuyến nghị để giống paper hơn

1. tách rõ teacher model cho annotation vs actor model cho rollout
2. thêm judge/ORM-equivalent score vào trace
3. track failure classes theo website/domain/task-type
4. giữ versioned dataset snapshots cho từng ablation stage

## 12) Kết luận

Nếu triển khai đúng kế hoạch tracing này, framework hiện tại sẽ có:
1. dữ liệu training có lineage rõ ràng
2. đủ điều kiện tái hiện các block data-centric của paper
3. khả năng mở rộng sang paper agent khác chỉ bằng cách thay adapters + annotators
