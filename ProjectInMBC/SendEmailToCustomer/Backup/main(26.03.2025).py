import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import os

# Hàm chọn file Excel
def chon_file_excel():
    file_path = filedialog.askopenfilename(
        title="Chọn file Excel",
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )
    if file_path:
        entry_file_excel.delete(0, tk.END)
        entry_file_excel.insert(0, file_path)

# Hàm chọn file TXT
def chon_file_txt():
    file_path = filedialog.askopenfilename(
        title="Chọn file TXT",
        filetypes=[("Text files", "*.txt")]
    )
    if file_path:
        entry_file_txt.delete(0, tk.END)
        entry_file_txt.insert(0, file_path)

# Hàm xử lý nút "Gửi dữ liệu khách hàng"
def gui_du_lieu():
    file_excel = entry_file_excel.get()
    file_txt = entry_file_txt.get()
    if file_excel and file_txt:
        messagebox.showinfo("Thông báo", f"File Excel: {file_excel}\nFile TXT: {file_txt}\nChức năng gửi dữ liệu đang được thực thi!")
    else:
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn cả file Excel và file TXT trước!")

# Hàm thoát chương trình
def thoat():
    if messagebox.askokcancel("Thoát", "Bạn có chắc chắn muốn thoát?"):
        root.destroy()

# Hàm hiển thị kích thước khi kéo thả
def on_resize(event):
    width = root.winfo_width()
    height = root.winfo_height()
    root.title(f"Gửi Dữ Liệu Khách Hàng - {width}x{height}")

# Hàm reset tiêu đề khi thả ra
def on_release(event):
    root.title("Gửi Dữ Liệu Khách Hàng")

# Hàm chọn file Data trong Config
def chon_file_data():
    file_path = filedialog.askopenfilename(
        title="Chọn file Data",
        filetypes=[("Excel files", "*.xlsx *.xls *.xlsm *.xlsb"), ("All files", "*.*")]
    )
    if file_path:
        entry_data_path.delete(0, tk.END)
        entry_data_path.insert(0, file_path)

# Hàm xử lý nút "Xuất Data"
def xuat_data():
    data_path = entry_data_path.get()
    if not data_path:
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn file Data trước khi xuất!")
        return
    try:
        df = pd.read_excel(data_path, header=1)
        column_k = 'Gửi Lot DAI DIEN: "DD" Gửi TOAN BO Lot: "TB"'
        if column_k not in df.columns:
            messagebox.showerror("Lỗi", f"Không tìm thấy cột '{column_k}' trong file Excel!")
            return
        columns_to_keep = {
            'SS': 'SS',
            'Mã hàng': 'Mã hàng',
            'MSKH': 'MSKH',
            'Tên khách hàng': 'Tên khách hàng',
            column_k: 'Gửi Lot',
            'Gửi dữ liệu [M]': 'Gửi dữ liệu',
            'Nội dung gửi mail': 'Nội dung gửi email',
            'Địa chỉ gửi mail': 'Địa chỉ gửi email'
        }
        missing_cols = [col for col in columns_to_keep.keys() if col not in df.columns]
        if missing_cols:
            messagebox.showerror("Lỗi", f"Không tìm thấy các cột sau trong file Excel: {missing_cols}")
            return
        filtered_df = df[df[column_k].isin(['TB', 'DD'])]
        filtered_df = filtered_df[list(columns_to_keep.keys())]
        filtered_df.columns = list(columns_to_keep.values())
        output_path = os.path.splitext(data_path)[0] + "_filtered.csv"
        filtered_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        messagebox.showinfo("Thông báo", f"Dữ liệu đã được xuất thành công ra file: {output_path}")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi khi xử lý file: {str(e)}")

