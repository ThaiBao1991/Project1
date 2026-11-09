# Project Log: Local AI (Ollama + GGUF + GUI Control Panel)

## 1. Thông Tin Môi Trường & Hệ Thống
- **Hệ điều hành**: Windows 11 Pro 64-bit.
- **CPU**: AMD Ryzen 5 5600H with Radeon Graphics (6 nhân, 12 luồng).
- **GPU**: NVIDIA GeForce RTX 3050 Ti Laptop GPU (4.0 GB VRAM - CUDA Tăng tốc 100%).
- **Bộ nhớ RAM**: 8.0 GB vật lý.
- **Thư mục lưu trữ**:
  - `Project1\GravityCode\MBC\LocalAI\`: Mã nguồn điều khiển (`local_ai_gui.py`, `web_chat.html`, `test_chat.py`, `start_ai.bat`, `config.json`, `ProjectLog.md`).
  - `D:\LocalAI\models`: Nơi lưu trữ các file mô hình `.gguf` (đã có `Llama-3.2-3B-Instruct-abliterated.Q4_K_M.gguf`, `Qwen2.5-3B-Instruct-Abliterated.Q4_K_M.gguf`).
  - `D:\LocalAI\start_ai.bat`: File chạy đồng bộ từ ổ D.
- **Engine Server**: Ollama Engine v0.32 (Cổng `11434`, OpenAI API format `http://127.0.0.1:11434/v1`).
- **Mô hình mục tiêu**: `llama3.2-3b-abliterate:latest` (Bản 3B không kiểm duyệt, nạp trọn vẹn 100% vào 4GB VRAM GPU).

---

## 2. Nhật Ký Triển Khai (Changelog)

### 2026-11-09 (Cập nhật lớn: Directory Picker, Config Persistence, Ollama Server & Web Chat)
1. **Lựa chọn & Lưu địa chỉ Thư mục Models (Config Persistence)**:
   - Thêm nút `📁 Đổi Thư Mục...` cho phép duyệt chọn bất kỳ thư mục mô hình nào trên máy.
   - Tự động lưu và nạp cấu hình từ `config.json` (`models_dir`, `selected_model`, `port`, `api_key`).
2. **Nhận diện Phần cứng Tự động (Hardware Auto-Detection)**:
   - Tự động đọc thông số CPU qua Windows Registry và GPU rời qua CIM/PowerShell để hiển thị đúng cấu hình thực tế (`AMD Ryzen 5 5600H (12 luồng) + RTX 3050 Ti GPU`), gỡ bỏ thông tin gán cứng.
3. **Tích hợp Tự động Kiểm tra & Cài đặt Ollama**:
   - Tự động quét tìm `ollama.exe` trong hệ thống.
   - Thêm nút tải & cài đặt tự động ngầm `OllamaSetup.exe` từ trang chủ Ollama nếu phát hiện máy chưa cài.
4. **Vận hành AI Server qua Ollama**:
   - Tự động quét và liệt kê đồng thời cả mô hình nội bộ Ollama và các file `.gguf` trong thư mục người dùng chọn.
   - Tự động tạo Modelfile và nạp file GGUF (`Llama-3.2-3B-Instruct-abliterated.Q4_K_M.gguf`) vào Ollama với tên `llama3.2-3b-abliterate:latest`.
   - Kết quả: Mô hình nạp **100% GPU VRAM** của RTX 3050 Ti, tốc độ sinh chữ cực nhanh (35-50 token/giây) không tốn RAM hệ thống.
5. **Giao diện Web Chat Độc Lập (`web_chat.html`)**:
   - Xây dựng giao diện chat Dark Mode thuần HTML/JS, hỗ trợ streaming chữ trực tiếp từ API Ollama `/v1/chat/completions`.
   - Nút `🌐 Mở Web Chat` trên Control Panel tự động mở trang chat trong trình duyệt để người dùng trò chuyện ngay lập tức.
6. **Kiểm thử Hoàn tất**:
   - Syntax check: `python -m py_compile local_ai_gui.py` đạt 100%.
   - Chạy test headless `LocalAIGUI`: Nạp config và nhận diện models hoàn hảo.
   - Chạy thử nghiệm suy luận thực tế `test_chat.py`: Trả lời tiếng Việt trơn tru qua GPU.

