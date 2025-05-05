import os
import pandas as pd
from tkinter import messagebox
from .state import data_df, original_df, filters, tree, current_period
from difflib import SequenceMatcher
import math
from .config import load_config
import datetime
import shutil

selected_row_details={}

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

    status_file = f"Data Test/data_{period.lower()}.csv"
    display_columns = [
        "SS", "Mã hàng", "MSKH", "Tên khách hàng", "Đối tượng gửi dữ liệu",
        "Yêu cầu đặc biệt khi gửi dữ liệu", "Gửi Lot DAI DIEN: 'DD' Gửi TOAN BO Lot: 'TB'",
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
        "Yêu cầu đặc biệt khi gửi dữ liệu", "Gửi Lot DAI DIEN: 'DD' Gửi TOAN BO Lot: 'TB'",
        "Nơi nhận dữ liệu", "Nội dung gửi mail", "Địa chỉ gửi mail", "DUNG LƯỢNG 1 LẦN GỬI", "Status"
    ]
    data_columns = [
        "SS", "Mã hàng", "MSKH", "Tên khách hàng", "Đối tượng gửi dữ liệu",
        "Yêu cầu đặc biệt khi gửi dữ liệu", "Gửi Lot DAI DIEN: 'DD' Gửi TOAN BO Lot: 'TB'",
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
        required_cols = ["SS", "Mã hàng", "MSKH", "Đối tượng gửi dữ liệu","Nơi nhận dữ liệu", "Gửi Lot DAI DIEN: 'DD' Gửi TOAN BO Lot: 'TB'"]
        col_mapping = map_columns(base_data.columns, required_cols)
        # Chỉ đổi tên cột nếu ánh xạ tìm thấy
        if col_mapping:
            base_data = base_data.rename(columns=col_mapping)
        print(f"Ánh xạ cột từ data.csv (trong update_data): {col_mapping}")


        # Kiểm tra các cột bắt buộc sau khi ánh xạ
        missing_cols_check = ["SS", "Mã hàng", "MSKH", "Đối tượng gửi dữ liệu"]
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


def convert_txt_to_csv(txt_file):
    """Chuyển file TXT sang data_work.csv"""
    # Giữ nguyên logic này, đã hoạt động dựa trên output bạn cung cấp
    encodings = ['utf-8-sig', 'utf-16', 'latin1', 'utf-8']
    separators = ['\t', ',', ';']

    if not txt_file or not os.path.exists(txt_file):
        messagebox.showwarning("Cảnh báo", "Đường dẫn file TXT không hợp lệ!")
        return

    print(f"Đang cố gắng đọc file TXT: {txt_file}")

    for encoding in encodings:
        for sep in separators:
            try:
                txt_data = pd.read_csv(txt_file, sep=sep, encoding=encoding, engine='python', on_bad_lines='warn')
                print(f"Đọc thành công với sep='{sep}', encoding='{encoding}'")
                print(f"Cột đọc được: {txt_data.columns.tolist()}")

                if len(txt_data.columns) > 1: # Chỉ cần nhiều hơn 1 cột là dấu hiệu tốt
                     txt_data.to_csv("data_work.csv", index=False, encoding='utf-8-sig')
                     messagebox.showinfo("Thông báo", f"Dữ liệu từ {txt_file} đã được chuyển sang data_work.csv (sep: '{sep}', encoding: {encoding})")
                     print(f"Các cột trong data_work.csv: {txt_data.columns.tolist()}")
                     return # Chuyển đổi thành công

                else:
                    print(f"Đọc thành công nhưng chỉ có 1 cột với sep='{sep}', encoding='{encoding}'. Thử tiếp.")
                    continue


            except Exception as e:
                print(f"Lỗi khi đọc với encoding {encoding} và sep '{sep}': {e}")
                continue

    messagebox.showerror("Lỗi", f"Không thể đọc file TXT: {txt_file}\nDữ liệu không được tách thành cột với các tùy chọn thử. Vui lòng kiểm tra định dạng file hoặc encoding.")


def gui_du_lieu(file_txt, period, df):
    """Xác nhận dữ liệu từ data_work.csv, copy file PDF và cập nhật status"""
    global data_df, selected_row_details
    
    if not file_txt or not os.path.exists(file_txt):
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn file TXT trước!")
        return

    if df is None or df.empty:
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
        
        if not all(col in work_df.columns for col in required_work_cols):
            missing = [col for col in required_work_cols if col not in work_df.columns]
            messagebox.showerror("Lỗi", f"File data_work.csv thiếu các cột bắt buộc: {', '.join(missing)}")
            return

        updated = False
        temp_df = df.copy()
        selected_year = datetime.datetime.now().strftime("%Y")
        
        # Bước 1: Xác nhận dữ liệu trước
        temp_df = df.copy()
        confirmed_count = 0
        for index, row in temp_df.iterrows():
            current_status = str(row.get("Status", "")).strip()
            if current_status in ["Đã xác nhận", "Đã copy dữ liệu", "Đã gửi dữ liệu"]:
                continue
                
            ss = str(row.get("SS", "")).strip()
            mskh = str(row.get("MSKH", "")).strip()
            
            if not ss or not mskh:
                continue

            # Kiểm tra khớp dữ liệu với data_work.csv
            matched_data = work_df[
                (work_df["Sales Part No"].astype(str).str.strip() == ss) &
                (work_df["End Customer No"].astype(str).str.strip() == mskh)
            ]
            
            if not matched_data.empty:
                temp_df.loc[index, "Status"] = "Đã xác nhận"
                confirmed_count += 1

        if confirmed_count == 0:
            messagebox.showinfo("Thông báo", "Không có dữ liệu mới nào được xác nhận!")
            return
            
        data_df = temp_df.copy()
        save_status(period, data_df)
        
        # Bước 2: Xử lý copy file PDF
        copied_files_count = 0
        # Dictionary để lưu các thư mục đã tạo theo từng nơi nhận
        created_folders = {}
        
        for index, row in data_df.iterrows():
            if str(row.get("Status", "")).strip() != "Đã xác nhận":
                continue
                
            ss = str(row.get("SS", "")).strip()
            mskh = str(row.get("MSKH", "")).strip()
            ma_hang = str(row.get("Mã hàng", "")).strip()
            noi_nhan = str(row.get("Nơi nhận dữ liệu", "")).strip()
            gui_lot = str(row.get("Gửi Lot DAI DIEN: 'DD' Gửi TOAN BO Lot: 'TB'", "")).strip().upper()

            # Lấy danh sách LotNo và W/d/r No
            filtered_data = work_df[
                (work_df["Sales Part No"].astype(str).str.strip() == ss) &
                (work_df["End Customer No"].astype(str).str.strip() == mskh)
            ]
            
            if gui_lot == "DD":
                lot_data = [filtered_data.iloc[0]]
            elif gui_lot == "TB":
                lot_data = filtered_data.to_dict('records')
            else:
                continue
            
            # Xử lý từng LotNo
            files_copied_for_row = 0
            for lot_row in lot_data:
                lot_no = str(lot_row["Lot No"]).strip()
                wdr_no = str(lot_row.get("W/d/r No", "")).strip() if "W/d/r No" in lot_row else ""
                lot_folder = os.path.join(data_origin_path, selected_year, ss, lot_no)
                
                if not os.path.exists(lot_folder):
                    continue
                    
                # Tìm file PDF phù hợp
                for file in os.listdir(lot_folder):
                    if not file.lower().endswith('.pdf'):
                        continue
                        
                    file_name = file.upper()
                    if (lot_no.upper() in file_name and 
                        ma_hang.upper() in file_name and 
                        mskh.upper() in file_name):
                        
                        # Tạo thư mục đích với cấu trúc mới
                        if noi_nhan not in created_folders:
                            base_folder = os.path.join(
                                data_temp_path,
                                f"Gửi {noi_nhan}",
                                selected_year,
                                f"Gửi {datetime.datetime.now().strftime('%y.%m.%d')}"
                            )
                            os.makedirs(base_folder, exist_ok=True)
                            created_folders[noi_nhan] = base_folder
                            
                        # Tạo thư mục con theo SS
                        ss_folder = os.path.join(created_folders[noi_nhan], ss)
                        os.makedirs(ss_folder, exist_ok=True)
                        
                        # Đổi tên file theo yêu cầu
                        new_filename = f"{lot_no}-{ma_hang}-{mskh}-{wdr_no}.pdf" if wdr_no else f"{lot_no}-{ma_hang}-{mskh}.pdf"
                        src_file = os.path.join(lot_folder, file)
                        dest_file = os.path.join(ss_folder, new_filename)
                        
                        try:
                            shutil.copy2(src_file, dest_file)
                            copied_files_count += 1
                            files_copied_for_row += 1
                        except Exception as e:
                            print(f"Lỗi khi copy file {file}: {e}")
            
            if files_copied_for_row > 0:
                data_df.loc[index, "Status"] = "Đã copy dữ liệu"
        
        # Cập nhật trạng thái cuối cùng
        save_status(period, data_df)
        from .gui import update_table
        update_table(data_df)
        
        if copied_files_count > 0:
            messagebox.showinfo("Thành công", 
                f"Đã xác nhận {confirmed_count} dòng dữ liệu\n"
                f"Đã copy {copied_files_count} file PDF vào thư mục đích")
        else:
            messagebox.showinfo("Thông báo", 
                "Đã xác nhận dữ liệu nhưng không tìm thấy file PDF phù hợp để copy!")

    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi khi xử lý dữ liệu: {str(e)}")

def send_all_data(period, df):
    """Gửi toàn bộ dữ liệu đã xác nhận"""
    global data_df
    if df is None or df.empty:
        messagebox.showwarning("Cảnh báo", "Không có dữ liệu để gửi!")
        return
    if "Status" in df.columns:
        # Chỉ cập nhật trạng thái của các dòng "Đã xác nhận"
        df.loc[df["Status"] == "Đã xác nhận", "Status"] = "Đã gửi dữ liệu"
        data_df = df.copy()
        save_status(period, data_df)
        try:
            from .gui import update_table
            update_table(data_df)
        except ImportError: pass
        messagebox.showinfo("Thông báo", "Đã gửi toàn bộ dữ liệu đã xác nhận!")
    else:
         messagebox.showwarning("Cảnh báo", "Không tìm thấy cột 'Status' trong dữ liệu.")


def send_selected_data(period, df):
    """Gửi các dòng dữ liệu được chọn"""
    global data_df, tree
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

    updated = False
    temp_df = df.copy()

    if "Status" not in temp_df.columns:
         messagebox.showwarning("Cảnh báo", "Không tìm thấy cột 'Status' trong dữ liệu.")
         return

    # Tạo một mapping từ item id của Treeview sang index của DataFrame
    # Đây là cách an toàn hơn so với dựa vào vị trí hiển thị
    # Cần đảm bảo khi populate Treeview, ta lưu trữ index DataFrame vào item
    # Hiện tại code gốc không làm điều này. Tạm thời giữ nguyên logic dựa vào index vị trí,
    # nhưng cần lưu ý đây có thể là nguồn lỗi nếu có lọc/sắp xếp.
    # Một cách tốt hơn là lấy giá trị SS/MSKH từ item và tìm trong DataFrame gốc (original_df)
    # để lấy index chính xác.

    # Dựa trên cách update_table hiện tại, index vị trí có thể tạm dùng nếu không có sắp xếp/lọc phức tạp.
    df_indices_to_update = []
    for item in selected_items:
        try:
            # Lấy index vị trí trong Treeview
            tree_index = tree.index(item)
            # Nếu DataFrame chưa bị lọc/sắp xếp, index này có thể tương ứng index DataFrame
            if tree_index < len(temp_df):
                 # Kiểm tra trạng thái trước khi thêm vào danh sách cập nhật
                 if temp_df.iloc[tree_index].get("Status", "") == "Đã xác nhận":
                      df_indices_to_update.append(tree_index)
                 # else:
                      # print(f"Send Selected: Row at tree index {tree_index} not 'Đã xác nhận'. Status: {temp_df.iloc[tree_index].get('Status', '')}") # Debug print

        except Exception as e:
            print(f"Lỗi khi xử lý item được chọn {item}: {e}")
            continue

    # Chỉ cập nhật trạng thái cho các index đã xác định và có trạng thái "Đã xác nhận"
    if df_indices_to_update:
         for index in df_indices_to_update:
              temp_df.loc[index, "Status"] = "Đã gửi dữ liệu"
         updated = True


    if updated:
        data_df = temp_df.copy()
        save_status(period, data_df)
        try:
            from .gui import update_table
            update_table(data_df)
        except ImportError: pass
        messagebox.showinfo("Thông báo", "Đã gửi các dòng dữ liệu đang chọn!")
    else:
        messagebox.showinfo("Thông báo", "Không có dòng nào được chọn hoặc các dòng được chọn chưa ở trạng thái 'Đã xác nhận'.")


def save_status(period, df):
    """Lưu trạng thái vào file CSV"""
    if df is None or df.empty:
         print(f"Không lưu trạng thái cho kỳ {period} vì DataFrame rỗng.")
         # Có thể xóa file trạng thái nếu DataFrame rỗng, tùy logic
         # if os.path.exists(f"Data Test/data_{period.lower()}.csv"):
         #      try: os.remove(f"Data Test/data_{period.lower()}.csv")
         #      except Exception as e: print(f"Lỗi xóa file trạng thái rỗng: {e}")
         return

    status_file = f"Data Test/data_{period.lower()}.csv"
    try:
        if not os.path.exists("Data Test"):
             os.makedirs("Data Test")
        df.to_csv(status_file, index=False, encoding='utf-8-sig')
        print(f"Đã lưu trạng thái vào {status_file}")
    except Exception as e:
        print(f"Lỗi khi lưu trạng thái vào {status_file}: {e}")
        messagebox.showerror("Lỗi", f"Không thể lưu trạng thái vào file {status_file}:\n{str(e)}")


def reset_status():
    """Reset trạng thái về rỗng cho dữ liệu đang hiển thị"""
    global data_df, current_period
    if data_df is not None and not data_df.empty:
        if "Status" in data_df.columns:
            # Sử dụng .copy() để tránh SettingWithCopyWarning
            temp_df = data_df.copy()
            temp_df["Status"] = ""
            data_df = temp_df.copy() # Cập nhật biến global

            period_to_save = current_period.get() if current_period and current_period.get() else "Tháng"
            save_status(period_to_save, data_df)
            try:
                from .gui import update_table
                update_table(data_df)
            except ImportError: pass
            messagebox.showinfo("Thông báo", "Đã reset toàn bộ trạng thái!")
        else:
             messagebox.showwarning("Cảnh báo", "Không tìm thấy cột 'Status' để reset.")

    else:
        messagebox.showinfo("Thông báo", "Không có dữ liệu trong bảng để reset trạng thái!")