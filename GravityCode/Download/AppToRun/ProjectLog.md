# PyPackGUI — ProjectLog

## Thông tin dự án
- **Tên**: PyPackGUI — Python App Builder
- **Mục đích**: GUI app (CustomTkinter) giúp đóng gói Python app thành .exe mà không cần gõ lệnh
- **Backend**: PyInstaller (chính), cx_Freeze, Nuitka
- **GUI**: CustomTkinter dark mode

## Cấu trúc
`
AppToRun/
├── main.py
├── ProjectLog.md
└── app/
    ├── __init__.py
    ├── ui.py
    ├── builder.py
    ├── config.py
    └── installer.py
`

## Tính năng
- Chọn main.py, App Name, Output, Icon
- Toggle: Onefile/Onedir, Console, UPX
- Add Data / Hidden Imports / Extra Args
- Auto-detect tool (PyInstaller → cx_Freeze → Nuitka)
- Auto-install PyInstaller/Nuitka
- Real-time build log (streaming)
- Lưu/Load config JSON
- Open output folder

---

## Changelog

### 2026-08-13 — v1.0.0 (Initial)
- Tạo toàn bộ project từ đầu
- Dark mode CustomTkinter UI, sidebar nav
- Real-time subprocess streaming log

## Known Issues
- cx_Freeze GUI mode chưa hỗ trợ đầy đủ
- Nuitka cần C compiler (MSVC/MinGW)

### 2026-08-13 — Cập nhật tính năng Đính kèm & Giải nén Dữ liệu
- Nâng cấp UI (pp/ui.py) cho phép thêm danh sách File/Thư mục đính kèm.
- Thêm cơ chế chọn mode: Chỉ đọc (mặc định) hoặc Giải nén (chỉnh sửa được).
- Viết lại pp/builder.py để tự động sinh file pypackgui_wrapper.py khi build nếu có file cần giải nén.
- Logic giải nén: copy đè (overwrite) mọi file cấu hình mới nhất từ ruột .exe ra thư mục bên ngoài.
- Thêm file trợ giúp PyPackHelper.py để hỗ trợ code Python đọc đường dẫn chuẩn.
