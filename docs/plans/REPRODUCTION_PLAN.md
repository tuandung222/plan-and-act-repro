# Reproduction Plan - Plan-and-Act (arXiv:2503.09572v3)

Navigation:
- Reading hub: [`READING_GUIDE.md`](../READING_GUIDE.md)
- Project README: [`README.md`](../../README.md)
- Paper review: [`PLAN_AND_ACT_REVIEW.md`](../analysis/PLAN_AND_ACT_REVIEW.md)
- Notebook demo: [`notebooks/01_plan_and_act_real_tool_demo.ipynb`](../../notebooks/01_plan_and_act_real_tool_demo.ipynb)

## 0) Mục tiêu tái hiện (reproduce target)

Mục tiêu thực tế chia 3 mức để dễ kiểm soát kỳ vọng:

1. **Level A - Functional Reproduction**
- Dựng đầy đủ pipeline `Planner -> Executor -> (Dynamic) Replanner`.
- Chạy end-to-end trên WebArena-Lite-style tasks.

2. **Level B - Method Reproduction**
- Tái hiện các block chính của paper:
  - Synthetic Trajectory Generation
  - Grounded Plan Generation
  - Synthetic Plan Expansion
  - Targeted Augmentation
  - Dynamic Replanning
  - CoT augmentation

3. **Level C - Performance Reproduction (trend-level)**
- Tái hiện **xu hướng cải thiện** qua ablation giống paper.
- Không cam kết tuyệt đối cùng điểm số SOTA do khác model stack (paper dùng nhiều backbone/teacher khác nhau).

## 1) Chọn framework agent

Framework đề xuất: **LangGraph** (trên LangChain ecosystem), kết hợp WebArena/browser environment.

Lý do chọn:
1. Dễ mô hình hóa graph nhiều node (Planner, Executor, Replanner, Judge).
2. Dễ kiểm soát state, retry, checkpoint, trace.
3. Dễ mở rộng từ baseline sang dynamic replanning mà không phá kiến trúc.
4. Dễ đọc cho researcher (flow rõ ràng theo graph/state machine).

Note:
- Dù benchmark chính vẫn bám paper (WebArena/WebVoyager), framework implementation được thiết kế theo hướng **domain-agnostic** để tái sử dụng cho API/tool/data-workflow agents.

## 2) Stack kỹ thuật đề xuất

1. **Model API**
- Primary: `gpt-4` (theo yêu cầu của bạn).
- Cấu hình qua env var `OPENAI_API_KEY`, tuyệt đối không hard-code key trong source.

2. **Core libs**
- `python>=3.11`
- `langgraph`, `langchain`, `openai`, `pydantic`, `typer`
- `playwright` (nếu cần browser control ngoài benchmark harness)
- `pandas`, `numpy`, `scikit-learn` (analysis)
- `orjson`, `pyyaml`, `rich`, `tenacity`

3. **Experiment tracking**
- Ưu tiên `mlflow` hoặc `wandb` (chọn 1).
- Log đầy đủ: config, seed, prompt version, model version, metric theo split.

## 3) Cấu trúc mã nguồn chuẩn (clean + research-friendly)

```text
plan_and_act_repro/
  README.md
  REPRODUCTION_PLAN.md
  pyproject.toml
  .env.example
  .gitignore

  configs/
    base.yaml
    models.yaml
    data.yaml
    eval.yaml
    prompts/
      planner.yaml
      executor.yaml
      replanner.yaml
      cot.yaml

  src/
    plan_and_act/
      __init__.py
      core/
        state.py
        types.py
        schemas.py
      agents/
        planner.py
        executor.py
        replanner.py
        judge.py
      graph/
        workflow.py
        transitions.py
      data/
        trajectory_gen.py
        grounded_plan_gen.py
        plan_expansion.py
        targeted_augmentation.py
      training/
        build_sft_data.py
        dataset_checks.py
      eval/
        runner.py
        metrics.py
        ablation.py
      prompts/
        templates.py
      utils/
        io.py
        logging.py
        seeding.py

  scripts/
    setup_env.sh
    run_baseline.sh
    run_ablation.sh
    run_eval_webarena_lite.sh
    generate_synthetic_data.sh

  data/
    raw/
    interim/
    processed/
    synthetic/

  artifacts/
    runs/
    checkpoints/
    reports/

  notebooks/
    01_data_audit.ipynb
    02_ablation_analysis.ipynb

  tests/
    test_planner_output_schema.py
    test_executor_action_schema.py
    test_replanning_transition.py
```

## 4) Kế hoạch triển khai theo phase

## Phase 1 - Baseline hệ thống (3-4 ngày)
1. Dựng skeleton project + config system.
2. Dựng LangGraph workflow bản tối thiểu:
- `Planner -> Executor -> Stop/Continue`.
3. Chuẩn hóa schema I/O bằng Pydantic:
- PlanStep, Action, Observation, EpisodeState.
4. Chạy smoke test 5-10 task nhỏ.

