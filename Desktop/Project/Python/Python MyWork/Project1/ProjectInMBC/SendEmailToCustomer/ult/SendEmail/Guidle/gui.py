import tkinter as tk
import os
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
# Đảm bảo các biến global được import đúng
from ult.SendEmail.Guidle import state
from .state import data_df,period, original_df, filters, current_period, tree, frame_buttons, send_frame, label_file, entry_file, frame_table, frame_status_buttons, btn_back, month_year_var,month_year_value
# Import các hàm từ .data
from .data import initialize_data, gui_du_lieu, send_all_data, send_selected_data, reset_status, convert_txt_to_csv, update_data
import pandas as pd
from tkcalendar import Calendar, DateEntry
import datetime
from .config import load_config
from ..File.Data.file_data import find_project_root
selected_row_details = {}

def standardize_period(period):
    period_map = {"tháng": "MONTH", "tuần": "WEEK", "ngày": "DAY", "month": "MONTH", "week": "WEEK", "day": "DAY"}
    return period_map.get(str(period).strip().lower(), "MONTH")

def create_main_window(root):
    global main_frame
    main_frame = tk.Frame(root, bg="#e8ecef")
    main_frame.pack(fill="both", expand=True)

    # Frame Gửi Email Khách Hàng
    frame_email = tk.LabelFrame(main_frame, text="Gửi Email Khách Hàng", font=("Helvetica", 14, "bold"), bg="#e8ecef", padx=20, pady=20, fg="#2c3e50")
    frame_email.pack(side="left", fill="both", expand=True, padx=30, pady=30)

    btn_email_month = tk.Button(frame_email, text="Gửi Email Tháng", font=("Helvetica", 13, "bold"), bg="#3498db", fg="white", height=2)
    btn_email_week = tk.Button(frame_email, text="Gửi Email Tuần", font=("Helvetica", 13, "bold"), bg="#27ae60", fg="white", height=2)
    btn_email_day = tk.Button(frame_email, text="Gửi Email Ngày", font=("Helvetica", 13, "bold"), bg="#f39c12", fg="white", height=2)

    btn_email_month.pack(fill="x", pady=10)
    btn_email_week.pack(fill="x", pady=10)
    btn_email_day.pack(fill="x", pady=10)

    # Frame Gửi dữ liệu MonthData
    frame_monthdata = tk.LabelFrame(main_frame, text="Gửi dữ liệu MonthData", font=("Helvetica", 14, "bold"), bg="#e8ecef", padx=20, pady=20, fg="#2c3e50")
    frame_monthdata.pack(side="left", fill="both", expand=True, padx=30, pady=30)

    btn_monthly = tk.Button(frame_monthdata, text="Gửi Monthly", font=("Helvetica", 13, "bold"), bg="#8e44ad", fg="white", height=2)
    btn_monthly.pack(fill="x", pady=10)

    # Trả về các nút để main.py gán lệnh
    return btn_email_month, btn_email_week, btn_email_day, btn_monthly

