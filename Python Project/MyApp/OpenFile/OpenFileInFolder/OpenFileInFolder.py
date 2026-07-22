import tkinter as tk
from tkinter import filedialog, messagebox
import os
import webbrowser

def open_files():
    folder_path = entry_path.get()
    extensions = entry_ext.get().split(',')  # Lấy danh sách đuôi file
    max_files = entry_max.get()

    if not folder_path or not os.path.exists(folder_path):
        messagebox.showerror("Lỗi", "Vui lòng chọn thư mục hợp lệ!")
        return

    # Lấy danh sách tất cả file
    files_to_open = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # Kiểm tra đuôi file (nếu ô đuôi trống thì mở tất cả)
            if not entry_ext.get() or any(file.lower().endswith(ext.strip().lower()) for ext in extensions):
                files_to_open.append(os.path.join(root, file))

    # Giới hạn số lượng
    if max_files.isdigit():
        files_to_open = files_to_open[:int(max_files)]

    if not files_to_open:
        messagebox.showinfo("Thông báo", "Không tìm thấy file nào khớp yêu cầu.")
        return

    # Mở file
    for f in files_to_open:
        try:
            os.startfile(f) # Dùng cho Windows
        except:
            webbrowser.open(f)

    messagebox.showinfo("Hoàn tất", f"Đã mở {len(files_to_open)} file.")

# Thiết lập giao diện
root = tk.Tk()
root.title("Công cụ mở File tự động")

tk.Label(root, text="Chọn thư mục:").grid(row=0, column=0)
entry_path = tk.Entry(root, width=50)
entry_path.grid(row=0, column=1)
tk.Button(root, text="Duyệt", command=lambda: entry_path.insert(0, filedialog.askdirectory())).grid(row=0, column=2)

tk.Label(root, text="Đuôi file (VD: .pdf, .docx):").grid(row=1, column=0)
entry_ext = tk.Entry(root, width=50)
entry_ext.grid(row=1, column=1)

tk.Label(root, text="Số lượng tối đa (để trống = mở hết):").grid(row=2, column=0)
entry_max = tk.Entry(root, width=50)
entry_max.grid(row=2, column=1)

tk.Button(root, text="Mở tất cả file", command=open_files).grid(row=3, column=1, pady=20)

root.mainloop()