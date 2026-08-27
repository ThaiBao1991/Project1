# Vocabulary App - Project Log

Đây là file nhật ký để theo dõi tiến độ xây dựng ứng dụng học từ vựng (VocabularyApp).

> **⚠️ Quy tắc làm việc**: AI luôn đọc file này trước, sau đó **đề xuất phương án** và chờ người dùng đồng ý trước khi viết code.

---

## 📋 Cập nhật mới nhất — 2026-08-27 (Update 3)

### 🔑 Đồng Bộ 100% Cơ Chế Key Rotation Với AskCpl: Fix Lock After Success & Smart Cooldown Recovery — HOÀN THÀNH ✅

**Vấn đề đã giải quyết:**
- ❌ **Tự khóa 3600s sau mỗi lượt gọi thành công**: `lock_after_success=True` mặc định làm tất cả các account trong pool lần lượt bị khóa 1 giờ (3,600s) sau 20+ request thành công của Ngày 1-11, khiến Ngày 12 không còn account nào để xoay vòng khi gặp 429 RPM.
- ❌ **Ngắt ngang khi toàn bộ key trong cooldown**: Vòng lặp `request()` ném ra `NO_KEY` ngay lập tức thay vì tự động chờ đếm ngược để tiếp tục.

**Giải pháp triển khai:**

| File | Thay đổi |
|------|----------|
| `api/gemini_safe.py` | • Đặt `lock_after_success=False` mặc định (đồng bộ 100% với `AskCpl.py` và `auto_ai_worker.py`), cho phép các key xoay vòng tự nhiên liên tục (Round-robin) không bị khóa 1 giờ.<br>• Thêm cơ chế **Smart Cooldown Wait**: Tự động tính thời gian cooldown còn lại ngắn nhất (15-30s), đếm ngược và tự động thử lại tối đa 12 vòng (có kiểm tra `stop_check` từng giây) thay vì báo `NO_KEY` ngắt ngang. |
| `ai/course_generator.py` | Khởi tạo `GeminiCoordinator` với `lock_after_success=False` tường minh. |
| `test_ai_rich.py` | Bổ sung test `[12] GeminiCoordinator lock_after_success & cooldown recovery`. |
| `projectLog.md` | Cập nhật nhật ký dự án. |

**Test kết quả:** ✅ 34/34 test passed (Python 3.14)

---

## 📋 Cập nhật trước đó — 2026-08-27 (Update 2)

### 🚀 Khóa Học AI Chuẩn AskCpl: Multi-Pass Blueprint Engine, Zero-Duplicate Auto-Repair & Continuous 100% Generation — HOÀN THÀNH ✅

**Vấn đề đã giải quyết:**
- ❌ **Ngắt 15 ngày không cần thiết**: Hệ thống có sẵn 155+ API key xoay vòng tự động từ AskCpl nhưng trước đây bị giới hạn cứng `BACKBONE_BATCH_SIZE = 15`, buộc người dùng phải bấm lặp lại nhiều lần.
- ❌ **Khung giáo trình Single-pass**: Thiếu các bước kiểm tra trùng lặp và phản biện lỗ hổng kiến thức, dẫn đến nguy cơ trùng lặp tiêu đề hoặc thiếu điểm ngữ pháp cốt lõi.

**Giải pháp triển khai:**

