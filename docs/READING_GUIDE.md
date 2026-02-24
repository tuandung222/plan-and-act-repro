# Plan-and-Act Reading Guide

Use this page as the navigation hub when browsing on GitHub.

## Recommended Order

1. Project overview and quick start:
[`../README.md`](../README.md)
2. Reproduction roadmap and implementation phases:
[`plans/REPRODUCTION_PLAN.md`](plans/REPRODUCTION_PLAN.md)
3. Training-data tracing implementation plan:
[`plans/TRAINING_DATA_TRACING_PLAN.md`](plans/TRAINING_DATA_TRACING_PLAN.md)
4. Tracing review mindset (LLM Scientist perspective):
[`tracing/TRACE_DATA_REVIEW_MINDSET.md`](tracing/TRACE_DATA_REVIEW_MINDSET.md)
5. Tracing review checklist:
[`tracing/TRACE_DATA_REVIEW_CHECKLIST.md`](tracing/TRACE_DATA_REVIEW_CHECKLIST.md)
6. Trace-to-SFT practical walkthrough:
[`tracing/TRACE_TO_SFT_CODE_REVIEW_WALKTHROUGH.md`](tracing/TRACE_TO_SFT_CODE_REVIEW_WALKTHROUGH.md)
7. Technical deep-dive review of the paper:
[`analysis/PLAN_AND_ACT_REVIEW.md`](analysis/PLAN_AND_ACT_REVIEW.md)
8. Framework architecture details and implementation rationale:
[`architecture/AGENT_FRAMEWORK_ARCHITECTURE.md`](architecture/AGENT_FRAMEWORK_ARCHITECTURE.md)
9. Visual architecture and sequence diagrams:
[`architecture/AGENT_ARCHITECTURE_VISUAL_GUIDE.md`](architecture/AGENT_ARCHITECTURE_VISUAL_GUIDE.md)
10. Orchestration pseudocode for sub-agents:
[`architecture/ORCHESTRATION_SUBAGENTS_PSEUDOCODE.md`](architecture/ORCHESTRATION_SUBAGENTS_PSEUDOCODE.md)
11. Interactive module inspection + real tool demo:
[`../notebooks/01_plan_and_act_real_tool_demo.ipynb`](../notebooks/01_plan_and_act_real_tool_demo.ipynb)

## Source Materials

- Paper PDF:
[`../paper_assets/2503.09572v3.pdf`](../paper_assets/2503.09572v3.pdf)
- Paper HTML:
[`../paper_assets/2503.09572v3.html`](../paper_assets/2503.09572v3.html)
- arXiv abstract page:
[https://arxiv.org/abs/2503.09572v3](https://arxiv.org/abs/2503.09572v3)

## Implementation Entry Points

- Main package:
[`../src/plan_and_act/`](../src/plan_and_act/)
- Workflow graph:
[`../src/plan_and_act/graph/workflow.py`](../src/plan_and_act/graph/workflow.py)
- Environment adapters:
[`../src/plan_and_act/environments/`](../src/plan_and_act/environments/)
- Tool implementations:
[`../src/plan_and_act/tools/`](../src/plan_and_act/tools/)
- No-key tools architecture:
[`architecture/AGENT_FRAMEWORK_ARCHITECTURE.md`](architecture/AGENT_FRAMEWORK_ARCHITECTURE.md#5-real-tools-without-model-api-key)
- CLI runner:
[`../src/plan_and_act/eval/runner.py`](../src/plan_and_act/eval/runner.py)
- Scripts:
[`../scripts/`](../scripts/)
- No-key real tools demo script:
[`../scripts/run_real_tools_demo.sh`](../scripts/run_real_tools_demo.sh)
- Traced episode script:
[`../scripts/run_episode_with_trace.sh`](../scripts/run_episode_with_trace.sh)
- Notebook execution test script:
[`../scripts/test_notebook.sh`](../scripts/test_notebook.sh)
- Tests:
[`../tests/`](../tests/)
