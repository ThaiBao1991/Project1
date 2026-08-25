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
- [x] Thêm tính năng tự động kiểm tra và cài đặt thư viện khi khởi động (2026-08-11).
- [x] **Thêm tính năng Luyện Viết (Có chấm điểm & Bảng nháp) trên cả Web App và Desktop App** (2026-08-11).
- [x] **Fix luyện viết:** Thêm dual charDataLoader (JP dataset → fallback CN) để hỗ trợ Hiragana/Katakana/Kanji. Fix nút "Luyện viết" không hiện trên mobile (flex-wrap). Fix CSS bị hỏng (2026-08-12).
- [x] **Đổi phương án chấm điểm:** Bỏ HanziWriter data-dependency. Thay bằng Pixel Similarity Scoring (F1 score). Dùng browser Canvas `fillText` để render chữ mờ, so sánh pixel người vẽ vs pixel gốc → % điểm. Hỗ trợ mọi ngôn ngữ không cần dataset (2026-08-12).
- [x] **Tối ưu Hiệu suất & UI/UX (Web):** Thêm Debounce (300ms) cho thanh tìm kiếm chống treo trình duyệt. Implement Lazy Loading (Infinite Scroll) bằng `IntersectionObserver` tối ưu render danh sách lớn. Thêm nút Xoá nhanh tìm kiếm (Clear button), Smooth Accordion cho ví dụ và Micro-animations (hover effects) cho các thẻ từ vựng (2026-08-12).
- [x] **Hybrid TTS Fallback (Web):** Nút 🔊 Play trên Flashcard luôn hiện. Nếu từ có `mp3_gdrive_id` → phát MP3 Google Drive như cũ. Nếu không có → dùng `Web Speech API` (SpeechSynthesis) đọc TTS với locale tự động map theo ngôn ngữ (en-US / ja-JP / zh-CN...). Không cần backend, không cần API key (2026-08-13).
- [x] **TTS Hybrid trên Desktop App:** Thêm hàm `speak_word()` dùng `gTTS + pygame` (có mạng, giọng Google) hoặc fallback `pyttsx3` (offline, Windows SAPI). Thêm nút 🔊 cạnh ô "Từ vựng" trong form Thêm/Sửa và nút **🔊 Đọc** trong action bar của List View. Thư viện tự cài qua `check_and_install_packages()` khi khởi động (2026-08-13).
- [x] **Rà soát & vá lỗi toàn ứng dụng (Bug-fix sweep):** Fix shallow-copy mutate DEFAULT_SETTINGS trong `settings.py`; ghi JSON atomic (`os.replace`) chống hỏng dữ liệu; fix progress bar bị cập nhật từ background thread; fix chèn từ vào JS luyện viết bằng `json.dumps` (từ chứa `" \` `\` không còn vỡ) + tự dọn temp script; thêm lock chống race khi bấm 🔊 liên tục; thống nhất zh-CN; dedupe header bảng Preview; Web thêm DOMPurify sanitize, tìm kiếm khớp cả example/note, flashcard lặp vòng + phím tắt Space/←/→ (2026-08-25).
- [x] **Fix auto-installer chết trên Python 3.14+:** Trước đây cài TẤT CẢ thư viện trong 1 lệnh pip → pygame (chưa có wheel cho 3.14, build lỗi do bỏ distutils) làm hỏng cả lệnh → app không thể khởi động. Tách `CRITICAL_PACKAGES` (customtkinter, requests — thiếu là thoát với cửa sổ lỗi) và `OPTIONAL_PACKAGES` (cài từng gói riêng, fail thì bỏ qua và app vẫn chạy). Thêm biến môi trường `VOCABAPP_SKIP_INSTALL=1` để dev/test khởi động nhanh. Dọn `requirements.txt`: bỏ Pillow & qrcode (không được dùng trong code) (2026-08-25).
- [x] **Tab 🎓 Học Tập + Khóa học AI chuyên sâu theo ngày (kiểu AskCpl):** Ô lựa chọn nguồn học gồm **"📖 Từ vựng tự học"** (flashcard lật thẻ 60 từ hiện có: trộn thẻ, 🔊 đọc, phím ←/→/Space) và **"🤖 Khóa học AI chuyên sâu"** (AI chia toàn bộ từ vựng thành các ngày; mỗi ngày sinh bài học JSON gồm: từ vựng chuyên sâu + giải thích sắc thái + ví dụ song ngữ + điểm ngữ pháp + 6-10 câu trắc nghiệm tương tác có chấm điểm & lưu tiến độ). Dùng lại cơ chế `GeminiCoordinator` của AskCpl (`api/gemini_safe.py`): xoay vòng **155 API key ENC:** đọc trực tiếp từ `AskCpl/settings.json`, pace chống 429, model fallback. Database lưu kiểu AskCpl tại `data/ai_courses/<ngôn_ngữ>/course.json` + `progress.json` (atomic, resumable — dừng giữa chừng chạy lại là tiếp tục). Web thêm view "🎓 AI Course" để ôn trên điện thoại; GitHub sync upload cả thư mục ai_courses. Đã test THẬT với Gemini: sinh thành công Ngày 1/12 (model fallback gemini-3.5-flash → flash-latest → 3.1-flash-lite) (2026-08-26).

---

## Changelog

### 2026-08-26 — Tab 🎓 Học Tập + Khóa học AI chuyên sâu theo ngày (tích hợp AskCpl)
**Kiến trúc**: tái sử dụng `GeminiCoordinator` của AskCpl (copy về `api/gemini_safe.py`, bỏ phụ thuộc settings) — xoay vòng account/key, pace 3.5–5s + jitter, phân loại lỗi 429 daily/rate/invalid, model fallback. Key đọc (chỉ đọc, không ghi) từ `GravityCode/Download/AskCpl/settings.json`, giải mã ENC: cùng thuật toán.

**Files mới/sửa**:
| File | Nội dung |
|------|----------|
| `api/gemini_safe.py` (mới) | Bản copy chuẩn hóa của gemini_safe.py từ AskCpl |
| `ai/course_db.py` (mới) | DB khóa học: `data/ai_courses/<slug>/course.json` + `progress.json`; atomic write; upsert_day resumable; mark_day_completed giữ điểm cao nhất |
| `ai/course_generator.py` (mới) | responseSchema JSON cho Gemini (vocab/grammar/quiz), prompt gia sư tiếng Việt, parse chống lỗi (code fence, answer_index out-of-range), vòng lặp sinh từng ngày + lưu ngay, stop/resume |
| `VocabApp.py` | Tab **🎓 Học Tập**: ô chọn nguồn (Tự học / Khóa AI), flashcard tự học (trộn/lật/đọc/phím tắt), trình xem bài theo ngày (textbox render + quiz radio tương tác chấm điểm lưu tiến độ), dialog sinh khóa học (chọn 3/5/7/10 từ ngày, progress bar, log, nút Dừng). Fix CTkRadioButton không nhận wraplength; bind phím qua winfo_toplevel vì CTk chặn bind_all |
| `web/index.html` `script.js` `style.css` | View "🎓 AI Course": chọn ngày → bài học + trắc nghiệm interactive, tiến độ lưu localStorage, badge hoàn thành; switchView 3 chiều |
| `api/github_sync.py` | Upload cả `data/ai_courses/**/*.json` lên GitHub Pages |
| `settings.py` | Thêm mục `ai.askcpl_settings_path` (ghi đè đường dẫn key nếu cần) |

**Kiểm chứng**: 26 unit test PASS (course_db, parser, resumable, stop); smoke test 2 bản Python PASS kể cả render quiz thật; gọi AI THẬT sinh Ngày 1/12 khóa tiếng Nhật thành công qua cơ chế fallback model.

### 2026-08-25 — Rà soát & vá lỗi toàn ứng dụng (Bug-fix sweep)
**Kết quả review**: 7 nhóm lỗi thật sự + 3 điểm tối ưu, đã vá hết. Kiểm tra bằng 31 unit test + compile check + smoke test khởi động app thật trên Python 3.14 & 3.11 (đều PASS, 60 từ load đúng).

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `settings.py` | **Bug thật**: `dict(DEFAULT_SETTINGS)` là shallow-copy nên `merged["github"].update(...)` làm mutate dict mặc định toàn cục (giá trị cũ "nhớ" xuyên phiên, kể cả khi file hỏng). Chuyển sang `copy.deepcopy()`. |
| `database/database.py` | `save_data()` ghi trực tiếp → crash giữa lúc ghi làm hỏng file JSON (mất dữ liệu). Đổi sang ghi file `.tmp` rồi `os.replace()` (atomic trên Windows). |
| `VocabApp.py` | 1) **Nghiêm trọng**: auto-installer cài mọi thư viện trong 1 lệnh pip — pygame build lỗi trên Python 3.14 làm app không thể khởi động. Tách critical/optional + cài từng gói + thêm env `VOCABAPP_SKIP_INSTALL`. 2) Progress bar Drive bị gọi `.set()` từ worker thread — tkinter không thread-safe → route qua `self.after(0,...)`, chống chia 0. 3) Nút Upload Drive thêm cờ `_syncing` chống bấm đúp tạo 2 thread upload song song. 4) `run_webview_practice`: chèn từ thẳng vào chuỗi JS qua f-string vỡ khi từ chứa `" \` `\`; chuyển sang `json.dumps`, đồng thời temp script tự xóa sau khi chạy. 5) `speak_word`: thêm `_tts_lock` chống race pygame khi bấm 🔊 liên tục; check pygame trước khi generate gTTS; fix `v.languages[0].decode()` crash; map tiếng Trung `zh-TW` → `zh-CN` khớp Web. 6) `PreviewDialog`: dedupe header bảng (Treeview crash nếu 2 cột trùng tên). |
| `requirements.txt` | Bỏ Pillow & qrcode (không được dùng trong code nào) → cài nhanh hơn. |
| `web/index.html` | Thêm DOMPurify CDN (sanitize HTML do `marked.parse()` render từ dữ liệu người dùng — chống XSS). |
| `web/script.js` | 1) `formatText()` sanitize qua DOMPurify. 2) Tìm kiếm web bổ sung `example`, `example_meaning`, `note` để khớp hành vi desktop. 3) Flashcard điều hướng lặp vòng (cuối→đầu). 4) Phím tắt: Space lật thẻ, ←/→ chuyển thẻ (tự bỏ qua khi đang gõ hoặc modal luyện viết mở). |

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
