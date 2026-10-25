# 📦 BÀN GIAO — VocabularyApp Update 16 (2026-10-22)

> **ĐỌC FILE NÀY TRƯỚC KHI LÀM BẤT KỲ VIỆC GÌ.** Nó chứa toàn bộ trạng thái
> kỹ thuật, cách chạy, giới hạn thật đã đo, và việc còn lại.
> Cùng với `projectLog.md` (nhật ký dự án) và `.agents/skills/vocab_ai_media/SKILL.md`.

---

## 0. TL;DR cho phiên sau

| Câu hỏi | Trả lời |
|---|---|
| App làm gì? | Quản lý từ vựng đa ngôn ngữ + **sinh khóa học AI 6 chặng (3.010 ngày / 30.102 từ)** cho 8 ngôn ngữ, kèm **ảnh minh họa + âm thanh TTS + hội thoại roleplay**. |
| Đã xong gì? | Toàn bộ 9 phase: media pipeline, schema v5, orchestrator tự trị, 28 bug fix, skill+rule, dẫn chứng, SRS. |
| Test? | `test_ai_rich.py` **79/79** · `verify_all_native_courses.py` **27/27** · `tools/verify_p0_fixes.py` **14/14** |
| Còn thiếu gì? | Xem mục 7. Ưu tiên: chạy `--mode enrich` (IPA thật) + tích hợp `ai/srs.py` vào GUI + `ai/evidence.py` vào pipeline. |
| Lệnh quan trọng nhất? | `python -m ai.pipeline --all --mode media --full --allow-degraded --workers 6` |

---

## 1. BẢN ĐỒ KIẾN TRÚC

```
VocabularyApp/
├── VocabApp.py            3.3k dòng  · GUI CustomTkinter (18 class)
├── settings.py/.json                · GitHub/Drive/AI/media config
├── requirements.txt                  · 15 gói (đã thêm edge-tts, Pillow, Flask, numpy, selenium)
├── .gitignore                        · chặn settings.json, data/, __pycache__, *.zip
│
├── ai/
│   ├── paths.py            ★ 84      · NGUỒN SỰ THẬT DUY NHẤT cho slug/path
│   ├── media_schema.py     ★ 332     · Schema v5 (IPA, khẩu hình, dialogue ngắn, references)
│   ├── media_store.py      ★ 410     · lưu media + manifest + reindex + cache RAM
│   ├── image_pipeline.py    ★ 365     · chuỗi 4 tầng ảnh + lọc 6 lớp + aHash
│   ├── dictionary_image.py  ★ 656     · Wikipedia/Wiktionary/Commons + throttle + breaker
│   ├── tts_config.py       ★ 195     · bảng voice 11 ngôn ngữ + đặc tả 6 chặng
│   ├── tts_generator.py    ★ 549     · cascade 4 tầng + tracker quota ngày
│   ├── evidence.py         ★ 864     · DẪN CHỨNG (Wiktionary/Wikipedia API + verify URL)
│   ├── srs.py              ★ 377     · SM-2 thuần (chưa nối vào GUI)
│   ├── pipeline.py         ★ 892     · ORCHESTRATOR TỰ TRỊ (12 stage)
│   ├── pipeline_store.py   ★ 289     · checkpoint + jobs.json + budget bền
│   ├── pipeline_log.py     ★ 164     · log JSONL có cấu trúc
│   ├── pipeline_media.py   ★ 269     · 4 stage media
│   ├── providers.py        ★ 198     · ProviderChain (gemini → web → dict)
│   ├── course_generator.py  2.5k     · engine sinh nội dung (schema v5)
│   ├── course_db.py        247       · DB khóa học + migration 2 tầng
│   ├── language_profiler.py 256       · hồ sơ Bản xứ C2
│   ├── bridge_server.py    281       · bridge HTTP 5690 (đã auth + chống path traversal)
│   ├── web_ai_bridge.py    251       · tầng web: addon → selenium → openclaw
│   ├── web_ai_urls.py      ★ 218     · MỞ GEMINI/GROK (copy prompt + mở tab)
│   ├── openclaw_web_ai.py  451       · wrapper OpenClaw CLI (đã thêm Grok/Claude/...)
│   └── selenium_web_ai.py  309       · Selenium anti-detect (đã thêm 4 nền tảng)
│
├── api/
│   ├── gemini_safe.py      921       · GeminiCoordinator + pace thích ứng + blocklist
│   ├── github_sync.py      251       · sync GitHub Pages (loại file hệ thống)
│   └── gdrive_sync.py      213       · upload mp3/mp4 lên Drive
│
├── web/                              · PWA (3 view + AI Course + luyện viết)
│   ├── index.html  style.css  script.js  paths.js ★  manifest.json
├── addon/VocabAIExtractor/           · Chrome addon MV3 (7 nền tảng AI)
├── tools/                 ★ 12 script chẩn đoán/verify
├── .agents/
│   ├── skills/vocab_ai_media/SKILL.md        ★ 12 mục kiến thức
│   └── rules/vocab_ai_content_rules.md       ★ 11 mục quy tắc
└── docs/UPGRADE_16.md            ★ FILE NÀY
```

