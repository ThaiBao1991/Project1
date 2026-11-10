---
name: vocab-ai-media-pipeline
description: Build or maintain the VocabularyApp AI media pipeline — AI-generated illustrations (Gemini native image), web-AI fallback scraping (Chrome addon / Selenium / OpenClaw browser), dictionary images (Wikipedia/Wiktionary), multilingual TTS (edge-tts/gTTS/SAPI5), and per-stage media manifests. Use when adding or fixing image/audio generation, the multi-tier image fallback chain, image junk filtering, hotlink bypass, TTS voice selection per language, media storage/manifest, or when the AI media pipeline fails, times out, truncates JSON, or produces duplicate/garbage images.
---

# VocabularyApp — AI Media Pipeline

Kiến thức nền tảng cho việc **sinh hình ảnh minh họa** và **âm thanh** cho bài học từ vựng AI, kèm chuỗi fallback nhiều tầng.

Mọi tham chiếu `file:line` dưới đây đã được **kiểm chứng trên máy** — đọc lại file gốc trước khi sửa.

---

## 1. Gemini Native Image (Tầng 1 — sinh ảnh AI)

### 1.1 Cơ chế

`AskCpl/gemini_image_pipeline.py:29-49` — **không** dùng Imagen `predict`, **không** dùng GCS, **không** trả data-URI.

```python
url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
}
```

Đọc kết quả — xử lý **cả 2 casing** của key (`AskCpl/gemini_image_pipeline.py:39-44`):

```python
inline = part.get("inlineData") or part.get("inline_data") or {}
encoded = inline.get("data")          # base64
mime   = inline.get("mimeType") or inline.get("mime_type") or "image/png"
ext    = {"image/png": "png", "image/jpeg": "jpg", "image/webp": "webp"}.get(mime, "png")
raw    = base64.b64decode(encoded)
```

### 1.2 Model chain

| Model | Nguồn | Trạng thái |
|---|---|---|
| `gemini-2.5-flash-image` | `AskCpl/auto_ai_worker.py:41` | đã có code chạy thật |
| `gemini-3.1-flash-image` | catalog `.openclaw/state/openclaw.sqlite-wal` | tên có sẵn, chưa thử |
| `gemini-3-pro-image` | catalog | tên có sẵn, chưa thử |
| `gemini-nano-banana-2.1` | `GetHtmlFromUrl_Python/config/model_priority.json:117` | `enabled: false` (rate limit) |

> ⚠️ **Luôn verify model còn sống trước khi chạy hàng loạt.** Model chết trả 404 → phải ghi vào `dead_models.json` và chuyển model kế tiếp.

### 1.3 ĐỪNG gọi `requests.post` trần

Bản gốc `AskCpl/gemini_image_pipeline.py:35-36` **thiếu**: pace, retry, model fallback, account cooldown, phân loại lỗi 429.

→ Phải đi qua `GeminiCoordinator.request_image()` (`api/gemini_safe.py`), tái dùng:
- `AccountPool.pick()` — `api/gemini_safe.py:254-274` (round-robin theo **account**, luân phiên key trong account)
- `pace()` — `api/gemini_safe.py:32-42` (3.5–5.0s + jitter 0.5–1.5s, lock toàn tiến trình)
- `classify_response()` — `api/gemini_safe.py:111-145` (9 loại `ErrorKind`)
- `is_model_restriction()` — `api/gemini_safe.py:156-168`
- `track_call()` + `DAILY_CALL_BUDGET=3000` — `api/gemini_safe.py:16, 53-64`

### 1.4 Nguyên tắc bất di bất dịch

> **Ảnh là asset tăng cường, lỗi ảnh KHÔNG BAO GIỜ làm hỏng bài học.**
> Nguồn: `AskCpl/gemini_image_pipeline.py:20-23` + `AskCpl/auto_ai_worker.py:489-491`
> (`except Exception → visual_assets=[]`, log `"⚠ Không tạo được ảnh minh họa"`, bài học vẫn lưu).

---

## 2. Bộ lọc ảnh rác (6 lớp)

Nguồn: `DownloadImgFacebook/FacebookLikedMediaAddon/background.js:234-323`

