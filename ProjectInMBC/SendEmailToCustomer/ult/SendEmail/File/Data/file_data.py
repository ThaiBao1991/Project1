import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import os
import math

# Thêm các biến định nghĩa cột cần thiết ở đầu file
REQUIRED_COLUMNS = [
    "SS", "Mã hàng", "MSKH", "Part Number", "Đối tượng gửi dữ liệu","Nguồn dữ liệu",
    "Yêu cầu đặc biệt khi gửi dữ liệu", 'Gửi Lot DAI DIEN: "DD"\nGửi TOAN BO Lot: "TB"',
    "Nơi nhận dữ liệu", "DUNG LƯỢNG 1 LẦN GỬI"
]

SHOW_COLUMNS = [
    "SS", "Mã hàng", "MSKH", "Part Number", "Đối tượng gửi dữ liệu","Nguồn dữ liệu",
    "Yêu cầu đặc biệt khi gửi dữ liệu", 'Gui_DL',
    "Nơi nhận dữ liệu", "DUNG LƯỢNG 1 LẦN GỬI"
]
import os

def find_project_root(current_path, marker_file_or_dir=".git"):
    """
    Tìm thư mục gốc của dự án bằng cách đi lên các cấp thư mục
    cho đến khi tìm thấy một file/thư mục đánh dấu.
    """
    current_dir = current_path
    while not os.path.exists(os.path.join(current_dir, marker_file_or_dir)):
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir: # Đã đến thư mục gốc của hệ thống (ví dụ: C:\)
            raise FileNotFoundError(f"Không tìm thấy thư mục gốc dự án với dấu hiệu '{marker_file_or_dir}'")
        current_dir = parent_dir
    return current_dir

