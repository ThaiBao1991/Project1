import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import sys
from pathlib import Path

# Import modules
try:
    from stamp_modules import KTCKStamp, HieuChinhStamp
    print("✓ Import thành công từ stamp_modules")
except Exception as e:
    print(f"✗ Lỗi import: {e}")
    messagebox.showerror("Lỗi", f"Không thể import modules: {e}")
    sys.exit(1)

class StampPDFApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Công cụ đóng dấu PDF")
        self.root.geometry("750x550")
        
        # Đường dẫn các thư mục
        self.base_dir = Path(__file__).parent
        self.setting_dir = self.base_dir / "setting"
        self.stamps_dir = self.setting_dir / "stamps"
        self.output_dir = self.base_dir / "processed"
        
        # Tạo các thư mục nếu chưa tồn tại
        self.setting_dir.mkdir(exist_ok=True)
        self.stamps_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        # Đường dẫn file settings
        self.settings_file = self.setting_dir / "settings.json"
        
        # Biến lưu trữ
        self.pdf_path = None
        self.stamp_types = []
        self.current_settings = None
        self.stamp_modules = {
            'ktck': KTCKStamp,
            'hieuchinh': HieuChinhStamp
        }
        
        # Tạo giao diện TRƯỚC khi tải settings
        self.setup_ui()
        
        # Sau đó mới tải settings (vì đã có info_text)
        self.load_settings()
        
    def setup_ui(self):
        # Frame chọn file
        file_frame = ttk.LabelFrame(self.root, text="Chọn file PDF", padding=10)
        file_frame.pack(fill="x", padx=10, pady=5)
        
        self.file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path_var, width=60).pack(side="left", padx=5)
        ttk.Button(file_frame, text="Chọn file", command=self.select_pdf).pack(side="left")
        
        # Frame chọn loại đóng dấu
        stamp_frame = ttk.LabelFrame(self.root, text="Chọn loại đóng dấu", padding=10)
        stamp_frame.pack(fill="x", padx=10, pady=5)
        
        self.stamp_type_var = tk.StringVar()
        self.stamp_combo = ttk.Combobox(stamp_frame, textvariable=self.stamp_type_var, 
                                         values=[],  # Sẽ cập nhật sau khi load settings
                                         state="readonly", width=40)
        self.stamp_combo.pack(side="left", padx=5)
        self.stamp_combo.bind('<<ComboboxSelected>>', self.on_stamp_selected)
        
        # Frame tùy chọn lưu file
        save_frame = ttk.LabelFrame(self.root, text="Tùy chọn lưu file", padding=10)
        save_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_mode = tk.StringVar(value="overwrite")
        ttk.Radiobutton(save_frame, text="Lưu đè lên file gốc (giống code Access)", 
                       variable=self.save_mode, value="overwrite").pack(anchor="w")
        ttk.Radiobutton(save_frame, text="Lưu thành file mới trong thư mục processed", 
                       variable=self.save_mode, value="new").pack(anchor="w")
        
        # Frame thông tin chi tiết
        info_frame = ttk.LabelFrame(self.root, text="Thông tin chi tiết & Đặc thù đóng dấu", padding=10)
        info_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Text widget để hiển thị thông tin
        self.info_text = tk.Text(info_frame, height=12, wrap="word")
        self.info_text.pack(fill="both", expand=True)
        
        # Scrollbar cho text widget
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
        ttk.Button(button_frame, text="Đóng dấu", 
                  command=self.stamp_pdf, style="Accent.TButton").pack(side="right", padx=5)
        
        # Style cho nút đóng dấu
        style = ttk.Style()
        style.configure("Accent.TButton", font=('Arial', 10, 'bold'))
        
        # Hiển thị thông tin khởi tạo
        self.info_text.insert(tk.END, "=== HỆ THỐNG ĐÓNG DẤU PDF ===\n")
        self.info_text.insert(tk.END, f"Thư mục stamps: {self.stamps_dir}\n")
        self.info_text.insert(tk.END, f"File settings: {self.settings_file}\n")
        self.info_text.insert(tk.END, "Đang tải cấu hình...\n\n")
        self.root.update()
        
    def load_settings(self):
        """Tải cấu hình từ file settings.json"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.current_settings = json.load(f)
                    self.stamp_types = self.current_settings.get('stamp_types', [])
                
                # Cập nhật combobox
                self.stamp_combo['values'] = [s["name"] for s in self.stamp_types]
                if self.stamp_types:
                    self.stamp_combo.current(0)
                    self.on_stamp_selected()  # Hiển thị thông tin của loại đầu tiên
                
                self.info_text.insert(tk.END, "✓ Đã tải settings thành công\n")
                self.info_text.insert(tk.END, f"✓ Tìm thấy {len(self.stamp_types)} loại đóng dấu\n")
                
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể đọc file settings: {str(e)}")
                self.stamp_types = []
                self.info_text.insert(tk.END, f"✗ Lỗi đọc settings: {str(e)}\n")
        else:
            # Tạo file settings mặc định
            self.create_default_settings()
    
    def create_default_settings(self):
        """Tạo file settings mặc định"""
        default_settings = {
            "stamp_types": [
                {
                    "id": "ktck",
                    "name": "Kiểm tra cơ khí",
                    "image": "condauKTCK.png",
                    "search_text": "Xác nhận",
                    "scale": 0.12,
                    "description": "Đóng dấu kiểm tra cơ khí - Đặt sát bên dưới text",
                    "position_offset": {
                        "y_bottom_offset": 2,
                        "height_offset": 6,
                        "x_offset": 0
                    }
                },
                {
                    "id": "hieuchinh",
                    "name": "Hiệu chỉnh",
                    "image": "condauHieuChinh.png",
                    "search_text": "Xác nhận",
                    "scale": 0.2,
                    "description": "Đóng dấu hiệu chỉnh - Dịch phải 50 đơn vị",
                    "position_offset": {
                        "y_bottom_offset": 1,
                        "height_offset": 5,
                        "x_offset": 20
                    }
                }
            ],
            "output_folder": "processed",
            "default_settings": {
                "auto_open_folder": True
            }
        }
        
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(default_settings, f, ensure_ascii=False, indent=4)
            
            self.stamp_types = default_settings['stamp_types']
            self.current_settings = default_settings
            
            # Cập nhật combobox
            self.stamp_combo['values'] = [s["name"] for s in self.stamp_types]
            if self.stamp_types:
                self.stamp_combo.current(0)
                self.on_stamp_selected()
            
            self.info_text.insert(tk.END, "✓ Đã tạo file settings mặc định\n")
            self.info_text.insert(tk.END, f"✓ Đã tạo {len(self.stamp_types)} loại đóng dấu\n")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tạo file settings: {str(e)}")
            self.info_text.insert(tk.END, f"✗ Lỗi tạo settings: {str(e)}\n")
    
    def select_pdf(self):
        """Chọn file PDF"""
        filename = filedialog.askopenfilename(
            title="Chọn file PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filename:
            self.pdf_path = filename
            self.file_path_var.set(filename)
            self.info_text.insert(tk.END, f"✓ Đã chọn file: {filename}\n")
            # Cuộn xuống cuối
            self.info_text.see(tk.END)
    
    def on_stamp_selected(self, event=None):
        """Xử lý khi chọn loại đóng dấu"""
        if not self.stamp_types:
            return
            
        selected_name = self.stamp_type_var.get()
        if not selected_name and self.stamp_types:
            selected_name = self.stamp_types[0]["name"]
            self.stamp_type_var.set(selected_name)
            
        selected_stamp = next((s for s in self.stamp_types if s["name"] == selected_name), None)
        
        if selected_stamp:
            # Xóa nội dung cũ
            self.info_text.delete(1.0, tk.END)
            
            info = f"=== THÔNG TIN ĐÓNG DẤU ===\n"
            info += f"Loại: {selected_stamp['name']}\n"
            info += f"Mô tả: {selected_stamp.get('description', 'N/A')}\n"
            info += f"Đặc thù: {selected_stamp.get('description', 'N/A')}\n"
            info += f"Ảnh: {selected_stamp.get('image', 'N/A')}\n"
            info += f"Tìm text: '{selected_stamp.get('search_text', 'Xác nhận')}'\n"
            info += f"Scale: {selected_stamp.get('scale', 0.1)}\n"
            
            # Hiển thị offset đặc thù
            pos_offset = selected_stamp.get('position_offset', {})
            info += f"Dịch ngang (x_offset): {pos_offset.get('x_offset', 0)}\n"
            info += f"Dịch dọc dưới: {pos_offset.get('y_bottom_offset', 1)}\n"
            info += f"Chiều cao thêm: {pos_offset.get('height_offset', 5)}\n\n"
            
            # Kiểm tra file ảnh
            stamp_path = self.stamps_dir / selected_stamp['image']
            if stamp_path.exists():
                info += f"✓ File ảnh tồn tại: {stamp_path}\n"
            else:
                info += f"✗ File ảnh KHÔNG tồn tại: {stamp_path}\n"
                info += f"Vui lòng đặt file ảnh vào thư mục: {self.stamps_dir}\n"
            
            self.info_text.insert(1.0, info)
    
    def open_stamps_folder(self):
        """Mở thư mục chứa ảnh đóng dấu"""
        os.startfile(self.stamps_dir)
    
    def open_output_folder(self):
        """Mở thư mục chứa file đã xử lý"""
        os.startfile(self.output_dir)
    
    def stamp_pdf(self):
        """Thực hiện đóng dấu"""
        if not self.pdf_path:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn file PDF!")
            return
        
        if not self.stamp_type_var.get():
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn loại đóng dấu!")
            return
        
        selected_name = self.stamp_type_var.get()
        selected_stamp = next((s for s in self.stamp_types if s["name"] == selected_name), None)
        
        if not selected_stamp:
            messagebox.showerror("Lỗi", "Không tìm thấy loại đóng dấu đã chọn!")
            return
        
        # Kiểm tra file ảnh đóng dấu
        stamp_image_path = self.stamps_dir / selected_stamp['image']
        if not stamp_image_path.exists():
            messagebox.showerror("Lỗi", f"Không tìm thấy file ảnh đóng dấu:\n{stamp_image_path}")
            return
        
        try:
            # Lấy module tương ứng với đặc thù riêng
            stamp_id = selected_stamp['id']
            if stamp_id in self.stamp_modules:
                stamp_class = self.stamp_modules[stamp_id]
                stamp_module = stamp_class(str(stamp_image_path), selected_stamp)
                self.info_text.insert(tk.END, f"✓ Đã khởi tạo module: {stamp_id} (với đặc thù riêng)\n")
            else:
                messagebox.showerror("Lỗi", f"Không tìm thấy module cho loại đóng dấu: {selected_name}")
                return
            
            # Xác định đường dẫn output
            output_path = None
            if self.save_mode.get() == "new":
                base_name = os.path.basename(self.pdf_path)
                name, ext = os.path.splitext(base_name)
                output_path = self.output_dir / f"{name}_{stamp_id}{ext}"
                self.info_text.insert(tk.END, f"Sẽ lưu file mới: {output_path}\n")
            else:
                self.info_text.insert(tk.END, "Sẽ lưu đè lên file gốc\n")
            
            # Thực hiện đóng dấu
            self.info_text.insert(tk.END, f"\nĐang đóng dấu với đặc thù riêng...\n")
            self.root.update()
            
            success, result, stamp_count = stamp_module.stamp_pdf(
                self.pdf_path, 
                str(output_path) if output_path else None
            )
            
            if success:
                message = f"ĐÃ ĐÓNG DẤU THÀNH CÔNG!\n"
                message += f"Số dấu đã đóng: {stamp_count}\n"
                message += f"Loại đóng dấu: {selected_stamp['name']}\n"
                message += f"Đặc thù: {selected_stamp.get('description', 'N/A')}\n\n"
                
                if output_path:
                    message += f"File đã lưu tại: {result}"
                else:
                    message += f"Đã lưu đè lên file gốc:\n{result}"
                
                self.info_text.insert(tk.END, f"✓ {message}\n")
                messagebox.showinfo("Thành công", message)
                
                # Tự động mở thư mục chứa file đã xử lý
                if self.save_mode.get() == "new" and self.current_settings.get('default_settings', {}).get('auto_open_folder', True):
                    self.open_output_folder()
            else:
                error_msg = f"ĐÓNG DẤU THẤT BẠI: {result}"
                self.info_text.insert(tk.END, f"✗ {error_msg}\n")
                messagebox.showerror("Lỗi", error_msg)
            
            # Cuộn xuống cuối
            self.info_text.see(tk.END)
                
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.info_text.insert(tk.END, f"✗ LỖI: {str(e)}\n")
            self.info_text.insert(tk.END, f"Chi tiết: {error_details}\n")
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra:\n{str(e)}")
            self.info_text.see(tk.END)

def main():
    root = tk.Tk()
    app = StampPDFApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()