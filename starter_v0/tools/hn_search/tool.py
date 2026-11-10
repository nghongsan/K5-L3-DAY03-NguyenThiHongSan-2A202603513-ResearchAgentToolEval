from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, clamp_int, err


def hn_search(query: str = "", sort_by: str = "relevance", limit: int = 5) -> dict[str, Any]:
    """Search Hacker News stories via the Algolia API (no API key)."""
    try:
        query = (query or "").strip()
        if not query:
            raise ValueError("query must not be empty")
        sort_by = sort_by if sort_by in {"relevance", "date"} else "relevance"
        limit = clamp_int(limit, 5, 1, 20)
        endpoint = "search_by_date" if sort_by == "date" else "search"
        response = requests.get(
            f"https://hn.algolia.com/api/v1/{endpoint}",
            params={"query": query, "tags": "story", "hitsPerPage": limit},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        items = []
        for hit in response.json().get("hits") or []:
            story_id = hit.get("objectID")
            if not story_id:
                continue
            discussion = f"https://news.ycombinator.com/item?id={story_id}"
            items.append({
                "title": hit.get("title"),
                "url": hit.get("url") or discussion,
                "source": "news.ycombinator.com",
                "summary": f"{hit.get('points') or 0} points · {hit.get('num_comments') or 0} comments",
                "discussion_url": discussion,
                "created_at": hit.get("created_at"),
            })
        return {"tool": "hn_search", "query": query, "sort_by": sort_by, "items": items[:limit]}
    except Exception as exc:
        return err("hn_search", exc)
