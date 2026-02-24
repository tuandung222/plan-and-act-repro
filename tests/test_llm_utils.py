from __future__ import annotations

from dataclasses import dataclass

import pytest
from tenacity import RetryError

from plan_and_act.utils.llm import LLMClient, _extract_usage, _parse_json_content, _redact_secrets


def test_redact_secrets_masks_openai_key_patterns() -> None:
    text = "token sk-proj-abc123_DEF and sk-legacy-xyz789 should be redacted"
    redacted = _redact_secrets(text)

    assert "sk-proj-abc123_DEF" not in redacted
    assert "sk-legacy-xyz789" not in redacted
    assert redacted.count("[REDACTED_OPENAI_KEY]") == 2


def test_parse_json_content_supports_direct_fenced_and_substring() -> None:
    assert _parse_json_content('{"a": 1}') == {"a": 1}
    assert _parse_json_content("```json\n{\"b\":2}\n```") == {"b": 2}
    assert _parse_json_content("text before {\"c\":3} text after") == {"c": 3}


def test_parse_json_content_raises_for_invalid_payload() -> None:
    with pytest.raises(ValueError, match="not valid JSON"):
        _parse_json_content("plain text with no braces")


@dataclass
class _Usage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


@dataclass
class _Response:
    usage: _Usage | None = None


def test_extract_usage_handles_missing_and_partial_values() -> None:
    assert _extract_usage(_Response(usage=None)) == {}
    assert _extract_usage(_Response(usage=_Usage(prompt_tokens=5, completion_tokens=7, total_tokens=12))) == {
        "prompt_tokens": 5,
        "completion_tokens": 7,
        "total_tokens": 12,
    }
    assert _extract_usage(_Response(usage=_Usage(prompt_tokens=3, completion_tokens=None, total_tokens=None))) == {
        "prompt_tokens": 3
    }


def test_llm_client_emits_trace_payload_without_network(monkeypatch: pytest.MonkeyPatch) -> None:
    traces: list[dict] = []
    client = LLMClient(trace_hook=traces.append)
    client.api_key = "dummy-key"

    class _Message:
        content = '{"ok": true}'

    class _Choice:
        message = _Message()

    class _UsageObj:
        prompt_tokens = 10
        completion_tokens = 5
        total_tokens = 15

    class _Resp:
        choices = [_Choice()]
        usage = _UsageObj()

    class _Completions:
        @staticmethod
        def create(**kwargs):
            return _Resp()

    class _Chat:
        completions = _Completions()

    class _FakeOpenAI:
        chat = _Chat()

    monkeypatch.setattr(client, "_build_client", lambda: _FakeOpenAI())

    payload = client.chat_json(
        model="gpt-4",
        system_prompt="sys",
        user_prompt="user",
        temperature=0.0,
        trace_context={"component": "planner", "step": 1},
    )

    assert payload == {"ok": True}
    assert len(traces) == 1
    assert traces[0]["status"] == "success"
    assert traces[0]["component"] == "planner"
    assert traces[0]["usage"]["total_tokens"] == 15


def test_llm_client_trace_records_parse_error(monkeypatch: pytest.MonkeyPatch) -> None:
    traces: list[dict] = []
    client = LLMClient(trace_hook=traces.append)
    client.api_key = "dummy-key"

    class _Message:
        content = "not-json"

    class _Choice:
        message = _Message()

    class _Resp:
        choices = [_Choice()]
        usage = None

    class _Completions:
        @staticmethod
        def create(**kwargs):
            return _Resp()

    class _Chat:
        completions = _Completions()

    class _FakeOpenAI:
        chat = _Chat()

    monkeypatch.setattr(client, "_build_client", lambda: _FakeOpenAI())

    with pytest.raises(RetryError):
        client.chat_json(
            model="gpt-4",
            system_prompt="sys",
            user_prompt="user",
            temperature=0.0,
            trace_context={"component": "executor", "step": 3},
        )

    # chat_json is retried 3 times by tenacity on parse errors.
    assert len(traces) == 3
    assert all(item["status"] == "parse_error" for item in traces)
    assert all(item["component"] == "executor" for item in traces)
