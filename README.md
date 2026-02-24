# Plan-and-Act Reproduction (arXiv:2503.09572v3)

Navigation:
- Docs home: [`docs/README.md`](docs/README.md)
- Reading hub: [`docs/READING_GUIDE.md`](docs/READING_GUIDE.md)
- Reproduction roadmap: [`docs/plans/REPRODUCTION_PLAN.md`](docs/plans/REPRODUCTION_PLAN.md)
- Training-data tracing plan: [`docs/plans/TRAINING_DATA_TRACING_PLAN.md`](docs/plans/TRAINING_DATA_TRACING_PLAN.md)
- Tracing review mindset: [`docs/tracing/TRACE_DATA_REVIEW_MINDSET.md`](docs/tracing/TRACE_DATA_REVIEW_MINDSET.md)
- Tracing review checklist: [`docs/tracing/TRACE_DATA_REVIEW_CHECKLIST.md`](docs/tracing/TRACE_DATA_REVIEW_CHECKLIST.md)
- Trace-to-SFT walkthrough: [`docs/tracing/TRACE_TO_SFT_CODE_REVIEW_WALKTHROUGH.md`](docs/tracing/TRACE_TO_SFT_CODE_REVIEW_WALKTHROUGH.md)
- Paper deep-dive review: [`docs/analysis/PLAN_AND_ACT_REVIEW.md`](docs/analysis/PLAN_AND_ACT_REVIEW.md)
- Framework architecture guide: [`docs/architecture/AGENT_FRAMEWORK_ARCHITECTURE.md`](docs/architecture/AGENT_FRAMEWORK_ARCHITECTURE.md)
- Visual architecture guide: [`docs/architecture/AGENT_ARCHITECTURE_VISUAL_GUIDE.md`](docs/architecture/AGENT_ARCHITECTURE_VISUAL_GUIDE.md)
- Orchestration pseudocode: [`docs/architecture/ORCHESTRATION_SUBAGENTS_PSEUDOCODE.md`](docs/architecture/ORCHESTRATION_SUBAGENTS_PSEUDOCODE.md)
- Planning/orchestration deep dive: [`docs/architecture/PLANNING_ORCHESTRATION_DEEP_DIVE.md`](docs/architecture/PLANNING_ORCHESTRATION_DEEP_DIVE.md)
- Notebook demo: [`notebooks/01_plan_and_act_real_tool_demo.ipynb`](notebooks/01_plan_and_act_real_tool_demo.ipynb)
- Notebook full trace demo: [`notebooks/02_complex_query_full_trace_gpt4.ipynb`](notebooks/02_complex_query_full_trace_gpt4.ipynb)
- Repository root: [`../README.md`](../README.md)

Research-friendly codebase to reproduce the main ideas in **Plan-and-Act**:
- Planner-Executor modular architecture
- Synthetic planning-data pipeline
- Dynamic replanning
- CoT-enhanced planning/execution
- Domain-agnostic environment adapters (not limited to browser/web)

## Quick Start

1. Create env and install:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

2. Configure API key:
```bash
cp .env.example .env
# set OPENAI_API_KEY in .env
```

3. Run baseline episode:
```bash
plan-act-run run-episode --goal "Follow the top contributor of this GitHub project" --environment simulator --dynamic-replanning
```

4. Run tool-calling domain episode:
```bash
plan-act-run run-episode --goal "Find top contributor of openai/openai-python" --environment tool --dynamic-replanning
```

5. Run real tools demo (no model API key required):
```bash
plan-act-run demo-tools \
  --query "plan and act llm agents" \
  --url "https://arxiv.org/abs/2503.09572v3" \
  --expression "(42 * 13) / 7 + sqrt(81)"
```

6. Execute notebook end-to-end test:
```bash
./scripts/test_notebook.sh
```

7. Run one traced episode (writes `session.json` and `events.jsonl`):
```bash
./scripts/run_episode_with_trace.sh
```

## Project Layout

- `configs/`: model/data/eval/prompt configs
- `src/plan_and_act/`: source code
- `src/plan_and_act/environments/`: domain adapters (`simulator`, `tool`)
- `src/plan_and_act/tools/`: reusable external tools (e.g., GitHub API)
- `tests/`: unit tests for schema/graph transitions
- `data/`: raw/interim/processed/synthetic datasets
- `artifacts/`: run traces and reports
- `paper_assets/`: downloaded arXiv HTML/PDF

## Notes

- This scaffold starts with a deterministic environment simulator to validate workflow wiring.
- Includes no-key real tools: web search, URL fetch, calculator.
- Replace/add domain adapters (browser/API/desktop/data pipelines) as needed.
