---
name: pypack_exe_builder
description: Hướng dẫn đóng gói ứng dụng Python thành 1 file .exe duy nhất bằng PyInstaller, tích hợp kỹ thuật Monkey Patching PyPackHelper tự động tìm và nạp file config/data bên ngoài mà không làm crash ứng dụng.
---

# Hướng Dẫn Đóng Gói Python Ra File .EXE Độc Lập

Kỹ năng này giải quyết triệt để lỗi phổ biến nhất khi đóng gói PyInstaller (`FileNotFoundError` khi app đọc file cấu hình, JSON, hình ảnh hoặc database).

## 1. Cơ Chế Monkey Patching Thông Minh (PyPackHelper)
Khi chạy dưới dạng `.exe` `--onefile`:
- Các asset nhúng được giải nén vào thư mục tạm `sys._MEIPASS`.
- Các file cấu hình người dùng cần sửa (`config.json`, `settings.json`) nằm cạnh file `.exe`.

Chỉ cần đặt file `PyPackHelper.py` cạnh file code chính và thêm dòng đầu tiên:
```python
import PyPackHelper
```

`PyPackHelper` sẽ tự động chuyển hướng hàm `open()`:
1. Khi **đọc file** (`mode='r'`): Tự động ưu tiên tìm file ngoài ổ đĩa (cạnh `.exe`), nếu không có sẽ tìm trong bộ nhớ tạm `_MEIPASS`.
2. Khi **ghi file** (`mode='w'` hoặc `'a'`): Luôn ghi trực tiếp ra thư mục chứa `.exe`.

## 2. Lệnh Đóng Gói Chuẩn PyInstaller
```bash
pyinstaller --onefile --noconsole --name "TenUngDung" --icon "assets/icon.ico" --add-data "config.json;." main.py
```
- `--noconsole`: Ẩn cửa sổ dòng lệnh đen khi chạy ứng dụng GUI (CustomTkinter/Tkinter).
- `--add-data "source;target"`: Nhúng kèm file data/asset tĩnh.

## 3. Quản Lý File Đính Kèm Theo 2 Chế Độ
- **Chỉ đọc**: Dành cho hình ảnh, âm thanh, icon (đóng băng vĩnh viễn trong file .exe).
- **Giải nén ra ngoài**: Ở lần chạy đầu tiên, nếu file cấu hình chưa tồn tại bên cạnh `.exe`, ứng dụng tự động copy file mẫu từ bộ nhớ nhúng ra ngoài để người dùng chỉnh sửa.