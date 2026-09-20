# 📝 PROJECT MEMORY — GetHtmlFromUrl (Bản Python)

## 📍 Thông tin dự án
- **Tên dự án**: GetHtmlFromUrl Python Port
- **Đường dẫn**: `C:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\Download\Download truyen\GetHtmlFromUrl_Python`
- **Môi trường**: Python 3.11+, PyQt6, BeautifulSoup4, requests, cloudscraper
- **Mục tiêu**: Chuyển đổi 100% tính năng từ phiên bản Java Swing cũ sang Python. Kế thừa nguyên vẹn file cấu hình `ghfuConfig.json`.

## 🏗️ Kiến trúc dự án
```text
GetHtmlFromUrl_Python/
│
├── main.py                     # Entry point (PyQt6)
├── ProjectLog.md               # Nhật ký dự án
├── requirements.txt            # requests, bs4, PyQt6, cloudscraper
├── config/
│   └── ghfuConfig.json         # 510+ site rules (kế thừa từ Java)
│
├── core/
│   ├── engine.py               # Scraping engine: AJAX mode + Static HTML mode
│   └── page_config_mgr.py      # Parse ghfuConfig.json → PageConfig objects
│
├── models/
│   ├── chapter.py
│   ├── login_info.py
│   └── page_config.py          # + 2 field mới: ajax_list_chap_url, ajax_list_chap_id
│
└── gui/
    ├── main_window.py          # UI chính — clone 1:1 Java Swing
    ├── dialogs.py              # DownloadRangeDialog, EbookInfoDialog
    └── workers.py              # QThread — tương đương TAuto.java
```

## 📋 Trạng thái dự án

### ✅ Phase 1 — Core Engine & Data Model — HOÀN THÀNH
- [x] `models/` — PageConfig, Chapter, LoginInfo dataclasses
- [x] `core/page_config_mgr.py` — parse JSON + camelCase→snake_case mapping
- [x] `core/engine.py` — BeautifulSoup + cloudscraper, filter_html() y hệt Java

### ✅ Phase 2 — UI Clone 1:1 Java Swing — HOÀN THÀNH
- [x] `gui/main_window.py` — Clone bố cục chính: URL, Nơi lưu, Host filter, Tùy chọn, Console.
- [x] **Hệ thống Menubar đầy đủ**: Menu Tệp, Thông Tin, Đường Dẫn Trợ Giúp, Công Cụ (đã clone 100% item list giống Java gốc).
- [x] `gui/dialogs.py` — DownloadRangeDialog (chọn chương từ/đến), EbookInfoDialog
- [x] `gui/workers.py` — QThread đầy đủ: download range, lưu gộp/chia file, html_to_text
- [x] `_total_chapters` tracking + progress bar chính xác kể cả khi end_idx = -1
- [x] QSettings lưu/khôi phục trạng thái checkbox

### ✅ Phase 3 — Advanced Features — HOÀN THÀNH
- [x] `cloudscraper` tích hợp vào engine.py (tự động khi `byPassCloudFlare=true`)
- [x] **AJAX Pagination**: `_get_links_ajax()` tự detect book_id từ HTML và fetch hết tất cả trang qua `/get/listchap/{id}?page={n}` → lấy đủ 2883 chương truyennet.org
- [x] **Static Pagination**: `_get_links_static()` hỗ trợ auto-paging qua `paging_pattern` CSS selector
- [x] Config `truyennet.org` thêm `ajaxListChapUrl` → test pass: 2883/2883 chương

### ✅ Phase 4 — Mở rộng UI nâng cao (Advanced UIs) — HOÀN THÀNH
- [x] **Settings UI** (`gui/settings_dialog.py`): Cho phép cấu hình Timeout, Thời gian nghỉ, Số kết nối, và lưu vào `QSettings`.
- [x] **Quick Login UI** (`gui/quick_login_dialog.py`): Cho phép người dùng nhập trực tiếp chuỗi Cookies. Tự động parse và inject vào `requests.Session()` bên trong `engine.py`.
- [x] **Manual GET UI** (`gui/manual_get_ui.py`): Cho phép người dùng dán hàng loạt URL vào textarea và tải trực tiếp, không qua bước get mục lục. Tái sử dụng và nâng cấp `DownloadWorker` hỗ trợ `manual_links`.
- [x] **PageConfigManager UI** (`gui/config_mgr_dialog.py`): Cửa sổ Splitter chia làm 2 phần: List bên trái và Form (trên 15 fields CSS/Regex/Checkbox) bên phải. Cho phép cập nhật `PageConfig` và ghi đè trực tiếp xuống `ghfuConfig.json` thông qua `page_config_mgr.py`.

