# Project Log - MBC Quản Lý Công Việc & Hiệu Suất Nhóm

## Thông Tin Dự Án
- **Tên dự án:** Ứng dụng Web Quản Lý Công Việc & Nhân Sự Toàn Diện (Gantt Timeline & Performance Points)
- **Vị trí:** `c:\Users\12953 Bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\GravityCode\MBC\QuanLyCongViecNhom`
- **Phiên bản:** v5.5.0 (Thêm Tính Năng Xuất Excel Chuẩn Biểu Mẫu "Quản Lý Đối Ứng Chỉ Thị Nội Bộ P.KT - Năm 2026")
- **Ngày cập nhật:** 26/10/2026.

---

## Nhật Ký Cập Nhật (Change Log)

### Phiên Bản 5.5.0 (26/10/2026) - Xuất Excel Chuẩn Biểu Mẫu "Quản Lý Đối Ứng Chỉ Thị Nội Bộ P.KT - Năm 2026":

1. **Khởi Tạo Chức Năng Xuất Excel Biểu Mẫu P.KT (`exportDoiUngChiThiExcel`):**
   - **Tương thích chính xác biểu mẫu:** Khớp 100% cấu trúc, bố cục dòng tiêu đề, màu sắc header (`#E6B8B7`), tên sheet XML (`Nghiệp vụ chung`) theo file mẫu gốc: `FormMau/2. File quan ly doi ung chi thi noi bo P.Kiem Tra-nam 2026.xlsb`.
   - **Cấu trúc 12 cột chuẩn:**
     1. `Đối tượng`: Trích xuất từ `task.taskSource` (Giám đốc, Trưởng phòng, Mục tiêu năm, Nội bộ P.KT...).
     2. `Đảm trách`: Người đang nhận việc (`task.empName`), tự động chuẩn hóa sang định dạng Mã NV + Tên (ví dụ: `12333 Sỹ`, `13011 Thanh`, `11466 Thảo`, `25762 Na`, `20301 Liễu`, `11533 Vũ`...).
     3. `Chịu trách nhiệm`: Mặc định là **`12953 Bảo`** theo chỉ đạo.
     4. `Nội dung`: Tên / nội dung chi tiết công việc kết hợp đầy đủ (`task.title: task.detail`).
     5. `Ngày chỉ thị lần đầu`: Ngày bắt đầu công việc `dd/mm/yyyy`.
     6. `Kỳ hạn yêu cầu`: Ngày hạn kế hoạch `dd/mm/yyyy`.
     7. `Ngày hoàn tất`: Ngày hoàn thành thực tế (chỉ hiển thị ngày hoặc để trống nếu chưa xong).
     8. `Tình trạng xử lý`: Chuẩn hóa mã trạng thái biểu mẫu (`HT DUNGHAN`, `HT TRUOCHAN`, `HT TREHAN`, `CHUADENHAN`, `TRE HAN`, `TAM DUNG`).
     9. `Lý do thay đổi kỳ hạn`: Trích xuất từ `task.changeReason`.
     10. `Note`: Lấy **nội dung nhật ký / ghi chú mới nhất** từ `statusLogs` hoặc `task.note`.
     11. `Link dữ liệu`: Render hyperlink chữ **`XEM`** màu xanh dương đậm có gạch chân, click mở tài liệu trực tiếp.
     12. `Nơi báo cáo`: Xác định cấp báo cáo (`Giám đốc`, `Trưởng Phòng`...) dựa trên nguồn việc `task.taskSource`.
   - **Quy tắc sắp xếp:** Chuẩn hóa thứ tự 3 cấp: `Dự án chính => Người đảm trách => Tình trạng xử lý => Ngày bắt đầu`.
   - **Giao diện người dùng (UI):**
     + Thêm nút bấm tại **Menu Quản Trị (Admin)**: `Xuất Đối Ứng Chỉ Thị P.KT (Form 2026)`.
     + Thêm nút bấm nổi bật tại **Modal Sao Lưu & Xuất Dữ Liệu**: `Xuất Đối Ứng Chỉ Thị P.KT (Form Mẫu 2026 .xls)`.

---

### Phiên Bản 5.4.0 (14/10/2026) - Khớp 100% 63 Công Việc, Nút [Toàn Bộ] & Chuẩn Hóa Xuất Excel:

1. **Khắc Phục 63 vs 54 Công Việc & Nút [Toàn Bộ] (Hình 1):**
   - **Nguyên nhân gốc:** Logic `tEnd` trong bộ lọc tháng trước đây lấy `parseDate(task.actualEndDate)` trước khi kiểm tra việc đã xong hay chưa, khiến 5 công việc đang làm/tạm dừng có ngày cũ trong `actualEndDate` bị tính nhầm là kết thúc trong quá khứ và bị ẩn. Thêm 4 việc của tháng khác/năm sau dẫn đến thiếu đúng 9 việc (63 - 9 = 54).
   - **Xử lý:**
     + Sửa thuật toán tính `tEnd` trong `renderMainTable()`, `isTaskInMonth()`, `isTaskInYear()`: Việc chưa hoàn thành luôn tồn đọng và hiển thị, không dùng `actualEndDate` cũ để loại bỏ.
     + Bổ sung nút **[Toàn bộ]** ngay cạnh nút `[Nay]` và `[Vừa hạn cuối]` trên thanh công cụ. Click 1 chạm là hiển thị trọn vẹn **63/63 công việc** không sót việc nào.
     + Click thẻ KPI "Tổng số việc (63)" tự động kích hoạt chế độ toàn bộ và thu phóng biểu đồ khớp 63 việc.

2. **Chuẩn Hóa Cấu Trúc Cột Xuất Báo Cáo Excel (Hình 2):**
   - Cột **"Dự Án Chính"**: Hiển thị tên/mã dự án thực tế (`task.mainTaskTitle || task.mainTaskId || 'Việc độc lập'`), loại bỏ hoàn toàn các chuỗi không có ý nghĩa như "Độc lập" hay "Đang làm (1/3)".
   - Cột **"Hoàn Thành"**: Chỉ hiển thị ngày hoàn thành thực tế (`dd/mm/yyyy`), nếu chưa hoàn thành để ô trống `""` (không còn điền chữ "Tạm dừng" hay "Chưa xong" trùng lặp với cột Tình trạng).
   - Bổ sung 6 cột mới theo yêu cầu:
     + **Người Giao Việc**: Trích xuất từ `task.taskSource` (Tổng Giám đốc, Giám đốc, Trưởng phòng...).
     + **Thể Loại**: Phân loại chuẩn `Theo dự án` hoặc `Việc độc lập`.
     + **Hiện Trạng (Mới Nhất)**: Nội dung ghi chú cập nhật mới nhất từ `statusLogs` hoặc `task.note`.
     + **Ghi Chú Lần 1**: Lịch sử cập nhật lần 1 `[Ngày - Tiến độ%]: Nội dung`.
     + **Ghi Chú Lần 2**: Lịch sử cập nhật lần 2 `[Ngày - Tiến độ%]: Nội dung`.
     + **Ghi Chú Lần 3**: Lịch sử cập nhật lần 3 `[Ngày - Tiến độ%]: Nội dung`.

3. **Khắc Phục Wraptext Chống Đè Chữ, Khớp Bộ Lọc & Sắp Xếp 3 Cấp (Hình 3):**
   - **Chống đè chữ:** Áp dụng CSS `white-space: normal; word-break: break-word; overflow-wrap: break-word; height: auto; mso-height-source: auto; table-layout: auto;` kết hợp độ rộng cột hào phóng (200px - 240px cho mô tả và nhật ký), đảm bảo Excel tự động tính chiều cao hàng theo nội dung, chữ không bao giờ bị đè hay cắt ngang.
   - **Sửa triệt để lọc "Đang làm" lọt việc "Tạm dừng":** Sử dụng `getTaskEffectiveStatus(task, today)` trong hàm xuất Excel, khi lọc `DANG_LAM` loại bỏ triệt để 100% các công việc có trạng thái `Tạm dừng` hoặc đã hoàn thành.
   - **Sắp xếp 3 cấp khi xuất Excel:**
     1. Cấp 1: Nhóm theo **Dự án chính** (các công việc cùng dự án đứng liền kề nhau, việc độc lập gom sau).
     2. Cấp 2: Sắp xếp theo **Người thực hiện** (A ➔ Z).
     3. Cấp 3: Sắp xếp theo **Tình trạng** (`Đang làm` ➔ `Đang làm (Trễ hạn)` ➔ `Tạm dừng` ➔ `Hoàn thành` ➔ `Hoàn thành trễ`).

---

### Phien Ban 5.3.0 (14/10/2026) - Chon Nhanh Nhan Su & Bao Toan Nhat Ky Hien Trang:

1. **Chon Nhanh Nhan Vien Chinh (taskModal):**
   - O tim kiem taskEmpSearchInput + datalist taskEmpDatalist goi y ten/ma NV khi go.
   - Go ten hoac ma NV (vd: Bao, NV06) tu dong map sang select taskEmpId.
   - Badge xanh taskEmpSelectedBadge hien thi NV da chon. Nut X de xoa.
   - Khi sua CV cu: o search tu dien ten NV chinh tu database.

2. **Chon Nhanh Nhan Su Phoi Hop/Phu (taskModal):**
   - Nut Tat ca va Bo chon de chon/bo chon toan bo nguoi phu cung luc.
   - O loc nhanh supportEmpSearchInput - filter realtime trong danh sach checkbox.
   - Badge supportEmpCountBadge cap nhat realtime so nguoi phu da chon.

