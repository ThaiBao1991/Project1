import tkinter as tk
import os
from tkinter import filedialog, messagebox, ttk
# Đảm bảo các biến global được import đúng
from .state import data_df, original_df, filters, current_period, tree, frame_buttons, send_frame, label_file, entry_file, frame_table, frame_status_buttons, btn_back, month_year_var
# Import các hàm từ .data
from .data import initialize_data, gui_du_lieu, send_all_data, send_selected_data, reset_status, convert_txt_to_csv, update_data
import pandas as pd
from tkcalendar import Calendar, DateEntry
import datetime
from .config import load_config

selected_row_details = {}

def create_main_window(root):
    """Tạo frame chính với các nút Gửi Email Tháng/Tuần/Ngày"""
    global frame_buttons
    frame_title = tk.Frame(root, bg="#e8ecef")
    frame_title.pack(pady=20, fill="x")
    tk.Label(frame_title, text="GỬI EMAIL KHÁCH HÀNG TỰ ĐỘNG", font=("Helvetica", 24, "bold"), bg="#e8ecef", fg="#2c3e50").pack()

    frame_buttons = tk.Frame(root, bg="#e8ecef")
    tk.Button(frame_buttons, text="Gửi Email Tháng", font=("Helvetica", 14, "bold"), bg="#3498db", fg="white", padx=30, pady=15,
              command=lambda: show_send_frame(root, "Tháng")).pack(side=tk.LEFT, padx=20)
    tk.Button(frame_buttons, text="Gửi Email Tuần", font=("Helvetica", 14, "bold"), bg="#27ae60", fg="white", padx=30, pady=15,
              command=lambda: show_send_frame(root, "Tuần")).pack(side=tk.LEFT, padx=20)
    tk.Button(frame_buttons, text="Gửi Email Ngày", font=("Helvetica", 14, "bold"), bg="#f39c12", fg="white", padx=30, pady=15,
              command=lambda: show_send_frame(root, "Ngày")).pack(side=tk.LEFT, padx=20)

    return frame_buttons

