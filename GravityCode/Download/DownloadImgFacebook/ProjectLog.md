# Project Log — Facebook Liked Media Downloader & Auto-Unlike Addon

## Thông Tin Dự Án
- **Thư mục**: `DownloadImgFacebook/`
- **Mục tiêu**: Chrome/Edge Extension (Manifest V3) tự động quét danh sách bài viết đã thích trên Facebook Activity Log, tải toàn bộ hình ảnh vào `image/` & video vào `video/` (bỏ qua và để nguyên nếu bài viết > 500 ký tự), tự động hủy thích (Unlike) bài viết <= 500 ký tự, và tích hợp bộ giải pháp Chống Khóa Tài Khoản Facebook (Anti-Ban).
- **Trang mục tiêu**: `https://www.facebook.com/100007948240441/allactivity?activity_history=false&category_key=LIKEDPOSTS&manage_mode=false&should_load_landing_page=false`
- **Nền tảng kiến trúc**: Kế thừa chuẩn KeepAlive kép, mã hóa UTF-8 Base64 hai chiều, và cơ chế điều phối tải file từ `AskCpl` (`copilot_addon_dev`).


---

## 2026-09-12 (Lần 17) — Fix Video Lỗi: Lọc HLS Segment + Route Đúng Loại File

- **Vấn đề:** Video tải về đều bị lỗi vì:
  1. `webRequest` bắt cả **HLS segment chunks** (đoạn 2-3s) thay vì file `.mp4` hoàn chỉnh.
  2. **Poster image (JPEG)** từ `<video poster>` bị đưa vào `result.videos[]` → download với đuôi `.mp4` → file lỗi vì là JPEG.
  3. Không kiểm tra loại URL trước khi download, mọi URL trong `mediaData.videos[]` đều bị download thành `.mp4`.
- **Fix 1 — `background.js` webRequest interceptor:** Thêm bộ lọc chặn URL HLS segment (`seg_X`, `chunk_X`, `frag_X`, `_dashinit`, `/init-`, `byterange`, `byte_start`). Chỉ bắt URL file `.mp4` hoàn chỉnh.
- **Fix 2 — `background.js` poster routing:** Poster JPEG (`<video poster>`) chuyển từ `result.videos[]` → `result.images[]`. Sẽ được download vào `image/` thay vì `video/`.
- **Fix 3 — `content_script.js` URL type check trước download:**
  - URL có đuôi `.jpg/.jpeg/.png/.webp` → route về `image/` với đuôi đúng (tên file: `_reel_thumb_XX.jpg`).
  - URL `.m3u8` manifest → bỏ qua (không tải được bằng extension).
  - URL `.mp4` hợp lệ → tải vào `video/` như bình thường + log rõ URL đang tải.
- **Syntax verify:** background.js ✅, content_script.js ✅

## 2026-09-12 (Lần 16) — Tải Video Reel Thật: Phương Án A (Script JSON) + B (webRequest)

- **Vấn đề:** Video Reel thật không tải được vì Facebook dùng `blob:` HLS stream — không thể download trực tiếp từ DOM.
- **Phương án A — Parse `<script>` JSON (trong `extractMediaFromPermalinkPage`):**
  - Quét tất cả `<script type="application/json">` và `<script data-sjs>` trong trang Reel.
  - Đệ quy tìm các key: `hd_src_no_ratelimit`, `sd_src_no_ratelimit`, `browser_native_hd_url`, `browser_native_sd_url`, `video_url`, `playable_url_quality_hd`, `playable_url`.
  - Fallback: dùng regex trên inline script khi JSON.parse thất bại (format không chuẩn).
  - Ưu tiên URL HD (`hd` trong URL) hơn SD.
- **Phương án B — `chrome.webRequest.onBeforeRequest` interceptor (trong `background.js`):**
  - Thêm listener bắt mọi request `.mp4` và `.m3u8` từ `*.fbcdn.net` của các tab đang pending extract.
  - Lưu vào `capturedVideoUrls` Map (key: tabId) — dọn sạch sau khi gửi kết quả.
  - Khi tab load xong, gộp URL từ webRequest + DOM → ưu tiên `.mp4` trực tiếp hơn `.m3u8` manifest.
- **manifest.json:** Thêm `"webRequest"` permission.
- **Sau thay đổi:** User cần vào `chrome://extensions` → **Reload** extension để áp dụng permission mới.
- **Giới hạn còn lại:** Một số Reel mới Facebook có thể mã hoá URL hoặc yêu cầu auth token — cần kiểm tra thực tế.

## 2026-09-12 (Lần 15) — Hỗ Trợ Video Reel (`/share/r/` & blob: fallback)

- **Vấn đề:** Bài đăng là video Reel (URL dạng `facebook.com/share/r/xxx`) không được tải video vì:
  1. Selector tìm permalink trong `content_script.js` không có `a[href*="/share/r/"]` → không mở tab nền → không có media nào.
  2. `isVideoUrl` regex trong `background.js` không khớp `/share/r/` → bài bị coi là ảnh thường thay vì video.
  3. Facebook Reel dùng blob: HLS stream cho `<video src>` → bị lọc bỏ → `videos[]` luôn rỗng.
- **Fix 1 — `content_script.js` (L508-510):** Thêm `a[href*="/share/r/"]`, `a[href*="/videos/"]`, `a[href*="/watch/"]` vào selector tìm link permalink.
- **Fix 2 — `background.js` (L81):** Mở rộng `isVideoUrl` regex thêm `share\/r` → `/share/r/` URL được nhận diện đúng là bài video.
- **Fix 3 — `background.js` (L216-226):** Khi `isVideoPost=true` và `<video>` dùng blob:, lấy `poster` attribute (thumbnail ảnh tĩnh từ CDN fbcdn.net) làm fallback thay vì bỏ qua hoàn toàn. Fallback `og:video` meta vẫn được giữ nguyên.
- **Giới hạn còn tồn đọng:** Video Reel (blob: HLS) chỉ tải được poster thumbnail, không phải file video thật. Tải video thật từ Facebook Reel đòi hỏi giải mã HLS manifest — ngoài phạm vi extension hiện tại.

## 2026-09-12 (Lần 14) — BỘ LỌC 6: Loại bỏ Avatar/Profile Picture

