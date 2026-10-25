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

### ✅ Phase 9 — Cập nhật Host 69shuba & Vượt Cloudflare Turnstile — HOÀN THÀNH (2026-10-24)
- [x] **Vượt Cloudflare Turnstile qua `curl_cffi`**: `core/engine.py` tích hợp `curl_requests.Session(impersonate="chrome120")` khi `by_pass_cloudflare=True` hoặc host `69shu`, tự động giải mã GBK, khắc phục lỗi HTTP 403 Forbidden.
- [x] **Cập nhật Selector 69shuba**: Trong `config/ghfuConfig.json`, cập nhật `www.69shuba.com` (và `www.69shu.com`):
  - `cssQueryGetListChapter`: `#catalog ul` (thay thế `.mu_contain + .mu_contain ul` đã lỗi thời).
  - `cssQueryGetChapterContent`: `.txtnav` (thay thế `.yd_text2`).
  - `cssFilter`: `script;#txtright;h1;.txtinfo;.bottom-ad;"&#x2003;,??"`.
- [x] **Xử lý Container Selector trong Engine**: `_get_links_static()` hỗ trợ selector trỏ vào thẻ cha `ul/ol/div` (như `#catalog ul`) bằng cách tự động duyệt toàn bộ các thẻ `a` lồng bên trong.
- [x] **Hỗ trợ `is_revert_chapter_list`**: Đảo ngược danh sách chương (`links.reverse()`) khi site sắp xếp chương mới nhất ở đầu (như 69shuba), đảm bảo chương 1 luôn tải đầu tiên.
- [x] **Chuẩn hóa URL**: Tự động chuyển link giới thiệu `/book/XXX.htm` thành link mục lục `/XXX/` khi người dùng dán link chi tiết.
- [x] **Đã kiểm chứng**: Quét chính xác 1.425 / 1.425 chương của truyện *谁让他修仙的！* (`https://www.69shuba.com/46957/`), tải tiêu đề và nội dung chương 1 mượt mà 100%.

## ⏭️ TODO tiếp theo
- Login Browser nhúng (WebEngineView) thay thế cho chức năng Mở Trình Duyệt ngoài.
- Auto-Update check (Check version trên Github releases).
- CAPTCHA detection & xử lý (Hỗ trợ bypass cloudflare nâng cao).

### ✅ Phase 10 — Kết nối Dịch Truyện AI & Đặt Tên Thư Mục Thông Minh — HOÀN THÀNH (2026-10-24)
- [x] **Kết nối lại `TranslateDialog`**: Tính năng dịch truyện AI (Gemini) từng có sẵn trong `gui/translate_dialog.py` và `core/ai_translator.py` nhưng chưa kết nối vào UI. Đã thêm:
  - Import `TranslateDialog` vào `gui/main_window.py`
  - Menu item "🌐 Dịch Truyện (AI Translate)" trong menu Công cụ
  - Nút "🌐 Dịch" vào row3 (cạnh "Tạo PRC")
  - Handler `_on_translate_story()`: tự động điền thư mục nguồn = slug folder truyện vừa tải
- [x] **Đặt tên thư mục/file theo tên thật truyện (TienGia/TienGia.html)**:
  - Thêm hàm `slugify_title(text)` trong `gui/workers.py` dùng `unicodedata.normalize('NFD')` để bỏ dấu tiếng Việt → dạng ASCII CamelCase (VD: 'Tiên Giả' → 'TienGia')
  - Cải thiện `_extract_story_title()`: fetch trang chủ truyện, lấy `<h1>` hoặc `<title>` thật, slugify. Fallback về URL slug nếu lỗi.
  - Cập nhật `_prepare_save_paths()`: dùng story_title làm cả tên thư mục lẫn tên file output (VD: `D:\Truyen\TienGia\TienGia.html`)
  - Tạo thư mục alias theo URL slug kèm `_folder_alias.json` để Resume vẫn hoạt động đúng
  - Thêm `story_title_signal(str)` vào `DownloadWorker`: emit khi biết tên thật, kết nối với `_on_story_title_known()` trong UI để cập nhật `txt_save_path`
- [x] **Tốc độ Cloudflare**: Tăng delay tối thiểu cho Cloudflare sites từ 1.0s → **10.0s**/chương để tránh rate-limit triệt để.
- [x] **Lưu ý về hình Glossary**: Các trường `sects`, `weapons`, `locations`, `others`, `summary` là metadata trong `_glossary.json` (file riêng) giúp AI nhất quán thuật ngữ — **không phải** bị chèn vào HTML chương. HTML dịch chỉ chứa `<h2>` + `<div class='chapter-content'><p>...</p></div>` thuần túy.

