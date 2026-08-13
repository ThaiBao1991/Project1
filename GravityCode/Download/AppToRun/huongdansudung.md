# Hướng Dẫn Sử Dụng PyPackGUI

PyPackGUI là công cụ giúp bạn đóng gói các dự án Python thành 1 file .exe duy nhất mà **không cần gõ lệnh**. Điểm mạnh nhất của tool là giải quyết triệt để vấn đề "quản lý file config / data" của PyInstaller.

## 1. Cách Đóng Gói Cơ Bản
1. Mở file main.py của **PyPackGUI**.
2. Chọn file main.py của dự án bạn cần đóng gói.
3. Chọn thư mục đầu ra và icon.
4. Bấm **Bắt đầu đóng gói**.

## 2. Quản Lý File Đính Kèm (Config, Data, Hình ảnh)
Ở phần **Dữ liệu đính kèm**, bạn có thể thêm các file cần thiết cho app (như config.json, thư mục images, database.sqlite...).

Có 2 tùy chọn cho mỗi file:
- **Chỉ đọc**: Dành cho hình ảnh, âm thanh... không bao giờ bị thay đổi. Code của bạn có thể đọc được nhưng không sửa được (đóng băng vĩnh viễn trong file .exe).
- **Giải nén**: Dành cho config.json, 	oken.txt... Ở lần chạy .exe đầu tiên, PyPackGUI sẽ tự động giải phóng (copy) các file này ra **nằm cạnh file .exe**. Nhờ đó, người dùng có thể mở nó lên và chỉnh sửa bình thường.

## 3. "Ma thuật" của PyPackHelper (Không cần sửa code nhiều)
Thông thường, khi đóng gói ra .exe, nếu code bạn dùng open("config.json", "r"), nó sẽ bị lỗi không tìm thấy file. 
Để giải quyết việc này một cách tự động hoàn toàn:

1. Copy file PyPackHelper.py vào cùng thư mục chứa code dự án của bạn.
2. Mở file code gốc của bạn (ví dụ: main.py của bạn).
3. Đặt dòng này ở trên cùng của file:
   `python
   import PyPackHelper
   `
**Chỉ cần như vậy!** Bạn không cần sửa bất kỳ hàm open() nào trong code cũ. 
PyPackHelper sẽ sử dụng kỹ thuật "Monkey Patching" để can thiệp ngầm vào hệ thống Python. 
Bất cứ khi nào code của bạn gọi open("tên_file.json", "r"):
- Nó sẽ tự kiểm tra xem đang chạy code python hay file exe.
- Nó sẽ tự tìm xem file json đó đang nằm trong ổ cứng bên ngoài (dành cho chế độ giải nén) hay nằm ẩn trong bộ nhớ tạm (dành cho chế độ chỉ đọc) và tự động nối đường dẫn chính xác cho bạn.
- Bạn hoàn toàn code như bình thường, mọi thứ tự động được lo liệu!

## 4. Lưu ý khi ghi file (Write)
- Tính năng tự động tìm đường dẫn của PyPackHelper chỉ áp dụng cho thao tác **đọc** (mode = 'r'). 
- Nếu bạn mở file để **ghi** (mode = 'w' hoặc 'a'), hệ thống sẽ lưu thẳng vào thư mục hiện hành (nơi đặt file .exe) theo cách thông thường, điều này giúp bạn xuất file hoặc lưu cấu hình mới ra ngoài hoàn toàn chính xác.
