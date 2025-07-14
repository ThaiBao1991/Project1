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

def open_gui_monthly_data(root):
    window = tk.Toplevel(root)
    window.title("Gửi Monthly Data")
    window.geometry("1200x700")
    window.configure(bg="#e8ecef")
    window.lift()
    window.grab_set()
    window.focus_force()

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
        cal = ttk.Combobox(top, values=[f"{m:02d}/{datetime.datetime.now().year}" for m in range(1,13)], font=("Helvetica", 12))
        cal.pack(padx=20, pady=20)
        cal.set(month_var.get() or datetime.datetime.now().strftime("%m/%Y"))
        def set_month():
            month_var.set(cal.get())
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

    # Nút chức năng
    frame_btn = tk.Frame(window, bg="#e8ecef")
    frame_btn.pack(pady=10)
    tk.Button(frame_btn, text="Update dữ liệu", font=("Helvetica", 12, "bold"),
              bg="#f39c12", fg="white", padx=18, pady=6,
              command=update_data).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_btn, text="Xác nhận dữ liệu", font=("Helvetica", 12, "bold"),
              bg="#27ae60", fg="white", padx=18, pady=6,
              command=lambda: messagebox.showinfo("Thông báo", "Chức năng xác nhận đang phát triển!")).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_btn, text="Chỉnh sửa nội dung", font=("Helvetica", 12, "bold"),
              bg="#3498db", fg="white", padx=18, pady=6,
              command=lambda: messagebox.showinfo("Thông báo", "Chức năng chỉnh sửa đang phát triển!")).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_btn, text="Nén file", font=("Helvetica", 12, "bold"),
              bg="#f39c12", fg="white", padx=18, pady=6,
              command=lambda: messagebox.showinfo("Thông báo", "Chức năng nén file đang phát triển!")).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_btn, text="Reset", font=("Helvetica", 12, "bold"),
              bg="#e74c3c", fg="white", padx=18, pady=6,
              command=refresh_tree).pack(side=tk.LEFT, padx=10)
    tk.Button(window, text="Đóng", command=window.destroy, font=("Helvetica", 12, "bold"),
              bg="#8e44ad", fg="white", padx=20, pady=8).pack(pady=12)