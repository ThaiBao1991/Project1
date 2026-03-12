import tkinter as tk
from tkinter import filedialog, messagebox
import os
import excel_processor # Import module xử lý Excel

class ExcelConverterGUI:
    def __init__(self, master):
        self.master = master
        self.top_level = None # Để giữ tham chiếu đến cửa sổ Toplevel
        self.create_conversion_window() # Gọi hàm tạo cửa sổ ngay khi khởi tạo

    def create_conversion_window(self):
        """Tạo và hiển thị cửa sổ chuyển đổi file."""
        if self.top_level is not None and self.top_level.winfo_exists():
            # Nếu cửa sổ đã tồn tại, đưa nó lên đầu
            self.top_level.deiconify()
            self.top_level.lift()
            return

        self.top_level = tk.Toplevel(self.master)
        self.top_level.title("Chuyển đổi & Cắt Excel (Giữ công thức, định dạng)")
        self.top_level.protocol("WM_DELETE_WINDOW", self.hide_window) # Xử lý đóng cửa sổ

        # Frame chọn file
        file_frame = tk.LabelFrame(self.top_level, text="Chọn file đầu vào (.xlsb, .xlsm, .xlsx, .xls)", padx=5, pady=5)
        file_frame.pack(padx=10, pady=5, fill=tk.X)

        self.input_entry = tk.Entry(file_frame, width=50)
        self.input_entry.pack(side=tk.LEFT, padx=5)

        browse_btn = tk.Button(file_frame, text="Duyệt...", command=self.browse_file)
        browse_btn.pack(side=tk.LEFT, padx=5)

        # Frame cài đặt cột
        col_frame = tk.LabelFrame(self.top_level, text="Cài đặt cột (Chỉ số 0 = cột A)", padx=5, pady=5)
        col_frame.pack(padx=10, pady=5, fill=tk.X)

        tk.Label(col_frame, text="Cột bắt đầu (0 = cột A):").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.first_col_entry = tk.Entry(col_frame, width=15)
        self.first_col_entry.grid(row=0, column=1, padx=5, pady=2)
        self.first_col_entry.insert(0, "0") # Giá trị mặc định

        tk.Label(col_frame, text="Cột kết thúc (Để trống nếu lấy hết):").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.start_col_entry = tk.Entry(col_frame, width=15)
        self.start_col_entry.grid(row=1, column=1, padx=5, pady=2)

        # Frame cài đặt dòng
        row_frame = tk.LabelFrame(self.top_level, text="Cài đặt dòng (Chỉ số 0 = dòng 1)", padx=5, pady=5)
        row_frame.pack(padx=10, pady=5, fill=tk.X)

        tk.Label(row_frame, text="Dòng bắt đầu (0 = dòng 1):").grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        self.first_row_entry = tk.Entry(row_frame, width=15)
        self.first_row_entry.grid(row=0, column=1, padx=5, pady=2)
        self.first_row_entry.insert(0, "0") # Giá trị mặc định

        tk.Label(row_frame, text="Dòng kết thúc (Để trống nếu lấy hết):").grid(row=1, column=0, padx=5, pady=2, sticky=tk.W)
        self.start_row_entry = tk.Entry(row_frame, width=15)
        self.start_row_entry.grid(row=1, column=1, padx=5, pady=2)

        # Frame nút điều khiển
        button_frame = tk.Frame(self.top_level, padx=5, pady=5)
        button_frame.pack(padx=10, pady=5, fill=tk.X)

        start_btn = tk.Button(button_frame, text="Start", command=self.convert_excel)
        start_btn.pack(side=tk.LEFT, padx=5)

        close_btn = tk.Button(button_frame, text="Đóng", command=self.hide_window)
        close_btn.pack(side=tk.LEFT, padx=5)
        
        # Ẩn cửa sổ ban đầu
        self.top_level.withdraw()

    def hide_window(self):
        """Ẩn cửa sổ thay vì đóng hoàn toàn."""
        if self.top_level:
            self.top_level.withdraw()

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Chọn file",
            filetypes=(("Excel Files", "*.xlsb;*.xlsm;*.xlsx;*.xls"), ("All Files", "*.*"))
        )
        if file_path:
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, file_path)

    def convert_excel(self):
        input_path = self.input_entry.get()
        
        try:
            first_col_idx = int(self.first_col_entry.get()) if self.first_col_entry.get() else 0
            start_col_idx = int(self.start_col_entry.get()) if self.start_col_entry.get() else None
            first_row_idx = int(self.first_row_entry.get()) if self.first_row_entry.get() else 0
            start_row_idx = int(self.start_row_entry.get()) if self.start_row_entry.get() else None
        except ValueError:
            messagebox.showerror("Lỗi", "Các giá trị nhập vào phải là số nguyên.")
            return
        
        # Gọi hàm xử lý từ module excel_processor
        excel_processor.process_excel_file(
            input_path, 
            first_col_idx, 
            start_col_idx, 
            first_row_idx, 
            start_row_idx
        )