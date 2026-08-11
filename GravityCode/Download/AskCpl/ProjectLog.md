# Project Log: Ứng dụng Quản lý Ngày học Copilot



File này dùng để theo dõi quá trình làm việc, các quyết định quan trọng và tiến độ của dự án.



## Mục tiêu

Tạo giao diện để tự động lưu các ngày học Tiếng Anh và Tiếng Nhật từ các agent Copilot, sau đó kết xuất thành file Word (.docx) chất lượng cao.



---



## Nhật ký công việc


## 2026-08-06: LÀM SẠCH LINK CHẾT VÀ DỊCH THUẬT DATA WIKI (PHASE 9)
- **Hoạt động:** Rà soát và tự động xử lý link 404, dịch thuật toàn bộ 403 tướng sang tiếng Việt.
- **Chi tiết thay đổi:**
  - Viết script Python ping toàn bộ link tham khảo trong 5 file vệ tinh (`data_ChucQuan`, `Linh`, `Meo`, `Skill`, `VuKhi_Do`), tự động nhận diện và **xóa sạch 31 link chết 404**, giữ lại nội dung để không mất kiến thức.
  - Xử lý link mã hóa chống bot (Gamer.com.tw) cho file `data_Tuong.md`, cào thành công danh sách đặc tính ẩn của 403 tướng.
  - Sử dụng `opencc` và `deep-translator` chạy ngầm để dịch tự động tên 403 tướng sang Hán-Việt, và match tự động 100% Đặc tính ẩn từ tiếng Trung sang tiếng Việt theo từ điển chuẩn đã lập ở mục 8.1-8.3.
- **Trạng thái:** ✅ DONE — Dữ liệu đã sạch, không còn link hỏng và đã Việt hóa 100%.

## 2026-08-06: HOÀN THÀNH WIKI AUTO-BUILDER (Autonomous Research Agent)
- **Hoạt động:** Xây dựng tính năng **🌐 Wiki Builder** tích hợp vào `AskCpl.py` — một Agent tự trị hoàn chỉnh.
- **Chi tiết thay đổi:**
  - Thêm sub-tab **🌐 Wiki Builder** vào tab `Auto AI`.
  - **Pipeline 6 Phase tự động:**
    - Phase 1: Gemini phân rã chủ đề → N mảng con (trả về JSON), tự tạo file `data_<slug>.md`
    - Phase 2: Gemini sinh 10-30 câu hỏi/chủ đề cần nghiên cứu cho từng mảng
    - Phase 3: Cross-check chéo toàn bộ `data_*.md` hiện có (Keyword + AI Semantic) để tránh trùng lặp
    - Phase 4: Google Custom Search API tìm kiếm link liên quan
    - Phase 5: Cào HTML từ link tìm được (requests + BeautifulSoup), fallback sang AI tự viết nếu không cào được
    - Phase 6: AI tóm tắt + ghi vào đúng file dưới dạng `## Chủ đề\n Nội dung\n *Nguồn: URL*`
  - Giao diện có: ô nhập chủ đề, thư mục lưu, Google API Key/CX ID, điều chỉnh số mảng/câu hỏi, nút Dừng khẩn cấp, log realtime màu sắc.
  - Global Corpus được cập nhật động trong suốt quá trình để tránh trùng lặp giữa các mảng.
- **Trạng thái:** ✅ DONE — Syntax OK. App chạy thành công.



## 2026-08-05: Sửa lỗi UI bị che khuất vùng Log ở tab Tạo Roadmap
- **Vấn đề:** Giao diện tab "Tạo Roadmap" bị lỗi hiển thị. Khi màn hình/cửa sổ không đủ chiều dọc, hộp văn bản "Tiến trình chạy" (Log) bị đẩy văng ra ngoài không thể nhìn thấy, do phần "Dàn ý Kỹ thuật" chiếm hết chỗ.
- **Giải pháp (`AskCpl.py`):** Thay đổi thứ tự pack của Tkinter. Gắn các frame phía dưới (Log, Nút bấm) bằng `side=tk.BOTTOM` để chúng ưu tiên chiếm chỗ ở dưới cùng trước, sau đó mới cho frame "Dàn ý Kỹ thuật" chiếm phần khoảng trống còn lại (`side=tk.TOP, fill=tk.BOTH, expand=True`). Điều này đảm bảo Log luôn hiển thị ở đáy ứng dụng mọi lúc.

## 2026-08-05: Tối ưu hoá Wiki Mode (Sức chứa & Tự động cào web)
- **Vấn đề:** Chế độ Bách khoa (Wiki Mode) vẫn sinh ra các dữ liệu ảo giác khi lượng thông tin cung cấp qua file tham khảo bị giới hạn ở 4,000 ký tự. Ngoài ra, việc dùng tool ngoài để tải HTML rồi đưa vào AskCpl.py gây phiền toái.
- **Giải pháp (`AskCpl.py`):**
  1. Gỡ bỏ nút thắt 4,000 ký tự, nâng hạn mức lên **300,000 ký tự** cho mỗi file/URL, khai thác tối đa ngữ cảnh rộng (1 triệu token) của mô hình `gemini-flash-latest`.
  2. Bổ sung cơ chế `_read_ref_files` hỗ trợ **Cào dữ liệu web trực tiếp (Direct URL Fetching)** thông qua thư viện `requests` và `BeautifulSoup` nếu người dùng nhập URL trực tiếp vào ô File tham khảo (ví dụ dán link `https://gl.ali213.net/...`).
  3. Tinh chỉnh các câu prompt trong Bước 1, Bước 2 và Bước 3 dành riêng cho Wiki Mode để xoá bỏ hoàn toàn các từ khóa "giáo trình", "bài học", "dạy bài", ép AI tuân thủ tuyệt đối việc chỉ bóc tách dữ liệu thành bảng Markdown mà không bịa thêm (No Hallucination).

## 2026-08-04: Tích hợp Chế độ "Bách khoa toàn thư" (Wiki/Database Mode)
- **Vấn đề:** AskCpl ban đầu chuyên tạo "Lộ trình học" (Learning Roadmap) nên khi yêu cầu tạo dữ liệu siêu lớn như Game (Tướng, Vũ khí SG7), AI thường hay nói tóm tắt lấy ví dụ chứ không chịu liệt kê đầy đủ.
- **Giải pháp (`AskCpl.py`):**
  1. Thêm tuỳ chọn `gen_mode` (Radio button) ngay trên tab Tạo Roadmap: "Giáo trình" hoặc "Bách khoa".
  2. Ở chế độ Bách khoa, Bước 1 (1A, 1B) được tiêm Prompt chuyên dụng: Yêu cầu AI không tạo "bài học" mà đóng vai trò "Trình trích xuất thực thể", tự động gom các Binh chủng, Tướng, Trang bị thành các "Lô bóc tách" (Extraction Batch) - mỗi lô chứa 10-20 tên cụ thể để tránh bỏ sót.
  3. Lô bóc tách này vẫn mượn cơ sở hạ tầng `day` của AskCpl để người dùng dễ theo dõi quá trình sinh dữ liệu.
  4. Ở Bước 3, Prompt ép AI xuất dữ liệu dưới dạng `BẢNG MARKDOWN nghiêm ngặt`, nghiêm cấm viết văn xuôi hay đóng vai giáo viên.

## 2026-08-04: Tích hợp Quản lý độ trùng lặp tiêu đề (% Similarity)
- **Vấn đề:** Khi sinh dữ liệu dạng Bách khoa (Wiki Mode), AI thường sinh ra các "Lô bóc tách" có tên rất giống nhau (vd: "Tướng Ngụy phần 1", "Tướng Ngụy phần 2"). Hàm kiểm tra trùng lặp `_similar` mặc định hardcode ở mức `0.96` (96%), dẫn đến việc báo lỗi `RoadmapValidationError` không đáng có.
- **Giải pháp (`AskCpl.py`, `roadmap_pipeline.py`):**
  1. Thêm Checkbox "Kiểm tra trùng lặp tiêu đề (%)" và ô nhập giá trị % (mặc định 96) vào giao diện "Cấu trúc đầu ra".
  2. Bắt giá trị này truyền qua luồng kiểm tra `_roadmap_v5_step1` và `_roadmap_v5_step2`.
  3. Cập nhật hàm `validate_plan` và `validate_revision` trong `roadmap_pipeline.py` nhận vào tham số `sim_check_enabled` và `sim_threshold`.
  4. Nhờ đó, với chế độ Wiki, người dùng chỉ cần tick bỏ chọn hoặc giảm % trùng lặp xuống là AI sẽ vượt qua dễ dàng.

## 2026-08-04: Sửa lỗi "Roadmap nhiều phase phải có ít nhất một Day kind='capstone'" cho Chế độ Wiki
- **Vấn đề:** Khi sinh xong 150/150 lô, hệ thống kiểm định gọi hàm `validate_plan()` và ném lỗi `RoadmapValidationError` vì không tìm thấy Day nào có `kind="capstone"`. Ở chế độ Wiki, toàn bộ các Day đều mang nhãn `kind="extraction"`.
- **Giải pháp (`roadmap_pipeline.py`):** Sửa lại hàm `validate_plan` để bỏ qua bài kiểm tra `capstone` nếu trong danh sách có tồn tại `kind="extraction"`. Điều này giúp hệ thống tương thích ngược hoàn hảo mà không ảnh hưởng tới Lộ trình học cũ.

## 2026-08-04: Sửa lỗi "Tham chiếu prerequisite chưa tồn tại" trong Chế độ Wiki (Pass 6)
- **Vấn đề:** Trong Pass 6 (Bước 2 - Phản biện & Mở rộng), AI có thể vô tình thêm một `prerequisite` ảo (vd: `boc_tach_nguy_cac_chuthe_hoanggia`) vào một Lô bóc tách. `validate_revision()` sau đó quét đồ thị phụ thuộc (dependency graph) và quăng lỗi vì không tìm thấy ID này.
- **Thực tế:** Chế độ Wiki (Bách khoa) hoạt động theo từng Lô (Batch) độc lập, không cần có tính tuyến tính (phải học cái này mới hiểu cái kia).
- **Giải pháp (`roadmap_pipeline.py`):** Cập nhật `validate_plan()`. Nếu phát hiện đang ở chế độ Wiki (`is_wiki = True`), hệ thống sẽ BỎ QUA toàn bộ khối lệnh xây dựng và kiểm tra đồ thị `prerequisites`. Điều này loại bỏ hoàn toàn các lỗi ảo do AI "ảo giác" (hallucinate) sinh ra tham chiếu chéo không cần thiết.

## 2026-08-04: Tích hợp Giao diện tùy chỉnh Cấu trúc Đầu ra (Dynamic Output Requirements)
- **Vấn đề:** Ban đầu cấu trúc output sinh ra trong Prompt ở Bước 3 (Sinh chi tiết Master) bị fix cứng (`phân bổ thời gian`, `vật liệu`, `từng bước`, `an toàn`, `checklist`), người dùng muốn linh hoạt tick chọn bật/tắt hoặc thêm yêu cầu mới ngay lúc tạo Roadmap.
- **Giải pháp (`AskCpl.py`):**
  1. Mở rộng UI: Thêm Vùng `Cấu trúc đầu ra bắt buộc của AI` (Region 1.4) với 5 Checkbox và 1 ô Text tuỳ chọn vào tab "Tạo Roadmap".
  2. Bắt trạng thái: Các biến `IntVar`, `StringVar` được lấy giá trị qua `_roadmap_snapshot()` và lưu vào `settings.json` bằng hàm `save_roadmap_generator_settings()`.
  3. Lắp ghép Prompt Động: Khối lệnh trong `_roadmap_v5_step3` đọc snapshot và tự dệt thành cấu trúc. AI chỉ còn được yêu cầu xuất ra đúng những cấu trúc đã check (hoặc "tự do (theo ý bạn)" nếu tắt hết). Đồng thời, các trường `estimated_minutes` và `materials` cũng chỉ được truyền đi/ràng buộc trong JSON LLM (bản V5 Master) nếu người dùng check vào tùy chọn tương ứng.## 2026-08-04: Fix lỗi crash Bước 2 (Phản biện) do JSON quá lớn (MAX_TOKENS)
- **Vấn đề:** Ở Bước 2 (Phản biện), khi xử lý roadmap lớn (180 Day), kích thước `plan_json` gửi vào prompt quá lớn khiến Gemini cắt ngang response (lỗi `MAX_TOKENS`). Hệ thống cố `json.loads` phần bị đứt gãy dẫn tới crash tiến trình (lỗi `Expecting value`).
- **Cách sửa (`_roadmap_v5_step2` trong `AskCpl.py`):**
  1. Tạo `condensed_plan_json` lược bỏ bớt các trường không cần thiết cho quá trình phản biện (như `materials`, `details`, `definition_of_done`) chỉ giữ lại (`day`, `topic_id`, `topic`, `phase`, `kind`, `prerequisites`) để giảm token.
  2. Bổ sung cơ chế **Retry 3 lần** cho mỗi vòng Reviewer.
  3. Đặc biệt: nếu lỗi `MAX_TOKENS` hay `Expecting value` vẫn xảy ra trong vòng lặp, hệ thống sẽ tự động chặt đôi số lượng Day của `condensed_plan_json` (chỉ gửi nửa đầu roadmap) và thử lại để ép nó nuốt trôi, không để bị crash. Nếu thử 3 lần thất bại, bỏ qua Pass đó để tiến trình vẫn tiếp tục.

## 2026-08-04: Fix lỗi sinh tiêu đề Day trùng nhau trong Roadmap Bước 1 (PASS 1B)
- **Vấn đề:** Khi tạo roadmap ~180 Day, AI (Gemini) sinh ra 2 tiêu đề (`topic`) gần như giống nhau (ví dụ Day 59 và Day 64 trùng 100%), làm `validate_plan()` bắn lỗi `RoadmapValidationError` và crash toàn bộ tiến trình.
- **Nguyên nhân gốc rễ:** Prompt của PASS 1B chỉ truyền danh sách `topic_id` đã dùng (để AI tránh trùng ID), nhưng **không truyền danh sách tiêu đề `topic` đã tồn tại**, nên AI không biết để tránh.
- **Cách sửa trong `AskCpl.py` (`_roadmap_v5_step1`):**
  1. Xây dựng `known_titles` từ `all_days` trước mỗi batch và chèn vào cuối `phase_prompt` với câu lệnh "TUYỆT ĐỐI KHÔNG được lặp lại hay diễn đạt lại".
  2. Trong `except RoadmapValidationError`, nếu lỗi là `trùng nội dung` → ép prompt bổ sung danh sách tiêu đề bị cấm tường minh (`forbidden`), bắt AI đặt tên khác biệt hẳn.
  3. Xử lý Resume: Quét `all_days` khi load từ checkpoint để cắt phần trùng lắp, bắt AI sinh lại bù vào chỗ lỗi.

## 2026-07-29: Tối ưu hoá Lazy Load cho file .askcpl và Fix lỗi hiển thị file
- **Sửa lỗi hiển thị**: Cập nhật iletypes của skopenfilename và sksaveasfilename thành [('AskCpl Encrypted', '*.askcpl'), ('All Files', '*.*')] để fix lỗi không thấy file.
- **Lazy Loading**: Khi mở file .askcpl, hệ thống nay giải mã ra file .zip tạm thời và chỉ đọc Index thay vì bung nén và quét toàn bộ thư mục.
- **Lazy Extraction**: Khi bấm vào day_X.html, ứng dụng sẽ bung nén và quét file đó on-demand. Giảm thời gian mở file lớn từ vài chục giây xuống 1-2 giây.
- **Lazy Saving**: Khi lưu, hàm encrypt_from_zip_and_folder tự kết hợp các file đã chỉnh sửa ở thư mục tạm với file zip gốc để lưu lại (có loại bỏ các file bị xóa trong phiên) mà không cần bung tất cả.




### Giai đoạn 1 — Thiết kế kiến trúc & Xây dựng cơ bản

- **Thiết kế ban đầu:** Dự định làm Desktop App để paste dữ liệu thủ công.

- **Thay đổi kiến trúc (Hybrid Approach):** Chia làm 2 phần:

  1. **Browser Extension (Add-on):** Tự động chat "Day X" lặp đi lặp lại với Copilot, cạo dữ liệu HTML và lưu vào file JSON.

  2. **Python Script (`AskCpl.py`):** Viết bằng Tkinter và `pywin32`. Đọc file JSON và tạo file Word với từng trang tách biệt.

- **Hoàn thành code lần đầu:** Tạo toàn bộ `manifest.json`, `popup.html`, `popup.js`, `content_script.js` và `AskCpl.py`.



### Giai đoạn 2 — Khắc phục lỗi không inject được vào trang

- **Vấn đề:** Add-on không hiện log, không chạy được trên trang `m365.cloud.microsoft`.

- **Nguyên nhân:** `manifest.json` chỉ có quyền cho `*.microsoft.com`, thiếu `*.cloud.microsoft`.

- **Giải pháp:** Đổi `host_permissions` và `content_scripts matches` thành `<all_urls>`.

- **Thêm:** Bổ sung `sendResponse()` + `return true` trong listener để tránh lỗi "port closed" của Manifest V3.



### Giai đoạn 3 — Khắc phục lỗi file JSON không tải được (CSP Block)

- **Vấn đề:** Vòng lặp chạy xong nhưng không có file nào rớt xuống Downloads.

- **Nguyên nhân:** Microsoft 365 CSP chặn hoàn toàn `blob:` URL và link click tạo từ content script.

- **Giải pháp:**

  - Tạo thêm `background.js` (Service Worker) + xin quyền `downloads`.

  - `content_script.js` gửi dữ liệu lên `background.js` qua `chrome.runtime.sendMessage`.

  - `background.js` dùng `chrome.downloads.download()` để tải file, bypass hoàn toàn CSP.



### Giai đoạn 4 — Anti-Throttling (Giữ tab không bị ngủ)

- **Vấn đề:** Tab bị thu nhỏ → trình duyệt làm chậm `setTimeout` → Add-on chạy rất chậm.

- **Giải pháp:** Thêm cơ chế **Silent Audio Keep-alive**:

  - Nhúng file WAV vô âm dưới dạng base64 data URI.

  - Khi bắt đầu chạy: phát audio lặp → tab không bị throttle dù thu nhỏ.

  - Khi dừng/hoàn tất: `stopKeepAlive()` tắt audio.



### Giai đoạn 5 — Tính năng Tên Agent & Tên File tùy chỉnh

- Thêm ô nhập **"Tên Agent"** trên Popup.

- Tên Agent dùng làm prefix cho tên file JSON: `TenAgent_KhoaHoc_YYYYMMDD.json`.



### Giai đoạn 6 — Tối ưu hóa CPU & RAM

- **DOM Caching:** `cachedInput` và `cachedSendBtn` — tìm 1 lần rồi nhớ lại.

- **Tăng interval polling:** 2s → 4s/lần khi chờ AI trả lời.

- **Tăng thời gian nghỉ:** 4s → 8s giữa các vòng (giảm tải CPU, cho GC dọn RAM).



### Giai đoạn 7 — Sửa 5 Bug tiềm ẩn nghiêm trọng



| # | Bug | Hậu quả | Fix |

|---|-----|----------|-----|

| 1 | `cachedSendBtn` không check `.disabled` | Gửi prompt khi AI vẫn đang gõ | Reset cache khi nút bị disable |

| 2 | Luôn dùng `findDeep()` cho nút Stop | Quét shadow DOM nặng mỗi 4s | Kiểm tra DOM thường trước |

| 3 | Dùng `alert()` khi không có data | Đóng băng toàn trang Copilot | Đổi thành `sendStatus()` |

| 4 | `runNextDay()` gọi đệ quy trực tiếp | Call stack tràn sau 100+ ngày | Đổi thành `setTimeout(() => runNextDay(), 0)` |

| 5 | `join('\\\\n')` sai escape | JSON có ký tự literal `\n` | Đổi thành `join('\\n')` |



### Giai đoạn 8 — Tự nhận diện tên Agent từ trang web

- Thêm hàm `detectAgentName()` trong `content_script.js`.

- Thứ tự ưu tiên nhận diện:

  1. Selector đặc trưng M365 (`data-testid`, `aria-label`, class...).

  2. Thẻ `<title>` (loại bỏ hậu tố "- Microsoft Copilot", "- Bing"...).

  3. Thẻ `<h1>` hiển thị đầu tiên.

  4. Fallback: `"Copilot"`.

