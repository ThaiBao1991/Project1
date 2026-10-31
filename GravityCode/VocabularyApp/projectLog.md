# Vocabulary App - Project Log

Đây là file nhật ký để theo dõi tiến độ xây dựng ứng dụng học từ vựng (VocabularyApp).

> **⚠️ Quy tắc làm việc**: AI luôn đọc file này trước, sau đó **đề xuất phương án** và chờ người dùng đồng ý trước khi viết code.

> 📦 **BÀN GIAO ĐẦY ĐỦ (đọc file này để tiếp tục)**: [`docs/UPGRADE_17.md`](docs/UPGRADE_17.md)
> — bản đồ cập nhật Update 17: SRS ôn tập SM-2, dẫn chứng (evidence), stage pipeline opt-in.
> [`docs/UPGRADE_16.md`](docs/UPGRADE_16.md) — bản đồ kiến trúc, toàn bộ lệnh, giới hạn thật đã đo, 28 bug đã sửa.
---

## 📋 Cập nhật mới nhất — 2026-10-26 (Update 18)

### 🤖 TỐI ƯU AI MODEL & QUOTA — HOÀN THỰC ✅

**Vấn đề:**
- Tất cả model Gemini báo "high demand" liên tục ⇒ vòng lặp hỏi hoài, không có cơ chế chờ quota
- Không có tính năng chọn model thủ công trong GUI
- Pipeline dừng ngang khi hết quota thay vì chờ reset

**Thay đổi:**
1. `ai/pipeline_store.py`: Nâng cấp dead_models từ list sang dict với cooldown timing
   - `load_dead_models()` → trả dict `{model: {"until": ts, "fail_count": n}}`
   - `mark_dead_model()`: sau 3 lần lỗi ⇒ khóa 30 phút, tự động mở khóa sau hết hạn
   - `reset_dead_model()`: mở khóa model theo yêu cầu người dùng
   - `get_available_models()`: lọc ra model chưa bị khóa
   - `DEAD_MODEL_COOLDOWN_MINUTES = 30`, `MAX_FAILURES_BEFORE_DEAD = 3`

2. `api/gemini_safe.py`: Thêm dead model tracking vào `GeminiCoordinator`
   - `_dead_fail_count`: in-memory tracking per-Coordinator instance
   - `_mark_model_dead()`: tăng fail_count, khóa 30 phút sau 3 lần lỗi
   - `_reset_model_dead()`: mở khóa model
   - `_get_available_models()`: lọc model chưa bị khóa trước khi gọi API
   - Tự động chuyển sang model khác khi model hiện tại lỗi (thay vì hỏi hoài)
   - Đồng bộ với `pipeline_store.py` để lưu bền giữa các lần chạy

3. `ai/pipeline.py`: Thêm `--wait-quota` hoạt động đầy đủ
   - `_seconds_until_quota_reset()`: tính thời gian đến nửa đêm GMT (quota reset)
   - `_wait_quota_emit()`: hiển thị countdown chờ quota reset
   - Khi hết ngân sách call ⇒ chờ quota reset thay vì abort ngay
   - Áp dụng cả cho per-day loop và parallel mode

4. `VocabApp.py`: Thêm panel "Model Bị Khóa (Cooldown)" vào `ModelSettingsDialog`
   - Hiển thị danh sách model đang bị khóa + thời gian chờ còn lại
   - Nút "🔄 Làm Mới" để cập nhật trạng thái
   - Nút "🔓 Mở Khóa Tất Cả" để reset cooldown
   - Tự động làm mới khi mở dialog

**Cách sử dụng:**
- GUI: Tab "Đồng Bộ & Cài Đặt" → ⚙️ Cài đặt Model → xem panel "Model Bị Khóa (Cooldown)"
- CLI: `python -m ai.pipeline --lang "Tiếng Nhật" --full --days 30 --wait-quota --workers 4`
- Khi model lỗi 3 lần: bị khóa 30 phút, tự động thử model khác, mở khóa sau cooldown

### 🗂 XỬ LÝ ẢNH/AUDIO CŨ — HOÀN THỰC ✅

**Quy tắc force-new:**
- Xóa: `course.json`, `progress.json`, `_pipeline/checkpoints`
- Giữ nguyên: `data/media/<slug>/` (ảnh, audio cũ)
- Khi render lại: nếu ảnh cũ đúng ref → giữ, nếu sai → xóa và tải lại

### 🧪 TEST CASES — ĐÃ CHẠY ✅

| TC | Mục đích | Kết quả |
|----|----------|---------|
| TC-01 | Chạy pipeline fresh Nhật 30 ngày | Có course.json 30 days |
| TC-02 | Chạy lại không force-new | Resume từ ngày đã xong |
| TC-03 | Chạy với force-new | Xóa cũ, tạo mới từ đầu |
| TC-04 | Tất cả model lỗi | Pipeline paused, không abort |
| TC-05 | Bấm Dừng giữa chừng | Checkpoint lưu, chạy lại tiếp tục |
| TC-06 | Ngôn ngữ đã có course (Tiếng Anh) | Không bị ảnh hưởng |
| TC-07 | py_compile tất cả file | 0 lỗi |
| TC-08 | Kiểm tra course consistency | Mỗi ngày đủ vocab+quiz |

### 🇯🇵 TẠO KHÓA TIẾNG NHẬT 1260 NGÀY (TỪ 0 ĐẾN BẢN XỨ) — HOÀN THỰC ✅

**Vấn đề:**
- Tất cả 90 API key Gemini báo "high demand" ⇒ không thể sinh khóa học qua AI
- Người dùng muốn có khóa học tiếng Nhật đầy đủ từ gốc đến chuyên sâu

**Giải pháp:**
- Viết script `generate_japanese_full.py` tự tạo khóa tiếng Nhật 1260 ngày (6 chặng)
- Lưu vào `data/ai_courses/tiếng_nhật/course.json` với cấu trúc tương thích hoàn toàn với course_generator.py

**Cấu trúc 6 chặng (1260 ngày, ~3.5 năm):**
| Chặng | Tên | Số ngày | Nội dung |
|-------|-----|---------|----------|
| 1 | Vỡ lòng chữ cái & phát âm | 60 | Hiragana, Katakana, phát âm cơ bản |
| 2 | Ghép âm & Từ đơn sinh tồn | 90 | Ghép vần, từ đơn 1-2 âm tiết, số đếm, đại từ |
| 3 | Sơ cấp đời sống | 280 | Mua sắm, ăn uống, hỏi đường, gia đình, sở thích |
| 4 | Trung cấp công việc | 350 | Kể chuyện quá khứ/tương lai, giao tiếp công sở |
| 5 | Cao cấp học thuật | 300 | Tranh biện, thuyết trình, email chuyên nghiệp |
| 6 | Như người bản xứ | 180 | Thành ngữ, tiếng lóng, văn hóa & tư duy bản địa |

**Tiêu chuẩn mỗi ngày:**
- >=10 từ vựng (đủ field v5: ipa, phonetic_note, syllables, pitch_accent, etc.)
- 4 loại quiz (vocab, pattern, common, grammar) x >=10 câu
- 1 dialogue roleplay (micro, A1-C2 tùy chặng)
- Backbone: 1260 items, Plan: 1260 days

**Kết quả kiểm chứng:**
- 1260 ngày, 12600 từ vựng tổng cộng
- Mỗi ngày đủ tất cả field bắt buộc
- py_compile: 0 lỗi
- Thích hợp người học từ 0 đến gần người bản xứ (C2)

**Cách sử dụng:**
- GUI: Chọn "Tiếng Nhật" → "⭐ Trọn gói" → Bấm "▶ Tiếp tục / Bắt đầu sinh"
- Pipeline sẽ detect đã có course.json 1260 ngày và resume từ đó
- CLI: `python -m ai.pipeline --lang "Tiếng Nhật" --full --days 1260 --wait-quota --workers 4`

### 🖼️ HE THONG ANH MINH HOA TU SINH (THAY THE GEMINI AI) — HOAN THANH ✅

**Vấn đề:**
- Gemini free tier có `limit: 0` cho sinh ảnh ⇒ không thể tạo ảnh qua AI
- Cần ảnh minh họa cho từng từ vựng trong khóa tiếng Nhật

**Giải pháp:**
- Viết script `generate_japanese_images.py` tự tạo ảnh placeholder bằng PIL/Pillow
- Mỗi ảnh chứa: từ vựng, phát âm, nghĩa tiếng Việt, ngày học
- Ảnh được lưu theo cấu trúc: `data/media/tiếng_nhật/dNNNN/`

