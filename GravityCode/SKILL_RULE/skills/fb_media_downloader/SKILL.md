---
name: "fb_media_downloader"
description: "Hướng dẫn vận hành, bảo trì và phát triển Extension tự động trích xuất media (ảnh HD, video) và unlike bài viết trên Facebook Activity Log theo điều kiện độ dài ký tự."
---

# Kỹ năng Facebook Liked Media Downloader & Unlike (Anti-Ban Safe)

Tài liệu tổng hợp kiến trúc, cơ chế chống ban Facebook (Anti-Ban Engine), bộ quy chuẩn thư mục tách biệt (image/ vs video/), kỹ thuật chẩn đoán DOM thực tế và giải pháp trích xuất media tab ngầm loại bỏ ảnh bình luận.

---

## 1. Cấu Trúc Dự Án (Manifest V3)

```
DownloadImgFacebook/
├── ProjectLog.md                           # Nhật ký phát triển và kiểm thử
├── FacebookLikedMediaAddon/
│   ├── manifest.json                       # Khai báo permissions: downloads, storage, scripting, activeTab, tabs
│   ├── icons/                              # icon16, icon48, icon128 (PNG)
│   ├── background.js                       # Tab Watcher, điều phối tải file tách image/ và video/, bộ lọc comment
│   ├── popup.html & popup.css & popup.js   # Giao diện Anti-Ban, bộ đếm cooldown, Debug DOM và console log
│   └── content_script.js                   # Trích xuất DOM Activity Log, đo ký tự, điều phối tab ngầm, unlike an toàn
└── .agents/skills/fb_media_downloader/
    └── SKILL.md                            # Kỹ năng này
```

---

## 2. Quy Tắc Nghiệp Vụ Cốt Lõi

### A. Quy tắc đếm ký tự bài viết (Ngưỡng 500 ký tự)
- **Bài viết $\le 500$ ký tự**:
  - Trích xuất toàn bộ hình ảnh độ phân giải cao và video của bài viết chính.
  - Tải ảnh vào thư mục `image/`, video vào thư mục `video/`.
  - Thực hiện **Hủy Thích (Unlike)**.
- **Bài viết $> 500$ ký tự**:
  - **ĐỂ NGUYÊN HOÀN TOÀN**: Không tải hình ảnh, không tải video, và **KHÔNG HỦY THÍCH**.
  - Đánh dấu đã duyệt vào bộ nhớ đệm và bỏ qua ngay sang bài viết tiếp theo.

### B. Quy chuẩn lưu trữ file phẳng trực tiếp (`background.js`)
File tải về qua `chrome.downloads` được lưu phẳng trực tiếp vào từng nhóm thư mục cha (không tạo subfolder con lồng nhau), có timestamp giờ phút trích xuất từ bài viết để Windows Explorer tự sắp xếp chuẩn xác từ mới nhất đến cũ nhất:
- Ảnh: `Downloads/FB_Liked_Media/image/Post_{YYYYMMDD}_{HHmm}_{ID}_img_01.jpg`
- Video: `Downloads/FB_Liked_Media/video/Post_{YYYYMMDD}_{HHmm}_{ID}_video_01.mp4`
- Tóm tắt: `Downloads/FB_Liked_Media/post_info/Post_{YYYYMMDD}_{HHmm}_{ID}_info.txt`

---

## 3. Các Kỹ Thuật Bóc Tách DOM Thực Chiến Trên Facebook

### A. Kỹ thuật chẩn đoán DOM trực tiếp & Quản lý Bộ Nhớ Đệm (Cache)
- **Live DOM Debugger:** Sử dụng handler `DEBUG_SCAN` trên content script và nút `🔬 Debug DOM` trên Popup để dump cấu trúc thực tế khi Facebook đổi giao diện.
- **Quản lý Cache (`processedIds`):** Để tránh tải trùng hoặc spam bot, tiện ích tự động lưu ID bài viết đã duyệt vào `fb_processed_cache`. Khi muốn quét lại toàn bộ bài cũ từ đầu, bắt buộc bấm nút **`🧹 Reset Cache`** trên giao diện chính.
- **Copy Log:** Bật `user-select: text` và nút `📋 Copy Log` cho phép người dùng 1 click sao chép toàn bộ log để báo cáo sự cố ngay lập tức.


