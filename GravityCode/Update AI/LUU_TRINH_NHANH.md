# LƯU TRÌNH KÍCH HOẠT & CỘNG DỒN GOOGLE AI PRO (5 TB)
> **Tài khoản hiện tại**: `svendn03@gmail.com`  
> **Trạng thái hiện tại**: Đã kích hoạt thành công gói 12 tháng (hạn dùng đến `20/11/2027`).

---

## ⚡ 1. Tóm Tắt Nhanh Các Bước Tiếp Theo (Bấm là Chạy)

Sau khi kiểm tra/mở thẻ ngân hàng sẵn sàng thanh toán quốc tế:

| Bước | Mục tiêu | File thực thi (.bat) | Lệnh tương đương (PowerShell/CMD) | Số ngày hiển thị trên giao diện |
|---|---|---|---|---|
| **Bước 1** | 12 tháng (0đ) | `2_Pro_12_thang_Buoc_1.bat` | `python ultra0.py --account "current@device" --no-add --force --plan pro12` | 365 ngày (0đ) — **[ĐÃ XONG]** |
| **Bước 2** | +6 tháng (thành 18 tháng) | `3_Pro_Them_6_thang_Buoc_2.bat` | `python ultra0.py --account "current@device" --no-add --force --stack --plan pro6` | 546 ngày (0đ) — **[ĐÃ XONG]** |
| **Bước 3** | +6 tháng (thành 24 tháng) | `4_Pro_Them_6_thang_Buoc_3.bat` | `python ultra0.py --account "current@device" --no-add --force --stack --plan pro6b` | **728 ngày** (0,00 US$ hôm nay) |
| **Bước 4** | +6 tháng dự phòng (tối đa 30 tháng) | `5_Pro_Du_phong_6_thang.bat` | `python ultra0.py --account "current@device" --no-add --force --stack --plan pro6c` | **910 ngày** (0,00 US$ hôm nay) |

---

## 🔍 2. Dấu Hiệu Nhận Biết "Cộng Dồn Đúng" Trên Màn Hình

Khi hộp thoại thanh toán của Google Play mở lên:
- ✅ **Đúng**: 
  - Hôm nay trừ: **`0,00 US$`** (hoặc `JP¥0`).
  - Dòng mô tả ghi rõ: **`546 ngày (bao gồm 364 ngày được chuyển đổi từ gói hiện tại của bạn)`** (hoặc 728 ngày / 910 ngày ở các bước sau).
- ❌ **Sai / Dừng ngay không bấm xác nhận**:
  - Nếu hiện giá tiền > 0đ (VD: `19.99 US$`).
  - Nếu ghi là trừ tiền ngay hôm nay và không có dòng quy đổi ngày cũ.

---

## 🛠️ 3. Xử Lý Các Lỗi Thường Gặp

### Lỗi 1: "Công ty phát hành thẻ của bạn đã từ chối khoản thanh toán"
- **Nguyên nhân**: Ngân hàng chặn giao dịch xác minh thẻ 0đ của Google, hoặc thẻ ảo/thẻ quốc tế chưa bật tính năng thanh toán trực tuyến/quốc tế.
- **Cách xử lý**:
  1. Vào ứng dụng ngân hàng (Vietcombank, Techcombank, MB, VPBank, Timo...) -> Quản lý thẻ -> Bật **"Thanh toán trực tuyến / quốc tế"** và kiểm tra hạn mức.
  2. Đảm bảo tài khoản có số dư tối thiểu từ 20.000đ - 50.000đ (khoảng 1-2 USD) đề phòng ngân hàng giữ tiền tạm thời để verify rồi hoàn lại.
  3. Hoặc vào CH Play -> Hồ sơ -> Phương thức thanh toán -> Thêm thẻ phụ khác.

### Lỗi 2: Không đọc được purchaseToken (kẹt ở queryPurchases)
- **Đã được fix sẵn**: Hệ thống đã cập nhật cơ chế đọc SQLite WAL (`library.db*`). Script sẽ tự động lấy token mới nhất từ database mà không cần can thiệp thủ công.

### Lỗi 3: Kẹt ở connecting hoặc không mở được cửa hàng Play
- Mở LDPlayer 9 -> Bấm mở ứng dụng **CH Play (Play Store)** lên để chạy nền, sau đó chạy lại script.

---

## ⚠️ 4. Lưu Ý Quan Trọng Về Gia Hạn

- **Tuyệt đối KHÔNG HỦY gói** trong lúc đang cộng dồn giữa các bước. Gói phải ở trạng thái **Đang hoạt động (Active)** thì Google Play mới cho phép nâng cấp và cộng dồn ngày.
- Sau khi đã cộng dồn thành công đủ các bước (18/24/30 tháng), bạn có thể vào `play.google.com/store/account/subscriptions` bấm **Hủy gói đăng ký**.
- **Quyền lợi vẫn giữ nguyên 100%** đến đúng ngày hết hạn (năm 2028), không bị mất sớm, và tránh bị trừ tiền tự động sau khi hết thời hạn khuyến mãi.
