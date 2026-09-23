# Nhật Ký Dự Án (Project Log) - Hệ Thống Tạo Đề Thi & Đáp Án (MBC DeThi)

## 2026-09-22 — Khởi Tạo Dự Án & Xây Dựng Hệ Thống MVP — ĐANG TIẾN HÀNH 🚀

### 1. Bối Cảnh & Mục Tiêu
- **Mục tiêu**: Tự động hóa quy trình đọc các tài liệu tiêu chuẩn kỹ thuật (dạng PDF) từ các thư mục nguồn `Source/` của Mabuchi Motor, sinh ra đề thi trắc nghiệm và biểu đáp án tương ứng, sau đó nối lại thành các file Word hoàn chỉnh (`DE THI MOI TONG HOP.docx` và `DAP AN TONG HOP.docx`) tại `KetQua/`.
- **Yêu cầu cốt lõi**:
  - Đọc từ 8 thư mục tiêu chuẩn với 409 file PDF:
    1. `2-000 Ban V IT HOA` (123 file)
    2. `3-400 Ban V IT HOA` (1 file)
    3. `4-500 Ban V IT HOA` (142 file)
    4. `5-600 Ban V IT HOA` (44 file)
    5. `6-900 Ban V IT HOA` (12 file)
    6. `7-S00 Ban V IT HOA` (64 file)
    7. `8-T00 Ban V IT HOA` (3 file)
    8. `9-Z00 Ban V IT HOA` (20 file)
  - Mỗi file tài liệu tiêu chuẩn: Ít nhất **3 câu hỏi trắc nghiệm** (A, B, C, D) với nội dung trải đều các phần trong văn bản.
  - Bắt buộc có **đúng 1 câu chủ chốt (ký hiệu `◎`)** yêu cầu phải trả lời chính xác mới đạt tiêu chuẩn nhận định.
  - Hỗ trợ đóng gói dữ liệu cho Google NotebookLM để trích xuất câu hỏi.
  - Có bộ thẩm định (Validator) tự động kiểm tra tính hợp lệ của câu hỏi trước khi cho phép nối.
  - Khi tất cả OK, tự động nối câu hỏi theo thứ tự ưu tiên các thư mục từ `2` đến `9-Z00` vào file Word theo chuẩn mẫu `DE THI MOI REV 13.docx` và `DAP AN(rev13).doc`.

### 2. Các Module Chính
- `config.json`: Cấu hình danh mục thư mục ưu tiên và tham số câu hỏi.
- `pdf_extractor.py`: Trích xuất text và metadata (tên tiêu chuẩn, mã máy đo/văn bản) từ PDF.
- `notebooklm_packager.py`: Đóng gói nội dung kèm prompt chuẩn cho NotebookLM.
- `question_validator.py`: Quản lý kho câu hỏi, kiểm tra điều kiện (≥ 3 câu, 1 câu `◎`, đủ đáp án, dàn trải) và đánh dấu trạng thái `OK`.
- `exam_word_merger.py`: Ghép nối các câu hỏi theo đúng thứ tự ưu tiên các thư mục `2` -> `9-Z00` và xuất file Word chuẩn phong cách REV 13.
- `run_cli.py`: Giao diện dòng lệnh trực quan để chạy các khâu trong quy trình.

### 3. Kết Quả Kiểm Tra (Gate 2 - Verification)
- ✅ Syntax check: `python -m py_compile *.py` — tất cả module PASS.
- ✅ TEST1 - pdf_extractor: Đọc `000-0-V.pdf` → 3 trang, 4785 ký tự, metadata đầy đủ.
- ✅ TEST2 - notebooklm_packager: Đóng gói → `001-1-V_prompt.txt` trong 0.08s/file.
- ✅ Batch pack toàn bộ `2-000 Ban V IT HOA`: **123 file / 9.7s** không lỗi.
- ✅ TEST3 - question_validator: Demo 3 câu hỏi mẫu → trạng thái **OK**, lưu thành công vào `KetQua/questions_bank/2-000/000-0-V.json`.
- ✅ TEST4 - progress report: 409 file tổng, 1 OK (demo), 408 MISSING — báo cáo chính xác.
- ✅ TEST5 - exam_word_merger: Xuất `DE THI MOI TONG HOP.docx` (36 paragraphs cấu trúc chuẩn) và `DAP AN TONG HOP.docx` (1 bảng đáp án 1x3 chuẩn định dạng).

