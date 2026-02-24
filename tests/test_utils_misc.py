from __future__ import annotations

import logging
import os
import random
from pathlib import Path

import pytest

from plan_and_act.tools.base import ToolRegistry
from plan_and_act.utils.io import load_yaml, write_json
from plan_and_act.utils.logging import get_logger
from plan_and_act.utils.seeding import set_seed


def test_load_yaml_requires_mapping(tmp_path: Path) -> None:
    mapping_file = tmp_path / "ok.yaml"
    mapping_file.write_text("a: 1\nb: test\n", encoding="utf-8")
    assert load_yaml(mapping_file) == {"a": 1, "b": "test"}

    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("- 1\n- 2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must be a mapping"):
        load_yaml(bad_file)


def test_write_json_creates_parent(tmp_path: Path) -> None:
    out = tmp_path / "nested" / "payload.json"
    write_json(out, {"x": 1})
    assert out.exists()
    assert '"x": 1' in out.read_text(encoding="utf-8")


def test_set_seed_sets_env_and_is_deterministic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PYTHONHASHSEED", raising=False)

    set_seed(123)
    first = random.random()
    set_seed(123)
    second = random.random()

    assert first == second
    assert os.environ["PYTHONHASHSEED"] == "123"


def test_get_logger_reuses_existing_handler() -> None:
    logger = get_logger("plan_and_act.tests.logger")
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 1

    same = get_logger("plan_and_act.tests.logger")
    assert same is logger
    assert len(same.handlers) == 1


def test_tool_registry_has_and_error_for_missing_tool() -> None:
    registry = ToolRegistry({})
    assert registry.has("missing") is False
    result = registry.call("missing", {"q": "x"})
    assert result["ok"] is False
    assert "not registered" in result["error"]
