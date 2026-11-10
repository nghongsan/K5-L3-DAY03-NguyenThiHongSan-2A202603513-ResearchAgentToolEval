from __future__ import annotations

import re
from typing import Any

import requests

from tools._shared import TIMEOUT, USER_AGENT, clamp_int, err

LANGS = {"vi", "en"}


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def wiki_search(query: str = "", lang: str = "vi", limit: int = 3) -> dict[str, Any]:
    """Search Wikipedia and return short encyclopedic summaries (no API key)."""
    try:
        query = (query or "").strip()
        if not query:
            raise ValueError("query must not be empty")
        lang = lang if lang in LANGS else "vi"
        limit = clamp_int(limit, 3, 1, 10)
        response = requests.get(
            f"https://{lang}.wikipedia.org/w/rest.php/v1/search/page",
            params={"q": query, "limit": limit},
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        pages = response.json().get("pages") or []
        items = [{
            "title": page.get("title"),
            "url": f"https://{lang}.wikipedia.org/wiki/{page.get('key')}",
            "source": f"{lang}.wikipedia.org",
            "summary": page.get("description") or _strip_html(page.get("excerpt", "")),
        } for page in pages if page.get("key")]
        return {"tool": "wiki_search", "query": query, "lang": lang, "items": items[:limit]}
    except Exception as exc:
        return err("wiki_search", exc)
