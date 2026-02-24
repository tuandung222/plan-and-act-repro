#!/usr/bin/env bash
set -euo pipefail

source .venv/bin/activate

python scripts/execute_notebook.py \
  --input notebooks/01_plan_and_act_real_tool_demo.ipynb \
  --output artifacts/reports/01_plan_and_act_real_tool_demo.executed.ipynb \
  --timeout 300
