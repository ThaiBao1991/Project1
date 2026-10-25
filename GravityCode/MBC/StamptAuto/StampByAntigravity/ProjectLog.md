# Nhật Ký Dự Án: StampByAntigravity

> **⚠️ ĐỌC FILE NÀY TRƯỚC KHI LÀM BẤT KỲ ĐIỀU GÌ**
> Đây là tài liệu bắt buộc phải đọc đầu tiên mỗi phiên làm việc.
> Nó ghi lại toàn bộ kiến trúc, quyết định thiết kế và lịch sử thay đổi của dự án.

---

## 1. Giới Thiệu & Mục Đích

`StampByAntigravity` là hệ thống **đóng dấu PDF tự động** hoạt động theo 2 phương pháp:
- **Đóng dấu theo Hình Ảnh**: Nhận diện logo/ký hiệu trên PDF bằng OpenCV Template Matching, sau đó chèn ảnh con dấu vào vị trí tương ứng.
- **Đóng dấu theo Chữ**: Tìm một đoạn văn bản cụ thể (VD: "TỔNG CỘNG") và đặt con dấu cạnh chữ đó, dùng offset X/Y để tinh chỉnh.

Mục tiêu là được gọi tự động từ **Microsoft Access (VBA)** mà không cần thao tác tay.

---

## 2. Cấu Trúc File & Vai Trò

```
StampByAntigravity/
├── StampByAntigravity.py   # Engine lõi: stamp_pdf(), load_config(), CLI entry point
├── main_gui.py             # Giao diện Tkinter. Gọi engine qua import StampByAntigravity
├── config_generator.py     # Tạo file .py config tự chứa (nhúng ảnh base64)
├── ProjectLog.md           # FILE NÀY — nhật ký bắt buộc đọc đầu tiên
├── stamp_configs/
│   ├── Image/              # Configs đóng dấu theo Hình Ảnh (.json)
│   └── Text/               # Configs đóng dấu theo Chữ (.json)
├── Chay_Giao_Dien.bat      # Chạy giao diện bằng double-click
└── AccessVBA_StampByAntigravity.bas  # Code VBA tích hợp Access
```

---

## 3. Kiến Trúc Quan Trọng — Tọa Độ & Đơn Vị

> **⚠️ Đây là phần HAY GÂY LỖI NHẤT. Phải nắm rõ trước khi chỉnh code.**

| Tên biến | Đơn vị | Mô tả |
|---|---|---|
| `stamp_bbox` (canvas) | pixels màn hình | Vùng user khoanh trên Canvas Tkinter |
| `stamp_bbox_pdf` | PDF points | Sau khi quy đổi = `canvas * (pdf_size / canvas_size)` |
| `stamp_center` (canvas) | pixels màn hình | Tâm con dấu user click trên Canvas |
| `exact_center` | PDF points | Sau quy đổi, dùng trực tiếp để đặt dấu |
| `offset_x_pdf`, `offset_y_pdf` | PDF points | Khoảng cách từ tâm template tới tâm dấu |

**Luồng quy đổi tọa độ trong `main_gui.py`:**
```
user click (canvas px) → calculate_exact_position() → exact_center (PDF pts)
user drag (canvas px) → on_mouse_up() → stamp_bbox (canvas) + stamp_bbox_pdf (PDF pts)
```

**Luồng engine `StampByAntigravity.py`:**
```
stamp_bbox (PDF pts) × 2.0 → tọa độ trên ảnh x2 render → cắt template
match_pos (pixel ảnh x2) × (pdf_size/img_size) → tọa độ PDF
+ offset_x_pdf, offset_y_pdf → tâm đóng dấu cuối cùng
```

---

## 4. Thuật Toán Template Matching

- Render PDF bằng `fitz.Matrix(2.0, 2.0)` → ảnh rộng gấp đôi PDF
- Dùng `cv2.matchTemplate` với `TM_CCOEFF_NORMED`
- **Multi-scale 50%→150%** (16 mức): tìm được dù ảnh scan bị phóng/thu nhỏ
- `find_match_position()` trả về `(cx, cy)` là **tâm của match** (pixel ảnh x2)
- Quy đổi về PDF: `cx_pdf = cx_img × (pdf_w / img_w)`

