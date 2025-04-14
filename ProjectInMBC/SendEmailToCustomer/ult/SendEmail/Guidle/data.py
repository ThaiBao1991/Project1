import os
import pandas as pd
from tkinter import messagebox
from .state import data_df, original_df, filters, tree, current_period
from difflib import SequenceMatcher

def similar(a, b):
    """Tính tỷ lệ giống nhau giữa hai chuỗi"""
    return SequenceMatcher(None, a, b).ratio()

def map_columns(df_columns, required_cols, threshold=0.9):
    """Ánh xạ cột dựa trên độ giống tên cột > 90%"""
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

def initialize_data(period):
    """Khởi tạo dữ liệu từ data_thang.csv (không xóa), rơi về data.csv nếu cần"""
    global data_df, original_df, filters
    filters = {}
    
    status_file = f"Data Test/data_{period.lower()}.csv"
    display_columns = [
        "SS", "Mã hàng", "MSKH", "Tên khách hàng", "Đối tượng gửi dữ liệu",
        "Yêu cầu đặc biệt khi gửi dữ liệu", "Gửi Lot DAI DIEN: 'DD' Gửi TOAN BO Lot: 'TB'",
        "Nơi nhận dữ liệu", "Nội dung gửi mail", "Địa chỉ gửi mail", "DUNG LƯỢNG 1 LẦN GỬI", "Status"
    ]
    column_mapping = {
        "Gửi Lot": "Gửi Lot DAI DIEN: 'DD' Gửi TOAN BO Lot: 'TB'"
    }
    data_columns = [
        "SS", "Mã hàng", "MSKH", "Tên khách hàng", "Đối tượng gửi dữ liệu",
        "Yêu cầu đặc biệt khi gửi dữ liệu", "Gửi Lot",
        "Nơi nhận dữ liệu", "Nội dung gửi mail", "Địa chỉ gửi mail", "DUNG LƯỢNG 1 LẦN GỬI"
    ]
    
    try:
        if not os.path.exists("Data Test"):
            os.makedirs("Data Test")
        
        # Đọc từ status_file (data_thang.csv) mà không xóa
        if os.path.exists(status_file):
            try:
                data_df = pd.read_csv(status_file, encoding='utf-8-sig')
                if data_df.empty:
                    messagebox.showinfo("Thông báo", f"File {status_file} trống!")
                    print(f"File {status_file} trống, thử đọc từ data.csv")
                else:
                    # Đảm bảo các cột cần thiết
                    for col in display_columns:
                        if col not in data_df.columns:
                            data_df[col] = ""
                    data_df = data_df.reindex(columns=display_columns, fill_value="")
                    original_df = data_df.copy()
                    from .gui import update_table
                    update_table(data_df)
                    print(f"Đã đọc dữ liệu từ {status_file} khi khởi động")
                    return
            except Exception as e:
                messagebox.showwarning("Cảnh báo", f"Không đọc được {status_file}: {str(e)}. Đang thử đọc từ data.csv...")
                print(f"Lỗi khi đọc {status_file}: {e}")
        
        # Đọc từ data.csv nếu data_thang.csv không khả dụng
        if not os.path.exists("data.csv"):
            messagebox.showerror("Lỗi", "Không tìm thấy file data.csv! Vui lòng tạo file qua File > Data.")
            data_df = pd.DataFrame(columns=display_columns)
            original_df = data_df.copy()
            from .gui import update_table
            update_table(data_df)
            return

        encodings = ['utf-8-sig', 'utf-8', 'latin1', 'iso-8859-1', 'utf-16']
        base_data = None
        for encoding in encodings:
            try:
                base_data = pd.read_csv("data.csv", encoding=encoding)
                break
            except Exception as e:
                print(f"Lỗi với encoding {encoding} khi đọc data.csv: {e}")
                continue
        if base_data is None:
            messagebox.showerror("Lỗi", "Không thể đọc file data.csv với bất kỳ encoding nào.")
            data_df = pd.DataFrame(columns=display_columns)
            original_df = data_df.copy()
            from .gui import update_table
            update_table(data_df)
            return

        # Ánh xạ cột tương tự
        required_cols = ["SS", "Mã hàng", "MSKH", "Đối tượng gửi dữ liệu"]
        col_mapping = map_columns(base_data.columns, required_cols)
        if col_mapping:
            base_data = base_data.rename(columns=col_mapping)
            print(f"Ánh xạ cột: {col_mapping}")

        # Kiểm tra các cột bắt buộc
        missing_cols = [col for col in ["SS", "Mã hàng", "MSKH", "Đối tượng gửi dữ liệu"] if col not in base_data.columns]
        if missing_cols:
            messagebox.showerror("Lỗi", f"File data.csv thiếu các cột bắt buộc (hoặc không ánh xạ được): {', '.join(missing_cols)}.\nCác cột hiện có: {', '.join(base_data.columns)}")
            data_df = pd.DataFrame(columns=display_columns)
            original_df = data_df.copy()
            from .gui import update_table
            update_table(data_df)
            return

        # Lọc dữ liệu theo kỳ
        if period == "Tháng":
            base_data = base_data[base_data["Đối tượng gửi dữ liệu"].str.upper() == "MONTH"]
        elif period == "Tuần":
            base_data = base_data[base_data["Đối tượng gửi dữ liệu"].str.upper() == "WEEK"]
        elif period == "Ngày":
            base_data = base_data[base_data["Đối tượng gửi dữ liệu"].str.upper() == "DAY"]

        if base_data.empty:
            messagebox.showinfo("Thông báo", f"Không có dữ liệu cho kỳ {period} trong data.csv! Vui lòng thêm dữ liệu qua File > Data.")
            data_df = pd.DataFrame(columns=display_columns)
            original_df = data_df.copy()
            from .gui import update_table
            update_table(data_df)
            return
        
        available_cols = [col for col in data_columns if col in base_data.columns]
        base_data = base_data[available_cols]

        # Khởi tạo data_df
        data_df = base_data.copy()
        for col in data_columns:
            if col not in data_df.columns:
                data_df[col] = ""
        data_df["Status"] = ""
        data_df = data_df.rename(columns=column_mapping)
        data_df = data_df.reindex(columns=display_columns, fill_value="")

        # Không lưu vào data_thang.csv khi khởi động
        original_df = data_df.copy()
        from .gui import update_table
        update_table(data_df)
        print(f"Đã đọc dữ liệu từ data.csv khi khởi động")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi tải dữ liệu: {str(e)}")
        data_df = pd.DataFrame(columns=display_columns)
        original_df = data_df.copy()
        from .gui import update_table
        update_table(data_df)