### ✅ Phase 5 — Tối ưu Tốc độ & Khôi phục thông minh (Multi-threading & Exact Resume) — HOÀN THÀNH
- [x] **Multi-threading (Concurrent Downloads)**: Áp dụng `ThreadPoolExecutor` trong `DownloadWorker`, tự động tải nhiều chương cùng lúc theo cấu hình `max_connection` trong `QSettings`.
- [x] **Auto-Retry 5 lần**: Nếu 1 chương tải thất bại, luồng sẽ tự động thử lại tối đa 5 lần (mỗi lần cách nhau 1s) trước khi đánh dấu lỗi hẳn.
- [x] **Exact-Position Resume**: Cải tiến cấu trúc `_Resume.json` lưu trữ chi tiết danh sách chương, `save_dir` và trạng thái lỗi.
- [x] **ResumeDialog**: Chuyển logic tải bù (Resume) từ việc mở form `Manual GET` sang việc khôi phục trực tiếp tiến trình (`DownloadWorker(resume_data=...)`), đảm bảo tải bù đúng các chương thiếu và chèn lại đúng vị trí trong mục lục (TOC).
- [x] **Direct HTML Patching**: Hỗ trợ khả năng trực tiếp trích xuất dữ liệu từ file HTML tổng cũ. Không cần phụ thuộc vào thư mục chứa các file tạm (`save_dir`). Ứng dụng sẽ đọc các chương đã có, tải 10 chương thiếu, và tự ráp đúng vị trí vào file HTML tổng.
- [x] **Preserve Line Breaks**: Xử lý triệt để lỗi không có khoảng cách dòng (xuống dòng) trong định dạng HTML bằng cách dùng Regular Expression `re.sub(r'(?<!>)\n(?!<)', '<br/>\n', content)` kết hợp CSS `white-space: pre-wrap`, đảm bảo tương thích mọi trình duyệt và ứng dụng đọc eBook.

### Phase 6: Hỗ trợ tự động tạo PRC (Mobi)
- [x] **Auto-download KindleGen**: Tự động tải công cụ `kindlegen.exe` từ Internet Archive vào thư mục `tools` nếu chưa có.
- [x] **Automated Pipeline**: Cập nhật logic để ngay khi tải và gộp HTML xong, tiến trình sẽ tự động kích hoạt `PrcWorker` chạy biên dịch ngầm HTML ra dạng sách `.prc`.
- [x] **Manual Compile**: Hỗ trợ nút ấn "Tạo PRC" riêng biệt trên giao diện để có thể chuyển đổi bất cứ file HTML nào tuỳ ý.

## 🔑 Kỹ thuật quan trọng
1. **CSS Filter Logic**: filter_html() áp dụng CHỈ trên content element, KHÔNG trên toàn trang → title không bị xóa.
2. **AJAX Mode**: Khi `page_config.ajax_list_chap_url != ""`, engine tự detect `book_id` từ pattern `page(BOOK_ID, PAGE)` trong JS HTML.
3. **Encoding & BOM (Sửa lỗi convert Mobi/PRC)**: HTML gộp được lưu với định dạng `utf-8-sig` (chứa BOM) và ghi kèm thẻ `<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />` để tương thích 100% với các công cụ build ebook cũ như KindleGen hay Mobipocket.
4. **Error Logging**: Các chương lỗi sẽ được gom và lưu thành danh sách link tại file `<Tên truyện>_ErrorLog.txt` ở cùng thư mục tải về. User có thể nhét danh sách này vào chức năng Manual GET để tải lại các chương hỏng.
3. **Cloudscraper**: Được dùng khi `page_config.by_pass_cloudflare = True` (cả fetch_html và AJAX requests).
4. **Download Range**: Worker nhận `start_idx/end_idx` từ UI → slice `all_links[start:end+1]`.
5. **Lưu file gộp**: HTML có TOC + anchor từng chương. TXT dùng html_to_text().
6. **Lưu file chia**: Mỗi chương → file riêng trong thư mục `TenTruyen_GHFU_Timestamp/`.

## 🐛 Bug đã biết / Giới hạn
- DownloadRangeDialog mở TRONG luồng tải — vẫn hoạt động nhờ signal/slot nhưng chưa block thread
- Nếu site không có pattern `page(ID, PAGE)` trong JS → AJAX mode sẽ fallback về static mode

