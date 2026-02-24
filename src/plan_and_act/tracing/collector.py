from __future__ import annotations

from typing import Any

from plan_and_act.tracing.schemas import TraceConfig, TraceEvent, TraceSession, utc_now_iso
from plan_and_act.tracing.writer import TraceWriter


class TraceCollector:
    def __init__(self, *, config: TraceConfig, run_id: str) -> None:
        self.config = config
        self.run_id = run_id
        self.enabled = config.enabled
        self.writer: TraceWriter | None = None
        self.session: TraceSession | None = None
        self._event_count = 0

        if self.enabled:
            self.writer = TraceWriter(base_dir=config.base_dir, run_id=run_id)

    @classmethod
    def disabled(cls) -> "TraceCollector":
        return cls(config=TraceConfig(enabled=False), run_id="disabled")

    def start_session(
        self,
        *,
        goal: str,
        environment: dict[str, Any],
        model_stack: dict[str, Any],
        runtime_config: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if not self.enabled or self.writer is None:
            return

        self.session = TraceSession(
            schema_version=self.config.schema_version,
            run_id=self.run_id,
            goal=goal,
            environment=environment,
            model_stack=model_stack,
            runtime_config=runtime_config,
            metadata=metadata or {},
        )
        self.writer.write_session(self.session.model_dump())

    def log_event(
        self,
        *,
        event_type: str,
        step: int,
        payload: dict[str, Any],
        meta: dict[str, Any] | None = None,
    ) -> None:
        if not self.enabled or self.writer is None:
            return

        event = TraceEvent(
            schema_version=self.config.schema_version,
            run_id=self.run_id,
            step=step,
            event_type=event_type,
            payload=payload,
            meta=meta or {},
        )
        self.writer.append_event(event.model_dump())
        self._event_count += 1

    def close(self, *, status: str, summary: dict[str, Any] | None = None) -> None:
        if not self.enabled or self.writer is None or self.session is None:
            return

        self.session.finished_at = utc_now_iso()
        self.session.status = status
        self.session.summary = {
            **(summary or {}),
            "event_count": self._event_count,
        }
        self.writer.write_session(self.session.model_dump())
