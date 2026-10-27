# Hướng Dẫn Sử Dụng VocabularyApp AI Pipeline

## 1. Tổng Quan

Pipeline tự trị sinh khóa học AI theo ngày cho mọi ngôn ngữ, bao gồm:
- Nội dung bài học (từ vựng, mẫu câu, câu thông dụng, ngữ pháp)
- Trắc nghiệm 4 loại (từ vựng, mẫu câu, câu thông dụng, ngữ pháp)
- Ảnh minh họa, âm thanh TTS, hội thoại roleplay
- Dẫn chứng Wikipedia/Wiktionary (tùy chọn)

## 2. Chạy Qua GUI

Mở `VocabApp.py`:

1. Chọn ngôn ngữ (ví dụ: "Tiếng Nhật")
2. Chọn cấp độ "⭐ Trọn gói: Từ con số 0 đến Như người bản xứ"
3. Chọn thời lượng (khuyên 30-60 ngày cho ngôn ngữ mới)
4. Tick "🖼️🔊 Sinh ảnh minh họa + âm thanh + hội thoại" nếu cần media
5. Bấm "▶ Tiếp tục / Bắt đầu sinh"

### Tùy chọn quan trọng

| Tùy chọn | Mô tả |
|----------|-------|
| Làm lại từ đầu | Xóa course cũ, tạo mới. Giữ nguyên ảnh/audio cũ. |
| Rà soát & Bổ sung | Kiểm tra chàng thiếu, tự động bổ sung. |
| Sinh ảnh + âm thanh | Bật pipeline media (ảnh, audio, hội thoại). |
| Sinh lại nội dung | Thêm IPA, khẩu hình phát âm (chế độ enrich). |

## 3. Chạy Qua CLI

```bash
# Xem trạng thái pipeline của ngôn ngữ
python -m ai.pipeline --lang "Tiếng Nhật" --status

# Chạy fresh 30 ngày, không media (chỉ text)
python -m ai.pipeline --lang "Tiếng Nhật" --full --days 30 --force-new --no-media

# Chạy với chờ quota khi hết (không dừng ngang)
python -m ai.pipeline --lang "Tiếng Nhật" --full --days 30 --wait-quota --workers 4

# Chỉ thêm media cho course đã có
python -m ai.pipeline --lang "Tiếng Nhật" --full --days 30 --mode media --workers 4

# Chạy cho tất cả ngôn ngữ
python -m ai.pipeline --all --full --workers 4

# Dry-run (không gọi AI, chỉ in kế hoạch)
python -m ai.pipeline --lang "Tiếng Nhật" --full --dry-run
```

### Các cờ CLI quan trọng

| Cờ | Mô tả |
|----|-------|
| `--lang` | Tên ngôn ngữ (ví dụ: "Tiếng Nhật") |
| `--all` | Chạy cho tất cả ngôn ngữ |
| `--full` | Sinh toàn bộ (content + quiz + media) |
| `--days` | Giới hạn số ngày mục tiêu |
| `--force-new` | Xóa course cũ, tạo mới từ đầu |
| `--wait-quota` | Chờ quota reset thay vì dừng ngang |
| `--workers` | Số ngày xử lý song social (1-8) |
| `--no-media` | Chỉ sinh text, không sinh ảnh/audio |
| `--mode` | full/media/enrich |
| `--status` | Xem trạng thái rồi thoát |
| `--dry-run` | Chỉ in kế hoạch, không gọi AI |

## 4. Cài Đặt AI Model

### Qua GUI
Tab "Đồng Bộ & Cài Đặt" → nút **⚙️ Cài Đặt Model**

Trong dialog:
- **Danh sách model**: Xem tất cả model đã cấu hình, tier (S/A/B), độ trễ
- **Bật/Tắt**: Tick checkbox để bật/tắt từng model
- **Sắp xếp**: Nút ↑ Lên / ↓ Xuống để đổi thứ tự ưu tiên
- **Tự động xếp**: Nút "🔀 Xếp theo Điểm" sắp xếp theo tier + tốc độ
- **Khôi phục**: Nút "↩ Mặc định" về danh sách mặc định
- **Auto Discover**: Nút "🔍 Auto Discover & Đánh giá" quét model mới từ Google API

### Panel Model Bị Khóa (Cooldown)
Hiển thị model đang bị khóa do lỗi 3 lần liên tiếp:
- 🔴 **Đỏ**: Đang bị khóa 30 phút
- 🟡 **Vàng**: Cảnh báo (lỗi 1-2 lần, chưa khóa)
- ✅ **Xanh**: Sẵn sàng sử dụng