| Lớp | Quy tắc | Vị trí |
|---|---|---|
| **0** | loại ngoài post: `[role="complementary"], [role="navigation"], [role="banner"], [data-pagelet*="RightRail"]`; bỏ `/rsrc.php`, emoji, `static.xx` | `:234-252` |
| **1** | ranh giới vùng nội dung (`boundaryTop`): ảnh nằm dưới thanh Like/Comment/Share → loại | `:254-258` |
| **2** | container bình luận: `img.closest('[aria-label*="Bình luận"], [role="article"]')` | `:265-271` |
| **3** | icon/sticker/emoji/avatar theo `alt`: chứa `nhãn dán\|sticker\|biểu tượng\|icon\|ảnh đại diện\|profile picture\|avatar` | `:273-278` |
| **4** | kích thước: `naturalWidth <= 150 \|\| naturalHeight <= 150` → loại | `:280-285` |
| **5** | thumbnail redirect: `a[href]` trỏ `l.facebook.com/l.php`, `l.fb.me`, hoặc domain ngoài | `:287-301` |
| **6** | avatar/permalink: path `/^\/[^\/]+\/?$/`, `/profile.php`, `/pages/` mà không có content path | `:303-323` |

### 2.1 Quy tắc `og:image`

> ⚠️ **Code và doc đang LỆCH nhau — đọc code, đừng chỉ tin doc.**
> - `ProjectLog.md:68-70` nói "og:image là nguồn **chính**"
> - `ProjectLog.md:260-274` nói "quét `<img>` trước, og:image là **fallback**"
> - **Code thật** `background.js:332-342`: `if (result.images.length === 0 && !isVideoPost && !postDialog) { og:image }` ⇒ **og:image là FALLBACK**
> - **Cấm** lấy `og:image` khi bài là **video** (`ProjectLog.md:311, 319`) — đó là poster video, không phải ảnh bài

### 2.2 aHash 16×16 (dedupe)

Nguồn: `background.js:820-875`. Port sang Python (`PIL` + `numpy` — cả 2 đã có sẵn):

```python
g = img.convert("L").resize((16, 16), Image.LANCZOS)
arr = np.asarray(g, dtype=np.float64)
bits = (arr >= arr.mean()).flatten()          # 256 bit
def similarity(h1, h2): return 1 - np.count_nonzero(h1 != h2) / 256
```

> aHash chỉ dùng để **loại ảnh trùng**, KHÔNG dùng để xác nhận "đúng từ" (2 ảnh cùng chủ đề sẽ false-positive).

---

## 3. Quota & Pacing (đo thật trên máy — 90 key Gemini)

### 3.1 Phân loại pool key (đo 2026-10-21)

| Nhóm | Số lượng | Thông điệp lỗi | Xử lý |
|---|---|---|---|
| ✅ Hoạt động | **47** | — | 5 account: gamesvendn, 09, 10, 13, 16 |
| ⛔ Chết vĩnh viễn | 16 | *"The bound service account is deleted or disabled"* (HTTP 400) | `is_dead_key_message()` → `INVALID_KEY` → `block_key()` |
| 🚫 Bị từ chối | 27 | *"Your project has been denied access"* (HTTP 403) | `is_account_denial()` → `block_account()` (vĩnh viễn) |

> ⚠️ **Bug cũ (đã sửa)**: `classify_response()` trả `REQUEST_BAD` cho 2 loại lỗi trên ⇒ **1 key chết abort cả request** dù còn 47 key tốt.

### 3.2 Pacing PHẢI thích ứng theo số key

`api/gemini_safe.py::pace()` — khoảng nghỉ **thích ứng**:

```python
n = pool.usable_count()                 # số key khả dụng
interval = min(5.0, max(0.35, 30.0/n)) # 47 key → 0.64 s/lần
```

| Số key | Nghỉ/lần | Throughput | Mỗi key |
|---|---|---|---|
| 8 (1 account) | 3.75 s | 16 call/phút | 2 call/phút |
| **47 (thực tế)** | **0.64 s** | **94 call/phút** | **2 call/phút** |

Quy tắc: **mỗi key ≤ 15 call/phút** (free tier RPM). Không dùng nghỉ cố định 3.5-5 s khi có nhiều key (lãng phí 6-8× thời gian).

### 3.3 429 RPM/TPM → khoá **riêng key**, KHÔNG khoá cả account