def update_data(period, root):
    """Xóa data_{period}.csv, tạo lại từ data.csv, và cập nhật Treeview"""
    global data_df, original_df, filters
    status_file = f"Data Test/data_{period.lower()}.csv"
    display_columns = [
        "SS", "Mã hàng", "MSKH", "Tên khách hàng", "Đối tượng gửi dữ liệu",
        "Yêu cầu đặc biệt khi gửi dữ liệu", "Gửi Lot DAI DIEN: 'DD' Gửi TOAN BO Lot: 'TB'",
        "Nơi nhận dữ liệu", "Nội dung gửi mail", "Địa chỉ gửi mail", "DUNG LƯỢNG 1 LẦN GỬI", "Status"
    ]
    column_mapping = {
        "Gửi Lot": "Gửi Lot DAI DIEN: 'DD' Gửi TOAN BO Lot: 'TB'"
    }
    data_columns = [
        "SS", "Mã hàng", "MSKH", "Tên khách hàng", "Đối tượng gửi dữ liệu",
        "Yêu cầu đặc biệt khi gửi dữ liệu", "Gửi Lot",
        "Nơi nhận dữ liệu", "Nội dung gửi mail", "Địa chỉ gửi mail", "DUNG LƯỢNG 1 LẦN GỬI"
    ]
    
    try:
        # Xóa file data_{period}.csv nếu tồn tại
        if os.path.exists(status_file):
            os.remove(status_file)
            print(f"Đã xóa {status_file}")

        # Đọc data.csv
        if not os.path.exists("data.csv"):
            messagebox.showerror("Lỗi", "Không tìm thấy file data.csv! Vui lòng tạo file qua File > Data.")
            data_df = pd.DataFrame(columns=display_columns)
            original_df = data_df.copy()
            from .gui import update_table
            update_table(data_df)
            return

        encodings = ['utf-8-sig', 'utf-8', 'latin1', 'iso-8859-1', 'utf-16']
        base_data = None
        for encoding in encodings:
            try:
                base_data = pd.read_csv("data.csv", encoding=encoding)
                break
            except Exception as e:
                print(f"Lỗi với encoding {encoding} khi đọc data.csv: {e}")
                continue
        if base_data is None:
            messagebox.showerror("Lỗi", "Không thể đọc file data.csv với bất kỳ encoding nào.")
            data_df = pd.DataFrame(columns=display_columns)
            original_df = data_df.copy()
            from .gui import update_table
            update_table(data_df)
            return

        # Ánh xạ cột tương tự
        required_cols = ["SS", "Mã hàng", "MSKH", "Đối tượng gửi dữ liệu"]
        col_mapping = map_columns(base_data.columns, required_cols)
        if col_mapping:
            base_data = base_data.rename(columns=col_mapping)
            print(f"Ánh xạ cột: {col_mapping}")

        # Kiểm tra các cột bắt buộc
        missing_cols = [col for col in ["SS", "Mã hàng", "MSKH", "Đối tượng gửi dữ liệu"] if col not in base_data.columns]
        if missing_cols:
            messagebox.showerror("Lỗi", f"File data.csv thiếu các cột bắt buộc (hoặc không ánh xạ được): {', '.join(missing_cols)}.\nCác cột hiện có: {', '.join(base_data.columns)}")
            data_df = pd.DataFrame(columns=display_columns)
            original_df = data_df.copy()
            from .gui import update_table
            update_table(data_df)
            return

        # Lọc dữ liệu theo kỳ
        if period == "Tháng":
            base_data = base_data[base_data["Đối tượng gửi dữ liệu"].str.upper() == "MONTH"]
        elif period == "Tuần":
            base_data = base_data[base_data["Đối tượng gửi dữ liệu"].str.upper() == "WEEK"]
        elif period == "Ngày":
            base_data = base_data[base_data["Đối tượng gửi dữ liệu"].str.upper() == "DAY"]

        if base_data.empty:
            messagebox.showinfo("Thông báo", f"Không có dữ liệu cho kỳ {period} trong data.csv! Vui lòng thêm dữ liệu qua File > Data.")
            data_df = pd.DataFrame(columns=display_columns)
            original_df = data_df.copy()
            from .gui import update_table
            update_table(data_df)
            return
        
        available_cols = [col for col in data_columns if col in base_data.columns]
        base_data = base_data[available_cols]

        # Khởi tạo data_df
        data_df = base_data.copy()
        for col in data_columns:
            if col not in data_df.columns:
                data_df[col] = ""
        data_df["Status"] = ""
        data_df = data_df.rename(columns=column_mapping)
        data_df = data_df.reindex(columns=display_columns, fill_value="")

        # Lưu vào status_file
        save_status(period, data_df)
        original_df = data_df.copy()
        from .gui import update_table
        update_table(data_df)
        messagebox.showinfo("Thông báo", f"Đã cập nhật dữ liệu cho kỳ {period} từ data.csv!")
        print(f"Đã tạo lại {status_file} từ data.csv")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi cập nhật dữ liệu: {str(e)}")
        data_df = pd.DataFrame(columns=display_columns)
        original_df = data_df.copy()
        from .gui import update_table
        update_table(data_df)

