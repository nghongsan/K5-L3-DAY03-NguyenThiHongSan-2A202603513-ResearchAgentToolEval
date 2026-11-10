"""Tool Unit Test Challenge — filled in.

Offline only: HTTP is mocked with `fake_http`, keys are set with `monkeypatch.setenv`.
One behaviour per test; each test is named after the behaviour it checks.
"""
from __future__ import annotations

import requests

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

clarify = TOOL_FUNCTIONS["clarify"]
format_tool = TOOL_FUNCTIONS["format"]
send = TOOL_FUNCTIONS["send"]
lookup = TOOL_FUNCTIONS["lookup"]
fetch = TOOL_FUNCTIONS["fetch"]
timeline = TOOL_FUNCTIONS["timeline"]
social_search = TOOL_FUNCTIONS["social_search"]
policy = TOOL_FUNCTIONS["policy"]
wiki = TOOL_FUNCTIONS["wiki"]
hn_search = TOOL_FUNCTIONS["hn_search"]
github_repo = TOOL_FUNCTIONS["github_repo"]
rss = TOOL_FUNCTIONS["rss"]


def _set_twitter_env(monkeypatch) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "rk")
    monkeypatch.setenv("RAPIDAPI_TWITTER_HOST", "twitter-api45.p.rapidapi.com")


def _tweets(n: int, start: int = 1) -> list[dict]:
    return [{"tweet_id": str(i), "screen_name": "sama", "text": f"tweet {i}"} for i in range(start, start + n)]


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    result = clarify(question="Chọn nguồn?", response_type="choice", options=["web", "twitter"])
    assert result["options"] == ["web", "twitter"]
    assert result["response_type"] == "choice"
    assert result["awaiting_user"] is True


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "a1", "url": "https://x.com/1", "section": "A"},
        {"title": "b1", "url": "https://x.com/2", "section": "B"},
        {"title": "a2", "url": "https://x.com/3", "section": "A"},
    ]
    markdown = format_tool(items=items, template="sections")["markdown"]
    assert markdown.count("## A") == 1
    assert markdown.count("## B") == 1
    assert markdown.index("a2") < markdown.index("## B")  # a2 grouped under A, before B


def test_format_thread_numbers_items() -> None:
    items = [{"title": f"t{i}", "url": f"https://e.com/{i}"} for i in range(3)]
    lines = format_tool(items=items, template="thread")["markdown"].split("\n\n")
    assert [line.split(" ")[0] for line in lines] == ["1/", "2/", "3/"]


def test_format_empty_items_does_not_crash() -> None:
    assert format_tool(items=None, template="sections")["item_count"] == 0
    assert format_tool(items=[], template="brief")["item_count"] == 0


def test_format_item_without_url_shows_source_without_broken_link() -> None:
    markdown = format_tool(items=[{"title": "No link", "source": "internal"}], template="bullets")["markdown"]
    assert markdown == "- No link - internal"
    assert "]()" not in markdown


def test_format_empty_section_falls_back_to_default_heading() -> None:
    # Regression: section="" / None used to render an empty "## " or "## None" heading.
    items = [{"title": "x", "url": "https://e.com", "section": ""}, {"title": "y", "url": "https://e.com", "section": None}]
    markdown = format_tool(items=items, template="sections")["markdown"]
    assert "## Tổng hợp" in markdown
    assert "## None" not in markdown and "## \n" not in markdown


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-10042")
    calls = fake_http(FakeResponse({"ok": True}))

    result = send(text="Bản tin AI", confirmed=True)

    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert "bot123:abc/sendMessage" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "-10042"
    assert calls[0]["json"]["text"] == "Bản tin AI"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    result = send(text="x", confirmed=True)
    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]
    assert calls == []


def test_send_string_false_is_not_treated_as_confirmation(monkeypatch, fake_http) -> None:
    # Regression: bool("false") is True, so confirmed="false" from a sloppy model used to SEND.
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-10042")
    calls = fake_http(FakeResponse({"ok": True}))
    for value in ("false", "no", 0, None):
        assert send(text="x", confirmed=value)["status"] == "needs_confirmation"
    assert calls == []


def test_send_http_error_does_not_leak_bot_token(monkeypatch, fake_http) -> None:
    # Regression: requests' HTTPError message contains the request URL .../bot<TOKEN>/sendMessage,
    # which used to be copied verbatim into the error dict (and from there into transcripts / the UI).
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:SECRET-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-10042")
    fake_http(requests.HTTPError(
        "400 Client Error: Bad Request for url: https://api.telegram.org/bot123456:SECRET-token/sendMessage"))
    result = send(text="x", confirmed=True)
    assert result["error"] == "HTTPError"
    assert "SECRET-token" not in result["message"]
    assert "bot***/sendMessage" in result["message"]


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "k")
    calls = fake_http(FakeResponse({"results": []}))
    lookup(query="AI", timeframe=None)
    assert "time_range" not in calls[0]["json"]


