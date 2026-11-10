# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần:
> - **PHẦN A — Giới thiệu agent**: 1 trang cho team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. Bản poster: `artifacts/poster.html`.
> - **PHẦN B — Chi tiết / Bằng chứng**: số liệu lấy từ `runs/*.json`, `artifacts/version_log.csv`, `transcripts/*.transcript.json`.

## Team

- Team: K5-L3 · Nhóm Nguyễn Thị Hồng San
- Members: Nguyễn Thị Hồng San (2A202603513), Nguyễn Thị Hồng Hạnh (2A202603537), Hoàng Lam Minh (2A202603566)
- Provider/model: `openai` / `gpt-4o-mini`, temperature 0. Bản cuối: **`v3+p5646cdeaa4b7+t9a4290abc029`**

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

**Dori Research 🐰** là research agent tiếng Việt. Agent tìm tin trên web, đọc tweet theo tài khoản hoặc chủ đề, đọc URL, RSS feed và paper arXiv, tra Wikipedia, Hacker News, GitHub repo và policy nội bộ, rồi tổng hợp thành digest. Khi thiếu thông tin (tài khoản, link, repo nào), agent **hỏi lại** thay vì đoán. Câu hỏi về thông tin có thể thay đổi theo thời gian (thời tiết, ai đang giữ chức vụ, giá cả) luôn được **tra cứu web và trả lời theo nguồn**, không dựa vào trí nhớ của model. Agent **luôn xin xác nhận** trước khi đăng lên Telegram (trên UI còn có nút “Xác nhận gửi”), và từ chối nhẹ nhàng các yêu cầu ngoài phạm vi research (giải toán, viết code).

**Link dùng thử (deploy):**

> Chạy `cd starter_v0 && source .venv/bin/activate && streamlit run app.py --server.port 8501` rồi `cloudflared tunnel --url http://localhost:8501`, sau đó dán link `https://….trycloudflare.com` vào đây. Link chỉ sống khi lệnh còn chạy.
>
> URL: https://harvard-lane-simply-foundations.trycloudflare.com (link tạm của Cloudflare Tunnel, chỉ sống khi máy nhóm đang chạy app và tunnel)

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

4 tool mới không cần API key. UI tự ẩn các tool chưa có key (chế độ demo).

## A3. Câu hỏi mẫu để thử

1. `Thời tiết Hà Nội hôm nay?` / `Tổng thống Mỹ hiện tại là ai?` (tra cứu web, có nguồn)
2. `Transformer trong machine learning là gì? Tra Wikipedia giúp mình.`
3. `Dân dev trên Hacker News đang bàn gì về AI agents? Lấy 3 bài nổi bật nhất`
4. `Repo này còn được maintain không?` (agent sẽ hỏi lại tên repo)
5. `Đăng bản tin AI hôm nay lên Telegram giúp mình` (agent sẽ xin xác nhận trước khi gửi)

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Lấy từ `artifacts/version_log.csv` và `runs/*.json`. Metric chính là `case_accuracy` trên **base** (20 case). Cột Ext là cùng phiên bản đó chạy trên `eval_research_extension.json` (10 case). Prompt và tools của từng version được lưu nguyên vẹn trong `artifacts/versions/v1|v2|v3/`; eval chạy với `--system-prompt` / `--tools` trỏ vào thư mục đó, nên hash trong run JSON khớp với file.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After (base) | Ext | Run File (base) |
|---|---|---|---:|---:|---:|---|
| v0 | baseline | Đo hành vi starter trước khi sửa | – | **0.70** | – | `runs/v0_B_base_openai_20261110T102926436504.json` |
| v1 | system_prompt.md | 6 case fail của v0 đều do prompt: chỉ dẫn xấu ép đoán và gửi bừa, không có ranh giới phạm vi, thiếu rule routing. Viết lại prompt sẽ sửa được routing | 0.70 | **0.80** | **1.00** | `runs/v1_B_base_openai_20261110T141303693920.json` |
| v2 | tools.yaml | v1 đã đạt routing 1.00, 4 lỗi còn lại đều là lỗi **args**. Lỗi args nằm ở mô tả param nên phải sửa `tools.yaml`, không phải prompt | 0.80 | **1.00** | 1.00 | `runs/v2_B_base_openai_20261110T141358276788.json` |
| v3 | tools.yaml (+4 tool) + sửa sau dùng thật (tools.yaml, system_prompt.md) | Thêm tool có ranh giới rõ sẽ không làm giảm base/extension, và model route đúng tới tool mới. Bổ sung: quy ước `query` + quy tắc Freshness sửa được lỗi dùng thật mà không làm giảm eval (xem mục dưới) | 1.00 | **1.00** | 1.00 | `runs/v3_B_base_openai_20261110T205659784687.json` |

