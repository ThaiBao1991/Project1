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

## 7.5. FIX SINH KHÓA HỌC AI — CONTENT RỖNG KÉO THEO QUIZ/ẢNH/AUDIO RỖNG (2026-10-30)

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
  - `is_project_billing_error()` + early return trong `_try_models`; `free tier is not available` được xử lý riêng ở mục 7.6 (tạm nghỉ KEY 24h, không khóa cả account).
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
- **1400 ngày**: profile tiếng Nhật đã sinh được 1400 ngày / 6 chặng `[100,200,300,350,250,200]`, backbone 1406 chủ đề (mục 7.6). Vẫn cần chạy full trên máy chính có data thật + pool JLPT (~12.500 từ).
- Validate từ vựng với từ điển/pool để chặn từ bị cắt như `ホテ` (đáng lẽ `ホテル`).

---

## 7.6. FIX ABORT SAU BACKBONE, ẢNH THẬT & XOAY KEY (2026-10-30)

### Triệu chứng
- GUI báo `0/0 ngày, calls=2, ảnh=0`, ABORTED, dù log đã sinh xong profile 1400 ngày + backbone 1406 chủ đề.
- Khóa mới toàn ảnh placeholder (chữ cái), không phải ảnh minh họa thật.

### Nguyên nhân
1. `_get_item_phase` là hàm **lồng** trong `generate_course()`, nhưng `ai/pipeline.py::_stage_plan` import ở cấp module ⇒ `ImportError: cannot import name '_get_item_phase'` sau khi đã đốt công sinh profile/backbone. `calls=2` là bộ đếm budget (2 lượt content), **không phải** số lần thử key/API.
2. `dictionary_image.WIKI_HOSTS` dùng tên hiển thị (`"Tiếng Nhật"`), còn pipeline truyền slug (`"tiếng_nhật"`) ⇒ rơi về `en.wikipedia.org` ⇒ không tìm được ảnh bài viết tiếng Nhật ⇒ placeholder. Cache âm lưu `None` vĩnh viễn nên lỗi 429/timeout tạm thời cũng thành placeholder mãi.
3. `free tier is not available` là lỗi cấp **PROJECT** (Google xét eligibility theo Google Cloud project), nhưng code khóa cả Gmail account 60 phút ⇒ bỏ qua oan các key khác (project khác) trong cùng account. Bản vá đầu tiên lại block **vĩnh viễn** key — quá tay, vì bật billing là key cũ dùng lại được.

### Đã sửa
- `ai/course_generator.py`: đưa `_get_item_phase` ra cấp module; `generate_course()` truyền `phase_indices`; pipeline import được.
- `ai/dictionary_image.py`: chuẩn hóa tên ngôn ngữ (`tiếng_nhật` == `Tiếng Nhật`) cho Wikipedia/Wiktionary; `IMAGE_CACHE_VERSION=2`; cache âm có TTL 7 ngày; deadline mỗi từ 10 → 20s.
- `api/gemini_safe.py`: `free tier is not available` → `block_key(ttl=24h)` (tạm nghỉ, `blocked_keys.json` có `until`) + bỏ qua key đó, **không** khóa account, **không** block vĩnh viễn; vẫn early-return trong `_try_models` để không thử 8 model trên cùng project chết. Áp dụng cả đường ảnh.
- Đã kiểm chứng thực tế 2 key bị lỗi × 4 model (`gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-flash-lite-latest`, `gemini-4-argon`): **cả 4 đều 403 cùng message** ⇒ lỗi cấp project, không phải model cũ. Google docs `troubleshooting#project-unavailable` cũng ghi rõ: tạo key mới trong cùng project không sửa được, phải bật billing.
- Trước khi tạm nghỉ key, code thử tối đa **1 model kế** để xác nhận: model kế chạy được ⇒ chỉ model cũ lỗi, key vẫn giữ; cả 2 cùng 403 ⇒ mới tạm nghỉ key 24h. Tránh khóa oan key vì một model cụ thể.

### Kết quả kiểm chứng (2026-10-30)
- Plan: **1406 ngày** (1400 template + 6 AI bổ sung).
- Ngày 13: **12 từ**, 10 mẫu câu, 10 câu thông dụng, 2 ngữ pháp, **quiz 40 câu** (10/10/10/10), 12 audio, 1 hội thoại, **0 từ giả**.
- Ảnh: **11/12 ảnh thật** (Wikipedia/Commons), 1 placeholder (`ホテ` — nhiều khả năng bị cắt từ `ホテル`).
- `test_ai_rich.py` **85/85** · adaptive **7/7** · model_catalog **13/13** · resolver **6/6** · `py_compile` OK.

### Xoay key — hành vi hiện tại
| Tình huống | Phạm vi khóa | Thời gian |
|---|---|---|
| 429 RPM/TPM | 1 key | ~60-65s (`retryDelay`) |
| 429 quota ngày | account | 60 phút (Google thực tế reset 00:00 Pacific) |
| 403 denied access | account | vĩnh viễn (`blocked_accounts.json`) |
| 401/403 invalid key | key | vĩnh viễn (`blocked_keys.json`) |
| 403 free tier not available | key (project) | tạm nghỉ 24h (`blocked_keys.json` có `until`) — bật billing là key cũ dùng lại được |
| 503/timeout | model | 90-300s (model cooldown) |

- Trong 1 key: `_try_models` thử lần lượt model (adaptive order). 429 daily → thử model kế (mỗi model một bucket quota riêng). 403 free-tier → dừng ngay vì cả project chết, không thử 8 model.
- Không "chỉ khóa model": cùng project thì model cũ lẫn mới đều 403 (đã test), nên khóa model sẽ lặp lại 8-10 lần vô ích. Khóa key có TTL là đúng phạm vi project, và vẫn tự phục hồi sau khi bật billing.
- Lỗi model cũ bị khai tử (`no longer available to new users`, 404) là lỗi **khác** → chỉ cooldown model, không đụng key.
- Giữa các account: `request()` lấy key từ pool, bỏ qua invalid/blocked/cooldown, thử tới khi thành công hoặc hết key. `MAX_REQUEST_SECONDS=300` giới hạn 1 request; nếu mọi key timeout 120s thì có thể dừng sau 2-3 key.
- Lock account 60 phút là **in-memory**; restart app sẽ reset. Blocklist invalid key là vĩnh viễn; free-tier là TTL 24h nên tự thử lại.

### Còn lại
- Validate vocab với từ điển/pool để chặn từ bị cắt (`ホテ`).
- Persist account cooldown nếu cần giữ qua restart.
- Chạy full 1400 ngày trên máy chính với pool JLPT thật.

---

## 7.7. PANEL CHỌN ĐƯỢC (TỪ VỰNG/NGỮ PHÁP) + LOG XOAY KEY + MERGE GITHUB (2026-10-31)

### Panel từ vựng chọn được (thay dải thẻ ngang — theo yêu cầu "10 từ = 10 lựa chọn")
- `StudyTab._render_vocab_panel(lesson)` mode-aware: 📚/📑 → `_render_vocab_rows`; 📖 → `_render_grammar_rows`; 🎧 → panel ẩn (`pack_forget`, dlg_panel đảm nhiệm).
- Mỗi dòng từ: `[ảnh thật 44px (Wikipedia/word-card fallback)] [từ + reading] [nghĩa VI] [▶]` — **click bất kỳ đâu trên dòng** → `MediaViewerDialog` (ảnh 384×384, ví dụ, ←/→, Esc).
- `_media_ring(idx)` highlight dòng đang phát bằng `fg_color` (bug cũ `border_color="transparent"` → ValueError bị nuốt). Badge cover 🖼🔊 + seq "🔊 Nghe cả ngày" giữ nguyên trên panel mới.

### Panel ngữ pháp click → chi tiết
- `_render_grammar_rows(lesson)`: mẫu câu 📝 (`sentence_patterns`) + bài ngữ pháp 📐 (`grammar`, dict đơn → list) — mỗi dòng click → `GrammarDetailDialog` (lớp mới, UX như MediaViewerDialog).
- `GrammarDetailDialog`: giải thích · ví dụ JP+VI (🔊 `speak_word`) · `common_mistakes` ❌/✅ · `mini_quiz` 🧠 · ←/→ chuyển mục · Esc đóng.

### Log AI đang dùng key/account nào (`api/gemini_safe.py`)
- `GeminiCoordinator._log_key_pick(pool, key_obj, email)` — gọi trong `request()` + `request_image()` sau `pool.pick()`:
  `🔑 Đang dùng key của account: user@gmail.com [key 3/90]` (lần đầu) · `🔄 Đổi sang account: …` (khi đổi) — **chỉ hiện khi đổi**, không spam mỗi request.
- Mục đích: người theo dõi bằng mắt thấy rõ xoay vòng account, không để 1 account dùng liên tục.

### Merge `origin/master` vào branch (chuẩn bị đẩy GitHub)
- 6 file conflict giải kiểu **giữ cả 2 phía**: VocabApp.py (header ngày master + media/dlg panel branch) · gemini_safe.py (adaptive probe HEAD + dead-model tracking master — 2 hệ thống độc lập đều dùng ngoài conflict) · database.py (canonical dedup + trả dict `{display, slug, num_days}` — App sort theo `num_days`, dùng `slug` làm `current_language`) · pipeline.py (offline guard + wait_quota) · course_generator.py (`ai_lang_name`) · projectLog.md.
- Test: `test_ai_rich` 85/85 · `tools/test_3mode` **41/41** (17 test mới) · `test_slug_canonical` 6/6 · `py_compile` OK.

---

## 7.8. FIX NÚT CHẾ ĐỘ · BÙ ẢNH THẬT · QUẢN LÝ API KEY (2026-11-01)

### 4 nút chế độ — hàng riêng, to, có trạng thái đang chọn
- Bug: nút pack vào `head` (height=64) sau `head_inner` (`expand=True`) bị nén ~60px.
- Fix: `mode_row` riêng 52px dưới header · nút 150×40 bold 14 · `_mode_btns` + `_highlight_mode(mode)` (gọi trong `_load_mode`) tô nút đang chọn nền accent.

### Bù ảnh thật — `tools/fix_placeholder_images.py` (miễn phí, 0 key)
- Nguyên nhân placeholder: (1) **cache âm** `dictionary_image` — Wikimedia 429 lúc sinh khóa ⇒ "không có ảnh" bị nhớ 7 ngày (`NEGATIVE_CACHE_TTL`); (2) từ kana/từ trừu tượng Wikipedia thực sự không có ảnh.
- Tool: đếm before → `--refresh-cache` purge cache âm của từ ngày đang xử lý → `_stage_dict` LIVE (`providers=["dict"]`, không đè ảnh thật) → course.json atomic + `.bak1` → `media_store.flush_index()` (bắt buộc — không flush thì manifest mất entry mới khi thoát).
- Kết quả thật 24 ngày: 18 → 35 ảnh thật · placeholder 194 → 182 (182 còn lại xác minh LIVE là không có nguồn miễn phí; thumbnail fallback word-card). Lệnh:
  `python tools/fix_placeholder_images.py "tiếng_nhật" --days 1-24 --refresh-cache`

### Quản lý API key — `ApiKeyManagerDialog` (VocabApp.py)
- Nút 🗂️ ở tab Cài đặt · ghi thẳng **AskCpl settings.json** (nguồn chung AskCpl/GetHtmlFromUrl/VocabApp).
- Bảng email · key mask · 🟢/🔴 · latency ms · Thêm/Sửa/Xóa/Bật-Tắt · 🔍/⚡ kiểm tra (thread nền, gọi thật Gemini "Hi") · 💾 Lưu atomic + backup `.bak1`, giữ nguyên khóa khác, key encode `ENC:`.
- Helpers thuần test được: `keymgr_mask_key/decode_key/load_keys/save_keys/validate_key`; test `tools/test_key_manager.py` **42/42**.
- Regression: test_3mode 41/41 · ai_rich 85/85 · slug 6/6 · py_compile OK.

---

## 7.9. FIX AUDIO 0 TRACK → PIPELINE PAUSED + TRÙNG KEYWORD GUI (2026-11-02)

### Vì sao `PAUSED, DoD=False` — audio 0 track mọi ngày
- **Bug 1 (gốc):** `pipeline_media.py` gọi `synthesize(..., voice="ja-JP"/"vi-VN")` nhưng `synthesize()` **không có tham số `voice`** (thêm trong commit `704b2ad`, sau lần chạy 30/10) → `TypeError` bị `except: return {}` **nuốt im lặng** → 0 track → `media_verify` đánh audio `pending` (`thiếu 12 ref`) → check `all_days_audio=False` → `status = "paused"`. (Các ngày done 12 tracks là di vật từ trước bug.)
- **Bug 2 (ẩn):** `tts_bilingual_mode=True` (default) → `_one` trả **tuple** `(res_jp, res_vi)` nhưng tracks loop gọi `r.get("engine")` trên tuple → `AttributeError` (chưa từng nổ vì bug 1 xảy ra trước).
- **Bug 3 (ẩn):** `_audio_items_for` không copy `meaning_vi` → fallback `it["text"]` ⇒ đọc lại từ Nhật bằng giọng Việt; `voice="ja-JP"` hardcode ⇒ khóa Trung/Hàn bị đọc giọng Nhật.

### Đã sửa
- `ai/tts_config.py`: **`voice_conf_for_locale(locale)`** — BCP-47 → `LANG_VOICES` (prefix `edge_voice` → `sapi` → `gtts_lang`), fallback `DEFAULT_VOICE`, không ném lỗi.
- `ai/tts_generator.py`: **`synthesize(..., voice: str = "")`** — locale tùy chọn; rỗng → `voice_for(language)` như cũ (không đổi hành vi caller cũ).
- `ai/pipeline_media.py`: `_loc_target` từ `voice_for(language)["edge_voice"]` (bỏ hardcode) · `_one` log lỗi (`⚠️ Lỗi TTS`, closure list, không race 4 luồng) · tracks loop **tách tuple → 2 track** (JP → `audio_ref`, VI → `meaning_audio_ref` field phụ) · `_audio_items_for` copy `meaning_vi`.
- `VocabApp.py`: `btn/lbl/h1/h2` → `opts = dict(...); opts.update(kw)` **chống trùng keyword** (`CTkButton() got multiple values for 'width'` — crash ModelSettingsDialog); fix `width` lọt `.pack()` trong bảng key.
- **`tools/test_gui_smoke.py` (mới):** mở 12 dialog + `App()` toàn tab → bắt crash lúc khởi tạo · **15/15**.

### Kết quả thật
- Ngày 11 test: **0 → 24 track** (song ngữ JP+VI). Chạy lại 24 ngày: **`DONE 24/24 … DoD: True`** (458.6s) — trước: `PAUSED, DoD=False`.
- `--status`: **✅ all_days_audio** · ❌ all_days_images (38 từ kana/abstract không có ảnh nguồn miễn phí — degraded, xem 7.8).
- Checkpoint 25/27 done · **440 tracks** · 2 file ngày 25-26 mồ côi từ plan cũ 26 ngày (course 24 ngày, không ảnh hưởng DoD).
- Test: smoke **15/15** · key_manager **42/42** · 3mode **41/41** · ai_rich **85/85** · slug **6/6** · compile OK.