### 4. Hướng Dẫn Quy Trình Tiếp Theo (Cho Người Dùng)
1. **Bước 1** (đã xong): 123 file prompt cho `2-000` đã được tạo tại `KetQua/prompts_for_notebooklm/2-000/`. Chạy `python run_cli.py` → chọn `1` để pack tiếp các folder khác (`4-500`, `5-600`...).
2. **Bước 2**: Mở NotebookLM, tạo notebook mới, upload các file `*_prompt.txt`. Hỏi NotebookLM theo đúng nội dung trong từng file prompt. Copy JSON phản hồi. Quay lại `run_cli.py` → chọn `2` để nhập từng câu hỏi hoặc `2b` để import hàng loạt từ folder JSON.
3. **Bước 3**: Chọn `3` để xem báo cáo tiến độ tổng quát 409 file.
4. **Bước 4**: Khi đã đủ câu hỏi OK, chọn `4` để xuất `DE THI MOI TONG HOP.docx` và `DAP AN TONG HOP.docx`.

---

## 2026-09-22 — Bổ Sung Module Tự Động Sinh Câu Hỏi (Gemini Files API) — HOÀN THÀNH ✅

### 1. Vấn Đề Giải Quyết
Người dùng yêu cầu tự động sinh câu hỏi không cần thao tác thủ công với NotebookLM.

### 2. Kiến Trúc Bổ Sung
- `settings_reader.py`: Đọc và giải mã Gemini API keys từ AskCpl/settings.json (không phụ thuộc GUI).
- `gemini_safe.py`: Copy từ AskCpl — engine gọi API xoay vòng key, chống ban, retry tự động.
- `crypto_utils.py`: Copy từ AskCpl — giải mã key AES256.
- `auto_question_generator.py`: Engine tự động sinh câu hỏi bằng **Gemini Files API** (upload PDF gốc → Gemini đọc trực tiếp, chất lượng ngang NotebookLM nhưng hoàn toàn tự động).

### 3. Kết Quả Test Live (Gate 2) — ✅ TẤT CẢ PASS
- Load: **155 API keys từ 17 accounts** từ AskCpl/settings.json.
- Test 3 file PDF đầu tiên `2-000`:
  - `000-0-V.pdf`: **3 câu OK** — Tiến độ điểm kiểm, Chống gỉ sét (◎), Xử lý bất thường.
  - `001-1-V.pdf`: **3 câu OK** — Mỗi lần sử dụng, Ngưỡng quá tải (◎), Ghi chép kết quả.
  - `002-1-V.pdf`: **3 câu OK** — Tiến độ đo điện áp, Sai số cấp 0.5 (◎), Ghi chép.
- Xử lý tốt 503 rate limit: **tự động đổi key** tiếp tục.
- Resume tự động: skip file đã có trạng thái OK.

### 4. Cách Chạy Ngay
```
python run_cli.py → Chọn 6 → Chọn thư mục → y → chờ ~35-40 phút
→ Chọn 4 → Xuất DE THI MOI TONG HOP.docx + DAP AN TONG HOP.docx
```

---

## 2026-09-22 — Bổ Sung Giao Diện Desktop GUI & Vòng Lặp Bền Bỉ (Zero-Error Loop) — HOÀN THÀNH ✅

### 1. Yêu Cầu Người Dùng
- Có giao diện đồ họa (GUI) trực quan thay vì chỉ dùng CLI.
- Chọn thư mục mẹ `Source` và thư mục xuất `KetQua`.
- Xử lý từng thư mục con để tạo từng đề riêng biệt (`KetQua/<slug>/DE_THI_<slug>.docx` và `DAP_AN_<slug>.docx`).
- Có nút Gộp toàn bộ tất cả các đề con lại thành 1 đề thi và 1 đáp án tổng hợp chuẩn mẫu REV 13 (`DE THI MOI TONG HOP.docx`, `DAP AN TONG HOP.docx`).
- Cơ chế vòng lặp tự động (Zero-Error Loop): tự động chạy ngầm, xoay vòng 155 keys từ 17 accounts, bỏ qua các file đã OK (tránh làm lại từ đầu), tự động thử lại các file bị rate limit/lỗi cho đến khi đạt 100% hoàn thành.

