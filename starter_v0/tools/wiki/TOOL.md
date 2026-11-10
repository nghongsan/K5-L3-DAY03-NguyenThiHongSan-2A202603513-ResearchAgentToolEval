---
name: wiki
track: bonus
kind: live_api
provider: Wikipedia REST API
requires_env: []
inputs: [query, lang, limit]
outputs: [items]
side_effect: false
---
# wiki

Tìm trên Wikipedia (`vi` hoặc `en`) và trả về tiêu đề, URL, mô tả ngắn.
Dùng cho câu hỏi khái niệm/định nghĩa/lý lịch ("X là gì", "ai là Y") — kiến thức ổn định,
không phải tin tức mới. Không cần API key.

Guardrails: query rỗng → error dict; `lang` ngoài enum → `vi`; `limit` bị ép về 1..10
(chuỗi `"5"` được chấp nhận, `0`/âm → mặc định 3).