def open_data_window(parent):
    global csv_file_path, data_df, original_df, filters
    data_dir = os.path.join(os.getcwd(), "DATASETC")
    # print("Data dir là :",data_dir)
    os.makedirs(data_dir, exist_ok=True)
    csv_file_path = os.path.join(data_dir, "data.csv")
    
    if os.path.exists(csv_file_path):
        encodings = ['utf-8-sig', 'utf-8', 'latin1', 'iso-8859-1', 'utf-16']
        for encoding in encodings:
            try:
                data_df = pd.read_csv(csv_file_path, encoding=encoding)
                col_mapping = {
                    'Gửi Lot DAI DIEN: "DD"\nGửi TOAN BO Lot: "TB"': "Gui_DL",
                    'Gửi Lot DAI DIEN: "DD" Gửi TOAN BO Lot: "TB"': "Gui_DL",
                    "Gửi Lot DAI DIEN: 'DD' Gửi TOAN BO Lot: 'TB'": "Gui_DL",
                    "Gửi Lot DAI DIEN: 'DD'  Gửi TOAN BO Lot: 'TB'": "Gui_DL",
                    "Gửi Lot DAI DIEN: 'DD'\nGửi TOAN BO Lot: 'TB'": "Gui_DL"
                }
                data_df = data_df.rename(columns=col_mapping)
                break
            except Exception as e:
                print(f"Lỗi với encoding {encoding} khi đọc data.csv: {e}")
                continue
        else:
            messagebox.showerror("Lỗi", f"Không thể đọc file data.csv với bất kỳ encoding nào.")
            data_df = pd.DataFrame()
    else:
        data_df = pd.DataFrame()
        data_df.to_csv(csv_file_path, index=False, encoding='utf-8-sig')
    
    
    
    original_df = data_df.copy()
    filters = {}

    data_window = tk.Toplevel(parent)
    data_window.title("Data")
    data_window.geometry("1200x600")
    data_window.configure(bg="#e8ecef")
    data_window.lift()
    data_window.grab_set()

    frame_table = tk.Frame(data_window, bg="#e8ecef")
    frame_table.pack(pady=10, fill="both", expand=True)

    columns = list(data_df.columns) if not data_df.empty else []
    tree = ttk.Treeview(frame_table, columns=columns, show="headings", height=20)
    for col in columns:
        tree.heading(col, text=col, command=lambda c=col: show_filter_entry(c, tree, data_window))
        tree.column(col, width=150, anchor="center")
    
    scrollbar_y = ttk.Scrollbar(frame_table, orient="vertical", command=tree.yview)
    scrollbar_y.pack(side=tk.RIGHT, fill="y")
    tree.configure(yscrollcommand=scrollbar_y.set)
    
    scrollbar_x = ttk.Scrollbar(frame_table, orient="horizontal", command=tree.xview)
    scrollbar_x.pack(side=tk.BOTTOM, fill="x")
    tree.configure(xscrollcommand=scrollbar_x.set)
    
    tree.pack(fill="both", expand=True)

    # Bind double-click để sửa dữ liệu
    tree.bind("<Double-1>", lambda event: modify_data(data_window, tree))

    frame_buttons = tk.Frame(data_window, bg="#e8ecef")
    frame_buttons.pack(pady=10)

    def update_table(df, tree_widget=tree):
        tree_widget["columns"] = list(df.columns) if not df.empty else []
        tree_widget.delete(*tree_widget.get_children())
        for col in (df.columns if not df.empty else []):
            tree_widget.heading(col, text=col, command=lambda c=col: show_filter_entry(c, tree_widget, data_window))
            tree_widget.column(col, width=150, anchor="center")
        for _, row in df.iterrows():
            tree_widget.insert("", "end", values=tuple(row))
        for col in (df.columns if not df.empty else []):
            if col in filters and filters[col]:
                tree_widget.heading(col, text=f"{col} (filter)")
            else:
                tree_widget.heading(col, text=col)

    def save_to_csv():
        try:
            # Đảm bảo thư mục tồn tại
            os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)
            # Lưu file
            if not data_df.empty:
                data_df.to_csv(csv_file_path, index=False, encoding='utf-8-sig')
            else:
                pd.DataFrame(columns=REQUIRED_COLUMNS).to_csv(csv_file_path, index=False, encoding='utf-8-sig')
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu file: {str(e)}")

    def load_from_csv():
        global csv_file_path, data_df, original_df
        if os.path.exists(csv_file_path):
            encodings = ['utf-8-sig', 'utf-8', 'latin1', 'iso-8859-1', 'utf-16']
            for encoding in encodings:
                try:
                    data_df = pd.read_csv(csv_file_path, encoding=encoding)
                    break
                except Exception as e:
                    print(f"Lỗi với encoding {encoding} khi đọc data.csv: {e}")
                    continue
            else:
                messagebox.showerror("Lỗi", f"Không thể đọc file data.csv với bất kỳ encoding nào.")
                return
            original_df = data_df.copy()
            update_table(data_df)

    def add_data():
        add_window = tk.Toplevel(data_window)
        add_window.title("Add Data")
        add_window.configure(bg="#e8ecef")
        add_window.lift()
        add_window.grab_set()

        entries = {}
        if data_df.empty and not data_df.columns.any():
            tk.Label(add_window, text="Chưa có cột nào trong data.csv!", font=("Helvetica", 12), bg="#e8ecef").pack(pady=10)
            tk.Label(add_window, text="Vui lòng sử dụng 'Update CSV Link' để thêm file có cột.", font=("Helvetica", 12), bg="#e8ecef").pack(pady=10)
            tk.Button(add_window, text="Đóng", command=add_window.destroy, font=("Helvetica", 12, "bold"), bg="#e74c3c", fg="white", padx=20, pady=10).pack(pady=20)
            return

        # Tính số cột và dòng
        num_cols = len(data_df.columns)
        max_rows = min(15, num_cols)  # Giới hạn tối đa 15 dòng mỗi cột
        num_grid_cols = max(1, math.ceil(num_cols / max_rows))
        rows_per_col = min(max_rows, math.ceil(num_cols / num_grid_cols))

        # Tạo frame chính với thanh cuộn
        main_frame = tk.Frame(add_window, bg="#e8ecef")
        main_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(main_frame, bg="#e8ecef")
        scrollbar_y = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(main_frame, orient="horizontal", command=canvas.xview)
        scrollable_frame = tk.Frame(canvas, bg="#e8ecef")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # Sắp xếp layout với grid
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # Chia label thành các cột
        columns_to_show = [col for col in REQUIRED_COLUMNS if col in data_df.columns]
        for idx, col in enumerate(columns_to_show):
            grid_col = idx // rows_per_col
            grid_row = idx % rows_per_col
            tk.Label(scrollable_frame, text=f"{col}:", font=("Helvetica", 12), bg="#e8ecef").grid(row=grid_row, column=grid_col*3, padx=10, pady=5, sticky="e")
            entry = tk.Entry(scrollable_frame, width=30, font=("Helvetica", 12))
            entry.grid(row=grid_row, column=grid_col*3+1, padx=10, pady=5)
            entries[col] = entry
            if col in columns_to_show:
                tk.Label(scrollable_frame, text="*", fg="red", bg="#e8ecef").grid(row=grid_row, column=grid_col*3+2, sticky="w")

        # Tính kích thước cửa sổ
        window_width = min(400 + 300 * (num_grid_cols ), 1000)
        window_height = min(100 + 60 * rows_per_col, 600)
        add_window.geometry(f"{window_width}x{window_height}")

        def save_data():
            global data_df, original_df
            # Chỉ lấy các cột có trong entries, nếu thiếu thì để ""
            new_data = {col: entries[col].get() if col in entries else "" for col in data_df.columns}
            columns_to_show = [col for col in REQUIRED_COLUMNS if col in data_df.columns]
            required_data = {k: new_data[k] for k in columns_to_show if k in new_data}
            missing_fields = [col for col, val in required_data.items() if not val]
            if missing_fields:
                messagebox.showwarning(
                    "Cảnh báo",
                    f"Vui lòng điền đầy đủ các trường bắt buộc!\nThiếu: {', '.join(missing_fields)}"
                )
                return
            data_df = pd.concat([data_df, pd.DataFrame([new_data])], ignore_index=True)
            original_df = data_df.copy()
            save_to_csv()
            update_table(data_df)
            add_window.destroy()

        tk.Button(scrollable_frame, text="Save", command=save_data, font=("Helvetica", 12, "bold"), bg="#3498db", fg="white", padx=20, pady=10).grid(row=rows_per_col, column=0, columnspan=num_grid_cols*3, pady=20)

    def modify_data(parent_window, tree_widget):
        selected = tree_widget.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một dòng để sửa!")
            return
        item = selected[0]
        values = tree_widget.item(item, "values")
        # Xác định các cột khóa (ví dụ: "SS", "Mã hàng", "MSKH")
        mask = (
            (data_df["SS"].astype(str) == values[data_df.columns.get_loc("SS")]) &
            (data_df["Mã hàng"].astype(str) == values[data_df.columns.get_loc("Mã hàng")]) &
            (data_df["MSKH"].astype(str) == values[data_df.columns.get_loc("MSKH")])
        )
        idx_list = data_df[mask].index.tolist()
        if not idx_list:
            messagebox.showwarning("Cảnh báo", "Không tìm thấy dòng dữ liệu để sửa!")
            return
        index = idx_list[0]
        if index >= len(data_df):
            messagebox.showwarning("Cảnh báo", "Dữ liệu không hợp lệ!")
            return

        modify_window = tk.Toplevel(parent_window)
        modify_window.title("Modify Data")
        modify_window.configure(bg="#e8ecef")
        modify_window.lift()
        modify_window.grab_set()

        entries = {}
        # Tính số cột và dòng
        num_cols = len(data_df.columns)
        max_rows = min(15, num_cols)
        num_grid_cols = max(1, math.ceil(num_cols / max_rows))
        rows_per_col = min(max_rows, math.ceil(num_cols / num_grid_cols))

        # Tạo frame chính với thanh cuộn
        main_frame = tk.Frame(modify_window, bg="#e8ecef")
        main_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(main_frame, bg="#e8ecef")
        scrollbar_y = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(main_frame, orient="horizontal", command=canvas.xview)
        scrollable_frame = tk.Frame(canvas, bg="#e8ecef")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # Sắp xếp layout với grid
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(0, weight=1)

        # Điền dữ liệu hiện tại
        columns_to_show = [col for col in SHOW_COLUMNS if col in data_df.columns]
        current_data = data_df.iloc[index][columns_to_show].to_dict()
        
        for idx, col in enumerate(columns_to_show):
            grid_col = idx // rows_per_col
            grid_row = idx % rows_per_col
            tk.Label(scrollable_frame, text=f"{col}:", font=("Helvetica", 12), bg="#e8ecef").grid(row=grid_row, column=grid_col*3, padx=10, pady=5, sticky="e")
            entry = tk.Entry(scrollable_frame, width=30, font=("Helvetica", 12))
            entry.grid(row=grid_row, column=grid_col*3+1, padx=10, pady=5)
            entry.insert(0, str(current_data.get(col, "")))
            entries[col] = entry
            if col in columns_to_show:
                tk.Label(scrollable_frame, text="*", fg="red", bg="#e8ecef").grid(row=grid_row, column=grid_col*3+2, sticky="w")

        # Tính kích thước cửa sổ
        window_width = min(400 + 300 * (num_grid_cols ), 1000)
        window_height = min(100 + 60 * rows_per_col, 600)
        modify_window.geometry(f"{window_width}x{window_height}")

        def save_modified_data():
            global data_df, original_df
            modified_data = {col: entries[col].get() for col in data_df.columns}
            required_data = {k: modified_data[k] for k in columns_to_show if k in modified_data}
            if columns_to_show and not all(required_data.values()):
                messagebox.showwarning("Cảnh báo", "Vui lòng điền đầy đủ các trường bắt buộc (SS, Mã hàng, MSKH nếu có)!")
                return
            data_df.iloc[index] = pd.Series(modified_data)
            original_df = data_df.copy()
            save_to_csv()
            update_table(data_df)
            modify_window.destroy()

        tk.Button(scrollable_frame, text="Save", command=save_modified_data, font=("Helvetica", 12, "bold"), bg="#3498db", fg="white", padx=20, pady=10).grid(row=rows_per_col, column=0, columnspan=num_grid_cols*3, pady=20)

    def delete_data():
        delete_menu = tk.Menu(data_window, tearoff=0)
        delete_menu.add_command(label="Xóa dữ liệu đang chọn", command=delete_selected_data)
        delete_menu.add_command(label="Xóa toàn bộ dữ liệu", command=delete_all_data)
        delete_button = frame_buttons.winfo_children()[1]
        delete_menu.post(
            delete_button.winfo_rootx(),
            delete_button.winfo_rooty() + delete_button.winfo_height()
        )

    def delete_selected_data():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn ít nhất một dòng để xóa!")
            return
        global data_df, original_df
        indices = [int(tree.index(item)) for item in selected]
        data_df = data_df.drop(indices).reset_index(drop=True)
        original_df = data_df.copy()
        save_to_csv()
        update_table(data_df)
        messagebox.showinfo("Thông báo", "Đã xóa các dòng dữ liệu được chọn!")

    def delete_all_data():
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa toàn bộ dữ liệu trong data.csv?"):
            global data_df, original_df
            data_df = pd.DataFrame(columns=data_df.columns) if not data_df.empty else pd.DataFrame()
            original_df = data_df.copy()
            save_to_csv()
            update_table(data_df)
            messagebox.showinfo("Thông báo", "Đã xóa toàn bộ dữ liệu!")

    def update_csv_link():
        global csv_file_path, data_df, original_df
        file_path = filedialog.askopenfilename(title="Chọn file CSV", filetypes=[("CSV files", "*.csv")])
        if file_path:
            try:
                # Đọc file với các encoding khác nhau
                new_df = None
                encodings = ['utf-8-sig', 'utf-8', 'latin1', 'iso-8859-1', 'utf-16']
                for encoding in encodings:
                    try:
                        new_df = pd.read_csv(file_path, encoding=encoding)
                        break
                    except Exception as e:
                        continue

                if new_df is None:
                    messagebox.showerror("Lỗi", "Không thể đọc file CSV với bất kỳ encoding nào")
                    return

                # Chỉ lấy các cột cần thiết nếu có
                available_columns = [col for col in REQUIRED_COLUMNS if col in new_df.columns]
                if not available_columns:
                    messagebox.showwarning("Cảnh báo", "File không chứa các cột cần thiết!")
                    return

                new_df = new_df[available_columns]

                # Cập nhật DataFrame
                if not data_df.empty:
                    data_df = data_df.reindex(columns=available_columns, fill_value="")
                    data_df = pd.concat([data_df, new_df], ignore_index=True)
                else:
                    data_df = new_df

                # Xóa dòng trùng lặp dựa trên SS, Mã hàng, MSKH
                if all(col in available_columns for col in ["SS", "Mã hàng", "MSKH"]):
                    data_df = data_df.drop_duplicates(subset=["SS", "Mã hàng", "MSKH"], keep="last")
                    
                print(data_df.head())            
                
                
                if len(data_df.columns) > 7:
                    old_column_name = data_df.columns[7]
                    data_df = data_df.rename(columns={old_column_name: "Gui_DL"})
                    print(f"Đã đổi tên cột thứ 8 từ '{old_column_name}' thành 'Gui_DL' trong new_df")
                else:
                    print("File CSV có ít hơn 8 cột, không thể đổi tên cột thứ 8")

                
                print(data_df.head())
               
                save_to_csv()
                update_table(data_df)
                messagebox.showinfo("Thành công", f"Đã cập nhật dữ liệu từ file: {file_path}")

            except Exception as e:
                messagebox.showerror("Lỗi", f"Lỗi khi cập nhật dữ liệu: {str(e)}")


    def show_filter_entry(column, tree_widget, parent_window):
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
            global data_df, original_df, filters
            value = entry.get().strip()
            if value:
                filters[column] = value
            else:
                filters.pop(column, None)
            filtered_df = original_df.copy()
            for col, val in filters.items():
                filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(val, case=False, na=False)]
            data_df = filtered_df
            update_table(data_df)
            filter_window.destroy()

        tk.Button(filter_window, text="Apply", command=apply_filter, font=("Helvetica", 12, "bold"), bg="#3498db", fg="white", padx=20, pady=10).pack(pady=10)

    def clear_filter():
        global data_df, original_df, filters
        filters.clear()
        data_df = original_df.copy()
        update_table(data_df)

    tk.Button(frame_buttons, text="Add Data", command=add_data, font=("Helvetica", 12, "bold"), bg="#27ae60", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_buttons, text="Delete Data", command=delete_data, font=("Helvetica", 12, "bold"), bg="#e74c3c", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_buttons, text="Update CSV Link", command=update_csv_link, font=("Helvetica", 12, "bold"), bg="#f39c12", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_buttons, text="Clear Filter", command=clear_filter, font=("Helvetica", 12, "bold"), bg="#3498db", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)

    update_table(data_df)

    def on_data_close():
        global csv_file_path, original_df
        if not original_df.empty:
            original_df.to_csv(csv_file_path, index=False, encoding='utf-8-sig')
        data_window.destroy()

    data_window.protocol("WM_DELETE_WINDOW", on_data_close)