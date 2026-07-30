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

## ⏭️ TODO tiếp theo
- Login Browser nhúng (WebEngineView) thay thế cho chức năng Mở Trình Duyệt ngoài.
- Auto-Update check (Check version trên Github releases).
- CAPTCHA detection & xử lý (Hỗ trợ bypass cloudflare nâng cao).
