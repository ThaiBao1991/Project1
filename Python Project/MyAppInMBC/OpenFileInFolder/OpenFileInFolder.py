import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import subprocess
import platform

class FileOpenerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Opener - Mở nhiều file cùng lúc")
        self.root.geometry("600x400")
        
        # Biến lưu trữ
        self.selected_folder = tk.StringVar()
        self.file_extensions = tk.StringVar()
        self.num_files_to_open = tk.StringVar()
        self.all_files = []
        
        # Tạo giao diện
        self.create_widgets()
        
    def create_widgets(self):
        # Frame chính
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 1. Chọn thư mục
        ttk.Label(main_frame, text="1. Chọn thư mục:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.selected_folder, width=50)
        self.folder_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(folder_frame, text="Duyệt...", command=self.select_folder).pack(side=tk.LEFT)
        
        # 2. Nhập các loại đuôi file
        ttk.Label(main_frame, text="2. Nhập các đuôi file (cách nhau bằng dấu phẩy):").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        ext_frame = ttk.Frame(main_frame)
        ext_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(ext_frame, text="Ví dụ: pdf,doc,docx,xlsx,ppt,pptx").pack(anchor=tk.W)
        self.ext_entry = ttk.Entry(ext_frame, textvariable=self.file_extensions, width=50)
        self.ext_entry.pack(fill=tk.X, pady=5)
        
        # 3. Số lượng file mở
        ttk.Label(main_frame, text="3. Số lượng file sẽ mở:").grid(row=4, column=0, sticky=tk.W, pady=5)
        
        num_frame = ttk.Frame(main_frame)
        num_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(num_frame, text="Nhập số (0 để mở tất cả):").pack(anchor=tk.W)
        self.num_entry = ttk.Entry(num_frame, textvariable=self.num_files_to_open, width=20)
        self.num_entry.pack(anchor=tk.W, pady=5)
        
        # Nút thực thi
        ttk.Button(main_frame, text="Mở File", command=self.open_files, 
                  style="Accent.TButton").grid(row=6, column=0, pady=20)
        
        # Khung hiển thị danh sách file
        ttk.Label(main_frame, text="Danh sách file tìm thấy:").grid(row=7, column=0, sticky=tk.W, pady=5)
        
        # Tạo Treeview để hiển thị file
        tree_frame = ttk.Frame(main_frame)
        tree_frame.grid(row=8, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree = ttk.Treeview(tree_frame, columns=("STT", "Tên file", "Đường dẫn"), 
                                 show="headings", yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)
        
        self.tree.heading("STT", text="STT")
        self.tree.heading("Tên file", text="Tên file")
        self.tree.heading("Đường dẫn", text="Đường dẫn")
        
        self.tree.column("STT", width=50)
        self.tree.column("Tên file", width=200)
        self.tree.column("Đường dẫn", width=300)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Thanh trạng thái
        self.status_var = tk.StringVar()
        self.status_var.set("Sẵn sàng")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Cấu hình grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(8, weight=1)
        
    def select_folder(self):
        """Mở dialog chọn thư mục"""
        folder = filedialog.askdirectory()
        if folder:
            self.selected_folder.set(folder)
            self.scan_files()
    
    def scan_files(self):
        """Quét các file trong thư mục đã chọn"""
        folder = self.selected_folder.get()
        if not folder:
            return
        
        extensions = self.file_extensions.get().strip()
        if not extensions:
            return
        
        # Xử lý danh sách đuôi file
        ext_list = [ext.strip().lower() for ext in extensions.split(',')]
        ext_list = [ext if ext.startswith('.') else f'.{ext}' for ext in ext_list]
        
        # Quét file
        self.all_files = []
        try:
            for file in Path(folder).iterdir():
                if file.is_file() and file.suffix.lower() in ext_list:
                    self.all_files.append(str(file))
            
            # Sắp xếp theo tên
            self.all_files.sort()
            
            # Hiển thị danh sách
            self.update_file_list()
            
            self.status_var.set(f"Tìm thấy {len(self.all_files)} file")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể quét thư mục: {str(e)}")
    
    def update_file_list(self):
        """Cập nhật danh sách file lên Treeview"""
        # Xóa dữ liệu cũ
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Thêm dữ liệu mới
        for idx, file_path in enumerate(self.all_files, 1):
            file_name = os.path.basename(file_path)
            self.tree.insert("", "end", values=(idx, file_name, file_path))
    
    def open_files(self):
        """Mở file theo số lượng yêu cầu"""
        if not self.all_files:
            messagebox.showwarning("Cảnh báo", "Không có file nào để mở!")
            return
        
        # Lấy số lượng file cần mở
        try:
            num_to_open = int(self.num_files_to_open.get())
        except ValueError:
            messagebox.showerror("Lỗi", "Vui lòng nhập số hợp lệ!")
            return
        
        # Xác định số lượng file thực tế sẽ mở
        if num_to_open <= 0:
            files_to_open = self.all_files
        else:
            files_to_open = self.all_files[:num_to_open]
        
        if not files_to_open:
            messagebox.showwarning("Cảnh báo", "Không có file nào để mở!")
            return
        
        # Xác nhận trước khi mở
        confirm = messagebox.askyesno(
            "Xác nhận", 
            f"Bạn có chắc muốn mở {len(files_to_open)} file không?"
        )
        
        if not confirm:
            return
        
        # Mở các file
        opened_count = 0
        failed_files = []
        
        for file_path in files_to_open:
            try:
                if platform.system() == 'Windows':
                    os.startfile(file_path)
                elif platform.system() == 'Darwin':  # macOS
                    subprocess.run(['open', file_path])
                else:  # Linux
                    subprocess.run(['xdg-open', file_path])
                opened_count += 1
            except Exception as e:
                failed_files.append(os.path.basename(file_path))
        
        # Thông báo kết quả
        if failed_files:
            messagebox.showwarning(
                "Cảnh báo", 
                f"Đã mở thành công {opened_count}/{len(files_to_open)} file.\n"
                f"Không thể mở các file: {', '.join(failed_files)}"
            )
        else:
            messagebox.showinfo("Thành công", f"Đã mở thành công {opened_count} file!")
        
        self.status_var.set(f"Đã mở {opened_count} file")
    
    def on_ext_change(self, *args):
        """Tự động quét lại file khi thay đổi đuôi file"""
        if self.selected_folder.get():
            self.scan_files()

def main():
    root = tk.Tk()
    app = FileOpenerApp(root)
    
    # Bind sự kiện khi thay đổi đuôi file
    app.file_extensions.trace('w', lambda *args: app.on_ext_change())
    
    root.mainloop()

if __name__ == "__main__":
    main()