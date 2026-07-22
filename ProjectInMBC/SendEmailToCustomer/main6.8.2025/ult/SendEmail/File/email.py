import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import os
import json
import re
import math


EMAIL_COLUMNS = [
    "MÃ HÀNG", "Tên KH", "CategoryEmail", "Mã số KH", "Địa chỉ gửi mail", "Nội dung gửi mail","Max MB"
]

EMAIL_DIR = os.path.join(os.getcwd(), "DATASETC", "Email")
EMAIL_CSV = os.path.join(EMAIL_DIR, "email.csv")
EMAIL_JSON = os.path.join(EMAIL_DIR, "email.json")

def open_email_window(parent):
    os.makedirs(EMAIL_DIR, exist_ok=True)
    filters = {}
    original_df = None
    # Đọc dữ liệu từ CSV
    if os.path.exists(EMAIL_CSV):
        try:
            df = pd.read_csv(EMAIL_CSV, encoding='utf-8-sig')
        except Exception as e:
            print(f"Lỗi khi đọc file CSV: {e}")
            df = pd.DataFrame(columns=EMAIL_COLUMNS)
    else:
        df = pd.DataFrame(columns=EMAIL_COLUMNS)

    email_window = tk.Toplevel(parent)
    email_window.title("Quản lý Email Khách Hàng")
    email_window.geometry("1100x600")
    email_window.configure(bg="#e8ecef")
    email_window.lift()
    email_window.grab_set()
    email_window.state('zoomed')# Thêm dòng này để phóng to cửa sổ

    frame_table = tk.Frame(email_window, bg="#e8ecef")
    frame_table.pack(pady=10, fill="both", expand=True)

    columns = EMAIL_COLUMNS
    tree = ttk.Treeview(frame_table, columns=columns, show="headings", height=20)
    for col in columns:
        tree.heading(col, text=col, command=lambda c=col: show_filter_entry(c, tree, email_window))
        tree.column(col, width=180, anchor="center")
    tree.pack(fill="both", expand=True)

    def modify_email():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một dòng để sửa!")
            return
        item = selected[0]
        values = tree.item(item, "values")
        # Tìm đúng index trong df dựa trên giá trị các cột (ưu tiên các cột khóa)
        # Ở đây dùng "Tên KH", "MÃ HÀNG", "CategoryEmail", "Địa chỉ gửi mail"
        mask = (
            (df["Tên KH"] == values[EMAIL_COLUMNS.index("Tên KH")]) &
            (df["MÃ HÀNG"].astype(str) == values[EMAIL_COLUMNS.index("MÃ HÀNG")]) &
            (df["CategoryEmail"].astype(str) == values[EMAIL_COLUMNS.index("CategoryEmail")]) &
            (df["Địa chỉ gửi mail"] == values[EMAIL_COLUMNS.index("Địa chỉ gửi mail")])
        )
        idx_list = df[mask].index.tolist()
        if not idx_list:
            messagebox.showwarning("Cảnh báo", "Không tìm thấy dòng dữ liệu để sửa!")
            return
        index = idx_list[0]
        
        if index >= len(df):
            messagebox.showwarning("Cảnh báo", "Dữ liệu không hợp lệ!")
            return

        modify_win = tk.Toplevel(email_window)
        modify_win.title("Sửa Email")
        modify_win.configure(bg="#e8ecef")
        entries = {}
        for idx, col in enumerate(EMAIL_COLUMNS):
            tk.Label(modify_win, text=f"{col}:", font=("Helvetica", 12), bg="#e8ecef").grid(row=idx, column=0, padx=10, pady=5, sticky="e")
            entry = tk.Entry(modify_win, width=50, font=("Helvetica", 12))
            entry.grid(row=idx, column=1, padx=10, pady=5)
            entry.insert(0, str(df.iloc[index].get(col, "")))
            entries[col] = entry

        def save_modified():
            nonlocal df,original_df
            new_row = {col: entries[col].get() for col in EMAIL_COLUMNS}
            if not new_row["Tên KH"]:
                messagebox.showwarning("Cảnh báo", "Tên KH không được để trống!")
                return
            for col in EMAIL_COLUMNS:
                df.at[index, col] = new_row[col]
            save_to_csv_and_json()
            original_df = df.copy()  # Cập nhật lại bản gốc
            update_table()
            modify_win.destroy()
            modify_win.destroy()

        tk.Button(modify_win, text="Lưu", command=save_modified, font=("Helvetica", 12, "bold"), bg="#27ae60", fg="white", padx=20, pady=10).grid(row=len(EMAIL_COLUMNS)+1, column=0, columnspan=2, pady=20)

    tree.bind("<Double-1>", lambda event: modify_email())

    def update_table(filtered_df=None):
        tree.delete(*tree.get_children())
        display_df = filtered_df if filtered_df is not None else df
        for _, row in display_df.iterrows():
            tree.insert("", "end", values=tuple(row[col] if col in row else "" for col in columns))
        # Đánh dấu cột đang filter
        for col in columns:
            if col in filters and filters[col]:
                tree.heading(col, text=f"{col} (filter)")
            else:
                tree.heading(col, text=col)
    def show_filter_entry(column, tree_widget, parent_window):
        nonlocal filters, original_df, df
        filter_window = tk.Toplevel(parent_window)
        filter_window.title(f"Filter {column}")
        filter_window.geometry("300x150")
        filter_window.configure(bg="#e8ecef")
        filter_window.transient(parent_window)
        filter_window.grab_set()

        tk.Label(filter_window, text=f"Nhập giá trị lọc cho {column}:", font=("Helvetica", 12), bg="#e8ecef").pack(pady=10)
        entry = tk.Entry(filter_window, width=30, font=("Helvetica", 12))
        entry.pack(pady=10)
        entry.insert(0, filters.get(column, ""))

        def apply_filter():
            value = entry.get().strip()
            nonlocal df, original_df, filters
            if original_df is None:
                original_df = df.copy()
            if value:
                filters[column] = value
            else:
                filters.pop(column, None)
            filtered_df = original_df.copy()
            for col, val in filters.items():
                filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(val, case=False, na=False)]
            update_table(filtered_df)
            filter_window.destroy()

        tk.Button(filter_window, text="Apply", command=apply_filter, font=("Helvetica", 12, "bold"), bg="#3498db", fg="white", padx=20, pady=10).pack(pady=10)
    def save_to_csv_and_json():
        df.to_csv(EMAIL_CSV, index=False, encoding='utf-8-sig')
        json_dict = {}
        for idx, row in df.iterrows():
            ten_kh = str(row.get("Tên KH", "")).strip()
            category = str(row.get("CategoryEmail", "")).strip()
            ma_so_kh = str(row.get("Mã số KH", "")).strip()
            dia_chi = str(row.get("Địa chỉ gửi mail", "")).strip()
            if not ten_kh or not category:
                continue
            key = f"{ten_kh}|{category}|{ma_so_kh}|{dia_chi}|{idx}"
            ma_hang = str(row.get("MÃ HÀNG", "")).strip()
            noi_dung = str(row.get("Nội dung gửi mail", "")).strip()
            max_mb = row.get("Max MB", "")
            # Chuyển max_mb về chuỗi hoặc số, không để NaN
            if pd.isna(max_mb) or (isinstance(max_mb, float) and math.isnan(max_mb)):
                max_mb = ""
            else:
                max_mb = str(max_mb)
            ma_list = ["ALL"]
            if ma_hang and ma_hang.lower() != "nan":
                ma_list = [m.strip() for m in str(ma_hang).split("&") if m.strip()]
            json_dict[key] = {
                "Tên KH": ten_kh,
                "MÃ HÀNG": ma_list,
                "CategoryEmail": category,
                "Mã số KH": ma_so_kh,
                "Địa chỉ gửi mail": dia_chi,
                "Nội dung gửi mail": noi_dung,
                "Max MB": max_mb
            }
        with open(EMAIL_JSON, "w", encoding="utf-8") as f:
            json.dump(json_dict, f, ensure_ascii=False, indent=2)

    def add_email():
        add_win = tk.Toplevel(email_window)
        add_win.title("Thêm Email")
        add_win.configure(bg="#e8ecef")
        entries = {}
        for idx, col in enumerate(EMAIL_COLUMNS):
            tk.Label(add_win, text=f"{col}:", font=("Helvetica", 12), bg="#e8ecef").grid(row=idx, column=0, padx=10, pady=5, sticky="e")
            entry = tk.Entry(add_win, width=50, font=("Helvetica", 12))
            entry.grid(row=idx, column=1, padx=10, pady=5)
            entries[col] = entry

        def save_email():
            nonlocal df
            new_row = {col: entries[col].get() for col in EMAIL_COLUMNS}
            if not new_row["Tên KH"]:
                messagebox.showwarning("Cảnh báo", "Tên KH không được để trống!")
                return
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_to_csv_and_json()
            original_df = df.copy()
            update_table()
            add_win.destroy()

        tk.Button(add_win, text="Lưu", command=save_email, font=("Helvetica", 12, "bold"), bg="#27ae60", fg="white", padx=20, pady=10).grid(row=len(EMAIL_COLUMNS), column=0, columnspan=2, pady=20)

    def import_csv():
        file_path = filedialog.askopenfilename(title="Chọn file CSV", filetypes=[("CSV files", "*.csv")])
        data_csv = os.path.join(os.getcwd(), "DATASETC", "data.csv")  # Sử dụng data.csv
        def normalize_name(name):
            if pd.isna(name):
                return ""
            return str(name).lstrip().replace('\n', '').replace('\r', '')

        if file_path:
            try:
                new_df = pd.read_csv(file_path, encoding='utf-8-sig')
                available_cols = [col for col in EMAIL_COLUMNS if col in new_df.columns]
                if not available_cols:
                    messagebox.showwarning("Cảnh báo", "File không chứa các cột cần thiết!")
                    return
                new_df = new_df[available_cols]
                nonlocal df
                df = pd.concat([df, new_df], ignore_index=True)
                df = df.drop_duplicates(subset=["Tên KH", "MÃ HÀNG", "Địa chỉ gửi mail"], keep="last")

                # Chỉ cập nhật Max MB nếu thiếu hoặc rỗng
                if os.path.exists(data_csv):
                    data_full_df = pd.read_csv(data_csv, encoding='utf-8-sig')
                    # Chuẩn hóa tên để ánh xạ chính xác
                    data_full_df['Nơi nhận dữ liệu chuẩn'] = data_full_df['Nơi nhận dữ liệu'].apply(normalize_name)
                    mb_map = dict(zip(data_full_df['Nơi nhận dữ liệu chuẩn'], data_full_df['DUNG LƯỢNG 1 LẦN GỬI']))
                    df['Tên KH chuẩn'] = df['Tên KH'].apply(normalize_name)
                    def get_mb(row):
                        if pd.isna(row.get("Max MB", "")) or str(row.get("Max MB", "")).strip() == "":
                            return mb_map.get(row["Tên KH chuẩn"], "")
                        return row["Max MB"]
                    df["Max MB"] = df.apply(get_mb, axis=1)
                    df = df.drop(columns=['Tên KH chuẩn'], errors='ignore')

                save_to_csv_and_json()
                update_table()
                messagebox.showinfo("Thành công", f"Đã nhập dữ liệu từ file: {file_path}")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Lỗi khi nhập dữ liệu: {str(e)}")

    def delete_selected():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn ít nhất một dòng để xóa!")
            return
        indices = [int(tree.index(item)) for item in selected]
        nonlocal df
        df = df.drop(indices).reset_index(drop=True)
        save_to_csv_and_json()
        update_table()
        messagebox.showinfo("Thông báo", "Đã xóa các dòng dữ liệu được chọn!")

    def delete_all():
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa toàn bộ dữ liệu email?"):
            nonlocal df
            df = pd.DataFrame(columns=EMAIL_COLUMNS)
            save_to_csv_and_json()
            update_table()
            messagebox.showinfo("Thông báo", "Đã xóa toàn bộ dữ liệu email!")

    frame_buttons = tk.Frame(email_window, bg="#e8ecef")
    frame_buttons.pack(pady=10)
    tk.Button(frame_buttons, text="Thêm Email", command=add_email, font=("Helvetica", 12, "bold"), bg="#27ae60", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_buttons, text="Nhập CSV", command=import_csv, font=("Helvetica", 12, "bold"), bg="#f39c12", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_buttons, text="Xóa đã chọn", command=delete_selected, font=("Helvetica", 12, "bold"), bg="#e74c3c", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_buttons, text="Xóa toàn bộ", command=delete_all, font=("Helvetica", 12, "bold"), bg="#e74c3c", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_buttons, text="Clear Filter", command=lambda: clear_filter(), font=("Helvetica", 12, "bold"), bg="#3498db", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)
    update_table()
    def clear_filter():
        nonlocal filters, original_df, df
        filters.clear()
        if original_df is not None:
            update_table(original_df)
        else:
            update_table(df)
    def on_close():
        save_to_csv_and_json()
        email_window.destroy()
    email_window.protocol("WM_DELETE_WINDOW", on_close)