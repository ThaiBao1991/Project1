# -*- coding: utf-8 -*-
"""
Module: check_requirements.py
Mục đích:
- Kiểm tra toàn bộ thư viện cần thiết của hệ thống MBC DeThi.
- Tự động tải và cài đặt phiên bản mới nhất nếu phát hiện máy tính chưa có.
- Nếu quá trình tải bị lỗi (mất mạng, quyền admin, proxy công ty chặn...):
  Hiển thị thông báo chi tiết danh sách thư viện lỗi và cung cấp câu lệnh pip
  để người dùng có thể chạy cài đặt bằng tay.
"""

import sys
import subprocess
import importlib

# Cấu hình encoding stdout để hiển thị tiếng Việt trên Windows CMD không bị lỗi font
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Danh sách toàn bộ thư viện bên ngoài (external packages) mà dự án yêu cầu
REQUIRED_PACKAGES = [
    {
        "import_name": "customtkinter",
        "package_name": "customtkinter",
        "desc": "Giao diện đồ họa Desktop (Dark Mode UI)"
    },
    {
        "import_name": "docx",
        "package_name": "python-docx",
        "desc": "Xử lý, đọc và xuất file Word (.docx) Đề thi & Đáp án"
    },
    {
        "import_name": "fitz",
        "package_name": "pymupdf",
        "desc": "Đọc và trích xuất nội dung từ tài liệu PDF tiêu chuẩn"
    },
    {
        "import_name": "requests",
        "package_name": "requests",
        "desc": "Kết nối và gọi API Google Gemini"
    },
    {
        "import_name": "cryptography",
        "package_name": "cryptography",
        "desc": "Giải mã và bảo mật khóa API Gemini (AES-256)"
    },
]


def is_module_installed(import_name: str) -> bool:
    """Kiểm tra xem thư viện đã được cài đặt và có thể import được hay không."""
    try:
        importlib.import_module(import_name)
        return True
    except ImportError:
        return False
    except Exception:
        # Nếu import lỗi do dependencies bị thiếu bên trong
        return False


def install_package(package_name: str) -> tuple[bool, str]:
    """
    Tự động cài đặt hoặc nâng cấp lên phiên bản mới nhất của thư viện bằng pip.
    Trả về: (thành_công: bool, thông_tin_lỗi: str)
    """
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", package_name]
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        if res.returncode == 0:
            return True, ""
        else:
            err_msg = res.stderr.strip() or res.stdout.strip()
            return False, err_msg
    except Exception as e:
        return False, str(e)


def show_error_dialog(failed_packages: list[dict]):
    """Hiển thị hộp thoại lỗi Windows (GUI) nếu có tkinter."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        failed_names = [p["package_name"] for p in failed_packages]
        pip_cmd = f"pip install {' '.join(failed_names)}"

        details = "\n".join([f"  • {p['package_name']} ({p['desc']})" for p in failed_packages])
        msg = (
            "HỆ THỐNG PHÁT HIỆN THIẾU THƯ VIỆN VÀ KHÔNG THỂ TỰ ĐỘNG TẢI:\n\n"
            f"{details}\n\n"
            "Vui lòng mở Command Prompt / PowerShell và chạy lệnh sau bằng tay:\n\n"
            f"   {pip_cmd}\n\n"
            "Hoặc chạy trong thư mục dự án:\n"
            "   pip install -r requirements.txt"
        )
        messagebox.showerror("Thiếu Thư Viện - Cần Cài Đặt Bằng Tay", msg)
        root.destroy()
    except Exception:
        pass


def ensure_dependencies(show_gui: bool = True, auto_exit_on_fail: bool = True) -> bool:
    """
    Hàm cốt lõi:
    1. Quét kiểm tra tất cả thư viện.
    2. Nếu thiếu, tự động tải bản mới nhất bằng pip.
    3. Nếu tải lỗi, in báo cáo chi tiết và pop-up hướng dẫn pip bằng tay.
    """
    missing_packages = []
    for pkg in REQUIRED_PACKAGES:
        if not is_module_installed(pkg["import_name"]):
            missing_packages.append(pkg)

    # Nếu tất cả đã có đủ, tiếp tục thực thi bình thường
    if not missing_packages:
        return True

    print("=" * 70)
    print(" [KIỂM TRA HỆ THỐNG] Phát hiện thiếu các thư viện sau:")
    for p in missing_packages:
        print(f"   - {p['package_name']} (tên import: {p['import_name']}) -> {p['desc']}")
    print("-" * 70)
    print(" [*] Đang tự động tải và cài đặt phiên bản mới nhất từ PyPI...")
    print("=" * 70)

    failed_packages = []
    installed_packages = []

    for p in missing_packages:
        pkg_name = p["package_name"]
        print(f" [+] Đang tải '{pkg_name}'...", end=" ", flush=True)
        ok, err = install_package(pkg_name)
        if ok and is_module_installed(p["import_name"]):
            print(">> THÀNH CÔNG [OK]")
            installed_packages.append(p)
        else:
            print(">> THẤT BẠI [LỖI]")
            p["error"] = err
            failed_packages.append(p)

    # Trường hợp có thư viện tải bị lỗi
    if failed_packages:
        failed_names = [p["package_name"] for p in failed_packages]
        pip_cmd = f"pip install {' '.join(failed_names)}"

        print("\n" + "!" * 70)
        print(" [!] LỖI CÀI ĐẶT: Không thể tự động tải một số thư viện:")
        for p in failed_packages:
            print(f"\n   * Gói: {p['package_name']}")
            print(f"     Chức năng: {p['desc']}")
            if p.get("error"):
                # In 3 dòng cuối của lỗi pip để dễ chẩn đoán
                err_lines = [l for l in p["error"].splitlines() if l.strip()]
                short_err = "\n       ".join(err_lines[-3:]) if err_lines else p["error"]
                print(f"     Chi tiết lỗi: {short_err}")

        print("\n" + "=" * 70)
        print(" HƯỚNG DẪN CÀI ĐẶT BẰNG TAY (CHẠY LỆNH DƯỚI ĐÂY TRONG CMD / TERMINAL):")
        print(f"    {pip_cmd}")
        print(" hoặc cài toàn bộ danh sách:")
        print("    python -m pip install -r requirements.txt")
        print("=" * 70 + "\n")

        if show_gui:
            show_error_dialog(failed_packages)

        if auto_exit_on_fail:
            try:
                input("Nhấn phím Enter để thoát...")
            except Exception:
                pass
            sys.exit(1)
        return False

    print("\n [✓] Tất cả thư viện đã được cài đặt thành công! Đang tiếp tục...\n")
    return True


if __name__ == "__main__":
    print("=== KIỂM TRA VÀ CÀI ĐẶT THƯ VIỆN DỰ ÁN MBC DETHI ===")
    success = ensure_dependencies(show_gui=True, auto_exit_on_fail=False)
    if success:
        print("[✓] Môi trường Python đã sẵn sàng đầy đủ các thư viện.")
    else:
        sys.exit(1)
