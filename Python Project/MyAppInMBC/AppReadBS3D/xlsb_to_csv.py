import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox

class XlsbToCsvConverter:
    def __init__(self, root, back_to_menu_callback):
        self.root = root
        self.back_to_menu = back_to_menu_callback

        self.file_xlsb = None
        self.file_csv = None
        self.header_row = tk.StringVar(value="0")

        tk.Label(root, text="Chuyển đổi .xlsb sang .csv", font=("Arial", 14, "bold")).pack(pady=10)
        frame = tk.Frame(root)
        frame.pack(pady=10)

        self.select_xlsb_button = tk.Button(frame, text="Chọn file .xlsb", command=self.select_xlsb, font=("Arial", 10))
        self.select_xlsb_button.grid(row=0, column=0, padx=5, pady=5)
        self.xlsb_label = tk.Label(frame, text="Chưa chọn file .xlsb", font=("Arial", 10))
        self.xlsb_label.grid(row=0, column=1, padx=5, pady=5)

        self.select_csv_button = tk.Button(frame, text="Chọn nơi lưu .csv", command=self.select_csv, font=("Arial", 10))
        self.select_csv_button.grid(row=1, column=0, padx=5, pady=5)
        self.csv_label = tk.Label(frame, text="Chưa chọn nơi lưu .csv", font=("Arial", 10))
        self.csv_label.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(frame, text="Chọn dòng làm tiêu đề:", font=("Arial", 10)).grid(row=2, column=0, padx=5, pady=5)
        self.header_entry = tk.Entry(frame, textvariable=self.header_row, width=5, font=("Arial", 10), justify="center")
        self.header_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        tk.Label(frame, text="(0 là dòng đầu, 1 là dòng thứ hai,...)", font=("Arial", 8, "italic")).grid(row=3, column=1, padx=5, pady=0, sticky="w")

        self.start_button = tk.Button(root, text="Start", command=self.start_conversion, font=("Arial", 12, "bold"), 
                                      bg="green", fg="white", width=10, state="disabled")
        self.start_button.pack(pady=10)

        tk.Button(root, text="Quay lại menu", command=self.back_to_menu, font=("Arial", 10), bg="gray", fg="white").pack(pady=10)

        self.header_row.trace("w", self.validate_header_input)

    def validate_header_input(self, *args):
        value = self.header_row.get()
        if not value.isdigit() and value != "":
            self.header_row.set("0")
        self.check_start_button()

    def select_xlsb(self):
        self.file_xlsb = filedialog.askopenfilename(title="Chọn file .xlsb", filetypes=[("Excel Binary Files", "*.xlsb"), ("All Files", "*.*")])
        if self.file_xlsb:
            self.xlsb_label.config(text=f"File: {self.file_xlsb.split('/')[-1]}")
            self.check_start_button()
        else:
            self.xlsb_label.config(text="Chưa chọn file .xlsb")

    def select_csv(self):
        self.file_csv = filedialog.asksaveasfilename(title="Lưu file .csv", defaultextension=".csv", filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")])
        if self.file_csv:
            self.csv_label.config(text=f"Lưu tại: {self.file_csv.split('/')[-1]}")
            self.check_start_button()
        else:
            self.csv_label.config(text="Chưa chọn nơi lưu .csv")

    def check_start_button(self):
        header_value = self.header_row.get()
        if self.file_xlsb and self.file_csv and header_value.isdigit():
            self.start_button.config(state="normal")
        else:
            self.start_button.config(state="disabled")

    def start_conversion(self):
        try:
            header_row = int(self.header_row.get())
            if header_row < 0:
                raise ValueError("Dòng tiêu đề không thể là số âm!")
            df = pd.read_excel(self.file_xlsb, engine="pyxlsb", header=header_row)
            df.to_csv(self.file_csv, index=False, encoding='utf-8-sig')
            messagebox.showinfo("Thành công", f"Đã chuyển đổi từ {self.file_xlsb.split('/')[-1]} sang {self.file_csv.split('/')[-1]} "
                                             f"với tiêu đề lấy từ dòng {header_row}")
        except ValueError as ve:
            messagebox.showerror("Lỗi", f"Giá trị dòng tiêu đề không hợp lệ: {str(ve)}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Đã xảy ra lỗi: {str(e)}")