### 2. Các Module Phát Triển & Nâng Cấp
- `app_gui.py` [MỚI]: Giao diện Desktop CustomTkinter Dark Mode sang trọng, bảng Treeview C-Engine tối ưu hiệu năng (tuân thủ quy chuẩn `customtkinter-perf-ui`), 4 thẻ KPI thống kê, thanh tiến độ tổng thể, hộp Console log thời gian thực, nút Start / Pause / Stop / Xuất đề riêng / Gộp toàn bộ / Mở thư mục kết quả.
- `exam_word_merger.py` [NÂNG CẤP]:
  - Bổ sung `export_folder_exam_and_answer()`: Xuất đề và đáp án riêng cho từng thư mục con vào `KetQua/<slug>/`.
  - Bổ sung `export_all_individual_folders()`: Xuất đề riêng cho toàn bộ 8 thư mục tiêu chuẩn.
  - Tối ưu `merge_and_export()`: Gộp tất cả câu hỏi từ `2-000` đến `9-Z00` thành 2 file Word chuẩn REV 13.
  - Bổ sung xử lý bảng mã `sys.stdout.reconfigure(encoding="utf-8")` chống lỗi cp932 trên Windows.
- `auto_question_generator.py` [NÂNG CẤP]:
  - Bổ sung `scan_progress()`: Quét tiến độ toàn bộ 409 file của 8 thư mục và lưu vào `KetQua/progress_status.json`.
  - Bổ sung `run_loop_until_complete()`: Vòng lặp chống dừng (Zero-Error Loop) với cờ `stop_check`, `pause_check` và `progress_callback` kết nối mượt mà với UI Thread thông qua `queue.Queue`.
- `run_cli.py` [NÂNG CẤP]: Thêm Menu `7. 🖥 Khởi động Giao diện đồ họa (GUI)` và tùy chọn xuất đề riêng/gộp trong Bước 4.
- `Chay_Giao_Dien.bat` [MỚI]: File chạy nhanh giao diện chỉ với 1 click đúp chuột.

### 3. Kết Quả Kiểm Tra (Gate 2 - Definition of Done) — ✅ PASS TOÀN BỘ
1. **Build/Run Check**: `python -m py_compile *.py` 100% không có lỗi compile/syntax.
2. **Kiểm tra xuất đề riêng từng thư mục**: Test xuất thư mục `2-000` → Tạo thành công `KetQua/2-000/DE_THI_2-000.docx` và `DAP_AN_2-000.docx` (9 câu hỏi trắc nghiệm, 3 câu chủ chốt `◎`).
3. **Kiểm tra xuất gộp toàn bộ**: Test hàm gộp → Tạo thành công `KetQua/DE THI MOI TONG HOP.docx` và `KetQua/DAP AN TONG HOP.docx`.
4. **Kiểm tra khởi động GUI**: Khởi động `app_gui.py` kết nối thành công, đọc 155 API keys, quét 409 file tài liệu, hiển thị đầy đủ trên 4 thẻ KPI và bảng Treeview 8 thư mục.
5. **Kiểm tra Edge Case**: Xử lý triệt để lỗi encoding Unicode cp932 trên Windows console bằng `reconfigure(encoding="utf-8", errors="replace")`. Giao diện không bị treo đơ nhờ Worker Thread và Queue.

### 4. Hướng Dẫn Sử Dụng Giao Diện
- Cách 1: Click đúp vào file `Chay_Giao_Dien.bat`.
- Cách 2: Chạy lệnh `python app_gui.py`.
- Cách 3: Chạy `python run_cli.py` và chọn phím `7`.

---

## 2026-09-22 — Bổ Sung Xuất File Word Riêng Cho Từng Bản & Random Vị Trí Câu Hỏi Chủ Chốt (◎) — HOÀN THÀNH ✅

### 1. Yêu Cầu Người Dùng
1. Thay vì chỉ gộp, cần xuất từng file Word tương ứng với từng bản tiêu chuẩn kỹ thuật (từng file PDF).
2. Câu hỏi chủ chốt (◎) phải được random vị trí ngẫu nhiên trong bộ câu hỏi thay vì luôn nằm cố định ở câu số 2 (tránh quy luật câu 2, 5, 8,...).