---

## 7.10. ĐỒNG BỘ KEY 2 CHIỀU GETHTMLFROMURL ↔ ASKCPL (2026-11-03)

### Mục tiêu
Nút bấm trong `ApiKeyManagerDialog` để hợp nhất key giữa 2 nguồn chung: **GetHtmlFromUrl** `config/gemini_keys.json` (mảng JSON `{id,key,email,status,note,cooldown_until}`) ↔ **AskCpl** `settings.json` (`gemini.api_keys`). Cùng chuẩn key mã hoá `ENC:` (đảo + base64) với `core/key_manager.py` của GetHtmlFromUrl.

### Thanh công cụ (dòng 2 — `ctrl2`)
Dòng 1 đã ~742px (cửa sổ 960px) nên 2 nút đồng bộ tách hàng riêng:
- **📥 Nhận từ GetHtmlFromUrl** → `keymgr_sync_from_gethtml()` — ghi thẳng AskCpl settings.json.
- **📤 Gửi sang GetHtmlFromUrl** → `keymgr_sync_to_gethtml()` — ghi thẳng gemini_keys.json.
- Cả 2: thiếu file/thư mục → log ❌ rõ ràng (không ném), thành công → reload + render bảng.

### Helpers mới (`VocabApp.py`, thuần — test không cần GUI)
| Helper | Vai trò |
|---|---|
| `keymgr_gethtml_keys_path()` | đường dẫn tuyệt đối tới `gemini_keys.json` (không hardcode ổ đĩa) |
| `keymgr_load_gethtml_keys()` | đọc mảng JSON — thiếu/hỏng/sai kiểu → `[]` (không ném) |
| `keymgr_save_gethtml_keys()` | ghi atomic (tmp + `os.replace`) + backup `.bak1` 1 lần |
| `_keymgr_merge(src, dst, fields=None)` | hợp nhất theo **key thô** (decode trước): trùng → **giữ bản dst** (disabled/cooldown không bị đổi) chỉ lấp email/note **trống**; mới → append, encode `ENC:`, **tự sinh id** khi thiếu/trùng; `fields` lọc field khi sang phía GetHtmlFromUrl (error_msg/latency_ms không lọt) |
| `keymgr_sync_from_gethtml(askcpl, gethtml="")` | trả `(added, total, changed)` — idempotent, chỉ ghi khi `changed` |
| `keymgr_sync_to_gethtml(askcpl, gethtml="")` | trả `(added, total, changed)` — như trên, phía GetHtmlFromUrl |

### Kết quả thật
- **Dry-run 2 file THẬT** (chỉ đọc): GetHtmlFromUrl **197 key** = AskCpl **197 key**, giao 197/197, cả 2 chiều `+0, changed=False` → 2 nguồn đã đồng bộ, bấm nút sẽ báo "Không có key mới" (an toàn, không ghi gì).
- **Test `tools/test_key_manager.py`: 42 → 80/80** (section 7 mới, file tạm — không đụng file thật): path/load/sanitize, save atomic + `.bak1`, merge dedup key thô (thô vs ENC: cũng nhận), keep dst vs lấp chỗ trống, id tự sinh + chống trùng id, sync 2 chiều, idempotent chạy lại, file thiếu không ném, giữ khóa khác (`github.token`), lọc field lạ, roundtrip tập key thô bằng nhau, thiếu `gemini.api_keys` không ném.
- **Bug test đã bắt + sửa**: biến `total` trong `main()` trùng tên bảng đếm toàn cục → `TypeError` cuối file; expectation email fixture sai (email 2 phía giống nhau ⇒ test "giữ bản dst" vô nghĩa → đổi fixture phân biệt rõ keep vs fill).
- **Suite xanh**: key_manager **80/80** · smoke **15/15** · 3mode **41/41** · ai_rich **85/85** · slug **6/6** · `py_compile` OK.

---

## 7.11. FIX LỜI GHI 429 "TỐC ĐỘ" NÓI DỊC + XOAY 197 KEY VÔ TẬN (2026-11-05)

### Triệu chứng (log người dùng)
```
⚠ 'gemini-3.5-flash' fail (429 tốc độ) → thử 'gemini-flash-lite-latest'…
🔄 Đổi sang account: …[key 173/197] → key 93 → 192 → 1 → 85 → 22 → 35 … (lặp vô tận)
```
Log hứa "thử model kế" nhưng thực tế **xoay sang account khác** và không bao giờ thử model kế; key không bao giờ được cooldown ⇒ cùng một model đầu bảng (adaptive luôn xếp `gemini-3.5-flash` lên đầu) bị đập lại trên mọi account.

### Nguyên nhân (4 lỗi, đã đọc code xác minh)

| # | Vị trí | Lỗi |
|---|---|---|
| 1 | `_try_models()` | **Không có nhánh `QUOTA_RATE`** → 429 tốc độ rơi thẳng xuống `return` cuối hàm ⇒ bỏ cuộc sau đúng 1 model (trong khi 429 quota ngày và 503/timeout đều có nhánh `continue` sang model kế) |
| 2 | `request()` · nhánh `QUOTA_RATE` | `if _mi < len-1: log("→ thử model kế"); continue` — nhưng `continue` là vòng **NGOÀI** → `pool.pick()` **đổi account**, không thử model kế. `_mi` còn tính trên `self._models` tĩnh trong khi `_try_models` chạy theo thứ tự **adaptive** (sai lệch index). Hệ quả: `lock_key()` chỉ nằm sau nhánh này ⇒ **gần như không bao giờ chạy** → key không cooldown |
| 3 | `request()` · nhánh `QUOTA_DAILY` | Cùng cấu trúc "nói dối" y hệt (bug tiềm ẩn cùng gốc, index lệch adaptive) |
| 4 | `pace()` | `base = random.uniform(0.6, 1.0) × interval` ⇒ có thời điểm chạy nhanh hơn target tới **1.67×** → burst vượt 15 RPM/project → chính nó sinh ra 429 tốc độ dồn dập |

**Lỗi 5 (phát hiện thêm khi verify — nghiêm trọng nhất, ảnh hưởng production):**
`request()` gọi `pool.sync(loader())` **mỗi vòng lặp**, còn `_load_gemini_keys()` trả về `dict MỚI` mỗi lần (`item = dict(k)`) ⇒ `cooldown_until` mà `lock_key()` ghi trên dict cũ **bị vứt ngay vòng kế**. Tức cooldown 65s **vô hiệu 100% trong production** — mọi key "cooldown" vẫn bị pick lại. Repro sẵn có: `tools/test_key_cooldown.py`.

### Đã sửa (`api/gemini_safe.py`)

1. **`_try_models()`** — thêm nhánh `QUOTA_RATE`: `_cooldown_model(model, retry_delay_from(msg))` rồi `continue` sang **model tiếp theo trên CÙNG key** (đúng lời log đã hứa). Chỉ trả `QUOTA_RATE` ra ngoài khi đã hết model.
2. **`request()` · `QUOTA_RATE`** — xoá hẳn nhánh `_mi < len-1 → continue` nói dối. Khi mọi model đã fail tốc độ ⇒ `lock_key(key_obj, retry_delay)` (65s) **thật** + `exclude` + đổi key thật, log truthy `"Cooldown riêng key, đổi key..."`.
3. **`request()` · `QUOTA_DAILY`** — xoá nhánh tương tự ⇒ đi thẳng tới `_lock_account(ACCOUNT_COOLDOWN=3600)` + `_mark(exhausted)` + `exclude`.
4. **`pace()`** — `uniform(0.6, 1.0)` → **`uniform(0.85, 1.15)`**: không bao giờ vượt target quá 15% (trước: 1.67×).
5. **`AccountPool`** — thêm `_key_cooldown: {raw_key → unlock_ts}` **level-pool**; `lock_key()` ghi cả vào map này; `sync()` dọn entry hết hạn và **dán lại `cooldown_until` vào dict mới**. (Cấp account vốn đã sống nhờ `self._cooldown` dict — chỉ cấp key là bị mất.)

### Test mới — `tools/test_quota_rate.py` (mock `requests.post`, 0 mạng thật) **36/36 PASS**

| # | Case |
|---|---|
| 1 | model A 429-tốc-độ → model B 200 ⇒ **OK trên CÙNG key**, log có `→ thử`, **KHÔNG** có `Đổi sang account`, key không bị khóa oan (2 POST, cùng key) |
| 2 | mọi model 429-tốc-độ ⇒ `_try_models` trả `QUOTA_RATE` (hết rơi `return` mập mờ), đã thử đủ 2 model |
| 3 | mọi model 429-tốc-độ ⇒ `lock_key` 65s **thật** + `Đổi sang account: b@` thật + cooldown **sống sót qua `pool.sync(dict mới)`** |
| 4 | mọi model 429-quota-ngày ⇒ khóa account ~3600s + đổi key; mọi log `→ thử` đều có tag account (thật); không còn log `…` cấp `request()` |
| 5 | Regression: 429 quota ngày model A → model B OK cùng key |
| 6 | `pace()` kịch bản xấu nhất (uniform lấy cận dưới) ⇒ nghỉ ≥ 0.85 × interval; không còn `(0.6, 1.0)` |
| 7 | `classify_response`: `Please retry in 13h`→DAILY · `exhausted`→RATE · `limit: 0`→DAILY · `per day`→DAILY |
| 8 | `lock_key` + `sync` lặp lại ⇒ `usable` giữ 0 (bug cũ trả về 1) |

### Kết quả hồi quy (mọi suite xanh)
`test_quota_rate` **36/36** · `test_adaptive_model` **7/7** · `test_3mode` **41/41** · `test_key_manager` **80/80** · `test_key_cooldown` PASS · `test_ai_rich` **85/85** · `test_gui_smoke` **15/15** · `test_slug_canonical` **6/6** · `py_compile` OK.

### Phát hiện thêm — cập nhật ở §7.12
- ~~**`_try_image_models()`** (path sinh ảnh): 429 tốc độ cũng rơi thẳng `return`~~ → **ĐÃ SỬA ở §7.12** (P6a), kèm cả **bug X** phát hiện thêm: lọc candidate model ảnh giao với model TEXT ⇒ fallback sai model.
- **2 tiến trình dùng chung 197 key** (VocabApp + GetHtmlFromUrl) cùng lúc: `pace()` chỉ tính trong 1 tiến trình ⇒ tổng rate ×2. **VẪN CHƯA LÀM** (P6b — người dùng quyết định không làm lượt này; muốn phải đặt rate-limiter chia sẻ file lock / đếm tập trung).

---

## 7.12. HỌC TỪ GETHTMLFROMURL: BACKOFF RPM · GAP/ACCOUNT · KEY 3 TRẠNG THÁI · UI ĐA CHỌN · SỬA GHE (2026-11-05b)

So sánh kỹ 2 bên: VocabApp (`api/gemini_safe.py`) vs GetHtmlFromUrl bản Desktop thật (`core/ai_translator.py` 3590 dòng, `gui/key_manager_dialog.py` 1176 dòng PyQt6). Người dùng duyệt lần lượt: **P1+P2, P4, P3, P5, P6a** + **bug X**; **không làm P6b**.

### P1 — Backoff RPM lũy tiến 65 → 120 → 300s (GHE → VocabApp)
- `compute_rpm_cooldown(msg, consecutive)` (mới, `api/gemini_safe.py`): 429 tốc độ lần 1 → 65s, lần 2 → 120s, ≥3 → 300s (cap), luôn tôn trọng `retryDelay` thật của Google nếu lớn hơn.
- `AccountPool.record_rpm_429(account)` đếm 429 **liên tiếp** per-account (chuỗi cách >10 phút tự reset), `clear_rpm_429` gọi khi `request()` thành công ⇒ backoff tự về 0.
- Áp ở cả 2 đường text (`request()` QUOTA_RATE) và ảnh (`request_image` QUOTA_RATE). **Giữ lock granularity = `lock_key`** (không khoá account như GHE — quota RPM theo project nhưng khoá key nhẹ hơn, xoay được).

### P2 — Gap cứng ≥8s giữa 2 lần gọi CÙNG account (GHE `_wait_pacing` → VocabApp)
- Hằng `PER_ACCOUNT_MIN_GAP = 8.0`, dict `_account_last_used`; `pace(interval, account=None)` áp gap cứng theo account (luôn tôn trọng, kể cả khi chỉ còn 1 account) bên trên pace toàn cục.
- Mọi call site đổi thành `pace(account=email)`.

### P5 — Phản hồi rỗng ≠ lỗi mạng (`had_real_response`/`MAX_EMPTY_ROUNDS` của GHE → VocabApp)
- Tách `ErrorKind.EMPTY` khỏi nhánh transient (`SERVER/NETWORK` giữ nguyên y hệt); đếm `MAX_EMPTY_ROUNDS = 3` → dừng với message đúng bệnh: **"rất có thể prompt bị safety filter lọc"**, không sleep retry 2^n vô ích.
- `_try_models()`: 200 nhưng rỗng → thử model **kế** trên cùng key (trước đây return ngay sau 1 model); rỗng ≥2 lần liên tiếp → demote (cooldown 300s) kèm log "N lần liên tiếp".
- Bug bắt được khi test: streak bị `pop` trước khi đếm ⇒ luôn là 1 → chỉ pop khi **text THẬT**.

### P6a + bug X — đường sinh ảnh
- **P6a**: thêm nhánh `QUOTA_RATE` vào `_try_image_models` (429 → `_cooldown_model` + thử model ảnh **kế** trên cùng key; hết list mới trả `QUOTA_RATE`).
- **bug X** (mock chứng minh, 0 mạng): `request_image`/`_try_image_models` lọc candidate bằng `self._get_available_models()` (danh sách model **TEXT**) → giao rỗng → fallback về model TEXT → URL gửi lên Google là `models/gemini-3.5-flash` thay vì model ảnh. Sửa bằng helper `_filter_live_models(candidates)` lọc theo đúng danh sách ẢNH sống; verify: URL ra `models/gemini-2.5-flash-image`, trả ảnh OK.