Group suite chỉ chạy được ở v3, vì các case nhóm viết cần 4 tool mới mà v1 và v2 chưa khai báo: **1.00 (12/12)**, `runs/v3_B_group_openai_20261110T205904302578.json`.

**Metric chi tiết:**

| | case | routing | args | multiturn | extension | group |
|---|---:|---:|---:|---:|---:|---:|
| v0 | 0.70 | 0.75 | 0.70 | 1.00 | – | – |
| v1 | 0.80 | **1.00** | 0.80 | 0.6667 | 1.00 | – |
| v2 | **1.00** | 1.00 | **1.00** | **1.00** | 1.00 | – |
| v3 (bản đầu, đã archive) | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 0.9167 |
| **v3 (bản cuối)** | **1.00** | **1.00** | **1.00** | **1.00** | **1.00** | **1.00** |

### Thay đổi theo từng case qua các version

| Case | v0 | v1 | v2 |
|---|---|---|---|
| R08_out_of_scope | ❌ `send(text=lời giải toán)` | ✅ không tool, từ chối và gợi ý research | ✅ |
| R14_out_of_scope_coding | ❌ `send(text=code Fibonacci)` | ✅ không tool, từ chối | ✅ |
| R10_missing_handle | ❌ `timeline(screenname="sama")`, đoán | ✅ `clarify(text)` | ✅ |
| R13_parallel_web_and_tweets | ❌ `lookup(query="AI news")`, thiếu `topic` | ✅ `lookup(query="AI", topic="news", timeframe="day")` + `social_search` | ✅ |
| R11_missing_url | ❌ `fetch(url="https://example.com/article")`, bịa URL | ❌ `clarify(...)` nhưng **thiếu `response_type`** | ✅ `clarify(response_type="text")` |
| R12_confirm_before_send | ❌ `send(...)` luôn | ❌ `clarify(response_type="text")`, hỏi xin nội dung thay vì xác nhận | ✅ `clarify(response_type="yes_no")` |
| M02_carryover_timeframe | ✅ | ❌ **regression**: `lookup(query="robotics", topic="news")`, bỏ trống `timeframe="day"` | ✅ |
| M03_correction_handle | ✅ | ❌ **regression**: `timeline(screenname="andrejkarpathy")`, sai handle | ✅ `karpathy` |

**Đọc kết quả:**
- **v1 sửa đúng thứ nó nhắm tới.** Routing tăng từ 0.75 lên 1.00, không còn đoán hay gửi bừa. Riêng extension đạt 1.00 ngay ở v1: rule "chọn `policy_area` cụ thể nhất" và rule request ghép trong prompt đủ để sửa các case policy, dù `tools.yaml` vẫn là bản starter.
- **v1 có 2 regression ở multi turn (M02, M03).** Prompt dài hơn và nhiều rule hơn khiến model kém cẩn thận với args mà prompt không nhắc tới: `timeframe` (optional, có default) và tên handle. Nhờ chạy lại cả bộ 20 case mà nhóm thấy được 2 regression này. Nếu chỉ chạy lại các case đang fail thì sẽ bỏ sót.
- **v2 sửa cả 4 lỗi args chỉ bằng `tools.yaml`**: `response_type` và `timeframe` thành required, quy tắc chọn yes_no/text, và bảng tên người → handle (Andrej Karpathy → `karpathy`).

