# Project Log: LocFile (Ứng Dụng Lọc File Siêu Tốc Windows)

## Thông Tin Dự Án
- **Tên dự án**: LocFile (Fast Windows File Filter)
- **Mục tiêu**: Xây dựng ứng dụng lọc file siêu tốc trên Windows, duyệt đệ quy thư mục con, hỗ trợ đa bộ lọc (ngày sửa, dung lượng, định dạng) và mở file hàng loạt bằng ứng dụng mặc định.
- **Công nghệ**: Python 3.12, CustomTkinter, ttk.Treeview Dark Theme, os.scandir (Win32 fast scanning), Multi-threading.

---

## Nhật Ký Phát Triển

### [2026-09-17] Hoàn Thành Triển Khai Ban Đầu (v1.0.0)
- **Các thành phần đã triển khai**:
  - `LocFileApp.py`:
    - Tích hợp chuẩn `python_auto_install` tự động phát hiện và cài `customtkinter>=5.2.0`.
    - Tự động cấu hình mã hóa stdout/stderr UTF-8 tương thích mọi hệ điều hành Windows (kể cả cp932 / cp437).
    - Lõi `FileScannerEngine`: Duyệt đệ quy bằng `os.scandir` + ngăn xếp tránh tràn stack, `follow_symlinks=False`, bắt `PermissionError` & `OSError`.
    - Đa luồng nền (`threading.Thread`) + `queue.Queue` với cơ chế cập nhật batch 200 items/30ms đảm bảo UI 60fps Zero-Lag.
    - Bộ lọc đa tiêu chí:
      - Khoảng ngày sửa đổi: Hôm nay, 3/7/30/90 ngày qua, Năm nay, Tùy chỉnh (YYYY-MM-DD hoặc DD/MM/YYYY).
      - Kích thước file: < 1MB, 1-10MB, 10-100MB, > 100MB, Tùy chỉnh Min/Max (MB).
      - Định dạng/Nhóm file: Tài liệu, Hình ảnh, Video, Âm thanh, File nén, Mã nguồn, Tùy chỉnh đuôi file tự do.
      - Từ khóa trong tên file: Tìm kiếm không phân biệt chữ hoa/thường.
    - Bảng kết quả `ttk.Treeview` chuẩn `customtkinter-perf-ui` giao diện Dark Mode Catppuccin Mocha sang trọng:
      - Các cột: Tên file, Ngày sửa đổi, Dung lượng (tự đổi B/KB/MB/GB), Đường dẫn thư mục.
      - Hỗ trợ chọn nhiều file: Click, `Ctrl + Click`, `Shift + Click`, `Ctrl + A` (chọn tất cả).
      - Sắp xếp thông minh khi click tiêu đề cột (kích thước theo bytes, ngày theo timestamp, tên theo alphabet, có mũi tên ▲/▼).
      - Double-click hoặc nhấn Enter: Mở file bằng ứng dụng mặc định (`os.startfile`).
      - Click chuột phải (Context Menu): Mở file, Mở thư mục chứa trong Explorer (`explorer /select,"path"`), Sao chép đường dẫn, Sao chép tên file.
      - Cảnh báo an toàn: Nhắc nhở xác nhận nếu mở hơn 10 file cùng lúc.
  - `requirements.txt`: Khai báo `customtkinter>=5.2.0`.
- **Kết quả Kiểm Thử (Gate 2 Checklist)**:
  - Cú pháp & Compile: `python -m py_compile LocFileApp.py` pass 100%.
  - Tự động kiểm thử Engine: Kiểm tra định dạng dung lượng, parse ngày tháng, quét thực tế theo đuôi, kích thước, ngày tháng — pass 100%.
  - Tự động kiểm thử GUI: Khởi tạo và hủy cửa sổ thành công 0 lỗi runtime.
  - Dọn dẹp: Đã xóa file test tạm `test_scanner.py`.
