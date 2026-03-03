import os
import pandas as pd
from tkinter import messagebox
from ult.SendEmail.Guidle import state
from .state import data_df, original_df, filters, current_period, tree, frame_buttons, send_frame, label_file, entry_file, frame_table, frame_status_buttons, btn_back, month_year_var,month_year_value
from difflib import SequenceMatcher
import math
from .config import load_config
import datetime
import shutil
import zipfile
from PyPDF2 import PdfReader, PdfWriter
from PIL import Image
import io
import win32com.client as win32
import re
import json

selected_row_details={}
ZIP_DIR = os.path.join(os.getcwd(), "DATASETC", "ZipFile")
os.makedirs(ZIP_DIR, exist_ok=True)
ZIP_LOG_JSON = os.path.join(ZIP_DIR, "zipfile.json")

def standardize_period(period):
    period_map = {"tháng": "MONTH", "tuần": "WEEK", "ngày": "DAY", "month": "MONTH", "week": "WEEK", "day": "DAY"}
    return period_map.get(str(period).strip().lower(), "MONTH")

def send_email_via_outlook(subject, body, to_email, attachment_paths):
    """Gửi email qua Outlook với các file đính kèm"""
    try:
        outlook = win32.Dispatch('Outlook.Application')
        mail = outlook.CreateItem(0)
        mail.Subject = subject
        mail.Body = body
        mail.To = to_email
        
        for attachment in attachment_paths:
            if os.path.exists(attachment):
                mail.Attachments.Add(attachment)
        
        # mail.Display(True)  # Hiển thị cửa sổ soạn email để người dùng xem trước
        mail.Send()  # Nếu muốn gửi tự động không cần xem trước thì dùng dòng này
        
        return True
    except Exception as e:
        print(f"Lỗi khi gửi email: {e}")
        return False

def get_email_components(row, month_year):
    """Tạo subject và body email từ dữ liệu row"""
    try:
        # Kiểm tra nếu month_year là None hoặc rỗng
        if not month_year or not isinstance(month_year, str):
            now = datetime.datetime.now()
            month_year = now.strftime("%m/%Y")
        
        # Xử lý month_year từ định dạng mm/yyyy
        try:
            month, year = month_year.split('/')
            month_name = datetime.datetime.strptime(month, "%m").strftime("%B")
            formatted_month_year = f"{month_name}-{year}"
        except:
            # Nếu định dạng không đúng, sử dụng tháng hiện tại
            now = datetime.datetime.now()
            month_name = now.strftime("%B")
            formatted_month_year = f"{month_name}-{now.year}"
        
        noi_nhan = str(row.get("Nơi nhận dữ liệu", "")).strip()
        ss = str(row.get("SS", "")).strip()
        ma_hang = str(row.get("Mã hàng", "")).strip()
        email_content = str(row.get("Nội dung gửi mail", "")).strip()
        
        # Tách subject và content từ email_content
        subject_match = re.search(r'Subject:\s*(.*?)\n', email_content, re.IGNORECASE)
        content_match = re.search(r'Content:\s*(.*)', email_content, re.IGNORECASE | re.DOTALL)
        
        if subject_match and content_match:
            subject_template = subject_match.group(1)
            content_template = content_match.group(1)
        else:
            # Template mặc định nếu không tìm thấy
            subject_template = "<Noi_Nhan> Motor outgoing inspection record on <Month-Year> <SS>-<Ma_Hang>"
            content_template = "I send you the outgoing data in shipment on <Month-Year>.\nPlease see attached file.\nIf you have any question, please contact to me.\nThanks and best regard."
        
        # Thay thế các placeholder
        subject = subject_template.replace("<Noi_Nhan>", noi_nhan) \
                                .replace("<Month-Year>", formatted_month_year) \
                                .replace("<SS>", ss) \
                                .replace("<Ma_Hang>", ma_hang)
                                
        body = content_template.replace("<Month-Year>", formatted_month_year)
        
        return subject, body
    except Exception as e:
        print(f"Lỗi khi tạo nội dung email: {e}")
        return None, None

def compress_pdf(input_path, output_path, quality=50):
    """Giảm dung lượng file PDF bằng cách nén hình ảnh"""
    try:
        reader = PdfReader(input_path)
        writer = PdfWriter()

        # Sao chép các trang từ file gốc
        for page in reader.pages:
            writer.add_page(page)

        # Nén hình ảnh trong PDF
        for page in writer.pages:
            if '/Resources' in page and '/XObject' in page['/Resources']:
                x_object = page['/Resources']['/XObject'].get_object()
                for obj in x_object:
                    if x_object[obj]['/Subtype'] == '/Image':
                        img_obj = x_object[obj]
                        if '/Filter' in img_obj and img_obj['/Filter'] in ['/DCTDecode', '/FlateDecode']:
                            try:
                                # Lấy dữ liệu hình ảnh
                                img_data = img_obj._data
                                img = Image.open(io.BytesIO(img_data))
                                if img.mode != 'RGB':
                                    img = img.convert('RGB')
                                
                                # Nén hình ảnh
                                output_buffer = io.BytesIO()
                                img.save(output_buffer, format='JPEG', quality=quality, optimize=True)
                                compressed_data = output_buffer.getvalue()
                                
                                # Cập nhật dữ liệu hình ảnh đã nén
                                img_obj._data = compressed_data
                                img_obj['/Filter'] = '/DCTDecode'  # Sử dụng JPEG sau khi nén
                                img_obj['/ColorSpace'] = '/DeviceRGB'
                                img_obj['/BitsPerComponent'] = 8
                                img_obj['/Width'] = img.width
                                img_obj['/Height'] = img.height
                            except Exception as e:
                                print(f"Lỗi khi nén hình ảnh trong PDF: {e}")
                                continue

        # Lưu file đã nén
        with open(output_path, "wb") as f:
            writer.write(f)

        # Kiểm tra kích thước file
        original_size = os.path.getsize(input_path)
        compressed_size = os.path.getsize(output_path)
        if compressed_size >= original_size:
            print(f"Cảnh báo: File nén ({compressed_size} bytes) không nhỏ hơn file gốc ({original_size} bytes). Sử dụng file gốc.")
            shutil.copy2(input_path, output_path)  # Ghi đè file nén bằng file gốc
            return False
        else:
            # print(f"Nén PDF thành công: {original_size} -> {compressed_size} bytes")
            return True

    except Exception as e:
        print(f"Lỗi khi nén PDF: {e}")
        shutil.copy2(input_path, output_path)  # Sao chép file gốc nếu lỗi
        return False
    
def zip_folder_by_size(folder_path, output_prefix, max_size_mb):
    try:
        file_list = []
        total_size = 0
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                total_size += file_size
                file_list.append((file_path, file_size))
        
        file_list.sort(key=lambda x: x[1], reverse=True)
        
        part_num = 1
        current_size = 0
        current_files = []
        max_size_bytes = (max_size_mb - 0.3) * 1024 * 1024
        
        for file_path, file_size in file_list:
            if current_size + file_size > max_size_bytes and current_files:
                zip_path = f"{output_prefix}_{part_num:02d}.zip"
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for f_path, _ in current_files:
                        arcname = os.path.relpath(f_path, folder_path)
                        zipf.write(f_path, arcname)
                
                part_num += 1
                current_files = []
                current_size = 0
            
            current_files.append((file_path, file_size))
            current_size += file_size
        
        if current_files:
            zip_path = f"{output_prefix}_{part_num:02d}.zip"
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for f_path, _ in current_files:
                    arcname = os.path.relpath(f_path, folder_path)
                    zipf.write(f_path, arcname)
        
        return True
    except Exception as e:
        print(f"Lỗi khi nén thư mục: {e}")
        return False

def similar(a, b):
    """Tính tỷ lệ giống nhau giữa hai chuỗi, bỏ qua khoảng trắng và chuẩn hóa chữ thường"""
    a_clean = str(a).replace(" ", "").lower() # Ensure strings and handle None/NaN
    b_clean = str(b).replace(" ", "").lower() # Ensure strings and handle None/NaN
    return SequenceMatcher(None, a_clean, b_clean).ratio()

