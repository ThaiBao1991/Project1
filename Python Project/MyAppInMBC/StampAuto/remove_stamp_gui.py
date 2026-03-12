"""
GUI Test cho chức năng xóa dấu PDF
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import sys
from pathlib import Path
from remove_stamp import StampRemover, KTCKStampRemover, HieuChinhStampRemover

class RemoveStampApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Công cụ xóa dấu PDF")
        self.root.geometry("700x500")
        
        # Đường dẫn các thư mục
        self.base_dir = Path(__file__).parent
        self.setting_dir = self.base_dir / "setting"
        self.stamps_dir = self.setting_dir / "stamps"
        self.output_dir = self.base_dir / "processed_removed"
        
        # Tạo thư mục output nếu chưa tồn tại
        self.output_dir.mkdir(exist_ok=True)
        
        # Đường dẫn file settings
        self.settings_file = self.setting_dir / "settings.json"
        
        # Biến lưu trữ
        self.pdf_path = None
        self.stamp_types = []
        self.custom_stamp_image = None
        self.selected_stamp_image = None
        
        # Tạo giao diện
        self.setup_ui()
        
        # Tải settings
        self.load_settings()
    
    def setup_ui(self):
        # Frame chọn file PDF
        pdf_frame = ttk.LabelFrame(self.root, text="1. Chọn file PDF cần xóa dấu", padding=10)
        pdf_frame.pack(fill="x", padx=10, pady=5)
        
        self.pdf_path_var = tk.StringVar()
        ttk.Entry(pdf_frame, textvariable=self.pdf_path_var, width=60).pack(side="left", padx=5)
        ttk.Button(pdf_frame, text="Chọn file PDF", command=self.select_pdf).pack(side="left")
        
        # Frame chọn loại dấu cần xóa
        stamp_frame = ttk.LabelFrame(self.root, text="2. Chọn loại dấu cần xóa", padding=10)
        stamp_frame.pack(fill="x", padx=10, pady=5)
        
        self.stamp_type_var = tk.StringVar()
        self.stamp_combo = ttk.Combobox(stamp_frame, textvariable=self.stamp_type_var,
                                         state="readonly", width=40)
        self.stamp_combo.pack(side="left", padx=5)
        self.stamp_combo.bind('<<ComboboxSelected>>', self.on_stamp_selected)
        
        # Nút chọn ảnh thủ công
        ttk.Button(stamp_frame, text="Hoặc chọn ảnh mẫu...", 
                  command=self.select_stamp_image).pack(side="left", padx=5)
        
        # Frame tùy chọn xóa
        option_frame = ttk.LabelFrame(self.root, text="3. Tùy chọn xóa", padding=10)
        option_frame.pack(fill="x", padx=10, pady=5)
        
        # Phương pháp xóa
        ttk.Label(option_frame, text="Phương pháp:").grid(row=0, column=0, sticky="w", padx=5)
        self.method_var = tk.StringVar(value="image")
        ttk.Radiobutton(option_frame, text="So sánh ảnh (chính xác cao)", 
                       variable=self.method_var, value="image").grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(option_frame, text="So sánh hash (nhanh hơn)", 
                       variable=self.method_var, value="hash").grid(row=0, column=2, sticky="w", padx=10)
        
        # Ngưỡng tương đồng (cho phương pháp image)
        ttk.Label(option_frame, text="Ngưỡng tương đồng:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.threshold_var = tk.DoubleVar(value=0.85)
        threshold_scale = ttk.Scale(option_frame, from_=0.5, to=1.0, 
                                    variable=self.threshold_var, orient="horizontal", length=200)
        threshold_scale.grid(row=1, column=1, sticky="w", pady=5)
        self.threshold_label = ttk.Label(option_frame, text="0.85")
        self.threshold_label.grid(row=1, column=2, sticky="w", padx=5)
        
        def update_threshold_label(*args):
            self.threshold_label.config(text=f"{self.threshold_var.get():.2f}")
        
        self.threshold_var.trace('w', update_threshold_label)
        
        # Frame tùy chọn lưu file
        save_frame = ttk.LabelFrame(self.root, text="4. Tùy chọn lưu file", padding=10)
        save_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_mode = tk.StringVar(value="new")
        ttk.Radiobutton(save_frame, text="Lưu thành file mới (khuyên dùng)", 
                       variable=self.save_mode, value="new").pack(anchor="w")
        ttk.Radiobutton(save_frame, text="Lưu đè lên file gốc (nguy hiểm)", 
                       variable=self.save_mode, value="overwrite").pack(anchor="w")
        
        # Frame thông tin
        info_frame = ttk.LabelFrame(self.root, text="Thông tin chi tiết", padding=10)
        info_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.info_text = tk.Text(info_frame, height=10, wrap="word")
        self.info_text.pack(fill="both", expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.info_text)
        scrollbar.pack(side="right", fill="y")
        self.info_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.info_text.yview)
        
        # Frame nút điều khiển
        button_frame = ttk.Frame(self.root)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(button_frame, text="Mở thư mục stamps", 
                  command=self.open_stamps_folder).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Mở thư mục output", 
                  command=self.open_output_folder).pack(side="left", padx=5)
        ttk.Button(button_frame, text="XÓA DẤU", 
                  command=self.remove_stamps, style="Remove.TButton").pack(side="right", padx=5)
        
        # Style cho nút xóa
        style = ttk.Style()
        style.configure("Remove.TButton", font=('Arial', 10, 'bold'), foreground='red')
        
        # Hiển thị thông tin khởi tạo
        self.info_text.insert(tk.END, "=== CÔNG CỤ XÓA DẤU PDF ===\n")
        self.info_text.insert(tk.END, "Chọn file PDF và loại dấu cần xóa\n\n")
    
    def load_settings(self):
        """Tải cấu hình từ file settings.json"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.stamp_types = settings.get('stamp_types', [])
                
                # Cập nhật combobox
                self.stamp_combo['values'] = [f"{s['name']} ({s['image']})" for s in self.stamp_types]
                if self.stamp_types:
                    self.stamp_combo.current(0)
                    self.on_stamp_selected()
                
                self.info_text.insert(tk.END, f"✓ Đã tải {len(self.stamp_types)} loại dấu\n")
                
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể đọc settings: {str(e)}")
    
    def select_pdf(self):
        """Chọn file PDF"""
        filename = filedialog.askopenfilename(
            title="Chọn file PDF cần xóa dấu",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            self.pdf_path = filename
            self.pdf_path_var.set(filename)
            self.info_text.insert(tk.END, f"✓ Đã chọn file PDF: {filename}\n")
            self.info_text.see(tk.END)
    
    def select_stamp_image(self):
        """Chọn ảnh mẫu thủ công"""
        filename = filedialog.askopenfilename(
            title="Chọn ảnh mẫu của dấu cần xóa",
            initialdir=self.stamps_dir,
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if filename:
            self.custom_stamp_image = filename
            self.stamp_type_var.set(f"TỰ CHỌN: {os.path.basename(filename)}")
            self.info_text.insert(tk.END, f"✓ Đã chọn ảnh mẫu: {filename}\n")
    
    def on_stamp_selected(self, event=None):
        """Xử lý khi chọn loại dấu từ danh sách"""
        selected = self.stamp_combo.get()
        if selected and not selected.startswith("TỰ CHỌN"):
            # Trích xuất tên file ảnh
            import re
            match = re.search(r'\((.*?)\)', selected)
            if match:
                self.selected_stamp_image = self.stamps_dir / match.group(1)
                self.custom_stamp_image = None  # Clear custom selection
                self.info_text.insert(tk.END, f"✓ Đã chọn dấu: {selected}\n")
                self.info_text.insert(tk.END, f"  Ảnh mẫu: {self.selected_stamp_image}\n")
    
    def open_stamps_folder(self):
        """Mở thư mục chứa ảnh đóng dấu"""
        os.startfile(self.stamps_dir)
    
    def open_output_folder(self):
        """Mở thư mục chứa file đã xóa dấu"""
        os.startfile(self.output_dir)
    
    def remove_stamps(self):
        """Thực hiện xóa dấu"""
        # Kiểm tra file PDF
        if not self.pdf_path:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn file PDF!")
            return
        
        # Xác định ảnh mẫu
        stamp_image = None
        if self.custom_stamp_image:
            stamp_image = self.custom_stamp_image
        elif self.selected_stamp_image:
            stamp_image = self.selected_stamp_image
        else:
            # Thử lấy từ combobox
            selected = self.stamp_combo.get()
            if selected and not selected.startswith("TỰ CHỌN"):
                import re
                match = re.search(r'\((.*?)\)', selected)
                if match:
                    stamp_image = self.stamps_dir / match.group(1)
        
        if not stamp_image or not os.path.exists(str(stamp_image)):
            messagebox.showerror("Lỗi", "Vui lòng chọn ảnh mẫu của dấu cần xóa!")
            return
        
        # Xác định output path
        output_path = None
        if self.save_mode.get() == "new":
            base_name = os.path.basename(self.pdf_path)
            name, ext = os.path.splitext(base_name)
            output_path = self.output_dir / f"{name}_removed{ext}"
        
        # Tạo remover với ngưỡng tương đồng tùy chỉnh
        config = {
            'similarity_threshold': self.threshold_var.get()
        }
        
        # Xác định loại remover dựa trên tên file ảnh
        stamp_image_str = str(stamp_image)
        if 'KTCK' in stamp_image_str or 'ktck' in stamp_image_str:
            remover = KTCKStampRemover(stamp_image_str, config)
            self.info_text.insert(tk.END, "✓ Sử dụng bộ xóa dấu KTCK\n")
        elif 'HieuChinh' in stamp_image_str or 'hieuchinh' in stamp_image_str:
            remover = HieuChinhStampRemover(stamp_image_str, config)
            self.info_text.insert(tk.END, "✓ Sử dụng bộ xóa dấu Hiệu chỉnh\n")
        else:
            remover = StampRemover(stamp_image_str, config)
            self.info_text.insert(tk.END, "✓ Sử dụng bộ xóa dấu mặc định\n")
        
        # Xác nhận trước khi xóa
        if self.save_mode.get() == "overwrite":
            confirm = messagebox.askyesno(
                "Xác nhận",
                "Bạn có chắc muốn xóa dấu và lưu đè lên file gốc?\n"
                "Hành động này không thể hoàn tác!"
            )
            if not confirm:
                return
        
        # Thực hiện xóa
        try:
            self.info_text.insert(tk.END, f"\nĐang xóa dấu...\n")
            self.info_text.insert(tk.END, f"Phương pháp: {self.method_var.get()}\n")
            self.info_text.insert(tk.END, f"Ngưỡng tương đồng: {self.threshold_var.get():.2f}\n")
            self.root.update()
            
            success, message, count = remover.remove_stamps(
                self.pdf_path, 
                str(output_path) if output_path else None,
                method=self.method_var.get()
            )
            
            if success:
                result_msg = f"✓ {message}\n"
                result_msg += f"Số dấu đã xóa: {count}\n"
                
                if output_path:
                    result_msg += f"File kết quả: {output_path}"
                else:
                    result_msg += f"Đã cập nhật file gốc: {self.pdf_path}"
                
                self.info_text.insert(tk.END, result_msg + "\n")
                messagebox.showinfo("Thành công", result_msg)
                
                # Mở thư mục output nếu lưu file mới
                if output_path and self.save_mode.get() == "new":
                    self.open_output_folder()
            else:
                error_msg = f"✗ {message}"
                self.info_text.insert(tk.END, error_msg + "\n")
                messagebox.showerror("Lỗi", error_msg)
            
            self.info_text.see(tk.END)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.info_text.insert(tk.END, f"✗ LỖI: {str(e)}\n")
            self.info_text.insert(tk.END, f"Chi tiết: {error_details}\n")
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra:\n{str(e)}")


def main():
    root = tk.Tk()
    app = RemoveStampApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()