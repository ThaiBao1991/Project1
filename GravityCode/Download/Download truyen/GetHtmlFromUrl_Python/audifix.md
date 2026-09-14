# Audit chức năng — GetHtmlFromUrl Python Port

Ngày audit: 2026-09-14  
Phạm vi: so sánh mã Python với `../gethtmlfromurl-git-e78ccddd8982df4992a26d85295b91df9386a41c`, cấu hình `ghfuConfig.json`, và kiểm tra biên dịch Python. Đây là audit tĩnh; chưa chạy tải thật tới từng site vì các site nguồn thay đổi độc lập theo thời gian.

## Tóm tắt

Port đã có luồng tải cơ bản, tải đồng thời, resume, gộp HTML và tạo PRC. Tuy nhiên chưa đạt mục tiêu "100% tính năng Java": nhiều cờ trong 513 cấu hình host được đọc vào nhưng không được engine thực thi. Hệ quả lớn nhất là một phần đáng kể trong 509 host kế thừa (forum, site phân trang đặc biệt, site yêu cầu JavaScript/AJAX, và link tương đối) sẽ tải thiếu chương hoặc sai nội dung.

| Mức | Số mục | Ý nghĩa |
|---|---:|---|
| P0 | 1 | Có thể tải sai phạm vi người dùng đã chọn |
| P1 | 7 | Hỏng chức năng chính hoặc mất độ tin cậy cho nhiều host |
| P2 | 8 | Thiếu tính năng/độ bền hoặc UX không đúng mô tả |

## P0 — sửa trước

### A-01 — Chọn phạm vi tải không được đồng bộ với worker

- Bằng chứng: `gui/workers.py:184-205` lấy `selected_links` và bắt đầu tải ngay trong `run()`. Dialog chỉ được mở sau signal `chapter_list_ready` tại `gui/main_window.py:648-660`; signal từ `QThread` được xử lý bất đồng bộ nên không thể chặn worker. Việc gán lại `worker.start_idx/end_idx` sau đó không thay lại `selected_links` đã cắt.
- Tác động: bật **Chọn Phạm Vi Tải** vẫn có thể tải toàn bộ truyện hoặc phạm vi mặc định. Đây là lỗi đã được ghi trong `projectLog.md` nhưng vẫn tồn tại.
- Fix đề xuất: tách bước lấy mục lục khỏi worker tải chương. Main UI mở dialog trước, rồi tạo worker mới với `start_idx/end_idx` đã chốt; hoặc dùng cơ chế request/response thread-safe để worker chờ lựa chọn.
- Kiểm thử: fake engine trả 10 URL, chọn 3–5, xác nhận chỉ request URL chỉ số 2, 3, 4 và TOC có đúng 3 chương.

## P1 — ảnh hưởng trực tiếp đến khả năng tải

### A-02 — Engine bỏ qua phần lớn semantic của `PageConfig`

- Bằng chứng: `models/page_config.py:22-33` có các cờ tương thích Java, nhưng ngoài filter UI, tìm kiếm chỉ thấy chúng trong `gui/config_mgr_dialog.py`; `core/engine.py` không sử dụng `is_chapter_link_absolute`, `is_enable_chapter_sign`, `is_revert_chapter_list`, `is_forum_type`, `is_use_jsoup_get`, `over_max_size_page_count_state`, `script_js`, `main_host`, hoặc `use_brute_force_method`.
- So với Java: `GetHtmlCss.java` và `GetHtmlCsMix.java` thực thi các nhánh forum, title sign, AJAX đặc thù, CAPTCHA và paging state. Python hiện chỉ có một AJAX rule mới cho `truyennet.org`.
- Tác động: các host có cờ này hiện không tương đương bản cũ. Ví dụ config có 6 forum host và ít nhất 10 host `isRevertChapterList=true`; thứ tự chương/HTML forum có thể sai.
- Fix đề xuất: lập ma trận hỗ trợ cho từng cờ và triển khai chung trước (url resolution, đảo list, chapter sign, paging state), sau đó port các adapter host đặc biệt. Nếu chưa hỗ trợ thì chặn tải tự động và dẫn sang Manual GET, không hiển thị như host tự động hỗ trợ.

