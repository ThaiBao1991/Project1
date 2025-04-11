import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from File.Data.file_data import open_data_window
import os
import pandas as pd

# Tạo thư mục Data Test nếu chưa có
if not os.path.exists("Data Test"):
    os.makedirs("Data Test")

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

    # Cập nhật bảng
    update_table(data_df)

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
    for encoding in encodings:
        try:
            txt_data = pd.read_csv(txt_file, sep=',', encoding=encoding)  # Dùng dấu phẩy vì dữ liệu mẫu là CSV
            txt_data.to_csv("data_work.csv", index=False, encoding='utf-8-sig')
            messagebox.showinfo("Thông báo", f"Dữ liệu từ {txt_file} đã được chuyển sang data_work.csv (encoding: {encoding})")
            return
        except Exception as e:
            continue
    messagebox.showerror("Lỗi", f"Không thể đọc file TXT: {txt_file}\nVui lòng kiểm tra định dạng hoặc mã hóa của file.")

def gui_du_lieu(file_txt, period, df):
    if not file_txt:
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn file TXT trước!")
        return
    
    work_df = pd.read_csv("data_work.csv", encoding='utf-8-sig')
    updated = False
    for index, row in df.iterrows():
        if row["Status"] != "Đã gửi":  # Chỉ xử lý các dòng chưa gửi
            ss = row["SS"]
            mskh = row["MSKH"]
            filtered_data = work_df[(work_df["Invoice No"] == ss) & (work_df["End Customer No"] == mskh)]
            if not filtered_data.empty:
                df.at[index, "Status"] = "Đã gửi"
                updated = True
    
    if updated:
        save_status(period, df)
        update_table(df)
        messagebox.showinfo("Thông báo", f"Đã gửi dữ liệu cho các dòng chưa có trạng thái 'Đã gửi' trong {period}!")
    else:
        messagebox.showinfo("Thông báo", "Không có dữ liệu nào cần gửi!")

def show_details(event):
    selected = tree.selection()
    if not selected:
        return
    index = int(tree.index(selected[0]))
    ss = data_df.at[index, "SS"]
    mskh = data_df.at[index, "MSKH"]

    work_df = pd.read_csv("data_work.csv", encoding='utf-8-sig')
    filtered_data = work_df[(work_df["Invoice No"] == ss) & (work_df["End Customer No"] == mskh)][["End Customer No", "Sales Part No", "Lot No"]]

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

def update_table(df):
    tree.delete(*tree.get_children())
    for _, row in df.iterrows():
        tree.insert("", "end", values=tuple(row))

def save_status(period, df):
    status_file = f"Data Test/data_{period.lower()}.csv"
    df.to_csv(status_file, index=False, encoding='utf-8-sig')

def reset_status():
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn một dòng để reset trạng thái!")
        return
    global data_df
    data_df["Status"] = ""
    save_status(current_period.get(), data_df)
    update_table(data_df)
    messagebox.showinfo("Thông báo", "Đã reset toàn bộ trạng thái!")

root = tk.Tk()
root.title("Gửi Dữ Liệu Khách Hàng")
root.geometry("1200x600")
root.configure(bg="#e8ecef")

icon = tk.PhotoImage(file="LogoMabuchiWhite.png")
root.iconphoto(True, icon)

root.bind("<Configure>", on_resize)
root.bind("<ButtonRelease-1>", on_release)

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

# Frame gửi dữ liệu (ẩn ban đầu)
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
tree.bind("<Double-1>", show_details)  # Double-click để xem chi tiết

# Nút điều khiển trạng thái
frame_status_buttons = tk.Frame(send_frame, bg="#e8ecef")
frame_status_buttons.pack(pady=10)
tk.Button(frame_status_buttons, text="Gửi dữ liệu", command=lambda: gui_du_lieu(entry_file.get(), current_period.get(), data_df), 
          font=("Helvetica", 12, "bold"), bg="#27ae60", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)
tk.Button(frame_status_buttons, text="Reset", command=reset_status, 
          font=("Helvetica", 12, "bold"), bg="#e74c3c", fg="white", padx=20, pady=10).pack(side=tk.LEFT, padx=10)

btn_send = tk.Button(send_frame, text="Gửi dữ liệu khách hàng", font=("Helvetica", 14, "bold"), bg="#3498db", fg="white", padx=30, pady=15)
btn_send.pack(pady=10)
btn_back = tk.Button(send_frame, text="Quay lại", command=back_to_main, font=("Helvetica", 14, "bold"), bg="#e74c3c", fg="white", padx=30, pady=15)
btn_back.pack(pady=10)

# Biến toàn cục
current_period = tk.StringVar()

# Cập nhật period khi nhấp nút
for period in ["Tháng", "Tuần", "Ngày"]:
    send_menu.entryconfig(f"Email {period}", command=lambda p=period: [current_period.set(p), show_send_frame(p)])
    frame_buttons.winfo_children()[["Tháng", "Tuần", "Ngày"].index(period)].config(command=lambda p=period: [current_period.set(p), show_send_frame(p)])

root.mainloop()