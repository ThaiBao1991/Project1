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
| **`429` (Rate/Daily)** | **Exhausted** | Hết Quota hoặc quá tốc độ RPM | **Khóa Cooldown 60 phút (3600s)** cho tài khoản đó, tự động đổi sang tài khoản khác. |
| **`503` (Overloaded)** | **Active (Busy)** | Server Google quá tải tạm thời | **Giữ nguyên trạng thái Active** (KHÔNG đánh dấu invalid). Đổi sang tài khoản khác với Random Jitter Delay (1.0s - 2.2s). |
| **`401 / 403 / 400`** | **Invalid** | Key bị thu hồi (`API_KEY_INVALID`) | Đánh dấu `invalid` (loại bỏ khỏi pool). |
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
- Nếu phải gọi lại cùng tài khoản, bắt buộc chờ ít nhất **8 - 15 giây** hoặc tự động luân chuyển Round-Robin sang tài khoản khác.

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

---

## 6. Pattern Model Rotation Nâng Cao (2026-10 — GetHtmlFromUrl / ai_translator)

### 6.1. Per-Account Model Restriction (403 per account ≠ global)
- Lỗi `403 + is_model_restriction()` **phụ thuộc vào account GCP**, không phải toàn cục.  
- Account A bị 403 với `gemini-3.8-flash` không có nghĩa account B cũng bị.  
- ✅ Đúng: Lưu vào `_account_restricted_models: Dict[str, Set[str]]` (key = email).  
- ❌ Sai: `self.models.remove(model)` — xóa vĩnh viễn khỏi session, các account khác mất quyền thử.

```python
# Trong _call_api_with_retry:
restricted_for_acct = self._account_restricted_models.get(email, set())
models_to_try = [m for m in self.models if m not in restricted_for_acct]
if not models_to_try:
    # ⚠️ CỰC KỲ QUAN TRỌNG: Dùng continue, TUYỆT ĐỐI KHÔNG dùng break!
    # Đoạn này nằm trực tiếp trong 'while not self.is_stopped:', break sẽ thoát văng khỏi vòng lặp và làm sập pipeline dịch.
    for k in self.pool._keys:
        if self.pool.account_of(k) == email:
            exclude.add(k.get("key", ""))
    account_attempts += 1
    continue

if status == 404 or is_model_restriction(resp_text):
    self._account_restricted_models.setdefault(email, set()).add(model)
    continue  # Không xóa khỏi self.models!
```

### 6.2. had_real_response Flag — Phân Biệt "403 Restriction" vs "Empty Content"
- **Bug hay gặp**: Đếm "all_empty_rounds" cả khi toàn bộ models bị 403 (không phải empty thật).  
- Sau 3 account đều 403 → báo lỗi "safety filter" sai — thực ra chưa model nào được thử thật sự.  
- ✅ Giải pháp: `had_real_response = False` trước for loop; set `True` khi `status == 200`.

```python
had_real_response = False
for model in models_to_try:
    ...
    if status == 200:
        had_real_response = True
        ...

# Sau for loop:
if had_real_response:
    all_empty_rounds += 1        # Empty thật → tăng counter
    if all_empty_rounds >= MAX_EMPTY_ROUNDS:
        return False, "", "Safety filter blocked..."
else:
    pass  # 403/restriction → KHÔNG tăng, xoay account tiếp
exclude.add(api_key)
```

### 6.3. all_empty_rounds Guard — Thoát Khỏi Infinite Empty Loop
- Khi tất cả models đều trả về HTTP 200 nhưng content rỗng (bị safety filter), for loop kết thúc bình thường → while loop pick lại key cũ → **loop vô tận**.  
- ✅ Giải pháp: `all_empty_rounds` counter + `MAX_EMPTY_ROUNDS = 3`. Sau 3 lần HTTP-200-but-empty thực sự → return lỗi rõ ràng.  
- ✅ Kết hợp `exclude.add(api_key)` sau for loop để đảm bảo pick account mới mỗi round.

### 6.4. safetySettings BLOCK_NONE — Bypass Safety Filter Cho Văn Học
- Tiểu thuyết tu tiên có thể trigger Gemini safety filter (nội dung bạo lực, trang phục, v.v.) → response HTTP 200 nhưng `finishReason = "SAFETY"`.  
- ✅ Thêm `safetySettings` vào mọi request body:

```json
"safetySettings": [
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",  "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH",        "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT",  "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HARASSMENT",         "threshold": "BLOCK_NONE"}
]
```

- ✅ Detect `finishReason == "SAFETY"` → log riêng `🚫 SAFETY FILTER`, không đếm vào empty_count.  
- ⚠️ Lưu ý: `BLOCK_NONE` không bypass hard-coded policy của Google. Content hoàn toàn bị cấm vẫn sẽ bị chặn.

### 6.5. 503 Server Overload — Chờ Trước Khi Thử Model Tiếp
- 503 = Server quá tải tạm thời, **KHÔNG liên quan đến nội dung hay account**.  
- ❌ Sai: Chuyển model ngay lập tức → hammer tất cả 8 models trong vài giây → aggravate overload.  
- ✅ Đúng: Đẩy model xuống cuối queue + chờ **10s** trước khi thử model tiếp.

```python
if status in (500, 503):
    self.models.remove(model); self.models.append(model)
    for _ in range(10):
        if self.is_stopped: return False, "", "Stopped"
        time.sleep(1.0)
    continue
```

### 6.6. Không Promote Model Thành Công Lên Đầu List
- Pattern cũ: Khi model X thành công → `self.models.insert(0, X)` → phá vỡ thứ tự ưu tiên đã cấu hình.  
- Sau nhiều request, tất cả call dồn vào model X → rate limit tập trung → 429 liên tục.  
- ✅ Đúng: Giữ nguyên thứ tự `self.models` (từ settings.json), chỉ reset `_model_consecutive_empty[model] = 0` khi thành công.

---
