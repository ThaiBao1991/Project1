import tkinter as tk
from xlsb_to_csv import XlsbToCsvConverter
from email_sender import EmailSender
from file_encryption import FileEncryption
from file_splitter import FileSplitter

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Ứng dụng đa năng")
        self.root.geometry("500x450")  # Tăng chiều cao để chứa thêm nút
        self.show_menu()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_menu(self):
        self.clear_window()
        tk.Label(self.root, text="Chọn tính năng", font=("Arial", 14, "bold")).pack(pady=20)

        tk.Button(self.root, text="1. Đổi file .xlsb sang .csv", font=("Arial", 12), 
                  command=self.show_xlsb_to_csv, width=25).pack(pady=10)
        tk.Button(self.root, text="2. Gửi email tự động", font=("Arial", 12), 
                  command=self.show_email_sender, width=25).pack(pady=10)
        tk.Button(self.root, text="3. Mã hóa và giải mã file", font=("Arial", 12), 
                  command=self.show_file_encryption, width=25).pack(pady=10)
        tk.Button(self.root, text="4. Split và merge file", font=("Arial", 12), 
                  command=self.show_file_splitter, width=25).pack(pady=10)

    def show_xlsb_to_csv(self):
        self.clear_window()
        self.xlsb_converter = XlsbToCsvConverter(self.root, self.show_menu)

    def show_email_sender(self):
        self.clear_window()
        self.email_sender = EmailSender(self.root, self.show_menu)

    def show_file_encryption(self):
        self.clear_window()
        self.file_encryption = FileEncryption(self.root, self.show_menu)

    def show_file_splitter(self):
        self.clear_window()
        self.file_splitter = FileSplitter(self.root, self.show_menu)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()