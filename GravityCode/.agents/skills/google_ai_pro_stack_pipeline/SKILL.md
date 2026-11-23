---
name: google_ai_pro_stack_pipeline
description: Quy trình tự động kích hoạt và cộng dồn thời hạn Google AI Pro (5 TB) từ 12 tháng lên đến 30 tháng thông qua Frida Hook BillingClient, trích xuất token từ SQLite WAL của Google Play và xử lý nâng cấp thuê bao (SubscriptionUpdateParams CHARGE_FULL_PRICE).
---

# Google AI Pro (5 TB) Subscription Stacking Pipeline

Kỹ thuật và quy trình chuẩn để mở dùng thử và cộng dồn các gói ưu đãi Google AI Pro (5 TB) qua Android Google Play Billing Client Hook trên giả lập (LDPlayer 9 / MuMu).

---

## 1. Cơ Chế Kiến Trúc Nâng Cấp & Cộng Dồn (Subscription Proration)

Google Play Store không cho phép mua trùng cùng một gói cước ưu đãi nếu mua trực tiếp. Để cộng dồn thời gian dùng thử (ví dụ: 12 tháng + 6 tháng = 18 tháng = 546 ngày), hệ thống bắt buộc phải đi qua cơ chế nâng cấp gói thuê bao (`SubscriptionUpdateParams`):

1. **Đọc `purchaseToken` hiện tại**:
   - `purchaseToken` của gói đang hoạt động được lưu trong bảng `ownership` của database Google Play: `/data/data/com.android.vending/databases/library.db`.
   - **Lưu ý chí mạng về SQLite WAL**: Google Play Store luôn chạy ở chế độ SQLite WAL (Write-Ahead Logging). Khi có giao dịch mới (vừa mua 12 tháng), dữ liệu chỉ nằm trong file `library.db-wal` và `library.db-shm`. Nếu chỉ copy `library.db`, SQLite sẽ không đọc được giao dịch mới! Bắt buộc phải copy đồng thời cả `library.db*` (hoặc thực hiện checkpoint) để đọc được token mới nhất.

2. **Cấu hình tham số nâng cấp (`BillingFlowParams`)**:
   - Sử dụng `BillingFlowParams.SubscriptionUpdateParams`:
     ```java
     var SUP = Java.use("com.android.billingclient.api.BillingFlowParams$SubscriptionUpdateParams");
     var sb = SUP.newBuilder();
     sb = sb.setReplaceProrationMode(5); // 5 = CHARGE_FULL_PRICE
     sb = sb.setOldPurchaseToken(oldToken);
     billingFlowParams = billingFlowParams.setSubscriptionUpdateParams(sb.build());
     ```
   - Chế độ `5 (CHARGE_FULL_PRICE)` báo cho Google Play quy đổi toàn bộ thời gian dùng thử còn lại của gói cũ và cộng dồn trực tiếp vào kỳ thanh toán đầu tiên của gói mới.

3. **Màn hình xác nhận hợp lệ**:
   - Số tiền hôm nay: `0,00 US$` (hoặc `JP¥0`).
   - Thời hạn: `546 ngày` (Bước 2), `728 ngày` (Bước 3), `910 ngày` (Bước 4).

---

## 2. Quy Trình 4 Bước Cộng Dồn

| Thứ tự | Plan ID | Thời hạn cộng dồn | File thực thi |
|---|---|---|---|
| **Bước 1** | `pro12` (`12months-eft`) | 12 tháng (365 ngày) | `2_Pro_12_thang_Buoc_1.bat` |
| **Bước 2** | `pro6` (`6months-eft`) | 18 tháng (546 ngày) | `3_Pro_Them_6_thang_Buoc_2.bat` |
| **Bước 3** | `pro6b` (`6months-eft-2`) | 24 tháng (728 ngày) | `4_Pro_Them_6_thang_Buoc_3.bat` |
| **Bước 4 (Dự phòng)** | `pro6c` (`6months-eft-ss-2026`) | 30 tháng (910 ngày) | `5_Pro_Du_phong_6_thang.bat` |