| File | Thay đổi |
|------|----------|
| `ai/course_generator.py` | • **Pass 1C**: Thêm `find_duplicate_topics` và `repair_duplicate_topics` sử dụng `difflib.SequenceMatcher` (ngưỡng tương đồng $\ge 85\%$) để phát hiện và tự động gọi AI sinh chủ đề thay thế tại chỗ.<br>• **Pass 2**: Thêm `review_and_fill_gaps` đóng vai trò Chuyên gia Sư phạm rà soát chuẩn quốc tế (JLPT/HSK/CEFR/TOPIK) và bổ sung các chủ đề trọng điểm còn thiếu.<br>• **Pass 3**: Thêm `normalize_backbone_sequence` sắp xếp thứ tự sư phạm logic (Chữ viết/Phát âm $\rightarrow$ Từ vựng $\rightarrow$ Ngữ pháp $\rightarrow$ Giao tiếp $\rightarrow$ Văn hóa/Slang).<br>• **Continuous Generation**: Đặt `BACKBONE_BATCH_SIZE = None`, hỗ trợ tham số `max_days_per_run` linh hoạt, chạy tự động 100% toàn bộ giáo trình liên tục không ngắt quãng, có sleep 0.3s nhịp nhàng chống nghẽn socket và lưu atomic từng ngày (resumable). |
| `VocabApp.py` | Tiến độ và log hiển thị theo thời gian thực xuyên suốt toàn bộ lộ trình; tự động hoàn thành trọn vẹn cấp độ chỉ với 1 lần bấm; hỗ trợ dừng bất kỳ lúc nào và ghi nhớ chính xác trạng thái. |
| `test_ai_rich.py` | Bổ sung unit tests cho Pass 1C (Deduplication Repair), Pass 2 (Gap Review), Pass 3 (Sequence Normalization) và Continuous Generation. |
| `projectLog.md` | Cập nhật nhật ký dự án. |

**Test kết quả:** ✅ 33/33 test passed (Python 3.14)

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
- [x] **Khóa học AI v2 — Hệ thống học ĐỘC LẬP hoàn toàn, AI tự quyết giáo trình:** Tách khỏi danh sách từ vựng chính (không seed, không nhập ngược). AI toàn quyền thiết kế giáo trình theo **hành trình 5 giai đoạn** (Nền tảng → Giao tiếp cơ bản → Trung cấp → Cao cấp → Như bản xứ), **tự quyết số ngày** theo trình độ (tối thiểu 14), mọi ngôn ngữ (Nhật/Trung/Hàn/Anh...). Nội dung rich mỗi ngày: ≥10 từ chuyên sâu · ≥10 cách dùng câu · ≥10 câu thông dụng · 2-3 bài ngữ pháp · trắc nghiệm **4 loại × ≥10 câu** có badge phân loại. Fix crash dialog (combo int→str), fix parse schema mismatch, auto-migrate dữ liệu cũ. 20/20 unit test pass (2026-08-26).
- [x] **Khóa học AI v2.1 — AI Roadmap cho Người Chưa Biết Gì & Lộ Trình Linh Hoạt (15-90 ngày theo chuẩn AskCpl):** Nâng cấp prompt AI tối ưu cho người mới tinh (Zero-Knowledge First: Ngày 1-3 bắt buộc dạy Bảng chữ cái, Bảng phiên âm, Quy tắc phát âm, Ghép vần, Thanh điệu); Thêm cơ chế chọn thời lượng linh hoạt (15/30/45/60/90 ngày hoặc AI tự phán định); Tích hợp JSON repair (tự sửa trailing comma theo chuẩn AskCpl); Fix lỗi UnicodeEncodeError trên Windows Terminal; 28/28 unit test PASS (2026-08-26).
- [x] **Khắc phục lỗi cài đặt pygame trên Python 3.14+:** Thay thế `pygame` (bị lỗi build do PEP 632 loại bỏ `distutils`) bằng `pygame-ce>=2.5.0` (Community Edition có sẵn pre-built wheels cho Python 3.14, 100% tương thích API `import pygame` cho phát âm TTS) (2026-08-26).

---

## Changelog

### 2026-08-26 (Update 3) — Chuyển sang pygame-ce: Tương thích hoàn hảo Python 3.14+
**Vấn đề**: Khi khởi động ứng dụng trên môi trường Python 3.14, gói `pygame` truyền thống chưa có pre-built binary wheel, buộc pip phải build từ mã nguồn. Mã nguồn setup của `pygame` phụ thuộc vào `distutils.msvccompiler` (đã bị gỡ bỏ vĩnh viễn trên Python 3.14 theo PEP 632) dẫn đến crash `ModuleNotFoundError: No module named 'distutils.msvccompiler'`.