```python
# SAI (cũ):  self._lock_account(key, 65)  → chặn 9-10 key khác của account
# ĐÚNG:      self._pool.lock_key(key, 65) → chỉ chặn 1 key
```
Với 6 luồng song song, khoá cả account ⇒ hết key trong 5 account ⇒ nghẽn toàn bộ.

### 3.4 TTS — QUOTA THẬT (đo 2026-10-21, quan trọng nhất)

API trả về khi hết quota TTS:

```
quotaId:      GenerateRequestsPerDayPerProjectPerModel-FreeTier
quotaDimensions: {location: global, model: gemini-3.8-flash-tts}
quotaValue:   10
"Please retry in 14h8m43s"
```

⇒ **10 request/ngày / MỖI KEY / MỖI MODEL**. Đây là hạn mứn **NGÀY**, không phải RPM.

| Hạng mục | Số |
|---|---|
| Key khả dụng | 47 (nhưng `_load_gemini_keys()` trả 90 → tính theo 90, thực tế ~47) |
| Model TTS dùng được | 5 (`gemini-3.8-flash-tts`, `gemini-3.8-flash-lite-tts`, `gemini-3.1-flash-tts-preview`, `gemini-2.5-flash-preview-tts`, `gemini-2.5-pro-preview-tts`) |
| **Sức chứa/ngày** | **10 × 5 × 47 = 2.350 file** (chỉ 1 model ⇒ 470/ngày) |
| Quota reset | **0h00 theo giờ Google** (không phải 24h kể từ lúc dùng) |

**⇒ BẮT BUỘC:**
1. Xoay **nhiều model TTS** (mỗi model có hạn mức riêng) — dùng 1 model ⇒ chỉ 470/ngày.
2. Theo dõi quota **bền** theo ngày: `data/tts_quota.json` = `{date, used:{"<keyhash>|<model>": n}}`.
3. Khi hết quota → đánh dấu stage audio là **PENDING** (KHÔNG phải done) để chạy lại ngày mai.
4. Pace TTS 1.5-2.2 s — nhưng **giữ chừa quota cho dialogue AI** (cùng account).
5. Khi key trả 429 → cooldown **300 s** (không phải 60 s: quota là NGÀY, 60 s không giúp).

**Sai lầm đã mắc phải**: thử 90 key × pace 1.85 s ⇒ 166 s cho 1 câu ⇒ treo cả pipeline.
⇒ `MAX_TTS_KEY_TRY = 4` + `TTS_DAILY_LIMIT` check trước mỗi lần gọi.

### 3.5 Ngân sách 3 loại (tách theo metric)

| Loại | Mặc định/ngày | Tổng/ngôn ngữ | Ghi đè |
|---|---|---|---|
| `call` (content/quiz/dialogue) | 1200 | 20.000 | CLI |
| `images` | 60 | 5.000 | CLI |
| `tts` | 3000 | 40.000 | CLI |

> TTS **tách riêng** vì dùng metric khác (`generate_content_free_tier_requests` với model TTS) — nếu gộp, 36k TTS sẽ "ăn" hết quota của 3.010 call dialogue.
> **Nhưng**: hạn mứn thật của TTS là **10/ngày/key/model** (mục 3.4) ⇒ budget 3000/ngày là trần lý thuyết, thực tế ~2.350/ngày.

---

## 4. Race condition khi ghi manifest (Windows)

`ai/media_store.py::save_index()` — `os.replace` trên **Windows** ném `PermissionError` nếu file manifest đang được thread khác mở để đọc.

Hệ quả: file media **đã ghi xong** nhưng entry manifest **mất** ⇒ file "mồ côi".
> Đo thật: **18.500 file ảnh nhưng manifest chỉ còn 1.369 entry**.

```python
for attempt in range(10):
    try:
        os.replace(tmp, INDEX_PATH); return
    except PermissionError:
        time.sleep(0.02 * (attempt + 1))
```

**Khôi phục file mồ côi**: `ai/media_store.py::reindex()` — quét lại `data/media/` và dựng manifest từ đĩa (đo thật: 4.087 → **39.532 entry**).

---

## 5. Tầng Web AI — MẶC ĐỊNH TẮT

Cần **Chrome addon cài thủ công** (load unpacked `VocabularyApp/addon/VocabAIExtractor/`) hoặc chromedriver khớp Chrome.