3. **Bao Toan Lich Su Nhat Ky Hien Trang (statusLogs):**
   - Sua handleSaveTask(): task.statusLogs KHONG bi xoa khi chinh sua CV da hoan thanh.
   - Task moi khoi tao statusLogs: [] de nhat quan cau truc du lieu.

4. **Ham JS Moi:** populateTaskEmpDatalist, handleLeadEmpSearch, handleLeadEmpSelectChange,
   clearLeadEmpSearch, selectAllSupportEmps, clearAllSupportEmps,
   filterSupportEmpList, updateSupportEmpCountBadge.

### Phiên Bản 5.2.0 (14/10/2026) - Khớp 100% 56 Thống Kê KPI, Bộ Lọc Tháng/Năm & Nút Mở Thử Kênh Đôi:

1. **Khớp Chuẩn Xác 100% 56 Công Việc Thống Kê KPI (Hình 1):**
   - **Vấn đề cũ:** Tổng số công việc là 56, nhưng các thẻ con cộng lại chỉ được 24 việc (thiếu 32 việc). Nguyên nhân:
     + Hàm `updateKPIStats()` so khớp nhầm trạng thái `st === 'Quá hạn'` trong khi `getTaskEffectiveStatus()` trả về chuỗi `'Đang làm (Trễ hạn)'`, dẫn tới toàn bộ các việc đang làm bị trễ hạn bị rơi ra ngoài không được đếm vào thẻ Đang làm hay Quá hạn.
     + Thiếu hoàn toàn thẻ thống kê cho 15 công việc đang ở trạng thái **Tạm dừng**.
   - **Xử lý triệt để:**
     + Bổ sung thẻ KPI thứ 5: **"Tạm dừng"** (`cardKpiPaused`, icon `fa-circle-pause`, số lượng 15 việc). Click vào thẻ lọc ngay danh sách 15 việc tạm dừng.
     + Sửa thuật toán đếm: Tổng số (56) = Đang thực hiện (29) + Đúng hạn (9) + Hoàn thành trễ (3) + Tạm dừng (15). Khớp chuẩn 100% không bao giờ lệch dù chỉ 1 việc.
     + Thẻ phụ "Tồn đọng trễ hạn" hiển thị đúng số lượng công việc đang làm mà đã quá thời hạn kế hoạch.

2. **Bộ Lọc Phạm Vi Thời Gian Cho Hàng Thẻ Thống Kê KPI (Hình 1):**
   - Tích hợp thanh điều khiển phạm vi ngay trên hàng thẻ KPI:
     + Dropdown `#kpiScopeFilter`:
       - `🌐 Toàn bộ (Tất cả 56 công việc)`: Thống kê toàn cảnh mọi công việc trong hệ thống.
       - `📅 Theo tháng đang xem`: Tự động tính toán số lượng việc giao thoa với tháng được chọn trên thanh công cụ (vd: Tháng 10/2026).
       - `📆 Cả năm (2026)`: Thống kê toàn bộ các việc phát sinh hoặc diễn ra trong năm.
     + Badge nhãn `#kpiScopeSummary`: Hiển thị trực quan phạm vi và số việc đang xét (vd: `Phạm vi: Toàn bộ (56 việc)` hoặc `Phạm vi: Tháng 10/2026 (48 việc)`).

3. **Cơ Chế Mở File / Thư Mục Kênh Đôi & Nút [ ↗ Mở Thử ] Trên Modal Link (Hình 2):**
   - **Nút [ ↗ Mở Thử ]:** Bổ sung nút màu xanh ngọc lục bảo ngay trong modal `taskLinkModal`. Khi dán đường dẫn file Excel, Word hoặc thư mục mạng UNC (`\\vdm-fsvr\...`), người dùng có thể bấm `[ ↗ Mở Thử ]` để kiểm tra mở Explorer hoặc ứng dụng Windows ngay lập tức trước khi lưu.
   - **Kỹ thuật Mở Kênh Đôi (Dual-Channel Bridge):**
     + Kênh 1 (`fetch`): Gửi yêu cầu tới `http://127.0.0.1:38271/open?path=...`.
     + Kênh 2 (`invisible iframe` fallback): Nếu trình duyệt Chrome chạy từ giao thức `file:///` chặn CORS / Private Network Access, hệ thống tự động kích hoạt một `iframe` ngầm không hiển thị để gửi lệnh GET trực tiếp tới Python helper, đảm bảo lệnh mở `explorer.exe` hoặc `os.startfile` luôn luôn được thực thi 100%.
     + Tự động sao chép đường dẫn sạch vào Clipboard kèm thông báo hướng dẫn.
   - **Khởi động Localhost Cùng Origin:** Cập nhật `Chay_Ung_Dung_MBC.vbs` và `start_app.bat` tự động mở trình duyệt tới `http://127.0.0.1:38271/` (phục vụ trực tiếp từ helper), loại bỏ hoàn toàn mọi rào cản CORS và bảo mật trình duyệt.

---

### Phiên Bản 5.1.0 (14/10/2026) - CSDL Đa Profile, Tự Làm Sạch Link & Popup Sửa Nhân Sự:

1. **CSDL Tập Trung Lưu Thẳng Ổ Đĩa Dùng Chung Mọi Chrome Profile (Hình 1):**
   - Vấn đề cũ: Người dùng có nhiều tài khoản/Profile Chrome (`gms00-09`, `gms10-19`, `gsv20->`), trước đây lưu vào `localStorage` riêng lẻ của từng profile dẫn đến lệch dữ liệu.
   - Giải pháp: Bổ sung 2 API vào `open_file_helper.py`:
     - `GET /api/data`: Đọc file `database.json` trong thư mục `QuanLyCongViecNhom` trên máy tính.
     - `POST /api/data`: Nhận dữ liệu cập nhật và ghi trực tiếp vào `database.json` (tự động sao lưu `database.backup.json` an toàn chống hỏng file).
   - Bảo toàn tuyệt đối dữ liệu: Khi mở web app trên profile `gms00-09`, nếu `localStorage` có dữ liệu thực tế (16 nhân viên, danh sách công việc đầy đủ) lớn hơn file mẫu trên máy, hệ thống ưu tiên giữ nguyên 100% dữ liệu này và đồng bộ ngay vào `database.json`. Các profile khác (`gms10-19`, `gsv20->`) mở lên sẽ tự động nạp chung CSDL này.
   - Mọi thao tác thêm/sửa/xóa công việc, nhân sự đều ghi đồng thời vào `localStorage` và `database.json` trên ổ đĩa.

2. **Tự Động Làm Sạch & Chuẩn Hóa Link Windows Khi Dán (Hình 2):**
   - Vấn đề cũ: Khi người dùng copy đường dẫn từ Explorer bằng "Copy as path", Windows tự bọc dấu ngoặc kép `"..."`. Code cũ không gỡ bỏ ngoặc kép làm `os.startfile` bị lỗi cú pháp `WinError 123`.
   - Giải pháp:
     - Tạo hàm `autoCleanWindowsPath()` ở cả frontend `app.js` và `open_file_helper.py`: Tự động loại bỏ hoàn toàn mọi dấu ngoặc kép (`"`, `'`), khoảng trắng thừa, tiền tố `file:///`, chuẩn hóa dấu gạch chéo ngược `\` cho cả ổ đĩa cục bộ (`C:\...`) và thư mục mạng UNC (`\\vdm-fsvr\...`).
     - Tích hợp sự kiện `oninput` và `onpaste` trên các ô nhập link (`taskLink`, `taskLinkModalInput`): Khi người dùng dán đường dẫn từ Windows Explorer, hệ thống tự động làm sạch và hiển thị đường dẫn chuẩn ngay lập tức.
     - `openTaskFileLink()`: Gọi `autoCleanWindowsPath()` trước khi gửi sang Python helper, hiển thị thông báo lỗi chi tiết nếu đường dẫn không tồn tại trên máy thay vì báo sai "Chưa bật helper".

3. **Bộ Lọc Dự Án Trực Quan (Hình 3):**
   - Vấn đề cũ: Dùng thẻ HTML5 `<datalist>` khiến Chrome không tự động mở danh sách khi nhấp chuột vào ô (chỉ hiện con trỏ nhấp nháy `|-- Tất cả dự án --`), gõ tìm kiếm không ăn khớp.
   - Giải pháp: Chuyển đổi bộ lọc Dự án thành dạng Dropdown `<select id="filterMainTask">` giao diện đẹp mắt, nhấp chuột là mở ngay danh sách tất cả các dự án kèm số lượng công việc con `[Mã] Tên dự án (N việc)`, có mục `🍃 Chưa thuộc dự án nào (Việc riêng lẻ)`, chọn là lọc ngay lập tức; có nút `[x]` để xóa chọn về Tất cả dự án.

4. **Modal Popup Chỉnh Sửa Nhân Sự Trực Tiếp (Hình 4):**
   - Vấn đề cũ: Khi danh sách nhân viên dài và người dùng cuộn xuống dòng cuối cùng (như NV-0016 Võ Thị Lý), nhấn nút sửa [✏️] thì form nằm khuất ở đầu trang, màn hình không tự cuộn lên nên người dùng tưởng nút bị liệt.
   - Giải pháp: Tạo Modal Popup **"Chỉnh Sửa Thông Tin Nhân Sự"** (`editEmployeeModal`) hiện ngay giữa màn hình khi nhấn nút [✏️]:
     - Hiển thị đầy đủ: Mã NV, Họ & Tên, Bộ phận / Phòng ban.
     - Nhấn [Cập Nhật] là lưu dữ liệu, tự động đồng bộ tên nhân sự trong tất cả các công việc liên quan và ghi xuống `database.json`.

1. **File Khởi Động 1-Click `Chay_Ung_Dung_MBC.vbs`:**
   - Thay thế hoàn toàn `start_app.bat`: Click đúp → Python helper chạy hoàn toàn ngầm (không hiện cửa sổ đen) + trình duyệt tự mở `index.html`.
   - Tạo `cai_dat_tu_khoi_dong.bat`: Chạy 1 lần duy nhất → Python helper tự khởi động cùng Windows mỗi khi bật máy.
   - Tạo `huy_tu_khoi_dong.bat`: Gỡ cài đặt tự khởi động khi cần.

2. **Sửa Triệt Để Lỗi Mở File/Thư Mục UNC Mạng Nội Bộ (Hình 1 & 2):**
   - Hàm `_normalizeWindowsPathForBridge()` trong `app.js`: Bảo toàn 100% định dạng UNC (`\\vdm-fsvr\...`), xử lý mọi biến thể (`file://`, `file:///`, `\\`, `//`).
   - `open_file_helper.py`: Logic chuẩn hóa đường dẫn hoàn toàn cải tiến — nhận diện UNC vs local drive; fallback tự động qua `explorer.exe` nếu `os.startfile` báo lỗi.
   - **`_fallbackLocalFileOpen()`** khi helper chưa chạy: Tuyệt đối KHÔNG gọi `window.open()` (tránh Chrome tải file về hoặc hiển thị "Index of"). Chỉ sao chép đường dẫn vào Clipboard + hiển thị toast cảnh báo hướng dẫn.

