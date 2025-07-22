import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os

DATA_DIR = os.path.join(os.getcwd(), "DATASETC", "dataMontlydata")
os.makedirs(DATA_DIR, exist_ok=True)
CSV_PATH = os.path.join(DATA_DIR, "dataMontly.csv")

DISPLAY_COLUMNS = ["Chủng loại", "Mã hàng", "Khách hàng" ]

def load_data():
    if os.path.exists(CSV_PATH):
        try:
            return pd.read_csv(CSV_PATH, encoding="utf-8-sig")
        except Exception:
            return pd.DataFrame(columns=DISPLAY_COLUMNS)
    return pd.DataFrame(columns=DISPLAY_COLUMNS)

def save_data(df):
    df.to_csv(CSV_PATH, index=False, encoding="utf-8-sig")

def open_data_montly_window(root):
    window = tk.Toplevel(root)
    window.title("Data Montly")
    window.state('zoomed')  # Phóng to cửa sổ
    window.configure(bg="#e8ecef")
    window.lift()
    window.grab_set()
    window.focus_force()

    # Frame cho các nút
    frame_btn = tk.Frame(window, bg="#e8ecef")
    frame_btn.pack(fill="x", pady=10, padx=10)

    # Treeview
    frame_tree = tk.Frame(window, bg="#e8ecef")
    frame_tree.pack(fill="both", expand=True, padx=10, pady=10)
    tree = ttk.Treeview(frame_tree, columns=DISPLAY_COLUMNS, show="headings", height=25)
    for col in DISPLAY_COLUMNS:
        tree.heading(col, text=col)
        tree.column(col, width=250, anchor="center")
    tree.pack(side="left", fill="both", expand=True)
    scrollbar = ttk.Scrollbar(frame_tree, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    # Load data
    df = load_data()
    original_df = df.copy()
    filters = {}

    def refresh_tree(data=None):
        nonlocal df
        if data is None:
            data = df
        tree.delete(*tree.get_children())
        for _, row in data.iterrows():
            tree.insert(
                "",
                "end",
                values=(
                    row.get("Chủng loại", ""),
                    row.get("Mã hàng", ""),
                    row.get("Khách hàng", "")
                )
            )


    def apply_filters():
        filtered = df.copy()
        for col in DISPLAY_COLUMNS:
            val = filter_vars[col].get().strip()
            if val:
                filtered = filtered[filtered[col].astype(str).str.contains(val, case=False, na=False)]
        return filtered

    def show_filter(col):
        filter_win = tk.Toplevel(window)
        filter_win.title(f"Lọc theo {col}")
        filter_win.geometry("400x180")
        filter_win.configure(bg="#e8ecef")
        filter_win.lift()
        filter_win.grab_set()
        tk.Label(filter_win, text=f"Nhập giá trị lọc cho {col}:", font=("Helvetica", 12), bg="#e8ecef").pack(pady=15)
        entry = tk.Entry(filter_win, width=35, font=("Helvetica", 12))
        entry.pack(pady=10)
        entry.insert(0, filter_vars[col].get())
        def apply_filter():
            filter_vars[col].set(entry.get().strip())
            filtered_data = filter_datamonthly_df()
            refresh_datamonthly_tree(filtered_data)
            filter_win.destroy()
        tk.Button(filter_win, text="Lọc", command=apply_filter, font=("Helvetica", 12, "bold"),
                bg="#3498db", fg="white", padx=20, pady=8).pack(pady=15)

    refresh_tree()
    def clear_filter():
        for c in DISPLAY_COLUMNS:
            filter_vars[c].set("")
        refresh_datamonthly_tree(df)
    
    # AddData
    def add_data():
        add_win = tk.Toplevel(window)
        add_win.title("Thêm dữ liệu")
        add_win.geometry("400x260")
        add_win.configure(bg="#e8ecef")
        add_win.lift()
        add_win.grab_set()
        tk.Label(add_win, text="Chủng loại:", font=("Helvetica", 12), bg="#e8ecef").pack(pady=7)
        entry_a = tk.Entry(add_win, font=("Helvetica", 12))
        entry_a.pack(pady=5)
        tk.Label(add_win, text="Mã hàng:", font=("Helvetica", 12), bg="#e8ecef").pack(pady=7)
        entry_b = tk.Entry(add_win, font=("Helvetica", 12))
        entry_b.pack(pady=5)
        tk.Label(add_win, text="Khách hàng:", font=("Helvetica", 12), bg="#e8ecef").pack(pady=7)
        entry_c = tk.Entry(add_win, font=("Helvetica", 12))
        entry_c.pack(pady=5)
        def confirm_add():
            a, b, c = entry_a.get().strip(), entry_b.get().strip(), entry_c.get().strip()
            if not a or not b or not c:
                messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập đủ thông tin!")
                return
            nonlocal df, original_df
            df = pd.concat([df, pd.DataFrame([{"Chủng loại": a, "Mã hàng": b, "Khách hàng": c}])], ignore_index=True)
            original_df = df.copy()
            save_data(df)
            refresh_tree(apply_filters())
            add_win.destroy()
        tk.Button(add_win, text="Thêm", command=confirm_add, font=("Helvetica", 12, "bold"),
                  bg="#27ae60", fg="white", padx=20, pady=6).pack(pady=15)

    # Sửa dữ liệu (double click)
    def modify_data(event):
        selected = tree.selection()
        if not selected:
            return
        item = selected[0]
        values = tree.item(item, "values")
        # Tìm đúng index trong df sau khi filter
        filtered_df = apply_filters()
        idx = filtered_df.index[tree.index(item)]
        row = df.loc[idx]

        modify_win = tk.Toplevel(window)
        modify_win.title("Sửa dữ liệu")
        modify_win.geometry("400x260")
        modify_win.configure(bg="#e8ecef")
        modify_win.lift()
        modify_win.grab_set()
        tk.Label(modify_win, text="Chủng loại:", font=("Helvetica", 12), bg="#e8ecef").pack(pady=7)
        entry_a = tk.Entry(modify_win, font=("Helvetica", 12))
        entry_a.pack(pady=5)
        entry_a.insert(0, row["Chủng loại"])
        tk.Label(modify_win, text="Mã hàng:", font=("Helvetica", 12), bg="#e8ecef").pack(pady=7)
        entry_b = tk.Entry(modify_win, font=("Helvetica", 12))
        entry_b.pack(pady=5)
        entry_b.insert(0, row["Mã hàng"])
        tk.Label(modify_win, text="Khách hàng:", font=("Helvetica", 12), bg="#e8ecef").pack(pady=7)
        entry_c = tk.Entry(modify_win, font=("Helvetica", 12))
        entry_c.pack(pady=5)
        entry_c.insert(0, row["Khách hàng"])
        def confirm_modify():
            a, b, c = entry_a.get().strip(), entry_b.get().strip(), entry_c.get().strip()
            if not a or not b or not c:
                messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập đủ thông tin!")
                return
            nonlocal df, original_df
            df.at[idx, "Chủng loại"] = a
            df.at[idx, "Mã hàng"] = b
            df.at[idx, "Khách hàng"] = c
            original_df = df.copy()
            save_data(df)
            refresh_tree(apply_filters())
            modify_win.destroy()
        tk.Button(modify_win, text="Lưu", command=confirm_modify, font=("Helvetica", 12, "bold"),
                  bg="#3498db", fg="white", padx=20, pady=6).pack(pady=15)

    tree.bind("<Double-1>", modify_data)

    # UpdateExcelFileXlsx
    def update_excel():
        file_path = filedialog.askopenfilename(
            title="Chọn file Excel",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if not file_path:
            return
        try:
            xls = pd.ExcelFile(file_path)
            if "FILE GOC" not in xls.sheet_names:
                messagebox.showerror("Lỗi", "Không tìm thấy sheet 'FILE GOC' trong file Excel!")
                return
            df_xlsx = pd.read_excel(file_path, sheet_name="FILE GOC", header=None)
            # Nếu dòng đầu là tiêu đề, bỏ dòng đầu
            first_row = df_xlsx.iloc[0, :3].tolist()
            if first_row == DISPLAY_COLUMNS:
                df_xlsx = df_xlsx.iloc[1:, :]
            df_new = df_xlsx.iloc[:, :3]
            df_new.columns = DISPLAY_COLUMNS
            nonlocal df, original_df
            df = df_new.reset_index(drop=True)
            original_df = df.copy()
            save_data(df)
            refresh_tree(apply_filters())
            messagebox.showinfo("Thành công", "Đã cập nhật dữ liệu từ file Excel!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể đọc file Excel: {e}")

    # Filter logic
    filter_vars = {col: tk.StringVar() for col in DISPLAY_COLUMNS}
    
    for col in DISPLAY_COLUMNS:
        tree.heading(col, text=col, command=lambda c=col: show_filter(c))

    # DeleteData menu
    def delete_selected():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Chọn dòng", "Vui lòng chọn dòng để xóa!")
            return
        filtered_df = apply_filters()
        idxs = [filtered_df.index[tree.index(item)] for item in selected]
        nonlocal df, original_df
        df = df.drop(idxs).reset_index(drop=True)
        original_df = df.copy()
        save_data(df)
        refresh_tree(apply_filters())

    def delete_all():
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa toàn bộ dữ liệu?"):
            nonlocal df, original_df
            df = pd.DataFrame(columns=DISPLAY_COLUMNS)
            original_df = df.copy()
            save_data(df)
            refresh_tree()

    def show_delete_menu(event=None):
        menu = tk.Menu(window, tearoff=0)
        menu.add_command(label="Delete Selected File", command=delete_selected)
        menu.add_command(label="Delete All File", command=delete_all)
        x = frame_btn.winfo_rootx() + btn_delete.winfo_x()
        y = frame_btn.winfo_rooty() + btn_delete.winfo_y() + btn_delete.winfo_height()
        menu.tk_popup(x, y)

    def filter_datamonthly_df():
        filtered = df.copy()
        for col in DISPLAY_COLUMNS:
            val = filter_vars[col].get().strip()
            if val:
                filtered = filtered[filtered[col].astype(str).str.contains(val, case=False, na=False)]
        return filtered

    def refresh_datamonthly_tree(data=None):
        nonlocal df
        if data is None:
            data = df
        tree.delete(*tree.get_children())
        for _, row in data.iterrows():
            tree.insert(
                "",
                "end",
                values=(
                    row.get("Chủng loại", ""),
                    row.get("Mã hàng", ""),
                    row.get("Khách hàng", "")
                )
            )


    # Nút chức năng
    tk.Button(frame_btn, text="Add Data", command=add_data, font=("Helvetica", 12, "bold"),
              bg="#27ae60", fg="white", padx=18, pady=6).pack(side=tk.LEFT, padx=10)
    btn_delete = tk.Button(frame_btn, text="Delete Data ▼", font=("Helvetica", 12, "bold"),
              bg="#e74c3c", fg="white", padx=18, pady=6)
    btn_delete.pack(side=tk.LEFT, padx=10)
    btn_delete.bind("<Button-1>", show_delete_menu)
    tk.Button(frame_btn, text="UpdateExcelFileXlsx", command=update_excel, font=("Helvetica", 12, "bold"),
              bg="#f39c12", fg="white", padx=18, pady=6).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_btn, text="Clear Filter", command=clear_filter, font=("Helvetica", 12, "bold"),
          bg="#3498db", fg="white", padx=18, pady=6).pack(side=tk.LEFT, padx=10)

    tk.Button(window, text="Đóng", command=window.destroy, font=("Helvetica", 12, "bold"),
              bg="#8e44ad", fg="white", padx=20, pady=8).pack(pady=12)