# Hàm mở cửa sổ Config
def open_config(event=None):
    root.withdraw()
    config_window = tk.Toplevel(root)
    config_window.title("Config")
    config_window.geometry("1150x300")
    config_window.configure(bg="#e8ecef")
    config_window.resizable(False, False)

    def on_config_close():
        config_window.destroy()
        root.deiconify()

    config_window.protocol("WM_DELETE_WINDOW", on_config_close)

    frame_config = tk.Frame(config_window, bg="#e8ecef")
    frame_config.pack(pady=20)

    tk.Label(frame_config, text="Cập nhật dữ liệu khách hàng:", font=("Helvetica", 14, "bold"), bg="#e8ecef", fg="#2c3e50").grid(row=0, column=0, padx=20, pady=20, sticky="e")
    global entry_data_path
    entry_data_path = tk.Entry(frame_config, width=40, font=("Helvetica", 12), bd=2, relief="sunken", bg="#ffffff")
    entry_data_path.grid(row=0, column=1, padx=20, pady=20)
    tk.Button(frame_config, text="Chọn file Data", command=chon_file_data, font=("Helvetica", 11, "bold"), bg="#27ae60", fg="white", activebackground="#219653", bd=0, padx=20, pady=10).grid(row=0, column=2, padx=20, pady=20)
    tk.Button(frame_config, text="Xuất Data", command=xuat_data, font=("Helvetica", 11, "bold"), bg="#f39c12", fg="white", activebackground="#e67e22", bd=0, padx=20, pady=10).grid(row=0, column=3, padx=20, pady=20)

    tk.Label(frame_config, text="Địa chỉ lưu dữ liệu:", font=("Helvetica", 14, "bold"), bg="#e8ecef", fg="#2c3e50").grid(row=1, column=0, padx=20, pady=20, sticky="e")
    global entry_save_path
    entry_save_path = tk.Entry(frame_config, width=40, font=("Helvetica", 12), bd=2, relief="sunken", bg="#ffffff")
    entry_save_path.grid(row=1, column=1, padx=20, pady=20)
    tk.Button(frame_config, text="Chọn nơi lưu dữ liệu", command=chon_noi_luu, font=("Helvetica", 11, "bold"), bg="#27ae60", fg="white", activebackground="#219653", bd=0, padx=20, pady=10).grid(row=1, column=2, padx=20, pady=20)

    frame_buttons = tk.Frame(config_window, bg="#e8ecef")
    frame_buttons.pack(pady=20)
    tk.Button(frame_buttons, text="Save", command=save_config, font=("Helvetica", 12, "bold"), bg="#3498db", fg="white", activebackground="#2980b9", bd=0, padx=20, pady=10).pack(side=tk.LEFT, padx=20)
    tk.Button(frame_buttons, text="Close", command=on_config_close, font=("Helvetica", 12, "bold"), bg="#e74c3c", fg="white", activebackground="#c0392b", bd=0, padx=20, pady=10).pack(side=tk.LEFT, padx=20)

# Hàm chọn nơi lưu dữ liệu
def chon_noi_luu():
    folder_path = filedialog.askdirectory(title="Chọn nơi lưu dữ liệu")
    if folder_path:
        entry_save_path.delete(0, tk.END)
        entry_save_path.insert(0, folder_path)

# Hàm lưu cấu hình
def save_config():
    save_path = entry_save_path.get()
    if save_path:
        messagebox.showinfo("Thông báo", f"Địa chỉ lưu dữ liệu đã được lưu: {save_path}")
    else:
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn địa chỉ lưu dữ liệu trước!")