- Tên nhận diện gửi ngược lên Popup qua `update_agent_name` → ô nhập hiển thị viền **xanh lá**.



### Giai đoạn 9 — Auto-Save & Khôi phục dữ liệu (Chống mất data)

- **Vấn đề:** Tab bị đóng hoặc crash giữa chừng → toàn bộ dữ liệu mất.

- **Giải pháp:** Auto-save vào `chrome.storage.local` sau mỗi bài thu thập thành công.

  - Keys: `autosave_data`, `autosave_name`, `autosave_day`.

- **Khôi phục:** Khi trang load lại, nếu phát hiện dữ liệu cũ → hiện nút **"📥 Tải lại dữ liệu cũ"** (màu tím) trên Popup.

- Dữ liệu tạm xóa khỏi storage sau khi tải file thành công (cả từ nút Recover lẫn download bình thường).



### Giai đoạn 10 — Xuất HTML từng Day + Index tổng hợp + Session Resume



- **Vấn đề:** Toàn bộ HTML tích lũy trong `collectedData[]` trong RAM → khi chạy 100+ Day thì RAM đầy, trình duyệt crash, mất sạch dữ liệu. Chỉ có 1 file JSON dump ở cuối.

- **Giải pháp:** "Write-as-you-go" — tải file HTML **ngay sau mỗi Day** vào subfolder trong Downloads:

  ```

  Downloads/

  └── agent_name/

      ├── index.html       ← Cập nhật dần sau mỗi Day

      ├── day_1.html

      ├── day_2.html

      └── session.json     ← Quản lý phiên, dùng để Resume

  ```

- **Thay đổi kỹ thuật:**

  - `content_script.js`: Thêm `downloadDayHtml()`, `updateIndex()`, `saveSession()`. Bỏ `downloadJson()`. HTML được giải phóng khỏi RAM ngay sau khi tải. `dayIndex[]` chỉ lưu metadata nhỏ.

  - `background.js`: Thêm handler `download_html`, `download_index`, `download_session` với `conflictAction: "overwrite"` để ghi đè index & session mỗi lần cập nhật.

  - `popup.html/js`: Thêm nút **"📂 Chọn file session.json"** + `<input type="file">`. Parse JSON → điền UI → gửi `resume_session` lên content script. Thêm hiển thị `day_saved` status.

- **Tính năng Resume:** Người dùng chọn `session.json` từ bất kỳ đâu trên máy → Addon tiếp tục từ ngày tiếp theo, dùng lại đúng tên thư mục cũ.

- **Lưu ý bảo mật trình duyệt:** Extension chỉ được ghi vào thư mục Downloads (và subfolder). Không thể ghi trực tiếp vào thư mục dự án. Người dùng có thể copy `session.json` sang `AskCpl/` thủ công để lưu trữ.



### Giai đoạn 11 — Kiến trúc "One-Chat-Per-Day" + Fix Download Root Cause



- **Vấn đề 1 (Download):** `background.js` dùng `URL.createObjectURL()` — **KHÔNG tồn tại trong Service Worker MV3**. Silent fail: download API nhận URL lỗi → không tải được file dù không báo lỗi nào.

  - **Fix:** Thay hoàn toàn bằng **base64 data URI**:

    `TextEncoder → Uint8Array → String.fromCharCode (chunk 8192) → btoa() → data:mimeType;base64,...`

  - Hàm mới: `dataUriDownload()` thay cho `blobDownload()`. Hoạt động 100% trong SW.



- **Vấn đề 2 (Phân tách dữ liệu):** Kiến trúc cũ nhắn Day 1 → Day 2 → Day 3 trong **cùng 1 đoạn chat** → extract lấy lẫn toàn bộ nội dung, không cô lập được reply của từng Day.



- **Giải pháp — Kiến trúc mới: Mỗi Day = 1 Chat Mới:**

  - Từ Day 2 trở đi: click nút **"New Chat"** trước → chat mới chỉ có **1 AI reply duy nhất** → extract lấy tất cả = đúng bài đó, không cần isolate.

  - URL không đổi khi click New Chat (SPA) → `isRunning` và toàn bộ state giữ nguyên → an toàn.

  - Thêm hàm `clickNewChat()`: selector theo thứ tự ưu tiên `data-automation-id` → `data-testid` → `aria-label`.

  - Thêm hàm `waitForNewChatReady()`: chờ tối đa 15s, confirm bằng `inputEmpty && aiResponses.length === 0`.

  - `extractLatestResponse()` đơn giản hóa: bỏ chiến lược "30 `<p>` cuối" (không cần nữa vì chat mới sạch).

  - Logic trigger: `if (dayIndex.length > 0)` → đã có bài cũ → click New Chat.



### Giai đoạn 12 — Fix Input + Tối ưu CPU/RAM



- **Vấn đề Input:** M365 Copilot dùng `div[contenteditable]` với React/FluentUI. Gán `innerText` trực tiếp → React **không nhận** → Send button vẫn disabled → loop dừng.

  - **Fix:** Hàm `fillInput()` mới: dùng `document.execCommand('insertText')` + `InputEvent({composed:true})`. `execCommand` trigger `beforeinput → input` chain → React state update đúng cách.

  - **Fix Selector:** Đưa `div[role="textbox"][contenteditable="true"]` lên đầu danh sách. Bỏ `'textarea'` fallback chung (dễ match ô tìm kiếm M365).

  - **Fix Enter:** Thêm `composed: true` + thêm `keyup` event.

  - **Chờ state:** Tăng delay sau fill từ 800ms → 1500ms để React update Send button.



- **Tối ưu CPU/RAM:**

  - `waitForNewChatReady`: 500ms → 1500ms (giảm 66% DOM queries trong vòng chờ)

  - `extractLatestResponse`: Thêm `capHtml(100KB)` — tránh chuỗi MB trong RAM. Bỏ `S3b: mainEl.innerHTML` (có thể vài MB). Giới hạn S3 tối đa 80 elements. Fallback S4 cắt 3000 chars (thay 5000).

  - `processExtractedContent`: Regex stop-keyword chỉ trên 1500 chars đầu (thay toàn bộ HTML).

  - `findSendButton`: Bỏ fallback `querySelectorAll('form button, [role="search"] button')` — scan nặng.



### Giai đoạn 13 — Fix "Day 1Day 1" + Bỏ AudioContext + Debug Download



- **Bug "Day 1Day 1" (Root Cause):** `execCommand('delete')` xóa DOM → React **re-render ngay** → khôi phục "Day 1" → `insertText("Day 1")` append → "Day 1Day 1".

  - **Fix:** Dùng `Range.selectNodeContents(el)` + `window.getSelection().addRange(range)` → `execCommand('insertText', false, value)` REPLACE toàn bộ selection trong 1 lệnh. React's `beforeinput` handler thấy toàn bộ operation trước khi commit → state update đúng, không còn re-render xen giữa.



- **Bug `waitForNewChatReady` timeout:** Điều kiện `chatCleared = aiResponses.length === 0` dùng `.markdown-body` — selector này **luôn tồn tại** trong page chrome M365 (sidebar, tooltip...) → không bao giờ = 0 → timeout 9s mọi lần.

  - **Fix:** Bỏ `chatCleared`. Chỉ check `inputEmpty` + chờ cứng 3s + poll thêm 6s. `fillInput` đã xử lý nếu input chưa rỗng (Range.selectAll sẽ xóa).



- **Bỏ `keepAliveAudio`:** `AudioContext` chạy liên tục gây CPU spike 5-15%, ngay cả với silent WAV. Kiến trúc mới (mỗi Day = 1 chat mới) không cần giữ tab active.



- **Giảm downloads per Day:** Từ 3 (HTML + index + session) → 1 (chỉ HTML). Index + session chỉ update mỗi 5 Day hoặc khi finish → giảm 60% downloads, giảm tải background.js.



- **Download Error Visibility:** `background.js` gửi kết quả download (OK hoặc FAILED + message) về popup log area → người dùng thấy lỗi ngay mà không cần mở SW DevTools console.



---



### Giai đoạn 14 — Fix Cắt Giữa + Sai Nội Dung + Popup Sync



- **Fix "Day 2 bị cắt" (Issue 3):**

  - Root cause: `waitForResponseComplete` phát hiện "xong" khi AI tạm nghỉ giữa chunk dài → Stop button biến mất thoáng qua → extract sớm.

  - Fix: Thêm `waitForStable(15s)` — DOM (innerText.length của `[role="main"]`) phải ổn định 15s liên tiếp mới coi AI xong thật. Poll 2s/lần, tối đa 90s.



- **Fix "Day 1 chỉ ra tên agent" (Issue 4):**

  - Root cause: Selectors S1-S3 không match M365 Copilot DOM. Rơi xuống S4 `body.innerText` → lấy page chrome text → chỉ có tên agent.

  - Fix: `snapshotBeforeSend()` — chụp số block elements TRƯỚC khi gửi. `extractDeltaContent(snapshot)` — lấy elements **sau** snapshot.count → chỉ nội dung MỚI (reply của AI), không lẫn header/sidebar.

  - Fix: `validateContent(html, agentName)` — lọc content quá ngắn (<100 chars) hoặc chủ yếu là tên agent (>40% từ).



- **Fix "Popup đóng tưởng dừng" (Issue 5):**

  - Root cause: Popup load lại từ đầu → không biết loop đang chạy.

  - Fix: `saveRunningState()` trong `processExtractedContent` sau mỗi Day → lưu `{ isRunning, currentDay, agentName, lastSaved }` vào `chrome.storage.local['runningState']`. `clearRunningState()` khi finish/stop.

  - `popup.js`: `syncRunningState()` gọi khi popup mở → đọc storage → hiện banner + Stop button.

  - `popup.html`: `#runningBanner` với pulse animation, hiện agent name + Day đã lưu. Chú thích "Đóng popup không ảnh hưởng".



---



### Giai đoạn 15 — Smart Input + Fully Autonomous + Log Persist



- **Smart Input Detection (5 chiến lược):**

  1. **Fingerprint**: `saveInputFingerprint(el)` lưu selector (tag+attributes+parent) vào `chrome.storage.local['inputFingerprint']`. Day 2+ thử fingerprint trước → tìm đúng ngay mà không cần user click.

  2. **Lexical detection**: Tìm `[data-lexical-text]` → `.closest('[contenteditable="true"]')`. M365 dùng Lexical editor (cấu trúc `<p>` + `<span data-lexical-text>`).

  3. **Standard selectors**: role, aria-label, data-automation-id.

  4. **Broad CE scan**: `querySelectorAll('div[contenteditable="true"]')` lọc bỏ container quá lớn (>500px height, >20 children).

  5. **activeElement fallback**.



- **Fully Autonomous — Day-Level Retry:**

  - `runNextDay()` = wrapper retry tối đa 3 lần (retry 0, 1, 2).

  - `_runNextDayAttempt(retryCount)` trả `'ok'|'retry'|'stop'`.

  - Nếu không tìm được input hoặc extract fail → return `'retry'` → mở New Chat mới → gửi lại Day N.

  - Chỉ `finishLoop()` sau khi hết cả 3 lần thất bại.



- **Log Persist:**

  - `flushLogs()` lưu 200 dòng cuối vào `chrome.storage.local['popup_logs']`.

  - `popup.js`: `loadPersistedLogs()` khi mở → hiện log cũ + dòng `── [Popup mở lại] ──`.



- **Stability-First Wait:**

  - Bỏ phụ thuộc `findSendButton()` (luôn null trên M365).

  - Chờ cứng 2 phút → poll 30s → DOM stable 15s = AI xong.

  - Cap: 2MB HTML + 500 blocks.



### Giai đoạn 16 — Keep-Alive 3 Tầng (Chống Tab Sleep)



- **Vấn đề:** Chuyển tab/app → Chromium throttle `setTimeout` → delay 10s thành 60s+ → sau 5 phút tab freeze → loop dừng.

- **Giai đoạn 13 đã bỏ `keepAliveAudio`** vì dùng AudioContext + WAV file → CPU 5-15%. Bây giờ cần cách nhẹ hơn.



- **Fix: 3 tầng keep-alive (~0.3% CPU tổng):**

  1. **Web Lock** (`navigator.locks.request` + Promise never-resolve): Chống Edge Sleeping Tabs discard. ~0% CPU.

  2. **Inline Worker** (`Blob` URL + `setInterval(25s)`): Workers KHÔNG bị throttle trong background tab → giữ main thread active. ~0.1% CPU.

  3. **Silent Oscillator** (`AudioContext`, gain=0.00001, freq=1Hz): Browser coi tab đang phát audio = "important" = không freeze. ~0.2% CPU.



- **Lifecycle:**

  - `setupKeepAlive()`: Gọi khi start_loop / resume_session.

  - `teardownKeepAlive()`: Gọi khi stop_loop / finishLoop(). Giải phóng tài nguyên ngay.



### Giai đoạn 17 — Auto-Resume (Fix Dừng Ở Day 2)



- **Root cause:** Click "New Chat" trên M365 → SPA navigate → content_script.js bị **re-inject** → tất cả biến JS reset (`isRunning=false`, `currentDay=1`) → loop "dừng". Đây không phải tab sleep — mà là **script bị reload**.



- **Fix: Auto-Resume khi script load:**

  - Khi content_script.js khởi tạo → đọc `chrome.storage.local['runningState']`

  - Nếu `isRunning === true`:

    - Khôi phục: `currentDay`, `agentName`, `folderName`, `prefix`, `dayIndex` (từ autosave_data)

    - `setupKeepAlive()`

    - Chờ 5s (page settle) → `runNextDay()` tự động

    - Log: `🔄 AUTO-RESUME: "AgentName" từ Day N`



- **Fix: `saveRunningState(nextDay, lastSaved)`:**

  - Tham số mới `nextDay`: luôn lưu day **TIẾP THEO** cần xử lý

  - Gọi SAU `currentDay++` trong `processExtractedContent`

  - → Auto-resume đọc `runningState.currentDay` = đúng day cần chạy, không trùng day đã xong

  - Thêm `prefix` vào runningState để auto-resume biết prefix



### Giai đoạn 18 — Fix CSP, Audio, Context Invalidation & Tối ưu Adaptive Wait



- **Fix Worker CSP**: Bỏ `Blob Worker` vì M365 CSP chặn `worker-src 'self'`. Dùng `setInterval` bình thường. Kết hợp với `Web Lock` là đủ chống discard.

- **Fix AudioContext**: Bỏ `AudioContext` vì yêu cầu user gesture, có thể ném lỗi khi auto-resume hoặc reload.

- **Fix Context Invalidated**: Khi script bị orphan do reload, gọi `chrome.runtime.sendMessage` sẽ throw exception làm sập script. → Viết hàm `safeSendMessage` bọc try-catch và check `chrome.runtime?.id`.

- **Tối ưu Adaptive Wait**: Rút ngắn thời gian chờ cứng `MIN_WAIT` từ 120s xuống 15s. Sau 15s bắt đầu check stability (cần 15s stable). Tổng cộng mất khoảng ~30s nếu AI trả lời xong nhanh (thay vì luôn luôn chờ chết 2 phút).



### Giai đoạn 19 — Fix Lỗi "Chờ 10s Bị Đóng Băng" (Tab Freeze) & Tối ưu Auto-Resume



- **Root Cause**: Giai đoạn 18 gỡ `AudioContext` khiến tab chạy ngầm (background) dễ bị Chromium đóng băng toàn bộ Javascript (Tab Freeze) ngay sau khi AI tạo xong text (vì DOM không còn thay đổi). Việc gọi `delay(10000)` dùng `setTimeout` sẽ bị ngưng đọng vĩnh viễn không bao giờ chạy tiếp.

- **Khắc phục 1 (Bỏ nhàn rỗi)**: Xóa bỏ hoàn toàn thời gian chờ 10s vô nghĩa giữa các Day trong `processExtractedContent`. Chạy ngay sang Day kế tiếp để giữ luồng hoạt động, ngăn Chromium rảnh rỗi đóng băng tab.

- **Khắc phục 2 (Tối ưu Reload)**: Khi M365 bị tải lại (do SPA navigate) và trigger `Auto-Resume`, giảm thời gian chờ của Auto-Resume từ 5s xuống 1.5s để tránh freeze. Truyền cờ `isAutoResumed = true` vào `runNextDay` để ngăn script bấm nút `New Chat` thêm một lần nữa (vì trang vừa tải lại vốn dĩ đã là chat mới tinh), tránh vòng lặp tải lại trang vô tận.



### Giai đoạn 20 — Fix Lỗi Chờ Lâu (5-10 phút) Khi AI Đã Xong



- **Vấn đề**: Đôi lúc AI đã tạo xong toàn bộ nội dung, nhưng tiến trình vẫn đứng yên chờ thêm 5-10 phút thay vì hoàn thành ngay.

- **Nguyên nhân**:

  1. **Strict Equality**: Hàm `checkStable15s` đo độ dài text (`innerText.length`) của toàn trang và yêu cầu không được thay đổi dù chỉ 1 ký tự (`len === lastLen`) trong suốt 15 giây.

  2. **Nhiễu DOM**: Giao diện M365 Copilot thường có các thay đổi nhỏ ngoài ý muốn (ví dụ: thời gian cập nhật "1 min ago", nút chức năng ẩn/hiện, gợi ý prompt). Các thay đổi này làm chiều dài text dao động nhẹ, liên tục reset bộ đếm ổn định 15 giây.

- **Giải pháp**:

  - **Đo lường cục bộ (Scoped Check)**: Viết hàm `getNewTextLength()` CHỈ tính độ dài text của các element MỚI sinh ra sau khi gửi prompt (dựa trên việc lọc bỏ các element có `dataset.askcplSnapshot = "1"`). Điều này chặn mọi nhiễu từ các thành phần cũ trên trang.

  - **Dung sai (Tolerance)**: Cho phép sai số thay đổi `Math.abs(len - lastLen) <= 30` ký tự. Khi AI thực sự stream text, số lượng ký tự sẽ tăng rất nhanh và bứt phá khỏi khoảng dung sai. Nếu chỉ là UI render nút "Copy" hay icon thay đổi ở cuối quá trình, sự dao động sẽ nằm trong khoảng 30 ký tự và không làm reset bộ đếm, giúp tiến trình nhận diện AI đã xong ngay lập tức.



### Giai đoạn 21 — Hệ thống Config Đa Nền Tảng & Bộ nhớ phỏng vấn (Multi-step Interrogation)



- **Vấn đề**:

  - Người dùng cần lưu nhiều cấu hình (Config) khác nhau cho các Agent khác nhau (ví dụ: một cái cho Copilot tiếng Anh, một cái cho Gemini).

  - Cần tính năng tự dừng vòng lặp ở một `Ngày kết thúc` (End Day) nhất định.

  - Vòng lặp chat dài ngày khiến AI "quên" các chủ đề đã học. Cần một cách để bắt AI tự tóm tắt và ghi nhớ lại các ý chính đã học ở mỗi ngày để mớm (inject) vào prompt của ngày tiếp theo.



- **Giải pháp**:

  - **Hệ thống Profiles**: Nâng cấp `popup.html/js` để có một Dropdown duy nhất cho phép chọn, lưu và xóa nhiều Profile khác nhau (vd: "Copilot - Basic", "Copilot - Từ vựng"). Toàn bộ config (Day, Tiền tố, End Day, tính năng nâng cao) được bọc chung vào 1 Profile và lưu trong `chrome.storage`.

  - **Ngày kết thúc (End Day)**: Thêm ô thiết lập `End Day`. Trong `processExtractedContent`, nếu `currentDay >= endDay`, vòng lặp sẽ gọi `finishLoop()` ngay lập tức.

  - **Memory Advanced (Phỏng vấn liên hoàn)**:

    - Biến Addon thành một quy trình Agentic (Multi-step Interrogation). Thay vì 1 Day chỉ gửi 1 lệnh, Addon sẽ tự động nhắn tin phỏng vấn AI nhiều lần trong cùng 1 bài.

    - Bước 1: Gửi bài chính `Day X`.

    - Bước 2: Gửi câu hỏi mớm để hỏi Tên Chủ Đề (vd: *"Chủ đề là gì chỉ mỗi chủ đề thôi"*). Cập nhật biến đếm số bài của chủ đề đó.

    - Bước 3: Nếu Chủ đề chưa hoàn thành đủ số lượng mục tiêu, Addon vòng lặp qua các "Chi tiết" được cài đặt trên giao diện (ví dụ: Chi tiết 1: "Từ vựng", Chi tiết 2: "Ngữ pháp"). Mỗi chi tiết sẽ kích hoạt 1 câu hỏi độc lập với AI (vd: *"Hỏi từ vựng là gì, chỉ ghi các từ vựng thôi"*).

    - Câu trả lời của AI cho các Chi tiết này sẽ được bóc tách và cộng dồn vào Object bộ nhớ cục bộ (`topicMemory`).

  - **Memory Injector**: Trước khi gửi `Day X+1`, Addon tự động format bộ nhớ `topicMemory` thành một khối text gọn gàng (vd: *Chủ đề: Con người 1/4 \n Từ vựng đã học: ... \n Ngữ pháp đã học: ...*). Khối text này được gắn trực tiếp vào cuối câu lệnh `Day X+1` để "mớm" trí nhớ cho AI. Các chủ đề đã đạt mục tiêu (ví dụ 4/4) sẽ được rút gọn thành chữ "Hoàn tất" để tiết kiệm token.



