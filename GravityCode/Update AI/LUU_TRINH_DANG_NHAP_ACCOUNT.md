# Quy Trình Tự Động Đăng Nhập Tài Khoản Google Vào Giả Lập LDPlayer 9

Tài liệu này lưu trữ lưu trình tự động hóa đăng nhập hàng loạt tài khoản Google (`gamesvendn25` - `gamesvendn30`...), xử lý bỏ qua các màn hình cập nhật thông tin cá nhân và thông báo theo đúng quy chuẩn.

---

## 1. Lưu Trình Chuẩn (Flow Chart)

```
[Mở Cài Đặt Thêm Tài Khoản]
   am start -a android.settings.ADD_ACCOUNT_SETTINGS
          ↓
[Chọn 'Google'] -> tap(97, 99) hoặc tap_text("Google")
          ↓
[Nhập Email]
  Trường EditText tại (480, 314) -> input text <email> -> bấm TIẾP THEO (889, 514)
          ↓
[Nhập Mật Khẩu]
  Trường EditText tại (480, 292) -> input text <pass_1: satthubibon> -> bấm TIẾP THEO (889, 514)
  *Nếu báo "Mật khẩu không chính xác"*: Xóa và nhập <pass_2: satthubibon01>
          ↓
[Vòng Lặp Bỏ Qua Thông Báo & Cập Nhật]
  ├─ 1. Màn hình "Đảm bảo rằng bạn luôn có thể đăng nhập" (Số điện thoại / email khôi phục):
  │     Cuộn màn hình: input swipe 500 500 500 100
  │     Bấm: "Huỷ" tại (308, 495)
  ├─ 2. Màn hình "Đặt địa chỉ nhà riêng" (Home address):
  │     Bấm: "Bỏ qua" tại (780, 504)
  ├─ 3. Màn hình "Tôi đồng ý" (Terms of Service):
  │     Bấm: "Tôi đồng ý" tại (717, 492)
  ├─ 4. Màn hình "Dịch vụ của Google" (Sao lưu):
  │     Bấm: "Xem thêm" -> "Chấp nhận"
  └─ 5. Màn hình "Để sau" / "Không cảm ơn" / "Skip":
        Bấm: "Để sau" / "Bỏ qua"
          ↓
[Xác Minh Hoàn Tất]
  Kiểm tra lệnh dumpsys account: Tài khoản xuất hiện trong danh sách thiết bị.
```

---

## 2. Bảng Tọa Độ Chuẩn Trên Độ Phân Giải 960x540 (LDPlayer 9)

| Màn hình | Nút / Trường | Class | Tọa độ chuẩn (x, y) |
|---|---|---|---|
| Danh sách thêm tài khoản | **Google** | TextView | `(97, 99)` |
| Nhập Email | Ô nhập Email | EditText | `(480, 314)` |
| Nhập Email | Nút TIẾP THEO | Button | `(889, 514)` |
| Nhập Mật khẩu | Ô nhập Mật khẩu | EditText | `(480, 292)` |
| Nhập Mật khẩu | Nút TIẾP THEO | Button | `(889, 514)` |
| Hỏi số điện thoại / Khôi phục | Nút Huỷ (sau khi vuốt) | Button | `(308, 495)` |
| Hỏi địa chỉ nhà | Nút Bỏ qua | Button | `(780, 504)` |
| Điều khoản dịch vụ | Nút Tôi đồng ý | Button | `(717, 492)` |

---

## 3. Lệnh Tự Động Hóa Một Chạm

Chạy script tự động nạp toàn bộ danh sách tài khoản:
```powershell
$env:PATH += ";D:\LDPlayer\LDPlayer9"
python -X utf8 auto_login_accounts.py
```