def test_lookup_string_max_results_is_coerced_to_int(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "k")
    calls = fake_http(FakeResponse({"results": []}))
    lookup(query="AI", max_results="3")
    assert calls[0]["json"]["max_results"] == 3


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc")
    calls = fake_http(FakeResponse({"data": {
        "markdown": "# Hello\nbody",
        "metadata": {"title": "T", "sourceURL": "https://www.openai.com/research/"},
    }}))

    result = fetch(url="https://www.openai.com/research/")

    assert calls[0]["url"] == "https://api.firecrawl.dev/v1/scrape"
    assert calls[0]["json"]["url"] == "https://www.openai.com/research/"
    assert calls[0]["headers"]["Authorization"] == "Bearer fc"
    assert result["items"][0] == {
        "title": "T", "url": "https://www.openai.com/research/",
        "source": "openai.com", "summary": "# Hello\nbody",
    }


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc")
    fake_http(FakeResponse({"data": {"markdown": "x" * 9000, "metadata": {}}}))
    assert len(fetch(url="https://e.com")["items"][0]["summary"]) == 4000


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    _set_twitter_env(monkeypatch)
    raw = [{"screen_name": "sama", "text": "no id"}, *_tweets(6)]
    calls = fake_http(FakeResponse({"timeline": raw}))

    result = timeline(screenname="sama", limit=3)

    assert calls[0]["params"] == {"screenname": "sama"}
    assert len(result["items"]) == 3
    assert [item["url"] for item in result["items"]] == [f"https://x.com/sama/status/{i}" for i in (1, 2, 3)]


def test_timeline_negative_limit_does_not_drop_last_tweet(monkeypatch, fake_http) -> None:
    # Regression: items[:int(-1)] silently returned all-but-last. Now clamps to the default.
    _set_twitter_env(monkeypatch)
    fake_http(FakeResponse({"timeline": _tweets(3)}))
    assert len(timeline(screenname="sama", limit=-1)["items"]) == 3


def test_timeline_non_numeric_limit_uses_default(monkeypatch, fake_http) -> None:
    _set_twitter_env(monkeypatch)
    fake_http(FakeResponse({"timeline": _tweets(8)}))
    result = timeline(screenname="sama", limit="five")
    assert "error" not in result
    assert len(result["items"]) == 5


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    _set_twitter_env(monkeypatch)
    calls = fake_http(FakeResponse({"timeline": []}))
    social_search(query="OpenAI", search_type="Top")
    social_search(query="OpenAI", search_type="Latest")
    assert calls[0]["params"] == {"query": "OpenAI", "search_type": "Top"}
    assert calls[1]["params"]["search_type"] == "Latest"
    assert calls[0]["headers"]["x-rapidapi-key"] == "rk"


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    assert policy(query="")["results"] == []
    assert policy(query="   ")["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    results = policy(query="dữ liệu khách hàng API key", policy_area="data_privacy", top_k=5)["results"]
    assert results
    assert all(item["policy_area"] == "data_privacy" for item in results)


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    results = policy(query="injection probe citation", policy_area="source_citation", top_k=10)["results"]
    probe = next(item for item in results if item["section"] == "Injection probe")
    assert any(line.lower().startswith("assistant:") for line in probe["untrusted_text"])
    assert "assistant:" not in probe["facts"].lower()


# ---------------- NEW TOOL: wiki ----------------

def test_wiki_maps_search_pages_to_items(fake_http) -> None:
    calls = fake_http(FakeResponse({"pages": [
        {"key": "Trí_tuệ_nhân_tạo", "title": "Trí tuệ nhân tạo", "description": "lĩnh vực khoa học máy tính",
         "excerpt": "<span>Trí tuệ</span> nhân tạo"},
    ]}))

    result = wiki(query="trí tuệ nhân tạo", lang="vi", limit="2")

    assert calls[0]["url"] == "https://vi.wikipedia.org/w/rest.php/v1/search/page"
    assert calls[0]["params"] == {"q": "trí tuệ nhân tạo", "limit": 2}
    assert "User-Agent" in calls[0]["headers"]
    assert result["items"][0] == {
        "title": "Trí tuệ nhân tạo", "url": "https://vi.wikipedia.org/wiki/Trí_tuệ_nhân_tạo",
        "source": "vi.wikipedia.org", "summary": "lĩnh vực khoa học máy tính",
    }


def test_wiki_bad_input_from_model(fake_http) -> None:
    calls = fake_http(FakeResponse({"pages": [{"key": "AI", "title": "AI", "excerpt": "<b>AI</b> is"}]}))
    assert wiki(query="   ")["error"] == "ValueError"      # empty query -> error dict, no request
    assert calls == []
    result = wiki(query="AI", lang="fr", limit=0)           # out-of-enum lang, zero limit
    assert calls[0]["url"].startswith("https://vi.wikipedia.org")
    assert calls[0]["params"]["limit"] == 3
    assert result["items"][0]["summary"] == "AI is"         # HTML stripped from excerpt fallback


def test_wiki_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=503))
    assert wiki(query="AI")["error"] == "HTTPError"


