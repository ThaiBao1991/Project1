"""
AlowGPT - DPI & SNI Bypass Desktop Tool for ChatGPT
Entry point to launch the application.
"""

import sys
import os

def main():
    try:
        from app_gui import run_app
        run_app()
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            import tkinter.messagebox as mb
            mb.showerror("Lỗi Khởi Động", f"Không thể khởi chạy ứng dụng:\n{e}")
        except Exception:
            pass

if __name__ == "__main__":
    main()