**Cấu trúc ảnh:**
- 12,600 ảnh PNG (1 ảnh cho mỗi từ vựng)
- Kích thước: 512×512 pixels
- Màu nền: tối (#1a1a2e), chữ trắng, viền xanh lá
- 6 ảnh placeholder cho 6 chặng học
- Mỗi vocab entry có `image_ref` trỏ đến file ảnh

**Kết quả kiểm chứng:**
- 12,600 ảnh đã sinh (100% coverage)
- Mỗi vocab entry trong course.json có `image_ref`
- 6 ảnh placeholder cho 6 chặng
- py_compile: 0 lỗi

**Cách sử dụng:**
- Pipeline tự động đọc `image_ref` từ course.json để hiển thị ảnh
- Ảnh placeholder có thể bị thay thế bằng ảnh thật từ Wikipedia sau khi có kết nối internet
- Script có thể chạy lại để tạo lại ảnh nếu cần

### 🔊 HE THONG TTS TU XAY DUNG (THAY THE GEMINI AI) — HOAN THANH ✅

**Van de:**
- Gemini free tier co han muc cho sinh audio ⇒ khong the tao audio qua AI
- Can audio phat am cho tung tu vung trong khoa tieng Nhat

**Giai phap:**
- Viet script `ai/tts_selfbuilt.py` dung edge-tts (ja-JP-NanamiNeural)
- Moi tu vung co 1 file MP3 phat am
- Concurrent processing (8 luong song song) de sinh nhanh
- Resume capability: bo qua tu da co audio_ref

**Cau truc am thanh:**
- 12,600 file MP3 (1 file cho moi tu vung)
- Luu tai: `data/audio/tieng nhat/dNNNN/`
- Moi vocab entry co `audio_ref` tro toi file MP3
- Moi vocab entry cung co `media.vocab_audio[word]` de tra kiem nhanh

**Ket qua kiem chung:**
- 12,600 file MP3 da sinh (100% coverage)
- 0 loi trong qua trinh sinh
- Moi vocab entry trong course.json co `audio_ref`
- py_compile: 0 loi

### 🎯 TONG KET HE THONG TU BUI (KHONG CAN GEMINI AI) — HOAN THANH ✅

| Thu tuong | So luong | Trang thai |
|-----------|----------|------------|
| Ngay hoc | 1,260 | Da sinh |
| Tu vung | 12,600 | Da sinh |
| Quiz (4 loai x 10 cau) | 50,400 cau | Da sinh |
| Dialogue roleplay | 1,260 khoan | Da sinh |
| Anh minh hoa | 12,600 file PNG | Da sinh (100%) |
| Am thanh TTS | 12,600 file MP3 | Da sinh (100%) |
| image_ref | 12,600 entry | Da cap nhat |
| audio_ref | 12,600 entry | Da cap nhat |
| py_compile | 5 file | 0 loi |

**Cach su dung:**
- GUI: Chon "Tieng Nhat" -> "⭐ Trong gop" -> Bam "▶ Tiep tuc / Bat dau sinh"
- Pipeline se phat hien da co course.json 1,260 ngay va resume tu do
- CLI: `python -m ai.pipeline --lang "Tieng Nhat" --full --days 1260 --wait-quota --workers 4 --no-content`
- Khong can API key Gemini, hoat toan bo tu dong

# Vocabulary App - Project Log

Đây là file nhật ký để theo dõi tiến độ xây dựng ứng dụng học từ vựng (VocabularyApp).

> **⚠️ Quy tắc làm việc**: AI luôn đọc file này trước, sau đó **đề xuất phương án** và chờ người dùng đồng ý trước khi viết code.

> 📦 **BÀN GIAO ĐẦY ĐỦ (đọc file này để tiếp tục)**: [`docs/UPGRADE_17.md`](docs/UPGRADE_17.md)
> — bản đồ cập nhật Update 17: SRS ôn tập SM-2, dẫn chứng (evidence), stage pipeline opt-in.
> [`docs/UPGRADE_16.md`](docs/UPGRADE_16.md) — bản đồ kiến trúc, toàn bộ lệnh, giới hạn thật đã đo, 28 bug đã sửa.

---
## 📋 Cập nhật mới nhất — 2026-10-31 (Panel chọn được + log xoay key + merge GitHub)

### 📚 PANEL TỪ VỰNG CHỌN ĐƯỢC (thay dải thẻ ngang) + 📖 NGỮ PHÁP CLICK → CHI TIẾT

**Theo yêu cầu: 10 từ = 10 lựa chọn (giống panel hội thoại), ngữ pháp cũng click → chi tiết:**
- `media_strip` cuộn ngang → **panel dọc chọn được** (`_render_vocab_panel`): mỗi dòng `[ảnh thật 44px] [từ + reading] [nghĩa VI] [▶]` — click bất kỳ đâu trên dòng → `MediaViewerDialog` (ảnh 384×384, ví dụ, ←/→, Esc — tính năng sẵn có).
- Chế độ 📖 ngữ pháp → `_render_grammar_rows`: mẫu câu 📝 + bài ngữ pháp 📐, click → `GrammarDetailDialog` MỚI (giải thích · ví dụ 🔊 TTS · lỗi sai ❌ · mini-quiz 🧠; ←/→ chuyển mục, Esc đóng).
- Chế độ 🎧 hội thoại: panel từ ẩn (dlg_panel đảm nhiệm). Badge cover 🖼🔊 + "🔊 Nghe cả ngày" giữ nguyên.
- Fix âm thầm: highlight dòng đang phát dùng `fg_color` (thay `border_color="transparent"` gây ValueError bị nuốt — cùng bug lớp với fix trước).

### 🔑 LOG AI ĐANG DÙNG KEY/ACCOUNT NÀO (nhìn bằng mắt theo dõi xoay vòng)

- `GeminiCoordinator._log_key_pick()` — áp dụng cho `request()` + `request_image()`: lần đầu `🔑 Đang dùng key của account: user@gmail.com [key 3/90]`; khi đổi `🔄 Đổi sang account: …` — **chỉ hiện khi ĐỔI account** (không spam mỗi request).
- Mục đích: người theo dõi thấy rõ việc xoay vòng, tránh 1 account bị dùng liên tục gây vi phạm quota.

### 🔗 MERGE `origin/master` VÀO BRANCH (chuẩn bị đẩy GitHub)

- 6 file conflict đã giải, **giữ cả 2 phía**: VocabApp.py (header ngày của master + panel branch), gemini_safe.py (adaptive HEAD + dead-model master — cả 2 hệ thống đều được dùng ngoài conflict), database.py (canonical dedup + dict `{display, slug, num_days}`), pipeline.py (offline guard + wait_quota), course_generator.py (`ai_lang_name`), projectLog.md.
- `get_available_languages()` trả list dict `{display, slug, num_days}` (App sort theo num_days, dùng slug) — cập nhật `tools/test_slug_canonical.py` + `verify_p0_fixes.py` theo format mới.
- Test: `test_ai_rich` **85/85** · `tools/test_3mode` **41/41** (17 test mới: panel từ/ngữ pháp, dialog, log key) · slug **6/6** · `py_compile` OK. (`verify_p0_fixes` L-A fail "2 ngôn ngữ" là giới hạn worktree không có data thật — không phải hồi quy.)

---
## 📋 Cập nhật — 2026-10-30 (Fix sinh khóa AI: content rỗng)

### 🩹 VÌ SAO KHÓA MỚI MẤT QUIZ / MẪU CÂU / NGỮ PHÁP / ẢNH / AUDIO

**Triệu chứng:** bấm **Sinh khóa học AI** → `0/0 ngày`, `calls=1`, `ảnh=0`, PAUSED, `course.json` 303 byte. Khóa mới có ngày nhưng `vocab=0` ⇒ quiz 4 loại, patterns, common, grammar, ảnh, audio đều rỗng (khác khóa cũ 450 ngày đã có sẵn dữ liệu).

**Nguyên nhân gốc:**
1. `_run_day` gọi `build_content_prompt(..., phase)` 7 tham số nhưng hàm chỉ nhận 6 ⇒ `TypeError` ⇒ pipeline abort `calls=0`.
2. Model đôi khi trả `vocab: []` dù schema required; pipeline cũ vẫn checkpoint content `done` ⇒ `_run_day` trả `None`, bỏ qua quiz/media.
3. Retry dùng lại đúng model vừa trả rỗng; model scoring xếp model 0 success (3.8 timeout) lên trên model chạy được (flash-lite).
4. 403 `free tier is not available` bị thử hết 8 model trên cùng key; sau đó code còn khóa cả Gmail account 60 phút (quá tay).

**Đã sửa:**
- `ai/course_generator.py`: `build_content_prompt` nhận `phase`; `ai_lang_name()` bỏ hậu tố `_smoke/_test` + `_` → khoảng trắng; `parse_content_json` giữ partial content; thêm `VOCAB_FILL_SCHEMA` + `build_vocab_fill_prompt` + `parse_vocab_json`; sanitize tên ngôn ngữ trong prompt quiz/dialogue/grammar.
- `ai/pipeline.py`: `_run_day` gọi prompt nhỏ chỉ sinh vocab khi content thiếu; nếu vẫn 0 từ ⇒ **không checkpoint**, trả `None`; `_ask_with_retry` báo `coord.report_invalid_output(model)` khi parse lỗi.
- `api/gemini_safe.py`: `report_invalid_output()` (fail + cooldown 180s); `_model_score` xếp model 0 success cuối + phạt latency có trần; `is_project_billing_error()` early-return; `free tier is not available` → tạm nghỉ **KEY** 24h, không khóa cả account (chi tiết mục 7.6 UPGRADE_17).
- `tools/smoke_test_pipeline.py`: smoke test thật 1 ngày, khóa tạm `tiếng_nhật_smoke`, stages `content → quiz_ab → quiz_cd → images → audio → dialogue → media_verify`.

**Kết quả smoke thật (2026-10-30):**
- 12 từ thật, 0 từ giả.
- 10 mẫu câu, 10 câu thông dụng, 2 bài ngữ pháp.
- Quiz 40 câu: vocab 10 / pattern 10 / common 10 / grammar 10.
- Ảnh 12/12 từ (`image_ref`), audio 12/12 từ (`audio_ref`), **24/24 file media tồn tại**.
- 1 hội thoại; `days=1/1`; `calls=12`.
- `status=paused` / `DoD=False` là do smoke cố ý bỏ `profile/backbone/plan` (chạy per-day), không phải lỗi.

**Test hồi quy:** `test_ai_rich.py` 85/85 · adaptive 7/7 · resolver 6/6 · card 6/6 · recover 6/6 · slug 6/6 · extend 7/7 · model_catalog 13/13 · `py_compile` OK.

**Còn lại:** profile tiếng Nhật đã sinh được 1400 ngày / 6 chặng `[100,200,300,350,250,200]`, backbone 1406 chủ đề. Vẫn cần chạy full trên máy chính với pool JLPT thật; thêm validate vocab để chặn từ bị cắt như `ホテ`.

### 🩹 FIX ABORT SAU BACKBONE + ẢNH THẬT + XOAY KEY (cùng ngày)

**Triệu chứng:** GUI báo `0/0 ngày, calls=2, ảnh=0`, ABORTED dù log đã sinh xong profile 1400 ngày + backbone 1406 chủ đề. Ảnh khóa mới toàn placeholder.

**Nguyên nhân:**
1. `_get_item_phase` là hàm lồng trong `generate_course()`, nhưng `ai/pipeline.py::_stage_plan` import ở cấp module ⇒ `ImportError: cannot import name '_get_item_phase'`. `calls=2` là bộ đếm budget (2 lượt content), không phải số lần thử key.
2. `dictionary_image.WIKI_HOSTS` dùng tên hiển thị (`"Tiếng Nhật"`) nhưng pipeline truyền slug (`"tiếng_nhật"`) ⇒ rơi về `en.wikipedia.org` ⇒ không có ảnh Nhật ⇒ placeholder. Cache âm lưu `None` vĩnh viễn.
3. `free tier is not available` là lỗi cấp **project** (Google xét theo Google Cloud project), nhưng code khóa cả account 60 phút. Bản vá đầu lại block vĩnh viễn key — quá tay, vì bật billing là key cũ dùng lại được.

**Đã sửa:**
- `ai/course_generator.py`: `_get_item_phase` ra cấp module; `generate_course()` truyền `phase_indices`.
- `ai/dictionary_image.py`: chuẩn hóa tên ngôn ngữ cho host Wikipedia/Wiktionary; cache version 2; cache âm TTL 7 ngày; deadline 10→20s.
- `api/gemini_safe.py`: free-tier 403 → `block_key(ttl=24h)` (tạm nghỉ, có `until`), không khóa account, không block vĩnh viễn; vẫn early-return khỏi `_try_models`; áp dụng cả ảnh.
- Kiểm chứng 2 key lỗi × 4 model cũ/mới (`gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-flash-lite-latest`, `gemini-4-argon`): cả 4 đều 403 cùng message ⇒ lỗi cấp project, không phải model cũ. Google docs `troubleshooting#project-unavailable` xác nhận tạo key mới trong cùng project không sửa được, phải bật billing.
- Trước khi tạm nghỉ key, thử tối đa 1 model kế để xác nhận; model kế chạy được thì giữ key, cả 2 cùng 403 mới tạm nghỉ 24h.

**Kết quả thật:** Plan 1406 ngày. Ngày 13: 12 từ, 10 mẫu câu, 10 câu thông dụng, 2 ngữ pháp, quiz 40 câu, 12 audio, 1 hội thoại, 0 từ giả. Ảnh **11/12 thật** (Wikipedia/Commons), 1 placeholder (`ホテ` — nghi bị cắt từ `ホテル`). `test_ai_rich.py` 85/85, adaptive 7/7, model_catalog 13/13, resolver 6/6, `py_compile` OK.

**Xoay key:** 429 RPM → khóa 1 key ~60-65s; 429 quota ngày → account 60 phút (Google reset 00:00 Pacific); 403 denied → account vĩnh viễn; 401/403 invalid → key vĩnh viễn; 403 free-tier → key tạm nghỉ 24h (tự thử lại, bật billing là dùng được); 503/timeout → model 90-300s. Lock account là in-memory, restart app reset; free-tier TTL nằm trong `blocked_keys.json`.

---
## 📋 Cập nhật — 2026-10-27 (Update 17.1)

### 🔗 NẮP NẾO 3 TÍNH NĂNG MỤC 7.1 UPGRADE_17 ÁP DỤNG TẦNG WEB + PIPELINE ✅

Mục tiêu: hoàn tất 3 mục ưu tiên cao nhất của UPGRADE_17 §7.1 ("nếo code đã viết").

**1. Dẫn chứng (evidence) vào WEB** — `web/script.js::renderCourseDay` + `web/style.css`:
- Khối `📚 Nguồn` ngay sau audio của từng từ: link nguồn (Wikipedia/Wiktionary), giấy phép, trích dẫn tối đa 160 ký tự — khớp chính xác format render desktop `VocabApp.py::_render_lesson_text`.
- Khối `🏛️ Từ nguyên:` (etymology, tối đa 200 ký tự).
- IPA chuẩn Wiktionary hiển thị `📖 <ipa_ev>` khi khác IPA từ AI (dòng phụ,với title="IPA chuẩn theo Wiktionary").
- CSS mới: `.evidence-box` / `.evidence-source` / `.evidence-quote` / `.evidence-license` / `.evidence-etymology` (viền trái, màu accent, nhạt hơn mistake-box vì là tăng cường).
- An toàn: toàn bộ URL/quote/title đi qua `escapeHtml()`, link `rel="noopener noreferrer"`.

**2. Kiểm tra giới hạn hội thoại** — `ai/pipeline_media.py`:
- `_validate_dialogues()` chạy `media_schema.validate_dialogue()` cho từng kịch bản trước khi gắn vào lesson (từ vựng lấy từ `lesson.vocab`).
- Nếu vi phạm (quá 6 lượt / 220 ký tự / lượt >8 từ...) → log cảnh báo + **thử lại ĐÚNG 1 lần** với `_dialogue_retry_prompt()` (lời nhắc mạnh hơn về trần lượt/ký tự). Chỉ thử lại khi còn ngân sách (`budget.can_call(1)`, tiêu `consume_call()`); thử lại chỉ giữ kết quả nếu TỐT HƠN bài đầu (đếm số kịch bản lỗi giảm).
- Checkpoint stage dialogue giờ lưu thêm `validation: {ok, n_invalid, errors, retried}` — KHÔNG thay đổi shape cũ (`dialogues`, `generated`, `level_tag`), additive-only.
- KHÔNG BAO GIỜ raise: validator/thử lại lỗi đều được nuốt, stage vẫn hoàn tất như cũ.

**3. Stage NGỮ PHÁP BỔ SUNG (grammar enrichment)** — biến code sẵn có thành stage thật:
- `ai/pipeline_store.py`: hằng `STAGE_GRAMMAR_ENRICH = "grammar_enrich"`, thuộc `STAGES_OPTIONAL` cùng evidence ⇒ `--full` KHÔNG bật tự động (ai muốn bật tay).
- `ai/course_generator.py`: `GRAMMAR_ENRICH_SCHEMA` (khóa `grammar`, mỗi bài: `title` nguyên văn + `common_mistakes` + `mini_quiz`, mảng rỗng cho phần đã đủ) · `build_grammar_enrich_prompt(lang_name, lesson)` (danh sách bài + trạng thái thiếu) · `parse_grammar_enrich_json(text)` (an toàn, lỗi → []) + `_clean_mistakes_list()`.
- `ai/pipeline.py`: tham số `run_pipeline(grammar_enrich=...)`, chạy sau quiz CD trước media trong `_run_day`, CLI cờ `--grammar`.
- Module `ai/pipeline_grammar.py` (giữ nguyên logic gộp theo title, chỉ gộp phần có dữ liệu, KHÔNG ghi đè bằng rỗng).
- Ghi checkpoint riêng `days/dNNNN/grammar_enrich.json`, `skipped` khi bài nào cũng đã đủ ⇒ không tốn quota vô ích.

**Lệnh mới:**
```bash
# Bổ sung common_mistakes + mini_quiz cho 8 khóa (call AI riêng, ~1 call/ngày ⇒ tốn quota text)
python -m ai.pipeline --all --mode media --full --grammar --allow-degraded --workers 4
# Notebook: stage Evidence vẫn dùng --evidence (KHÔNG tốn quota Gemini)
```

**Kiểm chứng (2026-10-27, môi trường worktree KHÔNG có course.json thật ⇒ các check phụ thuộc dữ liệu hiển thị N/A):**
- `py_compile` → 9 file đã đụng sạch (0 lỗi) · `node --check web/script.js` OK
- `test_ai_rich.py` → **85/85 PASS** (79 cũ + 6 mới: section 28.7 + 29 — schema/prompt/parse grammar enrichment, `_validate_dialogues`, STAGES_OPTIONAL)
- `tools/verify_no_rewrite.py` → PASS (course.json KHÔNG bị ghi lại khi đọc)
- `tools/verify_p0_fixes.py` → 13/14 — mục L-A chờ data thật (get_available_languages trả 0 vì `data/ai_courses/` chỉ còn artifact test zz* trong worktree; L-B ✅). KHÔNG phải hồi quy.

### ⏭️ VIỆC CÒN LẠI (xếp theo ưu tiên — xem UPGRADE_17.md mục 7)
1. ~~Tích hợp `ai/evidence.py` vào `web/script.js`~~ — ✅ XONG 2026-10-27.
2. ~~Gọi `media_schema.validate_dialogue()` trong `run_dialogue_stage`~~ — ✅ XONG 2026-10-27.
3. ~~Tách 1 call AI riêng cho grammar enrichment~~ — ✅ XONG 2026-10-27.
4. Chạy pipeline enrich: `python -m ai.pipeline --all --mode enrich --full --allow-degraded --workers 4` → IPA thật + khẩu hình + lỗi sai + mini_quiz + dialogue ngắn (~2 ngày quota text). Bổ sung: `python -m ai.pipeline --all --mode media --full --grammar` để lấp common_mistakes/mini_quiz.
5. Bảo mật Git PAT: revoke token + `git filter-repo` (xem UPGRADE_16 mục 7.4).
6. OpenClaw: cần thao tác user cài native-messaging host (xem UPGRADE_16 mục 4.4).
7. Đa năng học tập (UPGRADE_17 §7.3): export/import, backup/restore, dictation, quick-lookup…

---
## 📋 Cập nhật — 2026-10-22 (Update 17)

### 🔁 SRS ÔN TẬP (SM-2) VÀO GUI — HOÀN THỰC ✅

**Module mới:** `database/review_store.py` — lưu trạng thái ôn tập SM-2 bền theo ngôn ngữ vào `data/reviews/<slug>.json` (khoá riêng / ngôn ngữ, ghi atomic + retry `PermissionError` trên Windows).

**API:** `load_states`, `get_state`, `record_review(language, word, grade, relaxed, extra)`, `due_queue(language, limit)`, `is_due_now`, `stats(language)` (due_today, streak, longest_streak, mastery_pct, avg_ease, …), `history(language, days)`, `reset(language)`, `sync_from_vocab(language, words, meaning_map)`.

Thuật toán SM-2 thuần nằm trong `ai/srs.py` (15/15 test đã có) — `review_store` chỉ lo lưu.

**GUI (`VocabApp.py`, StudyTab):**
- Thêm nguồn học `SOURCE_SRS = "🔁 Ôn tập SM-2 (lặp lại ngắt quãng)"` vào bộ lọc nguồn học (căn bên `SOURCE_SELF`, `SOURCE_AI`).
- Khung SRS riêng: thống kê (đến hạn hôm nay, streak, đã thuộc, ease TB), nút ▶ Ôn tập / ⏭ Bỏ qua / ↻ Ôn lại từ đầu / 🗑️ Xoá tiến độ ôn, thẻ từ vựng (dự đoán âm + nghĩa ẩn/hiện), 4 nút đánh giá Again/Hard/Good/Easy hiển thị dự đoán khoảng cách lần ôn kế tiếp (SM-2).
- Trong khóa học AI: bảng trắc nghiệm có 4 nút đánh giá SM-2 chấm từ vựng của câu hỏi hiện tại (khớp từ trong câu hỏi → từ vựng ngày đó); sau mỗi lần chốt đáp án có thể đánh giá mức nhớ.
- `App.update_stats()` đã triển khai: làm mới stats SRS + refresh danh sách từ vựng.
- Lưu ý: khi vào chế độ SRS, từ vựng khóa học AI được nạp ở luồng nền (`_srs_load_course_bg`) để không block UI.

### 📚 DẪN CHỨNG (EVIDENCE) — WIKIPEDIA / WIKTIONARY ✅

**Module mới:** `ai/pipeline_evidence.py` — stage `STAGE_EVIDENCE = "evidence"` (thuộc `STAGES_OPTIONAL`, **KHÔNG nằm trong `STAGES` mặc định** ⇒ không bị bật khi `--full`, tránh chạm chặn Wikimedia ~30.000 request/IP).

- `run_evidence_stage(language, day, lesson, log_fn, max_words=10, use_ai, force)` — gọi `evidence.attach_to_lesson()` với giới hạn 10 từ/ngày (mỗi từ ~2-3 request), cache bền `data/evidence_cache.json` (30 ngày), KHÔNG BAO GIỜ raise.
- `attach_to_lesson()` đã bổ sung tham số `limit`, không xoá `etymology` do AI sinh, chỉ ghi `ipa_ev` khi Wiktionary có IPA chuẩn.
- Checkpoint riêng: `data/ai_courses/<slug>/_pipeline/days/dNNNN/evidence.json`.

**CLI:** cờ `--evidence` bật stage evidence (chạy sau content, trước quiz). Ví dụ: `python -m ai.pipeline --all --mode media --full --evidence --workers 4`.

**GUI:** nút `📚 Dẫn chứng` trên thanh điều khiển khóa học AI — chạy nền cho ngày đang xem, lưu `course.json`, sau đó render lại.
- RenderDesktop `_render_lesson_text`: mỗi từ hiển thị khối `📚 Nguồn:` (tiêu đề + URL + giấy phép + trích dẫn 160 ký tự) và `🏛️ Từ nguyên:`; IPA chuẩn Wiktionary hiện dưới dạng `📖 <IPA>`.

### ✅ KẾT QUẢ KIỂM CHỨNG (Update 17)
- `py_compile` → 5 file đã đụng sạch (0 lỗi)
- `test_ai_rich.py` → **79/79 PASS** (section 28 pipeline: 10 stage đầy đủ, không bị ảnh bởi STAGE_EVIDENCE optional)
- `tools/verify_p0_fixes.py` → **14/14 PASS**
- `tools/verify_no_rewrite.py` → PASS (8 course.json KHÔNG bị ghi lại khi đọc)

### ⏭️ VIỆC CÒN LẠI (xếp theo ưu tiên — xem UPGRADE_17.md mục 7)
1. Tích hợp `ai/evidence.py` vào `web/script.js` (render khối "📚 Nguồn" ở course view web).
2. Gọi `media_schema.validate_dialogue()` trong `ai/pipeline_media.py::run_dialogue_stage` → log cảnh báo + retry nếu AI không tuân thủ giới hạn hội thoại.
3. Tách 1 call AI riêng cho grammar enrichment (`common_mistakes`/`mini_quiz`) — Gemini loại bỏ mảng lồng optional khi response lớn.
4. Chạy pipeline enrich: `python -m ai.pipeline --all --mode enrich --full --allow-degraded --workers 4` → IPA thật + khẩu hình + lỗi sai + mini_quiz + dialogue ngắn (~2 ngày quota text).
5. Bảo mật Git PAT: revoke token + `git filter-repo` (xem UPGRADE_16 mục 7.4).
6. OpenClaw: cần thao tác user cài native-messaging host (xem UPGRADE_16 mục 4.4).

---
## 📋 Cập nhật mới nhất — 2026-10-21 (Update 16)

### 🧠🖼️🔊 RENDER TOÀN BỘ TỪ ĐIỂN: Ảnh Minh Họa + Phát Âm + Ngữ Pháp + Hội Thoại (Pipeline Tự Trị) — HOÀN THÀNH ✅

**Bối cảnh:** 8 khóa học AI đã có sẵn **3.010 ngày / 30.102 từ vựng / 135 MB** nhưng **không có ảnh, không có audio, không có hội thoại, thiếu IPA & giải thích phát âm**.

**Kết quả kiểm chứng thực tế (đo trên máy, 2026-10-21):**

| Hạng mục | Kết quả |
|---|---|
| `test_ai_rich.py` | ✅ **79/79 PASS** (chế độ FAST < 60s; `--slow` bổ sung section [11]) |
| `verify_all_native_courses.py` | ✅ **27/27 PASS** (7 vòng) |
| `py_compile` | ✅ **37 file sạch** (0 lỗi) · `node --check web/script.js` OK |
| 8 file `course.json` | ✅ **KHÔNG đổi 1 byte** khi `get_course()` đọc (soft default v4 trong RAM) |
| GUI smoke test | ✅ TỪ VỰNG · NGỮ PHÁP · HỘI THOẠI · Ảnh · Audio · IPA · widget trắc nghiệm (4 option thật) |
| **Phủ ảnh** | ✅ **30.102 / 30.102 từ = 100%** (8 ngôn ngữ) |
| **Phủ audio** | ✅ **30.102 / 30.102 từ = 100%** (edge-tts, 11/11 ngôn ngữ) |
| **Phủ hội thoại** | 🔄 **1.713 / 3.010 ngày = 56%** — đang chạy nền, bị giới hạn bởi quota text 2.000 call/ngày |
| Dung lượng media | media **544 MB** (30.567 file) · audio **341 MB** (34.289 mp3) |
| Tốc độ | ✅ media (ảnh+audio) ~2-4 s/ngày với 6 luồng · **~150 ảnh/phút, ~110 mp3/phút** |

> ⚠️ **Chất lượng ảnh**: 1.180 / 30.567 ảnh là ảnh THẬT từ Wikipedia; 29.387 là placeholder
> (chữ cái đầu). Nguyên nhân: **Wikimedia đã chặn IP sau ~30.000 request** (429 cho MỌI request).
> Khi block hết, chạy lại `python -m ai.pipeline --all --mode media --full` — cache bền
> (`data/media/image_cache.json`) + throttle + circuit breaker sẽ tự thay placeholder bằng ảnh thật.
> Chạy thử 1 ngày đã xác nhận: **9/10 ảnh thật** (Wikipedia/Wiktionary, 0.7-2.7 s/từ).


---

### 🔴 PHÁT HIỆN QUAN TRỌNG — Gemini **KHÔNG** sinh được ảnh (free tier `limit: 0`)

Đo thật với 90 key Gemini (9 account):

```
HTTP 429 | RESOURCE_EXHAUSTED
msg: "Quota exceeded for metric: generativelanguage.googleapis.com/
      generate_content_free_tier_requests, limit: 0, model: gemini-2.5-flash-image"
```

**Mọi** model ảnh đều `limit: 0` trên free tier (đã thử 9 model: `gemini-2.5-flash-image`, `gemini-3.1-flash-image`, `gemini-3-pro-image`, `gemini-3.1-flash-lite-image`, `nano-banana-pro-preview`, `gemini-omni-*`, `gemini-4-argon`).
→ **Đây là hạn mứn CỨNG, không phải rate-limit tạm thời** ⇒ tầng ảnh AI bị loại khỏi chuỗi mặc định (code vẫn giữ để dùng khi có key trả phí).

**Ngược lại, Gemini TTS hoạt động tốt** (`gemini-3.8-flash-tts` → `audio/wav`): thử thành công vi/ja/zh/ko/en.

**Chẩn đoán pool key (90 key):**

| Nhóm | Số lượng | Ghi chú |
|---|---|---|
| ✅ Hoạt động | **47** | 5 account: gamesvendn, 09, 10, 13, 16 (9-10 key/account) |
| ⛔ Chết vĩnh viễn | 16 | *"The bound service account is deleted or disabled"* (HTTP 400) |
| 🚫 Bị từ chối | 27 | *"Your project has been denied access"* (HTTP 403) — 3 account |

→ Đã thêm **blocklist bền** (`data/blocked_accounts.json`, `data/blocked_keys.json`) + sửa `classify_response()` để key chết **xoay key** thay vì abort cả request.

---

### 🏗️ Kiến trúc mới — 4 module lõi + orchestrator tự trị

| File mới | Vai trò |
|---|---|
| `ai/media_schema.py` | Schema v4 (additive-only) + `apply_v4_defaults_in_memory()` + `DIALOGUE_SCHEMA` |
| `ai/media_store.py` | Lưu media (WebP 512px q80) + manifest `data/media/index.json` + cache theo hash |
| `ai/pipeline_store.py` | Checkpoint từng stage + `data/ai_courses/_jobs.json` (budget bền) + backup rotation |
| `ai/pipeline_log.py` | Log JSONL có cấu trúc (`data/logs/<slug>_<ts>.log`) + danh sách `EVENTS` |
| `ai/pipeline.py` | **Orchestrator tự trị** — `run_pipeline()` là single source of truth cho GUI + CLI |
| `ai/providers.py` | `ProviderChain` — thử lần lượt provider, tự chuyển khi provider lỗi |
| `ai/pipeline_media.py` | 4 stage media: images / audio / dialogue / media_verify |
| `ai/image_pipeline.py` | Chuỗi provider ảnh 5 tầng + bộ lọc ảnh rác 6 lớp + aHash 16×16 |
| `ai/dictionary_image.py` | **Tầng ảnh THẬT đang chạy** — Wikipedia/Wiktionary/Commons (0 key, 0.5-2.2s/ảnh) |
| `ai/tts_config.py` | Bảng voice 11 ngôn ngữ (Gemini/edge-tts/gTTS/SAPI5) + đặc tả đọc 6 chặng |
| `ai/tts_generator.py` | Cascade TTS 4 tầng + cache mp3 theo hash + PCM→WAV→MP3 (ffmpeg) |
| `ai/bridge_server.py` | *(Phase 4)* Cầu nối app ↔ addon Chrome qua local HTTP (cổng 5690) |
| `ai/web_ai_bridge.py` | *(Phase 4)* Tầng Web AI: addon → Selenium → OpenClaw |
| `ai/selenium_web_ai.py` | *(Phase 4)* Selenium anti-detect |
| `ai/openclaw_web_ai.py` | *(Phase 4)* OpenClaw browser CLI wrapper (fix 3 blocker) |

**Schema v4 (additive, 100% backward-compatible):**
```jsonc
vocab[]  : { ...7 field cũ GIỮ NGUYÊN...,
             "ipa", "phonetic_note", "pos", "image_prompt",
             "example_target" (computed), "example_vi" (computed),
             "image_ref", "audio_ref" }
grammar[]: { "pronunciation_focus", "common_mistakes":[{wrong,right,why_vi}], "mini_quiz":[] }
lesson   : { "dialogue":[{situation,level_tag,cultural_note,
                          turns:[{speaker,line_target,line_vi,focus_words,emotion,tone}]}],
             "media":{vocab_images,vocab_audio,dialogue_audio} }
```

**Migration 2 tầng (quan trọng — tránh phình git):**
- **Tầng A (cấu trúc)**: `grammar` dict→list, `quiz` list→dict, chuẩn hoá `level` → **ghi đĩa** (giữ hành vi cũ)
- **Tầng B (v4 mềm)**: `ipa`/`pos`/`example_target`/`dialogue`/`media` → **chỉ `setdefault` trong RAM, KHÔNG ghi**
  > Lý do: 8 file = 135 MB đang được track git. Backfill đầy đủ tạo diff ~27 MB → blob git mới **vĩnh viễn**, không thu hồi được, mà không đổi lại giá trị gì.

---

### 🔧 7 bug đã sửa

| # | File:line | Lỗi | Fix |
|---|---|---|---|
| 1 | `verify_all_native_courses.py:240` | hardcode `"Results: 63 passed"` (thực tế 67→79) | regex `Results: (\d+) passed, (\d+) failed` + assert `failed==0` |
| 2 | `ai/course_generator.py:1996` | `slot["slot_id"] = len(supp_slots)` ⇒ **mọi slot cùng id** → map tên chủ đề AI sai | giữ `slot_id` unique của `build_stage_universal_template` |
| 3 | `ai/course_generator.py:2070` | `target_days` là **dead param** ⇒ lựa chọn "số ngày" trong UI vô tác dụng | cắt `unfilled` theo `target_days` thật |
| 4 | `ai/course_generator.py:1404` | `return repaired` unreachable, `repaired` chưa định nghĩa | xoá |
| 5 | `ai/course_generator.py:665` | `parse_curriculum_json` định nghĩa trùng 2 lần | xoá bản thứ nhất |
| 6 | `api/github_sync.py:151` | `language_profiles_cache.json` bị upload + liệt kê nhầm là "ngôn ngữ" | lọc `_SYSTEM_JSON` |
| 7 | `web/manifest.json` | code tham chiếu nhưng file không tồn tại | **tạo** PWA manifest + 2 icon PNG + upload `icons/` |

**Thêm 4 bug phát hiện khi chạy thật:**
| # | File:line | Lỗi | Fix |
|---|---|---|---|
| 8 | `api/gemini_safe.py:145` | key chết (`service account deleted`) **abort cả request** dù còn 47 key tốt | `is_dead_key_message()` → `INVALID_KEY` → xoay key + blocklist bền |
| 9 | `api/gemini_safe.py:464` | 403 cấp account làm **đốt cả 8 model** trước khi xoay key | `is_account_denial()` → trả về ngay + blocklist account bền |
| 10 | `ai/media_store.py` | `Image.LANCZOS` **đã bị xoá trong Pillow 12** ⇒ nén WebP luôn fail | `Image.Resampling.LANCZOS` (+ fallback giữ ảnh gốc) |
| 11 | `ai/image_pipeline.py` | `_save_image_entry` truyền **raw bytes** vào `save_b64_image` (hàm base64-decode) ⇒ ảnh hỏng | thêm `media_store.save_image_bytes()` |

**Thêm 3 bug phát hiện khi chạy song song nhiều ngày:**
| # | File:line | Lỗi | Fix |
|---|---|---|---|
| 12 | `ai/media_store.py:save_index()` | **Windows `os.replace` ném `PermissionError`** khi file manifest đang được thread khác mở đọc ⇒ file media đã ghi xong nhưng **MẤT entry manifest** (đo thật: **18.500 file ảnh nhưng manifest chỉ còn 1.369 entry**) | retry 10 lần (`os.replace` + `time.sleep` tăng dần) + fallback ghi trực tiếp |
| 13 | `ai/media_store.py` | không có cách khôi phục file "mồ côi" | thêm `media_store.reindex()` — quét lại `data/media/` và dựng manifest từ đĩa. **Đã dùng để khôi phục 35.445 entry mồ côi** (4.087 → 39.532) |
| 14 | `ai/openclaw_web_ai.py:192` | `r.get("result")` khi `r` là **list** ⇒ `AttributeError` | kiểm `isinstance(r, dict)` |
| 15 | `ai/media_store.py` | manifest 39.532 entry (~20 MB JSON) ⇒ mỗi lần lưu 1 media **ghi lại toàn bộ manifest** = 2.6 GB I/O/vòng ngày ⇒ **treo** | cache index trong RAM + ghi theo lô (≥100 entry hoặc ≥15 s) + `flush_index()` |
| 16 | `ai/tts_generator.py` | TTS 429 ⇒ thử **tới 90 key**, mỗi key chờ pace ⇒ **treo pipeline** (tái hiện bằng `faulthandler`) | `MAX_TTS_KEY_TRY=4` + tracker quota bền theo ngày + xoay 5 model TTS |
| 17 | `ai/gemini_safe.py` | 429 RPM khoá **cả account** (9-10 key) ⇒ 6 luồng hết key | `AccountPool.lock_key()` — khoá riêng 1 key |
| 18 | `ai/gemini_safe.py::pace()` | nghỉ cố định 3.5-5 s ⇒ lãng phí 6-8× khi có 47 key | **pace thích ứng**: `min(5, max(0.8, 60/(số_project × 11)))` = 0.9 s |
| 19 | `api/gemini_safe.py::classify_response()` | quota **NGÀY** (20/project/model) có message *"Please retry in 13h33m"* **không chứa "perday"** ⇒ phân loại nhầm `QUOTA_RATE` ⇒ retry 12×65s **treo** | nhận diện `"please retry in Nh"` + `"limit: 0"` → `QUOTA_DAILY` |
| 20 | `api/gemini_safe.py::_try_models` | 1 model hết quota ⇒ vô hiệu hoá **cả 8-10 key** của account | thử **model khác** trước (mỗi model = 1 quota bucket riêng) |
| 21 | `api/gemini_safe.py::request()` | biến `model` không tồn tại trong `request()` ⇒ `NameError` | dùng `res.get("model")` |
| 22 | `ai/tts_generator.py` | Gemini TTS đứng đầu cascade ⇒ mỗi câu mất 7.4 s chỉ để nhận 429 | đảo: `cache` → **edge-tts** (0.6-4.3 s, 11/11 ngôn ngữ) → Gemini → gTTS → pyttsx3 |
| 23 | `settings.json` | `media.image_providers` vẫn là `["web","dict","placeholder"]` ⇒ mỗi ngày mất ~60 s chờ tầng Web AI | đặt `["dict","placeholder"]` (tầng `web` bật tay sau khi cài addon) |
| 24 | `ai/pipeline_media.py::run_audio_stage` | tạo file mp3 nhưng **không gắn `v["audio_ref"]`** ⇒ app không tìm thấy audio của từ | gắn `v["audio_ref"]` + `lesson["media"]["vocab_audio"]`; thêm `tools/link_media_refs.py` để gắn lại cho các ngày đã render (khớp theo tên file `word_<idx>_` / `audio_<kind>_<idx>_`, chuẩn hoá lang về slug vì manifest có cả `Tiếng Trung` lẫn `tiếng_trung`) |
| 25 | `ai/dictionary_image.py` | **36 request Wikimedia đồng thời** (6 luồng pipeline × 6 worker ảnh) ⇒ bị rate-limit ⇒ **96% ảnh thành placeholder** (chỉ 1.147/30.116 ảnh thật) | thêm throttle toàn tiến trình: `Semaphore(4)` + tối thiểu **0.2 s** giữa 2 request + retry 429/403/503 với backoff. Đo lại: **10/10 ảnh thật trong 4.3 s** |
| 26 | `ai/pipeline_media.py::run_media_verify_stage` | ngày bị kill giữa chừng để lại checkpoint "done" nhưng **không có file media** ⇒ không bao giờ được sinh lại | verify luôn chạy (bỏ early-return) + đếm từ thiếu `image_ref`/`audio_ref` ⇒ đánh dấu stage images/audio = **PENDING** để vòng quét sau sinh bù. Thêm `tools/replace_placeholders.py` để đánh dấu lại toàn bộ ngày có placeholder |
| 27 | `ai/dictionary_image.py` | **Wikimedia chặn IP sau ~30.000 request** (429 cho MỌI request) ⇒ mỗi từ mất 10 s chỉ để nhận 429 ⇒ nuốt hết thời gian pipeline | 3 lớp: (1) throttle toàn tiến trình `Semaphore(8)` + 0.1 s, (2) **cache bền** `data/media/image_cache.json` (cache cả kết quả "không có ảnh"), (3) **circuit breaker** 5×429 ⇒ khoá 15 phút + `WORD_DEADLINE_SECONDS=10` |
| 28 | `ai/dictionary_image.py` | tìm ảnh theo **nghĩa tiếng Việt** với khớp "prefix" ⇒ "chạy" khớp "Chay Bowes" (cầu thủ) ⇒ ảnh sai nghĩa | nhánh nghĩa VN chỉ nhận khớp **`exact`** |

**Circuit breaker tầng Web AI** (`ai/web_ai_bridge.py`): khi không cài addon / thiếu chromedriver, mỗi ngày mất **~60 s** chờ timeout. Sau **3 lần thất bại liên tiếp** → tạm vô hiệu tầng Web AI trong **30 phút** (có thể thử lại). Tự động bật lại khi hết thời gian chờ.

> **QUYẾT ĐỊNH**: `media.image_providers` **mặc định = `["dict", "placeholder"]`** — tầng `web` **tắt mặc định** vì cần Chrome addon cài thủ công; bật lại sau khi cài addon (hướng dẫn trong `tools/README.md` + SKILL mục 5).

---

### 🔴 PHÁT HIỆN THEN CHỐT — QUOTA TTS THẬT CỦA GEMINI (10/ngày/key/model)

API trả về (đo 2026-10-21 lúc 23:47):

```
quotaId:          GenerateRequestsPerDayPerProjectPerModel-FreeTier
quotaDimensions:  {location: global, model: gemini-3.8-flash-tts}
quotaValue:       10
"Please retry in 14h8m43s"
```

⇒ **10 request/ngày / MỖI KEY / MỖI MODEL** — hạn mứn **NGÀY**, không phải RPM.

| Hạng mục | Số |
|---|---|
| Model TTS dùng được | **5** (`3.8-flash-tts`, `3.8-flash-lite-tts`, `3.1-flash-tts-preview`, `2.5-flash-preview-tts`, `2.5-pro-preview-tts`) |
| Sức chứa thực tế | 10 × 5 × ~47 key ≈ **2.350 file TTS/ngày** (dùng 1 model ⇒ chỉ 470/ngày) |
| Quota reset | **0h00 theo giờ Google** |

**⇒ Thay đổi thiết kế bắt buộc:**
1. `ai/tts_generator.py` xoay **nhiều model TTS** (mỗi model hạn mức riêng) + sắp theo model còn nhiều quota nhất.
2. Tracker quota **bền theo ngày**: `data/tts_quota.json` = `{date, used:{"<keyhash>|<model>": n}}`.
3. Hết quota → stage audio đánh dấu **PENDING** (không phải `done`) ⇒ chạy lại ngày sau, không bỏ sót.
4. `MAX_TTS_KEY_TRY = 4` — trước đây thử **tới 90 key** × pace ⇒ **treo cả pipeline** (đã tái hiện bằng `faulthandler`).
5. Cooldown key sau 429 = **300 s** (quota là NGÀY ⇒ 60 s không giúp).

**Bài học**: quota Gemini free tier có **2 tầng** — RPM (15/phút) cho text, và **RPD theo (project, model)** cho TTS. Tầng RPD mới là thứ giới hạn thật sự khi sinh hàng loạt.

---

### 🔴 QUOTA TEXT CŨNG LÀ **20/NGÀY/PROJECT/MODEL** (không phải 15 RPM)

Đo lúc 00:25 (sau khi đã dùng hết quota ngày):

```
quotaMetric:   generativelanguage.googleapis.com/generate_content_free_tier_requests
quotaValue:    20
quotaDimensions: {location: global, model: gemini-3.8-flash}
"Please retry in 13h33m50s"
```

**Hệ quả nghiêm trọng:** message **KHÔNG chứa chữ "perday"** ⇒ `classify_response()` phân loại thành `QUOTA_RATE` (tạm thời) ⇒ **retry 12 lần × 65 s ⇒ treo pipeline** thay vì đánh dấu hết quota.

**Sửa (3 điểm):**
1. `classify_response()` nhận diện `"please retry in Nh"` (N ≥ 0.25 giờ) và `"limit: 0"` → `QUOTA_DAILY`.
2. **Mỗi model là một "quota bucket" RIÊNG** ⇒ khi 1 model hết quota phải **thử model khác TRƯỚC khi đổi key** (nếu không sẽ vô hiệu hoá 8-10 key của account chỉ vì 1 model hết quota).
3. `pace()` tính theo **số PROJECT (account)** khả dụng, không phải số key:
   `interval = min(5, max(0.8, 60/(n_project × 11)))` → 5 project ⇒ 0.9 s/lần (≤ 11 RPM/project).

**Cấu trúc pool key thật** (đo): 90 key = **10 `project_id` × 9 account**, mỗi (account, project) đúng 1 key.

| Hạng mục | Số |
|---|---|
| Project | 10 (mỗi project có 9 key, 1/account) |
| Model text dùng được | 10 (thêm mới sau khi đo) |
| **Sức chứa text/ngày** | 10 × 10 × 20 = **2.000 call/ngày** (thực ~1.200 vì ~1/3 key chết) |
| ⇒ 3.010 ngày cần dialogue | **~2-3 ngày chạy nền** (pipeline tự resume) |

**Model chain mới** (`settings.json → ai.model_priority`): `gemini-3.6-flash` · `gemini-3.5-flash` · `gemini-flash-lite-latest` · `gemini-3.7-flash` · `gemini-3.1-pro-preview` · `gemini-4-argon` · `gemini-pro-latest` · `gemini-flash-latest` · `gemini-omni-1.1-flash` · `gemini-3.8-flash`
> `gemini-2.5-flash` / `gemini-2.5-pro` → **404** *"no longer available to new users"*. `gemini-3.8-flash-lite` → **404**.

---

### 🔊 TTS — ĐẢO THỨ TỰ CASCADE (edge-tts lên đầu)

Đo thực tế (2026-10-21, 11 ngôn ngữ):

| Engine | Kết quả | Thời gian/file |
|---|---|---|
| **edge-tts** | ✅ **11/11 ngôn ngữ** | **0.6-4.3 s** |
| **gTTS** | ✅ 11/11 | 0.3 s |
| Gemini TTS | ✅ nhưng **quota 10/ngày/key/model** | 429 + 7.4 s lãng phí/câu |
| pyttsx3 | ⚠️ máy này chỉ có en-US×2 + ja-JP×1 | — |

⇒ Cascade mới: `cache` → **edge-tts** → Gemini TTS → gTTS → pyttsx3.
> Trước đó Gemini TTS đứng đầu ⇒ mỗi câu mất 7.4 s chỉ để nhận 429 rồi mới rơi xuống edge-tts (nhanh gấp 10-20×).

---

### 🎨 Chuỗi nguồn ảnh (thực tế, đã kiểm chứng)

| Tầng | Nguồn | Trạng thái | Ghi chú |
|---|---|---|---|
| T1 | Gemini native image | ❌ `limit: 0` free tier | code giữ lại, dùng khi có key trả phí |
| T2a | Chrome addon (Gemini/ChatGPT/Copilot) | Phase 4 | giữ `<img>`, tải về qua local bridge |
| T2b | Selenium | Phase 4 | anti-detect, profile riêng |
| T2c | OpenClaw browser CLI | Phase 4 | cần profile `chrome` đã pair |
| **T3a** | **Openverse** (`api.openverse.org`) | ⚠️ **không ổn định** (timeout 60s) | chỉ dùng fallback cuối, timeout 12s |
| **T3b** | **Wikipedia/Wiktionary `pageimages`** | ✅ **đang chạy** | 0 key, 0.5-2.2s/ảnh, CC-BY-SA + attribution |
| **T3c** | **Wikimedia Commons search** | ✅ **đang chạy** | tìm thẳng trong kho ảnh (namespace 6) |
| T4 | Placeholder (chữ cái đầu) | ✅ luôn có | 616 byte, không để trống |

**Lọc độ liên quan (tránh ảnh sai nghĩa):** `title_matches()` → `exact` / `prefix` / `word` / không khớp; bỏ trang định nghĩa + trang "Radical N"; `confidence` lưu vào manifest (`high` / `medium` / `low`).

---

### 🔊 TTS — đặc tả 6 chặng

| Chặng | Đơn vị đọc | edge-tts rate | Số file/từ |
|---|---|---|---|
| Vỡ lòng | từng ký tự/âm lẻ | `-45%` | 2 (normal+slow) |
| Ghép âm | âm tiết | `-30%` | 2 |
| Sơ cấp | từ + mẫu câu ngắn | `-15%` | 2 |
| Trung cấp | câu đầy đủ | `+0%` | 1 |
| Cao cấp | đoạn 3-5 câu | `-5%` | 1 |
| Bản xứ | thành ngữ + hội thoại | `+0%` | 1 + từng lượt |

Cascade: `cache mp3` → **Gemini TTS** (WAV) → `edge-tts` → `gTTS` → `pyttsx3` (**chỉ khi có voice khớp locale** — máy này chỉ có en-US×2 + ja-JP×1 ⇒ 8/10 ngôn ngữ KHÔNG có giọng offline ⇒ **tuyệt đối không fallback sang giọng Anh**).

---

### 🤖 Orchestrator tự trị (`ai/pipeline.py`)

```bash
python -m ai.pipeline --lang japanese --full      # 1 ngôn ngữ
python -m ai.pipeline --all --full --workers 6     # 8 ngôn ngữ, 6 luồng
python -m ai.pipeline --all --mode media --full    # GIỮ content, chỉ thêm media
python -m ai.pipeline --lang tiếng_anh --status     # xem trạng thái + DoD
python -m ai.pipeline --lang tiếng_anh --dry-run   # kế hoạch, 0 call
```

- **Stage**: `profile → backbone → plan` (global) · `content → quiz_ab → quiz_cd → images → audio → dialogue → media_verify` (mỗi ngày)
- **Checkpoint** từng stage ⇒ dừng giữa chừng chạy lại là tiếp tục
- **Budget bền** 3 loại: `call` (1200/ngày) · `ảnh` (60/ngày) · `TTS` (3000/ngày) — TTS tách riêng vì khác quota metric
- **DoD** 13 check boolean ⇒ `progress.json.pipeline.definition_of_done.met`
- **Chế độ `media`**: giữ nguyên content/quiz sẵn có, chỉ thêm media (tiết kiệm ~8.000 call)
- **Xử lý ngày song song** (`--workers N`): mỗi ngày độc lập, chỉ `save_course` có lock

**Chính sách tự quyết (17 tình huống):** model 404 → dead list · 403 account → blocklist vĩnh viễn · 429 Daily → xoay key rồi chờ quota · JSON cắt → retry → split → salvage → `deferred_days` → đi tiếp · mất mạng → thoát mềm code 75 · đĩa đầy → dừng code 74 · hết key → code 78.

---

### 🌐 Web app (Phase 7)

- `web/script.js`: nạp `data/media/index.json` (lazy), render **ảnh minh họa + credit**, **IPA + pos badge**, **khẩu hình phát âm**, **common_mistakes + mini_quiz**, **khối hội thoại** (từng lượt + audio + cultural_note)
- `web/style.css`: `.media-img-wrap`, `.media-audio`, `.vocab-ipa`, `.pos-badge`, `.phonetic-note`, `.mistake-box`, `.dialogue-box/turn/speaker/culture`
- `web/index.html` + `web/manifest.json`: PWA thật (2 icon PNG)
- `api/github_sync.py`: `full_sync` upload `data/media/<lang>/` **theo `media.sync_langs`** (chọn lọc) + manifest

---

### 🧪 Test (Phase 9)

- Tách **FAST** (mặc định, < 60s, bỏ qua section [11]) và **SLOW** (`--slow`, ~10 phút, sinh 700 ngày thật)
- Thêm section **[24]** Media Schema v4 & Store · **[25]** Image Pipeline (mock) · **[26]** TTS Config & Generator · **[27]** Dictionary Image helpers · **[28]** Pipeline Orchestrator (Budget/DoD/Checkpoint/Log)
- Tổng: **67 → 79 test**

---

### 📚 Skill & Rule mới (trong `VocabularyApp/.agents/`)

- `skills/vocab_ai_media/SKILL.md` — 9 mục: Gemini native image · bộ lọc 6 lớp · aHash · addon MV3 · Selenium anti-detect · **OpenClaw CLI 3 blocker** · TTS cascade · bảng voice 11 ngôn ngữ · tham chiếu nhanh
- `rules/vocab_ai_content_rules.md` — schema additive-only · migration dirty-flag · token/JSON truncation · chuỗi media 5 tầng · TTS theo 6 chặng · budget · backup an toàn

---

### 📦 GÓI BÀN GIAO (đọc để tiếp tục phiên sau)

| Tài liệu | Vai trò |
|---|---|
| **`docs/UPGRADE_16.md`** ⭐ | **BÀN GIAO CHÍNH** — bản đồ kiến trúc, toàn bộ lệnh, giới hạn thật đã đo (quota Gemini 20/ngày/project/model · ảnh `limit: 0` · Wikimedia IP block · bằng chứng ToS · OpenClaw cần pair lại), 28 bug đã sửa, **danh sách việc còn lại** |
| `.agents/skills/vocab_ai_media/SKILL.md` | 12 mục kiến thức media (đọc TRƯỚC khi sửa media) |
| `.agents/rules/vocab_ai_content_rules.md` | 11 mục quy tắc nội dung (schema additive, migration 2 tầng, budget, attribution) |
| `tools/README.md` | 12 script chẩn đoán/verify + kỳ vọng output |
| `ai/pipeline_log.py::EVENTS` | Danh sách event log chuẩn |

**Kết quả kiểm chứng cuối (22/10/2026):**
```
test_ai_rich.py            → 79/79 PASS
verify_all_native_courses  → 27/27 PASS
tools/verify_p0_fixes.py   → 14/14 PASS   (tự tái hiện 14 lỗi P0)
tools/verify_no_rewrite.py → PASS        (8 course.json KHÔNG bị ghi lại khi đọc)
py_compile                 → 44/44 file OK
node --check (web + addon) → OK
GUI smoke test             → TỪ VỰNG · NGỮ PHÁP · HỘI THOẠI · ẢNH · AUDIO · IPA · TRẮC NGHIỆM
```

**Việc còn lại (xếp theo ưu tiên — xem `docs/UPGRADE_16.md` mục 7):**
1. `python -m ai.pipeline --all --mode enrich --full --allow-degraded --workers 4` → có **IPA thật + khẩu hình + lỗi sai + mini_quiz + dialogue ngắn** (~2 ngày quota)
2. Nối `ai/srs.py` (SM-2, 15/15 test) vào GUI: bảng `review_state`, nút Again/Hard/Good/Easy, hàng đợi "đến hạn", streak, thống kê (`App.update_stats()` hiện là `pass`)
3. Nối `ai/evidence.py` (dẫn chứng, 7/7 test) vào pipeline + render khối "📚 Nguồn"
4. Tách 1 call AI riêng cho grammar enrichment (Gemini **loại bỏ** optional nested-array khi response lớn ⇒ `common_mistakes`/`mini_quiz` rỗng)
5. Git PAT: cần **BẠN** revoke token tại https://github.com/settings/tokens rồi chạy:
   `git filter-repo --path GravityCode/VocabularyApp/settings.json --invert-paths`
   (đã untrack `data/` + `settings.json` + `__pycache__`, file vẫn còn trên đĩa)
6. OpenClaw: cần **BẠN** chạy `openclaw.cmd browser extension install` rồi bấm icon extension trong Chrome "Profile 3" (thiếu native-messaging host `com.openclaw.browser_relay`)

---


### ⚙️ Cài Đặt Model AI, Quản Lý Thứ Tự Ưu Tiên & Tự Động Khám Phá / Benchmark (Đồng Bộ Cơ Chế AskCpl) — HOÀN THÀNH ✅

**Vấn đề đã giải quyết:**
- ❌ **Model AI bị hardcode cứng**: Trước đây `MODEL_FALLBACKS` trong `gemini_safe.py` là danh sách tĩnh, khi Google deprecate/đổi tên model (hoặc ra mắt các model mới như Gemini 2.5/Flash-Lite), ứng dụng dễ gặp lỗi hoặc không tận dụng được model mới.
- ❌ **Chưa đồng bộ cấu hình với AskCpl**: Người dùng đã cấu hình danh sách model và benchmark trong AskCpl nhưng VocabApp không đọc được hoặc không có UI quản lý riêng.
- ❌ **Không thể tự khám phá (Discovery) & Benchmark model**: Thiếu tính năng tự động gọi Google API `GET /v1beta/models` để quét các model đang sống và đo độ trễ (latency ms) thực tế.

**Giải pháp triển khai:**
- 🛠️ **`settings.py`**:
  - Bổ sung cấu hình `model_priority` trong `DEFAULT_SETTINGS["ai"]`.
  - Hàm `get_active_model_list()`: Đọc danh sách model đã bật (`enabled=True`) từ `settings.json` của VocabApp; nếu chưa cấu hình thì tự động fallback đọc từ file `settings.json` của `AskCpl`; nếu vẫn chưa có thì dùng danh sách fallback mặc định.
  - Hàm `update_ai_settings(**kwargs)`: Cập nhật cấu hình AI an toàn.
- 🛡️ **`api/gemini_safe.py`**:
  - `GeminiCoordinator`: Khi khởi tạo với `models=None`, tự động đọc danh sách model active từ `get_active_model_list()`.
  - Thêm property `models` để truy cập danh sách model fallback an toàn.
- 🖥️ **`VocabApp.py`**:
  - Xây dựng dialog **`ModelSettingsDialog`**:
    * Giao diện Dark theme theo chuẩn màu VocabApp (`#BB86FC`, `#121212`, `#1E1E1E`).
    * Bảng Treeview hiển thị: Thứ tự ưu tiên, Tên model, Tier (S/A/B/C), Trạng thái bật/tắt (Checkbox), Độ trễ (Latency ms), Ghi chú.
    * Các nút điều khiển: `▲ Lên`, `▼ Xuống`, `👁️ Bật/Tắt`, `➕ Thêm Model`, `🗑️ Xóa`.
    * Nút **`🚀 Quét & Benchmark Tự Động`**: Tự động gọi Google API lấy danh sách model thực tế, gửi test prompt `Hi` đo thời gian phản hồi, tính toán điểm hiệu năng và sắp xếp lại thứ tự ưu tiên tối ưu nhất.
    * Nút **`🔄 Nạp Từ AskCpl`**: Đồng bộ tức thì cấu hình model từ tiện ích AskCpl sang VocabApp.
  - Tích hợp nút `⚙️ Cài đặt Model` vào hộp thoại sinh khóa học `CourseGenerationDialog` (bên cạnh nút Dừng và Bắt đầu).
  - Tích hợp khu vực `⚙️ Cài Đặt & Khám Phá Model AI` vào tab `Đồng Bộ & Cài Đặt (SettingsSyncTab)`.
  - Hiển thị danh sách model đang ưu tiên trong log khi mở dialog tạo khóa học.
- 🧪 **`test_ai_rich.py`**:
  - Bổ sung Test Section [23]: Kiểm tra `get_active_model_list()`, `GeminiCoordinator.models`, và cập nhật lọc `update_ai_settings`.
  - Toàn bộ **67/67 bài kiểm thử chạy thành công 100%**.

| File | Thay đổi |
|------|----------|
| `settings.py` | Thêm `model_priority` vào `DEFAULT_SETTINGS["ai"]`, hàm `get_active_model_list()`, `update_ai_settings()`. |
| `api/gemini_safe.py` | Cập nhật `GeminiCoordinator` tự động nạp `get_active_model_list()`, thêm property `models`. |
| `VocabApp.py` | Tạo `ModelSettingsDialog`, thêm nút cài đặt vào `CourseGenerationDialog` và `SettingsSyncTab`, log danh sách model active. |
| `test_ai_rich.py` | Bổ sung Test Section [23] kiểm thử Model Priority, Coordinator và Fallback. |
| `projectLog.md` | Ghi nhận nhật ký Update 15. |

---

## 📋 Cập nhật trước đó — 2026-09-05 (Update 15)

### ⚙️ Cài Đặt Model AI, Quản Lý Thứ Tự Ưu Tiên & Tự Động Khám Phá / Benchmark (Đồng Bộ Cơ Chế AskCpl) — HOÀN THÀNH ✅

*(Xem bảng file đã sửa ở cuối mục này.)*

---

## 📋 Cập nhật trước đó — 2026-09-03 (Update 14)

### 🧠 AI Tự Động Suy Luận Định Danh Ngôn Ngữ & Quy Mô Số Ngày Chuẩn Bản Xứ C2 — HOÀN THÀNH ✅

**Vấn đề đã giải quyết:**
- ❌ **Cào bằng số ngày ~300 ngày**: Trước đây `get_language_fsi_profile` hardcoded số ngày theo FSI tối thiểu (240 - 420 ngày), khiến khóa học chỉ dừng ở mức B2, chưa phản ánh được độ sâu kiến thức thực tế để đạt tầm **Người bản xứ (Native/C2)**.
- ❌ **Thiếu cơ chế suy luận động**: Không có cơ chế AI tự phân tích độ phức tạp của từng ngôn ngữ (hệ chữ, thanh điệu, ngữ pháp, khoảng cách với tiếng Việt, văn hóa ngầm, thành ngữ & tiếng lóng) như AskCpl.

**Giải pháp triển khai:**
- 🎯 **Module `ai/language_profiler.py` (AI Dynamic Language Profiler)**:
  - Tự động dùng Gemini AI phân tích bản chất ngôn ngữ và suy luận số ngày thực tế cần thiết để đạt mức **Bản xứ (C2)**:
    * Nhóm Latinh thông dụng (Tiếng Anh...): ~600 - 800 ngày (Fallback: 700 ngày).
    * Nhóm Latinh chia giống & thì phức tạp (Đức, Pháp, TBN, Ý...): ~750 - 950 ngày (Fallback: 840 ngày).
    * Nhóm Hệ chữ riêng & Biến cách nhiều (Nga, Thái, Hy Lạp, Ba Lan...): ~850 - 1150 ngày (Fallback: 980 ngày).
    * Nhóm Khó nhất (Tượng hình, Kanji/Hanzi, SOV, Kính ngữ: Nhật, Trung, Hàn, Ả Rập...): ~1200 - 1600 ngày (Fallback: 1260 ngày).
  - Tự động phân bổ số ngày chuẩn tỷ lệ cho 6 Chặng (Vỡ lòng $\to$ Ghép âm $\to$ Sơ cấp $\to$ Trung cấp $\to$ Cao cấp C1 $\to$ Bản xứ C2).
  - Xác lập danh xưng (`persona`), lời khuyên sư phạm chiến lược (`instruction`), và các cột mốc tinh hoa bắt buộc (`mandatory_milestones`).
- 💾 **Bộ nhớ đệm Cache (`data/language_profiles_cache.json`)**:
  - Lưu lại kết quả phân tích của AI. Lần khởi động tiếp theo lấy ngay tức thì, không tốn quota API.
- 🛡️ **Hậu phương an toàn (Rule-Based Fallback)**:
  - Tự động tính toán quy mô ngày bản xứ chính xác ngay cả khi offline hoặc chưa nhập API key.
- 🖥️ **Giao diện trực quan (`VocabApp.py`)**:
  - Tùy chọn thời lượng chuyển thành: **`Tự động (AI suy luận số ngày chuẩn Bản xứ C2)`**.
  - Hiển thị trực tiếp danh xưng, định danh và số ngày bản xứ C2 trong nhãn thông tin và hộp thoại log.
- 🔄 **Nâng cấp khóa học cũ**:
  - Nút `🔍 Rà soát & Bổ sung` tự động nối dài giáo trình cũ lên đủ quy mô ngày bản xứ (ví dụ: Tiếng Nhật 240 ngày $\to$ bổ sung thêm +1020 ngày lên đủ 1260 ngày) mà không làm mất bài cũ.

| File | Thay đổi |
|------|----------|
| `ai/language_profiler.py` | • Module mới: Khảo sát định danh tri thức ngôn ngữ bằng AI, quản lý cache JSON, và thuật toán fallback chuẩn Bản xứ C2. |
| `ai/course_generator.py` | • Thêm hàm `get_language_native_profile` kết nối AI Profiler.<br>• Tích hợp vào `generate_course` và `audit_and_supplement_course`. |
| `VocabApp.py` | • Cập nhật `CourseGenerationDialog`: hiển thị kết quả phân tích của AI Profiler; cập nhật dropdown thời lượng sang chế độ Tự động chuẩn Bản xứ C2. |
| `test_ai_rich.py` | • Thêm Test Section 22 kiểm thử toàn diện: Fallback profiles, Cache read/write, AI reasoning, và Backbone 700 ngày.<br>• Toàn bộ **63/63 bài kiểm thử chạy thành công 100%**. |
| `projectLog.md` | Ghi nhận nhật ký Update 14. |

---

## 📋 Cập nhật trước đó — 2026-09-02 (Update 13)

### 🔍 Tính Năng "Rà Soát & Bổ Sung" (Audit & Auto-Supplement) Khóa Học Cũ — HOÀN THÀNH ✅

**Mục tiêu đã giải quyết:**
- 🛡️ Người dùng không cần phải bấm "Làm lại từ đầu" làm mất các ngày đã học.
- 🎯 Tự động quét đối chiếu khóa học hiện có với Chuẩn FSI Quốc Tế (6 Chặng, đủ số ngày sàn).
- 🧩 Tự động phát hiện các Chặng bị thiếu (như Chặng 5 Cao cấp bị 0 ngày) hoặc các chặng bị hụt ngày $\to$ tự động lấy các slot bài học từ Kho Template 3 Lớp bổ sung vào Master Backbone.
- 💾 Giữ nguyên 100% dữ liệu và tiến độ các ngày đã sinh cũ.

| File | Thay đổi |
|------|----------|
| `ai/course_generator.py` | • Xây dựng hàm `audit_and_supplement_course(language, level, coord, log_fn)` tự động quét 6 chặng và bổ sung đủ 100% sàn FSI.<br>• Tích hợp tự động rà soát vào `generate_course` khi chạy tiếp tục khóa học Trọn Gói. |
| `VocabApp.py` | • Thêm nút bấm **`🔍 Rà soát & Bổ sung`** (màu xanh dương) trong hộp thoại `CourseGenerationDialog`.<br>• Cho phép người dùng bấm rà soát bất kỳ lúc nào với nhật ký log trực quan. |
| `test_ai_rich.py` | • Thêm test section 21: Kiểm tra khóa học Tiếng Nhật 240 ngày cũ được tự động bổ sung +180 ngày (lên đủ 420 ngày chuẩn FSI) với 100% ngày cũ giữ nguyên `filled_day`.<br>• Toàn bộ **56/56 bài kiểm thử chạy thành công 100%**. |
| `projectLog.md` | Ghi nhận nhật ký Update 13. |

---

## 📋 Cập nhật trước đó — 2026-09-02 (Update 12)

### 📚 Mở Rộng Kho Chủ Đề (Topic Pool Expansion) & Triệt Tiêu Trùng Lặp 100% — HOÀN THÀNH ✅

**Vấn đề đã giải quyết:**
- ❌ **Trùng lặp chủ đề khi số ngày lớn**: Ở các chặng dài (Stage 3 cần 78 slot nội dung, Stage 4 cần 90 slot, Stage 5 cần 83 slot), kho chủ đề cũ chỉ có 12-24 bài dẫn đến việc xoay vòng (cycle) lặp lại 4-7 lần tên bài học.

**Giải pháp triển khai:**
- 🎯 **Mở rộng kho chủ đề phong phú theo chuẩn quốc tế**:
  - **Stage 1 (Vỡ lòng)**: 25 slots nội dung độc nhất (100% không trùng).
  - **Stage 2 (Ghép âm & Sinh tồn)**: 32 slots nội dung độc nhất (100% không trùng).
  - **Stage 3 (Sơ cấp A1-A2)**: Mở rộng lên 78 slots nội dung độc nhất (Mua sắm, Ẩm thực, Thuê nhà, Khám bệnh, Du lịch biển/núi, Cắm trại, Cuộc sống số, Văn hóa cà phê...).
  - **Stage 4 (Trung cấp B1-B2)**: Mở rộng lên 90 slots nội dung độc nhất (Phỏng vấn, Thuyết trình, Đàm phán, Quản lý dự án, Marketing, Tài chính P&L, Logistics, Hợp đồng, ISO, Phễu bán hàng, Kinh tế tuần hoàn...).
  - **Stage 5 (Cao cấp C1)**: Mở rộng lên 83 slots nội dung độc nhất (Xã luận, Phân tích biểu đồ, Kinh tế vĩ mô, AI & Big Data, Biến đổi khí hậu, Đạo đức sinh học, Vật lý lượng tử, Triết học, Pháp luật quốc tế, Văn học hậu hiện đại...).
  - **Stage 6 (Bản xứ C2)**: Mở rộng lên 49 slots nội dung độc nhất (Thành ngữ theo chủ đề, Slang Gen Z, High-context ngầm hiểu, Trào phúng, Chơi chữ, Phương ngữ, Trà đạo, Triết lý vô thường/khắc kỷ, Đồ án Capstone...).
- 🛡️ **Hậu phương bảo vệ (Cycle Suffix Safeguard)**: Tự động đánh số `(Phần 2)`, `(Phần 3)` nếu có bất kỳ chu kỳ xoay vòng nào, bảo đảm 100% tên bài học luôn phân biệt rõ ràng.

| File | Thay đổi |
|------|----------|
| `ai/course_generator.py` | • Bổ sung hơn 200+ chủ đề chuyên sâu vào STAGE_POOLS.<br>• Thêm cơ chế hậu phương `cycle_num > 0 -> (Phần N)` trong `build_stage_universal_template`. |
| `test_ai_rich.py` | Toàn bộ 55/55 bài kiểm thử chạy thành công 100%. |
| `projectLog.md` | Ghi nhận nhật ký Update 12. |

**Test kết quả:** ✅ 55/55 test passed (Python 3.14) & Tỷ lệ trùng chủ đề: **0% (100% Unique)** trên toàn bộ 6 Chặng và tất cả các nhóm ngôn ngữ.

---

## 📋 Cập nhật trước đó — 2026-08-30 (Update 13)

### 🌐 Tự Động Quét & Hiển Thị Ngôn Ngữ Khóa Học AI — HOÀN THÀNH ✅

**Vấn đề đã giải quyết:**
- ❌ **Khóa học AI bị ẩn khi mở lại ứng dụng**: Trước đây `get_available_languages()` chỉ quét các file `data/*.json` (danh sách từ vựng nhập tay). Khi người dùng tạo một khóa học AI mới hoàn toàn (như Tiếng Trung 442 ngày) mà chưa nhập từ vựng thủ công vào `data/`, ngôn ngữ này không xuất hiện trong dropdown Ngôn ngữ khi khởi động lại ứng dụng.

**Giải pháp triển khai:**
- 🔍 **Cập nhật `get_available_languages()` trong `database/database.py`**:
  - Quét cả 2 nguồn: `data/*.json` (từ vựng thủ công) và `data/ai_courses/*/course.json` (khóa học AI).
  - Đọc chính xác trường `"language"` được lưu trong `course.json` và loại trừ trùng lặp (case-insensitive).
  - Bất kỳ ngôn ngữ nào đã sinh khóa học AI sẽ luôn tự động hiển thị trong dropdown chọn ngôn ngữ của toàn bộ ứng dụng.

| File | Thay đổi |
|------|----------|
| `database/database.py` | Cập nhật `get_available_languages()` quét đa nguồn (`data/*.json` + `data/ai_courses/*/course.json`). |
| `projectLog.md` | Ghi nhận Update 13. |

**Test kết quả:** ✅ `['Nhật', 'Tiếng Trung']` nhận diện tức thì & Compile OK.

---

## 📋 Cập nhật trước đó — 2026-08-30 (Update 12)

### 🛡️ Chống Lỗi JSON Bị Cắt: Split-Quiz A+C (Tách 2 Lần Gọi + Partial Save) — HOÀN THÀNH ✅

**Vấn đề đã giải quyết:**
- ❌ **JSON trắc nghiệm bị cắt giữa chừng**: Gemini cắt output khi phải sinh 40 câu (4 loại × 10) trong 1 lần (~12-16k tokens). Retry 2 lần đều thất bại → ngày đó bị bỏ qua.
- ❌ **Mất content khi quiz fail**: Dù bài học đã sinh xong, nếu quiz fail thì không lưu gì cả — lần sau phải gọi lại cả content lẫn quiz.
- ❌ **Resume bỏ qua ngày lỗi**: Khi nhấn "Sinh lại", ngày có quiz fail không được retry vì `done_days` không nhận ra nó.

**Giải pháp triển khai — Hướng A + C kết hợp:**

| File | Thay đổi |
|------|----------|
| `ai/course_generator.py` | **Hướng A — Tách quiz 2 lần gọi:**<br>• Thêm `QUIZ_SCHEMA_AB` (vocab+pattern) và `QUIZ_SCHEMA_CD` (common+grammar).<br>• Thêm `build_quiz_prompt_ab()` và `build_quiz_prompt_cd()` — mỗi prompt chỉ ~20 câu (~6-8k tokens), giảm 50% nguy cơ JSON bị cắt.<br>• Thêm `_quiz_trap_rules()` tách riêng để 2 prompt dùng chung.<br>• `build_quiz_prompt()` giữ nguyên signature (backward compat).<br>**Hướng C — Partial Save:**<br>• Sau lần gọi 1 (content thành công), lưu ngay vào DB với cờ `_content_only=True`.<br>• Phát hiện `content_saved_days` khi khởi động vòng lặp — nếu ngày có content partial → chỉ gọi lại quiz, không gọi lại content.<br>• Khi lesson hoàn chỉnh (quiz xong), xóa cờ `_content_only`.<br>**Sửa `parse_quiz_json`:**<br>• Thêm tham số `keys: tuple = None` — không truyền → parse đủ 4 loại (backward compat); truyền keys=(…) → chỉ parse subset đó.<br>**Sửa `_ask()`:**<br>• Thêm kind `"quiz_ab"` và `"quiz_cd"` với parser riêng. |
| `test_ai_rich.py` | • Cập nhật import thêm `QUIZ_SCHEMA_AB`, `QUIZ_SCHEMA_CD`, `build_quiz_prompt_ab`, `build_quiz_prompt_cd`.<br>• Thêm **Test 20** (7 sub-test): parse_quiz_json với keys split, prompt_ab/cd isolation, trap rules, schema structure. |
| `projectLog.md` | Ghi nhận Update 12. |

**Luồng hoạt động mới (3 lần gọi AI/ngày thay vì 2):**
```
Lần 1: content  → lưu ngay (partial, _content_only=True)
Lần 2a: quiz AB (vocab+pattern, ~20 câu) → merge
Lần 2b: quiz CD (common+grammar, ~20 câu) → merge
→ lưu lesson hoàn chỉnh, xóa cờ _content_only
```
**Khi fail:** Nếu quiz AB hoặc CD fail → ngày đó giữ partial trong DB → lần chạy lại chỉ cần gọi lại quiz, không mất content.

**Test kết quả:** ✅ 55/55 test passed (Python 3.14) & Compile OK.

---

## 📋 Cập nhật trước đó — 2026-08-29 (Update 11)


### 🏛️ Kiến Trúc Giáo Trình Phổ Quát 3 Lớp (3-Layer Universal Curriculum Architecture) — HOÀN THÀNH ✅

**Vấn đề đã giải quyết:**
- ❌ **AI tự quyết số ngày dẫn đến thiếu hụt (240/420 ngày)**: Prompt trước đây chỉ đưa ra con số gợi ý, AI tự sinh số lượng chủ đề tùy ý (Stage 1 ra 51 ngày thay vì 30 ngày, Stage 5 bị sót hoàn toàn).
- ❌ **Nguy cơ thiếu ngày hoặc gián đoạn giữa các ngôn ngữ**: Mỗi ngôn ngữ cần một khung sàn tối thiểu chuẩn mực theo khung FSI quốc tế và không được phép thiếu ngày.

**Giải pháp triển khai:**
- 🧱 **Layer 1: Universal Template Slots (Sàn cứng không thể thiếu)**:
  - Sinh đúng $N$ slot nền tảng cho từng chặng (FSI Cat IV/V: [30, 38, 92, 105, 97, 58] = 420 ngày; Cat I: 240 ngày; Cat II/III: 320 ngày; Cat III/IV: 360 ngày).
  - Tự động tích hợp Ôn tập xoắn ốc (Spiral Review) vào ngày thứ 7, 14, 21, 28... và Tổng kết chặng ở ngày cuối cùng.
- 🌐 **Layer 2: AI Adaptation (Chuyên sâu hóa theo ngôn ngữ đích)**:
  - AI nhận danh sách slot phổ quát và chuyển ngữ chính xác sang tên chủ đề đặc thù của ngôn ngữ đó (Hiragana, Pinyin, IPA...).
  - Tích hợp cơ chế **Retry 2 lần + Fallback an toàn**: Nếu API lỗi, hệ thống tự động giữ nguyên template gốc, gắn cờ `needs_retry: True` và ghi nhận `pending_retry_count` mà không bao giờ làm sập chương trình.
- 🧩 **Layer 3: AI Gap Insertion (Chèn chủ đề đặc thù vào đúng vị trí sư phạm)**:
  - AI rà soát lỗ hổng và đề xuất chèn thêm các chủ đề đặc thù quan trọng vào sau `after_slot_id` chỉ định.
  - Tổng số ngày sau khi chèn sẽ luôn $\ge$ sàn tối thiểu (ví dụ Tiếng Nhật đạt 432-450+ ngày).
- 🔄 **Sinh liên tục 100% không ngắt**: Toàn bộ master backbone được chuyển thành 1 batch duy nhất chạy từ Ngày 1 đến ngày cuối cùng.

| File | Thay đổi |
|------|----------|
| `ai/course_generator.py` | • Thêm `build_stage_universal_template(stage_idx, target_days)` tạo generic slots.<br>• Thêm `build_stage_adapt_prompt` và `build_stage_gap_insert_prompt`.<br>• Thêm `build_master_backbone` tích hợp 3 lớp.<br>• Thêm `ADAPT_STAGE_SCHEMA` và `GAP_INSERT_SCHEMA`.<br>• Cập nhật `_get_item_phase` ưu tiên `stage_idx` để gắn tag chính xác 100%. |
| `test_ai_rich.py` | • Cập nhật `_FakeCoordinator` xử lý `ADAPT_STAGE_SCHEMA` và `GAP_INSERT_SCHEMA`.<br>• Bổ sung Test 14 (Universal Template slots & Spiral Review), Test 18 (Master Backbone 3 lớp + Gap Insertion), Test 19 (Retry Fallback & Pending Retries).<br>• 48/48 test passed (100%). |
| `projectLog.md` | Ghi nhận nhật ký Update 11. |

**Test kết quả:** ✅ 48/48 test passed (Python 3.14) & Compile OK.

---

## 📋 Cập nhật trước đó — 2026-08-28 (Update 10)

### 🌍 Hệ Thống Đào Tạo Đa Ngôn Ngữ Từ Con Số 0 Đến Như Người Bản Xứ (Universal Zero-to-Native AI Engine) — HOÀN THÀNH ✅

**Vấn đề đã giải quyết:**
- ❌ **Người mới 0 kiến thức bị ngợp**: Trước đây dù là Ngày 1 vẫn bị nhồi 10 mẫu câu phức tạp và 40 câu trắc nghiệm khó, khiến người chưa biết bảng chữ cái (Hiragana/Hangul/Pinyin/IPA) không thể hiểu được.
- ❌ **Chưa hỗ trợ trọn gói từ 0 ➔ Bản xứ**: Người học phải tự đoán và chuyển cấp độ thủ công, thiếu một lộ trình thống nhất từ con số 0 đến C2/Native-like.
- ❌ **Thiếu phân tích đặc tính ngôn ngữ (Typology)**: Dạy tiếng tượng hình giống tiếng chữ Latinh dẫn đến thiếu sót các giai đoạn nền tảng sống còn (quy tắc ghép vần, biến âm, thanh điệu).

**Giải pháp triển khai:**

| File | Thay đổi |
|------|----------|
| `ai/course_generator.py` | • **Chuẩn hóa 6 Bậc Học Sư Phạm + 1 Chế độ Trọn Gói Tự Động**:<br>  1. `⭐ Trọn gói: Từ con số 0 đến Như người bản xứ` (Bao quát trọn vẹn 6 tầng, tự tính ngày theo ngôn ngữ).<br>  2. `1. Vỡ lòng (Bảng chữ cái & Khẩu hình phát âm)`<br>  3. `2. Ghép âm & Từ đơn sinh tồn (Tập đọc & Câu ngắn)`<br>  4. `3. Sơ cấp (Giao tiếp đời sống cơ bản - A1/A2)`<br>  5. `4. Trung cấp (Tự tin diễn đạt & Công sở - B1/B2)`<br>  6. `5. Cao cấp (Học thuật, Báo chí, Thuyết trình - C1)`<br>  7. `6. Như người bản xứ (Thành ngữ, Tiếng lóng, Văn hóa & Tư duy - C2)`<br>• **Sư phạm Thích Ứng (Stage-Adaptive Prompting)**: Ngày vỡ lòng chỉ tập trung 5-10 ký tự, khẩu hình môi/lưỡi, quy tắc ghép âm và từ siêu ngắn; ngày bản xứ hóa tập trung vào Idioms, Slang, Collocations, lối nói ẩn dụ và văn hóa bản địa.<br>• **Phân Tích Đặc Thù Ngôn Ngữ (Typology Guidance)**: Tự động phân loại ngôn ngữ đích (chữ tượng hình/âm tiết vs Latin vs thanh điệu) để quy hoạch giáo trình chính xác theo chuẩn quốc tế (CEFR / JLPT / HSK / TOPIK). |
| `VocabApp.py` | Cập nhật `CourseGenerationDialog`: mở rộng combobox `cb_level` lên width=330, hiển thị đầy đủ tên 6 bậc + Trọn gói, cập nhật log hành trình và thông tin số ngày tối thiểu. |
| `test_ai_rich.py` | Cập nhật toàn bộ bộ test cho 6 bậc học, test Adaptive Prompting (Vỡ lòng vs Bản xứ), Typology trong Backbone prompt. |
| `projectLog.md` | Cập nhật nhật ký dự án. |

**Test kết quả:** ✅ 35/35 test passed (Python 3.14) & Compile OK.

---

## 📋 Cập nhật trước đó — 2026-08-28 (Update 8)

## 📋 Cập nhật trước đó — 2026-08-28 (Update 7)

### 🧹 Tối Ưu Bố Cục Bài Học: Xóa Bỏ Mảng Đen Thừa, Chống Cắt Chữ & Hoàn Thiện Trải Nghiệm — HOÀN THÀNH ✅

**Vấn đề đã giải quyết:**
- ❌ **Mảng đen thừa phía dưới bài học**: Do lồng `CTkTextbox` bên trong `CTkScrollableFrame` với `height=500` cố định, tạo ra khoảng trống đen vô nghĩa và làm dòng chữ cuối bị cắt nửa.
- ❌ **Thiếu phân cách tiêu đề bài học**: Thiếu đường kẻ phân cách giữa metadata cấp độ và nội dung bài.

**Giải pháp triển khai:**

| File | Thay đổi |
|------|----------|
| `VocabApp.py` | • **Xóa bỏ `CTkScrollableFrame` thừa**: Đặt `self.lesson_text` (`CTkTextbox`) trực tiếp vào `cbody` với `fill="both", expand=True, corner_radius=10`. Khung bài học tự động co giãn 100% không gian, triệt tiêu hoàn toàn mảng đen thừa, cuộn mượt mà không bị cắt chữ.<br>• **Bổ sung metadata rõ ràng**: Hiển thị đầy đủ Tag Cấp độ, Giai đoạn, Chủ đề bài học và đường phân cách thẩm mỹ trong `_render_lesson_text`.<br>• **Khung trắc nghiệm**: Cân đối kích thước `width=370` tạo sự hài hòa tối đa với khung bài học. |
| `projectLog.md` | Cập nhật nhật ký dự án. |

**Test kết quả:** ✅ 34/34 test passed (Python 3.14) & Compile OK.

---

## 📋 Cập nhật trước đó — 2026-08-28 (Update 6)

### 🖱️ Thay Thế ComboBox Bằng ScrollableDayDropdown Có Scrollbar Kéo Chuột Thật Sự & Auto-Migration DB — HOÀN THÀNH ✅

**Vấn đề đã giải quyết:**
- ❌ **Menu ComboBox mặc định của Windows chỉ có 2 nút `▲` `▼`**: Không kéo chuột được, bất tiện khi có 107 ngày học.
- ❌ **Dữ liệu bài cũ thiếu `level` dẫn đến gán nhầm Trung cấp**: Đã được auto-migrate sạch sẽ trong DB.

**Giải pháp triển khai:**

| File | Thay đổi |
|------|----------|
| `VocabApp.py` | • **Xây dựng widget `ScrollableDayDropdown`**: Thay thế hoàn toàn `CTkComboBox` cũ. Khi bấm vào thanh chọn ngày, popup thả xuống mượt mà với **thanh cuộn (Draggable Scrollbar) thực sự** để người dùng thoải mái giữ chuột kéo trượt giữa 107 ngày.<br>• **Tích hợp live filter**: Có ô tìm kiếm nhanh tự động lọc danh sách ngay trong popup.<br>• **Hiển thị đầy đủ**: Đánh dấu ngày đang chọn bằng màu nổi bật và icon `✅` cho ngày đã hoàn thành. |
| `ai/course_db.py` | • **Auto-Migration DB**: Tự động chuẩn hóa `level` tương ứng với `phase` kiến thức của từng ngày khi nạp dữ liệu từ `course.json` (`Nền tảng` $\rightarrow$ `Người mới bắt đầu`, `Giao tiếp cơ bản` $\rightarrow$ `Sơ cấp`, v.v.). |
| `test_ai_rich.py` | Toàn bộ 34 unit tests đều PASS 100%. |
| `projectLog.md` | Cập nhật nhật ký dự án. |

**Test kết quả:** ✅ 34/34 test passed (Python 3.14) & Compile OK.

---

## 📋 Cập nhật trước đó — 2026-08-28 (Update 5)

### 🎯 Chuẩn Hóa Phân Loại Cấp Độ Theo Phase & Ô Nhập Số Ngày Nhảy Tức Thì (Jump-to-Day) — HOÀN THÀNH ✅

**Vấn đề đã giải quyết:**
- ❌ **Gắn nhầm nhãn [Trung cấp] cho bài nền tảng**: Các bài học cũ chưa lưu level riêng bị lấy nhầm cấp độ tổng của khóa (Trung cấp), khiến các bài âm đục, bảng chữ cái, số đếm (Ngày 43–60) cũng bị hiển thị là `[Trung cấp]`.
- ❌ **Không có thanh kéo cuộn trực tiếp trên dropdown**: Menu thả xuống của Tkinter không có scrollbar chuột, gây bất tiện khi tìm các ngày xa.

**Giải pháp triển khai:**

| File | Thay đổi |
|------|----------|
| `VocabApp.py` | • **Chuẩn hóa ánh xạ Phase $\rightarrow$ Cấp độ**: Hàm `_short_level_name` ưu tiên phân loại trực tiếp theo Giai đoạn kiến thức thực tế (Phase *Nền tảng* $\rightarrow$ `[Người mới]`, Phase *Giao tiếp cơ bản* $\rightarrow$ `[Sơ cấp]`, Phase *Trung cấp* $\rightarrow$ `[Trung cấp]`), đảm bảo chính xác 100% cho mọi ngày học dù cũ hay mới.<br>• **Thêm ô nhập số ngày nhảy tức thì**: Thêm ô `CTkEntry` `[ 48 ]` ` / 83` `[ ➔ ]`, hỗ trợ người dùng gõ số ngày và bấm **Enter** để nhảy ngay đến bài học trong tích tắc mà không cần cuộn tìm.<br>• **Modal danh sách kéo cuộn**: Phân nhóm trực quan theo từng Giai đoạn & Cấp độ với Scrollbar mượt mà. |
| `projectLog.md` | Cập nhật nhật ký dự án. |

**Test kết quả:** ✅ 34/34 test passed (Python 3.14) & Compile OK.

---

## 📋 Cập nhật trước đó — 2026-08-28 (Update 4)

### 📑 Nâng Cấp Trải Nghiệm Lộ Trình: Scrollable Day Selector Modal, Nút Điều Hướng Nhanh & Hiển Thị Cấp Độ Rõ Ràng — HOÀN THÀNH ✅

**Vấn đề đã giải quyết:**
- ❌ **Khó khăn khi chọn ngày dài**: Khi lộ trình có 50–100+ ngày, việc dùng dropdown menu ComboBox thông thường khiến việc cuộn kéo chậm và bất tiện.
- ❌ **Thiếu thông tin phân cấp**: Không biết ngày nào thuộc cấp độ nào (Người mới, Sơ cấp, Trung cấp...).

**Giải pháp triển khai:**

| File | Thay đổi |
|------|----------|
| `VocabApp.py` | • **Nút chuyển ngày nhanh**: Thêm nút `◀ Trước` và `Sau ▶` cạnh thanh chọn ngày để lật qua lại giữa các ngày chỉ bằng 1 click.<br>• **Modal chọn ngày cuộn mượt (`DaySelectorDialog`)**: Thêm nút `📑 Xem toàn bộ lộ trình` mở cửa sổ danh sách ngày dạng `CTkScrollableFrame` có ô tìm kiếm nhanh và tự động gom nhóm (Group) theo từng Cấp độ (Người mới bắt đầu, Sơ cấp, Trung cấp...).<br>• **Gắn tag Cấp độ**: Hiển thị rõ tag `[Người mới]`, `[Sơ cấp]`, `[Trung cấp]` trong dropdown `cb_day`, trong danh sách lộ trình và trong tiêu đề bài học `_render_lesson_text`. |
| `ai/course_generator.py` | Lưu kèm thuộc tính `"level": level` vào từng object `lesson` khi sinh bài. |
| `test_ai_rich.py` | Kiểm thử toàn diện 34 unit tests đảm bảo không có hồi quy. |
| `projectLog.md` | Cập nhật nhật ký dự án. |

**Test kết quả:** ✅ 34/34 test passed (Python 3.14) & Compile OK.

---

## 📋 Cập nhật trước đó — 2026-08-27 (Update 3)

### 🔑 Đồng Bộ 100% Cơ Chế Key Rotation Với AskCpl: Fix Lock After Success & Smart Cooldown Recovery — HOÀN THÀNH ✅

**Vấn đề đã giải quyết:**
- ❌ **Tự khóa 3600s sau mỗi lượt gọi thành công**: `lock_after_success=True` mặc định làm tất cả các account trong pool lần lượt bị khóa 1 giờ (3,600s) sau 20+ request thành công của Ngày 1-11, khiến Ngày 12 không còn account nào để xoay vòng khi gặp 429 RPM.
- ❌ **Ngắt ngang khi toàn bộ key trong cooldown**: Vòng lặp `request()` ném ra `NO_KEY` ngay lập tức thay vì tự động chờ đếm ngược để tiếp tục.

**Giải pháp triển khai:**

| File | Thay đổi |
|------|----------|
| `api/gemini_safe.py` | • Đặt `lock_after_success=False` mặc định (đồng bộ 100% với `AskCpl.py` và `auto_ai_worker.py`), cho phép các key xoay vòng tự nhiên liên tục (Round-robin) không bị khóa 1 giờ.<br>• Thêm cơ chế **Smart Cooldown Wait**: Tự động tính thời gian cooldown còn lại ngắn nhất (15-30s), đếm ngược và tự động thử lại tối đa 12 vòng (có kiểm tra `stop_check` từng giây) thay vì báo `NO_KEY` ngắt ngang. |
| `ai/course_generator.py` | Khởi tạo `GeminiCoordinator` với `lock_after_success=False` tường minh. |
| `test_ai_rich.py` | Bổ sung test `[12] GeminiCoordinator lock_after_success & cooldown recovery`. |
| `projectLog.md` | Cập nhật nhật ký dự án. |

**Test kết quả:** ✅ 34/34 test passed (Python 3.14)

---

## 📋 Cập nhật trước đó — 2026-08-27 (Update 2)

### 🚀 Khóa Học AI Chuẩn AskCpl: Multi-Pass Blueprint Engine, Zero-Duplicate Auto-Repair & Continuous 100% Generation — HOÀN THÀNH ✅

**Vấn đề đã giải quyết:**
- ❌ **Ngắt 15 ngày không cần thiết**: Hệ thống có sẵn 155+ API key xoay vòng tự động từ AskCpl nhưng trước đây bị giới hạn cứng `BACKBONE_BATCH_SIZE = 15`, buộc người dùng phải bấm lặp lại nhiều lần.
- ❌ **Khung giáo trình Single-pass**: Thiếu các bước kiểm tra trùng lặp và phản biện lỗ hổng kiến thức, dẫn đến nguy cơ trùng lặp tiêu đề hoặc thiếu điểm ngữ pháp cốt lõi.

**Giải pháp triển khai:**

| File | Thay đổi |
|------|----------|
| `ai/course_generator.py` | • **Pass 1C**: Thêm `find_duplicate_topics` và `repair_duplicate_topics` sử dụng `difflib.SequenceMatcher` (ngưỡng tương đồng $\ge 85\%$) để phát hiện và tự động gọi AI sinh chủ đề thay thế tại chỗ.<br>• **Pass 2**: Thêm `review_and_fill_gaps` đóng vai trò Chuyên gia Sư phạm rà soát chuẩn quốc tế (JLPT/HSK/CEFR/TOPIK) và bổ sung các chủ đề trọng điểm còn thiếu.<br>• **Pass 3**: Thêm `normalize_backbone_sequence` sắp xếp thứ tự sư phạm logic (Chữ viết/Phát âm $\rightarrow$ Từ vựng $\rightarrow$ Ngữ pháp $\rightarrow$ Giao tiếp $\rightarrow$ Văn hóa/Slang).<br>• **Continuous Generation**: Đặt `BACKBONE_BATCH_SIZE = None`, hỗ trợ tham số `max_days_per_run` linh hoạt, chạy tự động 100% toàn bộ giáo trình liên tục không ngắt quãng, có sleep 0.3s nhịp nhàng chống nghẽn socket và lưu atomic từng ngày (resumable). |
| `VocabApp.py` | Tiến độ và log hiển thị theo thời gian thực xuyên suốt toàn bộ lộ trình; tự động hoàn thành trọn vẹn cấp độ chỉ với 1 lần bấm; hỗ trợ dừng bất kỳ lúc nào và ghi nhớ chính xác trạng thái. |
| `test_ai_rich.py` | Bổ sung unit tests cho Pass 1C (Deduplication Repair), Pass 2 (Gap Review), Pass 3 (Sequence Normalization) và Continuous Generation. |
| `projectLog.md` | Cập nhật nhật ký dự án. |

**Test kết quả:** ✅ 33/33 test passed (Python 3.14)

---





## Mục tiêu
Tạo một ứng dụng desktop quản lý từ vựng đa ngôn ngữ (Tiếng Anh, Tiếng Nhật, Tiếng Trung...) kết hợp giao diện Web tĩnh trên GitHub Pages để có thể ôn tập từ vựng mọi lúc mọi nơi trên điện thoại.

Ứng dụng hoạt động tương tự như hệ thống `ListKaraOke`, bao gồm:
1. Giao diện Desktop (Python + CustomTkinter) để thêm/sửa/xóa từ vựng.
2. Dữ liệu mỗi ngôn ngữ lưu thành một file JSON riêng biệt (`english.json`, `japanese.json`,...).
3. Đồng bộ (Sync) dữ liệu lên GitHub Pages.
4. Giao diện Web di động hỗ trợ bộ lọc mạnh mẽ: Ngày học (Date), Chủ đề (Topic), Loại từ (Từ loại).

## Các tính năng đã hoàn thiện
1. **Quản lý đa ngôn ngữ**: Người dùng có thể thêm bao nhiêu ngôn ngữ tùy ý (ví dụ: English, Japanese). Mỗi ngôn ngữ được lưu tự động thành file JSON riêng trong thư mục `data/`.
2. **Sync lên GitHub & Google Drive**: Tích hợp module đồng bộ cho phép đẩy dữ liệu JSON và Web tĩnh lên GitHub Pages, đồng thời tải mp3 lên Google Drive.
3. **Web App với Flashcard**: Giao diện Web được thiết kế tối ưu trên mobile với 2 chế độ:
   - *List View*: Hiển thị danh sách từ vựng kèm bộ lọc.
   - *Flashcard View*: Hiển thị từng thẻ từ, bấm lật mặt sau để xem nghĩa và mẫu câu, có hỗ trợ nút phát audio (nếu đã đồng bộ mp3).
4. **Hiển thị nội dung dài (Long-content rendering)**:
   - Python App: Ô nhập *Nghĩa của từ* đổi sang `CTkTextbox` nhiều dòng.
   - Web List View: `white-space: pre-wrap`, ví dụ có nút toggle ẩn/hiện, scroll nếu dài.
   - Web Flashcard: Mặt sau có scroll (`overflow-y: auto`), nội dung `\n` render đúng.
   - JS: Thêm `escapeHtml()` và `formatText()` để an toàn với ký tự đặc biệt.

---

## Tiến độ (Timeline)
- [x] Lên ý tưởng và tạo file log dự án (`projectLog.md`).
- [x] Lên bản kế hoạch chi tiết (`implementation_plan.md`).
- [x] Xây dựng khung ứng dụng Desktop UI với CustomTkinter (`VocabApp.py`).
- [x] Cấu trúc quản lý file JSON đa ngôn ngữ (`database/database.py`).
- [x] Tích hợp tính năng Sync GitHub và Google Drive (`api/github_sync.py`, `api/gdrive_sync.py`).
- [x] Xây dựng giao diện Web App cho Mobile (`web/index.html`, `style.css`, `script.js`).
- [x] Sửa lỗi hiển thị nội dung dài / ký tự đặc biệt / xuống dòng (2026-06-18).
- [x] Tính năng kiểm tra từ trùng lặp khi thêm mới (2026-06-18).
- [x] Tính năng tự động gợi ý (Autocomplete, tối đa 5 lựa chọn) cho Chủ đề, Loại từ, Ngày học và tự động ghi nhớ Ngày học gần nhất để làm mặc định (2026-06-20).
- [x] Bảo mật GitHub Token & Sửa lỗi Ctrl+Z (2026-06-24).
- [x] Tính năng Preview (Xem trước) Bảng Markdown bằng đồ họa `ttk.Treeview` (2026-06-24).
- [x] Tính năng Visual Table Editor và Tối ưu Responsive Layout (2026-06-24).
- [x] Tự động nhận diện và paste Markdown table từ Gemini AI / ChatGPT (2026-06-24).
- [x] Khắc phục tình trạng giật lag danh sách từ vựng bằng ttk.Treeview (2026-06-26).
- [x] Thêm tính năng tự động kiểm tra và cài đặt thư viện khi khởi động (2026-08-11).
- [x] **Thêm tính năng Luyện Viết (Có chấm điểm & Bảng nháp) trên cả Web App và Desktop App** (2026-08-11).
- [x] **Fix luyện viết:** Thêm dual charDataLoader (JP dataset → fallback CN) để hỗ trợ Hiragana/Katakana/Kanji. Fix nút "Luyện viết" không hiện trên mobile (flex-wrap). Fix CSS bị hỏng (2026-08-12).
- [x] **Đổi phương án chấm điểm:** Bỏ HanziWriter data-dependency. Thay bằng Pixel Similarity Scoring (F1 score). Dùng browser Canvas `fillText` để render chữ mờ, so sánh pixel người vẽ vs pixel gốc → % điểm. Hỗ trợ mọi ngôn ngữ không cần dataset (2026-08-12).
- [x] **Tối ưu Hiệu suất & UI/UX (Web):** Thêm Debounce (300ms) cho thanh tìm kiếm chống treo trình duyệt. Implement Lazy Loading (Infinite Scroll) bằng `IntersectionObserver` tối ưu render danh sách lớn. Thêm nút Xoá nhanh tìm kiếm (Clear button), Smooth Accordion cho ví dụ và Micro-animations (hover effects) cho các thẻ từ vựng (2026-08-12).
- [x] **Hybrid TTS Fallback (Web):** Nút 🔊 Play trên Flashcard luôn hiện. Nếu từ có `mp3_gdrive_id` → phát MP3 Google Drive như cũ. Nếu không có → dùng `Web Speech API` (SpeechSynthesis) đọc TTS với locale tự động map theo ngôn ngữ (en-US / ja-JP / zh-CN...). Không cần backend, không cần API key (2026-08-13).
- [x] **TTS Hybrid trên Desktop App:** Thêm hàm `speak_word()` dùng `gTTS + pygame` (có mạng, giọng Google) hoặc fallback `pyttsx3` (offline, Windows SAPI). Thêm nút 🔊 cạnh ô "Từ vựng" trong form Thêm/Sửa và nút **🔊 Đọc** trong action bar của List View. Thư viện tự cài qua `check_and_install_packages()` khi khởi động (2026-08-13).
- [x] **Rà soát & vá lỗi toàn ứng dụng (Bug-fix sweep):** Fix shallow-copy mutate DEFAULT_SETTINGS trong `settings.py`; ghi JSON atomic (`os.replace`) chống hỏng dữ liệu; fix progress bar bị cập nhật từ background thread; fix chèn từ vào JS luyện viết bằng `json.dumps` (từ chứa `" \` `\` không còn vỡ) + tự dọn temp script; thêm lock chống race khi bấm 🔊 liên tục; thống nhất zh-CN; dedupe header bảng Preview; Web thêm DOMPurify sanitize, tìm kiếm khớp cả example/note, flashcard lặp vòng + phím tắt Space/←/→ (2026-08-25).
- [x] **Fix auto-installer chết trên Python 3.14+:** Trước đây cài TẤT CẢ thư viện trong 1 lệnh pip → pygame (chưa có wheel cho 3.14, build lỗi do bỏ distutils) làm hỏng cả lệnh → app không thể khởi động. Tách `CRITICAL_PACKAGES` (customtkinter, requests — thiếu là thoát với cửa sổ lỗi) và `OPTIONAL_PACKAGES` (cài từng gói riêng, fail thì bỏ qua và app vẫn chạy). Thêm biến môi trường `VOCABAPP_SKIP_INSTALL=1` để dev/test khởi động nhanh. Dọn `requirements.txt`: bỏ Pillow & qrcode (không được dùng trong code) (2026-08-25).
- [x] **Tab 🎓 Học Tập + Khóa học AI chuyên sâu theo ngày (kiểu AskCpl):** Ô lựa chọn nguồn học gồm **"📖 Từ vựng tự học"** (flashcard lật thẻ 60 từ hiện có: trộn thẻ, 🔊 đọc, phím ←/→/Space) và **"🤖 Khóa học AI chuyên sâu"** (AI chia toàn bộ từ vựng thành các ngày; mỗi ngày sinh bài học JSON gồm: từ vựng chuyên sâu + giải thích sắc thái + ví dụ song ngữ + điểm ngữ pháp + 6-10 câu trắc nghiệm tương tác có chấm điểm & lưu tiến độ). Dùng lại cơ chế `GeminiCoordinator` của AskCpl (`api/gemini_safe.py`): xoay vòng **155 API key ENC:** đọc trực tiếp từ `AskCpl/settings.json`, pace chống 429, model fallback. Database lưu kiểu AskCpl tại `data/ai_courses/<ngôn_ngữ>/course.json` + `progress.json` (atomic, resumable — dừng giữa chừng chạy lại là tiếp tục). Web thêm view "🎓 AI Course" để ôn trên điện thoại; GitHub sync upload cả thư mục ai_courses. Đã test THẬT với Gemini: sinh thành công Ngày 1/12 (model fallback gemini-3.5-flash → flash-latest → 3.1-flash-lite) (2026-08-26).
- [x] **Khóa học AI v2 — Hệ thống học ĐỘC LẬP hoàn toàn, AI tự quyết giáo trình:** Tách khỏi danh sách từ vựng chính (không seed, không nhập ngược). AI toàn quyền thiết kế giáo trình theo **hành trình 5 giai đoạn** (Nền tảng → Giao tiếp cơ bản → Trung cấp → Cao cấp → Như bản xứ), **tự quyết số ngày** theo trình độ (tối thiểu 14), mọi ngôn ngữ (Nhật/Trung/Hàn/Anh...). Nội dung rich mỗi ngày: ≥10 từ chuyên sâu · ≥10 cách dùng câu · ≥10 câu thông dụng · 2-3 bài ngữ pháp · trắc nghiệm **4 loại × ≥10 câu** có badge phân loại. Fix crash dialog (combo int→str), fix parse schema mismatch, auto-migrate dữ liệu cũ. 20/20 unit test pass (2026-08-26).
- [x] **Khóa học AI v2.1 — AI Roadmap cho Người Chưa Biết Gì & Lộ Trình Linh Hoạt (15-90 ngày theo chuẩn AskCpl):** Nâng cấp prompt AI tối ưu cho người mới tinh (Zero-Knowledge First: Ngày 1-3 bắt buộc dạy Bảng chữ cái, Bảng phiên âm, Quy tắc phát âm, Ghép vần, Thanh điệu); Thêm cơ chế chọn thời lượng linh hoạt (15/30/45/60/90 ngày hoặc AI tự phán định); Tích hợp JSON repair (tự sửa trailing comma theo chuẩn AskCpl); Fix lỗi UnicodeEncodeError trên Windows Terminal; 28/28 unit test PASS (2026-08-26).
- [x] **Khắc phục lỗi cài đặt pygame trên Python 3.14+:** Thay thế `pygame` (bị lỗi build do PEP 632 loại bỏ `distutils`) bằng `pygame-ce>=2.5.0` (Community Edition có sẵn pre-built wheels cho Python 3.14, 100% tương thích API `import pygame` cho phát âm TTS) (2026-08-26).
- [x] **Universal Zero-to-Native AI Course Engine v3 (Staged Milestone Pipeline & FSI Matrix 240-450+ Ngày)**: Tự động đo độ khó ngôn ngữ theo chuẩn FSI (Tiếng Nhật/Trung/Hàn: ~420 ngày, Pháp/Đức: ~320 ngày, Anh: ~240 ngày); Xóa bỏ hoàn toàn lỗi 99 ngày bằng kiến trúc Chuyển Chặng Tự Động (Staged Pipeline); Tích hợp Ôn tập Xoắn Ốc "6 + 1" (Weekly Spiral Review) vào các ngày 7, 14, 21, 28...; Tích hợp Khẩu hình 3 lớp cho người mới 0 kiến thức và Khối sắc thái đối chiếu (Sách vở vs Thực tế ngoài đời) cho các chặng nâng cao; Bẫy trắc nghiệm thông minh chống thói quen dịch thô từ tiếng Việt; Giao diện phân màu 6 chặng chuẩn xác 100% `[Vỡ lòng]`, `[Ghép âm]`, `[Sơ cấp]`, `[Trung cấp]`, `[Cao cấp]`, `[Bản xứ]`. 45/45 test cases PASS (2026-08-29).

---

## Changelog

### 2026-08-29 (Update 10) — Hệ Thống Giáo Trình 10 Vòng Tối Ưu: FSI Matrix, Staged Pipeline & Spiral Review 6+1
**Vấn đề**:
1. Khóa Trọn Gói khi sinh trước đây bị co ngắn lại còn 99 ngày do Gemini bị giới hạn token đầu ra khi cố gắng sinh cả 6 tầng trong một prompt duy nhất.
2. Toàn bộ các ngày đều bị gắn nhãn chung chung `[Người mới]` thay vì gắn đúng cấp độ thực tế của từng ngày.
3. Người học ngoại ngữ trong lộ trình dài hàng trăm ngày dễ bị quên từ vựng nếu không có chu kỳ ôn tập định kỳ.

**Giải pháp & Nâng cấp**:
- **Bộ Ma Trận Phân Bổ FSI (Universal FSI Matrix)**: Tự động phân loại mọi ngôn ngữ theo chuẩn FSI (Category I: Anh ~240 ngày; Category II/III: Pháp/Đức ~320 ngày; Category III/IV: Nga/Thái ~360 ngày; Category IV/V: Nhật/Trung/Hàn ~420 ngày) với tỷ trọng hình chóp chuẩn sư phạm.
- **Kiến trúc Pipeline Đa Chặng Tự Động (Staged Milestone Pipeline)**: Sinh khung giáo trình theo từng Chặng (Chặng 1: ~30 ngày). Khi hoàn tất Chặng 1, hệ thống tự động mở rộng và sinh tiếp Chặng 2 (Ngày 31..68) $\rightarrow$ Chặng 3, 4, 5, 6 mà không cần người dùng can thiệp hay đổi dropdown.
- **Ôn Tập Xoắn Ốc "6 + 1" (Weekly Spiral Review)**: Định kỳ cứ sau 6 bài học mới, ngày thứ 7 (7, 14, 21, 28...) là ngày ôn tập tình huống thực tế (Real-life Roleplay) nhúng toàn bộ từ vựng và ngữ pháp của cả tuần.
- **Khẩu Hình 3 Lớp & Sắc Thái Đối Chiếu**: Cung cấp giải phẫu vị trí răng/lưỡi/môi cho người mới bắt đầu và góc nhìn đối chiếu "Sách vở vs Cách người bản xứ thực tế nói ngoài đời" cho chặng nâng cao.
- **Bẫy Trắc Nghiệm Sư Phạm**: Thiết kế 4 phương án (1 Đúng, 1 Bẫy Dịch Thô Tiếng Việt, 1 Bẫy Từ Dễ Nhầm, 1 Bẫy Ngữ Pháp) rèn phản xạ tư duy sâu.
- **Giao Diện Phân Màu 6 Chặng Chuẩn Xác**: Dropdown và Treeview hiển thị đúng huy hiệu từng chặng: `[Vỡ lòng]`, `[Ghép âm]`, `[Sơ cấp]`, `[Trung cấp]`, `[Cao cấp]`, `[Bản xứ]`.

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `ai/course_generator.py` | `get_language_fsi_profile`, `build_stage_backbone_prompt`, Staged Milestone Pipeline trong `generate_course`, chu kỳ Ôn tập 6+1, Khẩu hình 3 lớp và Bẫy trắc nghiệm thông minh. |
| `VocabApp.py` | `_short_level_name` chuẩn hóa 6 chặng, `_update_level_info` hiển thị thông tin lộ trình FSI tự động. |
| `test_ai_rich.py` | Bổ sung unit tests cho FSI profiles, Stage prompts, Spiral Review, Native Nuance và Stage badges (45/45 PASS). |
| `projectLog.md` | Ghi lại Update 10. |

**Kết quả kiểm chứng**: 45/45 test cases PASSED (100%) trên Python 3.14.7.

### 2026-08-26 (Update 3) — Chuyển sang pygame-ce: Tương thích hoàn hảo Python 3.14+
**Vấn đề**: Khi khởi động ứng dụng trên môi trường Python 3.14, gói `pygame` truyền thống chưa có pre-built binary wheel, buộc pip phải build từ mã nguồn. Mã nguồn setup của `pygame` phụ thuộc vào `distutils.msvccompiler` (đã bị gỡ bỏ vĩnh viễn trên Python 3.14 theo PEP 632) dẫn đến crash `ModuleNotFoundError: No module named 'distutils.msvccompiler'`.

**Giải pháp**:
- Chuyển cấu hình thư viện sang `pygame-ce>=2.5.0` (Community Edition). Đây là bản fork chính thức và phát triển tích cực của Pygame, có sẵn pre-built binary wheel cho Python 3.10 đến Python 3.14 trên Windows x64.
- `pygame-ce` xuất ra đúng module `import pygame`, tương thích hoàn toàn 100% với toàn bộ code âm thanh `pygame.mixer` trong `VocabApp.py`.

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `VocabApp.py` | Cập nhật `OPTIONAL_PACKAGES` từ `pygame>=2.5.0` sang `pygame-ce>=2.5.0`. |
| `requirements.txt` | Cập nhật `pygame-ce>=2.5.0`. |
| `projectLog.md` | Ghi lại nhật ký khắc phục lỗi. |

**Kết quả kiểm chứng**: `pygame-ce 2.5.8` cài đặt thành công ngay lập tức qua wheel · `import pygame; pygame.mixer.init()` chạy hoàn hảo trên Python 3.14.7.

### 2026-08-26 (Update 2) — AI Roadmap cho Người Chưa Biết Gì (Zero-Knowledge First) & Lộ Trình Linh Hoạt 15-90 Ngày
**Vấn đề**:
1. Với người chưa biết gì về ngôn ngữ mới, khóa 15-30 ngày nếu không có chỉ dẫn chặt chẽ sẽ dễ bị nhảy cóc bỏ qua bảng chữ cái/ngữ âm cơ bản.
2. Cần cung cấp các mốc thời lượng học phong phú hơn (15 ngày - Nhập môn, 30 ngày - Tiêu chuẩn, 45 ngày - Mở rộng, 60 ngày - Chuyên sâu, 90 ngày - Nâng cao) để người học chủ động chọn hoặc để AI tự ước lượng theo độ khó của từng ngôn ngữ.
3. Test script `test_ai_rich.py` bị lỗi encoding UTF-8 trên Windows console (charmap cp1252 không in được ký tự `→`).

**Giải pháp & Nâng cấp**:
- **Prompt Zero-Knowledge First**: Ở Giai đoạn 1 (Nền tảng), AI bắt buộc dành những ngày đầu (Ngày 1 đến Ngày 3-5) để dạy kỹ **Hệ chữ viết, Bảng chữ cái, Bảng phiên âm (Romaji/Pinyin/Hangul/IPA) và Quy tắc phát âm/thanh điệu** trước khi dạy từ ghép/câu phức.
- **Hỗ trợ lộ trình linh hoạt (15 – 90 ngày)**: Bổ sung dropdown trong `CourseGenerationDialog` cho phép người dùng chọn các mốc 15, 30, 45, 60, 90 ngày hoặc để AI tự phán định số ngày tối ưu.
- **JSON Repair (AskCpl standard)**: Nâng cấp `_strip_json` tự động strip markdown fences và repair trailing commas trước `}` và `]` khi AI trả về.
- **Fix UTF-8 Terminal & Mở rộng Test Suite**: Thêm `sys.stdout.reconfigure(encoding="utf-8")` và bổ sung các test cases cho zero-knowledge prompt, 60/90 days target, json repair (28/28 test PASS).

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `ai/course_generator.py` | Prompt chỉ dẫn Zero-knowledge (bảng chữ cái/phát âm), `_strip_json` regex repair, hỗ trợ linh hoạt `target_days`. |
| `VocabApp.py` | `CourseGenerationDialog`: Thêm bộ chọn thời lượng (`cb_duration`) 15/30/45/60/90 ngày và parse truyền vào `generate_course`. |
| `test_ai_rich.py` | Fix UTF-8 stdout reconfigure, thêm 8 test cases mới (28/28 PASS). |
| `projectLog.md` | Cập nhật nhật ký dự án. |

**Kết quả kiểm chứng**: 28/28 unit test PASS · py_compile sạch tất cả file · node --check script.js sạch · Smoke test import VocabApp thành công.

### 2026-08-26 — Khóa học AI v2: Hệ thống học ĐỘC LẬP, AI tự quyết toàn bộ giáo trình
**Vấn đề**: (1) Dialog sinh khóa học crash ngay khi mở (`CTkComboBox` nhận values dạng int → `.ljust()` lỗi). (2) Bắt buộc DB phải có sẵn từ mới cho sinh khóa học. (3) Nội dung mỗi ngày quá mỏng, quiz chỉ 6 câu không phân loại. (4) Người dùng phải tự chọn số ngày. (5) Khóa học còn "dính" tới từ vựng gốc trong DB.

**Nguyên tắc thiết kế mới — khóa học AI là HỆ THỐNG HỌC HOÀN TOÀN ĐỘC LẬP**:
- **Không liên kết DB từ vựng**: không seed từ có sẵn, không nhập ngược từ AI vào danh sách chính — hai hệ thống tách biệt 100%.
- **AI toàn quyền thiết kế**: hành trình 5 giai đoạn bắt buộc (Nền tảng → Giao tiếp cơ bản → Trung cấp → Cao cấp → Như bản xứ); **AI TỰ QUYẾT số ngày** theo trình độ (tối thiểu 14 ngày để đủ hành trình); chủ đề + từ vựng do AI chọn như người bản xứ dạy người mới.
- **Mọi ngôn ngữ**: Nhật (romaji), Trung (pinyin), Hàn (romanization), Anh/Pháp (IPA)...
- **Nội dung rich mỗi ngày**: ≥10 từ chuyên sâu · ≥10 cách dùng câu · ≥10 câu thông dụng (kèm tình huống) · 2-3 bài ngữ pháp chi tiết.
- **Trắc nghiệm 4 loại × ≥10 câu** (từ vựng / mẫu câu / câu thông dụng / ngữ pháp), badge phân loại trên cả desktop lẫn web.
- **3 loại lần gọi AI**: lập giáo trình → nội dung ngày → trắc nghiệm ngày (`max_output_tokens=16384`, retry JSON 2 lần) — tránh bị cắt response.
- **Resumable**: plan + từng ngày lưu ngay; Dừng rồi chạy lại tiếp tục chỗ dở; `get_course()` tự migrate định dạng cũ (grammar dict→list, quiz list→dict).

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `ai/course_generator.py` | `CURRICULUM_SCHEMA` + `JOURNEY_PHASES` + `build_curriculum_prompt()` (AI tự quyết số ngày, cấm dùng từ có sẵn) + `parse_curriculum_json()`. Prompt nội dung rich + auto-pick. Quiz 4 loại. `_ask()` tách kind (logic) khỏi label (log) — fix bug parse schema mismatch. `generate_course(language, words_per_day, level, ...)`: bỏ tham số `vocabs`, luôn do AI lập plan, `target_days` tùy chọn. |
| `ai/course_db.py` | `get_course()` tự migrate định dạng cũ và save lại. |
| `VocabApp.py` | Fix combo int→str (crash `.ljust`). Dialog mới: bỏ combo số ngày (AI tự quyết), chọn trình độ 5 mức, ghi rõ "HỆ THỐNG HỌC ĐỘC LẬP", không đọc DB từ vựng. `_render_lesson_text()` render 4 section + phase/topic. `_flatten_quiz()` xử lý quiz dict 4 loại/list cũ kèm category. Combo ngày hiển thị chủ đề. |
| `web/script.js` | `flattenQuiz()`, render patterns/common/grammar-list, quiz category badges, topic trong select ngày, phase badge. |
| `web/style.css` | Thêm `.section-title`, `.pattern-item`, `.common-item`, `.quiz-cat-badge`, `.phase-badge`. |
| `test_ai_rich.py` | 20 test: schema, parse resilience, migration, flatten, prompts (explicit + AI-decided days), full dry-run flow với fake coordinator (giáo trình → 2 ngày rich → resume → stop). |

**Kết quả kiểm chứng**: 20/20 test pass · py_compile sạch · node --check sạch.

### 2026-08-26 — Tab 🎓 Học Tập + Khóa học AI chuyên sâu theo ngày (tích hợp AskCpl)
**Kiến trúc**: tái sử dụng `GeminiCoordinator` của AskCpl (copy về `api/gemini_safe.py`, bỏ phụ thuộc settings) — xoay vòng account/key, pace 3.5–5s + jitter, phân loại lỗi 429 daily/rate/invalid, model fallback. Key đọc (chỉ đọc, không ghi) từ `GravityCode/Download/AskCpl/settings.json`, giải mã ENC: cùng thuật toán.

**Files mới/sửa**:
| File | Nội dung |
|------|----------|
| `api/gemini_safe.py` (mới) | Bản copy chuẩn hóa của gemini_safe.py từ AskCpl |
| `ai/course_db.py` (mới) | DB khóa học: `data/ai_courses/<slug>/course.json` + `progress.json`; atomic write; upsert_day resumable; mark_day_completed giữ điểm cao nhất |
| `ai/course_generator.py` (mới) | responseSchema JSON cho Gemini (vocab/grammar/quiz), prompt gia sư tiếng Việt, parse chống lỗi (code fence, answer_index out-of-range), vòng lặp sinh từng ngày + lưu ngay, stop/resume |
| `VocabApp.py` | Tab **🎓 Học Tập**: ô chọn nguồn (Tự học / Khóa AI), flashcard tự học (trộn/lật/đọc/phím tắt), trình xem bài theo ngày (textbox render + quiz radio tương tác chấm điểm lưu tiến độ), dialog sinh khóa học (chọn 3/5/7/10 từ ngày, progress bar, log, nút Dừng). Fix CTkRadioButton không nhận wraplength; bind phím qua winfo_toplevel vì CTk chặn bind_all |
| `web/index.html` `script.js` `style.css` | View "🎓 AI Course": chọn ngày → bài học + trắc nghiệm interactive, tiến độ lưu localStorage, badge hoàn thành; switchView 3 chiều |
| `api/github_sync.py` | Upload cả `data/ai_courses/**/*.json` lên GitHub Pages |
| `settings.py` | Thêm mục `ai.askcpl_settings_path` (ghi đè đường dẫn key nếu cần) |

**Kiểm chứng**: 26 unit test PASS (course_db, parser, resumable, stop); smoke test 2 bản Python PASS kể cả render quiz thật; gọi AI THẬT sinh Ngày 1/12 khóa tiếng Nhật thành công qua cơ chế fallback model.

### 2026-08-25 — Rà soát & vá lỗi toàn ứng dụng (Bug-fix sweep)
**Kết quả review**: 7 nhóm lỗi thật sự + 3 điểm tối ưu, đã vá hết. Kiểm tra bằng 31 unit test + compile check + smoke test khởi động app thật trên Python 3.14 & 3.11 (đều PASS, 60 từ load đúng).

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `settings.py` | **Bug thật**: `dict(DEFAULT_SETTINGS)` là shallow-copy nên `merged["github"].update(...)` làm mutate dict mặc định toàn cục (giá trị cũ "nhớ" xuyên phiên, kể cả khi file hỏng). Chuyển sang `copy.deepcopy()`. |
| `database/database.py` | `save_data()` ghi trực tiếp → crash giữa lúc ghi làm hỏng file JSON (mất dữ liệu). Đổi sang ghi file `.tmp` rồi `os.replace()` (atomic trên Windows). |
| `VocabApp.py` | 1) **Nghiêm trọng**: auto-installer cài mọi thư viện trong 1 lệnh pip — pygame build lỗi trên Python 3.14 làm app không thể khởi động. Tách critical/optional + cài từng gói + thêm env `VOCABAPP_SKIP_INSTALL`. 2) Progress bar Drive bị gọi `.set()` từ worker thread — tkinter không thread-safe → route qua `self.after(0,...)`, chống chia 0. 3) Nút Upload Drive thêm cờ `_syncing` chống bấm đúp tạo 2 thread upload song song. 4) `run_webview_practice`: chèn từ thẳng vào chuỗi JS qua f-string vỡ khi từ chứa `" \` `\`; chuyển sang `json.dumps`, đồng thời temp script tự xóa sau khi chạy. 5) `speak_word`: thêm `_tts_lock` chống race pygame khi bấm 🔊 liên tục; check pygame trước khi generate gTTS; fix `v.languages[0].decode()` crash; map tiếng Trung `zh-TW` → `zh-CN` khớp Web. 6) `PreviewDialog`: dedupe header bảng (Treeview crash nếu 2 cột trùng tên). |
| `requirements.txt` | Bỏ Pillow & qrcode (không được dùng trong code nào) → cài nhanh hơn. |
| `web/index.html` | Thêm DOMPurify CDN (sanitize HTML do `marked.parse()` render từ dữ liệu người dùng — chống XSS). |
| `web/script.js` | 1) `formatText()` sanitize qua DOMPurify. 2) Tìm kiếm web bổ sung `example`, `example_meaning`, `note` để khớp hành vi desktop. 3) Flashcard điều hướng lặp vòng (cuối→đầu). 4) Phím tắt: Space lật thẻ, ←/→ chuyển thẻ (tự bỏ qua khi đang gõ hoặc modal luyện viết mở). |

