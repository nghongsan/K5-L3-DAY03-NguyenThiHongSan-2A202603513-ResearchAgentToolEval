# Báo cáo cá nhân — NguyenThiHongSan-2A202603513

## 1. Thông tin thành viên

- Họ tên: Nguyễn Thị Hồng San
- MSSV: 2A202603513
- Email: *(điền)*

## 2. Phần việc phụ trách

- Eval lead: setup provider (`openai` / `gpt-4o-mini`), preflight, chạy và ghi log v0–v3.
- Prompt và tool declaration; 4 tool mới (`wiki`, `hn_search`, `github_repo`, `rss`) cùng unit test.
- UI Streamlit "Dori Research", kết nối Telegram (bot @dori_k5_bot), mở link dùng thử bằng Cloudflare Tunnel.
- Báo cáo nhóm `report/team/group_report.md` và poster.

## 3. Đóng góp cụ thể

- Baseline v0: case_accuracy 0.70, phân loại 6 case FAIL (`starter_v0/runs/v0_B_base_openai_20261110T102926436504.json`).
- v1 (prompt) 0.80 → v2 (tools.yaml) 1.00 → v3 (+4 tool, sửa lỗi dùng thật) base 1.00, extension 1.00, group 10/10.
- 10 case eval nhóm (`starter_v0/data/eval_group.json`).
- 5 bug trong tool có sẵn (send coi `"false"` là xác nhận, lộ bot token, limit âm/không phải số, section rỗng) và vá SSRF cho `rss`; `pytest` 118 passed, 0 skipped.

## 4. Bằng chứng

- File/commit/PR: các commit `dadfa16` → commit chốt trên nhánh `nguyenthihongsan`; `starter_v0/artifacts/version_log.csv`; `starter_v0/transcripts/`.
- AI/công cụ đã dùng và cách tự kiểm tra kết quả: Claude Code (Anthropic) hỗ trợ viết code, test, chạy eval và soạn báo cáo. *(San tự viết: mình đã tự kiểm tra kết quả thế nào, ví dụ đọc run JSON, chạy lại pytest, tự hỏi thử trên UI…)*

## 5. Tự đánh giá

*(San tự viết)*
