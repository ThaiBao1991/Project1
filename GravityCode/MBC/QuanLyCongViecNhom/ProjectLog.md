# Project Log - MBC Quản Lý Công Việc & Hiệu Suất Nhóm

## Thông Tin Dự Án
- **Tên dự án:** Ứng dụng Web Quản Lý Công Việc & Nhân Sự Toàn Diện (Gantt Timeline & Performance Points)
- **Vị trí:** `c:\Users\12953 Bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\GravityCode\MBC\QuanLyCongViecNhom`
- **Phiên bản:** v4.3.0 (Đánh Số Tuần Theo Từng Tháng & Quy Tắc Giao Thời Tháng Trên Timeline Gantt)
- **Ngày cập nhật:** 09/10/2026.

---

## Nhật Ký Cập Nhật (Change Log)

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