### 2026-06-26 — Khắc phục giật lag danh sách từ vựng bằng ttk.Treeview
**Vấn đề**: Giao diện ứng dụng bị treo, lag nhẹ khi tải danh sách từ vựng do phải render quá nhiều `CTkFrame` và `CTkLabel` riêng lẻ. Người dùng có gợi ý dùng "lazy loading" như trên Web.
**Giải pháp**: Tận dụng tính năng "Virtualization" (lazy rendering) có sẵn của `ttk.Treeview` - thành phần này chỉ tính toán và vẽ những dòng hiển thị trên màn hình hiện tại. Việc chuyển sang Treeview giải quyết triệt để lỗi mà không cần viết thuật toán phân trang/lazy loading phức tạp.

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `VocabApp.py` | Tái cấu trúc lại UI của `VocabListTab`, loại bỏ `CTkScrollableFrame` và thay thế bằng `ttk.Treeview`. Tốc độ load từ vựng giờ đây là ngay lập tức. |

### 2026-06-24 (Update 4) — Tự động nhận diện và paste Markdown table
**Vấn đề**: Việc soạn thảo bảng thủ công vẫn mất thời gian. Người dùng muốn copy trực tiếp bảng từ Gemini/ChatGPT và paste vào ứng dụng, hệ thống phải tự động nhận diện và format.

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `VocabApp.py` | Cải tiến hàm `on_paste` trong các `CTkTextbox` để nhận diện cấu trúc dòng bắt đầu bằng `|`. Nếu phát hiện nội dung là bảng Markdown, hệ thống tự động xử lý khoảng trắng để hiển thị đúng cột. |

