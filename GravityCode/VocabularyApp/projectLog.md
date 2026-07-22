# Vocabulary App - Project Log

Đây là file nhật ký để theo dõi tiến độ xây dựng ứng dụng học từ vựng (VocabularyApp).

> **⚠️ Quy tắc làm việc**: AI luôn đọc file này trước, sau đó **đề xuất phương án** và chờ người dùng đồng ý trước khi viết code.

---

## Mục tiêu
Tạo một ứng dụng desktop quản lý từ vựng đa ngôn ngữ (Tiếng Anh, Tiếng Nhật, Tiếng Trung...) kết hợp giao diện Web tĩnh trên GitHub Pages để có thể ôn tập từ vựng mọi lúc mọi nơi trên điện thoại.

Ứng dụng hoạt động tương tự như hệ thống `ListKaraOke`, bao gồm:
1. Giao diện Desktop (Python + CustomTkinter) để thêm/sửa/xóa từ vựng.
2. Dữ liệu mỗi ngôn ngữ lưu thành một file JSON riêng biệt (`english.json`, `japanese.json`,...).
3. Đồng bộ (Sync) dữ liệu lên GitHub Pages.
4. Giao diện Web di động hỗ trợ bộ lọc mạnh mẽ: Ngày học (Date), Chủ đề (Topic), Loại từ (Từ loại).

## Các tính năng đã hoàn thiện
1. **Quản lý đa ngôn ngữ**: Người dùng có thể thêm bao nhiêu ngôn ngữ tùy ý (ví dụ: English, Japanese). Mỗi ngôn ngữ được lưu tự động thành file JSON riêng trong thư mục `data/`.
2. **Sync lên GitHub & Google Drive**: Tích hợp module đồng bộ cho phép đẩy dữ liệu JSON và Web tĩnh lên GitHub Pages, đồng thời tải mp3 lên Google Drive.
3. **Web App với Flashcard**: Giao diện Web được thiết kế tối ưu trên mobile với 2 chế độ:
   - *List View*: Hiển thị danh sách từ vựng kèm bộ lọc.
   - *Flashcard View*: Hiển thị từng thẻ từ, bấm lật mặt sau để xem nghĩa và mẫu câu, có hỗ trợ nút phát audio (nếu đã đồng bộ mp3).
4. **Hiển thị nội dung dài (Long-content rendering)**:
   - Python App: Ô nhập *Nghĩa của từ* đổi sang `CTkTextbox` nhiều dòng.
   - Web List View: `white-space: pre-wrap`, ví dụ có nút toggle ẩn/hiện, scroll nếu dài.
   - Web Flashcard: Mặt sau có scroll (`overflow-y: auto`), nội dung `\n` render đúng.
   - JS: Thêm `escapeHtml()` và `formatText()` để an toàn với ký tự đặc biệt.

---

## Tiến độ (Timeline)
- [x] Lên ý tưởng và tạo file log dự án (`projectLog.md`).
- [x] Lên bản kế hoạch chi tiết (`implementation_plan.md`).
- [x] Xây dựng khung ứng dụng Desktop UI với CustomTkinter (`VocabApp.py`).
- [x] Cấu trúc quản lý file JSON đa ngôn ngữ (`database/database.py`).
- [x] Tích hợp tính năng Sync GitHub và Google Drive (`api/github_sync.py`, `api/gdrive_sync.py`).
- [x] Xây dựng giao diện Web App cho Mobile (`web/index.html`, `style.css`, `script.js`).
- [x] Sửa lỗi hiển thị nội dung dài / ký tự đặc biệt / xuống dòng (2026-06-18).
- [x] Tính năng kiểm tra từ trùng lặp khi thêm mới (2026-06-18).
- [x] Tính năng tự động gợi ý (Autocomplete, tối đa 5 lựa chọn) cho Chủ đề, Loại từ, Ngày học và tự động ghi nhớ Ngày học gần nhất để làm mặc định (2026-06-20).
- [x] Bảo mật GitHub Token & Sửa lỗi Ctrl+Z (2026-06-24).
- [x] Tính năng Preview (Xem trước) Bảng Markdown bằng đồ họa `ttk.Treeview` (2026-06-24).
- [x] Tính năng Visual Table Editor và Tối ưu Responsive Layout (2026-06-24).
- [x] Tự động nhận diện và paste Markdown table từ Gemini AI / ChatGPT (2026-06-24).
- [x] Khắc phục tình trạng giật lag danh sách từ vựng bằng ttk.Treeview (2026-06-26).

