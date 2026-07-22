import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from openpyxl import Workbook

class SimpleExcelCreator:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel File Creator")
        self.root.geometry("500x250")
        
        # Biến lưu đường dẫn và tên file
        self.folder_path = tk.StringVar()
        self.file_name = tk.StringVar(value="NewExcelFile.xlsx")
        
        self.setup_ui()
    
    def setup_ui(self):
        # Tiêu đề
        title_label = ttk.Label(self.root, text="Create Excel File", font=("Arial", 16, "bold"))
        title_label.pack(pady=20)
        
        # Frame chọn folder
        folder_frame = ttk.Frame(self.root)
        folder_frame.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(folder_frame, text="Folder:").pack(side=tk.LEFT)
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path, width=40)
        folder_entry.pack(side=tk.LEFT, padx=(10, 5))
        
        ttk.Button(folder_frame, text="Browse...", command=self.browse_folder).pack(side=tk.LEFT)
        
        # Frame nhập tên file
        file_frame = ttk.Frame(self.root)
        file_frame.pack(fill="x", padx=20, pady=5)
        
        ttk.Label(file_frame, text="File Name:").pack(side=tk.LEFT)
        file_entry = ttk.Entry(file_frame, textvariable=self.file_name, width=30)
        file_entry.pack(side=tk.LEFT, padx=(10, 0))
        ttk.Label(file_frame, text=".xlsx").pack(side=tk.LEFT, padx=(5, 0))
        
        # Nút tạo file
        ttk.Button(self.root, text="Create Excel File", command=self.create_excel, 
                  style="Accent.TButton").pack(pady=30)
        
        # Trạng thái
        self.status_label = ttk.Label(self.root, text="Ready to create Excel file", foreground="blue")
        self.status_label.pack()
        
        # Cấu hình style
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 10, "bold"))
    
    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)
    
    def create_excel(self):
        # Kiểm tra đầu vào
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a folder first!")
            return
        
        if not self.file_name.get():
            messagebox.showerror("Error", "Please enter a file name!")
            return
        
        try:
            # Lấy thông tin
            folder = self.folder_path.get()
            filename = self.file_name.get()
            if not filename.endswith('.xlsx'):
                filename += '.xlsx'
            
            full_path = os.path.join(folder, filename)
            
            # Kiểm tra nếu file đã tồn tại
            if os.path.exists(full_path):
                if not messagebox.askyesno("Confirm", f"File '{filename}' already exists. Overwrite?"):
                    self.status_label.config(text="Cancelled", foreground="orange")
                    return
            
            # Cập nhật trạng thái
            self.status_label.config(text="Creating Excel file...", foreground="orange")
            self.root.update()
            
            # Tạo workbook mới
            wb = Workbook()
            
            # Lấy sheet active và đổi tên
            ws = wb.active
            ws.title = "Data"
            
            # Thêm giá trị vào ô A2
            ws['A2'] = "Giá trị của A2"
            
            # Lưu file
            wb.save(full_path)
            
            # Thông báo thành công
            self.status_label.config(text="Excel file created successfully!", foreground="green")
            messagebox.showinfo("Success", 
                f"Excel file created successfully!\n\n"
                f"File: {filename}\n"
                f"Location: {folder}\n"
                f"Sheet: Data\n"
                f"Cell A2: 'Giá trị của A2'")
            
            # Hỏi có muốn mở file không
            if messagebox.askyesno("Open File", "Do you want to open the Excel file?"):
                os.startfile(full_path)
                
        except Exception as e:
            self.status_label.config(text="Error occurred!", foreground="red")
            messagebox.showerror("Error", f"Failed to create Excel file:\n\n{str(e)}")

if __name__ == "__main__":
    # Kiểm tra và cài đặt openpyxl nếu cần
    try:
        from openpyxl import Workbook
    except ImportError:
        print("Installing openpyxl...")
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
        from openpyxl import Workbook
    
    root = tk.Tk()
    app = SimpleExcelCreator(root)
    root.mainloop()