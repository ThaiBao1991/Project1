import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import pandas as pd
import json

try:
    from File.Data.file_data import open_data_window
except ImportError:
    def open_data_window(root):
        messagebox.showerror("Lỗi", "Không tìm thấy module file_data. Vui lòng kiểm tra đường dẫn!")

# Tạo thư mục Data Test nếu chưa có
if not os.path.exists("Data Test"):
    os.makedirs("Data Test")

# File config
CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def thoat():
    if messagebox.askokcancel("Thoát", "Bạn có chắc chắn muốn thoát?"):
        root.destroy()

def on_resize(event):
    width = root.winfo_width()
    height = root.winfo_height()
    root.title(f"Gửi Dữ Liệu Khách Hàng - {width}x{height}")

def on_release(event):
    root.title("Gửi Dữ Liệu Khách Hàng")

def show_send_frame(period):
    frame_buttons.pack_forget()
    send_frame.pack(pady=10, fill="both", expand=True)

    label_file.config(text=f"Chọn file TXT dữ liệu {period.lower()}:")
    btn_send.config(command=lambda: gui_du_lieu(entry_file.get(), period, data_df))

    # Đường dẫn file trạng thái
    status_file = f"Data Test/data_{period.lower()}.csv"
    columns = ["SS", "Mã hàng", "MSKH", "Gửi Lot", "Status"]
    
    try:
        # Tải dữ liệu từ data.csv và file status
        base_data = pd.read_csv("data.csv", encoding='utf-8-sig')[["SS", "Mã hàng", "MSKH", "Gửi Lot"]]
        if os.path.exists(status_file):
            status_data = pd.read_csv(status_file, encoding='utf-8-sig')
            global data_df
            data_df = base_data.merge(status_data[["SS", "Mã hàng", "MSKH", "Status"]], 
                                     on=["SS", "Mã hàng", "MSKH"], how="left").reindex(columns=columns, fill_value="")
        else:
            data_df = base_data.reindex(columns=columns, fill_value="")
            data_df["Status"] = ""
            data_df.to_csv(status_file, index=False, encoding='utf-8-sig')

        global original_df
        original_df = data_df.copy()  # Lưu dữ liệu gốc
        update_table(data_df)

        # Gắn hàm lọc vào tiêu đề cột
        for col in data_df.columns:
            tree.heading(col, text=col, command=lambda c=col: show_filter_entry(c, tree, root))
    except FileNotFoundError:
        messagebox.showerror("Lỗi", "Không tìm thấy file data.csv!")
        back_to_main()
        return
    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi tải dữ liệu: {str(e)}")
        back_to_main()
        return

def back_to_main():
    send_frame.pack_forget()
    frame_buttons.pack(pady=50)

def chon_file_txt():
    file_path = filedialog.askopenfilename(
        title="Chọn file TXT",
        filetypes=[("Text files", "*.txt")]
    )
    if file_path:
        entry_file.delete(0, tk.END)
        entry_file.insert(0, file_path)
        convert_txt_to_csv(file_path)

def convert_txt_to_csv(txt_file):
    encodings = ['utf-8-sig', 'utf-16', 'latin1']
    separators = ['\t', ',', ' ']
    
    for encoding in encodings:
        for sep in separators:
            try:
                txt_data = pd.read_csv(txt_file, sep=sep, encoding=encoding)
                if len(txt_data.columns) > 1:
                    txt_data.to_csv("data_work.csv", index=False, encoding='utf-8-sig')
                    messagebox.showinfo("Thông báo", f"Dữ liệu từ {txt_file} đã được chuyển sang data_work.csv (sep: '{sep}', encoding: {encoding})")
                    print(f"Các cột trong data_work.csv: {txt_data.columns.tolist()}")
                    return
            except Exception as e:
                print(f"Lỗi với encoding {encoding} và sep '{sep}': {e}")
                continue
    
    messagebox.showerror("Lỗi", f"Không thể đọc file TXT: {txt_file}\nDữ liệu không được tách thành cột. Vui lòng kiểm tra định dạng file.")

