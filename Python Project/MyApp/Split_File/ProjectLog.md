# ProjectLog — Split_File

## 2026-11-23 — Sửa lỗi `merge_files` gán cứng đuôi `.pdf`

### Thay đổi đã thực hiện
- **`main.py` & `SplitFile.py`** (đồng bộ cùng logic):
  - Bỏ việc gán cứng `f"{base_name}.pdf"`; dùng `file_name.rsplit(".part_", 1)[0]` để khôi phục đúng tên và phần mở rộng gốc (tránh `abc.pdf.pdf`, giữ đúng mọi định dạng như `.zip`, `.xlsx`, `.tar.gz`, tên có sẵn `.part_`, tên tiếng Việt UTF-8 hoặc không có đuôi).
  - Lọc chặt chỉ nhận các file có hậu tố số sau `.part_` (`suffix.isdigit()`), tránh crash khi có file rác cùng tiền tố (VD `.part_backup`).
  - Nếu không tìm thấy file phần nào (`not part_files`), báo lỗi và dừng ngay — không ghi đè file rỗng lên file gốc.
  - Ghi file nối theo chunk 1 MB qua file tạm `.merging_tmp` rồi `os.replace` để tránh hỏng file nếu lỗi giữa chừng, sau đó mới xoá các file `.part_xxx`.

### Kết quả kiểm thử đã chạy
- `python -m py_compile` + đối chiếu nội dung `main.py` và `SplitFile.py`: **Pass**.
- Test đầy đủ 7 kịch bản trên cả `main` và `SplitFile` (dọn sạch thư mục tạm sau khi chạy): `abc.pdf`, `archive.tar.gz`, `my.part_v2.zip`, `README`, `Báo cáo tháng 11.xlsx` (kèm file mồi `.part_backup`), trường hợp không có `.part_xxx` (giữ nguyên file gốc), và trường hợp chọn trực tiếp tên file gốc khi đã có `.part_001..003`: **Pass 100%**.

---

## 2026-11-23 — Bổ sung khung auto-install chuẩn, thoát sạch Python/CMD và file `.bat` click-là-chạy

### Thay đổi đã thực hiện
- **`main.py` & `SplitFile.py`** (đồng bộ cùng logic; giữ nguyên file backup `main 10-09-2024.py`):
  - Bổ sung khung `python_auto_install` chuẩn (UTF-8 console an toàn cho cả `python` và `pythonw`, `REQUIRED_PACKAGES = {}` sẵn sàng mở rộng vì app hiện chỉ dùng thư viện chuẩn `tkinter` & `os`, auto-heal xung đột hoa/thường Windows, fallback `pycryptodomex`, hộp thoại lỗi bọc ngoặc kép chuẩn có nút copy + thoát mã `2`).
  - Đưa phần khởi tạo giao diện Tkinter vào `def main():` + `if __name__ == "__main__": main()`.
  - Gắn `WM_DELETE_WINDOW` gọi `root.quit()` + `root.destroy()`, xử lý `KeyboardInterrupt` và kết thúc bằng `sys.exit(0)` để đảm bảo thoát sạch tiến trình Python và cửa sổ CMD khi đóng app.
- **`Run_Split_File.bat`** (chuẩn CRLF):
  - Bật `chcp 65001 >nul`, chuyển thư mục `cd /d "%~dp0"`, tự dò `python` / `py -3` / `py` (bỏ qua stub Microsoft Store), dùng `goto :NO_PYTHON` tránh lỗi ngoặc `)` trong khối `if (...)`.
  - Tự đóng luôn cửa sổ CMD khi app thoát với mã `0` hoặc `2`; chỉ `pause` khi gặp lỗi crash bất thường.
- **`requirements.txt`**: Ghi chú dự án hiện chỉ dùng thư viện chuẩn Python, sẵn sàng điền thêm khi mở rộng.

### Kết quả kiểm thử đã chạy
- `python -m py_compile` cho `main.py` và `SplitFile.py`: **Pass**.
- Import `main` và `SplitFile` (không tự mở cửa sổ GUI khi import): **Pass**.
- Kiểm thử `split_by_count`, `split_by_size` và `merge_files` trên dữ liệu mẫu trong thư mục tạm (dọn sạch sau test): **Pass** — khớp nội dung byte-by-byte và xoá file `.part_*` sau khi nối.
- Mô phỏng thiếu thư viện + offline (`fake-pkg>=1.2.3`): lệnh trên hộp thoại được bọc ngoặc kép chuẩn (`"fake-pkg>=1.2.3"`) và thoát sạch với mã `2`: **Pass**.
- Chạy thật `cmd.exe /c Run_Split_File.bat` → cửa sổ `File Splitter & Merger` mở sau 0.64s → gửi `WM_CLOSE` → cả `python.exe` và `cmd.exe` thoát sạch sau 0.29s (mã `0`, kiểm tra `Win32_Process` không còn `python.exe` chạy ngầm): **Pass**.

### Ghi chú tồn đọng
- Chưa thay đổi logic `merge_files` hiện có (vẫn giữ nguyên `f"{base_name}.pdf"` theo code gốc của dự án).