def map_columns(df_columns, required_cols, threshold=0.85):
    """Ánh xạ cột dựa trên độ giống tên cột > 85%, ưu tiên cột quan trọng"""
    mapping = {}
    for req_col in required_cols:
        best_match = None
        best_score = 0
        for col in df_columns:
            score = similar(req_col, col)
            if score > best_score and score >= threshold:
                best_score = score
                best_match = col
        if best_match:
            mapping[best_match] = req_col
    return mapping


def initialize_data(period): # Doc du lieu data_period và đưa ra lại data_df từ data_month.csv
    """Khởi tạo dữ liệu chỉ từ data_{period}.csv"""
    global data_df, original_df, filters
    filters = {}
    
    # Tạo thư mục DATASETC và subfolders
    data_dir = os.path.join(os.getcwd(), "DATASETC")
    customer_time_dir = os.path.join(data_dir, "DATA_customer_time")
    os.makedirs(customer_time_dir, exist_ok=True)
    
    # Đường dẫn file trạng thái
    status_file = os.path.join(customer_time_dir, f"data_{period.lower()}.csv")
    
    display_columns = [
        "SS", "Mã hàng", "MSKH", "Đối tượng gửi dữ liệu","Nguồn dữ liệu","Yêu cầu đặc biệt khi gửi dữ liệu",
        "Part Number", "Gui_DL",
        "Gui_DL", "Status"
    ]

    os.makedirs(os.path.join(os.getcwd(), "DATASETC", "DATA_customer_time"), exist_ok=True)
    
    # Đảm bảo khởi tạo original_df ngay cả khi đọc file thất bại
    if original_df is None:
        original_df = pd.DataFrame(columns=display_columns)

    # Khởi tạo DataFrame rỗng mặc định
    data_df = pd.DataFrame(columns=display_columns)
    original_df = data_df.copy()

    # Đọc dữ liệu từ file trạng thái nếu có
    if os.path.exists(status_file):
        encodings = ['utf-8-sig', 'utf-8', 'latin1', 'iso-8859-1', 'utf-16']
        for encoding in encodings:
            try:
                data_df = pd.read_csv(status_file, encoding=encoding)

                # print(data_df.head())
                
                # kiêm tra nếu DataFrame không rỗng và có cột
                # print("status file là" , status_file)
                # print(data_df.head())  # In ra đầu DataFrame để kiểm tra
                
                break
            except Exception as e:
                print(f"Lỗi với encoding {encoding} khi đọc {status_file}: {e}")
                continue
        else:
            messagebox.showerror("Lỗi", f"Không thể đọc file {status_file} với bất kỳ encoding nào.")
            data_df = pd.DataFrame(columns=display_columns)
            data_df.to_csv(status_file, index=False, encoding='utf-8-sig')
    else:
        data_df = pd.DataFrame(columns=display_columns)
        data_df.to_csv(status_file, index=False, encoding='utf-8-sig')

    original_df = data_df.copy()
    return data_df


def update_data(period, root):
    """
    Xóa data_{period}.csv, tạo lại từ data.csv, và cập nhật Treeview.
    Chỉ lấy các dòng có 'Đối tượng gửi dữ liệu' đúng với kỳ tương ứng.
    """
    global data_df, original_df, filters

    period_value= standardize_period(period)

    status_file = os.path.join(os.getcwd(), "DATASETC", "DATA_customer_time", f"data_{period_value}.csv")
    display_columns = [
        "SS", "Mã hàng", "MSKH", "Đối tượng gửi dữ liệu", "Nguồn dữ liệu", "Yêu cầu đặc biệt khi gửi dữ liệu",
        "Part Number", "Gui_DL",
        "Nơi nhận dữ liệu", "DUNG LƯỢNG 1 LẦN GỬI", "Status"
    ]
    data_columns = [
        "SS", "Mã hàng", "MSKH", "Đối tượng gửi dữ liệu", "Nguồn dữ liệu", "Yêu cầu đặc biệt khi gửi dữ liệu",
        "Part Number", "Gui_DL",
        "Nơi nhận dữ liệu", "DUNG LƯỢNG 1 LẦN GỬI"
    ]

    os.makedirs(os.path.dirname(status_file), exist_ok=True)

    try:
        # Xóa file data_{period}.csv nếu tồn tại
        if os.path.exists(status_file):
            try:
                os.remove(status_file)
            except OSError as e:
                messagebox.showwarning("Cảnh báo", f"Không thể xóa file {status_file}. Vui lòng đóng file nếu đang mở và thử lại.")
                return

        # Đọc data.csv để tạo lại file data_{period}.csv
        data_csv_path = os.path.join(os.getcwd(), "DATASETC", "data.csv")
        if not os.path.exists(data_csv_path):
            messagebox.showerror("Lỗi", "Không tìm thấy file data.csv! Không thể cập nhật dữ liệu trạng thái.")
            data_df = pd.DataFrame(columns=display_columns)
            original_df = data_df.copy()
            from .gui import update_table
            update_table(data_df)
            return

        # Đọc data.csv với nhiều encoding
        encodings = ['utf-8-sig', 'utf-8', 'latin1', 'iso-8859-1', 'utf-16']
        base_data = None
        for encoding in encodings:
            try:
                base_data = pd.read_csv(data_csv_path, encoding=encoding)
                if base_data is not None and not base_data.empty and not base_data.columns.empty:
                    break
            except Exception:
                continue

        if base_data is None or base_data.empty or base_data.columns.empty:
            messagebox.showerror("Lỗi", "Không thể đọc file data.csv hoặc file rỗng. Không thể cập nhật dữ liệu trạng thái.")
            data_df = pd.DataFrame(columns=display_columns)
            original_df = data_df.copy()
            from .gui import update_table
            update_table(data_df)
            return

        # Ánh xạ cột cho các cột bắt buộc
        required_cols = [
            "SS", "Mã hàng", "MSKH", "Đối tượng gửi dữ liệu", "Nguồn dữ liệu", "Yêu cầu đặc biệt khi gửi dữ liệu",
            "Gui_DL","Nơi nhận dữ liệu", "DUNG LƯỢNG 1 LẦN GỬI"
        ]
        col_mapping = map_columns(base_data.columns, required_cols)
        if col_mapping:
            base_data = base_data.rename(columns=col_mapping)

        # Kiểm tra các cột bắt buộc
        missing_cols = [col for col in required_cols if col not in base_data.columns]
        if missing_cols:
            messagebox.showerror("Lỗi", f"File data.csv thiếu các cột bắt buộc: {', '.join(missing_cols)}")
            data_df = pd.DataFrame(columns=display_columns)
            original_df = data_df.copy()
            from .gui import update_table
            update_table(data_df)
            return

        # Lọc dữ liệu theo kỳ (chỉ lấy đúng kỳ)
        if period_value:
            before = len(base_data)
            base_data = base_data[base_data["Đối tượng gửi dữ liệu"].astype(str).str.upper() == period_value]
            print(f"Đã lọc dữ liệu cho kỳ '{period}'. Số dòng trước: {before}, sau: {len(base_data)}")

        # Nếu rỗng sau lọc, tạo file rỗng
        if base_data.empty:
            data_df = pd.DataFrame(columns=display_columns)
            data_df.to_csv(status_file, index=False, encoding='utf-8-sig')
            original_df = data_df.copy()
            from .gui import update_table
            update_table(data_df)
            messagebox.showinfo("Thông báo", f"Không có dữ liệu cho kỳ {period} trong data.csv.")
            return

        # Lọc các cột cần thiết
        data_df = base_data[[col for col in data_columns if col in base_data.columns]].copy()
        # Đảm bảo đủ các cột hiển thị
        for col in display_columns:
            if col not in data_df.columns:
                data_df[col] = ""
        data_df = data_df.reindex(columns=display_columns, fill_value="")
        data_df["Status"] = ""  # Reset trạng thái

        # Lưu vào status_file
        data_df.to_csv(status_file, index=False, encoding='utf-8-sig')
        original_df = data_df.copy()
        from .gui import update_table
        update_table(data_df)
        messagebox.showinfo("Thông báo", f"Đã cập nhật dữ liệu cho kỳ {period} từ data.csv!")

    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi cập nhật dữ liệu: {str(e)}")
        data_df = pd.DataFrame(columns=display_columns)
        original_df = data_df.copy()
        from .gui import update_table
        update_table(data_df)


