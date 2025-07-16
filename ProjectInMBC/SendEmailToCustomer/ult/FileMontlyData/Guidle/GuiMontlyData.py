import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import os
import pandas as pd
import calendar
import datetime
from ult.FileMontlyData.Guidle import stateMontly

CHECK_DIR = os.path.join(os.getcwd(), "DATASETC", "dataMontlydata", "Check")
os.makedirs(CHECK_DIR, exist_ok=True)
CHECK_CSV = os.path.join(CHECK_DIR, "DataMontlyCheck.csv")
DATA_CSV = os.path.join(os.getcwd(), "DATASETC", "dataMontlydata", "dataMontly.csv")
DISPLAY_COLUMNS = ["Chủng loại", "Mã hàng", "Khách hàng", "Link", "Status"]
def open_config_monthly_window(root):
    window = tk.Toplevel(root)
    window.title("Config Monthly Data")
    window.geometry("900x420")
    window.configure(bg="#e8ecef")

    from ult.SendEmail.Guidle.config import load_monthly_config, save_monthly_config

    config = load_monthly_config()

    # ====== Địa chỉ file nguồn ======
    frame_tempt = tk.Frame(window, bg="#e8ecef")
    frame_tempt.pack(pady=15, fill="x", padx=30)
    tk.Label(frame_tempt, text="Chọn thư mục tạm:", font=("Helvetica", 12), bg="#e8ecef").pack(side=tk.LEFT)
    entry_tempt = tk.Entry(frame_tempt, width=40, font=("Helvetica", 12))
    entry_tempt.pack(side=tk.LEFT, padx=10)
    entry_tempt.insert(0, config.get("tempt_path", ""))
    def select_tempt_folder():
        folder = filedialog.askdirectory(title="Chọn thư mục tạm")
        if folder:
            entry_tempt.delete(0, tk.END)
            entry_tempt.insert(0, folder)
    tk.Button(frame_tempt, text="Chọn", command=select_tempt_folder,
            font=("Helvetica", 11, "bold"), bg="#3498db", fg="white", padx=10).pack(side=tk.LEFT)


    # ====== Địa chỉ file gốc ======
    frame_origin = tk.Frame(window, bg="#e8ecef")
    frame_origin.pack(pady=15, fill="x", padx=30)
    tk.Label(frame_origin, text="Địa chỉ file gốc:", font=("Helvetica", 12), bg="#e8ecef").pack(side=tk.LEFT)
    entry_origin = tk.Entry(frame_origin, width=40, font=("Helvetica", 12))
    entry_origin.pack(side=tk.LEFT, padx=10)
    entry_origin.insert(0, config.get("origin_path", ""))
    def select_origin_folder():
        folder = filedialog.askdirectory(title="Chọn thư mục gốc")
        if folder:
            entry_origin.delete(0, tk.END)
            entry_origin.insert(0, folder)
    tk.Button(frame_origin, text="Chọn", command=select_origin_folder,
              font=("Helvetica", 11, "bold"), bg="#3498db", fg="white", padx=10).pack(side=tk.LEFT)

    # ====== File Excel ======
    frame_excel = tk.Frame(window, bg="#e8ecef")
    frame_excel.pack(pady=15, fill="x", padx=30)
    tk.Label(frame_excel, text="File Excel:", font=("Helvetica", 12), bg="#e8ecef").pack(side=tk.LEFT)
    entry_excel = tk.Entry(frame_excel, width=32, font=("Helvetica", 12))
    entry_excel.pack(side=tk.LEFT, padx=10)
    entry_excel.insert(0, config.get("excel_path", ""))

    def select_excel_file():
        file_path = filedialog.askopenfilename(
            title="Chọn file Excel",
            filetypes=[("Excel files", "*.xlsx *.xls *.xlsm *.csv"), ("All files", "*.*")]
        )
        if file_path:
            entry_excel.delete(0, tk.END)
            entry_excel.insert(0, file_path)

    tk.Button(frame_excel, text="Chọn", command=select_excel_file,
              font=("Helvetica", 11, "bold"), bg="#3498db", fg="white", padx=10).pack(side=tk.LEFT)

    def convert_excel_to_csv():
        excel_path = entry_excel.get()
        if not excel_path or not os.path.exists(excel_path):
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn file Excel hợp lệ!")
            return
        try:
            xl = pd.ExcelFile(excel_path)
            sheet_names = xl.sheet_names

            select_window = tk.Toplevel(window)
            select_window.title("Chọn sheet và vùng dữ liệu")
            select_window.geometry("420x320")
            select_window.configure(bg="#e8ecef")

            tk.Label(select_window, text="Chọn sheet:", font=("Helvetica", 12), bg="#e8ecef").pack(pady=8)
            sheet_var = tk.StringVar(value=sheet_names[0])
            sheet_menu = ttk.Combobox(select_window, textvariable=sheet_var, values=sheet_names, state="readonly", font=("Helvetica", 12))
            sheet_menu.pack(pady=5)

            row_frame = tk.Frame(select_window, bg="#e8ecef")
            row_frame.pack(pady=5)
            tk.Label(row_frame, text="Dòng bắt đầu (từ 0):", font=("Helvetica", 12), bg="#e8ecef").pack(side=tk.LEFT)
            entry_row_start = tk.Entry(row_frame, width=6, font=("Helvetica", 12))
            entry_row_start.pack(side=tk.LEFT, padx=5)
            entry_row_start.insert(0, "0")

            tk.Label(row_frame, text="Dòng kết thúc (từ 0, để trống lấy hết):", font=("Helvetica", 12), bg="#e8ecef").pack(side=tk.LEFT)
            entry_row_end = tk.Entry(row_frame, width=6, font=("Helvetica", 12))
            entry_row_end.pack(side=tk.LEFT, padx=5)

            col_frame = tk.Frame(select_window, bg="#e8ecef")
            col_frame.pack(pady=5)
            tk.Label(col_frame, text="Cột bắt đầu (từ 0):", font=("Helvetica", 12), bg="#e8ecef").pack(side=tk.LEFT)
            entry_col_start = tk.Entry(col_frame, width=6, font=("Helvetica", 12))
            entry_col_start.pack(side=tk.LEFT, padx=5)
            entry_col_start.insert(0, "0")

            tk.Label(col_frame, text="Cột kết thúc (từ 0, để trống lấy hết):", font=("Helvetica", 12), bg="#e8ecef").pack(side=tk.LEFT)
            entry_col_end = tk.Entry(col_frame, width=6, font=("Helvetica", 12))
            entry_col_end.pack(side=tk.LEFT, padx=5)

            def do_convert():
                try:
                    sheet = sheet_var.get()
                    row_start = entry_row_start.get().strip()
                    row_end = entry_row_end.get().strip()
                    col_start = entry_col_start.get().strip()
                    col_end = entry_col_end.get().strip()

                    df = pd.read_excel(excel_path, sheet_name=sheet, header=None)
                    row_start = int(row_start) if row_start else 0
                    row_end = int(row_end) if row_end else None
                    col_start = int(col_start) if col_start else 0
                    col_end = int(col_end) if col_end else None

                    df = df.iloc[row_start:row_end, col_start:col_end]

                    base_name = os.path.splitext(os.path.basename(excel_path))[0]
                    output_csv = os.path.join(os.path.dirname(excel_path), f"{base_name}_monthly_convert.csv")
                    df.to_csv(output_csv, index=False, header=False, encoding='utf-8-sig')

                    # Lưu lại đường dẫn vào config
                    config = load_monthly_config()
                    config["excel_path"] = excel_path
                    config["excel_csv"] = output_csv
                    save_monthly_config(config)
                    messagebox.showinfo("Thành công", f"Đã convert file Excel sang CSV:\n{output_csv}")
                    select_window.destroy()
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Không thể convert file Excel: {e}")

            tk.Button(select_window, text="Convert", command=do_convert,
                      font=("Helvetica", 12, "bold"), bg="#f39c12", fg="white", padx=18).pack(pady=18)

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể đọc file Excel: {e}")

    tk.Button(frame_excel, text="Convert to CSV", command=convert_excel_to_csv,
              font=("Helvetica", 11, "bold"), bg="#f39c12", fg="white", padx=10).pack(side=tk.LEFT, padx=8)

    # ====== Nút lưu và đóng ======
    frame_btn = tk.Frame(window, bg="#e8ecef")
    frame_btn.pack(pady=30)
    def save():
        config = {
        "tempt_path": entry_tempt.get(),
        "origin_path": entry_origin.get(),
        "excel_path": entry_excel.get()
    }
        save_monthly_config(config)
        messagebox.showinfo("Thành công", "Đã lưu cấu hình Monthly Data!")

    tk.Button(frame_btn, text="Lưu cấu hình", command=save, font=("Helvetica", 12, "bold"),
              bg="#27ae60", fg="white", padx=20, pady=6).pack(side=tk.LEFT, padx=20)
    tk.Button(frame_btn, text="Đóng", command=window.destroy, font=("Helvetica", 12, "bold"),
              bg="#e74c3c", fg="white", padx=20, pady=6).pack(side=tk.LEFT, padx=20)

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
    
    
def edit_content():
    # Đọc config
    from ult.SendEmail.Guidle.config import load_monthly_config
    config = load_monthly_config()
    tempt_dir = config.get("tempt_path", "")
    origin_dir = config.get("origin_path", "")

    # Đọc tháng/năm từ stateMontly
    import ult.FileMontlyData.Guidle.stateMontly as state_monthly
    month = state_monthly.MonthSelect or datetime.datetime.now().strftime("%m")
    year = state_monthly.YearsSelect or datetime.datetime.now().strftime("%Y")

    # Đọc DataMontlyCheck.csv
    df = load_check_data()
    copied_files = []
    for _, row in df.iterrows():
        if str(row["Status"]) != "Xác nhận có dữ liệu KJS":
            continue
        # Lấy thông tin
        chungloaiMini = ""
        tenmahangMini = ""
        parts = str(row["Mã hàng"]).split("-")
        if len(parts) >= 3:
            chungloaiMini = parts[1]
            tenmahangMini = parts[2]
        khach_hang = str(row["Khách hàng"])
        # Tìm file nguồn
        src_folder = os.path.join(origin_dir, f"Hang {chungloaiMini}", f"Ma Hang {tenmahangMini}", year)
        if not os.path.exists(src_folder):
            continue
        # Tìm file theo pattern
        pattern = f"{tenmahangMini}-{year}.{month}"
        for fname in os.listdir(src_folder):
            if pattern in fname:
                src_file = os.path.join(src_folder, fname)
                # Đích: tempt_dir/{Year}/{Month}/{KhachHang}/
                dest_folder = os.path.join(tempt_dir, year, month, khach_hang)
                os.makedirs(dest_folder, exist_ok=True)
                dest_file = os.path.join(dest_folder, fname)
                try:
                    import shutil
                    shutil.copy2(src_file, dest_file)
                    copied_files.append(dest_file)
                except Exception as e:
                    print(f"Lỗi copy {src_file}: {e}")
    messagebox.showinfo("Kết quả", f"Đã copy {len(copied_files)} file vào thư mục tạm.")

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
        top.geometry("300x350")
        top.configure(bg="#e8ecef")

        tk.Label(top, text="Tháng:", font=("Helvetica", 12), bg="#e8ecef").pack(pady=5)
        month_cb = ttk.Combobox(top, values=[f"{i:02d}" for i in range(1, 13)], width=5, font=("Helvetica", 12), state="readonly")
        month_cb.pack()
        month_cb.set(datetime.datetime.now().strftime("%m"))

        tk.Label(top, text="Năm:", font=("Helvetica", 12), bg="#e8ecef").pack(pady=5)
        year_cb = ttk.Combobox(top, values=[str(y) for y in range(datetime.datetime.now().year-3, datetime.datetime.now().year+4)], width=7, font=("Helvetica", 12), state="readonly")
        year_cb.pack()
        year_cb.set(datetime.datetime.now().strftime("%Y"))

        def set_month():
            month = month_cb.get()
            year = year_cb.get()
            month_var.set(f"{month}/{year}")
            # Lưu vào stateMontly
            stateMontly.MonthSelect = month
            stateMontly.YearsSelect = year
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
            # Chủng loại: lấy 2 phần đầu, ghép lại không dấu "-"
            parts = ma_hang.split("-")
            if len(parts) >= 2:
                chung_loai = parts[0] + parts[1]
                ChungloaiMini = parts[1]
                tenmahangMini=parts[2]
            else:
                chung_loai = ma_hang
                ChungloaiMini=""
                tenmahangMini=""
            khach_hang = str(row["Khách hàng"])  # lấy từ dòng hiện tại

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
                    item_key = str(kjs_row["ITEM"])
                    item_info = {
                        "ChungLoai": chung_loai,
                        "ChungloaiMini": ChungloaiMini,
                        "TenmahangMini": tenmahangMini,
                        "KhachHang": khach_hang,
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
          command=edit_content).pack(side=tk.LEFT, padx=10)
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
