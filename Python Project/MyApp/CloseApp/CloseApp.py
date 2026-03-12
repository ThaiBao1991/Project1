
import tkinter as tk
from tkinter import messagebox
import psutil
import os

def kill_processes_by_keyword(keyword):
    keyword = keyword.lower()
    killed = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if keyword in proc.info['name'].lower():
                os.kill(proc.info['pid'], 9)
                killed.append(proc.info['name'])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return killed

def on_kill_button_click():
    keyword = entry.get().strip()
    if not keyword:
        messagebox.showwarning("Cảnh báo", "Vui lòng nhập từ khóa!")
        return
    killed = kill_processes_by_keyword(keyword)
    if killed:
        messagebox.showinfo("Thành công", f"Đã thoát các tiến trình:\n" + "\n".join(killed))
    else:
        messagebox.showinfo("Không tìm thấy", "Không có tiến trình nào phù hợp.")

# Giao diện
root = tk.Tk()
root.title("Tắt ứng dụng theo từ khóa")

tk.Label(root, text="Nhập từ khóa (ví dụ: exc):").pack(pady=5)
entry = tk.Entry(root, width=30)
entry.pack(pady=5)

tk.Button(root, text="Tắt ứng dụng", command=on_kill_button_click).pack(pady=10)

root.mainloop()