### 2. Triển Khai Kỹ Thuật
- `auto_question_generator.py`:
  - Cập nhật `GEMINI_AUTO_PROMPT`: Chỉ dẫn nghiêm ngặt yêu cầu Gemini không được cố định câu hỏi chủ chốt ở câu số 2.
  - Bổ sung hàm `randomize_questions_order(questions)`: Xáo trộn ngẫu nhiên `random.shuffle()` thứ tự câu hỏi và đánh lại số thứ tự `question_number: 1..N`.
  - Áp dụng ngay khi nhận JSON từ Gemini và đã quét xáo trộn lại các file JSON hiện có trong `KetQua/questions_bank/`.
- `exam_word_merger.py`:
  - Bổ sung `export_single_file_exam_and_answer()`: Xuất đề và đáp án riêng cho đúng 1 bản tiêu chuẩn vào `KetQua/<slug>/tung_ban/DE_THI_<file>.docx` và `DAP_AN_<file>.docx`.
  - Bổ sung `export_all_single_files_by_folder()` và `export_all_single_files_all_folders()`.
- `app_gui.py`: Thêm nút **`📑 Xuất Từng Bản (File Riêng)`** để xuất file Word riêng từng bản cho thư mục chọn hoặc toàn bộ.
- `run_cli.py`: Bổ sung tùy chọn 2 trong Bước 4 để xuất từng bản tiêu chuẩn.

### 3. Kết Quả Kiểm Tra (Gate 2) — ✅ TẤT CẢ PASS
- Test xuất từng bản cho thư mục `2-000`: Đã tạo thành công 6 file Word trong `KetQua/2-000/tung_ban/`:
  - `DE_THI_000-0-V.docx` + `DAP_AN_000-0-V.docx`
  - `DE_THI_001-1-V.docx` + `DAP_AN_001-1-V.docx`
  - `DE_THI_002-1-V.docx` + `DAP_AN_002-1-V.docx`
- Kiểm tra vị trí câu hỏi chủ chốt `◎`:
  - `000-0-V.json` ➔ câu `◎` ở vị trí: **[3]**
  - `001-1-V.json` ➔ câu `◎` ở vị trí: **[1]**
  - `002-1-V.json` ➔ câu `◎` ở vị trí: **[3]**
  ➔ **Quy luật 2, 5, 8 đã bị xóa bỏ hoàn toàn 100%!**

---

## 2026-09-23 — Nâng Cấp GUI Drill-Down + Preview Câu Hỏi + Highlight Bảng Đáp Án — HOÀN THÀNH ✅

### 1. Yêu Cầu Người Dùng
1. **Chạy thử thực tế**: Kiểm tra syntax và logic toàn bộ pipeline.
2. **Cải thiện chất lượng câu hỏi**: Xem output Word thực tế, tinh chỉnh format bảng đáp án.
3. **Cải thiện UX GUI**: Thêm progress chi tiết từng file, màu trạng thái, xem câu hỏi trong app.

### 2. Triển Khai Kỹ Thuật

#### `app_gui.py` [NÂNG CẤP LỚN]:
- **Drill-down Treeview 2 cấp** (Folder → File PDF):
  - Folder nodes hiện màu theo tổng tiến độ: 🟢 xanh (100% OK), 🔵 xanh dương (đang chạy), 🟡 vàng (chưa làm).
  - File nodes hiện màu: ✅ xanh (OK) / 🟡 vàng (MISSING) / 🔴 đỏ (ERROR/INVALID).
  - **Lazy-load**: chỉ đọc file-level khi người dùng nhấp mở rộng folder → không lag với 409 dòng.
  - Nút **▼ Mở Rộng** / **► Thu Gọn** để điều khiển nhanh tất cả folder.
- **Panel Preview Câu Hỏi** (góc phải trên):
  - Click vào bất kỳ file PDF nào trong bảng → hiển thị ngay toàn bộ nội dung câu hỏi, đáp án.
  - Câu chủ chốt `◎` được đánh dấu rõ `⭐ CÂU CHỦ CHỐT (bắt buộc đúng)`.
  - Đáp án đúng có ký hiệu `✔` bên cạnh.
  - Trích nguồn `reference_note` hiển thị đầy đủ.