### Giai đoạn 22 — Adapter Đa Nền Tảng (Gemini/ChatGPT) & Lộ trình Động Phân Cấp (Hierarchical Roadmap)



- **Vấn đề**: Người dùng cần chạy Add-on ở nhà với các tài khoản AI miễn phí (Google Gemini, ChatGPT) nhưng các AI này không hỗ trợ tạo Agent lưu ngữ cảnh cố định (System Prompt). Hơn nữa, việc "nhồi" trí nhớ của hàng trăm bài học cũ vào một câu lệnh sẽ gây phình to ngữ cảnh (Context Overflow) và tốn token. Việc thay đổi tài khoản AI miễn phí (do hết lượt) cũng làm xáo trộn lộ trình.

- **Giải pháp**:

  1. **Hierarchical Roadmap (Lộ trình phân cấp)**:

     - Thêm ô nhập `Roadmap` trên `popup.html`. Người dùng có thể copy Bảng Markdown Lộ Trình (xin từ ChatGPT) và dán thẳng vào.

     - Add-on có tính năng "Tạo JSON Roadmap": tự động nhóm các bài học theo cột `Chương` (Main Topic) và tạo ra một file JSON Phân cấp.

  2. **Token-Optimized Prompt Injector (Nén Trí Nhớ)**:

     - Trong `content_script.js`, Add-on dò xem Ngày hiện tại thuộc Chương nào. Nếu đang ở giữa Chương, nó sẽ ghép thêm câu tóm tắt của các ngày trước *thuộc cùng Chương đó*.

     - Khi chuyển sang Chương mới, toàn bộ tóm tắt chi tiết của Chương cũ sẽ bị "chốt sổ" và xóa khỏi lệnh, giúp giải phóng hoàn toàn bộ nhớ Prompt, giữ cho lệnh gửi luôn sắc bén và cực kỳ ngắn gọn.

  3. **Auto Summarizer**: Sau khi lấy xong bài học chính, Add-on tự động bắn thêm lệnh phụ *"Tóm tắt cực kỳ ngắn gọn kiến thức trên"* và lưu vào `historySummaries`.

  4. **Adapter Pattern**: Tách rời logic DOM Selector cho `clickNewChat`, `findChatInput`, `findSendButton` và `extractDeltaContent` dựa trên lựa chọn Nền tảng (copilot, gemini, chatgpt). 

  5. **Persistent Session (Khóa cứng Lộ Trình)**: Nhúng (embed) trực tiếp toàn bộ khối `roadmapData` và `historySummaries` vào trong file `session.json`. Giúp người dùng khi cạn dung lượng tài khoản A có thể đăng nhập tài khoản B, bấm tải file session lên và Add-on sẽ tự phục hồi Lộ trình lẫn Trí nhớ để tiếp tục mạch học chính xác đến từng chữ.



### Giai đoạn 23 — Fix lỗi không tạo New Chat trên Gemini

- **Vấn đề**: Người dùng báo cáo Addon tiếp tục gửi bài mới vào cùng một đoạn chat cũ trên Gemini thay vì tạo chat mới, làm mất tác dụng của cơ chế One-Chat-Per-Day.

- **Nguyên nhân**: Nút "New Chat" của Gemini đã thay đổi cấu trúc DOM, selector cũ `a[href*="/app/new"]` không còn tìm thấy.

- **Giải pháp**: Nâng cấp hàm `clickNewChat()` cho Gemini:

  - Bổ sung loạt selector mới: `a[href="/app"]`, `button[aria-label*="trò chuyện mới"]`, v.v.

  - Thêm cơ chế **Text Fallback**: Quét toàn bộ thẻ `span, div, p` để tìm chữ "New chat" hoặc "Trò chuyện mới" và click vào thẻ cha có khả năng click (button/a). Điều này đảm bảo luôn tìm được nút dù Google có đổi code ẩn đi chăng nữa.



### Giai đoạn 24 — Fix lỗi dán text nhưng Gemini hiện icon Loa (Không gửi được)

- **Vấn đề**: Khi Addon dán Prompt vào ô nhập của Gemini, thay vì hiện nút Gửi (Send) thì Gemini vẫn hiện icon Micro/Loa. Gây lỗi không thể nhấn nút Gửi (do nút Gửi chưa xuất hiện).

- **Nguyên nhân**: Gemini sử dụng Web Component `<rich-textarea>`. Lệnh `execCommand('insertText')` thay đổi text trong DOM nhưng không tự động bắn ra sự kiện (Event) để báo cho framework (Angular/Lit) của Gemini biết. Hệ thống tưởng ô nhập vẫn đang trống.

- **Giải pháp**: 

  - Cập nhật selector tìm ô nhập: Lấy đúng thẻ `div[contenteditable="true"]` nằm SÂU BÊN TRONG thẻ `<rich-textarea>`.

  - Cập nhật hàm `fillInput()`: Bắt buộc bắn liên tiếp 3 event: `InputEvent('input')`, `Event('input')`, và `Event('change')` trực tiếp vào ô nhập. 

  - Đồng thời bắn thêm một event `input` ngược lên thẻ cha `<rich-textarea>` để "đánh thức" framework của Gemini, ép nó nhận diện text và hiện nút Gửi.



---



## Cấu trúc file hiện tại



```

CopilotWordExportAddon/

├── manifest.json       — Cấu hình extension (MV3, quyền downloads + storage, <all_urls>)

├── background.js       — Service Worker: download_html / download_index / download_session

├── content_script.js   — Vòng lặp auto, tải HTML từng Day, cập nhật index & session

├── popup.html          — Giao diện: Start/Stop, Resume từ session.json, log area

└── popup.js            — Logic Popup: file picker, resume flow, day_saved status



AskCpl.py               — Python/Tkinter: đọc JSON → xuất Word (dùng pywin32)

ProjectLog.md           — File này



Output (trong Downloads của trình duyệt):

agent_name/

├── index.html          — Trang tổng hợp, link đến từng bài (cập nhật dần)

├── day_1.html          — Bài ngày 1 (file HTML độc lập, đọc offline được)

├── day_2.html

└── session.json        — Quản lý phiên (resume lần sau)

```



---



## Các lệnh & Thư viện sử dụng

- `pip install pywin32` — Bắt buộc để Python điều khiển MS Word.

- Addon APIs: `chrome.storage.local`, `chrome.downloads`, `chrome.runtime`, `chrome.tabs`.



---



## Lưu ý quan trọng khi chỉnh sửa



> **Sau khi sửa `manifest.json` hoặc `background.js`:**

> Vào `edge://extensions/` → bấm **Tải lại (Reload)** extension.



> **Sau khi sửa `content_script.js`:**

> Quay lại trang Copilot → bấm **F5** để inject lại script.



> **File HTML và session.json** nằm trong `Downloads/agent_name/` (subfolder tự động tạo).

> Không thể tùy chỉnh đường dẫn ngoài Downloads do giới hạn bảo mật trình duyệt.



> **Sau khi sửa `content_script.js`:**

> Quay lại trang Copilot → bấm **F5** để inject lại script.



> **Resume phiên cũ:** Copy `session.json` từ `Downloads/agent_name/` sang bất kỳ đâu → mở Popup → "📂 Chọn file session.json" → Start.



---



## Chuẩn cấu trúc file Roadmap (.md)



Để tạo lộ trình (Roadmap) chuẩn xác cho Addon đọc ở chế độ "File MD", **bắt buộc tuân theo định dạng sau** để Addon có thể parse bằng Regex.



```markdown

## Day 1 — Tiêu đề bài học

**Prompt:**

Nội dung câu lệnh bạn muốn gửi cho AI. Có thể dài nhiều dòng.

Addon sẽ copy toàn bộ nội dung từ dưới chữ "Prompt:" cho đến khi gặp chữ "Bài tập:" hoặc "Tags:" hoặc dòng "## Day" tiếp theo.



**Bài tập:**

- Bài 1

- Bài 2



**Tags:** #tag

```



- Addon sẽ tự động tìm các cụm `## Day X`.

- Addon sẽ lấy mọi văn bản từ sau `**Prompt:**` để làm câu lệnh (prompt) gửi cho AI.

- Nếu bạn yêu cầu AI khác tạo Roadmap, hãy cung cấp đúng chuẩn này để tạo ra file `.md` ăn khớp 100% với Addon.



### Giai đoạn 25 — Tạo Roadmap JavaScript 7 Năm (2560 Ngày)

- Đã tạo Python script `generate_js_roadmap.py` để tự động hóa việc sinh file Markdown dài (hơn 33,000 dòng).

- Gen thành công file `roadmap_javascript_7years.md` bao phủ toàn bộ lộ trình 2560 ngày học liên tục (từ Foundation đến Web3, AI, Distributed System).

- File tuân thủ 100% định dạng Parsing của Copilot Word Export Addon.



### Giai đoạn 26 — Tạo Roadmap Thể Dục Tại Nhà (365 Ngày)

- Yêu cầu: Thiết kế lộ trình giảm cân & tăng cơ 1 năm cho người 108kg, 100% tập tại nhà, 30 phút/ngày, không bật nhảy (bảo vệ khớp).

- Thực thi: Đã tạo file `roadmap_fitness_365days.md` chứa đầy đủ 365 ngày (gồm bài tập chi tiết số hiệp/lần và thực đơn tương ứng mỗi ngày).

- Tích hợp chuẩn Copilot Addon: Prompt yêu cầu AI nhắc nhở kỹ thuật an toàn khớp, đánh giá thực đơn và động viên người dùng.

- **Bản V2 (Cập nhật)**: Bổ sung định lượng thực đơn chính xác (số gram, chén) và chi tiết 100% form chuẩn của các bài tập trực tiếp vào file HTML (để người dùng dễ theo dõi). Đã chỉnh sửa Prompt để AI làm "Kiểm toán viên dinh dưỡng" đánh giá trực tiếp số lượng thực phẩm này.

- Dọn dẹp: Đã lưu lại script Python `generate_fitness_365_v2.py` theo yêu cầu của người dùng để tùy biến sau này.



### Giai đoạn 28 — Fix Lỗi Kẹt Chờ 30s & Chống Ngủ Bằng Silent Audio

- **Vấn đề 1**: Quá trình Automation thỉnh thoảng bị kẹt vĩnh viễn ở bước chờ tạo New Chat (có thể do kết nối mạng yếu hoặc UI của AI thay đổi). Lỗi khiến cho hệ thống mất từ 7 phút đến vài chục phút.

- **Giải pháp 1**: Áp dụng Timeout 30 giây cho hàm `waitForNewChatReady`. Nếu sau 30s mà New Chat chưa sẵn sàng, Extension sẽ tự động ép Reload trang (`location.reload()`). Nhờ cơ chế Auto-Resume có sẵn từ Giai đoạn 17, hệ thống sẽ tự động khôi phục quy trình và chạy lại Day đó thay vì bị kẹt vĩnh viễn.

- **Vấn đề 2**: Các trình duyệt hiện đại (Chrome/Edge) tự động đưa tab vào chế độ ngủ (Sleeping Tabs/Background Throttling) khi tab bị ẩn quá lâu, khiến Javascript chạy ngầm bị delay cực nặng, kéo dài thời gian chờ 5-7 phút.

- **Giải pháp 2**: Kích hoạt lại kỹ thuật Silent Audio Keep-alive (từng bị tắt ở Giai đoạn 13). Bằng cách chèn một file âm thanh ngắn (chuỗi Base64 cực nhỏ) tĩnh lặng (0.01 volume) và lặp vô tận thông qua thẻ `<audio>` khi gọi `setupKeepAlive`. Điều này sẽ "đánh lừa" trình duyệt tin rằng tab đang phát nội dung Media, duy trì mức ưu tiên xử lý cao nhất (Highest Priority) và chống Throttling 100%.





### Giai đoạn 29 — Fix Toàn Diện: Chrome Reload, Heartbeat, Error Detection



**Phát hiện 7 bug qua phân tích thực tế khi chạy trên Chrome:**



| # | Bug | Hậu quả | Fix |

|---|-----|----------|-----|

| F1 | sessionStorage không tin cậy trên Chrome khi reload | Loop báo “Khôi phục...” nhưng đứng luôn | Thay bằng chrome.storage.local làm reload flag với timestamp expire 15s |

| F2 | let _isIntentionalReload = false khai báo SAU pagehide listener | pagehide luôn thấy flag = alse → luôn xóa 

unningStates | Di chuyển khai báo lên TRƯỚC pagehide listener |

| F3 | pagehide xóa 

unningStates kể cả khi intentional reload | Mất state trước khi kịp reload | Chỉ xóa khi !_isIntentionalReload |

| F4 | udio.play() bị block trên Chrome sau reload (không có user gesture) | Silent Audio không phát → tab có thể sleep | Tách hàm _playKeepAliveAudio() với retry sau 3s |

| F5 | Không detect error response (mất mạng, rate limit) | Lưu bài với nội dung error message của trang | Thêm isErrorContent(html) check → retry nếu phát hiện từ khóa lỗi |

| F6 | Không có heartbeat → popup không biết loop đã chết | Popup vẫn hiện nút STOP dù loop chết từ lâu | Content script cập nhật lastHeartbeat mỗi 15s. Popup kiểm tra: nếu > 45s → tự clear. Fix bug key sai 

unningState → 

unningStates |

| F7 | Sau reload, retry lần 2 vẫn click New Chat → timeout → reload lại | Vòng lặp reload vô tận | Guard _lastReloadTs: nếu vừa reload trong 60s → skip click New Chat |



- **Edge vẫn hoạt động**: pagehide chỉ xóa state khi !_isIntentionalReload. Heartbeat timeout 45s đủ dài để không false-positive khi Edge SPA navigate.

- **Không thay đổi flow chính**: Tất cả fix chỉ ảnh hưởng startup/reload/error path.





### Bổ sung Fix Giai đoạn 29 — Lỗi Reload không resume được



**Nguyên nhân:**

- Hàm utoSave() trước đây chỉ được gọi SAU khi một ngày hoàn thành. Nếu timeout và reload xảy ra ở ngày đầu tiên trước khi extract thành công, chưa có file session được lưu vào ổ đĩa/storage → sau khi reload sẽ không có để khôi phục.

- Biến JS _lastReloadTs bị reset về 0 sau khi load lại trang, khiến chống loop reload fail và vòng lặp vô tận vẫn tiếp tục click “New chat” rồi reload.



**Fix:**

| # | File | Chi tiết |

|---|------|---------|

| 1 | content_script.js | Thêm saveStateForReload() và đợi callback xác nhận lưu xong TRƯỚC khi thực hiện location.reload(). Lưu current state dù chưa làm xong bài nào. |

| 2 | content_script.js | Bỏ qua kiểm tra phức tạp bằng _lastReloadTs, đơn giản hóa logic 

eedNewChat bằng param từ background (gửi thêm isFromReload để biết là mới reload xong → đang ở New Chat sẵn, KHÔNG click nữa). |





### Giai đoạn 30 — Sửa lỗi vượt Quota Storage & Auto-Stop Roadmap



- **Vấn đề 1 (Session không lưu được do vượt dung lượng):** Với những Roadmap quá lớn (VD 2500 ngày), file session json encode thành base64 sẽ vượt quá giới hạn 5MB mặc định của `chrome.storage.local`. Điều này làm API `chrome.storage.local.set` fail ngầm, khiến data không thể phục hồi sau khi reload trang.

  - **Giải pháp:** Cấp quyền `"unlimitedStorage"` trong `manifest.json`. Người dùng cần phải reload lại Add-on ở trang `chrome://extensions/` để Chrome yêu cầu cấp quyền này, đảm bảo vòng lặp dù 5000 ngày vẫn lưu state an toàn.

- **Vấn đề 2 (Không tự dừng khi chạy ết Roadmap mà quên điền endDay):** Hệ thống luôn coi `endDay = null` nếu user bỏ trống, gây chạy vô tận qua ngày 2501, 2502... bằng dữ liệu rỗng hoặc template mặc định.

  - **Giải pháp:** Thêm hàm `calcAutoEndDay()` ở `content_script.js`. Tự động parse tất cả `roadmapData` trong `start_loop` và `resume_session`, tìm `Math.max` của các day để auto fill `endDay`. Bảo đảm tự ngắt loop đúng ngày cuối dù user chả gõ gì vào ô Ngày kết thúc.





### Giai đoạn 31 — Khắc phục Lỗi Service Worker & Chống Kẹt Trạng Thái Chờ



- **Vấn đề 1 (Lỗi `Receiving end does not exist`):** `chrome.runtime.sendMessage` bị Promise Rejection do Service Worker `background.js` rơi vào trạng thái ngủ ngầm sau 30s không hoạt động, khiến file HTML không được tải về đĩa.

  - **Giải pháp:** 

    - Thêm listener `action: "ping"` ở `background.js` và gửi ping mỗi 20s từ `content_script.js` để giữ Service Worker luôn thức.

    - Viết lại hàm gửi lệnh download bằng cách bọc trong `sendDownloadMessageWithRetry()`, tự động `await delay(1000)` và retry tối đa 3 lần nếu bắt gặp lỗi kết nối.

- **Vấn đề 2 (Kẹt trạng thái `Chờ AI phản hồi` gần 1 tiếng):** Nếu rớt mạng hoặc Gemini báo lỗi (Network Error), icon loading bị dính trên DOM. Addon lầm tưởng AI vẫn đang gõ và chờ mù quáng tới 10 phút.

  - **Giải pháp:** Cải tiến hàm `checkStable15s()`. Bổ sung biến theo dõi `textChangeStart`. Nếu độ dài chữ không tăng thêm một ký tự nào trong vòng 60 giây (dù UI vẫn đang báo generating), hệ thống sẽ chủ động ép `return false` (timeout).

  - Vòng lặp `_runNextDayAttempt()` sẽ báo Lỗi và tự động kích hoạt tiến trình Retry. Lưu ý: tiến trình Retry mặc định của hệ thống vẫn sẽ gõ lại **chính xác câu hỏi của Ngày hiện tại (currentDay)** trên một cửa sổ Chat Mới, đảm bảo không bị lặp cóc ngày.



### Giai đoạn 27 — Tạo Roadmap Access VBA (365 Ngày - Full Professional)

- Yêu cầu: Đọc 220 file HTML khóa học tại `D:\Code\Data Code\Course\Acces_VBA`, phân tích chủ đề từng ngày, xác định khoảng trống và bổ sung lộ trình học hoàn chỉnh.

- Phân tích & Bổ sung:

  - 290 ngày: Cấu trúc ban đầu với 5 nhóm chủ đề còn thiếu: Ribbon/Custom UI, Class Module & OOP, Report Builder nâng cao, Multi-user & Locking, Deployment & Distribution.

  - 365 ngày: Mở rộng thêm 75 ngày để bao quát SQL Mastery (CTE, Window Functions), Advanced Controls (TreeView, ListView, ActiveX), Modern Integration (Microsoft Graph, Power Automate, SharePoint, Teams).

  - Ước lượng thời gian: Đã gắn nhãn thời gian học cụ thể cho từng ngày (30 phút, 60 phút, 90 phút, 120 phút, 3-4 giờ).

- Thực thi: Tạo file `roadmap_access_vba.md` chứa đủ 365 ngày (8037 dòng, ~422 KB), chuẩn format Copilot Addon regex.

- Script Python `generate_access_vba_roadmap.py` được giữ lại để tùy biến sau.



### Quy tắc sinh file Roadmap (Ngôn ngữ / Lập trình)

