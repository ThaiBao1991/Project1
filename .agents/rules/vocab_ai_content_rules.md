# VocabularyApp — AI Content & Media Rules

Áp dụng cho mọi thay đổi liên quan tới nội dung AI sinh (bài học, từ vựng, ngữ pháp, hội thoại) và media (ảnh, âm thanh) trong `VocabularyApp`.

---

## 1. Schema — additive-only (không bao giờ phá dữ liệu cũ)

1. **Không đổi tên / không xoá** field cũ. Mọi field mới đều là *additive*.
2. `example_sentence` / `example_meaning_vi` / `part_of_speech` là **canonical** — `web/script.js` và `VocabApp.py` đọc theo tên. Alias mới (`example_target`, `example_vi`) là **computed**, không do AI sinh.
3. Mọi field mới đều **optional**. Thiếu ⇒ renderer bỏ qua, không lỗi.
4. `format_version` là **metadata quản trị**, KHÔNG phải điều kiện render. Renderer quyết định dựa trên **sự tồn tại của field**, không dựa trên version.
5. `COURSE_FORMAT_VERSION` định nghĩa **1 nơi duy nhất** (`ai/course_db.py`).
6. Quiz **không** thêm category mới — `flattenQuiz` (`web/script.js:477`) và `_flatten_quiz` (`VocabApp.py:2881`) duyệt cứng 5 key `vocab/pattern/common/grammar/mixed`. `mini_quiz` của grammar **không** được trộn vào quiz chính.

---

## 2. Migration — dirty-flag, không ghi lại file lớn

1. **Tầng A (cấu trúc)**: `grammar` dict→list, `quiz` list→dict, chuẩn hoá `level` → ghi đĩa (giữ hành vi hiện tại).
2. **Tầng B (v4 soft)**: `ipa`, `pos`, `example_target`, `example_vi`, `dialogue: []`, `media: {}` → **`setdefault` trong RAM, KHÔNG `save_course()`**.
   > Lý do: 8 file `course.json` = 135 MB đang được track git. Backfill sẽ tạo diff ~27 MB → blob git mới **vĩnh viễn**, không thu hồi được, mà không đổi lại giá trị gì (app mới có default runtime).
3. Một stage chỉ ghi `status="done"` **sau khi** payload đã qua validator.
4. Xoá file checkpoint **không** làm mất tiến độ `course.json`, và ngược lại.

---

## 3. Token & JSON truncation

1. `max_output_tokens=16384` là trần. `projectLog.md:155-179` (Update 12) đã ghi nhận lỗi **JSON bị cắt** khi output ~12–16k token.
2. **Hội thoại = call AI riêng** (`DIALOGUE_SCHEMA`), KHÔNG gộp vào content. Lý do: content v4 thêm ~2.500 token ⇒ biên an toàn chỉ còn ~35%; gộp dialogue sẽ mất **cả bài học** khi cắt.
3. Quiz tách 2 lần gọi (`QUIZ_SCHEMA_AB` / `QUIZ_SCHEMA_CD`) — giữ nguyên nguyên tắc.
4. Mọi prompt phải kết thúc bằng: *"Chỉ trả về JSON, không thêm chữ nào ngoài JSON."*
5. Khi JSON hỏng: retry kèm hint → **split-retry** (2 prompt nửa) → **salvage** bằng `json.JSONDecoder().raw_decode()` → `deferred_days` + **đi tiếp ngày sau** (không abort).

---

## 4. Media — ảnh (5 tầng fallback)

**Thứ tự cứng, không hỏi người dùng:**

```
T1  Gemini API (native image)     → ưu tiên, có 90 key
T2a Chrome addon (web AI)         → cần addon load unpacked
T2b Selenium (web AI)             → cần chromedriver
T2c OpenClaw browser (web AI)     → cần profile 'chrome' đã pair
T3  Wikipedia/Wiktionary          → 0 key, luôn khả dụng
T4  Placeholder (chữ cái đầu)     → KHÔNG để trống
```

**Quy tắc bất di bất dịch:**
- **Media lỗi KHÔNG BAO GIỜ chặn nội dung chữ.** Bài học vẫn hoàn chỉnh dù thiếu ảnh/audio.
  > Nguồn: `AskCpl/gemini_image_pipeline.py:20-23` — *"A failure leaves the lesson intact."*
- Mỗi ảnh ghi `image_source` ∈ `ai|web|dict|placeholder` + `image_credit` + `image_license`.
  > Ảnh Wikimedia là **CC-BY-SA** ⇒ bắt buộc attribution.
- Áp bộ lọc 6 lớp (icon/avatar/small/redirect/sidebar) trước khi lưu.
- Canonicalize URL ảnh (cắt query `utm_*`) — URL có utm sẽ hỏng theo thời gian.
- Tải ảnh: `Referer` thủ công khi fetch từ service worker; fetch trong page-context thì browser tự gắn.
- Pre-flight: `content-type` phải `image/*`, `bytes >= 5KB`, HTTP < 400.
- Nén **WebP 512px quality 80**, strip EXIF (PIL đã có sẵn, `features.check('webp') == True`).
- Cache theo `sha256(prompt|model|lang)` ⇒ không gọi lại cùng 1 ảnh.

---

## 5. Media — âm thanh

