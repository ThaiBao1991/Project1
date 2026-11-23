# Project Log - File Encrypt & Converter (Ứng dụng đa năng)

## 📌 Tổng Quan Dự Án
- **Thư mục dự án**: `C:\Users\12953 Bao\Desktop\desktop\work\Project\Python\BasicLearnPython\W3schools\Python Tutorial\Python Project\MyApp\File Encrypt`
- **Giao diện**: Tkinter GUI (Desktop App)
- **Tập tin chạy chính**: `main.py` (hoặc `run.bat`)
- **Chức năng chính**:
  1. **Đổi file .xlsb sang .csv**: Hỗ trợ đọc file Excel binary (.xlsb) với engine `pyxlsb` và xuất file CSV chuẩn UTF-8-SIG, tùy biến dòng header.
  2. **Mã hóa và giải mã file/thư mục**: Sử dụng chuẩn AES-CBC (128-bit key) ngẫu nhiên, lưu danh bạ file `data.txt` và khóa `key.key`, sinh các file mã hóa `.ecrb`.
  3. **Gửi email tự động**: Module dự phòng (đang phát triển).

---

## 📦 Danh Sách Thư Viện (Dependencies)
- `pycryptodome>=3.18.0`: Cung cấp module `Crypto.Cipher.AES`, `Crypto.Util.Padding`, `Crypto.Random`. *(Tuyệt đối KHÔNG cài `pip install crypto` vì là gói khác gây xung đột)*.
- `pandas>=2.0.0`: Thao tác dữ liệu bảng và xuất CSV.
- `pyxlsb>=1.0.10`: Engine đọc file nhị phân Excel `.xlsb`.
- `tkinter`: Thư viện GUI có sẵn của Python trên Windows.

---

## 📝 Lịch Sử Thay Đổi & Khắc Phục Lỗi

### [2026-11-20] - Khắc phục lỗi khởi động & Chuẩn hóa bộ cài đặt
- **Vấn đề phát hiện**:
  - Không thể chạy ứng dụng do lỗi `ModuleNotFoundError: No module named 'Crypto'`.
  - Môi trường máy tính trước đó cài nhầm gói PyPI `crypto 1.4.1`, gói này không tương thích và chiếm namespace trên Windows khiến `Crypto` không tìm thấy.
  - Thiếu thư viện `pyxlsb` khiến tính năng chuyển đổi `.xlsb` sẽ crash khi thực thi.
  - File `run.bat` thiếu `cd /d "%~dp0"`, có thể lỗi khi kích hoạt từ desktop/shortcut.
- **Giải pháp đã thực hiện**:
  - Đã chạy gỡ bỏ triệt để gói lỗi: `pip uninstall -y crypto`.
  - Đã cài đặt các gói chuẩn: `pip install pycryptodome pyxlsb`.
  - Tích hợp pattern `python_auto_install` vào đầu file `main.py` và `Encrypt.py`. Nếu chạy trên máy mới chưa có thư viện, app sẽ tự gọi pip cài đặt hoặc hiển thị popup hướng dẫn người dùng.
  - Cập nhật `run.bat`: Bổ sung `cd /d "%~dp0"` và cơ chế tạm dừng (`pause`) khi gặp mã lỗi giúp dễ dàng chẩn đoán.
  - Tạo mới `requirements.txt`: Khai báo phiên bản các thư viện phụ thuộc.
  - Tạo mới `CAI_DAT_THU_VIEN.bat`: Tiện ích 1-click tự động gỡ `crypto` xung đột và cài `requirements.txt`.
  - Tạo mới `HUONG_DAN_CAI_DAT.md`: Hướng dẫn chi tiết bằng tiếng Việt.
- **Trạng thái kiểm thử (Verification)**:
  - Cú pháp `python -m py_compile` cả 2 file: Đạt 100%.
  - Import tất cả module (`pandas`, `Crypto`, `pyxlsb`): Đạt 100%.
  - Headless test quy trình mã hóa AES và giải mã file: Đạt 100%.
