import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import os
import pandas as pd
import calendar
import datetime

CHECK_DIR = os.path.join(os.getcwd(), "DATASETC", "dataMontlydata", "Check")
os.makedirs(CHECK_DIR, exist_ok=True)
CHECK_CSV = os.path.join(CHECK_DIR, "DataMontlyCheck.csv")
DATA_CSV = os.path.join(os.getcwd(), "DATASETC", "dataMontlydata", "dataMontly.csv")
DISPLAY_COLUMNS = ["Chủng loại", "Mã hàng", "Khách hàng", "Link", "Status"]

def update_check_data():
    # Xóa file cũ nếu có
    if os.path.exists(CHECK_CSV):
        os.remove(CHECK_CSV)
    # Đọc dataMontly.csv
    if os.path.exists(DATA_CSV):
        df = pd.read_csv(DATA_CSV, encoding="utf-8-sig")
        # Thêm cột Link, Status nếu chưa có
        if "Link" not in df.columns:
            df["Link"] = ""
        if "Status" not in df.columns:
            df["Status"] = ""
        df = df[["Chủng loại", "Mã hàng", "Khách hàng", "Link", "Status"]]
        df.to_csv(CHECK_CSV, index=False, encoding="utf-8-sig")
    else:
        df = pd.DataFrame(columns=DISPLAY_COLUMNS)
        df.to_csv(CHECK_CSV, index=False, encoding="utf-8-sig")

def load_check_data():
    if os.path.exists(CHECK_CSV):
        try:
            return pd.read_csv(CHECK_CSV, encoding="utf-8-sig")
        except Exception:
            return pd.DataFrame(columns=DISPLAY_COLUMNS)
    return pd.DataFrame(columns=DISPLAY_COLUMNS)

def save_check_data(df):
    df.to_csv(CHECK_CSV, index=False, encoding="utf-8-sig")

