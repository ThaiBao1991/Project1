---
name: "chrome-ai-autochat-extractor-addon"
description: "Use this skill for building or maintaining ANY Chrome/Edge Extension (Manifest V3) that automates looping a conversation with a web-based AI assistant (Copilot, Gemini, ChatGPT, Claude, etc.), extracts each reply, and downloads/exports the results — not limited to one specific addon; applies to clones, forks, or new addons built on the same pattern (content_script.js DOM injection + background.js service worker + popup UI, roadmap-driven day/topic loop). Trigger on: content script not injecting on a target site, downloads silently failing (CSP / blob: URL blocked in service worker), chrome.storage.local size limits, chrome.runtime.sendMessage / IPC payload dropped silently, Base64/UTF-8 double-encoding corruption, session.json / auto-save / resume-after-crash logic, tab throttling when minimized (setTimeout delay, keep-alive, Web Locks API, silent audio), multi-tab or multi-profile state collisions, false-positive error detection in scraped text, CJK/non-space-delimited language word-count bugs, or large roadmap data causing popup/UI freeze."
---

# Hướng dẫn phát triển Addon Auto-Chat & Extract (mẫu: AskCpl)

Kỹ năng này cung cấp kiến thức nền tảng và tài liệu tham khảo về luồng hoạt động của dạng addon tự động lặp hội thoại với trợ lý AI trên web (Copilot, Gemini, ChatGPT, Claude...), trích xuất nội dung trả lời và xuất file. Áp dụng cho addon gốc `AskCpl` lẫn mọi bản fork/clone/addon mới xây trên cùng kiến trúc. Khi bảo trì hoặc phát triển tính năng mới cho loại addon này, hãy luôn tuân theo các quy ước và ghi nhớ các bẫy kỹ thuật dưới đây.

---

## 1. Cấu trúc Addon (Manifest V3)

| File | Vai trò |
|------|---------|
| `manifest.json` | Phân quyền (`downloads`, `storage`, `scripting`), Host Permission |
| `popup.html` & `popup.js` | Giao diện điều khiển — nạp Roadmap, gửi Start/Stop/Resume |
| `background.js` | Service Worker — xử lý `chrome.downloads` (CSP workaround) |
| `content_script.js` | "Bộ não" — DOM injection, điền prompt, thu thập kết quả |

---

## 2. Luồng hoạt động chính (State Machine)

1. **Khởi tạo**: Popup → `{ action: "start_loop", tabId }` → Content Script.
2. **State Memory**: `isRunning = true`, `currentTabId` → lưu vào `chrome.storage.local`.
3. **Run Day X**: `_runNextDayAttempt()` → tìm ô nhập → điền prompt → Enter/Click → `waitForResponseComplete()`.
4. **Trích xuất & Tải file**: HTML → gửi về `background.js` Base64 Data URI → `chrome.downloads.download()`.
5. **Chuyển ngày**: Tăng `currentDay` → cập nhật storage → reload nếu cần → tiếp tục loop.

---

## 3. QUY TẮC BẮT BUỘC KHI VIẾT CODE

### ⚠️ VÀNG — Mã hóa Base64 2 chiều đồng bộ
Khi lưu/đọc dữ liệu JSON qua Base64 (đặc biệt khi có tiếng Việt, ký hiệu Unicode):

```javascript
// Khi LƯU (Encode):
btoa(unescape(encodeURIComponent(JSON.stringify(obj))))

// Khi ĐỌC (Decode):
JSON.parse(decodeURIComponent(escape(atob(str))))
```

**Hậu quả nếu thiếu `decodeURIComponent` khi đọc:** Chuỗi byte UTF-8 bị hiểu nhầm thành Latin-1. Sau hàng trăm vòng lặp Auto-Resume, dung lượng ký tự nhân đôi theo cấp số nhân → file JSON phình từ 4MB lên 50MB+ → IPC bị drop → Addon treo hoàn toàn.