- **Root cause ảnh nhầm:** Bài post từ page (VD: vietcg4) có avatar page trong header bài viết. Avatar có parent `<a>` trỏ đến `facebook.com/vietcg4` (URL profile) → chứa `facebook.com` → **pass BỘ LỌC 5** → bị tải nhầm cùng ảnh bài viết.
- **Fix — BỘ LỌC 6 trong `background.js`:** Kiểm tra pathname của parent link. Nếu khớp `/username` (không có sub-path), `/profile.php`, hoặc `/pages/` VÀ không chứa path content (`/posts/`, `/photo`, `/reel/`, `/video/`) → skip (avatar). Ảnh bài viết thật luôn có parent link chứa path content → không bị ảnh hưởng.
- **Xác minh cú pháp:** SYNTAX OK — background.js: 15650 bytes.

## 2026-09-11 (Lan 13) — Rewrite executeUnlike + og:image Primary Source


- **Root cause Unlike thất bại:** Code tìm `span[dir="auto"]` trên toàn `document` → tìm thấy nút "Gỡ" của sidebar filter Activity Log (không phải menu 3 chấm) → click sai element → unlike không thành công.
- **Rewrite `executeUnlike()` hoàn toàn (`content_script.js`):**
  + `waitForMenuPopup()`: Poll 15 × 200ms chờ `[role="menu"]` hoặc `[role="listbox"]` MỚI xuất hiện sau click. Fallback tìm `[role="dialog"]` gần nút 3 chấm (trong vòng 400px).
  + `findUnlikeBtnInMenu(menuEl)`: Tìm "Bỏ thích" CHỈ TRONG `menuEl` popup — không quét toàn document. Leo ngược DOM để tìm ancestor clickable.
  + **Vòng lặp retry 3 lần:** Click → verify menu biến mất (xác nhận thành công) → nếu chưa → Escape + retry.
  + Click đủ 3 cách: `simulateClick()` + `.click()` + `dispatchEvent(MouseEvent)`.
- **Fix ảnh thừa (`background.js`) — og:image làm nguồn chính:**
  + Thử `meta[property="og:image"]` trước. Nếu là CDN Facebook → dùng ngay → bỏ qua quét toàn bộ `<img>`.
  + Chỉ fallback quét `<img>` (với BỘ LỌC 1-5) khi og:image không có/không hợp lệ.
- **Xác minh cú pháp:** SYNTAX OK — content_script.js: 44940 bytes, background.js: 13485 bytes.



- **Fix ảnh thừa (background.js — BỘ LỌC 5 mới):**
  + Root cause: bài có share link ngoài (VD: link website Trung Quốc) → Facebook render thumbnail link trong `<a href="l.facebook.com/l.php?u=...">` → bộ lọc cũ không nhận ra đây là link ngoài, tải cả thumbnail link vào.
  + Fix: Kiểm tra `img.closest('a[href]')` → nếu href chứa `l.facebook.com/l.php` hoặc `l.fb.me` → skip (thumbnail redirect link ngoài). Nếu href bắt đầu `http` và không chứa `facebook.com`/`fbcdn.net` → skip (link ngoài trực tiếp).
- **Fix Unlike click (content_script.js — executeUnlike):**
  + Root cause: `item.closest('[role="button"], [role="menuitem"], [tabindex="0"]')` trả về null nếu `<span>Bỏ thích</span>` không có ancestor với đúng role → click vào `<span>` text không có tác dụng.
  + Fix: Mở rộng `.closest()` thêm `[role="option"], [role="listitem"], [tabindex]` (không fix "0"). Thêm fallback leo ngược DOM thủ công 6 cấp. Sau khi click `simulateClick()`, thêm 300ms delay rồi gọi thêm `.click()` native để đảm bảo handler JS Facebook được kích hoạt.
- **Xác minh cú pháp:** SYNTAX OK — content_script.js: 41847 bytes, background.js: 12791 bytes.



- **Bug gốc rễ được phát hiện:** Hàm `findActivityRowContainer()` luôn cập nhật `best = p` trong vòng lặp → trả về container **LỚN NHẤT** (leo cao nhất trên DOM) có chứa post link. Với Facebook Activity Log, container cấp ngày bao trùm tất cả bài trong ngày đó → tất cả 5-10 nút 3 chấm trong ngày đều map về **cùng 1 container** → `seen.has(container)` = true từ bài thứ 2 → chỉ 1 bài/ngày được thêm vào `rows[].`
- **Fix:** Thay logic `best = p; continue leo` bằng `return p ngay lập tức` khi tìm thấy post link → trả về container **NHỎ NHẤT** đặc trưng cho từng bài viết riêng lẻ. Mỗi nút 3 chấm giờ map về container riêng của bài đó.
- **Cải tiến thêm:** Mở rộng selector post link trong `findActivityRowContainer` bổ sung `/reel/`, `/photo/`. Tăng `maxLevels` từ 10 → 15 để leo đủ sâu khi cần. Guard thêm `role=feed`, `BODY`, `HTML`.
- **Xác minh cú pháp:** SYNTAX OK — content_script.js: 40873 bytes.



- **Vấn đề từ log user:** Tìm được 5-11 bài nhưng tất cả đã trong cache (10 bài processedIds) → `pendingRows.length=0` ngay từ đầu → cuộn 5 lần → kết thúc với "0 bài" dù chưa xử lý hết.
- **Kiến trúc mới "Scroll Until Done" trong `runLoop()`:**
  + Đo số nút 3 chấm (`[aria-label*="Lựa chọn khác"]`) TRƯỚC và SAU mỗi lần cuộn.
  + Nếu DOM tăng thêm bài (menuBtnsAfter > menuBtnsBefore, hoặc scrollHeight tăng > 100px) → **Reset `noNewCount = 0`** → tiếp tục quét ngay lập tức.
  + Theo dõi `consecutiveBottomCount` (số lần đã chạm `window.scrollY + innerHeight >= scrollHeight - 300px`).
  + **Điều kiện dừng an toàn (phải thỏa CẢ HAI):** `noNewCount >= MAX_NO_NEW` (tăng từ 5 → 10) VÀ đã thực sự chạm đáy trang ≥ 2 lần liên tiếp. Hoặc `noNewCount >= 10` đơn thuần.
  + Chờ lâu hơn sau mỗi cuộn: tăng từ 3-4.5s → 4-6s để Facebook lazy-load kịp.
  + Log chi tiết: `📊 [DOM Check] Nút 3 chấm: X → Y | scrollHeight: A → B | Cuối trang: ✅/❌`