★ = file mới trong Update 16.

---

## 2. LỆNH ĐỘNG

### 2.1 Chạy app
```bash
cd "C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\VocabularyApp"
python VocabApp.py            # hoặc run.bat
```

### 2.2 Pipeline tự trị (quan trọng nhất)
```bash
# Tất cả 8 ngôn ngữ: thêm ảnh + audio + hội thoại (GIỮ nguyên content)
python -m ai.pipeline --all --mode media --full --allow-degraded --workers 6

# Regenerate CONTENT để có IPA thật + khẩu hình + lỗi sai thường gặp (~3.010 call)
python -m ai.pipeline --all --mode enrich --full --allow-degraded --workers 4

# 1 ngôn ngữ / 1 khoảng ngày
python -m ai.pipeline --lang tiếng_anh --mode media --full --from-day 1 --to-day 30

# Xem trạng thái + DoD 13 check
python -m ai.pipeline --all --status

# Kế hoạch (0 call, 0 ghi)
python -m ai.pipeline --all --dry-run

# Ghi log ra file, JSON kết quả
python -m ai.pipeline --lang tiếng_anh --mode media --full --json --quiet
```
**Exit code**: `0` done/paused · `75` chờ quota/mạng · `74` lỗi đĩa · `78` lỗi key/config · `130` bị ngắt

### 2.3 Verify
```bash
python test_ai_rich.py                    # 79 test, FAST < 60s
python test_ai_rich.py --slow             # + section [11] sinh 700 ngày thật (~10 phút)
python verify_all_native_courses.py       # 27 check 7 vòng
python tools/verify_p0_fixes.py           # 14 check hồi quy P0
python tools/verify_no_rewrite.py         # chứng minh course.json KHÔNG bị ghi lại khi đọc
```

### 2.4 Công cụ
```bash
python -m ai.paths --export-js            # sinh lại web/paths.js
python -m ai.srs                          # demo SM-2
python -m ai.evidence --word cat --lang en
python -m ai.web_ai_urls --list           # 8 nền tảng AI web
python -m ai.web_ai_urls --open gemini   # copy prompt + mở tab
python tools/diag_gemini_keys.py          # phân loại 90 key
python tools/diag_list_models.py          # model Gemini còn sống
python tools/link_media_refs.py           # gắn lại image_ref/audio_ref từ file đĩa
python tools/replace_placeholders.py --all # đánh dấu ngày có placeholder để sinh lại
```

---

## 3. TRẠNG THÁI DỮ LIỆU THẬT (đo 22/10/2026)

