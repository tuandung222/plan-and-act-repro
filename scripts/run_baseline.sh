#!/usr/bin/env bash
set -euo pipefail

source .venv/bin/activate
plan-act-run run-episode \
  --goal "Follow the top contributor of this GitHub project" \
  --environment simulator \
  --dynamic-replanning \
  --no-use-cot
