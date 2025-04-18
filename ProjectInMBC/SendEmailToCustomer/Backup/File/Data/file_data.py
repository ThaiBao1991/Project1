import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import os

def open_data_window(parent):
    global csv_file_path, data_df, original_df, filters
    csv_file_path = "data.csv"
    
    if os.path.exists(csv_file_path):
        # Thử đọc data.csv với nhiều encoding
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
            data_df = pd.DataFrame()  # Khởi tạo DataFrame rỗng nếu không đọc được
    else:
        data_df = pd.DataFrame()  # Khởi tạo DataFrame rỗng nếu file không tồn tại
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

    # Khởi tạo Treeview với các cột từ data_df (nếu có)
    columns = list(data_df.columns) if not data_df.empty else []
    tree = ttk.Treeview(frame_table, columns=columns, show="headings", height=20)
    for col in columns:
        tree.heading(col, text=col, command=lambda c=col: show_filter_entry(c, tree, data_window))
        tree.column(col, width=150, anchor="center")
    
    # Thêm thanh cuộn ngang và dọc
    scrollbar_y = ttk.Scrollbar(frame_table, orient="vertical", command=tree.yview)
    scrollbar_y.pack(side=tk.RIGHT, fill="y")
    tree.configure(yscrollcommand=scrollbar_y.set)
    
    scrollbar_x = ttk.Scrollbar(frame_table, orient="horizontal", command=tree.xview)
    scrollbar_x.pack(side=tk.BOTTOM, fill="x")
    tree.configure(xscrollcommand=scrollbar_x.set)
    
    tree.pack(fill="both", expand=True)

    frame_buttons = tk.Frame(data_window, bg="#e8ecef")
    frame_buttons.pack(pady=10)

    def update_table(df, tree_widget=tree):
        # Cập nhật cột trong Treeview, giữ nguyên thứ tự từ df.columns
        tree_widget["columns"] = list(df.columns) if not df.empty else []
        tree_widget.delete(*tree_widget.get_children())
        # Cập nhật heading và column mới
        for col in (df.columns if not df.empty else []):
            tree_widget.heading(col, text=col, command=lambda c=col: show_filter_entry(c, tree_widget, data_window))
            tree_widget.column(col, width=150, anchor="center")
        # Thêm dữ liệu
        for _, row in df.iterrows():
            tree_widget.insert("", "end", values=tuple(row))
        # Cập nhật tiêu đề cột với bộ lọc
        for col in (df.columns if not df.empty else []):
            if col in filters and filters[col]:
                tree_widget.heading(col, text=f"{col} (filter)")
            else:
                tree_widget.heading(col, text=col)

    def save_to_csv():
        global csv_file_path, original_df
        if not original_df.empty:
            original_df.to_csv(csv_file_path, index=False, encoding='utf-8-sig')
        else:
            # Nếu DataFrame rỗng, tạo file rỗng
            with open(csv_file_path, 'w', encoding='utf-8-sig') as f:
                f.write("")

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
        add_window.geometry("400x500")
        add_window.configure(bg="#e8ecef")
        add_window.lift()
        add_window.grab_set()

        entries = {}
        # Nếu không có cột, yêu cầu người dùng thêm cột trước
        if data_df.empty and not data_df.columns.any():
            tk.Label(add_window, text="Chưa có cột nào trong data.csv!", font=("Helvetica", 12), bg="#e8ecef").pack(pady=10)
            tk.Label(add_window, text="Vui lòng sử dụng 'Update CSV Link' để thêm file có cột.", font=("Helvetica", 12), bg="#e8ecef").pack(pady=10)
            tk.Button(add_window, text="Đóng", command=add_window.destroy, font=("Helvetica", 12, "bold"), bg="#e74c3c", fg="white", padx=20, pady=10).pack(pady=20)
            return

        required_fields = ["SS", "Mã hàng", "MSKH"] if all(col in data_df.columns for col in ["SS", "Mã hàng", "MSKH"]) else []
        for i, col in enumerate(data_df.columns):
            tk.Label(add_window, text=f"{col}:", font=("Helvetica", 12), bg="#e8ecef").grid(row=i, column=0, padx=10, pady=10, sticky="e")
            entry = tk.Entry(add_window, width=30, font=("Helvetica", 12))
            entry.grid(row=i, column=1, padx=10, pady=10)
            entries[col] = entry
            if col in required_fields:
                tk.Label(add_window, text="*", fg="red", bg="#e8ecef").grid(row=i, column=2, sticky="w")

        def save_data():
            global data_df, original_df
            new_data = {col: entries[col].get() for col in data_df.columns}
            required_data = {k: new_data[k] for k in required_fields if k in new_data}
            if required_fields and not all(required_data.values()):
                messagebox.showwarning("Cảnh báo", "Vui lòng điền đầy đủ các trường bắt buộc (SS, Mã hàng, MSKH nếu có)!")
                return
            data_df = pd.concat([data_df, pd.DataFrame([new_data])], ignore_index=True)
            original_df = data_df.copy()
            save_to_csv()
            update_table(data_df)
            add_window.destroy()

        tk.Button(add_window, text="Save", command=save_data, font=("Helvetica", 12, "bold"), bg="#3498db", fg="white", padx=20, pady=10).grid(row=len(data_df.columns), column=0, columnspan=2, pady=20)

    def delete_data():
        # Tạo menu ngữ cảnh cho xóa dữ liệu
        delete_menu = tk.Menu(data_window, tearoff=0)
        delete_menu.add_command(label="Xóa dữ liệu đang chọn", command=delete_selected_data)
        delete_menu.add_command(label="Xóa toàn bộ dữ liệu", command=delete_all_data)
        
        # Hiển thị menu tại vị trí nút "Delete Data"
        delete_button = frame_buttons.winfo_children()[1]  # Nút "Delete Data" là nút thứ 2
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
            # Thử đọc file với nhiều encoding
            encodings = ['utf-8-sig', 'utf-8', 'latin1', 'iso-8859-1', 'utf-16']
            new_df = None
            for encoding in encodings:
                try:
                    new_df = pd.read_csv(file_path, encoding=encoding)
                    break
                except Exception as e:
                    print(f"Lỗi với encoding {encoding} khi đọc {file_path}: {e}")
                    continue
            if new_df is None:
                messagebox.showerror("Lỗi", f"Không thể đọc file CSV: {file_path}\nVui lòng kiểm tra định dạng hoặc encoding file.")
                return
            
            # Sử dụng cột từ new_df, không giữ cột cũ từ data_df
            all_columns = list(new_df.columns)
            # Chuẩn hóa new_df với các cột này
            new_df = new_df.reindex(columns=all_columns, fill_value="")
            # Nếu data_df có dữ liệu, chuẩn hóa để gộp
            if not data_df.empty:
                data_df = data_df.reindex(columns=all_columns, fill_value="")
                # Gộp dữ liệu
                data_df = pd.concat([data_df, new_df], ignore_index=True)
            else:
                data_df = new_df
            # Xóa trùng lặp nếu có các cột SS, Mã hàng, MSKH
            if all(col in all_columns for col in ["SS", "Mã hàng", "MSKH"]):
                data_df = data_df.drop_duplicates(subset=["SS", "Mã hàng", "MSKH"], keep="last").reset_index(drop=True)
            
            original_df = data_df.copy()
            save_to_csv()
            load_from_csv()
            update_table(data_df)
            messagebox.showinfo("Thông báo", f"Đã cập nhật dữ liệu từ file: {file_path} vào data.csv")

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