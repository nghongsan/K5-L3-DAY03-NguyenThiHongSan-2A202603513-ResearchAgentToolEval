# v0 Failure Analysis (A gửi B)

- Run: `runs/v0_B_base_openai_20261110T102926436504.json`
- Artifact: `v0+pf0c107a9d7a1+t8db0ba629f52`. Provider `openai`, model `gpt-4o-mini`.
- Metric: case_accuracy **0.70** (14/20), tool_routing **0.75**, argument **0.70**, multiturn **1.00** (6/6).

Toàn bộ 6 case FAIL đều là single turn. Cả 6 case multi turn đều PASS.

## Các case FAIL

| Case | Loại lỗi | Input | Expected | Actual | Nguyên nhân gốc |
|---|---|---|---|---|---|
| R08_out_of_scope | out_of_scope | "nguyên hàm của x^2 là gì?" | no tool, từ chối | `send(text=đáp án)` | Prompt không có ranh giới phạm vi. Model dùng `send` làm kênh trả lời. |
| R14_out_of_scope_coding | out_of_scope | "Viết hàm Python Fibonacci" | no tool, từ chối | `send(text=code)` | Giống R08 |
| R10_missing_handle | missing_info | "Tóm tắt 5 tweet mới nhất" | `clarify(response_type=text)` | `timeline(screenname=sama)` | Prompt ra lệnh *"pick a well-known account like Sam Altman"* |
| R11_missing_url | missing_info | "Tóm tắt bài viết này" | `clarify(response_type=text)` | `fetch(url=https://example.com/article)` | Prompt ra lệnh *"assume a likely URL"* |
| R12_confirm_before_send | wrong_boundary | "Đăng bản tin này lên Telegram" | `clarify(response_type=yes_no)` | `send(text=...)` | Prompt ra lệnh *"just go ahead and do it"* |
| R13_parallel_web_and_tweets | wrong_arg_value* | "Tìm trên web tin AI hôm nay và tìm thêm tweet về AI" | `lookup(query=AI, topic=news, timeframe=day)` và `social_search(query=AI)` | `lookup(query="AI news", timeframe=day)` và `social_search(...)` | Chọn đúng 2 tool. Thiếu `topic=news`, và nhồi chữ "news" vào query. |

\* R13 có `failure_type` gốc là `wrong_tool`, nhưng mismatch quan sát được là `wrong_arg_value`: tool chọn đúng, sai ở args.

`send` không thật sự gửi tin nhắn nào. Tool tự chặn khi thiếu `confirmed=true` và trả về `status: needs_confirmation`.

## Nhóm theo nguyên nhân, gợi ý thứ tự sửa

| Nhóm | Case | Số case | Sửa ở đâu |
|---|---|---:|---|
| 1. Chỉ dẫn xấu cố ý trong prompt (đoán, gửi luôn) | R10, R11, R12 | 3 | `system_prompt.md` |
| 2. Không có ranh giới phạm vi, dùng `send` làm kênh trả lời | R08, R14 | 2 | `system_prompt.md` và mô tả `send` trong `tools.yaml` |
| 3. Quy ước args của `lookup` | R13 | 1 | Mô tả `topic`/`query` trong `tools.yaml` |

Gợi ý mỗi version một giả thuyết:
- **v1:** bỏ 3 chỉ dẫn xấu, thay bằng "thiếu thông tin thì `clarify`; hành động gửi phải hỏi yes_no trước". Kỳ vọng sửa R10, R11, R12, lên khoảng 0.85.
- **v2:** thêm ranh giới phạm vi: câu ngoài research (toán, code) thì trả lời bằng text, không gọi tool; `send` không phải kênh trả lời. Kỳ vọng sửa R08, R14, lên khoảng 0.95.
- **v3:** `tools.yaml`: hỏi tin tức thì `topic=news`, `query` chỉ giữ chủ đề (không thêm "news"/"tin"). Kỳ vọng sửa R13, đạt 1.00.

Sau mỗi version cần kiểm tra lại các case đang PASS, nhất là R09 (no tool) và M01 đến M06, để bắt regression.