def convert_txt_to_csv(txt_file):
    """Chuyển file TXT sang data_work.csv"""
    encodings = ['utf-8-sig', 'utf-16', 'latin1']
    separators = ['\t', ',', ' ']
    
    for encoding in encodings:
        for sep in separators:
            try:
                txt_data = pd.read_csv(txt_file, sep=sep, encoding=encoding)
                if len(txt_data.columns) > 1:
                    txt_data.to_csv("data_work.csv", index=False, encoding='utf-8-sig')
                    messagebox.showinfo("Thông báo", f"Dữ liệu từ {txt_file} đã được chuyển sang data_work.csv (sep: '{sep}', encoding: {encoding})")
                    print(f"Các cột trong data_work.csv: {txt_data.columns.tolist()}")
                    return
            except Exception as e:
                print(f"Lỗi với encoding {encoding} và sep '{sep}': {e}")
                continue
    
    messagebox.showerror("Lỗi", f"Không thể đọc file TXT: {txt_file}\nDữ liệu không được tách thành cột. Vui lòng kiểm tra định dạng file.")

def gui_du_lieu(file_txt, period, df):
    """Xác nhận dữ liệu từ data_work.csv"""
    global data_df
    if not file_txt:
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn file TXT trước!")
        return
    
    if df is None or df.empty:
        messagebox.showwarning("Cảnh báo", "Không có dữ liệu để xác nhận!")
        return
    
    try:
        work_df = pd.read_csv("data_work.csv", encoding='utf-8-sig')
        updated = False
        for index, row in df.iterrows():
            if row["Status"] not in ["Đã xác nhận", "Đã gửi dữ liệu"]:
                ss = str(row["SS"]).strip()
                mskh = str(row["MSKH"]).strip()
                # So khớp với Sales Part No và End Customer No
                filtered_data = work_df[
                    (work_df["Sales Part No"].astype(str).str.strip() == ss) & 
                    (work_df["End Customer No"].astype(str).str.strip() == mskh)
                ]
                if not filtered_data.empty:
                    df.at[index, "Status"] = "Đã xác nhận"
                    updated = True
        
        if updated:
            data_df = df.copy()
            save_status(period, data_df)
            from .gui import update_table
            update_table(data_df)
            messagebox.showinfo("Thông báo", f"Đã xác nhận dữ liệu cho {period}!")
        else:
            messagebox.showinfo("Thông báo", "Không có dữ liệu nào được xác nhận!")
    except FileNotFoundError:
        messagebox.showerror("Lỗi", "Không tìm thấy file data_work.csv!")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi xử lý dữ liệu: {str(e)}")