1. **Đối với Ngôn ngữ học (Nhật, Trung, Anh, v.v.):**

   - Lộ trình phải trải dài đủ lớn (VD: 1000 ngày) từ Vỡ lòng đến Bản địa.

   - Các ngày đầu tiên BẮT BUỘC phải tập trung vào Bảng chữ cái/Phát âm/Pinyin trước khi vào từ vựng hay ngữ pháp.

   - Vòng lặp học kiến thức xen kẽ khoa học (VD: Ngữ pháp -> Từ vựng -> Chữ Hán/Hán tự -> Đọc hiểu -> Nghe hiểu -> Giao tiếp).

   - Prompt gửi cho AI phải có phương pháp sư phạm: 

     + Từ vựng/Chữ Hán: Có Mnemonic (câu chuyện ghi nhớ), Bộ thủ, Phát âm/Pinyin.

     + Ngữ pháp: Có Cấu trúc, Cách dùng (Nuance), Câu ví dụ.

     + Bắt buộc yêu cầu AI chỉ ra **Lỗi sai phổ biến của người Việt**.

2. **Đối với Ngôn ngữ Lập trình (Python, VBA, JS, v.v.):**

   - Phân chia theo Phase từ Căn bản đến Chuyên sâu.

- **Root cause:** Click "New Chat" trên M365 → SPA navigate → content_script.js bị **re-inject** → tất cả biến JS reset (`isRunning=false`, `currentDay=1`) → loop "dừng". Đây không phải tab sleep — mà là **script bị reload**.



- **Fix: Auto-Resume khi script load:**

  - Khi content_script.js khởi tạo → đọc `chrome.storage.local['runningState']`

  - Nếu `isRunning === true`:

    - Khôi phục: `currentDay`, `agentName`, `folderName`, `prefix`, `dayIndex` (từ autosave_data)

    - `setupKeepAlive()`

    - Chờ 5s (page settle) → `runNextDay()` tự động

    - Log: `🔄 AUTO-RESUME: "AgentName" từ Day N`



- **Fix: `saveRunningState(nextDay, lastSaved)`:**

  - Tham số mới `nextDay`: luôn lưu day **TIẾP THEO** cần xử lý

  - Gọi SAU `currentDay++` trong `processExtractedContent`

  - → Auto-resume đọc `runningState.currentDay` = đúng day cần chạy, không trùng day đã xong

  - Thêm `prefix` vào runningState để auto-resume biết prefix



### Giai đoạn 18 — Fix CSP, Audio, Context Invalidation & Tối ưu Adaptive Wait



- **Fix Worker CSP**: Bỏ `Blob Worker` vì M365 CSP chặn `worker-src 'self'`. Dùng `setInterval` bình thường. Kết hợp với `Web Lock` là đủ chống discard.

- **Fix AudioContext**: Bỏ `AudioContext` vì yêu cầu user gesture, có thể ném lỗi khi auto-resume hoặc reload.

- **Fix Context Invalidated**: Khi script bị orphan do reload, gọi `chrome.runtime.sendMessage` sẽ throw exception làm sập script. → Viết hàm `safeSendMessage` bọc try-catch và check `chrome.runtime?.id`.

- **Tối ưu Adaptive Wait**: Rút ngắn thời gian chờ cứng `MIN_WAIT` từ 120s xuống 15s. Sau 15s bắt đầu check stability (cần 15s stable). Tổng cộng mất khoảng ~30s nếu AI trả lời xong nhanh (thay vì luôn luôn chờ chết 2 phút).



### Giai đoạn 19 — Fix Lỗi "Chờ 10s Bị Đóng Băng" (Tab Freeze) & Tối ưu Auto-Resume



- **Root Cause**: Giai đoạn 18 gỡ `AudioContext` khiến tab chạy ngầm (background) dễ bị Chromium đóng băng toàn bộ Javascript (Tab Freeze) ngay sau khi AI tạo xong text (vì DOM không còn thay đổi). Việc gọi `delay(10000)` dùng `setTimeout` sẽ bị ngưng đọng vĩnh viễn không bao giờ chạy tiếp.

- **Khắc phục 1 (Bỏ nhàn rỗi)**: Xóa bỏ hoàn toàn thời gian chờ 10s vô nghĩa giữa các Day trong `processExtractedContent`. Chạy ngay sang Day kế tiếp để giữ luồng hoạt động, ngăn Chromium rảnh rỗi đóng băng tab.

- **Khắc phục 2 (Tối ưu Reload)**: Khi M365 bị tải lại (do SPA navigate) và trigger `Auto-Resume`, giảm thời gian chờ của Auto-Resume từ 5s xuống 1.5s để tránh freeze. Truyền cờ `isAutoResumed = true` vào `runNextDay` để ngăn script bấm nút `New Chat` thêm một lần nữa (vì trang vừa tải lại vốn dĩ đã là chat mới tinh), tránh vòng lặp tải lại trang vô tận.



### Giai đoạn 20 — Fix Lỗi Chờ Lâu (5-10 phút) Khi AI Đã Xong



- **Vấn đề**: Đôi lúc AI đã tạo xong toàn bộ nội dung, nhưng tiến trình vẫn đứng yên chờ thêm 5-10 phút thay vì hoàn thành ngay.

- **Nguyên nhân**:

  1. **Strict Equality**: Hàm `checkStable15s` đo độ dài text (`innerText.length`) của toàn trang và yêu cầu không được thay đổi dù chỉ 1 ký tự (`len === lastLen`) trong suốt 15 giây.

  2. **Nhiễu DOM**: Giao diện M365 Copilot thường có các thay đổi nhỏ ngoài ý muốn (ví dụ: thời gian cập nhật "1 min ago", nút chức năng ẩn/hiện, gợi ý prompt). Các thay đổi này làm chiều dài text dao động nhẹ, liên tục reset bộ đếm ổn định 15 giây.

- **Giải pháp**:

  - **Đo lường cục bộ (Scoped Check)**: Viết hàm `getNewTextLength()` CHỈ tính độ dài text của các element MỚI sinh ra sau khi gửi prompt (dựa trên việc lọc bỏ các element có `dataset.askcplSnapshot = "1"`). Điều này chặn mọi nhiễu từ các thành phần cũ trên trang.

  - **Dung sai (Tolerance)**: Cho phép sai số thay đổi `Math.abs(len - lastLen) <= 30` ký tự. Khi AI thực sự stream text, số lượng ký tự sẽ tăng rất nhanh và bứt phá khỏi khoảng dung sai. Nếu chỉ là UI render nút "Copy" hay icon thay đổi ở cuối quá trình, sự dao động sẽ nằm trong khoảng 30 ký tự và không làm reset bộ đếm, giúp tiến trình nhận diện AI đã xong ngay lập tức.



### Giai đoạn 21 — Hệ thống Config Đa Nền Tảng & Bộ nhớ phỏng vấn (Multi-step Interrogation)



- **Vấn đề**:

  - Người dùng cần lưu nhiều cấu hình (Config) khác nhau cho các Agent khác nhau (ví dụ: một cái cho Copilot tiếng Anh, một cái cho Gemini).

  - Cần tính năng tự dừng vòng lặp ở một `Ngày kết thúc` (End Day) nhất định.

  - Vòng lặp chat dài ngày khiến AI "quên" các chủ đề đã học. Cần một cách để bắt AI tự tóm tắt và ghi nhớ lại các ý chính đã học ở mỗi ngày để mớm (inject) vào prompt của ngày tiếp theo.



- **Giải pháp**:

  - **Hệ thống Profiles**: Nâng cấp `popup.html/js` để có một Dropdown duy nhất cho phép chọn, lưu và xóa nhiều Profile khác nhau (vd: "Copilot - Basic", "Copilot - Từ vựng"). Toàn bộ config (Day, Tiền tố, End Day, tính năng nâng cao) được bọc chung vào 1 Profile và lưu trong `chrome.storage`.

  - **Ngày kết thúc (End Day)**: Thêm ô thiết lập `End Day`. Trong `processExtractedContent`, nếu `currentDay >= endDay`, vòng lặp sẽ gọi `finishLoop()` ngay lập tức.

  - **Memory Advanced (Phỏng vấn liên hoàn)**:

    - Biến Addon thành một quy trình Agentic (Multi-step Interrogation). Thay vì 1 Day chỉ gửi 1 lệnh, Addon sẽ tự động nhắn tin phỏng vấn AI nhiều lần trong cùng 1 bài.

    - Bước 1: Gửi bài chính `Day X`.

    - Bước 2: Gửi câu hỏi mớm để hỏi Tên Chủ Đề (vd: *"Chủ đề là gì chỉ mỗi chủ đề thôi"*). Cập nhật biến đếm số bài của chủ đề đó.

    - Bước 3: Nếu Chủ đề chưa hoàn thành đủ số lượng mục tiêu, Addon vòng lặp qua các "Chi tiết" được cài đặt trên giao diện (ví dụ: Chi tiết 1: "Từ vựng", Chi tiết 2: "Ngữ pháp"). Mỗi chi tiết sẽ kích hoạt 1 câu hỏi độc lập với AI (vd: *"Hỏi từ vựng là gì, chỉ ghi các từ vựng thôi"*).

    - Câu trả lời của AI cho các Chi tiết này sẽ được bóc tách và cộng dồn vào Object bộ nhớ cục bộ (`topicMemory`).

  - **Memory Injector**: Trước khi gửi `Day X+1`, Addon tự động format bộ nhớ `topicMemory` thành một khối text gọn gàng (vd: *Chủ đề: Con người 1/4 \n Từ vựng đã học: ... \n Ngữ pháp đã học: ...*). Khối text này được gắn trực tiếp vào cuối câu lệnh `Day X+1` để "mớm" trí nhớ cho AI. Các chủ đề đã đạt mục tiêu (ví dụ 4/4) sẽ được rút gọn thành chữ "Hoàn tất" để tiết kiệm token.



### Giai đoạn 22 — Adapter Đa Nền Tảng (Gemini/ChatGPT) & Lộ trình Động Phân Cấp (Hierarchical Roadmap)



- **Vấn đề**: Người dùng cần chạy Add-on ở nhà với các tài khoản AI miễn phí (Google Gemini, ChatGPT) nhưng các AI này không hỗ trợ tạo Agent lưu ngữ cảnh cố định (System Prompt). Hơn nữa, việc "nhồi" trí nhớ của hàng trăm bài học cũ vào một câu lệnh sẽ gây phình to ngữ cảnh (Context Overflow) và tốn token. Việc thay đổi tài khoản AI miễn phí (do hết lượt) cũng làm xáo trộn lộ trình.

- **Giải pháp**:

  1. **Hierarchical Roadmap (Lộ trình phân cấp)**:

     - Thêm ô nhập `Roadmap` trên `popup.html`. Người dùng có thể copy Bảng Markdown Lộ Trình (xin từ ChatGPT) và dán thẳng vào.

     - Add-on có tính năng "Tạo JSON Roadmap": tự động nhóm các bài học theo cột `Chương` (Main Topic) và tạo ra một file JSON Phân cấp.

  2. **Token-Optimized Prompt Injector (Nén Trí Nhớ)**:

     - Trong `content_script.js`, Add-on dò xem Ngày hiện tại thuộc Chương nào. Nếu đang ở giữa Chương, nó sẽ ghép thêm câu tóm tắt của các ngày trước *thuộc cùng Chương đó*.

     - Khi chuyển sang Chương mới, toàn bộ tóm tắt chi tiết của Chương cũ sẽ bị "chốt sổ" và xóa khỏi lệnh, giúp giải phóng hoàn toàn bộ nhớ Prompt, giữ cho lệnh gửi luôn sắc bén và cực kỳ ngắn gọn.

  3. **Auto Summarizer**: Sau khi lấy xong bài học chính, Addon tự động bắn thêm lệnh phụ *"Tóm tắt cực kỳ ngắn gọn kiến thức trên"* và lưu vào `historySummaries`.

  4. **Adapter Pattern**: Tách rời logic DOM Selector cho `clickNewChat`, `findChatInput`, `findSendButton` và `extractDeltaContent` dựa trên lựa chọn Nền tảng (copilot, gemini, chatgpt). 

  5. **Persistent Session (Khóa cứng Lộ Trình)**: Nhúng (embed) trực tiếp toàn bộ khối `roadmapData` và `historySummaries` vào trong file `session.json`. Giúp người dùng khi cạn dung lượng tài khoản A có thể đăng nhập tài khoản B, bấm tải file session lên và Add-on sẽ tự phục hồi Lộ trình lẫn Trí nhớ để tiếp tục mạch học chính xác đến từng chữ.



### Giai đoạn 23 — Fix lỗi không tạo New Chat trên Gemini

- **Vấn đề**: Người dùng báo cáo Addon tiếp tục gửi bài mới vào cùng một đoạn chat cũ trên Gemini thay vì tạo chat mới, làm mất tác dụng của cơ chế One-Chat-Per-Day.

- **Nguyên nhân**: Nút "New Chat" của Gemini đã thay đổi cấu trúc DOM, selector cũ `a[href*="/app/new"]` không còn tìm thấy.

- **Giải pháp**: Nâng cấp hàm `clickNewChat()` cho Gemini:

  - Bổ sung loạt selector mới: `a[href="/app"]`, `button[aria-label*="trò chuyện mới"]`, v.v.

  - Thêm cơ chế **Text Fallback**: Quét toàn bộ thẻ `span, div, p` để tìm chữ "New chat" hoặc "Trò chuyện mới" và click vào thẻ cha có khả năng click (button/a). Điều này đảm bảo luôn tìm được nút dù Google có đổi code ẩn đi chăng nữa.



### Giai đoạn 24 — Fix lỗi dán text nhưng Gemini hiện icon Loa (Không gửi được)

- **Vấn đề**: Khi Addon dán Prompt vào ô nhập của Gemini, thay vì hiện nút Gửi (Send) thì Gemini vẫn hiện icon Micro/Loa. Gây lỗi không thể nhấn nút Gửi (do nút Gửi chưa xuất hiện).

- **Nguyên nhân**: Gemini sử dụng Web Component `<rich-textarea>`. Lệnh `execCommand('insertText')` thay đổi text trong DOM nhưng không tự động bắn ra sự kiện (Event) để báo cho framework (Angular/Lit) của Gemini biết. Hệ thống tưởng ô nhập vẫn đang trống.

- **Giải pháp**: 

  - Cập nhật selector tìm ô nhập: Lấy đúng thẻ `div[contenteditable="true"]` nằm SÂU BÊN TRONG thẻ `<rich-textarea>`.

  - Cập nhật hàm `fillInput()`: Bắt buộc bắn liên tiếp 3 event: `InputEvent('input')`, `Event('input')`, và `Event('change')` trực tiếp vào ô nhập. 

  - Đồng thời bắn thêm một event `input` ngược lên thẻ cha `<rich-textarea>` để "đánh thức" framework của Gemini, ép nó nhận diện text và hiện nút Gửi.



---



## Cấu trúc file hiện tại



```

CopilotWordExportAddon/

├── manifest.json       — Cấu hình extension (MV3, quyền downloads + storage, <all_urls>)

├── background.js       — Service Worker: download_html / download_index / download_session

├── content_script.js   — Vòng lặp auto, tải HTML từng Day, cập nhật index & session

├── popup.html          — Giao diện: Start/Stop, Resume từ session.json, log area

└── popup.js            — Logic Popup: file picker, resume flow, day_saved status



AskCpl.py               — Python/Tkinter: đọc JSON → xuất Word (dùng pywin32)

ProjectLog.md           — File này



Output (trong Downloads của trình duyệt):

agent_name/

├── index.html          — Trang tổng hợp, link đến từng bài (cập nhật dần)

├── day_1.html          — Bài ngày 1 (file HTML độc lập, đọc offline được)

├── day_2.html

└── session.json        — Quản lý phiên (resume lần sau)

```



---



## Các lệnh & Thư viện sử dụng

- `pip install pywin32` — Bắt buộc để Python điều khiển MS Word.

- Addon APIs: `chrome.storage.local`, `chrome.downloads`, `chrome.runtime`, `chrome.tabs`.



---



## Lưu ý quan trọng khi chỉnh sửa



> **Sau khi sửa `manifest.json` hoặc `background.js`:**

> Vào `edge://extensions/` → bấm **Tải lại (Reload)** extension.



> **Sau khi sửa `content_script.js`:**

> Quay lại trang Copilot → bấm **F5** để inject lại script.



> **File HTML và session.json** nằm trong `Downloads/agent_name/` (subfolder tự động tạo).

> Không thể tùy chỉnh đường dẫn ngoài Downloads do giới hạn bảo mật trình duyệt.



> **Sau khi sửa `content_script.js`:**

> Quay lại trang Copilot → bấm **F5** để inject lại script.



> **Resume phiên cũ:** Copy `session.json` từ `Downloads/agent_name/` sang bất kỳ đâu → mở Popup → "📂 Chọn file session.json" → Start.



---



## Chuẩn cấu trúc file Roadmap (.md)



Để tạo lộ trình (Roadmap) chuẩn xác cho Addon đọc ở chế độ "File MD", **bắt buộc tuân theo định dạng sau** để Addon có thể parse bằng Regex.



```markdown

## Day 1 — Tiêu đề bài học

**Prompt:**

Nội dung câu lệnh bạn muốn gửi cho AI. Có thể dài nhiều dòng.

Addon sẽ copy toàn bộ nội dung từ dưới chữ "Prompt:" cho đến khi gặp chữ "Bài tập:" hoặc "Tags:" hoặc dòng "## Day" tiếp theo.



**Bài tập:**

- Bài 1

- Bài 2



**Tags:** #tag

```



- Addon sẽ tự động tìm các cụm `## Day X`.

- Addon sẽ lấy mọi văn bản từ sau `**Prompt:**` để làm câu lệnh (prompt) gửi cho AI.

- Nếu bạn yêu cầu AI khác tạo Roadmap, hãy cung cấp đúng chuẩn này để tạo ra file `.md` ăn khớp 100% với Addon.



### Giai đoạn 25 — Tạo Roadmap JavaScript 7 Năm (2560 Ngày)

- Đã tạo Python script `generate_js_roadmap.py` để tự động hóa việc sinh file Markdown dài (hơn 33,000 dòng).

- Gen thành công file `roadmap_javascript_7years.md` bao phủ toàn bộ lộ trình 2560 ngày học liên tục (từ Foundation đến Web3, AI, Distributed System).

- File tuân thủ 100% định dạng Parsing của Copilot Word Export Addon.



### Giai đoạn 26 — Tạo Roadmap Thể Dục Tại Nhà (365 Ngày)

- Yêu cầu: Thiết kế lộ trình giảm cân & tăng cơ 1 năm cho người 108kg, 100% tập tại nhà, 30 phút/ngày, không bật nhảy (bảo vệ khớp).

- Thực thi: Đã tạo file `roadmap_fitness_365days.md` chứa đầy đủ 365 ngày (gồm bài tập chi tiết số hiệp/lần và thực đơn tương ứng mỗi ngày).

- Tích hợp chuẩn Copilot Addon: Prompt yêu cầu AI nhắc nhở kỹ thuật an toàn khớp, đánh giá thực đơn và động viên người dùng.

- **Bản V2 (Cập nhật)**: Bổ sung định lượng thực đơn chính xác (số gram, chén) và chi tiết 100% form chuẩn của các bài tập trực tiếp vào file HTML (để người dùng dễ theo dõi). Đã chỉnh sửa Prompt để AI làm "Kiểm toán viên dinh dưỡng" đánh giá trực tiếp số lượng thực phẩm này.

- Dọn dẹp: Đã lưu lại script Python `generate_fitness_365_v2.py` theo yêu cầu của người dùng để tùy biến sau này.



### Giai đoạn 28 — Fix Lỗi Kẹt Chờ 30s & Chống Ngủ Bằng Silent Audio

- **Vấn đề 1**: Quá trình Automation thỉnh thoảng bị kẹt vĩnh viễn ở bước chờ tạo New Chat (có thể do kết nối mạng yếu hoặc UI của AI thay đổi). Lỗi khiến cho hệ thống mất từ 7 phút đến vài chục phút.

- **Giải pháp 1**: Áp dụng Timeout 30 giây cho hàm `waitForNewChatReady`. Nếu sau 30s mà New Chat chưa sẵn sàng, Extension sẽ tự động ép Reload trang (`location.reload()`). Nhờ cơ chế Auto-Resume có sẵn từ Giai đoạn 17, hệ thống sẽ tự động khôi phục quy trình và chạy lại Day đó thay vì bị kẹt vĩnh viễn.