Deliverable:
- End-to-end run được, log đầy đủ trace từng step.

## Phase 2 - Static Plan-and-Act (4-6 ngày)
1. Planner sinh structured plan nhiều bước.
2. Executor nhận plan + obs, sinh action hợp lệ.
3. Evaluation harness cho WebArena-Lite split.
4. Báo cáo baseline:
- No Planner vs Static Planner.

Deliverable:
- Báo cáo `artifacts/reports/phase2_baseline.md`.

## Phase 3 - Synthetic data pipeline (7-10 ngày)
1. **Trajectory Generation**:
- Từ seed query sinh query mới.
- Rollout actor để thu trajectories.
- Filter success/failure bằng judge/ORM-equivalent.
2. **Grounded Plan Generation**:
- Reverse-engineer plan từ trajectory.
- Map plan step <-> action span.
3. **Plan Expansion**:
- Sinh thêm query-plan pairs đa dạng.
4. **Targeted Augmentation**:
- Phân loại failure modes.
- Sinh dữ liệu tập trung vào nhóm lỗi.

Deliverable:
- Bộ dữ liệu synthetic versioned + data cards.

## Phase 4 - Dynamic replanning + CoT (5-7 ngày)
1. Replanning mỗi bước (bản faithful với paper).
2. Bổ sung CoT traces cho Planner/Executor.
3. Ablation theo đúng thứ tự paper:
- `No Planner`
- `+Static Planner`
- `+Synthetic Traj`
- `+Plan Expansion`
- `+Targeted Aug`
- `+Dynamic Replan`
- `+CoT`

Deliverable:
- Bảng metric so sánh đầy đủ và đồ thị xu hướng.

## Phase 5 - Research report & packaging (2-3 ngày)
1. Viết report chuẩn research blog + kỹ thuật.
2. Chuẩn hóa scripts 1-lệnh để chạy từng ablation.
3. Viết reproducibility checklist.

Deliverable:
- `artifacts/reports/final_reproduction_report.md`
- Public repo sạch, dễ đọc, có guideline chạy lại.

## 5) Thiết kế prompts/schemas (chuẩn hoá ngay từ đầu)

1. Planner output bắt buộc JSON schema:
- `goal`
- `steps[]` gồm `step_id`, `intent`, `success_criteria`

2. Executor output bắt buộc JSON schema:
- `action_type`
- `target`
- `arguments`
- `rationale` (tuỳ bật CoT)

3. Replanner input nên gồm:
- original goal
- previous plan
- executed actions
- latest observation
- failure hint (nếu có)

## 6) Bộ metric cần theo dõi

1. Task Success Rate (primary).
2. Plan validity rate (đúng schema + khả thi).
3. Action grounding accuracy.
4. Replan efficiency:
- số lần replan/episode
- token cost/episode
- latency/episode
5. Failure taxonomy:
- planning error
- grounding error
- observation misunderstanding
- loop/stuck error

## 7) Risk & kiểm soát rủi ro

1. **API chi phí cao**
- Giới hạn token, batch chạy nhỏ trước.
- Cache prompt-response khi phù hợp.

2. **Benchmark instability**
- Freeze seed + snapshot config + run metadata.

3. **Data drift từ synthetic loop**
- Áp quality gates (schema check, dedup, contradiction filter).

4. **Overfitting prompt**
- Tách validation set cố định cho từng website/task type.

## 8) Coding standards (cho audience researcher)

1. Type hints 100% cho core modules.
2. Pydantic schemas cho mọi boundary I/O.
3. Docstring ngắn, đúng ý nghĩa nghiên cứu.
4. Unit tests cho parser/schema/transition logic.
5. Không viết business logic trong notebook.
6. Config-driven, không hard-code model/prompt/path.

## 9) Quy ước chạy thí nghiệm

1. Mỗi run có `run_id` + commit hash + config hash.
2. Mỗi bảng kết quả phải có script tái tạo.
3. Mỗi cải tiến phải có ablation độc lập.
4. Kết luận chỉ dựa trên run đã log artifact đầy đủ.

## 10) Security note rất quan trọng

Bạn đã gửi API key trong chat. Khuyến nghị:
1. **Rotate key ngay** trong OpenAI dashboard.
2. Chỉ dùng key mới qua biến môi trường cục bộ (`OPENAI_API_KEY`).
3. Không commit key vào git, notebook output, log, hay markdown.

## 11) Kết luận lựa chọn thực thi

Nếu mục tiêu là “linh hoạt, dễ hiện thực, dễ mở rộng, dễ đọc cho researcher”, thì:
1. **LangGraph + schema-first design + config-driven experiments** là lựa chọn phù hợp nhất.
2. Triển khai theo 5 phase ở trên sẽ vừa giữ chất lượng kỹ thuật, vừa bám sát đóng góp cốt lõi của paper.
