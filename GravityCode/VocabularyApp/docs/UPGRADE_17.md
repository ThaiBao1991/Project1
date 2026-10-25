# 📦 BÀN GIAO — VocabularyApp Update 17 (2026-10-22)

> **ĐỌC FILE NÀY TRƯỚC KHI LÀM BẤT KỲ VIỆC GÌ.** Nó chứa toàn bộ trạng thái kỹ thuật
> sau Update 17, cách chạy, giới hạn thật đã đo, và việc còn lại.
> Cùng với `projectLog.md` (nhật ký dự án) và `docs/UPGRADE_16.md` (kiến trúc chi tiết, quota, 28 bug).

---

## 0. TL;DR cho phiên sau

| Câu hỏi | Trả lời |
|---|---|
| App làm gì? | Quản lý từ vựng đa ngôn ngữ + sinh khóa học AI 6 chặng (3.010 ngày / 30.102 từ) cho 8 ngôn ngữ, kèm ảnh minh họa + âm thanh TTS + hội thoại roleplay. |
| **Update 17 đã thêm gì?** | **SRS ôn tập SM-2 vào GUI** (hàng đợi đến hạn, 4 nút Again/Hard/Good/Easy, streak, stats) + **Dẫn chứng Wikipedia/Wiktionary** (stage `evidence` opt-in, không tốn quota Gemini) + render "📚 Nguồn" trên desktop. |
| Test? | `test_ai_rich.py` **79/79** · `tools/verify_p0_fixes.py` **14/14** · `tools/verify_no_rewrite.py` PASS · `py_compile` OK |
| Còn thiếu gì? | Xem mục 7. Ưu tiên: dẫn chứng vào web (`web/script.js`) + `validate_dialogue` + grammar enrichment call riêng + chạy `--mode enrich`. |
| Lệnh quan trọng nhất? | `python -m ai.pipeline --all --mode media --full --allow-degraded --workers 6` |

---

## 1. THAY ĐỔI Update 17 (tóm tắt)

| File | Thay đổi |
|---|---|
| `database/review_store.py` | **Mới**: lưu trạng thái SRS (SM-2) bền theo ngôn ngữ (`data/reviews/<slug>.json`), API `record_review`/`due_queue`/`stats`/`reset`/`sync_from_vocab`. |
| `VocabApp.py` | Thêm nguồn học `SOURCE_SRS` + khung ôn tập SM-2 (4 nút, dự đoán khoảng cách, streak), nút đánh giá trong trắc nghiệm, nút "📚 Dẫn chứng", `App.update_stats()` đã triển khai, render "📚 Nguồn"/IPA chuẩn/từ nguyên trong `_render_lesson_text`. |
| `ai/evidence.py` | `attach_to_lesson()` thêm tham số `limit` (giới hạn từ/ngày), không xoá `etymology` AI đã có, chỉ ghi `ipa_ev` khi Wiktionary có IPA. |
| `ai/pipeline_evidence.py` | **Mới**: stage `STAGE_EVIDENCE = "evidence"` (Wikipedia/Wiktionary, cache bền, giới hạn 10 từ/ngày, KHÔNG raise). |
| `ai/pipeline_store.py` | Thêm hằng `STAGE_EVIDENCE` + `STAGES_OPTIONAL = (STAGE_EVIDENCE,)` (KHÔNG nằm trong `STAGES` mặc định ⇒ `--full` không bật evidence). |
| `ai/pipeline.py` | Stage evidence chạy sau content (khi bung qua `--evidence` / `--stages evidence`); CLI cờ `--evidence`. |

---

## 2. LỆNH ĐỘNG

### 2.1 Chạy app
```bash
cd "C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\VocabularyApp"
python VocabApp.py            # hoặc run.bat
```

### 2.2 Pipeline tự trị
```bash
# Tất cả 8 ngôn ngữ: giữ content, chỉ thêm ảnh + audio + hội thoại
python -m ai.pipeline --all --mode media --full --allow-degraded --workers 6

# Regenerate CONTENT để có IPA thật + khẩu hình + lỗi sai + mini_quiz (~3.010 call, ~2 ngày quota)
python -m ai.pipeline --all --mode enrich --full --allow-degraded --workers 4

# Thêm dẫn chứng Wikipedia/Wiktionary (opt-in, không tốn quota Gemini)
python -m ai.pipeline --all --mode media --full --evidence --workers 4

# 1 ngôn ngữ / 1 khoảng ngày
python -m ai.pipeline --lang tiếng_anh --mode media --full --from-day 1 --to-day 30

# Xem trạng thái + DoD
python -m ai.pipeline --all --status

# Kế hoạch (0 call, 0 ghi)
python -m ai.pipeline --all --dry-run
```

