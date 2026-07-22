import tkinter as tk
from gui import ExcelConverterGUI
from data_exporter_gui import DataExporterGUI # Import lớp mới

class MainApplication:
    def __init__(self, master):
        self.master = master
        master.title("Ứng dụng Excel")
        master.geometry("300x100")
        master.resizable(False, False)

        self.converter_gui = ExcelConverterGUI(master)
        self.exporter_gui = DataExporterGUI(master) # Khởi tạo lớp GUI mới

        self.create_menu()

    def create_menu(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Chuyển đổi file", command=self.show_converter_gui)
        file_menu.add_command(label="Xuất dữ liệu 4 Điểm", command=self.show_exporter_gui) # Thêm mục menu mới
        file_menu.add_separator()
        file_menu.add_command(label="Thoát", command=self.master.quit)

    def show_converter_gui(self):
        self.converter_gui.top_level.deiconify()
        self.converter_gui.top_level.lift()

    def show_exporter_gui(self): # Hàm mới để hiển thị GUI xuất dữ liệu
        self.exporter_gui.top_level.deiconify()
        self.exporter_gui.top_level.lift()

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()