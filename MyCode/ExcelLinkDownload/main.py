# main.py
import tkinter as tk
from tkinter import ttk
from gui_main import MainTab
from gui_update import UpdateTab
from config import APP_NAME, APP_VERSION

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        
        # Phóng to hết cỡ màn hình khi mở
        try:
            self.root.state('zoomed')  # Windows
        except:
            try:
                self.root.attributes('-zoomed', True)  # Linux
            except:
                self.root.geometry("1200x800")  # Fallback
        
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Arial", 10, "bold"))
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.main_tab = MainTab(self.notebook)
        self.notebook.add(self.main_tab, text="Tải dữ liệu")
        
        self.update_tab = UpdateTab(self.notebook)
        self.notebook.add(self.update_tab, text="Cập nhật Excel")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = App()
    app.run()