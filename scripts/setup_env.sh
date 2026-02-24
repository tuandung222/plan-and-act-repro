#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]

echo "Environment ready. Copy .env.example to .env and set OPENAI_API_KEY."
