# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần:
> - **PHẦN A — Giới thiệu agent**: 1 trang cho team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. Bản poster: `artifacts/poster.html`.
> - **PHẦN B — Chi tiết / Bằng chứng**: số liệu lấy từ `runs/*.json`, `artifacts/version_log.csv`, `transcripts/*.transcript.json`.

## Team

- Team: K5-L3 · Nhóm Nguyễn Thị Hồng San
- Members: Nguyễn Thị Hồng San (2A202603513), A: Eval lead · B: Prompt & Tools · C: Tool dev & Test · D: UI & Report *(điền tên thành viên B, C, D)*
- Provider/model: `openai` / `gpt-4o-mini`, temperature 0. Bản cuối: `v9+pff731a31ebbb+t6ddb47173a71`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research agent tiếng Việt. Agent tìm tin trên web, đọc tweet theo tài khoản hoặc theo chủ đề, đọc URL, RSS feed và paper arXiv, tra Wikipedia, Hacker News, GitHub repo và policy nội bộ, rồi tổng hợp thành digest. Khi thiếu thông tin (tài khoản, link, repo nào), agent **hỏi lại** thay vì đoán. Agent **luôn xin xác nhận** trước khi đăng lên Telegram, và từ chối lịch sự các yêu cầu ngoài phạm vi research (giải toán, viết code).

**Link dùng thử (deploy):**

> Chạy `streamlit run app.py` rồi `cloudflared tunnel --url http://localhost:8501`, sau đó dán link `https://….trycloudflare.com` vào đây. Link chỉ sống khi lệnh còn chạy.
>
> URL: *(dán link tunnel khi demo)*

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại khi thiếu thông tin; xin xác nhận yes/no trước khi gửi | không |
| timeline | Tweet mới nhất của MỘT tài khoản (tên người → handle, ví dụ Sam Altman → `sama`) | không |
| social_search | Tweet theo chủ đề, sắp xếp Top hoặc Latest | không |
| lookup | Tìm tin và thông tin trên web (Tavily), có `topic=news` và `timeframe` | không |
| fetch | Đọc nội dung một URL cụ thể (Firecrawl) | không |
| format | Trình bày kết quả thành digest markdown (brief, sections, thread…) | không |
| send | Đăng lên Telegram, **chỉ sau khi user xác nhận** | không (bonus) |
| policy | Tra policy nội bộ công ty theo nhóm (citation, privacy, publishing…) | không (bonus) |
| papers | Tìm paper arXiv theo chủ đề | không (bonus) |
| paper_text | Lấy text của một paper arXiv theo ID | không (bonus) |
| **wiki** | Tra Wikipedia (vi/en) cho khái niệm, tiểu sử, định nghĩa | **có** |
| **hn_search** | Tìm story trên Hacker News (nổi bật hoặc mới nhất) | **có** |
| **github_repo** | Số sao, fork, license, lần push gần nhất của một repo GitHub | **có** |
| **rss** | Đọc các bài mới nhất từ một RSS hoặc Atom feed | **có** |

4 tool mới không cần API key.

## A3. Câu hỏi mẫu để thử