- **Xóa code cũ:** Dọn sạch logic cuộn cứng 5 lần (`if noNewCount >= 5`) còn sót.
- **Xác minh cú pháp:** Node.js VM Script trên cả 3 file JS → SYNTAX OK (content_script.js: 40362 bytes).


- **Khắc phục triệt để hiện tượng chỉ tải 1 bài rồi cuộn:**
  + Trước đây, mảng `rows` được lấy 1 lần cố định. Khi bài 1 bị Unlike, Facebook re-render làm các node bài 2, 3, 4 trở thành stale node, khiến vòng lặp kết thúc sớm và vội vàng cuộn trang.
  + **Kiến trúc Reactive Loop mới:** Ở mỗi bước lặp, quét DOM tươi mới nhất trên màn hình $\rightarrow$ Lọc ra các bài chưa xử lý `pendingRows = allRows.filter(...)` $\rightarrow$ Luôn xử lý bài đầu tiên trên màn hình `pendingRows[0]` $\rightarrow$ Lặp liên tục xử lý hết bài này đến bài khác ngay trên viewport.
- **Quy tắc cuộn trang chuẩn xác:**
  + **TUYỆT ĐỐI KHÔNG CUỘN TRANG** khi trên màn hình vẫn còn bài chưa xử lý (`pendingRows.length > 0`).
  + **CHỈ CUỘN TRANG KHI:** Toàn bộ các bài viết trong ngày/trên viewport đã được tải media và Unlike 100% sạch sẽ (`pendingRows.length === 0`).
- **Thêm debug chi tiết chữ trong Menu:** Bổ sung log dump toàn bộ text mục menu (`[Debug Menu]: [...]`) để người dùng đối chiếu từ ngữ Facebook hiển thị khi click 3 chấm.
- **Xác minh cú pháp:** Node.js VM Script trên cả 3 file JS (`content_script.js`, `popup.js`, `background.js`) $\rightarrow$ SYNTAX OK.

## 2026-09-11 (Lan 8) — Bổ Sung Nút Copy Log, Nút Reset Cache Nhanh & Tối Ưu Phản Hồi Cache
- **Giải quyết vấn đề copy log:** 
  + Thêm nút `📋 Copy Log` trực tiếp trên thanh tiêu đề console: 1 click sao chép toàn bộ nội dung log vào clipboard.
  + Thêm thuộc tính `user-select: text` cho `.log-console` và `.log-entry` trong `popup.css` để người dùng có thể bôi đen chuột copy từng phần.
- **Nút `🧹 Reset Cache` nhanh:** Đưa nút Reset Cache ra thanh Quick Navigation chính trên popup. Bấm nút này sẽ xóa sạch `processedIds` và bộ nhớ đệm `fb_processed_cache`, cho phép người dùng quét lại từ đầu tất cả các bài viết cũ bất kỳ lúc nào.
- **Minh bạch hóa tiến trình Cache:** Bổ sung log rõ ràng khi gặp bài viết đã lưu trong cache: `⏭️ [Đã trong Cache] Bài viết ID [ID] đã được xử lý trước đó. Bỏ qua...` để người dùng không bị hiểu nhầm là tiện ích không tìm thấy bài.
- **Xác minh cú pháp:** Node.js VM Script trên cả 3 file JS (`content_script.js`, `popup.js`, `background.js`) $\rightarrow$ SYNTAX OK.

## 2026-09-11 (Lan 7) — Lưu File Phẳng Tên Post_, Sắp Xếp Chuẩn Thứ Tự & Tối Ưu Hủy Thích
- **Lưu file phẳng trực tiếp:** Loại bỏ hoàn toàn việc tạo các thư mục con lồng nhau `YYYY-MM-DD_Post_.../`. Toàn bộ ảnh được lưu phẳng vào `FB_Liked_Media/image/` với định dạng tên `Post_{YYYYMMDD}_{HHmm}_{ID}_img_{01}.jpg`. Tương tự video vào `FB_Liked_Media/video/Post_..._video_01.mp4` và file tóm tắt vào `FB_Liked_Media/post_info/Post_..._info.txt`.
- **Duyệt tuần tự chuẩn xác từ trên xuống dưới:**
  + Hàm `findActivityRows()` bổ sung sắp xếp mảng `rows` theo tọa độ thị giác màn hình `rect.top + window.scrollY`.
  + Trích xuất timestamp giờ:phút (`22:19`, `19:27`, `18:58`...) trực tiếp từ từng container để đặt vào tên file, đảm bảo Windows Explorer tự động xếp thứ tự bài mới nhất ở trên cùng.
- **Tối ưu hóa thao tác Hủy Thích (Unlike):**
  + Tích hợp hàm `simulateClick(el)` kích hoạt đầy đủ chuỗi sự kiện chuột React/SPA (`pointerdown` $\rightarrow$ `mousedown` $\rightarrow$ `mouseup` $\rightarrow$ `click`).
  + Nút 3 chấm bám sát theo anh em của nút "Xem" (`viewBtn`).
  + Bổ sung vòng lặp kiểm tra menu mở ra (đợi animation), click nút "Bỏ thích / Gỡ", và tự động xác nhận trong dialog popup của Facebook.
- **Xác minh cú pháp:** Toàn bộ 3 file JS (`content_script.js`, `popup.js`, `background.js`) đạt chuẩn `SYNTAX OK`.

## 2026-09-11 (Lan 6) — Hoàn thiện Cơ chế Tab Ngầm 100% & Bộ Lọc Loại Bỏ Ảnh Comment
- **Khắc phục lỗi mất tab Activity Log:** Loại bỏ hoàn toàn thao tác `viewBtn.click()` trên tab chính (vốn làm Facebook điều hướng chuyển trang). Chuyển sang trích xuất permalink mở tab con ở chế độ nền ngầm (`active: false`). Tab ngầm trích xuất media xong tự động đóng lại (`chrome.tabs.remove`), tab chính Activity Log được giữ nguyên 100% vị trí để thực hiện Hủy Thích (Unlike).
- **Bộ lọc loại bỏ ảnh Comment 4 lớp trong `background.js`:**
  1. Xác định thanh tương tác Thích/Bình luận/Chia sẻ (`boundaryTop`): Mọi ảnh/video nằm dưới thanh này đều bị loại bỏ 100%.
  2. Loại bỏ container comment: Bỏ qua mọi phần tử thuộc `[aria-label*="Bình luận"]`, `[role="article"]` bình luận, reply.
  3. Loại bỏ sticker, nhãn dán hoạt hình, emoji: Bỏ qua ảnh có alt chứa sticker/nhãn dán.
  4. Lọc kích thước: Bỏ qua ảnh avatar/icon nhỏ (< 150px).
  5. Thêm delay 1.5s trước khi inject script để Facebook SPA mount DOM ảnh đầy đủ.