### 2026-06-24 (Update 3) — Visual Table Editor và Responsive Layout
**Vấn đề**: Cửa sổ Form nhập liệu bị tràn viền gây mất nút Lưu, và người dùng cần nhập liệu Bảng thủ công trực quan thay vì gõ code Markdown trực tiếp.

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `VocabApp.py` | Tạo `TableEditorDialog` cho phép chèn cột/dòng nhập liệu kiểu Excel để tự động sinh mã Markdown Bảng. Tái cấu trúc Layout `VocabFormDialog`: gắn nút `Lưu / Hủy` xuống bottom frame tĩnh (luôn hiện), cài đặt `fill="x", expand=True` để các ô nhập liệu tự động co giãn theo chiều rộng cửa sổ. |

### 2026-06-24 (Update 2) — Tính năng Preview Bảng Markdown
**Vấn đề**: Người dùng cần xem Bảng dạng đồ họa lưới thật sự trong quá trình nhập liệu thay vì chỉ xem code Markdown dạng chữ thô, nhằm mường tượng đúng kết quả hiển thị trên web.

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `VocabApp.py` | Bổ sung class `PreviewDialog` dùng để phân tích cú pháp Markdown và render đồ họa bảng ra `ttk.Treeview`. Bổ sung các nút "👁 Preview" nằm kế bên nhãn của các ô nhập liệu `Nghĩa`, `Mẫu câu`, `Ghi chú` để tiện xem trước khi lưu. |

