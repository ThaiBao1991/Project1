# TRẠNG THÁI TẠM DỪNG — cập nhật 25/11/2026 09:18

> Người dùng yêu cầu **tạm dừng**. Không xoá dữ liệu, không đổi state.
> Chạy lại sẽ tiếp tục đúng ngày đang thiếu.

## 1. Đã dừng

| Thứ | Trạng thái |
|---|---|
| `pipeline_daemon` (PID 10664) | đã dừng |
| `fill_remaining` / `fill_lite` / `ai.pipeline` (Nga) | đã dừng |
| `finalize_lite --watch` | đã dừng |
| `cleanup_done_media --watch` | đã dừng |
| Tự chạy khi đăng nhập `VocabularyApp_Pipeline.vbs` | đã gỡ |
| Lock trong `D:\VocabularyAppData\state\locks` | đã dọn (0 file) |

Còn `python main.py` — app desktop người dùng đang mở, không phải task nền.

## 2. Mốc tiến độ (09:17)

| Khóa | Trạng thái |
|---|---|
| Nhật | ✅ upload, local đã dọn |
| Trung | ✅ upload, local đã dọn |
| Anh | ✅ upload, local đã dọn |
| Hàn | ✅ upload (`93220ee4`), local đã dọn |
| Tây Ban Nha | ✅ upload (`2d928f32`), local đã dọn |
| Đức | ✅ upload (24/11), local đã dọn |
| Pháp | ✅ upload 08:24 25/11 (raw 200), local đã dọn |
| **Nga** | **695/2.520** — thiếu từ ngày **696**, chưa upload |

- Còn **1.825 ngày** (~27,6%) → khoảng **23–29 giờ** nếu chạy lại.
- Đĩa: **C: 16,4 GB · D: 41,7 GB**.

## 3. Chạy lại

```powershell
cd "C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\VocabularyApp"
python -X utf8 tools\pipeline_daemon.py --install-startup
python -X utf8 tools\pipeline_daemon.py
```

Chỉ chạy thủ công:

```powershell
python -X utf8 tools\fill_remaining_after_chinese.py
python -X utf8 tools\finalize_lite.py --watch --interval 300
python -X utf8 tools\cleanup_done_media.py --watch --interval 300
```

## 4. Kiểm tra sau khi chạy lại

```powershell
python -X utf8 tools\progress.py
python -X utf8 tools\pipeline_daemon.py --status
```

- Nga phải tiếp tục từ **ngày 696**, không làm lại từ đầu.
- Khi Nga đủ 2.520: tự pack → upload 85 gói → deploy → dọn local → **hoàn tất 8/8 khóa**.

## 5. Lưu ý

- Không xoá `data/media`, `data/audio`, `data/ai_courses`, `web/data`, `publish`
  (đều là junction → D:).
- State ở `D:\VocabularyAppData\state` (2 bản + history) — không sửa tay.
