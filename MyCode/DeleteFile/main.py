"""
Ứng dụng xóa file thông minh với các ngoại lệ
Entry point chính của chương trình
"""

import tkinter as tk
from config_manager import ConfigManager
from gui import FileDeleterGUI

def main():
    """Hàm chính khởi động ứng dụng"""
    try:
        # Khởi tạo root window
        root = tk.Tk()
        
        # Khởi tạo config manager
        config_manager = ConfigManager("config.json")
        
        # Khởi tạo GUI
        app = FileDeleterGUI(root, config_manager)
        
        # Chạy ứng dụng
        root.mainloop()
        
    except Exception as e:
        print(f"Lỗi khi khởi động ứng dụng: {e}")
        input("Nhấn Enter để thoát...")

if __name__ == "__main__":
    main()