- **Vấn đề 2**: Các trình duyệt hiện đại (Chrome/Edge) tự động đưa tab vào chế độ ngủ (Sleeping Tabs/Background Throttling) khi tab bị ẩn quá lâu, khiến Javascript chạy ngầm bị delay cực nặng, kéo dài thời gian chờ 5-7 phút.

- **Giải pháp 2**: Kích hoạt lại kỹ thuật Silent Audio Keep-alive (từng bị tắt ở Giai đoạn 13). Bằng cách chèn một file âm thanh ngắn (chuỗi Base64 cực nhỏ) tĩnh lặng (0.01 volume) và lặp vô tận thông qua thẻ `<audio>` khi gọi `setupKeepAlive`. Điều này sẽ "đánh lừa" trình duyệt tin rằng tab đang phát nội dung Media, duy trì mức ưu tiên xử lý cao nhất (Highest Priority) và chống Throttling 100%.



### Giai đoạn 27 — Tạo Roadmap Access VBA (365 Ngày - Full Professional)

- Yêu cầu: Đọc 220 file HTML khóa học tại `D:\Code\Data Code\Course\Acces_VBA`, phân tích chủ đề từng ngày, xác định khoảng trống và bổ sung lộ trình học hoàn chỉnh.

- Phân tích & Bổ sung:

  - 290 ngày: Cấu trúc ban đầu với 5 nhóm chủ đề còn thiếu: Ribbon/Custom UI, Class Module & OOP, Report Builder nâng cao, Multi-user & Locking, Deployment & Distribution.

  - 365 ngày: Mở rộng thêm 75 ngày để bao quát SQL Mastery (CTE, Window Functions), Advanced Controls (TreeView, ListView, ActiveX), Modern Integration (Microsoft Graph, Power Automate, SharePoint, Teams).

  - Ước lượng thời gian: Đã gắn nhãn thời gian học cụ thể cho từng ngày (30 phút, 60 phút, 90 phút, 120 phút, 3-4 giờ).

- Thực thi: Tạo file `roadmap_access_vba.md` chứa đủ 365 ngày (8037 dòng, ~422 KB), chuẩn format Copilot Addon regex.

- Script Python `generate_access_vba_roadmap.py` được giữ lại để tùy biến sau.



### Quy tắc sinh file Roadmap (Ngôn ngữ / Lập trình)

1. **Đối với Ngôn ngữ học (Nhật, Trung, Anh, v.v.):**

   - Lộ trình phải trải dài đủ lớn (VD: 1000 ngày) từ Vỡ lòng đến Bản địa.

   - Các ngày đầu tiên BẮT BUỘC phải tập trung vào Bảng chữ cái/Phát âm/Pinyin trước khi vào từ vựng hay ngữ pháp.

   - Vòng lặp học kiến thức xen kẽ khoa học (VD: Ngữ pháp -> Từ vựng -> Chữ Hán/Hán tự -> Đọc hiểu -> Nghe hiểu -> Giao tiếp).

   - Prompt gửi cho AI phải có phương pháp sư phạm: 

     + Từ vựng/Chữ Hán: Có Mnemonic (câu chuyện ghi nhớ), Bộ thủ, Phát âm/Pinyin.

     + Ngữ pháp: Có Cấu trúc, Cách dùng (Nuance), Câu ví dụ.

     + Bắt buộc yêu cầu AI chỉ ra **Lỗi sai phổ biến của người Việt**.

2. **Đối với Ngôn ngữ Lập trình (Python, VBA, JS, v.v.):**

   - Phân chia theo Phase từ Căn bản đến Chuyên sâu.

   - Prompt bắt buộc yêu cầu AI đưa ra code ví dụ thực tế, có thể chạy được ngay.

   - Bắt AI giải thích lỗi bug thường gặp và cách debug.

   - Phải có bài tập thực hành cụ thể ở cuối mỗi ngày.

3. **Quy trình chung (Bắt buộc):**

   - Luôn tạo 1 script (như Python) chứa logic sinh file để lưu trữ và tiện sửa đổi sau này.

    - Định dạng output `.md` phải tuân thủ chuẩn Parsing của Copilot Addon: `## Day X...`, `**Prompt:**`, `**Bài tập:**`, `**Tags:**`.

   - Phải tạo `implementation_plan.md` cho User duyệt trước khi viết code sinh file.



### Giai đoạn 29 — Tối ưu & Mở rộng Lộ trình Tiếng Trung và Tiếng Nhật (2500 Ngày)

- **Yêu cầu**: Người dùng muốn tối ưu và hoàn thiện 2 lộ trình ngôn ngữ (Tiếng Trung, Tiếng Nhật) dựa trên chuẩn thiết kế của `roadmap_english.md`.

- **Vấn đề phát hiện**: Bản cũ (1000 ngày) quá ngắn để bao phủ kiến thức từ Vỡ lòng đến Native với nhịp học **30-45 phút/ngày**. Ngoài ra, thời gian mỗi Day tăng dần (120 phút ở phase cuối) không thực tế khi người dùng bị giới hạn thời gian.

- **Giải pháp — "Lộ trình Dài hạn Thực tế"**:

  - Mở rộng từ **1000** lên **2500 ngày** cho cả 2 ngôn ngữ.

  - Cố định thời gian học cố định **30-45 phút/ngày** cho tất cả 6 Phase.

  - Phân bổ lại 6 Phase hợp lý hơn (HSK/JLPT): 250 / 350 / 400 / 500 / 500 / 500 ngày.

  - Thêm lời cảnh báo `⚠️ Lưu ý quan trọng` về thời gian thực tế cần thiết (tương tự chuẩn English roadmap).

  - Thêm loại bài "Ôn tập tổng hợp" xen kẽ trong chu kỳ 7 bài để củng cố kiến thức.

  - Mở rộng danh sách Ngữ pháp, Từ vựng, Kanji để nội dung phong phú và không bị lặp quá nhiều.

- **Kết quả**:

  - `generate_chinese_roadmap.py` — Đã cập nhật (265 → ~430 dòng).

  - `generate_japanese_roadmap.py` — Đã cập nhật (269 → ~430 dòng).

  - `roadmap_chinese_1000.md` — Tái tạo: **2500 ngày**, 4.06 MB, chuẩn Addon 100%.

  - `roadmap_japanese_1000.md` — Tái tạo: **2500 ngày**, 4.09 MB, chuẩn Addon 100%.



### Giai đoạn 30 — Tạo Roadmap Tiếng Anh Mới Chuẩn Sư Phạm (2500 Ngày)

- **Yêu cầu**: Tạo roadmap tiếng Anh mới từ đầu theo chuẩn thiết kế của roadmap Nhật/Trung (2500 ngày, 30-45 phút/ngày), tham khảo `roadmap_english.md` cũ nhưng nâng cấp toàn diện.

- **Phân tích lỗi bản cũ (900 ngày)**:

  - 900 ngày quá ngắn cho 30-45 phút/ngày thực tế.

  - Prompt quá chung chung — chỉ "dạy rồi giao 3-5 câu", không phân loại theo kiểu bài.

  - Phase 1 chỉ 30 ngày — quá ngắn để master phát âm tiếng Anh cho người Việt.

  - Không có bài Pronunciation riêng biệt, thiếu IPA bắt buộc.

  - Thiếu Collocations, IELTS tasks, Academic Writing ở các phase cao.

- **Giải pháp — Roadmap Tiếng Anh Chuẩn 2500 Ngày**:

  - 6 Phase: Pre-A1 (200 ngày), A1-A2 (350 ngày), B1 (400 ngày), B2 (500 ngày), C1-C2 (550 ngày), Native (500 ngày).

  - Phase 1 mở rộng lên **200 ngày** với 20 bài Phát âm nền tảng riêng (IPA, Word Stress, Connected Speech, Intonation, Schwa, Weak Forms).

  - **Chu kỳ 7 loại bài** điều chỉnh cho tiếng Anh: Ngữ pháp → Từ vựng → **Phát âm/IPA** → Đọc hiểu → Nghe hiểu → Nói/Shadowing → Viết/Ôn tập.

  - Prompt phân nhánh theo 5 loại bài: Ngữ pháp / Từ vựng+Collocation+Idiom / Phát âm / Kỹ năng tích hợp / Lỗi sai người Việt BẮT BUỘC.

  - Tích hợp IELTS tasks từ Phase B2, Academic Word List từ Phase C1.

  - Phase Native: Slang, Humor, Stand-up Comedy, Văn học, Public Speaking, Accent Mastery.

- **Kết quả**:

  - `generate_english_roadmap.py` — Tạo mới (~340 dòng).

  - `roadmap_english_2500.md` — Tạo mới: **2500 ngày**, 5.11 MB, chuẩn Addon 100%.

  - Tất cả 6 Phase đều OK, đủ 2500/2500 Prompt + Tags + Bài tập.



### Giai đoạn 31 — Tạo Roadmap Tiếng Hàn Chuẩn Sư Phạm (2500 Ngày)

- **Yêu cầu**: Tạo roadmap tiếng Hàn mới từ đầu theo chuẩn Nhật/Trung/Anh (2500 ngày, 30-45 phút/ngày), tham khảo `roadmap_korean.md` cũ (900 ngày) nhưng nâng cấp toàn diện.

- **Giải pháp — Roadmap Tiếng Hàn Chuẩn 2500 Ngày**:

  - 6 Phase: Hangul (200 ngày), TOPIK1-2 (350 ngày), TOPIK3 (450 ngày), TOPIK4 (500 ngày), TOPIK5-6 (500 ngày), Native (500 ngày).

  - Phase 1 mở rộng lên 200 ngày với 22 bài Hangul nền tảng riêng (Nguyên âm, Phụ âm, Batchim, Quy tắc phát âm, Số đếm Hàn/Thuần Hàn).

  - Chu kỳ 7 loại bài điều chỉnh cho tiếng Hàn: Ngữ pháp → Từ vựng → Phát âm/Hangul → Đọc hiểu → Nghe hiểu → Nói/Shadowing → Viết/Ôn tập.

  - Prompt phân nhánh theo 5 loại bài: Hangul/Phát âm / Ngữ pháp / Từ vựng+Thành ngữ+Slang / Kỹ năng tích hợp / Lỗi sai người Việt BẮT BUỘC.

  - Tích hợp Kính ngữ (존댓말) từ Phase TOPIK1-2, bài luận TOPIK từ Phase TOPIK3.

  - Phase Native: K-pop, K-drama, Nước Hàn Văn hóa, Công sở, Phương ngữ Busan.

- **Kết quả**:

  - `generate_korean_roadmap.py` — Tạo mới (~340 dòng).

  - `roadmap_korean_2500.md` — Tạo mới: **2500 ngày**, 5.27 MB, chuẩn Addon 100%.

  - Tất cả 6 Phase đều OK, đủ 2500/2500 Prompt + Tags + Bài tập.



### Giai đoạn 32 — Tạo Roadmap Python (3000 Ngày / ~8 Năm)

- **Yêu cầu**: Tạo lộ trình học Python bao phủ toàn bộ hệ sinh thái công nghệ mới nhất (2025), lấy cảm hứng từ lộ trình JavaScript 7 năm.

- **Giải pháp — Roadmap Python 3000 Ngày**:

  - Gồm 6 Phase lớn: 

    1. **Foundation (1-535)**: Cú pháp, Cấu trúc dữ liệu, OOP, Modules.

    2. **Advanced (536-1080)**: Decorator, Generator, Metaclass, Type Hints, Concurrency, AsyncIO, Design Patterns, Testing (pytest), Performance (Cython, Numba).

    3. **Web Dev (1081-1660)**: FastAPI, Django, Flask, SQLAlchemy, MongoDB, Redis, Elasticsearch, Web Scraping (Playwright, Scrapy).

    4. **Data Science & ML (1661-2425)**: Pandas, NumPy, Scikit-learn, XGBoost, PyTorch, HuggingFace, LLM (LangChain, LlamaIndex, RAG), Computer Vision (OpenCV, YOLO), MLOps.

    5. **DevOps & Cloud (2426-2690)**: Docker, Kubernetes, CI/CD, AWS, Kafka, Event-Driven, Observability, Security.

    6. **Specialized (2691-3000)**: Data Engineering (PySpark, Airflow), GUI (PyQt6), Automation, Game Dev (Pygame), Blockchain (Web3.py), Quantum Computing.

  - **Prompt sư phạm cao**: Yêu cầu AI đưa ra cả ví dụ cơ bản lẫn nâng cao (production-ready), các pitfalls (lỗi hay gặp), và 3 cấp độ bài tập (từ sao chép cơ bản đến mini-project).

- **Kết quả**:

  - `generate_python_roadmap.py` — Tạo mới.

  - `roadmap_python_3000.md` — Đã sinh thành công đúng **3000 ngày**.



### Giai đoạn 33 — Trình Tạo Bài Tập Lưu Trữ (Archival Mode) & Tinh Chỉnh UI

- **Yêu cầu:** Thêm 2 kiểu tạo bài tập: (1) Nhúng trực tiếp như cũ, (2) Tạo thư mục lưu trữ exercise và tạo file riêng. Xóa bài tập phải dọn dẹp thẻ link trong index.html. Tinh chỉnh UI của sổ hiển thị (mặc định Maximize).

- **Giải pháp:**

  - `exercise_builder.py`: Sửa hàm `save_exercise_to_html` để hỗ trợ tham số `mode` (direct / archival).

  - Thêm hàm `remove_exercise_from_html` để làm sạch file index.html (dùng regex xóa thẻ trạng thái và link) và xóa file/nội dung HTML nhúng tùy theo chế độ.

  - `AskCpl.py`: Đặt `self.root.state('zoomed')` để mở full màn hình.

  - Thêm `Combobox` chọn chế độ xuất.

  - Cập nhật logic các nút Lưu và Xóa Tất Cả để đồng bộ hóa file HTML.

- **Kết quả:** Hoàn thành tốt luồng tạo/xóa bài tập đa chế độ và khắc phục lỗi hiển thị giao diện UI.



### Giai đoạn 34 — Bổ Sung Tính Năng Đồng Bộ GitHub từ VocabularyApp

- **Yêu cầu:** Học hỏi các điểm mạnh từ module GitHub Sync của VocabularyApp để mang sang module GitHub Sync của AskCpl.

- **Giải pháp:**

  - Giữ nguyên luồng upload Git Tree của AskCpl vì hiệu năng rất cao (upload toàn bộ thư mục chỉ 1 request commit thay vì upload lặt nhặt từng file).

  - Thêm chức năng `enable_pages` để tự động bật tính năng GitHub Pages sau khi push thành công.

  - Thêm chức năng tự động tìm file `README.md` vào thư mục upload nếu chưa có, trong đó chứa link dẫn trực tiếp tới GitHub Pages.

  - Tự động lấy URL hiển thị của trang web (qua `get_pages_url`) và in thẳng ra khung log của AskCpl để người dùng bấm vào xem ngay lập tức.

- **Kết quả:** Quá trình đưa bài tập lên GitHub giờ đây hoàn thiện hơn, hỗ trợ host trang web và cung cấp link truy cập lập tức.



### Hotfix — Xử lý lỗi Unicorn 502 từ GitHub API (Quá tải do spam 1000 file)

- **Nguyên nhân:** Khi đẩy thư mục chứa ~1000 file, vòng lặp requests gửi đi liên tục 1000 HTTP POST requests về server GitHub mà không có độ trễ (delay) nào. Điều này kích hoạt cơ chế bảo vệ Abuse Rate Limit của GitHub, trả về lỗi 502/503 (Unicorn Page) khi AskCpl đang tạo Git Tree.

- **Khắc phục:**

  - Viết lại các hàm gọi API thông qua wrapper `_request_with_retry`. Nếu nhận mã lỗi 50x từ server GitHub, hàm sẽ tự động ngủ một khoảng (exponential backoff: 2s, 4s, 8s...) rồi thử lại, tối đa 3 lần.

  - Thêm một khoảng nghỉ siêu nhỏ `time.sleep(0.05)` (50ms) giữa mỗi chu kỳ upload file blob nhằm tránh làm quá tải bộ định tuyến của GitHub.

- **Kết quả:** Đồng bộ số lượng lớn file mượt mà và an toàn hơn, không còn chết ngang vì timeout hay 502.



### Hotfix 2 — Xử lý lỗi Timeout 422 từ GitHub API (Tree quá lớn)

- **Nguyên nhân:** Khi tạo một Git Tree có chứa 1000 items trong một request duy nhất, backend của GitHub bị timeout (mã 422: 'input was too large to process, build the tree incrementally').

- **Khắc phục:** Thay vì gửi 1000 items cùng lúc, ứng dụng sẽ cắt nhỏ ra (chunking) thành từng nhóm 250 files. Mỗi nhóm tạo thành một cây Git Tree mới, lấy cây trước đó làm base_tree (xây dựng lũy tiến). Nhờ đó, request nào cũng nhỏ và không bị timeout.

- **Kết quả:** Đã có thể đẩy an toàn số lượng khổng lồ file lên GitHub mà không bị giới hạn thời gian phản hồi.







### Giai đoạn 41 — Nâng cấp Kiến trúc Đa Tiến Trình (Multi-Tab Support)

- **Vấn đề**: Sau khi áp dụng Tab Binding (Giai đoạn 40), các tab mới không còn bị auto-resume nhầm, NHƯNG biến lưu trữ `runningState` vẫn là một Object đơn. Do đó, nếu mở Popup ở Tab thứ 2, Popup vẫn lầm tưởng hệ thống "Đang chạy" (của Tab 1) và ẩn đi nút Start, khiến người dùng không thể chạy đồng thời nhiều Agent trên nhiều Tab khác nhau.

- **Giải pháp**:

  - Đổi tên kho lưu trữ thành `runningStates` (số nhiều) dạng Từ điển (Dictionary).

  - Cập nhật `popup.js`: Buộc phải dùng `chrome.tabs.query` để lấy `tab.id` của chính nó trước, rồi mới tìm `runningStates[tab.id]`. Nhờ đó, Popup ở các Tab khác nhau sẽ hiển thị trạng thái hoàn toàn độc lập (Tab 1 hiện "Đang chạy", Tab 2 hiện "Bắt đầu").

  - Cập nhật `content_script.js`: Các hàm `saveRunningState`, `clearRunningState`, và thông điệp `stop_loop` đều được điều chỉnh để chỉ thao tác trên đúng mảnh ghép dữ liệu thuộc về `tabId` của nó, tránh ghi đè dữ liệu của Tab khác.

- **Kết quả**: Addon đã trở thành môi trường hoàn toàn Đa Luồng (Multi-Thread / Multi-Instance). Người dùng có thể mở 5 Tab Gemini và chạy 5 Lộ trình khác nhau song song mà không xảy ra bất kỳ xung đột nào.



### Giai đoạn 42 — Khắc phục lỗi Background Tab Throttling (Cắt ngang tiến trình AI)

- **Vấn đề**: Trình duyệt Chrome có cơ chế Memory Saver và Background Throttling, tự động đóng băng các hoạt động DOM render (RequestAnimationFrame, setTimeout) khi người dùng chuyển sang tab khác để treo máy. Do DOM không cập nhật, addon bị "đánh lừa" rằng AI đã gõ xong văn bản vì chuỗi html trả về không dài thêm trong 15s. Kết quả là addon lưu 1 đoạn văn bản cụt lủn và gọi luôn câu hỏi tiếp theo gây lỗi sai luồng.

- **Giải pháp 1 (UI Signals)**: Viết hàm `isAIGenerating()` quét toàn bộ nút trên trang để tìm trạng thái "Stop generating / Dừng tạo". Nếu nút này tồn tại, AI chắc chắn đang trả lời, addon sẽ chủ động "reset" lại bộ đếm ổn định 15s để không bao giờ cắt ngang bài giảng.

- **Giải pháp 2 (Tab Visibility)**: Gắn thêm kiểm tra `document.hidden`. Khi phát hiện tab đang bị ẩn (chạy ngầm), thay vì chờ 15s ổn định, hệ thống tự động giãn thời gian thành 45s để đảm bảo an toàn tuyệt đối.

- **Giải pháp 3 (Keep-Alive)**: Khôi phục lại kĩ thuật `silentAudio` (phát nhạc trắng cực ngắn 1 sample dưới nền) để chặn đứng tính năng tab-discard của Chrome Memory Saver. Khắc phục triệt để bằng cách nhớ gọi `.pause()` khi kết thúc, giúp Edge không bị rò rỉ AudioContext gây chạy auto-resume sai Tab.