| Chỉ số | Giá trị |
|---|---|
| Khóa học | 8 ngôn ngữ · **3.010 ngày** · **30.102 từ** |
| Ảnh | **30.102/30.102 = 100%** (30.567 file) — nhưng **chỉ ~200 là ảnh THẬT**, còn lại là placeholder (Wikimedia chặn IP) |
| Audio | **30.102/30.102 = 100%** (34.289 mp3, edge-tts 11/11 ngôn ngữ) |
| Hội thoại | 1.713/3.010 = 56% (đang chạy nền theo quota) |
| Dung lượng | media 544 MB · audio 341 MB |
| **IPA thật** | **0%** — `ipa` hiện là copy `pronunciation`; cần `--mode enrich` |
| **Dẫn chứng** | **0%** — module `ai/evidence.py` đã có, chưa nối vào pipeline |

---

## 4. GIỚI HẠN THẬT ĐÃ ĐO (đừng lặp lại sai)

### 4.1 Quota Gemini free tier
```
ẢNH (mọi model):  limit: 0   ⇒ KHÔNG THỂ sinh ảnh qua Gemini API
TEXT:             20 call/ngày / PROJECT / MODEL
Pool: 90 key = 10 project_id × 9 account  (mỗi key 1 project, 1 account)
      47 key OK · 16 key chết ("service account deleted") · 27 key 403 (3 account bị deny)
Sức chứa text:   10 project × 10 model × 20 = 2.000 call/ngày
⇒ 3.010 ngày dialogue cần ~2 ngày quota
```
**Sửa đã làm**: `classify_response()` nhận diện quota NGÀY (message Gemini **KHÔNG** chứa "perday" mà chứa *"Please retry in 13h33m"* + `limit: 0`); `pace()` tính theo **số PROJECT** (15 RPM/project, không phải 15/key); `AccountPool.lock_key()` khoá riêng key thay vì cả account; blocklist bền `data/blocked_accounts.json` + `data/blocked_keys.json`.

### 4.2 Wikimedia
```
~30.000 request  ⇒ 429 cho MỌI request (chặn IP)
Sửa đã làm: Semaphore(8) + 0.1s throttle + cache bền (data/media/image_cache.json)
             + circuit breaker (5×429 ⇒ khoá 15 phút) + deadline 10s/từ
Đo lại 1 ngày (khi block hết): 9/10 ảnh thật, 0.7-2.7 s/từ
```

### 4.3 ToS — BẰNG CHỨNG TRÊN CHÍNH MÁY
```
https://www.google.com/sorry/index?continue=...gemini.google.com/app&q=...   (2 lượt)
→ Google ĐÃ trả CAPTCHA cho truy cập tự động
https://grok.com/tos-gate                                                      (4 lượt)
→ Grok có ToS gate
```
⇒ **Tầng scrape ảnh MẶC ĐỊNH TẮT** (`media.image_providers = ["dict","placeholder"]`).
Bật tay bằng cách thêm `"web"` vào `settings.json → media.image_providers` SAU khi cài addon.

### 4.4 OpenClaw (đã kiểm chứng trên máy)
```
✅ Extension OpenClaw v2.3.0 → đã load + bật trong Chrome "Profile 3"
✅ ĐÃ pair (ws://127.0.0.1:18799/extension) · relay 18799 + gateway 18789 đang LISTEN
❌ NHƯNG `openclaw browser --browser-profile chrome tabs --json` → LỖI
   "browserType.connectOverCDP: Timeout 9000ms exceeded"
   → extension `registrations: []`, `manualSetupRequired: true`,
     thiếu native-messaging host `com.openclaw.browser_relay` trong HKCU
⇒ CẦN 1 THAO TÁC USER: `openclaw.cmd browser extension install`
   rồi bấm icon extension trong Chrome "Profile 3"
```