def send_all_data(period, df):
    """Gửi toàn bộ dữ liệu đã xác nhận"""
    global data_df
    if df is None or df.empty:
        messagebox.showwarning("Cảnh báo", "Không có dữ liệu để gửi!")
        return
    df.loc[df["Status"] == "Đã xác nhận", "Status"] = "Đã gửi dữ liệu"
    data_df = df.copy()
    save_status(period, data_df)
    from .gui import update_table
    update_table(data_df)
    messagebox.showinfo("Thông báo", "Đã gửi toàn bộ dữ liệu đã xác nhận!")

def send_selected_data(period, df):
    """Gửi các dòng dữ liệu được chọn"""
    global data_df
    if df is None or df.empty:
        messagebox.showwarning("Cảnh báo", "Không có dữ liệu để gửi!")
        return
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn các dòng để gửi!")
        return
    for item in selected:
        index = int(tree.index(item))
        if df.at[index, "Status"] == "Đã xác nhận":
            df.at[index, "Status"] = "Đã gửi dữ liệu"
    data_df = df.copy()
    save_status(period, data_df)
    from .gui import update_table
    update_table(data_df)
    messagebox.showinfo("Thông báo", "Đã gửi các dòng dữ liệu đang chọn!")

def save_status(period, df):
    """Lưu trạng thái vào file CSV"""
    if df is not None and not df.empty:
        status_file = f"Data Test/data_{period.lower()}.csv"
        df.to_csv(status_file, index=False, encoding='utf-8-sig')

def reset_status():
    """Reset trạng thái về rỗng"""
    global data_df
    if data_df is not None and not data_df.empty:
        data_df["Status"] = ""
        save_status(current_period.get() if current_period else "Tháng", data_df)
        from .gui import update_table
        update_table(data_df)
        messagebox.showinfo("Thông báo", "Đã reset toàn bộ trạng thái!")
    else:
        messagebox.showinfo("Thông báo", "Không có dữ liệu để reset!")