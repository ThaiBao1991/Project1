"""Generate Excel VBA Roadmap - 1,000 Days (Master Spreadsheet Computing & AI System Integrator).

Covers 33 Phases: Range/Sheet/Workbook Model, High-Speed 2D Arrays, WinAPI Memory Pointers,
Dictionary/Sorting Algorithms, Modern Flat UI UserForms, Pivot & Power Pivot DAX, Power Query M-code,
Real-time Dashboards, Financial Modeling (DCF/Monte Carlo/Solver), Hardware COM Ports, Web Scraping,
REST API/OAuth2, Commercial Add-ins (.xlam), Ribbon XML, and Generative AI Async UDFs.
"""

import os

filepath = os.path.join(os.path.dirname(__file__), "roadmap_excel_vba_365.md")
# Also support 1000-day specific filename
filepath_1000 = os.path.join(os.path.dirname(__file__), "roadmap_excel_vba_1000.md")

def get_time(day_num, is_project=False):
    if is_project:
        return ("🚀", 210, "Dự án Tự động hóa & Add-in — 3.5 tiếng")
    if day_num <= 60:
        return ("🟢", 30, "Nền tảng Bảng tính & Cú pháp — 30 phút")
    elif day_num <= 200:
        return ("🟡", 60, "Range Mastery, Events & UI — 60 phút")
    elif day_num <= 500:
        return ("🟠", 90, "Mảng 2D, Thuật toán & Pivot — 90 phút")
    elif day_num <= 800:
        return ("🔴", 120, "Tài chính, WinAPI, Scraping & COM — 120 phút")
    else:
        return ("🔥", 150, "Add-in Ribbon, Cloud & AI Master — 150 phút")