### ✅ Phase 6 — Smart Resume & Manual Merge — HOÀN THÀNH (2026-07-31)
- [x] **Slug Folder cố định**: `_prepare_save_paths()` nay dùng URL slug (`ta-mo-phong.../`) thay vì `_GHFU_timestamp/`. Thư mục chương tồn tại vĩnh viễn, không bị xóa.
- [x] **Auto-detect Resume**: `_on_start_download()` tự kiểm tra slug folder đã có → nếu có `_Resume.json` → hiện popup hỏi: "Chỉ tải X chương còn thiếu?" hoặc "Tải lại từ đầu?".
- [x] **_start_worker() helper**: Tách logic tạo DownloadWorker thành hàm riêng, dùng chung cho tải mới và resume.
- [x] **Bỏ auto-merge**: Sau khi tải xong, KHÔNG tự gộp. Thay vào đó emit message "Nhấn [📚 Gộp] để tạo file tổng."
- [x] **Bỏ auto-cleanup**: Thư mục slug không bị xóa sau khi tải xong. Chỉ xóa `_Resume.json` khi resume hoàn tất 0 lỗi.
- [x] **MergeWorker(QThread)**: Class mới trong `workers.py` — scan *.html trong folder, sort theo tên, gộp thành file HTML tổng có TOC + UTF-8-SIG BOM.
- [x] **Nút "📚 Gộp"** thêm vào row3 (cạnh "Tải Tiếp") và menu Công cụ → Gộp Truyện từ Thư Mục.
- [x] **_on_merge_story()**: Mở dialog chọn folder → chọn output path → chạy MergeWorker.
- [x] **Bugfix engine.py** (2026-07-31): Sửa 3 bug trong `core/engine.py`:
  1. `get_chapter_title_and_content()` truyền `page_config.by_pass_cloudflare` (bool) vào `fetch_html()` thay vì `page_config` → scraper không được chọn đúng.
  2. `_get_links_static()` cùng lỗi trên.
  3. AJAX errors chỉ ghi vào `logger.error` (không hiển thị GUI) + không có retry → thoát vòng lặp im lặng sau 700 chương khi gặp timeout/rate-limit.
  - Fix: thêm `log_fn` callback để emit lỗi ra GUI, thêm retry 3 lần với delay 2s mỗi AJAX page.

### ✅ Phase 7 — Auto-Features — HOÀN THÀNH (2026-08-01)
- [x] **Auto-fill Tên File**: Khi dán URL, tự động trích xuất slug, lọc dấu và định dạng "Title Case" để làm tên file. Tự động gắn kèm `last_save_dir` (nếu có).
- [x] **Nhận Diện Host Nhanh**: Dán URL xong sẽ hiện ngay dòng trạng thái "✅ Đã nhận diện host..." hoặc "❌ Host chưa được hỗ trợ...".
- [x] **Auto-Resume 5 Lần**: Xử lý lỗi Rate-limit/Timeout bằng cách tự động Retry những chương lỗi trong quá trình tải (tối đa 5 lần) trước khi kết thúc tiến trình.
- [x] **Auto-Merge**: Khôi phục lại tính năng gộp file tự động nếu quá trình tải thành công 100%.
- [x] **Delete Folder**: Thêm tùy chọn "Xóa thư mục tạm sau khi gộp" (lưu tùy chọn qua các lần chạy) dọn dẹp sạch sẽ rác nếu muốn.
- [x] **Bổ sung host metruyenchuvn.org**: Đã tích hợp thành công cấu hình cho host `metruyenchuvn.org` vào `ghfuConfig.json`.
- [x] **Giải quyết lỗi 700 chương trên truyennet.org**: Thuật toán lấy chương AJAX mới (cùng với tính năng Auto-Resume 5 lần) đã đảm bảo các request không bị ngắt giữa chừng.

### ✅ Phase 8 — Nâng cấp công cụ PRC & Bổ sung Host mới — HOÀN THÀNH
- [x] **Chuyển đổi Pipeline PRC (OPF Package)**: Để khắc phục việc KindleGen đứng máy hoặc hết RAM với các truyện khổng lồ (hàng ngàn chương), quá trình nén PRC nay đã được thiết kế lại. File HTML tổng sẽ được tự động bóc tách thành hàng ngàn file HTML lẻ (mỗi chương 1 file) cùng với file mục lục `.ncx` và `.opf` trong thư mục tạm, giúp KindleGen nén siêu tốc.
- [x] **HTML Sanitization (Chống Crash)**: Đã thêm bộ lọc Regex trước khi nén để chặt đứt các thẻ `<input>`, `<button>`, `<script>`, `<form>`,... khỏi nội dung chương, ngăn chặn hoàn toàn lỗi KindleGen Access Violation (`3221225477`).
- [x] **Trạng thái nén thời gian thực (Progress UI)**: KindleGen nay sẽ phản hồi tiến trình (từ 60% đến 95%) để hiển thị lên thanh ProgressBar thay vì kẹt mãi ở 50%.
- [x] **Quản lý Process**: Đảm bảo `kindlegen.exe` sẽ bị `kill` ngay lập tức nếu người dùng đóng ứng dụng giữa chừng.
- [x] **Bổ sung host metruyenhotvn.com**: Đã cập nhật rules JSON cho `metruyenhotvn.com` (và `metruyenhot.me`) với pagination `?page=` và CSS queries chuẩn xác.