def show_send_frame(root, period):
    global current_period, send_frame, label_file, entry_file, frame_table, tree, frame_status_buttons, btn_back, data_df, month_year_var
    # --- Thêm biến chế độ lọc ---
    global filter_mode_var, entry_file_kjs
    global main_frame, frame_buttons
    
    # Ẩn hoặc hủy các frame cũ trước khi tạo frame mới
    if send_frame and send_frame.winfo_exists():
        send_frame.pack_forget()
        send_frame.destroy()
        send_frame = None
    if main_frame and main_frame.winfo_exists():
        main_frame.pack_forget()
    if frame_buttons and frame_buttons.winfo_exists():
        frame_buttons.pack_forget()
    
    # Ẩn frame chính nếu đang hiển thị
    if 'main_frame' in globals() and main_frame and main_frame.winfo_ismapped():
        main_frame.pack_forget()
    if 'frame_buttons' in globals() and frame_buttons and frame_buttons.winfo_ismapped():
        frame_buttons.pack_forget()
    filter_mode_var = tk.StringVar(value="MAP_ERP")  # Mặc định là MAP_ERP
    
    if month_year_var is None:
        month_year_var = tk.StringVar()
        month_year_var.set(datetime.datetime.now().strftime("%m/%Y"))
    # Ẩn frame chính nếu đang hiển thị
    if frame_buttons:
        frame_buttons.pack_forget()
        
    # Thiết lập cửa sổ full màn hình
    root.state('zoomed')  # Thêm dòng này để mở full màn hình
    
    # # Thiết lập kích thước cửa sổ
    # root.geometry("1700x980")

    # Khởi tạo biến period
    current_period = tk.StringVar()
    current_period.set(period)

    # Khởi tạo dữ liệu
    from .data import initialize_data
    data_df = initialize_data(period)

    # Tạo frame gửi dữ liệu
    send_frame = tk.Frame(root, bg="#e8ecef")
    send_frame.pack(pady=10, fill="both", expand=True)

     # --- Phần chọn file và tháng ---
    frame_file_month = tk.Frame(send_frame, bg="#e8ecef")
    frame_file_month.pack(fill="x", padx=20, pady=10)
    
    # Thay thế phần radio buttons bằng 2 file entry
    frame_file_select = tk.Frame(frame_file_month, bg="#e8ecef")
    frame_file_select.pack(fill="x", pady=5)
    
    # Label và Entry chọn file - bố cục ngang
    # Entry cho MAP-ERP
    tk.Label(frame_file_select, text=f"Chọn file TXT MAP-ERP:", 
            font=("Helvetica", 12), bg="#e8ecef").pack(side=tk.LEFT)
    entry_file = tk.Entry(frame_file_select, width=50, font=("Helvetica", 12))
    entry_file.pack(side=tk.LEFT, padx=10)
    tk.Button(frame_file_select, text="Chọn file", command=lambda: chon_file_txt("MAP_ERP", entry_file),
             font=("Helvetica", 11, "bold"), bg="#27ae60", fg="white", padx=20, pady=5).pack(side=tk.LEFT)

    # Entry cho KJS
    frame_file_kjs = tk.Frame(frame_file_month, bg="#e8ecef")
    frame_file_kjs.pack(fill="x", pady=5)
    tk.Label(frame_file_kjs, text=f"Chọn file TXT/CSV KJS:", 
            font=("Helvetica", 12), bg="#e8ecef").pack(side=tk.LEFT)
    entry_file_kjs = tk.Entry(frame_file_kjs, width=50, font=("Helvetica", 12))
    entry_file_kjs.pack(side=tk.LEFT, padx=10)
    tk.Button(frame_file_kjs, text="Chọn file", command=lambda: chon_file_txt("KJS", entry_file_kjs),
             font=("Helvetica", 11, "bold"), bg="#27ae60", fg="white", padx=20, pady=5).pack(side=tk.LEFT)

    # Label và nút chọn tháng
    frame_month_select = tk.Frame(frame_file_month, bg="#e8ecef")
    frame_month_select.pack(fill="x", pady=5)
    
    tk.Label(frame_month_select, text="Chọn tháng:", font=("Helvetica", 12), bg="#e8ecef").pack(side=tk.LEFT)

    # Combobox chọn tháng
    month_values = [f"{i:02d}" for i in range(1, 13)]
    current_month = datetime.datetime.now().strftime("%m")
    month_cb = ttk.Combobox(frame_month_select, values=month_values, width=4, font=("Helvetica", 12), state="readonly")
    month_cb.set(current_month)
    month_cb.pack(side=tk.LEFT, padx=5)

    # Combobox chọn năm
    current_year = datetime.datetime.now().year
    year_values = [str(y) for y in range(current_year - 3, current_year + 4)]
    year_cb = ttk.Combobox(frame_month_select, values=year_values, width=6, font=("Helvetica", 12), state="readonly")
    year_cb.set(str(current_year))
    year_cb.pack(side=tk.LEFT, padx=5)
    
    def update_month_year_var(event=None):
        value = f"{month_cb.get()}/{year_cb.get()}"
        month_year_var.set(value)
        state.month_year_value = value
        state.month_year_var = month_year_var

    month_cb.bind("<<ComboboxSelected>>", update_month_year_var)
    year_cb.bind("<<ComboboxSelected>>", update_month_year_var)
    update_month_year_var()
    
    # Tạo Treeview
    frame_table = tk.Frame(send_frame, bg="#e8ecef")
    frame_table.pack(pady=10, fill="both", expand=True)
    
    columns = list(data_df.columns) if not data_df.empty else []
    tree = ttk.Treeview(frame_table, columns=columns, show="headings", height=20)
    
    # Thêm thanh cuộn
    scrollbar_y = ttk.Scrollbar(frame_table, orient="vertical", command=tree.yview)
    scrollbar_x = ttk.Scrollbar(frame_table, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
    
    # Cấu hình layout
    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar_y.grid(row=0, column=1, sticky="ns")
    scrollbar_x.grid(row=1, column=0, sticky="ew")
    frame_table.columnconfigure(0, weight=1)
    frame_table.rowconfigure(0, weight=1)

    # Cập nhật Treeview ngay lập tức
    update_table(data_df)

    # Tạo các nút điều khiển
    frame_status_buttons = tk.Frame(send_frame, bg="#e8ecef")
    frame_status_buttons.pack(pady=10)
    
    tree.bind("<Double-1>", lambda event: show_details(root, event))

    # Sửa lại nút xác nhận dữ liệu
    tk.Button(
        frame_status_buttons, 
        text="Xác nhận dữ liệu",
        command=lambda: validate_and_process_data(entry_file.get(), entry_file_kjs.get()),
        font=("Helvetica", 12, "bold"), 
        bg="#27ae60", 
        fg="white", 
        padx=20, 
        pady=10
    ).pack(side=tk.LEFT, padx=10)
    
     # Nút nén dữ liệu
    tk.Button(
        frame_status_buttons, text="Nén dữ liệu",
        command=lambda: nen_du_lieu(data_df, period),
        font=("Helvetica", 12, "bold"), bg="#2980b9", fg="white", padx=20, pady=10
    ).pack(side=tk.LEFT, padx=10)
    
    tk.Button(frame_status_buttons, text="Reset", command=reset_status,
              font=("Helvetica", 12, "bold"), bg="#e74c3c", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)

    # Tạo menu gửi dữ liệu
    send_data_menu = tk.Menu(root, tearoff=0)
    send_data_menu.add_command(label="Gửi toàn bộ",
                               command=lambda: send_all_data(current_period.get() if current_period else period, data_df))
    send_data_menu.add_command(label="Gửi các dòng đang chọn",
                               command=lambda: send_selected_data(current_period.get() if current_period else period, data_df))
    tk.Button(frame_status_buttons, text="Gửi dữ liệu", font=("Helvetica", 12, "bold"), bg="#3498db", fg="white", padx=20, pady=10,
              command=lambda: send_data_menu.post(frame_status_buttons.winfo_children()[2].winfo_rootx(),
                                                 frame_status_buttons.winfo_children()[2].winfo_rooty() +
                                                 frame_status_buttons.winfo_children()[2].winfo_height())).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_status_buttons, text="Hủy Filter", command=clear_filter,
              font=("Helvetica", 12, "bold"), bg="#f39c12", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_status_buttons, text="Update dữ liệu",
              command=lambda: update_data(period, root),
              font=("Helvetica", 12, "bold"), bg="#9b59b6", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)


    btn_back = tk.Button(send_frame, text="← Quay lại", font=("Helvetica", 12, "bold"), bg="#e74c3c", fg="white", padx=20, pady=10, command=back_to_main)
    btn_back.pack(anchor="nw", padx=20, pady=20)
    
    # Khởi tạo dữ liệu và cập nhật Treeview
    # Cài đặt các cột trước khi initialize_data chạy
    display_columns = [
        "SS", "Mã hàng", "MSKH", "Đối tượng gửi dữ liệu","Nguồn dữ liệu","Yêu cầu đặc biệt khi gửi dữ liệu",
        "Part Number", "Gui_DL",
        "Nơi nhận dữ liệu", "DUNG LƯỢNG 1 LẦN GỬI", "Status"
    ]
    tree["columns"] = display_columns
    for col in display_columns:
        tree.heading(col, text=col, command=lambda c=col: show_filter_entry(c, tree, root))
        tree.column(col, width=150, anchor="center")

    # Gọi initialize_data để load data_df
    # initialize_data sẽ gọi update_table bên trong khi load xong data
    initialize_data(period)

    # Lên lịch gọi update_table sau một khoảng thời gian ngắn
    # Điều này giúp đảm bảo Treeview đã sẵn sàng khi được cập nhật dữ liệu
    # Kiểm tra nếu root vẫn tồn tại trước khi gọi after
    if root.winfo_exists():
        print("Scheduling update_table after 200ms") # Debug print
        # Tăng thời gian chờ lên 200ms để chắc chắn hơn
        root.after(200, lambda: update_table(data_df))
    
