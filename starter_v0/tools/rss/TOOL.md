---
name: rss
track: bonus
kind: live_api
provider: any RSS 2.0 / Atom feed
requires_env: []
inputs: [feed_url, limit]
outputs: [items]
side_effect: false
---
# rss

Đọc các bài mới nhất từ MỘT feed RSS 2.0 hoặc Atom khi user đưa URL feed
(thường kết thúc bằng `/feed`, `/rss`, `.xml`, `.atom`). Không cần API key.

Guardrails: URL không phải http(s) → error dict, không gọi mạng; XML lỗi → error dict;
`limit` ép về 1..20.
