import os
import zipfile
import win32com.client
from tkinter import messagebox
import csv
import time
import re
import shutil
import json # Thêm thư viện json

# --- Đường dẫn file JSON để lưu trạng thái tải về ---
# Đặt nó ở đây để có thể truy cập từ các hàm khác nếu cần,
# hoặc có thể truyền vào hàm fetch_hyperlink_data nếu muốn linh hoạt hơn.
# Hiện tại, đặt trong cùng thư mục với script là tiện lợi.
# data_getlink_json_path = "data_getlink.json"
# Sẽ đặt trong thư mục Data DL4D do người dùng chọn
# ----------------------------------------------------

def is_valid_excel_file(file_path):
    """Kiểm tra file Excel hợp lệ (bao gồm cả .xlsm)"""
    try:
        if file_path.lower().endswith('.xlsm'):
            with zipfile.ZipFile(file_path, 'r') as z:
                return 'xl/workbook.xml' in z.namelist()
        return True
    except Exception:
        return False

def process_excel_file(input_path, first_col_idx, start_col_idx, first_row_idx, start_row_idx):
    """
    Xử lý file Excel: Xóa các cột/dòng không nằm trong phạm vi định nghĩa.
    Giữ nguyên công thức và định dạng.
    """
    if not os.path.exists(input_path):
        messagebox.showerror("Lỗi", "File không tồn tại.")
        return False

    if not is_valid_excel_file(input_path):
        messagebox.showerror("Lỗi", "File không phải là Excel hợp lệ hoặc đã bị hỏng.")
        return False

    file_ext = os.path.splitext(input_path)[1].lower()
    
    output_file_format = 51
    output_extension = "_converted.xlsx"

    if file_ext == '.xlsm':
        output_file_format = 52
        output_extension = "_converted.xlsm"

    if file_ext not in ('.xlsb', '.xlsm', '.xlsx', '.xls'):
        messagebox.showerror("Lỗi", "Chỉ hỗ trợ file .xlsb, .xlsm, .xlsx và .xls.")
        return False

    output_path = os.path.splitext(input_path)[0] + output_extension

    excel = None
    try:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        excel.AskToUpdateLinks = False
        excel.ScreenUpdating = False

        wb = excel.Workbooks.Open(os.path.abspath(input_path))

        for ws in wb.Worksheets:
            max_row = ws.Cells.SpecialCells(11).Row
            max_col = ws.Cells.SpecialCells(11).Column

            if first_row_idx > 0:
                ws.Rows(f"1:{first_row_idx}").Delete()

            current_max_row = ws.Cells.SpecialCells(11).Row
            if start_row_idx is not None and start_row_idx + 1 < current_max_row:
                ws.Rows(f"{start_row_idx + 2}:{current_max_row}").Delete()

            if first_col_idx > 0:
                ws.Columns(f"1:{first_col_idx}").Delete()

            current_max_col = ws.Cells.SpecialCells(11).Column
            if start_col_idx is not None and start_col_idx + 1 < current_max_col:
                ws.Columns(f"{start_col_idx + 2}:{current_max_col}").Delete()
        
        wb.SaveAs(os.path.abspath(output_path), FileFormat=output_file_format)
        wb.Close(SaveChanges=False)

        messagebox.showinfo("Thành công", f"Đã chuyển đổi và cắt file thành công:\n{output_path}")
        return True

    except Exception as e:
        messagebox.showerror("Lỗi", f"Có lỗi xảy ra khi xử lý file Excel:\n{str(e)}")
        return False
    finally:
        if excel:
            excel.DisplayAlerts = True
            excel.ScreenUpdating = True
            excel.AskToUpdateLinks = True
            excel.Quit()