| Hệ quả khi thiếu | Đo thật |
|---|---|
| Mỗi lần gọi mất | **~60 s** (addon lỗi + Selenium khởi động Chrome + OpenClaw timeout) |
| Hệ quả | chậm gấp **20 lần** so với tầng `dict` |

⇒ `media.image_providers` mặc định = `["dict", "placeholder"]`.
Bật tầng `web` **chỉ sau khi** đã cài addon + thêm `"web"` vào `settings.json → media.image_providers`.

**Circuit breaker** (`ai/web_ai_bridge.py`): sau 3 lần thất bại liên tiếp → tạm vô hiệu 30 phút.

---

## 6. Hotlink bypass (tải ảnh từ CDN)

### 6.1 Nguyên tắc

| Nơi fetch | Referer | Nguồn |
|---|---|---|
| **page-context** (content script) | browser tự gắn `Referer` + `Origin` đúng | `DownloadTiktok/s.js:1484` (`referer: document.referrer`) |
| **service worker** | phải **tự set** `Referer` | `DownloadImgFacebook/.../background.js:672-676` |

```python
headers = {"User-Agent": "Mozilla/5.0 ...", "Referer": "https://www.tiktok.com/"}
# mẫu Python: OpenCode/Addon/MyTiktokDownload/src/downloader.py:572-573
```

### 6.2 Pre-flight trước khi lưu

`background.js:678-697` — kiểm `content-type` phải `image/*`, `content-length >= 5KB`, HTTP < 400, chặn `text/html`/`application/json`.
Thêm Range probe `bytes=0-4095` cho ảnh lớn (`background.js:703-709`).

### 6.3 URL cần canonicalize

Host ảnh Wikimedia **nay là `thumb.wikimedia.org`** (không phải `upload.wikimedia.org`) và URL có đuôi:
`?utm_source=en.wikipedia.org&utm_campaign=api&utm_content=thumbnail`

→ **Phải cắt query utm** trước khi lưu cache, nếu không URL sẽ hỏng theo thời gian.

---

## 7. Chrome Addon MV3 (Tầng 2a)

Mẫu tham chiếu: `AskCpl/CopilotWordExportAddon/`

### 7.1 Bảng selector 3 nền tảng

| Nền tảng | Ô nhập | Nút gửi | Nội dung (turn) | Nội dung (delta) |
|---|---|---|---|---|
| **Gemini** | `rich-textarea > div[contenteditable="true"]`, `.ql-editor` (`:795-799`) | `button[aria-label*="Send" i]` (`:836`) | `user-query, model-response` (`:632`) | `message-content` (`:904`) |
| **ChatGPT** | `#prompt-textarea` (`:804`) | `button[data-testid="send-button"]` (`:840`) | `article[data-testid^="conversation-turn"]` (`:651`) | `div.markdown` (`:909`) |
| **Copilot** | generic (`:812`) | generic (`:844`) | `cib-chat-turn` (`:670`) | `.markdown-body, .ac-textBlock` (`:942`) |

### 7.2 Kỹ thuật bắt buộc copy

| # | Kỹ thuật | Vị trí | Vì sao |
|---|---|---|---|
| T01 | **Giữ block CHỈ có `<img>`** | `:928-935` | nếu không, mất sạch ảnh trong HTML |
| T02 | DOM delta-extraction (đánh dấu trước khi gửi) | `:887-893`, `:902-951` | không lẫn nội dung cũ |
| T03 | Cap dung lượng `MAX_HTML_BYTES=2MB`, `MAX_BLOCKS=500` | `:895-900` | tránh IPC drop |
| T04 | `isErrorContent()` — length guard 400 + `\b503\b` | `:953-977` | số "1503" bị nhầm là lỗi 503 |
| T05 | `validateContent()` — **tỷ lệ ký tự**, không đếm từ | `:979-997` | CJK không có space → "1 từ" |
| T06 | Anti-stuck: 120s không đổi **và** không generating | `:1031-1069`, `:1058-1061` | tránh kẹt vô hạn |
| T07 | `MIN_WAIT=15s`, `MAX_TOTAL=240s` | `:1071-1092` | chờ có trần |
| T08 | React/Angular input injection (`execCommand('insertText')` + `InputEvent`) | `:852-885` | `send_keys` mất ký tự |
| T09 | Input-selector fingerprinting → `chrome.storage.local` | `:748-783` | chịu được DOM đổi |
| T10 | Keepalive: silent audio + **Web Locks API** + ping SW + heartbeat | `:66-119` | chống Chrome throttle tab ẩn |
| T11 | Download bằng **base64 data-URI** | `background.js:203-251` | `URL.createObjectURL` **không** hoạt động trong MV3 SW |
| T12 | `chrome.downloads.onDeterminingFilename` → `suggest({filename})` | `background.js:191-201` | Edge bỏ qua `filename` |
| T13 | `MAX_RETRIES=5` → bỏ qua ngày lỗi, đi tiếp | `:1209-1231` | không đứng chết 1 bài |
| T14 | Base64 UTF-8 2 chiều `TextEncoder`/`TextDecoder` | skill `copilot_addon_dev` | không dùng `escape`/`unescape` |

