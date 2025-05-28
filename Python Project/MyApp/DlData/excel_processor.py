import os
import zipfile
import win32com.client
from tkinter import messagebox
import csv
import time
import re
import shutil
import json # Thêm thư viện json

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
    
    output_file_format = 51 # xlsx
    output_extension = "_converted.xlsx"

    if file_ext == '.xlsm':
        output_file_format = 52 # xlsm
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

# --- Bổ sung hàm mới cho tính năng Xuất dữ liệu 4 Điểm ---
def export_4_point_data(excel_file_path, base_output_folder, progress_callback=None): # Đổi output_folder_path thành base_output_folder
    if not os.path.exists(excel_file_path):
        messagebox.showerror("Lỗi", "File Excel bộ 4 điểm không tồn tại.")
        return False

    # --- ĐỊNH NGHĨA THƯ MỤC GỐC "Data B4D" VÀ TẠO NẾU CHƯA CÓ ---
    # File data_loc.csv sẽ nằm trong thư mục này
    data_b4d_base_dir = os.path.join(base_output_folder, "Data B4D")
    if not os.path.exists(data_b4d_base_dir):
        os.makedirs(data_b4d_base_dir)
    # -----------------------------------------------------------

    data_loc_path = os.path.join(data_b4d_base_dir, "data_loc.csv") # Đã sửa đường dẫn file CSV

    excel = None
    try:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        excel.AskToUpdateLinks = False
        excel.ScreenUpdating = False

        wb_com = excel.Workbooks.Open(os.path.abspath(excel_file_path))
        ws_com = wb_com.Sheets(1) # Lấy sheet đầu tiên

        # Lấy giá trị ô B1 làm tiêu đề cho CSV
        header_b1 = ws_com.Cells(1, 2).Value 
        if header_b1 is None:
            header_b1 = "Mã số bộ tiêu chuẩn" # Giá trị mặc định nếu B1 rỗng

        # Đọc dữ liệu CSV hiện có nếu có
        existing_data = {} # key: tên_từ_excel, value: {dòng_excel: ..., tổng_ô_không_rỗng: ...}
        if os.path.exists(data_loc_path):
            with open(data_loc_path, 'r', newline='', encoding='utf-8-sig') as f: # Dùng utf-8-sig để đọc đúng BOM
                reader = csv.reader(f)
                next(reader, None) # Bỏ qua header
                for row in reader:
                    if len(row) >= 3: # Đảm bảo đủ cột: Tên, Dòng, Tổng ô không rỗng
                        try:
                            existing_data[row[0]] = {
                                'line': int(row[1]), 
                                'non_empty_count': int(row[2])
                            }
                        except ValueError:
                            # Bỏ qua dòng lỗi hoặc xử lý phù hợp
                            print(f"Cảnh báo: Bỏ qua dòng lỗi trong data_loc.csv: {row}")
                            continue

        updated_data = existing_data.copy()

        last_row = ws_com.UsedRange.Rows.Count # Lấy dòng cuối cùng có dữ liệu thực tế
        
        # Các cột liên quan bao gồm cả cột B (2) để kiểm tra giá trị chính của dòng
        # Cột H (8), AD (30), AF (32), AH (34), AJ (36), AL (38), AN (40)
        relevant_columns_indices = [2, 8, 30, 32, 34, 36, 38, 40] 
        
        # Đọc toàn bộ vùng dữ liệu liên quan để tối ưu hiệu suất
        # Lấy cột cuối cùng trong các cột liên quan
        max_relevant_col_idx = max(relevant_columns_indices)
        max_relevant_col_letter = _col_idx_to_excel_col(max_relevant_col_idx)

        excel_data = ()
        if last_row >= 2: # Chỉ đọc nếu có ít nhất 1 dòng dữ liệu (từ dòng 2)
            excel_data_range = ws_com.Range(f"B2:{max_relevant_col_letter}{last_row}") # Bắt đầu từ cột B
            excel_data = excel_data_range.Value
            
            # Xử lý trường hợp chỉ có 1 ô/1 dòng dữ liệu đọc ra không phải tuple of tuples
            if excel_data is not None and not isinstance(excel_data, tuple):
                excel_data = ((excel_data,),)
            elif excel_data is not None and isinstance(excel_data, tuple) and not isinstance(excel_data[0], tuple):
                excel_data = (excel_data,) # Chuyển đổi thành tuple of tuples cho 1 dòng

        total_rows_to_process = len(excel_data) if excel_data else 0
        processed_rows_count = 0
        
        # Duyệt qua dữ liệu đọc được từ Excel
        # `excel_data` là một tuple of tuples. Index của cột trong `row_data` sẽ khác với index trong Excel
        # Cột B (Excel index 2) sẽ là index 0 trong `row_data` (vì range bắt đầu từ B)
        # Cột H (Excel index 8) sẽ là index (8 - 2) = 6 trong `row_data`
        # Các cột AD, AF, ... sẽ tương tự (col_excel_idx - 2)
        
        # Tạo ánh xạ từ Excel col index sang array index
        col_map_to_array_idx = {col_idx: col_idx - 2 for col_idx in relevant_columns_indices}
        
        for i, row_data in enumerate(excel_data):
            current_excel_row = i + 2 # Dòng trong Excel (bắt đầu từ 2)
            processed_rows_count += 1

            cell_b_value = row_data[col_map_to_array_idx[2]] # Lấy giá trị cột B (index 0 trong array)
            cell_b_str = str(cell_b_value).strip() if cell_b_value is not None else ""

            # Lấy giá trị cột H (index 6 trong array)
            cell_h_value = row_data[col_map_to_array_idx[8]] if 8 in col_map_to_array_idx and col_map_to_array_idx[8] < len(row_data) else None
            cell_h_str = str(cell_h_value).strip() if cell_h_value is not None else ""

            # Chỉ đếm và xử lý nếu cột B CÓ GIÁ TRỊ HOẶC cột H CÓ GIÁ TRỊ
            if (cell_b_str != "") or (cell_h_str != ""):
                non_empty_count = 0
                for col_idx in relevant_columns_indices:
                    # Kiểm tra xem col_idx có tồn tại trong col_map_to_array_idx và trong row_data không
                    array_idx = col_map_to_array_idx[col_idx]
                    if array_idx < len(row_data):
                        cell_value = row_data[array_idx]
                        if cell_value is not None and str(cell_value).strip() != "":
                            non_empty_count += 1
                
                # Xác định tên để xuất: ưu tiên cột B, nếu B rỗng thì dùng "Chưa có tên"
                name_to_export = cell_b_str if cell_b_str != "" else "Chưa có tên"

                # So sánh và cập nhật dữ liệu để ghi vào CSV
                # Nếu tên chưa có hoặc tổng ô không rỗng mới lớn hơn dữ liệu cũ
                if name_to_export not in updated_data or \
                   non_empty_count > updated_data[name_to_export]['non_empty_count']:
                    
                    updated_data[name_to_export] = {
                        'line': current_excel_row,
                        'non_empty_count': non_empty_count
                    }
            
            # Cập nhật tiến độ sau mỗi dòng được xử lý
            if progress_callback:
                progress_callback(processed_rows_count, current_excel_row, non_empty_count, total_rows_to_process)


        wb_com.Close(SaveChanges=False) # Đóng workbook không cần lưu thay đổi
        
        # Ghi dữ liệu đã cập nhật vào file CSV
        with open(data_loc_path, 'w', newline='', encoding='utf-8-sig') as f: # Dùng utf-8-sig để đảm bảo hiển thị tiếng Việt đúng
            writer = csv.writer(f)
            writer.writerow([header_b1, "Dòng Excel", "Tổng ô khác rỗng"]) # Header
            # Sắp xếp updated_data theo tên (Mã số bộ tiêu chuẩn) để CSV có thứ tự
            sorted_updated_data = sorted(updated_data.items(), key=lambda item: item[0])
            for name, data in sorted_updated_data:
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
    
    # --- ĐỊNH NGHĨA THƯ MỤC GỐC "Data B4D" ---
    # data_loc.csv và data_getlink.json sẽ nằm trong thư mục này
    data_b4d_base_dir = os.path.join(data_loc_folder, "Data B4D")
    if not os.path.exists(data_b4d_base_dir): # Đảm bảo thư mục "Data B4D" tồn tại
        messagebox.showerror("Lỗi", f"Thư mục 'Data B4D' không tồn tại trong:\n{data_loc_folder}\nVui lòng chạy 'Xuất Data' trước.")
        return False
    # ----------------------------------------

    data_loc_csv_path = os.path.join(data_b4d_base_dir, "data_loc.csv") # Đã sửa đường dẫn CSV
    if not os.path.exists(data_loc_csv_path):
        messagebox.showerror("Lỗi", f"Không tìm thấy file data_loc.csv tại:\n{data_loc_csv_path}\nVui lòng 'Xuất Data' trước.")
        return False

    data_getlink_json_path = os.path.join(data_b4d_base_dir, "data_getlink.json") # Đã thay đổi đường dẫn JSON
    
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

    download_status = _read_getlink_status(data_getlink_json_path)

    excel = None
    try:
        excel = win32com.client.Dispatch("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        excel.AskToUpdateLinks = False
        excel.ScreenUpdating = False

        wb_com = excel.Workbooks.Open(os.path.abspath(excel_file_path))
        ws_com = wb_com.Sheets(1) 

        relevant_columns = [8, 30, 32, 34, 36, 38, 40] # Cột H, AD, AF, AH, AJ, AL, AN

        total_items = len(data_to_fetch)
        processed_count = 0
        downloaded_count = 0 

        for item in data_to_fetch:
            name = item['name']
            line_num = item['line']
            
            processed_count += 1
            if progress_callback:
                progress_callback(f"Đang xử lý: {name} (Dòng {line_num})", processed_count, total_items)
            
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
                                    continue
                            else:
                                full_file_path = part1 + part2 
                            
                            if full_file_path:
                                filename = os.path.basename(full_file_path)
                                # Đường dẫn đích trong thư mục "Data B4D"
                                destination_path = os.path.join(data_b4d_base_dir, name, filename) 
                                
                                if name in download_status and filename in download_status[name] and \
                                   os.path.exists(destination_path):
                                    print(f"File đã tồn tại và được ghi nhận: {filename} trong {name}/")
                                    downloaded_count += 1
                                    continue 

                                if os.path.exists(full_file_path):
                                    try:
                                        # TẠO THƯ MỤC CON CHO MÃ HÀNG BÊN TRONG "Data B4D"
                                        output_subdir = os.path.join(data_b4d_base_dir, name)
                                        if not os.path.exists(output_subdir):
                                            os.makedirs(output_subdir)

                                        shutil.copy2(full_file_path, destination_path)
                                        print(f"Đã sao chép: {filename} vào {name}/")
                                        downloaded_count += 1
                                        
                                        if name not in download_status:
                                            download_status[name] = []
                                        if filename not in download_status[name]: 
                                            download_status[name].append(filename)
                                        _write_getlink_status(data_getlink_json_path, download_status)
                                        
                                    except Exception as copy_err:
                                        print(f"Lỗi sao chép {filename}: {copy_err}")
                                        messagebox.showwarning("Cảnh báo", f"Không thể sao chép file:\n{filename}\nVào thư mục:\n{name}\nLỗi: {copy_err}")
                                else:
                                    print(f"File nguồn không tồn tại: {full_file_path}")
                            else:
                                print(f"Không thể tạo đường dẫn đầy đủ cho {name} ở dòng {line_num}.")

                        except Exception as ref_err:
                            print(f"Lỗi khi xử lý ô tham chiếu hoặc đường dẫn cho {name} (Dòng {line_num}, Cột {_col_idx_to_excel_col(col_idx)}): {ref_err}")
        
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
            
# --- Hàm mới cho tính năng "Nhập data đã xuất" ---
def import_exported_data(excel_file_path, data_loc_folder, progress_callback=None):
    if not os.path.exists(excel_file_path):
        messagebox.showerror("Lỗi", "File Excel bộ 4 điểm không tồn tại.")
        return False
    
    # --- ĐỊNH NGHĨA THƯ MỤC GỐC "Data B4D" ---
    # data_loc.csv và data_getlink.json sẽ nằm trong thư mục này
    data_b4d_base_dir = os.path.join(data_loc_folder, "Data B4D")
    if not os.path.exists(data_b4d_base_dir): # Đảm bảo thư mục "Data B4D" tồn tại
        messagebox.showerror("Lỗi", f"Thư mục 'Data B4D' không tồn tại trong:\n{data_loc_folder}\nVui lòng chạy 'Xuất Data' trước.")
        return False
    # ----------------------------------------

    data_loc_csv_path = os.path.join(data_b4d_base_dir, "data_loc.csv") # Đã sửa đường dẫn CSV
    if not os.path.exists(data_loc_csv_path):
        messagebox.showerror("Lỗi", f"Không tìm thấy file data_loc.csv tại:\n{data_loc_csv_path}\nVui lòng 'Xuất Data' trước.")
        return False

    data_getlink_json_path = os.path.join(data_b4d_base_dir, "data_getlink.json") # Đã thay đổi đường dẫn JSON
    
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
        new_files_count = 0 # Đếm số file mới được import

        # Tạo thư mục gốc "NewUpdate" bên trong "Data B4D"
        new_update_base_dir = os.path.join(data_b4d_base_dir, "NewUpdate") # Đã thay đổi đường dẫn NewUpdate
        if not os.path.exists(new_update_base_dir):
            os.makedirs(new_update_base_dir)

        for item in data_to_fetch:
            name = item['name']
            line_num = item['line']
            
            processed_count += 1
            # Cập nhật tiến độ: Đang kiểm tra từng item (mã số bộ tiêu chuẩn)
            if progress_callback:
                progress_callback(f"Đang kiểm tra: {name} (Dòng {line_num})", new_files_count, processed_count, total_items)
            
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
                        
                        full_file_path_source = "" # Đường dẫn file gốc (nguồn)

                        try:
                            if ref_cell_str:
                                ref_cell_value = ws_com.Range(ref_cell_str).Value
                                if ref_cell_value is not None:
                                    full_file_path_source = part1 + str(ref_cell_value) + part2
                                else:
                                    continue # Bỏ qua nếu giá trị tham chiếu rỗng
                            else:
                                full_file_path_source = part1 + part2 
                            
                            if full_file_path_source:
                                filename = os.path.basename(full_file_path_source)
                                
                                # Đường dẫn đích trong thư mục chính (Data B4D/Mã số bộ tiêu chuẩn) để kiểm tra xem đã có chưa
                                destination_path_main = os.path.join(data_b4d_base_dir, name, filename) # Đã thay đổi đường dẫn kiểm tra

                                # Kiểm tra xem file đã được ghi nhận trong JSON và đã tồn tại trong thư mục chính chưa
                                if name in download_status and filename in download_status[name] and \
                                   os.path.exists(destination_path_main):
                                    continue # Bỏ qua, đây không phải là file mới
                                
                                # Nếu file nguồn tồn tại VÀ file này chưa được ghi nhận/chưa có trong thư mục chính
                                if os.path.exists(full_file_path_source):
                                    # --- TẠO THƯ MỤC CON TRONG NEWUPDATE BÊN TRONG "Data B4D" CHỈ KHI CÓ FILE MỚI CẦN SAO CHÉP ---
                                    output_subdir_new_update = os.path.join(new_update_base_dir, name)
                                    if not os.path.exists(output_subdir_new_update):
                                        os.makedirs(output_subdir_new_update)
                                    # -----------------------------------------------------------------------------------------

                                    destination_path_new_update = os.path.join(output_subdir_new_update, filename)
                                    try:
                                        shutil.copy2(full_file_path_source, destination_path_new_update)
                                        print(f"Đã sao chép file MỚI: {filename} vào NewUpdate/{name}/")
                                        new_files_count += 1
                                        
                                        # Cập nhật trạng thái tải về vào JSON
                                        if name not in download_status:
                                            download_status[name] = []
                                        if filename not in download_status[name]:
                                            download_status[name].append(filename)
                                        _write_getlink_status(data_getlink_json_path, download_status)
                                        
                                        # Cập nhật tiến độ sau khi tìm thấy và sao chép file mới
                                        if progress_callback:
                                            progress_callback(f"Đã tìm thấy: {filename}", new_files_count, processed_count, total_items)
                                            
                                    except Exception as copy_err:
                                        print(f"Lỗi sao chép file MỚI {filename}: {copy_err}")
                                        messagebox.showwarning("Cảnh báo", f"Không thể sao chép file MỚI:\n{filename}\nVào thư mục:\nNewUpdate/{name}\nLỗi: {copy_err}")
                                else:
                                    print(f"File nguồn không tồn tại: {full_file_path_source}")
                            else:
                                print(f"Không thể tạo đường dẫn đầy đủ cho {name} ở dòng {line_num}.")

                        except Exception as ref_err:
                            print(f"Lỗi khi xử lý ô tham chiếu hoặc đường dẫn cho {name} (Dòng {line_num}, Cột {_col_idx_to_excel_col(col_idx)}): {ref_err}")
        
        wb_com.Close(SaveChanges=False)
        messagebox.showinfo("Hoàn tất", f"Đã kiểm tra và nhập {new_files_count} file mới vào thư mục 'NewUpdate'.")
        return True

    except Exception as e:
        messagebox.showerror("Lỗi", f"Có lỗi xảy ra khi nhập dữ liệu từ Excel:\n{str(e)}")
        return False
    finally:
        if excel:
            excel.DisplayAlerts = True
            excel.ScreenUpdating = True
            excel.AskToUpdateLinks = True
            excel.Quit()