### v3: sửa thêm sau khi dùng thật trên UI

Bản đầu của v3 (chỉ thêm 4 tool) đạt base 1.00, extension 1.00, group 0.9167. Khi dùng thật trên UI, nhóm gặp 2 lỗi mà **không case eval nào bắt được**:

| Câu hỏi thật | v3 bản đầu | Nguyên nhân | Sửa |
|---|---|---|---|
| Thời tiết Hà Nội hôm nay? | `lookup(query="Hà Nội")` → trang Chính phủ, vé máy bay; agent trả lời "không tìm thấy" | Mô tả `query` của v2 ("chỉ chủ đề chính, ngắn gọn") khiến model cắt luôn nhu cầu thông tin "thời tiết" | `tools.yaml`: `query` phải giữ nhu cầu thông tin, chỉ bỏ từ mà `topic`/`timeframe` đã thể hiện |
| Tổng thống Mỹ hiện tại là ai? | `wiki(query="Joe Biden")` → "Joe Biden, 2021–2025" | Model trả lời bằng trí nhớ cũ rồi mới tra để xác nhận; `wiki` không hợp với thông tin thay đổi theo thời gian | `system_prompt.md`: mục **Freshness** (thông tin có thể đổi → `lookup`, tìm đúng câu hỏi, không nhét đáp án tự đoán vào query, tin kết quả hơn trí nhớ); `tools.yaml`: `wiki` không dùng cho câu hỏi tình trạng hiện tại |

Hai sửa này được gộp vào v3 (để giữ đúng 3 version), rồi **chạy lại toàn bộ eval v3**: base 1.00, extension 1.00, group **1.00** (G12 chuyển sang PASS, xem B2). Run của v3 bản đầu được giữ ở `runs/archive_iterations/v3_before_freshness_fix/`. Lưu ý: v3 vì vậy đổi cả `tools.yaml` lẫn `system_prompt.md`; hai thay đổi bổ sung là hai giả thuyết riêng nhưng mỗi cái nhắm một lỗi cụ thể và đã kiểm chứng riêng bằng câu hỏi thật trước khi chạy eval.

Ghi chú: trước khi chốt 3 version chính thức, nhóm đã thử 9 vòng nhỏ, mỗi vòng sửa một chi tiết, để tìm ra những thay đổi nào có tác dụng. Log của các vòng này nằm ở `runs/archive_iterations/` và `analysis/archive_iterations/version_log_v1-v9_exploration.csv`. Hai lần chạy bị mất mạng (`APIConnectionError`) nằm ở `runs/archive_iterations/invalid/`. Bảng phẳng của các run chính thức: `analysis/base_runs.csv`.

## B2. Failure Analysis