3. **Cải Thiện Nút "Tự Làm Dự Án" (Hình 3):**
   - Click `[⭐ Tự làm Dự án]`: Hệ thống tự động lấy nội dung chi tiết (`taskDetail`) của công việc hiện tại làm Tên Dự Án Mẹ mới. Mã dự án mẹ = mã công việc hiện tại.
   - Danh sách chọn dự án mẹ `getAvailableParentTasks()`: Loại bỏ hoàn toàn các công việc thường, **chỉ giữ lại Dự án thực thụ** (sạch sẽ, đúng chuẩn).

4. **Bộ Lọc Công Việc Chưa Thuộc Dự Án (Hình 4):**
   - Thêm option `🍃 Chưa thuộc dự án nào (Việc riêng lẻ)` vào ô lọc Dự án.
   - Cả 3 block `filterMainTask` trong `applyFilters`, `fitTimelineToTaskDates` và banner đều xử lý đúng khi `__NO_PROJECT__`.
   - Có thể chọn từ dropdown hoặc gõ "chưa thuộc" / "riêng lẻ" vào ô tìm kiếm dự án.

5. **Gom Gọn Header: Menu Quản Trị CSDL Dropdown (Hình 5):**
   - Giữ lại 3 nút nghiệp vụ: `+ Thêm Công Việc`, `Cập Nhật Tiến Độ`, `Bảng Điểm KPI`.
   - 8 nút admin gom vào menu `[🗄️ Quản Trị CSDL ▾]` sang trọng: Dự án, Nhân sự, Lịch nghỉ, Xóa CV, Xuất Excel Gantt, Xuất CSDL xlsx, Import CV, Import Nhân sự, File JSON.
   - Chấm màu `🟢/⚪` ngay trên nút báo trạng thái File Helper đang chạy hay chưa; tự kiểm tra mỗi 15 giây.
   - Menu tự đóng khi click ra ngoài.

---
---

## Nhật Ký Cập Nhật (Change Log)

### Phiên Bản 4.9.0 (14/10/2026) - Chuẩn Hóa Ngày Hoàn Thành Thực Tế & Micro-Bridge Mở File Windows Trực Tiếp:

1. **Chuẩn Hóa Cột "Thời Gian Hoàn Thành" Khi Chưa Có Ngày Thực Tế (Hình 1 & Hình 2):**
   - **Vấn đề cũ:** Tại modal sửa công việc, trường *Thời gian hoàn thành thực tế* để trống (`dd/mm/yyyy`), nhưng trên bảng dữ liệu chính cột *Thời gian hoàn thành* lại bị tự động điền ngày kết thúc kế hoạch (`25/06/2026`).
   - **Xử lý:**
     - Loại bỏ hoàn toàn fallback tự điền ngày kết thúc kế hoạch vào cột hoàn thành thực tế.
     - Kiểm tra biến `hasActualEnd = !!(task.actualEndDate && String(task.actualEndDate).trim() && String(task.actualEndDate).trim() !== 'Chưa hoàn thành')`.
     - Nếu `hasActualEnd` có giá trị: Hiển thị ngày dạng `dd/mm/yyyy` (in đậm màu ngọc bích `text-emerald-700`).
     - Nếu chưa có: Hiển thị rõ ràng là **"Chưa có"** (màu xám `text-slate-400`), hoặc **"Tạm dừng"** nếu công việc đang hoãn. Tuyệt đối không sinh ngày ảo.

2. **Giải Pháp Mở Tệp Cục Bộ Bằng Ứng Dụng Mặc Định Windows (Hình 3):**
   - **Vấn đề cũ:** Do Sandbox bảo mật của trình duyệt web (Chrome, Edge), khi bấm nút `[Mở]` tệp đính kèm (như `.xlsx`, `.docx`, `.pdf`), trình duyệt mặc định tải tệp về thư mục Downloads thay vì khởi chạy trực tiếp Microsoft Excel/Word.
   - **Xử lý triệt để:**
     - Tạo micro-bridge chuẩn Python không phụ thuộc thư viện ngoài: `open_file_helper.py` chạy dịch vụ HTTP cục bộ siêu nhẹ tại `127.0.0.1:38271`.
     - Khi nhận yêu cầu `/open?path=...`, helper gọi trực tiếp hàm native `os.startfile(clean_path)` của Windows, mở ngay ứng dụng mặc định (Excel, Word, PDF Reader, File Explorer) với đúng file gốc mà **không tải xuống**.
     - Cung cấp file chạy nhanh 1-click **`start_app.bat`**: Tự động bật `open_file_helper.py` dưới nền và mở `index.html` trên trình duyệt.
     - Hàm `openTaskFileLink(taskId)` trên `app.js` gửi `fetch` tới helper cục bộ (timeout 1.2s). Nếu helper đang chạy -> file mở ngay lập tức trên máy. Nếu chưa bật helper -> tự động kích hoạt fallback sao chép đường dẫn vào Clipboard và hướng dẫn người dùng.

---

### Phiên Bản 4.8.0 (13/10/2026) - Chuẩn Hóa Trạng Thái Công Việc, Lọc Nguồn & Tìm Kiếm Nhanh Datalist:

1. **Chuẩn Hóa Trạng Thái "Hoàn Thành" & "Đang Thực Hiện" (Hình 1 & Hình 2):**
   - **Hình 1:** Khi công việc có trạng thái được ghi nhận là "Hoàn thành" (như qua cập nhật hoặc file Excel), hệ thống giữ nguyên vẹn kết quả là **"Hoàn Thành"** đúng hạn kể cả khi ô `actualEndDate` chưa nhập riêng. Cột thời gian hoàn thành tự động hiển thị ngày kết thúc kế hoạch thay vì hiển thị "Chưa hoàn thành".
   - **Hình 2:** Công việc đang làm dở dù đã vượt quá thời hạn dự tính kế hoạch vẫn giữ đúng bản chất là **"Đang thực hiện"** kèm chỉ báo trễ tiến độ (`Đang thực hiện (Trễ hạn)`). Khi người dùng lọc thẻ "Đang thực hiện", các công việc này **vẫn luôn hiển thị đầy đủ**, không còn bị loại nhầm khỏi danh sách đang làm.

2. **Cơ Chế Mở Tệp / Link & Tự Động Sao Chép Đường Dẫn Windows (Hình 3):**
   - Do chính sách bảo mật Sandbox của trình duyệt web (Chrome, Edge) không cho phép mã web kích hoạt trực tiếp phần mềm hệ thống (như tự mở Excel/Word) mà sẽ tải tệp xuống:
   - Hệ thống bổ sung tính năng **Tự động sao chép đường dẫn tệp sạch (Clean Path)** vào Clipboard ngay khi click nút `[Mở]` kèm Toast thông báo hướng dẫn: *"Nhấn Win+R hoặc dán vào File Explorer để mở trực tiếp"*.
   - Hướng dẫn người dùng thiết lập 1 lần trên trình duyệt: Chuột phải vào file tải xuống chọn *"Luôn mở tệp loại này"* (Always open files of this type) để trình duyệt tự động gọi phần mềm mặc định của máy tính mở file khi nhấp.

3. **Sửa Lỗi Lọc Nguồn Yêu Cầu "Cải Tiến" / "Cải Thiện" (Hình 4):**
   - Bổ sung cơ chế so khớp linh hoạt hai chiều: Khi click badge `[Cải tiến]`, bộ lọc sẽ tìm kiếm đồng thời cả từ khóa `Cải tiến` lẫn `Cải thiện` / `Cải thiện nội bộ`. Tương tự, hỗ trợ viết tắt `TGĐ` cho `Tổng Giám đốc`, `TP` cho `Trưởng phòng`.
   - Cung cấp thông báo Toast hiển thị trực quan nguồn yêu cầu đang lọc và tự động đồng bộ giá trị trên dropdown `#filterPriority`.