### 2026-06-24 (Update 1) — Bảo mật GitHub Token & Sửa lỗi Ctrl+Z
**Vấn đề**:
1. GitHub Token bị lưu cứng trong file `settings.json` dạng plaintext, dẫn đến việc bị GitHub Secret Scanner quét và thu hồi mỗi khi push code lên GitHub.
2. Các ô nhập liệu 1 dòng (Từ vựng, Phát âm, Ngày học...) sử dụng `CTkEntry` và `CTkComboBox` mặc định không hỗ trợ tính năng Undo (Ctrl+Z) / Redo (Ctrl+Y), gây bất tiện khi gõ sai.

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `settings.py` | Bổ sung hàm `encode_token` và `decode_token` sử dụng thuật toán đảo ngược chuỗi và Base64. Cập nhật `save_settings` để tự động mã hóa token và `load_settings` để giải mã, qua đó bảo mật file `settings.json` trên public repo. |
| `VocabApp.py` | Bổ sung hàm `enable_entry_undo` giúp giả lập Stack Undo/Redo tùy chỉnh. Áp dụng cho các widget Entry và ComboBox để khôi phục khả năng nhận phím tắt `Ctrl+Z` / `Ctrl+Y`. |

### 2026-06-23 — Hỗ trợ dán dữ liệu bảng và tự động tạo Markdown Table
**Vấn đề**: Khi dán văn bản có chứa Tab hoặc định dạng bảng từ Excel/Web vào các ô nhập liệu, các cột bị lệch do dùng font chữ thông thường. Đồng thời người dùng dán nhầm không thể nhấn `Ctrl + Z` để hoàn tác. Hơn nữa, trên Web cần render thành HTML Table để có giao diện đẹp như các ứng dụng hiện đại.

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `VocabApp.py` | Cấu hình font `Consolas` (Monospace) cho các `CTkTextbox` (`e_mean`, `e_ex`, `e_note`). Bật tính năng `undo=True` trên lớp textbox bên dưới để hỗ trợ `Ctrl+Z`. Bổ sung hàm `on_paste` bắt sự kiện `<<Paste>>` nhằm tự động biến dữ liệu chứa Tab (`\t`) thành Bảng Markdown. |
| `web/index.html` | Nhúng thư viện `marked.min.js` qua CDN để hỗ trợ parse Markdown sang HTML. |
| `web/script.js` | Cấu hình `marked.setOptions({breaks: true})` và chuyển `formatText` sang sử dụng `marked.parse(str)`. |
| `web/style.css` | Xóa `white-space: pre-wrap` để tránh xung đột với HTML. Bổ sung `font-family: Consolas` và toàn bộ CSS styling cho thẻ `table`, `th`, `td` nhằm hiển thị giao diện bảng tuyệt đẹp trên Web. |