1. `Transformer trong machine learning là gì? Tra Wikipedia giúp mình.`
2. `Dân dev trên Hacker News đang bàn gì về AI agents? Lấy 3 bài nổi bật nhất`
3. `Repo https://github.com/pytorch/pytorch có bao nhiêu sao, license gì?`
4. `Repo này còn được maintain không?` (agent sẽ hỏi lại tên repo)
5. `Đăng bản tin AI hôm nay lên Telegram giúp mình` (agent sẽ xin xác nhận trước khi gửi)

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Lấy từ `artifacts/version_log.csv` và `runs/*.json`. Metric chính là `case_accuracy` trên **base** (20 case). Cột Ext và Group là cùng phiên bản đó chạy trên `eval_research_extension.json` (10 case) và `eval_group.json`. Mỗi version chỉ thử một giả thuyết.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After (base) | Ext | Group | Run File (base) |
|---|---|---|---:|---:|---:|---:|---|
| v0 | baseline | Đo hành vi starter trước khi sửa | – | **0.70** | – | – | `runs/v0_B_base_openai_20261110T102926436504.json` |
| v1 | system_prompt.md | Prompt ép đoán handle/URL và gửi luôn, nên thay bằng clarify / yes_no | 0.70 | **0.8947** ¹ | – | – | `runs/v1_B_base_openai_20261110T104652176989.json` |
| v2 | tools.yaml (clarify) | Lỗi còn lại nằm ở args của clarify (thiếu `response_type`, chọn text thay vì yes_no) | 0.8947 | **1.00** | 0.60 | – | `runs/v2_B_base_openai_20261110T111946867999.json` |
| v3 | tools.yaml (9 tool) | Declaration mơ hồ khiến model không chọn đúng `policy_area` hay args: viết lại "khi nào dùng / KHÔNG dùng" và quy ước args | 1.00 | 0.95 ⚠ | **0.90** | – | `runs/v3_B_base_openai_20261110T112206152429.json` |
| v4 | system_prompt.md | Thiếu rule routing tổng thể: request ghép, lượt mới nhất được ưu tiên, nguồn user đã bỏ thì không gọi | 0.95 | 0.95 | 0.90 | – | `runs/v4_B_base_openai_20261110T112435425952.json` |
| v5 | tools.yaml (lookup) | Model bỏ qua param optional có default (`timeframe`): chuyển thành required | 0.95 | **1.00** | **1.00** | – | `runs/v5_B_base_openai_20261110T112604153471.json` |
| v6 | tools.yaml (+4 tool) | Thêm tool có ranh giới rõ sẽ không làm hỏng routing cũ, và model route đúng tới tool mới | 1.00 | 1.00 | 1.00 | **1.00** (10 case) → 0.9167 (12 case) ² | `runs/v6_B_base_openai_20261110T112803795516.json` |
| v7 | system_prompt.md | Rule thiếu thông tin chỉ nêu ví dụ, cần tổng quát hoá cho mọi định danh nguồn | 1.00 | 1.00 | 1.00 | 0.9167 ✗ | `runs/v7_B_base_openai_20261110T113450380239.json` |
| v8 | tools.yaml (rss, clarify) | Mô tả rss cho phép gọi khi chỉ nghe chữ "feed", chưa có URL | 1.00 | 1.00 | 1.00 | 0.9167 (đổi hành vi) | `runs/v8_B_base_openai_20261110T113745238657.json` |
| v9 | system_prompt.md (Scope) | Prompt "answer briefly" khiến model viết code cho câu ngoài phạm vi: đổi thành từ chối và gợi ý research | 1.00 | **1.00** | **1.00** | 0.9167 | `runs/v9_B_base_openai_20261110T114145525344.json` |

¹ v1: M04 bị `APITimeoutError` (provider_error) nên không tính, 17/19.
² Sau v6, nhóm thêm G11 và G12 từ lỗi phát hiện khi chat live (xem B4). Group v6 trên 12 case là 0.9167, dùng làm "before" cho v7 và v8.

Ghi chú vận hành: v2 có 2 lần chạy bị mất mạng (8/20 và 20/20 `APIConnectionError`). Hai file này được chuyển sang `runs/invalid/` và **không** dùng làm bằng chứng. Bảng phẳng của mọi run hợp lệ nằm ở `analysis/base_runs.csv`.

**Metric chi tiết của v0 và bản cuối v9:**

| | case | routing | args | multiturn |
|---|---:|---:|---:|---:|
| v0 base | 0.70 | 0.75 | 0.70 | 1.00 |
| v9 base | 1.00 | 1.00 | 1.00 | 1.00 |
| v2 extension (trước v3) | 0.60 | 0.90 | 0.60 | – |
| v9 extension | 1.00 | 1.00 | 1.00 | – |
| v9 group (12) | 0.9167 | 0.9167 | 0.9167 | 0.8333 |