Nút **"🔓 Mở Khóa Tất Cả"** để reset cooldown ngay lập tức.

### Qua settings.json
File `settings.json` → mục `ai.model_priority`:
```json
{
  "ai": {
    "model_priority": [
      {"name": "gemini-3.6-flash", "enabled": true, "tier": "S"},
      {"name": "gemini-3.5-flash", "enabled": true, "tier": "S"},
      ...
    ]
  }
}
```

## 5. Xử Lỗi Phổ Biến

| Lỗi | Nguyên nhân | Cách khắc phục |
|-----|------------|----------------|
| "high demand" | Gemini quá tải | Chờ `--wait-quota` hoặc đổi model |
| "quota_daily" | Hết quota ngày | Chờ đến nửa đêm GMT reset |
| "0 ngày" | Chưa có course | Chạy `--force-new` lần đầu |
| Model bị khóa | Lỗi 3 lần liên tiếp | Chờ 30 phút hoặc bấm "Mở Khóa Tất Cả" |
| Tất cả model lỗi | Hết quota tất cả model | Pipeline paused, chạy lại sau |

## 6. Render Lại Từ Đầu

1. Mở GUI hoặc dùng CLI với `--force-new`
2. Tick "Làm lại từ đầu (xóa khóa cũ)"
3. Bấm "▶ Tiếp tục / Bắt đầu sinh"
4. **Ảnh/audio cũ được giữ nguyên**, chỉ `course.json` mới được tạo

## 7. Tiến Độ & Resume

Pipeline tự động lưu checkpoint sau mỗi ngày:
- Nếu dừng giữa chừng, chạy lại sẽ **tiếp tục từ chỗ dừng**
- Không tạo trùng các ngày đã sinh xong
- Trạng thái được lưu trong `data/ai_courses/<slug>/_pipeline/`

## 8. Cấu Thúc Thư Mục Dữ Liệu

```
data/
├── ai_courses/
│   ├── _jobs.json              # Bảng job + budget bền
│   ├── tiếng_nhật/
│   │   ├── course.json         # Khóa học (tất cả ngày)
│   │   ├── progress.json       # Tiến độ học, điểm quiz
│   │   └── _pipeline/
│   │       ├── profile.json    # Hồ sơ ngôn ngữ (số ngày, chặng)
│   │       ├── backbone.json   # Khung giáo trình
│   │       ├── plan.json       # Danh sách ngày
│   │       ├── dead_models.json # Model bị khóa cooldown
│   │       ├── state.json      # Trạng thái pipeline
│   │       └── days/
│   │           ├── d0001/
│   │           │   ├── content.json
│   │           │   ├── quiz_ab.json
│   │           │   ├── quiz_cd.json
│   │           │   ├── images.json
│   │           │   ├── audio.json
│   │           │   └── dialogue.json
│   │           └── ...
│   └── tiếng_anh/
│       └── ...
├── media/
│   └── tiếng_nhật/
│       └── d0001/              # Ảnh + audio đã sinh
├── logs/
│   └── tiếng_nhật_*.log        # Log JSONL chi tiết
└── reviews/                    # SRS SM-2 state
```

## 9. Test Cases

Chạy kiểm tra toàn bộ:

```bash
# Kiểm tra cú pháp tất cả file
python -m py_compile ai/*.py api/*.py VocabApp.py

# Kiểm tra pipeline Nhật
python -m ai.pipeline --lang "Tiếng Nhật" --full --days 30 --force-new --no-media

# Kiểm tra trạng thái
python -m ai.pipeline --lang "Tiếng Nhật" --status
```

### Danh sách test case

| TC | Mục đích | Lệnh |
|----|----------|------|
| TC-01 | Chạy pipeline fresh Nhật 30 ngày | `--lang "Tiếng Nhật" --full --days 30 --force-new --no-media` |
| TC-02 | Chạy lại không force-new (resume) | `--lang "Tiếng Nhật" --full --days 30 --no-media` |
| TC-03 | Chạy với force-new | `--lang "Tiếng Nhật" --full --days 30 --force-new --no-media` |
| TC-04 | Tất cả model lỗi | Chạy khi hết quota, kiểm tra status = paused |
| TC-05 | Dừng giữa chừng | Bấm Dừng trong GUI, kiểm tra checkpoint |
| TC-06 | Ngôn ngữ đã có course | `--lang "Tiếng Anh" --full --mode media --workers 4` |
| TC-07 | py_compile | `python -m py_compile ai/*.py api/*.py VocabApp.py` |
| TC-08 | Course consistency | Kiểm tra mỗi ngày có vocab + quiz đầy đủ |