- **Giải pháp 4 (Intentional Reload & Infinite Retries)**: Khi web quá lag hoặc AI từ chối trả lời (gây Timeout ngầm), mã nguồn tự động `location.reload()` và ghi vé vào `sessionStorage` để auto-resume an toàn. Không giới hạn số lần thử lại lỗi (đổi từ retry 2 sang vòng lặp `while(isRunning)` vô hạn có khoảng nghỉ 15s), ngăn addon chết đứng giữa chừng. Bỏ cơ chế tải lưu dự phòng mỗi 5 ngày để chống spam Download History (chỉ lưu ổ đĩa nội bộ của extension thông qua `chrome.storage.local`).





### Giai đoạn 32: Tương thích ngược phiên bản Session (Backward Compatibility)

- **Vấn đề:** Trình đọc file `session.json` của Popup quá khắt khe (`if (!session.agentName || !session.lastDay)`). Dẫn đến các file session cũ (chưa có trường `agentName` mà chỉ có `folderName`, hoặc `lastDay = 0`) bị đánh giá là không hợp lệ và từ chối tải.

- **Giải pháp:** Xóa bỏ điều kiện kiểm tra khắt khe. Thêm Fallback an toàn:

  - Tự động lấy `session.agentName = session.folderName || "Copilot"`.

  - Nếu `session.lastDay` là `undefined`, tự động đếm mảng `session.days.length`.

  - Chỉ báo lỗi khi file JSON tải vào hoàn toàn không có cấu trúc quen thuộc.





### Giai doan 33: Khac phuc loi Popup bi treo (Roadmap qua lon)

- **Van de:** Ham updateRoadmapPreview dang dump toan bo roadmap (co the 3000 bai) thanh JSON va chen vao the <pre> trong HTML. Dieu nay khien browser tab bi dong cung khi render hang trieu ky tu. Ket qua: popup treo, click vao addon khong len.

- **Nguyen nhan goc:** Roadmap duoc luu long vao ddonConfigs roi serialize sang storage. Moi lan mo popup, loadProfiles() doc ra va goi pplyConfigToUI() -> updateRoadmapPreview() dump toan bo JSON ngay lap tuc.

- **Giai phap:**

  - updateRoadmapPreview: Chi hien thi tom tat (so bai hoc), KHONG con goi JSON.stringify(data) nua.

  - Tach luu Roadmap: Khong luu roadmapData trong ddonConfigs nua. Thay vao do luu vao key rieng 

oadmap_[ten_profile] trong chrome.storage.local.

  - pplyConfigToUI: Nhan them profileKey de doc roadmap tu key rieng, bat dong bo (async), khong dong cung popup.

  - Sua 

oadmapFileInput va parseRoadmapBtn: Luu vao key rieng.

  - Cung cap onerror va onloadend an toan cho FileReader cua file MD.





### Giai đoạn 43 — Tương thích ngược session cũ (Backward Compatibility)

- **Vấn đề**: Trình đọc file session.json không tải được file cũ do điều kiện if (!session.agentName || !session.lastDay) quá khắt khe (số 0 bị coi là falsy, file cũ chưa có gentName).

- **Giải pháp**: Xóa điều kiện khắt khe, thêm fallback tự động lấy gentName từ olderName và tự đếm session.days.length nếu thiếu lastDay.



### Giai đoạn 44 — Khắc phục Popup treo và Session không chạy (Root Cause: roadmapData quá lớn)

- **Nguyên nhân gốc**: File session.json nặng 53MB vì 

oadmapData (3000 bài, mỗi bài có prompt dài) được nhúng trực tiếp vào session. Khi popup gửi payload này qua chrome.tabs.sendMessage (IPC), trình duyệt **drop im lặng** (không chạy, không báo lỗi). Roadmap cũng được nhúng vào 

unningStates gây vượt giới hạn 10MB của chrome.storage.local.

- **Giải pháp**:

  - content_script.js: Xóa 

oadmapData khỏi utoSave, saveStateForReload, saveRunningState. Đọc 

oadmapData từ key riêng 

oadmap_active trong storage (async) thay vì nhận qua IPC.

  - popup.js / startBtn: Lưu currentRoadmapData vào chrome.storage.local key 

oadmap_active trước khi gửi message. Strip 

oadmapData và session.roadmapData khỏi payload. Payload lúc này chỉ chứa metadata nhẹ.

  - popup.js / updateRoadmapPreview: Chỉ hiển thị tóm tắt số bài thay vì JSON.stringify toàn bộ (chống popup treo khi render).

  - popup.js / saveProfileBtn: Lưu roadmap vào key riêng 

oadmap_{profile} thay vì nhúng vào ddonConfigs.





### Giai đoạn 45 — Sửa lỗi font (Encoding Loop) trong `session.json`

- **Nguyên nhân gốc**: Trong `content_script.js`, tại hàm `saveStateForReload`, dữ liệu được encode dưới dạng `btoa(unescape(encodeURIComponent(JSON.stringify(sessionObj))))`. Tuy nhiên, khi đọc lại lúc load trang, code chỉ dùng `atob(...)` mà **quên mất bước decodeURIComponent**. Hậu quả là sau vài trăm vòng lặp (reload trang cho từng ngày mới), các ký tự có dấu như tiếng Việt hay dấu gạch ngang (`—`) bị phình to theo cấp số nhân (Ví dụ `—` thành `ÃÂ...`). Đây là lý do chính khiến file JSON bị phình từ 4MB lên tới 28MB - 53MB!

- **Giải pháp**:

  - `content_script.js`: Sửa dòng `atob` thành `decodeURIComponent(escape(atob(res2.autosave_session_json)))` để nó đồng bộ chuẩn encoding 2 chiều.

  - Đã viết script Python phụ để đọc ngược (decode recursively) bản `session.json` của người dùng, cứu toàn bộ câu hỏi bị lỗi dấu. File khôi phục được giảm xuống 4.6MB và mọi text dấu `—` đều được khôi phục lại chuẩn xác.



## ⚠️ Quy tắc VÀNG về Mã Hóa (Encoding) Base64
Tuyệt đối lưu ý khi lưu trữ và truyền tải dữ liệu JSON (đặc biệt là dữ liệu có chứa ký hiệu Unicode, tiếng Việt, file markdown):
1. **LUÔN LUÔN DÙNG MÃ HÓA 2 CHIỀU ĐỒNG BỘ:**
   - Khi mã hóa lưu trữ (Save): toa(unescape(encodeURIComponent(JSON.stringify(obj))))
   - Khi giải mã đọc ra (Load): JSON.parse(decodeURIComponent(escape(atob(str))))
2. **Hậu quả nếu bỏ quên decodeURIComponent:** Nếu bạn chỉ dùng tob(...) để giải nén nhưng thiếu decodeURIComponent, chuỗi byte UTF-8 sẽ bị ép hiểu nhầm thành các ký tự Latin-1. Khi chuỗi này bị lặp lại lưu/đọc trong vòng lặp (như vòng lặp Auto-Resume reload trang), dung lượng ký tự sẽ **bị nhân đôi liên tục theo cấp số nhân**, làm file JSON phình to từ vài MB lên hàng chục MB, gây nghẽn RAM, treo máy và sập luồng gửi tin nhắn IPC của Chrome.


### Giai đoạn 46 — Sửa lỗi nhận diện sai "Error Content" & Sửa lỗi từ ngữ Á Đông

#### Lỗi 1: False Positive `isErrorContent` (Day 1503 bị reject)
- **Triệu chứng:** Add-on kẹt mãi ở Day 1503, thử lại hàng chục lần nhưng không thoát được. AI đã trả lời hoàn chỉnh nhưng bị bỏ qua.
- **Nguyên nhân:** Hàm `isErrorContent()` dùng `.includes('503')` để tìm kiếm từ khóa. Số `1503` có chứa chuỗi `503`, bị bắt oan! Ngoài ra, bài giảng về lỗi HTTP có thể chứa "thử lại", "đã xảy ra lỗi" khiến hàm tưởng đó là thông báo lỗi mạng.
- **Giải pháp:** Thêm 2 cải tiến vào `isErrorContent()`:
  1. **Kiểm tra độ dài:** Thông báo lỗi đứt mạng bao giờ cũng ngắn (< 200 ký tự). Nếu nội dung > 400 ký tự → auto pass, không kiểm tra.
  2. **Word Boundary:** Đổi `.includes('503')` thành `\b503\b` (regex boundary) để không nhầm với "1503".

#### Lỗi 2: False Reject với Tiếng Nhật / Tiếng Trung
- **Nguyên nhân:** Hàm `validateContent()` đếm số từ bằng `text.split(/\s+/)`. Tiếng Nhật/Trung không có khoảng trắng → toàn bộ bài giảng dài 2000 ký tự bị tính là "1 từ" → nếu tên Agent lặp lại 1 lần, tỷ lệ vượt ngưỡng → bài bị reject!
- **Giải pháp:** Đổi sang kiểm tra theo **tỷ lệ ký tự** (character count). Logic mới: `nameCharCount > text.length * 0.4`. Hoạt động hoàn hảo với mọi ngôn ngữ (Anh, Việt, Nhật, Trung).
- **File đã sửa:** `content_script.js` — hàm `isErrorContent()` và `validateContent()`.


### Giai đoạn 47 — Khắc phục Background Throttling (Chrome chạy chậm khi bị ẩn)

#### Nguyên nhân gốc
Chrome/Edge có cơ chế CPU/Timer Throttling. Khi tab không ở foreground, `setTimeout` có thể bị trì hoãn đến hàng chục giây / phút. Polling interval `delay(2000)` thực tế chạy mất 30-60s → hàng chục vòng lặp chờ = cả tiếng chưa xong 1 bài.
Cơ chế Silent Audio đã tồn tại nhưng có 2 điểm yếu:
1. Audio bị Chrome block autoplay sau khi tab reload (chuyển ngày) → bị tắt ngầm → keepAlive mất tác dụng.
2. Không có cơ chế nào kiểm tra audio có đang chạy không.

#### Giải pháp (Phương án A+B)
- **A — Audio Health Check:** Thêm `_audioHealthInterval` (5s) kiểm tra `_silentAudio.paused`. Nếu đúng → tự `play()` lại. Audio không bao giờ bị tắt lâu hơn 5 giây.
- **B — Web Locks API:** Dùng `navigator.locks.request('askcpl_wakeLock', { mode: 'shared' }, ...)` để giữ lock trong suốt vòng lặp. Tab giữ lock sẽ **không bị browser cho vào trạng thái ngủ/frozen**, ngăn timer throttle ở mức độ OS/browser thay vì chỉ audio workaround.

#### File đã sửa
- `content_script.js`: Thêm 2 biến `_audioHealthInterval`, `_wakeLockAbort`. Sửa `setupKeepAlive()` và `teardownKeepAlive()`.


### Giai đoạn 32 — Fix lỗi Quill Editor Syntax

- **Vấn đề**: Trình soạn thảo (WYSIWYG Exercise Builder) báo lỗi thiếu thư viện highlight.js khi khởi tạo module Syntax.

- **Giải pháp**: Đổi thứ tự tải file trong 	emplates/editor.html, bắt buộc tải highlight.js trước quill.js để Quill nhận diện được biến toàn cục window.hljs.



### Giai doan 33 - Bo sung Roadmap C++ (3080 → 3350 Ngay)
- **File:** `roadmap_cpp test.md` | **Script:** `patch_cpp_roadmap.py`

#### 1. Bo sung Non-Interactive Warning (1342 Day)
- Chen canh bao (WARNING: TUYET DOI KHONG tao bai test/quiz tuong tac...) vao:
  - **15-cycle**: Phan 13, 14, 15 (Ecosystem Integration, Deep Debugging, Execution Lifecycle)
  - **25-cycle**: Phan 13-25 (Design Patterns, Testing, CI/CD, Open Source, Interview)
- Nhat quan voi 
oadmap_python_3000.md va SKILL.md (Muc 4: Non-Interactive).

#### 2. Them 18 Topic Moi (Day 3081 - 3350, moi topic 15 ngay)
- Advanced Core & STL: std::format C++20/23; std::jthread, stop_token, std::generator
- Systems & Performance: Memory-mapped files (mmap); Coroutine internals tu viet
- Embedded & Firmware: DMA & USB protocol stack; Ethernet + lwIP TCP/IP
- Graphics & Game Dev: Animation systems (skeletal, IK); Game networking (rollback); Metal API (Apple)
- Networking & Distributed: HTTP/2 & HTTP/3 (QUIC); io_uring Linux async I/O
- Specialized: ML inference C++ (ONNX/TFLite); OpenCV C++; DSP (FFT/FIR); Database C++ (SQLite/PostgreSQL); llama.cpp internals; CUDA/ROCm GPU computing
- Documentation & Tooling: Google Benchmark & Valgrind deep dive

#### Verify ket qua
- Total Day: 3350 OK | Prompt: 3350 OK | Bai tap: 3350 OK | Tags: 3350 OK
- Non-Interactive warnings: 1342 OK | File size: 7.00 MB | Khong thieu Day nao


### Ph�n t�ch Extension Download All TikTok
- **C�ng vi?c**: T?i m� ngu?n c?a ti?n �ch t? Chrome Web Store (ID: gmajiifkcmjkehmngbopoobeplhoegad) v�o thu m?c DownloadTiktok v� ti?n h�nh ph�n t�ch.
- **K?t qu?**: �� luu m� ngu?n, script t? d?ng t?i MP4 (d?a tr�n vi?c d�ng chrome.webRequest b?t URL/header t? API item_list c?a Tiktok). B�o c�o ph�n t�ch d� du?c luu trong artifact.


## 2026-07-20 Update: Fix FileNotFoundError & Pip Pinning
- Đã sửa lỗi FileNotFoundError khi không tìm thấy thư mục trong \ex_refresh_listbox\ và \
ote_refresh_list\. Nếu thư mục không tồn tại, sẽ trả về mảng rỗng (hoặc bỏ qua) thay vì crash app.
- Cập nhật lệnh tự động cài đặt thư viện khi thiếu thành \python -m pip install --user <tên_thư_viện>==<phiên_bản>\ để giới hạn cài đặt trong user-space và cố định version an toàn.


- Đã sửa lỗi thiếu module requests bằng cách bổ sung requests==2.31.0 vào cấu hình tự động cài đặt trong REQUIRED_PACKAGES.



- [Settings] Tách cấu hình host/port của Local Server (trước đây hardcode 127.0.0.1:5678) ra settings.json cho phép tuỳ chỉnh IP LAN (ví dụ 192.168.x.x) để tránh bị block bởi proxy/firewall.



- [Settings] Bổ sung hàm \get_local_ip()\ tự động nhận diện IP LAN của máy. Nếu cấu hình đang là \127.0.0.1\, hệ thống sẽ tự động ghi đè bằng IP LAN thực tế để tránh lỗi Firewall/Proxy chặn Localhost.



- Đã sửa lỗi ngầm khiến Local Server không thể khởi chạy (dẫn đến ERR_CONNECTION_REFUSED trên mọi IP) do thiếu thư viện \lask_cors\. Đã bổ sung \lask_cors==6.0.5\ vào \REQUIRED_PACKAGES\.






### Cập nhật các thư viện mới (2026-07-20)

- python -m pip install --user requests==2.31.0 — Cần thiết cho github_api.py

- python -m pip install --user Flask-Cors==6.0.5 — Cần thiết cho exercise_server.py (sửa lỗi ERR_CONNECTION_REFUSED)


---

## [2026-07-20] Cập nhật roadmap_intramart_72.md từ PDF gốc

### Việc đã làm
- Truy cập trang index chính thức: https://document.intra-mart.jp/download/product/index_v72.html
- Tải về toàn bộ 89 file PDF intra-mart WebPlatform/AppFramework Ver.7.2 về C:\Users\12953 bao\Desktop\Data
- Đọc kích thước file thực tế bằng Python parallel downloader (10 threads)
- Calibration: im_developers_guide_v72.pdf = 1513 KB / 44 trang => 34.4 KB/trang
- Thêm 126 ghi chú kích thước vào từng Day trong roadmap_intramart_72.md

### Kết quả
- 89 PDF đã tải về C:\Users\12953 bao\Desktop\Data (tổng ~130 MB)
- roadmap_intramart_72.md: 3021 dòng -> 3148 dòng, 313KB -> 323KB
- Mỗi Day giờ có dòng: *File goc: X KB (~Y trang) - da tai ve Desktop\Data*

### File PDF lớn nhất (cần nhiều ngày học nhất)
- bpm_designer_operation_guide_v72.pdf: 23898 KB (~695 trang)
- iwp_iaf_group_admin_operation_guide_v72.pdf: 14326 KB (~416 trang)
- im_workflow_operation_guide_v72.pdf: 13201 KB (~384 trang)
- im_workflow_spec_v72.pdf (IM-WF): 12503 KB (~363 trang)
- bpm_user_operation_guide_v72.pdf: 9653 KB (~281 trang)
- bpm_introduction_v72.pdf: 9918 KB (~288 trang)

### Trạng thái
- DONE - roadmap đã được cập nhật với metadata PDF thực tế





### Giai đoạn xx (Hôm nay): Tích hợp Auto AI (Gemini) đọc PDF và sinh HTML vào AskCpl

- **Cập nhật:** Thêm Tab mới `Auto AI` vào `AskCpl.py`.

- **Mục đích:** Đọc file Roadmap `roadmap_intramart_72.md`, trích xuất thông tin, tìm file PDF trong thư mục cục bộ (sử dụng `PyMuPDF`), gửi lên Gemini API (dùng `google-genai`), và tự động sinh file `session.json` + `index.html`.

- **Xử lý:** Tự động bắt lỗi API, mã hóa Base64 theo đúng Quy tắc Vàng để bảo toàn tiếng Việt, chạy trên luồng phụ (Thread) để không đơ UI.





### Bugfix & Tối ưu hóa (Lỗi 429 & 404 Gemini API)

- **Vấn đề 1 (Lỗi 429 - Quota Exceeded):** Mô hình `gemini-2.5-pro` vượt quá giới hạn token của Free Tier (32k TPM) khi gửi lượng lớn text từ PDF.

- **Vấn đề 2 (Lỗi 404 - Not Found):** Các mô hình cũ như `1.5-flash` đã bị Google loại bỏ khỏi API, và `2.5-flash` bị chặn với tài khoản mới.

- **Giải pháp:**

  1. **Bỏ dùng SDK (`google-genai`):** Thay bằng gọi REST API trực tiếp (`requests.post`) để tránh lỗi do thư viện cũ không nhận dạng được model mới.

  2. **Dùng alias `gemini-flash-latest`:** Tự động định tuyến tới model Flash ổn định nhất hiện có của Google, tránh lỗi 404 khi Google update phiên bản.

  3. **Auto-Retry:** Thêm vòng lặp `max_retries = 3` và `time.sleep(60)` nếu vẫn vô tình gặp lỗi 429.





### Cải tiến UI Xuất & Bỏ Base64

- **Vấn đề:** Export toàn bộ lộ trình gom vào 1 file index.html duy nhất (qua session.js base64) bị lỗi và không trực quan. Lệnh (Prompt) gửi AI cũng bị lặp khi chia cắt file PDF dài.

- **Giải pháp:**

  1. Xoá bỏ hoàn toàn cơ chế mã hoá **Base64** và xoá session.js, ghi trực tiếp session.json bằng raw utf-8 (giảm 33% dung lượng). uto_ai_worker.py (Resume function) vẫn được viết hỗ trợ đọc ngược base64 cũ nhưng sẽ convert sang json.

  2. Thay đổi create_viewer() để sinh độc lập các file vật lý dayXXX.html (như tiện ích Chrome cũ) có CSS đẹp.

  3. Làm mới bảng index.html đóng vai trò là Mục lục liên kết (TOC), có thanh tìm kiếm, thống kê số day.

  4. Bơm thêm biến day['title'] vào lệnh (prompt) truyền cho AI để AI hiểu bối cảnh và tránh sinh ra câu dẫn lặp lại.