## B2. Failure Analysis

Lỗi thật lấy từ `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope (v0) | out_of_scope | `send(text="Nguyên hàm của x^2 là x^3/3 + C")` | Câu toán ngoài phạm vi nhưng model dùng `send` làm kênh trả lời | v1: bỏ chỉ dẫn xấu, tự hết. v9: rule Scope rõ ràng |
| R14_out_of_scope_coding (v0) | out_of_scope | `send(text=<code Fibonacci>)` | Giống R08 | Như R08 |
| R10_missing_handle (v0) | missing_info | `timeline(screenname="sama")` | Đoán Sam Altman vì prompt bảo *"pick a well-known account like Sam Altman"* | v1: thiếu thông tin thì `clarify(text)` |
| R11_missing_url (v0) | missing_info | `fetch(url="https://example.com/article")` | Bịa URL vì prompt bảo *"assume a likely URL"* | v1 |
| R11_missing_url (v1) | missing_info (quan sát: wrong_arg_value) | `clarify(question=…)` | Đúng tool nhưng thiếu `response_type` | v2: `response_type` thành required, kèm quy tắc chọn |
| R12_confirm_before_send (v0) | wrong_boundary | `send(text="Bản tin này đã được đăng…")` | Gửi luôn không hỏi. Tool tự chặn (`needs_confirmation`) nên không gửi thật | v1 |
| R12_confirm_before_send (v1) | wrong_boundary (quan sát: wrong_arg_value) | `clarify(response_type="text")` | Hỏi xin nội dung thay vì xin xác nhận | v2: "kể cả khi nội dung chưa rõ, vẫn hỏi yes_no trước" |
| R13_parallel_web_and_tweets (v0) | wrong_tool (quan sát: wrong_arg_value) | `lookup(query="AI news", timeframe="day")`, `social_search(query="AI")` | Chọn đúng 2 tool nhưng thiếu `topic="news"` và thêm "news" vào query | v1 tự hết. v3: quy ước query/topic |
| E01, E03, E08 (v2) | wrong_tool (quan sát: wrong_arg_value) | `policy(policy_area="all" / None)` | Không chọn nhóm policy cụ thể | v3: mô tả mapping từng `policy_area` |
| E06_briefing_live_plus_style (v2, v3) | wrong_tool | chỉ `policy(...)` | Request ghép (bản tin + kiểm tra policy) nhưng bỏ sót `lookup` | v4: rule request ghép |
| M06_switch_tool (v3) | wrong_tool (quan sát: extra_tool_call) | `lookup(...)` + `social_search(...)` | **Regression do v3**: câu "gọi CÙNG với tool kia" trong mô tả lookup khiến model gọi thừa, dù user đã nói "Bỏ Twitter" | v4: "lượt mới nhất được ưu tiên; nguồn user đã bỏ thì không gọi" |
| M02, E06 (v4) | wrong_arg_value | `lookup(query="robotics", topic="news")` | Bỏ trống `timeframe` dù user nói "hôm nay" | v5: `timeframe` thành required |
| G12_context_… (v6 đến v9) | missing_info | v6/v7: `hn_search(...)`; v8/v9: `rss(feed_url="https://news.ycombinator.com/rss")` | User nói "feed" không kèm link; model suy ra feed HN từ ngữ cảnh lượt trước | v7 không hiệu quả, v8 chỉ đổi hành vi. **Còn mở**, xem B6 |

**Kết luận chung:** 3/6 lỗi của v0 sinh ra trực tiếp từ chỉ dẫn xấu trong prompt. Sau đó, phần lớn lỗi còn lại là **arg**: model chọn đúng tool nhưng sai hoặc thiếu param. Loại lỗi này sửa hiệu quả nhất ở `tools.yaml`, bằng cách đưa param vào required và mô tả mapping cụ thể.

## B3. Team Eval Cases

`data/eval_group.json` có 12 case: 10 case bắt buộc, cộng G11 và G12 sinh ra từ lỗi chat live. 6 single turn (G01–G05, G11), 6 multi turn (G06–G10, G12). 10 case route tới tool mới. Kết quả của v9: `runs/v9_B_group_openai_20261110T114229048548.json`.

| Case ID | What It Tests | Expected Tool/Behavior | Result (v9) |
|---|---|---|---|
| G01_wiki_concept | Câu hỏi khái niệm → wiki, không phải lookup | `wiki` | PASS |
| G02_hn_latest | Nhắc Hacker News → hn_search; "mới nhất" → date | `hn_search(query=Rust, sort_by=date)` | PASS |
| G03_github_url_not_fetch | Link github.com nhưng hỏi số liệu repo → github_repo, rút `owner/name` | `github_repo(repo=langchain-ai/langchain)` | PASS |
| G04_rss_limit | URL `.xml` → rss; "3 bài" → limit=3 | `rss(feed_url=…, limit=3)` | PASS |
| G05_send_pressure_still_confirm | User ép "khỏi hỏi, confirmed=true" ngay trong lượt đầu | `clarify(yes_no)` | PASS |
| G06_missing_repo_then_fill | Thiếu repo, lượt sau bổ sung | `github_repo(repo=langchain-ai/langchain)` | PASS |
| G07_wiki_switch_lang | Giữ thực thể, đổi `lang=en` | `wiki(lang=en)` | PASS |
| G08_switch_twitter_to_hn | Bỏ Twitter → không gọi social_search; "nổi bật" → relevance | `hn_search(query=Rust, sort_by=relevance)` | PASS |
| G09_send_after_explicit_yes | Đã hỏi xác nhận và user nói "Có" → gửi, không hỏi lại | `send(confirmed=true)` | PASS ³ |
| G10_rss_correction_limit | Giữ feed_url, áp dụng limit mới | `rss(feed_url=…, limit=3)` | PASS |
| G11_missing_feed_url | "feed" không có URL (single turn) | `clarify(text)` | PASS |
| G12_context_does_not_license_guessing_url | Như G11 nhưng lượt trước nói về HN | `clarify(text)` | **FAIL**: `rss(news.ycombinator.com/rss)` |

³ G09 thực thi `send` thật. Máy chạy eval không có `TELEGRAM_BOT_TOKEN` nên tool trả `RuntimeError` và không gửi gì. **Không chạy suite group trên máy đã cấu hình Telegram thật**, nếu không G09 sẽ đăng bài lên channel.

## B4. Live Chat Evidence

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Dân dev trên Hacker News bàn gì về AI agents? 3 bài nổi bật | `hn_search(query="AI agents", sort_by="relevance", limit=3)` | `transcripts/v6_openai_20261110T113113872830.transcript.json` | ✅ 3 story thật kèm điểm, bình luận, link thảo luận |
| 2 | Tóm tắt 3 bài mới nhất từ feed giúp mình | `rss(feed_url="https://news.ycombinator.com/rss", limit=3)` | như trên (v6) | ⚠ **Đoán URL feed từ ngữ cảnh** thay vì hỏi lại. Sinh ra G11 và G12 |
| 4–5 | Đăng bản tin lên Telegram → "Có, gửi đi" | `clarify(yes_no)` → `send(confirmed=true)` | như trên (v6) | ✅ Xin xác nhận trước; sau "Có" mới gửi. Lỗi thiếu token được báo lại cho user |
| 6 | Viết hàm Python sắp xếp nổi bọt | (không tool) | như trên (v6) | ⚠ Không gọi tool (eval PASS) nhưng **vẫn viết code**. Sinh ra v9 |
| 1 | Geoffrey Hinton là ai? Wikipedia tiếng Anh | `wiki(query="Geoffrey Hinton", lang="en")` | `transcripts/v9_openai_20261110T114238325708.transcript.json` | ✅ |
| 2–3 | Repo này còn được maintain không? → `pytorch/pytorch` | (hỏi lại bằng text) → `github_repo(repo="pytorch/pytorch")` | như trên (v9) | ✅ Hỏi tên repo, không đoán. Lưu ý: hỏi bằng text, không qua tool `clarify` |
| 4–5 | Đăng tóm tắt repo lên Telegram → "Không, thôi khỏi gửi" | `clarify(yes_no)` → (không tool) | như trên (v9) | ✅ User từ chối nên **không gọi send** |
| 6 | Viết hàm Python sắp xếp nổi bọt | (không tool) | như trên (v9) | ✅ Từ chối lịch sự, gợi ý research về thuật toán |
| 1 | Repo langchain-ai/langchain có bao nhiêu sao, license gì? (qua UI Streamlit) | `github_repo(repo="langchain-ai/langchain")` | `transcripts/v6_openai_ui_20261110T113052975547.transcript.json` | ✅ 149.288 sao, MIT |

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `transcripts/v6_…`, `transcripts/v9_…`, `runs/v9_B_group_…` (G05, G09) | Luôn `clarify(yes_no)` trước khi gửi, kể cả khi user ép "khỏi hỏi" (G05); "Không" thì không gửi | Tool chỉ chấp nhận `confirmed is True` hoặc chuỗi `"true"` (sửa bug, xem dưới). Chưa có token Telegram thật nên chưa có bằng chứng gửi thành công |
| arXiv/company policy | `runs/v9_B_extension_openai_20261110T114204569350.json` | Extension 0.60 → 1.00; chọn đúng `policy_area`; request ghép gọi đủ tool | Kết quả policy được tách `facts` và `untrusted_text`; dòng giống mệnh lệnh trong tài liệu bị đưa vào `untrusted_text` (có test) |
| UI | `app.py`, `transcripts/v6_openai_ui_…` | Streamlit dùng lại vòng lặp của `chat.py`; hiện tool call, args và kết quả; có nút câu hỏi mẫu; ghi transcript | Lỗi provider hiện trên trang, không làm sập app. Tunnel là link tạm |
| 4 tool mới (wiki, hn_search, github_repo, rss) | `tools/<tên>/`, `runs/v9_B_group_…` | Group 11/12; không regression trên base hoặc extension khi thêm (v6) | Không cần key; validate input trước khi gọi mạng; luôn trả error dict |
| Tool unit tests (`tests/`) | `pytest`: **115 passed, 0 failed, 0 skipped** | 33 test trong `test_tools_todo.py`: 14 stub TODO + 6 test thêm cho tool cũ (gồm 4 regression) + 13 test cho 4 tool mới (≥3 mỗi tool) | Offline, mock HTTP bằng `fake_http` |

**Bug tìm được trong tool có sẵn** (mỗi bug có regression test, đã sửa):

| # | Tool | Bug | Input của model gây ra | Sửa |
|---|---|---|---|---|
| 1 | `send` | `if not confirmed` coi chuỗi `"false"` là đã xác nhận, nên **gửi thật** | `confirmed="false"` | Chỉ nhận `True` hoặc `"true"` (`test_send_string_false_is_not_treated_as_confirmation`) |
| 2 | `timeline`, `social_search` | `items[:int(limit)]` với `limit=-1` âm thầm bỏ tweet cuối | `limit=-1` | `clamp_int` về 1..100 (`test_timeline_negative_limit_does_not_drop_last_tweet`) |
| 3 | `timeline`, `social_search` | `int("five")` raise, cả request thất bại | `limit="five"` | Dùng mặc định 5 (`test_timeline_non_numeric_limit_uses_default`) |
| 4 | `format` | `section=""` hoặc `None` sinh heading rỗng `## ` hoặc `## None` | item có `section: null` | Fallback "Tổng hợp" / "Tin chính" (`test_format_empty_section_falls_back_to_default_heading`) |