### ✅ Phase 9 — Auto-Install Dependencies — HOÀN THÀNH (2026-09-01)
- [x] **Auto-Install Packages Pattern**: Tích hợp cơ chế kiểm tra và tự động cài đặt thư viện (`PyQt6`, `requests`, `beautifulsoup4`, `cloudscraper`, `lxml`) vào đầu file `main.py`.
- [x] **Fallback UI Dialog**: Tự động hiển thị giao diện báo lỗi và cung cấp lệnh pip để copy nếu cài đặt ngầm thất bại.

### ✅ Phase 10 — Smart PRC Gating & Accurate Error Reporting — HOÀN THÀNH (2026-09-01)
- [x] **Boolean Success Flag**: Nâng cấp `finished_signal = pyqtSignal(bool, str)` trong `DownloadWorker` để phân định chính xác giữa tải thành công 100% và tải dở dang / lỗi.
- [x] **Chặn tạo PRC khi thiếu chương**: `main_window.py` nay kiểm tra chặt chẽ `if success:` trước khi kích hoạt `PrcWorker`. Tuyệt đối không tự động tạo PRC nếu vẫn còn chương bị thiếu.
- [x] **Cảnh báo thiếu chương tức thì (Warning Dialog)**: Khi phát hiện có chương lỗi/thiếu, ứng dụng lập tức hiện hộp thoại cảnh báo người dùng và hướng dẫn bấm "Tiếp Tục" (Resume) để tải bù đủ 100% trước khi tạo eBook.

### ✅ Phase 11 — Tích hợp host xtruyen.vn (Cơ chế mã hóa đặc biệt) — HOÀN THÀNH (2026-09-14)
- [x] **Phân tích cơ chế xtruyen.vn**: Nội dung chương được mã hóa bằng custom base64 + zlib inflate nhúng trực tiếp trong `<script>` của HTML tĩnh (biến `data_x`). Không cần browser hay login.
- [x] **`models/page_config.py`**: Thêm field `content_mode: str = ""` — cho phép mỗi host đăng ký phương thức tải nội dung riêng.
- [x] **`core/engine.py`** — 3 thay đổi lớn:
  1. **Dispatch mode**: `get_chapter_title_and_content()` kiểm tra `content_mode` và gọi đúng method phù hợp.
  2. **`_get_chapter_xtruyen()`**: Method mới — parse `data_x`, dịch bảng chữ cái custom→standard base64, decode + zlib inflate, extract title từ JSON-LD schema.
  3. **`<option>` selector**: `_get_links_static()` giờ xử lý được `<select option>` selector (xtruyen.vn dùng `<select>` làm bảng mục lục), build URL dạng `/truyen/{slug}/chuong-{N}/`.
- [x] **`core/page_config_mgr.py`**: Fix bug mapping `byPassCloudFlare` → `by_pass_cloud_flare` (sai) thành `by_pass_cloudflare` (đúng) qua bảng `_CAMEL_OVERRIDE`. Bug này ảnh hưởng **tất cả** host dùng CloudFlare bypass.
- [x] **`config/ghfuConfig.json`**: Thêm entry `xtruyen.vn` với `contentMode: "xtruyen_decrypt"`.
- [x] **Kết quả test**: 1273 chương được detect; 5/5 chương tải OK qua engine với title đúng, content đầy đủ.

### ✅ Phase 12 — Chống Ban IP & Kiểm Soát Tốc Độ Tải (Anti-Spam & Rate Limiting) — HOÀN THÀNH (2026-09-14)
- [x] **Cơ chế Per-Host Rate Limiting**:
  - `models/page_config.py` thêm `delay_ms` và `max_connection` hỗ trợ cấu hình tốc độ và số luồng riêng cho từng host.
  - `config/ghfuConfig.json`: Cấu hình cho `xtruyen.vn` thêm `"delayMs": 2500` và `"maxConnection": 1` (bắt buộc đơn luồng an toàn).
- [x] **Chống Spam & Random Jitter trong `gui/workers.py`**:
  - Chuyển khoảng nghỉ giữa các request vào đúng chu kỳ thực thi kèm `random.uniform(0.3, 1.0)` jitter ngẫu nhiên để xóa dấu vết hành vi bot tuần hoàn.
  - `_get_max_workers()` và `_get_delay_ms()` tự động ưu tiên cấu hình riêng của host trước khi dùng cài đặt chung của app.
