# TRẠNG THÁI TẠM DỪNG — cập nhật 24/11/2026 05:02

> Người dùng yêu cầu **dừng**. Không xoá dữ liệu, không đổi state.
> Chạy lại sẽ tiếp tục đúng chỗ đang dở.

## 1. Đã dừng

| Thứ | Trạng thái |
|---|---|
| `pipeline_daemon` (PID 27788) | đã dừng |
| `fill_remaining` / `fill_lite` / `ai.pipeline` | đã dừng |
| `finalize_lite --watch` | đã dừng |
| `cleanup_done_media --watch` | đã dừng |
| `upload_media_api --lang tiếng_đức` | **bị dừng giữa lúc upload** (xem mục 3) |
| Tự chạy khi đăng nhập `VocabularyApp_Pipeline.vbs` | đã gỡ |
| Lock trong `D:\VocabularyAppData\state\locks` | đã dọn (0 file) |

Còn `python main.py` — app desktop người dùng đang mở, không phải task nền.

## 2. Mốc tiến độ (05:01 ngày 24/11)

| Khóa | Media | Ghi chú |
|---|---:|---|
| Nhật | 2.520 | ✅ upload, local đã dọn |
| Trung | 2.520 | ✅ upload, local đã dọn |
| Anh | 2.520 | ✅ upload, local đã dọn |
| Hàn | 2.520 | ✅ upload (`93220ee4`), local đã dọn |
| Tây Ban Nha | 2.520 | ✅ upload (`2d928f32`), local đã dọn |
| **Đức** | **2.520** | ⚠️ **đã đủ media + đã pack 85 gói (758 MB) nhưng upload bị dừng giữa chừng** — chưa có trong `finalize_done` |
| Pháp | 600 | chờ (thiếu từ ngày 601) |
| Nga | 600 | chờ (thiếu từ ngày 601) |

- Còn **3.840 ngày** media (1.920 × 2 khóa Pháp + Nga).
- Đĩa: **C: 5,8 GB · D: 9,2 GB**.
- `publish/tiếng_đức` vẫn còn 85 gói (758 MB) — giữ lại, lần chạy lại sẽ pack lại rồi upload.

## 3. Lưu ý về Đức

- Pack đã xong lúc **04:55:40** (85 gói, 758 MB), upload đang chạy thì bị dừng.
- Upload dở không tạo commit ⇒ **chưa có gì trên GitHub**; lần chạy lại sẽ upload lại 85 gói (~10 phút), rồi pages + deploy + cleanup.
- Không cần làm lại media (đã đủ 2.520 ngày).

## 4. Chạy lại

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

## 5. Kiểm tra sau khi chạy lại

```powershell
python -X utf8 tools\progress.py
python -X utf8 tools\pipeline_daemon.py --status
```

- Trong ~15 phút đầu, `finalize` sẽ tự xử lý **Đức** (pack → upload → deploy → dọn local).
- Sau đó `fill_remaining` chạy **Pháp** từ ngày 601, rồi **Nga**.

## 6. Lưu ý chung

- Không xoá `data/media`, `data/audio`, `data/ai_courses`, `web/data`, `publish`
  (đều là junction → D:).
- State ở `D:\VocabularyAppData\state` (2 bản + history) — không sửa tay.