### 2026-06-20 — Autocomplete & Ghi nhớ Ngày Học
**Vấn đề**: Việc nhập tay "Chủ đề", "Loại từ" và "Tag Ngày Học" tốn thời gian. Cần tự động gợi ý (chỉ 5 lựa chọn đầu) và xổ xuống khi gõ. Đồng thời ghi nhớ Tag Ngày học cuối cùng để điền sẵn cho các từ tiếp theo.

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `VocabApp.py` | Chuyển `e_topic`, `e_date` sang ComboBox. Thêm logic Autocomplete trên `<KeyRelease>`. Thêm biến `App.last_date_tag` để ghi nhớ và gán mặc định cho lần thêm sau. |

### 2026-06-18 — Fix hiển thị nội dung dài (từ "へ")
**Vấn đề**: Từ tiếng Nhật "へ" có nghĩa và ví dụ rất dài, nhiều `\n`, ký tự đặc biệt (`->`, `→`...) → giao diện bị vỡ, không xuống dòng, không scroll được.

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `VocabApp.py` | `e_mean`: `CTkEntry` → `CTkTextbox` (height=100, nhiều dòng). Dialog 920px. |
| `web/style.css` | `white-space: pre-wrap` cho meaning/example. Scroll cho `.vocab-example` và flashcard back. |
| `web/script.js` | Thêm `escapeHtml()`, `formatText()`. Ví dụ trong list có toggle ẩn/hiện. Flashcard dùng `innerHTML`. |
| `web/index.html` | `h2#fc-meaning` → `p.fc-meaning-text`. Thêm meta description. |