# ---------------- NEW TOOL: hn_search ----------------

def test_hn_search_date_sort_uses_search_by_date_and_maps_hits(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": [
        {"objectID": "1", "title": "Show HN: X", "url": "https://x.dev", "points": 120, "num_comments": 30},
        {"objectID": "2", "title": "Ask HN: Y?", "url": None, "points": 5, "num_comments": 2},
        {"title": "no id"},
    ]}))

    result = hn_search(query="LLM agents", sort_by="date", limit=5)

    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search_by_date"
    assert calls[0]["params"] == {"query": "LLM agents", "tags": "story", "hitsPerPage": 5}
    assert len(result["items"]) == 2
    assert result["items"][0]["summary"] == "120 points · 30 comments"
    assert result["items"][1]["url"] == "https://news.ycombinator.com/item?id=2"  # Ask HN -> discussion link


def test_hn_search_bad_input_from_model(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))
    assert hn_search(query="")["error"] == "ValueError"
    assert calls == []
    hn_search(query="rust", sort_by="popular", limit="100")
    assert calls[0]["url"].endswith("/search")          # unknown sort -> relevance
    assert calls[0]["params"]["hitsPerPage"] == 20       # clamped


def test_hn_search_network_error_returns_error_dict(fake_http) -> None:
    fake_http(requests.ConnectionError("down"))
    result = hn_search(query="x")
    assert result["error"] == "ConnectionError"


# ---------------- NEW TOOL: github_repo ----------------

def test_github_repo_accepts_url_and_maps_metadata(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
    calls = fake_http(FakeResponse({
        "full_name": "openai/openai-python", "html_url": "https://github.com/openai/openai-python",
        "description": "Python SDK", "stargazers_count": 25000, "forks_count": 3000,
        "open_issues_count": 50, "language": "Python", "license": {"spdx_id": "Apache-2.0"},
        "pushed_at": "2026-11-01T00:00:00Z", "archived": False,
    }))

    result = github_repo(repo="https://github.com/openai/openai-python.git")

    assert calls[0]["url"] == "https://api.github.com/repos/openai/openai-python"
    assert calls[0]["headers"]["Authorization"] == "Bearer ghp_test"
    item = result["items"][0]
    assert result["repo"] == "openai/openai-python"
    assert (item["stars"], item["license"], item["language"]) == (25000, "Apache-2.0", "Python")


def test_github_repo_bad_input_from_model_makes_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({}))
    for bad in ("", "openai", "@openai/openai-python", "https://gitlab.com/a/b", "a/b/c"):
        assert github_repo(repo=bad)["error"] == "ValueError", bad
    assert calls == []


def test_github_repo_404_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=404))
    result = github_repo(repo="nobody/nothing")
    assert result["error"] == "HTTPError"
    assert "404" in result["message"]


# ---------------- NEW TOOL: rss ----------------

RSS_XML = """<?xml version="1.0"?><rss version="2.0"><channel><title>Blog</title>
<item><title>Post 1</title><link>https://blog.example.com/1</link><description>&lt;p&gt;Hello&lt;/p&gt;</description><pubDate>Mon, 09 Nov 2026</pubDate></item>
<item><title>Post 2</title><link>https://blog.example.com/2</link></item>
<item><title>Post 3</title><link>https://blog.example.com/3</link></item>
</channel></rss>"""

ATOM_XML = """<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><title>Atom A</title><link href="https://atom.example.com/a"/><summary>sum</summary><updated>2026-11-09</updated></entry>
</feed>"""


def test_rss_parses_rss2_items_and_respects_limit(fake_http) -> None:
    calls = fake_http(FakeResponse(text=RSS_XML))
    result = rss(feed_url="https://blog.example.com/feed", limit=2)
    assert calls[0]["url"] == "https://blog.example.com/feed"
    assert [item["title"] for item in result["items"]] == ["Post 1", "Post 2"]
    assert result["items"][0]["summary"] == "Hello"
    assert result["items"][0]["source"] == "blog.example.com"


def test_rss_parses_atom_entries(fake_http) -> None:
    fake_http(FakeResponse(text=ATOM_XML))
    item = rss(feed_url="https://atom.example.com/feed.atom")["items"][0]
    assert (item["title"], item["url"], item["published"]) == ("Atom A", "https://atom.example.com/a", "2026-11-09")


def test_rss_bad_input_from_model_makes_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse(text=RSS_XML))
    assert rss(feed_url="")["error"] == "ValueError"
    assert rss(feed_url="blog.example.com/feed")["error"] == "ValueError"
    assert calls == []


def test_rss_invalid_xml_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(text="<html>not a feed"))
    assert rss(feed_url="https://e.com/feed")["error"] == "ParseError"
