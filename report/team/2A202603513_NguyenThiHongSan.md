# Báo cáo cá nhân — NguyenThiHongSan-2A202603513

## 1. Thông tin thành viên

- Họ tên: Nguyễn Thị Hồng San
- MSSV: 2A202603513
- Email: *(điền)*
- GitHub: `nghongsan`
- Vai trò trong nhóm: nhóm trưởng; Eval lead (vai A trong bảng phân công), đồng thời phụ trách prompt/tools, tool mới, UI và báo cáo nhóm.

## 2. Phần việc phụ trách

| Hạng mục | Nội dung |
|---|---|
| Setup và baseline (CP1) | Cấu hình provider `openai` / `gpt-4o-mini` và key tool (Tavily, Firecrawl, RapidAPI, Telegram) trong `.env`; chạy preflight; chạy baseline v0 và phân loại lỗi |
| Vòng lặp v1–v3 (CP2) | Chạy eval base/extension/group cho từng version, ghi `starter_v0/artifacts/version_log.csv`; sửa `system_prompt.md` (v1) và `tools.yaml` (v2, v3) |
| Tool mới và test (CP3) | 4 tool không cần key: `wiki`, `hn_search`, `github_repo`, `rss`; unit test; điền các stub TODO |
| Eval nhóm (CP4) | 10 case trong `starter_v0/data/eval_group.json` (5 single + 5 multi turn) |
| UI, live chat, báo cáo (CP5) | UI Streamlit "Dori Research", kết nối Telegram thật, mở link dùng thử bằng Cloudflare Tunnel, báo cáo nhóm và poster |

## 3. Đóng góp cụ thể

**Đánh giá và tối ưu agent**
- Baseline v0: `case_accuracy` 0.70 (14/20). 6 case FAIL, 3 trong số đó do chỉ dẫn xấu cố ý của starter (đoán handle, bịa URL, gửi Telegram không hỏi).
- v1 (chỉ sửa prompt): routing 0.75 → 1.00, base 0.80, extension 1.00. Phát hiện 2 regression multi turn (M02, M03).
- v2 (chỉ sửa `tools.yaml`): base 1.00. Sửa cả 4 lỗi args còn lại (`response_type`, `timeframe`, tên → handle).
- v3: thêm 4 tool; sau khi tự dùng thử trên UI, sửa thêm 2 lỗi mà eval không bắt được (câu thời tiết bị cắt mất chữ "thời tiết"; câu "tổng thống Mỹ hiện tại" bị trả lời bằng trí nhớ cũ "Joe Biden"), rồi chạy lại toàn bộ eval: base 1.00, extension 1.00, group 10/10.

**Code và kiểm thử**
- 4 tool mới, mỗi tool có `tool.py`, `TOOL.md`, đăng ký trong registry và `tools.yaml`; 15 test cho tool mới.
- 5 bug tìm được trong tool có sẵn, mỗi bug có regression test: `send` coi chuỗi `"false"` là đã xác nhận; `send` làm lộ bot token trong thông báo lỗi; `timeline`/`social_search` xử lý sai `limit=-1` và `limit="five"`; `format` sinh heading rỗng.
- Vá lỗ hổng SSRF của `rss` (không cho đọc localhost/mạng nội bộ khi mở link public); `run_eval.py` thêm `--allow-send` để eval không đăng Telegram thật.
- `pytest`: 118 passed, 0 failed, 0 skipped.

**UI và demo**
- UI Streamlit: lịch sử trò chuyện tách theo trình duyệt, thẻ câu hỏi gợi ý, nhãn khi agent hỏi lại, thẻ "Xác nhận gửi" cho Telegram, chế độ demo tự ẩn tool thiếu key, giới hạn số câu hỏi.
- Kết nối Telegram thật (bot @dori_k5_bot, private channel của nhóm) và gửi thành công sau xác nhận.

## 4. Bằng chứng

