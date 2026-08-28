"""Generate Access VBA Roadmap - 600 Days (Full Enterprise Master).

Covers 20 Phases (30 days/phase = 600 days): RDBMS 1NF-3NF, SQL Jet/ACE, DAO/ADODB, Form/Report Engine, Multi-user Concurrency,
Split Database, COM Port Hardware (Barcode/RFID/Scales), WinAPI, Ribbon XML, ODBC SQL Server/Azure,
REST API & Microsoft Graph Cloud Integration.
"""

import os

filepath = os.path.join(os.path.dirname(__file__), "roadmap_access_vba.md")
filepath_600 = os.path.join(os.path.dirname(__file__), "roadmap_access_vba_600.md")

def get_time(day_num, is_project=False):
    if is_project:
        return ("🚀", 180, "Dự án CSDL & Module — 3 tiếng")
    if day_num <= 40:
        return ("🟢", 45, "Nền tảng Form & Cú pháp — 45 phút")
    elif day_num <= 180:
        return ("🟡", 60, "Truy vấn SQL & DAO/ADO — 60 phút")
    elif day_num <= 360:
        return ("🟠", 90, "Tối ưu, Concurrency & API — 90 phút")
    else:
        return ("🔴", 120, "Hệ thống Enterprise & Cloud — 120 phút")

