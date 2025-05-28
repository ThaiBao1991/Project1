import tkinter as tk
from tkinter import filedialog, messagebox
import os

def split_by_size(file_path, size_mb):
    try:
        size_bytes = int(size_mb) * 1024 * 1024
        if size_bytes <= 0:
            messagebox.showerror("Error", "Size must be greater than 0 MB")
            return False

        with open(file_path, 'rb') as f:
            data = f.read()
            total_parts = (len(data) + size_bytes - 1) // size_bytes
            base_name = file_path + ".part_"

            for i in range(total_parts):
                part_data = data[i * size_bytes:(i + 1) * size_bytes]
                part_filename = f"{base_name}{str(i + 1).zfill(3)}"
                with open(part_filename, 'wb') as part_file:
                    part_file.write(part_data)

        messagebox.showinfo("Success", f"File split into {total_parts} parts successfully!")
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Error splitting file: {str(e)}")
        return False

def split_by_count(file_path, count):
    try:
        count = int(count)
        if count <= 0:
            messagebox.showerror("Error", "Count must be greater than 0")
            return False

        with open(file_path, 'rb') as f:
            data = f.read()
            total_size = len(data)
            part_size = (total_size + count - 1) // count
            base_name = file_path + ".part_"

            for i in range(count):
                part_data = data[i * part_size:(i + 1) * part_size]
                part_filename = f"{base_name}{str(i + 1).zfill(3)}"
                with open(part_filename, 'wb') as part_file:
                    part_file.write(part_data)

        messagebox.showinfo("Success", f"File split into {count} parts successfully!")
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Error splitting file: {str(e)}")
        return False

def merge_files(file_path):
    try:
        file_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        base_name, ext = os.path.splitext(file_name)
        merged_filename = os.path.join(file_dir, f"{base_name}_merged{ext}")

        # Tìm tất cả các phần tệp tin có cùng tên gốc
        part_files = [f for f in os.listdir(file_dir) if f.startswith(base_name + ".part_")]

        # Sắp xếp theo thứ tự số phần
        part_files.sort(key=lambda x: int(x.split('_')[-1]))

        with open(merged_filename, 'wb') as merged_file:
            for part_filename in part_files:
                part_path = os.path.join(file_dir, part_filename)
                with open(part_path, 'rb') as part_file:
                    merged_file.write(part_file.read())

        # Xóa các phần tệp tin đã nối
        for part_filename in part_files:
            part_path = os.path.join(file_dir, part_filename)
            os.remove(part_path)

        messagebox.showinfo("Success", "Files merged successfully!")
        return True
    except Exception as e:
        messagebox.showerror("Error", f"Error merging files: {str(e)}")
        return False

def open_file_dialog():
    file_path = filedialog.askopenfilename()  # Hiển thị hộp thoại chọn tệp tin
    if file_path:
        merge_result = merge_files(file_path)
        if merge_result:
            print("Files merged successfully!")
        else:
            print("Error merging files.")

def split_by_size_dialog():
    file_path = filedialog.askopenfilename()
    if file_path:
        top = tk.Toplevel()
        top.title("Split by Size")
        top.geometry("300x100")
        entry_label = tk.Label(top, text="Enter size (MB):")
        entry_label.pack()
        size_entry = tk.Entry(top)
        size_entry.pack()
        split_button = tk.Button(top, text="Split", command=lambda: split_by_size(file_path, size_entry.get()))
        split_button.pack()

def split_by_count_dialog():
    file_path = filedialog.askopenfilename()
    if file_path:
        top = tk.Toplevel()
        top.title("Split by Count")
        top.geometry("300x100")
        entry_label = tk.Label(top, text="Enter count:")
        entry_label.pack()
        count_entry = tk.Entry(top)
        count_entry.pack()
        split_button = tk.Button(top, text="Split", command=lambda: split_by_count(file_path, count_entry.get()))
        split_button.pack()

root = tk.Tk()
root.title("File Splitter & Merger")
root.geometry("300x200")

split_by_size_button = tk.Button(root, text="Split by Size", command=split_by_size_dialog)
split_by_size_button.pack()

split_by_count_button = tk.Button(root, text="Split by Count", command=split_by_count_dialog)
split_by_count_button.pack()

merge_files_button = tk.Button(root, text="Merge Files", command=open_file_dialog)
merge_files_button.pack()

root.mainloop()