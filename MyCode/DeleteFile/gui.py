"""
Xây dựng giao diện người dùng với tkinter
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
from typing import Optional
from config_manager import ConfigManager
from file_deleter import FileDeleter
import os

class FileDeleterGUI:
    """Giao diện chính cho ứng dụng xóa file"""
    
    def __init__(self, root: tk.Tk, config_manager: ConfigManager):
        """
        Khởi tạo giao diện
        
        Args:
            root: Root window của tkinter
            config_manager: Instance của ConfigManager
        """
        self.root = root
        self.config_manager = config_manager
        self.file_deleter = FileDeleter(config_manager)
        self.current_delete_thread: Optional[threading.Thread] = None
        self.is_deleting = False
        
        self.root.title("File Deleter - Xóa File Thông Minh")
        self.root.geometry("900x700")
        
        self.setup_ui()
        self.load_current_config()
    
    def setup_ui(self):
        """Thiết lập tất cả các thành phần giao diện"""
        
        # Notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab 1: Xóa file
        self.delete_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.delete_tab, text="Xóa File")
        self.setup_delete_tab()
        
        # Tab 2: Cấu hình ngoại lệ
        self.config_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.config_tab, text="Cấu Hình Ngoại Lệ")
        self.setup_config_tab()
    
    def setup_delete_tab(self):
        """Thiết lập tab xóa file"""
        
        # Frame chính
        main_frame = ttk.Frame(self.delete_tab, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Chọn thư mục
        folder_frame = ttk.LabelFrame(main_frame, text="Chọn Thư Mục Để Xóa", padding="10")
        folder_frame.pack(fill="x", pady=(0, 10))
        
        self.folder_path_var = tk.StringVar()
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path_var, width=70)
        folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        browse_btn = ttk.Button(folder_frame, text="Chọn Thư Mục", command=self.browse_folder)
        browse_btn.pack(side="right")
        
        # Progress bar
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill="x", pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                           maximum=100, mode='determinate')
        self.progress_bar.pack(fill="x", pady=(0, 5))
        
        self.progress_label = ttk.Label(progress_frame, text="Sẵn sàng")
        self.progress_label.pack()
        
        # Button xóa
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(0, 10))
        
        self.delete_btn = ttk.Button(button_frame, text="BẮT ĐẦU XÓA", command=self.start_delete,
                                     style="Accent.TButton")
        self.delete_btn.pack()
        
        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Nhật Ký Xóa", padding="10")
        log_frame.pack(fill="both", expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80,
                                                  wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True)
        
        # Thêm style cho button
        style = ttk.Style()
        style.configure("Accent.TButton", foreground="red", font=("", 10, "bold"))
        
        # Thống kê
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill="x", pady=(10, 0))
        
        self.stats_label = ttk.Label(stats_frame, text="Đã xóa: 0 | Bỏ qua: 0 | Lỗi: 0", 
                                    font=("", 10))
        self.stats_label.pack()
    
    def setup_config_tab(self):
        """Thiết lập tab cấu hình ngoại lệ"""
        
        # Tạo paned window để chia đôi màn hình
        paned = ttk.PanedWindow(self.config_tab, orient="horizontal")
        paned.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Left panel: Folder exceptions
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)
        
        # Folder exceptions
        folder_frame = ttk.LabelFrame(left_frame, text="Folder Không Xóa (Đường Dẫn Tuyệt Đối)", 
                                     padding="10")
        folder_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.folder_listbox = tk.Listbox(folder_frame, height=8)
        self.folder_listbox.pack(fill="both", expand=True, pady=(0, 5))
        
        folder_btn_frame = ttk.Frame(folder_frame)
        folder_btn_frame.pack(fill="x")
        
        ttk.Button(folder_btn_frame, text="Thêm Folder", 
                  command=self.add_excluded_folder).pack(side="left", padx=(0, 5))
        ttk.Button(folder_btn_frame, text="Xóa Folder", 
                  command=self.remove_excluded_folder).pack(side="left")
        
        # Folder keywords
        folder_kw_frame = ttk.LabelFrame(left_frame, text="Tên Folder Chứa Từ Khóa (Không Xóa)", 
                                        padding="10")
        folder_kw_frame.pack(fill="both", expand=True)
        
        self.folder_kw_listbox = tk.Listbox(folder_kw_frame, height=6)
        self.folder_kw_listbox.pack(fill="both", expand=True, pady=(0, 5))
        
        folder_kw_entry_frame = ttk.Frame(folder_kw_frame)
        folder_kw_entry_frame.pack(fill="x")
        
        self.folder_kw_var = tk.StringVar()
        ttk.Entry(folder_kw_entry_frame, textvariable=self.folder_kw_var).pack(side="left", 
                                                                               fill="x", 
                                                                               expand=True, 
                                                                               padx=(0, 5))
        ttk.Button(folder_kw_entry_frame, text="Thêm", 
                  command=self.add_folder_keyword).pack(side="right")
        
        # Right panel: File exceptions
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        
        # File exceptions
        file_frame = ttk.LabelFrame(right_frame, text="File Không Xóa (Đường Dẫn Tuyệt Đối)", 
                                   padding="10")
        file_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        self.file_listbox = tk.Listbox(file_frame, height=8)
        self.file_listbox.pack(fill="both", expand=True, pady=(0, 5))
        
        file_btn_frame = ttk.Frame(file_frame)
        file_btn_frame.pack(fill="x")
        
        ttk.Button(file_btn_frame, text="Thêm File", 
                  command=self.add_excluded_file).pack(side="left", padx=(0, 5))
        ttk.Button(file_btn_frame, text="Xóa File", 
                  command=self.remove_excluded_file).pack(side="left")
        
        # File keywords
        file_kw_frame = ttk.LabelFrame(right_frame, text="Tên File Chứa Từ Khóa (Không Xóa)", 
                                      padding="10")
        file_kw_frame.pack(fill="both", expand=True)
        
        self.file_kw_listbox = tk.Listbox(file_kw_frame, height=6)
        self.file_kw_listbox.pack(fill="both", expand=True, pady=(0, 5))
        
        file_kw_entry_frame = ttk.Frame(file_kw_frame)
        file_kw_entry_frame.pack(fill="x")
        
        self.file_kw_var = tk.StringVar()
        ttk.Entry(file_kw_entry_frame, textvariable=self.file_kw_var).pack(side="left", 
                                                                           fill="x", 
                                                                           expand=True, 
                                                                           padx=(0, 5))
        ttk.Button(file_kw_entry_frame, text="Thêm", 
                  command=self.add_file_keyword).pack(side="right")
    
    def browse_folder(self):
        """Mở dialog chọn thư mục"""
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path_var.set(folder)
    
    def add_excluded_folder(self):
        """Thêm folder vào danh sách không xóa"""
        folder = filedialog.askdirectory()
        if folder:
            self.config_manager.add_excluded_folder(folder)
            self.update_folder_listbox()
            self.log(f"Đã thêm folder ngoại lệ: {folder}", "info")
    
    def remove_excluded_folder(self):
        """Xóa folder khỏi danh sách không xóa"""
        selection = self.folder_listbox.curselection()
        if selection:
            folder = self.folder_listbox.get(selection[0])
            self.config_manager.remove_excluded_folder(folder)
            self.update_folder_listbox()
            self.log(f"Đã xóa folder ngoại lệ: {folder}", "info")
    
    def add_excluded_file(self):
        """Thêm file vào danh sách không xóa"""
        file_path = filedialog.askopenfilename()
        if file_path:
            self.config_manager.add_excluded_file(file_path)
            self.update_file_listbox()
            self.log(f"Đã thêm file ngoại lệ: {file_path}", "info")
    
    def remove_excluded_file(self):
        """Xóa file khỏi danh sách không xóa"""
        selection = self.file_listbox.curselection()
        if selection:
            file_path = self.file_listbox.get(selection[0])
            self.config_manager.remove_excluded_file(file_path)
            self.update_file_listbox()
            self.log(f"Đã xóa file ngoại lệ: {file_path}", "info")
    
    def add_folder_keyword(self):
        """Thêm keyword cho folder"""
        keyword = self.folder_kw_var.get().strip()
        if keyword:
            self.config_manager.add_folder_keyword(keyword)
            self.update_folder_keyword_listbox()
            self.folder_kw_var.set("")
            self.log(f"Đã thêm folder keyword: {keyword}", "info")
        else:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập từ khóa!")
    
    def add_file_keyword(self):
        """Thêm keyword cho file"""
        keyword = self.file_kw_var.get().strip()
        if keyword:
            self.config_manager.add_file_keyword(keyword)
            self.update_file_keyword_listbox()
            self.file_kw_var.set("")
            self.log(f"Đã thêm file keyword: {keyword}", "info")
        else:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập từ khóa!")
    
    def update_folder_listbox(self):
        """Cập nhật danh sách folder ngoại lệ"""
        self.folder_listbox.delete(0, tk.END)
        for folder in self.config_manager.get_excluded_folders():
            self.folder_listbox.insert(tk.END, folder)
    
    def update_file_listbox(self):
        """Cập nhật danh sách file ngoại lệ"""
        self.file_listbox.delete(0, tk.END)
        for file_path in self.config_manager.get_excluded_files():
            self.file_listbox.insert(tk.END, file_path)
    
    def update_folder_keyword_listbox(self):
        """Cập nhật danh sách folder keyword"""
        self.folder_kw_listbox.delete(0, tk.END)
        for keyword in self.config_manager.get_folder_keywords():
            self.folder_kw_listbox.insert(tk.END, keyword)
    
    def update_file_keyword_listbox(self):
        """Cập nhật danh sách file keyword"""
        self.file_kw_listbox.delete(0, tk.END)
        for keyword in self.config_manager.get_file_keywords():
            self.file_kw_listbox.insert(tk.END, keyword)
    
    def load_current_config(self):
        """Tải cấu hình hiện tại lên giao diện"""
        self.update_folder_listbox()
        self.update_file_listbox()
        self.update_folder_keyword_listbox()
        self.update_file_keyword_listbox()
    
    def log(self, message: str, log_type: str = "info"):
        """
        Ghi log vào text area
        
        Args:
            message: Nội dung log
            log_type: Loại log (info, delete, skip, error)
        """
        # Màu sắc cho các loại log
        tags = {
            "delete": ("delete", "red"),
            "skip": ("skip", "orange"),
            "error": ("error", "darkred"),
            "info": ("info", "black")
        }
        
        if log_type in tags:
            tag_name, color = tags[log_type]
            self.log_text.tag_config(tag_name, foreground=color)
            self.log_text.insert(tk.END, f"{message}\n", tag_name)
        else:
            self.log_text.insert(tk.END, f"{message}\n")
        
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def update_progress(self, current: int, total: int):
        """Cập nhật progress bar"""
        if total > 0:
            percent = (current / total) * 100
            self.progress_var.set(percent)
            self.progress_label.config(text=f"Đang xử lý: {current}/{total} files ({percent:.1f}%)")
            self.root.update_idletasks()
    
    def start_delete(self):
        """Bắt đầu quá trình xóa"""
        folder_path = self.folder_path_var.get()
        
        if not folder_path:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn thư mục cần xóa!")
            return
        
        if not os.path.exists(folder_path):
            messagebox.showerror("Lỗi", "Thư mục không tồn tại!")
            return
        
        # Xác nhận trước khi xóa
        confirm = messagebox.askyesno(
            "Xác nhận xóa",
            f"Bạn có chắc chắn muốn xóa TẤT CẢ các file trong thư mục:\n\n{folder_path}\n\n"
            f"(Sẽ giữ lại các folder/file theo cấu hình ngoại lệ)"
        )
        
        if not confirm:
            return
        
        # Chạy trong thread riêng để không block giao diện
        if not self.is_deleting:
            self.is_deleting = True
            self.delete_btn.config(state="disabled", text="ĐANG XÓA...")
            self.log_text.delete(1.0, tk.END)
            self.progress_var.set(0)
            self.progress_label.config(text="Đang khởi tạo...")
            
            self.current_delete_thread = threading.Thread(
                target=self.delete_worker,
                args=(folder_path,),
                daemon=True
            )
            self.current_delete_thread.start()
    
    def delete_worker(self, folder_path: str):
        """Worker thread cho việc xóa file"""
        try:
            # Thực hiện xóa
            stats = self.file_deleter.delete_files_in_folder(
                folder_path,
                progress_callback=self.update_progress,
                log_callback=self.log
            )
            
            # Hiển thị kết quả
            self.root.after(0, self.delete_complete, stats)
            
        except Exception as e:
            self.root.after(0, self.delete_error, str(e))
    
    def delete_complete(self, stats: dict):
        """Xử lý khi xóa hoàn tất"""
        self.is_deleting = False
        self.delete_btn.config(state="normal", text="BẮT ĐẦU XÓA")
        self.progress_label.config(text="Hoàn tất!")
        
        # Cập nhật thống kê
        self.stats_label.config(
            text=f"Đã xóa: {stats['deleted_files']} | "
                 f"Bỏ qua file: {stats['skipped_files']} | "
                 f"Bỏ qua folder: {stats['skipped_folders']} | "
                 f"Lỗi: {stats['errors']}"
        )
        
        messagebox.showinfo(
            "Hoàn tất",
            f"Đã xóa xong!\n\n"
            f"✓ Đã xóa: {stats['deleted_files']} file\n"
            f"○ Bỏ qua file: {stats['skipped_files']} file\n"
            f"○ Bỏ qua folder: {stats['skipped_folders']} folder\n"
            f"✗ Lỗi: {stats['errors']} file"
        )
    
    def delete_error(self, error_msg: str):
        """Xử lý khi có lỗi xảy ra"""
        self.is_deleting = False
        self.delete_btn.config(state="normal", text="BẮT ĐẦU XÓA")
        self.progress_label.config(text="Lỗi xảy ra!")
        messagebox.showerror("Lỗi", f"Có lỗi xảy ra:\n{error_msg}")