### A-03 — Phân trang tĩnh không tương thích format config Java

- Bằng chứng: `core/engine.py:237-249` chỉ thay `{i}` và `{i-1}`, còn nối trực tiếp các pattern khác. Config có 33 paging pattern chứa `;replace=...`, `{i+1}`, hoặc biểu thức thay thế; ví dụ `sstruyen.com`, `www.70shu.com`, `m.55dushu.com`.
- Tác động: URL trang tiếp theo bị tạo sai, khiến thiếu chương hoặc request URL lỗi. `overMaxSizePageCountState` cũng bị bỏ qua nên không xử lý được trang redirect về đầu/cuối như Java.
- Fix đề xuất: port logic `UrlHandler.getPagePatternUrl` và `GetHtmlCss.checkPageFound` từ Java, bao gồm parsing `;replace=...&with=...`, `{i±n}` và điều kiện dừng theo state.
- Kiểm thử: unit test bảng pattern thực từ JSON, kiểm tra URL trang 2/3 và điều kiện kết thúc.

### A-04 — Link chương tương đối được ghép sai và bỏ qua `main_host`

- Bằng chứng: `gui/workers.py:228` ghép mọi link không phải `http` thành `https://{page_config.page_code}{link}`. `core/engine.py` đã import `urljoin` nhưng không dùng. Cờ `is_chapter_link_absolute` và `main_host` không được dùng.
- Tác động: link dạng `chapter-1`, `../chapter-1`, `//cdn...`, host wildcard/host có protocol, hoặc chapter được trả từ subdomain sẽ sai URL. Config đang có nhiều host `isChapterLinkAsolute=false`.
- Fix đề xuất: dùng `urllib.parse.urljoin(story_url, href)` làm mặc định; chỉ dùng `main_host` khi adapter host yêu cầu, đồng thời tôn trọng cờ absolute.

### A-05 — Site Manual/JavaScript và browser login là stub

- Bằng chứng: `gui/main_window.py:739-740` chỉ báo "Sẽ mở MKBrowser trong tương lai"; `:773-774` chỉ thông báo login. `script_js` được lưu trong config nhưng không có nơi hiển thị/copy/chạy. `is_manual_get` cũng không chi phối luồng tự động.
- Tác động: các host cần script browser hoặc login (nhiều entry `isManualGet=true`) mất workflow vốn có của Java: mở browser, chạy/copy script, rồi dán HTML vào Manual GET.
- Fix đề xuất: ưu tiên một trong hai: tích hợp `QWebEngineView` với cookie jar; hoặc khôi phục workflow ngoài-browser an toàn (mở URL + dialog hiển thị script có nút copy). Manual GET cần nhận cả HTML rồi trích `<a href>`, không chỉ danh sách URL.

### A-06 — Các adapter AJAX/đặc thù từ Java chưa được port

- Bằng chứng: Java có nhánh riêng cho `sstruyen.com`, `tangthucac.com`, `truyendich.org`, truyencv, wikidich và tangthuvien trong `GetHtmlCss.java`/`GetHtmlCsMix.java`. Python chỉ có `_get_links_ajax()` theo template JSON, yêu cầu JSON có key `data` và regex `page(ID, page)` (`core/engine.py:103-205`).
- Tác động: các site cũ nêu trên không thể giả định là hoạt động chỉ nhờ selector CSS; một số endpoint cần POST, headers hoặc parse JSON riêng.
- Fix đề xuất: port theo adapter tách riêng, có fixture HTTP/HTML cho từng site; adapter tổng quát JSON nên cho phép method, headers, JSON path và URL/id regex qua config.

