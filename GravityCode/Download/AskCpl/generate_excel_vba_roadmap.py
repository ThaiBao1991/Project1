# Generate Excel VBA Roadmap - 365 Days (Full Professional)

import os

filepath = r"c:\Users\games\Desktop\Project\Python\Python MyWork\Project1\GravityCode\Download\AskCpl\roadmap_excel_vba_365.md"

def get_time(day_num, is_project=False):
    if is_project:
        return ("🚀", 210, "Dự án tổng hợp — 3-4 tiếng")
    if day_num <= 30:
        return ("🟢", 30, "Nền tảng — 30 phút")
    elif day_num <= 120:
        return ("🟡", 60, "Trung bình — 60 phút")
    elif day_num <= 240:
        return ("🟠", 90, "Nâng cao — 90 phút")
    else:
        return ("🔴", 120, "Chuyên gia — 120 phút")

def build_roadmap():
    roadmap = {}
    
    # helper to add phase
    def add_phase(start_day, phase_name, topics):
        prev_topic = "Bắt đầu hành trình" if start_day == 1 else roadmap[start_day - 1][0]
        for i, t in enumerate(topics):
            day = start_day + i
            title, exercise, is_proj = t
            roadmap[day] = (title, phase_name, prev_topic, exercise, is_proj)
            prev_topic = title

    # Phase 1: VBA Foundation (Day 1-30)
    p1 = [
        ("Macro Recorder – Ghi macro tự động", "Tạo file Excel demo, ghi macro đổi màu ô và chạy thử", False),
        ("VBE (Visual Basic Editor) – Giao diện lập trình", "Khám phá Project Explorer, Properties Window, Code Window", False),
        ("Sub & Procedure – Khởi tạo thủ tục", "Viết Sub đầu tiên in 'Hello VBA' ra MsgBox", False),
        ("Biến (Variables) & Data Types", "Khai báo biến Integer, String, Date và gán giá trị", False),
        ("Hằng số (Constants) & Scope", "Khai báo hằng số thuế VAT và biến toàn cục", False),
        ("Option Explicit – Bắt buộc khai báo biến", "Bật Option Explicit và sửa lỗi chưa khai báo biến", False),
        ("Toán tử (Operators) – Toán học & Logic", "Viết code tính tổng, hiệu, AND, OR", False),
        ("Lệnh rẽ nhánh If...Then...Else", "Viết hàm kiểm tra số chẵn lẻ bằng If Else", False),
        ("Lệnh rẽ nhánh Select Case", "Dùng Select Case phân loại điểm A, B, C, D", False),
        ("Vòng lặp For...Next", "Dùng For Next in số từ 1 đến 10 ra cột A", False),
        ("Vòng lặp For Each...Next", "Duyệt qua tất cả các Sheet trong Workbook và in tên ra", False),
        ("Vòng lặp Do While...Loop", "Dùng Do While đếm số cho đến khi gặp ô trống", False),
        ("Vòng lặp Do Until...Loop", "Dùng Do Until tính tổng các số nhập vào tới khi > 100", False),
        ("Lệnh thoát vòng lặp (Exit For, Exit Do)", "Duyệt cột A, tìm thấy chữ 'Stop' thì thoát vòng lặp", False),
        ("Function – Hàm tự tạo cơ bản", "Viết Function TinhDienTich(dai, rong)", False),
        ("Truyền tham số (ByVal & ByRef)", "Viết 2 hàm test ByVal và ByRef để thấy sự khác biệt", False),
        ("Optional Arguments – Tham số tùy chọn", "Viết hàm có tham số thứ 3 là Optional có giá trị mặc định", False),
        ("ParamArray – Tham số mảng động", "Viết hàm TinhTong nhiều số lượng không giới hạn", False),
        ("InputBox – Nhập dữ liệu từ người dùng", "Hiện InputBox yêu cầu nhập tên, rồi chào bằng MsgBox", False),
        ("MsgBox – Hiển thị thông báo phức tạp", "Dùng MsgBox Yes/No/Cancel và bắt kết quả", False),
        ("Xử lý chuỗi (String Functions)", "Dùng Left, Right, Mid, Len, InStr để tách họ tên", False),
        ("Xử lý ngày tháng (Date/Time Functions)", "Dùng Date, Time, DateAdd, DateDiff tính số ngày", False),
        ("Xử lý số & Toán học (Math Functions)", "Dùng Round, Int, Abs, Rnd tạo số ngẫu nhiên", False),
        ("Kiểu dữ liệu Variant – Cạm bẫy & Ứng dụng", "Demo lỗi hiệu năng khi dùng Variant cho vòng lặp lớn", False),
        ("Ghi chú (Comments) & Clean Code", "Format lại đoạn code rối rắm và thêm comment", False),
        ("Gọi Sub từ Sub khác (Call)", "Viết Sub Main gọi Sub1 và Sub2", False),
        ("Shortcut Keys & Quick Access Toolbar", "Gán Macro vào phím tắt Ctrl+Shift+M và nút trên QAT", False),
        ("Tạo Nút bấm (Button/Shape) gán Macro", "Vẽ Shape trên Sheet, gán macro chạy khi click", False),
        ("Bảo mật code VBA (Password Protect)", "Đặt mật khẩu bảo vệ Project VBA", False),
        ("Project 1: Ứng dụng tính lương cơ bản", "Dự án: Form đơn giản tính lương dựa trên InputBox/MsgBox", True)
    ]
    add_phase(1, "Phase 1: Excel VBA Foundation (Day 1-30)", p1)

    # Phase 2: Range & Worksheet Mastery (Day 31-60)
    p2 = [
        ("Workbook Object – Thao tác file", "Mở, đóng, lưu Workbook mới bằng code", False),
        ("Worksheet Object – Thao tác Sheet", "Thêm mới, đổi tên, ẩn, xóa Sheet", False),
        ("Range Object cơ bản (Range, Cells)", "Ghi dữ liệu vào Range('A1') và Cells(2, 2)", False),
        ("Đọc và Ghi dữ liệu vào Range", "Đọc ô A1, cộng 10, ghi vào ô B1", False),
        ("Offset & Resize – Di chuyển và thay đổi vùng", "Từ ô A1, offset 2 dòng, 3 cột và resize 5x5", False),
        ("CurrentRegion – Bắt trọn bảng dữ liệu", "Dùng CurrentRegion quét vùng dữ liệu liên tục", False),
        ("End(xlUp) / End(xlDown) – Tìm dòng cuối", "Tìm dòng cuối có dữ liệu ở cột A", False),
        ("UsedRange – Vùng dữ liệu thực sự", "In ra địa chỉ UsedRange của Sheet hiện tại", False),
        ("Copy, Paste & Paste Special", "Copy vùng A1:B10, Paste Value sang D1:E10", False),
        ("Xóa dữ liệu (Clear, ClearContents, ClearFormats)", "Xóa nội dung, định dạng của vùng chọn", False),
        ("Định dạng Font & Màu nền (ColorIndex, RGB)", "Đổi màu chữ đỏ, in đậm, nền xanh cho Range", False),
        ("Định dạng khung viền (Borders)", "Vẽ viền khung xung quanh bảng dữ liệu", False),
        ("Định dạng số (NumberFormat)", "Format ô C1 thành kiểu tiền tệ '#,##0 VNĐ'", False),
        ("RowHeight & ColumnWidth, AutoFit", "Tự động canh lề và chỉnh độ rộng cột Autofit", False),
        ("MergeCells – Trộn ô trong VBA", "Merge vùng A1:D1 và căn giữa", False),
        ("UnMerge và xử lý MergeCells", "Phát hiện ô Merge, bỏ Merge và fill dữ liệu", False),
        ("Find & Replace trong VBA", "Dùng Range.Find để tìm chữ 'Lỗi' và bôi vàng", False),
        ("AutoFilter – Lọc dữ liệu tự động", "Bật Filter, lọc cột B giá trị > 100", False),
        ("AdvancedFilter – Lọc nâng cao", "Dùng AdvancedFilter copy dữ liệu thỏa điều kiện sang sheet mới", False),
        ("Sort – Sắp xếp dữ liệu", "Sắp xếp bảng theo cột Ngày giảm dần", False),
        ("Name Manager – Đặt tên vùng (Named Ranges)", "Tạo Named Range cho bảng thuế và lấy dữ liệu qua tên", False),
        ("Data Validation – Xác thực dữ liệu", "Tạo Drop-down list (Validation) bằng VBA", False),
        ("Conditional Formatting bằng VBA", "Tạo điều kiện bôi đỏ ô có giá trị âm", False),
        ("Xử lý nhiều Worksheet cùng lúc", "Duyệt qua 10 sheet, copy header từ sheet 1 sang các sheet kia", False),
        ("Workbooks.Open & Xử lý nhiều File", "Mở tất cả file .xlsx trong folder và lấy dòng 1", False),
        ("Evaluate Method (Ký hiệu [])", "Dùng Evaluate('[A1:A10]') để tính tổng nhanh", False),
        ("SpecialCells (Blanks, Visible, Formulas)", "Xóa tất cả các dòng bị ẩn (Visible) hoặc trống", False),
        ("Xử lý In ấn (PageSetup, PrintOut)", "Chỉnh lề, Header/Footer và in tự động", False),
        ("Speed Optimization: Application properties", "Tắt ScreenUpdating, EnableEvents, Calculation", False),
        ("Project 2: Báo cáo tự động (Auto Report)", "Dự án: Đọc dữ liệu, gộp file, định dạng bảng, xuất báo cáo", True)
    ]
    add_phase(31, "Phase 2: Range & Worksheet Mastery (Day 31-60)", p2)

    # Phase 3: Events, Errors & Debugging (Day 61-90)
    p3 = [
        ("Giới thiệu VBA Events – Sự kiện là gì?", "Giải thích khái niệm Event-driven programming", False),
        ("Worksheet_SelectionChange", "Highlight dòng/cột tại ô đang chọn (Crosshair)", False),
        ("Worksheet_Change", "Tự động viết hoa, thêm timestamp khi sửa dữ liệu ô", False),
        ("Worksheet_Activate/Deactivate", "Hiện câu chào khi mở sheet, cảnh báo khi rời đi", False),
        ("Worksheet_BeforeDoubleClick/RightClick", "Double click vào ô để đánh dấu tick (✓)", False),
        ("Workbook_Open", "Tự động kiểm tra hạn sử dụng file khi mở", False),
        ("Workbook_BeforeClose/BeforeSave", "Ép người dùng phải điền đủ thông tin mới cho Save", False),
        ("Workbook_SheetChange", "Ghi log mọi thay đổi trên tất cả các sheet vào file text", False),
        ("EnableEvents – Kiểm soát vòng lặp sự kiện vô hạn", "Fix lỗi Worksheet_Change gọi lại chính nó", False),
        ("Application_OnTime (Hẹn giờ chạy lệnh)", "Cài đặt tự lưu file mỗi 5 phút", False),
        ("Application_OnKey (Gán phím tắt nâng cao)", "Vô hiệu hóa phím Ctrl+C, Ctrl+V trong workbook", False),
        ("Error Handling cơ bản (On Error Resume Next)", "Bỏ qua lỗi chia 0 và tiếp tục chạy", False),
        ("On Error GoTo [Label] – Bẫy lỗi", "Chuyển hướng code khi mở file không tồn tại", False),
        ("On Error GoTo 0 – Reset Error Handler", "Kết thúc bẫy lỗi ở những đoạn cần thiết", False),
        ("Err Object – Lấy thông tin lỗi (Number, Description)", "Ghi log lỗi kèm tên hàm, số lỗi, thời gian", False),
        ("Xây dựng cơ chế Error Logging (Ghi log lỗi)", "Tạo hàm log lỗi tập trung ra file txt", False),
        ("Debugging: Step Into (F8), Step Over (Shift+F8)", "Chạy từng dòng code để tìm bug thuật toán", False),
        ("Debugging: Breakpoints & Stop statement", "Dừng code tại vòng lặp thứ 100 để kiểm tra biến", False),
        ("Debugging: Immediate Window (? & Debug.Print)", "In ra giá trị của mảng ngay trong lúc code chạy", False),
        ("Debugging: Locals Window & Watch Window", "Theo dõi sự thay đổi của Object Worksheet", False),
        ("Xử lý lỗi #VALUE, #REF, #DIV/0 từ Cell", "Dùng IsError kiểm tra ô trước khi tính toán", False),
        ("Bảo vệ Code khỏi bị break khi lỗi (Production Ready)", "Tạo bộ khung Sub có bẫy lỗi chuẩn (Template)", False),
        ("Gỡ lỗi vòng lặp vô hạn (Infinite Loop)", "Nhận diện và thoát vòng lặp Do While lỗi điều kiện", False),
        ("Tạo Custom Error (Err.Raise)", "Chủ động quăng lỗi 'Sai định dạng' khi input không hợp lệ", False),
        ("Xử lý xung đột Event", "Quản lý khi SelectionChange và Change cùng kích hoạt", False),
        ("Event trên Chart/Shape (Giới thiệu)", "Click vào biểu đồ để lọc dữ liệu tương ứng", False),
        ("User-defined Function (UDF) & Volatile", "Viết UDF tính thuế tự cập nhật lại khi thay đổi (Application.Volatile)", False),
        ("Debug UDF (Cách bắt lỗi hàm tự tạo)", "Debug hàm tự tạo gọi từ Excel Cell", False),
        ("Tối ưu hóa: Tránh dùng On Error quá nhiều", "Thay On Error bằng IsNumeric, IsDate, Dir()", False),
        ("Project 3: Hệ thống Audit Trail", "Dự án: Theo dõi mọi thay đổi trong Workbook, lưu vào hidden sheet", True)
    ]
    add_phase(61, "Phase 3: Events, Errors & Debugging (Day 61-90)", p3)

    # Phase 4: UserForms & GUI Design (Day 91-120)
    p4 = [
        ("UserForm 101 – Thiết kế Giao diện", "Tạo form đơn giản, đổi màu, kích thước, tên", False),
        ("Hiển thị & Đóng Form (Show, Unload, Hide)", "Nút mở Form trên Sheet, nút Thoát trên Form", False),
        ("Modal vs Modeless Form (Show 0 vs 1)", "Tạo form nhập liệu Modeless cho phép click ngoài sheet", False),
        ("Label & TextBox (Thuộc tính cơ bản)", "Tạo form nhập thông vị trí, ràng buộc MaxLength", False),
        ("CommandButton & Accelerator Key", "Gán phím tắt Alt+S cho nút Save trên Form", False),
        ("ComboBox – Tạo Dropdown danh sách", "Load list danh mục từ Sheet vào ComboBox (AddItem)", False),
        ("ListBox (Single & Multi-Select)", "Load dữ liệu vào ListBox và cho phép chọn nhiều dòng", False),
        ("OptionButton (Radio) & Frame", "Dùng Frame nhóm giới tính Nam/Nữ", False),
        ("CheckBox – Hộp kiểm đa lựa chọn", "Tích chọn các dịch vụ đi kèm", False),
        ("MultiPage & TabStrip", "Tạo form cài đặt với 3 tabs (General, DB, View)", False),
        ("RefEdit Control (Chọn vùng Excel)", "Dùng RefEdit chọn dải ô trên sheet từ Form", False),
        ("ScrollBar & SpinButton", "Dùng SpinButton để tăng/giảm giá trị trong TextBox", False),
        ("Load Data vào Form (Form_Initialize)", "Lấy dữ liệu cấu hình đưa vào form khi vừa mở", False),
        ("Validate Data trên Form (BeforeUpdate, KeyPress)", "Chặn không cho nhập chữ vào TextBox số lượng", False),
        ("Lưu dữ liệu Form xuống Sheet (CRUD - Create)", "Nút Add lưu record xuống dòng cuối bảng", False),
        ("Hiển thị dữ liệu lên Form (CRUD - Read)", "Gõ ID vào Textbox, tự động load tên, tuổi ra", False),
        ("Cập nhật & Xóa dữ liệu (CRUD - Update, Delete)", "Sửa thông tin hoặc xóa dòng hiện tại", False),
        ("ListBox nâng cao – Hiển thị nhiều cột", "Load Range 5 cột vào ListBox (RowSource & List)", False),
        ("List & Column Properties trong ListBox", "Lấy giá trị ở cột ẩn (cột ID) của dòng được chọn", False),
        ("ComboBox Cascade (Phụ thuộc nhau)", "Chọn Tỉnh/Thành -> Load Huyện/Xã tương ứng", False),
        ("Search Form – Tự động lọc khi gõ (Search as you type)", "Gõ chữ, ListBox tự động thu hẹp kết quả", False),
        ("Form Đăng nhập (Login Form)", "Form yêu cầu User/Pass, sai 3 lần thoát ứng dụng", False),
        ("Progress Bar (Thanh tiến trình)", "Tạo thanh Progress Bar tự chế bằng Label/Frame", False),
        ("Truyền dữ liệu giữa nhiều UserForm", "Mở Form con tìm kiếm, truyền kết quả về Form cha", False),
        ("UserForm Resize (Co giãn các control tự động)", "Viết code form Resize tự đổi kích cỡ ListBox bên trong", False),
        ("Tạo Control động (Add Controls at Runtime)", "Sinh ra 10 TextBoxes bằng vòng lặp dựa trên số lượng cột", False),
        ("API Windows căn bản cho UserForm", "Bỏ nút [X] (Close) trên thanh tiêu đề Form", False),
        ("Xóa UserForm Flicker (Nháy màn hình)", "Tối ưu hóa tốc độ load Form bằng Application properties", False),
        ("Tách code Business Logic ra khỏi Form (MVC cơ bản)", "Gửi data từ form sang Module để xử lý, không viết trong Form", False),
        ("Project 4: Hệ thống Quản lý Bán hàng (Mini POS)", "Dự án: Form nhập xuất kho, hóa đơn, đầy đủ CRUD", True)
    ]
    add_phase(91, "Phase 4: UserForms & GUI Design (Day 91-120)", p4)

    # Phase 5: Arrays, Dictionary & Data Structures (Day 121-150)
    p5 = [
        ("Static vs Dynamic Array (Mảng tĩnh & động)", "Khai báo mảng 10 phần tử và mảng động ReDim", False),
        ("Mảng 1 chiều (1D Array)", "Lưu danh sách 12 tháng vào mảng và duyệt In ra", False),
        ("Mảng 2 chiều (2D Array)", "Tạo ma trận 3x3, gán giá trị và tính tổng", False),
        ("Giao tiếp Range & Array (Tốc độ ánh sáng)", "Đọc Range A1:C10000 vào mảng, nhân đôi, ghi lại", False),
        ("ReDim Preserve (Mở rộng mảng động)", "Thêm phần tử vào mảng mà không mất dữ liệu cũ", False),
        ("LBound & UBound (Giới hạn mảng)", "Viết vòng lặp For dùng Lbound to Ubound duyệt mảng 2D", False),
        ("Hàm Join & Split", "Tách chuỗi bằng dấu phẩy thành mảng, rồi gộp lại bằng dấu gạch ngang", False),
        ("Hàm Filter (Lọc mảng 1D)", "Lọc các phần tử chứa chữ 'Nguyễn' trong mảng tên", False),
        ("Xóa/Xoá phần tử trong Array (Thuật toán dịch chuyển)", "Viết hàm xóa phần tử thứ i trong mảng 1D", False),
        ("Sắp xếp mảng (Bubble Sort & Quick Sort)", "Viết hàm QuickSort sắp xếp mảng 1D tốc độ cao", False),
        ("Tìm kiếm nhị phân (Binary Search) trên Array", "Tìm kiếm trên mảng đã sort để lấy index", False),
        ("Scripting.Dictionary – Cấu trúc Key-Value", "Tạo Dictionary lưu giá sản phẩm (Mã - Giá)", False),
        ("Dictionary vs Collection (Ưu/nhược)", "So sánh tốc độ tìm kiếm Key giữa Dict và Collection", False),
        ("Lọc trùng lặp bằng Dictionary (Remove Duplicates)", "Dùng Dictionary lấy danh sách Unique từ 1 cột", False),
        ("Gom nhóm & Tính tổng bằng Dictionary (Group By)", "Nhóm mã sản phẩm, tính tổng số lượng (như PivotTable)", False),
        ("Dictionary of Arrays / Dictionary of Dictionary", "Tạo cấu trúc cây 2 cấp: Vùng -> Cửa hàng -> Doanh thu", False),
        ("VBA Collection – Tập hợp đối tượng", "Lưu các Worksheet muốn in vào 1 Collection", False),
        ("Dictionary: Lấy Keys() và Items() ra Range", "Xuất toàn bộ Key và Value ra 2 cột trong Sheet", False),
        ("VBScript.RegExp (Regular Expressions) cơ bản", "Regex kiểm tra định dạng Email hợp lệ", False),
        ("Regex Pattern & Flags (Global, IgnoreCase)", "Trích xuất tất cả các số điện thoại từ một đoạn text", False),
        ("Regex Replace – Thay thế chuỗi nâng cao", "Xóa toàn bộ ký tự đặc biệt, chỉ giữ lại số và chữ", False),
        ("Jagged Array (Mảng lồng mảng)", "Tạo mảng chứa các mảng khác có độ dài khác nhau", False),
        ("Mảng 3D & 4D (Nâng cao)", "Khai báo và duyệt mảng 3D (ví dụ: Tọa độ X,Y,Z)", False),
        ("Tối ưu Memory với Array (Erase)", "Giải phóng bộ nhớ mảng sau khi sử dụng", False),
        ("Transpose Array (Application.Transpose)", "Xoay mảng 2D dọc thành ngang và ngược lại", False),
        ("Xử lý lỗi Dimension của mảng (Bẫy lỗi)", "Kiểm tra mảng đã được khởi tạo hay chưa (IsArray/Error)", False),
        ("Truyền/Nhận Array qua Function", "Hàm nhận 2 mảng 1D, trả về 1 mảng gộp", False),
        ("Custom Data Types (Type...End Type)", "Tạo Type HocSinh (Ten, Diem, Tuoi) và tạo mảng HocSinh", False),
        ("So sánh tốc độ: Cell-by-Cell, Array, SQL", "Đo thời gian xử lý 100k dòng bằng 3 cách", False),
        ("Project 5: In-Memory Data Processor", "Dự án: Đọc 2 bảng lớn, Join (Vlookup), Group By toàn bộ bằng Memory Array + Dictionary", True)
    ]
    add_phase(121, "Phase 5: Arrays, Dictionary & Data Structures (Day 121-150)", p5)

    # Phase 6: File System Object & External Files (Day 151-180)
    p6 = [
        ("Dir() – Lấy danh sách file/folder cơ bản", "Dùng Dir duyệt lấy toàn bộ file .xlsx trong thư mục", False),
        ("Scripting.FileSystemObject (FSO) – Giới thiệu", "Add reference FSO, tạo FSO object (Early/Late binding)", False),
        ("FSO: Folder & File (Thao tác Thư mục/File)", "Tạo thư mục mới, copy file, đổi tên file bằng FSO", False),
        ("FSO: Kiểm tra tồn tại (FileExists, FolderExists)", "Kiểm tra file cấu hình trước khi chạy macro", False),
        ("FSO: Lấy thông tin File (Path, Size, DateCreated)", "Liệt kê danh sách file kèm kích thước và ngày tạo ra sheet", False),
        ("FSO: Đệ quy (Recursive) duyệt Folder con", "Viết hàm đệ quy tìm tất cả file .pdf trong thư mục và thư mục con", False),
        ("Mở hộp thoại chọn File (Application.GetOpenFilename)", "Hiện hộp thoại cho người dùng chọn 1 hoặc nhiều file Excel", False),
        ("Mở hộp thoại chọn Folder (Application.FileDialog)", "Cho chọn thư mục lưu báo cáo (msoFileDialogFolderPicker)", False),
        ("Đọc file Text (.txt) cơ bản (Open For Input)", "Đọc dòng từng dòng từ file txt ghi ra Debug.Print", False),
        ("Ghi file Text (Open For Output / Append)", "Ghi nội dung log vào cuối file text có sẵn", False),
        ("Đọc ghi file nhị phân (Open For Binary)", "Đọc file, mã hóa XOR đơn giản và ghi lại", False),
        ("FSO: TextStream – Đọc ghi Text nâng cao", "Dùng ReadAll, ReadLine đọc file dung lượng lớn", False),
        ("Xử lý file CSV bằng VBA (Tách dấu phẩy)", "Đọc CSV, xử lý dấu phẩy trong ngoặc kép (Regex)", False),
        ("Tạo và Ghi file CSV siêu tốc bằng Array", "Tạo file CSV chứa 1 triệu dòng trong < 5 giây", False),
        ("QueryTable / Workbooks.OpenText (Import Text nhanh)", "Dùng Excel native methods để mở Text/CSV", False),
        ("Xuất Sheet thành PDF (ExportAsFixedFormat)", "Lưu báo cáo định dạng PDF với tên file theo ngày tháng", False),
        ("Gộp PDF bằng VBA? (Giới hạn và Workarounds)", "Thảo luận về PDF Toolkit (PDFtk) command line từ VBA", False),
        ("Thao tác file ZIP bằng VBA (Shell.Application)", "Tự động giải nén file zip lấy từ email", False),
        ("Thao tác file ZIP: Nén file (Compress)", "Tạo file zip chứa các báo cáo vừa xuất", False),
        ("Shell function – Chạy file/lệnh ngoài hệ thống", "Dùng Shell gọi Notepad, Calculator, Cmd", False),
        ("WScript.Shell – Run (Chờ lệnh hoàn thành)", "Gọi lệnh ping từ cmd và chờ lấy kết quả về VBA", False),
        ("Windows Environment Variables", "Lấy tên user đăng nhập, thư mục %APPDATA% qua Environ()", False),
        ("Tạo Desktop Shortcut bằng VBA (WScript.Shell)", "Tạo shortcut mở file Excel hiện tại trên màn hình Desktop", False),
        ("Đọc ghi cấu hình INI file (Windows API)", "Khai báo API GetPrivateProfileString để lưu thiết lập", False),
        ("Đọc ghi Windows Registry bằng VBA", "Lưu/Đọc key Registry (GetSetting, SaveSetting)", False),
        ("Giao tiếp Clipboard (Copy/Paste text qua RAM)", "Đưa chuỗi vào Clipboard hoặc lấy text từ Clipboard (DataObject)", False),
        ("Late Binding vs Early Binding (FSO/Dictionary)", "Chuyển đổi code sang Late Binding (CreateObject) để tránh lỗi Reference", False),
        ("Tự động Add Reference bằng code (VBE Extensibility)", "Dùng VBA để tự tick vào 'Microsoft Scripting Runtime'", False),
        ("Bảo vệ thư mục (Read-only, Hidden attributes)", "Dùng VBA đổi thuộc tính file thành ẩn hoặc chỉ đọc", False),
        ("Project 6: File & Folder Manager (Auto Backup)", "Dự án: Tool backup dữ liệu, nén thành Zip, thêm timestamp, lưu ra ổ đĩa mạng", True)
    ]
    add_phase(151, "Phase 6: File System Object & External Files (Day 151-180)", p6)

    # Phase 7: Database Integration (ADO/SQL) (Day 181-210)
    p7 = [
        ("Giới thiệu ADO (ActiveX Data Objects)", "Sự khác biệt DAO và ADO, khai báo Reference ADODB", False),
        ("Connection String – Chuỗi kết nối", "Cách cấu hình chuỗi kết nối tới file Access .accdb", False),
        ("ADO Connection – Mở và Đóng kết nối", "Viết Sub tạo connection tới DB Access, báo lỗi nếu sai đường dẫn", False),
        ("ADO Recordset – Đọc dữ liệu (Select)", "Truy vấn bảng KhachHang, dùng CopyFromRecordset xuất ra sheet", False),
        ("SQL Căn bản (SELECT, WHERE, ORDER BY)", "Lấy dữ liệu có lọc điều kiện đơn giản", False),
        ("SQL Nâng cao (JOIN, GROUP BY)", "Kết nối 2 bảng Hóa Đơn và Chi Tiết", False),
        ("ADO Command – Thực thi INSERT, UPDATE, DELETE", "Dùng Connection.Execute để thêm 1 khách hàng mới", False),
        ("CRUD: Form Excel tương tác với Access DB", "Gắn UserForm với ADO để cập nhật thông tin", False),
        ("Truy vấn Excel như một Database (ADO to Excel)", "Kết nối tới 1 file Excel đóng khác (như 1 DB) và lấy data", False),
        ("Lọc trùng và JOIN dữ liệu 2 file Excel (SQL)", "Dùng ADO SQL để hợp nhất (UNION) data từ 2 workbook đóng", False),
        ("Tham số hóa SQL (ADO Parameters)", "Dùng Command Object với tham số để tránh SQL Injection", False),
        ("Kết nối SQL Server từ Excel (ODBC/OLEDB)", "Chuỗi kết nối SQL Server, Windows Auth và SQL Auth", False),
        ("Stored Procedures (Thực thi SP từ VBA)", "Gọi SP từ SQL Server truyền tham số đầu vào và lấy Recordset", False),
        ("Xử lý Stored Procedure có tham số OUTPUT", "Lấy giá trị trả về (OUTPUT parameter) từ SP", False),
        ("ADO Transaction (BeginTrans, CommitTrans, Rollback)", "Bảo toàn dữ liệu khi Insert master-detail, roll back nếu lỗi", False),
        ("Phân trang dữ liệu (Pagination) bằng ADO", "Recordset AbsolutePage, PageSize để phân trang lên UserForm", False),
        ("Ngắt kết nối (Disconnected Recordset)", "Lấy data về bộ nhớ, đóng kết nối, xử lý offline, cập nhật lại (BatchUpdate)", False),
        ("ADO Stream – Xử lý ảnh/File (BLOB)", "Đọc và lưu ảnh từ ổ đĩa vào trường OLE của Access/SQL Server", False),
        ("Recordset sang mảng 2D (GetRows)", "Đọc Recordset tốc độ cao vào Variant Array bằng GetRows", False),
        ("Tạo Table/Database Access từ Excel (ADOX/DDL)", "Dùng SQL CREATE TABLE tạo bảng mới trong Access file", False),
        ("Excel làm Frontend chuyên nghiệp", "Quản lý state, giấu connection string, xử lý timeout", False),
        ("Tối ưu CursorType và LockType", "Hiểu về ForwardOnly, Keyset, Dynamic, Static, ReadOnly, Optimistic", False),
        ("Bẫy lỗi ADO Errors Collection", "Lặp qua ADODB.Connection.Errors để bắt lỗi SQL chi tiết", False),
        ("Kết nối MySQL/PostgreSQL từ Excel", "Chuỗi kết nối và cài đặt ODBC Driver cho MySQL", False),
        ("Hệ thống đa người dùng (Multi-user concurrency)", "Xử lý lỗi ghi đè (locking) khi 2 người cùng sửa DB", False),
        ("Kết nối Cloud Database (Azure SQL)", "Thực hành query lên database đám mây Azure từ Excel", False),
        ("Kiến trúc Data Access Layer (DAL)", "Tách module riêng chỉ chuyên xử lý DB, các module khác gọi hàm", False),
        ("Export Recordset ra XML / JSON", "Lưu Recordset thành file XML (Recordset.Save)", False),
        ("Đóng gói công cụ ADO Helper", "Viết Class Module ADO_Helper chuyên dùng kết nối, get_data, execute", False),
        ("Project 7: Hệ thống CRM/ERP Mini (Excel + SQL Server)", "Dự án: Frontend Excel giao tiếp toàn bộ qua SQL Server (Stored Proc)", True)
    ]
    add_phase(181, "Phase 7: Database Integration (ADO/SQL) (Day 181-210)", p7)

    # Phase 8: Office & OS Automation (Day 211-240)
    p8 = [
        ("Giới thiệu Office Automation (COM Automation)", "Khai báo Reference Word/Outlook, khái niệm Object Model", False),
        ("Điều khiển Word từ Excel (Tạo Document mới)", "Khởi tạo ứng dụng Word, tạo file mới và gõ text", False),
        ("Word: Mail Merge (Trộn thư) bằng VBA", "Điền dữ liệu Excel vào các Bookmark/Field trong file Word mẫu", False),
        ("Word: Export bảng/biểu đồ Excel sang Word", "Copy Range/Chart từ Excel paste vào Word Document", False),
        ("Word: Find and Replace văn bản", "Mở hợp đồng mẫu, thay chữ [Ten_KH] thành tên thật", False),
        ("Word: In ấn, lưu file PDF (Word Automation)", "Save as PDF hợp đồng rồi tự động đóng Word ẩn", False),
        ("Điều khiển Outlook từ Excel (Gửi Email)", "Tạo email, điền To, CC, Subject, Body và Send", False),
        ("Outlook: Đính kèm file (Attachments)", "Gửi email đính kèm file báo cáo Excel/PDF vừa tạo", False),
        ("Outlook: HTML Body & Chèn Bảng Excel", "Viết body HTML, chèn bảng Excel vào giữa email (HTML Publish)", False),
        ("Outlook: Gửi email hàng loạt (Bulk Email)", "Duyệt vòng lặp khách hàng, tạo và gửi email cá nhân hóa", False),
        ("Outlook: Đọc email (Inbox Automation)", "Quét Inbox, lọc email có tiêu đề 'Báo cáo', tải file đính kèm", False),
        ("Outlook: Di chuyển email (Folders)", "Sau khi tải đính kèm, di chuyển email sang folder 'Processed'", False),
        ("Điều khiển PowerPoint từ Excel", "Khởi tạo PPT, thêm Slide mới, thêm Text/Shapes", False),
        ("PowerPoint: Copy Bảng/Biểu đồ làm báo cáo", "Xuất 10 charts thành 10 slides PPT tự động cập nhật", False),
        ("PowerPoint: Cập nhật link dữ liệu (Update Links)", "Mở file PPT mẫu, update link dữ liệu từ Excel", False),
        ("Tương tác Internet Explorer / Edge (IE Mode)", "Cảnh báo về sự lỗi thời của IE, giới thiệu giải pháp thay thế", False),
        ("Windows API căn bản (Khai báo Declare PtrSafe)", "Khái niệm API 32-bit vs 64-bit, cách khai báo chuẩn", False),
        ("Windows API: Phát âm thanh (PlaySound)", "Phát tiếng 'bíp' báo hiệu code chạy xong", False),
        ("Windows API: Ẩn/Hiện cửa sổ Excel (FindWindow)", "Tìm handle của Excel, ẩn hoàn toàn Application", False),
        ("Windows API: Hẹn giờ nâng cao (Sleep, GetTickCount)", "Dừng code 500ms mà không ảnh hưởng CPU (Sleep)", False),
        ("Windows API: Đọc độ phân giải màn hình", "Lấy Screen Width, Height để căn giữa UserForm tự động", False),
        ("Windows API: Vô hiệu hóa chuột/bàn phím (BlockInput)", "Tạm khóa chuột user lúc code VBA đang chạy nặng", False),
        ("Lập lịch tác vụ với Windows Task Scheduler (qua VBS)", "Dùng Task Scheduler gọi file .vbs để mở Excel chạy Macro ẩn", False),
        ("SendKeys – Kẻ giả lập phím (Cạm bẫy)", "Dùng Sendkeys gửi lệnh in, phân tích sự không ổn định", False),
        ("Giao tiếp với file PDF (Đọc Text cơ bản)", "Thử nghiệm gọi Xpdf hoặc pdftotext CLI từ VBA", False),
        ("Thao tác AutoCAD / SolidWorks bằng VBA (Giới thiệu)", "Khái niệm COM với phần mềm thứ 3", False),
        ("Giao tiếp SAP GUI Scripting từ Excel", "Cách record script trên SAP và chuyển hóa vào Excel VBA", False),
        ("Điều khiển Chrome/Edge (Selenium Basic)", "Cài Selenium Basic, mở Chrome, duyệt web bằng VBA", False),
        ("Selenium: Tương tác web (Click, SendKeys)", "Đăng nhập website tự động bằng Selenium VBA", False),
        ("Project 8: Hệ thống Gửi Email Hàng Loạt", "Dự án: Tạo hóa đơn PDF từ Word/Excel, đính kèm và gửi Outlook hàng loạt", True)
    ]
    add_phase(211, "Phase 8: Office & OS Automation (Day 211-240)", p8)

    # Phase 9: Web Scraping, APIs & JSON (Day 241-270)
    p9 = [
        ("Giới thiệu Web HTTP Requests (XMLHTTP60)", "Khai báo Reference MSXML2, gửi GET request đơn giản", False),
        ("Gửi GET Request & Đọc mã HTML (ResponseText)", "Lấy HTML source của trang web thời tiết", False),
        ("Gửi POST Request (Forms, Headers)", "Gửi dữ liệu login (Username/Password) qua POST", False),
        ("Xử lý HTTP Status Codes", "Kiểm tra code 200 (OK), 404 (Not Found), 500 (Error)", False),
        ("Web Scraping: MSHTML (HTML Document)", "Parse HTML string vào HTMLDocument object", False),
        ("MSHTML: getElementById, getElementsByClassName", "Trích xuất giá vàng từ thẻ <div> có id cụ thể", False),
        ("MSHTML: getElementsByTagName, QuerySelector", "Lấy toàn bộ link (thẻ <a>) hoặc thẻ h1 bằng selector", False),
        ("Thu thập dữ liệu bảng (Table Scraping)", "Quét HTML Table, đưa vào Array và thả xuống Sheet", False),
        ("Xử lý dữ liệu động (AJAX / CSRF Token)", "Phân tích Network Tab trên trình duyệt để tìm API thật sự", False),
        ("Giới thiệu RESTful API", "Cách hoạt động của REST API, Endpoints, Methods", False),
        ("API Authentication (API Keys, Bearer Tokens)", "Gửi request kèm Header 'Authorization: Bearer <token>'", False),
        ("Giới thiệu định dạng JSON", "Cấu trúc JSON (Objects, Arrays), so sánh với XML", False),
        ("Phân tích JSON bằng VBA-JSON (JsonConverter)", "Tải thư viện VBA-JSON, parse chuỗi JSON thành Dictionary/Collection", False),
        ("Trích xuất dữ liệu từ JSON", "Lấy danh sách người dùng từ API JSON công khai (jsonplaceholder)", False),
        ("Tạo chuỗi JSON (Serialize) từ VBA", "Chuyển Dictionary chứa dữ liệu hóa đơn thành JSON string", False),
        ("Gửi dữ liệu lên API (POST JSON)", "POST JSON string lên Webhook/API server để tạo record mới", False),
        ("Tích hợp Telegram Bot API (Gửi tin nhắn)", "Dùng VBA gửi thông báo hoàn thành công việc qua Telegram", False),
        ("Tích hợp Slack / Teams Webhook", "Gửi báo cáo, cảnh báo tự động vào kênh Teams/Slack", False),
        ("Tải file từ Internet bằng API (Download File)", "Dùng XMLHTTP / ADODB.Stream tải file Excel/PDF từ URL", False),
        ("Upload file lên Server/API (Multipart Form-Data)", "Đóng gói file đẩy lên server qua POST request", False),
        ("Kết nối Google Sheets API (Tổng quan)", "Cấu hình OAuth2/Service Account để lấy Access Token (GCP)", False),
        ("Lấy dữ liệu Google Sheets về Excel VBA", "Gọi API lấy data Range của Google Sheets dưới dạng JSON", False),
        ("OAuth2 Authentication Flow trong VBA", "Hiểu cách lưu và làm mới Access Token/Refresh Token", False),
        ("Tương tác hệ thống tỷ giá (Forex API)", "Lấy tỷ giá Vietcombank/Ngân hàng nhà nước tự động", False),
        ("Xử lý Rate Limiting & Retry (API Delay)", "Viết cơ chế Retry sau 3 giây nếu API báo lỗi 429 Too Many Requests", False),
        ("Lấy dữ liệu chứng khoán (Stock Data API)", "Kéo giá cổ phiếu realtime về Excel", False),
        ("Web Scraping bất đồng bộ (Async XMLHTTP)", "Gửi request không khóa màn hình Excel", False),
        ("Vượt rào (Bypass) cơ bản (User-Agent, Cookies)", "Thêm custom User-Agent, xử lý Cookie để web không chặn request", False),
        ("Thử thách Scraping: JavaScript Rendered Pages", "Cách kết hợp Selenium hoặc API thay vì HTML Scraping truyền thống", False),
        ("Project 9: Data Hub (Dashboard Realtime)", "Dự án: Kéo data từ 3 API khác nhau (Thời tiết, Chứng khoán, Tỷ giá) update Dashboard 1 phút/lần", True)
    ]
    add_phase(241, "Phase 9: Web Scraping, APIs & JSON (Day 241-270)", p9)

    # Phase 10: Advanced OOP & Custom Classes (Day 271-300)
    p10 = [
        ("Giới thiệu Lập trình Hướng đối tượng (OOP) trong VBA", "Class là gì? Object là gì? Tại sao cần OOP?", False),
        ("Tạo Class Module đầu tiên", "Tạo Class clsEmployee, khai báo thuộc tính Name, Age", False),
        ("Khởi tạo Đối tượng (New Keyword)", "Set emp = New clsEmployee, gán giá trị và in ra", False),
        ("Property Get / Property Let (Đóng gói dữ liệu)", "Tạo Property Tuoi có Validate (không cho < 18)", False),
        ("Property Set (Thuộc tính dạng Object)", "Gán Range hoặc Worksheet cho thuộc tính của Class", False),
        ("Class Methods (Phương thức của Class)", "Viết hàm TinhLuong() bên trong clsEmployee", False),
        ("Class Events (Class_Initialize, Class_Terminate)", "Code tự chạy khi New Class và khi Set Nothing", False),
        ("Mảng/Collection chứa Objects", "Tạo Collection chứa 10 objects clsEmployee và duyệt tính tổng lương", False),
        ("Tạo Collection Class (Wrapper)", "Tạo Class clsEmployees (số nhiều) để quản lý thêm/xóa/duyệt clsEmployee", False),
        ("Từ khóa Me & Parent", "Truy xuất đến chính object hiện tại và object chứa nó", False),
        ("Thiết kế Object Model (Giống Excel Model)", "Cấu trúc App -> CuaHang -> SanPham", False),
        ("Kế thừa (Inheritance) trong VBA? (Implements)", "Khái niệm Interface trong VBA, cách mô phỏng đa hình", False),
        ("Tạo Interface (IAnimal)", "Tạo Interface có hàm Speak, clsDog và clsCat Implements nó", False),
        ("Factory Pattern trong VBA", "Tạo hàm CreateEmployee thay vì dùng New ở khắp nơi", False),
        ("Bắt sự kiện Application bằng Class (WithEvents)", "Tạo Class bẫy sự kiện App_SheetChange toàn cục", False),
        ("WithEvents với Control (UserForm động)", "Gán sự kiện Click chung cho 10 TextBoxes sinh ra bằng code", False),
        ("WithEvents: Chart / PivotTable", "Bắt sự kiện khi PivotTable thay đổi (PivotTableUpdate)", False),
        ("Mô hình MVC (Model-View-Controller) trong VBA", "Chia tách UI (Userform), Logic (Class) và Data (Sheet/DB)", False),
        ("Ví dụ MVC: Ứng dụng Quản lý Nhiệm vụ (Task)", "Tạo View (Form), Controller (Code), Model (clsTask)", False),
        ("Tạo Object Builder Pattern", "Thiết kế Class với chuỗi hàm (Fluent Interface): Task.WithName().WithDate().Build()", False),
        ("Tạo Custom Error Class", "Class chuyên đóng gói và quản lý lỗi hệ thống", False),
        ("Design Pattern: Singleton", "Đảm bảo chỉ có 1 instance của clsConfig được khởi tạo", False),
        ("Design Pattern: Observer (Publish/Subscribe)", "Class phát sự kiện, các Form khác lắng nghe và cập nhật giao diện", False),
        ("Đóng gói Code (Code Encapsulation)", "Bảo vệ code lõi, chỉ lộ ra các hàm public cần thiết qua Class", False),
        ("Tạo thư viện tiện ích (clsUtils)", "Tạo lớp dùng chung (mảng, chuỗi, thời gian, file)", False),
        ("Kiến trúc Plugin / Add-in mở rộng", "Cách viết code để sau này dễ thêm tính năng không sửa core", False),
        ("Memory Leaks & Object References", "Tránh vòng lặp tham chiếu chéo (Circular Reference) khiến bộ nhớ không giải phóng", False),
        ("Refactoring Code VBA cũ sang OOP", "Phân tích 1 đoạn code Procedural cũ dài 500 dòng, đập đi xây lại bằng OOP", False),
        ("Đánh giá Hiệu năng OOP vs Procedural", "Overhead của Object creation và khi nào không nên dùng OOP", False),
        ("Project 10: Khung ứng dụng OOP (Enterprise Framework)", "Dự án: Xây dựng hệ thống UI-DB kết nối qua OOP với Design Patterns", True)
    ]
    add_phase(271, "Phase 10: Advanced OOP & Custom Classes (Day 271-300)", p10)

    # Phase 11: Power Query (M), DAX & VBA Integration (Day 301-330)
    p11 = [
        ("Giới thiệu Power Query & Sự kết nối với VBA", "Tại sao dùng Power Query thay thế nhiều chức năng VBA?", False),
        ("VBA Refresh Power Query (BackgroundQuery)", "Viết code làm mới (Refresh) Table/Connection Power Query an toàn", False),
        ("Refresh All vs Refresh cụ thể theo thứ tự", "Đảm bảo Query A chạy xong mới chạy Query B (CalculateUntilAsyncQueriesDone)", False),
        ("VBA thay đổi tham số Power Query (M Parameter)", "Từ Excel Cell/Userform truyền tham số Date vào Power Query qua VBA", False),
        ("VBA lấy động chuỗi kết nối Power Query (Dynamic Path)", "Sửa chuỗi Source trong Power Query bằng VBA khi chuyển file sang máy khác", False),
        ("Xử lý lỗi khi Refresh Power Query bằng VBA", "Bẫy lỗi khi file nguồn của Power Query bị mất", False),
        ("Kết hợp VBA xuất file sau khi Power Query Refresh", "Làm mới xong tự động PDF/Email báo cáo", False),
        ("Giới thiệu Power Pivot & Data Model (DAX)", "Khái niệm Data Model, sự khác biệt với Sheet Data", False),
        ("VBA cập nhật Data Model", "Refresh các bảng trong Data Model bằng code (ModelConnections)", False),
        ("VBA tương tác Slicer của PivotTable/Data Model", "Dùng code chọn nhiều mục trên Slicer (SlicerItems)", False),
        ("VBA lấy dữ liệu từ Data Model (MDX Query)", "Dùng ADO/VBA query thẳng vào Data Model Excel bằng ngôn ngữ MDX", False),
        ("Tự động hóa PivotTable (Tạo mới, đổi tên)", "Sinh Pivot Table từ dữ liệu thô bằng VBA (PivotCaches)", False),
        ("Tùy biến Layout PivotTable bằng VBA", "Đổi dạng Report Layout, Tabular, tắt Subtotals, Grand Totals", False),
        ("Thay đổi Filter, Row, Column, Data Field", "Code VBA tự động kéo thả cột vào PivotTable", False),
        ("Lấy dữ liệu từ PivotTable bằng GetPivotData (qua VBA)", "Trích xuất giá trị chính xác từ bảng Pivot", False),
        ("Xóa/Clean bộ nhớ PivotTable (Missing Items)", "Dọn dẹp các trường dữ liệu rác (RetainMissingItems = xlMissingItemsNone)", False),
        ("VBA tạo PivotChart đồng bộ", "Vẽ biểu đồ PivotChart từ PivotTable bằng code", False),
        ("Tạo Dashboard tương tác (VBA + Pivot + Slicer)", "Kết nối nhiều Pivot/Chart với 1 Master Slicer qua VBA", False),
        ("Đọc Data Model thành Array (Advanced)", "Kéo dữ liệu khổng lồ từ Model xử lý tiếp bằng VBA", False),
        ("VBA + Power BI (Giới thiệu API Power BI)", "Có thể đẩy dữ liệu từ Excel lên Power BI Dataset bằng API?", False),
        ("Lập lịch chạy Power Query vào ban đêm", "Kết hợp VBA OnTime + Power Query Refresh + Windows Task", False),
        ("Tạo Add-in chuyên Refresh dữ liệu hệ thống", "Đóng gói nút chức năng 'Update All DBs' cho toàn công ty", False),
        ("So sánh Performance: VBA Array, Power Query, SQL", "Khi nào dùng công cụ nào cho 5 triệu dòng?", False),
        ("VBA xử lý kết quả trả về của Power Query", "Load to Connection Only, rồi VBA đọc Connection đổ ra Array/Form", False),
        ("VBA tạo Query M Code động", "Ghép chuỗi M code trong VBA và inject vào Power Query", False),
        ("Giải pháp 'Hybrid': Query xử lý nặng, VBA trình bày", "Tận dụng sức mạnh đa luồng của PQ và tính linh hoạt của VBA", False),
        ("Bảo mật Data Model & Query", "Ẩn Query, khóa sheet, khóa Model tránh bị xem trộm", False),
        ("Export dữ liệu từ Data Model sang CSV siêu tốc", "Dùng VBA kết xuất data khổng lồ từ DAX Model ra file", False),
        ("Review & Tối ưu hóa kiến trúc Hybrid", "Các best practices khi kết hợp VBA và Modern Excel", False),
        ("Project 11: Enterprise Dashboard (Hybrid VBA+PQ)", "Dự án: Kéo data tự động bằng PQ, xử lý UI tương tác bằng VBA Form", True)
    ]
    add_phase(301, "Phase 11: Power Query (M), DAX & VBA Integration (Day 301-330)", p11)

    # Phase 12: Add-ins, Ribbon UI & Cloud/AI (Day 331-365)
    p12 = [
        ("Excel Add-ins (.xlam) là gì?", "Cách tạo, lưu và cài đặt Add-in trong Excel", False),
        ("Quản lý Add-in: Cài đặt và Gỡ bỏ bằng VBA", "Viết script tự động cài Add-in cho người dùng (AddIns.Add)", False),
        ("ThisWorkbook Events trong Add-in", "Code chạy ngầm toàn cục (Application Events) từ trong Add-in", False),
        ("Lưu trữ dữ liệu trong Add-in", "Dùng Custom XML Parts hoặc Hidden Sheets trong .xlam để lưu cấu hình", False),
        ("Custom UI (Ribbon XML) – Giới thiệu", "Công cụ Custom UI Editor/Office RibbonX Editor", False),
        ("Tạo Tab và Group trên Ribbon", "Viết XML thêm Tab 'Công Cụ' và Group 'Báo Cáo'", False),
        ("Thêm Buttons vào Ribbon (onAction)", "Tạo nút bấm, gán icon (imageMso) và liên kết với Sub trong VBA", False),
        ("Ribbon DropDown & ComboBox", "Tạo danh sách chọn tháng/năm trực tiếp trên thanh Ribbon", False),
        ("Ribbon CheckBox & ToggleButton", "Tạo nút bật/tắt chế độ 'Debug Mode' trên Ribbon", False),
        ("Cập nhật Ribbon động (Invalidate/InvalidateControl)", "Đổi trạng thái nút bấm (Enable/Disable) tùy điều kiện", False),
        ("Tạo Custom Context Menu (Menu chuột phải)", "Thêm lệnh 'Gửi Báo Cáo' vào menu khi chuột phải trên Cell", False),
        ("Bảo vệ Add-in (Password & Obfuscation)", "Khóa VBA Project, hạn chế người xem source code", False),
        ("Vấn đề Trust Center & Macro Security", "Ký điện tử (Digital Signature - SelfCert) cho file VBA", False),
        ("Tạo file cài đặt tự động (Installer .exe / .bat)", "Viết file bat tự copy .xlam vào thư mục Addins của Windows", False),
        ("Tích hợp API Đám mây – Tổng quan cuối", "Ôn lại Json và API, chuẩn bị cho kỷ nguyên AI", False),
        ("Kết nối OpenAI API (ChatGPT) từ VBA", "Gửi text lên GPT-3.5/4 API, lấy phản hồi trả về Excel", False),
        ("Prompt Engineering bằng VBA", "Viết hàm =ASK_GPT(A1) để tự động dịch, tóm tắt nội dung ô", False),
        ("Kết nối Gemini API (Google AI) từ VBA", "Dùng API của Gemini tương tự OpenAI để xử lý văn bản", False),
        ("Tạo Chatbot trợ lý (AI UserForm)", "Tạo giao diện Chatbot bằng Userform, giao tiếp với API AI", False),
        ("Dùng AI sinh code VBA (Meta-programming)", "Gọi API sinh đoạn code, lưu ra file và (cẩn thận) import vào module", False),
        ("Phân tích dữ liệu tự động bằng AI (Data Insights)", "Gửi tóm tắt số liệu kinh doanh, yêu cầu AI viết nhận xét", False),
        ("AI nhận diện ngôn ngữ và chuỗi phức tạp", "Thay Regex phức tạp bằng API AI để lọc data phi cấu trúc", False),
        ("Tạo API Server bằng Python (Flask/FastAPI)", "Xây dựng server Python nhỏ, VBA gọi Python để xử lý Machine Learning", False),
        ("Chạy Script Python từ VBA (RunPython)", "Tích hợp xlwings hoặc chạy Shell command kết nối Python", False),
        ("VBA + Python (Pandas) xử lý Big Data", "Đẩy đường dẫn file cho Python xử lý, trả lại file kết quả cho VBA", False),
        ("Giới thiệu Office Scripts (TypeScript)", "Khái niệm mới trên Excel Online, sự thay thế của VBA?", False),
        ("Chuyển đổi VBA sang Office Scripts (Khái quát)", "Cách viết lại logic VBA (Range, Loop) sang ngôn ngữ TypeScript", False),
        ("Power Automate kết hợp Excel Automation", "Dùng Power Automate gọi Office Scripts thay VBA trên mây", False),
        ("Tương lai của VBA & Lộ trình tự học tiếp", "Làm sao để thích ứng, kết hợp VBA + Python + Cloud", False),
        ("Kiểm tra lỗ hổng & Best Practices", "Review lại 10 nguyên tắc Clean Code & Architecture trong VBA", False),
        ("Phiên bản hóa Code (Git cho VBA)", "Dùng công cụ export VBA modules (Rubberduck) để quản lý trên Github", False),
        ("Rubberduck VBA (Công cụ nâng cấp VBE)", "Cài đặt và dùng Rubberduck để Refactor, Code Inspection, Unit Testing", False),
        ("Unit Testing trong VBA", "Viết test tự động (Assert) cho các hàm Function cốt lõi", False),
        ("Đánh giá & Tối ưu lại toàn bộ ứng dụng lớn", "Quy trình bảo trì và scale up ứng dụng VBA của công ty", False),
        ("Project 12: Đóng gói Ứng dụng AI Add-in", "Dự án: Xây dựng Add-in Ribbon có tích hợp ChatGPT/Gemini API, có cấp license", True)
    ]
    add_phase(331, "Phase 12: Add-ins, Ribbon UI & Cloud/AI (Day 331-365)", p12)

    return roadmap

