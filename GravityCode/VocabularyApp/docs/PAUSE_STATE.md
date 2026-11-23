# TRẠNG THÁI TẠM DỪNG — cập nhật 23/11/2026 15:03

> Người dùng yêu cầu **tạm dừng** toàn bộ task chạy ẩn. Không xoá dữ liệu,
> không đổi state. Chạy lại sẽ tiếp tục đúng ngày đang thiếu.

## 1. Đã dừng

| Thứ | Trạng thái |
|---|---|
| `pipeline_daemon` (PID 33700) | đã dừng |
| `fill_remaining` / `fill_lite` / `ai.pipeline` (Đức) | đã dừng |
| `finalize_lite --watch` | đã dừng |
| `cleanup_done_media --watch` | đã dừng |
| Tự chạy khi đăng nhập `VocabularyApp_Pipeline.vbs` | đã gỡ |
| `VocabularyApp_Watchdog.vbs` | vẫn ở trạng thái `.disabled` từ 22/11 |
| Lock trong `D:\VocabularyAppData\state\locks` | đã dọn (0 file) |

Còn 1 process `python main.py` — đó là **app desktop đang mở** của người dùng,
không phải task nền; không đụng vào.

## 2. Mốc tiến độ (chính xác lúc 15:02)

| Khóa | Media | Thiếu từ ngày | Ghi chú |
|---|---:|---:|---|
| Nhật | 2.520 | — | ✅ upload, local đã dọn |
| Trung | 2.520 | — | ✅ upload, local đã dọn |
| Anh | 2.520 | — | ✅ upload, local đã dọn |
| Hàn | 2.520 | — | ✅ upload (commit `93220ee4`), local đã dọn |
| Tây Ban Nha | 2.520 | — | ✅ upload (commit `2d928f32`), local đã dọn |
| **Đức** | **1.592/2.520** | **1.593** | đang bù dở, **chưa upload** |
| Pháp | 600 | 601 | chờ |
| Nga | 600 | 601 | chờ |

- Còn **4.768 ngày** media (928 của Đức + 1.920 × 2).
- Tốc độ gần nhất: ~67–73 ngày/giờ ⇒ **~68 giờ (2,8 ngày)** nếu chạy lại.
- Đĩa lúc dừng: **C: 7,1 GB · D: 10,2 GB**.

## 3. Chạy lại

```powershell
cd "C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\VocabularyApp"
python -X utf8 tools\pipeline_daemon.py --install-startup
python -X utf8 tools\pipeline_daemon.py
```

Chỉ chạy thủ công, không cài tự chạy:

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

- Đức phải tiếp tục từ **ngày 1.593** (không làm lại từ đầu).
- Ngày dở dang sẽ được `media_verify` bổ sung ở lượt kế tiếp.

## 5. Lưu ý

- Không xoá `data/media`, `data/audio`, `data/ai_courses` (junction → D:).
- `web/data`, `publish` cũng là junction → D:; giữ nguyên.
- State ở `D:\VocabularyAppData\state` (2 bản + history) — không sửa tay.
- Đức chưa upload: lần chạy lại sẽ tự finalize khi đủ 2.520.