### 2.3 Verify
```bash
python test_ai_rich.py                    # 79 test, FAST < 60s
python tools/verify_p0_fixes.py           # 14 check hồi quy P0
python tools/verify_no_rewrite.py         # course.json KHÔNG bị ghi lại khi đọc
python -m py_compile VocabApp.py database\review_store.py ai\evidence.py ai\pipeline*.py
```

### 2.4 Công cụ SRS / dẫn chứng
```bash
python -m database.review_store --lang Tiếng Anh   # xem stats SRS
python -m database.review_store --lang Tiếng Anh --reset   # xoá tiến độ ôn
python -m ai.evidence --word cat --lang en         # tra dẫn chứng 1 từ (CLI)
```

---

## 3. TRẠNG THÁI DỮ LIỆU THẬT (đo 22/10/2026)

| Chỉ số | Giá trị |
|---|---|
| Khóa học | 8 ngôn ngữ · 3.010 ngày · 30.102 từ |
| Ảnh | 30.102/30.102 = 100% (chỉ ~200 ảnh THẬT, còn lại placeholder — Wikimedia chặn IP) |
| Audio | 30.102/30.102 = 100% (34.289 mp3, edge-tts 11/11 ngôn ngữ) |
| Hội thoại | 1.713/3.010 = 56% (đang chạy nền theo quota) |
| IPA thật | 0% — cần `--mode enrich` |
| Dẫn chứng | 0% — module `ai/evidence.py` đã có, stage opt-in chưa chạy toàn bộ |
| SRS | Module + GUI đã sẵn sàng, chưa có dữ liệu ôn thực tế |

---

## 4. GIỚI HẠN THẬT ĐÃ ĐO (đừng lặp lại sai)

- **Gemini ảnh**: mọi model `limit: 0` free tier ⇒ KHÔNG thể sinh ảnh qua Gemini API. Code giữ lại, dùng khi có key trả phí.
- **Gemini text**: 20 call/ngày / PROJECT / MODEL · pool 90 key = 10 project × 9 account (47 key OK) ⇒ ~1.200 call/ngày thực tế.
- **Wikimedia**: chặn IP sau ~30.000 request ⇒ stage evidence giới hạn 10 từ/ngày + cache bền + throttle (xem `ai/evidence.py`).
- **ToS**: Google/Grok đã trả CAPTCHA cho truy cập tự động ⇒ tầng scrape ảnh MẶC ĐỊNH TẮT.
- **TTS**: edge-tts 11/11 ngôn ngữ, không giới hạn quota ⇒ cascade đầu tiên.

---

## 5. KIẾN TRÚC PIPELINE (12 stage)

```
GLOBAL  : profile → backbone → plan
PER-DAY : content → [evidence] → quiz_ab → quiz_cd → images → audio → dialogue → media_verify → commit
```
- Stage `evidence` là **tùy chọn** (bật qua `--evidence`), chạy sau `content`, trước `quiz_ab`.
- `STAGES` (mặc định) = 10 stage không bao gồm `evidence`. `STAGES_OPTIONAL = ("evidence",)`.
- Media lỗi KHÔNG BAO GIỜ chặn nội dung chữ.

---

## 6. SRS ÔN TẬP (SM-2) — CÁCH DÙNG TRONG GUI

1. Mở tab **🎓 Học Tập** → chọn nguồn `🔁 Ôn tập SM-2 (lặp lại ngắt quãng)`.
2. Bấm **▶ Ôn tập** → hệ thống lấy từ vựng tự học + khóa học AI, tạo state mới cho các từ chưa có, xếp hàng đợi (quá hạn → mới đến hạn → từ mới).
3. Xem từ → bấm **🔄 Xem nghĩa** → chọn **😵 Quên / 😕 Khó / 🙂 Được / 😎 Dễ** ⇒ SM-2 tính ngày ôn tiếp theo, lưu bền vào `data/reviews/<slug>.json`.
4. Thống kê hiển thị: đến hạn hôm nay, streak, đã thuộc, ease trung bình.
5. Trong khóa học AI: bảng trắc nghiệm hiển thị 4 nút đánh giá cho từ vựng của câu hỏi hiện tại.