def open_gui_monthly_data(root, parent_window=None):
    window = tk.Toplevel(root)
    window.title("Gửi Monthly Data")
    window.geometry("1200x700")
    window.configure(bg="#e8ecef")
    window.lift()
    window.grab_set()
    window.focus_force()
    if parent_window:
        parent_window.withdraw()  # Ẩn cửa sổ gốc
        def on_close():
            parent_window.deiconify()
            window.destroy()
        window.protocol("WM_DELETE_WINDOW", on_close)
    # ==== Khu vực chọn file KJS và chọn tháng ====
    frame_top = tk.Frame(window, bg="#e8ecef")
    frame_top.pack(pady=10, fill="x")

    # Chọn file KJS
    tk.Label(frame_top, text="Chọn file KJS:", font=("Helvetica", 12), bg="#e8ecef").pack(side=tk.LEFT, padx=(10,0))
    entry_kjs = tk.Entry(frame_top, width=40, font=("Helvetica", 12))
    entry_kjs.pack(side=tk.LEFT, padx=5)
    def select_kjs_file():
        path = filedialog.askopenfilename(title="Chọn file KJS", filetypes=[("Excel/CSV", "*.xlsx *.xls *.csv"), ("All files", "*.*")])
        if path:
            entry_kjs.delete(0, tk.END)
            entry_kjs.insert(0, path)
    tk.Button(frame_top, text="Chọn", command=select_kjs_file, font=("Helvetica", 11, "bold"), bg="#3498db", fg="white", padx=10).pack(side=tk.LEFT, padx=5)

    # Chọn tháng
    tk.Label(frame_top, text="Chọn tháng:", font=("Helvetica", 12), bg="#e8ecef").pack(side=tk.LEFT, padx=(30,0))
    month_var = tk.StringVar()
    def pick_month():
        top = tk.Toplevel(window)
        top.title("Chọn tháng")
        top.geometry("300x120")
        top.configure(bg="#e8ecef")

        # Chọn tháng
        tk.Label(top, text="Tháng:", font=("Helvetica", 12), bg="#e8ecef").pack(pady=5)
        month_cb = ttk.Combobox(top, values=[f"{i:02d}" for i in range(1, 13)], width=5, font=("Helvetica", 12), state="readonly")
        month_cb.pack()
        month_cb.set(datetime.datetime.now().strftime("%m"))

        # Chọn năm
        tk.Label(top, text="Năm:", font=("Helvetica", 12), bg="#e8ecef").pack(pady=5)
        year_cb = ttk.Combobox(top, values=[str(y) for y in range(datetime.datetime.now().year-3, datetime.datetime.now().year+4)], width=7, font=("Helvetica", 12), state="readonly")
        year_cb.pack()
        year_cb.set(datetime.datetime.now().strftime("%Y"))

        def set_month():
            month_var.set(f"{month_cb.get()}/{year_cb.get()}")
            top.destroy()
        tk.Button(top, text="Chọn", command=set_month, font=("Helvetica", 12, "bold"), bg="#27ae60", fg="white").pack(pady=10)

    entry_month = tk.Entry(frame_top, textvariable=month_var, width=10, font=("Helvetica", 12))
    entry_month.pack(side=tk.LEFT, padx=5)
    tk.Button(frame_top, text="Chọn tháng", command=pick_month, font=("Helvetica", 11, "bold"), bg="#3498db", fg="white", padx=10).pack(side=tk.LEFT, padx=5)

    # Nút Update dữ liệu
    def update_data():
        update_check_data()
        refresh_tree()

    # TreeView
    frame_table = tk.Frame(window, bg="#e8ecef")
    frame_table.pack(pady=10, fill="both", expand=True)
    tree = ttk.Treeview(frame_table, columns=DISPLAY_COLUMNS, show="headings", height=20)
    for col in DISPLAY_COLUMNS:
        tree.heading(col, text=col)
        tree.column(col, width=200, anchor="center")
    tree.pack(side="left", fill="both", expand=True)
    scrollbar = ttk.Scrollbar(frame_table, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    # Load data
    df = load_check_data()
    def refresh_tree():
        nonlocal df
        df = load_check_data()
        tree.delete(*tree.get_children())
        for _, row in df.iterrows():
            tree.insert("", "end", values=(row["Chủng loại"], row["Mã hàng"], row["Khách hàng"], row["Link"], row["Status"]))
    refresh_tree()

    def confirm_data():
        kjs_path = entry_kjs.get().strip()
        if not kjs_path or not os.path.exists(kjs_path):
            messagebox.showwarning("Thiếu file", "Vui lòng chọn file KJS hợp lệ!")
            return

        try:
            # Đọc file KJS (Excel hoặc CSV)
            if kjs_path.lower().endswith(('.xlsx', '.xls')):
                kjs_df = pd.read_excel(kjs_path, dtype=str)
            else:
                kjs_df = pd.read_csv(kjs_path, dtype=str, encoding="utf-8-sig")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể đọc file KJS: {e}")
            return

        # Kiểm tra cột ITEM và PRODUCTION_ORDER_NO
        if "ITEM" not in kjs_df.columns or "PRODUCTION_ORDER_NO" not in kjs_df.columns:
            messagebox.showerror("Lỗi", "File KJS phải có cột 'ITEM' và 'PRODUCTION_ORDER_NO'!")
            return

        # Đọc DataMontlyCheck.csv
        df = load_check_data()
        found_count = 0
        filter_rows = []
        json_dict = {}

        for idx, row in df.iterrows():
            ma_hang = str(row["Mã hàng"])
            # Lấy phần cuối sau dấu "-"
            if "-" in ma_hang:
                code = ma_hang.split("-")[-1].strip()
            else:
                code = ma_hang.strip()
            # Lọc các dòng KJS có ITEM chứa code và PRODUCTION_ORDER_NO > 6 ký tự
            matched = kjs_df[
                kjs_df["ITEM"].astype(str).str.contains(code, case=False, na=False) &
                (kjs_df["PRODUCTION_ORDER_NO"].astype(str).str.len() > 6)
            ]
            if not matched.empty:
                df.at[idx, "Status"] = "Xác nhận có dữ liệu KJS"
                found_count += 1
                for _, kjs_row in matched.iterrows():
                    filter_rows.append(kjs_row)
                    # Sửa ở đây: mỗi ITEM là 1 list các dict
                    item_key = str(kjs_row["ITEM"])
                    item_info = {
                        "LOT_NO": kjs_row.get("LOT_NO", ""),
                        "CUSTOMER": kjs_row.get("CUSTOMER", ""),
                        "ACCEPT_QTY": kjs_row.get("ACCEPT_QTY", ""),
                        "PRODUCTION_ORDER_NO": kjs_row.get("PRODUCTION_ORDER_NO", "")
                    }
                    if item_key not in json_dict:
                        json_dict[item_key] = []
                    json_dict[item_key].append(item_info)
            else:
                df.at[idx, "Status"] = "Không có dữ liệu trong KJS"

        # Lưu lại DataMontlyCheck.csv
        save_check_data(df)
        refresh_tree()

        # Lưu DataMontlyFilter.csv
        if filter_rows:
            filter_df = pd.DataFrame(filter_rows)
            filter_csv_path = os.path.join(CHECK_DIR, "DataMontlyFilter.csv")
            filter_df.to_csv(filter_csv_path, index=False, encoding="utf-8-sig")
            # Lưu JSON
            import json
            filter_json_path = os.path.join(CHECK_DIR, "DataMontlyFilter.json")
            with open(filter_json_path, "w", encoding="utf-8") as f:
                json.dump(json_dict, f, ensure_ascii=False, indent=2)
        else:
            filter_csv_path = ""
            filter_json_path = ""

        messagebox.showinfo("Kết quả", f"Đã xác nhận xong!\nCó {found_count} mã hàng tìm thấy dữ liệu KJS.\n"
                                    f"Đã xuất file DataMontlyFilter.csv{' và DataMontlyFilter.json' if filter_rows else ''}.")
        
    # Nút chức năng
    frame_btn = tk.Frame(window, bg="#e8ecef")
    frame_btn.pack(pady=10)
    
    tk.Button(frame_btn, text="Xác nhận dữ liệu", font=("Helvetica", 12, "bold"),
            bg="#27ae60", fg="white", padx=18, pady=6,
            command=confirm_data).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_btn, text="Chỉnh sửa nội dung", font=("Helvetica", 12, "bold"),
              bg="#3498db", fg="white", padx=18, pady=6,
              command=lambda: messagebox.showinfo("Thông báo", "Chức năng chỉnh sửa đang phát triển!")).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_btn, text="Nén file", font=("Helvetica", 12, "bold"),
              bg="#f39c12", fg="white", padx=18, pady=6,
              command=lambda: messagebox.showinfo("Thông báo", "Chức năng nén file đang phát triển!")).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_btn, text="Reset", font=("Helvetica", 12, "bold"),
              bg="#e74c3c", fg="white", padx=18, pady=6,
              command=refresh_tree).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_btn, text="Update dữ liệu", font=("Helvetica", 12, "bold"),
              bg="#f39c12", fg="white", padx=18, pady=6,
              command=update_data).pack(side=tk.LEFT, padx=10)
    tk.Button(window, text="Đóng", command=window.destroy, font=("Helvetica", 12, "bold"),
              bg="#8e44ad", fg="white", padx=20, pady=8).pack(pady=12)