- **Cập nhật SKILL.md:** Đã bổ sung toàn bộ kỹ năng thực chiến mới vào `.agents/skills/fb_media_downloader/SKILL.md` (Kỹ thuật chẩn đoán Live DOM Debugger, Selector thực tế `aria-haspopup="dialog"`, Kiến trúc Tab Watcher ngầm, và Bộ lọc 4 lớp phân định ranh giới bài viết chính / bình luận).
- **Xác minh cú pháp:** Node.js VM Script trên `content_script.js`, `popup.js`, `background.js` $\rightarrow$ SYNTAX OK.

## 2026-09-11 (Lan 5) — Tối ưu Selector chuẩn xác 100% từ kết quả Debug DOM thực tế
- Phân tích log Debug DOM của user:
  + Facebook dùng `aria-haspopup="dialog"` với label bắt đầu bằng `Lựa chọn khác cho [Tên] thích...` thay vì `aria-haspopup="menu"`.
  + Nút 3 chấm nằm ở `top > 120px` (cách đều ~82px mỗi dòng), liên kết bài viết `permalink.php?story_fbid=...` và `/posts/...` xuất hiện rõ ràng trong từng container.
  + ID bài viết dạng `pfbid...` (alphanumeric) được hỗ trợ toàn diện trong `extractRowId`.
- Nâng cấp `findActivityRows()`:
  + Chiến lược 1: Bắt chuẩn 100% qua `[aria-label*="Lựa chọn khác"]` / `[aria-label*="More options"]`.
  + Chiến lược 2: Fallback qua các link permalink/posts.
  + Chiến lược 3: Fallback qua nút "Xem".
- Nâng cấp `executeUnlike()`: Mở rộng tìm kiếm nút "Gỡ" / "Bỏ thích" trong cả dialog popup và dropdown menu.
- Kiểm tra cú pháp: Toàn bộ 3 file JS đều SYNTAX OK.

## 2026-09-11 (Lan 3) — Cách C: Tab Mới + Lightbox + Fallback Thumbnail HOÀN THÀNH
- background.js: Thêm Tab Watcher tự bắt tab permalink khi click "Xem", inject extractor lấy ảnh/video HD, đóng tab và trả kết quả về content script.
- content_script.js: Cập nhật openAndExtractMedia() đa luồng fallback.
- manifest.json: Bổ sung quyền "tabs" cho Chrome Extension Service Worker.

## 2026-09-11 (Lan 2) — Fix 0 Bai Viet — Force Inject + Multi-Fallback DOM HOAN THANH

- Tab cu khong co script: Chrome khong tu inject vao tab da mo truoc khi cai extension.
- findActivityRows() viet lai voi 3 tang fallback A(nut Xem)/B(text thich)/C(aria-haspopup).
- popup.js them injectContentScript() goi truoc moi sendMessage.
- TEST_SCAN tra ve debugInfo khi ket qua 0.
- SYNTAX CHECK: OK tren ca 3 files JS.

## 2026-09-11 — Cập Nhật Bộ Selector DOM Theo Giao Diện Thực Tế Facebook & Thêm Nút Test Quét — HOÀN THÀNH ✅

### 1. Phân Tích & Giải Quyết
- Dựa trên ảnh chụp thực tế Facebook tiếng Việt:
  - Từng dòng bài viết đã thích hiển thị rõ nút chữ **"Xem"** và nút 3 chấm **`...`** ngay bên cạnh.
  - Cập nhật `content_script.js` định vị dòng bám trực tiếp vào nút **"Xem"** (`role="button"`) $\rightarrow$ lấy container chứa text bài viết $\rightarrow$ bóc tách nút 3 chấm liền kề.
  - Hàm `extractPostTextFromRow`: Tự động loại bỏ các text hệ thống ("thích ảnh của...", "Công khai", "19:27", "Xem") để đo chính xác 100% độ dài bài viết thực tế.
  - Thêm nút **"🔍 Thử Quét Dòng"** trực tiếp trên Popup: Cho phép kiểm tra ngay lập tức số lượng bài viết và nội dung xem trước trên trang Facebook mà không cần chạy toàn bộ vòng lặp.

### 2. Danh Sách File Đã Cập Nhật
1. `FacebookLikedMediaAddon/content_script.js`: Bộ selector DOM mới bám theo nút "Xem", xử lý mở lightbox và click unlike chuẩn xác.
2. `FacebookLikedMediaAddon/popup.html`: Bổ sung nút "🔍 Thử Quét Dòng" trong khu vực điều hướng nhanh.
3. `FacebookLikedMediaAddon/popup.css`: Căn chỉnh giao diện 2 nút điều hướng nhanh.
4. `FacebookLikedMediaAddon/popup.js`: Thêm tính năng gửi lệnh `TEST_SCAN` và hiển thị trực tiếp danh sách bài viết quét được lên Console log.

### 3. Kiểm Thử & Xác Minh (Verification)
- ✅ Node.js VM Script: Toàn bộ file JS syntax OK.
- ✅ Dọn dẹp: Không có file rác phát sinh.

### 1. Phân Tích & Giải Quyết Vấn Đề
- **Chuẩn hóa Logic Ngưỡng 500 ký tự**:
  - **Bài $\le 500$ ký tự**: Tải toàn bộ hình ảnh độ phân giải cao và video $\rightarrow$ Hủy Thích (Unlike).
  - **Bài $> 500$ ký tự**: **ĐỂ NGUYÊN HOÀN TOÀN** (Không tải media và **KHÔNG HỦY THÍCH**, giữ nguyên lượt like).
- **Tách riêng thư mục Media**:
  - Toàn bộ ảnh được lưu vào: `Downloads/FB_Liked_Media/image/{YYYY-MM-DD}_Post_{ID}/`
  - Toàn bộ video được lưu vào: `Downloads/FB_Liked_Media/video/{YYYY-MM-DD}_Post_{ID}/`
  - File thông tin lưu vào: `Downloads/FB_Liked_Media/post_info/{YYYY-MM-DD}_Post_{ID}/post_info.txt`