def convert_txt_to_csv(txt_file,mode="MAP_ERP"):
    """Chuyển file TXT sang data_work.csv"""
    # Giữ nguyên logic này, đã hoạt động dựa trên output bạn cung cấp
    encodings = ['utf-8-sig', 'utf-16', 'latin1', 'utf-8']
    separators = ['\t', ',', ';']

    if not txt_file or not os.path.exists(txt_file):
        messagebox.showwarning("Cảnh báo", "Đường dẫn file TXT không hợp lệ!")
        return

    # Tạo đường dẫn trong DATASETC
    data_dir = os.path.join(os.getcwd(), "DATASETC","Data by classification")
    os.makedirs(data_dir, exist_ok=True)
    
    output_file = os.path.join(data_dir, f"data_work_{mode}.csv")
    
    print(f"Đang cố gắng đọc file TXT: {txt_file}")
    
    output_dir = os.path.join(os.getcwd(), "DATASETC", "Data by classification")
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"data_work_{mode}.csv"
    output_file = os.path.join(output_dir, output_filename)

    for encoding in encodings:
        for sep in separators:
            try:
                txt_data = pd.read_csv(txt_file, sep=sep, encoding=encoding, engine='python', on_bad_lines='warn')
                print(f"Đọc thành công với sep='{sep}', encoding='{encoding}'")
                print(f"Cột đọc được: {txt_data.columns.tolist()}")

                if len(txt_data.columns) > 1:
                    txt_data.to_csv(output_file, index=False, encoding='utf-8-sig')
                    messagebox.showinfo("Thông báo", f"Dữ liệu từ {txt_file} đã được chuyển sang {output_file}")
                    return True
                else:
                    print(f"Đọc thành công nhưng chỉ có 1 cột với sep='{sep}', encoding='{encoding}'. Thử tiếp.")
                    continue

            except Exception as e:
                print(f"Lỗi khi đọc với encoding {encoding} và sep '{sep}': {e}")
                continue

    messagebox.showerror("Lỗi", f"Không thể đọc file TXT: {txt_file}")
    return False

