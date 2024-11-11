import tkinter as tk
from tkinter import filedialog
import os
# CHỉ hoạt động được với split by count còn chưa thể merge hoặc split by size
def split_by_size(file_path, size_mb):
    try:
        size_bytes = size_mb * 1024 * 1024
        with open(file_path, 'rb') as f:
            data = f.read()
            total_parts = len(data) // size_bytes + 1
            for i in range(total_parts):
                part_data = data[i * size_bytes:(i + 1) * size_bytes]
                part_filename = f"{file_path}.{str(i + 1).zfill(3)}"
                with open(part_filename, 'wb') as part_file:
                    part_file.write(part_data)
        return True
    except Exception as e:
        print(f"Error splitting file: {str(e)}")
        return False

def split_by_count(file_path, count):
    try:
        with open(file_path, 'rb') as f:
            data = f.read()
            total_parts = count
            size_bytes = len(data) // total_parts + 1
            for i in range(total_parts):
                part_data = data[i * size_bytes:(i + 1) * size_bytes]
                part_filename = f"{file_path}.{str(i + 1).zfill(3)}"
                with open(part_filename, 'wb') as part_file:
                    part_file.write(part_data)
        return True
    except Exception as e:
        print(f"Error splitting file: {str(e)}")
        return False

def merge_files(file_path):
    try:
        file_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        base_name = os.path.splitext(file_name)[0]
        merged_filename = os.path.join(file_dir, f"{base_name}.merged")
        with open(merged_filename, 'wb') as merged_file:
            part_num = 1
            while True:
                part_filename = f"{file_path}.{str(part_num).zfill(3)}"
                if os.path.isfile(part_filename):
                    with open(part_filename, 'rb') as part_file:
                        merged_file.write(part_file.read())
                    part_num += 1
                else:
                    break
        os.remove(file_path)  # Xóa file gốc đã được nối
        for i in range(2, part_num):
            part_filename = f"{file_path}.{str(i).zfill(3)}"
            os.remove(part_filename)  # Xóa các file phần
        return True
    except Exception as e:
        print(f"Error merging files: {str(e)}")
        return False

def open_file_dialog():
    file_path = filedialog.askopenfilename()
    if file_path:
        merge_files(file_path)

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
        split_button = tk.Button(top, text="Split", command=lambda: split_by_size(file_path, float(size_entry.get())))
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
        split_button = tk.Button(top, text="Split", command=lambda: split_by_count(file_path, int(count_entry.get())))
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