import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import os
import json
import re


EMAIL_COLUMNS = [
    "MÃ HÀNG", "Tên KH", "CategoryEmail", "Mã số KH", "Địa chỉ gửi mail", "Nội dung gửi mail"
]

EMAIL_DIR = os.path.join(os.getcwd(), "DATASETC", "Email")
EMAIL_CSV = os.path.join(EMAIL_DIR, "email.csv")
EMAIL_JSON = os.path.join(EMAIL_DIR, "email.json")

def open_email_window(parent):
    os.makedirs(EMAIL_DIR, exist_ok=True)
    if os.path.exists(EMAIL_CSV):
        try:
            df = pd.read_csv(EMAIL_CSV, encoding='utf-8-sig')
        except Exception:
            df = pd.DataFrame(columns=EMAIL_COLUMNS)
    else:
        df = pd.DataFrame(columns=EMAIL_COLUMNS)
        df.to_csv(EMAIL_CSV, index=False, encoding='utf-8-sig')

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

    def update_table():
        tree.delete(*tree.get_children())
        for _, row in df.iterrows():
            tree.insert("", "end", values=tuple(row[col] if col in row else "" for col in columns))

    def save_to_csv_and_json():
        df.to_csv(EMAIL_CSV, index=False, encoding='utf-8-sig')
        # Sinh file JSON
        json_dict = {}
        for _, row in df.iterrows():
            ten_kh = str(row.get("Tên KH", "")).strip()            
            # Loại bỏ các ký tự xuống dòng
            ten_kh = ten_kh.replace("\n", "").replace("\r", "")
            # Loại bỏ các dấu cách đầu tiên trước khi gặp chữ cái hoặc số
            ten_kh = re.sub(r'^\s+', '', ten_kh)

            ma_hang = str(row.get("MÃ HÀNG", "")).strip()
            category = str(row.get("CategoryEmail", "")).strip()
            ma_so_kh = str(row.get("Mã số KH", "")).strip()
            dia_chi = str(row.get("Địa chỉ gửi mail", "")).strip()
            noi_dung = str(row.get("Nội dung gửi mail", "")).strip()
            print(ma_hang,ten_kh)
            if not ten_kh:
                continue
            if not ma_hang or ma_hang=="nan":
                ma_list = ["ALL"]
            else:
                ma_list = [m.strip() for m in ma_hang.split("&") if m.strip()]
                ma_list = ','.join(ma_list)
            
            key = f"{ten_kh}|{category}"
            json_dict[key] = {
                "Tên KH": ten_kh,
                "MÃ HÀNG": ma_list,
                "CategoryEmail": category,
                "Mã số KH": ma_so_kh,
                "Địa chỉ gửi mail": dia_chi,
                "Nội dung gửi mail": noi_dung
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
        if file_path:
            try:
                new_df = pd.read_csv(file_path, encoding='utf-8-sig')
                # Chỉ lấy các cột cần thiết
                available_cols = [col for col in EMAIL_COLUMNS if col in new_df.columns]
                if not available_cols:
                    messagebox.showwarning("Cảnh báo", "File không chứa các cột cần thiết!")
                    return
                new_df = new_df[available_cols]
                nonlocal df
                df = pd.concat([df, new_df], ignore_index=True)
                df = df.drop_duplicates(subset=["Tên KH", "MÃ HÀNG", "Địa chỉ gửi mail"], keep="last")
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