def generate_markdown(roadmap_data):
    md_lines = [
        "# 🗂️ Lộ Trình Học Excel VBA – 365 Ngày (Từ Zero Đến Master)",
        "",
        "> **Mục tiêu**: Học Excel VBA từ Macro Recorder đầu tiên đến hệ thống automation + dashboard + tích hợp Cloud/AI hoàn chỉnh.",
        "> **Phạm vi**: 12 Phase, 365 ngày, bao phủ Range/Worksheet, UserForm, Chart, PivotTable/Power Query, Database, Office Automation, OOP, Financial Modeling, Cloud/AI Integration.",
        "> **Ký hiệu thời gian**: 🟢 30 phút | 🟡 60 phút | 🟠 90 phút | 🔴 120 phút | 🚀 3-4 giờ (Dự án)",
        ""
    ]

    for day in range(1, len(roadmap_data) + 1):
        if day not in roadmap_data:
            continue
        
        title, phase, prev_topic, exercise, is_proj = roadmap_data[day]
        emoji, mins, label = get_time(day, is_proj)

        md_lines.append(f"## Day {day} — {title}")
        md_lines.append("**Prompt:**")
        md_lines.append(f"Đóng vai trò là VBA Mentor chuyên Excel. Hôm nay là Day {day}: {title}.")
        md_lines.append(f"Giai đoạn: {phase}.")
        md_lines.append(f"Chủ đề hôm qua: {prev_topic}.")
        md_lines.append("")
        md_lines.append("(⚠️ LỆNH TỐI THƯỢNG: KHÔNG giải thích dông dài lý thuyết cơ bản. Chỉ đi thẳng vào thực chiến. TUYỆT ĐỐI KHÔNG tạo bài test/quiz tương tác chờ tôi trả lời. HÃY IN RA TOÀN BỘ nội dung để tôi tự đọc.)")
        md_lines.append("Yêu cầu:")
        md_lines.append(f"1. Giải thích rõ khái niệm '{title}' với ví dụ code VBA Excel thực tế, ngắn gọn và có thể chạy được ngay.")
        md_lines.append("2. Chỉ ra 2-3 lỗi thường gặp khi học chủ đề này và cách debug cụ thể.")
        md_lines.append(f"3. Liên kết với '{prev_topic}' (hôm qua) — điểm nào hôm nay kế thừa và mở rộng.")
        md_lines.append(f"4. Giao bài tập mini: {exercise}")
        md_lines.append("")
        md_lines.append("**Bài tập:**")
        md_lines.append(f"⏱️ **Thời gian ước tính:** {label}")
        md_lines.append(f"📌 **Chủ đề hôm nay:** {title}")
        md_lines.append(f"🔗 **Ôn lại ngày trước:** {prev_topic}")
        md_lines.append(f"💻 **Tự thực hành:** {exercise}")
        md_lines.append("")
        md_lines.append(f"**Tags:** #excel_vba #day{day} #vba")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    with open(filepath, 'w', encoding='utf-8') as mf:
        mf.write('\n'.join(md_lines))
        
if __name__ == '__main__':
    data = build_roadmap()
    generate_markdown(data)
    print(f"Generated {filepath} successfully with {len(data)} days.")
