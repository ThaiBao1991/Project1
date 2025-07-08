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
    # Đọc dữ liệu từ CSV
    if os.path.exists(EMAIL_CSV):
        try:
            df = pd.read_csv(EMAIL_CSV, encoding='utf-8-sig')
        except Exception as e:
            print(f"Lỗi khi đọc file CSV: {e}")
            df = pd.DataFrame(columns=EMAIL_COLUMNS)
    else:
        df = pd.DataFrame(columns=EMAIL_COLUMNS)

    # --- Lấy bảng MB duy nhất ---
    data_month_csv = os.path.join(os.getcwd(), "DATASETC", "DATA_customer_time", "data_month.csv")
    mb_map = {}
    if os.path.exists(data_month_csv):
        try:
            data_month_df = pd.read_csv(data_month_csv, encoding='utf-8-sig')
            # Chỉ lấy 2 cột, loại trùng "Nơi nhận dữ liệu"
            data_month_df = data_month_df[['Nơi nhận dữ liệu', 'DUNG LƯỢNG 1 LẦN GỬI']].drop_duplicates(subset=['Nơi nhận dữ liệu'], keep='first')
            # Tạo dict ánh xạ: nơi nhận dữ liệu -> MB
            mb_map = dict(zip(data_month_df['Nơi nhận dữ liệu'], data_month_df['DUNG LƯỢNG 1 LẦN GỬI']))
        except Exception as e:
            print(f"Lỗi khi xử lý file MB: {e}")

    # Xóa cột Max MB cũ nếu có
    if "Max MB" in df.columns:
        df = df.drop(columns=["Max MB"])
    df = df.merge(
        data_month_df[['Nơi nhận dữ liệu', 'DUNG LƯỢNG 1 LẦN GỬI']].drop_duplicates(subset=['Nơi nhận dữ liệu'], keep='first'),
        left_on='Tên KH',
        right_on='Nơi nhận dữ liệu',
        how='left'
    )
    df.rename(columns={'DUNG LƯỢNG 1 LẦN GỬI': 'Max MB'}, inplace=True)
    if 'Nơi nhận dữ liệu' in df.columns:
        df = df.drop(columns=['Nơi nhận dữ liệu'])
    # Nếu vẫn thiếu cột Max MB (do không khớp), thêm vào cho đủ
    if "Max MB" not in df.columns:
        df["Max MB"] = ""
    email_window = tk.Toplevel(parent)
    email_window.title("Quản lý Email Khách Hàng")
    email_window.geometry("1100x600")
    email_window.configure(bg="#e8ecef")
    email_window.lift()
    email_window.grab_set()

    frame_table = tk.Frame(email_window, bg="#e8ecef")
    frame_table.pack(pady=10, fill="both", expand=True)

    columns = EMAIL_COLUMNS
    tree = ttk.Treeview(frame_table, columns=columns, show="headings", height=20)
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=180, anchor="center")
    tree.pack(fill="both", expand=True)

    def modify_email():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một dòng để sửa!")
            return
        index = int(tree.index(selected[0]))
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
            nonlocal df
            new_row = {col: entries[col].get() for col in EMAIL_COLUMNS}
            if not new_row["Tên KH"]:
                messagebox.showwarning("Cảnh báo", "Tên KH không được để trống!")
                return
            for col in EMAIL_COLUMNS:
                df.at[index, col] = new_row[col]
            save_to_csv_and_json()
            update_table()
            modify_win.destroy()

        tk.Button(modify_win, text="Lưu", command=save_modified, font=("Helvetica", 12, "bold"), bg="#27ae60", fg="white", padx=20, pady=10).grid(row=len(EMAIL_COLUMNS)+1, column=0, columnspan=2, pady=20)

    tree.bind("<Double-1>", lambda event: modify_email())

    def update_table():
        tree.delete(*tree.get_children())
        for _, row in df.iterrows():
            tree.insert("", "end", values=tuple(row[col] if col in row else "" for col in columns))

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
            update_table()
            add_win.destroy()

        tk.Button(add_win, text="Lưu", command=save_email, font=("Helvetica", 12, "bold"), bg="#27ae60", fg="white", padx=20, pady=10).grid(row=len(EMAIL_COLUMNS), column=0, columnspan=2, pady=20)

    def import_csv():
        file_path = filedialog.askopenfilename(title="Chọn file CSV", filetypes=[("CSV files", "*.csv")])
        data_month_csv = os.path.join(os.getcwd(), "DATASETC", "DATA_customer_time", "data_month.csv")
        data_month_df = pd.read_csv(data_month_csv, encoding='utf-8-sig')
        # Giữ lại dòng đầu tiên cho mỗi khách hàng (Nơi nhận dữ liệu)
        data_month_df = data_month_df.drop_duplicates(subset=['Nơi nhận dữ liệu'], keep='first')
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
                df = df.merge(
                    data_month_df[['Nơi nhận dữ liệu', 'DUNG LƯỢNG 1 LẦN GỬI']],
                    left_on='Tên KH',
                    right_on='Nơi nhận dữ liệu',
                    how='left'
                )
                df.rename(columns={'DUNG LƯỢNG 1 LẦN GỬI': 'Max MB'}, inplace=True)
                df.drop(columns=['Nơi nhận dữ liệu'], inplace=True)
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

    update_table()

    def on_close():
        save_to_csv_and_json()
        email_window.destroy()
    email_window.protocol("WM_DELETE_WINDOW", on_close)