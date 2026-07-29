---
name: gemini_api_key_handling
description: Hướng dẫn xử lý API Key của Gemini (Google Cloud & AI Studio), cơ chế xoay key (key rotation), xử lý lỗi 429 (Quota) và lỗi 401/403 của các loại key đặc biệt (như AQ. prefix). Kỹ thuật Blind Fire.
---

# Kỹ năng xử lý Gemini API Keys & Key Rotation

Đây là bộ quy tắc bắt buộc khi lập trình các module gọi Google Gemini API (như `ai_agent.py` hay `auto_ai_worker.py`) có sử dụng danh sách nhiều API Keys.

## 1. Các định dạng API Key của Google
- **`AIza...`**: Định dạng truyền thống của Google API Key (tạo từ Google Cloud Console hoặc Google AI Studio).
- **`AQ....`**: Định dạng mới thường gặp trong các dự án Cloud hoặc Vertex AI / OIDC auth. Mặc dù trông giống một mã OAuth Token, nhưng nó vẫn được chấp nhận khi truyền qua tham số query `?key=...`.

## 2. Lỗi kinh điển: "Thông minh quá hóa ngu" (GET /models)
Khi sử dụng nhiều API Key, các Agent thường có xu hướng viết hàm "kiểm tra key này hỗ trợ những model nào" bằng cách gọi:
`GET https://generativelanguage.googleapis.com/v1beta/models?key={api_key}`

**⚠️ Cảnh báo:** Tuyệt đối KHÔNG sử dụng phương pháp này! 
- Với các key định dạng `AQ.`, API Gateway của Google sẽ nhận nhầm đó là một mã OAuth Token không hợp lệ cho endpoint `/models` và lập tức ném lỗi `401 Unauthorized` (Kèm thông báo `ACCESS_TOKEN_TYPE_UNSUPPORTED`).
- Hậu quả: Tool của bạn sẽ lầm tưởng Key đã chết và vứt bỏ nó, trong khi thực tế Key đó vẫn hoạt động hoàn hảo cho việc `generateContent`.

## 3. Kỹ thuật chuẩn: Blind Fire (Bắn thẳng)
- Không đi đường vòng. Ghép trực tiếp Key vào endpoint POST để sinh nội dung, sử dụng model mới nhất (vd: `gemini-flash-latest`).
- URL chuẩn: `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}`
- Nếu request thất bại do Model không hỗ trợ hoặc key sai, ta bắt mã lỗi HTTP (400, 401, 403, 429) để quyết định số phận của Key.

## 4. Bắt lỗi HTTP Code chuẩn xác
Khi thực hiện **Blind Fire**, đây là cách phân loại trạng thái Key:

- **HTTP 200 OK**: Key vẫn sống và model hỗ trợ. Cập nhật thời gian `last_check_time` và đổi status thành `active`.
- **HTTP 429 (Too Many Requests)** hoặc trong Error Message có chứa `"Quota"` / `"exhausted"`:
  - Key đã hết hạn mức sử dụng (Rate limit / Daily quota).
  - Hành động: Đánh dấu status là `exhausted`. Chuyển sang Key tiếp theo. Khôi phục lại trạng thái `active` sau 3 giờ (hoặc tuỳ setting).
- **HTTP 400, 401, 403**:
  - Đọc kỹ thông báo lỗi trả về trong JSON (trường `message` hoặc `reason`).
  - Nếu thông báo có chứa `API_KEY_INVALID` hoặc `invalid authentication credentials`: Key này đã bị Google thu hồi, xoá bỏ, hoặc sai cú pháp hoàn toàn. Đánh dấu status = `invalid` (vứt bỏ vĩnh viễn).
  - Nếu thông báo lỗi chỉ là "Model not found" hoặc lỗi do payload quá dài, v.v., thì giữ nguyên Key và **đổi Model khác** (vd đổi từ `gemini-2.0-flash` lùi xuống `gemini-1.5-flash`).

## 5. Lưu trữ & Mã hoá Key (Base64)
- Khi lưu Key vào file config (JSON), nên dùng Base64 và nối thêm tiền tố `ENC:` để tránh bị lộ khi chia sẻ file.
- Luôn phải có hàm `decode_key(raw_key)` bắt tiền tố `ENC:` để decode ra Key gốc trước khi đưa vào URL `?key=...`.

```python
def decode_key(raw_key):
    if raw_key.startswith("ENC:"):
        try:
            import base64
            return base64.b64decode(raw_key[4:]).decode("utf-8")
        except Exception:
            return raw_key
    return raw_key
```
