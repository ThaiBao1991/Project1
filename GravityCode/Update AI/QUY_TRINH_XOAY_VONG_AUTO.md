# QUY TRÌNH TỰ ĐỘNG XOAY VÒNG TÀI KHOẢN GOOGLE AI PRO (24 THÁNG)

Tài liệu này chuẩn hóa quy trình tự động hóa kích hoạt gói cước Google AI Pro (5 TB) 24 tháng cho toàn bộ danh sách tài khoản Google trên giả lập Android (LDPlayer 9).

---

## 1. Nguyên Tắc Cốt Lõi (Core Principles)
- **Mục tiêu mỗi account**: Đạt đúng **24 tháng** (hoặc 18/24 tháng).
- **Chuỗi gói cước**:
  1. `pro12` (12 tháng 0đ).
  2. `pro6` (+6 tháng = 18 tháng 0đ, dùng `--stack`).
  3. `pro6b` (+6 tháng = 24 tháng 0đ, dùng `--stack`).
- **An toàn thẻ tín dụng**:
  - Chỉ gắn thẻ khi tài khoản chưa có phương thức thanh toán.
  - Ngay sau khi hoàn thành 24 tháng (hoặc nếu dính cờ rủi ro), BẮT BUỘC gỡ thông tin thẻ ra khỏi tài khoản ngay lập tức.
- **Giải phóng Primary Account**:
  - Google Play Billing Client trên Android luôn ưu tiên Account 1 (Tài khoản đầu tiên trên máy).
  - Do đó, khi 1 tài khoản hoàn thành 24 tháng, sau khi gỡ thẻ, ta **Xóa (Remove) tài khoản đó khỏi máy giả lập** để tài khoản tiếp theo tự động trở thành Account 1.
- **Xử lý rủi ro & Giới hạn thử (Max 5 lần)**:
  - Nếu gặp lỗi rủi ro Google (`[OR-REH-04]`, Google bắt xác minh danh tính): Ghi nhận tình trạng, gỡ thẻ (nếu có), chuyển tài khoản khác.
  - Nếu bất kỳ bước nào thử quá 5 lần không thành công: Dừng, lưu log và chuyển tài khoản tiếp theo.

---

## 2. Các Bước Vận Hành Chi Tiết

### Bước 1: Xử lý tài khoản đã hoàn thành (`svendn03@gmail.com`)
1. Kiểm tra & gỡ thẻ thanh toán ra khỏi `svendn03@gmail.com` qua `https://play.google.com/store/paymentmethods`.
2. Xóa tài khoản `svendn03@gmail.com` khỏi máy giả lập LDPlayer qua Android Account Settings.
3. Xác nhận tài khoản tiếp theo (`gamesvendn@gmail.com`) đã lên làm tài khoản chính.

### Bước 2: Vòng lặp tự động cho tài khoản mục tiêu
1. **Kiểm tra trạng thái thẻ**:
   - Nếu chưa có: Nhập thẻ từ `ma the ngan hang.txt` (Visa 2646 / 03/30 / CVV 680).
2. **Kích hoạt lần 1 (`pro12`)**:
   - Đảm bảo Google One và Google Play đồng bộ tài khoản.
   - Inject Frida gọi BillingClient `12months-eft`.
   - Kiểm tra xác nhận 0đ và bấm Đăng ký.
3. **Cộng dồn lần 2 (`pro6`)**:
   - Đọc `purchaseToken` từ `library.db-wal`.
   - Inject Frida với `--stack --plan pro6`.
   - Xác nhận dời hạn thêm 6 tháng (18 tháng) 0đ.
4. **Cộng dồn lần 3 (`pro6b`)**:
   - Đọc `purchaseToken` mới nhất.
   - Inject Frida với `--stack --plan pro6b`.
   - Xác nhận dời hạn thêm 6 tháng (24 tháng) 0đ.
5. **Gỡ thẻ thanh toán**:
   - Mở Cài đặt thanh toán -> Xóa thẻ Visa 2646.
6. **Xóa tài khoản khỏi máy giả lập**:
   - Xóa tài khoản vừa xong để nhường quyền cho tài khoản kế tiếp.

---

## 3. Lệnh Kiểm Tra Nhanh
- Kiểm tra danh sách tài khoản: `adb shell dumpsys account`
- Kiểm tra database gói cước: `python check_all_accounts.py`