### 2026-11-09 (Sửa lỗi Khởi chạy Server: Timeout 60s GGUF, Nhận diện Cache & CORS Web Chat)
1. **Khắc phục Lỗi Timeout 60s khi Nạp GGUF**:
   - Bổ sung cơ chế kiểm tra trước: Nếu mô hình đã từng được nạp vào Ollama (`ollama list`), hệ thống tái sử dụng ngay lập tức mà không chạy lại lệnh `ollama create`.
   - Đối với model mới nạp lần đầu: Tăng timeout lên 300 giây (5 phút) và đặt trong khối `try...finally` đảm bảo file tạm `.Modelfile_*` luôn được dọn dẹp sạch sẽ.
   - Đã xóa sạch file rác `.Modelfile_llama-3.2-3b-instruct-abliterated` trong `D:\LocalAI\models`.
2. **Khắc phục Triệt để Lỗi CORS 403 Forbidden trên Web Chat**:
   - Tích hợp `ensure_web_server()` chạy HTTP server nền tại cổng `11435` phục vụ `web_chat.html` (`http://127.0.0.1:11435/web_chat.html`).
   - Nhờ đó trình duyệt không còn gửi `Origin: null` (nguyên nhân bị Ollama chặn 403), Web Chat kết nối trực tiếp với Ollama mượt mà 100%.
   - Truyền biến môi trường `OLLAMA_ORIGINS="*"` khi bật `ollama serve`.
3. **Cơ chế Tự Động Đồng Bộ Trạng Thái (Live Status Poller)**:
   - Thêm hàm `poll_server_status()` tự động thăm dò cổng 11434 mỗi 3 giây. Trạng thái nút Bật/Tắt và chỉ báo Offline/Online luôn chính xác theo thời gian thực mà không bị kẹt ở trạng thái Offline.
