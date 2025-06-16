import os
import pandas as pd
from tkinter import messagebox
from .state import data_df, original_df, filters, current_period, tree, frame_buttons, send_frame, label_file, entry_file, frame_table, frame_status_buttons, btn_back, month_year_var
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


selected_row_details={}

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
            print(f"Nén PDF thành công: {original_size} -> {compressed_size} bytes")
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
        else:
            # Kiểm tra thủ công cho cột "Gửi Lot DAI DIEN: 'DD' Gửi TOAN BO Lot: 'TB'"
            # Sử dụng upper() để so khớp không phân biệt chữ hoa chữ thường
            if "Gửi Lot DAI DIEN: 'DD' Gửi TOAN BO Lot: 'TB'".upper() == req_col.upper():
                for col in df_columns:
                    if "DAI DIEN".upper() in col.upper() and "TOAN BO".upper() in col.upper():
                        mapping[col] = req_col
                        break
    return mapping


def initialize_data(period):
    """Khởi tạo dữ liệu chỉ từ data_{period}.csv"""
    global data_df, original_df, filters
    filters = {}
    
    # Tạo thư mục DATASETC và subfolders
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "DATASETC")
    customer_time_dir = os.path.join(data_dir, "DATA_customer_time")
    os.makedirs(customer_time_dir, exist_ok=True)

    # Đường dẫn file trạng thái
    status_file = os.path.join(customer_time_dir, f"data_{period.lower()}.csv")
    display_columns = [
        "SS", "Mã hàng", "MSKH", "Tên khách hàng", "Đối tượng gửi dữ liệu",
        "Part Number", "Gửi Lot DAI DIEN: 'DD' Gửi TOAN BO Lot: 'TB'",
        "Nơi nhận dữ liệu", "Nội dung gửi mail", "Địa chỉ gửi mail", "DUNG LƯỢNG 1 LẦN GỬI", "Status"
    ]

    if not os.path.exists("Data Test"):
        os.makedirs("Data Test")
        print("Đã tạo thư mục Data Test")
    
    # Đảm bảo khởi tạo original_df ngay cả khi đọc file thất bại
    if original_df is None:
        original_df = pd.DataFrame(columns=display_columns)

    # Khởi tạo DataFrame rỗng mặc định
    data_df = pd.DataFrame(columns=display_columns)
    original_df = data_df.copy()

    # Chỉ cố gắng đọc từ status file nếu tồn tại
    if os.path.exists(status_file):
        encodings = ['utf-8-sig', 'utf-8', 'latin1', 'iso-8859-1', 'utf-16']
        loaded_df = None
        for encoding in encodings:
            try:
                # Thử đọc file
                temp_loaded_df = pd.read_csv(status_file, encoding=encoding)
                print(f"Đã thử đọc {status_file} với encoding {encoding}")
                
                # Kiểm tra nếu đọc thành công
                if temp_loaded_df is not None and not temp_loaded_df.columns.empty:
                    loaded_df = temp_loaded_df
                    break
                elif temp_loaded_df is not None and temp_loaded_df.empty:
                    loaded_df = temp_loaded_df
                    print(f"File {status_file} rỗng nhưng đọc thành công với encoding {encoding}")
                    break
                    
            except Exception as e:
                print(f"Lỗi với encoding {encoding} khi đọc {status_file}: {e}")
                continue

        if loaded_df is not None:
            # Đảm bảo có đủ các cột cần thiết
            for col in display_columns:
                if col not in loaded_df.columns:
                    loaded_df[col] = ""
            
            # Sắp xếp lại các cột theo đúng thứ tự
            data_df = loaded_df.reindex(columns=display_columns)
            original_df = data_df.copy()
            
            # Đảm bảo có cột Status
            if "Status" not in data_df.columns:
                data_df["Status"] = ""
                original_df["Status"] = ""
        else:
            print(f"Không thể đọc file {status_file} với bất kỳ encoding nào")
    else:
        print(f"Không tìm thấy file {status_file}")
        try:
            data_df.to_csv(status_file, index=False, encoding='utf-8-sig')
            print(f"Đã tạo file mới {status_file}")
        except Exception as e:
            print(f"Lỗi khi tạo file {status_file}: {e}")

    print(f"Khởi tạo dữ liệu thành công cho kỳ {period}")
    return data_df