- [x] **Phát hiện Khóa IP & Circuit Breaker (Hạ nhiệt thông minh)**:
  - `core/engine.py`: Bổ sung headers trình duyệt hiện đại (Referer, Accept-Language, Sec-Fetch-*), tự động phát hiện các chữ ký khóa IP/chặn spam của server (`"Truy cập bị từ chối"`, `"tạm khóa IP"`, HTTP 429/403) và bật cờ `chapter.is_ip_banned`.
  - `gui/workers.py`: Khi phát hiện tín hiệu bị khóa IP, lập tức ngừng gửi request (không retry mù quáng), kích hoạt hạ nhiệt 45s, probe thử 1 request. Nếu vẫn bị chặn thì dừng an toàn và bảo toàn file `_Resume.json` cho user.

### ✅ Phase 13 — Hỗ trợ Web Truyện Trung Quốc & Tích hợp 69shuba (2026-09-15)
- [x] **Bộ Lọc Host Tiếng Trung**: Bổ sung bộ lọc "Web: Trung Quốc" trong ComboBox host (`is_vietnamese_host == False`), tự động gắn nhãn `[Web: Trung Quốc]`.
- [x] **Bypass Cloudflare qua curl_cffi**: Tích hợp session `curl_cffi` (impersonate `chrome120`) vào `core/engine.py` khi `by_pass_cloudflare=True`, vượt qua 100% tường lửa Cloudflare Turnstile trên `69shuba.com` và các host tương tự.
- [x] **Hỗ trợ Bảng Mã Tiếng Trung (GBK/GB18030/UTF-8)**: Tự động phát hiện charset từ raw bytes của trang và giải mã an toàn, không bị lỗi font ký tự tiếng Trung.
- [x] **Cấu Hình Chuẩn 69shuba (`www.69shuba.com` & `69shuba.com`)**:
  - Tự động chuẩn hóa link `/book/{id}.htm` sang trang mục lục đầy đủ `/book/{id}/` (lấy trọn vẹn 1.543 chương).
  - Tích hợp cờ `is_revert_chapter_list: True` vào `core/engine.py` để đảo ngược danh sách chương, đảm bảo tải tuần tự từ Chương 1 đến chương cuối.
  - Bộ lọc CSS loại bỏ tiêu đề trùng, thông tin tác giả, quảng cáo thừa.
- [x] **Auto Title & Dịch Hán-Việt (`utils/translator.py`)**:
  - Tự động bóc tách tên truyện tiếng Trung từ trang và dịch âm Hán-Việt / tiếng Việt mượt mà.
  - Tự động đặt tên file và thư mục theo chuẩn: `China-{Tên truyện Trung}-({Tên truyện Việt dịch})` (Ví dụ: `China-苟在初圣魔门当人材-(Cẩu Tại Sơ Thánh Ma Môn Đương Nhân Tài)`).
- [x] **Tải Từng Chương Thành File HTML Riêng**:
  - Tự động kích hoạt checkbox "Mỗi chương thành 1 tệp".
  - Lưu từng chương thành file `.html` chuẩn UTF-8-SIG với tiêu đề và định dạng CSS tối ưu (`0001_第1章 百世书.html`).

### ✅ Phase 14 — Fix Bug UI Freeze khi dán URL Trung Quốc (2026-09-15)
- [x] **Root Cause**: `_on_url_changed` (kết nối với `textChanged`) gọi `self.engine.fetch_html()` trực tiếp trong **main UI thread** — khiến app đóng băng tới 25 giây mỗi khi user dán URL 69shuba. Đây là nguyên nhân thực sự của bug "chỉ tải được 1 chương" (app bị đơ, user không thấy progress).
- [x] **`TitleFetchWorker(QThread)`** (mới): Class background thread chuyên fetch title truyện Trung từ URL mà không block UI thread. Emit signal `title_ready(clean_title, save_path)` khi xong.
- [x] **Debounce Timer 600ms**: `QTimer.singleShot` 600ms trong `_on_url_changed` để tránh gửi request sau mỗi ký tự gõ. Chỉ bắt đầu fetch sau khi user dừng gõ 600ms.
- [x] **`_do_fetch_chinese_title()`**: Method mới kích hoạt bởi timer — tạo và chạy `TitleFetchWorker` ở background.
- [x] **`_on_title_fetched()`**: Callback nhận kết quả từ worker — cập nhật `txt_save_path` với tên truyện thật mà không race condition (kiểm tra URL còn khớp không trước khi update).
- [x] **UX cải thiện**: Hiển thị `⏳ Đang lấy tên truyện...` ngay lập tức sau khi dán URL, sau đó cập nhật `✅ Tên: ...` khi fetch xong — thay vì đóng băng hoàn toàn như trước.
- [x] **Verified**: `from gui.main_window import MainWindow, TitleFetchWorker` → import thành công, không lỗi compile.