### P4 — Nâng cấp `ApiKeyManagerDialog` (VocabApp.py)
- **Đa chọn**: `_sels` (set) + `_anchor`; bind `<Button-1>`, `<Control-Button-1>`, `<Shift-Button-1>` trên mọi widget con (test Tk thật: `<Button-1>` chỉ bắn khi **không** modifier ⇒ 3 bind không double-fire); `_select(i, event=None)` giữ backward-compat kiểu cũ; `<Delete>` xóa nhanh selection; nút **🧹 Xóa Key Lỗi** ở hàng `ctrl2` (có `askyesno` xác nhận) xóa mọi key có `error_msg`; `_clamp_sel()` giữ idx hợp lệ sau khi list đổi.
- **3 trạng thái key**: helper thuần `keymgr_classify_check(ok, msg)` → `active | exhausted | invalid | disabled` (thứ tự: ok → quota/429/retry → free-tier/billing → invalid markers → disabled) + `keymgr_retry_seconds(msg)` parse `'13h'/'33m'/'4s'` (default 3600, không nhầm `'450ms'`). `_on_check_result` ghi `next_check_time` + `reset_time` cho exhausted → pool tự skip tới hạn hồi.
- **UI**: toggle 4 nhãn 🟢 Bật / ⏳ Quota / ❌ Lỗi / 🔴 Tắt; cột Kiểm tra có màu ⏳ cho quota tạm; cột Ghi chú hiện **"⏳ hồi sau XhYm"**; `lbl_sum` hiện số dòng đang chọn; log từng trạng thái.
- **Pool (`_usable_keys`)**: thêm nhánh bỏ `status == "disabled"` — trước đây **🔴 Tắt không có tác dụng thật** (pool không đọc status này) + `exhausted` kiểm `max(next_check_time, reset_time)` (chuẩn field của GHE).

### P3 — Sửa GHE Desktop (**CHỈ GHI FILE, KHÔNG COMMIT** — WIP của người dùng)
- `core/ai_translator.py`:
  1. Nhánh 429 daily: bắt thêm regex `retry in\s+(\d+)\s*h` — "Please retry in 13h" không chứa marker "day" nào nên trước đây **rơi nhánh RPM 65s**; `reset_time` giờ lấy theo **giờ thật** Google báo (thay vì 86400 cứng).
  2. `retry_delay_from`: parse thêm đơn vị `h`/`m` (trước chỉ `s`) — verify thật `'Please retry in 13h'` → **46805s**.
  3. Gộp `is_model_restriction` định nghĩa **2 lần** (dòng ~159 & ~1659) → còn 1 nguồn (giữ def đầu file).
- `gui/key_manager_dialog.py`: `_on_test_selected` trước đây **validate đồng bộ trên GUI thread** (mỗi key timeout 7s + `processEvents()` vá tạm → chọn 20 key UI treo hàng chục giây) → tách `_start_validation(key_rows, done_title)` chạy `KeyValidationWorker` **dùng chung** với `_on_test_all`; cập nhật từng dòng realtime qua signal.
- Verify: `py_compile` cả 2 file OK + import module thật (`is_model_restriction` còn 1 def, `retry_delay_from` đúng 46805).

### Test (mở rộng, mock 0 mạng thật)
| Suite | Trước | Sau |
|---|---|---|
| `tools/test_quota_rate.py` | 36/36 | **72/72** (+sections 9–13: backoff unit + tích hợp 65→120→300s + clear, gap ≥8s/account với sleep giả, empty → safety filter 3 account, ảnh 429 + URL đúng model ảnh + `request_image` lock_key) |
| `tools/test_key_manager.py` | 80/80 | **111/111** (+sections 8–10: classify/retry, đa chọn Ctrl/Shift/clamp trên object giả không cần Tk, pool tôn trọng disabled/exhausted) |
| `test_adaptive_model` / `test_3mode` / `test_key_cooldown` / `test_slug_canonical` / `test_ai_rich` / `test_gui_smoke` | 7/7 · 41/41 · PASS · 6/6 · 85/85 · 15/15 | **y nguyên, xanh** (smoke tạo `ApiKeyManagerDialog` với UI mới OK) |
| `py_compile` | — | OK (`VocabApp.py`, `api/gemini_safe.py`, 2 file test, 2 file GHE) |

### KHÔNG làm (đã báo người dùng)
- **P6b** — rate-limiter chia sẻ giữa 2 tiến trình (file lock): rủi ro cao, chưa duyệt.
- Câu hỏi **10 key/account tạo cùng 1 project hay 10 project riêng** (197 key/20 account, `project_id` trống): ~~chưa trả lời~~ → **ĐÃ TRẢ LỜI: 10 project RIÊNG** — sửa ở mục 7.13.

---

## 7.13. P7 — HIỂU ĐÚNG "10 KEY/ACCOUNT = 10 PROJECT RIÊNG": KHOÁ QUOTA NGÀY THEO KEY · COUNTER 429 PER-KEY (2026-11-07)

**Câu hỏi đã trả lời (người dùng xác nhận):** 10 key/account = **10 project RIÊNG** (197 key/20 account, `project_id` trống) — KHÔNG phải "1 account = 1 project" như giả định cũ trong code. RPM/daily quota là **theo project = theo từng key**, không cộng dồn vào account. Phạm vi duyệt: **A (tối thiểu đúng-sai)** + **sửa cả GHE**; **GIỮ** gap 8s/account.

### Sửa trong `api/gemini_safe.py`
1. **`QUOTA_DAILY` (text + ảnh)**: `_lock_account(ACCOUNT_COOLDOWN)` → `self._pool.lock_key(key_obj, duration=daily_wait)` với helper mới **`daily_retry_from(msg)`** — parse `'Please retry in 13h33m50s'` → **48830s**, không parse được → fallback 60 phút, cap 24h. Trước: 1 key hết quota ngày → **9 key project khác của cùng account bị khoá oan 60 phút**.
2. **P1 counter per-key**: `record_rpm_429`/`clear_rpm_429` đổi identity từ email → **raw API key** (4 call site text + ảnh). Trước: key B thành công **xoá sai** backoff của key A; key C dính 429 lần đầu bị phạt 120s oan.
3. **`MAX_KEYS_PER_ACCOUNT` 2 → 10** + `account_health_report` bỏ nhánh ℹ — trước đây bắn ⚠/ℹ cho **mọi 20 account mỗi startup** (mỗi account 10 key là bình thường, không dồn quota).
4. **`account_locked()`**: chỉ nhìn `_cooldown` cấp account — trước True nếu **bất kỳ key nào** của account đang cooldown (khoá 1 key làm cả account bị coi là khoá ở batch rotation/mắt người đọc).
5. **`usable_project_count()`**: đếm theo **số key dùng được** (mỗi key = 1 project); sửa docstring `pace()`, `compute_rpm_cooldown()`, class `AccountPool` cho đúng thực tế.
6. **GIỮ NGUYÊN** (đã chốt): gap cứng `PER_ACCOUNT_MIN_GAP = 8s`/account (P2) — an toàn dưới cả 2 giả định (7.5 call/phút/account ≪ mọi ngưỡng); pace toàn cục vẫn cap 0.8s = 75 call/phút TỔNG.

### Sửa GHE Desktop (`core/ai_translator.py` — CHỈ GHI FILE, KHÔNG COMMIT — WIP người dùng)
- Nhánh 429 daily: bỏ `pool.lock_account` + loop `account_of(k) == email` đánh dấu **mọi key** của account `exhausted` → chỉ đánh dấu **key bị 429** (`cooldown_until` + `status`/`reset_time`/`next_check_time` trên chính `key_obj`); `save_local_keys` match theo **key** (`decode_token(lk.key) == raw` — file lưu bản `ENC:`) thay vì theo email; `exclude` chỉ thêm key đó ⇒ 9 key project khác vẫn dùng được.
- Verify: `py_compile` OK + import module thật OK (còn đúng 1 nhánh daily, không còn `lock_account` trong daily).

### Test (`tools/test_quota_rate.py`: 72 → **86/86**, mock 0 mạng)
- **Section 4 viết lại**: daily → key1 khoá **~48830s** (đúng `retry in 13h33m50s`), account a@ **KHÔNG** nằm trong `_cooldown`, key1B cùng account còn dùng được (`usable_count == 2`), log có "Khóa riêng key" và hết "Khóa account".
- **Section 10 đổi assert**: counter theo **key1** (key2 OK từng round không xoá được — bằng chứng per-key); clear khi key1 gọi tốt.
- **Section 14 mới (+10 case)**: `daily_retry_from` (parse/fallback 60 phút/cap 24h) · 2 key có counter độc lập + clear key B không đụng key A · `usable_project_count` 3 key/1 account = **3** · health 10 key = 0 cảnh báo / 11 key = đúng 1 ⚠ · ảnh daily cũng khoá key, account không khoá.

### Suite xanh
`test_quota_rate` **86/86** · `test_key_manager` **111/111** · `test_3mode` **41/41** · `test_adaptive_model` **7/7** · `test_slug_canonical` **6/6** · `test_ai_rich` **85/85** · `smoke_test_pipeline` **PASS** · `test_key_cooldown` **PASS** · `py_compile` 0 lỗi (VocabApp + test + GHE).

---

## 7.14. FIX PIPELINE MEDIA: SKIP RE-ATTACH · VERIFY GIỮ DATA + ĐẾM DIALOGUE · INVALIDATE KHI CONTENT ĐỔI TỪ (2026-11-07b)

**Triệu chứng (log thật):** `🏁 PAUSED: 34/34 ngày, calls=71, ảnh=30. DoD=False` với log mâu thuẫn: `"Audio Ngày N đã có — bỏ qua"` nhưng `"Ngày N thiếu 2 ảnh / 12 audio"`; ảnh `"Xong 10 ảnh"` vẫn `"thiếu 2 ảnh"`. Course `tiếng_nhật` day31-34: `co_audio=0, dialogue=0` dù checkpoint dialogue `done gen=1` → **hội thoại MẤT trong course.json** mà DoD vẫn `all_days_dialogue=true`.

**Đúng thiết kế 2-lượt (không phải bug):** run này mark `pending` → run sau sinh bù (ảnh cap 10/run, tích lũy — day1-30 đã 12/12). **4 bug THẬT:**
1. **Skip không re-attach** (`pipeline_media.py`): checkpoint done → log "bỏ qua" + trả data nhưng KHÔNG ghi ref vào lesson → verify đếm thấy thiếu trong CÙNG run (log trái nhau).
2. **Verify ghi đè phá data**: mark pending bằng `{"pending_reason"}` **thay thế toàn bộ `data`** → mất list tracks/images đã sinh.
3. **Verify KHÔNG đếm dialogue**: checkpoint dialogue vẫn done → skip mãi → `lesson.dialogue=0` flush vào course.json → **mất vĩnh viễn**, DoD `all_days_dialogue=true` = lừa (chỉ check status checkpoint).
4. **Content regen không invalidate** checkpoint media/dialogue → stale done → skip.

**Sửa:**
1. `ai/pipeline_media.py` — helper mới **`_reattach_audio()`**: skip audio → gắn lại `audio_ref`/`vocab_audio`/`meaning_audio_ref` từ tracks, **guard `text == word`** (từ đã đổi → KHÔNG gắn ref sai → verify mark pending sinh bù). Dialogue skip → ghi lại `lesson["dialogue"]` nếu rỗng.
2. **`run_media_verify_stage`**: mark pending = **merge** `pending_reason` vào data CÓ SẴN (không thay thế); đếm thêm `n_no_dlg` → mark `STAGE_DIALOGUE` pending + log `"... / N hội thoại"`.
3. **`pipeline.py::_run_day`**: content sinh lại mà danh sách từ **ĐỔI** → invalidate (pending) checkpoint images/audio/dialogue ngày đó → stage chạy lại NGAY trong run; từ **GIỐNG** → giữ nguyên (không đốt media oan).

**Test mới `tools/test_pipeline_media_fix.py`: 25/25 PASS** (mock 0 mạng) — 7 nhóm: re-attach text khớp/khác/variant vi · dialogue re-attach (kèm không đè) · verify giữ data khi pending · verify đếm dialogue · content đổi từ → invalidate / giống từ → giữ done.

**Suite xanh:** media_fix 25/25 · quota_rate 86/86 · key_manager 111/111 · 3mode 41/41 · slug 6/6 · adaptive 7/7 · ai_rich 85/85 · smoke PASS · cooldown PASS · `py_compile` 0 lỗi.

**Không làm (phạm vi B — chờ duyệt riêng):** bật `image_providers` gemini/web (ảnh AI thật — hiện chỉ `dict`/`placeholder` = chữ cái đầu) · GUI truyền `max_images_per_day` từ settings (60) thay vì default 10.

---

## 7.15. FIX NÚT DỪNG · LOG CÓ TIMESTAMP · 400 "API key not valid" KHÔNG SPAM (2026-11-07c)

**Triệu chứng (log thật):** bấm ⏹ Dừng nhưng pipeline vẫn chạy + spam `⚠ 'gemini-3.7-flash' fail (400 — API key not valid…) → thử 'model kế'` lặp vô hạn; log không có ngày giờ.

**Nguyên nhân (3):**
1. **Nút Dừng không ăn giữa request**: `GeminiCoordinator` tạo trong `GeminiApiProvider._ensure()` (`providers.py`) KHÔNG truyền `stop_check` → default `lambda: False` (`gemini_safe.py:705`) → `request()`/`_try_models` **không bao giờ thấy lệnh dừng**; `run_pipeline(stop_check)` chỉ check ở ranh giới ngày/backbone ⇒ bấm Dừng phải chờ hàng phút mới có hiệu lực.
2. **Log không timestamp**: `VocabApp.py` chưa `import time`; 3 hàm `_log` chèn `msg` trần.
3. **400 spam vô hạn**: `classify_response` nhánh 400 chỉ bắt `"api_key_invalid"` (gạch dưới) → message `"API key not valid"` **rơi `REQUEST_BAD`** → key chết KHÔNG bị loại → retry ×3 + quay hết mọi model (≈8 dòng log/request) + đốt RPM ⇒ **có thể dính 429 rate-limit oan**. *(400 key-invalid KHÔNG vi phạm chính sách — key sai thì Google từ chối, không "khóa" thêm; rủi ro duy nhất là spam RPM.)*

**Sửa:**
1. **Nút Dừng**: `ai/providers.py` — `GeminiApiProvider(stop_check=)` + `_ensure()` truyền vào `GeminiCoordinator(stop_check=...)`; `ProviderChain.default(..., stop_check=)`; `ai/pipeline.py` — `ProviderChain.default(..., stop_check=stop_check)` ⇒ chuỗi GUI → `request()` dừng ngay trong `while` (≤1s), kể cả giữa vòng thử model.
2. **Timestamp**: `VocabApp.py` — `import time` + 3 `_log` (dòng 1273/2820/3886) prefix `[HH:MM:SS]`.
3. **400 key-invalid**: `classify_response` nhánh 400 thêm `"api key not valid"` → **`INVALID_KEY`** → `_try_models` trả ngay model đầu (**0 model kế** — lỗi ở KEY không ở model) → `request()` đã có nhánh: `block_key` (blocklist bền) + `exclude` + **chuyển key khác** — hết spam.