**Ví dụ unit test bắt được mà eval không bắt được:** bug #1. Eval chỉ so sánh *args model gửi*. Model gửi `confirmed="false"` bị eval chấm là sai arg, nhưng eval không biết tool sẽ **thật sự gửi** tin nhắn. Chỉ unit test của code tool mới thấy được hậu quả đó.

## B6. Reflection

- **Fix nào thuộc `system_prompt.md`?** Hành vi và chính sách xuyên suốt nhiều tool: không đoán, xác nhận trước khi gửi (v1); request ghép, lượt mới nhất được ưu tiên, bỏ nguồn (v4); định danh nguồn phải từ user (v7); phạm vi và cách từ chối (v9). Đây là quy tắc ra quyết định, không gắn với một tool cụ thể.
- **Fix nào thuộc `tools.yaml`?** Mọi lỗi **args** và ranh giới giữa các tool gần nhau: `response_type` của clarify (v2), mapping `policy_area`, quy ước query và topic (v3), `timeframe` required (v5), điều kiện gọi rss (v8). Bài học rõ nhất: **param nào cần đúng thì đưa vào `required`**. `gpt-4o-mini` thường bỏ trống param optional và dựa vào default (v5 sửa 2 case chỉ bằng một dòng `required`).
- **Một thay đổi tốt có thể gây regression:** v3 tăng extension từ 0.60 lên 0.90 nhưng làm hỏng M06 trên base. Chỉ vì luôn chạy lại toàn bộ suite sau mỗi version mà nhóm mới thấy.
- **Failure nào cần manual review thay vì chấm tự động?**
  1. **Câu trả lời text của case `no_tool`.** Eval chỉ kiểm tra "không gọi tool". Ở v6, agent viết code cho câu ngoài phạm vi mà vẫn PASS. Phải đọc `actual_text` hoặc chat live mới thấy, từ đó có v9.
  2. **G12.** Agent điền `news.ycombinator.com/rss`, đây là feed HN chính thức, tồn tại thật, khác hẳn kiểu bịa `example.com/article` ở R11. Việc expectation "phải hỏi lại" có đúng không là một quyết định sản phẩm (mức tự chủ mong muốn), máy chấm không quyết được. Nhóm giữ G12 ở trạng thái FAIL để minh bạch và ghi lại là còn tranh luận.
  3. **Hỏi lại bằng text thay vì tool `clarify`** (chat v9, lượt 2). Hành vi đúng về mặt người dùng, nhưng UI không bắt được cờ `awaiting_user`.