### ✅ Phase 15 — Tiện ích AI Dịch Truyện (Google Gemini) với Glossary & Context (2026-09-15)
- [x] **Core Engine (`core/ai_translator.py`)**:
  - Tích hợp gọi Google Gemini API với cơ chế luân phiên key (Key Rotation) và chuyển đổi model thông minh (`gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-1.5-flash`, `gemini-3.5-flash`,...).
  - **Tự động đọc 156+ Gemini API Keys từ AskCpl** (`settings.json`) qua thuật ngữ giải mã `ENC:` đảo chuỗi Base64 — người dùng không cần nhập lại key thủ công.
  - **Từ điển Thuật ngữ (`_glossary.json`)**: Tự động lưu trữ và tích lũy tên nhân vật, môn phái, vũ khí, địa danh xuyên suốt các chương, đưa trực tiếp vào prompt để đảm bảo cách dịch cố định, không bị "lúc A lúc B".
  - **Rolling Summary Context (`_translate_progress.json`)**: Tóm tắt diễn biến then chốt của chương trước (2-3 câu) để truyền vào chương kế tiếp, giúp AI nắm bắt ngữ cảnh, bối cảnh và định hình xưng hô (huynh đệ, sư đồ, đại ca, tiểu muội,...) liền mạch.
  - **Pacing an toàn**: Nghỉ 3.5s - 5.0s giữa các chương kèm jitter để chống mã lỗi 429 Too Many Requests.
  - **Bóc tách & Lưu trữ HTML**: Trích xuất tiêu đề `<h2>` và văn bản `<div class='chapter-content'>` an toàn với mã hóa UTF-8/GB18030, lưu bản dịch ra HTML chuẩn có CSS thân thiện cho người đọc.
- [x] **Giao diện Tiện ích (`gui/translate_dialog.py`)**:
  - `TranslateDialog`: Cửa sổ tiện ích chọn thư mục nguồn tiếng Trung, tự động gợi ý thư mục lưu `/dich`.
  - Quản lý API Key, nút "🔑 Nạp từ AskCpl", điều chỉnh khoảng nghỉ (Pacing).
  - Chọn khoảng chương (Từ chương X đến chương Y hoặc All), cờ "Resume thông minh" (bỏ qua chương đã dịch).
  - `GlossaryDialog`: Bảng quản lý từ điển thuật ngữ phân loại theo tab (Nhân vật, Vũ khí/Bảo vật, Tông môn, Địa danh, Khác), cho phép thêm/sửa/xóa trực quan.
  - Nút "📚 Gộp Truyện Dịch" (gọi `MergeWorker` tạo file tổng có mục lục tiếng Việt) và "📱 Tạo PRC (Mobi)" (gọi `PrcWorker` chuyển sang sách đọc Kindle).
- [x] **Tích hợp Menubar (`gui/main_window.py`)**:
  - Thêm mục menu "🌐 AI Dịch Truyện (Gemini)" vào menu Công cụ (`menu_tools`).
  - Tự động điền thư mục lưu của truyện đang chọn vào hộp thoại dịch khi mở.

### ✅ Phase 16 — Đồng bộ Model Gemini chuẩn AskCpl & Bảo lưu chương truyện Trung Quốc (2026-09-16)
- [x] **Đồng bộ chuẩn 100% Model Fallbacks với AskCpl (`core/ai_translator.py`)**:
  - Cập nhật `DEFAULT_MODELS`: `["gemini-3.5-flash", "gemini-3-flash-preview", "gemini-flash-latest", "gemini-3.1-flash-lite", "gemini-flash-lite-latest"]`.
  - Loại bỏ hoàn toàn các model cũ/sai tên (`gemini-1.5-flash`, `gemini-2.0-flash`, `gemini-2.5-flash`) gây lỗi HTTP 404 `"models/... is not found for API version v1beta"`.
  - **Xử lý thông minh lỗi 503 (Server Overload)**: Khi Google báo 503 ở model hiện tại (ví dụ `gemini-3.5-flash` đang quá tải), hệ thống lập tức ghi log và tự động chuyển sang model fallback tiếp theo (`gemini-3-flash-preview`, `gemini-flash-latest`,...).
  - **Xử lý lỗi 404 & Model Restriction**: Tự động nhận diện chuỗi báo lỗi model restriction, loại bỏ model không khả dụng và tiếp tục thử model tiếp theo.
  - **Tích hợp live logging**: Truyền callback hiển thị trực tiếp model đang gọi trên log console của `TranslateDialog`.
- [x] **Bảo lưu chương truyện Trung Quốc (`gui/workers.py`)**:
  - Nhận diện truyện từ nguồn Trung Quốc (`is_vietnamese_host == False` hoặc `story_title.startswith("China-")`).
  - Khi tải xong, **KHÔNG tự động gộp file** và **KHÔNG xóa thư mục chương lẻ** (`save_dir`), bảo lưu 100% các file chương riêng lẻ trong thư mục để phục vụ dịch AI.