# Thêm hàm kiểm tra và xử lý dữ liệu
def validate_and_process_data(map_erp_file, kjs_file):
    if not map_erp_file or not kjs_file:
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn cả file MAP-ERP và KJS!")
        return

    # print Đọc nguồn dữ liệu từ 
    data_dir = os.path.join(os.getcwd(), "DATASETC", "DATA_customer_time")
    csv_file_path = os.path.join(data_dir, f"data_{current_period.get()}.csv")
    # print(pd.read_csv(csv_file_path, encoding='utf-8-sig').head())  # In ra 5 dòng đầu tiên của file CSV
    if state.month_year_value ==None or state.month_year_value == "":
        state.month_year_value = datetime.datetime.now().strftime("%m/%Y")
        
    gui_du_lieu(csv_file_path,current_period.get(),state.month_year_value, data_df)
    
    # gui_du_lieu(map_erp_file, current_period.get(), data_df, month_year_var.get(), "MAP_ERP")
    # gui_du_lieu(kjs_file, current_period.get(), data_df, month_year_var.get(), "KJS")
   

def back_to_main():
    global send_frame, main_frame, frame_buttons
    if send_frame:
        send_frame.pack_forget()
    if 'main_frame' in globals() and main_frame:
        main_frame.pack(fill="both", expand=True)
    elif 'frame_buttons' in globals() and frame_buttons:
        frame_buttons.pack(pady=50, fill="both", expand=True)
