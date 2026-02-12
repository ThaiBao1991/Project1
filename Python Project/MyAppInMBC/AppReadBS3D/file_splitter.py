import tkinter as tk
from tkinter import filedialog, messagebox
import os

class FileSplitter:
    def __init__(self, root, back_to_menu_callback):
        self.root = root
        self.back_to_menu = back_to_menu_callback

        tk.Label(self.root, text="Split và Merge file", font=("Arial", 14, "bold")).pack(pady=10)

        frame = tk.Frame(self.root)
        frame.pack(pady=10)

        self.split_by_size_button = tk.Button(frame, text="Split by Size", command=self.split_by_size_dialog, font=("Arial", 10))
        self.split_by_size_button.grid(row=0, column=0, padx=5, pady=5)

        self.split_by_count_button = tk.Button(frame, text="Split by Count", command=self.split_by_count_dialog, font=("Arial", 10))
        self.split_by_count_button.grid(row=0, column=1, padx=5, pady=5)

        self.merge_files_button = tk.Button(frame, text="Merge Files", command=self.merge_files_dialog, font=("Arial", 10))
        self.merge_files_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

        self.result_label = tk.Label(self.root, text="", font=("Arial", 10))
        self.result_label.pack(pady=10)

        tk.Button(self.root, text="Quay lại menu", command=self.back_to_menu, font=("Arial", 10), bg="gray", fg="white").pack(pady=10)

    def split_by_size(self, file_path, size_mb):
        try:
            size_bytes = int(size_mb) * 1024 * 1024
            if size_bytes <= 0:
                raise ValueError("Size must be greater than 0 MB")

            with open(file_path, 'rb') as f:
                data = f.read()
                total_parts = (len(data) + size_bytes - 1) // size_bytes
                base_name = file_path + ".part_"

                for i in range(total_parts):
                    part_data = data[i * size_bytes:(i + 1) * size_bytes]
                    part_filename = f"{base_name}{str(i + 1).zfill(3)}"
                    with open(part_filename, 'wb') as part_file:
                        part_file.write(part_data)

            self.result_label.config(text=f"File split into {total_parts} parts successfully!")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Error splitting file: {str(e)}")
            return False

    def split_by_count(self, file_path, count):
        try:
            count = int(count)
            if count <= 0:
                raise ValueError("Count must be greater than 0")

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

            self.result_label.config(text=f"File split into {count} parts successfully!")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Error splitting file: {str(e)}")
            return False

    def merge_files(self, file_path):
        try:
            file_dir = os.path.dirname(file_path)
            file_name = os.path.basename(file_path)
            
            if ".part_" in file_name:
                base_name = file_name.split(".part_")[0]
            else:
                base_name, _ = os.path.splitext(file_name)
            
            part_files = [f for f in os.listdir(file_dir) if f.startswith(base_name + ".part_")]
            part_files.sort(key=lambda x: int(x.split('_')[-1]))

            merged_filename = os.path.join(file_dir, f"{base_name}")

            with open(merged_filename, 'wb') as merged_file:
                for part_filename in part_files:
                    part_path = os.path.join(file_dir, part_filename)
                    with open(part_path, 'rb') as part_file:
                        merged_file.write(part_file.read())

            for part_filename in part_files:
                part_path = os.path.join(file_dir, part_filename)
                os.remove(part_path)

            self.result_label.config(text="Files merged successfully!")
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Error merging files: {str(e)}")
            return False

    def split_by_size_dialog(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            top = tk.Toplevel(self.root)
            top.title("Split by Size")
            top.geometry("300x100")
            entry_label = tk.Label(top, text="Enter size (MB):")
            entry_label.pack()
            size_entry = tk.Entry(top)
            size_entry.pack()
            split_button = tk.Button(top, text="Split", 
                                   command=lambda: [self.split_by_size(file_path, size_entry.get()), 
                                                  top.destroy() if self.split_by_size(file_path, size_entry.get()) else None])
            split_button.pack()

    def split_by_count_dialog(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            top = tk.Toplevel(self.root)
            top.title("Split by Count")
            top.geometry("300x100")
            entry_label = tk.Label(top, text="Enter count:")
            entry_label.pack()
            count_entry = tk.Entry(top)
            count_entry.pack()
            split_button = tk.Button(top, text="Split", 
                                   command=lambda: [self.split_by_count(file_path, count_entry.get()), 
                                                  top.destroy() if self.split_by_count(file_path, count_entry.get()) else None])
            split_button.pack()

    def merge_files_dialog(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            self.merge_files(file_path)