- **File/commit/PR** (nhánh `nguyenthihongsan`):

  | Commit | Nội dung |
  |---|---|
  | `dadfa16` | Baseline v0 (0.70) |
  | `988fe2b` | Vòng thử nghiệm, 4 tool mới, test, eval nhóm, UI, báo cáo |
  | `674f096` | Chế độ demo của UI, so sánh v0 → v1 |
  | `a323f6b` | Chốt 3 version chính thức v1–v3, chạy lại eval |
  | `fe983c5`, `2098d89` | UI "Dori Research", lịch sử trò chuyện, linh vật và bảng màu |
  | `6dc7ccb` | Thẻ "Xác nhận gửi" Telegram; vá lỗi lộ bot token |
  | `438aba9` | v3 bản cuối: sửa lỗi dùng thật (thời tiết, thông tin cũ), chạy lại eval |
  | `1c5e0a6` | Thành viên nhóm, bằng chứng gửi Telegram thật |
  | `2074fe0` | Vá bảo mật cho link public: SSRF, mã lịch sử, giới hạn câu hỏi |
  | `26018b4` | Gộp cấu trúc nộp bài mới, eval nhóm đúng 10 case |

  Run: `starter_v0/runs/v0_…` đến `starter_v0/runs/v3_…`; transcript: `starter_v0/transcripts/`; báo cáo: `report/team/group_report.md`.

  *Lưu ý:* các commit trên được tạo khi máy chưa cấu hình `git user.email`, nên mang email tự sinh `…@MacBook-Air-cua-San.local` thay vì email GitHub. Commit kể từ khi sửa cấu hình mang đúng tài khoản `nghongsan`.

- **AI/công cụ đã dùng và cách tự kiểm tra kết quả:**
  - Công cụ: Claude Code (Anthropic, chạy trong VS Code) hỗ trợ viết code tool, test, UI, chạy eval, phân tích run JSON và soạn báo cáo; OpenAI `gpt-4o-mini` là model của agent.
  - Tự kiểm tra bằng cách dùng thử agent trên UI (transcript lưu trong repo):
    - Hỏi "Thời tiết Hà Nội hôm nay?" thì thấy agent tìm `lookup(query="Hà Nội")` và trả lời "không tìm thấy" (`starter_v0/transcripts/archive_iterations/v3_before_freshness_fix/v3_openai_ui_20261110T202633921821.transcript.json`).
    - Hỏi "Tổng thống Mỹ hiện tại là ai?" thì thấy agent trả lời "Joe Biden" qua `wiki(query="Joe Biden")` (`…/v3_openai_ui_20261110T203701582721.transcript.json`).
    - Hai lỗi này dẫn tới bản sửa trong v3. Sau khi sửa, hỏi lại thời tiết, giá xăng, tổng thống Mỹ thì agent gọi `lookup` đúng (`starter_v0/transcripts/v3_openai_ui_20261110T210108093150.transcript.json`).
    - Tự test gửi Telegram: Dori hỏi xác nhận, trả lời "Chắc chắn", bấm nút, tin lên channel (`starter_v0/transcripts/v3_openai_ui_20261110T210223596995.transcript.json`).
  - *(San bổ sung bằng lời của mình: những bước kiểm tra khác đã làm, ví dụ đọc run JSON, chạy lại `pytest`, kiểm tra tin trên Telegram, chỗ nào đã không đồng ý với gợi ý của AI và vì sao.)*

## 5. Tự đánh giá

*(San tự viết phần này bằng lời của mình. RULES.md không cho phép dùng AI viết phần tự đánh giá. Các câu hỏi gợi ý:)*

- *Mình tự giải thích được những phần nào? (vì sao v1 chỉ sửa prompt mà routing lên 1.00; vì sao v2 sửa `tools.yaml`; vì sao v3 phải sửa thêm sau khi dùng thật; mỗi tool mới làm gì và test của nó kiểm tra gì)*
- *Phần nào mình làm tốt, phần nào còn yếu?*
- *Mình đã học được gì về cách đánh giá agent (ví dụ: eval đạt 1.00 nhưng dùng thật vẫn sai)?*
- *Nếu làm lại, mình sẽ làm khác điều gì?*