4. **Nâng Cấp Ô Nhập Tìm Kiếm Trực Tiếp Nhân Sự & Dự Án (Hình 5):**
   - Thay thế các dropdown tĩnh khó cuộn bằng cặp **Searchable Input + HTML5 `<datalist>`** cho cả **Nhân sự (`#filterEmployeeSearch`)** và **Dự án (`#filterMainTaskSearch`)**.
   - Người dùng vừa có thể bấm mũi tên chọn từ danh sách, vừa có thể **gõ trực tiếp** tên, mã nhân viên (vd: `Bảo`, `Thảo`, `NV01`) hoặc mã, tên dự án (vd: `4598`, `Brose`, `CV-2026-0049`) để lọc tức thì.
   - Bổ sung nút ✖ xóa nhanh để quay về chế độ hiển thị toàn bộ chỉ với 1 click.

---

### Phiên Bản 4.7.0 (13/10/2026) - Khắc Phục Lỗi Quản Lý Dự Án & Chuẩn Hóa Logic Hoàn Thành Công Việc:

1. **Khắc Phục Lỗi Quản Lý Dự Án & Bổ Sung Xóa Nhanh Hàng Loạt (Hình 1 & 2):**
   - **Nguyên nhân cũ:** `getUniqueMainTasks()` trước đó dùng fallback `t.mainTaskId || t.id`, dẫn tới tất cả việc riêng lẻ không thuộc dự án (`mainTaskId = ''`) đều tự động bị biến thành 1 dự án riêng (sinh ra 49 dự án ảo). Khi bấm xóa, task con vẫn còn nên dự án lại tự động sinh lại.
   - **Xử lý:**
     - Tách biệt hoàn toàn: Công việc riêng lẻ tuyệt đối KHÔNG bao giờ bị xem là dự án.
     - Hàm `ensureProjectsInitialized()` tự động dọn dẹp (cleanse) các dự án rác sinh nhầm từ ID của các công việc riêng lẻ cũ.
     - Thêm cột **Checkbox Chọn Nhiều** và nút **"Chọn tất cả" (`selectAllProjects`)** trong bảng quản lý dự án.
     - Bổ sung nút **"🗑️ Xóa đã chọn (n)" (`handleBulkDeleteProjects`)** trên toolbar: cho phép tick chọn hàng loạt dự án để xóa một lần nhanh chóng; toàn bộ công việc con thuộc các dự án đó tự động chuyển thành việc riêng lẻ an toàn.

2. **Sửa Lỗi Chưa Có Ngày Hoàn Thành Nhưng Được Tính Là Hoàn Thành (Hình 3):**
   - **Nguyên nhân cũ:** Logic hiển thị trạng thái và thống kê chỉ dựa vào chuỗi `task.status === 'Hoàn thành'` lưu từ trước mà không kiểm tra trường ngày kết thúc thực tế (`actualEndDate`).
   - **Xử lý:**
     - Xây dựng hàm chuẩn hóa duy nhất toàn hệ thống: `getTaskEffectiveStatus(task, refToday)`.
     - Quy tắc cứng: Nếu `actualEndDate` còn trống hoặc không hợp lệ -> Công việc **KHÔNG BAO GIỜ** được xem là "Hoàn thành" (hiển thị đúng là "Đang làm" hoặc "Quá hạn" nếu ngày kết thúc kế hoạch < hôm nay).

3. **Sửa Lỗi Thời Gian Hoàn Thành Đúng Kỳ Hạn Lại Bị Đánh Dấu Quá Hạn (Hình 4):**
   - **Nguyên nhân cũ:** Một số công việc đã có ngày kết thúc thực tế (`actualEndDate`) trùng khớp hoặc trước hạn kế hoạch (`planEndDate`) (ví dụ ngày kết thúc thực tế `09/10/2026` <= ngày kế hoạch `09/10/2026`), nhưng do `task.status` chưa được cập nhật từ import Excel hoặc form cũ, rơi vào nhánh so sánh ngày kế hoạch với `today (13/10/2026)` dẫn đến bị dán nhãn "Quá hạn".
   - **Xử lý:**
     - Khi `actualEndDate` tồn tại: so sánh trực tiếp `actualEndDate` với `planEndDate`.
     - Nếu `actualEndDate <= planEndDate` -> Luôn luôn là **"Hoàn thành"** (Đúng hạn).
     - Nếu `actualEndDate > planEndDate` -> Là **"Hoàn thành trễ"**.
     - Đồng bộ toàn diện: Cả bảng dữ liệu chính (`renderMainTable`), bộ lọc, thống kê điểm KPI (`updateKPIStats`), tiến độ công việc mẹ (`getMainTaskProgress`) và modal quản lý dự án (`renderProjectManageList`) đều dùng chung hàm `getTaskEffectiveStatus(task)` và `isTaskCompleted(task)`.

---

### Phiên Bản 4.6.0 (13/10/2026) - Quản Lý Dự Án CRUD, Click Thẻ KPI & Click Nguồn Yêu Cầu Lọc:

1. **Quản Lý Dự Án Toàn Diện (`projectManageModal` & Header Button):**
   - **Nút "Quản Lý Dự Án" trên Header:** Bổ sung nút truy cập nhanh với icon `fa-diagram-project` màu xanh dương nổi bật.
   - **Form Thêm Dự Án Mới:** Cho phép nhập mã dự án (hỗ trợ nút "Tự sinh" tự động đề xuất mã tiếp theo như `CV-2026-xxxx`), nhập tên dự án và thêm trực tiếp vào hệ thống.
   - **Bảng Danh Sách Dự Án Hệ Thống:**
     - Hiển thị toàn bộ các dự án kèm mã badge, tên dự án, số lượng công việc con và thanh tiến độ hoàn thành (% và số việc đã hoàn tất).
     - Ô tìm kiếm nhanh dự án theo mã hoặc tên theo thời gian thực.
     - **Nút ✏️ Sửa Tên Dự Án (`handleEditProjectTitle`):** Cho phép đổi tên dự án và tự động cập nhật đồng bộ cho toàn bộ công việc con thuộc dự án đó.
     - **Nút 🗑️ Xóa Dự Án (`handleDeleteProject`):** Cơ chế xóa an toàn. Nếu dự án có công việc con, hệ thống cung cấp lựa chọn giữ lại các công việc (chuyển thành việc riêng lẻ độc lập) trước khi xóa dự án; nếu dự án không có việc con thì xóa ngay.
   - Tự động đồng bộ và nạp `appData.projects`, lưu `saveDataToStorage()`, cập nhật dropdown `#filterMainTask` và danh sách chọn dự án mẹ trong modal thêm việc.

2. **Click Thẻ KPI Để Lọc Nhanh Công Việc (`filterByKpiStatus` & `highlightActiveKpiCard`):**
   - Các thẻ thống kê KPI ở hàng trên cùng đã trở thành các nút bấm tương tác (hiệu ứng hover nổi, scale nhẹ):
     - **Tổng công việc:** Click để xem tất cả công việc (`filterStatus = 'ALL'`).
     - **Đang thực hiện:** Click để lọc công việc đang làm (`filterStatus = 'DANG_LAM'`).
     - **Đúng hạn (+3đ):** Click để lọc công việc hoàn thành đúng hạn (`filterStatus = 'Hoàn thành'`).
     - **Hoàn thành trễ:** Click để lọc công việc hoàn thành trễ (`filterStatus = 'Hoàn thành trễ'`).
     - **Tồn đọng quá hạn:** Click để lọc công việc quá hạn chưa xong (`filterStatus = 'QUA_HAN'`).
   - **Cơ chế Toggle:** Click vào thẻ đang lọc một lần nữa sẽ tự động đưa bộ lọc về trạng thái mặc định (*Chưa hoàn thành*).
   - **Hiệu ứng Active Card:** Thẻ KPI đang được lọc sẽ có viền sáng xanh (`ring-2 ring-brand-500 bg-sky-50/50 shadow-md`) giúp người dùng nắm bắt ngay trạng thái hiển thị.

3. **Click Huy Hiệu Nguồn Yêu Cầu (Trưởng Phòng / Giám Đốc / TGĐ) & Dự Án Để Lọc Tức Thì:**
   - **Nguồn yêu cầu (`getSourceBadge`):** Chuyển toàn bộ các huy hiệu nguồn yêu cầu (Trưởng phòng, Giám đốc, Tổng Giám đốc, Đối ứng, Cải tiến, Chiến lược) thành các nút bấm tương tác.
   - **Hàm `filterByPriority(priorityVal)`:** Khi click vào badge "Trưởng phòng" trên bất kỳ dòng công việc nào, hệ thống sẽ tự động gán bộ lọc nguồn yêu cầu về "Trưởng phòng", cập nhật dropdown và lọc bảng tức thì. Click lại lần 2 để hủy lọc (quay về `ALL`).
   - **Badge Dự án (`mainBadge`) & Tên Dự Án:** Giữ nguyên và tăng cường tính năng click lọc theo mã/tên dự án kèm tính năng tự động thu phóng timeline biểu đồ Gantt vừa vặn theo tiến độ dự án.

---

1. **Tái thiết kế `getAvailableParentTasks(currentTaskId)` (`app.js`):**
   - Trước đây `getUniqueMainTasks()` chỉ lấy danh sách các `mainTaskId` nên task `CV-2026-0028` (đang là con của `CV-8174`) không xuất hiện trong danh sách chọn dự án mẹ.
   - Nay hàm mới trả về **toàn bộ**: (1) các dự án mẹ hiện có (gom từ `mainTaskId`) + (2) **tất cả công việc khác trong hệ thống** (kể cả việc riêng lẻ), loại trừ duy nhất chính công việc đang sửa.
   - Mỗi mục hiển thị badge loại (`Dự án` / `Công việc`), mã CV, tên, số lượng việc/người phụ trách.
   - **Tìm kiếm real-time** qua `searchStr` bao gồm: id, title, detail, empName, mainTaskTitle → gõ "SMI", "hộp mẫu", "Tới", "FVDM" là ra ngay.

