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
| Test? | `test_ai_rich.py` **85/85** · `tools/verify_p0_fixes.py` **13/14** (L-A chờ data thật) · `tools/verify_no_rewrite.py` PASS · `py_compile` OK · `node --check` OK |
| Còn thiếu gì? | Xem mục 7. ~~Mục 7.1 XONG (27/10/2026)~~ Ưu tiên tiếp: chạy `--mode enrich` + `--grammar` (item 7.2, cần quota). |
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

# Bổ sung common_mistakes + mini_quiz cho ngữ pháp (stage opt-in, ~1 call/ngày)
python -m ai.pipeline --all --mode media --full --grammar --allow-degraded --workers 4

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

### 7.1 NẮP NẾO CODE ĐÃ VIẾT — ✅ HOÀN THÀNH 27/10/2026 (Update 17.1, xem projectLog)
| Việc | Module sẵn có | Cần làm |
|---|---|---|
| ~~**Dẫn chứng vào web**~~ ✅ | `ai/evidence.py` | XONG: `web/script.js::renderCourseDay` render khối `📚 Nguồn` + `🏛️ Từ nguyên` + `📖 ipa_ev` (CSS `.evidence-*`, escapeHtml toàn bộ). |
| ~~**Dialogue validate**~~ ✅ | `media_schema.validate_dialogue()` | XONG: `_validate_dialogues()` trong `ai/pipeline_media.py` — log cảnh báo + thử lại 1 lần khi vi phạm 6 lượt/220 ký tự; checkpoint lưu `validation`. |
| ~~**Grammar enrichment**~~ ✅ | `pipeline_grammar.py` | XONG: `STAGE_GRAMMAR_ENRICH` (STAGES_OPTIONAL) + `GRAMMAR_ENRICH_SCHEMA`/prompt/parse trong `course_generator.py` + stage trong `_run_day` + CLI `--grammar`. |

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

## Update 17.2 — Media UI/UX + dữ liệu Nhật + Model selector (2026-10-27)

> Bản nâng cấp 7 phase theo plan `vocabapp-japanese-media-ux-plan.md`. Chi tiết đầy đủ trong `projectLog.md`.

### P1 — Media UI/UX
- **Mới** `ai/media_card.py` (thẻ từ PNG CJK, gradient, cache SHA-1 `data/media/_cards/`), `ai/media_resolver.py` (`m_*`/rel/abs/thiếu/traversal); `ai/paths.py` thêm `MEDIA_DIR/AUDIO_DIR/CARDS_DIR`.
- `VocabApp.py`: StudyTab media strip (thẻ 110×140, 🔊 Nghe cả dãy, ring highlight, `DEBUG_MEDIA_PATHS=1`), `play_audio_file/stop_audio`, `jp_font()` (CJK + Latin tách font), `MediaViewerDialog`; `on_close` dừng audio. Web parity `mediaEntry/mediaUrl/mediaAudioHtml`.

### P2 — Khôi phục 444 ngày thật (0 API)
- **Mới** `tools/recover_japanese_course.py`: manifest → course (SLUG chuẩn), quiz đúng key `vocab/pattern/common/grammar/mixed`, **assertion chặn từ giả** (`単語N`/`tangoN`/"Nghĩa từ vựng số"); seed `data/seed/ja/dict.json` (105 từ).

### P3 — canonical_slug, hết split-brain Nhật
- `ai/paths.py`: `LANG_ALIASES`/`canonical_slug`/`JAPANESE_CANONICAL`, `web_slug_table()` dedupe; `course_db.course_dir`, `media_store.media_dir/rel_path_for`, `database._get_json_path` đều qua canonical; `get_available_languages()` gộp alias + display chuẩn.
- **Mới** `tools/fix_japanese_slug.py` (dry-run mặc định; `--apply` archive + merge vocab có backup).