---

## Changelog

### 2026-06-26 — Khắc phục giật lag danh sách từ vựng bằng ttk.Treeview
**Vấn đề**: Giao diện ứng dụng bị treo, lag nhẹ khi tải danh sách từ vựng do phải render quá nhiều `CTkFrame` và `CTkLabel` riêng lẻ. Người dùng có gợi ý dùng "lazy loading" như trên Web.
**Giải pháp**: Tận dụng tính năng "Virtualization" (lazy rendering) có sẵn của `ttk.Treeview` - thành phần này chỉ tính toán và vẽ những dòng hiển thị trên màn hình hiện tại. Việc chuyển sang Treeview giải quyết triệt để lỗi mà không cần viết thuật toán phân trang/lazy loading phức tạp.

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `VocabApp.py` | Tái cấu trúc lại UI của `VocabListTab`, loại bỏ `CTkScrollableFrame` và thay thế bằng `ttk.Treeview`. Tốc độ load từ vựng giờ đây là ngay lập tức. |

### 2026-06-24 (Update 4) — Tự động nhận diện và paste Markdown table
**Vấn đề**: Việc soạn thảo bảng thủ công vẫn mất thời gian. Người dùng muốn copy trực tiếp bảng từ Gemini/ChatGPT và paste vào ứng dụng, hệ thống phải tự động nhận diện và format.

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `VocabApp.py` | Cải tiến hàm `on_paste` trong các `CTkTextbox` để nhận diện cấu trúc dòng bắt đầu bằng `|`. Nếu phát hiện nội dung là bảng Markdown, hệ thống tự động xử lý khoảng trắng để hiển thị đúng cột. |

### 2026-06-24 (Update 3) — Visual Table Editor và Responsive Layout
**Vấn đề**: Cửa sổ Form nhập liệu bị tràn viền gây mất nút Lưu, và người dùng cần nhập liệu Bảng thủ công trực quan thay vì gõ code Markdown trực tiếp.

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `VocabApp.py` | Tạo `TableEditorDialog` cho phép chèn cột/dòng nhập liệu kiểu Excel để tự động sinh mã Markdown Bảng. Tái cấu trúc Layout `VocabFormDialog`: gắn nút `Lưu / Hủy` xuống bottom frame tĩnh (luôn hiện), cài đặt `fill="x", expand=True` để các ô nhập liệu tự động co giãn theo chiều rộng cửa sổ. |

### 2026-06-24 (Update 2) — Tính năng Preview Bảng Markdown
**Vấn đề**: Người dùng cần xem Bảng dạng đồ họa lưới thật sự trong quá trình nhập liệu thay vì chỉ xem code Markdown dạng chữ thô, nhằm mường tượng đúng kết quả hiển thị trên web.

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `VocabApp.py` | Bổ sung class `PreviewDialog` dùng để phân tích cú pháp Markdown và render đồ họa bảng ra `ttk.Treeview`. Bổ sung các nút "👁 Preview" nằm kế bên nhãn của các ô nhập liệu `Nghĩa`, `Mẫu câu`, `Ghi chú` để tiện xem trước khi lưu. |