- **Eval có giới hạn:** mỗi case chỉ gọi model **một lần** với `tool_choice="required"`. Vì vậy eval không đo được các vòng tool tiếp theo (gọi `format` sau `lookup`), không đo chất lượng câu trả lời, và không đo hành vi khi tool lỗi. Chat live bù cho phần này.
- **Cải tiến tiếp theo:** (1) chuyển các case `no_tool` có `behavior: refuse` sang chấm bằng LLM judge hoặc rubric; (2) thêm case "tool trả lỗi thì agent báo lỗi trung thực"; (3) trong `chat.py` và UI, chặn `send` ở tầng code bằng một bước xác nhận của UI, không chỉ dựa vào prompt; (4) chạy mỗi version 3 lần để đo phương sai, vì base 20 case quá nhỏ: một case bằng 5 điểm phần trăm.

## B7. Small Local Model Challenge (bonus)

Chưa làm. Máy chạy lab chưa cài Ollama nên chưa có run local. Kế hoạch đã chuẩn bị: chạy `v9` trên `qwen2.5:7b` và `llama3.2:3b`, sau đó thử `system_prompt_local.md` rút gọn, có few-shot routing.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v9 | gpt-4o-mini (openai) | v9 | 1.00 | 1.00 | 1.00 | 1.00 | `runs/v9_B_base_openai_20261110T114145525344.json` |
| v9-qwen7b | (ollama) | v9 | – | – | – | – | – |
| v9-llama3b | (ollama) | v9 | – | – | – | – | – |
