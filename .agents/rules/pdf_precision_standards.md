# PDF Precision & Coordinate Standards

Áp dụng cho mọi tác vụ liên quan đến đọc, vẽ, trích xuất hoặc đóng dấu PDF bằng Python (PyMuPDF / fitz) hoặc JavaScript.

---

## 1. Nguyên Tắc Về Đơn Vị Đo & Hệ Tọa Độ
- **Chuẩn PDF Vector**: 1 inch = 72 points (DPI cơ sở = 72). Khổ A4 đứng chuẩn = $595.3 \times 841.9$ points.
- **Không giả định 1 pixel = 1 point**:
  - Khi render PDF ra ảnh pixmap để hiển thị lên màn hình (Canvas/GUI), nếu dùng matrix zoom $k$ (ví dụ: $2.0 \approx 144$ DPI), kích thước ảnh sẽ gấp $k$ lần kích thước PDF gốc.
  - Mọi tọa độ người dùng click trên màn hình BẮT BUỘC phải quy đổi ngược về PDF points bằng công thức:
    $$\text{pdf\_x} = \text{canvas\_x} \times \left(\frac{\text{page\_width\_pt}}{\text{canvas\_width\_px}}\right)$$
    $$\text{pdf\_y} = \text{canvas\_y} \times \left(\frac{\text{page\_height\_pt}}{\text{canvas\_height\_px}}\right)$$

---

## 2. Quy Tắc Chèn Ảnh & Đóng Dấu (PyMuPDF)
1. **Bảo toàn tỷ lệ gốc (`keep_proportion=True`)**:
   Khi chèn con dấu tròn hoặc chữ ký số, luôn bật `keep_proportion=True` trong `page.insert_image(rect, ...)` để tránh biến dạng méo hình khi kích thước `rect` không vuông hoàn hảo.
2. **Đối xứng quanh tâm (Center Placement)**:
   Tính toán vùng `fitz.Rect(cx - w/2, cy - h/2, cx + w/2, cy + h/2)` thay vì neo theo góc trên bên trái, giúp con dấu luôn nằm chính giữa ô ký tên.
3. **Tối ưu dung lượng khi lưu**:
   Luôn dùng `doc.save(output_path, garbage=4, deflate=True)` để dọn rác đối tượng thừa và nén luồng PDF sau khi đóng dấu hàng loạt.

---

## 3. Khử Lệch Tọa Độ Khi Xuất Từ Excel Sang PDF
- Excel tự động co giãn `Row Height` theo độ phân giải màn hình hoặc máy in mặc định.
- Để tọa độ con dấu trên PDF xuất ra khớp 100% với Server:
  - Cố định chiều cao dòng Excel bằng số điểm tuyệt đối (Row Height cố định, không dùng AutoFit).
  - Không thay đổi Page Setup (Margins, Scaling: Fit to 1 page wide) giữa các máy trạm.

