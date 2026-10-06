# Hướng Dẫn Sử Dụng Ứng Dụng Quản Lý Công Việc & Hiệu Suất Nhóm MBC (v2.6)

## 1. Cấu Trúc Thư Mục & Cách Khởi Chạy
- **index.html**: Giao diện chính của ứng dụng. Bạn chỉ cần **nhấp đúp chuột** vào file này để mở trực tiếp trên trình duyệt (Chrome, Edge, Firefox, Cốc Cốc) mà không cần cài đặt server.
- **database.js**: File cơ sở dữ liệu nền tảng JavaScript (chứa biến `window.MBC_DEFAULT_DATABASE`), giúp ứng dụng nạp dữ liệu tức thì 100% trơn tru khi mở trực tiếp file HTML offline mà không bị chặn bởi bảo mật CORS của trình duyệt.
- **style.css**: Chứa toàn bộ giao diện thẩm mỹ, màu sắc và biểu đồ mũi tên.
- **app.js**: Chứa toàn bộ logic xử lý dữ liệu, phân cấp công việc, chuyển đổi Ngày/Tuần/Tháng và xuất Excel.
- **database.json**: Toàn bộ cơ sở dữ liệu hệ thống (2026-2027) dùng để sao lưu và đồng bộ.
- **tasks.json**: File dữ liệu danh sách công việc.
- **employees.json**: File danh sách nhân sự.

---

## 2. Các Tính Năng Nâng Cấp Nổi Bật

### 2.1. Chế Độ Xem Toàn Cảnh (Theo Ngày / Theo Tuần / Theo Tháng)
- Thanh công cụ phía trên bảng có nút chuyển đổi linh hoạt:
  - **Theo Ngày:** Dành cho tác nghiệp hàng ngày (khung 10 ngày, 15 ngày, hoặc cả tháng).
  - **Theo Tuần:** Xem tiến độ theo từng tuần trong quý.
  - **Toàn Cảnh Năm (Tháng):** Hiển thị toàn bộ các tháng từ **T1/2026 đến T3/2027**. Ở chế độ này, mũi tên sẽ trải dài qua các tháng và **ô kết thúc hiển thị chính xác ngày/tháng hoàn thành** (ví dụ: `24/11`, `13/02/27`).

### 2.2. Phân Cấp Công Việc Chính & Nội Dung Chi Tiết (Parent Task & Subtasks)
- **Công việc chính (Parent Task):** Ví dụ `[CV-TUM] Sửa chữa máy TUM`.
- **Hạng mục chi tiết:** Các công việc nhỏ trong cùng một dự án chính (Giai đoạn 1: Xác nhận linh kiện, Giai đoạn 2: Thay van áp suất, Giai đoạn 3: Nghiệm thu vận hành) cùng chia sẻ một **Mã công việc chính chung**.
- **Khi thêm công việc mới (Nút Thêm Công Việc):**
  - Có dropdown **"Nhóm Công Việc Chính"**: Cho phép chọn nhanh công việc chính đã có (tự động khóa mã và tên công việc chính) hoặc chọn tạo công việc chính mới.
- **Khi cập nhật tiến độ (Nút Cập Nhật Tiến Độ):**
  - Có dropdown **"Chọn Nhanh Công Việc Chưa Xong"**: Tự động lọc ra các công việc dở dang của nhân viên đó để nhấp chọn và báo cáo tiến độ ngay.

### 2.3. Xuất Báo Cáo Excel Trực Quan (Gantt Matrix Đẹp Mắt)
- Khi nhấp **Xuất Báo Cáo Excel**:
  - Xuất hiện hộp thoại **Cấu hình tiêu đề báo cáo**: Hệ thống tự động điền tiêu đề thông minh theo nhân sự hoặc thời gian đang lọc (ví dụ: `BÁO CÁO KẾ HOẠCH & THỰC TÍCH - NHÂN SỰ: NGUYỄN QUANG THẢO - THÁNG 10/2026`). Bạn có thể chỉnh sửa lại theo ý muốn.
  - **Mũi tên Gantt liền mạch:** Không còn bị chia cắt bởi viền ô hay ký tự rời rạc; các ô liên tiếp được nối thành **dải màu nguyên khối** và kết thúc bằng mũi tên nhọn `►` chuẩn mực khi mở trong Microsoft Excel.

### 2.4. Quản Lý & Đồng Bộ File JSON
- Nút **File JSON** trên thanh công cụ:
  - Tải về cập nhật riêng từng file: `database.json`, `tasks.json`, `employees.json`.
  - Nạp file `.json` từ máy khác vào để khôi phục nguyên trạng cơ sở dữ liệu.