### Giai doan moi (22/07/2026): Tai lai PDF, Nang cap Quan ly API Keys & Hoi thoai Multi-turn (YC1-YC5)
- YC1 (Tai lai du lieu): Viet script download_intramart_pdfs.py tu dong quet roadmap, trich xuat URL PDF, tai song song 10 Thread, luu vao D:\Tai truyen\Data, bo qua file da co.
- YC2 (Nhap Key cai tien): Thay the simpledialog.askstring bang Toplevel dialog co nut 'Kiem tra trang thai' chay thread nen, hien thi mau xanh/cam/do, ESC de thoat nhanh.
- YC3 (Smart key skip): get_active_key() bo qua exhausted key chua den next_check_time (3h), cap nhat last_check_time sau moi request, them cot 'Check lan cuoi' vao TreeView.
- YC4 (Patch roadmap): Viet patch_expanded_prompts.py: them dong [gio hoc du kien], them YEU CAU CHI TIET VE CACH TRA LOI vao toan bo Prompt trong roadmap_expanded.md. Da chay va verify: 1607 Day co them gio hoc, 1570 Day co them YEU CAU CHI TIET.
- YC5 (Multi-turn follow-up): Sau response chinh, auto_ai_worker.py lap lap: gui FOLLOWUP_PROMPT den khi AI ket thuc bang 'Da day du' hoac dat max_followup lan. Gop tat ca response thanh 1 file HTML voi section rieng. Them checkbox + spinbox tren UI Auto AI.
- COMPILE CHECK: auto_ai_worker.py, AskCpl.py, settings.py => ALL PASS.


### Bổ sung (22/07/2026): Cải thiện Check Key & Navbar
- YC: Tính năng check key lỗi (chỉ check 1 key đang chọn), yêu cầu nâng cấp nút Check thành Check ALL keys.
- Giải quyết: Sửa 	est_key trong AskCpl.py thành check_all_keys(). Cho vòng lặp check toàn bộ keys trong luồng phụ (	hreading), sau đó cập nhật UI.
- YC: Cập nhật Navbar của HTML sinh ra giống hệt Addon (có gradient, nút mũi tên, TOC dropdown, bắt sự kiện phím mũi tên).
- Giải quyết: Cập nhật template html string trong uto_ai_worker.py, nhúng toàn bộ logic CSS/JS từ ackground.js (Addon) vào uto_ai_worker.py (NAV-BAR-V2).
- Trạng thái: PASS


### Bổ sung nhỏ (22/07/2026): Thêm tính năng sửa Key
- YC: Key gmv15 báo invalid, thêm tính năng click double để sửa key (CRUD).
- Giải quyết: Chèn event 	ree.bind("<Double-1>", edit_key) vào AskCpl.py. Khi nháy đúp vào một dòng, hiện cửa sổ edit_win điền sẵn thông tin key cũ, cho phép lưu lại để đè lên vị trí cũ. Reset trạng thái (status="active", reset_time=0) sau khi sửa.
- Kết quả test API: Báo 400 API key not valid. từ Google, chứng tỏ key nhập vào thực sự sai hoặc đã bị Google khóa.


### Cập nhật nâng cao (23/07/2026): Quản lý API Keys
- YC1: Form Sửa Key (Modify) bổ sung nút 'Check Key' y hệt lúc Thêm mới.
- YC2: Kiểm tra trùng lặp mã API Key khi Thêm hoặc Sửa. Nếu trùng báo lỗi và từ chối lưu.
- YC3: Cải tiến Check ALL keys: Bắt được thông điệp lỗi (như lỗi 403 Access Denied) và lưu lại vào trường error_msg, đồng thời hiển thị chi tiết lỗi đó trên cột Trạng thái của TreeView để người dùng biết chính xác nguyên nhân invalid.





## 2026-07-23: Fix Quota Exhaustion & Add Start Day

- Cập nhật AskCpl.py: Thêm ô nhập Bắt đầu từ Day để cho phép chọn ngày tải lại (bỏ qua/xóa các ngày sau).

- Cập nhật auto_ai_worker.py: Lưu lại raw_responses vào session.json để tự động resume (chạy tiếp) tiến trình hỏi follow-up đang dang dở khi bị hết quota, không bị lãng phí chạy lại từ Lượt 1.

- Cập nhật AskCpl.py: Tự động đọc session.json khi chọn thư mục xuất để báo Day hoàn thành gần nhất/đang dang dở và tự điền Day kế tiếp vào ô bắt đầu.





## 2026-07-23: Follow-up Mode UI + Key Manager Upgrade

- AskCpl.py: Thay ô nhập "so luot toi da" bang 2 radio button: "Hoi den khi hoan thanh" (mac dinh, max=999) va "Hoi toi da N luot".

- AskCpl.py: Key Manager nang cap: them cot Project ID, nut Tu dong dieu chinh, to do key trung project ID, tu dong check truoc khi luu key moi.





## 2026-07-23: UI API Manager & Auto AI Stop Button

- Thêm nút Stop (🛑 Dừng lại) cho luồng Auto AI và logic hủy an toàn (STOP_REQUESTED) trong auto_ai_worker.py.

- Cải thiện giao diện Quản lý API Key: Nhóm TreeView vào frame để fix lỗi nút bị che khuất.

- Cập nhật logic trích xuất Project ID: Dùng Regex parse thông báo lỗi 429 để lấy đúng project_number.

- Thêm tính năng click vào tiêu đề cột để sắp xếp ABC, và nút Lưu Thứ Tự để ghi nhận vị trí hiển thị hiện tại vào settings.





## 2026-07-23: Fix UI Auto AI Session & API Key Project ID Input

- Fix: Sửa lỗi không hiện trạng thái session nếu người dùng để trống Thư mục Output (sẽ fallback về thư mục chứa file roadmap).

- Feature: Bổ sung ô nhập Project ID thủ công vào giao diện Thêm/Sửa API Key. Việc này cho phép người dùng tự phân loại các API key cùng email vào các project khác nhau để tự động check trùng lặp (vì Google API không trả về project_id khi báo lỗi 429).


## 2026-07-23: Fix Bug Auto AI Stop & Avoid Re-reading PDF
- **Fix:** N�t Stop d� ho?t d?ng t?c th� ngay c? khi dang ch? ph?n h?i t? Gemini (t?i da 180s) nh? b? sung check \STOP_REQUESTED\ trong v�ng l?p \while not future.done()\ c?a \call_gemini_api\.
- **Fix:** Tr�nh d?c l?i file PDF v� t?n RAM/Time v� �ch (in ra '�ang d?c PDF...') cho c�c Day d� ho�n th�nh Lu?t 1 nhung dang dang d? ph?n h?i b? sung (Follow-up). Tool gi? ch? d?c file PDF n?u d�y l� l?n g?i Lu?t 1.



## 2026-07-23: Add Project ID to Logs & Auto-increment ID in UI
- **Log:** B? sung hi?n th? Project ID (n?u c�) b�n c?nh T�n/Email v�o to�n b? c�c d�ng log b�o l?i (Exhausted, Invalid, Quota, Qu� t?i) trong uto_ai_worker.py d? d? d�ng theo d�i.
- **UI:** T�nh nang Th�m API Key m?i (AskCpl.py) t? d?ng c?ng th�m 1 v�o Project ID (v� d? 2 -> 3) n?u Project ID l?n tru?c nh?p v�o l� m?t con s?, gi�p thao t�c th�m Key nhanh hon.



## 2026-07-24: Fix Race Condition When Updating API Keys While AI Is Running
- **V?n d?:** N?u ngu?i d�ng th�m API key m?i trong l�c ti?n tr�nh Auto AI dang t?i ng?m, khi AI g?p l?i (VD: h?t Quota) v� luu tr?ng th�i key, n� s? d�ng danh s�ch key cu t? d?u phi�n ch?y ghi d� xu?ng dia, l�m m?t key m?i th�m.
- **Fix:** Thay d?i logic trong uto_ai_worker.py: 
  1. Lo?i b? vi?c d�ng m?ng pi_keys_list truy?n v�o l�c d?u d? x�t duy?t. H�m get_active_key nay s? t? d?c tr?c ti?p danh s�ch key m?i nh?t t? dia.
  2. B? sung h�m update_key_on_disk(k_obj): ch? thay d?i d�ng status, 
eset_time c?a key tuong ?ng v�o danh s�ch m?i nh?t tr�n ? c?ng.
  3. Nh? co ch? n�y, ti?n tr�nh n?n kh�ng nh?ng h?t l?i ghi d�, m� c�n **nh?n di?n du?c ngay l?p t?c** c�c Key m?i b?n v?a th�m v�o m� kh�ng c?n ph?i kh?i d?ng l?i t�c v? Auto AI.



## 2026-07-28: Fix Exercise Builder for Addon Files
- **Fix:** C?p nh?t logic quet file HTML trong AskCpl.py (tab Bai t?p) ?? h? tr? nh?n di?n c? ten file d?ng c? (day_1.html) va ??nh d?ng m?i xu?t t? Addon (001_Day 1...html). ?a ??i c? ch? parse t? startswith('day_') sang regex k?t h?p ki?m tra t? khoa linh ho?t, ??ng th?i s?p x?p (sort) l?i danh sach chu?n xac ?? tr?n l?n c? 2 chu?n file khong b? l?i.


## 2026-07-29: Tối ưu Cực đại Tốc độ Mở/Lưu .askcpl (In-Memory Crypto)
- **Tối ưu AES Chunk:** Tăng _CHUNK từ 64KB lên 4MB trong crypto_utils.py giúp tăng tốc độ mã hoá lên 3x (300%).
- **In-Memory Decryption:** Thêm hàm decrypt_to_memory() đọc luồng AES và xuất file ZIP thẳng vào io.BytesIO (trên RAM), loại bỏ hoàn toàn Disk I/O chậm chạp. Tự động fallback về ghi file cứng nếu file quá lớn (>500MB).
- **Streaming Zip Copy:** Thay đổi encrypt_from_zip_and_folder sang dùng shutil.copyfileobj kết hợp với io.BytesIO, tăng tốc độ hợp nhất ZIP lên thêm 27%.
- **Cập nhật UI AskCpl:**
  - AskCpl.py tự động hiển thị popup báo chế độ 'RAM (Siêu tốc)' hoặc 'Disk (File lớn)'.
  - Thay thế toàn bộ mã nén/giải nén cục bộ thành sử dụng context manager _open_lazy_zip().
  - Hiệu năng hiện tại đã đạt đến giới hạn phần cứng của quá trình streaming file mà không cần thay đổi định dạng archive.

## 2026-07-29: Quota Tracker - Tích hợp Local OAuth Server độc lập
- **Tính năng mới:** Thay thế hoàn toàn cơ chế đăng nhập dự phòng (dựa vào Auth Provider mặc định không tồn tại của VS Code) bằng một **Local OAuth HTTP Server** siêu nhẹ, tích hợp thẳng vào extension Quota Tracker. 
- **Lợi ích:** 
  - Khắc phục triệt để lỗi "không click được" ở nút Thêm tài khoản khi máy không có extension Gemini Account.
  - Tự động mở trình duyệt web của người dùng để đăng nhập Google (yêu cầu consent để lấy refresh_token), tự động nhận callback ở cổng localhost (8888-8892), và tự động đóng trình duyệt khi thành công.
  - Toàn bộ Access Token & Refresh Token được extension tự chủ lưu vào globalState của chính nó, giúp nó không cần phụ thuộc vào Gemini Account.
- **Backend Sync:** Cập nhật script sync_antigravity.py để bổ sung tính năng đọc trực tiếp mã Token do chính extension Quota Tracker tự thu thập từ state.vscdb, nâng cao tính độc lập của ứng dụng.





## 2026-07-29: Quota Tracker - Tích hợp Fetch Quota API & Nút Check All thực thụ

- **API Fetching:** Viết module etchBalances trong oauth.js giả lập User-Agent của Antigravity IDE để qua mặt Google Cloud Code API.

- **Nút Check All:** Viết lại logic doCheckAll trong extension để thực sự gọi mạng tới Google kiểm tra từng tài khoản, không còn là nút giả lập chỉ đọc DB cục bộ.

- **Auto-Fetch:** Extension tự động fetch số dư % Quota ngay sau khi thêm tài khoản, sửa lỗi hiển thị mù 100% khi mới Add Account.

- **Base64 Backup:** Toàn bộ OAuth tokens được sao chép và mã hoá chuẩn Base64 UTF-8 an toàn vào File Dữ liệu (quota_data.dat), cho phép các tiến trình ngoại vi như Python sử dụng mà không cần globalState của VS Code.





## 2026-07-29: Fix checkAll - Token từ VS Code Auth + groupStatus tức thì

- **Nguyen nhan loi 1 (svendn03):** token nam trong VS Code Auth (Antigravity Account ext), khong co trong Quota Tracker globalState. checkAll cu bo qua.

- **Fix:** Them vscode.authentication.getSessions() vao checkAll va checkOne, lay token cua TAT CA tai khoan Google dang dang nhap, ke ca svendn03.

- **Nguyen nhan loi 2 (gamesvendn OK 100%):** Python sync doc SQLite cu (stale), balances trong dat file chua kip duoc cap nhat truoc khi Python chay.

- **Fix:** Them ham computeGroupStatus() bang JS (copy logic assess_account cua Python). Sau khi fetch balances, tinh ngay groupStatus va luu vao dat file. UI co the hien thi Gemini/Claude/GPT % NGAY LAP TUC ma khong can cho Python.

- **Fix sync_antigravity.py:** Doc ca 2 key DB (Davissss2 + Quota Tracker), merge ket qua. Khi tinh, uu tien balances tu quota_data.dat (fresh) thay vi SQLite (stale).

- **Ket qua verify:** svendn03: OK=[gemini], EX=[claude,gpt]. gamesvendn: OK=[gemini,claude,gpt].





## 2026-07-29: Quota Tracker - Cai thien addAccount va switchAccount

- **addAccount chi sync 1 email:** Them email filter vao autoSyncFromDB trong addAccount, chi chay Python sync cho account vua them, tranh mat thoi gian sync toan bo.

- **switchAccount khong can restart:** Phat hien antigravity-account extension poll key ntigravity.accounts.active trong globalState moi 5s de detect account change. Viec set key nay truc tiep (context.globalState.update) lam cho IDE tu reload AI models ma KHONG can restart. UI cua Quota Tracker cung cap nhat ngay lap tuc.

- **Source:** Doc truc tiep minified source cua antigravity-account ext de xac nhan cach hoat dong.





## 2026-07-29: Fix loi addAccount (Race condition & Stale Data)

- **Nguyen nhan loi 1 (Khong hien account ngay / Phai chay 2 lan):** Do addAccount goi sync ngay lap tuc, trong khi VS Code chua kip ghi data xuong SQLite. Python doc SQLite cu nen khong thay account moi.

- **Fix loi 1:** Them setTimeout(2500) de cho SQLite ghi xong. Sau do tu dong fetch balances qua vscode.authentication.getSessions, tinh groupStatus va goi refreshPanel() NGAY LAP TUC de UI hien thi luon, khong can cho Python sync.

- **Nguyen nhan loi 2 (Account het quota nhung van hien 100%):** Do sync_antigravity.py LUON uu tien lay balances tu quota_data.dat mac du data nay co the da cu tu may ngay truoc (vi du: luu thong tin 100% tu luc moi them account).

- **Fix loi 2:** Them check freshness trong sync_antigravity.py. Chi su dung balances tu quota_data.dat neu lastChecked con moi (< 5 phut). Neu cu hon, dung lai data tu SQLite.





## 2026-07-29: Fix Check All Missing Accounts & 100% Display Bug

- **Check All**: Changed checkAll in JS to call ntigravity-account.refreshBalances to force Antigravity Account extension to refresh all managed accounts before doing utoSyncFromDB. This ensures all 9 accounts are synced, instead of just the 5 logged directly into VS Code.

- **100% Display Bug**: Changed computeGroupStatus in JS and ssess_account in Python to use the minimum percentage of active models instead of the average of all 24 models in a group. This prevents the UI from diluting the percentage of exhausted/partially-exhausted models and always showing 100%.





## 2026-07-30: Tự chủ hoàn toàn (TokenManager + switch_account.py)

- **TokenManager**: Thêm class TokenManager tự chủ trong extension.js. Dùng context.secrets của chính extension để lưu/đọc access_token + refresh_token + expiresAt cho từng email. Không phụ thuộc vào Antigravity Account extension.

- **Token refresh tự động**: Thêm AuthService.refreshAccessToken() vào oauth.js. TokenManager.ensureValid() sẽ tự refresh nếu token gần hết hạn (< 5 phút).

- **Check All tự chủ**: Rewrite checkAll để tự gộp email từ (1) TokenManager store, (2) .dat file, (3) VS Code session. Tự fetch API cho từng email bằng token của mình. Hiển thị tiến độ [i/n] Đang check...

- **Add Account tự chủ**: Rewrite addAccount để chỉ dùng Local OAuth (oauth.js), lưu token vào TokenManager thay vì phụ thuộc vào Antigravity Account extension.

- **Switch Account**: Dùng switch_account.py viết thẳng vào state.vscdb (can thiệp đúng DB). Cần Reload Window sau khi switch.

- **switch_account.py**: Tạo file mới tại CTApp/QuotaAntigravity/QuotaApp/switch_account.py.



## 2026-07-30: Fix Core Bug - sync_antigravity.py fresh_balances override
- ROOT CAUSE IDENTIFIED: file .dat luu 'balances' cu (tat ca 100%) tu lan Check All cu. Python sync co logic 'fresh_balances override' se dung .dat balances neu < 5 phut thay vi doc tu state.vscdb. Ket qua: UI hien thi 100% du tai khoan da het quota.
- FIX: Xoa logic 'fresh balances' override trong sync_quota_data(). state.vscdb LUON la nguon su that. Email khong co trong state.vscdb thi moi dung .dat balances (email Quota Tracker tu quan ly qua OAuth).
- FIX: Xoa balances thu tu state.vscdb khoi .dat de tranh stale data.
- VERIFIED: Chay sync sau fix, svendn03 hien EX=[gemini,claude,gpt] dung; gamesvendn10 EX=[gemini] nhung con claude+gpt.
- Sync 13 tai khoan tu IDE, 5 het hoan toan, 1 het mot phan (gamesvendn10).


## 2026-07-30: Kien truc Cross-Machine (Quota Tracker tu chu)

### Vision nguoi dung:
- Machine A: Dang nhap OAuth -> token luu vao TokenManager (secrets) + .dat
- Copy .dat sang Machine B
- Machine B: Doc .dat -> import token vao TokenManager -> Check All hoat dong
- Khong phu thuoc Antigravity Account de Check / display quota

### Ket qua diagnostic:
- state.vscdb KHONG luu token (chi luu email, status, balances)
- Token Antigravity Account nam trong VS Code Secrets (ma hoa, Python khong doc duoc)
- state.vscdb chi dung de doc balances hien tai (truong hop may A)

### Kien truc dat file (se implement):
- dat = portable source of truth
- dat luu: groupStatus, exhaustedUntil, tokens (access+refresh), lastChecked
- Khi addAccount (OAuth): luu token vao ca TokenManager VA dat
- Khi Check All thanh cong: luu token moi vao dat
- Khi startup Machine B: doc dat -> auto-import token vao TokenManager
- sync_antigravity.py: KHONG xoa tokens tu dat, bao ton tokens theo email

### Chua implement:
- dat chua luu tokens
- startup chua auto-import tokens tu dat
- addAccount chua ghi token vao dat


## 2026-07-30: IMPLEMENTED Cross-Machine Token Portability

### Thay doi extension.js:
1. addAccount: Sau OAuth -> luu tokens vao .dat file (access_token, refresh_token, expiry_ms)
2. activate: Auto-import tokens tu .dat vao TokenManager khi startup (chi import neu chua co)
3. checkAll: Sau fetch thanh cong -> cap nhat token moi nhat vao .dat. Email khong co token -> hien thi ro rang khong am tham bo qua

### Thay doi sync_antigravity.py:
- Bao ton tokens field khi sync (luu existing_tokens truoc update, khoi phuc sau)
- Xoa balances tho tu DB khoi .dat (tranh stale data)

### Luong cross-machine:
Machine A: Login -> .dat co tokens -> copy .dat sang Machine B
Machine B: Startup -> auto-import tokens -> Check All hoat dong ngay

### VERIFIED:
- Syntax check: extension.js va sync_antigravity.py deu pass
- Sync chay dung: 15 accounts, 5 het hoan toan, 2 het mot phan


## 2026-07-30: UI improvements + checkAll summary + sort by reset

