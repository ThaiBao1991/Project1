# Enterprise Intranet & Browser Addon Standards

Áp dụng cho mọi tiện ích mở rộng trình duyệt (Edge/Chrome Manifest V3) thao tác trên các hệ thống doanh nghiệp (Intramart, ERP nội bộ, cổng thông tin bảo mật CSP cao).

---

## 1. Cấu Trúc Khung Mẫu & Phân Tầng Iframe
- **Cấu hình `all_frames: true`**: Hầu hết các hệ thống ERP chia tách menu và màn hình xử lý thành các thẻ `<frame>` hoặc `<iframe>`. Content script bắt buộc phải kích hoạt `all_frames: true` và `match_about_blank: true` để lắng nghe được DOM bên trong các frame con.
- **Xác định Frame Đích Trước Khi Chạy**:
  Kiểm tra URL hoặc sự tồn tại của form nghiệp vụ đặc thù trước khi kích hoạt logic tự động:
  ```javascript
  if (!document.querySelector('#target_form_id') && !window.location.href.includes('process_action')) {
    return; // Frame không liên quan, thoát sớm
  }
  ```

---

## 2. Vượt Rào Cản CSP & Giả Lập Chuỗi Sự Kiện Chuột
1. **Tuyệt đối không dùng `eval()` hoặc chèn `<script>` inline**: Vi phạm chính sách CSP của hệ thống doanh nghiệp sẽ khiến Extension bị chặn ngay lập tức.
2. **Kích hoạt đủ chuỗi 5 sự kiện chuột**:
   Các framework giao diện doanh nghiệp thường chặn sự kiện click ảo đơn lẻ. BẮT BUỘC gửi chuỗi:
   `pointerdown` $\rightarrow$ `mousedown` $\rightarrow$ `pointerup` $\rightarrow$ `mouseup` $\rightarrow$ `click`.
3. **Thao tác mượt mà & Đợi DOM ổn định**:
   Sau khi click nút "Chọn tất cả" hoặc chuyển tab, duy trì độ trễ tối thiểu `300ms - 600ms` để DOM hoàn tất render trước khi click bước kế tiếp.

---

## 3. An Toàn Trong Vòng Lặp Duyệt Hàng Loạt (Batch Loop Safety)
- **Giới hạn số vòng lặp tối đa (`max_rounds`)**: Đặt trần an toàn (ví dụ: tối đa 50 lần duyệt trong 1 phiên) để tránh rơi vào vòng lặp vô hạn khi hệ thống báo lỗi hoặc mạng chập chờn.
- **Logging rõ ràng & Trực quan**: Hiển thị trạng thái xử lý (số bản ghi đã duyệt thành công / thất bại) trên giao diện popup hoặc góc màn hình để người dùng nắm rõ tiến độ.

