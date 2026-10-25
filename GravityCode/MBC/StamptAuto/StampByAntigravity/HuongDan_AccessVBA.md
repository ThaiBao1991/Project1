# Hướng Dẫn Tích Hợp Đóng Dấu Tự Động Vào MS Access VBA

Tài liệu này hướng dẫn bạn các bước từ việc tạo cấu hình đóng dấu trên giao diện (GUI) cho đến cách viết mã VBA trong MS Access để tự động hóa việc đóng dấu lên file PDF bất kỳ.

## Bước 1: Tạo Cấu Hình Đóng Dấu Trên Giao Diện (GUI)

1. Mở phần mềm giao diện bằng cách nhấp đúp vào file `Chay_Giao_Dien.bat` (hoặc chạy file `main_gui.py`).
2. Tùy theo mẫu văn bản, hãy chọn loại đóng dấu bạn muốn ở 1 trong 2 tab:
   - **Tab Đóng Dấu Bằng Hình Ảnh**: Hệ thống sẽ dò tìm vị trí dựa vào một vùng hình ảnh được khoanh sẵn.
   - **Tab Đóng Dấu Bằng Chữ**: Hệ thống sẽ dò tìm vị trí dựa vào một cụm từ (Ví dụ: "Xác nhận", "Ký tên", "Giám đốc").
3. Nhập **File PDF Mẫu** và **Ảnh Con Dấu** của bạn.
4. Căn chỉnh **Tỷ lệ (%)** và các thông số vị trí cho phù hợp (Hãy dùng chức năng **Test Trang Này** để xem trước kết quả trực quan trên màn hình).
5. Khi đã ưng ý, bấm vào nút **Lưu Cấu Hình**.
6. Đặt tên cho cấu hình (khuyên dùng tên không dấu, không chứa các ký tự đặc biệt lạ). Ví dụ: `KTCK_(xacnhan)`.

*Lúc này, hệ thống sẽ tự động lưu lại file cấu hình và sinh thêm một file là `KTCK_(xacnhan).py` nằm bên trong thư mục `stamp_configs`. File `.py` này nhúng sẵn ảnh con dấu vào bên trong nó, đảm bảo tính độc lập.*

## Bước 2: Chuẩn Bị Code Trong Access VBA

Trong Access VBA, bạn cần gọi môi trường lệnh (Command Prompt) để chạy Engine `StampByAntigravity.py`, truyền vào đó **Đường dẫn file PDF** và **Tên Cấu Hình** bạn vừa tạo ở Bước 1.

### Đoạn Code Mẫu (VBA)

Bạn có thể copy đoạn code này vào một Sub, Function, hoặc sự kiện Click của một nút bấm trong MS Access.

```vba
Sub DongDauPDF()
    Dim wsh As Object
    Set wsh = CreateObject("WScript.Shell")
    
    Dim pythonExe As String
    Dim scriptPathNew As String
    Dim pdfPath As String
    Dim configName As String
    Dim cmd As String
    
    ' 1. Đường dẫn tới file python.exe của hệ thống
    pythonExe = "C:\Python312\python.exe"
    
    ' 2. Đường dẫn tới file Engine chính: StampByAntigravity.py
    scriptPathNew = "C:\Users\12953 bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\GravityCode\MBC\StamptAuto\StampByAntigravity\StampByAntigravity.py"
    
    ' 3. Đường dẫn tới file PDF thực tế bạn muốn đóng dấu ngay lúc này
    ' (Có thể lấy từ tham số truyền vào, hoặc đường dẫn động từ CSDL của bạn)
    pdfPath = "C:\Users\12953 bao\Desktop\CodingTest\Test\Dong dau\HoaDon_123.pdf"
    
    ' 4. Tên Cấu Hình mà bạn đã tạo bằng GUI ở Bước 1
    configName = "KTCK_(xacnhan)"
    
    ' 5. Xây dựng lệnh CMD
    ' Cấu trúc: cmd /c "python.exe" "StampByAntigravity.py" "file_pdf.pdf" "Tên_Config"
    ' Cần bọc nhiều dấu ngoặc kép (""") để xử lý các khoảng trắng có trong đường dẫn file
    cmd = "cmd /c """ & """" & pythonExe & """ """ & scriptPathNew & """ """ & pdfPath & """ """ & configName & """" & """"
    
    ' (Tùy chọn) In ra màn hình cửa sổ Immediate (Ctrl+G) để kiểm tra lệnh CMD
    Debug.Print cmd
    
    ' 6. Thực thi lệnh
    ' Số 0: Chạy ẩn cửa sổ đen CMD (chạy ngầm). Đổi thành 1 nếu bạn muốn xem cửa sổ log bật lên.
    ' True: Access sẽ tạm dừng chờ cho đến khi Python đóng dấu xong mới chạy tiếp câu lệnh dưới.
    wsh.Run cmd, 0, True
    
    ' Có thể thêm kiểm tra nếu file có thay đổi dung lượng/tồn tại thì báo thành công
    MsgBox "Đã gửi lệnh đóng dấu hoàn tất!", vbInformation
End Sub
```

## Các Lưu Ý Quan Trọng
- **Tham số dòng lệnh**: `StampByAntigravity.py` luôn yêu cầu chính xác 2 tham số:
  1. Đường dẫn file PDF (`pdfPath`)
  2. Tên cấu hình (Không cần đuôi `.json` hay `.py`, chỉ cần chữ `KTCK_(xacnhan)`)
- **Quản lý file**: Bạn không cần phải copy hình ảnh con dấu gửi theo Access. Mã nguồn đã "gói gọn" (embed base64) hình ảnh con dấu vào trong file `stamp_configs/KTCK_(xacnhan).py`. Khi chạy, nó sẽ tự lôi ảnh này ra để đóng dấu.
- **Log Lỗi**: Nếu chạy Access VBA mà không thấy file thay đổi, hãy mở file `stamp_log.txt` (nằm chung thư mục với `StampByAntigravity.py`) kéo xuống dòng cuối cùng để xem phần mềm báo lỗi gì (File không tồn tại, lỗi cấu hình, không tìm thấy chữ...).