### A-07 — Tải đa luồng dùng chung `requests.Session`/`cloudscraper`

- Bằng chứng: một `GetHtmlEngine` và một `requests.Session`/`cf_scraper` được tạo tại `gui/workers.py:69`, rồi được gọi đồng thời bởi `ThreadPoolExecutor` tại `:272-286`.
- Tác động: `requests.Session` và cookie jar không nên được dùng đồng thời không khóa; với max connection > 1 có thể sinh lỗi ngẫu nhiên, cookie lẫn hoặc retry không ổn định — đặc biệt sau Quick Login/Cloudflare.
- Fix đề xuất: tạo session/scraper theo thread (thread-local) nhưng clone cookie/header ban đầu, hoặc dùng lock quanh request khi cần giữ session chung. Đồng thời viết test concurrent bằng mock transport.

### A-08 — Đóng ứng dụng không thực sự hủy PRC process

- Bằng chứng: `PrcWorker.stop()` có gọi `compiler.cancel()` (`gui/workers.py:575-579`), nhưng `MainWindow.closeEvent()` chỉ `wait(2000)` cho `prc_worker`, không gọi `stop()` (`gui/main_window.py:848-856`).
- Tác động: KindleGen có thể vẫn chạy sau khi đóng cửa sổ, trái với mô tả Phase 8 và có thể giữ file/temp directory.
- Fix đề xuất: trong `closeEvent`, gọi `self.prc_worker.stop()` trước `wait`; nếu timeout, thông báo trạng thái thay vì thoát im lặng.

## P2 — hoàn thiện tính năng và độ bền

### A-09 — Checkbox “Mỗi chương thành 1 tệp” không có tác dụng

- Bằng chứng: `is_divide_file` được nhận tại `DownloadWorker.__init__` nhưng không được đọc ở nơi nào khác. `_save_single_chapter()` luôn chạy sau mỗi chương (`gui/workers.py:259-260`) và download thành công luôn tự gộp (`:346-364`).
- Tác động: UI hứa hai chế độ lưu nhưng kết quả thực tế luôn là file tạm từng chương + file tổng. Người dùng không thể chọn chỉ chia file như Java.
- Fix đề xuất: xác định semantics mong muốn: (a) chia file thì không tự gộp, hoặc (b) đổi label thành “Giữ file chương để resume”; bổ sung test đầu ra cho HTML/TXT ở cả hai chế độ.

### A-10 — Timeout trong Settings không được áp dụng

- Bằng chứng: `SettingsDialog` lưu `download/timeout` (`gui/settings_dialog.py:67-76`) nhưng request dùng hằng số 25/20/15 giây (`core/engine.py:66, 151, 153`). Worker chỉ đọc delay và số connection.
- Tác động: chỉnh timeout trên UI không thay đổi hành vi.
- Fix đề xuất: truyền timeout vào engine hoặc hàm đọc QSettings tập trung; dùng chung cho HTML, AJAX và retry.

### A-11 — Cập nhật config, kiểm tra update, help và embedded login chưa được triển khai

- Bằng chứng: `_on_check_update()` và `_on_download_config()` chỉ hiện thông báo (`gui/main_window.py:767-771`); Help cũng chỉ placeholder (`:764-765`).
- Tác động: các menu xuất hiện như chức năng thật nhưng không thực hiện action.
- Fix đề xuất: ẩn/disable menu chưa có hoặc triển khai. Download config cần backup, validate JSON schema, hiển thị diff và chỉ ghi sau xác nhận.

### A-12 — Config Manager có nguy cơ làm rơi field JSON chưa có trong dataclass

- Bằng chứng: `PageConfigManager.load_config()` chỉ gán key khi `hasattr(pc, snake_key)`; `save_config()` chỉ serialise `pc.__dict__` (`core/page_config_mgr.py:25-38, 53-73`). Mọi key mới từ file config server sẽ biến mất sau “LƯU TẤT CẢ”.
- Tác động: update config có thể âm thầm mất metadata/option mới, kể cả khi Python chưa hiểu chúng.
- Fix đề xuất: giữ `extra_fields` theo từng config và round-trip nguyên vẹn các key không biết; thêm test load-save so sánh JSON (trừ key do app chủ động thêm).

