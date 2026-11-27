# TRẠNG THÁI TẠM DỪNG — 27/11/2026 18:00

> Dừng theo yêu cầu. Không xoá dữ liệu; chạy lại tiếp tục đúng chỗ dở.

## 1. Đã dừng

| Thứ | Trạng thái |
|---|---|
| Batch sinh hội thoại tiếng Nhật (PID 22480) | đã dừng |
| Job nền chờ-rồi-chạy-audio | đã dừng (không chạy audio) |
| Audio từng lượt | không chạy |
| `pipeline_daemon` + watcher | đang tắt từ 26/11 |
| Tự chạy khi đăng nhập | đã gỡ |
| Lock | 0 file |
| Manifest | **FULL** 262 MB (không ở chế độ shard) |

Process còn lại: chỉ app bạn đang mở (`AskCpl.py`).

## 2. Tiến độ

### Media: 8/8 khóa
Đã upload + deploy + dọn local (xong 26/11).

### Hội thoại tiếng Nhật
| Hạng mục | Số liệu |
|---|---:|
| Ngày cần sinh lại | 1.311 |
| Đã sinh lại đạt chuẩn | **284** (21,7%) |
| Ngày đủ audio 2 giọng (Nhật + Việt) | 10 |
| Ngày cao nhất đã xử lý | 1.046 |

- Bản cũ giữ ở `dialogue_backup`.
- State đã đối soát: bỏ 8 ngày đánh dấu "done" nhưng chưa kịp ghi vào `course.json`
  (8, 16, 26, 28, 29, 37, 38, 47) ⇒ lần sau sẽ làm lại các ngày này.

## 3. Chạy tiếp

```powershell
cd "C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\VocabularyApp"

# 1) Hội thoại (tiếp tục từ ngày chưa xong)
python -X utf8 tools\regen_dialogues.py --lang "tiếng_nhật" --scope offline

# 2) Audio cho các ngày đã sinh lại (đa luồng, nhẹ RAM)
python -X utf8 tools\dialogue_audio_turns.py --lang "tiếng_nhật" --only-new --workers 4
```

- State: `data/logs/dialogue_regen_tiếng_nhật.json`,
  `data/logs/dialogue_audio_tiếng_nhật.json`.
- Không chạy 2 lệnh trên cùng lúc (cùng ghi `course.json.gz`).

## 4. Khi xong tiếng Nhật

1. `finalize_lite.py --once --lang "tiếng_nhật"` với `SKIP_SHRINK=1`
   (nếu audio đã 32 kbps) để pack → upload → deploy.
2. `verify_online.py` (9/9) + nghe thử 20 ngày mẫu.
3. Lặp quy trình cho 7 ngôn ngữ còn lại.

## 5. Đĩa

- **C: 35,8 GB** · **D: 39,0 GB**.
