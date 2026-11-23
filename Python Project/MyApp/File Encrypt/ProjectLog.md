# ProjectLog — File Encrypt

## 2026-11-23 — Bổ sung tự động cài đặt thư viện (có auto-heal), file `.bat` click-là-chay & đồng bộ Skill

### Thay đổi đã thực hiện
- **`main.py` & `Encrypt.py`** (đồng bộ cùng logic):
  - Bổ sung cơ chế tự động kiểm tra và cài đặt 3 thư viện phụ thuộc (`pandas>=2.0.0`, `pyxlsb>=1.0.10`, `pycryptodome>=3.19.0`) trước mọi lệnh `import` ngoài stdlib.
  - Bổ sung **Auto-Heal xung đột gói/chữ hoa-thường trên Windows** (`_heal_windows_package_conflict`): tự phát hiện và gỡ gói `crypto` / `pycrypto` gây trùng thư mục chữ thường `site-packages\crypto` với `Crypto` của `pycryptodome`, dọn thư mục sai chữ hoa rồi cài lại sạch `pycryptodome`; có gói dự phòng `pycryptodomex` (`Cryptodome`) nếu thư mục hệ thống bị khoá quyền.
  - Bọc ngoặc kép chuẩn cho mọi gói có ký tự toán tử (`"pycryptodome>=3.19.0"`) trong lệnh cài thủ công trên hộp thoại fallback để tránh lỗi CMD hiểu nhầm `>` thành chuyển hướng file.
  - Tự động nhận diện `venv` (không truyền `--user` trong venv), cập nhật `site.getusersitepackages()` + `importlib.invalidate_caches()` sau khi cài để chạy ngay lần đầu không cần khởi động lại.
  - Sửa lỗi tương thích Python 3.14 / Tcl-Tk 9.0: đổi `self.header_row.trace("w", ...)` thành `self.header_row.trace_add("write", ...)`.
  - Xử lý thoát sạch triệt để: gắn `WM_DELETE_WINDOW` gọi `root.quit()` + `root.destroy()`, kết thúc `main()` bằng `sys.exit(0)` và hộp thoại thiếu thư viện bằng `sys.exit(2)`.
- **`Run_File_Encrypt.bat`** (chuẩn CRLF):
  - Tự chuyển thư mục (`cd /d "%~dp0"`), bật UTF-8 (`chcp 65001 >nul`), tự dò `python` / `py -3` / `py` (bỏ qua stub Microsoft Store), không dùng khối `if (...)` nhiều dòng chứa dấu `)`.
  - Tự thoát sạch Python và đóng luôn cửa sổ CMD khi mã thoát là `0` (đóng app) hoặc `2` (đóng hộp thoại báo thiếu thư viện); chỉ `pause` khi gặp lỗi crash bất thường.
- **`requirements.txt`**: Khai báo `pandas>=2.0.0`, `pyxlsb>=1.0.10`, `pycryptodome>=3.19.0`.
- **Dọn dẹp**: Đã xoá file rác `3.19.0` sinh ra từ lệnh chưa bọc ngoặc kép trước đó.
- **Nâng cấp & đồng bộ Skill `python_auto_install`**:
  - Cập nhật `SKILL.md` và `SKILL_TEMPLATE.py` tại `Project1\GravityCode\SKILL_RULE\skills\python_auto_install\` và đồng bộ sang `Project2\SettingAILocal`, `~/.gemini/config/skills`, `.agents/skills`.

### Kết quả kiểm thử đã chạy
- `python -m py_compile` cho `main.py`, `Encrypt.py`, `SKILL_TEMPLATE.py`: **Pass**.
- Chạy thực tế auto-heal trên Python 3.14.7 khi đang tồn tại xung đột `crypto 1.4.1`: tự gỡ `crypto-1.4.1` + cài lại sạch `pycryptodome-4.6.0` thành thư mục `Crypto\`, import `Crypto.Cipher.AES`, `pandas 3.0.5`, `pyxlsb 1.0.10`: **Pass**.
- Khởi tạo đủ 3 màn hình GUI (gồm `XlsbToCsvConverter` trên Tcl/Tk 9.0) + mã hoá/giải mã file UTF-8 tiếng Việt: **Pass**.
- Mô phỏng nhánh offline: lệnh cài thủ công đã bọc ngoặc kép chuẩn và thoát sạch với mã `2`: **Pass**.
- Chạy thật `cmd.exe /c Run_File_Encrypt.bat` → cửa sổ `Ứng dụng đa năng` mở sau 3.07s → gửi `WM_CLOSE` → cả `python.exe` và `cmd.exe` thoát sạch hoàn toàn trong 0.53s (mã `0`, không còn tiến trình chạy ngầm): **Pass**.
- Kiểm tra byte-by-byte 4 bản copy của skill `python_auto_install`: **Khớp 100%**.

### Ghi chú tồn đọng
- Chức năng chuyển đổi `.xlsb` → `.csv` đã kiểm tra giao diện & `import pyxlsb`, chưa test với một file `.xlsb` thực tế của người dùng.
- File `Project2\SettingAILocal\sync_skills_rules.py` hiện có đánh dấu merge conflict Git (ngoài phạm vi task này, chưa đụng tới).
