---
name: github_repo
track: bonus
kind: live_api
provider: GitHub REST API
requires_env: []
inputs: [repo]
outputs: [items]
side_effect: false
---
# github_repo

Lấy thông tin công khai của MỘT repo GitHub: số sao, fork, issue mở, ngôn ngữ, license,
lần push gần nhất, archived. Nhận `owner/name` hoặc URL github.com.
Không bắt buộc key (giới hạn 60 request/giờ); đặt `GITHUB_TOKEN` để tăng hạn mức.

Guardrails: repo không đúng dạng → error dict (không gọi mạng); HTTP 404/403 → error dict.