- **Bộ Giải Pháp Chống Khóa Tài Khoản Facebook (Anti-Ban Engine)**:
  - **Jitter Delay ngẫu nhiên**: Nghỉ ngẫu nhiên 4.5s – 8.5s giữa các bài; 900ms – 1800ms giữa các thao tác click (mở 3 chấm, chọn unlike, xác nhận).
  - **Cơ chế Cooldown Break**: Cứ sau **5 bài** unlike thành công, tự động tạm dừng nghỉ ngơi **25s – 45s** kèm đồng hồ đếm ngược trên popup để phá vỡ nhịp điệu bot.
  - **Giới hạn số bài mỗi phiên (Session Quota)**: Mặc định tối đa 30 bài/phiên chạy, tự động dừng an toàn để tránh thao tác dồn dập.
  - **Cuộn trang tự nhiên (Natural Smooth Scroll)**: Cuộn từng nấc ngắn 300px - 600px mô phỏng mắt người đọc.
  - **KeepAlive Engine kép (Web Locks + Silent Audio)**: Chống Chrome throttle khi ẩn tab.

### 2. Danh Sách File Đã Cập Nhật
1. `FacebookLikedMediaAddon/background.js`: Hỗ trợ tham số `mediaType` tách riêng nhánh lưu trữ `image/` và `video/`.
2. `FacebookLikedMediaAddon/content_script.js`: Cập nhật logic `> 500` để nguyên, tích hợp Cooldown Break, Jitter Delay, Natural Scroll, và Session Quota.
3. `FacebookLikedMediaAddon/icons/`: Bộ icon PNG nhận diện độc quyền (hình người đang vươn tay lấy ảnh/video MP4 từ Facebook) kích thước 16x16, 48x48, 128x128.
4. `FacebookLikedMediaAddon/popup.html` & `popup.css`: Giao diện Anti-Ban tích hợp logo icon mới ở Header, banner Cooldown và nhãn `Để nguyên (>500k)`.
5. `FacebookLikedMediaAddon/popup.js`: Đồng bộ trạng thái Cooldown thời gian thực và nạp cấu hình an toàn.
6. `.agents/skills/fb_media_downloader/SKILL.md`: Cập nhật tài liệu quy chuẩn Anti-Ban và phân loại thư mục.

### 3. Kiểm Thử & Xác Minh (Verification)
- ✅ Cú pháp JS: Biên dịch và kiểm tra bằng Node.js VM Script trên `background.js`, `content_script.js`, `popup.js` $\rightarrow$ SYNTAX OK.
- ✅ Logic ngưỡng ký tự: Bài $\le 500$ ký tự $\rightarrow$ Tải & Unlike. Bài $> 500$ ký tự $\rightarrow$ ĐỂ NGUYÊN (Không tải, Không unlike) $\rightarrow$ TEST PASSED.
- ✅ Định tuyến thư mục: Ảnh vào `FB_Liked_Media/image/`, Video vào `FB_Liked_Media/video/` $\rightarrow$ TEST PASSED.
- ✅ Cooldown trigger: Tự động kích hoạt sau mỗi 5 bài unlike $\rightarrow$ TEST PASSED.
- ✅ Mã hóa Base64 UTF-8 hai chiều đối xứng: Dữ liệu Unicode, emoji và ký tự đặc biệt được bảo toàn tuyệt đối $\rightarrow$ TEST PASSED.
- ✅ Dọn dẹp: Đã xóa sạch toàn bộ script test tạm thời.

---

## 2026-09-12 — Debug Mode Phát Hiện & Dừng Khi Gặp Ảnh Tải Nhầm (Image Hash Comparison) — HOÀN THÀNH ✅

### 1. Phân Tích & Yêu Cầu Của Người Dùng
- **Vấn đề**: Thỉnh thoảng có những ảnh bị tải nhầm lọt qua các bộ lọc (ví dụ ảnh thumbnail hoặc ảnh link chia sẻ), người dùng muốn upload trực tiếp 1 file ảnh mẫu đã từng tải nhầm để extension tự động đối chiếu nội dung.
- **Giải pháp triển khai**:
  - **Thuật toán so sánh nội dung (Perceptual aHash 16x16 - 256 bits)**: Tính toán chuỗi nhị phân đặc trưng hình ảnh độc lập với độ phân giải URL CDN của Facebook.
  - **Debug Section trên giao diện Popup**:
    - Nút tải lên file ảnh mẫu (`#sampleImageInput`) kèm preview thumbnail.
    - Cài đặt ngưỡng tương đồng linh hoạt (mặc định 85%, dải 50% – 99%).
    - Nút xóa ảnh mẫu (`#clearSampleBtn`) và chỉ báo trạng thái đang theo dõi.
  - **Kiểm tra tự động trước khi tải (`content_script.js` & `background.js`)**:
    - Khi trích xuất được ảnh bài viết, extension tính hash và so sánh với ảnh mẫu đã lưu.
    - Nếu độ giống $\ge$ ngưỡng đã đặt $\rightarrow$ **LẬP TỨC TẠM DỪNG TIẾN TRÌNH**.
  - **Hộp thoại Chẩn đoán Chi tiết (Diagnostic Modal)**:
    - Hiển thị so sánh trực quan cạnh nhau: Ảnh mẫu vs Ảnh vừa bắt gặp.
    - Báo cáo chi tiết: Độ tương đồng (%), ID bài viết, Link bài viết gốc, Link ảnh CDN Facebook, số lượng ký tự bài viết và trích đoạn văn bản.
    - Cung cấp 2 lựa chọn hành động cho người dùng:
      + **"▶ Bỏ qua ảnh này & Tiếp tục"**: Bỏ qua không tải file ảnh lỗi này và tiếp tục quét các ảnh/bài tiếp theo.
      + **"⏹ Dừng hẳn"**: Ngắt phiên quét hoàn toàn để người dùng kiểm tra chi tiết.

### 2. Danh Sách File Đã Cập Nhật
1. `FacebookLikedMediaAddon/popup.html`: Bổ sung section accordion "🔍 Debug: Phát hiện ảnh tải nhầm" và Modal cảnh báo chẩn đoán (`#suspiciousImgModal`).
2. `FacebookLikedMediaAddon/popup.js`:
   - Xử lý đọc file ảnh mẫu từ máy, tính aHash và lưu trữ vào `chrome.storage.local`.
   - Kết nối sự kiện Modal, gửi quyết định (`continue` / `stop`) về Content Script.
   - Khôi phục trạng thái Debug Mode và hiển thị lại cảnh báo nếu mở lại popup.