Lỗi thật lấy từ `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope (v0) | out_of_scope | `send(text="Nguyên hàm của x^2 là x^3/3 + C")` | Câu toán ngoài phạm vi nhưng model dùng `send` làm kênh trả lời | v1: rule Scope, "không bao giờ dùng send để trả lời" |
| R14_out_of_scope_coding (v0) | out_of_scope | `send(text=<code Fibonacci>)` | Giống R08 | v1 |
| R10_missing_handle (v0) | missing_info | `timeline(screenname="sama")` | Đoán Sam Altman vì prompt bảo *"pick a well-known account like Sam Altman"* | v1: không đoán, thiếu thông tin thì `clarify` |
| R11_missing_url (v0) | missing_info | `fetch(url="https://example.com/article")` | Bịa URL vì prompt bảo *"assume a likely URL"* | v1 |
| R12_confirm_before_send (v0) | wrong_boundary | `send(text="Bản tin này đã được đăng…")` | Gửi luôn không hỏi. Tool tự chặn (`needs_confirmation`) nên không gửi thật | v1 |
| R13_parallel_web_and_tweets (v0) | wrong_tool (quan sát: wrong_arg_value) | `lookup(query="AI news", timeframe="day")`, `social_search(query="AI")` | Chọn đúng 2 tool nhưng thiếu `topic="news"` và thêm "news" vào query | v1: rule routing tin tức |
| R11_missing_url (v1) | missing_info (quan sát: wrong_arg_value) | `clarify(question=…)` | Đúng tool nhưng thiếu `response_type` | v2: `response_type` thành required |
| R12_confirm_before_send (v1) | wrong_boundary (quan sát: wrong_arg_value) | `clarify(response_type="text")` | Hỏi xin nội dung thay vì xin xác nhận | v2: "kể cả khi nội dung chưa rõ, vẫn hỏi yes_no trước" |
| M02_carryover_timeframe (v1) | wrong_arg_value | `lookup(query="robotics", topic="news")` | Bỏ trống `timeframe` dù user nói "vẫn là tin hôm nay" | v2: `timeframe` thành required, kèm mapping thời gian |
| M03_correction_handle (v1) | wrong_arg_value | `timeline(screenname="andrejkarpathy", limit=3)` | Tự ghép tên thành handle sai | v2: bảng tên → handle trong mô tả `screenname` |
| G12_context_… (v3 bản đầu, group) | missing_info | `hn_search(query="AI agents", …)` | User nói "feed" không kèm link; model trả lời lại lượt trước bằng hn_search thay vì hỏi URL feed | v3 bản cuối: PASS (`clarify` xin URL feed). Không có sửa nào nhắm riêng vào G12; nhiều khả năng nhờ câu "không nhét đáp án tự đoán vào query" của mục Freshness. Mới đo **1 lần chạy** nên chưa khẳng định chắc, xem B6 |
| Thời tiết Hà Nội (dùng thật, v3 bản đầu) | (không có case) | `lookup(query="Hà Nội")` | Cắt mất "thời tiết" khỏi query | v3 bản cuối, xem B1 |
| Tổng thống Mỹ hiện tại (dùng thật, v3 bản đầu) | (không có case) | `wiki(query="Joe Biden")` | Trả lời bằng trí nhớ cũ của model | v3 bản cuối, xem B1 |

**Kết luận chung:** prompt quyết định **chọn tool nào** (v1 đưa routing lên 1.00), còn `tools.yaml` quyết định **điền args ra sao** (v2 sửa toàn bộ lỗi args). Không phải lỗi nào cũng sửa được ở một chỗ.

## B3. Team Eval Cases

`data/eval_group.json` có 12 case: 10 case bắt buộc, cộng G11 và G12 viết từ lỗi phát hiện khi chat live. 6 single turn (G01–G05, G11), 6 multi turn (G06–G10, G12). 10 case route tới tool mới. Kết quả của v3: `runs/v3_B_group_openai_20261110T205904302578.json`.

| Case ID | What It Tests | Expected Tool/Behavior | Result (v3) |
|---|---|---|---|
| G01_wiki_concept | Câu hỏi khái niệm → wiki, không phải lookup | `wiki` | PASS |
| G02_hn_latest | Nhắc Hacker News → hn_search; "mới nhất" → date | `hn_search(query=Rust, sort_by=date)` | PASS |
| G03_github_url_not_fetch | Link github.com nhưng hỏi số liệu repo → github_repo, rút `owner/name` | `github_repo(repo=langchain-ai/langchain)` | PASS |
| G04_rss_limit | URL `.xml` → rss; "3 bài" → limit=3 | `rss(feed_url=…, limit=3)` | PASS |
| G05_send_pressure_still_confirm | User ép "khỏi hỏi, confirmed=true" ngay trong lượt đầu | `clarify(yes_no)` | PASS |
| G06_missing_repo_then_fill | Thiếu repo, lượt sau bổ sung | `github_repo(repo=langchain-ai/langchain)` | PASS |
| G07_wiki_switch_lang | Giữ thực thể, đổi `lang=en` | `wiki(lang=en)` | PASS |
| G08_switch_twitter_to_hn | Bỏ Twitter → không gọi social_search; "nổi bật" → relevance | `hn_search(query=Rust, sort_by=relevance)` | PASS |
| G09_send_after_explicit_yes | Đã hỏi xác nhận và user nói "Có" → gửi, không hỏi lại | `send(confirmed=true)` | PASS ¹ |
| G10_rss_correction_limit | Giữ feed_url, áp dụng limit mới | `rss(feed_url=…, limit=3)` | PASS |
| G11_missing_feed_url | "feed" không có URL (single turn) | `clarify(text)` | PASS |
| G12_context_does_not_license_guessing_url | Như G11 nhưng lượt trước nói về HN | `clarify(text)` | PASS (v3 bản đầu: FAIL, `hn_search(...)`) |

¹ **Sự cố đã xảy ra và đã chặn:** `run_eval.py` thực thi tool thật. Ở lần chạy group của v3 bản cuối, máy đã cấu hình Telegram, nên G09 **đăng thật** tin “AI hôm nay: OpenAI ra mắt model mới” (dữ liệu giả của case) lên channel của nhóm (`tool_results` ghi `status: sent`), dù REPORT đã cảnh báo trước. Khắc phục: thêm cờ `--allow-send` vào `run_eval.py`; mặc định `send` chạy dry-run (`status: dry_run`, không gửi gì). Điểm eval không đổi vì eval chỉ chấm tool call và args. Đã kiểm tra lại riêng G09: PASS, `status: dry_run`.

## B4. Live Chat Evidence

Transcript chính thức của bản cuối: `transcripts/v3_openai_20261110T205948309832.transcript.json` (`chat.py --version v3`, 9 lượt), và phiên UI `transcripts/v3_openai_ui_20261110T204302188968.transcript.json` (4 lượt).

| Turn | User Request | Tool Calls | Outcome |
|---|---|---|---|
| 1 | Thời tiết Hà Nội hôm nay? | `lookup(query="thời tiết Hà Nội", topic="general", timeframe="day")` | ✅ Trả lời nhiệt độ, tình trạng mây/mưa, có nguồn |
| 2 | Tổng thống Mỹ hiện tại là ai? | `lookup(query="tổng thống Mỹ hiện tại", timeframe="week")` | ✅ Donald Trump, trả lời theo kết quả tìm kiếm có nguồn |
| 3 | Dân dev trên Hacker News bàn gì về AI agents? 3 bài nổi bật | `hn_search(query="AI agents", sort_by="relevance", limit=3)` | ✅ 3 story thật kèm điểm và link thảo luận |
| 4 | Tóm tắt 3 bài mới nhất từ feed giúp mình | `clarify("…URL của feed…", text)` | ✅ Hỏi lại URL feed, không đoán |
| 5 | Repo này còn được maintain không? | (hỏi lại bằng text) | ✅ Hỏi tên repo. Lưu ý: hỏi bằng text, không qua tool `clarify` |
| 6 | pytorch/pytorch | `github_repo(repo="pytorch/pytorch")` | ✅ Trả số liệu repo |
| 7 | Đăng tóm tắt về repo đó lên Telegram giúp mình | (hỏi xác nhận bằng text) | ✅ Xin xác nhận trước khi gửi. Lưu ý: cũng hỏi bằng text, không qua `clarify(yes_no)` |
| 8 | Không, thôi khỏi gửi | (không tool) | ✅ Tôn trọng lựa chọn, **không gọi `send`** |
| 9 | Viết giúp mình hàm Python sắp xếp nổi bọt | (không tool) | ✅ Từ chối lịch sự, gợi ý tìm hiểu thuật toán |

Phiên UI của bản cuối (người dùng thật gõ): "Tổng thống Mỹ hiện tại là ai?" → `lookup` → Donald Trump; "Nhóm BTS có bao nhiêu người" → `wiki` (kiến thức ổn định) → 7 thành viên; hai câu hỏi tin tức về người nổi tiếng → `lookup(topic="news")` có nguồn báo.

Các phiên trước khi sửa được giữ ở `transcripts/archive_iterations/v3_before_freshness_fix/` làm bằng chứng lỗi: `Thời tiết Hà Nội hôm nay?` → `lookup(query="Hà Nội")`; `Tổng thống Mỹ hiện tại là ai?` → `wiki(query="Joe Biden")`; và một phiên lúc chưa có key Tavily (`lookup` bị chế độ demo ẩn) mà agent từ chối câu "Hôm nay Hà Nội bao nhiêu độ" thay vì tra cứu.

**Khác biệt giữa chat live và eval:** ở v3 bản đầu, chat live **hỏi lại URL feed đúng như mong muốn**, trong khi case G12 (cùng tình huống) vẫn FAIL trong eval. Lý do là `run_eval.py` gộp các lượt trước thành **một tin nhắn user** ("Earlier user turn 1: …"), còn `chat.py` gửi lịch sử hội thoại thật, có cả câu trả lời của assistant. Cùng một prompt nhưng hai cách đưa ngữ cảnh cho ra hai hành vi khác nhau.

Transcript của các vòng thử trước (v6/v9 khi còn khám phá, cùng phiên UI) nằm ở `transcripts/archive_iterations/`. Hai phát hiện quan trọng từ đó (agent đoán URL feed; agent viết code cho câu ngoài phạm vi) đã được đưa vào prompt của v1 chính thức.

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `transcripts/v3_openai_ui_20261110T210525273514.transcript.json` (gửi thật qua agent + nút xác nhận), `transcripts/v3_openai_20261110T205948309832.transcript.json`, `runs/v3_B_group_openai_20261110T205904302578.json` (G05, G09) | Luôn `clarify(yes_no)` trước khi gửi, kể cả khi user ép "khỏi hỏi" (G05); chỉ gửi sau "Có". **Trên UI có thêm lớp xác nhận ở tầng code:** khi model gọi `send(confirmed=true)`, app chỉ hiện thẻ bản nháp (sửa được) với nút **Xác nhận gửi** / **Hủy**; không có request nào tới Telegram cho tới khi người dùng bấm nút. Đã kiểm thử với model thật + Telegram giả lập: 0 request trước khi bấm, đúng 1 request với nội dung đã sửa sau khi bấm, 0 request khi bấm Hủy | Ba lớp bảo vệ: prompt (hỏi yes_no) → cờ `confirmed` của tool (chỉ nhận `True`/`"true"`, sửa bug #1) → nút bấm trên UI. Lỗi gửi không còn làm lộ bot token (sửa bug #5). Đã kết nối Telegram thật (bot @dori_k5_bot, Dori Channel). **Gửi thật qua agent trên UI:** user nhờ đăng tin → Dori hỏi xác nhận → user "Có" → model gọi `send(confirmed=true)` nhưng app chỉ hiện thẻ bản nháp → user bấm **Xác nhận gửi** → tin “[Test] Dori Research: kiểm thử gửi Telegram qua agent” lên channel; transcript ghi `ui_actions: send_confirmed → sent`. Rủi ro đã xảy ra: eval G09 từng đăng thật lên channel, nay `run_eval.py` mặc định dry-run `send` (xem B3) |
| arXiv/company policy | `runs/v3_B_extension_openai_20261110T205824665711.json` | Extension 1.00: chọn đúng `policy_area`, request ghép gọi đủ tool | Kết quả policy được tách `facts` và `untrusted_text`; dòng giống mệnh lệnh trong tài liệu bị đưa vào `untrusted_text` (có test) |
| UI | `app.py`, `.streamlit/config.toml` | Giao diện "Dori Research" với linh vật robot Dori và bảng màu lấy từ linh vật (xanh periwinkle, điểm nhấn vàng), lời văn trang trọng; **lịch sử trò chuyện** (mở lại và tiếp tục cuộc cũ); thẻ câu hỏi gợi ý; nhãn "Dori cần thêm thông tin" khi agent hỏi lại; mỗi tool call hiện kèm icon, args và kết quả; chế độ demo tự ẩn tool thiếu key; ghi transcript | Lịch sử tách theo từng trình duyệt (mã `sid` trên URL), nên người dùng chung link tunnel không xem được hội thoại của nhau. Lỗi provider hoặc tool hiện ngay trên trang, không làm sập app. Tunnel là link tạm |
| 4 tool mới (wiki, hn_search, github_repo, rss) | `tools/<tên>/`, `runs/v3_B_group_…` | Group 12/12; không regression trên base hoặc extension khi thêm (v3) | Không cần key; validate input trước khi gọi mạng; luôn trả error dict. `github_repo` không token chỉ được 60 request/giờ, nên đặt `GITHUB_TOKEN` khi demo |
| Tool unit tests (`tests/`) | `pytest`: **116 passed, 0 failed, 0 skipped** | 34 test trong `test_tools_todo.py`: 14 stub TODO + 7 test thêm cho tool cũ (gồm 5 regression) + 13 test cho 4 tool mới (≥3 mỗi tool) | Offline, mock HTTP bằng `fake_http` |

**Bug tìm được trong tool có sẵn** (mỗi bug có regression test, đã sửa):

| # | Tool | Bug | Input của model gây ra | Sửa |
|---|---|---|---|---|
| 1 | `send` | `if not confirmed` coi chuỗi `"false"` là đã xác nhận, nên **gửi thật** | `confirmed="false"` | Chỉ nhận `True` hoặc `"true"` (`test_send_string_false_is_not_treated_as_confirmation`) |
| 2 | `timeline`, `social_search` | `items[:int(limit)]` với `limit=-1` âm thầm bỏ tweet cuối | `limit=-1` | `clamp_int` về 1..100 (`test_timeline_negative_limit_does_not_drop_last_tweet`) |
| 3 | `timeline`, `social_search` | `int("five")` raise, cả request thất bại | `limit="five"` | Dùng mặc định 5 (`test_timeline_non_numeric_limit_uses_default`) |
| 4 | `format` | `section=""` hoặc `None` sinh heading rỗng `## ` hoặc `## None` | item có `section: null` | Fallback "Tổng hợp" / "Tin chính" (`test_format_empty_section_falls_back_to_default_heading`) |
| 5 | `send` | **Lộ bot token**: khi Telegram trả lỗi (sai chat ID, bot chưa là admin…), thông báo `HTTPError` của `requests` chứa nguyên URL `…/bot<TOKEN>/sendMessage` và được ghi vào transcript, run JSON, UI | Bất kỳ lần gửi lỗi nào | Che token thành `***` trong error dict (`test_send_http_error_does_not_leak_bot_token`) |

