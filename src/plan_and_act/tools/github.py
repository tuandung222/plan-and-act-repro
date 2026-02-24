from __future__ import annotations

import json
import urllib.request
from typing import Any


class GitHubTopContributorTool:
    """Real tool that calls GitHub REST API and returns top contributor."""

    name = "github_top_contributor"

    def __init__(self, *, user_agent: str = "plan-and-act-repro") -> None:
        self.user_agent = user_agent

    @staticmethod
    def _resolve_owner_repo(arguments: dict[str, Any]) -> tuple[str, str]:
        owner = str(arguments.get("owner", "")).strip()
        repo = str(arguments.get("repo", "")).strip()

        if owner and repo:
            return owner, repo

        query = str(arguments.get("query", "")).strip()
        if "/" in query:
            left, right = query.split("/", 1)
            if left.strip() and right.strip():
                return left.strip(), right.strip()

        return "openai", "openai-python"

    def run(self, arguments: dict[str, Any]) -> dict[str, Any]:
        owner, repo = self._resolve_owner_repo(arguments)
        url = f"https://api.github.com/repos/{owner}/{repo}/contributors?per_page=1"
        req = urllib.request.Request(
            url=url,
            headers={"User-Agent": self.user_agent},
            method="GET",
        )

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                payload = resp.read().decode("utf-8")
            data = json.loads(payload)
        except Exception as exc:  # pragma: no cover - network variability
            return {
                "ok": False,
                "error": str(exc),
                "owner": owner,
                "repo": repo,
            }

        if not data:
            return {
                "ok": False,
                "error": "No contributors returned",
                "owner": owner,
                "repo": repo,
            }

        top = data[0]
        return {
            "ok": True,
            "owner": owner,
            "repo": repo,
            "login": top.get("login", ""),
            "contributions": top.get("contributions", 0),
            "profile_url": top.get("html_url", ""),
        }