### ⚠️ IPC (sendMessage) giới hạn kích thước payload
- `chrome.runtime.sendMessage` bị **drop im lặng** nếu payload quá lớn (~5-10MB).
- **Không bao giờ nhúng Roadmap Data** (3000 bài) vào payload.
- Luôn lưu vào `chrome.storage.local` key riêng (`roadmap_active`, `roadmap_{profile}`) rồi đọc trong Content Script.

### ⚠️ chrome.storage.local giới hạn 10MB/key
- Không lưu toàn bộ `addonConfigs` (bao gồm roadmap) vào 1 key duy nhất.
- Roadmap phải lưu tách biệt: `chrome.storage.local.set({ ['roadmap_' + profileName]: data })`.

---

## 4. LỖI KINH ĐIỂN & GIẢI PHÁP (Đã áp dụng)

### A. Edge không tạo thư mục khi tải file
- **Hiện tượng**: Edge bỏ qua tham số `filename` từ `data:` URI, đổ hết ra thư mục Downloads ngoài.
- **Giải pháp**: Dùng `chrome.downloads.onDeterminingFilename` trong `background.js`. Dùng `suggest({ filename: "thu_muc/file.html" })` để ép tên file.

### B. Vòng lặp vô tận sau Stop (Thread Leaking)
- **Hiện tượng**: Bấm Stop, trang vẫn tự chạy sau khi reload.
- **Giải pháp**: Ghi `isRunning = false` xuống `chrome.storage.local` khi Stop. Chèn `if (!isRunning) return 'stop';` tại **mọi điểm await** trong luồng chính.

### C. Multi-Tab xung đột (chung biến `runningState`)
- **Hiện tượng**: Tab B vô tình chạy cùng Tab A.
- **Giải pháp**: Lưu trạng thái theo Dictionary `runningStates[tabId]`. Tab chỉ Auto-Resume khi `get_tab_id` từ Background khớp với tabId lưu trong storage.

### D. Roadmap quá lớn → Popup treo + IPC Drop [GĐ 43/44]
- **Hiện tượng**: Load session.json → click Run → Addon không phản hồi, icon không lên.
- **Giải pháp**:
  - Strip `roadmapData` khỏi `sendMessage` payload.
  - Lưu roadmap vào key riêng `roadmap_active`.
  - `updateRoadmapPreview` chỉ hiển thị số bài, không `JSON.stringify` toàn bộ.
  - Content Script đọc roadmap từ storage (async) thay vì nhận qua IPC.

### E. Encoding Loop → file JSON phình to [GĐ 45]
- **Hiện tượng**: Sau nhiều ngày chạy, session.json phình từ 4MB lên 28-53MB. Nội dung xuất hiện ký tự lỗi "ÃÂÃÂ...".
- **Nguyên nhân**: `btoa(unescape(encodeURIComponent(...)))` khi lưu, nhưng chỉ `atob(...)` khi đọc — thiếu `decodeURIComponent`.
- **Giải pháp**: Sửa `atob(str)` → `decodeURIComponent(escape(atob(str)))` ở `content_script.js` dòng tải lại session sau reload.

### F. `isErrorContent` False Positive — Day 1503 bị reject [GĐ 46]
- **Hiện tượng**: Add-on kẹt mãi ở bài có số chứa mã lỗi HTTP (VD: Day **1503** chứa **503**).
- **Nguyên nhân**: `isErrorContent()` dùng `.includes('503')` → số `1503` bị nhận nhầm là lỗi 503.
- **Giải pháp**:
  1. **Length guard**: nếu `text.length > 400` → bypass kiểm tra (chắc chắn là bài giảng).
  2. **Word Boundary**: dùng regex `\b503\b` thay cho `.includes('503')`.

### G. `validateContent` False Reject với tiếng Nhật/Trung [GĐ 46]
- **Nguyên nhân**: Đếm số từ bằng `split(/\s+/)`. Tiếng Nhật/Trung không có khoảng trắng → 2000 ký tự = "1 từ" → spam filter kích hoạt sai.
- **Giải pháp**: Đổi sang tỷ lệ ký tự: `nameCharCount > text.length * 0.4`.