def show_send_frame(root, period):
    global current_period, send_frame, label_file, entry_file, frame_table, tree, frame_status_buttons, btn_back, data_df, month_year_var
    # --- Thêm biến chế độ lọc ---
    global filter_mode_var, entry_file_kjs
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
    
    # Label và Entry chọn file - bố cục ngang
    # --- Dòng chọn file MAP_ERP ---
    frame_file_select = tk.Frame(frame_file_month, bg="#e8ecef")
    frame_file_select.pack(fill="x", pady=5)
    cb_map_erp = tk.Radiobutton(
        frame_file_select, text="Lọc dữ liệu theo MAP-ERP", variable=filter_mode_var, value="MAP_ERP",
        font=("Helvetica", 12), bg="#e8ecef", command=lambda: update_file_entries())
    cb_map_erp.pack(side=tk.LEFT)
    tk.Label(frame_file_select, text=f"Chọn file TXT dữ liệu {period.lower()}:", 
            font=("Helvetica", 12), bg="#e8ecef").pack(side=tk.LEFT)
    entry_file = tk.Entry(frame_file_select, width=60, font=("Helvetica", 12), bd=2, relief="sunken", bg="#ffffff")
    entry_file.pack(side=tk.LEFT, padx=10)
    tk.Button(frame_file_select, text="Chọn file", command=lambda: chon_file_txt("MAP_ERP"),
             font=("Helvetica", 11, "bold"), bg="#27ae60", fg="white", padx=20, pady=5).pack(side=tk.LEFT)

    # --- Dòng chọn file KJS ---
    frame_file_select_kjs = tk.Frame(frame_file_month, bg="#e8ecef")
    frame_file_select_kjs.pack(fill="x", pady=5)
    cb_kjs = tk.Radiobutton(
        frame_file_select_kjs, text="Lọc dữ liệu theo KJS", variable=filter_mode_var, value="KJS",
        font=("Helvetica", 12), bg="#e8ecef", command=lambda: update_file_entries())
    cb_kjs.pack(side=tk.LEFT)
    tk.Label(frame_file_select_kjs, text=f"Chọn file TXT/CSV KJS:", 
            font=("Helvetica", 12), bg="#e8ecef").pack(side=tk.LEFT)
    entry_file_kjs = tk.Entry(frame_file_select_kjs, width=60, font=("Helvetica", 12), bd=2, relief="sunken", bg="#ffffff")
    entry_file_kjs.pack(side=tk.LEFT, padx=10)
    tk.Button(frame_file_select_kjs, text="Chọn file", command=lambda: chon_file_txt("KJS"),
             font=("Helvetica", 11, "bold"), bg="#27ae60", fg="white", padx=20, pady=5).pack(side=tk.LEFT)

    # --- Ẩn/hiện entry theo chế độ ---
    def update_file_entries():
        if filter_mode_var.get() == "MAP_ERP":
            entry_file.config(state="normal")
            entry_file_kjs.config(state="disabled")
        else:
            entry_file.config(state="disabled")
            entry_file_kjs.config(state="normal")
    update_file_entries()

    # Label và nút chọn tháng
    frame_month_select = tk.Frame(frame_file_month, bg="#e8ecef")
    frame_month_select.pack(fill="x", pady=5)
    
    tk.Label(frame_month_select, text="Chọn tháng:", 
            font=("Helvetica", 12), bg="#e8ecef").pack(side=tk.LEFT)
    
    # Tạo DateEntry chỉ hiển thị tháng/năm
    month_year_var = tk.StringVar()
    month_year_var.set(datetime.datetime.now().strftime("%m/%Y"))  # Định dạng mặc định: mm/yyyy
    month_year_btn = tk.Button(
        frame_month_select,
        text=month_year_var.get(),
        font=("Helvetica", 12),
        relief="groove",
        command=lambda: show_month_year_picker(root, month_year_var))
    month_year_btn.pack(side=tk.LEFT, padx=10)
    
    def show_month_year_picker(parent, month_year_var):
        top = tk.Toplevel(parent)
        top.title("Chọn tháng/năm")
        top.geometry("300x280")
        top.resizable(False, False)
        
        # Lấy tháng/năm hiện tại từ biến
        current_value = month_year_var.get()
        try:
            month, year = map(int, current_value.split('/'))
        except:
            now = datetime.datetime.now()
            month, year = now.month, now.year
        
        # Tạo calendar với date_pattern chỉ hiển thị tháng/năm
        cal = Calendar(
            top,
            selectmode='day',
            year=year,
            month=month,
            day=1,
            showweeknumbers=False,
            date_pattern='y-mm-dd'  # Định dạng mặc định
        )
        cal.pack(pady=20, padx=20)
        
        def apply_selection():
            selected_date = cal.get_date()
            # Chuyển đổi thành định dạng mm/yyyy
            try:
                dt = datetime.datetime.strptime(selected_date, "%Y-%m-%d")
                month_year_var.set(dt.strftime("%m/%Y"))
                month_year_btn.config(text=month_year_var.get())
                # Debug: In ra giá trị để kiểm tra
                print(f"Giá trị đã chọn: {month_year_var.get()}")
            except ValueError as e:
                messagebox.showerror("Lỗi", f"Định dạng ngày không hợp lệ: {str(e)}")
            top.destroy()
        
        tk.Button(
            top,
            text="Chọn",
            command=apply_selection,
            font=("Helvetica", 12),
            width=10
        ).pack(pady=10)
        
        # Đảm bảo cửa sổ này nhận focus
        top.grab_set()

    # Tạo Treeview
    frame_table = tk.Frame(send_frame, bg="#e8ecef")
    frame_table.pack(pady=10, fill="both", expand=True)
    
    tree = ttk.Treeview(frame_table, columns=data_df.columns.tolist() if data_df is not None else [], 
                       show="headings", height=10)
    
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

    tk.Button(frame_status_buttons, text="Xác nhận dữ liệu",
        command=lambda: gui_du_lieu(
            entry_file.get() if filter_mode_var.get() == "MAP_ERP" else entry_file_kjs.get(),
            current_period.get() if current_period else period,
            data_df,
            month_year_var.get(),
            filter_mode_var.get()  # truyền chế độ lọc
        ),
        font=("Helvetica", 12, "bold"), bg="#27ae60", fg="white", padx=20, pady=10
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

    btn_back = tk.Button(send_frame, text="Quay lại", font=("Helvetica", 14, "bold"), bg="#e74c3c", fg="white", padx=30, pady=15,
                          command=back_to_main)
    btn_back.pack(pady=10)
    
    # Khởi tạo dữ liệu và cập nhật Treeview
    # Cài đặt các cột trước khi initialize_data chạy
    display_columns = [
        "SS", "Mã hàng", "MSKH", "Tên khách hàng", "Đối tượng gửi dữ liệu",
        "Part Number", "Gui_DL",
        "Nơi nhận dữ liệu", "Nội dung gửi mail", "Địa chỉ gửi mail", "DUNG LƯỢNG 1 LẦN GỬI", "Status"
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
    


def back_to_main():
    """Quay lại frame chính"""
    global send_frame, frame_buttons
    if send_frame:
        send_frame.pack_forget()
    if frame_buttons:
        frame_buttons.pack(pady=50, fill="both", expand=True)

def chon_file_txt(mode="MAP_ERP"):
    """Chọn file TXT hoặc CSV cho từng chế độ"""
    global entry_file, entry_file_kjs, current_period, data_df

    file_path = filedialog.askopenfilename(
        title="Chọn file dữ liệu (TXT hoặc CSV)",
        filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("All files", "*.*")]
    )
    if not file_path:
        return

    if mode == "MAP_ERP":
        entry_file.delete(0, tk.END)
        entry_file.insert(0, file_path)
    else:
        entry_file_kjs.delete(0, tk.END)
        entry_file_kjs.insert(0, file_path)

    try:
        if file_path.lower().endswith('.csv'):
            encodings = ['utf-8-sig', 'utf-8', 'latin1', 'iso-8859-1', 'utf-16']
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    if not df.empty:
                        df.to_csv("data_work.csv", index=False, encoding='utf-8-sig')
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
        initialize_data(current_period.get() if current_period else "Tháng")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể xử lý file: {str(e)}")


def update_table(df):
    """Cập nhật dữ liệu vào Treeview - Phiên bản tối ưu"""
    global tree, filters
    
    # Kiểm tra widget (giữ mức độ vừa phải)
    if tree is None or not tree.winfo_exists():
        print("[DEBUG] Treeview không khả dụng")  # Log ngắn gọn
        return

    # Debug log cần thiết
    print(f"[DEBUG] Cập nhật Treeview với {len(df) if df is not None else 0} dòng")
    
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
    """Hiển thị bảng chi tiết khi double-click dòng - Bổ sung cột W/d/r No"""
    global data_df, selected_row_details
    
    if tree is None or not tree.winfo_exists() or not tree.winfo_toplevel().winfo_exists():
        messagebox.showwarning("Cảnh báo", "Giao diện bảng chưa sẵn sàng.")
        return

    selected = tree.selection()
    if not selected:
        return
        
    try:
        # Lấy thông tin từ dòng được chọn
        item_id = selected[0]
        values = tree.item(item_id, 'values')
        tree_columns = tree["columns"]
        
        # Lấy các giá trị cần thiết
        ss_index = tree_columns.index("SS") if "SS" in tree_columns else -1
        mskh_index = tree_columns.index("MSKH") if "MSKH" in tree_columns else -1
        mh_index = tree_columns.index("Mã hàng") if "Mã hàng" in tree_columns else -1
        noinhan_index = tree_columns.index("Nơi nhận dữ liệu") if "Nơi nhận dữ liệu" in tree_columns else -1
        gui_dl_index = tree_columns.index("Gui_DL") if "Gui_DL" in tree_columns else -1
        
        ss = str(values[ss_index]).strip() if ss_index != -1 and len(values) > ss_index else ""
        mskh = str(values[mskh_index]).strip() if mskh_index != -1 and len(values) > mskh_index else ""
        ma_hang=str(values[mh_index]).strip() if mh_index != -1 and len(values) > mh_index else ""
        noinhan=str(values[noinhan_index]).strip() if noinhan_index != -1 and len(values) > noinhan_index else ""
        gui_dl = str(values[gui_dl_index]).strip() if gui_dl_index != -1 and len(values) > gui_dl_index else ""

        if not ss or not mskh:
            messagebox.showwarning("Cảnh báo", "Không tìm thấy giá trị SS hoặc MSKH trong dòng được chọn.")
            return

        # Đọc file data_work.csv
        if not os.path.exists("data_work.csv"):
            messagebox.showwarning("Cảnh báo", "Không tìm thấy file data_work.csv!\nVui lòng chọn file TXT để tạo.")
            return

        work_df = pd.read_csv("data_work.csv", encoding='utf-8-sig')

        # Kiểm tra và lấy tên cột thứ 22 (W/d/r No)
        wdr_col = work_df.columns[21] if len(work_df.columns) > 21 else None
        
        # Danh sách cột cần hiển thị
        display_cols = ["Sales Part No", "End Customer No", "Lot No"]
        if wdr_col:
            display_cols.append(wdr_col)
        
        # Kiểm tra cột tồn tại
        missing_cols = [col for col in display_cols if col not in work_df.columns]
        if missing_cols:
            messagebox.showerror("Lỗi", f"Thiếu các cột: {', '.join(missing_cols)}")
            return

        # Lọc dữ liệu
        filtered_data = work_df[
            (work_df["Sales Part No"].astype(str).str.strip() == ss) &
            (work_df["End Customer No"].astype(str).str.strip() == mskh)
        ][display_cols]
        
         # Lưu thông tin chi tiết vào biến toàn cục
        selected_row_details = {
            'ss': ss,
            'mskh': mskh,
            'ma_hang': ma_hang,
            'noi_nhan': noinhan,
            'gui_dl': gui_dl,
            'lot_nos': filtered_data["Lot No"].unique().tolist(),
            'wdr_nos': filtered_data["W/d/r No"].unique().tolist() if "W/d/r No" in filtered_data.columns else []
        }

        if filtered_data.empty:
            messagebox.showinfo("Thông báo", f"Không tìm thấy dữ liệu cho SS: {ss}, MSKH: {mskh}!")
            return
        
        # Tạo cửa sổ chi tiết
        try:
            detail_window = tk.Toplevel(root)
            detail_window.title(f"Chi tiết - SS: {ss}, MSKH: {mskh}")
            detail_window.geometry("800x400")
            detail_window.transient(root)
            detail_window.grab_set()
            
            # Tạo dictionary row từ values và tree_columns
            row = {}
            for i, col in enumerate(tree_columns):
                if i < len(values):
                    row[col] = values[i]
                else:
                    row[col] = ""
            
            # Thêm nút mở thư mục nếu đã copy file
            if str(row.get("Status", "")).strip() == "Đã copy dữ liệu":
                def open_target_folder():
                    config = load_config()
                    data_temp_path = config.get("data_temp_path", "")
                    if not data_temp_path:
                        messagebox.showerror("Lỗi", "Không tìm thấy đường dẫn thư mục tạm!")
                        return
                    
                    # Sử dụng giá trị noi_nhan đã lấy từ đầu hàm (đã kiểm tra)
                    noi_nhan = selected_row_details['noi_nhan']  # Sử dụng giá trị đã lưu trong selected_row_details
                    
                    print("Giá trị nơi nhận:", repr(noi_nhan))  # Debug in ra giá trị thực sự
                    
                    if not noi_nhan:
                        messagebox.showerror("Lỗi", "Không có thông tin nơi nhận trong dữ liệu!")
                        return
                        
                    selected_year = datetime.datetime.now().strftime("%Y")
                    ss_index = tree_columns.index("SS") if "SS" in tree_columns else -1
                    ss = str(values[ss_index]).strip() if ss_index != -1 and len(values) > ss_index else ""
                    
                    if not ss:
                        messagebox.showerror("Lỗi", "Không có thông tin SS trong dữ liệu!")
                        return
                        
                    target_folder = os.path.join(
                        data_temp_path,
                        f"Gửi {noi_nhan}",
                        selected_year,
                        f"Gửi {datetime.datetime.now().strftime('%y.%m')}",
                        ss
                    )
                    
                    print("Đường dẫn đích:", target_folder)
                    
                    if os.path.exists(target_folder):
                        os.startfile(target_folder)
                    else:
                        messagebox.showinfo("Thông báo", f"Không tìm thấy thư mục:\n{target_folder}")
                
                btn_open_folder = tk.Button(
                    detail_window, 
                    text="Mở thư mục đã copy",
                    command=open_target_folder,
                    font=("Helvetica", 12, "bold"),
                    bg="#3498db",
                    fg="white"
                )
                btn_open_folder.pack(pady=10)
            else:
                lbl_status = tk.Label(
                    detail_window,
                    text="Chưa copy file vào thư mục đích",
                    font=("Helvetica", 12),
                    fg="red"
                )
                lbl_status.pack(pady=10)

            # Tạo Treeview
            detail_tree = ttk.Treeview(detail_window, columns=display_cols, show="headings")
            for col in display_cols:
                detail_tree.heading(col, text=col)
                detail_tree.column(col, width=150, anchor="center")

            # Cấu hình màu highlight
            detail_tree.tag_configure("highlight", background="#3498db", foreground="white")

            # Xử lý highlight và thêm dữ liệu theo Gui_DL
            if gui_dl.upper() == "DD":
                # Tạo set để lưu W/d/r No đã gặp
                seen_wdr = set()
                highlighted_rows = []
                
                for _, row in filtered_data.iterrows():
                    values = [str(row[col]) for col in display_cols]
                    wdr_no = str(row.get("W/d/r No", "")).strip() if "W/d/r No" in row else ""
                    
                    tag = ()
                    # Nếu là W/d/r No mới, highlight và thêm vào seen_wdr
                    if wdr_no and wdr_no not in seen_wdr:
                        seen_wdr.add(wdr_no)
                        tag = ("highlight",)
                        highlighted_rows.append(values)
                    
                    detail_tree.insert("", "end", values=values, tags=tag)
                
                # Lưu các dòng được highlight để dùng cho việc copy
                selected_row_details['highlighted_rows'] = highlighted_rows
                
            elif gui_dl.upper() == "TB":
                # Highlight và copy tất cả các dòng
                highlighted_rows = []
                for _, row in filtered_data.iterrows():
                    values = [str(row[col]) for col in display_cols]
                    detail_tree.insert("", "end", values=values, tags=("highlight",))
                    highlighted_rows.append(values)
                
                selected_row_details['highlighted_rows'] = highlighted_rows

            detail_tree.pack(fill="both", expand=True)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi khi hiển thị chi tiết: {str(e)}")

    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi hiển thị chi tiết: {str(e)}")

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