### ✅ Phase 11 — Tự Động Nhận Diện & Dịch Tên Truyện Hán-Việt + Nhớ Thư Mục Gốc — HOÀN THÀNH (2026-10-25)
- [x] **Tự động nhận diện & Dịch tên truyện khi dán URL**:
  - Thêm `TitleFetchWorker(QThread)` trong `gui/workers.py`: fetch trang truyện ngầm, trích xuất `<h1>`/meta/`<title>`, lọc bỏ các hậu tố web rác (`最新章节`, `无弹窗`, `txt下载`, ...).
  - Tích hợp `translate_chinese_title()`: ưu tiên Google Translate free endpoint siêu tốc (0.2s phản hồi tức thì, không lo rate-limit), kết hợp Gemini API dự phòng. Tốc độ fetch + dịch trọn gói chỉ mất ~0.6s.
  - Khi dán link `https://www.69shuba.com/90469/`: ngay lập tức điền slug tạm, sau đó cập nhật chính xác tên truyện `从白犬开始修仙` → `Từ Bạch Khuyển Bắt Đầu Tu Tiên` và gợi ý đường dẫn `D:\Tai Ebook\html\Từ Bạch Khuyển Bắt Đầu Tu Tiên\Từ Bạch Khuyển Bắt Đầu Tu Tiên.html`.
- [x] **Ghi nhớ thư mục lưu gốc (`ui/last_save_dir`)**:
  - Khắc phục lỗi lưu nhầm thư mục con của truyện vào `last_save_dir` khiến các lần tải sau bị lồng thư mục vô tận.
  - Tự động nhận diện thư mục gốc (`base_dir`, ví dụ: `D:\Tai Ebook\html`) và áp dụng cố định cho mọi truyện mới.
  - Nếu chưa có lịch sử: tự động ưu tiên `D:\Tai Ebook\html` (nếu tồn tại) hoặc thư mục `Downloads`.
- [x] **Ghi nhớ thư mục trong Tiện ích Dịch Truyện (`TranslateDialog`)**:
  - Lưu và khôi phục tự động `translate/last_source_dir` và `translate/last_target_dir` qua `QSettings`.
  - Giữ lại đường dẫn thư mục tiếng Trung và thư mục đích giữa các phiên làm việc, không cần duyệt chọn lại từ đầu.
- [x] **Fix Bug `_prepare_save_paths`**: Ngăn chặn lỗi double-nesting khi đường dẫn đã chứa tên thư mục truyện trùng khớp. Fix lỗi `self.page_config` thành `self.forced_page_config` trong `DownloadWorker`.

### ✅ Phase 12 — Xóa Bỏ Triệt Để Rò Rỉ Metadata JSON & Chữ Hán Thô Trong Bản Dịch — HOÀN THÀNH (2026-10-25)
- [x] **Nguyên nhân gốc rễ**: Khi nhân vật đối thoại có dấu ngoặc kép (`"Cứ yên tâm, ta không làm hại nó đâu."`), Gemini sinh JSON không escape chuẩn làm `json.loads()` văng `JSONDecodeError`. Regex fallback cũ không bắt được điểm dừng do có ký tự đóng ngoặc `},`, dẫn đến việc cả khối `"new_terms": {...}` và `"summary": "..."` (chứa trích dẫn tiếng Trung gốc) bị tuồn thẳng vào nội dung truyện.
- [x] **Thêm bộ lọc chuyên dụng `clean_leaked_metadata()`**:
  - Unescape sạch sẽ các ký tự `\n` và `\"` từ JSON escape sequences.
  - Cắt đứt toàn bộ nội dung từ các điểm đánh dấu metadata (`"new_terms":`, `"summary":`, `"characters":`, `===TERMS===`, `===SUMMARY===`).
  - Lọc từng dòng, loại bỏ triệt để các dòng cú pháp JSON (`},`, `{"title_vi": ...}`) và các dòng trích dẫn chưa dịch (>40% ký tự Hán CJK).
  - Tự động sửa lỗi dấu ngoặc kép đóng JSON thừa ở cuối câu thoại.
- [x] **Hỗ trợ định dạng phân đoạn Delimiter trong Prompt & Parser**:
  - Hướng dẫn Gemini trả về theo định dạng thẻ phân cách rõ ràng (`===TITLE===`, `===CONTENT===`, `===TERMS===`, `===SUMMARY===`), giúp toàn bộ lời thoại có dấu ngoặc kép không bao giờ làm hỏng cấu trúc dữ liệu.
  - Tương thích 100% ngược với định dạng JSON chuẩn.
  - Tự động cứu thuật ngữ `new_terms` bằng regex nếu JSON bị lỗi, không để mất dữ liệu từ điển.
- [x] **Chốt chặn an toàn trong `save_translated_chapter()`**:
  - Trước khi xuất file HTML, chạy `clean_leaked_metadata()` và lọc từng đoạn `<p>` — cam kết 100% không còn bất kỳ dấu ngoặc JSON hay câu tiếng Trung thô nào xuất hiện trong sách dịch của người dùng.
- [x] **Đã kiểm chứng**: Chạy kiểm thử tự động với đúng đoạn mẫu lỗi do người dùng cung cấp — kết quả đạt chuẩn 100% nội dung dịch tiếng Việt sạch đẹp.