def update_data(period, root):
    """Xóa data_{period}.csv, tạo lại từ data.csv, và cập nhật Treeview"""
    # Giữ nguyên logic này nếu mục đích của nút "Update dữ liệu" là làm mới file trạng thái từ data.csv
    global data_df, original_df, filters
    status_file = f"Data Test/data_{period.lower()}.csv"
    display_columns = [
        "SS", "Mã hàng", "MSKH", "Tên khách hàng", "Đối tượng gửi dữ liệu",
        "Part Number", "Gửi Lot DAI DIEN: 'DD' Gửi TOAN BO Lot: 'TB'",
        "Nơi nhận dữ liệu", "Nội dung gửi mail", "Địa chỉ gửi mail", "DUNG LƯỢNG 1 LẦN GỬI", "Status"
    ]
    data_columns = [
        "SS", "Mã hàng", "MSKH", "Tên khách hàng", "Đối tượng gửi dữ liệu",
        "Part Number", "Gửi Lot DAI DIEN: 'DD' Gửi TOAN BO Lot: 'TB'",
        "Nơi nhận dữ liệu", "Nội dung gửi mail", "Địa chỉ gửi mail", "DUNG LƯỢNG 1 LẦN GỬI"
    ]

    if not os.path.exists("Data Test"):
        os.makedirs("Data Test")
        print("Đã tạo thư mục Data Test trong update_data")


    try:
        # Xóa file data_{period}.csv nếu tồn tại
        if os.path.exists(status_file):
            try:
                os.remove(status_file)
                print(f"Đã xóa {status_file}")
            except OSError as e:
                 print(f"Lỗi khi xóa file {status_file}: {e}. Có thể file đang được sử dụng bởi process khác.")
                 messagebox.showwarning("Cảnh báo", f"Không thể xóa file {status_file}. Vui lòng đóng file nếu đang mở và thử lại.")
                 return


        # Đọc data.csv để tạo lại file trạng thái
        if not os.path.exists("data.csv"):
            messagebox.showerror("Lỗi", "Không tìm thấy file data.csv! Không thể cập nhật dữ liệu trạng thái.")
            data_df = pd.DataFrame(columns=display_columns)
            original_df = data_df.copy()
            try:
                from .gui import update_table
                update_table(data_df)
            except ImportError: pass
            return

        encodings = ['utf-8-sig', 'utf-8', 'latin1', 'iso-8859-1', 'utf-16']
        base_data = None
        for encoding in encodings:
            try:
                base_data = pd.read_csv("data.csv", encoding=encoding)
                print(f"Đã thử đọc data.csv với encoding {encoding} trong update_data")
                if base_data is not None and not base_data.empty and not base_data.columns.empty:
                    break # Đọc thành công
                elif base_data is not None and base_data.empty:
                    print(f"File data.csv rỗng với encoding {encoding} trong update_data")
                    break # File rỗng nhưng đọc không lỗi
                else:
                    print(f"Đọc data.csv với encoding {encoding} không trả về DataFrame hợp lệ trong update_data")

            except Exception as e:
                print(f"Lỗi với encoding {encoding} khi đọc data.csv trong update_data: {e}")
                base_data = None
                continue # Thử encoding tiếp theo

        if base_data is None or base_data.empty or base_data.columns.empty:
             messagebox.showerror("Lỗi", "Không thể đọc file data.csv hoặc file rỗng. Không thể cập nhật dữ liệu trạng thái.")
             data_df = pd.DataFrame(columns=display_columns)
             original_df = data_df.copy()
             try:
                 from .gui import update_table
                 update_table(data_df)
             except ImportError: pass
             return


        print(f"Các cột trong data.csv (sau đọc trong update_data): {base_data.columns.tolist()}")

        # Ánh xạ cột cho các cột bắt buộc
        required_cols = ["SS", "Mã hàng", "MSKH", "Đối tượng gửi dữ liệu","Part Number","Nơi nhận dữ liệu", "Gửi Lot DAI DIEN: 'DD' Gửi TOAN BO Lot: 'TB'"]
        col_mapping = map_columns(base_data.columns, required_cols)
        # Chỉ đổi tên cột nếu ánh xạ tìm thấy
        if col_mapping:
            base_data = base_data.rename(columns=col_mapping)
        print(f"Ánh xạ cột từ data.csv (trong update_data): {col_mapping}")


        # Kiểm tra các cột bắt buộc sau khi ánh xạ
        missing_cols_check = ["SS", "Mã hàng", "MSKH","Part Number", "Đối tượng gửi dữ liệu"]
        missing_cols = [col for col in missing_cols_check if col not in base_data.columns]

        if missing_cols:
             messagebox.showerror("Lỗi", f"File data.csv thiếu các cột bắt buộc (hoặc không ánh xạ được): {', '.join(missing_cols)}.\nCác cột hiện có: {', '.join(base_data.columns)}")
             data_df = pd.DataFrame(columns=display_columns)
             original_df = data_df.copy()
             try:
                 from .gui import update_table
                 update_table(data_df)
             except ImportError: pass
             return


        # Lọc dữ liệu theo kỳ
        if "Đối tượng gửi dữ liệu" in base_data.columns:
            initial_rows = len(base_data)
            if period == "Tháng":
                base_data = base_data[base_data["Đối tượng gửi dữ liệu"].astype(str).str.upper() == "MONTH"]
            elif period == "Tuần":
                base_data = base_data[base_data["Đối tượng gửi dữ liệu"].astype(str).str.upper() == "WEEK"]
            elif period == "Ngày":
                base_data = base_data[base_data["Đối tượng gửi dữ liệu"].astype(str).str.upper() == "DAY"]
            else:
                 pass # Không lọc nếu kỳ không xác định

            print(f"Đã lọc dữ liệu cho kỳ '{period}'. Số dòng trước lọc: {initial_rows}, sau lọc: {len(base_data)}") # Debug print

        else:
            messagebox.showwarning("Cảnh báo", "Không tìm thấy cột 'Đối tượng gửi dữ liệu' trong data.csv sau khi ánh xạ. Không thể lọc theo kỳ.")
            # Tiếp tục với toàn bộ dữ liệu từ data.csv


        if base_data.empty:
            messagebox.showinfo("Thông báo", f"Không có dữ liệu cho kỳ {period} trong data.csv sau khi lọc. Tạo file trạng thái rỗng.")
            data_df = pd.DataFrame(columns=display_columns)
            original_df = data_df.copy()
            try:
                 from .gui import update_table
                 update_table(data_df)
            except ImportError: pass
            # Tạo file trạng thái rỗng
            try:
                data_df.to_csv(status_file, index=False, encoding='utf-8-sig')
                print(f"Đã tạo file {status_file} rỗng sau khi lọc rỗng.")
            except Exception as e:
                print(f"Lỗi khi tạo file {status_file} rỗng: {e}")

            return # Không có dữ liệu để cập nhật


        # Lọc các cột theo data_columns và đảm bảo display_columns
        available_cols_in_data_columns = [col for col in data_columns if col in base_data.columns]

        if not available_cols_in_data_columns:
             messagebox.showerror("Lỗi", "Không có cột nào trong data.csv khớp với các cột yêu cầu để tạo dữ liệu trạng thái.")
             data_df = pd.DataFrame(columns=display_columns)
             original_df = data_df.copy()
             try:
                 from .gui import update_table
                 update_table(data_df)
             except ImportError: pass
             return


        data_df = base_data[available_cols_in_data_columns].copy()
        # Đảm bảo tất cả các cột trong display_columns
        for col in display_columns:
            if col not in data_df.columns:
                data_df[col] = "" # Thêm cột thiếu với giá trị rỗng

        data_df = data_df.reindex(columns=display_columns, fill_value="") # Sắp xếp lại cột
        # Đảm bảo cột Status tồn tại và rỗng khi tạo mới từ data.csv, trừ khi nó đã có trong base_data
        if "Status" not in data_df.columns:
             data_df["Status"] = ""
        else:
             # Nếu Status đã có, có thể reset nó hoặc giữ nguyên tùy logic
             data_df["Status"] = "" # Reset trạng thái khi tạo lại từ data.csv


        lot_col = "Gửi Lot DAI DIEN: 'DD' Gửi TOAN BO Lot: 'TB'"
        if lot_col in data_df.columns:
            print(f"Dữ liệu cột '{lot_col}' trong data_df trước khi lưu (trong update_data): {data_df[lot_col].dropna().unique().tolist()}")
        else:
            print(f"Cột '{lot_col}' không tồn tại trong data_df trước khi lưu (trong update_data)!")


        # Lưu vào status_file
        data_df.to_csv(status_file, index=False, encoding='utf-8-sig')
        original_df = data_df.copy()
        print(f"Đã tạo lại {status_file} từ data.csv và lưu.")

        # Cập nhật Treeview (sẽ được lên lịch trong gui.py)
        try:
            from .gui import update_table
            # update_table(data_df) # Bỏ gọi trực tiếp ở đây
            pass
        except ImportError: pass

        messagebox.showinfo("Thông báo", f"Đã cập nhật dữ liệu cho kỳ {period} từ data.csv!")
        print(f"Đã tạo lại {status_file} từ data.csv")

    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi cập nhật dữ liệu: {str(e)}")
        data_df = pd.DataFrame(columns=display_columns)
        original_df = data_df.copy()
        try:
             from .gui import update_table
             update_table(data_df) # Giữ lại update_table cuối cùng trong except block
        except ImportError: pass