def gui_du_lieu(file_txt, period, df):
    if not file_txt:
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn file TXT trước!")
        return
    
    try:
        work_df = pd.read_csv("data_work.csv", encoding='utf-8-sig')
        updated = False
        for index, row in df.iterrows():
            if row["Status"] != "Đã xác nhận" and row["Status"] != "Đã gửi dữ liệu":
                ss = row["SS"]
                mskh = row["MSKH"]
                filtered_data = work_df[(work_df["Sales Part No"] == ss) & (work_df["End Customer No"] == mskh)]
                if not filtered_data.empty:
                    df.at[index, "Status"] = "Đã xác nhận"
                    updated = True
        
        if updated:
            save_status(period, df)
            update_table(df)
            messagebox.showinfo("Thông báo", f"Đã xác nhận dữ liệu cho {period}!")
        else:
            messagebox.showinfo("Thông báo", "Không có dữ liệu nào cần xác nhận!")
    except FileNotFoundError:
        messagebox.showerror("Lỗi", "Không tìm thấy file data_work.csv!")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi xử lý dữ liệu: {str(e)}")

def send_all_data(period, df):
    df.loc[df["Status"] == "Đã xác nhận", "Status"] = "Đã gửi dữ liệu"
    save_status(period, df)
    update_table(df)
    messagebox.showinfo("Thông báo", "Đã gửi toàn bộ dữ liệu đã xác nhận!")

def send_selected_data(period, df):
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn các dòng để gửi!")
        return
    for item in selected:
        index = int(tree.index(item))
        if df.at[index, "Status"] == "Đã xác nhận":
            df.at[index, "Status"] = "Đã gửi dữ liệu"
    save_status(period, df)
    update_table(df)
    messagebox.showinfo("Thông báo", "Đã gửi các dòng dữ liệu đang chọn!")

def show_details(event):
    selected = tree.selection()
    if not selected:
        return
    index = int(tree.index(selected[0]))
    ss = data_df.at[index, "SS"]
    mskh = data_df.at[index, "MSKH"]
    try:
        work_df = pd.read_csv("data_work.csv", encoding='utf-8-sig')
        filtered_data = work_df[(work_df["Sales Part No"] == ss) & (work_df["End Customer No"] == mskh)][["End Customer No", "Sales Part No", "Lot No"]]

        if filtered_data.empty:
            messagebox.showinfo("Thông báo", "Không tìm thấy dữ liệu chi tiết!")
            return

        detail_window = tk.Toplevel(root)
        detail_window.title(f"Chi tiết - SS: {ss}, MSKH: {mskh}")
        detail_window.geometry("600x400")

        detail_tree = ttk.Treeview(detail_window, columns=["End Customer No", "Sales Part No", "Lot No"], show="headings")
        for col in ["End Customer No", "Sales Part No", "Lot No"]:
            detail_tree.heading(col, text=col)
            detail_tree.column(col, width=180, anchor="center")
        detail_tree.pack(fill="both", expand=True)

        for _, row in filtered_data.iterrows():
            detail_tree.insert("", "end", values=(row["End Customer No"], row["Sales Part No"], row["Lot No"]))
    except FileNotFoundError:
        messagebox.showerror("Lỗi", "Không tìm thấy file data_work.csv!")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Lỗi khi hiển thị chi tiết: {str(e)}")

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

def save_status(period, df):
    status_file = f"Data Test/data_{period.lower()}.csv"
    df.to_csv(status_file, index=False, encoding='utf-8-sig')

def reset_status():
    global data_df
    data_df["Status"] = ""
    save_status(current_period.get(), data_df)
    update_table(data_df)
    messagebox.showinfo("Thông báo", "Đã reset toàn bộ trạng thái!")

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
        global data_df, filters
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
    global data_df, filters
    filters.clear()
    data_df = original_df.copy()
    update_table(data_df)
    messagebox.showinfo("Thông báo", "Đã hủy tất cả bộ lọc!")