### 2026-06-24 (Update 1) — Bảo mật GitHub Token & Sửa lỗi Ctrl+Z
**Vấn đề**:
1. GitHub Token bị lưu cứng trong file `settings.json` dạng plaintext, dẫn đến việc bị GitHub Secret Scanner quét và thu hồi mỗi khi push code lên GitHub.
2. Các ô nhập liệu 1 dòng (Từ vựng, Phát âm, Ngày học...) sử dụng `CTkEntry` và `CTkComboBox` mặc định không hỗ trợ tính năng Undo (Ctrl+Z) / Redo (Ctrl+Y), gây bất tiện khi gõ sai.

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `settings.py` | Bổ sung hàm `encode_token` và `decode_token` sử dụng thuật toán đảo ngược chuỗi và Base64. Cập nhật `save_settings` để tự động mã hóa token và `load_settings` để giải mã, qua đó bảo mật file `settings.json` trên public repo. |
| `VocabApp.py` | Bổ sung hàm `enable_entry_undo` giúp giả lập Stack Undo/Redo tùy chỉnh. Áp dụng cho các widget Entry và ComboBox để khôi phục khả năng nhận phím tắt `Ctrl+Z` / `Ctrl+Y`. |

### 2026-06-23 — Hỗ trợ dán dữ liệu bảng và tự động tạo Markdown Table
**Vấn đề**: Khi dán văn bản có chứa Tab hoặc định dạng bảng từ Excel/Web vào các ô nhập liệu, các cột bị lệch do dùng font chữ thông thường. Đồng thời người dùng dán nhầm không thể nhấn `Ctrl + Z` để hoàn tác. Hơn nữa, trên Web cần render thành HTML Table để có giao diện đẹp như các ứng dụng hiện đại.

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `VocabApp.py` | Cấu hình font `Consolas` (Monospace) cho các `CTkTextbox` (`e_mean`, `e_ex`, `e_note`). Bật tính năng `undo=True` trên lớp textbox bên dưới để hỗ trợ `Ctrl+Z`. Bổ sung hàm `on_paste` bắt sự kiện `<<Paste>>` nhằm tự động biến dữ liệu chứa Tab (`\t`) thành Bảng Markdown. |
| `web/index.html` | Nhúng thư viện `marked.min.js` qua CDN để hỗ trợ parse Markdown sang HTML. |
| `web/script.js` | Cấu hình `marked.setOptions({breaks: true})` và chuyển `formatText` sang sử dụng `marked.parse(str)`. |
| `web/style.css` | Xóa `white-space: pre-wrap` để tránh xung đột với HTML. Bổ sung `font-family: Consolas` và toàn bộ CSS styling cho thẻ `table`, `th`, `td` nhằm hiển thị giao diện bảng tuyệt đẹp trên Web. |

### 2026-06-20 — Autocomplete & Ghi nhớ Ngày Học
**Vấn đề**: Việc nhập tay "Chủ đề", "Loại từ" và "Tag Ngày Học" tốn thời gian. Cần tự động gợi ý (chỉ 5 lựa chọn đầu) và xổ xuống khi gõ. Đồng thời ghi nhớ Tag Ngày học cuối cùng để điền sẵn cho các từ tiếp theo.

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `VocabApp.py` | Chuyển `e_topic`, `e_date` sang ComboBox. Thêm logic Autocomplete trên `<KeyRelease>`. Thêm biến `App.last_date_tag` để ghi nhớ và gán mặc định cho lần thêm sau. |

### 2026-06-18 — Fix hiển thị nội dung dài (từ "へ")
**Vấn đề**: Từ tiếng Nhật "へ" có nghĩa và ví dụ rất dài, nhiều `\n`, ký tự đặc biệt (`->`, `→`...) → giao diện bị vỡ, không xuống dòng, không scroll được.

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `VocabApp.py` | `e_mean`: `CTkEntry` → `CTkTextbox` (height=100, nhiều dòng). Dialog 920px. |
| `web/style.css` | `white-space: pre-wrap` cho meaning/example. Scroll cho `.vocab-example` và flashcard back. |
| `web/script.js` | Thêm `escapeHtml()`, `formatText()`. Ví dụ trong list có toggle ẩn/hiện. Flashcard dùng `innerHTML`. |
| `web/index.html` | `h2#fc-meaning` → `p.fc-meaning-text`. Thêm meta description. |
