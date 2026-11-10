from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any

import requests

from tools._shared import TIMEOUT, USER_AGENT, check_public_url, clamp_int, domain, err

MAX_REDIRECTS = 3

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
        # Follow redirects by hand so every hop is checked: a public URL must not be able to
        # redirect the agent into localhost / the LAN (SSRF).
        url = feed_url
        for _ in range(MAX_REDIRECTS + 1):
            check_public_url(url)
            response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT, allow_redirects=False)
            if response.status_code in (301, 302, 303, 307, 308):
                from urllib.parse import urljoin
                url = urljoin(url, (getattr(response, "headers", None) or {}).get("Location", ""))
                continue
            break
        else:
            raise ValueError("too many redirects")
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