2. **3 Nút Hành Động Nhanh trong taskModal:**
   - **🍃 Việc riêng lẻ** (`setStandaloneProject()`): `mainTaskId = ''`, không thuộc dự án nào.
   - **⭐ Tự làm Dự án** (`setSelfAsProject()`): `mainTaskId = task.id`, tự trở thành dự án gốc độc lập.
   - **✨ + Tạo mới** (`selectParentTask('__NEW__')`): hiện ô nhập mã và tên dự án mẹ mới.

3. **Selected Card (`parentSelectedCard`):** Hiển thị trực quan trạng thái liên kết hiện tại (riêng lẻ / tự làm dự án / thuộc dự án X). Nút "Đổi dự án" toggle danh sách tìm kiếm.

4. **`handleSaveTask()` hỗ trợ đầy đủ 4 chế độ:**
   - `__STANDALONE__`: `mainTaskId = ''`.
   - `__SELF__`: `mainTaskId = task.id` (promote thành dự án gốc).
   - `__NEW__`: `mainTaskId` và `mainTaskTitle` lấy từ ô nhập mới.
   - **ID cụ thể (vd. `CV-2026-0028`):** Tự động promote công việc mẹ thành dự án gốc độc lập nếu trước đó nó đang bị gán dưới dự án khác (chống circular hierarchy).

5. **Root Cause Issue 2 đã fix:** `CV-2026-0028` không xuất hiện vì bị gán `mainTaskId: CV-8174`. Nay chọn `CV-2026-0028` làm mẹ cho `CV-2026-0053` → `CV-2026-0028` tự động được promote thành gốc, `CV-2026-0053` liên kết đúng.

---

### Phiên Bản 4.4.0 (13/10/2026) - Khắc Phục Lệch Cột, Lọc Dự Án Mẹ, Xuất Nhập Toàn Bộ Note Excel & Nhãn Mũi Tên Gantt:
1. **Khắc Phục Lỗi Lệch Cột Trên Bảng Gantt Chính (Hình 1):**
   - **Root cause:** Trong hàm `renderMainTable()` của `app.js`, `tr1.innerHTML` trước đó thiếu thẻ `tdPlanEndDate` ("Dự tính xong"), khiến tất cả các cột phía sau (`Thời gian hoàn thành`, `Hiện Trạng`, `Tình trạng`, `Ghi chú`, `Link / Tệp`, `Phân loại`) bị dịch chuyển lệch sang trái 1 cột so với header `thead`.
   - **Giải pháp:** Bổ sung `tdPlanEndDate` (`formatVnDate(task.planEndDate) || '—'`) ngay sau `tdPlanDays` trong `tr1.innerHTML`.
   - Khớp chuẩn 100% đúng **14 cột cố định** của bảng.
2. **Bộ Chọn & Lọc Nhanh Dự Án Mẹ Trong Task Modal (Hình 2):**
   - Cải tiến phần chọn `Nhóm Công Việc Chính (Dự án mẹ)` trong `taskModal` (`index.html` & `app.js`).
   - Bổ sung ô tìm kiếm nhanh `taskParentSearchInput`: Lọc tức thì theo mã dự án (`CV-...`) hoặc tên dự án theo thời gian thực (real-time).
   - Container cuộn tùy biến (`max-h-44 overflow-y-auto`) hiển thị thẻ từng dự án mẹ với mã badge, tên và số lượng hạng mục việc con.
   - Nút `+ Tạo Công Việc Chính Mới` luôn ghim đầu danh sách với màu xanh nổi bật, tự động sinh mã CV mới theo năm hiện tại khi chọn.
3. **Xuất/Nhập Toàn Bộ Lịch Sử Note Excel & Nút Gia Hạn 3 Ngày Không Lưu Note Rác (Hình 3):**
   - **Xuất Excel động (`exportCurrentTasksToExcel`):**
     - Quét toàn bộ công việc để tìm số lượng ghi chú nhiều nhất `maxNotes`.
     - Tự động sinh số cột động: `Nhật Ký 1 [Ngày - Tiến Độ - Nội Dung]`, `Nhật Ký 2`, ..., `Nhật Ký N`.
     - Xuất đầy đủ lịch sử theo thứ tự thời gian.
   - **Nhập Excel thông minh (`processSmartImport`):**
     - Tự động nhận diện các cột `Nhật ký`, `Lịch sử cập nhật`, `Hiện trạng ghi chú`.
     - Bóc tách ngày, % tiến độ, nội dung ghi chú và nạp đầy đủ vào mảng `task.statusLogs`.
     - Hỗ trợ cập nhật/ghép note bổ sung vào các công việc đã tồn tại trong hệ thống.
   - **Nút "Không có cập nhật mới (+3 ngày)":**
     - Tích hợp nút hành động trực tiếp vào chân modal cập nhật tình trạng (`statusLogModal`).
     - Khi bấm: Tự động cập nhật `task.lastStatusUpdate = hôm nay`, reset bộ đếm cảnh báo quá hạn cập nhật thêm 3 ngày mà **hoàn toàn không ghi thêm dòng note rác** vào `task.statusLogs`.
4. **Hiển Thị Ngày Bắt Đầu & Kết Thúc Trên Mũi Tên Biểu Đồ Gantt (Hình 4):**
   - Bỏ giới hạn chỉ bật ở chế độ Tháng: Giờ đây áp dụng đồng bộ cho **tất cả các chế độ xem (Ngày, Tuần, Tháng)**.
   - **Tại gốc mũi tên (`isStart`):** Luôn hiển thị nhãn ngày bắt đầu (`formatVnDate(task.startDate).slice(0, 5)`).
   - **Tại chóp mũi tên (`isEnd`):** 
     - Dòng Kế hoạch: Hiển thị ngày kết thúc kế hoạch (`planEndDate`).
     - Dòng Thực tích: Hiển thị ngày hoàn thành thực tế (`actualEndDate`) nếu đã xong, hoặc ngày hiện tại / hôm nay nếu đang làm / tạm dừng.
   - **Trường hợp thanh ngắn (1 ô vừa là gốc vừa là chóp):** Tự động hiển thị dạng kết hợp rút gọn `d/m → d/m` gọn gàng trong thân mũi tên.
   - Định dạng CSS `.arrow-date-tag`: Nền đen bóng mờ tương phản cao (`rgba(15, 23, 42, 0.7)`), chữ trắng đậm nét, đổ bóng tinh tế.
5. **Bảo Toàn Cơ Sở Dữ Liệu:** Giữ nguyên 100% file gốc `database.js`.
6. **Verify Gate 2 (Đạt chuẩn 100%):** Script kiểm tra tự động xác nhận toàn bộ 14 cột, các hàm modal, logic lọc, nút gia hạn, dynamic note export/import và date tag trên timeline.

### Phiên Bản 4.3.0 (09/10/2026) - Đánh Số Tuần Theo Từng Tháng & Quy Tắc Giao Thời:
1. **Đánh Số Tuần Nhóm Theo Từng Tháng (`Tuần X (TM)`):**
   - Thay vì đánh số tuần liên tục từ 1 đến 14 gây mất dấu chu kỳ tháng, hệ thống giờ đây **đánh số tuần theo từng tháng riêng biệt**.
   - **Quy tắc phân loại tháng của tuần:** Dựa theo **ngày bắt đầu của tuần (`wStart`)**:
     - Tuần bắt đầu trong tháng 9 (`wStart` ở tháng 9, ví dụ `Tuần 5: 29/09 - 05/10/26`) có ngày kết thúc lấn sang tháng 10 thì **vẫn được tính thuộc về Tháng 9**, mang nhãn `Tuần 5 (T9)`.
     - Tuần tiếp theo có ngày bắt đầu `06/10` (thuộc tháng 10) ➔ Hệ thống tự động **reset lại số tuần về 1**, mang nhãn `Tuần 1 (T10)`.
     - Tương tự khi chuyển sang tháng 11: `Tuần 4 (T10): 27/10 - 2/11/26` ➔ `Tuần 1 (T11): 3/11 - 9/11/26`.
2. **Đồng Bộ Lên Giao Diện & File Excel:**
   - Header bảng Gantt HTML: Hiển thị rõ nét `Tuần X (TM)` ở dòng trên và dải ngày `d/m - d/m/yy` ở dòng dưới.
   - Hàm `executeExportExcelReport`: Truyền `tasksToExport` vào `getTimelineColumns`, đồng bộ hoàn toàn nhãn tuần theo tháng khi xuất Gantt ra Excel.
3. **Verify Gate 2 (Pass 100%):** Script kiểm tra 14 tuần liên tiếp xác nhận đúng toàn bộ các mốc tuần `Tuần 5 (T9)`, `Tuần 1 (T10)`, `Tuần 4 (T10)`, `Tuần 1 (T11)`.

