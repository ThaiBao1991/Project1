import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from .state import data_df, original_df, filters, current_period, tree, frame_buttons, send_frame, label_file, entry_file, frame_table, frame_status_buttons, btn_back
from .data import initialize_data, gui_du_lieu, send_all_data, send_selected_data, reset_status, convert_txt_to_csv, update_data

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
    """Hiển thị frame gửi dữ liệu với Treeview và các nút điều khiển"""
    global current_period, send_frame, label_file, entry_file, frame_table, tree, frame_status_buttons, btn_back
    if frame_buttons:
        frame_buttons.pack_forget()

    # Khởi tạo widget
    send_frame = tk.Frame(root, bg="#e8ecef")
    send_frame.pack(pady=10, fill="both", expand=True)

    label_file = tk.Label(send_frame, text=f"Chọn file TXT dữ liệu {period.lower()}:", font=("Helvetica", 14, "bold"), bg="#e8ecef", fg="#2c3e50")
    label_file.pack(pady=10)
    entry_file = tk.Entry(send_frame, width=60, font=("Helvetica", 12), bd=2, relief="sunken", bg="#ffffff")
    entry_file.pack(pady=10)
    tk.Button(send_frame, text="Chọn file", command=chon_file_txt, font=("Helvetica", 11, "bold"), bg="#27ae60", fg="white", padx=20, pady=10).pack(pady=10)
    
    frame_table = tk.Frame(send_frame, bg="#e8ecef")
    frame_table.pack(pady=10, fill="both", expand=True)
    
    # Tạo Treeview với thanh cuộn tích hợp
    tree = ttk.Treeview(frame_table, columns=[], show="headings", height=10)
    scrollbar_y = ttk.Scrollbar(frame_table, orient="vertical", command=tree.yview)
    scrollbar_x = ttk.Scrollbar(frame_table, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
    
    # Sắp xếp layout với grid
    tree.grid(row=0, column=0, sticky="nsew")
    scrollbar_y.grid(row=0, column=1, sticky="ns")
    scrollbar_x.grid(row=1, column=0, sticky="ew")
    frame_table.columnconfigure(0, weight=1)
    frame_table.rowconfigure(0, weight=1)
    
    tree.bind("<Double-1>", lambda event: show_details(root, event))
    
    frame_status_buttons = tk.Frame(send_frame, bg="#e8ecef")
    frame_status_buttons.pack(pady=10)
    tk.Button(frame_status_buttons, text="Xác nhận dữ liệu", 
              command=lambda: gui_du_lieu(entry_file.get(), current_period.get() if current_period else period, data_df), 
              font=("Helvetica", 12, "bold"), bg="#27ae60", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)
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
    
    # Khởi tạo current_period
    current_period = tk.StringVar(root, value=period)

    # Khởi tạo dữ liệu và cập nhật Treeview
    display_columns = [
        "SS", "Mã hàng", "MSKH", "Tên khách hàng", "Đối tượng gửi dữ liệu",
        "Yêu cầu đặc biệt khi gửi dữ liệu", "Gửi Lot DAI DIEN: 'DD' Gửi TOAN BO Lot: 'TB'",
        "Nơi nhận dữ liệu", "Nội dung gửi mail", "Địa chỉ gửi mail", "DUNG LƯỢNG 1 LẦN GỬI", "Status"
    ]
    tree["columns"] = display_columns
    for col in display_columns:
        tree.heading(col, text=col, command=lambda c=col: show_filter_entry(c, tree, root))
        tree.column(col, width=150, anchor="center")
    
    initialize_data(period)
    update_table(data_df)

def back_to_main():
    """Quay lại frame chính"""
    if send_frame:
        send_frame.pack_forget()
    if frame_buttons:
        frame_buttons.pack(pady=50, fill="both", expand=True)

def chon_file_txt():
    """Chọn file TXT và chuyển thành data_work.csv"""
    file_path = filedialog.askopenfilename(
        title="Chọn file TXT",
        filetypes=[("Text files", "*.txt")]
    )
    if file_path:
        entry_file.delete(0, tk.END)
        entry_file.insert(0, file_path)
        convert_txt_to_csv(file_path)

def update_table(df):
    """Cập nhật dữ liệu vào Treeview"""
    if tree is None:
        return
    tree.delete(*tree.get_children())
    if df is not None and not df.empty:
        for _, row in df.iterrows():
            tree.insert("", "end", values=tuple(row))
    for col in tree["columns"]:
        if col in filters and filters[col]:
            tree.heading(col, text=f"{col} (filter)")
        else:
            tree.heading(col, text=col)

def show_details(root, event):
    """Hiển thị bảng chi tiết khi double-click dòng"""
    selected = tree.selection()
    if not selected:
        return
    index = int(tree.index(selected[0]))
    if data_df is None or index >= len(data_df):
        messagebox.showinfo("Thông báo", "Không có dữ liệu để hiển thị chi tiết!")
        return
    ss = data_df.at[index, "SS"]
    mskh = data_df.at[index, "MSKH"]
    gui_lot = data_df.at[index, "Gửi Lot DAI DIEN: 'DD' Gửi TOAN BO Lot: 'TB'"]
    try:
        import pandas as pd
        work_df = pd.read_csv("data_work.csv", encoding='utf-8-sig')
        filtered_data = work_df[(work_df["Sales Part No"] == ss) & (work_df["End Customer No"] == mskh)][["End Customer No", "Sales Part No", "Lot No"]]

        if filtered_data.empty:
            messagebox.showinfo("Thông báo", "Không tìm thấy dữ liệu chi tiết!")
            return

        detail_window = tk.Toplevel(root)
        detail_window.title(f"Chi tiết - SS: {ss}, MSKH: {mskh}")
        detail_window.geometry("600x400")

        detail_tree = ttk.Treeview(detail_window, columns=["End Customer No", "Sales Part No", "Lot No"], show="headings")
        for col in ["End Customer No", "Sales Part No", "Lot No"]:
            detail_tree.heading(col, text=col)
            detail_tree.column(col, width=180, anchor="center")
        
        detail_tree.tag_configure("highlight", background="#3498db", foreground="white")
        
        for i, (_, row) in enumerate(filtered_data.iterrows()):
            if gui_lot == "DD" and i == 0:
                detail_tree.insert("", "end", values=(row["End Customer No"], row["Sales Part No"], row["Lot No"]), tags=("highlight",))
            elif gui_lot == "TB":
                detail_tree.insert("", "end", values=(row["End Customer No"], row["Sales Part No"], row["Lot No"]), tags=("highlight",))
            else:
                detail_tree.insert("", "end", values=(row["End Customer No"], row["Sales Part No"], row["Lot No"]))
        
        detail_tree.pack(fill="both", expand=True)
    except FileNotFoundError:
        messagebox.showerror("Lỗi", "Không tìm thấy file data_work.csv!")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi hiển thị chi tiết: {str(e)}")

def show_filter_entry(column, tree_widget, parent_window):
    """Hiển thị cửa sổ nhập bộ lọc cho cột"""
    filter_window = tk.Toplevel(parent_window)
    filter_window.title(f"Filter {column}")
    filter_window.geometry("300x150")
    filter_window.configure(bg="#e8ecef")
    filter_window.lift()
    filter_window.grab_set()

    tk.Label(filter_window, text=f"Nhập giá trị lọc cho {column}:", font=("Helvetica", 12), bg="#e8ecef").pack(pady=10)
    entry = tk.Entry(filter_window, width=30, font=("Helvetica", 12))
    entry.pack(pady=10)
    entry.insert(0, filters.get(column, ""))

    def apply_filter():
        value = entry.get().strip()
        if value:
            filters[column] = value
        else:
            filters.pop(column, None)
        filtered_df = original_df.copy() if original_df is not None else None
        if filtered_df is not None:
            for col, val in filters.items():
                filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(val, case=False, na=False)]
            global data_df
            data_df = filtered_df
            update_table(data_df)
        filter_window.destroy()

    tk.Button(filter_window, text="Apply", command=apply_filter, font=("Helvetica", 12, "bold"), bg="#3498db", fg="white", padx=20, pady=10).pack(pady=10)

def clear_filter():
    """Hủy tất cả bộ lọc"""
    global data_df, original_df
    filters.clear()
    data_df = original_df.copy() if original_df is not None else None
    update_table(data_df)
    messagebox.showinfo("Thông báo", "Đã hủy tất cả bộ lọc!")