### ✅ Phase 17 — Tiện ích Tách Truyện Gộp & Smart Chunking Dịch Chương Dài (2026-09-17)
- [x] **Lõi Tách Truyện Gộp (`core/chapter_splitter.py`)**:
  - Hỗ trợ quét và bóc tách file HTML / TXT gộp (ví dụ `Cau.html`) thành danh sách các file chương riêng lẻ (`0001_...html`, `0002_...html`,...).
  - Tự động nhận diện ranh giới chương qua thẻ HTML (`<h2>`, `<h3>`, anchor `<a name='chap-...'>`) và Regex đa ngôn ngữ (Tiếng Trung: `第X章/回/节`, số đầu dòng; Tiếng Việt: `Chương X`, `Hồi X`, `Chapter X`).
  - Định dạng chuẩn UTF-8-SIG với cấu trúc CSS sạch, sẵn sàng nạp thẳng vào bộ dịch AI.
- [x] **Giao diện Tách Chương (`gui/chapter_splitter_dialog.py`)**:
  - `ChapterSplitterDialog`: Cho phép chọn file gộp, tự động gợi ý thư mục xuất `<tên_file>_tach/`.
  - Hỗ trợ nút "🔍 Quét Thử Danh Sách Chương" hiển thị bảng preview STT và tiêu đề trước khi tách.
  - Thanh tiến trình tách thời gian thực và nút mở trực tiếp thư mục sau khi hoàn thành.
  - Tích hợp nút bấm nhanh **"✂️ Tách File Gộp..."** ngay trên `TranslateDialog`, tự động gán thư mục vừa tách làm nguồn dịch.
  - Tích hợp vào menu chính **Công cụ** -> **"✂️ Tách Truyện Gộp Thành Từng Chương"**.
- [x] **Smart Chunking & Re-joining Dịch Chương Dài (`core/ai_translator.py`)**:
  - `split_text_into_chunks()`: Tự động đo độ dài chương. Nếu chương dài (> 1.400 chữ Hán), tự động chia nhỏ theo ranh giới đoạn văn / câu (`\n\n`, `\n`, `。`).
  - Dịch tuần tự từng phần với Glossary và Ngữ cảnh đầy đủ, sau đó tự động ghép nối (re-join) lại thành 1 file chương hoàn chỉnh.
  - Giải quyết triệt để vấn đề chương quá dài bị AI cắt cụt hoặc chỉ dịch được một phần nhỏ.

### ✅ Phase 18 — Tùy chọn Gộp hoặc Không Gộp File HTML Theo Chương (2026-09-17)
- [x] **Tùy Chọn Giao Diện (`gui/main_window.py`)**:
  - Bổ sung checkbox `Gộp các chương thành 1 tệp` (`chk_merge_files`) vào nhóm "Tùy Chỉnh Lưu Tệp".
  - **Mặc định luôn được kích hoạt (`Checked = True`)**; lưu và khôi phục trạng thái thông qua `QSettings` (`ui/merge_files`).
  - Tự động ràng buộc UX an toàn (`_on_merge_files_toggled`): khi người dùng bỏ chọn gộp file -> tự động vô hiệu hóa (`setEnabled(False)`) và bỏ chọn checkbox "Xóa thư mục tạm sau khi gộp" (`chk_delete_folder`) để chống mất toàn bộ file chương lẻ.
- [x] **Xử Lý Trong Lõi Tải (`gui/workers.py`)**:
  - `DownloadWorker.__init__`: Bổ sung tham số `is_merge_file: bool = True`.
  - Khi hoàn thành tải (`all_done`):
    - Nếu `is_merge_file == True`: Tự động gộp toàn bộ các chương thành 1 file tổng (`final_path`), kèm tùy chọn xóa thư mục tạm nếu được check.
    - Nếu `is_merge_file == False`: Bỏ qua bước gộp file, bảo lưu 100% các file chương riêng lẻ trong thư mục và ghi log thông báo chi tiết cho người dùng.

- [x] **Sửa Lỗi Import Path & Nhận Diện File Gộp Khi Dịch AI (`gui/main_window.py`, `gui/translate_dialog.py`)**:
  - Bổ sung `from pathlib import Path` trong `gui/main_window.py`, khắc phục hoàn toàn lỗi `NameError: Could not find name 'Path'` khi mở menu AI Dịch.
  - Nâng cấp luồng phát hiện file gộp: Khi người dùng chọn hoặc dán đường dẫn một file gộp (`.html`/`.txt`) vào ô thư mục nguồn của `TranslateDialog`, giao diện sẽ tự động cảnh báo màu đỏ và gợi ý bấm nút **"✂️ Tách File Gộp..."** để chia nhỏ các chương trước khi dịch.
  - Khi bấm "🚀 Bắt Đầu Dịch" trên một file gộp, hệ thống sẽ bật hộp thoại hỏi xác nhận và tự động mở công cụ tách file thay vì báo lỗi `NotADirectoryError`.