### Phiên Bản 4.2.0 (09/10/2026) - Tự Động Mở Rộng Gốc Timeline Gantt Cho Công Việc Quá Hạn & Tồn Đọng:
1. **Khắc Phục Lỗi Biểu Đồ Không Hiện Gốc Thời Gian Cho Việc Tồn Đọng / Quá Hạn Từ Tháng Trước (Hình ảnh người dùng):**
   - **Root cause cũ:** Khi xem theo tháng (ví dụ Tháng 10/2026), lưới timeline mặc định gán cứng `baseDate = 2026-10-01`. Do đó, công việc bắt đầu từ tháng 9 (như `CV-2026-0028` bắt đầu `20/09/2026`, hạn kế hoạch `27/09/2026`, chưa xong) bị rớt toàn bộ thanh Kế hoạch ra ngoài mép trái của biểu đồ (hàng Kế hoạch trống trơn), còn thanh Thực tích thì bắt đầu lơ lửng từ 01/10.
   - **Cơ chế mới (`getTimelineColumns(taskList)`):**
     - Quét toàn bộ danh sách công việc hiển thị (`taskList`) để tìm ngày bắt đầu sớm nhất `minTaskStart`.
     - Nếu có công việc bắt đầu từ tháng trước (`minTaskStart < defaultBase`): Tự động **mở rộng mốc bắt đầu của lưới timeline về gốc tháng của công việc đó** (ngày đầu tháng của `minTaskStart`, ví dụ `2026-09-01`).
     - Mở rộng số lượng tuần (14 tuần) và số ngày (trong chế độ xem cả tháng) để bao trọn từ tháng bắt đầu sớm nhất xuyên suốt qua tháng hiện tại và các tuần tiếp theo.
     - **Kết quả:**
       - Thanh **Kế hoạch** của công việc quá hạn tháng 9 hiển thị đầy đủ, sắc nét trên các tuần tháng 9 (Tuần 3 & 4).
       - Thanh **Thực tích** dải màu xanh/cyan kéo dài liên tục từ ngày bắt đầu 20/09 qua tháng 10 tới ngày hôm nay, thể hiện trung thực việc trễ hạn.
2. **Chuẩn Hóa Logic Lọc Tháng Cho Công Việc Chưa Xong (`renderMainTable`):**
   - Định lý giao nhau thời gian: Với công việc chưa hoàn thành (`!task.actualEndDate`), ngày hiệu lực kết thúc được tính là hôm nay (`systemToday`). Do đó công việc bắt đầu tháng 9 nhưng chưa xong luôn xuất hiện hợp lệ trong bảng theo dõi Tháng 10 ở cả 2 chế độ Ngày và Tuần (không bị lọc mất nhầm).
3. **Đồng Bộ Số Cột Cố Định Header:**
   - Sửa vòng lặp dọn header thành `while (headerRow.children.length > 13)` và điều chỉnh phân cách nhóm nhân sự thành `colspan="${13 + timelineCols.length}"` khớp chính xác 13 cột cố định của bảng.
4. **Bảo toàn CSDL:** Tuyệt đối giữ nguyên 100% dữ liệu trong `database.js`.
5. **Verify Gate 2 (Đạt chuẩn 9/9):** Đã chạy script mô phỏng kiểm tra, xác nhận task tháng 9 chưa xong qua bộ lọc tháng 10, timeline lùi về `01/09/2026`, thanh kế hoạch hiển thị 2 tuần tháng 9, thanh thực tích trải dài 4 tuần từ tháng 9 sang tháng 10.

### Phiên Bản 4.1.0 (09/10/2026) - Hiện Trạng Mới Nhất Trên Bảng Gantt & Đồng Bộ Xuất Excel Công Việc:
1. **Bổ Sung Cột "Hiện Trạng" Trực Tiếp Trên Bảng Gantt Chính:**
   - Vị trí: Đứng ngay **trước cột "Tình trạng"** (sau cột "Thời gian hoàn thành").
   - Header bảng Gantt: `<th class="min-w-[130px] max-w-[180px]">Hiện Trạng</th>` trong `index.html`.
   - Nội dung cell (`tdCurrentStatus`): Lấy **nội dung ghi chú của lần cập nhật mới nhất** (`latestLog.note`) kèm badge tiến độ `(X%)` và ngày cập nhật (`formatVnDate(latestLog.date)`).
   - Nếu chưa có lượt cập nhật nào: Hiển thị placeholder dấu gạch ngang mờ `—` (`text-slate-300`).
   - Có tooltip đầy đủ khi rê chuột qua ô: Ngày cập nhật + Tiến độ + Nội dung ghi chú.
   - Thẻ `td` có thuộc tính `rowspan="2"` khớp với cấu trúc 2 dòng (Kế hoạch / Thực tế) của bảng Gantt.
2. **Đồng Bộ Dữ Liệu Cập Nhật Mới Nhất Khi Xuất Excel Danh Sách Công Việc (`exportCurrentTasksToExcel`):**
   - Giải quyết bài toán: Người dùng muốn xem tình trạng cập nhật ngay trong file danh sách công việc mà không bị trùng lặp nhiều dòng như file xuất lịch sử log riêng.
   - Bổ sung 3 cột vào file Excel `DanhSachCongViec`:
     - `Hiện Trạng (Ghi Chú Cập Nhật Mới Nhất)` (độ rộng cột 40).
     - `Ngày Cập Nhật Cuối` (độ rộng cột 22).
     - `Tiến Độ (%)` (độ rộng cột 14).
   - Dữ liệu được trích xuất tự động từ entry mới nhất trong mảng `task.statusLogs`, đảm bảo 1 dòng = 1 công việc duy nhất, trực quan và tiện đối soát.
3. **Verify Gate 2 (Đạt chuẩn):**
   - Đã kiểm tra cú pháp và độ tương thích cấu trúc cột giữa `index.html` (13 cột cố định) và `app.js` (`tr1.innerHTML` chứa đúng 13 thẻ `td` theo đúng thứ tự).
   - Thử nghiệm logic trích xuất log mới nhất và xuất Excel hoạt động trơn tru.

### Phiên Bản 4.0.0 (09/10/2026) - Xuất Nhật Ký Cập Nhật Tình Trạng Ra Excel:
1. **Hàm `exportStatusLogsToExcel()` — Xuất Nhật Ký Cập Nhật Tình Trạng:**
   - Mỗi lượt cập nhật tình trạng (`statusLogs` entry) = **1 dòng riêng** trong file Excel (không gộp ô).
   - Cột xuất: `STT` | `Mã CV` | `Tên Công Việc` | `Nội Dung Chi Tiết` | `Người Thực Hiện` | `Trạng Thái CV Hiện Tại` | `Ngày Cập Nhật` | `Tình Trạng Báo Cáo` | `Tiến Độ (%)` | `Nội Dung Ghi Chú` | `Người Cập Nhật` | `Nguồn Yêu Cầu` | `Hạn Kế Hoạch` | `Cập Nhật Cuối`.
   - Sắp xếp: Mã CV → Ngày cập nhật tăng dần.
   - Task chưa có log nào vẫn xuất 1 dòng placeholder `(Chưa có nhật ký cập nhật)` màu xám để dễ phát hiện.
   - Màu sắc phân biệt trạng thái: Hoàn thành (xanh lá) | Hoàn thành trễ (cam) | Đang làm (xanh dương) | Tạm dừng (xám) | Dừng dự án (đỏ).
   - Header file màu tím Indigo phân biệt với file xuất Công Việc (xanh) và Nhân Sự (xanh dương).
   - Tên file: `NhatKy_CapNhat_TinhTrang_MBC_YYYYMMDD.xls`.
2. **Nút "Xuất Nhật Ký" — 2 vị trí:**
   - **importModal (Tab Công Việc):** Khối tím `#statusLogExportBox` — hiển thị khi ở tab CV, tự ẩn khi chuyển sang tab Nhân Sự (tích hợp vào `switchSmartImportTarget()`).
   - **syncModal (Khu vực xuất Excel bảng phẳng):** Nút tím trải dài `col-span-2` bên dưới 2 nút Xuất CV / Xuất NV.
3. **Fix bug:** Xóa đoạn code orphan bị duplicate trong `switchSmartImportTarget` (if/else block thừa ngoài hàm do lỗi tool replace trước đó).
4. **Verify Gate 2 (Pass 9/9 + 3 logic tests):** Hàm tồn tại, 2 nút HTML tồn tại, không còn orphan code, logic sort log và placeholder hoạt động đúng.

### Phiên Bản 3.9.0 (09/10/2026) - Người Phối Hợp / Người Phụ, Phân Cấp Tổng Giám Đốc & Bộ Lọc Nguồn Yêu Cầu:
1. **Hỗ Trợ Người Phối Hợp / Người Phụ Trên Mỗi Công Việc:**
   - Mỗi task giờ có thể có **1 người chính** (`empId`/`empName`) và **nhiều người phụ** (`supportEmpIds`, `supportEmpNames`).
   - Form thêm/sửa công việc (`taskModal`): Đổi nhãn thành **Người Thực Hiện Chính**, bổ sung container `#supportEmpContainer` hiển thị danh sách checkbox nhân viên còn lại để chọn làm người phối hợp.
   - Khi đổi người chính, hệ thống tự động cập nhật lại danh sách checkbox (loại trừ người đang chọn chính).
   - **Bảng Gantt:** Cột nhân sự hiển thị icon ⭐ tên người chính + badge nhỏ `PH: [Tên người phụ]` nếu có.
   - **Bộ lọc nhân viên:** Khi lọc 1 nhân viên, hiển thị cả công việc họ làm chính lẫn công việc họ phối hợp hỗ trợ.
   - **Tìm kiếm từ khóa:** Nhận diện tên người phối hợp trong kết quả tìm kiếm.
   - **Excel Xuất:** Thêm cột `Người phối hợp` (cột thứ 7 trong file `.xlsx`).
   - **Excel Nhập (Smart Import):** Nhận diện cột `Người phối hợp` / `Người phụ` / `Hỗ trợ`, tự động tách theo dấu phẩy/chấm phẩy, map ID nhân sự trong hệ thống, lưu vào task.
   - Hàm mới: `renderSupportEmpCheckboxes(selectedIds)`, `_onSupportEmpCheckboxChange(cb)`, `_updateSupportEmpOptions()`.
