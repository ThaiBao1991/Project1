import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import os

def open_data_window(parent):
    global csv_file_path, data_df, original_df, filters
    # File CSV mặc định
    csv_file_path = "data.csv"
    columns = ["SS", "Mã hàng", "MSKH", "Tên khách hàng", "Gửi Lot", "Gửi dữ liệu", "Nội dung gửi email", "Địa chỉ gửi email"]
    
    # Kiểm tra và tải hoặc tạo file data.csv
    if os.path.exists(csv_file_path):
        data_df = pd.read_csv(csv_file_path, encoding='utf-8-sig')
        data_df = data_df.reindex(columns=columns, fill_value="")
    else:
        data_df = pd.DataFrame(columns=columns)
        data_df.to_csv(csv_file_path, index=False, encoding='utf-8-sig')  # Tạo file mới nếu chưa có
    original_df = data_df.copy()  # Lưu dữ liệu gốc
    filters = {}  # Lưu các bộ lọc theo cột

    data_window = tk.Toplevel(parent)
    data_window.title("Data")
    data_window.geometry("1200x600")
    data_window.configure(bg="#e8ecef")
    
    # Đưa cửa sổ Data lên trên cùng và chiếm toàn bộ tương tác
    data_window.lift()  # Đưa cửa sổ lên trên
    data_window.grab_set()  # Ngăn tương tác với cửa sổ khác

    # Frame cho bảng dữ liệu
    frame_table = tk.Frame(data_window, bg="#e8ecef")
    frame_table.pack(pady=10, fill="both", expand=True)

    # Tạo Treeview để hiển thị bảng
    tree = ttk.Treeview(frame_table, columns=list(data_df.columns), show="headings", height=20)
    for col in data_df.columns:
        tree.heading(col, text=col, command=lambda c=col: show_filter_entry(c, tree, data_window))
        tree.column(col, width=150, anchor="center")
    tree.pack(side=tk.LEFT, fill="both", expand=True)

    # Thanh cuộn
    scrollbar = ttk.Scrollbar(frame_table, orient="vertical", command=tree.yview)
    scrollbar.pack(side=tk.RIGHT, fill="y")
    tree.configure(yscrollcommand=scrollbar.set)

    # Frame cho các nút
    frame_buttons = tk.Frame(data_window, bg="#e8ecef")
    frame_buttons.pack(pady=10)

    # Hàm cập nhật bảng và tiêu đề cột
    def update_table(df):
        tree.delete(*tree.get_children())
        for _, row in df.iterrows():
            tree.insert("", "end", values=tuple(row))
        # Cập nhật tiêu đề cột với biểu tượng (filter)
        for col in df.columns:
            if col in filters and filters[col]:
                tree.heading(col, text=f"{col} (filter)")
            else:
                tree.heading(col, text=col)

    # Hàm lưu dữ liệu vào file CSV
    def save_to_csv():
        global csv_file_path, data_df
        if not data_df.empty:
            data_df.to_csv(csv_file_path, index=False, encoding='utf-8-sig')

    # Hàm tải lại dữ liệu từ data.csv
    def load_from_csv():
        global csv_file_path, data_df, original_df
        if os.path.exists(csv_file_path):
            data_df = pd.read_csv(csv_file_path, encoding='utf-8-sig')
            data_df = data_df.reindex(columns=columns, fill_value="")
            original_df = data_df.copy()
            update_table(data_df)

    # Hàm thêm dữ liệu
    def add_data():
        add_window = tk.Toplevel(data_window)
        add_window.title("Add Data")
        add_window.geometry("400x500")
        add_window.configure(bg="#e8ecef")
        add_window.lift()  # Đưa cửa sổ Add Data lên trên
        add_window.grab_set()  # Ngăn tương tác với cửa sổ khác

        entries = {}
        for i, col in enumerate(data_df.columns):
            tk.Label(add_window, text=f"{col}:", font=("Helvetica", 12), bg="#e8ecef").grid(row=i, column=0, padx=10, pady=10, sticky="e")
            entry = tk.Entry(add_window, width=30, font=("Helvetica", 12))
            entry.grid(row=i, column=1, padx=10, pady=10)
            entries[col] = entry

        def save_data():
            global data_df, original_df
            new_data = {col: entries[col].get() for col in data_df.columns}
            if all(new_data.values()):
                data_df = pd.concat([data_df, pd.DataFrame([new_data])], ignore_index=True)
                original_df = data_df.copy()
                save_to_csv()  # Lưu ngay sau khi thêm
                update_table(data_df)
                add_window.destroy()
            else:
                messagebox.showwarning("Cảnh báo", "Vui lòng điền đầy đủ thông tin!")

        tk.Button(add_window, text="Save", command=save_data, font=("Helvetica", 12, "bold"), bg="#3498db", fg="white", padx=20, pady=10).grid(row=len(data_df.columns), column=0, columnspan=2, pady=20)

    # Hàm xóa dữ liệu
    def delete_data():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một dòng để xóa!")
            return
        global data_df, original_df
        index = int(tree.index(selected[0]))
        data_df = data_df.drop(index).reset_index(drop=True)
        original_df = data_df.copy()
        save_to_csv()  # Lưu ngay sau khi xóa
        update_table(data_df)

    # Hàm cập nhật file CSV
    def update_csv_link():
        global csv_file_path, data_df, original_df
        file_path = filedialog.askopenfilename(title="Chọn file CSV", filetypes=[("CSV files", "*.csv")])
        if file_path:
            new_df = pd.read_csv(file_path, encoding='utf-8-sig')
            new_df = new_df.reindex(columns=data_df.columns, fill_value="")
            data_df = pd.concat([data_df, new_df]).drop_duplicates(subset=["SS", "Mã hàng", "MSKH"], keep="last").reset_index(drop=True)
            original_df = data_df.copy()
            save_to_csv()  # Lưu vào data.csv ngay sau khi gộp
            load_from_csv()  # Tải lại từ data.csv để hiển thị
            messagebox.showinfo("Thông báo", f"Đã cập nhật dữ liệu từ file: {file_path} vào data.csv")

    # Hàm hiển thị ô nhập liệu để lọc
    def show_filter_entry(column, tree_widget, parent_window):
        filter_window = tk.Toplevel(parent_window)
        filter_window.title(f"Filter {column}")
        filter_window.geometry("300x150")
        filter_window.configure(bg="#e8ecef")
        filter_window.lift()  # Đưa cửa sổ Filter lên trên
        filter_window.grab_set()  # Ngăn tương tác với cửa sổ khác

        tk.Label(filter_window, text=f"Nhập giá trị lọc cho {column}:", font=("Helvetica", 12), bg="#e8ecef").pack(pady=10)
        entry = tk.Entry(filter_window, width=30, font=("Helvetica", 12))
        entry.pack(pady=10)
        entry.insert(0, filters.get(column, ""))  # Hiển thị giá trị lọc hiện tại nếu có

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

    # Hàm xóa bộ lọc
    def clear_filter():
        global data_df, original_df, filters
        filters.clear()
        data_df = original_df.copy()
        update_table(data_df)

    # Các nút trong frame_buttons
    tk.Button(frame_buttons, text="Add Data", command=add_data, font=("Helvetica", 12, "bold"), bg="#27ae60", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_buttons, text="Delete Data", command=delete_data, font=("Helvetica", 12, "bold"), bg="#e74c3c", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_buttons, text="Update CSV Link", command=update_csv_link, font=("Helvetica", 12, "bold"), bg="#f39c12", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_buttons, text="Clear Filter", command=clear_filter, font=("Helvetica", 12, "bold"), bg="#3498db", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)

    # Cập nhật bảng lần đầu
    update_table(data_df)

    # Hàm lưu dữ liệu khi đóng cửa sổ (vẫn giữ để an toàn)
    def on_data_close():
        global csv_file_path, data_df
        if not data_df.empty:
            data_df.to_csv(csv_file_path, index=False, encoding='utf-8-sig')
        data_window.destroy()

    data_window.protocol("WM_DELETE_WINDOW", on_data_close)