def export_4_point_data(excel_file_path, output_folder_path, progress_callback=None):
    if not os.path.exists(excel_file_path):
        messagebox.showerror("Lỗi", "File Excel bộ 4 điểm không tồn tại.")
        return False

    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)

    data_loc_path = os.path.join(output_folder_path, "data_loc.csv")

    excel = None
    try:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        excel.AskToUpdateLinks = False
        excel.ScreenUpdating = False

        wb_com = excel.Workbooks.Open(os.path.abspath(excel_file_path))
        ws_com = wb_com.Sheets(1)

        header_b1 = ws_com.Cells(1, 2).Value

        existing_data = {}
        if os.path.exists(data_loc_path):
            with open(data_loc_path, 'r', newline='', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if len(row) >= 3:
                        existing_data[row[0]] = {
                            'line': int(row[1]), 
                            'non_empty_count': int(row[2])
                        }

        updated_data = existing_data.copy()

        last_row = ws_com.Cells.SpecialCells(11).Row 
        
        relevant_columns_indices = [2, 8, 30, 32, 34, 36, 38, 40] 
        
        max_relevant_col_idx = max(relevant_columns_indices)
        max_relevant_col_letter = _col_idx_to_excel_col(max_relevant_col_idx)

        if last_row < 2:
            excel_data = ()
        else:
            excel_data_range = ws_com.Range(f"B2:{max_relevant_col_letter}{last_row}")
            excel_data = excel_data_range.Value
            
            if excel_data is not None and not isinstance(excel_data, tuple):
                 excel_data = ((excel_data,),)
            elif excel_data is not None and isinstance(excel_data, tuple) and not isinstance(excel_data[0], tuple):
                excel_data = (excel_data,)
            elif excel_data is None:
                 excel_data = ()

        current_row_excel_index_offset = 2

        col_b_idx_in_array = 0
        relevant_cols_in_array = [idx - 2 for idx in relevant_columns_indices[1:]]

        for i, row_data in enumerate(excel_data):
            current_excel_row = i + current_row_excel_index_offset

            cell_b_value = row_data[col_b_idx_in_array]
            cell_b_str = str(cell_b_value).strip() if cell_b_value is not None else ""

            non_empty_count = 0
            for col_array_idx in relevant_cols_in_array:
                if col_array_idx < len(row_data):
                    cell_value = row_data[col_array_idx]
                    if cell_value is not None and (isinstance(cell_value, str) and str(cell_value).strip() != ""):
                        non_empty_count += 1
                
            if progress_callback:
                progress_callback(current_excel_row, cell_b_str, non_empty_count)

            if cell_b_str and cell_b_str not in updated_data:
                updated_data[cell_b_str] = {
                    'line': current_excel_row,
                    'non_empty_count': non_empty_count
                }
            elif cell_b_str and non_empty_count > updated_data[cell_b_str]['non_empty_count']:
                updated_data[cell_b_str] = {
                    'line': current_excel_row,
                    'non_empty_count': non_empty_count
                }

        wb_com.Close(SaveChanges=False)
        
        with open(data_loc_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow([header_b1, "Dòng Excel", "Tổng ô khác rỗng"])
            for name, data in updated_data.items():
                writer.writerow([name, data['line'], data['non_empty_count']])

        messagebox.showinfo("Thành công", f"Đã xuất dữ liệu thành công vào:\n{data_loc_path}")
        return True

    except Exception as e:
        messagebox.showerror("Lỗi", f"Có lỗi xảy ra khi xuất dữ liệu:\n{str(e)}")
        return False
    finally:
        if excel:
            excel.DisplayAlerts = True
            excel.ScreenUpdating = True
            excel.AskToUpdateLinks = True
            excel.Quit()

def _col_idx_to_excel_col(idx):
    """Chuyển đổi chỉ số cột số nguyên (1-based) sang ký tự cột Excel (A, B, AA, ...)"""
    result = ""
    while idx > 0:
        idx, remainder = divmod(idx - 1, 26)
        result = chr(65 + remainder) + result
    return result

def _read_getlink_status(json_path):
    """Đọc trạng thái tải về từ file JSON."""
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"Cảnh báo: File JSON '{json_path}' bị lỗi định dạng. Tạo mới.")
            return {}
    return {}

def _write_getlink_status(json_path, status_data):
    """Ghi trạng thái tải về vào file JSON."""
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Lỗi khi ghi file JSON '{json_path}': {e}")


# --- Hàm chính cho tính năng "Lấy dữ liệu" ---
def fetch_hyperlink_data(excel_file_path, data_loc_folder, progress_callback=None):
    if not os.path.exists(excel_file_path):
        messagebox.showerror("Lỗi", "File Excel bộ 4 điểm không tồn tại.")
        return False
    
    data_loc_csv_path = os.path.join(data_loc_folder, "data_loc.csv")
    if not os.path.exists(data_loc_csv_path):
        messagebox.showerror("Lỗi", f"Không tìm thấy file data_loc.csv tại:\n{data_loc_csv_path}\nVui lòng 'Xuất Data' trước.")
        return False

    # Định nghĩa đường dẫn file JSON
    data_getlink_json_path = os.path.join(data_loc_folder, "data_getlink.json")
    
    # Đọc dữ liệu từ data_loc.csv
    data_to_fetch = []
    try:
        with open(data_loc_csv_path, 'r', newline='', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader) # Bỏ qua header
            for row in reader:
                if len(row) >= 2:
                    name = row[0]
                    line_num = int(row[1])
                    data_to_fetch.append({'name': name, 'line': line_num})
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể đọc file data_loc.csv:\n{e}")
        return False

    # Đọc trạng thái tải về hiện có từ JSON
    download_status = _read_getlink_status(data_getlink_json_path)

    excel = None
    try:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        excel.AskToUpdateLinks = False
        excel.ScreenUpdating = False

        wb_com = excel.Workbooks.Open(os.path.abspath(excel_file_path))
        ws_com = wb_com.Sheets(1) # Giả định dữ liệu ở sheet đầu tiên

        relevant_columns = [8, 30, 32, 34, 36, 38, 40] # Cột H, AD, AF, AH, AJ, AL, AN

        total_items = len(data_to_fetch)
        processed_count = 0
        downloaded_count = 0 # Đếm số file đã tải hoặc đã tồn tại

        for item in data_to_fetch:
            name = item['name']
            line_num = item['line']
            
            processed_count += 1
            if progress_callback:
                progress_callback(f"Đang xử lý: {name} (Dòng {line_num})", processed_count, total_items)
            
            # Tạo thư mục con cho mỗi "Mã số bộ tiêu chuẩn"
            output_subdir = os.path.join(data_loc_folder, name)
            if not os.path.exists(output_subdir):
                os.makedirs(output_subdir)

            for col_idx in relevant_columns:
                cell = ws_com.Cells(line_num, col_idx)
                
                if cell.HasFormula:
                    formula = cell.Formula
                    
                    hyperlink_match = re.search(
                        r'HYPERLINK\("?([^"]*)"?&?([A-Za-z]+\d+)?&?"([^"]*)",',
                        formula, re.IGNORECASE
                    )
                    
                    if hyperlink_match:
                        part1 = hyperlink_match.group(1)
                        ref_cell_str = hyperlink_match.group(2)
                        part2 = hyperlink_match.group(3)
                        
                        full_file_path = ""

                        try:
                            if ref_cell_str:
                                ref_cell_value = ws_com.Range(ref_cell_str).Value
                                if ref_cell_value is not None:
                                    full_file_path = part1 + str(ref_cell_value) + part2
                                else:
                                    # print(f"Giá trị ô tham chiếu ({ref_cell_str}) rỗng cho {name} ở dòng {line_num}. Không tạo đường dẫn.")
                                    continue
                            else:
                                full_file_path = part1 + part2 
                            
                            if full_file_path:
                                filename = os.path.basename(full_file_path)
                                destination_path = os.path.join(output_subdir, filename)
                                
                                # --- Kiểm tra trạng thái tải về trước khi tải ---
                                if name in download_status and filename in download_status[name] and \
                                   os.path.exists(destination_path):
                                    print(f"File đã tồn tại và được ghi nhận: {filename} trong {name}/")
                                    downloaded_count += 1
                                    continue # Bỏ qua, không tải lại
                                # -------------------------------------------------

                                if os.path.exists(full_file_path):
                                    try:
                                        shutil.copy2(full_file_path, destination_path)
                                        print(f"Đã sao chép: {filename} vào {name}/")
                                        downloaded_count += 1
                                        
                                        # --- Cập nhật trạng thái tải về vào JSON ---
                                        if name not in download_status:
                                            download_status[name] = []
                                        if filename not in download_status[name]: # Tránh trùng lặp trong list
                                            download_status[name].append(filename)
                                        _write_getlink_status(data_getlink_json_path, download_status)
                                        # ---------------------------------------------
                                        
                                    except Exception as copy_err:
                                        print(f"Lỗi sao chép {filename}: {copy_err}")
                                        messagebox.showwarning("Cảnh báo", f"Không thể sao chép file:\n{filename}\nVào thư mục:\n{name}\nLỗi: {copy_err}")
                                else:
                                    print(f"File nguồn không tồn tại: {full_file_path}")
                                    # messagebox.showwarning("Cảnh báo", f"File nguồn không tồn tại:\n{full_file_path}")
                            else:
                                print(f"Không thể tạo đường dẫn đầy đủ cho {name} ở dòng {line_num}.")

                        except Exception as ref_err:
                            print(f"Lỗi khi xử lý ô tham chiếu hoặc đường dẫn cho {name} (Dòng {line_num}, Cột {_col_idx_to_excel_col(col_idx)}): {ref_err}")
                            # messagebox.showwarning("Cảnh báo", f"Lỗi khi xử lý file cho {name} (Dòng {line_num}, Cột {_col_idx_to_excel_col(col_idx)}):\n{ref_err}")
        
        wb_com.Close(SaveChanges=False)
        messagebox.showinfo("Hoàn tất", f"Đã lấy dữ liệu hoàn tất cho {downloaded_count} file (bao gồm cả file đã có).")
        return True

    except Exception as e:
        messagebox.showerror("Lỗi", f"Có lỗi xảy ra khi lấy dữ liệu từ Excel:\n{str(e)}")
        return False
    finally:
        if excel:
            excel.DisplayAlerts = True
            excel.ScreenUpdating = True
            excel.AskToUpdateLinks = True
            excel.Quit()