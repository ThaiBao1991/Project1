# Project Log - MBC Quản Lý Công Việc & Hiệu Suất Nhóm

## Thông Tin Dự Án
- **Tên dự án:** Ứng dụng Web Quản Lý Công Việc & Nhân Sự Toàn Diện (Gantt Timeline & Performance Points)
- **Vị trí:** `c:\Users\12953 Bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\GravityCode\MBC\QuanLyCongViecNhom`
- **Phiên bản:** v2.6.0 (Enterprise)
- **Ngày cập nhật:** 05/10/2026.

---

## Nhật Ký Cập Nhật (Change Log)

### Phiên Bản 2.6.0 (05/10/2026) - Nâng Cấp Toàn Diện Theo Yêu Cầu Người Dùng:
1. **Tùy biến Tiêu đề Báo Cáo Excel (Config Header linh hoạt):**
   - Đã thêm Modal **Cấu hình xuất báo cáo Excel** trước khi tải file về.
   - Tiêu đề được tự động sinh thông minh dựa trên bộ lọc: Tự động gắn tên nhân sự đang xem, phòng ban và thời gian (ví dụ: `BÁO CÁO KẾ HOẠCH & THỰC TÍCH - NHÂN SỰ: NGUYỄN QUANG THẢO - THÁNG 10/2026`).
   - Cho phép người dùng chỉnh sửa tiêu đề và tên đơn vị tự do theo ý muốn.
2. **Khắc phục Mũi tên Excel (Nâng cấp thanh tiến độ liền mạch, không đứt đoạn):**
   - Đã loại bỏ hoàn toàn viền dọc ngăn cách (`border-left: none; border-right: none`) giữa các ô ngày liên tiếp của cùng 1 công việc.
   - Tạo thành dải màu **Solid Gantt Bar liền khối**, ô đầu có bo viền trái, ô cuối kết thúc bằng mũi tên nhọn `►` sắc nét, không còn hiện tượng ô vuông vỡ vụn khi mở trên Microsoft Excel.
3. **Bổ sung Dữ liệu Mẫu 12 Tháng Năm 2026 & Sang Năm 2027 + Chế độ xem Toàn cảnh:**
   - Dữ liệu thực tế phong phú trải dài từ Tháng 1 đến Tháng 12/2026 và Q1/2027 (bảo dưỡng đầu năm, kiểm toán ISO, cải tiến SCADA, dự án tự động hóa 2027).
   - Thêm thanh chuyển đổi chế độ xem:
     - **Theo Ngày:** Chi tiết 10 ngày, 15 ngày hoặc 1 tháng.
     - **Theo Tuần:** Tiến độ từng tuần trong quý.
     - **Toàn Cảnh Năm (Tháng):** Hiển thị toàn bộ các tháng từ T1/2026 đến T3/2027. Ở chế độ này, mũi tên kéo dài qua các tháng và ô kết thúc hiển thị chính xác ngày/tháng hoàn thành.
4. **Phân cấp Công việc Chính & Nội dung Chi tiết (Parent Task & Subtasks) + Chọn nhanh việc dở dang:**
   - Hỗ trợ công việc chính (ví dụ: `[CV-TUM] Sửa chữa máy TUM`) bao gồm nhiều giai đoạn chi tiết nhỏ (Giai đoạn 1, 2, 3) dùng chung mã công việc chính.
   - Form Thêm việc: Có dropdown **"Chọn công việc chính có sẵn"** (hoặc tạo mới) để tự động đồng bộ mã công việc chung.
   - Form Cập nhật tiến độ: Có dropdown **"Chọn nhanh công việc chưa xong"** của nhân viên để click chọn và cập nhật kết quả tức thì.