def gui_du_lieu(file_path, period,month_year, data_df):

    global original_df, month_year_var  # Thêm global original_df ở đây

    period= standardize_period(period)
    
    try:
        # Tạo thư mục DATASETC nếu chưa tồn tại
        input_dir = os.path.join(os.getcwd(), "DATASETC", "Data by classification")
        os.makedirs(input_dir, exist_ok=True)
        data_ERP_filename = f"data_work_MAP_ERP.csv"
        data_ERP = os.path.join(input_dir, data_ERP_filename)
        data_KJS_filename = f"data_work_KJS.csv"
        data_KJS = os.path.join(input_dir, data_KJS_filename)
        data_KJS_df = pd.read_csv(data_KJS, encoding='utf-8-sig', low_memory=False)
        data_ERP_df = pd.read_csv(data_ERP, encoding='utf-8-sig', low_memory=False)
        json_file = os.path.join(input_dir, f"json_data_{period}.json")
        created_folders = {}
        
        selected_year=None
        
        if os.path.exists(json_file):
            os.remove(json_file)
        
        required_cols_ERP = ["Sales Part No", "End Customer No", "Lot No"]
        if not all(col in data_ERP_df.columns for col in required_cols_ERP):
            missing = [col for col in required_cols_ERP if col not in data_ERP_df.columns]
            messagebox.showerror("Lỗi", f"File {os.path.basename(data_ERP)} thiếu các cột bắt buộc: {', '.join(missing)}")
            return
        required_cols_KJS = ["ITEM", "CUSTOMER", "LOT_NO"]
        if not all(col in data_KJS_df.columns for col in required_cols_KJS):
            missing = [col for col in required_cols_KJS if col not in data_KJS_df.columns]
            messagebox.showerror("Lỗi", f"File {os.path.basename(data_KJS)} thiếu các cột bắt buộc: {', '.join(missing)}")
            return

        data_ERP_csv =os.path.join(input_dir, f"data_ERP_{period}")
        data_KJS_csv =os.path.join(input_dir, f"data_KJS_{period}")
        
        if data_df is None or data_df.empty:
            messagebox.showwarning("Cảnh báo", "Không có dữ liệu trong bảng để xác nhận!")
        if not os.path.exists(data_ERP):
            messagebox.showwarning("Cảnh báo", f"Không tìm thấy file dữ liệu {os.path.basename(data_ERP)} !\nVui lòng kiểm tra lại logic tạo file.")
            return
        if not os.path.exists(data_KJS):
            messagebox.showwarning("Cảnh báo", f"Không tìm thấy file dữ liệu {os.path.basename(data_KJS)} !\nVui lòng kiểm tra lại logic tạo file.")
            return
    except:
        messagebox.showerror("Lỗi", "Không thể đọc dữ liệu từ file MAP_ERP hoặc KJS. Vui lòng kiểm tra lại file dữ liệu.")
        return

    # Kiểm tra nếu month_year là None hoặc rỗng
    if not month_year:
        month_year= datetime.datetime.now().strftime("%m/%Y")
    selected_date=datetime.datetime.strptime(month_year, "%m/%Y")
    selected_year = selected_date.strftime("%Y")
    formatted_date = selected_date.strftime("%y.%m")  # Định dạng yy.mm
   
    # Xuất data KJS và ERP theo tháng
    try:
        config = load_config()
        data_origin_path = config.get("data_origin_path", "")
        data_temp_path = config.get("data_temp_path", "")
        
        if not data_origin_path or not data_temp_path:
            messagebox.showerror("Lỗi", "Vui lòng cấu hình đường dẫn thư mục gốc và thư mục tạm trước!")
            return
        
        # So sánh xuất dữ liệu nhỏ riêng theo period của tháng và tuần.
        data_df["SS"] = data_df["SS"].astype(str).str.strip()
        data_df["MSKH"] = data_df["MSKH"].astype(str).str.strip()
        data_ERP_df["Sales Part No"] = data_ERP_df["Sales Part No"].astype(str).str.strip()
        data_ERP_df["End Customer No"] = data_ERP_df["End Customer No"].astype(str).str.strip()
        data_KJS_df["ITEM"] = data_KJS_df["ITEM"].astype(str).str.strip()
        data_KJS_df["CUSTOMER"] = data_KJS_df["CUSTOMER"].astype(str).str.strip()
        
        # Lọc các dòng thỏa mãn điều kiện trong data_ERP
        filtered_ERP_df = data_ERP_df[
            (data_ERP_df["Sales Part No"].isin(data_df["SS"])) &
            (data_ERP_df["End Customer No"].isin(data_df["MSKH"]))
        ]
        
        filtered_KJS_df = data_KJS_df[
            (data_KJS_df["ITEM"].isin(data_df["SS"])) &
            (data_KJS_df["CUSTOMER"].isin(data_df["MSKH"]))
        ]
        
        # # In ra các dòng dữ liệu đã lọc
        # print(data_df)
        
        # Kiểm tra nếu filtered_df rỗng
        if filtered_ERP_df.empty:
            messagebox.showinfo("Thông báo", "Không có dữ liệu nào thỏa mãn điều kiện lọc ERP!")
            return
        if filtered_KJS_df.empty:
            messagebox.showinfo("Thông báo", "Không có dữ liệu nào thỏa mãn điều kiện lọc KJS!")
            return
        
        # Xóa file data_MAP_ERP_month.csv nếu đã tồn tại
        if os.path.exists(data_ERP_csv):
            try:
                os.remove(data_ERP_csv)
                print(f"Đã xóa file: {data_ERP_csv}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa file {data_ERP_csv}: {str(e)}")
                return
        if os.path.exists(data_KJS_csv):
            try:
                os.remove(data_ERP_csv)
                print(f"Đã xóa file: {data_KJS_csv}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa file {data_KJS_csv}: {str(e)}")
                return

        
        # Xuất file CSV mới và thông báo
        filtered_ERP_df.to_csv(os.path.join(input_dir, f"data_ERP_{period}.csv"), index=False, encoding='utf-8-sig')
        # messagebox.showinfo("Thành công", f"Đã tạo file {os.path.basename(data_ERP_csv)} với {len(filtered_ERP_df)} dòng dữ liệu!")
        filtered_KJS_df.to_csv(os.path.join(input_dir, f"data_KJS_{period}.csv"), index=False, encoding='utf-8-sig')
        # messagebox.showinfo("Thành công", f"Đã tạo file {os.path.basename(data_KJS_csv)} với {len(filtered_KJS_df)} dòng dữ liệu!")
    except:
        messagebox.showerror("Lỗi", "Không đọc được file config và xuất data KJS hoặc ERP!")
    
           
    # Xác nhận dữ liệu để copy---------------------------------
    try:
        current_df= pd.read_csv(file_path, encoding='utf-8-sig', low_memory=False)
        current_df["Status"] = current_df["Status"].astype(str) # Chuyển đổi cột Status về kiểu chuỗi
        
        # Làm sạch: mỗi mã hàng chỉ giữ một nơi nhận dữ liệu (ưu tiên dòng đầu tiên)
        current_df = current_df.sort_values("Nơi nhận dữ liệu").drop_duplicates(
            subset=["SS", "Mã hàng", "MSKH"], keep="first"
        )
        json_data = {}
        for index, row in current_df.iterrows():               
            current_status = str(row.get("Status", "")).strip()
            if current_status in ["Đã xác nhận", "Đã copy dữ liệu", "Đã gửi dữ liệu","Không có dữ liệu"]:
                continue
                
            ss = str(row.get("SS", "")).strip()
            mahang=str(row.get("Mã hàng", "")).strip()
            mskh = str(row.get("MSKH", "")).strip()
            gui_dl = str(row.get("Gui_DL", "")).strip().upper()
            nguon_dl = str(row.get("Nguồn dữ liệu", "")).strip().upper()
            noi_nhan = str(row.get("Nơi nhận dữ liệu", "")).strip()  # Lấy nơi nhận
            part_number = str(row.get("Part Number", "")).strip()
            if part_number in ["", "NAN", "NaN", "nan", "-"]:
                part_number = ""
            

            if not ss or not mskh:
                continue
            if nguon_dl == "MAP":
                if gui_dl == "DD" or gui_dl == "DD (QMF-004)":
                    # Kiểm tra khớp dữ liệu với data_ERP
                    lot_data = filtered_ERP_df[
                        (filtered_ERP_df["Sales Part No"].astype(str).str.strip() == ss) &
                        (filtered_ERP_df["End Customer No"].astype(str).str.strip() == mskh)
                    ]
                    if lot_data.empty:
                        current_df.loc[index, "Status"] = "Không có dữ liệu"
                    
                    # Copy file
                    seen_wdr = set()
                    for _, lot_row in lot_data.iterrows():
                        lot_no= str(lot_row.get("Lot No", "")).strip()
                        wdr_no = str(lot_row.get("W/d/r No", "")).strip()
                        if wdr_no in seen_wdr:
                            continue
                        seen_wdr.add(wdr_no)
                        current_df.loc[index, "Status"] = "Đã xác nhận"
                        # Tạo key là tuple (SS, Mã hàng, MSKH)
                        key = f"{ss}|{mahang}|{mskh}|{noi_nhan}"
                        # Kiểm tra xem key đã tồn tại trong json_data chưa
                        if key not in json_data:
                            # Nếu key chưa có, khởi tạo một danh sách mới cho key đó
                            json_data[key] = []
                        
                        # 3. Ghi toàn bộ json_data đã cập nhật trở lại file MỘT LẦN sau khi vòng lặp kết thúc
                        with open(json_file, "w", encoding="utf-8") as f:
                            json.dump(json_data, f, ensure_ascii=False, indent=2)
                        save_status(period, current_df)
                        folder_name = ss
                        if part_number:
                            folder_name = f"{ss} ({part_number})"
                                                   
                        lot_folder = os.path.join(data_origin_path, selected_year, ss, lot_no)  
                        # print(data_origin_path)
                        if not os.path.exists(lot_folder):
                            continue
                            
                        for file in os.listdir(lot_folder):
                            if not file.lower().endswith('.pdf'):
                                continue
                                
                            file_name = file.upper()
                            if (lot_no.upper() in file_name and 
                                mahang.upper() in file_name and 
                                mskh.upper() in file_name):
                                
                                if noi_nhan not in created_folders:
                                    # Tạo thư mục tạm (_temp)
                                    base_folder_temp = os.path.join(
                                        data_temp_path,
                                        f"Gửi {noi_nhan}",
                                        selected_year,
                                        f"Gửi {formatted_date}_temp"
                                    )
                                    os.makedirs(base_folder_temp, exist_ok=True)
                                    
                                    # Tạo thư mục chính thức
                                    base_folder = os.path.join(
                                        data_temp_path,
                                        f"Gửi {noi_nhan}",
                                        selected_year,
                                        f"Gửi {formatted_date}"
                                    )
                                    os.makedirs(base_folder, exist_ok=True)
                                    
                                    created_folders[noi_nhan] = {
                                        'temp': base_folder_temp,
                                        'final': base_folder
                                    }
                                
                                # Tạo thư mục con theo SS-PartNumber trong thư mục tạm
                                ss_folder_temp = os.path.join(created_folders[noi_nhan]['temp'], folder_name)
                                os.makedirs(ss_folder_temp, exist_ok=True)

                                # Tạo thư mục con theo SS-PartNumber trong thư mục chính thức
                                ss_folder_final = os.path.join(created_folders[noi_nhan]['final'], folder_name)
                                os.makedirs(ss_folder_final, exist_ok=True)
                                
                                # Tạo tên file mới
                                new_filename = f"{lot_no}-{mahang}-{mskh}.pdf" if not wdr_no else f"{lot_no}-{mahang}-{mskh}-{wdr_no}.pdf"
                                
                                
                                # Bước 1: Copy file gốc vào thư mục tạm
                                src_file = os.path.join(lot_folder, file)
                                temp_file = os.path.join(ss_folder_temp, new_filename)

                                try:
                                    shutil.copy2(src_file, temp_file)                                   
                                    # Bước 2: Nén file PDF trong thư mục tạm
                                    compressed_file = os.path.join(ss_folder_final, new_filename)
                                    if not compress_pdf(temp_file, compressed_file):
                                        # Nếu nén thất bại, copy file gốc
                                        shutil.copy2(temp_file, compressed_file)
                                    
                                except Exception as e:
                                    print(f"Lỗi khi xử lý file {file}: {e}")
                                
                                # Chỉ append vào json_data[key] sau khi đã xác định ss_folder_final
                                json_data[key].append({
                                    "Lot No": lot_no,
                                    "W/d/r No": wdr_no,
                                    "FolderLink": ss_folder_final
                                })     
                                current_df.loc[index, "Status"] = "Đã copy dữ liệu"
                                save_status(period, current_df)
                                from .gui import update_table
                                update_table(current_df)
                                
                                for noi_nhan, folders in created_folders.items():
                                    temp_folder = folders['temp']
                                    if os.path.exists(temp_folder):
                                        try:
                                            shutil.rmtree(temp_folder)
                                            # print(f"Đã xóa thư mục tạm: {temp_folder}")
                                        except Exception as e:
                                            print(f"Lỗi khi xóa thư mục tạm: {e}")
                elif gui_dl == "TB":
                   # Kiểm tra khớp dữ liệu với data_ERP
                    lot_data = filtered_ERP_df[
                        (filtered_ERP_df["Sales Part No"].astype(str).str.strip() == ss) &
                        (filtered_ERP_df["End Customer No"].astype(str).str.strip() == mskh)
                    ]
                    if lot_data.empty:
                        current_df.loc[index, "Status"] = "Không có dữ liệu"
                    
                    # Copy file
                    seen_lot = set()
                    for _, lot_row in lot_data.iterrows():
                        lot_no= str(lot_row.get("Lot No", "")).strip()
                        wdr_no = str(lot_row.get("W/d/r No", "")).strip()
                        if lot_no in seen_lot:
                            continue
                        seen_lot.add(wdr_no)
                        current_df.loc[index, "Status"] = "Đã xác nhận"
                        # Tạo key là tuple (SS, Mã hàng, MSKH)
                        key = f"{ss}|{mahang}|{mskh}|{noi_nhan}"
                        # Kiểm tra xem key đã tồn tại trong json_data chưa
                        if key not in json_data:
                            # Nếu key chưa có, khởi tạo một danh sách mới cho key đó
                            json_data[key] = []
                        # 3. Ghi toàn bộ json_data đã cập nhật trở lại file MỘT LẦN sau khi vòng lặp kết thúc
                        with open(json_file, "w", encoding="utf-8") as f:
                            json.dump(json_data, f, ensure_ascii=False, indent=2)
                        save_status(period, current_df)
                        folder_name = ss
                        if part_number:
                            folder_name = f"{ss} ({part_number})"
                                                   
                        lot_folder = os.path.join(data_origin_path, selected_year, ss, lot_no)  
                        # print(data_origin_path)
                        if not os.path.exists(lot_folder):
                            continue
                            
                        for file in os.listdir(lot_folder):
                            if not file.lower().endswith('.pdf'):
                                continue
                                
                            file_name = file.upper()
                            if (lot_no.upper() in file_name and 
                                mahang.upper() in file_name and 
                                mskh.upper() in file_name):
                                
                                if noi_nhan not in created_folders:
                                    # Tạo thư mục tạm (_temp)
                                    base_folder_temp = os.path.join(
                                        data_temp_path,
                                        f"Gửi {noi_nhan}",
                                        selected_year,
                                        f"Gửi {formatted_date}_temp"
                                    )
                                    os.makedirs(base_folder_temp, exist_ok=True)
                                    
                                    # Tạo thư mục chính thức
                                    base_folder = os.path.join(
                                        data_temp_path,
                                        f"Gửi {noi_nhan}",
                                        selected_year,
                                        f"Gửi {formatted_date}"
                                    )
                                    os.makedirs(base_folder, exist_ok=True)
                                    
                                    created_folders[noi_nhan] = {
                                        'temp': base_folder_temp,
                                        'final': base_folder
                                    }
                                
                                # Tạo thư mục con theo SS-PartNumber trong thư mục tạm
                                ss_folder_temp = os.path.join(created_folders[noi_nhan]['temp'], folder_name)
                                os.makedirs(ss_folder_temp, exist_ok=True)

                                # Tạo thư mục con theo SS-PartNumber trong thư mục chính thức
                                ss_folder_final = os.path.join(created_folders[noi_nhan]['final'], folder_name)
                                os.makedirs(ss_folder_final, exist_ok=True)
                                
                                # Tạo tên file mới
                                new_filename = f"{lot_no}-{mahang}-{mskh}.pdf" if not wdr_no else f"{lot_no}-{mahang}-{mskh}-{wdr_no}.pdf"
                                
                               
                                
                                # Bước 1: Copy file gốc vào thư mục tạm
                                src_file = os.path.join(lot_folder, file)
                                temp_file = os.path.join(ss_folder_temp, new_filename)

                                try:
                                    shutil.copy2(src_file, temp_file)                                   
                                    # Bước 2: Nén file PDF trong thư mục tạm
                                    compressed_file = os.path.join(ss_folder_final, new_filename)
                                    if not compress_pdf(temp_file, compressed_file):
                                        # Nếu nén thất bại, copy file gốc
                                        shutil.copy2(temp_file, compressed_file)
                                    
                                except Exception as e:
                                    print(f"Lỗi khi xử lý file {file}: {e}")
                                # Chỉ append vào json_data[key] sau khi đã xác định ss_folder_final
                                json_data[key].append({
                                    "Lot No": lot_no,
                                    "W/d/r No": wdr_no,
                                    "FolderLink": ss_folder_final
                                })     
                                current_df.loc[index, "Status"] = "Đã copy dữ liệu"
                                save_status(period, current_df)
                                from .gui import update_table
                                update_table(current_df)
                                
                                for noi_nhan, folders in created_folders.items():
                                    temp_folder = folders['temp']
                                    if os.path.exists(temp_folder):
                                        try:
                                            shutil.rmtree(temp_folder)
                                            # print(f"Đã xóa thư mục tạm: {temp_folder}")
                                        except Exception as e:
                                            print(f"Lỗi khi xóa thư mục tạm: {e}")                   
                
            elif nguon_dl == "KJS":
                if gui_dl == "TB":
                    # Kiểm tra khớp dữ liệu với data_ERP
                    lot_data = filtered_KJS_df[
                        (filtered_KJS_df["ITEM"].astype(str).str.strip() == ss) &
                        (filtered_KJS_df["CUSTOMER"].astype(str).str.strip() == mskh)
                    ]
                    if lot_data.empty:
                        current_df.loc[index, "Status"] = "Không có dữ liệu"
                    
                    # Copy file
                    seen_lot = set()
                    for _, lot_row in lot_data.iterrows():
                        lot_no= str(lot_row.get("LOT_NO", "")).strip()
                        wdr_no = str(lot_row.get("PRODUCTION_ORDER_NO", "")).strip()
                        if lot_no in seen_lot:
                            continue
                        seen_lot.add(lot_no)
                        current_df.loc[index, "Status"] = "Đã xác nhận"
                        # Tạo key là tuple (SS, Mã hàng, MSKH)
                        key = f"{ss}|{mahang}|{mskh}|{noi_nhan}"
                        # Kiểm tra xem key đã tồn tại trong json_data chưa
                        if key not in json_data:
                            # Nếu key chưa có, khởi tạo một danh sách mới cho key đó
                            json_data[key] = []
                        

                        # 3. Ghi toàn bộ json_data đã cập nhật trở lại file MỘT LẦN sau khi vòng lặp kết thúc
                        with open(json_file, "w", encoding="utf-8") as f:
                            json.dump(json_data, f, ensure_ascii=False, indent=2)
                        save_status(period, current_df)
                        folder_name = ss
                        if part_number:
                            folder_name = f"{ss} ({part_number})"
                                                   
                        lot_folder = os.path.join(data_origin_path, selected_year, ss, lot_no)  
                        # print("DATA ORIGIN PATH",data_origin_path)
                        if not os.path.exists(lot_folder):
                            continue
                            
                        for file in os.listdir(lot_folder):
                            if not file.lower().endswith('.pdf'):
                                continue
                                
                            file_name = file.upper()
                            if (lot_no.upper() in file_name and 
                                mahang.upper() in file_name and 
                                mskh.upper() in file_name):
                                
                                if noi_nhan not in created_folders:
                                    # Tạo thư mục tạm (_temp)
                                    base_folder_temp = os.path.join(
                                        data_temp_path,
                                        f"Gửi {noi_nhan}",
                                        selected_year,
                                        f"Gửi {formatted_date}_temp"
                                    )
                                    os.makedirs(base_folder_temp, exist_ok=True)
                                    
                                    # Tạo thư mục chính thức
                                    base_folder = os.path.join(
                                        data_temp_path,
                                        f"Gửi {noi_nhan}",
                                        selected_year,
                                        f"Gửi {formatted_date}"
                                    )
                                    os.makedirs(base_folder, exist_ok=True)
                                    
                                    created_folders[noi_nhan] = {
                                        'temp': base_folder_temp,
                                        'final': base_folder
                                    }
                                
                                # Tạo thư mục con theo SS-PartNumber trong thư mục tạm
                                ss_folder_temp = os.path.join(created_folders[noi_nhan]['temp'], folder_name)
                                os.makedirs(ss_folder_temp, exist_ok=True)

                                # Tạo thư mục con theo SS-PartNumber trong thư mục chính thức
                                ss_folder_final = os.path.join(created_folders[noi_nhan]['final'], folder_name)
                                os.makedirs(ss_folder_final, exist_ok=True)
                                
                                # Tạo tên file mới
                                new_filename = f"{lot_no}-{mahang}-{mskh}.pdf" if not wdr_no else f"{lot_no}-{mahang}-{mskh}-{wdr_no}.pdf"
                                
                                
                                
                                # Bước 1: Copy file gốc vào thư mục tạm
                                src_file = os.path.join(lot_folder, file)
                                temp_file = os.path.join(ss_folder_temp, new_filename)

                                try:
                                    shutil.copy2(src_file, temp_file)                                   
                                    # Bước 2: Nén file PDF trong thư mục tạm
                                    compressed_file = os.path.join(ss_folder_final, new_filename)
                                    if not compress_pdf(temp_file, compressed_file):
                                        # Nếu nén thất bại, copy file gốc
                                        shutil.copy2(temp_file, compressed_file)
                                    
                                except Exception as e:
                                    print(f"Lỗi khi xử lý file {file}: {e}")
                                # Chỉ append vào json_data[key] sau khi đã xác định ss_folder_final
                                json_data[key].append({
                                    "Lot No": lot_no,
                                    "W/d/r No": wdr_no,
                                    "FolderLink": ss_folder_final
                                })     
                                current_df.loc[index, "Status"] = "Đã copy dữ liệu"
                                save_status(period, current_df)
                                from .gui import update_table
                                update_table(current_df)
                                
                                for noi_nhan, folders in created_folders.items():
                                    temp_folder = folders['temp']
                                    if os.path.exists(temp_folder):
                                        try:
                                            shutil.rmtree(temp_folder)
                                            # print(f"Đã xóa thư mục tạm: {temp_folder}")
                                        except Exception as e:
                                            print(f"Lỗi khi xóa thư mục tạm: {e}")
        messagebox.showinfo("Lỗi", "Đang thực hiện copy dữ liệu")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã bị lỗi lúc copy dữ liệu {e}")
