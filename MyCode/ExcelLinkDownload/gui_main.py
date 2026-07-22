# gui_main.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from datetime import datetime
from excel.factory import create_reader
from excel.formula_evaluator import get_link_from_cell
from download_manager import DownloadManager
from log_manager import save_log, load_log, merge_logs
from models import DownloadLog, FileInfo
from config import DEFAULT_SAVE_FOLDER
from utils import col_to_index, clean_link
from config_manager import load_config, save_config


class LogPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.log_count = 0
        self.max_log_lines = 500
        self.setup_ui()
        self.add_log("INFO", "Log panel đã sẵn sàng")
    
    def setup_ui(self):
        title_frame = ttk.Frame(self)
        title_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(title_frame, text="📋 LOG XỬ LÝ", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(frame, wrap=tk.WORD, height=20, width=50,
                                 font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4")
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text.tag_config("INFO", foreground="#4ec9b0")
        self.log_text.tag_config("WARNING", foreground="#dcdcaa")
        self.log_text.tag_config("ERROR", foreground="#f48771")
        self.log_text.tag_config("SUCCESS", foreground="#6a9955")
        self.log_text.tag_config("DEBUG", foreground="#9cdcfe")
        
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="🗑 Clear Log", command=self.clear_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="📋 Copy Log", command=self.copy_log).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="💾 Save Log", command=self.save_log_to_file).pack(side=tk.LEFT, padx=2)
    
    def add_log(self, level: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        icons = {"INFO": "ℹ️", "WARNING": "⚠️", "ERROR": "❌", "SUCCESS": "✅", "DEBUG": "🔍"}
        icon = icons.get(level, "•")
        log_line = f"[{timestamp}] {icon} [{level}] {message}\n"
        self.log_text.insert(tk.END, log_line, level)
        self.log_text.see(tk.END)
        self.log_count += 1
        if self.log_count > self.max_log_lines:
            self.log_text.delete(1.0, 101.0)
            self.log_count = self.max_log_lines
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        self.log_count = 0
        self.add_log("INFO", "Log đã được xóa")
    
    def copy_log(self):
        log_content = self.log_text.get(1.0, tk.END)
        self.clipboard_clear()
        self.clipboard_append(log_content)
        self.add_log("INFO", "Đã copy log vào clipboard")
    
    def save_log_to_file(self):
        filepath = filedialog.asksaveasfilename(
            title="Lưu log",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filepath:
            log_content = self.log_text.get(1.0, tk.END)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(log_content)
            self.add_log("SUCCESS", f"Đã lưu log vào {filepath}")


class MainTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.current_excel = None
        self.current_reader = None
        self.current_sheet = None
        self.current_page = 1
        self.rows_per_page = 20
        self.total_rows = 0
        
        self.config = load_config()
        self.setup_ui()
        self.restore_config()
    
    def restore_config(self):
        self.save_path.set(self.config.get("last_save_folder", DEFAULT_SAVE_FOLDER))
        self.base_path.set(self.config.get("base_path", ""))
        self.title_col.set(self.config.get("last_title_column", "A"))
        self.data_col.set(self.config.get("last_data_column", "C"))
        if self.config.get("last_excel_file") and os.path.exists(self.config.get("last_excel_file")):
            self.excel_path.set(self.config.get("last_excel_file"))
    
    def save_current_config(self):
        self.config["last_save_folder"] = self.save_path.get()
        self.config["base_path"] = self.base_path.get()
        self.config["last_title_column"] = self.title_col.get()
        self.config["last_data_column"] = self.data_col.get()
        if self.current_excel:
            self.config["last_excel_file"] = self.current_excel
        save_config(self.config)
    
    def setup_ui(self):
        file_frame = ttk.LabelFrame(self, text="File Excel", padding=5)
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.excel_path = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.excel_path, width=60).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="📂 OPEN", command=self.open_excel).pack(side=tk.LEFT, padx=5)
        
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(control_frame, text="Sheet:").pack(side=tk.LEFT, padx=5)
        self.sheet_combo = ttk.Combobox(control_frame, width=30)
        self.sheet_combo.pack(side=tk.LEFT, padx=5)
        self.sheet_combo.bind('<<ComboboxSelected>>', self.on_sheet_change)
        
        col_frame = ttk.Frame(control_frame)
        col_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Label(col_frame, text="Cột tiêu đề:").pack(side=tk.LEFT, padx=5)
        self.title_col = tk.StringVar(value="A")
        ttk.Entry(col_frame, textvariable=self.title_col, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(col_frame, text="Cột dữ liệu:").pack(side=tk.LEFT, padx=5)
        self.data_col = tk.StringVar(value="C")
        ttk.Entry(col_frame, textvariable=self.data_col, width=5).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="🔄 Refresh Preview", command=self.load_preview).pack(side=tk.LEFT, padx=10)
        
        base_frame = ttk.Frame(self)
        base_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(base_frame, text="🔗 Đường dẫn gốc (Base Path):").pack(side=tk.LEFT, padx=5)
        self.base_path = tk.StringVar(value="")
        ttk.Entry(base_frame, textvariable=self.base_path, width=60).pack(side=tk.LEFT, padx=5)
        ttk.Label(base_frame, text="(Để trống nếu link đã đầy đủ)", foreground="gray").pack(side=tk.LEFT, padx=5)
        
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=3)
        
        preview_frame = ttk.LabelFrame(left_frame, text="Preview dữ liệu", padding=5)
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("STT", "Cột tiêu đề", "Cột dữ liệu (gốc)", "Link đã parse", "Trạng thái")
        self.tree = ttk.Treeview(preview_frame, columns=columns, show="headings", height=18)
        
        self.tree.heading("STT", text="STT")
        self.tree.heading("Cột tiêu đề", text="Cột tiêu đề")
        self.tree.heading("Cột dữ liệu (gốc)", text="Cột dữ liệu (gốc)")
        self.tree.heading("Link đã parse", text="Link đã parse")
        self.tree.heading("Trạng thái", text="Trạng thái")
        
        self.tree.column("STT", width=50)
        self.tree.column("Cột tiêu đề", width=150)
        self.tree.column("Cột dữ liệu (gốc)", width=200)
        self.tree.column("Link đã parse", width=350)
        self.tree.column("Trạng thái", width=100)
        
        scrollbar_y = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        preview_frame.grid_rowconfigure(0, weight=1)
        preview_frame.grid_columnconfigure(0, weight=1)
        
        self.tree.tag_configure("empty_title", foreground="gray")
        
        page_frame = ttk.Frame(left_frame)
        page_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(page_frame, text="◀ Lùi", command=self.prev_page).pack(side=tk.LEFT, padx=5)
        self.page_label = ttk.Label(page_frame, text="Trang 1/?")
        self.page_label.pack(side=tk.LEFT, padx=5)
        ttk.Button(page_frame, text="Tới ▶", command=self.next_page).pack(side=tk.LEFT, padx=5)
        
        right_frame = ttk.Frame(main_paned)
        self.log_panel = LogPanel(right_frame)
        self.log_panel.pack(fill=tk.BOTH, expand=True)
        main_paned.add(right_frame, weight=1)
        
        option_frame = ttk.LabelFrame(self, text="Tùy chọn tải", padding=5)
        option_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.full_sheet_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(option_frame, text="✓ Lấy toàn bộ trang", 
                       variable=self.full_sheet_var).pack(side=tk.LEFT, padx=10)
        
        self.resume_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(option_frame, text="↻ Tải tiếp tục (resume)", 
                       variable=self.resume_var).pack(side=tk.LEFT, padx=10)
        
        save_frame = ttk.Frame(self)
        save_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(save_frame, text="📁 Địa chỉ lưu:").pack(side=tk.LEFT, padx=5)
        self.save_path = tk.StringVar(value=DEFAULT_SAVE_FOLDER)
        ttk.Entry(save_frame, textvariable=self.save_path, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(save_frame, text="Browse", command=self.browse_save_folder).pack(side=tk.LEFT, padx=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = ttk.Label(self, text="✅ Sẵn sàng")
        self.status_label.pack(pady=5)
        
        start_button = ttk.Button(self, text="🚀 START", command=self.start_download)
        start_button.pack(pady=10)
        
        self.log_panel.add_log("INFO", "Chương trình đã sẵn sàng")
    
    def apply_base_path(self, original_link: str) -> str:
        if not original_link:
            return original_link
        cleaned_link = clean_link(original_link)
        base_path = self.base_path.get().strip()
        if not base_path:
            return cleaned_link
        if cleaned_link.startswith('\\\\') or ':\\' in cleaned_link:
            return cleaned_link
        base = base_path.rstrip('\\') + '\\'
        link = cleaned_link.lstrip('\\')
        result = base + link
        result = clean_link(result)
        if base_path:
            self.log_panel.add_log("DEBUG", f"Ghép base path: {original_link[:50]} → {result[:50]}...")
        return result
    
    def open_excel(self):
        filepath = filedialog.askopenfilename(
            title="Chọn file Excel",
            filetypes=[("Excel files", "*.xlsx *.xlsm *.xls *.xlsb"), ("All files", "*.*")]
        )
        if filepath:
            try:
                if filepath.lower().endswith('.xls') and not filepath.lower().endswith('xlsx'):
                    self.log_panel.add_log("WARNING", "⚠️ File .xls (Excel 97-2003) được phát hiện!")
                self.log_panel.add_log("INFO", f"Đang mở file: {os.path.basename(filepath)}")
                self.current_reader = create_reader(filepath, parent_widget=self)
                self.current_excel = filepath
                self.excel_path.set(filepath)
                self.save_current_config()
                sheets = self.current_reader.get_sheet_names()
                self.sheet_combo['values'] = sheets
                if sheets:
                    self.sheet_combo.current(0)
                    self.current_sheet = sheets[0]
                    self.log_panel.add_log("SUCCESS", f"Đã mở file. Các sheet: {', '.join(sheets)}")
                    self.load_preview()
                else:
                    self.log_panel.add_log("ERROR", "File không có sheet nào")
            except ValueError as e:
                if "hủy" in str(e).lower():
                    self.log_panel.add_log("INFO", "Đã hủy mở file .xls")
                else:
                    self.log_panel.add_log("ERROR", str(e))
                    messagebox.showerror("Lỗi", str(e))
            except Exception as e:
                error_msg = f"Không thể đọc file Excel: {str(e)}"
                self.log_panel.add_log("ERROR", error_msg)
                messagebox.showerror("Lỗi", error_msg)
    
    def on_sheet_change(self, event):
        self.current_sheet = self.sheet_combo.get()
        self.current_page = 1
        self.log_panel.add_log("INFO", f"Chuyển sang sheet: {self.current_sheet}")
        self.load_preview()
    
    def load_preview(self):
        if not self.current_reader or not self.current_sheet:
            return
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        title_col_idx = col_to_index(self.title_col.get())
        data_col_idx = col_to_index(self.data_col.get())
        
        start_row = (self.current_page - 1) * self.rows_per_page + 2
        max_row = self.current_reader.get_max_row(self.current_sheet)
        end_row = min(start_row + self.rows_per_page - 1, max_row)
        self.total_rows = max_row
        
        loaded_rows = 0
        for row in range(start_row, end_row + 1):
            try:
                title_value = self.current_reader.get_cell_value(self.current_sheet, row, title_col_idx)
                if not title_value or str(title_value).strip() == "":
                    title = "(trống)"
                    status = "⏭ Bỏ qua (no title)"
                    tag = "empty_title"
                else:
                    title = str(title_value)
                    status = "⏳ Chờ tải"
                    tag = ""
                link = get_link_from_cell(self.current_reader, self.current_sheet, row, data_col_idx)
                if link:
                    link = self.apply_base_path(link)
                data_value = self.current_reader.get_cell_value(self.current_sheet, row, data_col_idx)
                if link:
                    status = "📥 Có link"
                self.tree.insert("", tk.END, values=(
                    row, title, str(data_value)[:100] if data_value else "", 
                    link[:200] if link else "", status
                ), tags=(tag,))
                loaded_rows += 1
            except:
                continue
        
        total_pages = (self.total_rows - 1 + self.rows_per_page) // self.rows_per_page
        self.page_label.config(text=f"Trang {self.current_page}/{max(1, total_pages)}")
        self.log_panel.add_log("INFO", f"Đã tải preview: {loaded_rows} dòng")
    
    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_preview()
    
    def next_page(self):
        total_pages = (self.total_rows - 1 + self.rows_per_page) // self.rows_per_page
        if self.current_page < total_pages:
            self.current_page += 1
            self.load_preview()
    
    def browse_save_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục lưu")
        if folder:
            self.save_path.set(folder)
            self.save_current_config()
            self.log_panel.add_log("INFO", f"Đã chọn thư mục lưu: {folder}")
    
    def update_progress(self, title, downloaded_mb, total_mb, percent):
        self.status_label.config(text=f"📥 Đang tải: {title} - {downloaded_mb:.1f}/{total_mb:.1f} MB ({percent:.1f}%)")
        self.progress_var.set(percent)
        self.update_idletasks()
    
    def start_download(self):
        self.save_current_config()
        
        if not self.current_reader or not self.current_sheet:
            self.log_panel.add_log("ERROR", "Chưa chọn file Excel hoặc sheet")
            messagebox.showerror("Lỗi", "Vui lòng chọn file Excel và sheet")
            return
        
        save_folder = self.save_path.get()
        if not save_folder:
            self.log_panel.add_log("ERROR", "Chưa chọn địa chỉ lưu")
            messagebox.showerror("Lỗi", "Vui lòng chọn địa chỉ lưu")
            return
        
        self.log_panel.add_log("INFO", "=" * 50)
        self.log_panel.add_log("INFO", "🚀 BẮT ĐẦU TẢI DỮ LIỆU")
        self.log_panel.add_log("INFO", f"📁 File: {os.path.basename(self.current_excel)}")
        self.log_panel.add_log("INFO", f"📄 Sheet: {self.current_sheet}")
        
        title_col_idx = col_to_index(self.title_col.get())
        data_col_idx = col_to_index(self.data_col.get())
        
        if self.full_sheet_var.get():
            start_row = 2
            end_row = self.current_reader.get_max_row(self.current_sheet)
        else:
            start_row = (self.current_page - 1) * self.rows_per_page + 2
            end_row = start_row
        
        files = []
        for row in range(start_row, end_row + 1):
            title_value = self.current_reader.get_cell_value(self.current_sheet, row, title_col_idx)
            if not title_value or str(title_value).strip() == "":
                continue
            title = str(title_value).strip()
            link = get_link_from_cell(self.current_reader, self.current_sheet, row, data_col_idx)
            if link:
                link = self.apply_base_path(link)
            if not link:
                continue
            files.append(FileInfo(sheet=self.current_sheet, row=row, title=title, old_link=link))
        
        self.log_panel.add_log("INFO", f"📊 Tìm thấy {len(files)} file cần tải")
        
        if not files:
            self.log_panel.add_log("ERROR", "❌ Không tìm thấy link nào")
            messagebox.showwarning("Cảnh báo", "Không tìm thấy link nào để tải")
            return
        
        old_log = None
        if self.resume_var.get():
            old_log = load_log(save_folder)
        
        files_to_download = merge_logs(old_log, files, save_folder)
        
        if not files_to_download:
            self.log_panel.add_log("SUCCESS", "✅ Tất cả file đã được tải")
            messagebox.showinfo("Thông báo", "Tất cả file đã được tải trước đó")
            return
        
        downloader = DownloadManager(save_folder, self.update_progress)
        downloaded, failed = downloader.download_batch(files_to_download, self.resume_var.get())
        
        for f in downloaded:
            self.log_panel.add_log("SUCCESS", f"✅ Đã tải: {f.title}")
        for f in failed:
            self.log_panel.add_log("ERROR", f"❌ Lỗi: {f.title}")
        
        new_log = DownloadLog(
            source_excel=self.current_excel,
            save_folder=save_folder,
            data_column=self.data_col.get(),
            title_column=self.title_col.get(),
            files=downloaded + failed
        )
        
        if old_log and self.resume_var.get():
            existing_dict = {(f.sheet, f.row): f for f in old_log.files}
            for f in new_log.files:
                existing_dict[(f.sheet, f.row)] = f
            new_log.files = list(existing_dict.values())
        
        save_log(save_folder, new_log)
        
        self.log_panel.add_log("SUCCESS", f"🎉 HOÀN THÀNH! Thành công: {len(downloaded)}, Thất bại: {len(failed)}")
        self.status_label.config(text=f"✅ Hoàn thành! Thành công: {len(downloaded)} | Thất bại: {len(failed)}")
        messagebox.showinfo("Kết quả", f"Đã tải xong!\n\n✅ Thành công: {len(downloaded)}\n❌ Thất bại: {len(failed)}")