# Sửa lại hàm chọn file
def chon_file_txt(mode, entry_widget):
    file_path = filedialog.askopenfilename(
        title=f"Chọn file {'MAP-ERP' if mode == 'MAP_ERP' else 'KJS'}",
        filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")],
        defaultextension=".csv"  # Prioritize CSV as default
    )
    output_dir = os.path.join(os.getcwd(), "DATASETC", "Data by classification")
    os.makedirs(output_dir, exist_ok=True)
    output_filename = f"data_work_{mode}.csv"
    output_file = os.path.join(output_dir, output_filename)
    if file_path:
        entry_widget.delete(0, tk.END)
        entry_widget.insert(0, file_path)
    try:
        if file_path.lower().endswith('.csv'):
            encodings = ['utf-8-sig', 'utf-8', 'latin1', 'iso-8859-1', 'utf-16']
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding,low_memory=False)
                    if not df.empty:
                        df.to_csv(output_file, index=False, encoding='utf-8-sig')
                        messagebox.showinfo("Thành công", "Đã sử dụng file CSV trực tiếp")
                        break
                except Exception:
                    continue
            else:
                messagebox.showerror("Lỗi", "Không thể đọc file CSV với bất kỳ encoding nào")
                return
        else:
            convert_txt_to_csv(file_path)
        from .data import initialize_data
        initialize_data(current_period.get() if current_period else "MONTH")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể xử lý file: {str(e)}")


def update_table(df):
    """Cập nhật dữ liệu vào Treeview - Phiên bản tối ưu"""
    global tree, filters
    
    # Kiểm tra widget (giữ mức độ vừa phải)
    if tree is None or not tree.winfo_exists():
        # print("[DEBUG] Treeview không khả dụng")  # Log ngắn gọn
        return

    # Debug log cần thiết
    # print(f"[DEBUG] Cập nhật Treeview với {len(df) if df is not None else 0} dòng")
    
    # Xóa dữ liệu cũ
    tree.delete(*tree.get_children())
    
    # Thêm dữ liệu mới (tối ưu hóa)
    if df is not None and not df.empty:
        # Sử dụng itertuples() nhanh hơn iterrows()
        for row in df.itertuples(index=False):
            try:
                tree.insert("", "end", values=tuple(str(x) for x in row))
            except Exception as e:
                print(f"[ERROR] Lỗi thêm dòng: {e}")
                continue
    
    # Cập nhật tiêu đề cột (giữ nguyên từ code cũ)
    for col in tree["columns"]:
        tree.heading(
            col, 
            text=f"{col} (filter)" if col in filters and filters[col] else col
        )
    
    # Force update nếu cần
    tree.update_idletasks()

