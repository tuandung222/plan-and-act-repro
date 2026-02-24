from __future__ import annotations

import json
import os
import re
import time
from collections.abc import Callable
from typing import Any

from openai import BadRequestError, OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

LLMTraceHook = Callable[[dict[str, Any]], None]
_SECRET_PATTERNS = (
    re.compile(r"sk-proj-[A-Za-z0-9_-]+"),
    re.compile(r"sk-[A-Za-z0-9_-]+"),
)


class LLMClient:
    def __init__(self, trace_hook: LLMTraceHook | None = None) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.base_url = os.getenv("OPENAI_BASE_URL", "").strip()
        self.trace_hook = trace_hook

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _build_client(self) -> OpenAI:
        kwargs: dict[str, Any] = {"api_key": self.api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return OpenAI(**kwargs)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=6))
    def chat_json(
        self,
        *,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        trace_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not self.enabled:
            raise RuntimeError("OPENAI_API_KEY is not set")

        client = self._build_client()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        start_time = time.perf_counter()
        raw_content = ""
        parsed_output: dict[str, Any] | None = None
        usage: dict[str, int] = {}
        used_response_format = True
        status = "success"
        error = ""

        def _request(*, with_response_format: bool) -> tuple[str, dict[str, int]]:
            request_kwargs: dict[str, Any] = {
                "model": model,
                "temperature": temperature,
                "messages": messages,
            }
            if with_response_format:
                request_kwargs["response_format"] = {"type": "json_object"}
            response = client.chat.completions.create(**request_kwargs)
            content = response.choices[0].message.content or "{}"
            return content, _extract_usage(response)

        try:
            try:
                raw_content, usage = _request(with_response_format=True)
            except BadRequestError as exc:
                if "response_format" not in str(exc):
                    raise
                used_response_format = False
                raw_content, usage = _request(with_response_format=False)

            parsed_output = _parse_json_content(raw_content)
            return parsed_output
        except BadRequestError as exc:
            status = "api_error"
            error = f"{type(exc).__name__}: {exc}"
            raise
        except Exception as exc:
            status = "parse_error" if isinstance(exc, ValueError) else "error"
            error = f"{type(exc).__name__}: {exc}"
            raise
        finally:
            self._emit_trace(
                {
                    **(trace_context or {}),
                    "status": status,
                    "error": error,
                    "model": model,
                    "temperature": temperature,
                    "used_response_format_json_object": used_response_format,
                    "latency_ms": round((time.perf_counter() - start_time) * 1000, 3),
                    "usage": usage,
                    "system_prompt": _redact_secrets(system_prompt),
                    "user_prompt": _redact_secrets(user_prompt),
                    "raw_response": _redact_secrets(raw_content),
                    "parsed_output": parsed_output,
                }
            )

    def _emit_trace(self, payload: dict[str, Any]) -> None:
        if self.trace_hook is None:
            return
        self.trace_hook(payload)


def _parse_json_content(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", content, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        return json.loads(fenced.group(1))

    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(content[start : end + 1])

    raise ValueError(f"Model output is not valid JSON: {content}")


def _extract_usage(response: Any) -> dict[str, int]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return {}

    prompt_tokens = getattr(usage, "prompt_tokens", None)
    completion_tokens = getattr(usage, "completion_tokens", None)
    total_tokens = getattr(usage, "total_tokens", None)

    out: dict[str, int] = {}
    if isinstance(prompt_tokens, int):
        out["prompt_tokens"] = prompt_tokens
    if isinstance(completion_tokens, int):
        out["completion_tokens"] = completion_tokens
    if isinstance(total_tokens, int):
        out["total_tokens"] = total_tokens
    return out


def _redact_secrets(text: str) -> str:
    redacted = text
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED_OPENAI_KEY]", redacted)
    return redacted