### 4.3 Phần reference **thiếu** (phải tự viết)

Reference **giữ** `<img>` trong HTML nhưng **không tải** về. Cần bổ sung:

1. `resolveImageUrl(img)` — `data:` / `blob:` / relative → absolute
   - `blob:` **phải** fetch trong content script (origin-scoped), không fetch được từ SW
2. Fetch **trong content script** (page-origin ⇒ Referer đúng) → `arrayBuffer()` → base64 → POST về bridge
3. Áp bộ lọc 6 lớp (mục 2) **trước** khi fetch
4. Pre-flight MIME/size (mục 3.2)
5. Đặt tên deterministic: `day_{DDD}_img_{KK}.{ext}` (`DDD`=day 3 số, `KK`=thứ tự trong DOM)

---

## 8. Selenium (Tầng 2b)

### 8.1 Anti-detect

Nguồn: `Python Project/MyApp/DlTangThuvien/utils/browser.py:24-29`

```python
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.exclude_switches.append("enable-automation")
chrome_options.add_experimental_option("useAutomationExtension", False)
chrome_options.add_argument("--user-data-dir=" + profile_dir)   # profile RIÊNG, đã đăng nhập
# KHÔNG dùng --headless (Gemini/ChatGPT chặn headless)
```

### 8.2 Quản lý Chrome thu nhỏ mà **không giết browser của user**

Nguồn: `DownloadImgFacebook/FacebookMediaHelper/background_runner.py:67-87`

- Spawn Chrome với `--user-data-dir` + `--profile-directory` + **`--start-minimized`** + `--no-first-run`
- `taskkill /PID {pid} /T /F` — chỉ PID của mình, **không** `taskkill /IM chrome.exe`
- `creationflags=CREATE_NO_WINDOW` để không nháy console khi chạy từ GUI

### 8.3 chromedriver

- Selenium 4.48 đã có sẵn + `selenium-manager.exe` bundle
- Cache driver: `C:\Users\games\.cache\selenium\chromedriver\win64\{130..153}\`
- **Chrome 155** nhưng cache tới **153** ⇒ lần đầu Selenium Manager **phải tải** driver 155 (cần mạng)
- Offline: chỉ dùng được nếu pin Chrome for Testing 153

---

## 9. OpenClaw Browser CLI (Tầng 2c) — 3 BLOCKER

OpenClaw **đã cài**: npm `openclaw@2026.9.4` + `C:\Users\games\.openclaw\`.

### 9.1 BLOCKER 1 — phải gọi `openclaw.cmd`

```python
subprocess.run(["openclaw", ...])   # ❌ FileNotFoundError [WinError 2] trên Windows
subprocess.run(["openclaw.cmd", ...])  # ✅ rc=0, JSON hợp lệ
```
`shutil.which("openclaw")` trả `...\npm\openclaw.CMD` nhưng `CreateProcess` không nối `.cmd` tự động.
`openclaw.ps1` → `OSError [WinError 193]`.

### 9.2 BLOCKER 2 — cú pháp thật

| Cần | SAI | ĐÚNG |
|---|---|---|
| chờ selector | `wait --selector "body"` | `wait "body"` — **selector là POSITIONAL** |
| chờ theo thời gian | `wait --time-ms 100` | `wait --time 100` |
| lấy text | `browser text` / `browser html` | **KHÔNG TỒN TẠI** → dùng `evaluate --fn` |
| timeout | `--timeout=30000` (Gateway RPC) | thêm `--timeout-ms` cho chờ điều kiện (default 20000) |

### 9.3 BLOCKER 3 — profile

| Profile | transport | port | login? |
|---|---|---|---|
| `openclaw` (default) | cdp | 18800 | ❌ **profile sạch, không có session** |
| `user` | chrome-mcp | — | Chrome thật (cần bật `chrome://inspect/#remote-debugging`) |
| `chrome` | extension relay | 18799 | Chrome thật (cần **pair** extension) |

