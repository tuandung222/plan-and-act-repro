#!/usr/bin/env bash
set -euo pipefail

source .venv/bin/activate

export OPENAI_API_KEY=""

plan-act-run run-episode \
  --goal "Find the top contributor of openai/openai-python" \
  --environment tool \
  --dynamic-replanning \
  --no-use-cot
