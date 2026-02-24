#!/usr/bin/env bash
set -euo pipefail

source .venv/bin/activate

export OPENAI_API_KEY=""

plan-act-run demo-tools \
  --query "plan and act llm agents" \
  --url "https://arxiv.org/abs/2503.09572v3" \
  --expression "(42 * 13) / 7 + sqrt(81)"
