import os
import squarify
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import filedialog, messagebox

# File lưu cấu hình
CONFIG_FILE = "config.txt"

# Hàm đọc cấu hình từ file
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) >= 2:
                exclude_folders_var.set(lines[0].strip())
                exclude_extensions_var.set(lines[1].strip())

# Hàm lưu cấu hình vào file
def save_config(exclude_folders, exclude_extensions):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        f.write(f"{exclude_folders}\n")
        f.write(f"{exclude_extensions}\n")

# Hàm tính kích thước của thư mục và các tệp con, có lọc thư mục và định dạng file
def get_directory_sizes(directory, exclude_folders=None, exclude_extensions=None):
    if exclude_folders is None:
        exclude_folders = []
    if exclude_extensions is None:
        exclude_extensions = []
    
    sizes = []
    labels = []
    
    for item in os.listdir(directory):
        if item in exclude_folders:
            continue
        
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path):
            file_extension = os.path.splitext(item)[1].lower().lstrip('.')
            if file_extension in exclude_extensions:
                continue
            size = os.path.getsize(item_path)
            sizes.append(size)
            labels.append(item)
        elif os.path.isdir(item_path):
            total_size = 0
            for root, dirs, files in os.walk(item_path):
                dirs[:] = [d for d in dirs if d not in exclude_folders]
                for file in files:
                    file_extension = os.path.splitext(file)[1].lower().lstrip('.')
                    if file_extension in exclude_extensions:
                        continue
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
            if total_size > 0:
                sizes.append(total_size)
                labels.append(item)
    
    return sizes, labels

# Hàm xuất cấu trúc thư mục vào file tree.md, có lọc thư mục và định dạng file
def export_directory_tree(directory, output_file, exclude_folders=None, exclude_extensions=None):
    if exclude_folders is None:
        exclude_folders = []
    if exclude_extensions is None:
        exclude_extensions = []
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Directory Tree for: {directory}\n\n")
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in exclude_folders]
            level = root.replace(directory, '').count(os.sep)
            indent = ' ' * 4 * level
            f.write(f"{indent}- {os.path.basename(root)}/\n")
            sub_indent = ' ' * 4 * (level + 1)
            for file in files:
                file_extension = os.path.splitext(file)[1].lower().lstrip('.')
                if file_extension in exclude_extensions:
                    continue
                f.write(f"{sub_indent}- {file}\n")

# Hàm xử lý khi nhấn nút Start
def start_processing():
    directory = directory_var.get()
    if not directory:
        messagebox.showerror("Error", "Please select a directory first!")
        return
    
    # Lấy danh sách thư mục và định dạng file cần loại trừ
    exclude_folders = [folder.strip() for folder in exclude_folders_var.get().split(',') if folder.strip()]
    exclude_extensions = [ext.strip().lower() for ext in exclude_extensions_var.get().split(',') if ext.strip()]
    
    try:
        # Lấy kích thước và nhãn để vẽ treemap
        sizes, labels = get_directory_sizes(directory, exclude_folders, exclude_extensions)
        
        if not sizes:
            messagebox.showwarning("Warning", "No data to display after filtering!")
            return
        
        # Vẽ treemap
        plt.figure(figsize=(12, 8))
        squarify.plot(sizes=sizes, label=labels, alpha=0.8)
        plt.title(f"Treemap of Directory: {directory}")
        plt.axis('off')
        treemap_path = os.path.join(directory, 'directory_treemap.png')
        plt.savefig(treemap_path, bbox_inches='tight')
        plt.close()
        
        # Xuất cấu trúc thư mục vào file tree.md
        tree_path = os.path.join(directory, 'tree.md')
        export_directory_tree(directory, tree_path, exclude_folders, exclude_extensions)
        
        # Lưu cấu hình
        save_config(exclude_folders_var.get(), exclude_extensions_var.get())
        
        messagebox.showinfo("Success", f"Treemap saved as {treemap_path}\nTree structure saved as {tree_path}")
    
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

# Hàm chọn thư mục
def browse_directory():
    directory = filedialog.askdirectory()
    if directory:
        directory_var.set(directory)

# Tạo giao diện UI
root = tk.Tk()
root.title("Directory Treemap Generator")
root.geometry("400x300")

# Biến lưu đường dẫn thư mục, thư mục loại trừ, và định dạng file loại trừ
directory_var = tk.StringVar()
exclude_folders_var = tk.StringVar()
exclude_extensions_var = tk.StringVar()

# Đọc cấu hình từ file (nếu có)
load_config()

# Tạo các thành phần UI
tk.Label(root, text="Select Directory:").pack(pady=5)
tk.Entry(root, textvariable=directory_var, width=40).pack(pady=5)
tk.Button(root, text="Browse", command=browse_directory).pack(pady=5)

tk.Label(root, text="Exclude Folders (comma-separated):").pack(pady=5)
tk.Entry(root, textvariable=exclude_folders_var, width=40).pack(pady=5)

tk.Label(root, text="Exclude File Extensions (comma-separated):").pack(pady=5)
tk.Entry(root, textvariable=exclude_extensions_var, width=40).pack(pady=5)

tk.Button(root, text="Start", command=start_processing).pack(pady=10)

# Chạy giao diện
root.mainloop()