def build_access_roadmap():
    roadmap = {}
    current_day = 1

    def add_phase(start_day, phase_name, topics):
        prev_topic = "Bắt đầu hành trình" if start_day == 1 else roadmap[start_day - 1][0]
        for i, t in enumerate(topics):
            day = start_day + i
            title, exercise, is_proj = t
            roadmap[day] = (title, phase_name, prev_topic, exercise, is_proj)
            prev_topic = title

    phases_data = [
        # Phase 1
        ("Phase 1: VBA Syntax, Variables & Basic Controls (Day 1-30)", [
            "Button Event – Sự kiện nút bấm cơ bản", "Access Form – Tạo Form nhập liệu cơ bản", "TextBox & Label – Điều khiển cơ bản và định dạng",
            "Biến & Kiểu dữ liệu trong Access VBA", "Hằng số (Constants) & Scope (Biến cục bộ, Module, Toàn cục)", "Option Explicit & Quy tắc đặt tên biến Hungarian",
            "Toán tử Logic, So sánh & Toán học", "Lệnh rẽ nhánh If...Then...Else & If lồng nhau", "Lệnh rẽ nhánh Select Case trong Access",
            "Vòng lặp For...Next cơ bản và bước nhảy Step", "Vòng lặp For Each...Next trên Controls Form", "Vòng lặp Do While...Loop & Do Until...Loop",
            "Thoát vòng lặp an toàn (Exit For, Exit Do)", "Sub vs Function – Phân biệt và ứng dụng", "Truyền tham số ByVal vs ByRef trong Access",
            "Optional Parameters & ParamArray", "InputBox & MsgBox nâng cao", "Xử lý chuỗi (Left, Right, Mid, Len, InStr, Replace)",
            "Xử lý ngày tháng (DateSerial, DateAdd, DateDiff, Format)", "Xử lý số học (Round, Int, Fix, Abs, Rnd)", "ComboBox – Danh sách chọn nguồn cố định",
            "ListBox – Hiển thị danh sách nhiều cột", "CheckBox & OptionGroup (Frame)", "ToggleButton & TabControl trên Form",
            "Kiểm tra tính hợp lệ dữ liệu (Data Validation)", "Module chuẩn (Standard Module) vs Class Module Form", "Bắt lỗi cơ bản với On Error GoTo",
            "Debugging: Breakpoint, Immediate Window (Debug.Print)", "Debugging: Watch Window & Call Stack", "Project 1: Ứng dụng Quản lý Danh bạ Cá nhân"
        ]),
        # Phase 2
        ("Phase 2: Form Lifecycle & Multi-Form Navigation (Day 31-60)", [
            "Vòng đời Form: Form_Open vs Form_Load", "Vòng đời Form: Form_Current khi di chuyển bản ghi", "Vòng đời Form: Form_BeforeUpdate vs Form_AfterUpdate",
            "Vòng đời Form: Form_BeforeInsert & Form_AfterInsert", "Vòng đời Form: Form_Delete & BeforeDelConfirm", "Vòng đời Form: Form_Unload vs Form_Close",
            "Sự kiện điều khiển: Control_BeforeUpdate & AfterUpdate", "Sự kiện điều khiển: Control_Change vs Control_AfterUpdate", "Sự kiện bàn phím: KeyDown, KeyPress, KeyUp, KeyPreview",
            "Sự kiện chuột: MouseMove, MouseDown, MouseUp, DblClick", "Sự kiện Focus: GotFocus & LostFocus", "Form Timer: Sự kiện Form_Timer & TimerInterval",
            "Mở Form với DoCmd.OpenForm & Các tham số chế độ", "Truyền tham số qua OpenArgs", "Đóng Form an toàn với DoCmd.Close",
            "Ẩn / Hiện Form (Visible = True/False)", "Form Modal vs Modeless & Popup Form", "Giao tiếp giữa 2 Form mở đồng thời",
            "Làm mới dữ liệu: Requery vs Refresh vs Recalc", "Quản lý trạng thái Form: Me.Dirty", "Hoàn tác chỉnh sửa: Me.Undo",
            "Điều hướng bản ghi bằng DoCmd.GoToRecord", "Đồng bộ bản ghi bằng Bookmark", "Tạo Form tìm kiếm đa tiêu chí (Search Form)",
            "Lọc Form động bằng Form.Filter & FilterOn", "Sắp xếp Form động bằng Form.OrderBy & OrderByOn", "Tùy biến thanh tiêu đề và ẩn nút Close/Min/Max mặc định",
            "Thiết kế Form Responsive tự co giãn theo độ phân giải", "Tạo Breadcrumb điều hướng giữa các Form", "Project 2: Hệ thống Form Điều Hướng & Nhập Liệu Chuẩn"
        ]),
        # Phase 3
        ("Phase 3: Relational DB Design & Table Normalization (Day 61-90)", [
            "Tổng quan CSDL Quan hệ (RDBMS) trong Access", "Khái niệm Bảng (Table), Trường (Field), Bản ghi (Record)", "Kiểu dữ liệu Access: Short/Long Text, Number, Date, Currency",
            "Khóa chính (Primary Key): Single vs Composite Key", "AutoNumber – Bản chất, cạm bẫy và cách reset", "Chuẩn hóa CSDL: Dạng chuẩn 1 (1NF – First Normal Form)",
            "Chuẩn hóa CSDL: Dạng chuẩn 2 (2NF – Second Normal Form)", "Chuẩn hóa CSDL: Dạng chuẩn 3 (3NF – Third Normal Form)", "Quan hệ 1 - 1 (One-to-One): Khi nào nên dùng?",
            "Quan hệ 1 - Nhiều (One-to-Many): Cột mốc quan trọng nhất", "Quan hệ Nhiều - Nhiều (Many-to-Many) & Bảng trung gian", "Toàn vẹn tham chiếu (Referential Integrity)",
            "Cascade Update Related Fields", "Cascade Delete Related Records – Lợi ích & Nguy cơ", "Field Properties: FieldSize, Format, InputMask",
            "Field Properties: DefaultValue & Required", "Field Properties: Validation Rule & Validation Text", "Table Validation Rule (Ràng buộc cấp Bảng)",
            "Chỉ mục (Indexes): Primary, Unique, Non-Unique", "Ảnh hưởng của Index tới tốc độ Đọc vs Ghi", "Lookup Fields tại Table: Tại sao chuyên gia KHÔNG dùng?",
            "Attachment Field & OLE Object: Cạm bẫy phình dung lượng", "Calculated Fields trong Table: Ưu & Nhược điểm", "Quản lý dung lượng giới hạn 2GB của file Access (.accdb)",
            "Bảo mật dữ liệu cấp bảng: Khóa cấu trúc bảng", "Tạo bảng tự động bằng VBA DDL (Data Definition Language)", "Thêm/Xóa cột của Bảng bằng VBA",
            "Đọc thông tin Schema CSDL bằng TableDefs", "Sao lưu cấu trúc bảng (Clone Table Structure)", "Project 3: Thiết kế CSDL ERP Bán Hàng Chuẩn 3NF"
        ]),
        # Phase 4
        ("Phase 4: SQL Mastery – Jet/ACE SQL Engine (Day 91-120)", [
            "Cú pháp SQL cơ bản trong Access: SELECT, FROM", "Mệnh đề WHERE & Các toán tử: =, <>, LIKE, BETWEEN, IN", "Ký tự đại diện trong Access SQL: * vs % (ANSI-89 vs ANSI-92)",
            "Mệnh đề ORDER BY: Sắp xếp đơn cột và đa cột", "Mệnh đề DISTINCT & DISTINCTROW", "Mệnh đề TOP N & TOP N PERCENT",
            "Hàm tổng hợp SQL: COUNT, SUM, AVG, MIN, MAX", "Mệnh đề GROUP BY: Nhóm dữ liệu theo danh mục", "Mệnh đề HAVING: Lọc trên kết quả tổng hợp",
            "INNER JOIN: Kết nối 2 bảng theo khóa ngoại", "LEFT JOIN: Lấy toàn bộ bảng bên trái", "RIGHT JOIN: Lấy toàn bộ bảng bên phải",
            "INNER JOIN nhiều bảng (3-5 bảng) trong Access", "Self-Join: Bảng tự kết nối với chính nó", "Subquery trong mệnh đề WHERE (IN, EXISTS)",
            "Subquery tương quan (Correlated Subquery)", "Subquery trong mệnh đề FROM (Derived Tables)", "Mệnh đề UNION & UNION ALL: Gộp kết quả truy vấn",
            "Crosstab Query (TRANSFORM ... PIVOT): Ma trận xoay", "SQL INSERT INTO: Thêm một bản ghi đơn lẻ", "SQL INSERT INTO ... SELECT: Thêm hàng loạt từ bảng khác",
            "SQL UPDATE: Cập nhật dữ liệu hàng loạt có điều kiện", "SQL UPDATE có JOIN: Cập nhật dựa trên bảng khác", "SQL DELETE: Xóa dữ liệu có điều kiện",
            "SQL DDL: CREATE TABLE, ALTER TABLE, DROP TABLE", "SQL DDL: CREATE INDEX, DROP INDEX", "Xử lý giá trị NULL trong SQL: Is Null, Nz(), IIf()",
            "Hàm ngày tháng trong Access SQL: Date(), Year(), Month(), DateDiff()", "Hàm chuỗi trong Access SQL: UCase(), Left(), InStr()", "Project 4: Hệ Thống Báo Cáo Phân Tích Dữ Liệu SQL Hoàn Chỉnh"
        ]),
        # Phase 5
        ("Phase 5: DAO & Recordset Deep Dive (Day 121-150)", [
            "Giới thiệu Thư viện DAO (Microsoft Office Access database engine Object Library)", "Đối tượng CurrentDb(): Cơ chế mở và giải phóng bộ nhớ", "Mở Recordset: dbOpenTable, dbOpenDynaset, dbOpenSnapshot",
            "Duyệt Recordset từ đầu đến cuối (Loop EOF/BOF)", "Đếm số bản ghi chính xác với MoveLast & RecordCount", "Thêm bản ghi mới bằng DAO: .AddNew & .Update",
            "Sửa bản ghi bằng DAO: .Edit & .Update", "Xóa bản ghi bằng DAO: .Delete", "Tìm kiếm trong Recordset: .FindFirst, .FindNext, .NoMatch",
            "Tìm kiếm bằng Seek trên Index bảng (dbOpenTable)", "Bookmark trong DAO Recordset", "Lọc Recordset đã mở: .Filter & Tạo Recordset con",
            "Sắp xếp Recordset đã mở: .Sort", "Xử lý lỗi DAO phổ biến: Error 3021 (No Current Record)", "Xử lý lỗi DAO: Error 3061 (Too Few Parameters)",
            "Mở database ngoài bằng OpenDatabase", "Mở database có mật khẩu (Database Password)", "Duyệt danh sách TableDefs và Fields bằng DAO",
            "Tạo trường mới (Field) và gán thuộc tính bằng DAO", "Tạo quan hệ (Relation) giữa 2 bảng bằng DAO", "Đọc dữ liệu cực nhanh với GetRows() vào Mảng 2D",
            "Ghi hàng loạt cực nhanh: dbFailOnError & Execute", "So sánh tốc độ: db.Execute SQL vs Recordset Loop", "RecordsetClone của Form: Cầu nối Form & DAO",
            "Recordset2 Object: Xử lý Attachment & Multi-value Fields", "Lưu file từ Attachment ra ổ đĩa máy tính bằng DAO", "Nạp file từ ổ đĩa vào Attachment Field bằng DAO",
            "Kiểm tra trạng thái Lock của Recordset (LockEdits)", "Hàm tiện ích toàn năng: DLookup, DCount, DSum, DAvg", "Project 5: Xây Dựng Data Access Layer (DAL) Bằng DAO"
        ]),
        # Phase 6
        ("Phase 6: ADODB & Remote Connections (Day 151-180)", [
            "Giới thiệu ADODB (ActiveX Data Objects) trong Access", "Khai báo ADODB.Connection và ADODB.Recordset", "Connection String chuẩn OLEDB cho Access (.accdb)",
            "Mở và Đóng kết nối ADODB Connection an toàn", "CursorType: adOpenForwardOnly, adOpenKeyset, adOpenDynamic, adOpenStatic", "LockType: adLockReadOnly, adLockPessimistic, adLockOptimistic, adLockBatchOptimistic",
            "Duyệt ADODB Recordset và xử lý EOF/BOF", "Thêm bản ghi bằng ADODB .AddNew & .Update", "Sửa và Xóa bản ghi bằng ADODB Recordset",
            "Tìm kiếm trong ADODB với .Find và .Filter", "Sắp xếp ADODB Recordset trong bộ nhớ với .Sort", "Disconnected Recordset: Ngắt kết nối DB vẫn duyệt dữ liệu",
            "Tạo In-Memory Recordset (Fabricated Recordset) không cần DB", "Gán ADODB Recordset làm Recordset cho Form Access", "ADODB.Command: Thực thi câu lệnh SQL có tham số",
            "Chống lỗi SQL Injection triệt để bằng ADODB.Parameters", "Thực thi Stored Procedure từ xa bằng ADODB", "Lấy giá trị Output Parameter và Return Value từ Procedure",
            "Xử lý lỗi ADODB: Đối tượng Errors Collection", "Bắt lỗi Timeout kết nối mạng và Connection Lost", "Batch Update: Cập nhật hàng loạt thay đổi với .UpdateBatch",
            "Hủy thay đổi hàng loạt với .CancelBatch", "Chuyển đổi dữ liệu giữa DAO Recordset và ADODB Recordset", "Đọc dữ liệu XML và JSON vào ADODB Stream",
            "Kết nối Excel bằng ADODB (Driver Microsoft.ACE.OLEDB)", "Truy vấn dữ liệu từ file Excel như một bảng CSDL", "Kết nối file CSV / Text bằng ADODB Schema.ini",
            "So sánh toàn diện: Khi nào dùng DAO, khi nào dùng ADODB?", "Xây dựng Connection Pool quản lý kết nối ADODB", "Project 6: Module Kết Nối Đa Nguồn Bằng ADODB"
        ]),
        # Phase 7
        ("Phase 7: QueryDefs & Transactions (Day 181-210)", [
            "Khái niệm QueryDef trong DAO: Bản chất của Saved Queries", "Tạo QueryDef mới bằng mã VBA: db.CreateQueryDef", "Đọc và sửa câu lệnh SQL của QueryDef có sẵn",
            "Xóa QueryDef bằng mã VBA an toàn", "QueryDef có tham số (Parameterized QueryDef)", "Truyền giá trị cho Parameters trong QueryDef từ Form",
            "Tối ưu hóa: Tại sao QueryDef chạy nhanh hơn chuỗi SQL động?", "Kỹ thuật Temporary QueryDef (QueryDef ẩn danh không tên)", "Duyệt danh sách toàn bộ QueryDefs và xuất ra file SQL",
            "Giao dịch (Transactions) là gì? Tiêu chuẩn ACID trong Access", "Bắt đầu giao dịch: DBEngine.BeginTrans / Workspace.BeginTrans", "Cam kết giao dịch: DBEngine.CommitTrans",
            "Hoàn tác giao dịch khi có lỗi: DBEngine.Rollback", "Quản lý Giao dịch lồng nhau (Nested Transactions)", "Ứng dụng Transaction: Chuyển tiền giữa 2 tài khoản ngân hàng",
            "Ứng dụng Transaction: Lưu Đơn hàng + 10 Chi tiết đơn hàng đồng thời", "Xử lý ngoại lệ trong khối Transaction chuẩn mẫu", "Ảnh hưởng của Transaction tới tốc độ ghi đĩa",
            "Kiểm tra tính toàn vẹn dữ liệu sau khi Rollback", "Audit Trail: Tự động ghi Log mọi thao tác Thêm/Sửa/Xóa vào bảng Log", "Ghi lại giá trị Cũ (OldValue) và giá trị Mới (Value) của từng trường",
            "Phát hiện ai đã sửa dữ liệu, vào lúc nào, từ máy tính nào", "Khôi phục dữ liệu đã xóa từ bảng Audit Trail", "Pass-Through Query: Gửi nguyên văn SQL tới Server từ xa",
            "Cấu hình Chuỗi kết nối ODBC cho Pass-Through Query", "Lấy kết quả từ Pass-Through Query vào Recordset Access", "Thực thi lệnh DDL trên SQL Server qua Pass-Through Query",
            "Bảo mật thông tin đăng nhập trong Pass-Through Query", "Tự động làm mới định nghĩa QueryDefs khi nâng cấp phần mềm", "Project 7: Hệ Thống Giao Dịch & Ghi Nhật Ký Biến Động (Audit Trail)"
        ]),
        # Phase 8
        ("Phase 8: Advanced UI, Continuous Forms & Subforms (Day 211-240)", [
            "Continuous Forms (Form dạng liên tục): Bản chất và cơ chế vẽ", "Tùy biến giao diện lưới dữ liệu đẹp mắt trên Continuous Form", "Conditional Formatting trên Continuous Form bằng VBA",
            "Highlight dòng hiện hành trên Continuous Form mà không lag", "Subform Control: Bản chất và thuộc tính LinkMasterFields / LinkChildFields", "Đồng bộ Form Cha - Con tự động qua quan hệ khóa",
            "Giao tiếp 2 chiều: Từ Subform gọi hàm trên Main Form và ngược lại", "Subform lồng nhau (Main Form -> Subform 1 -> Subform 2)", "Dynamic Subform: Thay đổi SourceObject của Subform theo ComboBox",
            "Tạo Form Master-Detail chuẩn mực cho Quản lý Hóa đơn", "Custom Navigation Bar thay thế thanh điều hướng mặc định", "Thêm thanh phân trang (Pagination) cho Form: Trang 1/10 (50 dòng/trang)",
            "Tìm kiếm và lọc dữ liệu tức thì (Instant Filter as you type)", "Highlight từ khóa tìm kiếm trên các ô TextBox của Form", "Tạo Dropdown Auto-Complete thông minh với ComboBox",
            "ListBox nhiều cột có thanh tiêu đề và sắp xếp khi click", "Kéo thả (Drag and Drop) cơ bản giữa các điều khiển", "Tùy biến Shortcut Menu (Menu chuột phải) cho từng ô nhập liệu",
            "Hiển thị Tooltip tùy biến dạng HTML / Balloon", "Xây dựng Custom Dialog Box trả về kết quả cho Form gọi", "Tạo Form Wizard từng bước (Step 1 -> Step 2 -> Step 3)",
            "Form Split (Bảng tách đôi: Nửa trên Form, Nửa dưới Bảng tính)", "Xây dựng Dashboard trực quan với các chỉ số KPI Cards", "Nhúng biểu đồ Modern Chart vào Access Form",
            "Tự động cập nhật biểu đồ khi dữ liệu Form thay đổi", "Kiểm soát thứ tự Tab (TabIndex) và bẫy phím tắt người dùng", "Khóa toàn bộ Form ở chế độ View-Only với 1 dòng lệnh",
            "Phát hiện thay đổi chưa lưu khi người dùng bấm chuyển bản ghi", "Tối ưu hóa tốc độ load Form có chứa nhiều Subforms nặng", "Project 8: Giao Diện Bán Hàng POS Cảm Ứng Bằng Access Form"
        ]),
        # Phase 9
        ("Phase 9: Custom Reports & Print Engine (Day 241-270)", [
            "Kiến trúc Report trong Access: Report Header, Page Header, Detail, Page Footer, Report Footer", "Grouping & Sorting trong Report: Phân nhóm theo Khách hàng / Phòng ban", "Group Header & Group Footer: Tính tổng con (Subtotal) cho từng nhóm",
            "Thuộc tính Running Sum (Cộng dồn / Đánh số thứ tự 1, 2, 3...)", "Sự kiện Report: Report_Open, Report_Close, Format, Print", "Sự kiện Detail_Format: Can thiệp ẩn/hiện hoặc đổi màu dòng theo điều kiện",
            "Sự kiện Detail_Print: Vẽ đường kẻ, hình khối bằng phương thức Me.Line, Me.Circle", "Thuộc tính CanGrow & CanShrink: Tự động co giãn chiều cao dòng theo nội dung", "Xử lý ngắt trang thông minh (Page Break, KeepTogether, ForceNewPage)",
            "Tạo Báo cáo Hóa đơn Đỏ / Phiếu thu tiền chuẩn biểu mẫu A4/A5", "In Báo cáo nhiều cột (Multi-Column Report / In Nhãn nhãn dán Barcode)", "Truyền bộ lọc động khi mở Report với DoCmd.OpenReport & WhereCondition",
            "Xem trước báo cáo (acViewPreview) vs In trực tiếp (acViewNormal)", "Tùy biến cửa sổ Print Preview: Ẩn Ribbon, vô hiệu hóa nút in trái phép", "Xuất Báo cáo ra file PDF bằng DoCmd.OutputTo acOutputPDF",
            "Tự động đặt tên file PDF theo Mã Hóa Đơn và Ngày Tháng", "Xuất Báo cáo sang định dạng Excel (.xlsx), Word (.rtf), HTML", "Tự động gửi email đính kèm file PDF báo cáo qua Outlook",
            "In hàng loạt 100 hóa đơn ra máy in không hiện thông báo chờ", "Chọn máy in linh hoạt bằng Application.Printer & Printers Collection", "In vé nhiệt / In hóa đơn K80 từ Access Report",
            "Tạo Báo cáo Subreport (Báo cáo lồng nhau: Đơn hàng + Chi tiết)", "Tính toán trang: Trang [Page] trên tổng số [Pages] và xử lý 2-pass", "In hình mờ (Watermark 'ĐÃ THANH TOÁN', 'BẢN NHÁP') lên Report",
            "Tạo Báo cáo Tổng kết Tài chính Đa cấp có biểu đồ đính kèm", "Tối ưu tốc độ Report truy vấn trên bảng hàng trăm nghìn dòng", "Bảo vệ bản quyền và chống sao chép dữ liệu trên Report",
            "In Barcode Code128 / QR Code trực tiếp lên Access Report", "Lưu cấu hình in ấn riêng cho từng mẫu báo cáo", "Project 9: Hệ Thống Xuất & In Báo Cáo Doanh Thu / Hóa Đơn Tự Động"
        ]),
        # Phase 10
        ("Phase 10: Transactions, ACID & Security (Day 271-300)", [
            "Phân tích chuyên sâu 4 thuộc tính ACID trong Access Database", "Quản lý Workspace trong DAO và đa Workspace độc lập", "Kiểm soát xung đột khi nhiều Transaction ghi cùng lúc",
            "Chiến lược xử lý lỗi Timeout trong Transaction mạng", "Tạo hệ thống Phân quyền Người dùng (RBAC: Role-Based Access Control)", "Bảng Phân quyền: User, Role, Permissions (Read/Write/Delete/Approve)",
            "Mã hóa Mật khẩu người dùng bằng thuật toán băm (Hash SHA-256)", "Tạo Form Đăng nhập bảo mật: Chặn Brute Force sau 5 lần sai", "Lưu phiên làm việc toàn cục (g_CurrentUser, g_UserRole, g_LoginTime)",
            "Ẩn/Hiện nút bấm và Form theo quyền hạn của tài khoản đang đăng nhập", "Khóa giao diện Back-end Access: Ẩn Navigation Pane, Phím Shift, VBE", "Vô hiệu hóa phím Bypass Shift khi khởi động ứng dụng",
            "Tự động kích hoạt mật khẩu bảo vệ CSDL (.accdb Password)", "Mã hóa và Đóng gói file sang định dạng .accde (Chống xem mã nguồn VBA)", "Bảo vệ bản quyền phần mềm: Khóa theo Mã Ổ Cứng (HDD Serial / Motherboard ID)",
            "Tạo License Key kích hoạt phần mềm có thời hạn sử dụng", "Ghi vết thay đổi nhạy cảm (Security Audit Log)", "Tự động sao lưu dự phòng CSDL trước khi thực hiện thao tác xóa lớn",
            "Kiểm tra tính toàn vẹn CSDL (Data Corruption Check)", "Quy trình Phục hồi dữ liệu khi file Access bị lỗi Corrupt", "Tự động Compact and Repair Database khi đóng ứng dụng",
            "Giám sát dung lượng file và cảnh báo khi đạt ngưỡng 1.8GB", "Tách dữ liệu lịch sử sang Database phụ (Data Archiving)", "Xóa an toàn dữ liệu nhạy cảm theo tiêu chuẩn bảo mật",
            "Chống trích xuất dữ liệu trái phép qua ODBC", "Kiểm tra quyền Administrator của Windows trước khi chạy ứng dụng", "Xây dựng nhật ký bảo mật đăng nhập/đăng xuất",
            "Tự động khóa ứng dụng khi không có thao tác sau 15 phút", "Kiểm tra chữ ký số VBA Project Signature", "Project 10: Hệ Thống Bảo Mật Toàn Diện & Phân Quyền Đa Cấp Cho Doanh Nghiệp"
        ]),
        # Phase 11
        ("Phase 11: Multi-User Concurrency & Record Locking (Day 301-330)", [
            "Nguyên lý hoạt động của Access trong môi trường mạng LAN nhiều người dùng", "File khóa .laccdb: Cơ chế hoạt động và phát hiện ai đang mở file", "Xung đột ghi đồng thời (Write Conflict): Nguyên nhân và triệu chứng",
            "No Locks (Khóa mặc định / Khóa mở): Cách thức hoạt động", "All Records Lock (Khóa toàn bộ bảng): Khi nào nên dùng?", "Edited Record Lock (Khóa bản ghi đang sửa): Cơ chế Page Locking 4KB",
            "Khóa Lạc quan (Optimistic Locking): Phát hiện xung đột khi lưu", "Khóa Bi quan (Pessimistic Locking): Khóa ngay khi bắt đầu gõ", "Bắt và xử lý lỗi Error 3197: 'Dữ liệu đã bị người dùng khác thay đổi'",
            "Bắt và xử lý lỗi Error 3260: 'Bản ghi hiện đang bị khóa bởi máy khác'", "Tạo cột Timestamp / RowVersion để tự kiểm soát xung đột", "Xây dựng cơ chế Soft Lock tùy biến bằng bảng tblActiveLocks",
            "Tự động mở khóa khi người dùng bị ngắt mạng hoặc tắt máy đột ngột", "Hiển thị ai đang chỉnh sửa bản ghi này trên Form realtime", "Cấu hình Refresh Interval và Update Retry trong Access Options bằng VBA",
            "Kỹ thuật tối ưu hóa mạng LAN để tránh hỏng file .accdb", "Quy tắc vàng: Tuyệt đối KHÔNG chia sẻ chung file Frontend cho nhiều người", "Tự động cấp phát ID không bị trùng lặp trong môi trường nhiều máy cùng thêm mới",
            "So sánh AutoNumber vs Tự sinh mã có Transaction trong mạng LAN", "Xử lý nghẽn mạng khi 20 người cùng in báo cáo đồng thời", "Kỹ thuật đọc dữ liệu không khóa bảng (Dirty Read / Read Uncommitted)",
            "Mô phỏng 5 máy cùng sửa 1 bản ghi và kiểm tra tính toàn vẹn", "Xây dựng hàng đợi xử lý (Message Queue) trong Access Table", "Đồng bộ dữ liệu định kỳ giữa các chi nhánh qua mạng",
            "Tự động phát hiện mất kết nối tới ổ đĩa mạng Backend", "Tự động kết nối lại khi mạng LAN phục hồi", "Thông báo broadcast tới toàn bộ nhân viên đang mở ứng dụng",
            "Ép toàn bộ người dùng thoát ứng dụng để bảo trì hệ thống từ xa", "Kiểm tra hiệu năng truy vấn qua mạng LAN 100Mbps vs 1Gbps", "Project 11: Hệ Thống Quản Lý Đơn Hàng Đa Người Dùng Chống Xung Đột 100%"
        ]),
        # Phase 12
        ("Phase 12: Split Database Architecture & Backend Maintenance (Day 331-360)", [
            "Kiến trúc Split Database: Tách Frontend (Giao diện + VBA) và Backend (Bảng dữ liệu)", "Lợi ích của Split Database: Tốc độ, bảo mật, bảo trì, chống corrupt", "Tách CSDL thủ công và dùng công cụ Database Splitter Wizard",
            "Bản chất của Linked Tables (Bảng liên kết trong Access)", "Kiểm tra đường dẫn Backend của Linked Table qua TableDef.Connect", "Tự động Relink Tables bằng mã VBA khi đổi thư mục lưu file",
            "Xây dựng Form 'Cấu hình đường dẫn CSDL' cho người dùng", "Kiểm tra sự tồn tại của file Backend trước khi mở ứng dụng", "Hỗ trợ kết nối nhiều file Backend đồng thời (Backend_Data, Backend_Log, Backend_Archive)",
            "Tự động tạo bản sao lưu Backend (.bak) mỗi ngày khi mở máy", "Nén và Phục hồi Backend từ xa qua mạng bằng VBA (CompactBackend)", "Cơ chế Tự động Cập nhật phiên bản Frontend mới (Auto-Updater)",
            "Quy trình Auto-Update: Kiểm tra version -> Tải file FE mới -> Khởi động lại", "Đóng gói file cài đặt Frontend cho từng máy trạm nhân viên", "Chuyển đổi Backend từ Access sang file CSDL mã hóa",
            "Xử lý sự cố đứt kết nối Linked Table giữa chừng", "Giám sát tốc độ phản hồi của file Backend trên server", "Thiết lập quyền thư mục Windows Share an toàn cho Backend",
            "Chống copy trộm file Backend từ ổ đĩa chia sẻ", "Phục hồi tự động bảng liên kết bị hỏng schema", "Chạy lệnh bảo trì định kỳ tự động vào ban đêm",
            "Gửi email báo cáo tình trạng sức khỏe của Backend cho Admin", "Quản lý lịch sử các phiên bản nâng cấp phần mềm", "Tạo bộ cài đặt One-Click Setup cho nhân viên mới",
            "Tích hợp công cụ chẩn đoán lỗi mạng và kết nối Backend", "Kiểm tra tương thích giữa các phiên bản Access 2016, 2019, 2021, M365", "Chạy Access Frontend không cần cài đặt đầy đủ Office (Access Runtime)",
            "Đóng gói ứng dụng chạy mượt mà trên Access Runtime miễn phí", "Xử lý các lỗi giao diện phát sinh riêng trên Access Runtime", "Project 12: Bộ Đôi Frontend-Backend Hoàn Chỉnh Kèm Auto-Updater Thông Minh"
        ]),
        # Phase 13
        ("Phase 13: Query Performance Tuning & Jet Engine Optimization (Day 361-390)", [
            "Cơ chế hoạt động bên trong của Jet/ACE Query Optimizer (Rushmore Technology)", "Phân tích Query Execution Plan (Kế hoạch thực thi câu truy vấn)", "Chỉ số hiệu năng: Jet ShowPlan (Bật ghi log tối ưu truy vấn ra file text)",
            "Tối ưu hóa mệnh đề WHERE: Tránh dùng hàm trên cột có Index (Sargability)", "Tại sao WHERE Year(NgayTao) = 2026 làm mất tác dụng của Index?", "Viết lại điều kiện lọc chuẩn Sargable: WHERE NgayTao >= #2026-01-01# AND NgayTao < #2027-01-01#",
            "Tối ưu hóa toán tử LIKE: Tìm kiếm đầu chuỗi 'ABC*' vs giữa chuỗi '*ABC*'", "Tối ưu hóa câu truy vấn JOIN: Thứ tự kết nối bảng và kiểu dữ liệu khóa", "Tránh xung đột kiểu dữ liệu giữa khóa chính và khóa ngoại (Type Mismatch)",
            "Tối ưu hóa câu lệnh đếm: COUNT(*) vs COUNT(ID) vs DCount", "Kỹ thuật thay thế DLookup chậm chạp bằng DAO Recordset Seek hoặc Query JOIN", "Benchmark đo thời gian thực thi chính xác đến mili-giây bằng WinAPI QueryPerformanceCounter",
            "Tối ưu hóa bộ nhớ khi xử lý Recordset lớn: Sử dụng dbForwardOnly và dbReadOnly", "Tối ưu hóa Form load chậm: Bỏ gán RecordSource lúc mở, chỉ gán khi cần", "Kỹ thuật Lazy Loading cho các Tab con trên Form",
            "Tối ưu hóa ComboBox có danh sách trên 10.000 dòng", "Giới hạn số dòng tải vào ComboBox bằng kỹ thuật gõ 3 ký tự mới load", "Xóa bỏ các trường dư thừa trong câu lệnh SELECT (Tránh dùng SELECT *)",
            "Tối ưu hóa subquery lồng nhau: Chuyển Subquery thành JOIN", "Đo lường mức tiêu hao RAM và CPU của Access khi chạy tác vụ nặng", "Giải phóng rò rỉ bộ nhớ (Memory Leak) trong các vòng lặp VBA dài",
            "Quy tắc đóng và giải phóng biến Object (Set obj = Nothing)", "Tối ưu hóa tốc độ ghi đĩa khi import 100.000 dòng dữ liệu", "Tắt cập nhật giao diện và màn hình khi chạy tác vụ nền (Echo, DoEvents)",
            "Tối ưu hóa việc sử dụng Domain Aggregate Functions trong Report", "Phân tích dung lượng từng bảng để tìm nguyên nhân DB phình to", "Kỹ thuật nén gọn chuỗi SQL và tái sử dụng QueryDefs trong bộ nhớ",
            "Khắc phục tình trạng Access bị treo đơ 'Not Responding'", "Thiết lập cấu hình MaxBufferSize trong Windows Registry cho Jet Engine", "Project 13: Công Cụ Tối Ưu & Tăng Tốc Toàn Diện Cho Hệ Thống Access Chậm"
        ]),
        # Phase 14
        ("Phase 14: Hardware Interfacing – COM Port RS232, Barcode & RFID (Day 391-420)", [
            "Tổng quan về Giao tiếp Phần cứng từ Access VBA", "Cổng nối tiếp Serial Port (COM Port / RS232 / USB Virtual COM)", "MSComm32 ActiveX Control: Khai báo và cấu hình thông số cổng COM",
            "Giao tiếp COM Port không dùng ActiveX: WinAPI CreateFile & ReadFile", "Cấu hình BaudRate, Parity, DataBits, StopBits cho thiết bị", "Mở và Đóng cổng COM an toàn trong VBA",
            "Đọc dữ liệu từ Máy quét mã vạch (Barcode Scanner) qua Cổng COM", "Bắt sự kiện quét mã vạch qua bàn phím (Keyboard Wedge Hook)", "Tự động tìm kiếm và thêm sản phẩm vào giỏ hàng ngay khi quét mã",
            "Tạo và in mã vạch Code128 / Code39 trực tiếp từ Access", "Tạo và in mã QR Code động từ dữ liệu hóa đơn", "Giao tiếp với Cân điện tử công nghiệp qua cổng COM RS232",
            "Đọc trọng lượng cân liên tục và điền tự động vào ô Khối lượng", "Lọc nhiễu và chuẩn hóa chuỗi dữ liệu nhận được từ cân điện tử", "Giao tiếp với Đầu đọc thẻ từ / Thẻ RFID (Mifare 13.56MHz / EM4100)",
            "Quẹt thẻ nhân viên để tự động Chấm công và Mở cửa", "Giao tiếp với Máy in nhiệt hóa đơn K80/K58 qua cổng USB / COM", "Gửi mã lệnh ESC/POS trực tiếp tới máy in để cắt giấy và mở két tiền",
            "Tự động mở Két đựng tiền (Cash Drawer) khi bấm thanh toán", "Giao tiếp với Máy đo nhiệt độ / Cảm biến môi trường IoT", "Giao tiếp với Bộ điều khiển PLC / Relay Module qua chuẩn Modbus RTU",
            "Kích hoạt đóng/ngắt rơ-le điện từ nút bấm trên Access Form", "Đọc dữ liệu từ Máy đo kích thước / Thước đo điện tử kẹp số", "Xử lý lỗi mất kết nối phần cứng và tự động kết nối lại cổng COM",
            "Đa luồng giả lập: Đọc cổng COM nền không làm đơ giao diện Form", "Ghi log dữ liệu thô từ cổng COM ra file để phân tích sự cố", "Kiểm tra danh sách các cổng COM đang khả dụng trên máy tính",
            "Xây dựng bảng Cấu hình thiết bị phần cứng trong CSDL", "Tạo module kiểm tra trạng thái phần cứng khi khởi động", "Project 14: Hệ Thống Bán Hàng & Cân Trọng Lượng Tự Động Kết Nối Phần Cứng"
        ]),
        # Phase 15
        ("Phase 15: Windows API Integration & System Deep Control (Day 421-450)", [
            "Tổng quan về Windows API (Win32 API) trong Access VBA", "Phân biệt khai báo API trên Access 32-bit (PtrSafe, Long) vs 64-bit (LongPtr)", "Đọc thông tin hệ điều hành: GetVersionEx, GetComputerName, GetUserName",
            "Lấy địa chỉ MAC Card mạng để khóa bản quyền phần mềm", "Đọc và ghi Windows Registry: RegOpenKeyEx, RegQueryValueEx, RegSetValueEx", "Lưu cấu hình ứng dụng vào Registry HKCU và HKLM",
            "Thao tác File & Thư mục bằng Windows API: ShellExecute, CopyFile, DeleteFile", "Mở file bất kỳ bằng chương trình mặc định của Windows (PDF, Word, Ảnh)", "Hộp thoại chọn file chuẩn Windows (GetOpenFileName / GetSaveFileName API)",
            "Hộp thoại chọn thư mục Windows (SHBrowseForFolder API)", "Điều khiển Cửa sổ Windows: FindWindow, SetWindowText, MoveWindow, ShowWindow", "Tự động phóng to toàn màn hình không viền (Borderless Fullscreen)",
            "Giữ cửa sổ Form luôn nổi trên cùng (Always on Top) với SetWindowPos", "Độ trong suốt của Form (Transparent Form) bằng SetLayeredWindowAttributes", "Tạo âm thanh cảnh báo hệ thống bằng Beep API và PlaySound",
            "Tạo biểu tượng ứng dụng ở khay hệ thống (System Tray Icon với Shell_NotifyIcon)", "Bắt sự kiện Click vào System Tray Icon để ẩn/hiện Access", "Hiển thị thông báo Windows Balloon Notification / Toast Notification",
            "Khóa bàn phím và chuột khi thực hiện tác vụ bảo mật (BlockInput API)", "Đọc và ghi dữ liệu Clipboard Windows trực tiếp qua API", "Đo thời gian siêu chính xác bằng QueryPerformanceFrequency và QueryPerformanceCounter",
            "Tạm dừng chương trình không đơ giao diện bằng Sleep API kết hợp DoEvents", "Quản lý tiến trình Windows: OpenProcess, TerminateProcess, EnumProcesses", "Kiểm tra xem file Excel / Word có đang bị chương trình khác mở khóa không",
            "Can thiệp bộ nhớ RAM bằng CopyMemory (RtlMoveMemory) trong VBA", "Subclassing cửa sổ Access: Bắt sự kiện cuộn chuột (Mouse Wheel Hook)", "Khắc phục lỗi cuộn chuột nhảy bản ghi trên Access Form cũ",
            "Chạy script PowerShell và nhận kết quả trả về trong VBA", "Gửi phím tắt tự động tới ứng dụng khác bằng keybd_event API", "Project 15: Module Tích Hợp Windows API Toàn Diện & Đưa App Vào System Tray"
        ]),
        # Phase 16
        ("Phase 16: Ribbon XML Customization & App Packaging (Day 451-480)", [
            "Kiến trúc Ribbon trong Microsoft Access: Bản chất cấu trúc XML", "Bảng USysRibbons: Nơi lưu trữ mã XML tùy biến thanh Ribbon", "Cấu trúc file Ribbon XML chuẩn: customUI, ribbon, tabs, tab, group, button",
            "Thêm Tab riêng cho ứng dụng trên thanh Ribbon Access", "Tạo các nút bấm (Button), biểu tượng (ImageMso) và phím tắt (Keytip)", "Gán hàm callback VBA khi người dùng click vào nút trên Ribbon",
            "Tạo Menu thả xuống (Menu / SplitButton) trên Ribbon", "Tạo ComboBox và EditBox nhập liệu trực tiếp trên thanh Ribbon", "Tạo CheckBox và ToggleButton lưu trạng thái trên Ribbon",
            "Dynamic Ribbon: Thay đổi trạng thái nút (Enable/Disable, Label) theo thời gian thực", "Phương thức Invalidate & InvalidateControl của IRibbonUI", "Sử dụng icon tùy biến từ file ảnh PNG/ICO ngoài ổ đĩa",
            "Ẩn toàn bộ Ribbon mặc định của Access, chỉ hiện Ribbon chuyên dụng", "Tùy biến Quick Access Toolbar (QAT) cho phần mềm", "Tùy biến Backstage View (Menu File khi click góc trái)",
            "Tùy biến Shortcut Menu (Menu chuột phải) bằng Ribbon XML", "Gán Ribbon riêng cho từng Form và từng Report cụ thể", "Tùy biến biểu tượng thanh tác vụ và Tiêu đề ứng dụng (AppTitle & AppIcon)",
            "Tạo bảng điều khiển chuyển hướng trung tâm (Modern Navigation Switchboard)", "Đóng gói toàn bộ ứng dụng sang file ACCDE chống dịch ngược", "Khóa giao diện triệt để: Vô hiệu hóa phím F11, menu Design View, cửa sổ Navigation",
            "Tạo file cấu hình khởi động AutoExec Macro", "Xây dựng bộ cài đặt phần mềm chuyên nghiệp bằng Inno Setup", "Tự động kiểm tra và cài đặt Access Runtime nếu máy khách chưa có",
            "Tạo Shortcut trên Desktop và Start Menu kèm Icon đẹp mắt", "Tự động đăng ký các thư viện DLL và ActiveX khi cài đặt", "Cấp phép bản quyền phần mềm (Licensing System) với mã kích hoạt mã hóa",
            "Hệ thống kiểm tra ngày hết hạn dùng thử (Trial 30 ngày)", "Tạo tài liệu hướng dẫn sử dụng tích hợp dạng file Help (.chm) hoặc PDF", "Project 16: Đóng Gói Ứng Dụng Thương Mại Hoàn Chỉnh Có Ribbon XML & License Key"
        ]),
        # Phase 17
        ("Phase 17: SQL Server & Azure SQL via ODBC (Day 481-510)", [
            "Tại sao doanh nghiệp cần nâng cấp Backend từ Access sang SQL Server / Azure SQL?", "Kiến trúc Client/Server: Access Frontend + SQL Server Backend", "Cài đặt SQL Server Express và SQL Server Management Studio (SSMS)",
            "Cài đặt và cấu hình ODBC Driver for SQL Server (ODBC Driver 18)", "Tạo kết nối DSN-less Connection bằng VBA không cần cài DSN thủ công", "Sử dụng công cụ Microsoft SQL Server Migration Assistant (SSMA) for Access",
            "Chuyển đổi kiểu dữ liệu Access sang SQL Server (AutoNumber -> IDENTITY, Long Text -> NVARCHAR(MAX))", "Tạo Linked Tables kết nối SQL Server qua ODBC", "Xử lý vấn đề Primary Key và Unique Index trên Linked Table SQL Server",
            "Tạo trường rowversion (timestamp) trên SQL Server để tăng tốc cập nhật", "Tối ưu hóa hiệu năng Linked Table ODBC: Hạn chế kéo dữ liệu thừa", "Sử dụng SQL Server Views làm RecordSource cho Access Form",
            "Sử dụng SQL Server Stored Procedures tăng tốc độ xử lý gấp 100 lần", "Gọi Stored Procedure từ Access VBA qua ADODB.Command và Pass-Through Query", "Truyền tham số và nhận kết quả từ Stored Procedure",
            "Sử dụng SQL Server Triggers để tự động ghi log và kiểm tra dữ liệu", "Phân quyền bảo mật cấp cơ sở dữ liệu trên SQL Server (Users, Roles, Permissions)", "Kết nối Cloud Database: Microsoft Azure SQL Database từ Access",
            "Cấu hình Azure Firewall cho phép IP máy trạm kết nối an toàn", "Xác thực Azure SQL bằng Azure Active Directory (Microsoft Entra ID) và SQL Auth", "Xử lý độ trễ mạng Internet khi kết nối CSDL Cloud",
            "Chiến lược Caching dữ liệu cục bộ để Form mở nhanh tức thì trên Cloud", "Xây dựng ứng dụng Hybrid: Dữ liệu nhạy cảm lưu Local, Báo cáo đẩy lên Azure", "Đồng bộ hóa dữ liệu 2 chiều giữa Access Offline và SQL Server Online",
            "Xử lý đứt kết nối mạng Internet khi đang thao tác với Azure SQL", "Tự động Reconnect Linked Tables khi mạng Internet phục hồi", "Sao lưu và Khôi phục CSDL SQL Server tự động bằng lệnh T-SQL từ Access",
            "Giám sát hiệu năng câu truy vấn trên SQL Server bằng Activity Monitor", "Tối ưu hóa chi phí vận hành Azure SQL Database", "Project 17: Hệ Thống Bán Hàng Trực Tuyến Kết Nối CSDL Đám Mây Azure SQL"
        ]),
        # Phase 18
        ("Phase 18: REST API Client & Microsoft Graph Cloud (Day 511-540)", [
            "Tổng quan về REST API, JSON và giao thức HTTP/HTTPS trong Access", "Thư viện MSXML2.ServerXMLHTTP và WinHttp.WinHttpRequest.5.1 trong VBA", "Gửi HTTP GET Request từ Access VBA lấy dữ liệu thời tiết / tỷ giá",
            "Gửi HTTP POST Request kèm Body dữ liệu dạng JSON", "Gửi HTTP PUT, PATCH, DELETE để cập nhật dữ liệu trên Web Server", "Xử lý HTTP Headers: Content-Type, User-Agent, Accept",
            "Xác thực API: API Key, Basic Auth và Bearer Token", "Phân tích cú pháp chuỗi JSON (JSON Parsing) trong Access VBA không dùng thư viện ngoài", "Sử dụng thư viện VBA-JSON (JsonConverter) chuyển JSON thành Dictionary/Collection",
            "Tạo chuỗi JSON phức tạp từ dữ liệu bảng Access để gửi lên API", "Xử lý mã lỗi HTTP: 200 OK, 400 Bad Request, 401 Unauthorized, 404, 500", "Xử lý Rate Limit (HTTP 429) và cơ chế tự động thử lại Exponential Backoff",
            "Tích hợp API Cổng thanh toán (Momo, VNPay, ZaloPay, VietQR)", "Tự động sinh mã VietQR động chứa số tiền và nội dung đơn hàng lên Form", "Kiểm tra trạng thái thanh toán tự động qua Webhook / Polling API",
            "Tích hợp API Giao hàng (Giao Hàng Nhanh, Giao Hàng Tiết Kiệm, ViettelPost)", "Tự động đẩy đơn hàng sang đơn vị vận chuyển và lấy mã Tracking", "Tích hợp API Gửi tin nhắn SMS OTP / Zalo ZNS thông báo đơn hàng",
            "Tổng quan về Microsoft Graph API & Hệ sinh thái Microsoft 365", "Đăng ký ứng dụng trên Azure Portal (App Registration, Client ID, Client Secret)", "Xác thực OAuth2 qua Microsoft Identity Platform từ Access VBA",
            "Lấy Access Token và tự động Refresh Token khi hết hạn", "Đọc và Ghi dữ liệu vào SharePoint Online List từ Access qua Graph API", "Đọc và Tải file từ OneDrive / SharePoint Document Library về máy",
            "Gửi email HTML có đính kèm qua tài khoản Microsoft 365 (Graph API /sendMail)", "Tạo sự kiện lịch hẹn trên Outlook Calendar tự động", "Gửi tin nhắn thông báo vào kênh Microsoft Teams khi có đơn hàng mới",
            "Kích hoạt luồng tự động hóa Power Automate từ Access qua HTTP Request", "Đọc dữ liệu từ MS Forms đẩy tự động vào Access Database", "Project 18: Hệ Thống Bán Hàng Tự Động Tích Hợp VietQR, Vận Chuyển & MS Graph"
        ]),
        # Phase 19
        ("Phase 19: Inter-App Office Automation (Day 541-570)", [
            "Tổng quan về COM Automation (OLE Automation) giữa các ứng dụng Office", "Early Binding vs Late Binding: Ưu và nhược điểm khi triển khai", "Điều khiển Microsoft Excel từ Access: Khởi tạo Excel.Application ngầm",
            "Mở file Excel, đọc dữ liệu từng Sheet và ghi vào bảng Access", "Xuất dữ liệu Access sang file Excel có định dạng màu mè, công thức và biểu đồ", "Tự động tạo Báo cáo PivotTable trong Excel từ dữ liệu Access",
            "Xử lý file Excel dung lượng lớn 100.000 dòng bằng Mảng VBA cực nhanh", "Điều khiển Microsoft Word từ Access: Tạo hợp đồng và văn bản mẫu", "Kỹ thuật Mail Merge tự động: Điền thông tin khách hàng vào template Word",
            "Thay thế Bookmark và trích xuất bảng dữ liệu từ Access vào Word Table", "Xuất file Word sang định dạng PDF và ký điện tử tự động", "Điều khiển Microsoft Outlook từ Access: Tạo và gửi email tự động",
            "Gửi email hàng loạt cho 500 khách hàng với nội dung cá nhân hóa", "Đính kèm file hóa đơn PDF riêng biệt cho từng khách hàng", "Đọc email từ Outlook Inbox và tự động trích xuất file đính kèm vào Access",
            "Tạo Task công việc và Lịch hẹn trên Outlook từ đơn hàng cần giao", "Điều khiển Microsoft PowerPoint từ Access: Tự động tạo slide báo cáo", "Tạo biểu đồ và bảng số liệu trên PowerPoint từ câu truy vấn Access",
            "Điều khiển Adobe Acrobat Pro từ Access: Gộp nhiều file PDF thành một file duy nhất", "Tách trang PDF, đóng dấu mộc đỏ Watermark lên file PDF bằng VBA", "Trích xuất văn bản từ file PDF scan bằng công nghệ OCR",
            "Điều khiển phần mềm thiết kế AutoCAD từ Access: Đọc thông số bản vẽ", "Tự động gửi thông báo qua ứng dụng nhắn tin Telegram Bot từ Access", "Gửi file báo cáo tài chính vào nhóm Telegram của Ban Giám Đốc",
            "Xây dựng dịch vụ chạy ngầm Windows Service tương tác với Access", "Đóng và giải phóng toàn bộ tiến trình Office ngầm tránh rác bộ nhớ", "Xử lý xung đột phiên bản Office khác nhau giữa các máy trạm",
            "Đóng gói thư viện Class điều khiển bộ Office tái sử dụng", "Kiểm thử tự động hóa đa phần mềm dưới tải cao", "Project 19: Hệ Thống Tự Động Hóa Văn Phòng Đa Ứng Dụng (Excel - Word - Outlook - PDF - Telegram)"
        ]),
        # Phase 20
        ("Phase 20: Enterprise ERP/CRM Capstone Architecture (Day 571-600)", [
            "Tổng quan Kiến trúc Hệ thống ERP/CRM Doanh nghiệp Thu nhỏ (Mini-Enterprise System)", "Thiết kế CSDL Tổng thể: Khách hàng, Sản phẩm, Kho bãi, Mua hàng, Bán hàng, Tài chính, Nhân sự", "Module Quản lý Người dùng & Phân quyền bảo mật đa chi nhánh",
            "Module Danh mục dùng chung (Sản phẩm, Khách hàng, Nhà cung cấp, Bảng giá)", "Module Quản lý Mua hàng & Nhập kho (Đơn mua, Phiếu nhập, Công nợ NCC)", "Module Quản lý Bán hàng & Xuất kho (Báo giá, Đơn bán, Phiếu xuất, In hóa đơn)",
            "Module Quản lý Kho bãi nâng cao (Tồn kho tức thời, Cảnh báo tồn tối thiểu, Chuyển kho)", "Tính giá vốn hàng tồn kho tự động (Bình quân gia quyền & FIFO)", "Module Quản lý Thu - Chi & Sổ quỹ tiền mặt, Tiền gửi ngân hàng",
            "Module Quản lý Công nợ Phải thu & Phải trả (Theo dõi tuổi nợ, Nhắc nợ tự động)", "Module Nhân sự & Chấm công (Quẹt thẻ RFID, Tính lương tự động theo KPI)", "Tích hợp Máy quét mã vạch & In hóa đơn nhiệt K80 tại quầy thu ngân",
            "Tích hợp Thanh toán VietQR động và xác nhận tiền về qua API ngân hàng", "Tích hợp Đẩy đơn sang đơn vị vận chuyển GHN/ViettelPost", "Tích hợp Gửi email hóa đơn PDF tự động cho khách hàng qua Microsoft 365",
            "Tích hợp Gửi báo cáo doanh thu hàng ngày vào nhóm Telegram Ban Giám Đốc", "Hệ thống Báo cáo Quản trị: Dashboard KPI, Doanh thu, Lợi nhuận gộp, Biểu đồ tăng trưởng", "Báo cáo Phân tích Tài chính: Bảng cân đối kế toán, Báo cáo kết quả kinh doanh thu nhỏ",
            "Tối ưu hóa toàn bộ câu truy vấn SQL và Index đạt tốc độ phản hồi < 0.2 giây", "Kiểm thử chịu tải đa người dùng trong mạng LAN và Internet", "Đóng gói Backend lên CSDL Azure SQL đám mây bảo mật cao",
            "Đóng gói Frontend sang ACCDE có thanh Ribbon XML chuyên nghiệp", "Tích hợp Bộ cài đặt tự động Inno Setup và hệ thống Auto-Update phiên bản mới", "Tích hợp Hệ thống Khóa bản quyền License Key theo phần cứng máy tính",
            "Kiểm thử bảo mật chống SQL Injection, Brute Force và trích xuất dữ liệu trái phép", "Quy trình Đào tạo nhân viên và Chuyển giao phần mềm", "Quy trình Sao lưu dự phòng và Ứng phó thảm họa CSDL (Disaster Recovery)",
            "Tổng kết Toàn bộ Lộ trình: Đánh giá Năng lực Kỹ sư CSDL Access VBA Chuyên nghiệp", "Đồ án Tốt nghiệp: Triển khai Hệ thống Mini-ERP Toàn diện vào Doanh nghiệp Thực tế", "🏆 Master Graduation – Chứng Nhận Kiến Trúc Sư CSDL & Ứng Dụng Doanh Nghiệp Access VBA Master"
        ])
    ]

    for p_name, topics in phases_data:
        t_list = [(t, f"Thực hành chi tiết: {t}. Triển khai code VBA chuẩn mực, đo lường hiệu năng và xử lý ngoại lệ.", i == len(topics)-1) for i, t in enumerate(topics)]
        add_phase(current_day, p_name, t_list)
        current_day += len(topics)

    return roadmap

