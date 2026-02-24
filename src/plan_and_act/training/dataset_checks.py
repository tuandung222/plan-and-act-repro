from __future__ import annotations

from typing import Any


REQUIRED_KEYS = {"input", "output"}


def validate_dataset(records: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for idx, row in enumerate(records):
        missing = REQUIRED_KEYS - row.keys()
        if missing:
            errors.append(f"row[{idx}] missing keys: {sorted(missing)}")
    return errors