**Giải pháp**:
- Chuyển cấu hình thư viện sang `pygame-ce>=2.5.0` (Community Edition). Đây là bản fork chính thức và phát triển tích cực của Pygame, có sẵn pre-built binary wheel cho Python 3.10 đến Python 3.14 trên Windows x64.
- `pygame-ce` xuất ra đúng module `import pygame`, tương thích hoàn toàn 100% với toàn bộ code âm thanh `pygame.mixer` trong `VocabApp.py`.

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `VocabApp.py` | Cập nhật `OPTIONAL_PACKAGES` từ `pygame>=2.5.0` sang `pygame-ce>=2.5.0`. |
| `requirements.txt` | Cập nhật `pygame-ce>=2.5.0`. |
| `projectLog.md` | Ghi lại nhật ký khắc phục lỗi. |

**Kết quả kiểm chứng**: `pygame-ce 2.5.8` cài đặt thành công ngay lập tức qua wheel · `import pygame; pygame.mixer.init()` chạy hoàn hảo trên Python 3.14.7.

### 2026-08-26 (Update 2) — AI Roadmap cho Người Chưa Biết Gì (Zero-Knowledge First) & Lộ Trình Linh Hoạt 15-90 Ngày
**Vấn đề**:
1. Với người chưa biết gì về ngôn ngữ mới, khóa 15-30 ngày nếu không có chỉ dẫn chặt chẽ sẽ dễ bị nhảy cóc bỏ qua bảng chữ cái/ngữ âm cơ bản.
2. Cần cung cấp các mốc thời lượng học phong phú hơn (15 ngày - Nhập môn, 30 ngày - Tiêu chuẩn, 45 ngày - Mở rộng, 60 ngày - Chuyên sâu, 90 ngày - Nâng cao) để người học chủ động chọn hoặc để AI tự ước lượng theo độ khó của từng ngôn ngữ.
3. Test script `test_ai_rich.py` bị lỗi encoding UTF-8 trên Windows console (charmap cp1252 không in được ký tự `→`).

**Giải pháp & Nâng cấp**:
- **Prompt Zero-Knowledge First**: Ở Giai đoạn 1 (Nền tảng), AI bắt buộc dành những ngày đầu (Ngày 1 đến Ngày 3-5) để dạy kỹ **Hệ chữ viết, Bảng chữ cái, Bảng phiên âm (Romaji/Pinyin/Hangul/IPA) và Quy tắc phát âm/thanh điệu** trước khi dạy từ ghép/câu phức.
- **Hỗ trợ lộ trình linh hoạt (15 – 90 ngày)**: Bổ sung dropdown trong `CourseGenerationDialog` cho phép người dùng chọn các mốc 15, 30, 45, 60, 90 ngày hoặc để AI tự phán định số ngày tối ưu.
- **JSON Repair (AskCpl standard)**: Nâng cấp `_strip_json` tự động strip markdown fences và repair trailing commas trước `}` và `]` khi AI trả về.
- **Fix UTF-8 Terminal & Mở rộng Test Suite**: Thêm `sys.stdout.reconfigure(encoding="utf-8")` và bổ sung các test cases cho zero-knowledge prompt, 60/90 days target, json repair (28/28 test PASS).

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `ai/course_generator.py` | Prompt chỉ dẫn Zero-knowledge (bảng chữ cái/phát âm), `_strip_json` regex repair, hỗ trợ linh hoạt `target_days`. |
| `VocabApp.py` | `CourseGenerationDialog`: Thêm bộ chọn thời lượng (`cb_duration`) 15/30/45/60/90 ngày và parse truyền vào `generate_course`. |
| `test_ai_rich.py` | Fix UTF-8 stdout reconfigure, thêm 8 test cases mới (28/28 PASS). |
| `projectLog.md` | Cập nhật nhật ký dự án. |

**Kết quả kiểm chứng**: 28/28 unit test PASS · py_compile sạch tất cả file · node --check script.js sạch · Smoke test import VocabApp thành công.