2. **Bổ Sung Cấp Tổng Giám Đốc (TGĐ):**
   - Huy hiệu `👑 TGĐ` màu đỏ đậm viền vàng (`bg-rose-900 text-amber-300 border-amber-400`) — phân biệt hẳn với Giám đốc (tím).
   - `getSourceBadge()`: Kiểm tra `Tổng Giám đốc` / `TGĐ` / `TGD` TRƯỚC khi kiểm tra `Giám đốc` để tránh match nhầm chuỗi con.
   - `getPriorityWeight()`: Tổng Giám đốc được trọng số cao nhất `0` (ưu tiên sắp xếp đầu tiên).
   - Form thêm/sửa công việc: Thêm option `👑 Yêu cầu từ: Tổng Giám đốc` vào select `taskSource`.
3. **Cập Nhật Bộ Lọc Toolbar - Nguồn Yêu Cầu:**
   - Đổi nhãn bộ lọc từ `Ưu tiên:` thành `📌 Nguồn yêu cầu:` (phản ánh đúng chức năng lọc theo cấp giao việc).
   - Thêm option `👑 Tổng Giám đốc` (ở đầu danh sách, trước Giám đốc).
   - Logic `applyFilters()`: Phân biệt rõ `Tổng Giám đốc` vs `Giám đốc` thuần túy — khi lọc `Giám đốc` sẽ loại trừ các task thuộc `Tổng Giám đốc`.
4. **Bảo toàn CSDL:** Tuyệt đối không chỉnh sửa `database.js` theo yêu cầu người dùng.
5. **Verify Gate 2 (Pass 17/17):** Tất cả hàm mới tồn tại trong `app.js`, tất cả element mới tồn tại trong `index.html`, parseDurationString test pass 5/5 case.

### Phiên Bản 3.8.0 (09/10/2026) - Tính Toán 2 Chiều Thời Gian Kế Hoạch, Đơn Vị Linh Hoạt & Cột Nguồn Yêu Cầu Excel:
1. **Tính toán 2 chiều trên Form Thêm/Sửa Công Việc (taskModal):**
   - **Chiều xuôi:** Nhập `Ngày bắt đầu` + `Thời gian dự kiến` (giờ / ngày / tuần / tháng) ➔ Tự động tính ra `Ngày kế hoạch xong`.
   - **Chiều ngược:** Mở khóa ô `Ngày kế hoạch xong` (bỏ readonly). Khi người dùng chọn/đổi `Ngày kế hoạch xong` ➔ Hệ thống tự động tính ngược ra `Thời gian dự kiến` (số ngày/tuần/tháng tương ứng) qua hàm `calculatePlanDurationFromEndDate()`.
2. **Cột "Nguồn Yêu Cầu" & Đơn Vị Thời Gian Linh Hoạt Trên File Excel:**
   - **Xuất Excel Hiện Tại (`exportCurrentTasksToExcel`):**
     - Bổ sung cột **"Nguồn yêu cầu"** (Giám đốc, Trưởng phòng, Đối ứng sự cố, Cải thiện nội bộ...) để đối soát rõ ràng người giao việc.
     - Cột **"Thời gian dự kiến"** xuất định dạng linh hoạt (`4 giờ`, `5 ngày`, `2 tuần`, `1 tháng`...) thay vì chỉ là con số trơn.
     - Bổ sung cột **"Ngày kế hoạch xong (YYYY-MM-DD)"** để phân biệt rõ ràng với ngày hoàn thành thực tế.
   - **File Mẫu Import Excel (`downloadExcelTemplate`):**
     - Đồng bộ các cột: `Nguồn yêu cầu`, `Thời gian dự kiến` (mẫu `1 ngày`, `3 ngày`, `2 tuần`), `Ngày kế hoạch xong (YYYY-MM-DD)`.
   - **Nhập Excel Thông Minh (`processSmartImport`):**
     - Hàm mới `parseDurationString(val)`: Tự động bóc tách số và đơn vị từ chuỗi (`"4 giờ"`, `"2 tuần"`, `"1 tháng"`, `"5 ngày"`, hoặc số thuần `5`).
     - Tự động nhận diện cột `Nguồn yêu cầu` / `Người giao việc`.
     - **Tự động tính 2 chiều khi Import:** Nếu file có thời gian dự kiến ➔ tự tính ngày kế hoạch xong; nếu file chỉ có ngày yêu cầu hoàn thành mà để trống thời gian dự kiến ➔ tự động tính ngược ra số ngày dự kiến.
3. **Bảo toàn CSDL:** Giữ nguyên 100% dữ liệu gốc trong `database.js`.

### Phiên Bản 3.7.1 (08/10/2026) - Xóa Nhanh Công Việc Trên Bảng Gantt & Khắc Phục Cảnh Báo Quá Hạn Cập Nhật:
1. **Xóa nhanh Công Việc trực tiếp trên Bảng Gantt chính:**
   - Bổ sung cột **Checkbox** đầu tiên vào bảng Gantt (cố định `sticky-col-left` ở mép trái, vị trí `left: 0`).
   - Checkbox header **"Chọn tất cả"** hỗ trợ chọn/bỏ chọn toàn bộ công việc đang hiển thị kèm trạng thái `indeterminate`.
   - Nút **"🗑️ Xóa đã chọn (N)"** xuất hiện động trên thanh toolbar chính (cạnh số lượng công việc) kèm hiệu ứng chú ý `animate-pulse` khi có công việc được tick.
   - Hộp thoại xác nhận xóa hiển thị chi tiết tên/mã các công việc đã chọn trước khi thực hiện.
   - Hàm mới: `_onGanttTaskCheckboxChange`, `toggleSelectAllGanttTasks`, `_updateGanttBulkDeleteUI`, `bulkDeleteGanttSelectedTasks`.
2. **Khắc phục triệt để lỗi "Công việc chưa có cập nhật gì nhưng không báo lên dù đã quá ngày" (Hình 1):**
   - **Root cause cũ:** Code trước đây dùng fallback `task.lastStatusUpdate || task.startDate`, khiến công việc chưa từng cập nhật bị gán ngày cập nhật là `startDate`. Nếu `startDate` gần ngày hiện tại thì điều kiện `daysSinceUpdate >= 3` không đạt, làm hệ thống im lặng dù công việc đã quá hạn kết thúc kế hoạch (`planEndDate < today`).
   - **Cơ chế mới:** Phân nhánh rõ ràng:
     - Nếu **chưa cập nhật lần nào** (`!task.lastStatusUpdate`): Hệ thống kiểm tra nếu đã qua ngày kết thúc kế hoạch (`planEndDate < today`), lập tức bật cảnh báo đỏ `Cần Cập Nhật (Quá hạn N ngày)` nhấp nháy, hoặc nếu đã qua ngày bắt đầu >= 3 ngày cũng tự động cảnh báo. Cột "CN cuối" hiển thị rõ `Chưa cập nhật` màu đỏ thay vì nhầm tưởng đã cập nhật vào ngày bắt đầu.
     - Nếu **đã từng cập nhật**: Kiểm tra quá 3 ngày chưa cập nhật tiếp, hoặc nếu công việc đã quá hạn kế hoạch mà lần cập nhật cuối diễn ra từ trước ngày kết thúc kế hoạch thì cũng bật cảnh báo yêu cầu cập nhật lại.
3. **Bảo toàn dữ liệu CSDL:** Giữ nguyên 100% dữ liệu gốc trong `database.js` theo đúng yêu cầu người dùng.

### Phiên Bản 3.7.0 (08/10/2026) - Xóa Nhanh Nhân Viên & Công Việc Hàng Loạt (Bulk Delete):
1. **Xóa nhanh Nhân Viên trong modal Quản Lý Nhân Sự:**
   - Thêm cột **checkbox** vào bảng danh sách nhân viên (cột đầu tiên).
   - Checkbox header **"Chọn tất cả"** kèm trạng thái nửa chọn (indeterminate) khi chất chọn một phần.
   - Nút **"🗑️ Xóa đã chọn (N)"** xuất hiện động khi có ít nhất 1 nhân viên được đánh dấu.
   - Xác nhận xóa hiện danh sách tên nhân viên rõ ràng và cảnh báo công việc KHÔNG bị xóa theo.
   - Hàm mới: `_onEmpCheckboxChange`, `_updateEmpBulkDeleteBtn`, `toggleSelectAllEmployees`, `bulkDeleteEmployees`.
2. **Xóa nhanh Công Việc qua modal riêng (Bulk Delete Task Modal):**
   - Thêm nút **"🗑️ Xóa Nhanh CV"** (màu đỏ Rose) trên thanh toolbar chính ngậy cạnh nút Cập Nhật Tiến Độ.
   - Modal `bulkDeleteTaskModal` liệt kê **toàn bộ** công việc trong hệ thống, hiển thị: Tên CV, Nhân viên, Ngày bắt đầu, Kết thúc KH, Tiến độ (%), Trạng thái (màu sắc theo loại).
   - Hỗ trợ **tìm kiếm thời gian thực** theo tên CV, tên/mã nhân viên, trạng thái.
   - Checkbox **"Chọn tất cả"** kèm badge "Đã chọn: N" cập nhật động.
   - Nút **"Xóa đã chọn (N)"** dưới footer, hiển thị số lượng, yêu cầu xác nhận trước khi xóa.
   - Hàm mới: `openBulkDeleteTaskModal`, `closeBulkDeleteTaskModal`, `renderBulkTaskTable`, `filterBulkTaskList`, `toggleSelectAllBulkTasks`, `updateBulkTaskSelectionUI`, `executeBulkDeleteTasks`.