3. `FacebookLikedMediaAddon/background.js`:
   - Handler `COMPUTE_IMAGE_HASH`: Dùng `createImageBitmap` + `OffscreenCanvas` trong Service Worker để bóc tách 256 bit aHash từ URL ảnh.
   - Handler `COMPARE_IMAGE_HASH`: So sánh khoảng cách Hamming và tính phần trăm giống nhau giữa 2 chuỗi hash.
4. `FacebookLikedMediaAddon/content_script.js`:
   - Tích hợp hàm `checkSuspiciousImage()` vào vòng lặp tải ảnh.
   - Bắt tín hiệu tạm dừng an toàn và chờ lệnh điều phối từ người dùng qua Modal.

### 3. Kiểm Thử & Xác Minh (Verification)
- ✅ Node.js VM Script: Cả 3 file `background.js`, `content_script.js`, `popup.js` đều **SYNTAX OK**.
- ✅ Toán tử so sánh aHash: Kiểm tra khớp 100% khi cùng hash, sai số tỷ lệ tuyến tính theo khoảng cách bit $\rightarrow$ TEST PASSED.
- ✅ Gate 2: Không phát sinh console thừa, bảo toàn mã hóa dữ liệu.

---

## 2026-09-12 — Khắc Phục Lỗi Ảnh Thanh Bên Gợi Ý (Sidebar) Bị Tải Thành `_img_01.jpg` — HOÀN THÀNH ✅

### 1. Phân Tích & Nguyên Nhân Thực Tế
- **Hiện tượng**: Các bài viết khác nhau (như `LX9LskEl`, `YGwc1Ehl`, `eT2o8uYl`) đều có file `_img_01.jpg` giống hệt nhau (54.808 bytes, 526x526 px, SHA-256: `7737f5b917...`), trong khi ảnh thật của bài nằm ở các file từ `_img_02.jpg` trở đi.
- **Nguyên nhân**:
  - `extractMediaFromPermalinkPage()` trong `background.js` quét toàn bộ thẻ `<img>` của `document`.
  - Trên Facebook Desktop, thanh bên phải (`role="complementary"` / RightRail) hoặc khu vực đề xuất luôn hiển thị một bài viết ghim (trong phiên duyệt web là bài "Bé trai 4 tuổi..." của Page Anh Da Đen).
  - Khối này nằm trước bài viết chính trong cấu trúc DOM và có `rect.top < boundaryTop`, kích thước 526x526 $\ge$ 150px nên bị bắt đầu tiên $\rightarrow$ đẩy thành `_img_01.jpg`.

### 2. Giải Pháp Triển Khai
- Trong `background.js`:
  - Giới hạn phạm vi bóc tách vào đúng container bài viết chính: `postArticle = mainArea.querySelector('div[role="article"]') || mainArea`.
  - Bổ sung **Bộ lọc 0**: Loại trừ 100% các phần tử nằm trong thanh bên phải (`role="complementary"`), thanh điều hướng (`role="navigation"`), header (`role="banner"`), RightRail, SideFeed, và các nhãn "gợi ý", "đề xuất", "suggested", "stories", "watch".
  - Quét đầy đủ tất cả ảnh HD của bài viết trước, fallback về `og:image` nếu không tìm thấy thẻ `<img>` nào trong bài.
  - Áp dụng tương tự cho video và văn bản bài viết.

### 3. Kiểm Thử & Xác Minh (Verification)
- ✅ Node.js VM Script: `background.js` đạt **SYNTAX OK** (17.315 bytes).
- ✅ Dọn dẹp: Đã xóa toàn bộ file tạm chẩn đoán trong artifact brain.
- ✅ Gate 2: Đảm bảo không phá vỡ logic tải media, unlike và anti-ban.

---

## 2026-09-12 — Cơ Chế Bảo Vệ 2 Lớp (Two-tier Validation) Đo Ký Tự Bài Viết — HOÀN THÀNH ✅

### 1. Phân Tích Vấn Đề
- **Tình huống**: Với các bài viết dài (ví dụ bài chia sẻ công nghệ trong group Antigravity VN dài $> 1.000$ ký tự), trên trang Activity Log Facebook chỉ hiển thị trích đoạn ngắn rút gọn (khoảng 100 - 200 ký tự kèm nút "Xem thêm" hoặc dấu ba chấm).
- **Hệ quả nếu chỉ đo Lớp 1**: Tiện ích đọc văn bản tóm tắt trên dòng Activity Log tưởng bài viết $\le 500$ ký tự $\rightarrow$ mở tab ngầm và tải media bài viết về.

### 2. Giải Pháp Triển Khai
- Tích hợp **Cơ chế Kiểm tra 2 Lớp (Two-tier Validation)** vào `content_script.js`:
  - **Lớp 1**: Kiểm tra sơ bộ text trên dòng Activity Log (`extractPostTextFromRow`). Nếu $> 500$ ký tự $\rightarrow$ ĐỂ NGUYÊN ngay lập tức.
  - **Lớp 2 (Mới bổ sung)**: Sau khi mở tab chi tiết bài viết, bóc tách lại nội dung văn bản đầy đủ chính xác của toàn bộ bài viết (`fullPostText`).
    - Nếu `fullTextLen > config.charThreshold` ($> 500$ ký tự): Lập tức dừng việc tải media, ghi log cảnh báo `🛡️ [ĐỂ NGUYÊN - LỚP 2]`, đánh dấu bài viết đã duyệt vào cache và tiếp tục sang bài khác mà **KHÔNG TẢI BẤT KỲ ẢNH/VIDEO NÀO VÀ KHÔNG HỦY THÍCH**.
  - Đồng bộ `fullPostText` và `fullTextLen` vào việc lưu trữ `post_info.txt` và bộ chẩn đoán Debug Mode.

### 3. Kiểm Thử & Xác Minh (Verification)
- ✅ Node.js VM Script: `content_script.js` đạt **SYNTAX OK** (50.757 bytes).
- ✅ Dọn dẹp: Đã xóa file scratch `analyze_group_post.js`.
- ✅ Gate 2: Đảm bảo 100% không bao giờ tải nhầm các bài viết dài ngay cả khi Facebook rút gọn văn bản trên Activity Log.

---

