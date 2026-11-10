from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
TIMEOUT = 30


def err(tool: str, exc: Exception) -> dict[str, Any]:
    return {"tool": tool, "error": type(exc).__name__, "message": str(exc)}


def domain(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def fold_text(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def terms(text: str) -> set[str]:
    stopwords = {
        "a", "an", "and", "are", "as", "at", "by", "for", "from", "in", "is", "of", "on", "or", "the", "to",
        "ban", "bao", "can", "cho", "co", "cua", "duoc", "gi", "giup", "la", "lam", "minh", "mot", "nay",
        "nen", "the", "thi", "trong", "va", "ve", "voi",
    }
    folded = fold_text(text)
    return {term for term in re.findall(r"[a-z0-9]+", folded) if len(term) > 1 and term not in stopwords}



def clamp_int(value: Any, default: int, lo: int, hi: int) -> int:
    """Coerce model-sent numbers ("5", 5.0, None, 0) into a safe int range."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    if number < lo:
        number = default if number <= 0 else lo
    return min(number, hi)


USER_AGENT = "AI20k-Day03-Research-Agent/1.0 (educational lab)"


def resolve_host(host: str) -> list[str]:
    """All IP addresses a hostname resolves to (separate function so tests can stub DNS)."""
    import socket
    return sorted({info[4][0] for info in socket.getaddrinfo(host, None)})


def check_public_url(url: str) -> str:
    """Raise ValueError unless `url` is http(s) and every address it resolves to is public.

    Blocks SSRF: a user of the public demo must not be able to make the agent fetch
    localhost, the LAN (router admin pages), link-local cloud metadata (169.254.x.x), etc.
    """
    import ipaddress
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("feed_url must be an http(s) URL")
    host = parsed.hostname
    try:
        addresses = [str(ipaddress.ip_address(host))]
    except ValueError:
        addresses = resolve_host(host)
    if not addresses:
        raise ValueError(f"cannot resolve host {host}")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global or ip.is_multicast:
            raise ValueError(f"blocked non-public address for {host}")
    return url