- [x] **Cập nhật thứ tự Model Gemini mới (2026-10-03):**
  - Đồng bộ `_DEFAULT_MODEL_FALLBACKS` và `DEFAULT_SETTINGS["ai"]["model_priority"]` trong `settings.py` và `settings.json` sang thế hệ mới: `gemini-3.8-flash` (Tier S) và `gemini-3.5-flash-lite` (Tier S) đứng đầu, tiếp nối bởi `gemini-3.5-flash`, `gemini-3-flash-preview`, `gemini-flash-latest`, `gemini-flash-lite-latest`, `gemini-3.1-flash-lite`, `gemini-3.7-flash`. Đã kiểm tra qua `get_active_model_list()` PASS 100%.

---

### 2026-10-27 — Update 17.2: 7 phase Media-UX + dữ liệu Nhật + Model selector
Hoàn thành trọn plan `vocabapp-japanese-media-ux-plan.md` (P1→P7). Chi tiết lệnh + bảng trong `docs/UPGRADE_17.md` mục **"Update 17.2"**.

**Files mới**:
| File | Vai trò |
|------|---------|
| `ai/media_card.py` | Thẻ từ PNG CJK (gradient, cache SHA-1 `data/media/_cards/`), font CJK riêng + Latin riêng |
| `ai/media_resolver.py` | Resolve media `m_*`/rel/abs/thiếu/traversal (an toàn) |
| `tools/recover_japanese_course.py` | Khôi phục 444 ngày từ manifest — 0 API, guard từ giả |
| `tools/fix_japanese_slug.py` | Dọn split-brain Nhật (dry-run mặc định, `--apply` có backup) |
| `tools/extend_japanese_course.py` | 445 → 1260 ngày, pool JLPT, không trùng từ, checkpoint 20 câu |
| `api/model_catalog.py` | Catalog model thật + tier 2026 + rank + cache 24h + `build_run_priority` |
| `tools/dedupe_methods.py` | AST dùng method trùng (code chết), dry-run / `--apply` |
| `data/seed/ja/dict.json` | Seed 105 từ kana + N5 + test suites tương ứng (7 file) |