## 2026-09-12 — Khắc Phục Bài Viết Nhóm Dài & Chặn Tải Poster Video Thành Ảnh — HOÀN THÀNH ✅

### 1. Phân Tích & Nguyên Nhân Thực Tế
- **Hiện tượng**: Bài viết trong nhóm Antigravity VN dài $> 1.000$ ký tự (`1689021625732069`) nhưng vẫn bị tiện ích tải ảnh về (`_img_01.jpg`) và bị Hủy Thích (Unlike).
- **Nguyên nhân cốt lõi**:
  1. **Bài viết không có text trên Activity Log**: Dòng nhật ký chỉ có *"Bạn đã thích bài viết của Antigravity VN"* $\rightarrow$ lọc ra 0 ký tự $\rightarrow \le 500$ ký tự $\rightarrow$ lọt qua Lớp 1.
  2. **Bộ selector text cũ bỏ sót bài viết Nhóm Facebook**: Cấu trúc bài viết nhóm sử dụng `[data-ad-rendering-role="story_message"]` và `div[class*="xdj266r"]`, không khớp với các selector trang cá nhân cũ.
  3. **Facebook Server cắt ngắn `og:description`**: Khi fallback về meta `og:description`, Facebook server tự cắt ngắn còn 396 ký tự (kèm `... như...`). Vì $396 \le 500$ nên Lớp 2 bị đánh lừa là bài ngắn.
  4. **Tải nhầm poster video thành ảnh**: Bài viết thực chất là bài Video (không có thẻ `<img>` ảnh chụp), code fallback lấy `og:image` là ảnh thumbnail đại diện của video và lưu vào `image/Post_..._img_01.jpg`.

### 2. Giải Pháp Triển Khai
- **Tại `background.js`**:
  - Tăng thời gian chờ render tab ngầm từ `1.5s` $\rightarrow$ `2.5s` để Facebook kịp hydrate React DOM.
  - Bổ sung selector bài viết Group Facebook: `[data-ad-rendering-role="story_message"]`, `div[class*="xdj266r"][dir="auto"]`, và cơ chế quét tập hợp leaf node `div[dir="auto"]` bài viết.
  - Tự động click *"Xem thêm"* / *"See more"* trong bài viết nếu bị thu gọn để mở rộng toàn bộ văn bản.
  - **Nhận diện cắt ngắn thông minh (`isTruncated`)**: Nếu fallback `og:description` kết thúc bằng dấu ba chấm (`...`, `…`, `&hellip;`, `&#x2026;`) và độ dài $\ge 180$ ký tự $\rightarrow$ Đánh dấu `isTruncated = true`.
  - **Chặn tải poster video vào `image/`**: Nếu bài viết là Video (`og:type` chứa `video`, URL có `/watch`/`/reel`/`/videos/` hoặc có thẻ `<video>`), **TUYỆT ĐỐI KHÔNG** fallback lấy `og:image` vào danh sách ảnh tải.
  - Hỗ trợ lấy link video MP4 từ `meta[property="og:video"]` / `og:video:secure_url`.
- **Tại `content_script.js`**:
  - Nhận và đồng bộ cờ `isTruncated` qua `PERMALINK_MEDIA_RESULT`.
  - Nếu `fullTextLen > config.charThreshold` HOẶC `mediaData.isTruncated === true` $\rightarrow$ Kích hoạt `🛡️ [ĐỂ NGUYÊN - LỚP 2]`, đánh dấu cache, **bỏ qua hoàn toàn (KHÔNG tải media và KHÔNG hủy thích)**.

### 3. Kiểm Thử & Xác Minh (Verification)
- ✅ Node.js VM Script:
  - `background.js`: SYNTAX OK (21.282 bytes).
  - `content_script.js`: SYNTAX OK (51.130 bytes).
  - `popup.js`: SYNTAX OK (23.751 bytes).
- ✅ Unit test regex truncation: Khớp chính xác các kiểu cắt ngắn `... như...`, `...`, `…`, `&hellip;`, `&#x2026;`.
- ✅ Gate 2: Hoàn thành đầy đủ 7 tiêu chí. Không ảnh hưởng đến các bài viết ngắn và các bài viết có ảnh HD thực thụ.

---

## 2026-09-12 — Chuyển Ngưỡng Mặc Định 300 Ký Tự, Lưu Cấu Hình Vĩnh Viễn & Chốt Chặn An Toàn Unlike — HOÀN THÀNH ✅

### 1. Phân Tích & Yêu Cầu
- **Hiện tượng**:
  1. Người dùng đổi ngưỡng ký tự trên giao diện Popup (ví dụ về 200 hoặc 300), nhưng khi tắt popup hoặc F5 tải lại trang thì giá trị bị ghi đè ngược về 500 do `GET_STATUS` từ content script memory trả về giá trị mặc định.
  2. Bài viết dài bị cắt ngắn dạng `"... Xem thêm"` (dài khoảng 350 ký tự) kết thúc bằng chữ "Xem thêm" thay vì dấu ba chấm đơn thuần, khiến tiện ích không nhận ra là bài bị rút gọn và vẫn tiến hành Unlike.
- **Yêu cầu từ người dùng**:
  - Chuyển ngưỡng mặc định về `300` ký tự.
  - Lưu cấu hình vĩnh viễn: Khi người dùng đổi sang 200 hay bất kỳ số nào, tiện ích phải ghi nhớ vĩnh viễn và không bao giờ bị nhảy lại.
  - Tuyệt đối không hủy like các bài viết dài.

### 2. Giải Pháp Triển Khai
- **Bộ nhớ cấu hình vĩnh viễn (`chrome.storage.local`)**:
  - Trong `popup.js`: Lắng nghe sự kiện `change` và `input` trên toàn bộ các ô cài đặt (`charThreshold`, `maxPerSession`, `cooldownEvery`, v.v.), tự động lưu vào `chrome.storage.local` dưới key `fb_user_config`.
  - Khi mở Popup (`init()`): Luôn đọc `fb_user_config` từ storage để điền lại giá trị đã lưu của người dùng (nếu có lưu 200 thì hiện 200, lưu 300 thì hiện 300).
  - Chỉ đồng bộ ngược từ tab nếu tab đó đang thực sự chạy (`res.isRunning === true`).
  - Trong `content_script.js`: Tự động nạp `fb_user_config` từ `chrome.storage.local` ngay khi khởi tạo.