def show_details(root, event):
    import json
    import os
    from tkinter import messagebox

    # Lấy dòng được chọn
    selected = tree.selection()
    if not selected:
        return

    item_id = selected[0]
    values = tree.item(item_id, 'values')
    tree_columns = tree["columns"]

    # Lấy các giá trị cần thiết
    ss = str(values[tree_columns.index("SS")]).strip() if "SS" in tree_columns else ""
    mskh = str(values[tree_columns.index("MSKH")]).strip() if "MSKH" in tree_columns else ""
    ma_hang = str(values[tree_columns.index("Mã hàng")]).strip() if "Mã hàng" in tree_columns else ""

    # Đọc file json_data_Month.json
    period = current_period.get() if current_period else "MONTH"
    json_file = Path.cwd() / "DATASETC" / "Data by classification" / f"json_data_{period.upper()}.json"
    if not json_file.exists():
        messagebox.showerror("Lỗi", f"Không tìm thấy file {json_file}")
        return

    with open(json_file, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    # Tìm tất cả các lot thuộc mọi key bắt đầu bằng key_prefix
    key_prefix = f"{ss}|{ma_hang}|{mskh}"
    lot_list = []
    for k, lots in json_data.items():
        if k.startswith(key_prefix):
            lot_list.extend(lots)

    if not lot_list:
        messagebox.showinfo("Thông báo", f"Không tìm thấy dữ liệu cho {key_prefix}!")
        return

    # Tạo cửa sổ chi tiết
    detail_window = tk.Toplevel(root)
    detail_window.title(f"Chi tiết - SS: {ss}, Mã hàng: {ma_hang}, MSKH: {mskh}")
    detail_window.geometry("900x400")
    detail_window.transient(root)
    detail_window.grab_set()

    # Tạo Treeview
    display_cols = ["Lot No", "W/d/r No", "FolderLink"]
    detail_tree = ttk.Treeview(detail_window, columns=display_cols, show="headings")
    for col in display_cols:
        detail_tree.heading(col, text=col)
        detail_tree.column(col, width=200, anchor="center")

    # Thêm dữ liệu
    for lot in lot_list:
        lot_no = lot.get("Lot No", "")
        wdr_no = lot.get("W/d/r No", "")
        folder_link = lot.get("FolderLink", None)
        detail_tree.insert("", "end", values=(lot_no, wdr_no, folder_link if folder_link else ""))

    detail_tree.pack(fill="both", expand=True, pady=10)

    # Nếu có FolderLink, tạo nút mở thư mục
    def open_selected_folder():
        selected_items = detail_tree.selection()
        if not selected_items:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một dòng có FolderLink!")
            return
        item = selected_items[0]
        folder_link = detail_tree.item(item, "values")[2]
        if folder_link and os.path.exists(folder_link):
            os.startfile(folder_link)
        else:
            messagebox.showinfo("Thông báo", f"Không tìm thấy thư mục:\n{folder_link}")

    tk.Button(
        detail_window,
        text="Mở thư mục đã copy",
        command=open_selected_folder,
        font=("Helvetica", 12, "bold"),
        bg="#3498db",
        fg="white"
    ).pack(pady=10)

def show_filter_entry(column, tree_widget, parent_window):
    """Hiển thị cửa sổ nhập bộ lọc cho cột"""
    global filters, data_df, original_df
    
    filter_window = tk.Toplevel(parent_window)
    filter_window.title(f"Filter {column}")
    filter_window.geometry("300x150")
    filter_window.configure(bg="#e8ecef")
    filter_window.transient(parent_window)
    filter_window.grab_set()

    tk.Label(filter_window, text=f"Nhập giá trị lọc cho {column}:", 
             font=("Helvetica", 12), bg="#e8ecef").pack(pady=10)
    
    entry = tk.Entry(filter_window, width=30, font=("Helvetica", 12))
    entry.pack(pady=10)
    entry.insert(0, filters.get(column, ""))

    def apply_filter():
        global data_df, original_df, filters
        value = entry.get().strip()
        
        # Đảm bảo original_df không None
        if original_df is None:
            original_df = data_df.copy() if data_df is not None else pd.DataFrame()
        
        if value:
            filters[column] = value
            # Lọc từ original_df
            filtered_df = original_df[original_df[column].astype(str).str.contains(value, case=False, na=False)]
            data_df = filtered_df.copy()
        else:
            if column in filters:
                del filters[column]
            # Trả về dữ liệu gốc
            data_df = original_df.copy()
        
        update_table(data_df)
        filter_window.destroy()

    tk.Button(filter_window, text="Apply", command=apply_filter, font=("Helvetica", 12, "bold"), bg="#3498db", fg="white", padx=20, pady=10).pack(pady=10)

def clear_filter():
    global filters, data_df, original_df
    
    # Đảm bảo original_df tồn tại
    if original_df is None:
        original_df = data_df.copy() if data_df is not None else pd.DataFrame()
    
    filters.clear()
    data_df = original_df.copy()
    update_table(data_df)
def nen_du_lieu(data_df, period):
    from .data import nen_du_lieu as nen_func
    nen_func(data_df, period)