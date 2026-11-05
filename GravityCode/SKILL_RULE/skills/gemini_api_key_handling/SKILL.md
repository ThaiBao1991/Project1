---
name: gemini_api_key_handling
description: Hướng dẫn toàn diện về xử lý Google Gemini API Keys, kỹ thuật xoay vòng Key (Key Rotation), Proxy trung gian cho Opencode, kỹ thuật Blind Fire, phân loại mã lỗi (429, 503 Overloaded, 401/403, 500), và Bộ quy chuẩn Chống Khóa Tài khoản Google (Anti-Ban & Anti-Abuse Protection).
---

# Kỹ năng Quản lý & Xoay vòng Gemini API Keys An Toàn (Anti-Ban Standard)

Tài liệu quy chuẩn bắt buộc áp dụng khi xây dựng các module gọi Google Gemini API (Agent, Proxy trung gian, Opencode rotation, Auto AI workers) nhằm đảm bảo hệ thống hoạt động ổn định và **TUYỆT ĐỐI KHÔNG BỊ GOOGLE KHÓA TÀI KHOẢN GMAIL/CLOUD**.

---

## 1. Các định dạng API Key của Google
- **`AIza...`**: Định dạng truyền thống từ Google Cloud Console hoặc Google AI Studio.
- **`AQ....`**: Định dạng mới (Vertex AI / Cloud project token). Vẫn được Google chấp nhận truyền qua header `x-goog-api-key` hoặc query `?key=...`.
- **`ENC:...`**: Chuỗi key đã được đảo ngược (reverse) và mã hóa Base64 trước khi lưu vào JSON để bảo mật:
  ```python
  import base64

  def decode_token(encoded: str) -> str:
      if not encoded or not isinstance(encoded, str):
          return ""
      if not encoded.startswith("ENC:"):
          return encoded.strip()
      try:
          b64 = encoded[4:]
          return base64.b64decode(b64.encode("utf-8")).decode("utf-8")[::-1].strip()
      except Exception:
          return encoded.strip()

  def encode_token(raw_key: str) -> str:
      if not raw_key:
          return ""
      reversed_str = raw_key[::-1]
      b64 = base64.b64encode(reversed_str.encode("utf-8")).decode("utf-8")
      return f"ENC:{b64}"
  ```

---

## 2. Kỹ thuật Chuẩn: Blind Fire (Bắn thẳng)
- **Tuyệt đối KHÔNG gọi `GET /models`** để check key: Với key định dạng `AQ.`, endpoint `/models` sẽ trả về lỗi `401 Unauthorized` (`ACCESS_TOKEN_TYPE_UNSUPPORTED`) làm hiểu nhầm là key đã chết.
- **Phương pháp chuẩn (Blind Fire)**: Gửi request POST thử nghiệm tạo nội dung ngắn trực tiếp lên model mới (vd: `gemini-flash-latest` hoặc `gemini-2.5-flash`):
  ```
  POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
  Headers: {"Content-Type": "application/json", "x-goog-api-key": api_key}
  Body: {"contents": [{"parts": [{"text": "ping"}]}], "generationConfig": {"maxOutputTokens": 1}}
  ```

---

## 3. Bảng Phân Loại & Xử Lý Mã Lỗi Google API

| Mã HTTP | Tình trạng | Nguyên nhân | Hành động chuẩn |
| :--- | :--- | :--- | :--- |
| **`200 OK`** | **Active** | Key sống, model hỗ trợ | Cập nhật `last_check_time`, tăng bộ đếm lượt gọi, tiếp tục sử dụng. |
| **`429` (Rate/Daily)** | **Exhausted** | Hết Quota hoặc quá tốc độ RPM | **Khóa Cooldown 60 phút (3600s)** cho Daily hoặc theo `retryDelay` (65s) cho RPM. Tự động đổi sang tài khoản khác. |
| **`503` (Overloaded)** | **Active (Busy)** | Server Google quá tải tạm thời | **Giữ nguyên trạng thái Active** (KHÔNG đánh dấu invalid). Đổi sang tài khoản khác với Random Jitter Delay (1.0s - 2.2s). |
| **`401` (Unauthorized)** | **Invalid** | Key sai, bị thu hồi, hoặc Service Account bị xóa/vô hiệu hóa | **Đánh dấu `invalid` vĩnh viễn**. **Ngắt ngay vòng lặp model (Blind Fire)**, chuyển thẳng sang account khác, KHÔNG thử các model tiếp theo trên key chết. |
| **`403` (Forbidden)** | **Invalid / Restrict** | Bị cấm quyền truy cập hoặc giới hạn model | Nếu do quyền tài khoản/billing/service account: đánh dấu `invalid`. Nếu do model restriction: ghi nhớ per-account và chuyển model khác. |
| **`500 / 502 / 504`** | **Server/Network** | Lỗi mạng hoặc hạ tầng Google | Thử lại có giãn cách Exponential Backoff (tối đa 2 lần). |
| **Nội bộ** | **`ALL_BUDGET_EXHAUSTED`** | Tất cả tài khoản trong pool đều đạt ngân sách ngày | **Dừng an toàn toàn bộ pipeline**, lưu checkpoint `session.json`, nghỉ ngơi đến 0h ngày hôm sau. |

