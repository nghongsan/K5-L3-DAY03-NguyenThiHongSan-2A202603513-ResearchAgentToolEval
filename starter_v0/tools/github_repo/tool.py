from __future__ import annotations

import os
import re
from typing import Any

import requests

from tools._shared import TIMEOUT, USER_AGENT, err

_REPO_RE = re.compile(r"^(?:https?://(?:www\.)?github\.com/)?([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?/?$")


def parse_repo(repo: str) -> tuple[str, str]:
    match = _REPO_RE.match((repo or "").strip())
    if not match:
        raise ValueError("repo must look like 'owner/name' or https://github.com/owner/name")
    return match.group(1), match.group(2)


def github_repo(repo: str = "") -> dict[str, Any]:
    """Get public metadata for one GitHub repository (GITHUB_TOKEN optional)."""
    try:
        owner, name = parse_repo(repo)
        headers = {"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = requests.get(f"https://api.github.com/repos/{owner}/{name}", headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        item = {
            "title": data.get("full_name") or f"{owner}/{name}",
            "url": data.get("html_url") or f"https://github.com/{owner}/{name}",
            "source": "github.com",
            "summary": data.get("description") or "",
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "open_issues": data.get("open_issues_count"),
            "language": data.get("language"),
            "license": (data.get("license") or {}).get("spdx_id"),
            "pushed_at": data.get("pushed_at"),
            "archived": data.get("archived"),
        }
        return {"tool": "github_repo", "repo": f"{owner}/{name}", "items": [item]}
    except Exception as exc:
        return err("github_repo", exc)
