import tkinter as tk
from tkinter import filedialog
import openpyxl
import pyxlsb
import os


from pyxlsb import open_workbook


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

def get_column_data_and_write(file_path, txt_file_path, sheet_index=1, start_row=6, column_index=1):
    existing_data = read_existing_data(txt_file_path)
    with open_workbook(file_path) as wb:
        with wb.get_sheet(sheet_index) as sheet:
            for row_idx, row in enumerate(sheet.rows(), start=1):
                if start_row <= row_idx <= get_max_row_with_data(file_path):
                    try:
                        cell_value = row[column_index].v
                        if cell_value is not None and cell_value not in existing_data:
                            existing_data.append(cell_value)
                            write_unique_data(txt_file_path, [cell_value])
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

def CheckData():
    print("Excel link là :", excel_link)
    print("Excel extension là:", excel_file_extension)
    if not excel_link:
        print("Vui lòng chọn file Excel trước khi bắt đầu.")
        return
    if excel_file_extension == '.xlsb':
        print("Đang xử lý file .xlsb bằng pyxlsb...")
        try:
            # Xử lý file .xlsb bằng pyxlsb
            workbook = pyxlsb.open_workbook(excel_link)
            sheet_name = workbook.sheets[0]
            print("sheet name là : ",sheet_name)
            
            max_row = get_max_row_with_data(excel_link,1)
            print(f"max row là : {max_row}")
            get_column_data_and_write(excel_link, 'DataMSMR.txt')
            
        except FileNotFoundError:
            print(f"File Excel {excel_file_extension} không tồn tại.")
        except Exception as e:
            print(f"Lỗi trong quá trình xử lý file {excel_file_extension}:", e)

    else:
        print(f"Định dạng file {excel_file_extension} không được hỗ trợ.")


# Tạo cửa sổ giao diện (không đổi)
root = tk.Tk()
root.title("Chương trình xử lý dữ liệu Excel")

btn_chon_file = tk.Button(root, text="Chọn file Excel", command=Pick_ExcelFile)
btn_chon_file.pack(pady=10)

btn_start = tk.Button(root, text="Start", command=CheckData)
btn_start.pack(pady=5)

root.mainloop()