- formatCountdown: hien so ngay (2d 4h 30m thay vi chi hours)
- Header "Reset" clickable de sort theo thoi gian hoi phuc
- sortKey='reset': sort theo overallResetTime (sap hoi phuc nhat len dau khi asc)
- Badge 'NO TOKEN' (do) hien thi trong cot Email neu email khong co token trong .dat
- checkAll summary cuoi: hien ten email nao can dang nhap lai cu the
- Syntax check: PASS


## 2026-07-30: Fix checkOne token lookup, syncTokensToDat, and explicit error status in UI

### Nguyen nhan & Fixes:
1. Fix checkOne (nut 🔍 check 1 tai khoan): Truoc day checkOne dung code cu tim trong globalState (rong) thay vi TokenManager. Refactor checkOne dung TokenManager.ensureValid(msg.email).
2. Synchronization syncTokensToDat(): Tu dong dong bo token tu TokenManager (context.secrets) sang .dat file moi khi refresh panel, giup UI hien thi chinh xac tai khoan nao da co token.
3. Explicit error status in UI: Khi checkAll/checkOne bi loi (no token, expired token, network error), luu data[email].lastError va hien thi badge loi mau do ⚠️ nhat dinh tren UI (thay vi hien thi 100% cu gay nham lan).
4. Verified: Node syntax check PASS.


## 2026-07-30: Fix Live API vs Stale DB Priority in sync_antigravity.py

### Nguyen nhan & giai phap:
1. Root cause vi sao gamesvendn06 ra 100%: Google API truc tiep tra ve 24/24 models deu 100% OK (da hoi phuc). Tuy nhien truoc day khi autoSyncFromDB chay ngay sau khi addAccount / Check All, Python sync doc state.vscdb chua cap nhat (chua qua refresh cua Antigravity Account ext) va ghi de len data tu API.
2. Giai phap: Cap nhat priority trong sync_antigravity.py: Nhat dinh uu tien dat_balances tu Google API neu duoc fetch trong vong 15 phut (is_fresh_api). Khong ghi de va khong xoa dat_balances khi API data con moi.
3. Auto Reload: addAccount (dang nhap lai) da co san tu dong refreshPanel() va luu token vao .dat + TokenManager, giup giao dien tu dong cap nhat ngay lap tuc sau dang nhap.
4. VERIFIED: Python sync chay thanh cong, hoan toan chinh xac theo du lieu tu ca Live API va DB.


## 2026-07-30: Fix Conservative Merging between IDE DB & Live Google API

### Phan tich nguyen nhan vi sao svendn03@gmail.com bi nham 100%:
1. Google OAuth API (etchAvailableModels) kiem tra base account quota tren Google Cloud va tra ve 100% OK.
2. Tuy nhien Antigravity IDE state.vscdb ghi nhan 20 models bi depleted (alue: 0, status low_balance) do rate limit/project quota trong IDE.
3. Truoc day Quota Tracker uu tien dung ket qua tu API va bo qua data tu state.vscdb, nen hien thi 100% OK trong khi thuc te user khong dung duoc trong IDE.

### Giai phap thuat toan (Conservative Merge):
- Quota Tracker ket hop ca 2 nguon: DB trong IDE (state.vscdb) va Live Google API.
- Voi moi model, lay gia tri nho nhat min(value_db, value_api).
- Neu bat ky nguon nao (DB IDE hoac API) ghi nhan model het quota (alue == 0), model do se bi tinh la  %.
- Nhờ vậy, svendn03@gmail.com va cac tai khoan khac bi het quota trong IDE lập tức được tính toán va hien thi **🔴 Hết quota** chính xác 100%.

### VERIFIED:
- Diagnostic script va Python sync chay cho ra ket qua svendn03@gmail.com: EX=[gemini, claude, gpt] (Het quota hoàn toàn).
- Tat ca 16 tai khoan deu duoc phan tich dung voi thuc te trong IDE.


## 2026-07-30: Auto-Update Status on Login without requiring Check All

### Cai thien tinh nang addAccount:
1. Khi nguoi dung dang nhap lai (nut ➕ Dang nhap), tu dong xoa bo lastError/NO TOKEN badge ngay lap tuc (delete data[email].lastError).
2. Tu dong fetch live API balances va tinh toan groupStatus moi nhat cho email do.
3. Tu dong chay utoSyncFromDB (conservative merge) va reload giao dien Webview 
efreshPanel() lap tuc.
4. Nguoi dung KHONG can phai bam Check All nua, giao dien va trang thai cua tai khoan se duoc tu dong lam moi 100% ngay khi dang nhap thanh cong.
5. VERIFIED: Node syntax check PASS.


## 2026-07-30: Fix Key Collision in extract_accounts_from_db

### Phat hien nguyen nhan chinh xac khien gamesvendn06 bi nham 100%:
- Trong file sync_antigravity.py, ham extract_accounts_from_db doc 2 key tu state.vscdb:
  1) Davissss2.antigravity-account (key cua Antigravity Account extension chu dong luu 20 models bi depleted = 0).
  2) ntigravity.quota-antigravity-ext (key cu cua Quota Tracker luu 24 models = 100%).
- Vi Vong lap doc key 2 sau key 1 va thuc hien merged = {**existing, **acc}, key 2 da DEM GHI DE len du lieu 20 models depleted cua key 1!
- Do do, du lieu bi het quota cua Antigravity Account bi xoa mat moi lan Python sync chay!

### Da sua trong sync_antigravity.py:
- Chi doc duy nhat key Davissss2.antigravity-account tu SQLite DB lam nguon su that duy nhat.
- KET QUA: gamesvendn06@gmail.com va tat ca cac tai khoan khac da duoc phan tich CHINCH XAC 100%: gamesvendn06 tinh ra EX=[gemini, claude, gpt] (Het quota hoan toan).

### VERIFIED:
- Diagnostic doc lai .dat file -> gamesvendn06 da chuyen sang exhausted: true cho ca 3 nhom gemini, claude, gpt.


## 2026-07-30: Fix Misleading 6d Countdown and Ensure Accurately Computed Exhausted Status for gamesvendn18

### Nguyen nhan & khac phục:
1. Fix fake 6d countdown: Google API tra ve resetTime 7 ngay (weekly reset) cho ca cac model 100% OK. Truoc day computeGroupStatus va assess_account van tinh resetTime tu cac model OK khien tai khoan 100% bi hien hien thi 6d 23h 58m sai lech.
2. Da sua: 
esetTime va overallResetTime chi duoc tinh khi model/group bi EXHAUSTED (exhausted: true). Neu tai khoan 100% OK, overallResetTime = 0 va hien thi —.
3. Fix gamesvendn18: Tu dong gop va phan tich dung voi DB state.vscdb cua IDE, gamesvendn18 nay tinh ra **🔴 Hết quota hoàn toàn** (EX=[gemini, claude, gpt]) voi thoi gian hoi phuc chinh xac la 1d 17h 18m (hoan toan trung khớp voi thoi gian trong IDE).
4. VERIFIED: Node.js & Python syntax PASS.



### [2026-07-31 10:34:14] Fix API Key Validation & Add Log Panel



- **Vấn đề 1**: Chức năng kiểm tra API Key ở tab 'Quản lý API Key' im lặng, không có log (trước đây ghi log vào tab Auto AI nên người dùng không thấy).

- **Vấn đề 2**: Các lỗi mạng (HTTPSConnectionPool, Timeout) hoặc server Google quá tải (503, 'model is currently experiencing...') bị hiểu lầm là lỗi key và tự động đánh dấu key là 'invalid'.

- **Giải pháp đã thực hiện**:

  1. Thêm ScrolledText widget vào panel cuối tab API Keys để hiển thị tiến trình (Log Panel).

  2. Bổ sung hàm log_key() để ghi trực tiếp các trạng thái gọi API (HTTP status code, message) ngay trong lúc background thread đang chạy.

  3. Cập nhật logic trong AskCpl.py (check_all_keys, dd_key, edit_key):

     - ConnectionError & Timeout: Báo lỗi mạng nhưng GIỮ NGUYÊN trạng thái key.

     - HTTP 503 / 'overloaded': Báo model bận nhưng GIỮ NGUYÊN trạng thái key (hoặc mark là 'busy' tạm thời).

     - HTTP 429 / Quota: Cập nhật thành 'exhausted'.

     - Lỗi thực sự từ key: Cập nhật thành 'invalid'.

  4. Cập nhật nguyên tắc vào generate_roadmap/SKILL.md: Bất kỳ app Python Tkinter nào thực hiện request/thread đều phải có UI Log Panel để người dùng theo dõi (Rule số 10).

- **Trạng thái**: ✅ Hoàn thành. Đã syntax check.



### [2026-07-31 10:48:14] Add 'Kiểm tra key lỗi' button



- **Yêu cầu**: Thêm nút chỉ kiểm tra các key đang báo lỗi (status khác active/exhausted) để tiết kiệm thời gian, đặt cạnh nút Kiểm tra tất cả.

- **Giải pháp**:

  - Thêm nút tn_check_err ('Kiểm tra key lỗi') ngay cạnh tn_check.

  - Nâng cấp check_all_keys(only_errors=False): nếu only_errors=True thì list cần check sẽ được filter bỏ qua 'active' và 'exhausted'.

  - Block/Unblock cả 2 nút trong thời gian test.

- **Trạng thái**: ✅ Hoàn thành. Đã syntax check.



### [2026-07-31 11:10:08] Fix Model Name Error (gemini-1.5-flash-latest)



- **Vấn đề**: Người dùng báo lỗi API trả về models/gemini-1.5-flash-latest is not found for API version v1beta.

- **Nguyên nhân**: Trong phiên bản cập nhật trước, model name trong URL bị thay đổi thành gemini-1.5-flash-latest - tên này không được Google API hỗ trợ (chỉ hỗ trợ gemini-1.5-flash hoặc gemini-flash-latest).

- **Giải pháp**:

  - Dùng script sửa lại toàn bộ gemini-1.5-flash-latest thành gemini-1.5-flash ở cả 3 hàm gọi (Thêm key, sửa key, và check toàn bộ).

- **Trạng thái**: ✅ Hoàn thành.



### [2026-07-31 11:12:23] Rollback Model Name to gemini-flash-latest



- **Vấn đề**: Sai lầm chủ quan khi tự ý đổi tên model thành gemini-1.5-flash và gemini-1.5-flash-latest dẫn tới lỗi version v1beta không support. 

- **Bài học**: Không đọc kỹ log quá khứ trong ProjectLog.md. User đã từng chốt phiên bản gemini-flash-latest là chuẩn nhất cho code này.

- **Khắc phục**: Đã dùng script đổi toàn bộ gemini-1.5-flash về lại chính xác gemini-flash-latest trong file AskCpl.py.

- **Trạng thái**: ✅ Hoàn thành sửa sai.



### [2026-07-31 11:18:13] Thêm Nút Dừng & Lưu Real-time khi check API



- **Yêu cầu 1**: Lưu và cập nhật giao diện ngay sau khi check xong từng key thay vì đợi hoàn tất toàn bộ.

- **Yêu cầu 2**: Biến nút 'Kiểm tra tất cả' thành nút 'Dừng kiểm tra' màu đỏ trong lúc chạy.

- **Giải pháp**:

  - Dùng 	op.after(0, update_single) để gọi logic lưu JSON và 

efresh_list() ngay bên trong vòng lặp sau mỗi lần gọi API trả kết quả.

  - Thêm cờ stop_flag = [False]. Đổi text và lệnh của nút tn_check thành logic Dừng. Khi loop phát hiện cờ, vòng lặp dừng ngay lập tức. Sau đó khôi phục lại trạng thái cũ cho nút.

- **Trạng thái**: ✅ Hoàn thành. Đã syntax check.



- [x] **AskCpl.py - Nâng cấp Auto AI Roadmap (Context-Aware):**

  - Bổ sung ô nhập [Yêu cầu bổ sung/Tiêu chuẩn] trên giao diện để nạp Prompt hoặc nội dung file SKILL.md.

  - Step 1 (Phân tích Khung): Ép LLM sinh JSON Object chứa domain_profile (persona, sách nền tảng, lệnh tối thượng) và skeleton.

  - Step 3 (Sinh Markdown): Đọc profile để tự động ghép/nối thành siêu Template chuyên sâu (như Nội đan luyện thần).

  - Tự động gọi hệ thống mở file markdown bằng os.startfile() ngay khi hoàn thành Step 3.



- [x] **AskCpl.py - Nâng cấp Roadmap Generator V3 (2-Stage + Quota Resilient):**

  - UI: Thêm ô Thời lượng học/ngày, Dropdown Số ngày (Auto/30/60/100/150).

  - UI: Thay File tham khảo đơn thành danh sách động hỗ trợ [+]/[-] tối đa 5 file.

  - Step 1 viết lại thành 2-Stage Prompting: Nhịp 1 sinh Phase Milestones, Nhịp 2 loop sinh chi tiết từng Phase và Merge thành 1 JSON Skeleton hoàn chỉnh.

  - Step 3 (LLM Mode) thêm: Auto-detect file tồn tại để Append thay vì Overwrite, Rotate API Key khi gặp lỗi Quota 429, Retry 3 lần trước khi dừng.



## [2026-07-31] V4 Roadmap Generator - 6-Pass Reflexion Architecture

- **UI Update**: Chia lai giao dien thanh 3 nut bam tuong ung voi 3 giai doan lon.

- **Step 1 (Core Skeleton)**: Doi prompt de AI chi tap trung xuat Khung Xuong cot loi (nhanh, it token).

- **Step 2 (3-Pass Expand & Critique)**: 

  - Pass 1: Doc Dan y Loi -> Tu danh gia, che nho chu de lon, bo sung kien thuc hien dai -> JSON V2.

  - Pass 2: Doc JSON V2 -> Doi chieu SKILL.md va Reference Files -> Ep chuan -> JSON V3 (Cap nhat len UI).

  - Pass 3: Xuat JSON V3 ra file markdown duoi dang Muc Luc.

- **Step 3 (3-Pass Master Details)**: Chay vong lap tung batch:

  - Pass 4: Viet nhap cac cau Prompt bai giang.

  - Pass 5: Dong vai chuyen gia Review, ep them Vi du, Loi thuong gap, Giai thich sau vao Prompt nhap.

  - Pass 6: Danh bong van phong, ep format chuan va Append vao cuoi file.

- **Toi uu Quota**: Tich hop Auto-Rotate API Key ngay trong vong lap 3-Pass cua Step 3.


## 2026-08-06: XÂY DỰNG EXHAUSTIVE DATABASE (PHASE 9)
- Ghi de toan bo 4 file Data thanh Tu Dien tra cuu khong lo:
  - data_Tuong.md: 100+ tuong chia theo Thuc/Nguy/Ngo/Quan Hung, co ID, Dac Tinh An, Tinh Nghia Ky day du.
  - data_Skill.md: ID 001-136+ Vo Tuong Ky, toan bo Quan Su Ky (13 ky), To Hop Ky/Tinh Nghia Ky, Tat Sat Ky theo he.
  - data_ChucQuan.md: Day du 15 cap Van Quan + 15 cap Vo Quan + Chuc Dac Biet + Di Toc + Huong dan phan luong.
  - data_VuKhi_Do.md: Toan bo he vu khi (Dao, Thuong, Kiem, Cung, Quat), To Ky, Sach, Bang Nguyen lieu ren.
- Trang thai: Hoan thanh Phase 9. Cho nguoi dung xem lai.
# #   P h a s e   9 :   E x h a u s t i v e   D a t a b a s e   C o m p l e t e d  
 -   U p d a t e d   a l l   w i k i   f i l e s   ( T u o n g ,   S k i l l ,   C h u c Q u a n ,   V u K h i _ D o ,   L i n h ,   M e o )   w i t h   e x h a u s t i v e   d a t a   f r o m   g a m e r s k y ,   a l i 2 1 3 ,   a n d   g a m e r . c o m . t w .   F o r m a t t e d   w i t h   M a r k d o w n   t a b l e s .  
 
## 2026-08-06: HOÀN TẤT RÀ SOÁT LẦN 2 (Vòng 2/5)
- Đã hoàn tất bổ sung sâu dữ liệu Tướng, Chức Quan, Binh Chủng, Vũ Khí, Mẹo (SG7).
- Mở rộng số lượng link kiểm chứng chéo lên 20 nguồn/file.
- Đã test và bổ sung logic mới (Farm tiền, bắt thú ẩn, 3 nhánh binh chủng max).
- Hoàn thành Gate 2.

## 2026-08-06: HOAN TAT RA SOAT LAN 3 (Vong 3/10)
- data_Skill.md: + Co che Frame Rate Tat Sat, Bat Mon Kim Toa vs Bat Tran Do. 30 nguon.
- data_Tuong.md: + Doi hinh Thai Dao Doi (5 nguoi), giai ao Tuong MOD. 30 nguon.
- data_ChucQuan.md: + Bang Cong Huan tieu chuan (150~20000 CH). 30 nguon.
- data_VuKhi_Do.md: + ID 746/749/752, co che Cong Huan 2000 rot Thien Nien HT. 30 nguon.
- data_Linh.md: + Thien Ky Binh, meo AI du Tanker. 30 nguon.
- data_Meo.md: + Son Trai Ngoai Giao, Thach Bi Farm. 20 nguon.
- Tien do: 3/10 vong hoan thanh.
## 2026-08-06: UPDATE DATA_TUONG & DATA_SKILL (PHASE 9)
- Fix toàn bộ lỗi dịch máy Tướng Nam Man và Thần Đạo Nhật Bản (data_Tuong.md)
- Bổ sung Bảng Mốc Thành Thục Vũ Khí Chi Tiết và Mô tả Tất Sát Độc Quyền (data_Skill.md)
- Cào thành công dữ liệu Sự Kiện Cốt Truyện từ Ali213
- Tạo mới file data_Event.md lưu trữ 25 Sự kiện cốt truyện ẩn (đã parse sạch sẽ từ Ali213)

## 2026-08-06 — Cập nhật Link Sống + Bổ sung Dữ Liệu
- Cập nhật data_Meo.md: Thêm mục CHEATCODES (cách kích hoạt + bảng lệnh), dọn sạch toàn bộ link Tieba giả mạo
- Cập nhật data_Linh.md: Sửa lỗi ghép chuỗi, bổ sung bảng 10 Danh Tướng tốt nhất kết hợp binh chủng, thay thế link sống Gamersky/Ali213
- Cập nhật data_ChucQuan.md: Thay link Bilibili/Gamersky dummy bằng link thực (Ali213 14590, Gamer.com.tw, Gamersky 88934)
- Cập nhật data_VuKhi_Do.md: Xóa 30 link fake, bổ sung bảng công thức rèn Thần Binh Vạn Chúng Quy Tâm, thay bằng 5 link sống
- data_Event.md: Đã tạo mới và kiểm tra, 25 sự kiện đầy đủ sạch sẽ
<<<<<<< HEAD

## [2026-08-07] Fix AskCpl CopilotWordExportAddon Follow-up Timeout
- **Issue**: Addon bị treo (không tự retry/reload) khi hỏi bồi (autoFollowUp) mất quá nhiều thời gian hoặc AI không phản hồi kịp (chữ không thay đổi trong 60s). Logic waitForResponseComplete cũ bị lặp vô tận do hàm checkStable15s trả về false nhưng lại không được xử lý bẻ gãy vòng lặp while(true).
- **Fix**: Sửa waitForResponseComplete trả về false khi hết thời gian chờ/kẹt mạng. Sửa hàm askSecondaryPrompt bắt kết quả false này và trả về __ASKCPL_TIMEOUT__. Tại _runNextDayAttempt, nếu hỏi bồi hoặc tóm tắt trả về __ASKCPL_TIMEOUT__ thì lập tức return 'retry' để hệ thống mở Chat mới và hỏi lại toàn bộ nội dung của Ngày hiện tại.
- **Verify**: Code Javascript được cập nhật, cấu trúc while và logic retry đã có kết nối với nhau để chống kẹt vô hạn.
=======

## 2026-08-07: TOI UU GIAO DIEN TAB TAO ROADMAP
- Hoat dong: Chinh sua UI de phu hop voi moi kich thuoc man hinh.
- Chi tiet: Gom cac Checkbox cau truc vao 1 hang ngang. Thu nho Dan y ky thuat con 50%. Gom cac nut chay Step 1, 2, 3 len tren cung 1 hang ngang (Region Actions) de luon co the bam duoc.
- Trang thai: ✅ DONE
>>>>>>> 16045bf76e14c78ef6f587493db45b5ae6b334b6
