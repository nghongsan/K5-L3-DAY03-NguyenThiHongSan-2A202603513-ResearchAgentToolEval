from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any

import requests

from tools._shared import TIMEOUT, USER_AGENT, clamp_int, domain, err

ATOM = "{http://www.w3.org/2005/Atom}"


def _text(node: ET.Element | None) -> str:
    return re.sub(r"<[^>]+>", "", (node.text or "") if node is not None else "").strip()


def read_rss(feed_url: str = "", limit: int = 5) -> dict[str, Any]:
    """Read the newest entries of an RSS 2.0 or Atom feed URL (no API key)."""
    try:
        feed_url = (feed_url or "").strip()
        if not feed_url.startswith(("http://", "https://")):
            raise ValueError("feed_url must be an http(s) URL")
        limit = clamp_int(limit, 5, 1, 20)
        response = requests.get(feed_url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        response.raise_for_status()
        root = ET.fromstring(response.text)
        items: list[dict[str, Any]] = []
        for node in root.iter("item"):
            items.append({
                "title": _text(node.find("title")),
                "url": _text(node.find("link")),
                "summary": _text(node.find("description"))[:500],
                "published": _text(node.find("pubDate")),
            })
        for node in root.iter(f"{ATOM}entry"):
            link = node.find(f"{ATOM}link")
            items.append({
                "title": _text(node.find(f"{ATOM}title")),
                "url": link.get("href", "") if link is not None else "",
                "summary": _text(node.find(f"{ATOM}summary"))[:500],
                "published": _text(node.find(f"{ATOM}updated")),
            })
        for item in items:
            item["source"] = domain(item["url"]) or domain(feed_url)
        return {"tool": "read_rss", "feed_url": feed_url, "items": items[:limit]}
    except Exception as exc:
        return err("read_rss", exc)