### 4.5 TTS
```
edge-tts  7.3.1  0.6-4.3 s/file, 11/11 ngôn ngữ, KHÔNG giới hạn quota  ← ĐÃ CÀI
gTTS      2.5.4  0.3 s/file, 11/11
Gemini TTS        ✅ nhưng 10 lần/ngày/key/model (5 model ⇒ 2.350/ngày)
pyttsx3           máy này chỉ có en-US×2 + ja-JP×1 ⇒ 8/10 ngôn ngữ KHÔNG có giọng offline
```

---

## 5. KIẾN TRÚC PIPELINE (12 stage)

```
GLOBAL  : profile → backbone → plan
PER-DAY : content → quiz_ab → quiz_cd → images → audio → dialogue → media_verify → commit
```
- **Checkpoint** từng stage: `data/ai_courses/<slug>/_pipeline/days/dNNNN/<stage>.json`
- **Budget bền**: `data/ai_courses/_jobs.json` (3 loại: call / images / tts)
- **Log JSONL**: `data/logs/<slug>_<ts>.log` (event có cấu trúc, xem `ai/pipeline_log.py::EVENTS`)
- **Manifest media**: `data/media/index.json` (64.858 entry)
- **Resume**: dừng giữa chừng chạy lại = tiếp tục. `--no-resume` = xoá checkpoint (giữ course.json)
- **Media lỗi KHÔNG BAO GIỜ chặn nội dung chữ** (nguyên tắc từ AskCpl)

### Chế độ
| `--mode` | Làm gì | Khi nào dùng |
|---|---|---|
| `media` | GIỮ content/quiz, chỉ thêm ảnh+audio+dialogue | Mặc định — rẻ, không tốn quota text |
| `enrich` | Regenerate CONTENT (IPA thật, khẩu hình, lỗi sai, mini_quiz) + media | Cần chất lượng nội dung tốt (~3.010 call) |
| `full` | Tạo mới từ đầu (backbone + content + quiz + media) | Khóa học mới |

---

## 6. BUG ĐÃ SỬA (28)

**P0 (14) — xem `tools/verify_p0_fixes.py` (tự tái hiện):**
L-A dropdown 13→8 ngôn ngữ · L-B push file hệ thống lên repo public · L-C UnboundLocalError `plan`/`done_days` · L-D cache TTS không bao giờ hit · L-E mất từ vựng khi JSON hỏng · L-F ghi đè course.json hỏng · L-G lộ bridge token · L-H path traversal · L-J race dict `course` · L-K bộ đếm quota không lock · L-L rò file handle · L-I .gitignore + PAT · L-M timeout addon 180s · L-U regex "Ngày 1" khớp "Ngày 11"

**P1 (14):** timeout addon · Tkinter var từ thread · upload `_pipeline/` · upload từng file 64k · `upsert_day` không lock · `synth_sapi5` dead code · `consume_call` vs `consume_tts` · `except: pass` mất cache · substring ngày · pip install lúc import · cache index không lock · `JOBS_LOCK` không dùng · 6 bản copy `lang_slug` (→ `ai/paths.py`) · `requirements.txt` thiếu 6 gói

---

## 7. VIỆC CÒN LẠI (xếp theo ưu tiên)

### 7.1 CHẠY NGAY (1 lệnh, tự trị)
```bash
python -m ai.pipeline --all --mode enrich --full --allow-degraded --workers 4
```
→ có IPA thật + khẩu hình + lỗi sai + mini_quiz + dialogue ngắn (≤6 lượt/≤220 ký tự).
Cần ~2 ngày quota. Chạy nền, tự dừng mềm khi hết quota, chạy lại là tiếp tục.