**Test `tools/test_quota_rate.py` 86 → 94/94** (mock 0 mạng):
- **Section 15**: key2 cứu request · key1 đúng **1 POST** (không quay model) · log `"bị từ chối (Invalid)"` · không log `→ thử` · key1 vào blocklist bền (+ restore file blocklist sau test).
- **Section 16**: `stop_check=True` → `kind=stopped` + **0 POST**; `GeminiApiProvider(stop_check=)` tạo coord THẬT còn stop → `request` STOPPED 0 POST (chứng minh chuỗi run_pipeline → chain → request).

**Suite xanh:** quota 94/94 · media_fix 25/25 · key_manager 111/111 · 3mode 41/41 · slug 6/6 · adaptive 7/7 · ai_rich 85/85 · smoke PASS · cooldown PASS · `py_compile` 0 lỗi.

---

## 7.16. DASHBOARD WEB ĐIỀU KHIỂN PIPELINE (localhost:5690) (2026-11-08)

**Yêu cầu:** trang web HTML trên CÙNG máy (localhost) để Start/Dừng pipeline, xem log realtime + tiến độ từ trình duyệt — cùng máy, không mở LAN.

**Kiến trúc:**
```
Browser http://127.0.0.1:5690/dashboard (poll JSON 1.5–2s)
   ▼
Flask bridge_server (bind 127.0.0.1 — CŨ, chỉ THÊM routes)
   ▼
ai/pipeline_control.py (MỚI) — trạng thái DÙNG CHUNG
   • STOP_EVENT singleton  → GUI ⏹ và web ⏹ set CÙNG 1 sự kiện (dừng ≤1s)
   • LOG buffer ring 2000 dòng có id tăng dần (thread-safe)
   • STATUS {running, source=gui|web, language, pct, day, stage…}
   ▼
run_pipeline(thread nền, stop_check=STOP_EVENT.is_set, log_fn=buffer)
```

**File mới (2):**
1. **`ai/pipeline_control.py`** — `STOP_EVENT` · `log_append()/log_snapshot(since_id)` · `set_running()/set_progress()/status_snapshot()` · `request_stop()` · `start_pipeline(...)` (guard `already_running:source`, ALWAYS `STOP_EVENT.clear()` trước run mới) · `_run_pipeline` (seam để test mock) · `_runner` (thread, ghi 🏁 + `last_result`).
2. **`web/dashboard.html`** — self-contained (CSS/JS inline, không CDN): dropdown khóa (từ `/dash/courses` — đọc DB thật) · dropdown cấp độ · từ/ngày · số ngày · force_new · nút ▶Start/⏹Dừng · thanh tiến độ + elapsed + nguồn (GUI/Web) · log timestamp auto-scroll (poll `since_id`, tối đa 2000 dòng) · ô nhập token (hiện khi chưa auth). Token nhận từ `?token=` URL → `sessionStorage` → nhúng server-side → nhập tay; URL tự `replaceState` giấu token.

**Sửa (2):**
3. **`ai/bridge_server.py`** — thêm routes: `GET /dashboard` (serve HTML, nhúng token CHỈ khi `?token=` đúng) · `GET /api/vocab/dash/status` · `GET /api/vocab/dash/logs?since=` · `GET /api/vocab/dash/courses` · `POST /api/vocab/dash/start` · `POST /api/vocab/dash/stop`. **Auth bắt buộc** header `X-Vocab-Bridge` HOẶC `?token=` (chống CSRF) → 401. `missing_language`→400, `already_running`→409. Fix import: `_build_app` insert base dir vào `sys.path` + helper `_pctl()` (chạy CLI `python ai/bridge_server.py` không còn `ModuleNotFoundError`).
4. **`VocabApp.py`** — ① `CourseGenerationDialog._stop_event` → dùng `pipeline_control.STOP_EVENT` (nút ⏹ GUI = ⏹ web); ② `_log` (dialog) vừa ghi LogBox vừa `log_append()` → web đọc được log GUI; ③ `_start`: guard `is_running()` (web đang chạy → warning, không start đôi) + `set_running(source="gui")`; `_supplement` cũng set; `_on_pipeline_progress()` mới đẩy `on_progress` lên STATUS + thanh GUI; `_on_day_done` cũng update; `_done` → `set_running(False)`; ④ `App.__init__` auto-start bridge sau 1.2s (`_autostart_bridge`) → mở app là dùng được ngay `http://127.0.0.1:5690/dashboard` (nhãn ở tab Cài đặt tự cập nhật; thiếu Flask → ghi rõ).

**Test `tools/test_web_dashboard.py` — 42/42 (Flask test client + mock `pc._run_pipeline`, 0 mở cổng, 0 gọi mạng):**
- pipeline_control thuần (15): guard missing_language · log since_id không lặp · start clear stop cũ · start lần 2 → `already_running:web` · request_stop → set event · fake thoát → `last_result=aborted` · log ⏹/🏁.
- routes (27): dashboard nhúng token đúng/sai · 6 endpoint thiếu/sai token → 401 · status qua header lẫn `?token=` · logs since · courses list · start→200 + 409 lần 2 → stop→`stopped:true` → running=false.

**Test thật (server CLI + HTTP thật + browser):** health/dashboard/status/logs/courses 200 (courses trả **2 khóa thật** + 7 levels) · thiếu token 401 · trang auto-auth qua `?token=` (`authBox` ẩn, nút Start bật) · `POST stop` từ JS trang → log hiện `[13:58:54] ⏹ Dashboard: Dừng khi chưa có run nào…` với timestamp.

**Suite xanh:** dashboard 42/42 · quota 94/94 · media_fix 25/25 · key_manager 111/111 · 3mode 41/41 · slug 6/6 · adaptive 7/7 · ai_rich 85/85 · smoke PASS · cooldown PASS · `py_compile` 0.

---

## 7.17. FIX DASHBOARD (dropdown sau auth · trạng thái CHƯA KẾT NỐI) + TRANG HỌC `/index` HIỂN THỊ NỘI DUNG (2026-11-10)

**Triệu chứng:** mở dashboard "không chạy ra kết quả gì" (log 0 dòng, dropdown trống); `web/index.html` không hiện nội dung khi serve qua server.

**Nguyên nhân (4):**
1. **Dropdown khóa trống vĩnh viễn**: `loadCourses()` chỉ gọi **1 lần lúc boot** — token chưa đúng khi mở trang → 401 bị nuốt (`catch{để sau}`) → dán token xong `refreshAuth()` **không gọi lại** → không chọn được khóa → không Start được.
2. **Giá trị mặc định gây hiểu nhầm**: chưa kết nối mà vẫn hiện `IDLE · 0% · chưa có run · 0 dòng`; mọi lỗi poll bị `catch{return}` nuốt im lặng.
3. **`/index` không có route**: server chỉ phục vụ `/dashboard` + API.
4. **`script.js` chết toàn bộ** (lỗi pre-existing khi serve qua HTTP): `paths.js` (load trước) khai `const VOCAB_SLUG` toàn cục, `script.js` khai `var VOCAB_SLUG` cùng tên → **`var` conflict `const` → SyntaxError "already been declared"** ngay khi instantiate → MỌI hàm (`init`, `switchView`, `loadLanguage`, `ensureCourseLoaded`) undefined → trang trắng/chưa có dữ liệu. *(Dòng `if (typeof…)` guard runtime không cứu được vì lỗi ở mức parse/instantiate.)*

**Sửa:**
1. **`web/dashboard.html`**: `setAuth(true)` khi chuyển **chưa auth → auth** → tự gọi `loadCourses()` (dropdown nạp ngay sau token đúng); log local `🔗 Đã kết nối bridge — N khóa học sẵn sàng.`; chưa auth → pill **`CHƯA KẾT NỐI`** (đỏ) + phase "cần dán token…"; poll lỗi mạng → pill **`MẤT KẾT NỐI`** (không còn im lặng); thêm nút header **`📚 Trang học` → `/index`**.
2. **`ai/bridge_server.py`**: thêm route `GET /index` (serve `web/index.html`) · `GET /<path:fn>` (static trong `web/`: script.js, style.css, paths.js, manifest, icons — `send_from_directory` chặn traversal) · `GET /data/<path:fn>` (serve `data/`: `ai_courses/*/course.json`, `media/index.json`, ảnh/audio; **fallback**: `data/index.json` thiếu → **synth** `{"languages":[khóa AI có course.json thật]}`; `<slug>.json` vocab chưa export → `{"vocabularies":[]}` để UI sạch thay vì lỗi đỏ; traversal → 4xx). Không auth (chỉ đọc, bind 127.0.0.1).
3. **`web/script.js`**: bỏ `var VOCAB_SLUG` trùng tên → alias `slugOf` (typeof-guard, fallback khi `paths.js` không load) + 2 chỗ gọi (`loadLanguage`, `ensureCourseLoaded`).

**Test `tools/test_web_dashboard.py` 42 → 54/54** (section 6: `/index` là index.html thật · script/style/paths/manifest 200 · index.json synth có `tiếng_nhật` · course.json THẬT 200 có `days` · vocab fallback rỗng · data thiếu 404 · traversal 4xx · media manifest 200).

**Test thật (server CLI + browser):**
- Dashboard chưa token → pill **`CHƯA KẾT NỐI`** + ô dán token hiện + Start disabled; `?token=` → auto-auth → dropdown **2 khóa** + log `🔗 Đã kết nối` + pill IDLE thật.
- `/index` → dropdown khóa (synth) → tab **AI Course**: badge `Hoàn thành 0/114 ngày · trình độ: ⭐ Trọn gói…`, **Ngày 1** render từ `course.json` thật với **12 ảnh + 12 audio** + quiz; tab List hiện sạch "Không tìm thấy từ vựng nào phù hợp" (fallback).

**Suite xanh:** dashboard 54/54 · quota 94/94 · media_fix 25/25 · key_manager 111/111 · 3mode 41/41 · slug 6/6 · ai_rich 85/85 · smoke PASS · `py_compile` 0.

---

## 7.18. TRANG HỌC HẾT NHẮC "ĐỒNG BỘ LÊN GITHUB" + HƯỚNG DẪN MỞ ĐÚNG CÁCH (2026-11-11)

**Triệu chứng (user):** mở trang thấy `Failed to load data` + dropdown ngày trống + *"Chưa có khóa học AI cho ."* + dòng "*sau đó Đồng Bộ lên GitHub để học tại đây*" → hiểu nhầm phải đẩy dữ liệu lên GitHub mới xem được.

**Sự thật:** dữ liệu (từ vựng · ảnh · âm thanh · khóa AI) nằm **LOCAL** trong `data/` của máy; trang đọc qua server nội bộ app (`127.0.0.1:5690`, route `/index` + `/data/*` §7.17) — **KHÔNG cần GitHub**. Dòng GitHub là copy placeholder cũ. Chẩn nhật: 5690 trống (app chưa mở) → user mở thẳng `web/index.html` (`file://`) → trình duyệt chặn `fetch` → init lỗi.

**Sửa (`web/script.js`, 3 chỗ):**
1. **`init()` catch** — thay `"Failed to load data"` chung chung: `file://` → `⚠ Mở sai cách (file://) — mở app VocabApp rồi vào 127.0.0.1:5690/index`; server khác → `⚠ Không tải được dữ liệu local — mở qua app VocabApp`.
2. **`loadLanguage()` catch** — thay `"Error loading vocabulary data."` bằng cùng 2 thông báo hướng dẫn (có link `http://127.0.0.1:5690/index`).
3. **Placeholder khóa học** — bỏ "*Đồng Bộ lên GitHub*": `file://` → hướng dẫn mở qua app (dữ liệu nằm ngay trên máy); server mà thiếu khóa → "*Khóa học lưu ngay trên máy, trang đọc trực tiếp từ `data/` local*" + sửa lỗi hiện "*cho .*" (language rỗng → "(chưa chọn khóa)").
4. **FIX thêm (không liên quan GitHub nhưng chặn "toàn bộ tính năng")**: dropdown **chọn ngày không có listener** → đổi ngày nội dung vẫn kẹt ở ngày đầu (`renderCourseDay` chỉ chạy 1 lần trong `renderCourseShell`) → thêm `daySelect.addEventListener("change", …)`.

**Test:** `test_web_dashboard.py` 54 → **57/57** (3 check mới: hết nhắc "Đồng Bộ lên GitHub" · có hướng dẫn `127.0.0.1:5690/index` + phân biệt `file://` · có listener đổi ngày). Test thật browser: `/index` init OK (dropdown 2 khóa) · List/Flashcard/AI Course render · 114 ngày + 12 ảnh + 12 audio · chặn fetch giả lập → catch hiện thông báo mới đúng · nhánh `file://` đúng chuỗi · dashboard `?token=` vẫn IDLE + 2 khóa + link 📚 Trang học. Suite xanh: dashboard57 · quota94 · media25 · keymgr111 · 3mode41 · slug6 · ai_rich85 · smoke PASS · compile0.

---

## 7.31. GÓI 7 — FIX "BẤM NÚT KHÔNG TỚI NƠI ĐÚNG" + VÒNG LẶP KIỂM TRA (2026-11-13)

**Triệu chứng (user, ảnh 13/11):** bấm "Ngữ pháp" **không đổi gì** (vẫn ra từ vựng) · chọn **Ngày 1095 nhưng nội dung ra Ngày 1** (dù khóa đã có 1.260 ngày).

**Nguyên nhân (tìm được bằng vòng lặp test, không phải đoán):**

| # | Nguyên nhân | Sửa |
|---|---|---|
| 1 | **`common_mistakes` là `list[str]` (AI sinh) nhưng code render giả định `list[dict]`** ⇒ `AttributeError` **CRASH** khi bấm "Ngữ pháp" ⇒ ô nội dung giữ nguyên ⇒ "bấm không đổi gì" | render chịu cả 2 kiểu (`VocabApp._render_lesson_text`) |
| 2 | `_reload_course()` (gọi cả khi **auto-sync 5 s**) luôn chọn `last_day` ⇒ **nhảy về ngày cũ** | giữ ngày đang xem nếu còn hợp lệ |
| 3 | Ô nhập ngày không đồng bộ dropdown | `_select_day_by_num` đồng bộ cả ô nhập |
| 4 | Mốc cắt `_sec` trỏ **trước khối "mẫu câu"** ⇒ bấm "Ngữ pháp" **xoá luôn phần ngữ pháp** | tách lọc: *Từ vựng (+câu thông dụng)* / *Ngữ pháp (+mẫu câu)* / *Hội thoại* |

**Tool mới `tools/test_day_nav_loop.py`** — **vòng lặp kiểm tra điều hướng** (mô phỏng đúng thao tác app, dùng **course THẬT 1.260 ngày**):
- **A.** chọn ngày N (ngẫu nhiên có seed) ⇒ tiêu đề + nội dung + ô nhập đúng N.
- **B.** bấm 4 chế độ ⇒ nội dung lọc đúng (Ngữ pháp không lẫn từ vựng, và ngược lại) + đúng ngày đang chọn.
- **C.** gọi lại `_load_selected_day()` / `_reload_course()` (mô phỏng auto-sync) ⇒ **KHÔNG nhảy ngày**.