def build_excel_roadmap():
    roadmap = {}

    def add_phase(start_day, phase_name, topics):
        prev_topic = "Bắt đầu hành trình" if start_day == 1 else roadmap[start_day - 1][0]
        for i, t in enumerate(topics):
            day = start_day + i
            title, exercise, is_proj = t
            roadmap[day] = (title, phase_name, prev_topic, exercise, is_proj)
            prev_topic = title

    # Define all 33 phases with rich, distinct, step-by-step topics
    phases_def = [
        # Phase 1
        ("Phase 1: Macro Recorder, VBE & VBA Foundation (Day 1-30)", [
            "Macro Recorder – Ghi macro tự động", "Khám phá VBE (Visual Basic Editor)", "Sub & Procedure – Khởi tạo thủ tục đầu tiên",
            "Biến (Variables) & Data Types cơ bản", "Hằng số (Constants) & Tầm vực biến (Scope)", "Option Explicit – Bắt buộc khai báo biến",
            "Toán tử toán học và logic trong VBA", "Lệnh rẽ nhánh If...Then...Else cơ bản", "Lệnh rẽ nhánh Select Case",
            "Vòng lặp For...Next cơ bản", "Vòng lặp For Each...Next trên Sheets", "Vòng lặp Do While...Loop",
            "Vòng lặp Do Until...Loop", "Thoát vòng lặp an toàn (Exit For, Exit Do)", "Function – Hàm tự tạo cơ bản",
            "Truyền tham số ByVal vs ByRef", "Tham số tùy chọn Optional Arguments", "Tham số mảng động ParamArray",
            "Hộp thoại InputBox nhập dữ liệu", "Hộp thoại MsgBox bắt sự kiện nút bấm", "Xử lý chuỗi: Left, Right, Mid, Len, InStr",
            "Xử lý ngày tháng: Date, DateAdd, DateDiff, Format", "Xử lý số học: Round, Int, Abs, Rnd", "Kiểu dữ liệu Variant – Cạm bẫy & Ứng dụng",
            "Ghi chú (Comments) & Chuẩn Clean Code", "Gọi Sub từ Sub khác (Call Statement)", "Gán Macro vào phím tắt và Quick Access Toolbar",
            "Tạo nút bấm (Button/Shape) gán Macro trên Sheet", "Bảo mật mã nguồn VBA (Password Protect)", "Project 1: Ứng dụng Bảng tính Lương Cơ bản"
        ]),
        # Phase 2
        ("Phase 2: Variables, Data Types & Memory Basics (Day 31-60)", [
            "Kiểu dữ liệu nguyên thủy: Byte, Integer, Long, LongLong", "Kiểu dữ liệu số thực: Single, Double, Currency, Decimal",
            "Kiểu dữ liệu chuỗi: String cố định vs String động", "Kiểu dữ liệu Boolean và xử lý cờ hiệu (Flags)",
            "Kiểu dữ liệu Date & Time – Bản chất số thực đằng sau", "Kiểu dữ liệu Object và quy tắc Set = Nothing",
            "Hàm kiểm tra kiểu: IsNumeric, IsDate, IsEmpty, IsNull", "Ép kiểu dữ liệu: CInt, CLng, CDbl, CStr, CDate",
            "Hằng số hệ thống và Enum tự định nghĩa", "Biến tĩnh (Static Variables) trong thủ tục",
            "Biến Private vs Public trong Module", "Biến Global trong toàn bộ Workbook",
            "Kiểu dữ liệu tự định nghĩa (User-Defined Types - Type...End Type)", "Mảng lồng trong User-Defined Types",
            "Quản lý bộ nhớ Stack vs Heap trong VBA", "Cạm bẫy tràn số (Overflow Error 6) với Integer",
            "Xử lý số tiền tệ siêu lớn bằng Currency và Decimal", "Tối ưu hóa kiểu dữ liệu để tăng tốc độ tính toán",
            "Làm việc với kiểu dữ liệu Null và chuỗi rỗng vbNullString", "Khai báo nhiều biến trên một dòng và lỗi thường gặp",
            "Bảo toàn giá trị biến giữa các lần chạy macro", "Đo lường dung lượng RAM tiêu thụ của các kiểu biến",
            "Khởi tạo giá trị mặc định cho biến và Struct", "Kỹ thuật tái sử dụng biến để tiết kiệm tài nguyên",
            "Debug giá trị biến trong Locals Window", "Debug giá trị biến trong Watch Window",
            "In giá trị biến trực tiếp ra Immediate Window (?var)", "Tạo Module chứa toàn bộ hằng số và cấu hình chung",
            "Xây dựng thư viện hàm chuyển đổi kiểu dữ liệu an toàn", "Project 2: Module Quản Lý Cấu Hình & Biến Hệ Thống Toàn Diện"
        ]),
        # Phase 3
        ("Phase 3: Control Flow – Advanced Conditions & Loops (Day 61-90)", [
            "Lệnh If...ElseIf nhiều tầng và cách tối ưu thứ tự điều kiện", "Toán tử logic lồng nhau: AND, OR, XOR, NOT, Eqv, Imp",
            "Toán tử Like và so khớp mẫu ký tự đại diện (*, ?, #, [a-z])", "Select Case với dải giá trị (Case 1 To 10, Case Is > 50)",
            "Select Case với chuỗi và danh sách phân cách bởi dấu phẩy", "Lồng ghép Select Case trong vòng lặp For",
            "Vòng lặp For lồng nhau (Nested For Loops) duyệt ma trận 2D", "Tối ưu hóa bước nhảy Step trong vòng lặp For (Step 2, Step -1)",
            "Duyệt ngược từ dưới lên trên (For i = LastRow To 1 Step -1) khi xóa dòng", "Vòng lặp Do Loop với điều kiện đặt ở đầu vs ở cuối",
            "Tránh bẫy vòng lặp vô tận (Infinite Loop) và nút dừng khẩn cấp Ctrl+Break", "Vòng lặp For Each duyệt qua Range các ô được chọn",
            "Vòng lặp For Each duyệt qua Shapes, Charts, Comments trên Sheet", "So sánh hiệu năng: For i = 1 To N vs For Each",
            "Lệnh GoTo – Khi nào nên dùng và tại sao nên tránh Spaghetti code", "Lệnh On...GoTo và On...GoSub chuyển hướng theo chỉ số",
            "Lệnh With...End With rút gọn truy cập Object và tăng tốc code", "With lồng nhau (Nested With) và các quy tắc cần nhớ",
            "Lệnh End, Stop và Exit Sub / Exit Function", "Cơ chế đánh giá điều kiện ngắn (Short-Circuit Evaluation) giả lập trong VBA",
            "Xây dựng máy trạng thái hữu hạn (State Machine) bằng Select Case", "Xử lý các bài toán logic phức tạp: Kiểm tra năm nhuận, tính thứ trong tuần",
            "Lọc dữ liệu đa điều kiện trong vòng lặp", "Gộp nhóm và tính tổng con trong vòng lặp duyệt hàng",
            "Phát hiện và đánh dấu các dòng trùng lặp bằng vòng lặp", "Tách dữ liệu từ 1 bảng thành nhiều bảng con theo điều kiện",
            "Duyệt qua danh sách file trong thư mục bằng vòng lặp Dir()", "Duyệt cây thư mục đệ quy (Recursive Loop)",
            "Tối ưu hóa vòng lặp lớn: Hạn chế tương tác trực tiếp với Cell", "Project 3: Thuật Toán Phân Loại & Xử Lý Hồ Sơ Khách Hàng Tự Động"
        ]),
        # Phase 4
        ("Phase 4: Procedures, Functions & Error Handling (Day 91-120)", [
            "Kiến trúc hàm Sub và Function chuẩn mực", "Quy tắc đặt tên hàm và tham số theo chuẩn công nghiệp",
            "Hàm tự tạo (UDF – User Defined Function) dùng trong công thức Excel", "Thuộc tính Application.Volatile – Khi nào nên bật?",
            "Thêm mô tả và danh mục cho UDF trong bảng Insert Function", "Hàm UDF trả về một mảng kết quả (Array Formula UDF)",
            "Hàm UDF nhận tham số là Range nhiều ô", "Xử lý tham số Range rỗng hoặc lỗi #VALUE! trong UDF",
            "Debug hàm UDF khi được gọi từ công thức bảng tính", "Đệ quy (Recursion) trong VBA: Tính giai thừa, dãy Fibonacci",
            "Đệ quy duyệt cây tổ chức nhân sự (Org Chart)", "Giới hạn độ sâu Stack đệ quy và bẫy tràn bộ nhớ Out of Stack Space",
            "Bản chất của bẫy lỗi: Khối On Error GoTo [Label]", "Lệnh On Error Resume Next – Lợi ích và hiểm họa khôn lường",
            "Lệnh On Error GoTo 0 – Đặt lại bộ xử lý lỗi mặc định", "Lệnh On Error GoTo -1 – Xóa trạng thái lỗi trong bộ nhớ",
            "Đối tượng Err: Err.Number, Err.Description, Err.Source", "Chủ động phát sinh lỗi bằng Err.Raise để kiểm tra",
            "Tự định nghĩa mã lỗi nghiệp vụ riêng cho ứng dụng", "Xây dựng hàm xử lý lỗi tập trung (Centralized Error Handler)",
            "Ghi log lỗi ra file text bên ngoài kèm Timestamp và tên máy tính", "Xử lý lỗi khi mở file không tồn tại hoặc bị khóa quyền",
            "Xử lý lỗi chia cho 0 (#DIV/0!) và lỗi tràn bộ nhớ", "Bảo vệ ứng dụng không bị Crash trước người dùng cuối",
            "Khôi phục trạng thái hệ thống khi xảy ra lỗi (ScreenUpdating, Events, Calculation)",
            "Cấu trúc Sub/Function mẫu chuẩn Enterprise (Production-Ready Template)",
            "Kỹ thuật kiểm thử đơn vị (Unit Testing) cho các hàm VBA cốt lõi",
            "Viết bộ Test Runner tự động kiểm tra 50 hàm tiện ích",
            "Đo lường thời gian chạy từng thủ tục bằng Timer", "Project 4: Thư Viện Tiện Ích Độc Lập Kèm Hệ Thống Bẫy Lỗi & Unit Test"
        ]),
        # Phase 5
        ("Phase 5: Workbook & Worksheet Object Model (Day 121-150)", [
            "Kiến trúc phân cấp đối tượng Excel: Application -> Workbooks -> Worksheets", "Đối tượng ThisWorkbook vs ActiveWorkbook",
            "Tạo mới Workbook: Workbooks.Add", "Mở Workbook: Workbooks.Open với các tham số ReadOnly, Password",
            "Lưu Workbook: Save, SaveAs, SaveCopyAs các định dạng .xlsx, .xlsm, .csv, .pdf", "Đóng Workbook an toàn: Close SaveChanges:=True/False",
            "Kiểm tra Workbook có đang mở hay không trước khi thao tác", "Duyệt qua toàn bộ Workbooks đang mở trong ứng dụng",
            "Đối tượng Sheets vs Worksheets (Phân biệt Worksheet và Chart Sheet)", "Tham chiếu Sheet theo Tên, Chỉ số Index và CodeName (VBE Name)",
            "Tại sao chuyên gia luôn dùng CodeName (Sheet1) thay vì Tên hiển thị?", "Tạo mới Worksheet: Worksheets.Add Before/After",
            "Đổi tên Worksheet an toàn (Bắt lỗi tên trùng, ký tự cấm: \\, /, ?, *, [, ])", "Xóa Worksheet không hiện cảnh báo (DisplayAlerts = False)",
            "Di chuyển và Sao chép Worksheet: Move, Copy sang Workbook khác", "Ẩn Sheet (xlSheetHidden) vs Siêu Ẩn (xlSheetVeryHidden)",
            "Bảo vệ Sheet bằng mật khẩu (Protect / Unprotect)", "Cho phép chỉnh sửa một số vùng nhất định khi Sheet bị khóa",
            "Bảo vệ cấu trúc Workbook (Protect Structure)", "Duyệt qua toàn bộ Worksheets trong Workbook và tổng hợp dữ liệu",
            "Gộp 20 Worksheets thành 1 bảng tổng hợp duy nhất", "Tách 1 bảng tổng hợp thành 20 Worksheets theo phòng ban",
            "Đọc và Ghi thuộc tính tài liệu (BuiltinDocumentProperties & CustomDocumentProperties)", "Xóa toàn bộ siêu dữ liệu cá nhân (Personal Information) trước khi gửi file",
            "Tùy biến chế độ xem: View, Zoom, FreezePanes (Cố định dòng/cột)", "Tùy biến hiển thị: Gridlines, Headings, FormulaBar, ScrollBars",
            "Xử lý in ấn trang tính: PageSetup, Orientation, PaperSize, PrintArea, FitToPages", "Thiết lập Header & Footer động bằng mã VBA",
            "Xuất Worksheet sang file PDF chất lượng cao", "Project 5: Hệ Thống Tự Động Hóa Quản Lý & Phân Tách Báo Cáo Đa Sheet"
        ]),
        # Phase 6
        ("Phase 6: Range & Cells Deep Dive – Navigation, Resize & Offset (Day 151-180)", [
            "Đối tượng Range: Các cách tham chiếu Range('A1'), Range('A1:C10'), Range('A:A')", "Thuộc tính Cells(Row, Column) – Ưu thế vượt trội khi dùng trong vòng lặp",
            "Kết hợp Range và Cells: Range(Cells(1, 1), Cells(10, 5))", "Thuộc tính Offset(RowOffset, ColumnOffset) – Di chuyển vùng chọn linh hoạt",
            "Thuộc tính Resize(RowSize, ColumnSize) – Co giãn kích thước vùng chọn", "Kết hợp Offset và Resize để bóc tách khối dữ liệu",
            "Tìm dòng cuối cùng có dữ liệu: Cells(Rows.Count, 'A').End(xlUp).Row", "Tìm cột cuối cùng có dữ liệu: Cells(1, Columns.Count).End(xlToLeft).Column",
            "Tại sao End(xlUp) an toàn hơn UsedRange khi tìm dòng cuối?", "Thuộc tính UsedRange: Bản chất, cạm bẫy ô rỗng có định dạng và cách reset",
            "Thuộc tính CurrentRegion: Bắt trọn khối bảng dữ liệu bao quanh bởi dòng/cột trống", "Tự động xác định Header và Data Region bằng CurrentRegion",
            "Đọc và Ghi giá trị đơn lẻ: Range.Value vs Range.Value2 vs Range.Text", "Tại sao Range.Value2 chạy nhanh hơn Range.Value khi xử lý Date/Currency?",
            "Đọc và Ghi công thức: Range.Formula, Range.FormulaR1C1, Range.Formula2 (Dynamic Array)", "Sao chép vùng dữ liệu: Range.Copy và PasteSpecial (Values, Formats, Transpose)",
            "Gán giá trị trực tiếp không qua Clipboard: Range('B1:B100').Value = Range('A1:A100').Value", "Xóa dữ liệu: Clear, ClearContents, ClearFormats, ClearComments",
            "Chèn và Xóa dòng/cột: EntireRow.Insert, EntireColumn.Delete", "Ẩn / Hiện dòng và cột: EntireRow.Hidden = True/False",
            "Chỉnh độ rộng cột và chiều cao dòng: ColumnWidth, RowHeight, AutoFit", "Làm việc với ô bị trộn (Merged Cells): MergeCells, Merge, UnMerge",
            "Phát hiện ô Merge, bỏ Merge và tự động điền lại giá trị (Fill Blanks)", "Duyệt qua từng ô trong Range lớn một cách tối ưu",
            "Chuyển đổi địa chỉ Range: Address, Address(False, False) bỏ dấu $", "Lấy số dòng và số cột của một Range: Range.Rows.Count, Range.Columns.Count",
            "Lấy danh sách các ô giao nhau: Application.Intersect", "Lấy hợp của nhiều vùng dữ liệu: Application.Union",
            "So sánh 2 Range và tìm ra các điểm khác biệt", "Project 6: Bộ Công Cụ Thao Tác & Chuẩn Hóa Cấu Trúc Bảng Tính Tự Động"
        ]),
        # Phase 7
        ("Phase 7: SpecialCells, Areas & Data Boundaries (Day 181-210)", [
            "Thuộc tính SpecialCells: Sức mạnh tiềm ẩn xử lý bảng tính lớn", "SpecialCells(xlCellTypeConstants): Chọn tất cả ô chứa giá trị cố định",
            "SpecialCells(xlCellTypeFormulas): Chọn tất cả ô chứa công thức", "SpecialCells(xlCellTypeBlanks): Chọn tất cả ô trống trong bảng",
            "Điền giá trị từ ô phía trên vào các ô trống (Fill Blanks down) trong 1 dòng lệnh", "SpecialCells(xlCellTypeVisible): Chỉ chọn các dòng đang hiển thị sau khi lọc",
            "Copy chỉ các dòng hiển thị sau khi Filter sang Sheet mới", "SpecialCells(xlCellTypeLastCell): Ô cuối cùng của trang tính",
            "SpecialCells(xlCellTypeSameValidation): Tìm các ô có cùng quy tắc Data Validation", "SpecialCells(xlCellTypeSameFormatConditions): Tìm các ô có cùng Conditional Formatting",
            "SpecialCells(xlCellTypeComments): Chọn tất cả ô có chú thích", "Xử lý lỗi Error 1004 khi SpecialCells không tìm thấy ô nào thỏa mãn",
            "Thuộc tính Areas Collection: Khi Range bao gồm nhiều vùng không liền kề", "Duyệt qua từng Area trong một Range ngắt quãng",
            "Đếm số lượng Area và tổng số ô trong các Area", "Chuyển đổi Range nhiều Area thành mảng 1 chiều liên tục",
            "Tự động xóa tất cả các dòng bị ẩn trong bảng tính lớn", "Tự động tô màu các ô chứa công thức bị lỗi (#N/A, #VALUE!, #REF!)",
            "Tự động khóa (Locked = True) chỉ các ô chứa công thức", "Phân tích cấu trúc bảng tính: Đếm tỷ lệ ô giá trị vs ô công thức",
            "Tìm kiếm nâng cao bằng Range.Find: What, After, LookIn, LookAt, SearchOrder", "Tham số LookIn: xlValues, xlFormulas, xlComments",
            "Tham số LookAt: xlWhole (Toàn bộ ô) vs xlPart (Một phần ô)", "Tìm kiếm liên tục bằng FindNext và FindPrevious trong vòng lặp",
            "Bắt điểm dừng của vòng lặp FindNext bằng địa chỉ ô đầu tiên", "Thay thế hàng loạt bằng Range.Replace: Tối ưu tốc độ gấp 100 lần vòng lặp",
            "Sắp xếp dữ liệu bằng Range.Sort: Sắp xếp đa cột (Key1, Key2, Key3)", "Sắp xếp theo thứ tự tùy biến (Custom List Sort: Thứ 2, Thứ 3...)",
            "Lọc tự động bằng Range.AutoFilter: Lọc đơn cột, đa cột, lọc theo màu sắc", "Project 7: Hệ Thống Dọn Dẹp, Làm Sạch & Sắp Xếp Dữ Liệu Bảng Tính Siêu Tốc"
        ]),
        # Phase 8
        ("Phase 8: Formatting, Borders, Colors & Number Formats (Day 211-240)", [
            "Định dạng Font chữ: Name, Size, Bold, Italic, Underline, Strikethrough", "Định dạng Màu chữ và Màu nền: ColorIndex vs RGB(R, G, B)",
            "Sử dụng bảng màu ThemeColors trong Microsoft Excel", "Tạo hiệu ứng Gradient chuyển màu cho ô bảng tính",
            "Định dạng Khung viền (Borders): BorderAround, Borders(xlEdgeBottom)...", "Cấu hình LineStyle, Weight (xlThin, xlMedium, xlThick) và Color của Border",
            "Định dạng Căn lề: HorizontalAlignment (Trái, Phải, Giữa), VerticalAlignment", "Thuộc tính WrapText (Tự xuống dòng) và Orientation (Xoay chữ góc nghiêng)",
            "Thuộc tính ShrinkToFit (Tự co chữ vừa ô) và IndentLevel (Thụt lề đầu dòng)", "Định dạng Số (NumberFormat): Cú pháp chuẩn 4 phần (Dương; Âm; Không; Văn bản)",
            "Định dạng Tiền tệ chuẩn Việt Nam Đồng: '#,##0 \"₫\"' và Đô la Mỹ: '$#,##0.00'", "Định dạng Ngày tháng: 'dd/mm/yyyy hh:mm:ss' và định dạng Thứ trong tuần",
            "Định dạng Tỷ lệ phần trăm: '0.00%' và định dạng Phân số", "Định dạng Số điện thoại, CCCD và Mã số thuế có số 0 ở đầu",
            "Định dạng Ẩn nội dung ô bằng cú pháp NumberFormat = ';;;'", "Định dạng Số đổi màu tự động: '[Green]#,##0;[Red]-#,##0;\"-\"'",
            "Conditional Formatting cơ bản: Thêm quy tắc tô màu ô lớn hơn/nhỏ hơn", "Conditional Formatting nâng cao: Dùng công thức VBA (FormatConditions.Add)",
            "Tô màu xen kẽ các dòng (Zebra Striping) bằng Conditional Formatting", "Tạo thanh dữ liệu (Data Bars) và thang màu (Color Scales) bằng VBA",
            "Tạo bộ biểu tượng (Icon Sets: Mũi tên, Đèn giao thông, Cờ) bằng VBA", "Xóa và Quản lý tất cả quy tắc Conditional Formatting trên Sheet",
            "Tạo Dropdown Danh sách (Data Validation List) bằng mã lệnh VBA", "Xác thực số nguyên, số thực, ngày tháng bằng Data Validation",
            "Tạo thông báo lỗi tùy biến khi người dùng nhập sai quy tắc Validation", "Tự động kẻ bảng và format tiêu đề theo chuẩn thiết kế hiện đại",
            "Tạo bảng mẫu (Template Theme) chuyển đổi qua lại giữa Dark Mode và Light Mode", "Sao chép toàn bộ định dạng từ ô mẫu sang vùng dữ liệu (PasteSpecial xlPasteFormats)",
            "Xóa sạch định dạng rác làm phình dung lượng file Excel", "Project 8: Trình Tạo Báo Cáo Tài Chính Chuẩn Mực Có Format Chuyên Nghiệp"
        ]),
        # Phase 9
        ("Phase 9: Formulas, Evaluation & Dynamic Named Ranges (Day 241-270)", [
            "Gán công thức Excel từ VBA: Range.Formula vs Range.FormulaR1C1", "Cú pháp R1C1: Tham chiếu tuyệt đối R1C1 vs Tham chiếu tương đối R[-1]C[1]",
            "Tại sao FormulaR1C1 cực kỳ mạnh mẽ khi gán công thức cho hàng nghìn dòng?", "Gán công thức mảng động (Dynamic Array Formulas) với Range.Formula2",
            "Chuyển toàn bộ công thức thành giá trị cố định (Formula to Values) siêu tốc", "Phương thức Application.Evaluate và ký hiệu tắt [A1:B10]",
            "Sử dụng Evaluate để tính toán biểu thức toán học dạng chuỗi '15 * (20 + 4)'", "Sử dụng Evaluate để lọc và biến đổi mảng không cần vòng lặp",
            "Quản lý Tên vùng dữ liệu (Names / Defined Names) trong VBA", "Tạo Named Range tĩnh: Names.Add Name:='BangGia', RefersTo:='=Sheet1!$A$1:$D$100'",
            "Tạo Dynamic Named Range tự co giãn bằng hàm OFFSET và COUNTA", "Tạo Dynamic Named Range bằng hàm INDEX",
            "Tầm vực của Name: Scope cấp Workbook vs Scope cấp Worksheet", "Duyệt danh sách toàn bộ Names trong Workbook và phát hiện Name bị lỗi (#REF!)",
            "Xóa sạch các Name rác bị lỗi ẩn trong file Excel", "Đọc giá trị từ Named Range trong mã VBA không cần biết địa chỉ ô",
            "Sử dụng các hàm Excel Worksheet trong VBA: Application.WorksheetFunction", "Phân biệt Application.VLookup vs Application.WorksheetFunction.VLookup khi có lỗi",
            "Bắt lỗi không tìm thấy (#N/A) khi dùng hàm tra cứu qua IsError", "Sử dụng XLOOKUP, XMATCH, FILTER, UNIQUE, SORT trong VBA (Excel 365)",
            "Tạo hàm Lambda tùy biến và lưu vào Name Manager bằng VBA", "Kiểm soát chế độ tính toán của Excel: Application.Calculation",
            "Chuyển sang chế độ tính toán thủ công: xlCalculationManual khi chạy macro lớn", "Kích hoạt tính toán lại: Calculate, Sheet.Calculate, Range.Calculate",
            "Tính toán ma trận: MMULT, TRANSPOSE, MINVERSE qua Evaluate", "Tự động phân tích và sửa lỗi phụ thuộc vòng tròn (Circular Reference)",
            "Theo dõi dấu vết công thức: ShowPrecedents, ShowDependents, TracePrecedents", "Xóa dấu vết mũi tên công thức: Sheet.ClearArrows",
            "Tự động audit công thức tính toán và phát hiện ô sai quy luật", "Project 9: Công Cụ Audit Công Thức & Quản Lý Dynamic Names Tự Động"
        ]),
        # Phase 10
        ("Phase 10: High-Performance 1D & 2D Variant Arrays (Day 271-300)", [
            "Tại sao thao tác Cell-by-Cell làm đơ máy? Triết lý làm việc trong RAM", "Nạp toàn bộ Range 100.000 dòng vào Mảng Variant: arr = Range('A1:Z100000').Value2",
            "Cấu trúc của Mảng 2 chiều sinh ra từ Range (Luôn bắt đầu từ Base 1: arr(1 To N, 1 To M))", "Khai báo Mảng tĩnh (Static Array) vs Mảng động (Dynamic Array)",
            "Định cỡ lại mảng bằng lệnh ReDim", "Bảo toàn dữ liệu cũ khi đổi kích thước: ReDim Preserve (Chỉ đổi được chiều cuối cùng)",
            "Lấy giới hạn dưới và giới hạn trên của mảng: LBound(arr, dimension), UBound(arr, dimension)", "Duyệt qua mảng 2 chiều bằng 2 vòng lặp For lồng nhau trong RAM",
            "Tính toán, lọc và xử lý dữ liệu hoàn toàn trên mảng RAM", "Ghi toàn bộ mảng kết quả ngược lại Range trong 0.05 giây: Range.Resize = arrResult",
            "Kỹ thuật chuyển đổi Mảng 1 chiều thành Mảng 2 chiều và ngược lại", "Hàm Application.Transpose: Lợi ích và giới hạn 65.536 dòng",
            "Tự viết hàm Custom Transpose không bị giới hạn số dòng của Excel", "Xóa mảng và giải phóng bộ nhớ RAM với lệnh Erase arr",
            "Kiểm tra mảng đã được khởi tạo hay chưa (Safe Array Allocated Check)", "Hàm Split: Tách chuỗi thành mảng 1 chiều (Base 0)",
            "Hàm Join: Ghép mảng 1 chiều thành chuỗi phân cách bởi ký tự", "Hàm Filter: Lọc nhanh các phần tử trong mảng chuỗi 1 chiều",
            "Gộp 2 mảng thành 1 mảng lớn trong bộ nhớ", "Trích xuất 1 cột bất kỳ từ mảng 2 chiều thành mảng 1 chiều",
            "Trích xuất 1 hàng bất kỳ từ mảng 2 chiều", "Thêm cột mới hoặc thêm dòng mới vào mảng 2 chiều",
            "Xóa dòng hoặc xóa cột thỏa mãn điều kiện khỏi mảng", "Xử lý dữ liệu đa kiểu (Text, Date, Number, Null) an toàn trong mảng Variant",
            "Đo tốc độ thực thi: Xử lý 100.000 dòng bằng Mảng (0.2s) vs bằng Cell (45s)", "Quy tắc vàng thiết kế code VBA tốc độ cao đạt chuẩn 60fps",
            "Quản lý dung lượng bộ nhớ khi làm việc với mảng chứa hàng triệu phần tử", "Xử lý bài toán gộp 50 file Excel vào 1 mảng duy nhất trước khi ghi ra sheet",
            "Kỹ thuật phân trang dữ liệu (Paging) trên mảng RAM", "Project 10: Động Cơ Xử Lý & Tổng Hợp 500.000 Dòng Dữ Liệu Trong 1 Giây"
        ])
    ]

    # Generate remaining phases 11 to 33 programmatically with extreme domain depth
    remaining_phases = [
        ("Phase 11: Memory Management, SafeArray & WinAPI Pointers (Day 301-330)", "Kỹ thuật con trỏ bộ nhớ CopyMemory (RtlMoveMemory), cấu trúc SafeArray, phân tích layout bộ nhớ VBA và tối ưu hóa zero-copy array slicing."),
        ("Phase 12: Data Structures – Dictionary, Collection & ArrayList (Day 331-360)", "Làm chủ Scripting.Dictionary, System.Collections.ArrayList, Collection, Stack, Queue, Hash Table và kỹ thuật nhóm dữ liệu đa cấp (Multi-level Grouping)."),
        ("Phase 13: Sorting & Searching Algorithms in VBA (Day 361-390)", "Tự cài đặt QuickSort 2D đa cột, MergeSort, HeapSort, Binary Search, Radix Sort và so sánh độ phức tạp O(n log n) trên bảng tính lớn."),
        ("Phase 14: Regular Expressions & Text Mining (Day 391-420)", "VBScript.RegExp chuyên sâu: Regex Pattern, Grouping, Lookahead, Lookbehind, trích xuất số điện thoại, email, MST, bóc tách hóa đơn và văn bản thô."),
        ("Phase 15: Event-Driven Programming – Sheet & Workbook Events (Day 421-450)", "Worksheet_Change, SelectionChange, BeforeDoubleClick, Workbook_Open, SheetChange, EnableEvents, bẫy vòng lặp sự kiện vô hạn và hệ thống Audit Trail."),
        ("Phase 16: Application Events & Class Module Architecture (Day 451-480)", "Tạo Class Module, WithEvents Application level, bắt sự kiện mở bất kỳ file nào, bắt sự kiện chuyển Workbook và xây dựng Event Listener Framework."),
        ("Phase 17: UserForm Foundation & Standard Controls (Day 481-510)", "Thiết kế UserForm, TextBox, ComboBox, ListBox đa cột, OptionButton, CheckBox, Frame, MultiPage, Form_Initialize, Validate dữ liệu và CRUD vào bảng."),
        ("Phase 18: Advanced UserForms – Modern Flat Dark/Light UI (Day 511-540)", "Thiết kế giao diện phẳng hiện đại (Modern Flat UI), Dark Mode / Light Mode, Gradient, bo tròn góc, Custom Icon, Animation trượt mượt mà trên UserForm."),
        ("Phase 19: Dynamic Controls & WithEvents Control Collections (Day 541-570)", "Khởi tạo controls động trong lúc chạy (Dynamic Runtime Controls), Class Module quản lý hàng loạt nút bấm với 1 sự kiện duy nhất, TreeView & Grid tự viết."),
        ("Phase 20: PivotTable & PivotChart Automation from VBA (Day 571-600)", "Tạo PivotCache, PivotTable, RowFields, ColumnFields, DataFields (xlSum, xlAverage), Calculated Fields, Grouping theo Ngày/Tháng và làm mới tự động."),
        ("Phase 21: Data Model, Slicers & Power Pivot DAX (Day 601-630)", "Tạo quan hệ trong Data Model (Power Pivot), tự động hóa Slicers & Timelines, viết biểu thức DAX từ VBA và truy vấn mô hình dữ liệu đa triệu dòng."),
        ("Phase 22: Power Query (M Code) Automation & ETL Pipeline (Day 631-660)", "Tự động sinh mã M Code từ VBA, kết nối API/Web/Folder qua Power Query, tự động Refresh BackgroundQuery=False và xử lý lỗi ETL tự động."),
        ("Phase 23: Advanced Charting Engine, Shapes & Canvas (Day 661-690)", "Tự động vẽ biểu đồ chuyên nghiệp (Gantt, Waterfall, Pareto, Gauge Meter), điều khiển Shape Canvas, SVG rendering và bắt sự kiện Chart Event."),
        ("Phase 24: Interactive Real-Time Dashboards & Visualizations (Day 691-720)", "Xây dựng Dashboard động thời gian thực: KPI Cards, biểu đồ tương tác khi click, bộ lọc động và xuất Dashboard sang ảnh/PDF chất lượng cao."),
        ("Phase 25: Financial Modeling – Cash Flow, DCF, NPV & IRR (Day 721-750)", "Xây dựng mô hình tài chính doanh nghiệp: Dự báo dòng tiền (Cash Flow), Định giá chiết khấu DCF, NPV, IRR, Lịch biểu khấu hao và Báo cáo tài chính."),
        ("Phase 26: What-If Analysis, Data Tables, Goal Seek & Solver (Day 751-780)", "Tự động hóa công cụ phân tích độ nhạy Data Tables, Goal Seek, thư viện Solver (SolverSolve, SolverAdd) giải bài toán tối ưu hóa chi phí sản xuất."),
        ("Phase 27: Monte Carlo Simulation & Risk Analysis (Day 781-810)", "Mô phỏng ngẫu nhiên Monte Carlo 100.000 kịch bản trong RAM, phân phối chuẩn Box-Muller, tính Value at Risk (VaR) và phân tích rủi ro danh mục đầu tư."),
        ("Phase 28: Hardware Interfacing – Serial COM Port RS232, PLC & Sensors (Day 811-840)", "Giao tiếp cổng COM phần cứng (RS232/USB Virtual COM) qua WinAPI/MSComm, đọc máy quét mã vạch, cân điện tử, cảm biến IoT, PLC Modbus RTU."),
        ("Phase 29: Windows API – GDI, Subclassing, Registry & Multi-threading (Day 841-870)", "Can thiệp Windows sâu: GDI vẽ giao diện, Subclassing cửa sổ Excel, đọc/ghi Registry, System Tray Icon và kỹ thuật giả lập Multi-threading qua PowerShell/DLL."),
        ("Phase 30: Web Scraping – Selenium & Chrome DevTools Protocol (Day 871-900)", "Cào dữ liệu web tự động: Selenium WebDriver, Chrome DevTools Protocol (CDP), MSXML/WinHttp, phân tích DOM HTML, vượt CAPTCHA và đăng nhập tự động."),
        ("Phase 31: REST API, OAuth2, Webhooks & Office Interop (Day 901-930)", "Gọi REST API (GET/POST/PUT/DELETE), OAuth2 Access Token, Webhook, tự động hóa liên ứng dụng (Word, PowerPoint, Outlook, Access, PDF Acrobat, AutoCAD)."),
        ("Phase 32: Commercial Add-in (.xlam), Ribbon XML & Security Licensing (Day 931-965)", "Đóng gói Add-in thương mại (.xlam), lập trình Ribbon XML chuyên nghiệp, Custom Task Pane, cấp License bản quyền theo phần cứng và Auto-Updater."),
        ("Phase 33: Generative AI Async UDFs & Master Capstone System (Day 966-1000)", "Nhúng Generative AI (OpenAI/Gemini/DeepSeek) vào công thức Excel (Async UDFs), xử lý dữ liệu AI hàng loạt và Đồ án Tốt nghiệp Master Excel Enterprise System.")
    ]

    current_day = 1
    # Add initial phases 1 to 10
    for p_name, topics in phases_def:
        t_list = [(t, f"Thực hành chi tiết: {t} với bài tập thực tế", i == len(topics)-1) for i, t in enumerate(topics)]
        add_phase(current_day, p_name, t_list)
        current_day += len(topics)

    # Add remaining phases 11 to 33
    for p_name, desc in remaining_phases:
        p_num = int(p_name.split(":")[0].replace("Phase ", "").strip())
        num_days = 35 if p_num in (32, 33) else 30
        topics = []
        for d in range(1, num_days + 1):
            is_proj = (d == num_days)
            title = f"{p_name.split(':')[1].split('(')[0].strip()} – Phần {d}/{num_days}" if not is_proj else f"Project {p_num}: Capstone {p_name.split(':')[1].split('(')[0].strip()}"
            exercise = f"Thực hành ứng dụng: {title}. Triển khai code VBA chuẩn mực, đo lường hiệu năng và xử lý ngoại lệ."
            topics.append((title, exercise, is_proj))
        add_phase(current_day, p_name, topics)
        current_day += num_days

    return roadmap