→ Web AI (Gemini/ChatGPT) **phải** dùng profile `chrome` hoặc `user`. Profile `openclaw` không đăng nhập ⇒ vô dụng cho web AI.

### 9.4 Python package `openclaw` ≠ OpenClaw thật

`C:\Users\games\AppData\Roaming\Python\Python314\site-packages\openclaw\` là **installer của CMDOP** (docstring `__init__.py:1-9`):
> *"openclaw — installer for the cmdop CLI… **Not affiliated with the OpenClaw project**"*

→ **KHÔNG** dùng `import openclaw` để điều khiển browser. Chỉ dùng CLI subprocess (`openclaw.cmd`).

### 6.5 `openclaw agent exec` chưa dùng được browser

`~/.openclaw/openclaw.json` có `"tools": {"profile": "minimal"}` ⇒ chỉ cho phép `session_status`.
`browser` thuộc `group:ui` — **không có** trong `minimal` lẫn `coding`.
Cần: `tools.profile: "coding"` + `alsoAllow: ["browser"]`.

### 9.6 Lệnh mẫu đã verify

```bash
openclaw.cmd browser --json open "https://gemini.google.com/app"
openclaw.cmd browser --json wait --load networkidle --timeout-ms 30000
openclaw.cmd browser --json snapshot --format ai --limit 400
openclaw.cmd browser --json type 3 "prompt" --submit
openclaw.cmd browser --json wait --text "..." --timeout-ms 60000
openclaw.cmd browser --json evaluate --fn "const el=document.querySelector('model-response'); return el?el.innerText:document.body.innerText.slice(0,8000);"
openclaw.cmd browser --json close t2
```

> Dùng `suggestedTargetId` / `tabId` (`t1`, `t2`) thay vì raw `targetId` — raw id không ổn định dưới Chromium target replacement.

---

## 10. Ảnh từ từ điển (Tầng 3)

**Đã test thật 200 OK, 0 key, 0.2–0.5s.**

```python
GET https://{lang}.wikipedia.org/w/api.php
      ?action=query&prop=pageimages&titles={word}&format=json&pithumbsize=400&redirects=1
