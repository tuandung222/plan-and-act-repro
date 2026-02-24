from __future__ import annotations

from typing import Any


def build_sft_dataset(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert normalized records into SFT-ready JSONL-like rows."""
    rows: list[dict[str, Any]] = []
    for record in records:
        rows.append(
            {
                "messages": [
                    {"role": "user", "content": record.get("input", "")},
                    {"role": "assistant", "content": record.get("output", "")},
                ]
            }
        )
    return rows