**Kết quả:** `test_day_nav_loop` **930/930 PASS** (30 vòng × course thật) · `test_study_sync` 39/39 · `test_3mode` 41/41 · `test_gui_smoke` 15/15 · `test_course_recovery` 18/18.

---

## 7.29. GÓI 6 (tiếp) — NGHĨA TIẾNG VIỆT & KẾT QUẢ KHÓA NHẬT SAU KHI BỔ SUNG OFFLINE (2026-11-12i)

**Nghĩa tiếng Việt cho nguồn offline**: Wiktionary Nhật chỉ có mục "Tiếng Việt" cho **3/1.200** từ ⇒ không đủ. Bổ sung `tools/translate_vi.py`: dịch gloss **tiếng Anh** (EDICT) → **tiếng Việt** theo **lô 25 từ/request** (delay 0,6 s), cache vĩnh viễn `data/offline_src/vi_meanings.json` ⇒ **gọi 1 lần (116 giây cho 2.200 từ) là xong, sau đó không cần mạng**. `offline_content.load_wiki_cache()` gộp 2 nguồn (Wiktionary + bản dịch).

**Kết quả khóa `tiếng_nhật` sau khi bổ sung (đo bằng `tools/verify_courses.py` + `tools/audit_curriculum.py`):**

| Hạng mục | Trước | Hiện tại |
|---|---|---|
| ngày | 103 | **200** (103 AI + 97 offline) |
| từ vựng | 1.219 | **2.189** (1.600 từ khác nhau) |
| ngữ pháp | 209 | **597 mục** (396 có ví dụ · 596 có mini_quiz) |
| hội thoại | 97 | **194 bài** (875 lượt · 560 có từ trọng tâm) |
| trắc nghiệm | 4.009 | **4.979 câu** (0 câu lỗi) |
| field/từ | 94-96 % | **97-100 %** (pronunciation · ipa · POS · nghĩa · ví dụ · phonetic_note · syllables) |
| placeholder | 0 | **0** |

**Nguyên tắc thiết kế (giữ nguyên):** **AI trước — offline làm lưới an toàn.** AI lỗi/hết quota ⇒ tự động rơi về offline (`stage.fallback_offline`, đã có test); AI chạy lại ⇒ nội dung AI ghi đè offline (checkpoint content `done` bị xoá ⇒ AI sinh lại). ⇒ *"API chạy đúng và chính bạn chạy vẫn đúng"*.

**Lỗi hệ thống đã vá (quan trọng):** `media_store.flush_index()` ghi thẳng **cache RAM của process** ⇒ khi 2 tiến trình cùng sinh media (pipeline + bù media), tiến trình này **xoá entry của tiến trình kia** ⇒ ảnh/âm thanh "biến mất" khỏi web dù file vẫn trên đĩa (đo thật: khóa Nhật 930 audio → **0** sau một lần job khác ghi manifest). Nay `flush_index()` **đọc đĩa + MERGE** trước khi ghi ⇒ nhiều tiến trình không còn đánh nhau.

**Số liệu cuối 8 khóa (`tools/verify_courses.py`, chỉ tính file THẬT):**

| | ngày | từ | ảnh | audio từ | audio nghĩa | audio hội thoại | placeholder | ngày rỗng |
|---|---|---|---|---|---|---|---|---|
| tiếng_anh | 259 | 2.590 | 2.590 ✓ | 2.590 ✓ | 2.590 ✓ | 241 ✓ | 0 | 0 |
| tiếng_hàn_quốc | 450 | 4.500 | 4.500 ✓ | 4.500 ✓ | 4.500 ✓ | 416 ✓ | 0 | 0 |
| tiếng_nga | 381 | 3.811 | 3.811 ✓ | 3.811 ✓ | 3.701 ✓ | 288 ↑ | 0 | 0 |
| **tiếng_nhật** | **200** | **2.189** | **2.189 ✓** | **2.189 ✓** | **2.189 ✓** | **194 ✓** | 0 | 0 |
| tiếng_pháp | 343 | 3.430 | 3.430 ✓ | 3.430 ✓ | 2.080 ↑ | 187 ↑ | 0 | 0 |
| tiếng_trung | 446 | 4.460 | 4.460 ✓ | 4.460 ✓ | 4.390 ✓ | 22 ⚠ | 0 | 0 |
| tiếng_tây_ban_nha | 345 | 3.450 | 3.450 ✓ | 3.450 ✓ | 3.420 ✓ | 16 ⚠ | 0 | 0 |
| tiếng_đức | 342 | 3.420 | 3.420 ✓ | 3.420 ✓ | 3.220 ✓ | 30 ⚠ | 0 | 0 |
| **TỔNG** | **2.666** | **27.850** | **27.850 (100 %)** | **27.850 (100 %)** | **26.090 (94 %)** | **1.394** | **0** | **0** |

Còn thiếu **hội thoại** của Trung/Tây/Đức ≈ 1.290 bài ⇒ cần 1 call Gemini/ngày ⇒ chờ quota reset (07:00 VN).

---

## 7.28. GÓI 6 — NGUỒN NỘI DUNG OFFLINE: KHÔNG CHỜ API, HỌC ĐƯỢC NGAY (2026-11-12h)

**Yêu cầu (user):** *"Nếu bạn có khả năng tự lấy và tạo giáo trình thì đừng chờ API nữa — tự kiểm tra, so sát, thay thế, bổ sung toàn bộ; ưu tiên tiếng Nhật; phải từ thấp lên cao (bảng chữ cái → từ vựng cơ bản → ngữ pháp…); đưa vào pipeline quản lý chặt chẽ, API chạy đúng và chính bạn chạy vẫn đúng."*

**Đã làm (KHÔNG tốn quota Gemini):**
1. **Nguồn offline** (`ai/offline_content.py`):
   • **EDICT/JMdict** (140.672 mục, tải 1 lần từ edrdg.org — file EUC-JP) → từ vựng + kana đọc + từ loại + nghĩa Anh.
   • **Wiktionary** (`ja.wiktionary.org` action API) → **nghĩa TIẾNG VIỆT** + ví dụ (cache `data/offline_src/wiktionary_vi.json`).
   • **Bảng 92 kana** (46 hiragana + 46 katakana) sinh bằng code: romaji · IPA · nghĩa Việt · mẹo phát âm.
   • **Bảng ngữ pháp N5→N3** tự soạn (`ai/offline_grammar.py`, 22 mục: mỗi mục có giải thích · 2 ví dụ JA/VI · trọng tâm phát âm · lỗi thường gặp · mini_quiz).
   • **Hội thoại micro 4 lượt** + **trắc nghiệm đảo nghĩa** sinh bằng template từ từ của ngày.
2. **Thứ tự "từ thấp lên cao"**: xếp theo (số kanji, số kana) ⇒ **0 kanji (kana thuần) → 1 kanji + 1-2 kana → 2 kanji**; **10 ngày đầu = bảng chữ cái**, sau đó = từ vựng cơ bản theo độ khó tăng dần. (Không có nguồn tần suất — edrdg/JPDB/GitHub-raw đều 404/chặn — nên dùng độ khó thay tần suất.)
3. **Đưa vào pipeline (fallback)**: `ai/pipeline.py` — khi stage **content** của AI thất bại (hết quota/lỗi mạng) ⇒ **tự sinh bằng nguồn offline** và ghi log `stage.fallback_offline` ⇒ "API chạy đúng" (dùng AI) mà "chính bạn chạy vẫn đúng" (không còn phụ thuộc quota).
4. **Tool `tools/build_offline_course.py`**: dựng cả khóa offline (mặc định 200 ngày) + ghi **đúng định dạng `course.json` + checkpoint** (content/quiz/dialogue) để pipeline/media chạy tiếp. Đã áp dụng cho `tiếng_nhật`: **200 ngày** (103 ngày AI + 97 ngày offline) · **1.992 từ, chỉ 11 từ lặp** · 1.994 câu hỏi · 200 bài hội thoại · 22 mục ngữ pháp.
5. **Tool `tools/fetch_offline_sources.py`**: tải EDICT + nghĩa Việt Wiktionary (có cache, chạy nền).

**Test:** `tools/test_offline_content.py` **18/18** (92 kana đủ field · EDICT >10.000 mục · thứ tự độ khó TĂNG DẦN không lùi · ngày 1 = bảng chữ cái có vocab/ngữ pháp/hội thoại/quiz · ngày 12 = từ vựng đủ field v4 · quiz đáp án hợp lệ · hội thoại ≥2 lượt và dùng từ của ngày).

**Khi quota Gemini reset (07:00 VN):** job AI sẽ tự sinh tiếp 1.060 ngày Nhật còn lại và **ghi đè phần offline** (checkpoint content `done` bị xoá ⇒ AI sinh lại) ⇒ nhưng nếu muốn GIỮ offline làm nền, dùng `--no-resume` có chọn lọc hoặc chạy pipeline với `--stages` bỏ content.

---

## 7.27. CHỮA MANIFEST MẤT ENTRY + ĐỘ ĐẦY ĐỦ MEDIA SAU GÓI 5 (2026-11-12g)

**Sự cố:** media khóa Nhật đã sinh đủ (3.761 file / 49 MB) và refs **đã ghi vào `course.json`**, nhưng **manifest (`data/media/index.json`) mất entry** ⇒ web `mediaEntry(ref)` trả `null` ⇒ **không hiện nút ảnh/âm thanh dù file có thật**. Nguyên nhân: job bị kết thúc đột ngột nên `media_store.flush_index()` (chạy trong `finally` của `run_pipeline`) **không kịp ghi manifest**; index chỉ lưu entry trong RAM của process.

**Cách chữa (đã chạy):** `python tools/reindex_media.py` — quét lại toàn bộ file trong `data/media/` và dựng lại manifest (`id = "m_" + hash(rel_path, sha256)` — **giống hệt** cách `save_*` tạo id ⇒ khớp đúng ref mà `course.json` đang trỏ). Kết quả: **89.672 → 81.629 entry** (bỏ các entry của file đã bị xoá) · 385 s · manifest 40,3 MB.
⇒ **Khi thấy nút media biến mất dù file có trên đĩa → chạy `tools/reindex_media.py`.**

**Độ đầy đủ media sau khi bù (đo bằng `tools/verify_courses.py`, chỉ tính file THẬT):**

| khóa học | ngày | từ | ảnh | audio từ | **audio nghĩa** | **audio hội thoại** |
|---|---|---|---|---|---|---|
| tiếng_anh | 259 | 2.590 | 2.590 ✓ | 2.590 ✓ | **2.590 ✓** | **241 ✓** |
| tiếng_hàn_quốc | 450 | 4.500 | 4.500 ✓ | 4.500 ✓ | **4.500 ✓** | **416 ✓** |
| **tiếng_nhật** | 103 | 1.219 | **1.219 ✓** | **1.219 ✓** | **1.219 ✓** | **97 ✓** |
| tiếng_nga | 381 | 3.811 | 3.811 ✓ | 3.811 ✓ | 3.061 ↑ | 234 ↑ |
| tiếng_đức | 342 | 3.420 | 3.420 ✓ | 3.420 ✓ | 3.220 ↑ | 30 |
| tiếng_tây_ban_nha | 345 | 3.450 | 3.450 ✓ | 3.450 ✓ | 3.420 ↑ | 16 |
| tiếng_trung | 446 | 4.460 | 4.460 ✓ | 4.460 ✓ | 4.390 ↑ | 22 |
| tiếng_pháp | 343 | 3.430 | 3.430 ✓ | 3.430 ✓ | 0 (đang bù) | 0 |
| **TỔNG** | 2.667 | **26.880** | **26.880 ✓** | **26.880 ✓** | **22.400 (83 %)** | **1.056** |

⇒ **Ảnh + audio từ: 100 % mọi khóa.** Còn thiếu: **audio nghĩa** của Pháp (đang bù) và **hội thoại** (nội dung + audio) của Trung/Tây/Đức/Pháp ≈ **1.400 bài** — cần 1 call Gemini/ngày ⇒ chờ quota reset 07:00 VN.

---

## 7.26. GÓI 5 (không cần AI) — LỘ TRÌNH HỌC TỪ 0 + TÌNH TRẠNG QUOTA (2026-11-12f)

**Bối cảnh:** quota Gemini **đã cạn** (197 key/20 account hết quota hôm nay) ⇒ job sinh khóa Nhật tự chờ reset **~20 giờ** (07:00 VN hôm sau) ⇒ mọi việc cần AI dừng. User chọn: **chờ reset, tập trung làm việc KHÔNG cần AI**.

**Đã làm (không dùng AI):**
1. **Dialog "🗺️ Lộ Trình Học Từ 0"** (GUI, `CourseRoadmapDialog`): 6 chặng giáo trình · mỗi chặng hiện **số ngày · số từ · số từ khác nhau · đã hoàn thành** · nút **"Bắt đầu (Ngày N)"** nhảy thẳng tới ngày đầu chặng · hàng hướng dẫn **5 bước mỗi ngày: ① Đọc chữ + phiên âm → ② Nghe TTS → ③ Nối câu (ví dụ) → ④ Tự nhớ (lật thẻ) → ⑤ Ôn SM-2 (chấm điểm)**. Nút `🗺️ Lộ trình` trong hàng "Thao tác:".
2. **Bù media tiếp (edge-TTS + Wikipedia, 0 quota)**: nhóm B xong (Trung · Tây · Đức — **1.103 ngày** bù media), Tiếng Anh xong, đang chạy: Hàn · Nga · Pháp · **Tiếng Nhật**.
3. **Gói 5.1** (logic sinh chống lặp từ) đã merge ở §7.25.

**Test:** `tools/test_study_sync.py` → **36/36** (thêm case lộ trình: mở được · hiện tên chặng · hiện mốc ngày/từ · có nút "Bắt đầu" cho từng chặng · bấm trả về đúng ngày). Full suite **2 vòng: FAILs = 0** (16 file test) · compile0.

**Khi quota reset (07:00 VN):** ① job sinh khóa Nhật tự chạy tiếp (đang chờ sẵn) → ② bù hội thoại Trung/Tây/Đức (~1.150 ngày, 1 call/ngày) → ③ đồng bộ field 7 khóa cũ (`phonetic_note`, `syllables`, `grammar.mini_quiz`) → ④ bù media cho các ngày Nhật mới sinh.

---

## 7.25. GÓI 5.1 — SỬA LOGIC SINH: CHỐNG AI LẶP TỪ (2026-11-12e)

**Vấn đề đo được (§7.24):** 24-48 % từ giữa các ngày là **trùng** ⇒ "1.260 ngày" thực chất chỉ ~630 từ khác nhau ⇒ học 200-450 ngày **không đủ nội dung mới**. Nguyên nhân **không phải quota** mà là prompt content **không yêu cầu tỷ lệ từ mới** — AI tự chọn lại từ dễ (động từ, số đếm…).