def open_config_window(event=None):
    password_window = tk.Toplevel(root)
    password_window.title("Nhập Password")
    password_window.geometry("300x150")
    tk.Label(password_window, text="Nhập password:").pack(pady=10)
    entry_password = tk.Entry(password_window, show="*")
    entry_password.pack(pady=10)
    tk.Button(password_window, text="Xác nhận", command=lambda: check_password(entry_password.get(), password_window)).pack(pady=10)

def check_password(password, window):
    if password == "bao1991":
        window.destroy()
        show_config_window()
    else:
        messagebox.showerror("Lỗi", "Password sai!")
        window.destroy()

def show_config_window():
    config_window = tk.Toplevel(root)
    config_window.title("Config")
    config_window.geometry("400x300")
    menu_bar = tk.Menu(config_window)
    config_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Config", menu=config_menu)
    config_menu.add_command(label="Config Gửi Email Tự động", command=config_email)
    config_menu.add_command(label="Config Montly Data", command=config_monthly_data)
    config_window.config(menu=menu_bar)

def config_email():
    messagebox.showinfo("Config", "Config Gửi Email Tự động (Chưa triển khai chi tiết)")

def config_monthly_data():
    messagebox.showinfo("Config", "Config Montly Data (Chưa triển khai chi tiết)")

# Khởi tạo cửa sổ gốc
root = tk.Tk()
root.title("Gửi Dữ Liệu Khách Hàng")
root.geometry("1200x600")
root.configure(bg="#e8ecef")

# Khởi tạo các biến toàn cục SAU khi có root
current_period = tk.StringVar()
data_df = None
filters = {}
original_df = None

try:
    icon = tk.PhotoImage(file="LogoMabuchiWhite.png")
    root.iconphoto(True, icon)
except tk.TclError:
    print("Không tìm thấy file LogoMabuchiWhite.png, bỏ qua icon.")

root.bind("<Configure>", on_resize)
root.bind("<ButtonRelease-1>", on_release)
root.bind("<Shift-Alt-S>", open_config_window)

# Menu
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)
file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="File", menu=file_menu)
file_menu.add_command(label="Data", command=lambda: open_data_window(root))
file_menu.add_separator()
file_menu.add_command(label="Exit", command=thoat)

send_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Gửi dữ liệu", menu=send_menu)
send_menu.add_command(label="Email Tháng", command=lambda: show_send_frame("Tháng"))
send_menu.add_command(label="Email Ngày", command=lambda: show_send_frame("Ngày"))
send_menu.add_command(label="Email Tuần", command=lambda: show_send_frame("Tuần"))

# Frame chính ban đầu
frame_title = tk.Frame(root, bg="#e8ecef")
frame_title.pack(pady=20)
tk.Label(frame_title, text="GỬI EMAIL KHÁCH HÀNG TỰ ĐỘNG", font=("Helvetica", 24, "bold"), bg="#e8ecef", fg="#2c3e50").pack()

frame_buttons = tk.Frame(root, bg="#e8ecef")
frame_buttons.pack(pady=50)
tk.Button(frame_buttons, text="Gửi Email Tháng", command=lambda: show_send_frame("Tháng"), font=("Helvetica", 14, "bold"), bg="#3498db", fg="white", padx=30, pady=15).pack(side=tk.LEFT, padx=20)
tk.Button(frame_buttons, text="Gửi Email Tuần", command=lambda: show_send_frame("Tuần"), font=("Helvetica", 14, "bold"), bg="#27ae60", fg="white", padx=30, pady=15).pack(side=tk.LEFT, padx=20)
tk.Button(frame_buttons, text="Gửi Email Ngày", command=lambda: show_send_frame("Ngày"), font=("Helvetica", 14, "bold"), bg="#f39c12", fg="white", padx=30, pady=15).pack(side=tk.LEFT, padx=20)