---

## 4. Bộ Quy Chuẩn Chống Khóa Tài Khoản Google (Anti-Ban & Anti-Abuse)

Đây là các nguyên tắc sống còn để tránh bị hệ thống Abuse Detection của Google quét và khóa tài khoản:

### 🛡️ 1. Nhịp thở tự nhiên (Human-like Pacing & Jitter)
- **Độ trễ tối thiểu giữa các request**: `2.5s` đến `4.5s`.
- **Độ trễ ngẫu nhiên (Random Jitter)**: Luôn chèn `random.uniform(0.5, 1.5s)` để phá vỡ tần số bot đều đặn.
- **Duy trì tốc độ an toàn**: Dưới **10 Requests / Phút (RPM)** (thấp hơn trần 15 RPM của Google Free Tier).

### 🛡️ 2. Giãn cách trên CÙNG 1 TÀI KHOẢN (`PER_ACCOUNT_MIN_GAP >= 8.0s`)
- Không bao giờ bắn liên tiếp 2 request vào cùng 1 tài khoản trong thời gian ngắn.
- **KHOÁ CỨNG KỂ CẢ KHI CHỈ CÒN 1 ACCOUNT**: Dù trong pool chỉ còn đúng 1 account duy nhất hoạt động, hệ thống vẫn bắt buộc đo khoảng cách từ lần gọi trước. Nếu chưa đủ `8.0s`, chủ động dừng ngủ bù số giây còn thiếu trước khi gửi request tiếp theo để không bao giờ vượt trần RPM.
- Khi có nhiều account: tự động ưu tiên Round-Robin sang các account đã nghỉ ngơi `>= 8.0s`.

### 🛡️ 3. Giới hạn số lần thử lại tối đa (`MAX_ATTEMPTS = 3`)
- Khi gặp lỗi (429, 503), mỗi prompt tối đa chỉ thử qua **3 tài khoản khác nhau**.
- Tuyệt đối không tạo vòng lặp thử dồn dập 8-10 tài khoản trong 1-2 giây vì sẽ bị Google nhận diện là tấn công từ chối dịch vụ (DDoS) và khóa IP/cụm tài khoản.

### 🛡️ 4. Khóa Cooldown 60 Phút nghiêm ngặt
- Tài khoản nào chạm giới hạn `429` phải được đưa vào hàng đợi nghỉ ngơi tối thiểu **60 phút (3600s)**.
- Không gửi thêm bất kỳ request nào đến tài khoản đó trong thời gian cooldown để Google phục hồi 100% hạn mức RPM/TPM tự nhiên.

### 🛡️ 5. Kiểm tra Key hàng loạt an toàn (Safe Bulk Health Check)
- Khi kiểm tra danh sách nhiều key (vd: 50 - 90 keys), bắt buộc chèn độ trễ an toàn **`2.8s - 4.2s/key`**.
- Không bắn dồn dập hàng loạt trong vài giây.

### 🛡️ 6. Phân bổ Key hợp lý (1-2 Key / Tài khoản)
- Mỗi tài khoản Google chỉ nên tạo tối đa **1 - 2 API Keys**. Không tạo dồn dập 10-20 key trên cùng 1 account.
- Hạn ngạch Google Free Tier (1,500 RPD) tính theo **Project / Account**, không tính theo số lượng key. Tạo nhiều key trong 1 project không làm tăng hạn ngạch.

### 🛡️ 7. Quản lý Ngân Sách Theo Từng Account (`DAILY_ACCOUNT_BUDGET = 1000`)
- Đặt trần an toàn cứng là **1,000 calls / ngày / account** (cách xa trần 1,500 RPD của Google để chống quá tải).
- Khi 1 account đạt 1,000 calls: Tự động loại trừ account đó khỏi danh sách chọn cho đến 0h ngày hôm sau, tự động luân chuyển sang account khác.
- Khi toàn bộ account đều đạt ngân sách: Báo mã lỗi nội bộ `ALL_BUDGET_EXHAUSTED` để dừng hệ thống an toàn và lưu checkpoint.

### 🛡️ 8. Bộ đếm Bền vững Qua Phiên Làm Việc (Session-Persistent Call Tracking)
- Theo dõi lượt gọi song song theo ngày `YYYY-MM-DD`: tổng toàn cục, tổng theo account (`email`), tổng theo key.
- Đồng bộ các trường `today_calls`, `today_account_calls`, `call_date` vào đĩa (`settings.json`). Khi ứng dụng khởi động lại giữa ngày, bộ đếm tự động khôi phục, ngăn ngừa việc gọi vượt hạn ngạch do restart app.

---