### ✅ Phase 19 — Khắc phục Lỗi Tách Trùng Chương & Làm Sạch Ký Tự \n Khi Dịch AI (2026-09-17)
- [x] **Khử Trùng Lặp & Khớp Chuẩn Anchor Khi Tách Chương (`core/chapter_splitter.py`)**:
  - Ưu tiên bóc tách theo cấu trúc chuẩn `<a name="chap-N"></a>` và bản đồ mục lục TOC `<a href="#chap-N">` của các file gộp do ứng dụng tải về.
  - Khắc phục triệt để lỗi thẻ `<h2>` lồng nhau (do file chương lẻ có sẵn `<h2>` và file gộp lại bọc thêm `<h2>`), loại bỏ hoàn toàn hiện tượng 1 chương bị nhân đôi thành 2 file (`0001` và `0002` cùng là Chương 1).
  - Bổ sung khử trùng lặp tiêu đề cho cả trường hợp quét theo thẻ Heading và Regex. Quét chính xác 1.543 / 1.543 chương của truyện 69shuba mà không bị lệch vị trí hay sót chương.
- [x] **Khử Lỗi Raw JSON & Ký Tự `\n` Thô Trong Bản Dịch (`core/ai_translator.py`)**:
  - Nâng cấp `_parse_translation_response`: tự động bóc tách đa tầng `content_vi`, lọc sạch các thẻ code block ````json`, rác cú pháp JSON khi Gemini trả về kết quả lỗi escape.
  - Tự động unescape chuỗi `\n` và `\"` thô thành ký tự xuống dòng và dấu ngoặc kép thực tế.
  - Cập nhật `save_translated_chapter`: chuẩn hóa phân đoạn `<p>`, đảm bảo không bao giờ để sót ký tự `\n\n` dạng text trên trình duyệt.

### ✅ Phase 20 — Nâng Cấp Pool Key & Xoay Vòng Account Chuẩn Anti-Ban AskCpl (2026-09-18)
- [x] **Khắc phục triệt để lỗi khóa key nhanh & dừng luồng dịch (`core/ai_translator.py`, `gui/translate_dialog.py`)**:
  - **Bảo lưu siêu dữ liệu Account Google**: `load_askcpl_key_objects()` và `enrich_key_objects()` tải trọn vẹn thông tin `email`, `project_id`, `status` từ AskCpl thay vì chỉ lấy mảng chuỗi trần.
  - **Account-Cluster Rotation**: Xây dựng class `AccountPool` luân chuyển theo tài khoản Google (`email`), tuyệt đối không gọi 2 lần liên tiếp vào các key thuộc cùng 1 tài khoản Google.
  - **Giữ giãn cách an toàn Anti-ban**: Bắt buộc `PER_ACCOUNT_MIN_GAP >= 8.0s` giữa 2 request vào cùng 1 Google account, kết hợp `_wait_pacing()` với Jitter ngẫu nhiên (`3.5s - 5.0s` + `0.5s - 1.5s`) phá vỡ tần số bot detection.
  - **Phân loại mã lỗi 429 & Hàng đợi Cooldown thông minh**:
    - **429 RPM/TPM**: Tự động parse `retryDelay` (thường ~65s) để đưa account vào hàng đợi cooldown tạm thời, **tuyệt đối không xóa hay vô hiệu hóa key**. Tự động chuyển sang account khác đang sẵn sàng.
    - **429 Daily Limit**: Khóa account 60 phút (`ACCOUNT_COOLDOWN = 3600s`).
    - **Cơ chế chống đốt dồn dập**: Nếu thử 3 account liên tiếp gặp limit, hệ thống tự động tạm dừng 15s để server Google giải tỏa lưu lượng.
  - **Đồng bộ tiến trình**: Sử dụng `get_shared_account_pool()` singleton dùng chung giữa các chương và các chunk trong suốt tiến trình dịch.
  - **Cập nhật giao diện**: `TranslateDialog` hiển thị chi tiết số lượng key và số lượng Google Account thực tế nạp từ AskCpl (VD: 156 keys từ 18 Google accounts).

## ⏭️ TODO tiếp theo
- Login Browser nhúng (WebEngineView) thay thế cho chức năng Mở Trình Duyệt ngoài.
- Auto-Update check (Check version trên Github releases).
- CAPTCHA detection & xử lý (Hỗ trợ bypass cloudflare nâng cao).
- Tích hợp OpenClaw (Chrome được mở bình thường) cho các site chặn headless/automation hoàn toàn.