### H. Background Throttling — Chrome chậm khi bị ẩn [GĐ 47]
- **Hiện tượng**: Khi dùng app khác (Chrome bị ẩn/thu nhỏ), cả tiếng chưa xong 1 bài.
- **Nguyên nhân**: Chrome throttle `setTimeout` của tab bị ẩn. Silent Audio có thể bị block bởi Autoplay Policy sau reload → bị tắt ngầm → throttle kích hoạt.
- **Giải pháp (A+B)**:
  - **A — Audio Health Check**: `_audioHealthInterval` (5s) kiểm tra `_silentAudio.paused` → tự `play()` lại nếu bị tắt.
  - **B — Web Locks API**: `navigator.locks.request('askcpl_wakeLock', { mode: 'shared' }, () => new Promise(...))` — giữ lock suốt vòng lặp. Tab giữ lock sẽ không bị Chrome/Edge đưa vào trạng thái ngủ/frozen.

---

## 5. KIẾN TRÚC KEEPALIVE (chống Chrome throttle)

```
setupKeepAlive()
  ├── _silentAudio (loop=true, volume=0.01)    ← phát audio im lặng
  ├── _audioHealthInterval (5s)                ← restart audio nếu bị tắt [GĐ47-A]
  ├── _wakeLockAbort (Web Locks API)           ← giữ lock chặn throttle [GĐ47-B]
  ├── _keepAliveInterval (20s)                 ← ping background Service Worker
  └── _heartbeatInterval (15s)                 ← cập nhật timestamp cho popup

teardownKeepAlive()
  ├── pause + removeAttribute('src') _silentAudio
  ├── clearInterval _audioHealthInterval
  ├── _wakeLockAbort._resolve() + .abort()     ← giải phóng lock
  ├── clearInterval _keepAliveInterval
  └── clearInterval _heartbeatInterval
```

---

## 6. TÍNH NĂNG NÂNG CAO

| Tính năng | Mô tả |
|-----------|-------|
| **Auto-Summarizer** | Hỏi AI secondary prompt tóm tắt < 20 từ sau mỗi bài. Xây dựng `historySummaries`. |
| **Multi-Step Interrogation** | Hỏi sâu chủ đề đến khi đủ `targetCount`. Lưu vào `topicMemory`. |
| **Roadmap Injection** | Nạp danh sách bài từ `.md` (cú pháp `## Day X`), tạo mục lục `index.html`. |
| **Multi-Platform** | Hỗ trợ Gemini (`message-content`), Copilot (`.ac-textBlock`), ChatGPT (`div.markdown`). |
| **Tab Binding** | Mỗi tab AI chạy lộ trình riêng song song. Trạng thái lưu theo `runningStates[tabId]`. |
| **Auto End Day** | Tự tính ngày kết thúc từ số bài trong Roadmap nếu không nhập `endDay`. |

---

## 7. Ghi chú phạm vi

Skill này chỉ chứa kiến thức kỹ thuật (cấu trúc addon, bẫy code, giải pháp đã kiểm chứng) — áp dụng chung cho mọi addon cùng dạng pattern. Quy trình làm việc (đọc log trước, xin duyệt plan, verify sau khi sửa...) được quản lý tập trung trong `AGENTS.md` / `GEMINI.md` ở cấp workspace/global, không lặp lại ở đây để tránh 2 nguồn quy tắc lệch nhau theo thời gian.

---

## 8. KỸ THUẬT NÂNG CAO — Bài học từ phân tích extension myfaveTT (19/07/2026)

### I. Header Hijacking — Mượn chữ ký xác thực của chính trình duyệt

**Bối cảnh:** API có cơ chế chống bot phức tạp (token động, cookie, chữ ký như X-Bogus). Không thể tự tạo token hợp lệ từ bên ngoài.

