# TRẠNG THÁI TẠM DỪNG — 22/11/2026 07:50

> Mục đích: lưu mốc tiến độ + cách khôi phục sau khi người dùng yêu cầu **dừng mọi
> task chạy ẩn**. Đọc file này trước khi chạy lại pipeline.

## 1. Đã dừng những gì

| Thứ | Trạng thái |
|---|---|
| `pipeline_daemon.py` (PID 18132) | đã dừng (`--stop`) |
| `fill_remaining_after_chinese.py` | đã dừng cùng cây tiến trình |
| `fill_lite.py` + `ai.pipeline` | đã dừng |
| `finalize_lite.py --watch` | đã dừng |
| `cleanup_done_media.py --watch` | đã dừng |
| Tự chạy khi đăng nhập `VocabularyApp_Pipeline.vbs` | đã gỡ |
| Tự chạy khi đăng nhập `VocabularyApp_Watchdog.vbs` | đổi tên thành `.vbs.disabled` |
| Lock trong `D:\VocabularyAppData\state\locks` | đã dọn (không còn tiến trình) |

Không còn process `python` nào của VocabularyApp. `OllamaServe.vbs` vẫn giữ
nguyên (không liên quan).

## 2. Mốc tiến độ (chính xác lúc 07:49)

| Khóa | Ngày có media | Ngày thiếu đầu tiên | Ghi chú |
|---|---:|---:|---|
| Nhật | 2.520 (đã upload, local = 0) | — | ✅ xong, đã cleanup |
| Trung | 2.520 (đã upload, local = 0) | — | ✅ xong, đã cleanup |
| Anh | 2.520 (đã upload, local = 0) | — | ✅ xong, đã cleanup |
| Hàn | 2.520 (đã upload, local = 0) | — | ✅ upload commit `93220ee4`, đã cleanup |
| **Tây Ban Nha** | **1.866/2.520** | **1867** | đang bù dở |
| Đức | 600/2.520 | 601 | chờ |
| Pháp | 600/2.520 | 601 | chờ |
| Nga | 600/2.520 | 601 | chờ |

- Còn **6.414 ngày** media (654 của Tây + 3×1.920).
- Tốc độ gần nhất: ~90 ngày/giờ ⇒ **~71 giờ (3 ngày)** nếu chạy lại.
- Đĩa lúc dừng: **C: 4,48 GB · D: 26,62 GB**.

## 3. Cách chạy lại

Cách nhanh (daemon quản lý cả 3 job + tự chạy khi đăng nhập):

```powershell
cd "C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\VocabularyApp"
python -X utf8 tools\pipeline_daemon.py --install-startup
python -X utf8 tools\pipeline_daemon.py
```

Cách thủ công (không cài tự chạy):

```powershell
cd "C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\VocabularyApp"
python -X utf8 tools\fill_remaining_after_chinese.py
python -X utf8 tools\finalize_lite.py --watch --interval 300
python -X utf8 tools\cleanup_done_media.py --watch --interval 300
```

Chạy lại watchdog AI (tuỳ chọn, chỉ cần nếu muốn nội dung/quota AI):

```powershell
Rename-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\VocabularyApp_Watchdog.vbs.disabled" "VocabularyApp_Watchdog.vbs"
```

## 4. Kiểm tra sau khi chạy lại

```powershell
python -X utf8 tools\pipeline_daemon.py --status
python -X utf8 -c "import os; p=r'data\media\tiếng_tây_ban_nha'; print(sum(1 for d in os.listdir(p) if os.path.isdir(os.path.join(p,d)) and os.listdir(os.path.join(p,d))))"
```

- Tây phải tiếp tục từ **ngày 1867** (không làm lại từ đầu).
- `fill_lite`/`ai.pipeline` resume theo `first_missing`; ngày dở dang sẽ được
  `media_verify` bổ sung ở lượt kế tiếp.

## 5. Lưu ý

- Không xoá `data/media`, `data/audio`, `data/ai_courses` (junction → D:).
- State ở `D:\VocabularyAppData\state` (2 bản + history) — không sửa tay.
- Nếu muốn dừng hẳn và không bao giờ tự chạy: đừng cài `--install-startup`, và giữ
  `VocabularyApp_Watchdog.vbs.disabled`.
