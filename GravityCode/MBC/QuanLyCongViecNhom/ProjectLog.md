# Project Log - MBC Quản Lý Công Việc & Hiệu Suất Nhóm

## Thông Tin Dự Án
- **Tên dự án:** Ứng dụng Web Quản Lý Công Việc & Nhân Sự Toàn Diện (Gantt Timeline & Performance Points)
- **Vị trí:** `c:\Users\12953 Bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\GravityCode\MBC\QuanLyCongViecNhom`
- **Phiên bản:** v3.3.0 (Timeline YEAR căn theo filter, Xuất Data Excel Công Việc & Nhân Sự, Hiển thị ngày cập nhật cuối)
- **Ngày cập nhật:** 07/10/2026.

---

## Nhật Ký Cập Nhật (Change Log)

### Phiên Bản 3.3.0 (07/10/2026) - Timeline Filter-Aware, Excel Data Export & Hiển Thị Cập Nhật Cuối:
1. **Timeline YEAR tự động căn theo khoảng lọc đang active:**
   - `getTasksYearSpan()` giờ ưu tiên `filterStartDate`/`filterEndDate` nếu người dùng đã chọn khoảng ngày tự do — trục năm co dãn khớp 100% với khoảng đó.
   - Khi không có filter ngày, hàm chỉ quét các task của nhân viên đang được lọc (filterEmp) thay vì toàn bộ CSDL — trục năm gọn hơn khi xem từng người.
2. **Xuất dữ liệu Công Việc & Nhân Sự ra Excel (bảng phẳng):**
   - Thêm 2 hàm mới: `exportTasksDataToExcel()` (16 cột: Mã CV, Dự án, Nhân Viên, Ngày, Trạng Thái, KPI, Cập Nhật Cuối...) và `exportEmployeesDataToExcel()` (11 cột: Mã NV, Họ Tên, Phòng Ban, Tổng CV, Hoàn Thành, Tỷ Lệ, KPI...).
   - Hai nút **"Xuất Công Việc (.xls)"** và **"Xuất Nhân Sự (.xls)"** xuất hiện trong Modal Quản Lý CSDL JSON (syncModal), khu vực riêng màu xanh lá emerald.
   - File xuất ra có tiêu đề chuyên nghiệp, màu sắc phân loại trạng thái, tên file tự động kèm ngày xuất.
3. **Hiển thị tường minh ngày cập nhật cuối (lastStatusUpdate) trên bảng:**
   - Mỗi dòng công việc chưa hoàn thành / chưa tạm dừng giờ hiển thị thêm dòng nhỏ "CN cuối: DD/MM/YYYY" (icon đồng hồ).
   - Nếu quá 3 ngày chưa cập nhật, dòng "CN cuối" này tự đổi màu đỏ + in đậm để người dùng nhận biết ngay tại sao việc đó bị cảnh báo.
   - Tooltip `title` trên cảnh báo cũng được cá nhân hóa để hiển thị đúng số ngày (`Quá X ngày chưa cập nhật`).


1. **Click chọn dự án & tự động căn chỉnh biểu đồ (Interactive Project Drill-down):**
   - Người dùng có thể click trực tiếp vào **Tên dự án** (như *Sửa chữa máy TUM*) hoặc **Huy hiệu mã dự án** (`[CV-TUM-2026]`) ngay trên bảng dữ liệu hoặc chọn qua dropdown **Dự án** trên thanh công cụ.
   - Khi chọn dự án: Hệ thống tự động lọc danh sách chỉ hiển thị các công việc con của dự án đó, đồng thời kích hoạt hàm `fitTimelineToTaskDates()` tự động co dãn, phóng to khung nhìn Timeline khớp khít 100% từ ngày bắt đầu đến ngày hoàn thành của dự án (loại bỏ hoàn toàn các ngày/tháng trống thừa).
   - Xuất hiện **Banner dự án đang chọn** nổi bật ngay trên đầu bảng, hiển thị tên dự án, số lượng công việc và nút `[✕ Xem tất cả dự án]` để quay lại xem toàn bộ. Click lại vào tên dự án cũng tự động đảo trạng thái quay về xem tất cả.
2. **Bổ sung tính năng Import Nhân Sự vào Modal Quản Lý Nhân Sự (Hình 1):**
   - Bổ sung nút **"📥 Import Excel Nhân Sự"** và **"Import Nhân Sự"** ngay trong modal Quản lý nhân sự & danh sách thành viên (`employeeModal`).
   - Tích hợp luồng import thông minh `openSmartImportModal('EMP')`: Hỗ trợ nạp file `.xlsx`, `.xls` hoặc `.json`, tự động đối soát Mã NV và Họ tên, chỉ chèn các nhân sự mới và tự động cập nhật bảng danh sách nhân viên ngay lập tức.
   - Tự động sinh mã `NV-XXXX` tuần tự chuẩn xác cho các nhân sự chưa có sẵn mã trong file Excel.
