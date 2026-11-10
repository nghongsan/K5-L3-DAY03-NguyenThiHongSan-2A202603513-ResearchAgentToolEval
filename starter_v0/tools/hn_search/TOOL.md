---
name: hn_search
track: bonus
kind: live_api
provider: Hacker News Algolia API
requires_env: []
inputs: [query, sort_by, limit]
outputs: [items]
side_effect: false
---
# hn_search

Tìm story trên Hacker News (cộng đồng dev/startup) qua Algolia API. `sort_by=relevance`
cho bài nổi bật, `date` cho bài mới nhất. Mỗi item có link bài gốc + link thảo luận HN.
Không cần API key.

Guardrails: query rỗng → error dict; `sort_by` lạ → `relevance`; `limit` ép về 1..20;
hit thiếu `objectID` bị bỏ qua; hit không có `url` (Ask HN) dùng link thảo luận.
