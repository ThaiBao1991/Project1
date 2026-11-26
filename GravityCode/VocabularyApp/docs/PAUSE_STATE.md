# TRẠNG THÁI TẠM DỪNG — 26/11/2026 13:47

> Dừng theo yêu cầu. Không xoá dữ liệu; chạy lại tiếp tục đúng chỗ dở.

## 1. Đã dừng

| Thứ | Trạng thái |
|---|---|
| Batch sinh lại hội thoại tiếng Nhật | đã dừng (hết quota ngày) |
| `dialogue_audio_turns.py` (audio từng lượt) | đã dừng |
| `pipeline_daemon` + 3 watcher | đã dừng |
| Tự chạy khi đăng nhập | đã gỡ |
| Lock | đã dọn (0 file) |
| Manifest | đã gộp **FULL** (262 MB, 647.123 entry) |

## 2. Trạng thái công việc

### Media 8/8 khóa
Đã upload + deploy + dọn local từ 26/11 01:50 (Nga là khóa cuối).

### Hội thoại tiếng Nhật (đang làm dở)
| Hạng mục | Số liệu |
|---|---|
| Ngày cần sinh lại (offline) | 1.311 |
| Đã sinh lại đạt chuẩn | **112 ngày** |
| Trong đó hội thoại kiểu mới (có `turn_type`, ≥2 cặp hỏi–đáp) | **104 ngày** |
| Ngày đã có audio 2 giọng (Nhật + Việt) | **10 ngày** |
| File audio lượt đã sinh | **123 file** (`dlg_*`, `dlgvi_*`) |

- Bản hội thoại cũ được giữ ở `lesson["dialogue_backup"]`.
- Nguyên nhân dừng batch: **toàn bộ 197 key hết quota ngày** (`no_key`).

## 3. Chạy tiếp

```powershell
cd "C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\VocabularyApp"

# 1) Sinh lại hội thoại (sau 00:05 khi quota reset, hoặc khi có key mới)
python -X utf8 tools\regen_dialogues.py --lang "tiếng_nhật" --scope offline

# 2) Audio từng lượt cho các ngày đã sinh lại
python -X utf8 tools\dialogue_audio_turns.py --lang "tiếng_nhật" --only-new

# 3) Khi xong toàn bộ: audio cho tất cả ngày
python -X utf8 tools\dialogue_audio_turns.py --lang "tiếng_nhật"
```

- Tiến độ tự lưu: `data/logs/dialogue_regen_tiếng_nhật.json`,
  `data/logs/dialogue_audio_tiếng_nhật.json`.
- Sau khi xong Nhật: export → pack → upload → deploy → `verify_online.py`
  (dùng `finalize_lite.py --once --lang "tiếng_nhật"`, `SKIP_SHRINK=1` nếu audio đã 32 kbps).
- Sau đó lặp cho 7 ngôn ngữ còn lại.

## 4. Kiểm tra

```powershell
python -X utf8 tools\progress.py                 # 8/8 media
python -X utf8 tools\media_index_swap.py status  # phải là FULL
python -X utf8 tools\pipeline_daemon.py --status # phải "KHÔNG chạy"
```

## 5. Lưu ý

- Chạy lại `regen_dialogues` sẽ bỏ qua ngày đã có trong state; muốn làm lại
  ngày cụ thể thì xoá ngày đó khỏi `done_days`.
- Audio cũ của hội thoại bị thay sẽ tự bị bỏ ref (không phát sai câu).
- Không chạy `regen_dialogues` và `dialogue_audio_turns` **cùng lúc** (cùng ghi
  `course.json.gz`).
