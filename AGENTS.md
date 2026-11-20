# AGENTS.md — hướng dẫn cho AI agent làm việc trong workspace này

Workspace `Project1` chứa **nhiều dự án độc lập**. Chỉ sửa đúng dự án được yêu cầu.

| Thư mục | Dự án | Ghi chú |
|---|---|---|
| `GravityCode/VocabularyApp` | App học từ vựng 8 ngôn ngữ | dự án chính, xem mục 2 |
| `OpenCode/Addon/MyTiktokDownload` | Extension tải TikTok | **không sửa** nếu không được yêu cầu |
| `GravityCode/Download/...` | tool tải/file | **không commit** `gemini_keys.json`, `settings.json` |
| `Game`, `MyCode`, ... | dự án khác | **không sửa** nếu không được yêu cầu |

## 1. Quy tắc bắt buộc

1. **Đọc trước khi làm**: `projectLog.md` của dự án liên quan (đọc phần cuối) và
   tài liệu runbook tương ứng.
2. **Plan trước, code sau**: nêu rõ file sẽ tạo/sửa/xoá + cách kiểm chứng, chờ
   người dùng đồng ý (`ok`, `go`, `approved`).
3. **Chỉ commit thay đổi thuộc phạm vi**: không commit `MyTiktokDownload`, `Game`,
   `gemini_keys.json`, `*.pyc`, hay thay đổi có sẵn của người dùng.
4. **Git identity**: `Thai Bao <thaibao1991dn@gmail.com>`; push bằng
   `python -X utf8 GravityCode/VocabularyApp/tools/push_master.py` (không hỏi mật khẩu).
5. **UTF-8 mọi nơi**: `chcp 65001`, `$env:PYTHONIOENCODING='utf-8'`, `python -X utf8`,
   file luôn `encoding="utf-8"`. Console hiện `?` không có nghĩa file hỏng.
6. **Không tạo worktree trong `C:`**; nếu cần, đặt ở `D:/opencode-worktrees`.
7. **Báo cáo trung thực**: chỉ nói "xong" khi đã chạy thật và có kết quả; nêu rõ
   phần chưa kiểm được.
8. **Dọn temp** sau khi test; không để file rác trong repo.

## 2. VocabularyApp — bắt buộc đọc trước khi chạm vào

1. `GravityCode/VocabularyApp/docs/PIPELINE_RUNBOOK.md` — cách vận hành, lệnh kiểm tra,
   bảng sự cố, các lỗi đã từng làm sai.
2. `GravityCode/VocabularyApp/projectLog.md` — lịch sử, đọc mục cuối.
3. `GravityCode/VocabularyApp/docs/AUDIT_WORKFLOW.md` — tiêu chí PASS.

Điểm phải nhớ:

- 8 khóa × 2.520 ngày. Nội dung chữ đã đủ; media đang bù dần (Hàn → Tây → Đức → Pháp → Nga).
- Media/audio dữ liệu nặng nằm ở `D:\VocabularyAppData`, nối bằng **junction**
  (`data/media`, `data/audio`, `data/ai_courses`) — **không di chuyển khi pipeline chạy**.
- Trạng thái pipeline nằm ở **2 nơi** (`D:\VocabularyAppData\state\` + `data/logs/`) qua
  `tools/statefile.py`; không sửa tay JSON state.
- **Chỉ finalize/upload khi khóa đủ 2.520 ngày**; media public là raw repo
  `ThaiBao1991/VocabularyData`, không phải GitHub Releases.
- Lệnh kiểm tra nhanh: xem mục 6 của runbook.
- Skill vận hành: `.agents/skills/vocab_media_pipeline/SKILL.md`.

## 3. Định nghĩa "xong" (Definition of Done)

- [ ] `python -m py_compile` các file đã sửa.
- [ ] Chạy thật luồng liên quan, có kết quả cụ thể.
- [ ] `verify_online.py` 9/9 nếu đụng web/media; `audit_all.py` 0 FAIL nếu đụng nội dung.
- [ ] `projectLog.md` có mục mới (ngày giờ, việc làm, số liệu thật).
- [ ] `git status` chỉ có file thuộc phạm vi; commit + push nếu được yêu cầu.
