from __future__ import annotations

from pathlib import Path
from typing import Any

import orjson


class TraceWriter:
    def __init__(self, *, base_dir: str, run_id: str) -> None:
        self.run_id = run_id
        self.run_dir = Path(base_dir) / run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.session_path = self.run_dir / "session.json"
        self.events_path = self.run_dir / "events.jsonl"

    def write_session(self, payload: dict[str, Any]) -> None:
        self.session_path.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2))

    def append_event(self, payload: dict[str, Any]) -> None:
        line = orjson.dumps(payload)
        with self.events_path.open("ab") as f:
            f.write(line)
            f.write(b"\n")