def split_and_zip(folder_path, zip_prefix, max_mb):
    """
    Nén các file PDF trong folder_path thành nhiều file zip nhỏ hơn max_mb (MB).
    Trả về danh sách đường dẫn các file zip đã tạo.
    """
    max_bytes = int((max_mb - 1) * 1024 * 1024)  # Trừ 1MB để an toàn
    pdf_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(root, file))
    zip_files = []
    part = 1
    current_zip_files = []
    current_size = 0
    for pdf in pdf_files:
        size = os.path.getsize(pdf)
        if current_size + size > max_bytes and current_zip_files:
            zip_name = f"{zip_prefix}_{part:02d}.zip" if part > 1 else f"{zip_prefix}.zip"
            zip_path = os.path.join(ZIP_DIR, zip_name)
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                for f in current_zip_files:
                    arcname = os.path.relpath(f, folder_path)
                    zf.write(f, arcname)
            zip_files.append(zip_path)
            part += 1
            current_zip_files = []
            current_size = 0
        current_zip_files.append(pdf)
        current_size += size
    if current_zip_files:
        zip_name = f"{zip_prefix}_{part:02d}.zip" if part > 1 else f"{zip_prefix}.zip"
        zip_path = os.path.join(ZIP_DIR, zip_name)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in current_zip_files:
                arcname = os.path.relpath(f, folder_path)
                zf.write(f, arcname)
        zip_files.append(zip_path)
    return zip_files