---

## 5. Lưu & Load Cấu Hình

- **Lưu**: `main_gui.py → save_config()` → lưu vào `stamp_configs/Image/` hoặc `stamp_configs/Text/` tùy tab đang dùng
- **Load danh sách**: `refresh_category_list()` quét cả 2 thư mục con, lưu vào `self.all_configs = {"[Ảnh] TênConfig": "/full/path.json"}`
- **Load cấu hình**: `load_selected_config()` → tra `self.all_configs[key]` lấy đường dẫn đầy đủ
- **Engine load**: `StampByAntigravity.load_config(name)` → tìm tuần tự trong `Text/`, `Image/`, rồi gốc

---

## 6. Test & Start Không Cần Lưu

Cả `test_stamp()` và `start_stamp_all()` hoạt động theo nguyên tắc:
1. Nếu combo box chọn config đã lưu → load từ file
2. Nếu combo box trống → gọi `get_current_ui_config()` lấy thông số từ màn hình trực tiếp

`get_current_ui_config()` truyền `stamp_bbox_pdf` (không phải `stamp_bbox` canvas) cho engine.

---

## 7. Chất Lượng Ảnh Con Dấu

- **Không dùng PIL resize** trước khi in. Ảnh gốc được lưu vào file tạm → PyMuPDF đọc ảnh gốc và tự scale theo bounding box.
- Kích thước bounding box trên PDF: `new_w = img_w × (scale_percent/100)` PDF points
- Kết quả: ảnh luôn sắc nét dù scale nhỏ, vì PyMuPDF dùng anti-aliasing nội bộ.

---

## 8. Lịch Sử Thay Đổi

### [2026-06-08] Phiên làm việc lớn — Tái cấu trúc toàn bộ GUI & Engine

#### 8.1 Những lỗi đã sửa
| Lỗi | Nguyên nhân | Cách sửa |
|---|---|---|
| Nút Start không chạy | MessageBox bị kẹt sau cửa sổ Maximized | Force `parent=self.root`, bắt exception vào log |
| `TypeError: stamp_pdf() unexpected keyword 'custom_output'` | Thêm tham số ở GUI nhưng chưa khai báo ở engine | Thêm `custom_output: str = None` vào `stamp_pdf()` |
| Dấu bị mờ/xấu khi thu nhỏ | PIL resize trước khi in làm mất nét | Xóa bỏ PIL resize, dùng ảnh gốc + PyMuPDF scale |
| Dấu lệch vị trí (offset sai) | `stamp_bbox` canvas px bị nhân ×2.0 thêm → sai đơn vị | Thêm `stamp_bbox_pdf` (PDF points), engine dùng trực tiếp |
| Load config không tìm thấy file | Tìm theo tên phẳng, config đã chuyển vào thư mục con | `load_config()` quét tuần tự `Text/`, `Image/`, gốc |
| `all_configs` chưa init | Gọi `load_selected_config()` trước `refresh_category_list()` | Init `self.all_configs = {}` trong `__init__` |
| `use_annotation` AttributeError | Biến bị xóa khỏi `__init__` | Khôi phục vào `__init__` |

#### 8.2 Tính năng mới thêm
- **Live Preview Scale**: Kéo slider % → khung nét đứt xanh hiển thị ngay kích thước dấu trên canvas
- **Tìm chữ trong vùng khoanh**: `page.search_for(text, clip=fitz.Rect(stamp_bbox_pdf))` → chỉ tìm trong vùng user khoanh
- **Multi-scale 50%-150%**: Template matching thử 16 mức scale → nhận diện tốt hơn ảnh scan biến dạng
- **Phân thư mục config**: `stamp_configs/Image/` và `stamp_configs/Text/` — không lẫn lộn
- **Test/Start không cần lưu**: Lấy thông số trực tiếp từ UI nếu chưa lưu config
- **Tab Chữ không bắt buộc ảnh**: `validate_inputs()` chỉ kiểm tra ảnh khi đang ở tab Image
- **Xóa double `sys.exit(0)`**: Sửa lỗi `sys.exit(0)` bị gọi 2 lần trong `main()`

