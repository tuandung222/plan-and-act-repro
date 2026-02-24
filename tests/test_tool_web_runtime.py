from __future__ import annotations

import pytest

from plan_and_act.tools.web import FetchURLTool, WebSearchTool


class _FakeWebResponse:
    def __init__(self, payload: str, *, status: int = 200, final_url: str = "https://example.com") -> None:
        self._payload = payload
        self.status = status
        self._final_url = final_url

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self) -> bytes:
        return self._payload.encode("utf-8")

    def geturl(self) -> str:
        return self._final_url


def test_web_search_tool_success_and_missing_query(monkeypatch: pytest.MonkeyPatch) -> None:
    tool = WebSearchTool()
    assert tool.run({})["ok"] is False

    html = """
    <html><body>
      <a class="result__a" href="https://example.com/a">Result A</a>
      <a class="result__a" href="https://example.com/b">Result B</a>
    </body></html>
    """
    monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=20: _FakeWebResponse(html))
    result = tool.run({"query": "test", "max_results": 1})

    assert result["ok"] is True
    assert result["count"] == 1
    assert result["results"][0]["title"] == "Result A"


def test_fetch_url_tool_validation_success_and_error(monkeypatch: pytest.MonkeyPatch) -> None:
    tool = FetchURLTool()
    assert tool.run({})["ok"] is False
    assert tool.run({"url": "ftp://example.com"})["ok"] is False

    html = "<html><head><title>T</title></head><body><p>Hello world</p></body></html>"
    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda req, timeout=20: _FakeWebResponse(html, status=201, final_url="https://example.com/final"),
    )
    ok = tool.run({"url": "https://example.com", "max_chars": 1000})
    assert ok["ok"] is True
    assert ok["status"] == 201
    assert ok["title"] == "T"
    assert "Hello world" in ok["content_preview"]

    def _raise(*args, **kwargs):
        raise RuntimeError("timeout")

    monkeypatch.setattr("urllib.request.urlopen", _raise)
    failed = tool.run({"url": "https://example.com"})
    assert failed["ok"] is False
    assert "timeout" in failed["error"]
