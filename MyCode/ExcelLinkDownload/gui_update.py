# gui_update.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
from datetime import datetime
from excel.factory import create_reader
from log_manager import load_log
from utils import col_to_index


class UpdateTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        frame1 = ttk.LabelFrame(self, text="File Excel cần cập nhật", padding=5)
        frame1.pack(fill=tk.X, padx=10, pady=10)
        
        self.excel_path = tk.StringVar()
        ttk.Entry(frame1, textvariable=self.excel_path, width=70).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame1, text="Browse", command=self.browse_excel).pack(side=tk.LEFT, padx=5)
        
        frame2 = ttk.LabelFrame(self, text="File data (JSON)", padding=5)
        frame2.pack(fill=tk.X, padx=10, pady=10)
        
        self.json_path = tk.StringVar()
        ttk.Entry(frame2, textvariable=self.json_path, width=70).pack(side=tk.LEFT, padx=5)
        ttk.Button(frame2, text="Browse", command=self.browse_json).pack(side=tk.LEFT, padx=5)
        
        info_frame = ttk.LabelFrame(self, text="Thông tin", padding=5)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.info_text = tk.Text(info_frame, height=10, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=scrollbar.set)
        
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Log panel nhỏ trong tab Update
        log_frame = ttk.LabelFrame(self, text="Log cập nhật", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD, font=("Consolas", 9))
        scrollbar_log = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar_log.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_log.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text.tag_config("INFO", foreground="blue")
        self.log_text.tag_config("SUCCESS", foreground="green")
        self.log_text.tag_config("ERROR", foreground="red")
        self.log_text.tag_config("WARNING", foreground="orange")
        
        ttk.Button(self, text="🔄 CẬP NHẬT EXCEL", command=self.update_excel,
                  style="Accent.TButton").pack(pady=20)
        
        self.status_label = ttk.Label(self, text="Sẵn sàng")
        self.status_label.pack(pady=5)
    
    def add_log(self, level: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}\n"
        self.log_text.insert(tk.END, log_line, level)
        self.log_text.see(tk.END)
        self.update_idletasks()
    
    def browse_excel(self):
        filepath = filedialog.askopenfilename(
            title="Chọn file Excel cần cập nhật",
            filetypes=[("Excel files", "*.xlsx *.xlsm *.xls *.xlsb"), ("All files", "*.*")]
        )
        if filepath:
            self.excel_path.set(filepath)
            self.load_info()
    
    def browse_json(self):
        filepath = filedialog.askopenfilename(
            title="Chọn file JSON log",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filepath:
            self.json_path.set(filepath)
            self.load_info()
    
    def load_info(self):
        if not self.json_path.get():
            return
        
        log = load_log(os.path.dirname(self.json_path.get()))
        if not log:
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, "Không thể đọc file JSON hoặc file không hợp lệ")
            return
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, f"File Excel nguồn: {log.source_excel}\n")
        self.info_text.insert(tk.END, f"Cột dữ liệu: {log.data_column}\n")
        self.info_text.insert(tk.END, f"Cột tiêu đề: {log.title_column}\n")
        self.info_text.insert(tk.END, f"Tổng số file đã tải: {len(log.files)}\n\n")
        
        # Đếm số file có new_link hợp lệ
        valid_files = [f for f in log.files if f.new_link and os.path.exists(f.new_link)]
        self.info_text.insert(tk.END, f"Số file có thể cập nhật: {len(valid_files)}/{len(log.files)}\n\n")
        
        self.info_text.insert(tk.END, "Danh sách file (10 đầu):\n")
        for i, f in enumerate(log.files[:10]):
            status = "✅" if (f.new_link and os.path.exists(f.new_link)) else "❌"
            self.info_text.insert(tk.END, f"  {status} {i+1}. {f.title} → {f.new_link}\n")
    
    def update_excel(self):
        excel_file = self.excel_path.get()
        json_file = self.json_path.get()
        
        if not excel_file or not json_file:
            messagebox.showerror("Lỗi", "Vui lòng chọn đầy đủ file Excel và file JSON")
            return
        
        if not os.path.exists(excel_file):
            messagebox.showerror("Lỗi", "File Excel không tồn tại")
            return
        
        self.add_log("INFO", "=" * 50)
        self.add_log("INFO", "BẮT ĐẦU CẬP NHẬT EXCEL")
        self.add_log("INFO", f"File Excel: {os.path.basename(excel_file)}")
        self.add_log("INFO", f"File JSON: {os.path.basename(json_file)}")
        
        # Đọc log
        log = load_log(os.path.dirname(json_file))
        if not log:
            self.add_log("ERROR", "Không thể đọc file JSON")
            messagebox.showerror("Lỗi", "Không thể đọc file JSON")
            return
        
        # Tạo backup
        backup_file = excel_file + ".backup"
        try:
            shutil.copy2(excel_file, backup_file)
            self.add_log("SUCCESS", f"Đã tạo backup: {backup_file}")
        except Exception as e:
            self.add_log("ERROR", f"Không thể tạo backup: {e}")
            messagebox.showerror("Lỗi", f"Không thể tạo backup: {e}")
            return
        
        # Mở file Excel
        try:
            reader = create_reader(excel_file)
            self.add_log("SUCCESS", f"Đã mở file Excel")
        except Exception as e:
            self.add_log("ERROR", f"Không thể mở file Excel: {e}")
            messagebox.showerror("Lỗi", f"Không thể mở file Excel: {e}")
            return
        
        data_col_idx = col_to_index(log.data_column)
        
        updated = 0
        skipped = 0
        failed = 0
        
        self.add_log("INFO", "-" * 40)
        self.add_log("INFO", "ĐANG CẬP NHẬT TỪNG DÒNG...")
        
        for file_info in log.files:
            if not file_info.new_link or not os.path.exists(file_info.new_link):
                self.add_log("WARNING", f"⏭ Bỏ qua dòng {file_info.row}: file không tồn tại")
                skipped += 1
                continue
            
            try:
                reader.update_cell(file_info.sheet, file_info.row, data_col_idx, file_info.new_link)
                updated += 1
                self.add_log("SUCCESS", f"✅ Dòng {file_info.row}: {file_info.title}")
                self.status_label.config(text=f"Đã cập nhật: {updated} file")
                self.update_idletasks()
            except Exception as e:
                failed += 1
                self.add_log("ERROR", f"❌ Lỗi dòng {file_info.row} ({file_info.title}): {e}")
        
        # Lưu file mới (không ghi đè gốc)
        if updated > 0:
            base_name = os.path.splitext(excel_file)[0]
            ext = os.path.splitext(excel_file)[1]
            new_excel_file = f"{base_name}_updated{ext}"
            
            try:
                reader.save(new_excel_file)
                self.add_log("SUCCESS", f"Đã lưu file mới: {new_excel_file}")
                
                result_msg = f"CẬP NHẬT XONG!\n\n"
                result_msg += f"✅ Thành công: {updated}\n"
                result_msg += f"⏭ Bỏ qua: {skipped}\n"
                result_msg += f"❌ Thất bại: {failed}\n\n"
                result_msg += f"📁 Backup: {backup_file}\n"
                result_msg += f"📁 File mới: {new_excel_file}"
                
                messagebox.showinfo("Kết quả", result_msg)
                
            except Exception as e:
                self.add_log("ERROR", f"Không thể lưu file: {e}")
                messagebox.showerror("Lỗi", f"Không thể lưu file: {e}")
        else:
            self.add_log("WARNING", "Không có file nào được cập nhật")
            messagebox.showinfo("Thông báo", "Không có file nào được cập nhật")
        
        reader.close()
        self.status_label.config(text=f"Hoàn thành! Thành công: {updated} | Thất bại: {failed}")
        self.add_log("INFO", "=" * 50)
        self.add_log("SUCCESS", f"HOÀN THÀNH! Thành công: {updated} | Thất bại: {failed}")