### A-13 — Resume/error reporting sai số và resume có thể không tải lại link lỗi

- Bằng chứng: mỗi lần retry thất bại cuối cùng `failed_links.append(full_link)` (`gui/workers.py:250`), nhưng nếu auto-resume sau đó thành công thì link cũ không bị xóa. `download_failed_count` cũng là tổng lỗi quá khứ, không phải số thiếu cuối cùng. Resume dialog hiển thị `failed_links`, trong khi worker thực tế dựa `chapters_status`.
- Tác động: `_ErrorLog.txt`/Resume UI có thể báo link đã thành công là lỗi; thông báo “còn N chương” không chính xác.
- Fix đề xuất: tạo danh sách lỗi từ `chapters_status` tại thời điểm kết thúc; reset/cập nhật counters mỗi vòng retry. Kiểm thử một chapter fail lần đầu rồi thành công lần sau.

### A-14 — Progress bar không phản ánh số chapter hoàn thành khi chạy song song

- Bằng chứng: `_on_progress()` tính `done = idx - start + 1` từ index chapter (`gui/main_window.py:636-646`), không đếm event đã hoàn tất.
- Tác động: tiến độ có thể nhảy lên cao rồi lùi hoặc đạt 100% khi các index thấp hơn còn đang chạy.
- Fix đề xuất: duy trì set/count các local index đã kết thúc và tính từ count/total; phân biệt success/failure/cancel.

### A-15 — PRC builder không XML-escape title và dùng temp directory cố định

- Bằng chứng: `_build_opf_package()` chèn `title` và `chap_title` thẳng vào OPF/NCX (`core/prc_compiler.py:140-164`); temp luôn là `%TEMP%/prc_build_temp` (`:191-193`).
- Tác động: ký tự `&`, `<` trong tên truyện/chương làm OPF/NCX lỗi. Hai cửa sổ tạo PRC đồng thời có thể xóa/ghi đè gói của nhau.
- Fix đề xuất: dùng `html.escape(..., quote=True)` cho XML text và `tempfile.mkdtemp(prefix="prc_build_")`, cleanup trong `finally`.

### A-16 — Auto-install package khi mở app không có consent và có thể treo UI

- Bằng chứng: `main.py:25-59` gọi `pip install` đồng bộ ngay khi import thiếu package.
- Tác động: lần chạy app có thể bị treo/lỗi network; tự thay đổi môi trường Python không có xác nhận người dùng.
- Fix đề xuất: hiển thị dialog trước khi cài, hỗ trợ Cancel và timeout; hoặc phát hành môi trường/installer kèm dependency.

## Những điểm đã xác nhận là ổn

- `python -m compileall -q GetHtmlFromUrl_Python` hoàn tất với exit code 0.
- Config Python có đủ toàn bộ 509 `pageCode` từ Java và thêm 4 host mới: `metruyenchuvn.org`, `metruyenhot.me`, `metruyenhotvn.com`, `truyennet.org`.
- Có cơ chế retry, resume JSON, BOM UTF-8-SIG, auto-merge và chặn auto-PRC khi worker báo thất bại.

## Lộ trình xử lý đề nghị

1. Sửa A-01, A-03, A-04 và A-10, kèm unit tests bằng fixture — đây là nền tảng để tải đúng link/phạm vi.
2. Sửa A-02/A-06/A-05 theo ma trận host: common rules trước, adapter đặc thù và browser/manual workflow sau.
3. Sửa A-07, A-08, A-13, A-15 để tránh lỗi ngẫu nhiên và mất tiến trình.
4. Hoàn thiện UX/config ở A-09/A-11/A-12/A-14/A-16.