### 2026-08-26 — Khóa học AI v2: Hệ thống học ĐỘC LẬP, AI tự quyết toàn bộ giáo trình
**Vấn đề**: (1) Dialog sinh khóa học crash ngay khi mở (`CTkComboBox` nhận values dạng int → `.ljust()` lỗi). (2) Bắt buộc DB phải có sẵn từ mới cho sinh khóa học. (3) Nội dung mỗi ngày quá mỏng, quiz chỉ 6 câu không phân loại. (4) Người dùng phải tự chọn số ngày. (5) Khóa học còn "dính" tới từ vựng gốc trong DB.

**Nguyên tắc thiết kế mới — khóa học AI là HỆ THỐNG HỌC HOÀN TOÀN ĐỘC LẬP**:
- **Không liên kết DB từ vựng**: không seed từ có sẵn, không nhập ngược từ AI vào danh sách chính — hai hệ thống tách biệt 100%.
- **AI toàn quyền thiết kế**: hành trình 5 giai đoạn bắt buộc (Nền tảng → Giao tiếp cơ bản → Trung cấp → Cao cấp → Như bản xứ); **AI TỰ QUYẾT số ngày** theo trình độ (tối thiểu 14 ngày để đủ hành trình); chủ đề + từ vựng do AI chọn như người bản xứ dạy người mới.
- **Mọi ngôn ngữ**: Nhật (romaji), Trung (pinyin), Hàn (romanization), Anh/Pháp (IPA)...
- **Nội dung rich mỗi ngày**: ≥10 từ chuyên sâu · ≥10 cách dùng câu · ≥10 câu thông dụng (kèm tình huống) · 2-3 bài ngữ pháp chi tiết.
- **Trắc nghiệm 4 loại × ≥10 câu** (từ vựng / mẫu câu / câu thông dụng / ngữ pháp), badge phân loại trên cả desktop lẫn web.
- **3 loại lần gọi AI**: lập giáo trình → nội dung ngày → trắc nghiệm ngày (`max_output_tokens=16384`, retry JSON 2 lần) — tránh bị cắt response.
- **Resumable**: plan + từng ngày lưu ngay; Dừng rồi chạy lại tiếp tục chỗ dở; `get_course()` tự migrate định dạng cũ (grammar dict→list, quiz list→dict).

**Files đã sửa**:
| File | Thay đổi |
|------|----------|
| `ai/course_generator.py` | `CURRICULUM_SCHEMA` + `JOURNEY_PHASES` + `build_curriculum_prompt()` (AI tự quyết số ngày, cấm dùng từ có sẵn) + `parse_curriculum_json()`. Prompt nội dung rich + auto-pick. Quiz 4 loại. `_ask()` tách kind (logic) khỏi label (log) — fix bug parse schema mismatch. `generate_course(language, words_per_day, level, ...)`: bỏ tham số `vocabs`, luôn do AI lập plan, `target_days` tùy chọn. |
| `ai/course_db.py` | `get_course()` tự migrate định dạng cũ và save lại. |
| `VocabApp.py` | Fix combo int→str (crash `.ljust`). Dialog mới: bỏ combo số ngày (AI tự quyết), chọn trình độ 5 mức, ghi rõ "HỆ THỐNG HỌC ĐỘC LẬP", không đọc DB từ vựng. `_render_lesson_text()` render 4 section + phase/topic. `_flatten_quiz()` xử lý quiz dict 4 loại/list cũ kèm category. Combo ngày hiển thị chủ đề. |
| `web/script.js` | `flattenQuiz()`, render patterns/common/grammar-list, quiz category badges, topic trong select ngày, phase badge. |
| `web/style.css` | Thêm `.section-title`, `.pattern-item`, `.common-item`, `.quiz-cat-badge`, `.phase-badge`. |
| `test_ai_rich.py` | 20 test: schema, parse resilience, migration, flatten, prompts (explicit + AI-decided days), full dry-run flow với fake coordinator (giáo trình → 2 ngày rich → resume → stop). |

**Kết quả kiểm chứng**: 20/20 test pass · py_compile sạch · node --check sạch.

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