**Đã sửa:**
- `ai/course_generator.build_content_prompt(..., known_words=[], min_new=5)`: thêm khối **"🧠 CÁC TỪ ĐÃ DÙNG Ở NHỮNG NGÀY TRƯỚC"** (150 từ gần nhất) + ràng buộc **"ÍT NHẤT 5 từ phải là TỪ MỚI"** + **"TỐI ĐA 5 từ được phép lặp lại (phần ÔN LẠI, kèm ví dụ câu khác)"** ⇒ mỗi ngày học **5 từ mới + 5 từ ôn lại** (đúng sư phạm "học từ 0": không quên từ cũ nhờ SM-2).
- `ai/pipeline._known_words(course, day_num, limit=150)`: gom từ của các ngày **trước** (bỏ từ rỗng, giới hạn 150 từ để prompt không phình).
- **Đo tỉ lệ từ mới** sau mỗi ngày: checkpoint content lưu `new_words` + `new_word_ratio`; tỉ lệ < 40 % ⇒ log cảnh báo `stage.low_new_ratio` (để thấy ngay ngày nào AI lặp).

**Test:** `tools/test_new_word_ratio.py` mới **13/13** (`_known_words` gom đúng + giới hạn + bỏ từ rỗng · prompt có/không khối "từ đã dùng" · đo `new_words`/`new_word_ratio` đúng · cảnh báo khi tỉ lệ thấp · không cảnh báo khi tỉ lệ cao).

**Kế hoạch còn lại của Gói 5:** 5.2 bù hội thoại cho Trung/Tây/Đức (~1.150 ngày) + media còn thiếu · 5.3 đồng bộ field cho 7 khóa cũ (`phonetic_note`, `syllables`, `grammar.mini_quiz`) — cả hai dùng quota Gemini nên chạy nền khi pool còn quota.

---

## 7.24. AUDIT CHẤT LƯỢNG NỘI DUNG + GIÁO TRÌNH + FIX TclError KHI ĐÓNG APP (2026-11-12d)

**1) Lỗi `_tkinter.TclError: invalid command name ...!ctkcanvas`** (user gặp khi đóng app): customtkinter đang **vẽ lại** một widget đã bị `destroy()` ⇒ lệnh canvas không còn tồn tại. Nguồn: timer tự đồng bộ 5 s của tab Học Tập (§7.22) còn sống lúc cửa sổ bị xoá.
**Đã sửa:** `_cancel_sync()` hủy timer trước khi `destroy()` (gọi từ `App.on_close`) · `_sync_tick` chỉ vẽ lại khi tab **đang hiển thị** (nếu không thì chỉ nhớ mtime, lần sau mở tab mới nạp) · mọi thao tác widget bọc `try/except`.
**Lưu ý vận hành:** trên máy đang chạy **4 tiến trình `main.py` + 1 `VocabApp.py`** ⇒ đóng các instance thừa (chỉ nên có 1 app).

**2) Tool mới `tools/audit_curriculum.py`** — đo chất lượng nội dung + giáo trình mọi khóa (không đo checkpoint, đo `course.json` thật):

| khóa học | ngày | từ (unique) | trùng lặp | pronunciation/ipa/POS/nghĩa/ví dụ | ngữ pháp (có ví dụ / mini_quiz) | hội thoại (lượt / có từ trọng tâm) | trắc nghiệm |
|---|---|---|---|---|---|---|---|
| tiếng_anh | 259 | 2.590 (**1.956**) | **24,5 %** | 100 % / 100 % / 100 % / 100 % / 100 % | 583 (100 % / **0 %**) | 241 bài · 2.268 lượt · 2.122 | 10.334 (0 lỗi) |
| tiếng_nhật (mới) | 103 | 1.197 (**627**) | **47,6 %** | 100 % / 100 % / 100 % / 100 % / 100 % | 205 (**3 %** / 99 %) | 97 bài · 487 lượt · 269 | 4.009 (0 lỗi) |

**3) Giáo trình — ĐÚNG KHUNG 6 CHẶNG** (backbone 1.260 mục = 1 ngày/mục, phase = tiền tố tiêu đề):
`Vỡ lòng chữ cái & phát âm` 60 ngày · `Ghép âm & Từ đơn sinh tồn` 90 · `Sơ cấp đời sống` 280 · `Trung cấp công việc` 350 · `Cao cấp học thuật` 300 · `Như người bản xứ` 180 = **1.260 ngày**. 10 ngày đầu khóa Nhật có **34,5 % kana thuần** ⇒ đúng bước "học từ 0" (bảng chữ cái trước).

**4) VẤN ĐỀ THẬT CẦN SỬA — "nhiều ngày" ≠ "nhiều nội dung mới":**
Đo trùng lặp **theo chặng** (khóa Nhật): chặng 1 `Vỡ lòng` 59 ngày → 272/701 từ lặp (**38 %**) · chặng 2 `Ghép âm` 44 ngày → 298/496 lặp (**60 %**). ⇒ 1.260 ngày hiện chỉ ~630 từ **khác nhau** ở 103 ngày đầu ⇒ học 200+ ngày mà không có đủ từ mới là do **logic sinh**, không phải do giới hạn quota.
⇒ Đề xuất **Gói 5** (chờ user duyệt): ① content prompt nhận "từ đã dùng" và yêu cầu **≥5 từ MỚI + ≤5 từ ÔN LẠI** mỗi ngày (đúng sư phạm), đo tỉ lệ từ mới theo ngày/chặng và ghi log; ② bổ sung field còn thiếu ở 6 khóa cũ (`phonetic_note`, `syllables`, `grammar.mini_quiz`); ③ tab "Bắt đầu từ 0" (lộ trình 6 chặng + mốc + flow đọc→nghe→nối câu→ôn SM-2); ④ sinh media (ảnh + audio từ/nghĩa/hội thoại) cho khóa Nhật.

---

## 7.23. GỘP 1 BẢN CHUẨN MỖI NGÔN NGỮ + LÀM LẠI HÀNG NÚT & PANEL RỖNG (2026-11-12c)

**Yêu cầu (user):** *"quá nhiều bản tiếng Nhật — thống nhất lại 1 bản chuẩn; cần từ vựng, ngữ pháp, phát âm, hình ảnh; giao diện các nút Sinh AI / Xóa tiến độ đang quá xấu."*

### ① Gộp khóa học — tool `tools/consolidate_courses.py`
Trước khi gộp có **8 thư mục cùng ngôn ngữ Nhật + 6 artifact test**:

| thư mục | ngày | có nội dung | MB | quyết định |
|---|---|---|---|---|
| `nhật` (alias cũ) | 1.414 | 59 | 8,4 | dọn (trùng) |
| `_alias_nhat_cu` | 1.414 | 59 | 8,4 | dọn |
| `_nhat_placeholder_cu` | 1.260 | 1.260 (**placeholder**) | 94,6 | dọn |
| `tiếng_nhật_smoke` | 1 | 1 | 0,1 | dọn (test) |
| `zz_corrupt` · `zzkhongcokey` · `zzlang` | 0 | 0 | 0 | dọn (test) |
| **`tiếng_nhật` (canonical)** | đang sinh | nội dung THẬT | – | **GIỮ** |

Nguyên tắc: mỗi ngôn ngữ chỉ giữ **một** bản (tên canonical + nhiều ngày có nội dung nhất); bản bị loại **chuyển vào `data/_trash/<timestamp>/`** (không xoá ngay — xoá hẳn bằng `--apply --purge-trash`); `__global__` (chứa `dead_models.json` dùng chung) **giữ nguyên**; media trùng (`media/nhật`, `media/_nhat_placeholder_cu` 352,6 MB, `media/tiếng_nhật_smoke`, `media/zztest`) + file review của alias cũng dọn.
**Kết quả:** còn **8 khóa chuẩn** (`tiếng_anh · hàn_quốc · nga · nhật · pháp · trung · tây_ban_nha · đức`) + `__global__`; giải phóng **~438 MB**; không mất khóa chuẩn nào (đã kiểm tra lại `course.json` còn đủ).

### ② Giao diện
- **Hàng nút hành động bị tràn**: 3 nút (`🤖 Sinh khóa học AI`, `🗑️ Xóa khóa & tiến độ`, `🔀 Trộn thẻ`) pack `side="right"` vào `head` trong khi `head_inner` (`expand=True`) đã chiếm hết bề ngang ⇒ nút bị đẩy và **bị cắt chữ** ("Iron the…" trong ảnh). Nay chuyển sang **hàng riêng "Thao tác:"** dưới header, kèm 2 nút mới: `🔄 Tải lại` (nạp lại khóa học) và `📚 Trang học (web)` (mở trang học 127.0.0.1:5690/index).
- **Panel Trắc nghiệm rỗng**: khi không có câu hỏi ⇒ **ẩn hẳn 4 nút chấm** (Quên/Khó/Được/Dễ đang mờ chết cứng) và bỏ dòng *"🧠 Không xác định được từ của câu này"* ⇒ không còn 2 dòng vô nghĩa + 4 nút mờ.

**Test:** `tools/test_study_sync.py` mở rộng lên **30/30** (thêm: **layout** — 5 nút hành động không bị nén và không tràn khỏi cửa sổ 1400×900; **panel rỗng** — 4 nút chấm bị ẩn khi không có câu và hiện lại khi có câu). Full suite **2 vòng: FAILs = 0** · compile0.

**Lưu ý vận hành:** đang chạy **2 tiến trình `VocabApp.py`** (24468, 24928) ⇒ đóng 1 instance, và **restart app** để nạp code GUI mới (auto-sync 5s · canonical slug · badge độ đầy đủ · hàng nút mới).

---

## 7.22. GÓI 4 — FIX UX "KHÔNG THẤY NỘI DUNG" + ĐỘ ĐẦY ĐỦ NGÀY (2026-11-12b)

**Triệu chứng (ảnh chụp từ user):** tab Học Tập hiện *"0/0 · 0/0"*, dòng *"nội dung đã lọc"*, ô *"Chưa hoàn thành"*, panel Ôn tập **0/0**, thanh tiến độ *0/1414 ngày* — trong khi file `course.json` trên đĩa **đã đầy**. Người dùng bấm "Sinh khóa học AI" mà **không thấy nội dung**.

**Nguyên nhân (3, đều là lỗi cache/slug — không phải lỗi sinh nội dung):**
1. **GUI giữ cache trong RAM**: `self._course` nạp lúc mở app ⇒ pipeline sinh xong (hoặc khóa học bị đổi tên) nhưng GUI vẫn hiện bản cũ (rỗng). Không có nút "làm mới", không tự nạp lại.
2. **Slug thô trong GUI**: `App.set_language()` lưu slug như `"nhật"` trong khi `course.json` nằm ở thư mục canonical `"tiếng_nhật"` ⇒ app đọc nhầm (hoặc đọc file rỗng) ⇒ mọi panel rỗng.
3. **Pool ôn tập không nạp lại**: `refresh_language()` xoá `_srs_pool_cache` nhưng **không nạp lại** ⇒ panel Ôn tập luôn 0/0 dù khóa học có hàng nghìn từ.

**Đã sửa (`VocabApp.py`):**
- **Tự đồng bộ 5 giây/lần**: `_course_file_mtime()` + `_sync_tick()` — thấy `course.json` trên đĩa đổi ⇒ **tự nạp lại khóa học, vẽ lại ngày đang xem, nạp lại pool ôn tập, cập nhật thống kê** (không cần bấm gì, không cần restart app).
- **Canonical slug** cho `App.set_language()` ⇒ alias (`nhật`/`ja`) và slug chuẩn luôn trỏ cùng file.
- **Empty state nói rõ làm gì tiếp** (3 lựa chọn cụ thể): bấm 🤖 Sinh khóa học AI · nội dung sẽ tự hiện nếu pipeline đang chạy · mở 📚 Trang học trên trình duyệt (thay vì 1 dòng "Chưa có khóa học AI" khiến tưởng app hỏng).
- **Ngày rỗng nêu rõ**: "⚠ Ngày N chưa có nội dung — bấm 🤖 Sinh khóa học AI để tạo, hoặc chọn ngày khác".
- **Badge độ đầy đủ ngày**: `⏳ Chưa hoàn thành · 12 từ · 2 ngữ pháp · 1 hội thoại · 12 audio · 10 ảnh` (thay vì "0/0 · 0/0" gây hiểu nhầm).
- **Pool ôn tập nạp lại** sau khi sinh/đổi khóa học.

**Tool mới:** `tools/verify_courses.py` — báo cáo độ đầy đủ mọi khóa (ngày rỗng · từ · ngữ pháp · hội thoại · quiz · ảnh · audio từ · audio nghĩa · audio hội thoại · số từ "placeholder") đo trên `course.json` + file media thật.

**Test:** `tools/test_study_sync.py` mới **16/16** (canonical slug · tóm tắt độ đầy đủ · **auto-sync khi file đổi (không bấm gì)** · empty state có hướng dẫn · pool ôn tập có nghĩa · không crash khi thiếu file). **Full suite chạy 2 vòng liên tiếp: FAILs = 0** (media25 · stop_makeup37 · recovery18 · srs_api17 · study_sync16 · dashboard57 · quota94 · keymgr111 · 3mode41 · slug6 · ai_rich85 · smoke15 · media_resolver6 · media_card6 · compile0).

**Lưu ý:** app đang chạy phải **restart 1 lần** để nạp code GUI mới; sau đó app tự đồng bộ mọi thay đổi tiếp theo.

---

## 7.21. GÓI 3 — WEB HỌC THẬT: ÔN TẬP SM-2 · TẢI THEO NGÀY · OFFLINE · AN TOÀN (2026-11-12)

**Vấn đề (đo thật):** rà soát web cho thấy trang học là **trình xem read-only**: không có API nào ghi tiến độ học ⇒ "học từ online" không đóng được vòng lặp. SM-2 (`ai/srs.py`) + kho trạng thái (`database/review_store.py`) đã viết hoàn chỉnh nhưng **chỉ app desktop gọi** — web không có route nào. Thêm: web tải **cả file `course.json` 47 MB** + manifest media 38 MB; phụ thuộc **2 script CDN**; `DOMPurify` lỗi ⇒ `innerHTML` thô của nội dung AI; `/data/*` mở toàn bộ (đọc được tiến độ ôn tập + log pipeline).

