import tkinter as tk
from tkinter import messagebox
import English
import Japan
import Chinese
import sys
import os

# Xử lý sys.stdout/sys.stderr cho --noconsole
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

def resource_path(relative_path):
    """Lấy đường dẫn tuyệt đối đến tài nguyên, hoạt động cho cả dev và PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        # Đường dẫn đến thư mục tạm khi chạy file .exe
        base_path = sys._MEIPASS
    else:
        # Đường dẫn khi chạy mã nguồn
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def open_english():
    root.withdraw()  # Ẩn cửa sổ chính
    try:
        English.english_menu(root)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể mở module tiếng Anh: {str(e)}")
        root.deiconify()

def open_japan():
    root.withdraw()
    try:
        Japan.japan_menu(root)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể mở module tiếng Nhật: {str(e)}")
        root.deiconify()

def open_chinese():
    root.withdraw()
    try:
        Chinese.chinese_menu(root)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể mở module tiếng Trung: {str(e)}")
        root.deiconify()

def exit_program():
    root.quit()  # Thoát hoàn toàn chương trình

# Tạo cửa sổ chính
root = tk.Tk()
root.title("Chương trình ôn từ vựng")
root.geometry("300x200")

# Tiêu đề
title_label = tk.Label(root, text="Chọn ngôn ngữ để ôn", font=("Arial", 14))
title_label.pack(pady=20)

# Nút chọn ngôn ngữ
btn_english = tk.Button(root, text="Tiếng Anh", command=open_english, width=20)
btn_english.pack(pady=5)

btn_japan = tk.Button(root, text="Tiếng Nhật", command=open_japan, width=20)
btn_japan.pack(pady=5)

btn_chinese = tk.Button(root, text="Tiếng Trung", command=open_chinese, width=20)
btn_chinese.pack(pady=5)

btn_exit = tk.Button(root, text="Thoát", command=exit_program, width=20)
btn_exit.pack(pady=5)

# Bind Esc để thoát hoàn toàn
root.bind("<Escape>", lambda event: root.quit())

# Chạy chương trình
root.mainloop()