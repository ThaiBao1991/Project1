import tkinter as tk
from tkinter import filedialog, messagebox
import os

def select_directory():
    """Opens a dialog to select a directory and updates the directory entry."""
    directory = filedialog.askdirectory()
    if directory:
        dir_entry.delete(0, tk.END)
        dir_entry.insert(0, directory)

def start_listing():
    """
    Lists files with the specified extension in the selected directory,
    removes the extension, sorts them, and copies them to the clipboard.
    """
    selected_directory = dir_entry.get()
    file_extension = ext_entry.get().strip()

    if not selected_directory:
        messagebox.showwarning("Lỗi nhập liệu", "Vui lòng chọn một thư mục.")
        return

    if not file_extension:
        messagebox.showwarning("Lỗi nhập liệu", "Vui lòng nhập đuôi file.")
        return

    # Thêm dấu chấm vào đuôi mở rộng nếu chưa có
    if not file_extension.startswith('.'):
        file_extension = '.' + file_extension

    try:
        found_file_names_without_extension = []
        for filename in os.listdir(selected_directory):
            if filename.endswith(file_extension):
                # Bỏ đuôi mở rộng khỏi tên file
                name_without_extension = filename[:-len(file_extension)]
                found_file_names_without_extension.append(name_without_extension)

        found_file_names_without_extension.sort()  # Sắp xếp tên file theo thứ tự ABC

        if not found_file_names_without_extension:
            messagebox.showinfo("Không tìm thấy file", f"Không tìm thấy file có đuôi '{file_extension}' trong thư mục đã chọn.")
            return

        # Chuẩn bị danh sách để copy vào clipboard, mỗi file trên một dòng mới
        files_to_copy = "\n".join(found_file_names_without_extension)
        root.clipboard_clear()
        root.clipboard_append(files_to_copy)
        messagebox.showinfo("Thành công", f"Đã sao chép {len(found_file_names_without_extension)} tên file vào clipboard!")

    except FileNotFoundError:
        messagebox.showerror("Lỗi", "Thư mục đã chọn không tồn tại.")
    except Exception as e:
        messagebox.showerror("Đã xảy ra lỗi", str(e))

# --- Cài đặt GUI ---
root = tk.Tk()
root.title("Ứng dụng Liệt kê File")

# Chọn thư mục
dir_frame = tk.Frame(root, padx=10, pady=10)
dir_frame.pack(fill=tk.X)

dir_label = tk.Label(dir_frame, text="Thư mục đã chọn:")
dir_label.pack(side=tk.LEFT, padx=(0, 5))

dir_entry = tk.Entry(dir_frame, width=50)
dir_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

browse_button = tk.Button(dir_frame, text="Duyệt", command=select_directory)
browse_button.pack(side=tk.LEFT, padx=(5, 0))

# Nhập đuôi file
ext_frame = tk.Frame(root, padx=10, pady=5)
ext_frame.pack(fill=tk.X)

ext_label = tk.Label(ext_frame, text="Đuôi file (ví dụ: mp4, txt):")
ext_label.pack(side=tk.LEFT, padx=(0, 5))

ext_entry = tk.Entry(ext_frame, width=20)
ext_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)

# Nút Bắt đầu
start_button = tk.Button(root, text="Bắt đầu Liệt kê và Sao chép", command=start_listing, padx=20, pady=10)
start_button.pack(pady=10)

root.mainloop()