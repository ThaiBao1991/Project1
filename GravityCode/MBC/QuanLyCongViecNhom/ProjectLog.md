# Project Log - MBC Quản Lý Công Việc & Hiệu Suất Nhóm

## Thông Tin Dự Án
- **Tên dự án:** Ứng dụng Web Quản Lý Công Việc & Nhân Sự Toàn Diện (Gantt Timeline & Performance Points)
- **Vị trí:** `c:\Users\12953 Bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\GravityCode\MBC\QuanLyCongViecNhom`
- **Phiên bản:** v2.8.0 (Grouped Tasks & Multi-Scale Timeline Suite)
- **Ngày cập nhật:** 06/10/2026.

---

## Nhật Ký Cập Nhật (Change Log)

### Phiên Bản 2.8.0 (06/10/2026) - Nâng Cấp 5 Tính Năng Tối Ưu Hóa & Gom Nhóm Dự Án:
1. **Tự động gom cụm các công việc cùng dự án/cùng mã chính đứng liền kề nhau:**
   - Xây dựng thuật toán `groupAndSortTasks` đa cấp tự động cho cả Giao diện Web và File Xuất Excel.
   - Các công việc có cùng Mã CV Chính (`mainTaskId`) hoặc Tên Công Việc Chính (`mainTaskTitle`) như **Sửa chữa máy TUM** luôn được gom lại đứng sát nhau 100%. Khắc phục triệt để hiện tượng công việc mới thêm (như việc *test máy*) bị nhảy xuống cuối bảng sau máy khác (như máy INEX).
   - Trong cùng 1 nhóm, các giai đoạn con tự động sắp xếp theo ngày bắt đầu tăng dần.
2. **Timeline động ôm khít hạn cuối thực tế (Bỏ giới hạn cứng 365 ngày):**
   - Bổ sung nút **"Vừa hạn cuối"** (`fitTimelineToTaskDates`) trên thanh công cụ: Tự động tính toán từ ngày bắt đầu nhỏ nhất đến đúng ngày kết thúc của công việc xa nhất trong bộ lọc, không vẽ thừa thãi các năm sau.
   - Nới lỏng giới hạn số ngày dự kiến trong form thêm việc lên tối đa 3.650 ngày (10 năm).
3. **Mở rộng linh hoạt đơn vị kế hoạch: Giờ, Ngày, Tuần, Tháng, Năm:**
   - Nâng cấp bộ chọn đơn vị hiển thị trên thanh công cụ thành 5 chế độ:
     - **Theo Giờ (`HOUR`):** Chia theo các mốc giờ làm việc trong ngày (07:00, 08:00... 19:00), rất trực quan cho sửa chữa máy móc khẩn cấp trong ca.
     - **Theo Ngày (`DAY`):** Chi tiết từng ngày.
     - **Theo Tuần (`WEEK`):** Chi tiết từng tuần.
     - **Theo Tháng (`MONTH`):** Toàn cảnh các tháng.
     - **Theo Năm (`YEAR`):** Toàn cảnh theo từng năm cho các kế hoạch dài hạn.
   - Tích hợp các đơn vị này vào cấu hình xuất báo cáo Excel (`exportScaleSelect`).
4. **Bổ sung tính năng Tạm dừng / Dừng dự án (`Tạm dừng`):**
   - Thêm trạng thái **`⏸ Tạm dừng / Dừng dự án`** vào bộ lọc, form thêm việc, form cập nhật nhanh và file xuất Excel.
   - Bổ sung nút bấm chuyển đổi nhanh **`⏸ Dừng` / `▶ Tiếp tục`** ngay trên cột Tên công việc mà không cần mở form phức tạp.
   - Thanh Gantt hiển thị dải màu xám sọc đá phiến (`timeline-arrow-paused`) và ký hiệu `⏸` phân biệt rõ ràng với công việc đang làm hay trễ hạn.
   - Công việc tạm dừng được loại trừ khỏi tính phạt trễ hạn trong hệ thống KPI.

### Phiên Bản 2.7.0 (06/10/2026) - Nâng Cấp 6 Tính Năng Quản Lý Toàn Diện:
1. **Lọc trạng thái & Ẩn mặc định các công việc "Hoàn thành":**
   - Đã thêm tùy chọn **"Chưa hoàn thành (Mặc định)"** (`CHUA_HOAN_THANH`) vào bộ lọc trạng thái.
   - Khi vừa tải trang hoặc lọc, các công việc đã kết thúc (100% hoặc có chữ "Hoàn thành") sẽ tự động ẩn đi, giúp giao diện tập trung hoàn toàn vào các đầu việc cần xử lý.
   - Người dùng có thể dễ dàng chọn lại "Tất cả trạng thái" hoặc "Hoàn thành" bất cứ lúc nào.
