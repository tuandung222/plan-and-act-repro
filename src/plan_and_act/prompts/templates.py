from __future__ import annotations

from pathlib import Path
from typing import Any

from plan_and_act.utils.io import load_yaml


class PromptTemplates:
    def __init__(self, config_dir: str = "configs/prompts") -> None:
        base = self._resolve_config_dir(config_dir)
        self.planner = load_yaml(base / "planner.yaml")
        self.executor = load_yaml(base / "executor.yaml")
        self.replanner = load_yaml(base / "replanner.yaml")
        self.cot = load_yaml(base / "cot.yaml")

    @staticmethod
    def _resolve_config_dir(config_dir: str) -> Path:
        candidate = Path(config_dir)
        if candidate.is_absolute():
            return candidate

        cwd_candidate = (Path.cwd() / candidate).resolve()
        if cwd_candidate.exists():
            return cwd_candidate

        # repo_root from: src/plan_and_act/prompts/templates.py -> repo root
        repo_root = Path(__file__).resolve().parents[3]
        repo_candidate = (repo_root / candidate).resolve()
        if repo_candidate.exists():
            return repo_candidate

        tried = [str(cwd_candidate), str(repo_candidate)]
        raise FileNotFoundError(
            f"Could not resolve prompt config_dir='{config_dir}'. Tried: {tried}"
        )

    @staticmethod
    def format_user(template: str, payload: dict[str, Any]) -> str:
        return template.format(**payload)