---

## 7. VIỆC CÒN LẠI (xếp theo ưu tiên)

### 7.1 NẮP NẾO CODE ĐÃ VIẾT (cao nhất)
| Việc | Module sẵn có | Cần làm |
|---|---|---|
| **Dẫn chứng vào web** | `ai/evidence.py` (7/7 test) | Render khối "📚 Nguồn" ở `web/script.js::renderCourseDay` (gần khối từ vựng), dùng `v.sources` / `v.ipa_ev` / `v.etymology`. |
| **Dialogue validate** | `media_schema.validate_dialogue()` | Gọi trong `ai/pipeline_media.py::run_dialogue_stage` → log cảnh báo + retry nếu AI không tuân thủ giới hạn (6 lượt / 220 ký tự). |
| **Grammar enrichment** | `build_quiz_prompt_ab/cd` làm mẫu | Tách 1 call AI riêng cho `common_mistakes`/`mini_quiz` (Gemini loại mảng lồng optional khi response lớn). |

### 7.2 CHẠY PIPELINE (cần quota)
```bash
python -m ai.pipeline --all --mode enrich --full --allow-degraded --workers 4
# → IPA thật + khẩu hình + lỗi sai + mini_quiz + dialogue ngắn (~2-3 ngày quota text)
```

### 7.3 Đa năng học tập (chưa làm)
Export/import (CSV/JSON/Anki .apkg/Markdown-Obsidian) · backup/restore nút GUI · tra từ điển offline · mode nghe/dictation/shadowing · quick-lookup Ctrl+K · favorites/tags · deep-link `vocab://` · đồng bộ tiến độ web↔desktop · PWA `sw.js` + `location.hash` · dark/light toggle.

### 7.4 Bảo mật (cần USER)
```powershell
# 1) Revoke token cũ: https://github.com/settings/tokens → tạo token MỚI
# 2) Xoá token khỏi history (phá hash commit cũ):
pip install git-filter-repo
git filter-repo --path GravityCode/VocabularyApp/settings.json --invert-paths
# 3) Token mới lưu NGOÀI git (đã .gitignore) hoặc nhập qua GUI
```

---

## 8. NGUYÊN TẮC BẮT BUỘC KHI SỬA TIẾP

1. Đọc `projectLog.md` + `docs/UPGRADE_17.md` trước. Cập nhật cả 2 sau khi sửa.
2. **Additive schema**: không đổi tên/xoá field cũ (`example_sentence`, `part_of_speech` là canonical).
3. **Migration 2 tầng** trong `ai/course_db.get_course()`: tầng A (cấu trúc) ghi đĩa; tầng B (v4/v5 mềm) **chỉ setdefault trong RAM** ⇒ 8 file `course.json` (135 MB) không bị ghi lại khi đọc.
4. **Slug**: dùng `ai/paths.lang_slug()` (1 nguồn) + `python -m ai.paths --export-js`.
5. **Media lỗi không chặn nội dung chữ.** Media/dẫn chứng là tăng cường, không phải điều kiện hoàn thành.
6. **Mọi ghi file** phải atomic (tmp + `os.replace`) + retry `PermissionError` (Windows).
7. **Mọi I/O mạng** phải có timeout + không raise ra ngoài (trả fallback an toàn).
8. **Tiếng Việt**: file UTF-8, `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` khi chạy CLI.
9. **Thread**: không đọc biến Tkinter từ thread; dùng `self.after(0, cb)`.
10. **Sau khi sửa**: chạy `python test_ai_rich.py` + `tools/verify_p0_fixes.py` + `python -m py_compile` trên file đã đụng.

---

## 9. FILE BẢN GIAO

| Tài liệu | Vai trò |
|---|---|
| `docs/UPGRADE_17.md` ⭐ | **BÀN GIAO CHÍNH** Update 17 (SRS + dẫn chứng) |
| `docs/UPGRADE_16.md` | Kiến trúc chi tiết, toàn bộ lệnh, giới hạn thật đã đo, 28 bug đã sửa, việc còn lại cũ |
| `projectLog.md` | Nhật ký dự án (Update 17 ở đầu file) |
| `ai/pipeline_log.py::EVENTS` | Danh sách event log chuẩn |
| `ai/paths.py` | Quy tắc slug/path duy nhất |