# Hàm mở cửa sổ Data
def open_data_window():
    global csv_file_path, data_df
    csv_file_path = None
    data_df = pd.DataFrame(columns=["SS", "Mã hàng", "MSKH", "Tên khách hàng", "Gửi Lot", "Gửi dữ liệu", "Nội dung gửi email", "Địa chỉ gửi email"])

    data_window = tk.Toplevel(root)
    data_window.title("Data")
    data_window.geometry("1200x600")
    data_window.configure(bg="#e8ecef")

    # Frame cho bảng dữ liệu
    frame_table = tk.Frame(data_window, bg="#e8ecef")
    frame_table.pack(pady=10, fill="both", expand=True)

    # Tạo Treeview để hiển thị bảng
    tree = ttk.Treeview(frame_table, columns=list(data_df.columns), show="headings", height=20)
    for col in data_df.columns:
        tree.heading(col, text=col)
        tree.column(col, width=150, anchor="center")
    tree.pack(side=tk.LEFT, fill="both", expand=True)

    # Thanh cuộn
    scrollbar = ttk.Scrollbar(frame_table, orient="vertical", command=tree.yview)
    scrollbar.pack(side=tk.RIGHT, fill="y")
    tree.configure(yscrollcommand=scrollbar.set)

    # Frame cho các nút
    frame_buttons = tk.Frame(data_window, bg="#e8ecef")
    frame_buttons.pack(pady=10)

    # Hàm cập nhật bảng
    def update_table(df):
        tree.delete(*tree.get_children())
        for _, row in df.iterrows():
            tree.insert("", "end", values=tuple(row))

    # Hàm thêm dữ liệu
    def add_data():
        add_window = tk.Toplevel(data_window)
        add_window.title("Add Data")
        add_window.geometry("400x500")
        add_window.configure(bg="#e8ecef")

        entries = {}
        for i, col in enumerate(data_df.columns):
            tk.Label(add_window, text=f"{col}:", font=("Helvetica", 12), bg="#e8ecef").grid(row=i, column=0, padx=10, pady=10, sticky="e")
            entry = tk.Entry(add_window, width=30, font=("Helvetica", 12))
            entry.grid(row=i, column=1, padx=10, pady=10)
            entries[col] = entry

        def save_data():
            global data_df
            new_data = {col: entries[col].get() for col in data_df.columns}
            if all(new_data.values()):  # Kiểm tra không để trống
                data_df = pd.concat([data_df, pd.DataFrame([new_data])], ignore_index=True)
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
        global data_df
        index = int(tree.index(selected[0]))
        data_df = data_df.drop(index).reset_index(drop=True)
        update_table(data_df)

    # Hàm cập nhật file CSV
    def update_csv_link():
        global csv_file_path, data_df
        file_path = filedialog.askopenfilename(title="Chọn file CSV", filetypes=[("CSV files", "*.csv")])
        if file_path:
            csv_file_path = file_path
            new_df = pd.read_csv(file_path, encoding='utf-8-sig')
            # Đồng bộ hóa cột với data_df
            new_df = new_df.reindex(columns=data_df.columns, fill_value="")
            # Gộp dữ liệu, thay thế nếu trùng SS, Mã hàng, MSKH
            combined_df = pd.concat([data_df, new_df]).drop_duplicates(subset=["SS", "Mã hàng", "MSKH"], keep="last").reset_index(drop=True)
            data_df = combined_df
            update_table(data_df)
            messagebox.showinfo("Thông báo", f"Đã cập nhật dữ liệu từ file: {file_path}")

    # Hàm lọc dữ liệu
    def filter_data():
        filter_window = tk.Toplevel(data_window)
        filter_window.title("Filter Data")
        filter_window.geometry("400x300")
        filter_window.configure(bg="#e8ecef")

        tk.Label(filter_window, text="Chọn cột để lọc:", font=("Helvetica", 12), bg="#e8ecef").pack(pady=10)
        column_var = tk.StringVar(value=data_df.columns[0])
        tk.OptionMenu(filter_window, column_var, *data_df.columns).pack(pady=10)
        tk.Label(filter_window, text="Giá trị lọc:", font=("Helvetica", 12), bg="#e8ecef").pack(pady=10)
        filter_entry = tk.Entry(filter_window, width=30, font=("Helvetica", 12))
        filter_entry.pack(pady=10)

        def apply_filter():
            global data_df
            col = column_var.get()
            value = filter_entry.get()
            filtered_df = data_df[data_df[col].astype(str).str.contains(value, case=False, na=False)]
            update_table(filtered_df)

        tk.Button(filter_window, text="Apply Filter", command=apply_filter, font=("Helvetica", 12, "bold"), bg="#3498db", fg="white", padx=20, pady=10).pack(pady=20)

    # Các nút trong frame_buttons
    tk.Button(frame_buttons, text="Add Data", command=add_data, font=("Helvetica", 12, "bold"), bg="#27ae60", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_buttons, text="Delete Data", command=delete_data, font=("Helvetica", 12, "bold"), bg="#e74c3c", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_buttons, text="Update CSV Link", command=update_csv_link, font=("Helvetica", 12, "bold"), bg="#f39c12", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)
    tk.Button(frame_buttons, text="Filter Data", command=filter_data, font=("Helvetica", 12, "bold"), bg="#3498db", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)

    # Hàm lưu dữ liệu khi đóng cửa sổ
    def on_data_close():
        global csv_file_path, data_df
        if csv_file_path and not data_df.empty:
            data_df.to_csv(csv_file_path, index=False, encoding='utf-8-sig')
            messagebox.showinfo("Thông báo", f"Dữ liệu đã được lưu vào: {csv_file_path}")
        data_window.destroy()

    data_window.protocol("WM_DELETE_WINDOW", on_data_close)

