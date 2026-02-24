from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ActionType = Literal["click", "type", "search", "exit"]


class ModelConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4"
    temperature: float = 0.0


class RuntimeConfig(BaseModel):
    experiment_name: str = "plan_and_act_baseline"
    seed: int = 42
    max_steps: int = Field(default=8, ge=1)
    dynamic_replanning: bool = True
    use_cot: bool = False
    save_artifacts: bool = True
    artifact_dir: str = "artifacts/runs"
