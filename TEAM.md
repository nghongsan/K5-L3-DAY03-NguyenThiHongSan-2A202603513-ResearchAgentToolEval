# Team

## Thông tin nhóm

- Tên nhóm: `NguyenThiHongSan-2A202603513`
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY03-NguyenThiHongSan-2A202603513-ResearchAgentToolEval`: https://github.com/nghongsan/K5-L3A-DAY03-NguyenThiHongSan-2A202603513-ResearchAgentToolEval
- Nhánh nộp: `main`
- Commit chốt: commit cuối cùng trên nhánh `main` trước deadline 23:59 ngày 10/11/2026 (GMT+7)
- Sản phẩm: research agent **Dori Research** (UI Streamlit `starter_v0/app.py`); báo cáo nhóm [`report/team/group_report.md`](report/team/group_report.md); poster [`report/team/poster.html`](report/team/poster.html).

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Nguyễn Thị Hồng San | 2A202603513 | 26ai.sannth@vinuni.edu.vn | [`nghongsan`](https://github.com/nghongsan) | Nhóm trưởng; Eval lead; prompt và tool declaration; tool mới và unit test; UI; báo cáo nhóm |
|   2 | Nguyễn Thị Hồng Hạnh | 2A202603537 | *(điền)* | *(điền)* | *(điền)* |
|   3 | Hoàng Lam Minh | 2A202603566 | *(điền)* | *(điền)* | *(điền)* |

## Cá nhân

Báo cáo cá nhân của từng thành viên nằm trong `report/team/` theo dạng `MSSV_HoTen.md`:

| Thành viên | Báo cáo cá nhân |
|---|---|
| Nguyễn Thị Hồng San | [`report/team/2A202603513_NguyenThiHongSan.md`](report/team/2A202603513_NguyenThiHongSan.md) |
| Nguyễn Thị Hồng Hạnh | `report/team/2A202603537_NguyenThiHongHanh.md` *(Hạnh tự tạo và commit)* |
| Hoàng Lam Minh | `report/team/2A202603566_HoangLamMinh.md` *(Minh tự tạo và commit)* |

## NguyenThiHongSan-2A202603513

### Phần việc phụ trách

- **CP1, setup và baseline:** cấu hình provider `openai` / `gpt-4o-mini` và key tool; chạy preflight, `pytest`; chạy baseline v0 và phân loại lỗi.
- **CP2, vòng lặp v1–v3:** sửa `starter_v0/artifacts/system_prompt.md` (v1) và `starter_v0/artifacts/tools.yaml` (v2, v3); chạy eval base, extension, group; ghi `starter_v0/artifacts/version_log.csv`.
- **CP3, tool mới:** `wiki`, `hn_search`, `github_repo`, `rss` cùng unit test.
- **CP4, eval nhóm:** 10 case trong `starter_v0/data/eval_group.json`.
- **CP5:** UI Streamlit, kết nối Telegram, link dùng thử (Cloudflare Tunnel), báo cáo nhóm và poster.

### Đóng góp cụ thể

- Baseline v0: `case_accuracy` 0.70 → v1 0.80 (routing 1.00) → v2 1.00 → v3 base 1.00, extension 1.00, group 10/10.
- 4 tool mới không cần API key; `pytest` 118 passed, 0 failed, 0 skipped.
- Tìm và sửa 5 bug trong tool có sẵn, mỗi bug có regression test; vá SSRF cho `rss`; eval chạy `send` ở chế độ dry-run.
- Phát hiện 2 lỗi khi dùng thật (câu thời tiết, câu "tổng thống Mỹ hiện tại") và sửa trong v3.
- Gửi Telegram thật sau khi xác nhận (bot `@dori_k5_bot`, private channel của nhóm).

### Bằng chứng

- Commit trên `main`: `dadfa16` (v0), `988fe2b`, `674f096`, `a323f6b` (v1–v3), `fe983c5`, `2098d89`, `6dc7ccb` (UI, Telegram), `438aba9` (v3 bản cuối), `1c5e0a6`, `2074fe0` (bảo mật), `26018b4` (cấu trúc nộp bài), `7f0d000` (báo cáo cá nhân).
- Run: `starter_v0/runs/v0_…` đến `starter_v0/runs/v3_…`; transcript: `starter_v0/transcripts/`; chi tiết trong [báo cáo cá nhân](report/team/2A202603513_NguyenThiHongSan.md).

## NguyenThiHongHanh-2A202603537

### Phần việc phụ trách

- *(Hạnh tự điền)*

### Đóng góp cụ thể

- *(Hạnh tự điền)*

### Bằng chứng

- *(commit / file của Hạnh)*

## HoangLamMinh-2A202603566

### Phần việc phụ trách

- *(Minh tự điền)*

### Đóng góp cụ thể

- *(Minh tự điền)*

### Bằng chứng

- *(commit / file của Minh)*