### P4 — Mở rộng 445 → 1260 ngày (0 API, <60s)
- **Mới** `tools/extend_japanese_course.py`: pool `dict.json` + `n5..n1_pool.json` + `pool_<tên>.json` (match `startswith("pool_")`); `%7` ôn, `%30` checkpoint đúng 20 câu; **không trùng** từ; RNG cố định (idempotent); hết pool → ngày ôn; guard khi đủ 1260; `--status/--dry-run/--apply/--start-day/--to-day`.
- Nhưng nhớ: `'pool_extra.json'.endswith('_pool.json')` là **SAI** — dùng `startswith("pool_")`; `glob` hỏng với temp dir trên Python 3.14 → `os.listdir`.

### P5 — Model selector (hết cảnh lặp 3.6/3.5)
- **Mới** `api/model_catalog.py`: GET `/v1beta/models` phân trang, lọc `generateContent`, cache 24h `data/model_catalog.json`; `infer_tier` (**pro→S · lite→B — check TRƯỚC flash · flash→A · khác→C; `-preview/-exp` hạ 1 bậc**); `rank_models` = tier + version + latency(<800ms bonus) − dead − preview; `build_run_priority` (Tự động → `[]`, Mới nhất/Ổn định/Rẻ–nhanh/<tên>); CLI `--status/--refresh/--rank`.
- `ModelSettingsDialog`: 7 cột (thêm `Version`, `Trạng thái` 🟢 sống/🟡 cooldown/⚫ chết/🚫 preview), bộ lọc Tất cả/Mới nhất/Ổn định/Rẻ–nhanh/Đang bật (`iid` = index thật ⇒ move/enable đúng lúc đang lọc), nút **🔄 Dò model mới** (catalog, không benchmark, dedupe + re-rank).
- `CourseGenerationDialog`: OptionMenu **Model** — ghi TẠM `model_priority` cho run rồi trả về trong `_done`/đóng dialog (`_model_override`/`_restore_models`); `_load_catalog_async` không khóa UI.
- `api/gemini_safe.py`: log fallback chỉ rõ model kế tiếp (`⏱ 'm1' fail (timeout >90s) → thử 'm2'`); **FIX NameError** biến `model`/`status_code` trong 2 nhánh QUOTA của `request()` — 429 tốc độ từng crash coordinator.

### P6 — Pipeline
- `GenerationStopped` import module-level (hết NameError khi Stop giữa chừng).
- CLI thêm `--offline` (0 API — chỉ `media_verify`), `--days` mặc định **60**, guard `target_days > budget` in cảnh báo khước từ treo im lặng; offline không cần key.
- `evaluate_dod().plan_complete` hết công thức hằng-True (`len==len`); progress.json ghi trạng thái trong `finally` — run paused/aborted không còn để bar 0%.

### P7 — Dọn & test
- **Mới** `tools/dedupe_methods.py` (AST, dry-run mặc định, `--apply` có `.bak`): VocabApp/pipeline/course_generator sạch.
- Kiểm tra: `test_ai_rich.py` **85/85** · resolver 6/6 · card 6/6 · recover 6/6 · slug 6/6 · extend 7/7 · **model_catalog 13/13** · `verify_no_rewrite.py` PASS · `node --check` OK (: L-A = 13/14 phụ thuộc data thật máy chính).

### Việc còn lại (chạy trên máy chính có data thật)
```powershell
python tools\fix_japanese_slug.py          # dry-run trước → --apply
python tools\test_extend_course.py         # rồi:
python tools\extend_japanese_course.py --status   # cần n5..n1_pool.json thật (~12.500 từ)
python tools\extend_japanese_course.py --dry-run  # → --apply
python -m ai.pipeline --lang tiếng_nhật --status
python -m api.model_catalog --refresh      # dò catalog thật (cần key)
# Dừng process cũ ghi log rác data/logs/nhật_* trước khi migrate (PID 25072 theo plan).
```

---

## 7.3. FIX SINH KHÓA HỌC AI — CONTENT RỖNG KÉO THEO QUIZ/ẢNH/AUDIO RỖNG (2026-10-30)

