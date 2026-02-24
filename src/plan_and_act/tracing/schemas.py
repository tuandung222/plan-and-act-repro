from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

TRACE_SCHEMA_VERSION = "1.1.0"
TRACE_EVENT_VERSION = 1


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class TraceConfig(BaseModel):
    enabled: bool = False
    base_dir: str = "data/raw/traces"
    flush_every: int = Field(default=1, ge=1)
    schema_version: str = TRACE_SCHEMA_VERSION


class TraceSession(BaseModel):
    schema_version: str = TRACE_SCHEMA_VERSION
    run_id: str
    started_at: str = Field(default_factory=utc_now_iso)
    finished_at: str = ""
    status: str = "running"
    goal: str
    environment: dict[str, Any] = Field(default_factory=dict)
    model_stack: dict[str, Any] = Field(default_factory=dict)
    runtime_config: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    summary: dict[str, Any] = Field(default_factory=dict)


class TraceEvent(BaseModel):
    schema_version: str = TRACE_SCHEMA_VERSION
    event_version: int = TRACE_EVENT_VERSION
    run_id: str
    step: int = 0
    event_type: str
    timestamp: str = Field(default_factory=utc_now_iso)
    payload: dict[str, Any] = Field(default_factory=dict)
    meta: dict[str, Any] = Field(default_factory=dict)