---

## 9. Hướng Dẫn Cho AI — Đọc File Này Trước

Nếu bạn là AI assistant đang làm việc trên project này, hãy thực hiện theo thứ tự:

1. **Đọc `ProjectLog.md` này** để hiểu kiến trúc và những quyết định đã có
2. **Xem mục 3** để nắm rõ đơn vị tọa độ trước khi chạm vào bất kỳ phép tính nào
3. **Đọc phần đầu `StampByAntigravity.py`** (khoảng 100 dòng đầu) để nắm imports, constants, CONFIG_DIR
4. **Đọc `main_gui.py` từ `__init__`** để biết các biến state hiện có
5. **Chỉ sau đó** mới bắt đầu phân tích lỗi hoặc thêm tính năng

---

*Cập nhật lần cuối: 2026-06-08 19:46 (GMT+7)*
### [2026-06-09] Cap nhat Template Matching, Combobox UI, Dynamic Scaling
- Sua loi Combobox UI (tach rieng cho tab Image/Text).
- Sua loi Template Matching (Them Early Stopping tranh nhieu diem trong).
- Them Dynamic Scaling (Kich thuoc va offset con dau tang theo scale theo khung chu ki tim duoc).

*Cap nhat lan cuoi: 2026-06-09 (GMT+7)*

### [2026-06-10] Cap nhat he thong sinh cau hinh & don dep
- Sua loi unicodeescape trong file .py do config_generator.py ghi duong dan Windows co chua dau \ vao docstring ma khong dung raw string.
- Sua loi config_generator.py khong tim thay file .json do chua tro dung vao thu muc con Text/ va Image/.
- **Cai thien UX GUI**:
  - Khi xoa config, ung dung se xoa triet de file .json, file .py da generate, va file anh _template.png tuong ung.
  - Khi luu de config dang mo, tu dong goi y dung ten cu thay vi bat go lai.
- **Don dep du an**: Da ra soat va xoa cac file tam sinh ra trong qua trinh test/debug.

*Cap nhat lan cuoi: 2026-06-10 13:40 (GMT+7)*

### [2026-07-07] Tinh nang Go Dau (Unstamp) & Bug Fixes

#### Tinh nang Go Dau:
- Them ham `remove_stamp_pdf(pdf_path, cfg, custom_output)` vao engine StampByAntigravity.py.
- Logic: Doc kich thuoc goc (width x height) cua anh con dau tu config, quet toan bo trang PDF, xoa Image XObject co kich thuoc trung khop. Luu lai voi garbage=3 de giam dung luong.
- **Tham so CLI (tu chon, khong bat buoc)**: Them tham so thu 3 `--remove` vao entry point.
  - Dong dau: python StampByAntigravity.py "file.pdf" "ConfigName"
  - Go dau:   python StampByAntigravity.py "file.pdf" "ConfigName" --remove
- **GUI (main_gui.py)**: Bo sung checkbox "Che do Go Dau" o vung nut hanh dong. Khi tick, nut Test Dau va START se goi `remove_stamp_pdf` thay vi `stamp_pdf`.

#### Bug Fixes:
- Fix ValueError: document closed trong show_page(): Them guard kiem tra current_pdf_doc is None va .is_closed truoc khi truy cap trang PDF.
- Fix `FileNotFoundError` trong `test_stamp()`: `validate_inputs()` nay kiem tra ca `os.path.exists()` cho PDF mau va anh dau, khong chi kiem tra path co rong khong.
- Fix load_config(): Neu pdf_sample_path trong config khong con ton tai, canh bao nen log va bo qua viec load preview (thay vi crash sau).

*Cap nhat lan cuoi: 2026-07-07 13:20 (GMT+7)*