---

## 3. Checklist Khắc Phục Sự Cố

- **Lỗi thẻ bị từ chối**: Do ngân hàng chặn auth 0đ quốc tế -> Bật "Thanh toán quốc tế/trực tuyến" trên app ngân hàng hoặc đổi thẻ Visa/Mastercard khác trên CH Play.
- **Lỗi không cộng dồn ngày mà trừ tiền luôn**: Do gói đăng ký đã bị hủy (Cancel) trước khi stack -> **Quy tắc vàng**: Gói phải luôn ở trạng thái "Đang hoạt động" trong suốt các bước cộng dồn. Chỉ bấm hủy gia hạn sau khi đã cộng dồn xong toàn bộ các bước.
- **Kẹt tiến trình CH Play**: Chạy `adb shell am force-stop com.android.vending && am start -n com.android.vending/com.google.android.finsky.activities.MainActivity`.

---

## 4. Quy Chuẩn Tổ Chức Thư Mục Dự Án (Workspace Hygiene)

Nhằm giữ workspace luôn gọn gàng và bảo mật dữ liệu quản trị:
1. **Thư mục `temp/`**:
   - Chứa toàn bộ file tạm sinh ra trong quá trình chạy tự động: ảnh chụp màn hình (`*.png`), file XML phân tích giao diện (`*.xml`), cơ sở dữ liệu tạm thời (`*.db`), và log nháp.
   - Các file trong `temp/` có thể xóa bất kỳ lúc nào mà không làm ảnh hưởng đến mã nguồn dự án.
2. **Thư mục `AdminData/`**:
   - Chứa toàn bộ file văn bản quản trị và dữ liệu nhạy cảm: `Pass.txt` (danh sách mật khẩu), `ma the ngan hang.txt` (thông tin thẻ thanh toán), `Huong_dan_su_dung.txt`.
   - Các script tự động phải ưu tiên đọc từ `AdminData/` trước khi fallback về thư mục gốc.

---

## 5. Quy Chuẩn Xoay IP & Đổi Danh Tính Thiết Bị (Anti-Fingerprint / IP & Device Rotation)

Khi gặp lỗi Google từ chối ưu đãi trial: *"Mặt hàng bạn đã yêu cầu không sẵn có cho đơn mua hàng."*:

1. **Bản chất**: Google Risk Engine kích hoạt cơ chế phát hiện lạm dụng (Anti-Abuse) khi cùng một địa chỉ IP mạng hoặc cùng một định danh thiết bị phần cứng (Android ID, IMEI, MAC Address) đăng ký dùng thử liên tiếp nhiều tài khoản.
2. **Quy trình Xoay IP Mạng (Network IP Rotation)**:
   - Tắt nguồn modem WiFi khoảng 30 giây rồi bật lại để nhận dải Public IP mới từ nhà mạng (ISP).
   - Kiểm tra xác nhận Public IP mới qua `https://api.ipify.org?format=json`.
3. **Quy trình Đổi mới Danh tính LDPlayer (Hardware Identity Rotation)**:
   - Tắt hoàn toàn giả lập (`ldconsole quit --index 0`).
   - Dùng lệnh LDConsole CLI để sinh mới 100% định danh phần cứng:
     ```bash
     ldconsole modify --index 0 --manufacturer samsung --model SM-S918B --imei auto --imsi auto --simserial auto --androidid auto --mac auto
     ```
   - Cấp mới: `Android ID` (16 hex), `IMEI` (15 số), `IMSI` (15 số), `SIM Serial` (20 số), `MAC Address` (12 hex), chuyển Model sang thiết bị cao cấp mới (`SM-S918B` - Samsung Galaxy S23 Ultra).
   - Khởi động lại giả lập và tiếp tục quy trình cho tài khoản mới.
