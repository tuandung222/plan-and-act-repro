from __future__ import annotations

import html
import re
import urllib.parse
import urllib.request
from typing import Any


def _strip_html(text: str) -> str:
    text = re.sub(r"<script[\\s\\S]*?</script>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<style[\\s\\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\\s+", " ", text).strip()
    return text


def parse_duckduckgo_results(html_text: str, max_results: int) -> list[dict[str, str]]:
    pattern = re.compile(
        r'<a[^>]+class="[^"]*result__a[^"]*"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
        flags=re.IGNORECASE | re.DOTALL,
    )

    items: list[dict[str, str]] = []
    for href, title_html in pattern.findall(html_text):
        title = _strip_html(title_html)
        resolved_url = href

        parsed = urllib.parse.urlparse(href)
        if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
            qs = urllib.parse.parse_qs(parsed.query)
            uddg = qs.get("uddg", [""])[0]
            if uddg:
                resolved_url = urllib.parse.unquote(uddg)

        items.append({"title": title, "url": resolved_url})
        if len(items) >= max_results:
            break

    return items


class WebSearchTool:
    """Simple no-key web search via DuckDuckGo HTML endpoint."""

    name = "web_search"

    def __init__(self, *, user_agent: str = "plan-and-act-repro") -> None:
        self.user_agent = user_agent

    def run(self, arguments: dict[str, Any]) -> dict[str, Any]:
        query = str(arguments.get("query", "")).strip()
        if not query:
            return {"ok": False, "error": "Missing query"}

        max_results = int(arguments.get("max_results", 5))
        max_results = max(1, min(max_results, 10))

        q = urllib.parse.quote_plus(query)
        url = f"https://duckduckgo.com/html/?q={q}"
        req = urllib.request.Request(
            url=url,
            headers={"User-Agent": self.user_agent},
            method="GET",
        )

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                payload = resp.read().decode("utf-8", errors="replace")
        except Exception as exc:  # pragma: no cover - network variability
            return {
                "ok": False,
                "query": query,
                "error": str(exc),
            }

        results = parse_duckduckgo_results(payload, max_results)
        return {
            "ok": True,
            "query": query,
            "count": len(results),
            "results": results,
        }


class FetchURLTool:
    """Fetch URL content and return compact text summary without API key."""

    name = "fetch_url"

    def __init__(self, *, user_agent: str = "plan-and-act-repro") -> None:
        self.user_agent = user_agent

    def run(self, arguments: dict[str, Any]) -> dict[str, Any]:
        url = str(arguments.get("url", "")).strip()
        if not url:
            return {"ok": False, "error": "Missing url"}

        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return {
                "ok": False,
                "url": url,
                "error": "Only http/https URLs are supported",
            }

        max_chars = int(arguments.get("max_chars", 1200))
        max_chars = max(200, min(max_chars, 8000))

        req = urllib.request.Request(
            url=url,
            headers={"User-Agent": self.user_agent},
            method="GET",
        )

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                status = getattr(resp, "status", 200)
                final_url = resp.geturl()
                payload = resp.read().decode("utf-8", errors="replace")
        except Exception as exc:  # pragma: no cover - network variability
            return {
                "ok": False,
                "url": url,
                "error": str(exc),
            }

        title_match = re.search(r"<title[^>]*>(.*?)</title>", payload, flags=re.IGNORECASE | re.DOTALL)
        title = _strip_html(title_match.group(1)) if title_match else ""
        text = _strip_html(payload)

        return {
            "ok": True,
            "url": url,
            "status": status,
            "final_url": final_url,
            "title": title,
            "content_preview": text[:max_chars],
            "content_length": len(text),
        }