def group_and_zip_folders(folder_paths, zip_prefix, max_mb, zip_dir):
    """
    Gộp liên tiếp các thư mục mã hàng vào file zip nhỏ hơn max_mb (MB).
    Nếu một thư mục mã hàng vượt quá max_mb thì chia nhỏ riêng thư mục đó.
    """
    import zipfile

    max_bytes = int((max_mb - 1) * 1024 * 1024)
    zip_files = []
    part = 1
    i = 0
    while i < len(folder_paths):
        folder = folder_paths[i]
        # Tính tổng dung lượng thư mục hiện tại
        folder_size = 0
        pdf_files = []
        for root, _, files in os.walk(folder):
            for file in files:
                if file.lower().endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    pdf_files.append(file_path)
                    folder_size += os.path.getsize(file_path)
        # Nếu thư mục này vượt quá max_bytes, chia nhỏ riêng nó
        if folder_size > max_bytes:
            # Chia nhỏ từng phần của thư mục này
            zip_files += split_and_zip(folder, f"{zip_prefix}_{part:02d}", max_mb)
            part += len(zip_files)
            i += 1
            continue
        # Gom nhiều thư mục nhỏ lại
        current_files = pdf_files.copy()
        current_size = folder_size
        j = i + 1
        while j < len(folder_paths):
            next_folder = folder_paths[j]
            next_size = 0
            next_files = []
            for root, _, files in os.walk(next_folder):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        file_path = os.path.join(root, file)
                        next_files.append(file_path)
                        next_size += os.path.getsize(file_path)
            if current_size + next_size > max_bytes:
                break
            current_files += next_files
            current_size += next_size
            j += 1
        # Nén các thư mục đã gom lại
        zip_name = f"{zip_prefix}_{part:02d}.zip" if part > 1 else f"{zip_prefix}.zip"
        zip_path = os.path.join(zip_dir, zip_name)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for f in current_files:
                arcname = os.path.relpath(f, os.path.commonpath(folder_paths))
                zf.write(f, arcname)
        zip_files.append(zip_path)
        part += 1
        i = j
    return zip_files
def nen_du_lieu(data_df, period):
    EMAIL_DIR = os.path.join(os.getcwd(), "DATASETC", "Email")
    EMAIL_JSON = os.path.join(EMAIL_DIR, "email.json")
    ZIP_DIR = os.path.join(os.getcwd(), "DATASETC", "ZipFile")
    os.makedirs(ZIP_DIR, exist_ok=True)
    
    # Xóa tất cả các file .zip trong thư mục ZIP_DIR trước khi tạo mới
    for file in os.listdir(ZIP_DIR):
        if file.endswith(".zip"):
            os.remove(os.path.join(ZIP_DIR, file))

    ZIP_LOG_JSON = os.path.join(ZIP_DIR, "zipfile.json")

    with open(EMAIL_JSON, "r", encoding="utf-8") as f:
        email_dict = json.load(f)

    config = load_config()
    data_temp_path = config.get("data_temp_path", "")
    if state.month_year_value ==None or state.month_year_value == "":
        state.month_year_value = datetime.datetime.now().strftime("%m/%Y")
    currentdt= datetime.datetime.strptime(state.month_year_value, "%m/%Y")
    selected_year = currentdt.strftime("%Y")
    formatted_date = currentdt.strftime("%y.%m")

    zip_log = []

    for key, info in email_dict.items():
        ten_kh = info["Tên KH"]
        category = info["CategoryEmail"]
        ma_hang_list = info["MÃ HÀNG"]
        dia_chi_email=info["Địa chỉ gửi mail"]
        max_mb = info.get("Max MB", "")
        try:
            max_mb = float(max_mb)
            if max_mb <= 0 or max_mb > 1000:
                max_mb = 8.0
        except:
            max_mb = 8.0

        customer_folder = os.path.join(data_temp_path, f"Gửi {ten_kh}", selected_year, f"Gửi {formatted_date}")
        if not os.path.exists(customer_folder):
            continue

        # Lấy danh sách thư mục con cần nén
        if ma_hang_list == ["ALL"]:
            # Lấy tất cả thư mục con
            folder_paths = [os.path.join(customer_folder, d) for d in os.listdir(customer_folder)
                            if os.path.isdir(os.path.join(customer_folder, d))]
            zip_prefix = f"{ten_kh}_{category}"
        else:
            # Lấy các thư mục con chứa mã hàng trong ma_hang_list
            folder_paths = []
            for ma in ma_hang_list:
                for d in os.listdir(customer_folder):
                    if ma in d:
                        folder_paths.append(os.path.join(customer_folder, d))
            zip_prefix = f"{ten_kh}_{category}"

        # Gom và nén các thư mục lại
        zip_files = group_and_zip_folders(folder_paths, zip_prefix, max_mb, ZIP_DIR)
        for zip_path in zip_files:
            zip_log.append({
                "Tên KH": ten_kh,
                "CategoryEmail": category,
                "MÃ HÀNG": "ALL" if ma_hang_list == ["ALL"] else ",".join(ma_hang_list),
                "zip_path": zip_path,
                "dia_chi_email":dia_chi_email,
                "noi_dung": info.get("Nội dung gửi mail", "")
            })

    with open(ZIP_LOG_JSON, "w", encoding="utf-8") as f:
        json.dump(zip_log, f, ensure_ascii=False, indent=2)
    messagebox.showinfo("Thành công", f"Đã nén và ghi log {len(zip_log)} file zip vào {ZIP_LOG_JSON}")