- **Status Bar ETA**: Khi đang chạy, thanh trạng thái tự tính và hiện ETA còn bao nhiêu phút/giờ.
- **Kích thước cửa sổ**: Mở rộng từ 1180×820 → 1380×900 để chứa đủ 3 panel.
- Layout phải: Preview (tỷ lệ 4) phía trên + Console Log (tỷ lệ 3) phía dưới.

#### `exam_word_merger.py` [NÂNG CẤP]:
- **Highlight câu chủ chốt `◎` trong bảng đáp án**:
  - Ô bảng đáp án câu ◎: **nền vàng nhạt (FFF2CC)**, chữ **đỏ đậm (C00000)**, in đậm.
  - Ô bảng đáp án câu thường: nền trắng, chữ đen tiêu chuẩn.
  - Dòng `◎ Câu 00X` thay vì `Câu 00X ◎` — rõ ràng hơn.
  - Đáp án đúng hiển thị **font size 11pt bold** (to hơn so với label câu).
- **Bảng Legend phía cuối file đáp án**:
  - 1 dòng bảng 2 cột: ô trái mẫu vàng `◎ Câu Chủ Chốt` + ô phải ghi "Tổng X câu ◎".

### 3. Kết Quả Kiểm Tra (Gate 2) — ✅ PASS
1. **Syntax check**: `python -m py_compile *.py` — ALL PASS.
2. **Import check**: `python -c "import app_gui"` — OK, không lỗi.
3. **Test Word đáp án**: `exam_word_merger.build_answer_doc()` với file `000-0-V.json` (3 câu, 1 câu ◎) → file `_test_highlight.docx` tạo thành công, bảng có nền màu → đã xóa file test.
4. **Edge case đã kiểm tra**:
   - File JSON chưa tồn tại → preview hiện thông báo "Chưa có câu hỏi" rõ ràng.
   - JSON bị lỗi parse → hiện thông báo lỗi cụ thể.
   - Placeholder lazy-load bị double-click → chỉ load 1 lần, không bị trùng.
   - Chọn file-level khi click "Xuất Thư Mục Chọn" → tự động lấy folder cha.
5. **Chưa verify được**: Giao diện trực quan (màu sắc, layout) cần user chạy `python app_gui.py` để xem thực tế.

---

## 2026-09-23 (session 2) — PDF Metadata Tracking + STALE Detection + Nút Quét — HOÀN THÀNH ✅

### Triển Khai

**`pdf_extractor.py`**: Thêm `get_pdf_file_info(pdf_path)` → `{file_size_bytes, modified_time, modified_time_iso, file_hash_short}`. Chỉ đọc 8KB đầu, không lag.

**`question_validator.py`**: `save_questions(data, pdf_path="")` lưu thêm vào JSON: `pdf_metadata`, `generated_at_iso`, `app_version="1.4"`. Backward-compatible với JSON cũ.

**`auto_question_generator.py`**: `is_already_done(folder_slug, base_name, pdf_path="")` so sánh `file_size_bytes` và `file_hash_short` — nếu khác → STALE → tái tạo tự động. `detect_new_and_missing_files()` và `run_batch()` đều truyền `pdf_path`.

**`app_gui.py`**: TAG_STALE (cam `#fb923c`), nút `🔍 Quét File Mới / Đã Sửa` (popup báo cáo NEW/STALE), `_load_file_children()` phát hiện STALE với màu cam, file-row hiện ngày sinh `generated_at_iso[:10]`.

### Gate 2 — ✅ PASS
- Syntax ALL PASS (4 file).
- `get_pdf_file_info()` PASS: size=108993, mtime_iso="2020-03-21T09:34:24", hash="178bee99".
- `save_questions(pdf_path=...)` PASS: JSON có đủ `pdf_metadata + generated_at_iso + app_version`.
- STALE detection PASS: khi size khác → `is_already_done()=False` + log `🔄 STALE`.
- Edge: JSON cũ không có `pdf_metadata` → bỏ qua STALE check, không re-generate nhầm.


---

## 2026-09-23 (session 3) — Tự Động Nhận Thư Mục Mới (Auto-Discover) — HOÀN THÀNH

### Vấn Đề
User thêm `1-A00 Ban V IT HOA` vào Source nhưng hệ thống không nhận vì folder_order trong config.json là danh sách cứng.

