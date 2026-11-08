# Python Desktop Application Standards

Áp dụng cho tất cả ứng dụng Python Desktop (CustomTkinter, Tkinter).

## 1. Hiệu Năng & Zero-Lag UI (CustomTkinter Performance)
- **C-Engine Treeview**: Với bảng danh sách hoặc dữ liệu lớn (>50 dòng), KHÔNG dùng nhiều `CTkLabel` hoặc `CTkFrame` lặp trong scroll frame. BẮT BUỘC dùng `ttk.Treeview` kết hợp tùy biến theme Dark Mode (Catppuccin Mocha palette) để đạt tốc độ 60fps mượt mà.
- **Worker Thread & Queue**: Mọi tác vụ nặng (quét file, gọi API, build file Word/Excel, I/O mạng) BẮT BUỘC chạy trong `threading.Thread(daemon=True)`.
- **Cập nhật UI an toàn**: Giao tiếp giữa Worker Thread và UI Thread qua `queue.Queue` và `root.after(ms, poll_fn)`. Tuyệt đối không gọi trực tiếp widget method từ thread phụ.
- **Batching Updates**: Khi nạp hàng trăm kết quả vào Treeview, gom nhóm cập nhật theo lô (batch 100-200 dòng/30ms) thay vì gọi `insert()` từng dòng đơn lẻ.

## 2. Mã Hóa & Tương Thích Windows
- **Bắt buộc UTF-8**: Luôn đặt ở đầu file entry point:
  ```python
  import sys
  if hasattr(sys.stdout, "reconfigure"):
      sys.stdout.reconfigure(encoding="utf-8", errors="replace")
  if hasattr(sys.stderr, "reconfigure"):
      sys.stderr.reconfigure(encoding="utf-8", errors="replace")
  ```
- Tránh lỗi crash với các bảng mã Windows tiếng Nhật (cp932) hoặc tiếng Anh (cp437/cp1252).
- Mọi hàm đọc/ghi file văn bản (`open(...)`) BẮT BUỘC khai báo `encoding="utf-8"`.

## 3. Tự Động Kiểm Tra & Cài Đặt Thư Viện
- Sử dụng pattern `python_auto_install` khi khởi động: tự động import, nếu thiếu thư viện thì tự gọi `subprocess.check_call([sys.executable, "-m", "pip", "install", ...])` hoặc hiển thị dialog hướng dẫn cài đặt.