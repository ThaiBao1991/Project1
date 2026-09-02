import sys
import os
import subprocess

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Danh sách thư viện yêu cầu
REQUIRED_PACKAGES = {
    'PyQt6': 'PyQt6>=6.7.0',
    'requests': 'requests>=2.31.0',
    'bs4': 'beautifulsoup4>=4.12.0',
    'cloudscraper': 'cloudscraper>=1.2.71',
    'lxml': 'lxml>=5.2.0',
}

def check_and_install_packages():
    missing = []
    for module_name, pip_name in REQUIRED_PACKAGES.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(pip_name)
            
    if missing:
        print(f"[*] Đang tự động cài đặt thư viện còn thiếu: {', '.join(missing)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
            print("[*] Cài đặt thành công!")
        except Exception as e:
            try:
                import tkinter as tk
                from tkinter import Tk, Label, Text, Button, END
                root = Tk()
                root.withdraw()
                err_win = tk.Toplevel(root)
                err_win.title("Lỗi Thiếu Thư Viện")
                err_win.geometry("550x300")
                Label(err_win, text="Ứng dụng thiếu một số thư viện cần thiết và không thể cài đặt tự động.", fg="red", font=("Arial", 11, "bold")).pack(pady=10)
                Label(err_win, text="Vui lòng copy dòng lệnh dưới đây và dán vào Terminal/CMD để cài đặt:", font=("Arial", 10)).pack(pady=5)
                
                txt = Text(err_win, height=3, width=60, font=("Consolas", 11))
                txt.pack(pady=10)
                cmd = f'"{sys.executable}" -m pip install ' + " ".join(missing)
                txt.insert(END, cmd)
                txt.config(state="disabled")
                
                Button(err_win, text="Thoát ứng dụng", command=root.destroy, width=15).pack(pady=15)
                root.mainloop()
            except Exception:
                pass
            sys.exit(1)

# Kiểm tra và tự động cài đặt thư viện trước khi load GUI
check_and_install_packages()

from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

