import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

def delete_files_in_folder(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                os.remove(file_path)
                print(f"Đã xóa file: {file_path}")
            except Exception as e:
                print(f"Lỗi khi xóa file {file_path}: {e}")

def select_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        confirm = messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa tất cả các file trong thư mục này và các thư mục con?")
        if confirm:
            delete_files_in_folder(folder_path)
            messagebox.showinfo("Thông báo", "Đã xóa tất cả các file trong thư mục và các thư mục con!")

# Tạo giao diện
root = tk.Tk()
root.title("Xóa File trong Thư mục")

frame = tk.Frame(root)
frame.pack(padx=20, pady=20)

label = tk.Label(frame, text="Chọn thư mục để xóa các file bên trong:")
label.pack(pady=10)

button = tk.Button(frame, text="Chọn Thư mục", command=select_folder)
button.pack(pady=10)

root.mainloop()