### B. Bộ Selector chuẩn trên Activity Log (Nhật ký hoạt động)
Facebook tiếng Việt hiện đại không dùng các chuẩn menu cổ điển:
1. **Nút 3 chấm thao tác:** Dùng `div[role="button"][aria-haspopup="dialog"]` với nhãn bắt đầu bằng:
   - `aria-label*="Lựa chọn khác cho [Tên người dùng] thích..."` hoặc `aria-label*="More options"`.
   - **Lưu ý lọc tọa độ:** Bỏ qua các nút ở thanh điều hướng trên cùng (`rect.top <= 120px`).
2. **Container từng dòng:** Leo ngược cây DOM từ nút 3 chấm để tìm phần tử cha chứa cả nút 3 chấm và thẻ `<a href>` dẫn đến bài viết gốc (`/posts/`, `permalink.php`, `story_fbid`).
3. **Định danh ID bài viết:** Facebook hiện đại dùng chuỗi Base64 `pfbid...`. Regex bắt buộc hỗ trợ chuỗi alphanumeric:
   ```javascript
   /(?:posts\/|story_fbid=|fbid=|\/reel\/|photo\.php\?fbid=)([a-zA-Z0-9_]+)/
   ```
4. **Nút Hủy Thích (Unlike):** Khi click nút 3 chấm, Facebook mở dialog chứa các lựa chọn. Selector cần tìm cả `div[role="button"]`, `div[role="menuitem"]` và `span[dir="auto"]` với các từ khóa:
   - `"bỏ thích"`, `"unlike"`, `"gỡ"`, `"gỡ cảm xúc"`, `"gỡ biểu cảm"`, `"xóa lượt tương tác"`.

---

## 4. Kiến Trúc Tab Ngầm & Bộ Lọc Media Bài Viết Chính (Chống Tải Ảnh Comment)

### A. Cơ chế Tab Nền Ngầm (Background Tab Watcher)
- **Vấn đề sống còn:** Tuyệt đối **KHÔNG click nút "Xem"** trên tab Activity Log chính. Thao tác này sẽ kích hoạt SPA navigation làm Facebook điều hướng tab hiện tại sang bài viết $\rightarrow$ Mất trang Activity Log $\rightarrow$ Quy trình bị đứt và không thể thực hiện Unlike.
- **Giải pháp:**
  1. Content script lấy URL permalink từ container bài viết.
  2. Gửi message `OPEN_PERMALINK_TAB` sang `background.js`.
  3. `background.js` gọi `chrome.tabs.create({ url, active: false })` để mở tab con ở chế độ nền.
  4. Đợi 1.5s cho Facebook SPA render DOM hoàn chỉnh $\rightarrow$ Inject hàm `extractMediaFromPermalinkPage`.
  5. Sau khi thu thập xong media, gửi kết quả về tab chính và gọi `chrome.tabs.remove(tabId)` để đóng tab con.
  6. Tab chính (Activity Log) không bị gián đoạn, thực hiện tải media và Unlike bình thường.

### B. Bộ lọc 4 lớp loại bỏ hoàn toàn ảnh bình luận (Comment Filtering)
Khi mở trang bài viết, Facebook tải cả ảnh của người bình luận (như ảnh bó hoa, meme hoạt hình, avatar). Để chỉ lấy ảnh của bài đăng chính:
1. **Lớp 1 - Vạch ranh giới (`boundaryTop`):**
   - Tìm vị trí của thanh nút tương tác (chứa nút *Thích*, *Bình luận*, *Chia sẻ*).
   - Mọi ảnh có `rect.top >= boundaryTop` đều nằm ở khu vực bình luận $\rightarrow$ **Loại bỏ 100%**.
2. **Lớp 2 - Loại trừ container comment:**
   - Dùng `img.closest()` kiểm tra `[aria-label*="Bình luận"]`, `[aria-label*="Comment"]`, `[role="article"]` của bình luận, `ul[role="list"]`.
3. **Lớp 3 - Lọc sticker / nhãn dán / emoji:**
   - Kiểm tra `img.alt`: Bỏ qua ảnh có alt chứa "nhãn dán", "sticker", "biểu tượng", "icon".
4. **Lớp 4 - Lọc kích thước:**
   - Bỏ qua ảnh có `width < 150px` hoặc `height < 150px` (loại trừ avatar người bình luận và icon nhỏ).

---

