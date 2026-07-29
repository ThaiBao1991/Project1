# 🔋 Quota Antigravity Tracker — Hướng dẫn sử dụng

> Extension theo dõi quota AI cho nhiều tài khoản Google trong Antigravity IDE.

---

## 📦 Yêu cầu

- **Antigravity IDE** (VSCode-based)
- Extension đã được cài vào thư mục:  
  `C:\Users\<tên_máy>\.antigravity-ide\extensions\antigravity.quota-antigravity-ext-1.0.0\`

---

## 🚀 Thiết lập lần đầu (Bắt buộc)

### Bước 1 — Xác nhận extension đã chạy

Sau khi mở IDE, nhìn vào **thanh Status Bar** (góc dưới bên phải màn hình).  
Bạn sẽ thấy dòng chữ kiểu: `$(account) your@gmail.com | Quota OK`.

> Nếu không thấy: nhấn `F1` → gõ `Developer: Reload Window` → Enter.  
> Nếu vẫn không thấy: tắt hẳn IDE và mở lại.

### Bước 2 — Chọn thư mục lưu File Data

**Click vào dòng chữ trên Status Bar** hoặc nhấn `F1` → `Quota: Mở bảng Quota Tracker`.

Lần đầu, bảng sẽ hiện banner cảnh báo màu vàng:
```
⚠️ Chưa chọn thư mục lưu Data. [Thiết lập ngay]
```
- Click nút **Thiết lập ngay** → hộp thoại chọn thư mục hiện ra
- Trỏ đến thư mục bạn muốn (ví dụ: `CTApp\QuotaAntigravity\`)
- IDE tự tạo file `quota_data.json` trong thư mục đó

---

## 🖥️ Bảng Quota Tracker (WebView Panel)

Click vào **Status Bar** để mở bảng đầy đủ:

```
🔋 Quota Antigravity Tracker          [your@gmail.com]

[🔴 Đánh dấu Hết Quota]  [📁 Đổi thư mục Data]  [🔄]

[🔍 Tìm email...]   [Tất cả]  [✅ Sẵn sàng]  [🔴 Hết quota]

📊 Tổng: 5   ✅ Sẵn sàng: 3   🔴 Hết quota: 2

Email               Trạng thái   Còn lại      Reset lúc
─────────────────────────────────────────────────────────
🔴 abc@gmail.com    🔴 Hết quota  18h 42m     29/07 08:00
🔴 xyz@gmail.com    🔴 Hết quota   5h 10m     28/07 18:00   ← đang dùng
✅ test@gmail.com   ✅ Sẵn sàng    —           —            [Đánh dấu hết]
✅ work@gmail.com   ✅ Sẵn sàng    —           —            [Đánh dấu hết]
```

**Tính năng bảng:**

| Tính năng | Mô tả |
|---|---|
| **Tìm kiếm** | Gõ tên email để lọc ngay |
| **Filter** | Xem Tất cả / Chỉ Sẵn sàng / Chỉ Hết quota |
| **Sort** | Click vào tiêu đề cột để sắp xếp |
| **Màu sắc** | 🔴 đỏ = hết quota, ✅ xanh = sẵn sàng |
| **Countdown** | Hiển thị thời gian còn lại trực quan |
| **Đánh dấu** | Nút [Đánh dấu hết] ngay trên từng dòng |
| **Auto-refresh** | Bảng tự cập nhật mỗi 30 giây |

---

## ⚡ Phím tắt cực nhanh

### `Alt + Q` — Đánh dấu hết quota ngay tức thì

Khi AI báo lỗi:
1. Nhấn **`Alt + Q`** — không cần mở menu, không cần click chuột
2. Extension lập tức đánh dấu email đang đăng nhập hết quota (24h)
3. Thông báo popup xuất hiện xác nhận

> ⚡ Đây là cách **nhanh nhất** — 1 phím duy nhất, không cần nhìn vào màn hình

---

## 🤖 Auto-Detect (Thực nghiệm)

Extension thử **tự động phát hiện** khi AI ngừng phản hồi thông qua `vscode.lm` API:
- Mỗi **30 giây**, extension kiểm tra xem AI models còn available không
- Nếu models biến mất → popup hỏi: *"AI có vẻ không phản hồi, đánh dấu hết quota?"*
- Bạn chọn **Đánh dấu ngay** hoặc **Bỏ qua**

> ⚠️ **Lưu ý**: Tính năng này thực nghiệm, có thể báo nhầm. Hãy xác nhận thật sự bị hết quota trước khi đánh dấu.

---

## 🔴 Quy trình hằng ngày

**Khi AI báo lỗi "Hết Quota / Resource Exhausted":**

1. Nhấn **`Alt + Q`** ← cách nhanh nhất
2. Hoặc click Status Bar → nhấn **[🔴 Đánh dấu Hết Quota]**
3. Extension ghi nhận email vào `quota_data.json`, reset sau 24h
4. Đổi tài khoản Google trong IDE sang email khác → làm việc tiếp

---

## ⌨️ Tất cả phím tắt & lệnh

Nhấn `F1` và gõ `Quota:` để thấy tất cả lệnh:

| Lệnh / Phím tắt | Chức năng |
|---|---|
| **`Alt + Q`** | Đánh dấu email hiện tại hết quota ngay lập tức |
| `Quota: Mở bảng Quota Tracker` | Mở WebView Panel đầy đủ |
| `Quota: Đánh dấu Hết Quota` | Đánh dấu email hiện tại hết quota |
| `Quota: Chọn thư mục lưu file Data` | Đổi vị trí lưu `quota_data.json` |
| `Quota: Làm mới danh sách` | Refresh TreeView sidebar |

---

## 📁 File Data (quota_data.json)

File JSON lưu trạng thái quota. Cấu trúc:

```json
{
  "abc@gmail.com": {
    "exhaustedUntil": 1753850400000,
    "lastUpdate": 1753764000000
  },
  "xyz@gmail.com": {
    "exhaustedUntil": 1753936800000,
    "lastUpdate": 1753850400000
  }
}
```

- `exhaustedUntil`: timestamp (ms) lúc quota reset. Nếu < `Date.now()` → email đã sẵn sàng
- File này **dùng chung** với QuotaApp Python nếu trỏ cùng đường dẫn

---

## 🔄 Tích hợp với QuotaApp (Python UI)

```
[IDE Extension] ──write──▶ quota_data.json ◀──read── [QuotaApp Python]
```

Không cần đồng bộ thủ công. Chỉ cần cùng trỏ đến 1 file.

---

## ❓ FAQ

**Q: Extension có tự reset sau 24h không?**  
A: Có. Bảng tự cập nhật mỗi 30 giây, Status Bar cập nhật mỗi phút. Không cần làm gì thêm.

**Q: IDE không tìm được email tự động?**  
A: Extension hỏi nhập email thủ công. Nhập email rồi Enter.

**Q: Muốn thay đổi thời gian reset khác 24h?**  
A: Mở `extension.js`, tìm `24 * 3600000` và đổi số theo ý muốn (đơn vị milliseconds).

**Q: Dùng chung file data trên nhiều máy?**  
A: Được — đặt `quota_data.json` vào OneDrive/Google Drive, hai máy trỏ cùng đường dẫn.