3. **Chế độ lưu & ghi nhớ cấu hình xuất báo cáo Excel (Hình 2):**
   - Trong modal Cấu hình xuất Excel (`exportConfigModal`), bổ sung checkbox **"Ghi nhớ cấu hình này cho các lần xuất sau"**, nút **"💾 Lưu cấu hình"** và nút **"Mặc định"**.
   - Lưu trữ an toàn cấu hình vào `localStorage` (`MBC_EXCEL_EXPORT_CONFIG`) bao gồm: Tiêu đề báo cáo, Tên đơn vị / phòng ban, Khung thời gian & đơn vị xuất.
   - Lần mở modal hoặc xuất báo cáo tiếp theo sẽ tự động nạp lại cấu hình người dùng đã lưu thay vì bị reset về mặc định ban đầu.

### Phiên Bản 3.1.0 (07/10/2026) - Đơn Vị Kế Hoạch Linh Hoạt, Mã Việc Tuần Tự & Bộ Lọc Đa Chiều:
1. **Khắc phục số lượng công việc máy TUM hiển thị chính xác 3 việc:**
   - Điều chỉnh bộ dữ liệu Nhóm 6 (Sửa chữa máy TUM) thành đúng 3 giai đoạn chi tiết trong tháng 10/2026 (`CV-2026-0015` GĐ 1: 01/10/2026, `CV-2026-0016` GĐ 2: 03/10/2026, `CV-2026-0017` GĐ 3: 06/10/2026).
   - Huy hiệu dự án đồng bộ chính xác `Dự án: X/3 việc`, hiển thị khớp 100% giữa số lượng dòng công việc trên bảng và tiến độ dự án mẹ.
2. **Kế hoạch dự kiến hỗ trợ đa đơn vị: Giờ, Ngày, Tuần, Tháng:**
   - Nâng cấp modal thêm/sửa công việc với ô nhập số lượng và bộ chọn đơn vị (`giờ`, `ngày`, `tuần`, `tháng`).
   - Tự động tính toán ngày kết thúc kế hoạch (`planEndDate`) theo đơn vị tương ứng (theo giờ: cùng ngày; tuần: x7 ngày; tháng: x30 ngày).
   - Cột Dự Kiến trên bảng Gantt và file xuất Excel hiển thị linh hoạt: `2 giờ`, `5 ngày`, `2 tuần`, `1 tháng`... qua hàm `formatPlanDuration(task)`.
3. **Chuẩn hóa mã công việc tăng dần tuần tự (Loại bỏ Math.random):**
   - Thay thế toàn bộ mã ngẫu nhiên bằng cơ chế sinh mã tự tăng tuần tự `generateNextTaskId(year)` (ví dụ: `CV-2026-0021`, `CV-2026-0022`...).
   - Đảm bảo mã công việc chính và mã công việc con luôn tăng dần theo thứ tự logic, không bị nhảy số ngẫu nhiên.
4. **Bộ lọc ưu tiên và 6 chế độ sắp xếp đa chiều:**
   - Thêm bộ lọc **Ưu tiên / Nguồn yêu cầu**: Giám đốc, Trưởng phòng, Đối ứng sự cố, Cải thiện nội bộ, Dự án chiến lược, Khác.
   - Thêm dropdown **Sắp xếp** 6 chế độ:
     1. `👤 Người ➔ Ngày nhận việc (Mặc định)`: Gom nhóm nhân sự, sắp xếp theo ngày nhận việc tăng dần.
     2. `🔢 Thứ tự mã việc`: Sắp xếp theo mã CV tăng dần.
     3. `📅 Ngày bắt đầu`: Việc bắt đầu sớm nhất xếp trước.
     4. `⏳ Hạn hoàn thành`: Deadline gấp nhất xếp trước.
     5. `🎯 Mức độ ưu tiên`: Giám đốc ➔ Trưởng phòng ➔ Đối ứng ➔ Cải tiến ➔ Chiến lược ➔ Khác.
     6. `⚠️ Quá hạn / Cần cập nhật`: Việc quá hạn và quá 3 ngày chưa cập nhật được ưu tiên đưa lên đầu trang.
5. **Nâng cấp DB_VERSION lên 3.1:**
   - Tự động xóa cache LocalStorage cũ khi tải trang để nạp toàn bộ cấu trúc dữ liệu mới nhất từ `database.js`.

### Phiên Bản 2.9.0 (07/10/2026) - Tối Ưu Timeline Tháng & Chuẩn Hóa Mã Công Việc:
1. **Timeline MONTH thông minh — chỉ hiển thị đúng khoảng tháng có công việc:**
   - Thêm `getTasksMonthSpan(taskList)`: tính startYear/startMonth → endYear/endMonth thực tế từ tập task (hỗ trợ lọc theo nhân viên).
   - `getTimelineColumns()` chế độ MONTH giờ tự động co giãn từ tháng sớm nhất đến tháng muộn nhất. Không còn hiện cố định 2026→2029.
   - Nếu có lọc khoảng ngày tự do, ưu tiên khoảng đó cho timeline MONTH.