## 10. Hệ Thống Ảnh Minh Họa Tự Sinh

Vì Gemini free tier có `limit: 0` cho sinh ảnh, hệ thống tự sinh ảnh placeholder thay thế:

**Cấu trúc:**
- Ảnh được lưu tại `data/media/tiếng_nhật/dNNNN/`
- Mỗi ảnh PNG 512×512 chứa: từ vựng, phát âm, nghĩa tiếng Việt
- 12,600 ảnh cho 12,600 từ vựng (100% coverage)
- 6 ảnh placeholder cho 6 chặng học

**Script sinh ảnh:**
```bash
python generate_japanese_images.py
```
File script nằm tại `generate_japanese_images.py` (temporary).

**Cách hoạt động:**
- Mỗi vocab entry trong course.json có trường `image_ref` trỏ đến file ảnh
- Pipeline tự động đọc `image_ref` để hiển thị ảnh trong GUI
- Ảnh có thể bị thay thế bằng ảnh thật từ Wikipedia sau khi có kết nối internet
- Script có thể chạy lại để tạo lại ảnh nếu cần

**Lưu ý:**
- Ảnh placeholder là ảnh văn bản (không phải ảnh thực tế từ internet)
- Để có ảnh thật, cần chạy pipeline với `--mode media` và có kết nối internet
- Wikimedia có thể chặn IP sau ~30.000 request

## 12. Hệ Thống Âm Thanh TTS Tự Sinh

Vì Gemini free tier có hạn mực cho sinh audio, hệ thống tự sinh audio bằng edge-tts thay thế:

**Cấu trúc:**
- Audio được lưu tại `data/audio/tiếng_nhật/dNNNN/`
- Mỗi file MP3 chứa phát âm của một từ vựng tiếng Nhật
- 12,600 file MP3 cho 12,600 từ vựng (100% coverage)
- Giọng đọc: ja-JP-NanamiNeural (ph nữ, chất lượng cao)

**Script sinh audio:**
```bash
python ai/tts_selfbuilt.py
```

**Cách hoạt động:**
- Mỗi vocab entry trong course.json có trường `audio_ref` trỏ đến file MP3
- Mỗi vocab entry cũng có `media.vocab_audio[word]` để tra cứu nhanh
- Pipeline tự động đọc `audio_ref` để phát âm trong GUI
- Script có thể chạy lại để sinh lại audio nếu cần

**Lưu ý:**
- Can th_edge-tts yêu cầu kết nối internet đến Microsoft TTS service
- Sau khi sinh xong, audio có thể dùng hoàn toàn offline
- Concurrent processing (8 luồng) để sinh nhanh

---

## 13. Hệ Hoàn Toàn Không Cần Gemini AI

Sau khi đã sinh xong toàn bộ dữ liệu (course.json, ảnh, audio), ứng dụng có thể chạy hoàn toàn không cần API key Gemini:

```bash
# Chỉ xử lý media từ course.json đã có (không gọi AI)
python -m ai.pipeline --lang "Tiếng Nhật" --mode media --full --workers 4 --no-content
```

**Ưu điểm:**
- Không phụ thuộc API key Gemini
- Không bị chặn quota hay high demand
- Chạy hoàn toàn offline sau khi sinh dữ liệu
- Chi phí = 0

**App vẫn giữ khả năng dùng AI:** Có thể bật lại Gemini khi có key mới bằng cách không dùng `--no-content`.

---

## 14. Lưu Ý Quan LoN

- **Tiếng Nhật**: 1260 ngày cho toàn bộ lộ trình C2. Khuyên bắt đầu từ 30-60 ngày đầu.
- **Quota Gemini**: 20 call/ngày/project/model. 90 key ≈ 1.200-2.000 call/ngày thực tế.
- **Ảnh**: Gemini free tier có `limit: 0` cho sinh ảnh ⇒ dùng dict/placeholder thay thế.
- **Audio**: TTS hoạt động tốt (edge-tts, gemini-tts).
- **Resume**: Pipeline luôn resume từ chỗ dừng, không mất tiến độ.