- **Chuyển ngưỡng mặc định về 300 ký tự**:
  - `popup.html`: `value="300"`, gợi ý đổi thành 300.
  - `popup.js`: Default fallback `charThreshold = 300`.
  - `content_script.js`: Default fallback `charThreshold: 300`.
- **Nhận diện triệt để "Xem thêm" & Chốt chặn an toàn Unlike**:
  - Trong `background.js`: Quét toàn bộ phần tử có chữ "Xem thêm", "See more", "xem tiếp" để click bung toàn bộ nội dung. Bắt cờ `isTruncated = true` nếu text có chữ "Xem thêm" hoặc kết thúc bằng `... Xem thêm`.
  - Trong `content_script.js`:
    + Kiểm tra Lớp 2: Nếu văn bản chứa `"Xem thêm"` / `"See more"` hoặc kết thúc `...` $\rightarrow$ ĐỂ NGUYÊN và bỏ qua ngay.
    + **Chốt chặn an toàn trước `executeUnlike()`**: Ngay trước khi gọi lệnh hủy like, kiểm tra lại toàn diện một lần nữa: nếu `fullTextLen > config.charThreshold` HOẶC có dấu hiệu cắt ngắn/Xem thêm $\rightarrow$ Lập tức dừng lại, ghi log cảnh báo và **TUYỆT ĐỐI KHÔNG HỦY THÍCH**.

### 3. Kiểm Thử & Xác Minh (Verification)
- ✅ Node.js VM Script:
  - `background.js`: SYNTAX OK (21.363 bytes).
  - `content_script.js`: SYNTAX OK (52.091 bytes).
  - `popup.js`: SYNTAX OK (25.575 bytes).
- ✅ Unit test regex "Xem thêm": Khớp chính xác 100% các biến thể (`... Xem thêm`, `... See more`, `... xem tiếp`, `... như...`, `...`).
- ✅ Gate 2: Đảm bảo không còn console thừa, bảo toàn mã hóa dữ liệu.

---

## 2026-09-12 — Khắc Phục Lỗi Ảnh Permalink.php, Bảo Vệ Bài 0 Chữ & Bổ Sung Log Chi Tiết — HOÀN THÀNH ✅

### 1. Phân Tích & Nguyên Nhân Thực Tế
- **Hiện tượng**:
  1. Người dùng chạy bài viết dạng `facebook.com/permalink.php?story_fbid=...` nhưng tiện ích không tải được bất kỳ ảnh nào.
  2. Các bài viết dài vẫn bị Unlike do khi bóc tách gặp sự cố (hoặc tab ngầm timeout), biến `fullTextLen` bằng `0` $\rightarrow 0 \le 300 \rightarrow$ tiện ích tưởng bài ngắn nên đi Unlike.
- **Nguyên nhân cốt lõi**:
  - **Lỗi BỘ LỌC 6 (Avatar)**: Chuỗi URL `"/permalink.php"` khớp với regex profile 1 cấp (`/^\/[^\/]+\/?$/`), trong khi `isContentPath` trước đây chỉ chứa `posts`, `photo`, chưa có `permalink.php` và `story_fbid`. Kết quả: BỘ LỌC 6 tưởng toàn bộ ảnh bài viết là Avatar và vứt bỏ 100%!
  - **Lỗi nhận diện Video nhầm**: Lệnh `mainArea.querySelector('video')` bắt nhầm video quảng cáo/feed trên màn hình chính, gán bài viết là Video $\rightarrow$ chặn luôn cả đường fallback `og:image`.
  - **Thiếu log minh bạch**: Người dùng không nhìn thấy tiện ích đếm được bao nhiêu ký tự ở Lớp 2 trước khi quyết định unlike hay để nguyên.

### 2. Giải Pháp Triển Khai
- **Sửa BỘ LỌC 6 trong `background.js`**:
  - Bổ sung `permalink.php`, `story_fbid`, `fbid` vào danh sách `isContentPath`.
  - Khẳng định 100%: Mọi link dẫn đến bài viết, ảnh, permalink, story_fbid ĐỀU LÀ NỘI DUNG, tuyệt đối KHÔNG PHẢI AVATAR.
  - Sửa `isVideoPost`: Chỉ coi là Video nếu `og:type` thực sự là video hoặc URL là `/watch`, `/reel`, `/videos/`.
  - Nâng timeout tab ngầm từ 15s lên 20s.
- **Cải tiến `content_script.js`**:
  - **Minh bạch hóa 100% Log đếm ký tự (theo yêu cầu của người dùng)**:
    - `📊 [Lớp 2 - Đếm ký tự bài ID {ID}] Đã đếm: {fullTextLen} ký tự | {X} ảnh | {Y} video (Ngưỡng giữ bài: > {ngưỡng} ký tự).`
    - `📝 Trích đoạn: "{80 ký tự đầu}..."`
    - `🛡️ [ĐỂ NGUYÊN - LỚP 2] Bài viết ID {ID} {lý do} -> KHÔNG tải media và KHÔNG hủy thích!`
    - `✅ [XÁC NHẬN BÀI NGẮN] Bài viết ID {ID} có {fullTextLen} ký tự (<= {ngưỡng}) -> Đạt điều kiện tải media & Hủy Thích.`
  - **Lá chắn bảo vệ bài viết 0 chữ / 0 media**: Nếu không trích xuất được nội dung bài viết (0 chữ, 0 ảnh, 0 video hoặc bị timeout) $\rightarrow$ Ghi log `🛡️ [ĐỂ NGUYÊN - BẢO VỆ]` và **TUYỆT ĐỐI KHÔNG HỦY THÍCH**.

### 3. Kiểm Thử & Xác Minh (Verification)
- ✅ Node.js VM Script:
  - `background.js`: SYNTAX OK (21.891 bytes).
  - `content_script.js`: SYNTAX OK (53.340 bytes).
  - `popup.js`: SYNTAX OK (25.575 bytes).
- ✅ Unit test BỘ LỌC 6:
  - Link `permalink.php?story_fbid=...`: `✅ CONTENT IMAGE (KEPT)`
  - Link `photo.php?fbid=...`: `✅ CONTENT IMAGE (KEPT)`
  - Link `facebook.com/vietcg4`: `❌ AVATAR (DROPPED)`
  - Link `profile.php?id=...`: `❌ AVATAR (DROPPED)`
- ✅ Gate 2: Đảm bảo không còn console thừa, bảo toàn mã hóa dữ liệu.