def convert_txt_to_csv(txt_file,mode="MAP_ERP"):
    """Chuyển file TXT sang data_work.csv"""
    # Giữ nguyên logic này, đã hoạt động dựa trên output bạn cung cấp
    encodings = ['utf-8-sig', 'utf-16', 'latin1', 'utf-8']
    separators = ['\t', ',', ';']

    if not txt_file or not os.path.exists(txt_file):
        messagebox.showwarning("Cảnh báo", "Đường dẫn file TXT không hợp lệ!")
        return

    # Tạo đường dẫn trong DATASETC
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "DATASETC")
    os.makedirs(data_dir, exist_ok=True)
    
    output_file = os.path.join(data_dir, f"data_work_{mode}.csv")
    
    print(f"Đang cố gắng đọc file TXT: {txt_file}")

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

def gui_du_lieu(file_path, period, data_df, month_year, filter_mode="MAP_ERP"):
    global original_df, month_year_var  # Thêm global original_df ở đây

    if filter_mode == "MAP_ERP":
       
        # Kiểm tra nếu month_year là None hoặc rỗng
        if not month_year or not isinstance(month_year, str):
            month_year = datetime.datetime.now().strftime("%m/%Y")
        current_month_year = month_year_var.get() if month_year_var else datetime.datetime.now().strftime("%m/%Y")
        if not current_month_year or not isinstance(current_month_year, str):
            current_month_year = datetime.datetime.now().strftime("%m/%Y")
        try:
            selected_date = datetime.datetime.strptime(current_month_year, "%m/%Y")
            selected_year = selected_date.strftime("%Y")
            formatted_date = selected_date.strftime("%y.%m")  # Định dạng yy.mm
        except:
            selected_date = datetime.datetime.now()
            selected_year = selected_date.strftime("%Y")
            formatted_date = selected_date.strftime("%y.%m")

        
        # Validate input
        if not file_path or not os.path.exists(file_path):
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn file TXT trước!")
            return

        if data_df is None or data_df.empty:
            messagebox.showwarning("Cảnh báo", "Không có dữ liệu trong bảng để xác nhận!")
            return

        if not os.path.exists("data_work.csv"):
            messagebox.showwarning("Cảnh báo", "Không tìm thấy file data_work.csv!\nVui lòng chọn file TXT để tạo.")
            return

        try:
            config = load_config()
            data_origin_path = config.get("data_origin_path", "")
            data_temp_path = config.get("data_temp_path", "")
            
            if not data_origin_path or not data_temp_path:
                messagebox.showerror("Lỗi", "Vui lòng cấu hình đường dẫn thư mục gốc và thư mục tạm trước!")
                return

            data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "DATASETC")
            work_file = os.path.join(data_dir, f"data_work_{filter_mode}.csv")

            if not os.path.exists(work_file):
                messagebox.showwarning("Cảnh báo", f"Không tìm thấy file {work_file}!\nVui lòng chọn file để tạo.")
                return False

            work_df = pd.read_csv(work_file, encoding='utf-8-sig')
            required_work_cols = ["Sales Part No", "End Customer No", "Lot No"]
            
            # Validate columns
            if not all(col in work_df.columns for col in required_work_cols):
                missing = [col for col in required_work_cols if col not in work_df.columns]
                messagebox.showerror("Lỗi", f"File data_work.csv thiếu các cột bắt buộc: {', '.join(missing)}")
                return

            # Xác nhận dữ liệu
            temp_df = data_df.copy()
            confirmed_count = 0
            for index, row in temp_df.iterrows():
                current_status = str(row.get("Status", "")).strip()
                if current_status in ["Đã xác nhận", "Đã copy dữ liệu", "Đã gửi dữ liệu"]:
                    continue
                    
                ss = str(row.get("SS", "")).strip()
                mskh = str(row.get("MSKH", "")).strip()
                gui_dl = str(row.get("Gui_DL", "")).strip().upper()
                
                if not ss or not mskh:
                    continue

                # Kiểm tra khớp dữ liệu
                lot_data = work_df[
                    (work_df["Sales Part No"].astype(str).str.strip() == ss) &
                    (work_df["End Customer No"].astype(str).str.strip() == mskh)
                ]
                
                if not lot_data.empty:
                    temp_df["Status"] = temp_df["Status"].astype(str)
                    temp_df.loc[index, "Status"] = "Đã xác nhận"
                    confirmed_count += 1
                    continue

            if confirmed_count == 0:
                messagebox.showinfo("Thông báo", "Không có dữ liệu mới nào được xác nhận!")
                return

                # Copy file dựa trên Gui_DL
            if gui_dl == "DD":
                # Chỉ copy đại diện mỗi W/d/r No
                seen_wdr = set()
                for _, lot_row in lot_data.iterrows():
                    wdr_no = str(lot_row.get("W/d/r No", "")).strip()
                    if wdr_no in seen_wdr:
                        continue
                    seen_wdr.add(wdr_no)
                    data_df = temp_df.copy()
                    save_status(period, data_df)
                    
                    # Xử lý file PDF
                    copied_files_count = 0
                    created_folders = {}
                    noi_nhan = None  # Lưu lại nơi nhận cho phần nén
                    
                    # Tạo bản sao để làm việc
                    temp_df = data_df.copy()
                    temp_original_df = original_df.copy() if original_df is not None else pd.DataFrame()
                    
                    for index, row in data_df.iterrows():
                        if str(row.get("Status", "")).strip() != "Đã xác nhận":
                            continue
                            
                        ss = str(row.get("SS", "")).strip()
                        mskh = str(row.get("MSKH", "")).strip()
                        ma_hang = str(row.get("Mã hàng", "")).strip()
                        noi_nhan = str(row.get("Nơi nhận dữ liệu", "")).strip()  # Lấy nơi nhận
                        part_number = str(row.get("Part Number", "")).strip()
                        if part_number in ["", "NAN", "NaN", "nan", "-"]:
                            part_number = ""
                        
                        # Tạo tên thư mục SS
                        folder_name = ss
                        if part_number:
                            folder_name = f"{ss} ({part_number})"
                        
                        filtered_data = work_df[
                            (work_df["Sales Part No"].astype(str).str.strip() == ss) &
                            (work_df["End Customer No"].astype(str).str.strip() == mskh)
                        ]
                        
                        # Xử lý từng Lot
                        if filtered_data.empty:
                            continue
                        
                        lot_data = filtered_data.to_dict('records')
                        
                        # Copy file
                        files_copied_for_row = 0
                        for lot_row in lot_data:
                            lot_no = str(lot_row["Lot No"]).strip()
                            wdr_no = str(lot_row.get("W/d/r No", "")).strip() if "W/d/r No" in lot_row else ""
                            lot_folder = os.path.join(data_origin_path, selected_year, ss, lot_no)
                            
                            if not os.path.exists(lot_folder):
                                continue
                                
                            for file in os.listdir(lot_folder):
                                if not file.lower().endswith('.pdf'):
                                    continue
                                    
                                file_name = file.upper()
                                if (lot_no.upper() in file_name and 
                                    ma_hang.upper() in file_name and 
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
                                    new_filename = f"{lot_no}-{ma_hang}-{mskh}.pdf" if not wdr_no else f"{lot_no}-{ma_hang}-{mskh}-{wdr_no}.pdf"
                                    
                                    # Bước 1: Copy file gốc vào thư mục tạm
                                    src_file = os.path.join(lot_folder, file)
                                    temp_file = os.path.join(ss_folder_temp, new_filename)
                                    
                                    try:
                                        shutil.copy2(src_file, temp_file)
                                        copied_files_count += 1
                                        files_copied_for_row += 1
                                        
                                        # Bước 2: Nén file PDF trong thư mục tạm
                                        compressed_file = os.path.join(ss_folder_final, new_filename)
                                        if not compress_pdf(temp_file, compressed_file):
                                            # Nếu nén thất bại, copy file gốc
                                            shutil.copy2(temp_file, compressed_file)
                                        
                                    except Exception as e:
                                        print(f"Lỗi khi xử lý file {file}: {e}")
                        
                        if files_copied_for_row > 0:
                            # Cập nhật trên cả temp_df và temp_original_df
                            temp_df.loc[index, "Status"] = "Đã copy dữ liệu"
                            
                            # Tìm và cập nhật trên original_df
                            if not temp_original_df.empty:
                                mask = (temp_original_df["SS"] == row["SS"]) & (temp_original_df["MSKH"] == row["MSKH"])
                                temp_original_df.loc[mask, "Status"] = "Đã copy dữ liệu"
                    
                    # Cập nhật lại các dataframe global
                    data_df = temp_df.copy()
                    original_df = temp_original_df.copy()
                    
                    # Lưu trạng thái
                    save_status(period, original_df)
                    
                    # Cập nhật data_df sau filter
                    data_df = original_df.copy()
                    for col, value in filters.items():
                        data_df = data_df[data_df[col].astype(str).str.contains(value, case=False, na=False)]
                    
                    # Cập nhật Treeview ngay lập tức
                    from .gui import update_table
                    update_table(data_df)
                    if copied_files_count > 0:
                        # Tạo dictionary để lưu các thư mục cần nén theo từng nơi nhận
                        folders_to_zip = {}
                        
                        # Sau khi copy và nén xong, xóa thư mục tạm
                        for noi_nhan, folders in created_folders.items():
                            temp_folder = folders['temp']
                            if os.path.exists(temp_folder):
                                try:
                                    shutil.rmtree(temp_folder)
                                    print(f"Đã xóa thư mục tạm: {temp_folder}")
                                except Exception as e:
                                    print(f"Lỗi khi xóa thư mục tạm: {e}")
            
            elif gui_dl == "TB":
                # Copy toàn bộ file
                for _, lot_row in lot_data.iterrows():
                    # Copy toàn bộ file logic ở đây
                    for index, row in data_df.iterrows():
                        if str(row.get("Status", "")).strip() != "Đã xác nhận":
                            continue
                            
                        ss = str(row.get("SS", "")).strip()
                        mskh = str(row.get("MSKH", "")).strip()
                        ma_hang = str(row.get("Mã hàng", "")).strip()
                        noi_nhan = str(row.get("Nơi nhận dữ liệu", "")).strip()  # Lấy nơi nhận
                        part_number = str(row.get("Part Number", "")).strip()
                        if part_number in ["", "NAN", "NaN", "nan", "-"]:
                            part_number = ""
                        
                        # Tạo tên thư mục SS
                        folder_name = ss
                        if part_number:
                            folder_name = f"{ss} ({part_number})"
                        
                        filtered_data = work_df[
                            (work_df["Sales Part No"].astype(str).str.strip() == ss) &
                            (work_df["End Customer No"].astype(str).str.strip() == mskh)
                        ]
                        
                        # Xử lý từng Lot
                        if filtered_data.empty:
                            continue
                        
                        lot_data = filtered_data.to_dict('records')
                        
                        # Copy file
                        files_copied_for_row = 0
                        for lot_row in lot_data:
                            lot_no = str(lot_row["Lot No"]).strip()
                            wdr_no = str(lot_row.get("W/d/r No", "")).strip() if "W/d/r No" in lot_row else ""
                            lot_folder = os.path.join(data_origin_path, selected_year, ss, lot_no)
                            
                            if not os.path.exists(lot_folder):
                                continue
                                
                            for file in os.listdir(lot_folder):
                                if not file.lower().endswith('.pdf'):
                                    continue
                                    
                                file_name = file.upper()
                                if (lot_no.upper() in file_name and 
                                    ma_hang.upper() in file_name and 
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
                                    new_filename = f"{lot_no}-{ma_hang}-{mskh}.pdf" if not wdr_no else f"{lot_no}-{ma_hang}-{mskh}-{wdr_no}.pdf"
                                    
                                    # Bước 1: Copy file gốc vào thư mục tạm
                                    src_file = os.path.join(lot_folder, file)
                                    temp_file = os.path.join(ss_folder_temp, new_filename)
                                    
                                    try:
                                        shutil.copy2(src_file, temp_file)
                                        copied_files_count += 1
                                        files_copied_for_row += 1
                                        
                                        # Bước 2: Nén file PDF trong thư mục tạm
                                        compressed_file = os.path.join(ss_folder_final, new_filename)
                                        if not compress_pdf(temp_file, compressed_file):
                                            # Nếu nén thất bại, copy file gốc
                                            shutil.copy2(temp_file, compressed_file)
                                        
                                    except Exception as e:
                                        print(f"Lỗi khi xử lý file {file}: {e}")
                        
                        if files_copied_for_row > 0:
                            # Cập nhật trên cả temp_df và temp_original_df
                            temp_df.loc[index, "Status"] = "Đã copy dữ liệu"
                            
                            # Tìm và cập nhật trên original_df
                            if not temp_original_df.empty:
                                mask = (temp_original_df["SS"] == row["SS"]) & (temp_original_df["MSKH"] == row["MSKH"])
                                temp_original_df.loc[mask, "Status"] = "Đã copy dữ liệu"
                    
                    # Cập nhật lại các dataframe global
                    data_df = temp_df.copy()
                    original_df = temp_original_df.copy()
                    
                    # Lưu trạng thái
                    save_status(period, original_df)
                    
                    # Cập nhật data_df sau filter
                    data_df = original_df.copy()
                    for col, value in filters.items():
                        data_df = data_df[data_df[col].astype(str).str.contains(value, case=False, na=False)]
                    
                    # Cập nhật Treeview ngay lập tức
                    from .gui import update_table
                    update_table(data_df)
                    if copied_files_count > 0:
                        # Tạo dictionary để lưu các thư mục cần nén theo từng nơi nhận
                        folders_to_zip = {}
                        
                        # Sau khi copy và nén xong, xóa thư mục tạm
                        for noi_nhan, folders in created_folders.items():
                            temp_folder = folders['temp']
                            if os.path.exists(temp_folder):
                                try:
                                    shutil.rmtree(temp_folder)
                                    print(f"Đã xóa thư mục tạm: {temp_folder}")
                                except Exception as e:
                                    print(f"Lỗi khi xóa thư mục tạm: {e}")
                update_table(temp_df)
                return True
        except Exception as e:
            messagebox.showerror("Lỗi", f"Đã xảy ra lỗi khi xử lý dữ liệu: {str(e)}")
    elif filter_mode == "KJS":
        # Kiểm tra nếu month_year là None hoặc rỗng
        if not month_year or not isinstance(month_year, str):
            month_year = datetime.datetime.now().strftime("%m/%Y")
        current_month_year = month_year_var.get() if month_year_var else datetime.datetime.now().strftime("%m/%Y")
        if not current_month_year or not isinstance(current_month_year, str):
            current_month_year = datetime.datetime.now().strftime("%m/%Y")
        try:
            selected_date = datetime.datetime.strptime(current_month_year, "%m/%Y")
            selected_year = selected_date.strftime("%Y")
            formatted_date = selected_date.strftime("%y.%m")  # Định dạng yy.mm
        except:
            selected_date = datetime.datetime.now()
            selected_year = selected_date.strftime("%Y")
            formatted_date = selected_date.strftime("%y.%m")

        
        # Validate input
        if not file_path or not os.path.exists(file_path):
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn file TXT trước!")
            return

        if data_df is None or data_df.empty:
            messagebox.showwarning("Cảnh báo", "Không có dữ liệu trong bảng để xác nhận!")
            return

        if not os.path.exists("data_work.csv"):
            messagebox.showwarning("Cảnh báo", "Không tìm thấy file data_work.csv!\nVui lòng chọn file TXT để tạo.")
            return

        try:
            config = load_config()
            data_origin_path = config.get("data_origin_path", "")
            data_temp_path = config.get("data_temp_path", "")
            
            if not data_origin_path or not data_temp_path:
                messagebox.showerror("Lỗi", "Vui lòng cấu hình đường dẫn thư mục gốc và thư mục tạm trước!")
                return

            work_df = pd.read_csv("data_work.csv", encoding='utf-8-sig')
            required_work_cols = ["Sales Part No", "End Customer No", "Lot No"]
            
            # Validate columns
            if not all(col in work_df.columns for col in required_work_cols):
                missing = [col for col in required_work_cols if col not in work_df.columns]
                messagebox.showerror("Lỗi", f"File data_work.csv thiếu các cột bắt buộc: {', '.join(missing)}")
                return

            # Xác nhận dữ liệu
            temp_df = data_df.copy()
            confirmed_count = 0
            for index, row in temp_df.iterrows():
                current_status = str(row.get("Status", "")).strip()
                if current_status in ["Đã xác nhận", "Đã copy dữ liệu", "Đã gửi dữ liệu"]:
                    continue
                    
                ss = str(row.get("SS", "")).strip()
                mskh = str(row.get("MSKH", "")).strip()
                gui_dl = str(row.get("Gui_DL", "")).strip().upper()
                
                if not ss or not mskh:
                    continue

                # Kiểm tra khớp dữ liệu
                lot_data = work_df[
                    (work_df["Sales Part No"].astype(str).str.strip() == ss) &
                    (work_df["End Customer No"].astype(str).str.strip() == mskh)
                ]
                
                if not lot_data.empty:
                    temp_df["Status"] = temp_df["Status"].astype(str)
                    temp_df.loc[index, "Status"] = "Đã xác nhận"
                    confirmed_count += 1
                    continue

            if confirmed_count == 0:
                messagebox.showinfo("Thông báo", "Không có dữ liệu mới nào được xác nhận!")
                return

                # Copy file dựa trên Gui_DL
            if gui_dl == "DD":
                # Chỉ copy đại diện mỗi W/d/r No
                seen_wdr = set()
                for _, lot_row in lot_data.iterrows():
                    wdr_no = str(lot_row.get("W/d/r No", "")).strip()
                    if wdr_no in seen_wdr:
                        continue
                    seen_wdr.add(wdr_no)
                    data_df = temp_df.copy()
                    save_status(period, data_df)
                    
                    # Xử lý file PDF
                    copied_files_count = 0
                    created_folders = {}
                    noi_nhan = None  # Lưu lại nơi nhận cho phần nén
                    
                    # Tạo bản sao để làm việc
                    temp_df = data_df.copy()
                    temp_original_df = original_df.copy() if original_df is not None else pd.DataFrame()
                    
                    for index, row in data_df.iterrows():
                        if str(row.get("Status", "")).strip() != "Đã xác nhận":
                            continue
                            
                        ss = str(row.get("SS", "")).strip()
                        mskh = str(row.get("MSKH", "")).strip()
                        ma_hang = str(row.get("Mã hàng", "")).strip()
                        noi_nhan = str(row.get("Nơi nhận dữ liệu", "")).strip()  # Lấy nơi nhận
                        part_number = str(row.get("Part Number", "")).strip()
                        if part_number in ["", "NAN", "NaN", "nan", "-"]:
                            part_number = ""
                        
                        # Tạo tên thư mục SS
                        folder_name = ss
                        if part_number:
                            folder_name = f"{ss} ({part_number})"
                        
                        filtered_data = work_df[
                            (work_df["Sales Part No"].astype(str).str.strip() == ss) &
                            (work_df["End Customer No"].astype(str).str.strip() == mskh)
                        ]
                        
                        # Xử lý từng Lot
                        if filtered_data.empty:
                            continue
                        
                        lot_data = filtered_data.to_dict('records')
                        
                        # Copy file
                        files_copied_for_row = 0
                        for lot_row in lot_data:
                            lot_no = str(lot_row["Lot No"]).strip()
                            wdr_no = str(lot_row.get("W/d/r No", "")).strip() if "W/d/r No" in lot_row else ""
                            lot_folder = os.path.join(data_origin_path, selected_year, ss, lot_no)
                            
                            if not os.path.exists(lot_folder):
                                continue
                                
                            for file in os.listdir(lot_folder):
                                if not file.lower().endswith('.pdf'):
                                    continue
                                    
                                file_name = file.upper()
                                if (lot_no.upper() in file_name and 
                                    ma_hang.upper() in file_name and 
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
                                    new_filename = f"{lot_no}-{ma_hang}-{mskh}.pdf" if not wdr_no else f"{lot_no}-{ma_hang}-{mskh}-{wdr_no}.pdf"
                                    
                                    # Bước 1: Copy file gốc vào thư mục tạm
                                    src_file = os.path.join(lot_folder, file)
                                    temp_file = os.path.join(ss_folder_temp, new_filename)
                                    
                                    try:
                                        shutil.copy2(src_file, temp_file)
                                        copied_files_count += 1
                                        files_copied_for_row += 1
                                        
                                        # Bước 2: Nén file PDF trong thư mục tạm
                                        compressed_file = os.path.join(ss_folder_final, new_filename)
                                        if not compress_pdf(temp_file, compressed_file):
                                            # Nếu nén thất bại, copy file gốc
                                            shutil.copy2(temp_file, compressed_file)
                                        
                                    except Exception as e:
                                        print(f"Lỗi khi xử lý file {file}: {e}")
                        
                        if files_copied_for_row > 0:
                            # Cập nhật trên cả temp_df và temp_original_df
                            temp_df.loc[index, "Status"] = "Đã copy dữ liệu"
                            
                            # Tìm và cập nhật trên original_df
                            if not temp_original_df.empty:
                                mask = (temp_original_df["SS"] == row["SS"]) & (temp_original_df["MSKH"] == row["MSKH"])
                                temp_original_df.loc[mask, "Status"] = "Đã copy dữ liệu"
                    
                    # Cập nhật lại các dataframe global
                    data_df = temp_df.copy()
                    original_df = temp_original_df.copy()
                    
                    # Lưu trạng thái
                    save_status(period, original_df)
                    
                    # Cập nhật data_df sau filter
                    data_df = original_df.copy()
                    for col, value in filters.items():
                        data_df = data_df[data_df[col].astype(str).str.contains(value, case=False, na=False)]
                    
                    # Cập nhật Treeview ngay lập tức
                    from .gui import update_table
                    update_table(data_df)
                    if copied_files_count > 0:
                        # Tạo dictionary để lưu các thư mục cần nén theo từng nơi nhận
                        folders_to_zip = {}
                        
                        # Sau khi copy và nén xong, xóa thư mục tạm
                        for noi_nhan, folders in created_folders.items():
                            temp_folder = folders['temp']
                            if os.path.exists(temp_folder):
                                try:
                                    shutil.rmtree(temp_folder)
                                    print(f"Đã xóa thư mục tạm: {temp_folder}")
                                except Exception as e:
                                    print(f"Lỗi khi xóa thư mục tạm: {e}")
            
            elif gui_dl == "TB":
                # Copy toàn bộ file
                for _, lot_row in lot_data.iterrows():
                    # Copy toàn bộ file logic ở đây
                    for index, row in data_df.iterrows():
                        if str(row.get("Status", "")).strip() != "Đã xác nhận":
                            continue
                            
                        ss = str(row.get("SS", "")).strip()
                        mskh = str(row.get("MSKH", "")).strip()
                        ma_hang = str(row.get("Mã hàng", "")).strip()
                        noi_nhan = str(row.get("Nơi nhận dữ liệu", "")).strip()  # Lấy nơi nhận
                        part_number = str(row.get("Part Number", "")).strip()
                        if part_number in ["", "NAN", "NaN", "nan", "-"]:
                            part_number = ""
                        
                        # Tạo tên thư mục SS
                        folder_name = ss
                        if part_number:
                            folder_name = f"{ss} ({part_number})"
                        
                        filtered_data = work_df[
                            (work_df["Sales Part No"].astype(str).str.strip() == ss) &
                            (work_df["End Customer No"].astype(str).str.strip() == mskh)
                        ]
                        
                        # Xử lý từng Lot
                        if filtered_data.empty:
                            continue
                        
                        lot_data = filtered_data.to_dict('records')
                        
                        # Copy file
                        files_copied_for_row = 0
                        for lot_row in lot_data:
                            lot_no = str(lot_row["Lot No"]).strip()
                            wdr_no = str(lot_row.get("W/d/r No", "")).strip() if "W/d/r No" in lot_row else ""
                            lot_folder = os.path.join(data_origin_path, selected_year, ss, lot_no)
                            
                            if not os.path.exists(lot_folder):
                                continue
                                
                            for file in os.listdir(lot_folder):
                                if not file.lower().endswith('.pdf'):
                                    continue
                                    
                                file_name = file.upper()
                                if (lot_no.upper() in file_name and 
                                    ma_hang.upper() in file_name and 
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
                                    new_filename = f"{lot_no}-{ma_hang}-{mskh}.pdf" if not wdr_no else f"{lot_no}-{ma_hang}-{mskh}-{wdr_no}.pdf"
                                    
                                    # Bước 1: Copy file gốc vào thư mục tạm
                                    src_file = os.path.join(lot_folder, file)
                                    temp_file = os.path.join(ss_folder_temp, new_filename)
                                    
                                    try:
                                        shutil.copy2(src_file, temp_file)
                                        copied_files_count += 1
                                        files_copied_for_row += 1
                                        
                                        # Bước 2: Nén file PDF trong thư mục tạm
                                        compressed_file = os.path.join(ss_folder_final, new_filename)
                                        if not compress_pdf(temp_file, compressed_file):
                                            # Nếu nén thất bại, copy file gốc
                                            shutil.copy2(temp_file, compressed_file)
                                        
                                    except Exception as e:
                                        print(f"Lỗi khi xử lý file {file}: {e}")
                        
                        if files_copied_for_row > 0:
                            # Cập nhật trên cả temp_df và temp_original_df
                            temp_df.loc[index, "Status"] = "Đã copy dữ liệu"
                            
                            # Tìm và cập nhật trên original_df
                            if not temp_original_df.empty:
                                mask = (temp_original_df["SS"] == row["SS"]) & (temp_original_df["MSKH"] == row["MSKH"])
                                temp_original_df.loc[mask, "Status"] = "Đã copy dữ liệu"
                    
                    # Cập nhật lại các dataframe global
                    data_df = temp_df.copy()
                    original_df = temp_original_df.copy()
                    
                    # Lưu trạng thái
                    save_status(period, original_df)
                    
                    # Cập nhật data_df sau filter
                    data_df = original_df.copy()
                    for col, value in filters.items():
                        data_df = data_df[data_df[col].astype(str).str.contains(value, case=False, na=False)]
                    
                    # Cập nhật Treeview ngay lập tức
                    from .gui import update_table
                    update_table(data_df)
                    if copied_files_count > 0:
                        # Tạo dictionary để lưu các thư mục cần nén theo từng nơi nhận
                        folders_to_zip = {}
                        
                        # Sau khi copy và nén xong, xóa thư mục tạm
                        for noi_nhan, folders in created_folders.items():
                            temp_folder = folders['temp']
                            if os.path.exists(temp_folder):
                                try:
                                    shutil.rmtree(temp_folder)
                                    print(f"Đã xóa thư mục tạm: {temp_folder}")
                                except Exception as e:
                                    print(f"Lỗi khi xóa thư mục tạm: {e}")
                update_table(temp_df)
                return True
        except Exception as e:
            messagebox.showerror("Lỗi", f"Đã xảy ra lỗi khi xử lý dữ liệu: {str(e)}")
        
def nen_du_lieu(data_df, period):
    """Nén dữ liệu đã copy thành các file zip"""
    try:
        config = load_config()
        data_temp_path = config.get("data_temp_path", "")
        
        if not data_temp_path or not os.path.exists(data_temp_path):
            messagebox.showerror("Lỗi", "Không tìm thấy đường dẫn thư mục tạm!")
            return False

        # Khởi tạo biến đếm và theo dõi
        copied_files_count = 0
        created_folders = {}
        
        # Duyệt qua từng dòng dữ liệu
        for index, row in data_df.iterrows():
            if str(row.get("Status", "")).strip() != "Đã copy dữ liệu":
                continue

            ss = str(row.get("SS", "")).strip()
            mskh = str(row.get("MSKH", "")).strip()
            noi_nhan = str(row.get("Nơi nhận dữ liệu", "")).strip()
            
            # Tạo đường dẫn thư mục
            customer_folder = os.path.join(data_temp_path, f"{ss}_{mskh}")
            if not os.path.exists(customer_folder):
                continue

            # Nén thư mục PDF thành zip
            pdf_folder = os.path.join(customer_folder, "PDF")
            if os.path.exists(pdf_folder):
                # Tính tổng kích thước các file PDF
                total_size = sum(os.path.getsize(os.path.join(pdf_folder, f)) 
                               for f in os.listdir(pdf_folder) 
                               if f.lower().endswith('.pdf'))
                
                # Nén file dựa trên kích thước
                max_size_mb = float(str(row.get("DUNG LƯỢNG 1 LẦN GỬI", "10")).replace("MB", "").strip())
                
                if total_size > max_size_mb * 1024 * 1024:
                    # Chia nhỏ file zip
                    zip_folder_by_size(
                        pdf_folder,
                        os.path.join(customer_folder, f"{ss}_{mskh}_{noi_nhan}"),
                        max_size_mb
                    )
                else:
                    # Tạo một file zip duy nhất
                    zip_name = os.path.join(customer_folder, f"{ss}_{mskh}_{noi_nhan}.zip")
                    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for root_dir, _, files in os.walk(pdf_folder):
                            for file in files:
                                file_path = os.path.join(root_dir, file)
                                arcname = os.path.relpath(file_path, pdf_folder)
                                zipf.write(file_path, arcname)

            created_folders[customer_folder] = True
            copied_files_count += 1

        if copied_files_count > 0:
            messagebox.showinfo("Thành công", 
                              f"Đã nén {copied_files_count} thư mục dữ liệu thành công!")
            return True
        else:
            messagebox.showwarning("Cảnh báo", 
                                 "Không có dữ liệu nào được nén!\nVui lòng xác nhận copy dữ liệu trước.")
            return False

    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi nén dữ liệu: {str(e)}")
        return False
    
def send_all_data(period, df):
    """Gửi toàn bộ dữ liệu đã xác nhận và gửi email"""
    global original_df,data_df,month_year_var
    
    # Đảm bảo original_df đã được cập nhật
    if original_df is None:
        status_file = f"Data Test/data_{period.lower()}.csv"
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

    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "DATASETC")
    customer_time_dir = os.path.join(data_dir, "DATA_customer_time")
    os.makedirs(customer_time_dir, exist_ok=True)
    
    status_file = os.path.join(customer_time_dir, f"data_{period.lower()}.csv")
    
    try:
        df.to_csv(status_file, index=False, encoding='utf-8-sig')
        print(f"Đã lưu trạng thái vào {status_file}")
    except Exception as e:
        print(f"Lỗi khi lưu trạng thái: {e}")
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