### Triệu chứng
- Bấm **Sinh khóa học AI** → `0/0 ngày`, `calls=1`, `ảnh=0`, PAUSED, `course.json` 303 byte.
- Khóa mới có ngày nhưng `vocab=0` ⇒ quiz 4 loại, mẫu câu, câu thông dụng, ngữ pháp, ảnh, audio đều rỗng.
- Khác với khóa cũ (450 ngày) vẫn có content + quiz vì dữ liệu cũ đã sinh sẵn.

### Nguyên nhân
1. `_run_day` gọi `build_content_prompt(..., phase)` **7 tham số** nhưng hàm chỉ nhận 6 ⇒ `TypeError` ⇒ pipeline abort với `calls=0`.
2. Model đôi khi trả `vocab: []` dù schema `required`; pipeline cũ vẫn checkpoint content `done` ⇒ `_run_day` trả `None`, không chạy quiz/media.
3. `parse_content_json` không kiểm tra vocab; `_ask_with_retry` retry đúng model vừa trả rỗng.
4. `_model_score` phạt latency quá nặng: model 0 success (3.8 timeout) vẫn xếp trên model chạy được (flash-lite) ⇒ mỗi run mất thêm 120s.
5. 403 `free tier is not available` bị thử hết 8 model trên cùng key thay vì khóa account và xoay key.

### Đã sửa
- `ai/course_generator.py`:
  - `build_content_prompt` nhận thêm `phase`; `ai_lang_name()` bỏ hậu tố `_smoke/_test/_demo` + đổi `_` → khoảng trắng để model không hiểu nhầm là ngôn ngữ lạ.
  - `parse_content_json` giữ partial content (patterns/common/grammar) khi vocab rỗng; thêm `VOCAB_FILL_SCHEMA`, `build_vocab_fill_prompt`, `parse_vocab_json`.
  - Sanitize tên ngôn ngữ trong prompt quiz/dialogue/grammar.
- `ai/pipeline.py`:
  - `_run_day` gọi prompt nhỏ **chỉ sinh vocab** khi content thiếu; nếu vẫn 0 từ ⇒ **không checkpoint**, trả `None` để retry, không tạo ngày rỗng.
  - `_ask_with_retry` báo `coord.report_invalid_output(model)` khi parse lỗi/rỗng.
- `api/gemini_safe.py`:
  - `report_invalid_output()`: ghi fail + cooldown 180s cho model trả output sai.
  - `_model_score`: model chưa từng thành công xếp cuối (`-100000`); phạt latency có trần 500.
  - `is_project_billing_error()` + early return trong `_try_models`; `is_model_restriction` nhận `free tier is not available` ⇒ khóa account, xoay key.
- `tools/smoke_test_pipeline.py`: smoke test thật 1 ngày (khóa tạm `tiếng_nhật_smoke`), stages `content → quiz_ab → quiz_cd → images → audio → dialogue → media_verify`.

### Kết quả smoke thật (2026-10-30)
- **12 từ thật**, 0 từ giả.
- **10 mẫu câu**, **10 câu thông dụng**, **2 bài ngữ pháp**.
- **Quiz 40 câu**: vocab 10 / pattern 10 / common 10 / grammar 10.
- **Ảnh 12/12 từ** có `image_ref`; **audio 12/12 từ** có `audio_ref`; **24/24 file media tồn tại**.
- **1 hội thoại**; `days=1/1`; `calls=12`.
- `status=paused` / `DoD=False` là do smoke cố ý bỏ `profile/backbone/plan` (chạy per-day), không phải lỗi sinh nội dung.

### Test hồi quy
`test_ai_rich.py` **85/85** · adaptive **7/7** · resolver **6/6** · card **6/6** · recover **6/6** · slug **6/6** · extend **7/7** · model_catalog **13/13** · `py_compile` OK.

### Còn lại
- **1400 ngày**: profile tiếng Nhật hiện 420 ngày; `--days 1400` chỉ cắt plan, chưa scale backbone. Cần Phase 3: scale `stage_days` + chunk AI adapt/gap theo lô ~80 slot.
- Chạy full trên máy chính có data thật + pool JLPT (~12.500 từ).

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