### 7.2 Tích hợp code đã viết nhưng CHƯA nối
| Việc | Module sẵn có | Cần làm |
|---|---|---|
| **SRS** | `ai/srs.py` (377 dòng, SM-2, 15/15 test) | Thêm bảng `review_state` vào `database/database.py`; nút Again/Hard/Good/Easy trong `StudyTab._render_question`; hàng đợi "đến hạn"; streak + thống kê (`App.update_stats()` hiện là `pass` — `VocabApp.py` ~3320) |
| **Dẫn chứng** | `ai/evidence.py` (864 dòng, 7/7 test) | Gọi `attach_to_lesson()` sau stage content trong `ai/pipeline.py`; render khối "📚 Nguồn" ở `web/script.js` + `VocabApp._render_lesson_text` |
| **Dialogue validate** | `media_schema.validate_dialogue()` | Gọi trong `ai/pipeline_media.py::run_dialogue_stage` → log cảnh báo + retry nếu AI không tuân thủ giới hạn |
| **Grammar enrichment** | — | Gemini **LOẠI BỎ** optional nested-array khi response lớn ⇒ `common_mistakes`/`mini_quiz` rỗng. Cần tách 1 call AI riêng (giống quiz_ab/cd) |

### 7.3 Đa năng học tập (chưa làm)
Export/import (CSV/JSON/Anki .apkg/Markdown-Obsidian) · backup/restore nút GUI · tra từ điển offline · mode nghe/dictation/shadowing · quick-lookup Ctrl+K · favorites/tags · deep-link `vocab://` · đồng bộ tiến độ web↔desktop · PWA `sw.js` + xử lý `location.hash` · dark/light toggle

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

1. **Đọc `projectLog.md` + file này trước.** Cập nhật cả 2 sau khi sửa.
2. **Additive schema**: không đổi tên/xoá field cũ (`example_sentence`, `part_of_speech` là canonical).
3. **Migration 2 tầng** trong `ai/course_db.get_course()`: tầng A (cấu trúc) ghi đĩa; tầng B (v4/v5 mềm) **chỉ setdefault trong RAM** ⇒ 8 file `course.json` (135 MB) không bị ghi lại khi đọc.
4. **Slug**: dùng `ai/paths.lang_slug()` (1 nguồn) + `python -m ai.paths --export-js`.
5. **Media lỗi không chặn nội dung chữ.** Media là tăng cường, không phải điều kiện hoàn thành.
6. **Mọi ghi file** phải atomic (tmp + `os.replace`) + retry `PermissionError` (Windows).
7. **Mọi I/O mạng** phải có timeout + không raise ra ngoài (trả fallback an toàn).
8. **Tiếng Việt**: file UTF-8, `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` khi chạy CLI.
9. **Thread**: không đọc biến Tkinter từ thread; dùng `self.after(0, cb)`.
10. **Sau khi sửa**: chạy `python test_ai_rich.py` + `tools/verify_p0_fixes.py` + `python -m py_compile` trên file đã đụng.

---

## 9. BẢN ĐỒ SỰ KIỆN / CHỈ SỐ

| File | Vai trò |
|---|---|
| `projectLog.md` | Nhật ký dự án (Update 16 ở đầu file) |
| `.agents/skills/vocab_ai_media/SKILL.md` | 12 mục kiến thức media (đọc TRƯỚC khi sửa media) |
| `.agents/rules/vocab_ai_content_rules.md` | 11 mục quy tắc nội dung |
| `tools/README.md` | Mô tả 12 script chẩn đoán/verify |
| `ai/pipeline_log.py::EVENTS` | Danh sách event log chuẩn |
| `ai/media_schema.py` | Schema v5 + `DIALOGUE_LIMITS` + `validate_dialogue()` |
| `ai/paths.py` | Quy tắc slug/path duy nhất |
| `data/ai_courses/_jobs.json` | Trạng thái + budget bền của pipeline |
| `data/media/index.json` | Manifest media (64.858 entry) |
| `data/logs/*.log` | Log JSONL mỗi run |
| `data/tts_voices.json` | Bảng voice xuất cho web |
| `data/blocked_accounts.json` / `blocked_keys.json` | Blocklist bền |