2. **Công việc chính tự động hoàn thành khi 100% công việc con hoàn thành:**
   - Xây dựng hàm `getMainTaskProgress(mainTaskId)` tự động tính toán tổng số việc con, số việc đã xong và tỷ lệ hoàn thành trung bình.
   - Hiển thị nhãn tiến độ sinh động `[Đã xong N/N việc]` (màu xanh lá) hoặc `[Đang làm X/N việc con - Y%]` (màu xanh dương) ngay cạnh tên công việc chính trên bảng Gantt.
3. **Lọc thời gian theo khoảng ngày tùy chọn (Từ ngày ... Đến ngày ...):**
   - Đã bổ sung 2 ô chọn ngày `filterStartDate` và `filterEndDate` cùng nút xóa nhanh trên thanh công cụ.
   - Khi chọn khoảng ngày, toàn bộ bảng Gantt tự động co giãn hiển thị chính xác các ngày thuộc khoảng lựa chọn mà không bị bó hẹp trong 1 tháng.
4. **Bộ nút Import Công Việc & Import Nhân Sự riêng biệt với cơ chế Smart Merge:**
   - Đã tách thành 2 nút chuyên dụng: **"Import Công Việc"** và **"Import Nhân Sự"** trên thanh Header.
   - Giao diện modal hỗ trợ chuyển đổi tab linh hoạt, tải file mẫu `.xlsx` chuẩn hóa (`Mau_Import_CongViec.xlsx`, `Mau_Import_NhanSu.xlsx`).
   - **Cơ chế Smart Merge thông minh:** Tự động đối chiếu mã ID (Mã CV chi tiết hoặc Mã NV). Chỉ chèn các mục chưa từng có trong hệ thống, bảo vệ 100% dữ liệu cũ không bị trùng lặp hoặc ghi đè mất mát.
5. **Timeline tự động mở rộng theo năm dữ liệu (2026 -> 2029+):**
   - Hàm `getTasksYearSpan()` tự động quét toàn bộ cơ sở dữ liệu để tìm năm nhỏ nhất và năm lớn nhất.
   - Timeline toàn cảnh tự động trải dài từ 2026 đến 2029 (hoặc xa hơn tùy theo các dự án dài hạn được nạp vào) thay vì bị giới hạn cố định.
6. **Nâng cấp giao diện xuất Báo cáo Excel chuyên nghiệp & sang trọng:**
   - Bổ sung khối **Dashboard KPI Summary Cards** ở đầu file Excel (Tổng số việc, Đã xong, Đang làm, Quá hạn, Tỷ lệ hoàn thành).
   - Bảng chú giải ký hiệu trực quan: `►` Kế hoạch, `✔` Hoàn thành đúng hạn, `⚠` Trễ hạn / Cảnh báo.
   - Thanh Gantt bar liền khối sắc nét, độ tương phản cao, căn chỉnh chiều rộng cột tự động trên mọi phiên bản Microsoft Excel.

### Phiên Bản 2.6.1 (06/10/2026) - Khắc Phục Triệt Để Vấn Đề Nạp & Giữ Dữ Liệu Khi Mở Mới / Reload File HTML:
1. **Khắc phục lỗi CORS chặn nạp dữ liệu khi mở file HTML trực tiếp (`file:///`):**
   - Đã tạo file `database.js` chứa toàn bộ cơ sở dữ liệu `window.MBC_DEFAULT_DATABASE` (14 công việc thực tế từ T1/2026 đến T2/2027 và 5 nhân sự).
   - Nhúng `<script src="database.js"></script>` vào `index.html`. Trình duyệt nạp trực tiếp qua thẻ `<script>` không bao giờ bị chính sách CORS chặn.
2. **Cơ chế nạp dữ liệu thông minh kiểm tra đa tầng (`loadInitialData`):**
   - **Tầng 1 (Ưu tiên dữ liệu cá nhân):** Kiểm tra `localStorage`. Nếu đã có dữ liệu công việc hợp lệ, giữ nguyên không làm mất bất kỳ thay đổi nào của người dùng.
   - **Tầng 2 (Bảo vệ khi mở mới / localStorage trống):** Tự động nạp đầy đủ từ `window.MBC_DEFAULT_DATABASE` và ghi nhớ ngay vào `localStorage`.
   - **Tầng 3 (Dự phòng Web Server):** Tự động fetch `database.json` nếu ứng dụng chạy trên môi trường máy chủ HTTP/HTTPS.
3. **Cải tiến tính năng Khôi phục & Quản lý CSDL:**
   - Hàm `resetToSampleData` và `restoreDefaultDatabase` khôi phục trực tiếp từ `window.MBC_DEFAULT_DATABASE` đồng bộ giao diện ngay lập tức mà không xóa trắng dữ liệu rồi reload.
   - Thêm nút **"Nạp CSDL từ database.js (Mặc Định 2026-2027)"** vào modal Quản lý File JSON để người dùng có thể nạp lại dữ liệu gốc bất kỳ lúc nào với 1 click.

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