3. **Nâng phiên bản:** DB_VERSION 3.6 → 3.7 trong `app.js` và `database.js`.

### Phiên Bản 3.6.0 (08/10/2026) - Tùy Chọn Ngày Cập Nhật Tiến Độ, Cột Link Từng Việc & Xuất Công Việc Hiện Tại:
1. **Tùy chọn Ngày cập nhật trong Modal Tiến độ (Hình 1):**
   - Bổ sung ô chọn ngày `<input type="date" id="statusLogDate">` ngay trong modal ghi nhận nhật ký / cập nhật tình trạng.
   - Mặc định tự động điền **Ngày hôm nay (`today`)**, người dùng có thể linh hoạt chọn ngày thực tế đã thực hiện công việc (ví dụ: hôm qua, tuần trước).
   - Nhật ký tiến độ và mốc thời gian cập nhật `lastStatusUpdate` lưu chuẩn theo ngày được chọn, biểu tượng ghi chú `📝` trên thanh Gantt và biểu đồ xuất hiện chuẩn xác tại đúng ngày đó.
2. **Cột Link / Tệp tài liệu tương ứng cho từng công việc (Yêu cầu 2):**
   - **Bảng Gantt chính:** Bổ sung cột cố định **"Link / Tệp"** (vị trí giữa Ghi chú và Phân loại).
   - **Tương tác nhanh:** Khi đã có link, hiển thị nút xanh `[↗ Mở]` kèm nút icon bút chì để sửa; khi chưa có link, hiển thị nút viền nét đứt `[+ Link]` giúp thao tác 1 chạm.
   - **Modal sửa link riêng biệt (`taskLinkModal`):** Cho phép sửa hoặc dán nhanh link tài liệu/folder bất kỳ lúc nào mà không cần mở form Admin CRUD phức tạp.
   - **Hỗ trợ đa định dạng đường dẫn:** Nhận diện và mở trực tiếp link web (`https://`, Google Drive...), giao thức `file:///` hoặc đường dẫn thư mục máy tính Windows (`C:\...`, mạng nội bộ UNC `\\server\share`).
   - **Form CRUD công việc:** Tích hợp trường nhập `taskLink` trong modal thêm/sửa công việc của Admin.
   - **Xuất báo cáo:** Cột Link / Tệp được đồng bộ hiển thị trên cả file Excel Gantt (`.xls`) và bảng dữ liệu phẳng (`.xlsx`).
3. **Xuất Danh Sách Công Việc Hiện Tại ra Excel (.xlsx) (Hình 2):**
   - Trong modal *Nhập Công Việc Vào Hệ Thống*, bổ sung khối màu Emerald **"📥 Xuất CV Hiện Tại (.xlsx)"** song song với khối Tải File Mẫu.
   - Tự động xuất toàn bộ `appData.tasks` ra file Excel định dạng chuẩn mẫu import (Mã CV, Mã CV Chính, Tên CV chính, Nội dung chi tiết, Người thực hiện, Mã NV, Ngày bắt đầu, Thời gian dự kiến, Ngày hoàn thành, Tình trạng, Link / Tệp, Ghi chú).
   - File xuất ra có thể dùng trực tiếp để chỉnh sửa hàng loạt và nạp lại qua Smart Merge (hệ thống tự động nhận diện `Mã CV` và nội dung để bảo toàn dữ liệu, không trùng lặp).
   - Tự động chuyển đổi hiển thị khối Xuất CV khi ở tab "Công việc" và khối Xuất NV khi ở tab "Nhân sự".

### Phiên Bản 3.5.0 (08/10/2026) - Khắc Phục Mũi Tên Tiến Độ, Note Icon Gantt & Excel, Tách Khối Xuất Nhân Sự Hiện Tại:
1. **Khắc phục triệt để lỗi mất mũi tên tình trạng (Hình 1):**
   - **Root cause:** Modal cập nhật tình trạng trước đây lưu `<option value="Dang lam">` (không dấu), làm lệch so sánh chuỗi `task.status === 'Đang làm'` khiến thanh thực tích không được kéo dài và bị ẩn hoàn toàn.
   - **Giải pháp:** Chuẩn hóa toàn bộ danh sách trạng thái trong `statusLogModal` sang tiếng Việt có dấu chuẩn (`Đang làm`, `Tạm dừng`, `Hoàn thành`, `Hoàn thành trễ`). Đồng thời thêm hàm `normalizeTaskStatuses()` tự động chuẩn hóa dữ liệu cũ đã lưu trong `localStorage`.
   - **Căn mốc ngày động:** Cho phép `tActualEnd` tự động nhận ngày cập nhật cuối `task.lastStatusUpdate` hoặc ngày hiện tại (thay vì cố định ở 07/10), giúp mũi tên cyan pulse của công việc đang làm vươn chuẩn xác đến đúng ngày cập nhật.
2. **Biểu tượng ghi chú 📝 gắn trực tiếp trên thân mũi tên Gantt & Xuất ra Excel (Yêu cầu 2):**
   - **Trên Web:** Ở những ngày có cập nhật tiến độ, biểu tượng ghi chú `📝` (kèm `%` tiến độ) được gắn **trực tiếp ngay giữa thân thanh mũi tên** trên biểu đồ Gantt. Rê chuột hiển thị popover/tooltip đầy đủ (Ngày, % tiến độ, nội dung ghi chú, người cập nhật). Click vào biểu tượng mở ngay modal lịch sử tiến độ.
   - **Trên Excel Gantt (`.xls`):** Ô ngày có cập nhật hiển thị biểu tượng `📝 [XX%]` với màu sắc nhận diện đặc trưng và chú thích `title`. Cột Kế hoạch / Đang làm / Hoàn thành hiển thị đồng bộ màu cyan `#0284c7` và ký hiệu `►`.
   - **Trên Excel Bảng phẳng (`.xlsx`):** Thêm cột riêng **"Lịch Sử Cập Nhật & Tiến Độ"** liệt kê chi tiết toàn bộ các mốc nhật ký của từng công việc.
3. **Tách riêng khối Xuất Danh Sách Nhân Sự Hiện Tại (Hình 2):**
   - Trong modal *Nhập Nhân Sự Vào Hệ Thống*, khu vực thao tác dữ liệu được tách thành 2 khối trực quan, rõ ràng:
     1. Khối tím Indigo: **"📥 Xuất NV Hiện Tại (.xlsx)"** — xuất toàn bộ nhân viên đang có trong hệ thống (Mã NV, Họ Tên, Phòng ban, Email, Số điện thoại) để đối soát hoặc sửa đổi.
     2. Khối xanh Teal: **"📄 Tải File Mẫu (.xlsx)"** — tải file mẫu trống chuẩn hóa cột để chuẩn bị import.
   - Nút xuất dữ liệu nhân sự luôn sẵn sàng và hoạt động mượt mà.

### Phiên Bản 3.4.0 (08/10/2026) - Marker Gantt, Quick Links & Excel Nhân Sự Hiện Tại:
1. **Lưu & Hiển thị lịch sử cập nhật tiến độ trên biểu đồ Gantt:**
   - Form "Cập nhật tình trạng" có thêm ô nhập **"Tiến độ hoàn thành (%)"** (0–100). Mỗi lần ghi nhận đều lưu `progress` vào `statusLogs[]`.
   - Trên hàng **Thực tích** của mỗi công việc: các ngày đã ghi log xuất hiện **chấm tròn vàng nhỏ (●)** — hover để xem nội dung cập nhật nhanh.
   - Modal "Cập nhật tình trạng" hiển thị **mini biểu đồ đường SVG** (tự động xuất hiện khi có ≥2 lần cập nhật có %) cho thấy tiến độ biến thiên qua thời gian.
   - **Fix bug:** `saveStatusLog` không còn hardcode ngày `'2026-10-07'` — dùng ngày thực tế `new Date()` của hệ thống.
2. **Nút "Liên Kết Nhanh" trên thanh Header:**
   - Nút **🔗 Liên Kết** cố định trên thanh công cụ → mở modal Quick Links.
   - Hỗ trợ mọi loại đường dẫn: `file:///`, `http://`, `https://`, đường dẫn Windows (`C:\...`) và UNC (`\\server\share`).
   - Thêm/Xóa link tùy ý — lưu bền vào `localStorage` (`MBC_QUICK_LINKS`). Có 2 link mặc định (thư mục dự án + hướng dẫn).
3. **Xuất nhân sự hiện tại ra Excel (.xlsx):**
   - Trong modal Import Nhân Sự: nút **"Xuất NV Hiện Tại"** xuất hiện khi chuyển sang tab Nhân Sự, ẩn khi ở tab Công Việc.
   - Xuất toàn bộ `appData.employees` ra file `.xlsx` (Mã NV, Họ Tên, Phòng Ban, Email, Điện Thoại) — phù hợp làm nguồn để chỉnh sửa và import lại.
   - File mẫu nhân sự cũng được mở rộng thêm cột Email và Điện Thoại (từ 3 lên 5 cột).



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
