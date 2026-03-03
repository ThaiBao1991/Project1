import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import openpyxl
import pyxlsb
import os
from pyxlsb import open_workbook
import time

excel_link = None
excel_file_extension = None

def Pick_ExcelFile():
    global excel_link, excel_file_extension
    excel_link_temp = filedialog.askopenfilename(filetypes=[("Excel Files", "*.xlsb;*.xls;*.xlsx;*.xlsm")])
    if excel_link_temp:
        excel_link = excel_link_temp
        excel_file_extension = os.path.splitext(excel_link)[1].lower()
        print(f"Đã chọn file Excel: {excel_link} (Định dạng: {excel_file_extension})")
    else:
        print("Bạn chưa chọn file Excel.")
        excel_link = None
        excel_file_extension = None

def get_max_row_with_data(file_path, sheet_index=1):
    max_row = 0
    with open_workbook(file_path) as wb:
        with wb.get_sheet(sheet_index) as sheet:
            for row_idx, row in enumerate(sheet.rows(), start=1):
                if any(cell.v is not None for cell in row):
                    max_row = row_idx
    return max_row

def get_column_data_and_write(file_path, txt_file_path, sheet_index=1, start_row=6, column_index=1, progress_window=None):
    existing_data = read_existing_data(txt_file_path)
    with open_workbook(file_path) as wb:
        with wb.get_sheet(sheet_index) as sheet:
            max_row = get_max_row_with_data(file_path)
            for row_idx, row in enumerate(sheet.rows(), start=1):
                if start_row <= row_idx <= max_row:
                    try:
                        cell_value = row[column_index].v
                        if cell_value is not None and cell_value not in existing_data:
                            existing_data.append(cell_value)
                            write_unique_data(txt_file_path, [cell_value])
                            # Cập nhật giao diện tiến độ theo thời gian thực
                            if progress_window:
                                progress_window.update_progress(f"Đang xử lý dòng {row_idx}: {cell_value}")
                                progress_window.listbox.insert(tk.END, f"Dòng {row_idx}: {cell_value}")
                                progress_window.listbox.see(tk.END)  # Cuộn xuống cuối danh sách
                                # Đảm bảo giao diện cập nhật ngay lập tức
                                progress_window.window.update()
                        time.sleep(0.1)  # Thêm độ trễ nhỏ để giao diện cập nhật mượt mà
                    except IndexError:
                        continue

def read_existing_data(file_path):
    try:
        with open(file_path, 'r') as f:
            existing_data = f.read().splitlines()
    except FileNotFoundError:
        existing_data = []
    return existing_data

def write_unique_data(file_path, data):
    with open(file_path, 'a') as f:
        for item in data:
            f.write(f"{item}\n")

class ProgressWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Tiến trình xử lý")
        self.window.geometry("400x500")
        
        # Label tiêu đề
        self.label = tk.Label(self.window, text="Tiến trình xử lý dữ liệu:")
        self.label.pack(pady=5)
        
        # Listbox để hiển thị mã hàng
        self.listbox = tk.Listbox(self.window, height=20, width=50)
        self.listbox.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.window, length=300, mode='determinate')
        self.progress.pack(pady=5)
        
        # Label tiến độ
        self.progress_label = tk.Label(self.window, text="")
        self.progress_label.pack(pady=5)
        
        # Nút đóng (có thể ẩn hoặc để tùy chọn)
        self.close_button = tk.Button(self.window, text="Đóng", command=self.window.destroy)
        self.close_button.pack(pady=5)

    def update_progress(self, message):
        self.progress_label.config(text=message)
        # Cập nhật tiến độ dựa trên số dòng
        try:
            row_num = int(message.split("đường")[1].split(":")[0].strip())
            total_rows = get_max_row_with_data(excel_link) - 5  # Giả sử bắt đầu từ dòng 6
            if total_rows > 0:
                progress = (row_num - 5) / total_rows * 100
                self.progress['value'] = progress
        except (IndexError, ValueError):
            pass
        self.window.update()

def CheckData():
    print("Excel link là :", excel_link)
    print("Excel extension là:", excel_file_extension)
    if not excel_link:
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn file Excel trước khi bắt đầu.")
        return
    if excel_file_extension == '.xlsb':
        print("Đang xử lý file .xlsb bằng pyxlsb...")
        try:
            # Tạo và hiển thị cửa sổ tiến trình ngay lập tức
            progress_window = ProgressWindow(root)
            progress_window.window.update()  # Đảm bảo cửa sổ hiển thị trước khi xử lý
            
            workbook = pyxlsb.open_workbook(excel_link)
            sheet_name = workbook.sheets[0]
            print("Sheet name là :", sheet_name)
            
            max_row = get_max_row_with_data(excel_link, 1)
            print(f"Max row là : {max_row}")
            get_column_data_and_write(excel_link, 'DataMSMR.txt', sheet_index=1, start_row=6, column_index=1, progress_window=progress_window)
            
            messagebox.showinfo("Hoàn thành", "Xử lý file Excel thành công!")
            progress_window.window.destroy()
            
        except FileNotFoundError:
            messagebox.showerror("Lỗi", f"File Excel {excel_file_extension} không tồn tại.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi trong quá trình xử lý file {excel_file_extension}: {str(e)}")
    else:
        messagebox.showwarning("Cảnh báo", f"Định dạng file {excel_file_extension} không được hỗ trợ.")

# Tạo cửa sổ giao diện
root = tk.Tk()
root.title("Chương trình xử lý dữ liệu Excel")

btn_chon_file = tk.Button(root, text="Chọn file Excel", command=Pick_ExcelFile)
btn_chon_file.pack(pady=10)

btn_start = tk.Button(root, text="Start", command=CheckData)
btn_start.pack(pady=5)

root.mainloop()