def send_all_data(period, df):

    # Lấy giá trị tháng/năm
    current_month_year = state.month_year_value if state.month_year_value else datetime.datetime.now().strftime("%m/%Y")
    month, year = current_month_year.split("/") if "/" in current_month_year else (datetime.datetime.now().strftime("%m"), datetime.datetime.now().strftime("%Y"))
    month_year_str = f"{month}-{year}"

    if not os.path.exists(ZIP_LOG_JSON):
        messagebox.showerror("Lỗi", "Không tìm thấy file zipfile.json!")
        return

    with open(ZIP_LOG_JSON, "r", encoding="utf-8") as f:
        zip_log = json.load(f)

    success, fail = 0, 0
    for entry in zip_log:
        to_email = entry.get("dia_chi_email", "")
        cc_email = "p.baoph.sgc@mabuchi-motor.com"
        zip_path = entry.get("zip_path", "")
        noi_dung = entry.get("noi_dung", "")

        # Tách subject và body
        subject = ""
        body = ""
        if noi_dung.lower().startswith("subject:"):
            parts = noi_dung.split("\n", 1)
            subject = parts[0][8:].strip()  # Bỏ "Subject:"
            body = parts[1].strip() if len(parts) > 1 else ""
        else:
            subject = "Gửi dữ liệu khách hàng"
            body = noi_dung

        # Thay thế <Month-Year> trong subject/body
        subject = subject.replace("<Month-Year>", month_year_str)
        body = body.replace("<Month-Year>", month_year_str)

        # Soạn email (chỉ mở cửa sổ, không gửi luôn)
        try:
            outlook = win32.Dispatch('Outlook.Application')
            mail = outlook.CreateItem(0)
            mail.Subject = subject
            mail.Body = body
            mail.To = to_email
            mail.CC = cc_email
            if os.path.exists(zip_path):
                mail.Attachments.Add(zip_path)
            mail.Display(True)  # Chỉ mở cửa sổ email, không gửi luôn
            success += 1
        except Exception as e:
            print(f"Lỗi khi soạn email cho {to_email}: {e}")
            fail += 1

    messagebox.showinfo("Kết quả", f"Đã soạn {success} email thành công\nLỗi: {fail} email")
    
def send_all_data_old(period, df):
    """Gửi toàn bộ dữ liệu đã xác nhận và gửi email"""
    global original_df,data_df,month_year_var
    print("Month year var là",month_year_var)
    # Đảm bảo original_df đã được cập nhật
    if original_df is None:
        status_file = os.path.join(os.getcwd(), "DATASETC", "DATA_customer_time", f"data_{period.lower()}.csv")
        if os.path.exists(status_file):
            original_df = pd.read_csv(status_file, encoding='utf-8-sig')
    
    # Lọc từ original_df thay vì df đang filter
    rows_to_send = original_df[original_df["Status"] == "Đã copy dữ liệu"]
    
    # Lấy giá trị tháng/năm từ biến StringVar
    current_month_year = month_year_var.get() if month_year_var else datetime.datetime.now().strftime("%m/%Y")

    if df is None or df.empty:
        messagebox.showwarning("Cảnh báo", "Không có dữ liệu để gửi!")
        return
        
    if "Status" not in df.columns:
        messagebox.showwarning("Cảnh báo", "Không tìm thấy cột 'Status' trong dữ liệu.")
        return
   
    # Lọc các dòng đã copy dữ liệu
    rows_to_send = df[df["Status"] == "Đã copy dữ liệu"]
    if rows_to_send.empty:
        messagebox.showwarning("Cảnh báo", "Không có dữ liệu nào ở trạng thái 'Đã copy dữ liệu' để gửi!")
        return

    config = load_config()
    data_temp_path = config.get("data_temp_path", "")
    if not data_temp_path:
        messagebox.showerror("Lỗi", "Không tìm thấy đường dẫn thư mục tạm trong cấu hình!")
        return

        # Kiểm tra nếu giá trị không hợp lệ thì sử dụng tháng/năm hiện tại
    if not current_month_year or not isinstance(current_month_year, str):
        current_month_year = datetime.datetime.now().strftime("%m/%Y")
    
    try:
        selected_date = datetime.datetime.strptime(current_month_year, "%m/%Y")
        selected_year = selected_date.strftime("%Y")
        formatted_date = selected_date.strftime("%y.%m")  # Định dạng yy.mm
        
        print(f"Sử dụng tháng/năm: {current_month_year}")
        print(f"Định dạng ngày: {formatted_date}")
    except Exception as e:
                print(f"[ERROR] Bị lỗi: {e}")    

    success_count = 0
    fail_count = 0
    
    # Tạo dictionary để nhóm theo nơi nhận
    recipients_dict = {}
    
    # Lọc các dòng đã copy dữ liệu từ original_df
    rows_to_send = original_df[original_df["Status"] == "Đã copy dữ liệu"]
    
    # Nhóm dữ liệu theo nơi nhận
    for index, row in rows_to_send.iterrows():
        noi_nhan = str(row.get("Nơi nhận dữ liệu", "")).strip()
        email_address = str(row.get("Địa chỉ gửi mail", "")).strip()
        
        if not noi_nhan or not email_address:

            print(f"Bỏ qua dòng {index} - thiếu thông tin nơi nhận hoặc email")
            fail_count += 1
            continue
            
        if noi_nhan not in recipients_dict:
            recipients_dict[noi_nhan] = {
                'email': email_address,
                'rows': [index],
                'subject_body': get_email_components(row, current_month_year)
            }
        else:
            recipients_dict[noi_nhan]['rows'].append(index)
    
    # Xử lý gửi email cho từng nơi nhận
    for noi_nhan, data in recipients_dict.items():
        # Tạo đường dẫn đến file zip
        base_folder = os.path.join(
            data_temp_path,
            f"Gửi {noi_nhan}",
            selected_year
        )
        
        # Tìm file zip (có thể có nhiều file nếu chia nhỏ)
        zip_files = []
        zip_prefix = f"{noi_nhan.replace(' ', '_')}_{formatted_date.replace('.', '-')}"
        
        # Kiểm tra file zip đơn
        single_zip = os.path.join(base_folder, f"{zip_prefix}.zip")
        if os.path.exists(single_zip):
            zip_files.append(single_zip)
        else:
            # Kiểm tra các file zip chia nhỏ
            i = 1
            while True:
                part_zip = os.path.join(base_folder, f"{zip_prefix}_{i:02d}.zip")
                if os.path.exists(part_zip):
                    zip_files.append(part_zip)
                    i += 1
                else:
                    break
        
        if not zip_files:
            print(f"Không tìm thấy file zip cho {noi_nhan}")
            fail_count += 1
            continue
            
        # Lấy thông tin email
        subject, body = data['subject_body']
        if not subject or not body:
            print(f"Không thể tạo nội dung email cho {noi_nhan}")
            fail_count += 1
            continue
        
        # Gửi từng email riêng cho mỗi file zip
        for zip_file in zip_files:
            if send_email_via_outlook(subject, body, data['email'], [zip_file]):
                success_count += 1
            else:
                fail_count += 1
        
        # Cập nhật status sau khi gửi tất cả file
        if success_count > 0:
            for row_index in data['rows']:
                original_df.loc[row_index, "Status"] = "Đã gửi dữ liệu"
    
    # Cập nhật lại data_df sau khi filter
    data_df = original_df.copy()
    for col, value in filters.items():
        data_df = data_df[data_df[col].astype(str).str.contains(value, case=False, na=False)]
    
    save_status(period, original_df)
    update_table(data_df)
    
    messagebox.showinfo("Kết quả", 
        f"Đã gửi {success_count} email thành công\n"
        f"Gửi thất bại {fail_count} email")