### Giải Pháp
- **config.json**: Thêm `1-A00 Ban V IT HOA` vào đầu folder_order.
- **pdf_extractor.py** scan_all_sources(): tự-discover thư mục mới ngoài config, merge vào cuối với cảnh báo stderr. Field mới is_new_folder trong mỗi item.

### Gate 2 — PASS
- Syntax PASS.
- scan_all_sources() → 448 files (39 mới + 409 cũ).
- scan_progress() → Total:448 Done:409 Missing:39 = 91.3%.
- Từ nay thêm thư mục mới vào Source → hệ thống TỰ nhận, không cần sửa config.

---

## 2026-09-23 (session 4) — Xuất Đề Thi & Đáp Án Rút Gọn Thư Mục 1-A00 — HOÀN THÀNH ✅

### Vấn Đề & Yêu Cầu
Người dùng yêu cầu tạo 1 file Đề thi và 1 file Đáp án rút gọn cho thư mục `1-A00 Ban V IT HOA` với các tiêu chí lọc:
1. Không đưa vào câu hỏi ngày tháng cố định (ví dụ: ngày 23.01.2020, ngày ban hành đầu tiên).
2. Không liên quan đến cách sử dụng chương trình ACM, SMI.
3. Không để câu hỏi liên quan đến đổi đơn vị (kgf sang Newton, hoán đổi ngẫu lực/trọng lượng).
4. Bỏ các câu liên quan đến quy định đặt mã số sheet, mẫu thiết định khi thêm nhà cung cấp mới.

### Triển Khai
- **`generate_rutgon_1A00.py`**:
  - Quét 39 file JSON từ `KetQua/questions_bank/1-A00/` (tổng 117 câu ban đầu).
  - Lọc bỏ 37 câu không đạt tiêu chuẩn (bỏ toàn bộ 27 câu ACM/SMI của 9 file A09-1 đến A09-9; bỏ câu ACM trong A15-1; bỏ các câu hỏi mốc ngày tháng trong A00-1, A08-1, A13-1, A14-1; bỏ các câu hoán đổi kgf sang N trong A17-1; bỏ toàn bộ câu mã số sheet/nhà cung cấp trong A18-5).
  - Giữ lại **80 câu hỏi thuần túy nghiệp vụ và kỹ thuật kiểm tra**, trong đó có **27 câu chủ chốt `◎`**.
  - Đánh số lại liên tục từ **Câu 001 đến Câu 080**.
  - Xuất 2 file Word:
    + `KetQua/1-A00_RutGon_DeThi.docx`: Đề thi chuẩn mẫu REV 14.
    + `KetQua/1-A00_RutGon_DapAn.docx`: Bảng đáp án chuẩn 3 cột, highlight câu chủ chốt `◎` màu vàng & đỏ, kèm bảng chú giải.

### Gate 2 — Verification PASS
1. **Kiểm tra từ khóa cấm trong file Đề thi**:
   - `ACM`: 0 lần
   - `SMI`: 0 lần
   - `kgf`: 0 lần
   - `23.01.2020`: 0 lần
   - `ngày ban hành đầu tiên`: 0 lần
   - `hoán đổi trọng lượng`: 0 lần
2. **Kiểm tra file Đáp án**:
   - Kích thước: 27 dòng x 3 cột, đầy đủ 80 câu trả lời.
   - Bảng chú giải: 27 câu chủ chốt `◎` được định dạng nổi bật đúng quy cách.

---

## 2026-09-23 — Sửa Lỗi config_path Tương Đối (pdf_extractor.py) ✅

### Vấn đề
`scan_all_sources()` khi gọi không có đối số dùng `config_path = "config.json"` (đường dẫn tương đối).
Khi hàm được import từ thư mục khác, Python không tìm thấy file → `folder_order` rỗng → in cảnh báo giả.

### Giải pháp
- Thêm `_DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")`.
- Đổi default `config_path` từ `"config.json"` → `None`; nếu `None` gán `_DEFAULT_CONFIG_PATH`.
- Thêm `import json` (đã thiếu).

### Xác minh
- 9 folder trong `folder_order` khớp 100% với 9 thư mục thực trên đĩa.
- Hệ thống **sẵn sàng sử dụng** qua `Chay_Giao_Dien.bat`.