# Frame gửi dữ liệu
send_frame = tk.Frame(root, bg="#e8ecef")
label_file = tk.Label(send_frame, text="", font=("Helvetica", 14, "bold"), bg="#e8ecef", fg="#2c3e50")
label_file.pack(pady=10)
entry_file = tk.Entry(send_frame, width=60, font=("Helvetica", 12), bd=2, relief="sunken", bg="#ffffff")
entry_file.pack(pady=10)
tk.Button(send_frame, text="Chọn file", command=chon_file_txt, font=("Helvetica", 11, "bold"), bg="#27ae60", fg="white", padx=20, pady=10).pack(pady=10)

# Bảng trạng thái
frame_table = tk.Frame(send_frame, bg="#e8ecef")
frame_table.pack(pady=10, fill="both", expand=True)
tree = ttk.Treeview(frame_table, columns=["SS", "Mã hàng", "MSKH", "Gửi Lot", "Status"], show="headings", height=10)
for col in ["SS", "Mã hàng", "MSKH", "Gửi Lot", "Status"]:
    tree.heading(col, text=col)
    tree.column(col, width=150, anchor="center")
tree.pack(side=tk.LEFT, fill="both", expand=True)
scrollbar = ttk.Scrollbar(frame_table, orient="vertical", command=tree.yview)
scrollbar.pack(side=tk.RIGHT, fill="y")
tree.configure(yscrollcommand=scrollbar.set)
tree.bind("<Double-1>", show_details)

# Nút điều khiển trạng thái
frame_status_buttons = tk.Frame(send_frame, bg="#e8ecef")
frame_status_buttons.pack(pady=10)
tk.Button(frame_status_buttons, text="Xác nhận dữ liệu", command=lambda: gui_du_lieu(entry_file.get(), current_period.get(), data_df), 
          font=("Helvetica", 12, "bold"), bg="#27ae60", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)
tk.Button(frame_status_buttons, text="Reset", command=reset_status, 
          font=("Helvetica", 12, "bold"), bg="#e74c3c", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)
tk.Button(frame_status_buttons, text="Gửi dữ liệu", font=("Helvetica", 12, "bold"), bg="#3498db", fg="white", padx=20, pady=10,
          command=lambda: send_data_menu.post(frame_status_buttons.winfo_children()[2].winfo_rootx(), 
                                             frame_status_buttons.winfo_children()[2].winfo_rooty() + 
                                             frame_status_buttons.winfo_children()[2].winfo_height())).pack(side=tk.LEFT, padx=10)
tk.Button(frame_status_buttons, text="Hủy Filter", command=clear_filter, 
          font=("Helvetica", 12, "bold"), bg="#f39c12", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)

# Menu con cho nút Gửi dữ liệu
send_data_menu = tk.Menu(root, tearoff=0)
send_data_menu.add_command(label="Gửi toàn bộ", command=lambda: send_all_data(current_period.get(), data_df))
send_data_menu.add_command(label="Gửi các dòng đang chọn", command=lambda: send_selected_data(current_period.get(), data_df))

btn_send = tk.Button(send_frame, text="Gửi dữ liệu khách hàng", font=("Helvetica", 14, "bold"), bg="#3498db", fg="white", padx=30, pady=15)
btn_send.pack(pady=10)
btn_back = tk.Button(send_frame, text="Quay lại", command=back_to_main, font=("Helvetica", 14, "bold"), bg="#e74c3c", fg="white", padx=30, pady=15)
btn_back.pack(pady=10)

# Cập nhật period khi nhấp nút
for period in ["Tháng", "Tuần", "Ngày"]:
    send_menu.entryconfig(f"Email {period}", command=lambda p=period: [current_period.set(p), show_send_frame(p)])
    frame_buttons.winfo_children()[["Tháng", "Tuần", "Ngày"].index(period)].config(command=lambda p=period: [current_period.set(p), show_send_frame(p)])

root.mainloop()