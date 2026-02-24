from __future__ import annotations

import json

import pytest

from plan_and_act.tools.github import GitHubTopContributorTool


class _FakeHTTPResponse:
    def __init__(self, payload: str) -> None:
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._payload.encode("utf-8")


def test_resolve_owner_repo_prefers_explicit_fields() -> None:
    owner, repo = GitHubTopContributorTool._resolve_owner_repo({"owner": "openai", "repo": "openai-python"})
    assert (owner, repo) == ("openai", "openai-python")

    owner, repo = GitHubTopContributorTool._resolve_owner_repo({"query": "owner-x/repo-y"})
    assert (owner, repo) == ("owner-x", "repo-y")

    owner, repo = GitHubTopContributorTool._resolve_owner_repo({})
    assert (owner, repo) == ("openai", "openai-python")


def test_github_tool_run_success(monkeypatch: pytest.MonkeyPatch) -> None:
    tool = GitHubTopContributorTool()

    payload = json.dumps(
        [
            {
                "login": "alice",
                "contributions": 42,
                "html_url": "https://github.com/alice",
            }
        ]
    )
    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=20: _FakeHTTPResponse(payload))

    result = tool.run({"query": "owner/repo"})
    assert result["ok"] is True
    assert result["owner"] == "owner"
    assert result["repo"] == "repo"
    assert result["login"] == "alice"


def test_github_tool_run_empty_and_error(monkeypatch: pytest.MonkeyPatch) -> None:
    tool = GitHubTopContributorTool()

    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=20: _FakeHTTPResponse("[]"))
    empty = tool.run({"query": "o/r"})
    assert empty["ok"] is False
    assert "No contributors" in empty["error"]

    def _raise(*args, **kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr("urllib.request.urlopen", _raise)
    failed = tool.run({"query": "o/r"})
    assert failed["ok"] is False
    assert "network down" in failed["error"]