def send_selected_data(period, df):
    """Gửi các dòng dữ liệu được chọn và gửi email"""
    global original_df, tree, data_df
    
    selected_items = tree.selection()
    temp_original_df = original_df.copy()
    
    if df is None or df.empty:
        messagebox.showwarning("Cảnh báo", "Không có dữ liệu để gửi!")
        return
        
    if tree is None or not tree.winfo_exists():
        messagebox.showwarning("Cảnh báo", "Giao diện bảng chưa sẵn sàng.")
        return

    selected_items = tree.selection()
    if not selected_items:
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn các dòng để gửi!")
        return

    # Lấy thông tin tháng/năm từ GUI (cần import từ state)
    from .state import month_year_var
    current_month_year = month_year_var.get() if month_year_var else datetime.datetime.now().strftime("%m/%Y")
    
    config = load_config()
    data_temp_path = config.get("data_temp_path", "")
    if not data_temp_path:
        messagebox.showerror("Lỗi", "Không tìm thấy đường dẫn thư mục tạm trong cấu hình!")
        return

    # Lấy ngày hiện tại
    selected_date = datetime.datetime.strptime(current_month_year, "%m/%Y")
    selected_year = selected_date.strftime("%Y")
    selected_day = datetime.datetime.now().day
    formatted_date = f"{selected_date.strftime('%y.%m')}.{selected_day:02d}"

    success_count = 0
    fail_count = 0
    recipients_dict = {}  # Dictionary để nhóm theo nơi nhận
    
    for item in selected_items:
        try:
            tree_index = tree.index(item)
            if tree_index >= len(original_df):
                continue
                
            row = original_df.iloc[tree_index]
            if str(row.get("Status", "")).strip() != "Đã copy dữ liệu":
                continue
                
            noi_nhan = str(row.get("Nơi nhận dữ liệu", "")).strip()
            email_address = str(row.get("Địa chỉ gửi mail", "")).strip()
            
            if not noi_nhan or not email_address:
                print(f"Bỏ qua dòng {tree_index} - thiếu thông tin nơi nhận hoặc email")
                fail_count += 1
                continue
                
            if noi_nhan not in recipients_dict:
                recipients_dict[noi_nhan] = {
                    'email': email_address,
                    'rows': [tree_index],
                    'subject_body': get_email_components(row, current_month_year)
                }
            else:
                recipients_dict[noi_nhan]['rows'].append(tree_index)
                
        except Exception as e:
            print(f"Lỗi khi xử lý dòng được chọn: {e}")
            fail_count += 1
    
    # Xử lý gửi email cho từng nơi nhận
    for noi_nhan, data in recipients_dict.items():
        # Tạo đường dẫn đến file zip
        base_folder = os.path.join(
            data_temp_path,
            f"Gửi {noi_nhan}",
            selected_year
        )
        
        # Tìm file zip
        zip_files = []
        zip_prefix = f"{noi_nhan.replace(' ', '_')}_{formatted_date.replace('.', '-')}"
        
        single_zip = os.path.join(base_folder, f"{zip_prefix}.zip")
        if os.path.exists(single_zip):
            zip_files.append(single_zip)
        else:
            i = 1
            while True:
                part_zip = os.path.join(base_folder, f"{zip_prefix}_{i:02d}.zip")
                if os.path.exists(part_zip):
                    zip_files.append(part_zip)
                    i += 1
                else:
                    break
        
        if not zip_files:
            print(f"Không tìm thấy file zip cho {noi_nhan}")
            fail_count += 1
            continue
            
        # Gửi từng email riêng cho mỗi file zip
        subject, body = data['subject_body']
        if not subject or not body:
            print(f"Không thể tạo nội dung email cho {noi_nhan}")
            fail_count += 1
            continue
            
        for zip_file in zip_files:
            if send_email_via_outlook(subject, body, data['email'], [zip_file]):
                success_count += 1
            else:
                fail_count += 1
        
        # Cập nhật status sau khi gửi tất cả file
        if success_count > 0:
            for row_index in data['rows']:
                original_df.loc[row_index, "Status"] = "Đã gửi dữ liệu"
    
    # Cập nhật lại data_df sau khi filter
    data_df = original_df.copy()
    for col, value in filters.items():
        data_df = data_df[data_df[col].astype(str).str.contains(value, case=False, na=False)]
    
    save_status(period, original_df)
    update_table(data_df)
    
    messagebox.showinfo("Kết quả", 
        f"Đã gửi {success_count} email thành công\n"
        f"Gửi thất bại {fail_count} email")

def update_table(df):
    """Cập nhật dữ liệu vào Treeview - Phiên bản tối ưu"""
    global tree
    
    if tree is None or not tree.winfo_exists():
        return

    # Xóa và thêm lại toàn bộ dữ liệu
    tree.delete(*tree.get_children())
    
    if df is not None and not df.empty:
        for row in df.itertuples(index=False):
            tree.insert("", "end", values=tuple(str(getattr(row, col)) for col in df.columns))
    
    # Cập nhật tiêu đề cột
    for col in tree["columns"]:
        tree.heading(col, text=f"{col} (filter)" if col in filters and filters[col] else col)
    
    # Force update GUI
    tree.update_idletasks()

def save_status(period, df):
    """Lưu trạng thái vào file CSV trong DATASETC"""
    if df is None or df.empty:
        print(f"Không lưu trạng thái cho kỳ {period} vì DataFrame rỗng.")
        return

    data_dir =  os.path.join(os.getcwd(),  "DATASETC")
    customer_time_dir = os.path.join(data_dir, "DATA_customer_time")
    os.makedirs(customer_time_dir, exist_ok=True)
    
    status_file = os.path.join(customer_time_dir, f"data_{period.lower()}.csv")
    
    try:
        df.to_csv(status_file, index=False, encoding='utf-8-sig')
        # print(f"Đã lưu trạng thái vào {status_file}")
    except Exception as e:
        # print(f"Lỗi khi lưu trạng thái: {e}")
        messagebox.showerror("Lỗi", f"Không thể lưu trạng thái: {str(e)}")


def reset_status():
    """Reset trạng thái về rỗng cho toàn bộ dữ liệu (kể cả khi đang filter)"""
    global data_df, original_df, current_period, filters
    
    if original_df is None or original_df.empty:
        messagebox.showinfo("Thông báo", "Không có dữ liệu trong bảng để reset trạng thái!")
        return

    if "Status" not in original_df.columns:
        messagebox.showwarning("Cảnh báo", "Không tìm thấy cột 'Status' để reset.")
        return

    # Reset toàn bộ status trong original_df
    original_df.loc[:, "Status"] = ""
    
    # Áp dụng lại filter hiện tại
    data_df = original_df.copy()
    for col, value in filters.items():
        data_df = data_df[data_df[col].astype(str).str.contains(value, case=False, na=False)]
    
    # Lưu trạng thái
    period_to_save = current_period.get() if current_period else "Tháng"
    save_status(period_to_save, original_df)
    
    # Cập nhật GUI
    try:
        from .gui import update_table
        update_table(data_df)
    except ImportError: 
        pass
    
    messagebox.showinfo("Thông báo", "Đã reset toàn bộ trạng thái!")


def send_zip_emails():
    ZIP_LOG_JSON = os.path.join(os.getcwd(), "DATASETC", "ZipFile", "zipfile.json")
    EMAIL_JSON = os.path.join(os.getcwd(), "DATASETC", "Email", "email.json")
    if not os.path.exists(ZIP_LOG_JSON):
        messagebox.showerror("Lỗi", "Không tìm thấy file zipfile.json!")
        return
    if not os.path.exists(EMAIL_JSON):
        messagebox.showerror("Lỗi", "Không tìm thấy file email.json!")
        return

    with open(ZIP_LOG_JSON, "r", encoding="utf-8") as f:
        zip_log = json.load(f)
    with open(EMAIL_JSON, "r", encoding="utf-8") as f:
        email_dict = json.load(f)

    success, fail = 0, 0
    for entry in zip_log:
        ten_kh = entry["Tên KH"]
        category = str(entry["CategoryEmail"])
        zip_path = entry["zip_path"]
        noi_dung = entry["noi_dung"]

        # Tìm key trong email_dict để lấy địa chỉ gửi mail
        to_email = ""
        for k, info in email_dict.items():
            if info["Tên KH"] == ten_kh and str(info["CategoryEmail"]) == category:
                to_email = info.get("Địa chỉ gửi mail", "")
                break

        if not to_email:
            print(f"Không tìm thấy địa chỉ gửi mail cho {ten_kh} - {category}")
            fail += 1
            continue

        subject = f"Gửi dữ liệu {ten_kh} - {category}"
        body = noi_dung

        # Soạn email (không gửi luôn)
        try:
            outlook = win32.Dispatch('Outlook.Application')
            mail = outlook.CreateItem(0)
            mail.Subject = subject
            mail.Body = body
            mail.To = to_email
            if os.path.exists(zip_path):
                mail.Attachments.Add(zip_path)
            mail.Display(True)  # Hiển thị cửa sổ soạn email, không gửi luôn
            success += 1
        except Exception as e:
            print(f"Lỗi khi soạn email cho {ten_kh}: {e}")
            fail += 1

    messagebox.showinfo("Kết quả", f"Đã soạn {success} email thành công\nLỗi: {fail} email")