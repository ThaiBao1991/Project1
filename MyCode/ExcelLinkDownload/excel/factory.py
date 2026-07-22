# excel/factory.py
import os
import tkinter as tk
from tkinter import messagebox
from .openpyxl_reader import OpenpyxlReader
from .pyxlsb_reader import PyxlsbReader
from .xlrd_reader import XlrdReader

def create_reader(filepath: str, parent_widget=None):
    """Tạo reader phù hợp dựa trên extension của file"""
    ext = os.path.splitext(filepath)[1].lower()
    
    if ext in ['.xlsx', '.xlsm', '.xltx', '.xltm']:
        return OpenpyxlReader(filepath)
    
    elif ext == '.xlsb':
        return PyxlsbReader(filepath)
    
    elif ext == '.xls':
        # Hiển thị cảnh báo cho file .xls cũ
        root = tk.Tk()
        root.withdraw()  # Ẩn cửa sổ chính
        result = messagebox.askyesno(
            "Cảnh báo - Định dạng file cũ",
            f"File {os.path.basename(filepath)} là định dạng .xls (Excel 97-2003).\n\n"
            "⚠️ LƯU Ý:\n"
            "- Việc đọc hyperlink từ file .xls có thể không chính xác 100%\n"
            "- Các ô hiển thị 'XEM', 'NO' có thể không parse được link\n"
            "- Khuyến nghị: Chuyển file sang .xlsx để có kết quả tốt nhất\n\n"
            "Bạn vẫn muốn mở file này không?",
            icon='warning'
        )
        root.destroy()
        
        if not result:
            raise ValueError("Người dùng đã hủy mở file .xls")
        
        return XlrdReader(filepath)
    
    else:
        raise ValueError(f"Không hỗ trợ định dạng file: {ext}")