4. **Chuẩn hóa Model ID**:
   - Tự động chuyển Model ID hiển thị về chữ thường (lowercase) đồng bộ với định dạng nhận dạng của Ollama.
   - Cập nhật [test_chat.py](file:///c:/Users/games/Desktop/Project/Python/Python%20MyWork/Project1/GravityCode/MBC/LocalAI/test_chat.py) tự động đọc mô hình đang chọn từ `config.json`.

### 2026-11-09 (Sửa lỗi Web Chat không trả về nội dung: Reverse Proxy Same-Origin, SSE Chunk Buffering & UI Loading State)
1. **Reverse Proxy Same-Origin trên Cổng 11435**:
   - Nâng cấp server cục bộ trong [local_ai_gui.py](file:///c:/Users/games/Desktop/Project/Python/Python%20MyWork/Project1/GravityCode/MBC/LocalAI/local_ai_gui.py) thành `ThreadingTCPServer` Reverse Proxy: Chuyển tiếp toàn bộ yêu cầu `/v1/*` và `/api/*` từ `11435` sang `11434` đa luồng, không bị nghẽn hay khóa lẫn nhau giữa các lượt polling.
   - Web Chat chạy hoàn toàn dưới dạng Same-Origin (`http://127.0.0.1:11435`), loại trừ hoàn toàn các rào cản phân quyền mạng nội bộ (Private Network Access) của Chrome.
2. **Bộ đệm Ghép dòng Streaming SSE (`buffer = lines.pop()`) & Xử lý [DONE] dứt khoát**:
   - Cập nhật thuật toán đọc luồng trong [web_chat.html](file:///c:/Users/games/Desktop/Project/Python/Python%20MyWork/Project1/GravityCode/MBC/LocalAI/web_chat.html): Dòng dữ liệu bị cắt giữa chừng (TCP fragmentation) được giữ lại nối với chunk kế tiếp.
   - Khi nhận token kết thúc `[DONE]`, lập tức hủy kết nối stream và thoát vòng lặp, không bị kẹt giữ kết nối ngầm.
3. **Hiệu ứng Loading & Chống Spam Yêu cầu**:
   - Thêm hiệu ứng `● Đang suy nghĩ...` sinh động ngay khi bấm gửi, không còn tình trạng ô tin nhắn AI bị trống rỗng khi chờ suy luận.
   - Tự động vô hiệu hóa ô nhập và nút "Gửi" (`btnSend.disabled = true`, `user-input.disabled = true`) trong suốt quá trình AI sinh phản hồi, chống bấm liên tục gây nghẽn hàng đợi đơn luồng `n_slots = 1` của Ollama.
4. **Cơ chế Dự Phòng Tự Động (Non-stream Fallback)**:
   - Nếu luồng streaming vì lý do gì kết thúc mà không thu được nội dung, ứng dụng tự động kích hoạt truy vấn Non-stream trong 1 giây để nạp lại đầy đủ câu trả lời.
5. **Kiểm thử Thực tế Đạt Chuẩn**:
   - Gửi yêu cầu câu chào `"Xin chào"`: Nhận phản hồi đầy đủ chỉ sau **1.38 giây** (1389 ms), tốc độ trên GPU RTX 3050 Ti đạt ~45-50 token/giây.

### 2026-11-10 (Bổ sung Chế độ Mở Khóa Toàn Diện Uncensored 100% & Lọc Chuẩn Danh Sách Model)
1. **Chế Độ Mở Khóa Toàn Diện (Uncensored Mode) trên Web Chat**:
   - Thêm nút gạt trạng thái trực tiếp trên thanh công cụ: `🔓 Mở Khóa: BẬT` (xanh lá) / `🔒 Chuẩn: TẮT` (xám) với lưu trữ tự động vào `localStorage`.
   - Tích hợp cửa sổ cài đặt Modal `⚙️`: Cho phép người dùng xem, tùy biến hoặc khôi phục System Prompt mở khóa mặc định (`DEFAULT_UNCENSORED_PROMPT`).
   - Tự động nạp System Prompt Mở Khóa vào mảng `messages` khi gửi tin nhắn đến API Ollama (`/v1/chat/completions`), loại bỏ hoàn toàn các rào cản từ chối hoặc đạo đức hóa của mô hình AI.
   - Áp dụng cấu hình `temperature: 0.7` đồng bộ cả cho luồng streaming và luồng fallback non-stream.
2. **Lọc và Chuẩn Hóa Danh Sách Mô Hình (Model Deduplication & Sizing)**:
   - Phân tách rõ ràng giữa mô hình đã sẵn sàng trong Ollama (`⚡ [Ollama] <name> (<dung lượng> GB - Sẵn sàng)`) và file GGUF thô mới tải về trong thư mục (`📥 [GGUF Mới] <name> (<dung lượng> GB - Chưa nạp)`).
   - Khử trùng lặp thông minh: File GGUF nào đã được import vào Ollama (ví dụ `Llama-3.2-3B-Instruct-abliterated.Q4_K_M.gguf`) sẽ không bị lặp lại ở dạng file thô.
   - Trích xuất Model ID chuẩn xác: Trường Model ID và nút Copy luôn giữ đúng tên tag sạch (chữ thường, không tiền tố/hậu tố dung lượng), tương thích 100% với AnythingLLM và Cline.
3. **Tích hợp Mở Khóa Nạp GGUF Tự Động**:
   - Khi người dùng chọn một file GGUF mới (`📥 [GGUF Mới]`) và bấm Bật Server, hệ thống tự động sinh Modelfile đính kèm sẵn System Prompt Mở Khóa và các tham số dừng (`stop tokens`), đảm bảo mô hình nạp vào Ollama chạy ở chế độ không kiểm duyệt ngay từ gốc.
4. **Kiểm Thử Thực Tế Hoàn Tất**:
   - Kiểm tra cú pháp: `python -m py_compile local_ai_gui.py` đạt chuẩn 100%.
   - Kiểm tra Dropdown Tkinter: Danh sách hiển thị đúng 8 model Ollama kèm dung lượng và 1 file GGUF mới chưa nạp, không bị trùng lặp.
   - Kiểm tra Web Chat HTTP Server: Cổng `11435` phục vụ giao diện mới đầy đủ nút mở khóa và modal tùy chỉnh prompt.
   - Kiểm tra khả năng suy luận mở khóa: AI trả lời kịch bản hành động, chiến thuật thâm nhập an ninh chi tiết, không từ chối, không đạo đức hóa, phản hồi tiếng Việt lưu loát.