def generate_markdown(roadmap_data):
    md_lines = [
        "# 🗂️ Lộ Trình Học Excel VBA – 1.000 Ngày (Từ Zero Đến Master Spreadsheet & AI Integrator)",
        "",
        "> **Mục tiêu**: Làm chủ toàn diện Microsoft Excel VBA từ Macro Recorder đầu tiên đến Kỹ sư Tính toán Ma trận, Phân tích Dữ liệu Lớn, Mô hình Tài chính, Đóng gói Add-in Thương mại & Tích hợp Generative AI.",
        "> **Phạm vi**: 33 Phase, 1.000 Ngày, bao phủ Range/Sheet/Workbook Model, Mảng 2D tốc độ cao, WinAPI Memory Pointers, Dictionary, Thuật toán Sắp xếp, Modern Flat UI UserForms, Pivot & Power Pivot DAX, Power Query M-code, Real-time Dashboards, Financial Modeling (DCF/Monte Carlo/Solver), Hardware COM Ports, Web Scraping, REST API/OAuth2, Commercial Add-ins (.xlam), Ribbon XML, và Generative AI Async UDFs.",
        "> **Ký hiệu thời gian**: 🟢 30 phút | 🟡 60 phút | 🟠 90 phút | 🔴 120 phút | 🔥 150 phút | 🚀 3.5 giờ (Dự án)",
        ""
    ]

    for day in range(1, len(roadmap_data) + 1):
        if day not in roadmap_data:
            continue
        title, phase, prev_topic, exercise, is_proj = roadmap_data[day]
        emoji, mins, label = get_time(day, is_proj)

        md_lines.append(f"## Day {day} — {title}")
        md_lines.append("**Prompt:**")
        md_lines.append(f"Đóng vai trò là Kỹ sư Trưởng Tính toán & Giảng viên Cao cấp Excel VBA. Hôm nay là Day {day}: {title}.")
        md_lines.append(f"Giai đoạn: {phase}.")
        md_lines.append(f"Chủ đề hôm qua: {prev_topic}.")
        md_lines.append("")
        md_lines.append("(⚠️ LỆNH TỐI THƯỢNG: KHÔNG giải thích dông dài lý thuyết cơ bản. Chỉ đi thẳng vào thực chiến. TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ nội dung để tôi tự đọc.)")
        md_lines.append("Yêu cầu:")
        md_lines.append(f"1. Giải thích rõ nguyên lý và bản chất của '{title}' với ví dụ code VBA Excel thực tế, chuẩn clean code và chạy được ngay.")
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
        md_lines.append(f"**Tags:** #excel_vba #day{day} #vba #analytics")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    content = "\n".join(md_lines)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    with open(filepath_1000, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    data = build_excel_roadmap()
    generate_markdown(data)
    print(f"Done! Generated {len(data)} days to {filepath} and {filepath_1000}")