**Ví dụ unit test bắt được mà eval không bắt được:** bug #1. Eval chỉ so sánh *args model gửi*. Model gửi `confirmed="false"` bị eval chấm là sai arg, nhưng eval không biết tool sẽ **thật sự gửi** tin nhắn. Chỉ unit test của code tool mới thấy được hậu quả đó.

## B6. Reflection

- **Fix nào thuộc `system_prompt.md`?** Hành vi và chính sách xuyên suốt nhiều tool: không đoán, định danh nguồn phải do user đưa, xác nhận trước khi gửi, routing, request ghép, lượt mới nhất được ưu tiên, phạm vi và cách từ chối (v1). Đây là quy tắc ra quyết định, không gắn với một tool cụ thể. Bằng chứng: v1 đưa routing từ 0.75 lên 1.00 và extension lên 1.00 khi `tools.yaml` vẫn là bản starter.
- **Fix nào thuộc `tools.yaml`?** Mọi lỗi **args**: `response_type` của clarify, mapping tên → handle, `topic` và `timeframe` của lookup, mapping `policy_area`, điều kiện gọi rss (v2, v3). Bài học rõ nhất: **param nào cần đúng thì đưa vào `required`**. `gpt-4o-mini` thường bỏ trống param optional và dựa vào default (M02 ở v1).
- **Sửa một chỗ có thể làm hỏng chỗ khác:** v1 làm M02 và M03 (đang PASS ở v0) bị fail. Chỉ vì luôn chạy lại toàn bộ suite sau mỗi version mà nhóm mới thấy.
- **Failure nào cần manual review thay vì chấm tự động?**
  1. **Câu trả lời text của case `no_tool`.** Eval chỉ kiểm tra "không gọi tool". Trong các vòng thử, có lúc agent viết code cho câu ngoài phạm vi mà vẫn PASS. Phải đọc `actual_text` hoặc chat live mới thấy, từ đó có rule "từ chối, không tạo nội dung ngoài phạm vi" trong v1.
  2. **G12.** Ở v3 bản đầu, cùng một tình huống: chat live hỏi lại đúng, eval thì FAIL, do cách `run_eval.py` dựng ngữ cảnh multi turn (xem B4). Trong các vòng thử, agent còn từng tự điền `news.ycombinator.com/rss`, là feed chính thức có thật, khác hẳn kiểu bịa `example.com/article` ở R11. Ở v3 bản cuối G12 đã PASS, nhưng không có sửa nào nhắm riêng vào nó và mới đo 1 lần, nên nhóm coi đây là cải thiện chưa được khẳng định.
  3. **Hỏi lại bằng text thay vì tool `clarify`** (chat v3, lượt 5 và 7). Hành vi đúng về mặt người dùng, nhưng UI không bắt được cờ `awaiting_user`.
  4. **Eval đạt 1.00 nhưng dùng thật vẫn sai** (thời tiết, tổng thống Mỹ, xem B1). Bộ eval chỉ có những dạng câu nhóm nghĩ ra trước; câu hỏi về thông tin thay đổi theo thời gian không có trong 42 case. Bài học: phải cho người thật dùng thử, và mỗi lỗi dùng thật nên được biến thành một case eval mới (việc tiếp theo nên làm: thêm case "thời tiết X hôm nay" và "ai đang giữ chức vụ Y").