**Ý tưởng:** Thay vì tự tạo token → để trình duyệt tạo token khi người dùng lướt web bình thường → intercept header đó rồi tái sử dụng.

```javascript
// background.js (service worker):
chrome.webRequest.onSendHeaders.addListener(
  function(details) {
    const { requestHeaders, url } = details;
    const ch = new BroadcastChannel("mychannel");
    ch.postMessage({ type: "HEADERS_INTERCEPTED", payload: { requestHeaders, url } });
    ch.close();
  },
  { urls: ["https://api.target.com/endpoint/*"] },
  ["requestHeaders"]
);
```

**Lưu ý:** Khai báo `"webRequest"` trong `permissions` và URL pattern trong `host_permissions`. Token có thời hạn — cần logic re-intercept.

---

### J. BroadcastChannel Collision — Xung đột kênh khi fork extension

**Hiện tượng:** Fork extension + load cả 2 bản → một bản bị block ngay khi khởi động với thông báo *"already running in another tab"*.

**Nguyên nhân:** `BroadcastChannel("tenkenh")` hoạt động trên **toàn bộ trình duyệt**. 2 extension dùng chung tên → handshake khởi động bị phản hồi bởi extension kia → block nhau.

**Giải pháp:** Khi fork, đổi tên kênh sang tên độc nhất, **đồng bộ ở TẤT CẢ các file** (background.js, content_script.js, relay script):
```javascript
// Bản gốc:  new BroadcastChannel("myfaveTT")
// Bản fork: new BroadcastChannel("mycustomFaveTT")
```

---

### K. Iframe `src` — Đường dẫn tương đối bị resolve sai origin

**Hiện tượng:** `iframe.src = "ui_offline/index.html"` → iframe trắng, không load được file.

**Nguyên nhân:** Script chạy trong context trang host (VD: `tiktok.com`) → resolve thành `tiktok.com/ui_offline/index.html` → 404.

**Giải pháp:** Dùng `chrome.runtime.getURL()`:
```javascript
// SAI:
iframe.src = "ui_offline/index.html";

// ĐÚNG:
iframe.src = chrome.runtime.getURL("ui_offline/index.html");
// → chrome-extension://[id]/ui_offline/index.html
```

File phải được khai báo trong `web_accessible_resources` của `manifest.json`.

---

### L. Fork Extension Offline — Checklist tách bản gốc thành bản Standalone

```
1. TẢI SOURCE:    Tải CRX → tìm ZIP magic bytes (PK\x03\x04) → giải nén
2. PHÂN TÍCH:     Đọc manifest.json → Grep tất cả https:// → liệt kê phụ thuộc
3. XÓA KEY:       Xóa trường "key" trong manifest → Chrome tạo ID mới, không ghi đè bản gốc
4. ĐỔI CHANNEL:   Đổi tên BroadcastChannel sang tên độc nhất
5. CÀO UI:        Scrape HTML/CSS/JS từ server UI về thư mục ui_offline/
6. SỬA LOADER:    iframe.src = chrome.runtime.getURL("ui_offline/index.html")
7. MANIFEST:      Thêm "ui_offline/*" vào web_accessible_resources
8. BYPASS AUTH:   Tìm biến kiểm soát xác thực → set = true khi khởi tạo
9. UNLOCK CAP:    Tìm hàm giới hạn số lượng → tăng lên 9999999
10. VERIFY:       Load unpacked → kiểm tra chạy song song với bản gốc
```

**Script Python tải và giải nén CRX:**
```python
import urllib.request, zipfile, io, os

def download_crx(ext_id, out_dir):
    url = (f"https://clients2.google.com/service/update2/crx"
           f"?response=redirect&prodversion=114.0"
           f"&x=id%3D{ext_id}%26uc")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as r:
        crx = r.read()
    start = crx.find(b'PK\x03\x04')  # ZIP magic bytes
    with zipfile.ZipFile(io.BytesIO(crx[start:])) as z:
        z.extractall(out_dir)
```