# Tạo cửa sổ chính
root = tk.Tk()
root.title("Gửi Dữ Liệu Khách Hàng")
root.geometry("1200x600")
root.configure(bg="#e8ecef")

icon = tk.PhotoImage(file="LogoMabuchiWhite.png")
root.iconphoto(True, icon)

root.bind("<Configure>", on_resize)
root.bind("<ButtonRelease-1>", on_release)
root.bind("<Alt-Shift-S>", open_config)

# Thêm menu File
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)
file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Data", command=open_data_window)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=thoat)

frame_title = tk.Frame(root, bg="#e8ecef")
frame_title.pack(pady=20)
tk.Label(frame_title, text="GỬI EMAIL KHÁCH HÀNG TỰ ĐỘNG", font=("Helvetica", 24, "bold"), bg="#e8ecef", fg="#2c3e50").pack()

frame_top = tk.Frame(root, bg="#e8ecef")
frame_top.pack(pady=50)
tk.Label(frame_top, text="Chọn file Excel 4 Điểm:", font=("Helvetica", 14, "bold"), bg="#e8ecef", fg="#2c3e50").grid(row=0, column=0, padx=20, pady=20, sticky="e")
entry_file_excel = tk.Entry(frame_top, width=60, font=("Helvetica", 12), bd=2, relief="sunken", bg="#ffffff")
entry_file_excel.grid(row=0, column=1, padx=20, pady=20)
tk.Button(frame_top, text="Chọn file", command=chon_file_excel, font=("Helvetica", 11, "bold"), bg="#27ae60", fg="white", activebackground="#219653", bd=0, padx=20, pady=10).grid(row=0, column=2, padx=20, pady=20)

tk.Label(frame_top, text="Chọn file TXT dữ liệu tháng:", font=("Helvetica", 14, "bold"), bg="#e8ecef", fg="#2c3e50").grid(row=1, column=0, padx=20, pady=20, sticky="e")
entry_file_txt = tk.Entry(frame_top, width=60, font=("Helvetica", 12), bd=2, relief="sunken", bg="#ffffff")
entry_file_txt.grid(row=1, column=1, padx=20, pady=20)
tk.Button(frame_top, text="Chọn file", command=chon_file_txt, font=("Helvetica", 11, "bold"), bg="#27ae60", fg="white", activebackground="#219653", bd=0, padx=20, pady=10).grid(row=1, column=2, padx=20, pady=20)

frame_bottom = tk.Frame(root, bg="#e8ecef")
frame_bottom.pack(pady=50)
tk.Button(frame_bottom, text="Gửi dữ liệu khách hàng", command=gui_du_lieu, font=("Helvetica", 14, "bold"), bg="#3498db", fg="white", activebackground="#2980b9", bd=0, padx=30, pady=15).pack(side=tk.LEFT, padx=40)
tk.Button(frame_bottom, text="Thoát", command=thoat, font=("Helvetica", 14, "bold"), bg="#e74c3c", fg="white", activebackground="#c0392b", bd=0, padx=30, pady=15).pack(side=tk.LEFT, padx=40)

# Chạy chương trình
root.mainloop()