**Đã sửa:**
1. **API ÔN TẬP SM-2** (mới, `ai/bridge_server.py`): `GET /api/vocab/srs/queue?lang=&limit=` · `POST /api/vocab/srs/review {lang, word, grade}` (grade ∈ again/hard/good/easy) · `GET /api/vocab/srs/stats`. Ghi **chung file `data/reviews/<slug>.json`** với app desktop ⇒ tiến độ học một nơi. Lần đầu mở tab Ôn tập sẽ `sync_from_vocab` để hàng đợi có từ chưa học. **Origin check** (chỉ `http://127.0.0.1:5690` / `localhost:5690`) ⇒ chặn CSRF từ web khác (Origin lạ → **403**).
2. **Tab 🧠 Ôn tập** trên web (`web/index.html` + `web/script.js`): thẻ từ (mặt trước: từ + phiên âm + audio · lật: nghĩa + ví dụ + ảnh + audio từ + audio nghĩa) · 4 nút chấm điểm đúng nhãn tiếng Việt của app (`😵 Quên hẳn / 😕 Khó / 🙂 Được / 😎 Rất dễ`) · hiện lịch ôn tới ("ôn lại sau N ngày") · thanh thống kê (đến hạn · đã thuộc · 🔥 streak) · phím tắt `1-4`.
3. **Tải khóa học THEO NGÀY**: `GET /api/vocab/course/<slug>/index` (danh sách ngày) + `GET /api/vocab/course/<slug>/day/<n>` (1 ngày ~40 KB), cache theo mtime phía server ⇒ mở tab/đổi ngày **không còn tải 47 MB**; có fallback về `course.json` cũ.
4. **BỎ phụ thuộc CDN**: `marked` + `DOMPurify` (jsdelivr) bị gỡ khỏi `index.html`; `formatText()` nay **tự escape** rồi áp markdown cơ bản ⇒ (i) app chạy được **offline**, (ii) không còn đường `innerHTML` thô của nội dung AI (XSS).
5. **Media lỗi hiện rõ**: trước `onerror` xoá im lặng (không phân biệt "chưa có" với "file hỏng") ⇒ nay hiện chip `⚠ Không có audio` / `⚠ Ảnh không tải được`; thêm hàng **audio nghĩa** (`meaning_audio_ref`) vốn có trong dữ liệu nhưng web bỏ qua.
6. **A11y & responsive**: bỏ `user-scalable=no` (chặn pinch-zoom) · `#clear-search` `<span>` → `<button>` có `aria-label` · `role="tablist"` + `aria-selected` + `aria-live` · `:focus-visible` cho bàn phím · `@media (max-width: 720px)` (bố cục dọc trên điện thoại) · `prefers-reduced-motion` · nhãn tiếng Việt thay chữ Anh.
7. **Bridge hardening**: `/data/*` **chặn** `reviews/`, `logs/`, `_pipeline/`, `*.bak*`, `*.tmp*` (403) — trang học không cần chúng · `/api/vocab/next` **không còn trả lại `bridge_token`** trong body.
8. **GUI**: nút **📚 Trang học** + **🎛️ Dashboard** (mở đúng URL, dashboard kèm token — trước phải gõ tay/copy tay) · **che token** trên màn hình (giống API key) · thông báo lỗi bridge nói đúng nguyên nhân (thiếu Flask) thay vì nuốt lỗi.

**Test:** `tools/test_srs_api.py` mới **17/17** (index + lesson theo ngày + queue có nghĩa/audio · review ghi state & lịch ôn tới · grade sai → 400 · Origin lạ → 403 · gzip · file review tách theo slug). Test thật bằng **trình duyệt**: dropdown hiện tên đẹp ("Tiếng Nhật") · khóa Nhật **1.260 ngày** trong dropdown · Ngày 1 render **10 audio + 10 ảnh** · tab Ôn tập: hàng đợi **1.956 từ** (Tiếng Anh) · chấm "Được" ⇒ streak **1 ngày**, "đến hạn" 1956 → 1955, file `data/reviews/tiếng_anh.json` ghi đúng (`cat`: state=review, interval≈4h, reps=1) · **0 lỗi console**. Suite xanh: media25 · stop_makeup37 · recovery18 · srs_api17 · dashboard57 · quota94 · keymgr111 · 3mode41 · slug6 · ai_rich85 · smoke15 · compile0.

**PHÁT HIỆN QUAN TRỌNG (cần quyết định — Gói 4):** sau khi khôi phục, đo nội dung khóa Nhật cho thấy **100% là dữ liệu sinh tự động** (`単語10`, `tango10`, "Nghĩa từ vựng số 10") ⇒ 1.260 ngày này **không dùng để học được**, phải sinh lại bằng Gemini (≈ 1.260 × 4 call). Sáu khóa còn lại (Anh · Hàn · Nga · Pháp · Trung · Tây · Đức) là nội dung thật nhưng thiếu **hội thoại (~130 ngày)** và **ảnh (~1.300 ngày `degraded`)** ⇒ cần bù media (edge-TTS + Wikipedia, **không tốn quota Gemini**).

---

## 7.20. GÓI 2 — KHÔI PHỤC & BẢO TOÀN KHÓA HỌC (2026-11-12)

**Bối cảnh:** rà soát toàn app (4 hướng: web UI · logic pipeline · key/anti-block · server/SRS) → chốt 4 gói cải tiến. User duyệt thứ tự **2 → 3 → 4** (Gói 1 = key để sau, xem mục *Khuyến nghị về key*).

**Chẩn thật (đo trên data Desktop, 2026-11-12):**

| slug | ngày | vocab rỗng | quiz rỗng | hội thoại rỗng | ảnh `degraded` | audio nghĩa | audio hội thoại |
|---|---|---|---|---|---|---|---|
| **tiếng_nhật** | **KHÔNG CÓ `course.json`** | – | – | – | – | – | – |
| nhật (alias cũ) | 1414 | **1410** | 1414 | 1410 | – | 0 | 0 |
| tiếng_anh | 259 | 0 | 1 | 18 | 1 | 0 | 0 |
| tiếng_hàn_quốc | 450 | 0 | 5 | 34 | 205 | 0 | 0 |
| tiếng_nga | 381 | 0 | 0 | 84 | **381** | 0 | 0 |
| tiếng_pháp | 343 | 0 | 0 | 57 | **343** | 0 | 0 |
| tiếng_trung | 446 | 0 | 4 | **423** | **446** | 0 | 0 |
| tiếng_tây_ban_nha | 345 | 0 | 4 | **329** | **345** | 0 | 0 |
| tiếng_đức | 342 | 0 | 0 | **310** | **335** | 0 | 0 |

⇒ **1.260 ngày Nhật đã sinh xong (content + quiz = `done` trong `_pipeline`) nhưng KHÔNG có `course.json` ⇒ web không hiển thị được**; khóa alias `nhật` là 1.414 ngày mà **1.410 ngày rỗng**; media manifest 32.8 MB / 65.013 entry trong khi đĩa có **77.626 file** ⇒ **12.655 file mồ côi** (mất entry ⇒ nút media biến mất).

**Đã sửa (10 mục):**
1. **Tool `tools/rebuild_course_from_checkpoints.py`** — dựng `course.json` canonical **TỪ CHECKPOINT** (0 call AI, 0 quota): `--dry-run` mặc định, `--apply` mới ghi (có backup). **Kết quả: 1.260 ngày · 12.600 từ · 50.400 câu hỏi · 46.9 MB** (`data/ai_courses/tiếng_nhật/course.json`).
2. **Tool `tools/reindex_media.py`** — dựng lại manifest từ file thật (id = `m_` + hash(rel_path, sha256), **giống hệt** cách `save_*` tạo id ⇒ khôi phục đúng ref mà `course.json` trỏ tới). `--check` chỉ báo cáo.
3. **Flush `course.json` Ở MỌI ĐƯỜNG THOÁT** (`pipeline.py` `finally`) — trước đây bấm ⏹ mất ≤9 ngày (checkpoint có, `course.json` chưa ⇒ web không thấy).
4. **Khôi phục quiz từ checkpoint khi resume** (`quiz_ab`/`quiz_cd` → `lesson["quiz"]`) — trước đây 14 ngày mất quiz **vĩnh viễn** dù data còn trên đĩa.
5. **Xoá skeleton ngày rỗng** khi stage content thất bại (`_drop_empty_lesson`) — web không còn hiện "ngày trống".
6. **`canonical_slug` thống nhất** cho `pipeline_store.pipeline_dir` · `tts_generator.audio_dir` · `review_store.reviews_path` — trước đây `--lang ja` ghi checkpoint vào thư mục **khác** với `course.json` ⇒ resume hỏng, mọi stage chạy lại tốn quota.
7. **Call hội thoại ĐƯỢC tính quota** (`can_call` + `consume_call`) — trước đây call đầu mỗi ngày không tính ⇒ ~1.400 call Gemini lọt khỏi bộ đếm bền `_jobs.json`.
8. **Ảnh phủ hết số từ** (`max_images_per_day=0` ⇒ theo số từ) — trước đây cap 10 < 12 từ/ngày ⇒ **25 ngày kẹt PENDING vĩnh viễn** + pass bù lặp mãi.
9. **Pass bù hội tụ** (`MAX_PENDING_MAKES=3`) — verify chỉ đánh dấu "sinh bù" tối đa 3 lần rồi chuyển `degraded` ⇒ hết hiện tượng **12 call Gemini mỗi run, mãi mãi**.
10. **Chống ghi đè `course.json`** — `course_db.update_day()` (đọc bản mới nhất trên đĩa → sửa đúng 1 ngày) thay cho việc GUI ghi lại `self._course` (snapshot cũ) ⇒ không còn mất ngày của pipeline; `media_store.save_index` không còn ghi thẳng vào file live (tránh manifest **truncated**); `bridge_server` bỏ qua thư mục dự phòng `_…` + trả `names` tên hiển thị đẹp.

**Test:** `tools/test_course_recovery.py` mới **18/18** (resume quiz · xoá ngày rỗng · flush khi dừng · canonical slug · dialogue tính quota · ảnh phủ hết từ · pass bù hội tụ · `update_day`). `tools/test_3mode.py` chuyển sang lesson mẫu khi khóa canonical chưa có hội thoại (trước đó test **SKIP** vì file chưa tồn tại, nay fail vì lý do không liên quan code) → 41/41. Suite xanh: media25 · stop_makeup37 · recovery18 · dashboard57 · quota94 · keymgr111 · 3mode41 · slug6 · ai_rich85 · smoke15 · compile0.

**Khuyến nghị về key (chưa làm — user chọn để sau):** repo `Project1` đang **PUBLIC** và 3 file chứa **197 key/20 account** đang được track trong git (`ENC:` chỉ là base64 đảo chuỗi ⇒ giải mộc được). Việc ít rủi ro nhất: **đổi repo sang private** (chặn ngay rò rỉ mới) → rồi mới gỡ file khỏi index + `gitignore` + purge history + **rotate key**.

---

## 7.19. FIX 3 LỖI PIPELINE: ⏹ DỪNG ĂN NGAY · BÙ TRONG CÙNG RUN · AUDIO NGHĨA/HỘI THOẠI (2026-11-11b)

**Triệu chứng (user):** ① bấm ⏹ Dừng mà pipeline vẫn chạy tiếp; ② media bị "đánh dấu sinh bù lần sau" thay vì chạy hết trong 1 run; ③ nhiều ngày chưa đủ âm thanh.

**Chẩn thật (data Desktop):** ③ **1.302 hội thoại → 0 có `audio_ref`** (`media.dialogue_audio={}` rỗng — không stage nào từng sinh audio hội thoại) · **`meaning_audio_ref` = 0/1.414** dù `tts_bilingual_mode: true` · khóa nhật chỉ 27 checkpoint content vs 1.414 ngày plan (hầu như rỗng) · `tiếng_nhật` 1.260 ngày media 0 file audio. ① `_run_days_parallel` submit hết futures chờ 4 luồng chạy hết ngày; `_run_day` không stop_check giữa stage; `_ask_with_retry` retry 3 lần khi `kind="stopped"`; `run_dialogue_stage` nuốt stopped → vẫn verify + mark makeup. ② GUI chạy single-pass (`passes=2` chỉ khi CLI `--all`) → verify mark PENDING luôn chờ lần chạy sau.

**Sửa:**
- **A. Dừng ăn ngay** (`pipeline.py` · `pipeline_media.py`): `_ask_with_retry` raise `GenerationStopped` NGAY khi `kind="stopped"`/exception (không retry 3) · `_run_day(..., stop_check=)` + `_stop()` trước MỖI stage · `run_images_stage`/`run_audio_stage` dừng giữa chừng → **save PENDING + raise** (giữ phần đã sinh, không synth thêm) · `run_dialogue_stage` raise thay nuốt · `_run_days_parallel`: `except GenerationStopped → "stopped"`, **cancel futures hàng đợi** (các luồng thoát ≤1 stage nhờ stop_check) + `try/finally` flush `course.json` (fix mất ≤9 ngày khi dừng).
- **B. Bù trong cùng run**: hàm mới `_media_pending_days` + `_makeup_pending_days(max_passes=2)` — **MỌI run (kể cả GUI ▶)** tự quét ngày media PENDING sau day loop và bù tối đa 2 vòng; dừng khi: đã Dừng · hết quota · hết thời gian · không ngày nào tiến triển. Giữ nguyên `passes=2 if --all` (vô hại).
- **C. Đủ âm thanh**: sinh **audio HỘI THOẠI** (edge-TTS, 1 file/hội thoại nối lượt bằng " … " → `media.dialogue_audio[di]` + `dlg.audio_ref`, checkpoint `dialogue_tracks`, re-attach guard theo TITLE) · make-up **skip-existing từng variant** (từ đã đủ `audio_ref`/`meaning_audio_ref` → không TTS lại; sinh nghĩa đọc `meaning_vi` thật — fix trước fallback sang `it["text"]` ⇒ đọc lại tiếng Nhật bằng giọng Việt) · `run_media_verify_stage` đếm thêm **audio nghĩa + audio hội thoại thiếu** → mark AUDIO pending với log liệt kê cụ thể · fix crash `chain=None` ở `coord = chain.providers…`. Web `/index` đọc `media.dialogue_audio[di] || dlg.audio_ref` (`script.js:694`) → nút phát hội thoại sáng ngay khi có ref; **verify chạy lại mọi ngày mỗi run** (không skip) nên khóa cũ thiếu audio cũng bị mark → bù ngay trong run.

**Test:** `tools/test_stop_makeup.py` mới **37/37** — A1/A1b dừng ngay (gọi ĐÚNG 1 lần) · A2 `_run_day` raise trước stage · A3 parallel không treo + finally save · A4 dialogue không checkpoint degraded · A5 audio dừng → PENDING không synth · B6/B7 makeup bù ngay/dừng khi Dừng/hết quota · **B8 integration**: `run_pipeline` thật → audio stage gọi đúng 2 lần (day loop + pass bù) → checkpoint DONE · C8/C8b skip-existing + audio nghĩa + audio hội thoại + reattach TITLE · C9 verify đếm. Suite xanh: dashboard57 · quota94 · media25 · stop_makeup37 · keymgr111 · 3mode41 · slug6 · ai_rich85 · smoke15 · compile0.

**Cách dùng:** restart app để nút ⏹/GUI chạy code mới → ▶ chạy bình thường; bấm ⏹ là dừng trong ≤1 stage (phần đã sinh giữ nguyên); ngày media thiếu tự bù **ngay trong run** (log `🔁 Pass bù …`); khóa cũ audio/hội thoại thiếu được verify đánh dấu + bù dần ở các run sau.

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


