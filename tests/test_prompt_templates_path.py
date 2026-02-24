from __future__ import annotations

from pathlib import Path

import pytest

from plan_and_act.prompts.templates import PromptTemplates


def test_prompt_templates_resolve_from_parent_cwd(monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = Path(__file__).resolve().parents[1]
    monkeypatch.chdir(project_root.parent)

    prompts = PromptTemplates(config_dir="configs/prompts")

    assert "system" in prompts.planner
    assert "user_template" in prompts.executor
    assert "system" in prompts.replanner


def test_prompt_templates_accept_absolute_path(monkeypatch: pytest.MonkeyPatch) -> None:
    project_root = Path(__file__).resolve().parents[1]
    abs_dir = project_root / "configs" / "prompts"
    monkeypatch.chdir(project_root.parent)

    prompts = PromptTemplates(config_dir=str(abs_dir))

    assert "system" in prompts.planner


def test_prompt_templates_missing_dir_raises_helpful_error() -> None:
    with pytest.raises(FileNotFoundError, match="Could not resolve prompt config_dir"):
        PromptTemplates(config_dir="configs/does-not-exist")