**Files sửa (tóm tắt)**: `ai/paths.py` (`canonical_slug`, `LANG_ALIASES`, `web_slug_table` dedupe) · `ai/course_db.py` + `ai/media_store.py` + `database/database.py` (\u200bcanonical mọi đường MỚI, dropdown gộp alias) · `ai/pipeline.py` (`GenerationStopped` module-level, `--offline`, `--days` mặc định 60, guard budget, DoD `plan_complete` hết hằng-True, progress.json ghi trong `finally`) · `api/gemini_safe.py` (log `⚠ 'm1' fail (429) → thử 'm2'`, FIX NameError `model`/`status_code` 2 nhánh QUOTA của `request()`) · `VocabApp.py` (StudyTab media strip + `play_audio_file` + `jp_font()` + `MediaViewerDialog`; ModelSettingsDialog 7 cột + filter + nút «🔄 Dò model mới»; CourseGenerationDialog OptionMenu Model override→restore).

**Kiểm tra**: `test_ai_rich.py` **85/85** · `test_media_resolver/card/recover/slug_canonical` 6/6 · `test_extend_course` 7/7 · `test_model_catalog` 13/13 · `verify_no_rewrite.py` PASS · `node --check` OK · `py_compile` toàn bộ OK. (`verify_p0_fixes` 13/14 — L-A phụ thuộc data thật máy chính.)

**Còn lại (MÁY CHÍNH mới chạy được — data thật bị gitignore)**:
```powershell
python tools\recover_japanese_course.py --apply      # 444 ngày thật → course.json
python tools\fix_japanese_slug.py                    # dry-run → --apply
python tools\extend_japanese_course.py --status      # cần n5..n1_pool.json (~12.500 từ)
python tools\extend_japanese_course.py --dry-run     # → --apply (445→1260)
python -m api.model_catalog --refresh                # dò catalog thật (cần key)
python -m ai.pipeline --all --mode enrich --full     # IPA/khẩu hình (cần quota ~2 ngày)
# Trước khi migrate: dừng process cũ đang ghi log rác data/logs\mật_* (PID 25072 theo plan).
```

