# Docs Home

This folder organizes project documentation by intent so references stay stable and easier to browse in GitHub/IDE.

## Structure

1. Architecture
- Framework rationale: [`architecture/AGENT_FRAMEWORK_ARCHITECTURE.md`](architecture/AGENT_FRAMEWORK_ARCHITECTURE.md)
- Visual diagrams: [`architecture/AGENT_ARCHITECTURE_VISUAL_GUIDE.md`](architecture/AGENT_ARCHITECTURE_VISUAL_GUIDE.md)
- Orchestration pseudocode (planner/executor/replanner): [`architecture/ORCHESTRATION_SUBAGENTS_PSEUDOCODE.md`](architecture/ORCHESTRATION_SUBAGENTS_PSEUDOCODE.md)
- Planning deep dive: [`architecture/PLANNING_ORCHESTRATION_DEEP_DIVE.md`](architecture/PLANNING_ORCHESTRATION_DEEP_DIVE.md)

2. Analysis
- Paper review: [`analysis/PLAN_AND_ACT_REVIEW.md`](analysis/PLAN_AND_ACT_REVIEW.md)

3. Plans
- Reproduction plan: [`plans/REPRODUCTION_PLAN.md`](plans/REPRODUCTION_PLAN.md)
- Training-data tracing plan: [`plans/TRAINING_DATA_TRACING_PLAN.md`](plans/TRAINING_DATA_TRACING_PLAN.md)

4. Tracing
- Review mindset: [`tracing/TRACE_DATA_REVIEW_MINDSET.md`](tracing/TRACE_DATA_REVIEW_MINDSET.md)
- Review checklist: [`tracing/TRACE_DATA_REVIEW_CHECKLIST.md`](tracing/TRACE_DATA_REVIEW_CHECKLIST.md)
- Trace-to-SFT walkthrough: [`tracing/TRACE_TO_SFT_CODE_REVIEW_WALKTHROUGH.md`](tracing/TRACE_TO_SFT_CODE_REVIEW_WALKTHROUGH.md)

5. Navigation
- Reading guide: [`READING_GUIDE.md`](READING_GUIDE.md)
- Project README: [`../README.md`](../README.md)

## Notebook entry points

- Real tool demo: [`../notebooks/01_plan_and_act_real_tool_demo.ipynb`](../notebooks/01_plan_and_act_real_tool_demo.ipynb)
- Complex query + full LLM I/O monitoring: [`../notebooks/02_complex_query_full_trace_gpt4.ipynb`](../notebooks/02_complex_query_full_trace_gpt4.ipynb)