### 🛡️ 9. Cơ chế Hàng Đợi Cooldown Thông Minh (Smart Cooldown Queue)
- Khi toàn bộ tài khoản trong pool đều đang bị tạm khóa cooldown (do 429 RPM hoặc rate limit):
  - **TUYỆT ĐỐI KHÔNG DỪNG / CRASH TIẾN TRÌNH**.
  - Tính thời gian chờ ngắn nhất đến khi tài khoản sớm nhất hồi phục (`soonest_acct = min(cd_until - now)`).
  - Nếu `wait_sec <= 300s`: Tự động đếm ngược chờ đủ số giây, hiển thị tiến độ cho người dùng và tự động tiếp tục công việc khi tài khoản sẵn sàng.
  - Chỉ dừng khi 100% key trong pool bị `HTTP 401 / Invalid` (chết vĩnh viễn không thể hồi phục).

### 🛡️ 10. Ngắt Lỗi Xác Thực 401 & 400 Dead Key Tức Thì (Instant 401/400 Auth Break)
- Mã lỗi **HTTP 401** và **HTTP 400 ("API key not valid")**:
  - Bao gồm `API_KEY_INVALID`, `The bound service account is deleted or disabled`, và `API key not valid. Please pass a valid API key`.
  - Đây là lỗi của **KEY / ACCOUNT**, hoàn toàn KHÔNG liên quan đến Model.
  - Khi gặp 401 hoặc 400 với thông điệp key không hợp lệ: Đánh dấu key là `invalid` ngay lập tức, ngắt ngay khỏi vòng lặp model (`break`) và chuyển sang account khác (Blind Fire). TUYỆT ĐỐI KHÔNG lặp thử 8 models trên cùng 1 key chết gây lãng phí thời gian và nghẽn luồng.

### 🛡️ 11. Đồng Bộ Động Danh Sách Key In-Memory (Dynamic Pool Hot-Reload)
- Khi người dùng thêm, xóa, sửa hoặc lọc bỏ key lỗi (❌) từ giao diện Quản lý API Key:
  - Hệ thống BẮT BUỘC gọi cập nhật ngay lập tức vào `AccountPool` in-memory đang chạy (`pool.sync(...)`).
  - Hộp thoại Quản lý Key khi đóng bằng bất kỳ cách nào (nút Đóng, Lưu & Áp Dụng, hoặc dấu [X]) đều phải tự động tải lại danh sách key hiển thị trên giao diện chính.
  - Đảm bảo các key vừa bị xóa biến mất khỏi RAM ngay tức khắc, không bao giờ bị gọi lại trong các chương dịch tiếp theo mà không cần khởi động lại ứng dụng.

### 🛡️ 12. Fallback Model Nội Bộ Khi Gặp 429 RPM (Intra-Account Model Fallback)
- Khi một model gặp HTTP 429 RPM (Resource Exhausted tạm thời):
  - **KHÔNG được vội khóa account ngay và ngắt vòng lặp model**: Google cấp hạn ngạch RPM độc lập cho từng model (ví dụ: `gemini-3.5-flash-lite`, `gemini-3-flash-preview`, `gemini-3.5-flash` đều có quota bucket riêng).
  - Hệ thống BẮT BUỘC thử ngay model dự phòng tiếp theo trên cùng account đó trước khi quyết định khóa account.
  - Chỉ khi TẤT CẢ các model khả dụng của account đó đều trả về 429 hoặc gặp 429 Daily Limit, lúc đó mới khóa account đó và chuyển account khác.

### 🛡️ 13. Phân Loại Trực Quan Trạng Thái Key (Tri-State Visual Status & Safe Cleaning)
- Kết quả kiểm tra key phải phân loại rõ ràng 3 trạng thái:
  - `✅` (Xanh): Key hoạt động tốt.
  - `⚠` (Cam): Cảnh báo tạm thời (HTTP 503 Server bận, HTTP 429 Hết quota tạm thời, Timeout mạng) $ightarrow$ **Key vẫn sống**, giữ lại để phục vụ dịch, tuyệt đối không đánh đồng với key hỏng.
  - `❌` (Đỏ): Key chết thực sự (HTTP 401 Unauthorized, HTTP 400 API key not valid, HTTP 403 Service account deleted/disabled/revoked).
- Tính năng "🧹 Xóa Key Lỗi" CHỈ ĐƯỢC PHÉP lọc và xóa các dòng có dấu `❌` đỏ, bảo vệ an toàn 100% cho các dòng `⚠` màu cam.

---

## 5. Kiến trúc Proxy Trung Gian cho Opencode (Local Proxy Architecture)

```
Opencode (baseURL: http://127.0.0.1:8787/v1beta)
     │ (HTTP POST streamGenerateContent)
     ▼
[Gemini Proxy Core / GUI Manager]
     ├─ Round-Robin Account Cluster Picker
     ├─ Safe Human-like Pacing & Jitter (2.5s - 4.5s)
     ├─ Per-Account Spacing Check (>= 8.0s)
     ├─ Error Classifier (200 / 429 Cooldown / 503 Overloaded / 401 Invalid)
     └─ SSE Stream Chunk Forwarder (Catch WinError 10054/10053)
     │
     ▼
https://generativelanguage.googleapis.com/v1beta/...
```

- **Xử lý SSE Streaming**: Khi Opencode ngắt sinh văn bản giữa chừng, client đóng socket $\rightarrow$ Bắt trọn ngoại lệ `BrokenPipeError`, `ConnectionResetError`, `ConnectionAbortedError` để luồng server không bị crash.