## 5. Bộ Giải Pháp Chống Khóa Tài Khoản Facebook (Anti-Ban Engine)

1. **Jitter Delay ngẫu nhiên**:
   - Khoảng cách giữa các bài: `4.5s – 8.5s` ngẫu nhiên.
   - Thao tác click menu / nút bấm: `900ms – 1800ms`.
2. **Nghỉ giải lao định kỳ (Cool-down Break)**:
   - Cứ sau mỗi **5 bài** unlike, tạm dừng hoàn toàn `25s – 45s` có đếm ngược để phá vỡ nhịp điệu đều đặn của bot.
3. **Giới hạn số bài mỗi phiên (Session Quota)**:
   - Mặc định tối đa 30 bài/phiên để tránh thao tác dồn dập trong thời gian ngắn.
4. **Cuộn trang tự nhiên (Natural Smooth Scroll)**:
   - Cuộn từng nấc ngắn 300px - 600px kèm độ trễ nhỏ mô phỏng ngón tay/chuột người dùng.
5. **KeepAlive Engine kép (Web Locks + Silent Audio)**:
   - Ngăn chặn Chrome bóp xung nhịp (throttle) khi người dùng thu nhỏ trình duyệt.
6. **Mã Hóa Base64 UTF-8 Hai Chiều Đối Xứng**:
   - Áp dụng cặp hàm `encodeBase64Utf8` / `decodeBase64Utf8` bằng `TextEncoder`/`TextDecoder` để lưu trữ dữ liệu cache trong `chrome.storage.local` an toàn tuyệt đối.

---

## 6. Hướng Dẫn Vận Hành An Toàn

1. Mở Chrome/Edge với profile Facebook chính.
2. Vào `chrome://extensions`, bật Developer Mode $\rightarrow$ Chọn `Load unpacked` thư mục `FacebookLikedMediaAddon` (hoặc bấm 🔄 Reload nếu đã cài).
3. Mở link [Nhật ký hoạt động bài viết đã thích](https://www.facebook.com/100007948240441/allactivity?activity_history=false&category_key=LIKEDPOSTS&manage_mode=false&should_load_landing_page=false).
4. Mở Popup tiện ích:
   - Bấm **`🔍 Thử Quét Dòng`** để kiểm tra số bài viết nhận diện trên viewport.
   - Bấm **`🔬 Debug DOM`** nếu cần chẩn đoán sâu cấu trúc DOM.
   - Bấm **`▶ Bắt Đầu Quét An Toàn`** để tiến trình tự động chạy.
5. Tiện ích sẽ mở tab nền ngầm tải media bài viết chính $\rightarrow$ tự đóng tab con $\rightarrow$ Unlike bài $\le 500$ ký tự $\rightarrow$ nghỉ Cooldown an toàn sau mỗi 5 bài.

## Live checks through OpenClaw

For a user-authorized live Facebook tab, read and follow the companion skill `openclaw-fb-addon-check`. It defines the dedicated-test-tab rule, read-only diagnostic commands, DASH-fragment versus complete-MP4 classification, and the required `ProjectLog.md` record.

## Addon Background Runner

## Video-only Unlike gate

A caption-less video-only post may be unliked only after the direct downloader or Reel mux helper reports success. A failed, skipped, or unverified video download must retain the Like. The verified-text length safeguard still takes precedence for posts over the configured threshold.

If that confirmed video download succeeds but Facebook rejects the Unlike click, store the post ID in `fb_pending_unlike_cache`. On a later scan, retry only the Unlike action once per session, without reopening the permalink or downloading the video again. Remove the pending ID only after an Unlike success.

The primary runner is `FacebookMediaHelper/background_runner.py` in this addon project, with `start_background.cmd` and `stop_background.cmd`. It starts a separate Chrome user-data directory with `--start-minimized` plus the local Reel helper. It must not use Chrome headless mode because the Facebook extension and authenticated session require a normal browser context. AskCpl may display optional controls, but only references this addon-owned runner.

- The first launch of a new profile requires the user to sign in to Facebook and load the unpacked extension once.
- Start/stop operations must use the runner's recorded PIDs only; never kill all Chrome processes.
- The optional Windows logon task is created or removed only through an explicit user action, whether from the launcher controls or AskCpl's reference UI.
- The helper can run background-only, but scan and Unlike still require this minimized authenticated Chrome process.
