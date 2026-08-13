import os
import sys
import tkinter as tk
from tkinter import messagebox

# Auto install dependencies pattern
def check_dependencies():
    try:
        import customtkinter
    except ImportError:
        import subprocess
        root = tk.Tk()
        root.withdraw()
        if messagebox.askyesno("Missing Dependencies", "Thư viện 'customtkinter' chưa được cài đặt. Cài đặt tự động bây giờ?"):
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter"])
                messagebox.showinfo("Success", "Cài đặt thành công. Vui lòng khởi động lại ứng dụng.")
            except Exception as e:
                messagebox.showerror("Error", f"Lỗi cài đặt: {e}")
        sys.exit()

if __name__ == '__main__':
    check_dependencies()
    from app.ui import PyPackGUI
    
    app = PyPackGUI()
    app.mainloop()
