---
name: pdf_coordinate_stamping
description: Precision coordinate conversion between GUI screen canvas (pixels) and vector PDF documents (points) using PyMuPDF (fitz) or browser DOM. Use when building or debugging PDF digital stamp tools, signature placement, bounding-box selection, offset alignment, or converting screen interaction to exact PDF print coordinates.
---

# PDF Precision Coordinate & Stamping Architecture

Tài liệu hướng dẫn và đặc tả kỹ thuật quy đổi hệ tọa độ giữa giao diện hiển thị (Canvas/DOM) và văn bản PDF chuẩn vector (72 points/inch) bằng Python (PyMuPDF / fitz) hoặc JavaScript.

---

## 1. Bản Chất Hệ Tọa Độ & Đơn Vị Đo

Trong xử lý tài liệu kỹ thuật số:
- **Màn hình hiển thị (Canvas / Web DOM)**: Đơn vị là **Pixels** (px), phụ thuộc vào độ phân giải màn hình, tỷ lệ zoom và kích thước khung vẽ.
- **Tài liệu PDF gốc (PDF Points)**: Đơn vị là **Points** (pt), trong đó chuẩn in ấn quốc tế là `1 inch = 72 points` (Ví dụ khổ A4 chuẩn: $595.3 \times 841.9$ pt).
- **Gốc tọa độ**:
  - Giao diện (Canvas / DOM): Gốc `(0, 0)` nằm ở **góc trên cùng bên trái** (Top-Left).
  - PDF (PyMuPDF): `(0, 0)` cũng là **Top-Left** (khác với PostScript gốc là Bottom-Left).

---

## 2. Công Thức Quy Đổi 2 Chiều Chuẩn Xác (Matrix Scaling)

Khi hiển thị PDF lên màn hình qua hình ảnh render hoặc thẻ Canvas:

```text
scale_x = pdf_page_width_points / canvas_display_width_pixels
scale_y = pdf_page_height_points / canvas_display_height_pixels
```

### Chuyển đổi từ Tọa độ Màn hình $\rightarrow$ Tọa độ PDF:
```python
def canvas_to_pdf_point(canvas_x, canvas_y, canvas_w, canvas_h, pdf_w, pdf_h):
    scale_x = pdf_w / canvas_w
    scale_y = pdf_h / canvas_h
    pdf_x = canvas_x * scale_x
    pdf_y = canvas_y * scale_y
    return (pdf_x, pdf_y)
```

### Chuyển đổi Bounding Box (Vùng Chọn):
```python
def canvas_rect_to_pdf_rect(canvas_bbox, canvas_size, pdf_size):
    # canvas_bbox = (x0, y0, x1, y1)
    scale_x = pdf_size[0] / canvas_size[0]
    scale_y = pdf_size[1] / canvas_size[1]
    return fitz.Rect(
        canvas_bbox[0] * scale_x,
        canvas_bbox[1] * scale_y,
        canvas_bbox[2] * scale_x,
        canvas_bbox[3] * scale_y
    )
```

---

## 3. Kiến Trúc Căn Chỉnh Con Dấu Tự Động (Template Matching & Offset)

Khi người dùng chọn vùng mẫu (template) và vị trí đóng dấu:
1. **Template Bounding Box**: Vùng đặc trưng nhận diện con dấu hoặc chữ ký (ví dụ: ô "Người duyệt", "Trưởng phòng").
2. **Offset Vector**: Khoảng cách từ tâm vùng mẫu tới tâm con dấu thực tế:
   $$\Delta x = \text{Center Stamp}_x - \text{Center Template}_x$$
   $$\Delta y = \text{Center Stamp}_y - \text{Center Template}_y$$
3. **Áp dụng hàng loạt**: Khi duyệt các trang hoặc tài liệu mới, thuật toán tìm lại vùng mẫu $\rightarrow$ Cộng $\Delta x, \Delta y$ để định vị chính xác vị trí đóng dấu mà không bị lệch dù bố cục trang có thay đổi nhẹ.

---

## 4. Thực Thi Đóng Dấu Bằng PyMuPDF (`fitz`)

```python
import fitz  # PyMuPDF

def apply_stamp(pdf_path, output_path, page_num, stamp_img_path, center_pt, stamp_size_pt):
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    
    # Tính rect đóng dấu đối xứng quanh tâm center_pt (x, y)
    w, h = stamp_size_pt
    rect = fitz.Rect(
        center_pt[0] - w / 2,
        center_pt[1] - h / 2,
        center_pt[0] + w / 2,
        center_pt[1] + h / 2
    )
    
    # Chèn ảnh trong suốt (PNG alpha)
    page.insert_image(rect, filename=stamp_img_path, keep_proportion=True, overlay=True)
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
```

---

## 5. Checklist Tránh Lỗi Phổ Biến

- [ ] **Không nhầm lẫn DPI khi render**: Nếu render ảnh trang PDF ở 150 DPI hoặc 300 DPI, kích thước pixmap sẽ gấp $\frac{\text{DPI}}{72}$ lần kích thước trang PDF points. BẮT BUỘC nhân/chia theo kích thước thực tế hiển thị trên Canvas chứ không dùng cố định số pixel ảnh raw.
- [ ] **Giữ tỷ lệ ảnh (Aspect Ratio)**: Luôn bật `keep_proportion=True` để con dấu tròn không bị méo thành oval.
- [ ] **Khử lệch dòng Excel sang PDF (Intramart Excel Row Height)**: Nếu văn bản xuất từ Excel ra PDF bị lệch tọa độ theo chiều dọc, giải pháp chuẩn là cố định `Row Height` trong Excel ở mức tuyệt đối thay vì auto-fit font.