- Cascade: `cache mp3` → `edge-tts` → `gTTS` → `pyttsx3` (**chỉ khi có voice khớp locale**).
- **Tuyệt đối không** fallback sang giọng Anh khi không có voice khớp. Báo *"Ngôn ngữ này chưa có giọng offline"* thay vì đọc sai.
- TTS theo 6 chặng — xem bảng rate/voice trong `skills/vocab_ai_media/SKILL.md` mục 8.4.
- Cache tên file = `sha256(lang|voice|rate|text)[:12]` ⇒ idempotent.
- Pacing: dùng **đúng** `pace()` của `api/gemini_safe.py` (3.5–5.0s + jitter) cho mọi request TTS. `TTS_DAILY_BUDGET` riêng (mặc định 1500).
- Hội thoại: mỗi lượt 1 file mp3 + 1 file "full dialogue".
- Ảnh/audio **không** nhúng base64 vào `course.json` — chỉ tham chiếu key manifest.

---

## 6. Lưu trữ & đồng bộ media

```
data/media/<lang_slug>/<day>/word_{idx}_{hash8}.webp
data/media/<lang_slug>/<day>/audio_{idx}_{hash8}.mp3
data/media/<lang_slug>/<day>/dialogue_{idx}.mp3
data/media/index.json          ← manifest (text only)
```

- `course.json` **không** chứa base64/bytes.
- Manifest chỉ chứa entry cho media **thực sự tồn tại**.
- GitHub sync: **chỉ** upload `data/media/<lang>/` của ngôn ngữ được chọn trong `media_langs` + `data/media/index.json`. Không bắt buộc đồng bộ toàn bộ.
- Ảnh từ điển Wikimedia phải kèm attribution hiển thị trên web.

---

## 7. Budget & quota (không bao giờ vượt)

### 7.1 Hạn mức THẬT của Gemini free tier (đo 2026-10-21)

| Tầng | Quota | Áp dụng cho |
|---|---|---|
| **RPD** (ngày) | **20 call / PROJECT / MODEL** | text + TTS |
| **RPM** (phút) | 15 call / PROJECT | text |
| **RPD hình ảnh** | **limit: 0** (không hề có) | mọi model ảnh ⇒ **tầng ảnh AI không dùng được** |

Pool key: 90 key = **10 `project_id` × 9 account** (mỗi key 1 project, 1 account).
⇒ Sức chứa text: 10 project × 10 model × 20 = **2.000 call/ngày**.
⇒ Sức chứa TTS: 10 project × 5 model × 20 = **1.000 file/ngày**.

### 7.2 Quy tắc bắt buộc

1. **Mỗi model là một quota bucket riêng** → khi 1 model hết quota, **thử model khác TRƯỚC khi đổi key**
   (nếu không sẽ vô hiệu hoá 8-10 key của account chỉ vì 1 model hết quota).
2. `pace()` tính theo **số project** khả dụng: `min(5, max(0.8, 60/(n_project × 11)))`.
3. `classify_response()` phải nhận diện quota NGÀY: `"please retry in Nh"` (N ≥ 0.25 h) và `"limit: 0"` → `QUOTA_DAILY`.
   > Message Gemini **KHÔNG** chứa chữ "perday" — bỏ qua ⇒ retry vô ích ⇒ treo pipeline.
4. 429 RPM → khoá **riêng key** (`AccountPool.lock_key`), **không** khoá cả account.
5. TTS: tracker quota bền theo ngày `data/tts_quota.json`; hết quota ⇒ stage `PENDING` (không phải `done`) để chạy lại ngày sau.
6. Giới hạn ngân sách pipeline (persist trong `_jobs.json`):

| Loại | Mặc định/ngày | Tổng/ngôn ngữ | Ghi đè |
|---|---|---|---|
| `call` (content/quiz/dialogue) | 1400 | 20.000 | CLI flag |
| `images` | 60 | 5.000 | CLI flag |
| `tts` | 3000 | 40.000 | CLI flag |
| `MAX_RUN_SECONDS` | 21600 (6h) | — | CLI flag |
| `MAX_STAGE_ATTEMPTS` | content/quiz 3 · images 3 · audio 2 · dialogue 2 | — | CLI flag |
| `MAX_DEFERRED_PASSES` | 3 | — | CLI flag |

- Bộ đếm phải **persist** (`_jobs.json`), không được chỉ nằm trong RAM (`track_call()` hiện chỉ RAM).
- `DAILY_CALL_BUDGET=3000` của `gemini_safe` là trần tuyệt đối ⇒ pipeline phải cắt trước.

---

## 8. Encoding (bắt buộc)

- Mọi file text: `encoding="utf-8"`.
- `json.dump(..., ensure_ascii=False, indent=2)`.
- Windows console: `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`.
- JS base64 Unicode: dùng `TextEncoder`/`TextDecoder` — **không** dùng `escape`/`unescape`.

---

## 9. Ghi đĩa an toàn

- Mọi ghi file JSON: **atomic** (tmp + `os.replace`).
- **Backup rotation** cho `course.json` / `progress.json`: giữ 5 bản `.bak1..bak5`.
- Trước khi `force_new` (xoá khóa học): backup bắt buộc.
- `course.json` hỏng khi đọc → khôi phục `.bak` → nếu hết → **dừng**, không ghi đè file hỏng.

---

## 10. Quy trình làm việc (Gate 1 / Gate 2)

Tuân thủ `.agents/rules/workflow_rules.md`:
- Đọc `projectLog.md` trước, cập nhật ngay sau mỗi thay đổi quan trọng.
- Trước khi code: liệt kê chính xác file sẽ tạo/sửa/xoá + trình bày plan + **chờ duyệt rõ ràng**.
- Sau khi code: compile/test chạy thật, rà soát edge case, dọn debug, **báo cáo trung thực** (không nói "chắc là xong"), cập nhật `projectLog.md`.