2. **Chuẩn hóa Mã Công Việc Chi Tiết sang CV-YYYY-XXXX:**
   - Thêm `generateNextTaskId(year)`: tự động tìm số thứ tự tiếp theo trong năm, trả về `CV-2026-0001`, `CV-2026-0002`...
   - `handleSaveTask()` khi tạo mới dùng `generateNextTaskId` thay vì `TASK-XXXX`.
   - Form thêm việc: mã Công Việc Chính mặc định sinh dạng `CV-YYYY-XXXX`.
3. **Fix hoisting bug trong `executeExportExcelReport()`:**
   - Tách thành 2 bước rõ ràng: Bước 1 lọc/gom task trước, Bước 2 xây dựng timelineCols sau → xóa lỗi `tasksToExport` chưa khai báo khi dùng FIT_TASKS.
4. **Bộ dữ liệu demo phong phú (database.js v2.9):**
   - **33 công việc** trải từ **T1/2026 → T6/2027**, 12 nhóm dự án, 5 nhân viên.
   - Phủ đủ mọi trạng thái: Hoàn thành (6), Hoàn thành trễ (5), Đang làm (14), Tạm dừng (2), Dừng dự án (1), Quá hạn (tự tính).
   - Tất cả ID đúng chuẩn `CV-YYYY-XXXX`.
5. **Auto-invalidate LocalStorage cache theo DB_VERSION:**
   - Thêm hằng `DB_VERSION = '2.9'` trong `app.js`. Khi bump version → cache cũ tự động xóa, data mới từ `database.js` được nạp lại ngay lập tức.


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

### Phiên Bản 3.0.0 (07/10/2026) - Nâng Cấp 6 Tính Năng Quản Lý Tiến Độ Nâng Cao:
1. **Mã Nhân Viên Tự Động Tăng (`NV-0001` → `NV-0002`...):**
   - Hệ thống tự động quét và tính toán số thứ tự lớn nhất, điền sẵn định dạng chuẩn `NV-XXXX` khi mở form thêm mới.
   - Ô mã NV ở chế độ read-only mặc định kèm nút cây bút cho phép chỉnh sửa thủ công khi cần.
2. **Biểu Đồ Thực Tích Khi Đang Làm (In-Progress Gantt Bar):**
   - Với các công việc đang thực hiện (chưa có ngày hoàn thành thực tế), biểu đồ thực tích tự động vẽ dải màu xanh ngọc / cyan gradient kèm hiệu ứng chuyển động nhịp nhàng (pulse animation) kéo dài từ ngày bắt đầu đến ngày hôm nay.
   - Giúp người quản lý nắm bắt trực quan các đầu việc đang chạy ngay cả khi chưa kết thúc.
3. **Cảnh Báo Quá 3 Ngày Chưa Cập Nhật & Modal Nhật Ký Tiến Độ:**
   - Đối với các kiện chưa hoàn tất, nếu quá 3 ngày chưa ghi nhận cập nhật, dòng công việc tự động nổi màu đỏ cảnh báo (`row-overdue-update`) kèm nhãn `Cần Cập Nhật (X ngày)`.
   - Bổ sung nút **"Cập nhật tình trạng"** trực tiếp trên từng dòng, mở Modal ghi nhật ký tiến độ (lưu lịch sử ngày, giờ, nội dung thay đổi, trạng thái, người cập nhật).
4. **Huy Hiệu Phân Loại Nguồn Yêu Cầu Đa Sắc:**
   - Thêm trường `taskSource` trong form công việc với các tùy chọn: Giám đốc (tím), Trưởng phòng (xanh dương), Đối ứng sự cố (vàng cam), Cải thiện nội bộ (xanh lá), Dự án chiến lược (đỏ hồng), Khác (xám).
   - Hiển thị trực tiếp dạng badge rõ nét ngay dưới tên công việc trên bảng Gantt.
5. **Bố Trí Công Việc: Người => Thứ Tự Việc (Theo Ngày Nhận Việc):**
   - Bảng công việc gom nhóm tổng thể theo từng Nhân viên phụ trách.
   - Có thanh tiêu đề phân cách nhóm nhân viên (`emp-group-header`).
   - Trong mỗi nhóm nhân viên, các công việc được sắp xếp tăng dần theo Ngày nhận việc (`startDate`), sau đó theo ID.
6. **Quản Lý Lịch Nghỉ Lễ & Ngày Nghỉ Đặc Biệt (Holiday Calendar):**
   - Bổ sung nút **"Lịch Nghỉ"** trên thanh công cụ và Modal quản lý ngày nghỉ.
   - Cho phép cài đặt ngày lễ quốc gia (màu đỏ) và ngày nghỉ đặc biệt nội bộ (màu tím).
   - Cột ngày nghỉ trên dòng thời gian Timeline được tô màu trực quan kèm tooltip hiển thị tên ngày nghỉ.