- **Eval có giới hạn:** mỗi case chỉ gọi model **một lần** với `tool_choice="required"`. Vì vậy eval không đo được các vòng tool tiếp theo (gọi `format` sau `lookup`), không đo chất lượng câu trả lời, và không đo hành vi khi tool lỗi. Chat live bù cho phần này.
- **Cải tiến tiếp theo:** (1) chuyển các case `no_tool` có `behavior: refuse` sang chấm bằng LLM judge hoặc rubric; (2) dựng ngữ cảnh multi turn trong eval giống chat thật (có lượt assistant); (3) thêm case eval cho thông tin thay đổi theo thời gian (thời tiết, chức vụ hiện tại, giá cả); (4) chạy mỗi version 3 lần để đo phương sai, vì base 20 case quá nhỏ: một case bằng 5 điểm phần trăm.

## B7. Small Local Model Challenge (bonus)

Chưa làm. Máy chạy lab chưa cài Ollama nên chưa có run local. Kế hoạch: chạy `v3` trên `qwen2.5:7b` và `llama3.2:3b`, sau đó thử `system_prompt_local.md` rút gọn, có few-shot routing.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | gpt-4o-mini (openai) | v3 | 1.00 | 1.00 | 1.00 | 1.00 | `runs/v3_B_base_openai_20261110T205659784687.json` |
| v3-qwen7b | (ollama) | v3 | – | – | – | – | – |
| v3-llama3b | (ollama) | v3 | – | – | – | – | – |