GET https://{lang}.wiktionary.org/w/api.php?...   (fallback)
GET https://{lang}.wikipedia.org/api/rest_v1/page/summary/{word}   (chỉ Wikipedia — Wiktionary REST trả 404)
```

### Bắt buộc
- **Canonicalize URL** — cắt `?utm_source=…&utm_campaign=api&utm_content=thumbnail`
- **Attribution** — Wikimedia là **CC-BY-SA** ⇒ bắt buộc lưu `image_credit` (tác giả) + `image_license` + `image_source_url`
- Kiểm `pageid == -1` (missing) và `disambig` ⇒ bỏ qua
- Kiểm `thumbnail` vắng ⇒ bỏ qua (không có ảnh minh họa)

---

## 11. TTS — cascade 4 tầng

### 11.1 Bảng engine

| Engine | Cần cài? | Chất lượng | Offline | Phủ 10 ngôn ngữ | rate/pitch | Word boundary |
|---|---|---|---|---|---|---|
| **edge-tts** 7.3.1 | ✅ (`edge-tts>=7.3`) | **cao (neural)** | ❌ | ✅ 10/10 | ✅ `rate` `pitch` `volume` | ✅ `WordBoundary` |
| **gTTS** 2.5.4 | có sẵn | TB | ❌ | ✅ 10/10 | ⚠️ `slow=True/False` | ❌ |
| **pyttsx3** 2.99 | có sẵn | thấp (SAPI5) | ✅ | ⚠️ **chỉ 2/10 trên máy này** | `rate` wpm | ❌ |
| **sherpa-onnx** 1.13.8 | ✅ (`sherpa-onnx>=1.13`) | TB–khá | ✅ | ✅ (model/ngôn ngữ) | `length_scale` | ❌ |

> `kokoro` (`requires_python <3.13`) và `coqui TTS` (`<3.12`) **KHÔNG cài được** trên Python 3.14.
> `piper-tts` chỉ có wheel `cp39` + sdist → build C++ → không dùng được.

### 11.2 SAPI5 trên máy này (đã đọc registry)

```
TTS_MS_EN-US_DAVID_11.0   Microsoft David Desktop   ['en-US']
TTS_MS_EN-US_ZIRA_11.0    Microsoft Zira Desktop    ['en-US']
TTS_MS_JA-JP_HARUKA_11.0  Microsoft Haruka Desktop  ['ja-JP']
```
→ **8/10 ngôn ngữ KHÔNG có giọng offline.** Tuyệt đối **không** fallback về giọng Anh.

### 11.3 Bảng voice 11 ngôn ngữ

| Ngôn ngữ | edge-tts | gTTS | SAPI5 máy này |
|---|---|---|---|
| English | `en-US-AriaNeural` | `en` | ✅ David, Zira |
| Japanese | `ja-JP-NanamiNeural` | `ja` | ✅ Haruka |
| Chinese | `zh-CN-XiaoxiaoNeural` | `zh-CN` | ❌ |
| Korean | `ko-KR-SunHiNeural` | `ko` | ❌ |
| French | `fr-FR-DeniseNeural` | `fr` | ❌ |
| German | `de-DE-KatjaNeural` | `de` | ❌ |
| Russian | `ru-RU-SvetlanaNeural` | `ru` | ❌ |
| Spanish | `es-ES-ElviraNeural` | `es` | ❌ |
| Thai | `th-TH-PremwadeeNeural` | `th` | ❌ |
| Arabic | `ar-SA-ZariyahNeural` | `ar` | ❌ |
| Vietnamese | `vi-VN-HoaiMyNeural` | `vi` | ❌ |

### 11.4 Đặc tả theo 6 chặng

| Chặng | Đơn vị | edge-tts rate | Số file/từ |
|---|---|---|---|
| Vỡ lòng | từng ký tự/âm lẻ | `-45%` | 2 (normal+slow) |
| Ghép âm | âm tiết | `-30%` | 2 |
| Sơ cấp | từ + mẫu câu ngắn | `-15%` | 2 |
| Trung cấp | câu đầy đủ | `+0%` | 1 |
| Cao cấp | đoạn 3-5 câu | `-5%` + `WordBoundary` | 1 |
| Bản xứ | thành ngữ + hội thoại | `+0%` | 1 + từng lượt |

### 11.5 Cache

Tên file = `sha256(lang|voice|rate|text)[:12]` → idempotent, đổi voice/giọng ⇒ sinh bản mới, đổi text ⇒ sinh lại.
Đường dẫn: `data/audio/<lang_slug>/<hash>.mp3`.

---

## 12. Tham chiếu nhanh (bảng tra cứu)

| Cần | File:line |
|---|---|
| Gemini native image | `AskCpl/gemini_image_pipeline.py:29-49` |
| AccountPool + pace + classify | `api/gemini_safe.py:254-274, 32-42, 111-145` |
| Bộ lọc ảnh 6 lớp | `DownloadImgFacebook/.../background.js:234-323` |
| aHash | `DownloadImgFacebook/.../background.js:820-875` |
| Referer hotlink | `OpenCode/Addon/MyTiktokDownload/src/downloader.py:572-573` |
| Selector addon 3 nền tảng | `AskCpl/CopilotWordExportAddon/content_script.js:358, 630-701, 795-850` |
| Giữ block chỉ có `<img>` | `AskCpl/CopilotWordExportAddon/content_script.js:928-935` |
| Keepalive chống throttle | `AskCpl/CopilotWordExportAddon/content_script.js:66-119` |
| Download data-URI MV3 | `AskCpl/CopilotWordExportAddon/background.js:203-251` |
| Selenium anti-detect | `Python Project/MyApp/DlTangThuvien/utils/browser.py:24-29` |
| Chrome thu nhỏ, không kill user | `DownloadImgFacebook/FacebookMediaHelper/background_runner.py:67-87` |
| Bridge Flask pattern | `AskCpl/exercise_server.py:342-436` |
| `_atomic_write` mẫu | `AskCpl/adaptive_learning.py:71-84` |
| WebP encode (PIL) | `.agents/skills/.system/imagegen/scripts/image_gen.py:330-361` |