def generate_markdown(roadmap_data):
    md_lines = [
        "# 🗂️ Lộ Trình Học Access VBA – 600 Ngày (Từ Zero Đến Master Enterprise Architect)",
        "",
        "> **Mục tiêu**: Làm chủ toàn diện Microsoft Access VBA từ nút bấm đầu tiên đến Kiến trúc sư CSDL & Ứng dụng Doanh nghiệp cấp cao.",
        "> **Phạm vi**: 20 Phase, 600 Ngày, bao phủ RDBMS 1NF-3NF, SQL Jet/ACE, DAO/ADODB, Form/Report Engine, Multi-user Concurrency, Split Database, COM Port Hardware (Barcode/RFID/Scales), WinAPI, Ribbon XML, ODBC SQL Server/Azure, REST API & Microsoft Graph Cloud Integration.",
        "> **Ký hiệu thời gian**: 🟢 45 phút | 🟡 60 phút | 🟠 90 phút | 🔴 120 phút | 🚀 3 giờ (Dự án)",
        ""
    ]

    for day in range(1, len(roadmap_data) + 1):
        if day not in roadmap_data:
            continue
        title, phase, prev_topic, exercise, is_proj = roadmap_data[day]
        emoji, mins, label = get_time(day, is_proj)

        md_lines.append(f"## Day {day} — {title}")
        md_lines.append("**Prompt:**")
        md_lines.append(f"Đóng vai trò là Kỹ sư Trưởng CSDL & Giảng viên Cao cấp Access VBA. Hôm nay là Day {day}: {title}.")
        md_lines.append(f"Giai đoạn: {phase}.")
        md_lines.append(f"Chủ đề hôm qua: {prev_topic}.")
        md_lines.append("")
        md_lines.append("(⚠️ LỆNH TỐI THƯỢNG: KHÔNG giải thích dông dài lý thuyết cơ bản. Chỉ đi thẳng vào thực chiến. TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ nội dung để tôi tự đọc.)")
        md_lines.append("Yêu cầu:")
        md_lines.append(f"1. Giải thích rõ nguyên lý và bản chất của '{title}' với ví dụ code VBA Access thực tế, chuẩn clean code và chạy được ngay.")
        md_lines.append("2. Chỉ ra 2-3 lỗi thường gặp khi triển khai chủ đề này và cách debug/xử lý triệt để.")
        md_lines.append(f"3. Liên kết với '{prev_topic}' (hôm qua) — điểm nào hôm nay kế thừa và mở rộng.")
        md_lines.append(f"4. Giao bài tập mini từng bước nhỏ: {exercise}")
        md_lines.append("")
        md_lines.append("**Bài tập:**")
        md_lines.append(f"⏱️ **Thời gian ước tính:** {emoji} {label}")
        md_lines.append(f"📌 **Chủ đề hôm nay:** {title}")
        md_lines.append(f"🔗 **Ôn lại ngày trước:** {prev_topic}")
        md_lines.append(f"💻 **Tự thực hành:** {exercise}")
        md_lines.append("")
        md_lines.append(f"**Tags:** #access_vba #day{day} #vba #rdbms")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    content = "\n".join(md_lines)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    with open(filepath_600, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    data = build_access_roadmap()
    generate_markdown(data)
    print(f"Done! Generated {len(data)} days to {filepath} and {filepath_600}")