---

## 7.30. GÓI 8 — LÀM LẠI GIAO DIỆN: THANH CÔNG CỤ + ẨN PANEL RỖNG (2026-11-14b)

**Yêu cầu user:** "các nút Sinh AI / Xoá tiến độ / hàng thao tác đang xấu → cần làm lại".

### Đã làm
1. **Thanh công cụ gom 3 nhóm** (thay 6 nút chen nhúc trên 1 hàng):
   - **Học**: 📚 Trang học · 🗺️ Lộ trình · 🔀 Trộn thẻ
   - **Khóa học**: 🤖 Sinh AI · 🔄 Tải lại
   - **Nguy hiểm**: 🗑️ Xóa (viền đỏ, tách bạch, đẩy sang phải)
   Nhãn rút gọn ≤ 16 ký tự (trước: "🤖 Sinh khóa học AI" 170 px), có **dấu phân cách** giữa các nhóm.
2. **Tooltip mới** (`class ToolTip` trong `VocabApp.py`): hover 500 ms → hiện giải thích nút
   (Tkinter không có tooltip sẵn; CTkButton bind vào `_canvas` nên phải bọc riêng).
3. **Ẩn panel rỗng** — `media_strip` (danh sách từ) và `dlg_panel` (hội thoại) **không còn hiện
   khung 248 px trống** khi ngày không có nội dung.
4. **Nhãn trạng thái rõ nghĩa**: "⏳ Chưa hoàn thành" → **"📖 Chưa học ngày này"** (nhãn cũ gây
   hiểu nhầm là app lỗi); "✅ Hoàn thành" → "✅ Đã học xong".

### BUG THẬT phát hiện khi làm UI (đo được)
`CTkScrollableFrame` (CustomTkinter **6.0.0**) dựng như sau:

```
_parent_frame
  └─ _parent_canvas (Canvas)   ← GRID vào _parent_frame  ⇒ QUYẾT ĐỊNH HIỂN THỊ
       └─ canvas window item → chính frame (pack trong canvas, KHÔNG quyết định hiển thị)
```

⇒ `media_strip.pack_forget()` **KHÔNG ẩn panel** (canvas vẫn nằm trong grid) ⇒ panel rỗng vẫn
chiếm 248 px. Đã thêm helper `set_scroll_visible(scrollable, visible)` dùng
`canvas.grid_remove()` / `canvas.grid()`.

### Test
`tools/test_ui_toolbar.py` → **7/7 PASS** (6 nút đúng nhãn · nhãn ≤ 16 ký tự · mọi nút có
tooltip bind `<Enter>` trên canvas · nút Xóa viền đỏ · panel rỗng ẩn thật (kiểm tra
`grid_info()` của `_parent_canvas`) · nhãn trạng thái mới).
Hồi quy: `test_day_nav_loop` **310/310** · `test_study_sync` **39/39** · `test_gui_smoke` **15/15**.

---

## 7.29. GÓI 7 — 5 LỖI "MEDIA KHÔNG BAO GIỜ ĐƯỢC BÙ" (2026-11-14a)

**Bối cảnh:** 8 khóa đều đã có **2.520 ngày** nội dung ("0 → bản xứ"), nhưng **media % rất thấp**
(ảnh 0-46 %, audio 12-92 %, hội thoại 0,6-92 %). Job "bù media" chạy mãi mà **không tăng** được
gì. Đo từng tầng ⇒ tìm ra **5 lỗi thật**, tất cả đều là *media 0 quota bị hệ thống chặn như
job AI* hoặc *sinh rồi bị coi là "xong" rồi bỏ rơi*.

### 5 lỗi (đều có số liệu đo được)

| # | Lỗi | Hậu quả đo được | Cách sửa |
|---|---|---|---|
| 1 | `_makeup_pending_days()` dùng `source=source` nhưng **không có tham số `source`** | `NameError` ⇒ **"đã bù 0/1157 ngày"** — pass bù media không bao giờ chạy | thêm `source: str = "auto"` + truyền `source=source` từ caller |
| 2 | `_run_days_parallel()` dùng `source=source` nhưng **không có tham số** | `NameError` ⇒ **600 `day.fail`** khi chạy `--workers > 1` (đúng cấu hình job bù media!) | thêm `source: str = "auto"` vào signature + truyền từ caller |
| 3 | `budget.can_call(4)` chạy **trước mỗi ngày** cho mọi pipeline ⇒ job media (**0 call Gemini**) cũng bị chặn khi hết quota AI | media đứng im ở 12-33 % | `_needs_ai_budget(stages)`: chỉ stage **cần AI** (content · quiz · dialogue) mới bị chặn |
| 4 | `run_images_stage` / `run_audio_stage`: checkpoint **`skipped`** (lúc đó ngày chưa có vocab) bị `stage_is_done` coi là **"đã xong"** ⇒ **không bao giờ sinh lại** | tiếng_trung **439/446 ngày** ảnh = skipped ⇒ ảnh % = 0 | nếu nay đã có vocab/dialogue mà checkpoint = skipped ⇒ **sinh lại** |
| 5 | `MAX_PENDING_MAKES = 3` áp cho **cả media** ⇒ sau 3 lần bù thất bại, chuyển `degraded` ⇒ `stage_is_done` coi là xong | tiếng_nhật **1.157 ngày** bị "chốt" | `MAX_PENDING_MAKES_MEDIA = 12` (media 0 quota không sợ đốt quota) |

### Bug thứ 6 (phát hiện khi đo song song)
`media_store._upsert_index()` khi flush theo lô **ghi thẳng cache RAM, không merge đĩa** ⇒ khi
nhiều tiến trình cùng sinh media (8 khóa song song) thì tiến trình này **xoá entry của tiến
trình kia** ⇒ file media có trên đĩa nhưng mất manifest ⇒ app không hiện.
Đo thật: **157.091 file media** nhưng manifest chỉ còn ~39.000 entry.
Sửa: `_flush_merged()` — đọc đĩa → merge cache → ghi atomic (giống `flush_index`).

### Công cụ mới
- `tools/fill_media.py` — **bù media nhiều khóa song song** (`--jobs`, `--workers`, `--all-days`),
  tự dừng khi disk < 6 GB, chạy lại được (idempotent).
- `tools/check_scope.py` (mới, trong `tools/`) — **kiểm tra tĩnh biến chưa định nghĩa** (loại
  NameError) bằng `ast` — chính là công cụ đã bắt được lỗi #2.

### Test
`tools/test_day_nav_loop.py --rounds 30` → **930/930** (course thật 2.520 ngày) ·
`tools/test_study_sync.py` → **39/39** · `tools/test_ui_toolbar.py` → **7/7** ·
`tools/test_gui_smoke.py` → **15/15** · `py_compile` toàn bộ file sửa → OK.

---

## 7.28. GÓI 6 — 1 LỆNH DỰNG "0 → BẢN XỨ" CHO MỌI NGÔN NGỮ (2026-11-13/14)

**Yêu cầu user:** *"vấn đề chính là phải học từ 0 → bản xứ với mọi ngôn ngữ · làm sao để tương
lai tạo được · hiện tại là bổ sung · lặp đến khi hoàn thành"*.

### ① "Tương lai tạo được" → 1 LỆNH
```powershell
python toolsuild_all_courses.py                 # mọi ngôn ngữ, LẶP tới khi đủ
python toolsuild_all_courses.py --lang tiếng_hàn_quốc
python toolsuild_all_courses.py --status        # chỉ xem bảng độ đầy đủ
```
Một lệnh đó chạy **vòng lặp 4 bước** (mỗi vòng bỏ qua phần đã đủ):
- **B1 nguồn từ**: `wordfreq` (tần suất thật) + **dịch lô 25 từ/request** → tiếng Việt
- **B2 giáo trình**: 6 chặng N5→N1 (từ thấp lên cao) + ngữ pháp **theo cấp độ chặng** +
  hội thoại + trắc nghiệm
- **B3 media**: ảnh (Wikipedia/điển) + audio edge-TTS (từ/nghĩa/hội thoại) — **0 quota Gemini**
- **B4 kiểm tra**: `tools/check_done.py` → tiêu chí "đủ" + **toast Windows**
Ngôn ngữ mới chỉ cần **thêm 1 dòng vào `ISO_BY_LANG`** (`ai/offline_content.py`) rồi chạy lệnh.

### ② "Dịch lô" — từ 231 từ/giờ → **300 từ/giây**
Trước đây gọi Wiktionary **1 request/từ** ⇒ 26.000 từ mất **4,6 ngày**. Đổi sang dịch lô
**25 từ/request** ⇒ 26.000 từ chỉ **~90 giây**.
Hai lỗi đo được khi làm:
- API dịch cả lô trả về **1 đoạn nhiều dòng** ⇒ mất 24/25 từ ⇒ phải tách theo `\n`.
- `sl=auto` **không nhận Hàn/Nga** (đo: 25.025 từ duyệt ⇒ **0 từ** có nghĩa Việt) ⇒ phải
  dùng **mã ngôn ngữ** (`sl=ko/ru/zh`). Test: `사람 → người`, `하지만 → Nhưng`.

### ③ Kết quả (đo thật 14/11)
8 khóa đều có **2.520 ngày** nội dung: tiếng_nhật · tiếng_trung · tiếng_anh · tiếng_hàn_quốc ·
tiếng_nga · tiếng_pháp · tiếng_đức · tiếng_tây_ban_nha — với **100 % nghĩa tiếng Việt**
(kiểm chứng: `한다 = làm`, `다른 = khác`, `дождался = chờ đợi`, `一个 = một`, `中国 = Trung Quốc`).

### ④ "Lặp đến khi hoàn thành" — 3 vòng lặp chạy song song
1. **Watchdog 24/7** (`tools/ai_watchdog.py`): AI (00:00 VN, quota reset) → bù media → verify → check_done.
2. **Task Scheduler `VocabularyApp-CheckDone`** mỗi 30 phút → `check_done` → **toast Windows** khi đủ.
3. **`build_all_courses.py`**: chạy lại bất kỳ lúc nào để bổ sung phần còn thiếu.
Theo dõi: `data/logs/check_status.txt` (bảng độ đầy đủ) · `data/logs/watchdog.log` ·
`data/logs/fill_media_v3.log` (bù media).


---

## 7.31. ĐỒNG BỘ NỘI DUNG 8 KHÓA + FIX MANIFEST MEDIA HỎNG (2026-11-14c)

### ① Nguồn từ bị hỏng ở 4 khóa (đo được)
`words_<iso>.json` lưu **10 từ** (Pháp) / 13.650 (Trung) / 21.850 (Anh) / 21.900 (Đức)
⇒ khóa Pháp chỉ có **2.560 từ khác nhau cho 2.520 ngày** (= 1 từ/ngày) ⇒ **không đạt
"0 → bản xứ"**. Nguyên nhân: lần fetch đầu dùng bản dịch lô cũ (mất 24/25 từ mỗi lô).
Đã fetch lại bằng bản dịch lô **đã sửa** (mã ngôn ngữ + tách theo dòng):
**en · zh · fr · ko · ru · es = 26.000 từ, 100 % có nghĩa tiếng Việt**.

### ② Khóa Hàn chỉ có 450 ngày ⇒ đã dựng lại lên 2.520 ngày
Trước: 450 ngày · 2.859 từ · 2,4 ngữ pháp/ngày. Sau: **2.520 ngày · 23.118 từ · 3,7 ngữ pháp/ngày**.

### ③ Dựng lại khóa mà KHÔNG mất ảnh/audio đã sinh
`build_offline_course.py` trước đây ghi đè `vocab` ⇒ mất `image_ref`/`audio_ref` ⇒ app mất
ảnh/âm thanh đã tải về (tốn hàng giờ TTS). Đã thêm: khi dựng lại, **giữ lại media ref của các
từ TRÙNG** (đo thật: Pháp giữ 1.071 · Trung 4.167 · Anh 6.467 · Đức 992).

### ④ Kết quả — 8 KHÓA ĐỒNG ĐỀU (đo thật)

| khóa học | ngày | từ khác nhau | câu/ngày | ngữ pháp/ngày |
|---|---|---|---|---|
| tiếng_nhật | 2.520 | 24.765 | 11,2 | 3,9 |
| tiếng_trung | 2.520 | 22.698 | 15,3 | 3,7 |
| tiếng_anh | 2.520 | 24.075 | 13,1 | 3,8 |
| tiếng_hàn_quốc | 2.520 | 23.118 | 15,3 | 3,7 |
| tiếng_nga | 2.520 | 23.805 | 14,5 | 3,7 |
| tiếng_pháp | 2.520 | 23.968 | 14,1 | 3,8 |
| tiếng_tây_ban_nha | 2.520 | 23.718 | 14,1 | 3,8 |
| tiếng_đức | 2.520 | 23.763 | 14,1 | 3,8 |

### ⑤ BUG MANIFEST NGHIÊM TRỌNG (làm mất TOÀN BỘ media)
`save_index()` ghi vào **tên file tmp CỐ ĐỊNH** `index.json.tmp` cho **mọi tiến trình** ⇒ khi
2 tiến trình ghi đồng thời: P1 mở file ở chế độ `"w"` (truncate) rồi ghi 86 MB, P2 cũng mở
file đó ở chế độ `"w"` ⇒ phần đuôi của JSON1 còn sót lại ⇒ `index.json` chứa **2 JSON nối liền**
⇒ `json.load` lỗi *"Extra data"* ⇒ `load_index()` **nuốt lỗi, trả index RỖNG** ⇒ **mọi khóa
báo "ảnh 0,0 %, audio 0,0 %"** (đo thật 14/11 22:11).

Đã sửa (3 phần):
1. `save_index` dùng **tên tmp DUY NHẤT theo PID + thread** ⇒ không process nào ghi đè của ai.
2. `load_index` khi JSON hỏng ⇒ **tự khôi phục**: thử `.tmp2` / `.bak_reindex` → nếu không được
   ⇒ `reindex()` dựng lại manifest từ toàn bộ file thật trên đĩa (đã phục hồi **169.560 entry**).
3. `tools/test_media_manifest.py` — test A: tên tmp duy nhất · B: manifest hỏng ⇒ tự phục hồi
   (không rỗng) · C: round-trip giữ entry · D: `reindex()` dựng lại từ đĩa.

### ⑥ Thêm 2 lỗi nhỏ khác
- `fill_media.py --lang` giờ là `action="append"` ⇒ `build_all_courses.py` truyền nhiều khóa
  thực sự bù được **tất cả** (trước argparse chỉ giữ giá trị CUỐI ⇒ chỉ bù 1 khóa).
- `build_all_courses.py` thêm **tiếng Nhật** (iso `ja`, dùng EDICT/JMdict — không cần fetch
  wordfreq) ⇒ 1 lệnh giờ phủ **đủ 8 khóa**.
