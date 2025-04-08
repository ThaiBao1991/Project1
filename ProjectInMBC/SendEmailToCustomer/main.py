import tkinter as tk
from tkinter import filedialog, messagebox
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
        # Đọc file Excel
        df = pd.read_excel(data_path, header=1)  # Bỏ qua dòng tiêu đề đầu tiên, lấy dòng thứ 2 làm header
        
        # In danh sách cột để kiểm tra
        print("Danh sách cột trong file Excel:", df.columns.tolist())
        
        # Tên cột thực tế trong file của bạn
        column_k = 'Gửi Lot DAI DIEN: "DD" Gửi TOAN BO Lot: "TB"'
        
        # Kiểm tra xem cột K có tồn tại không
        if column_k not in df.columns:
            messagebox.showerror("Lỗi", f"Không tìm thấy cột '{column_k}' trong file Excel!")
            return
        
        # Đổi tên cột theo chỉ số của bạn (B, C, F, I, K, L, O, P)
        columns_to_keep = {
            'SS': 'SS',  # Cột B
            'Mã hàng': 'Mã hàng',  # Cột C
            'MSKH': 'MSKH',  # Cột F
            'Tên khách hàng': 'Tên khách hàng',  # Cột I
            column_k: 'Gửi Lot',  # Cột K
            'Gửi dữ liệu [M]': 'Gửi dữ liệu',  # Cột L
            'Nội dung gửi mail': 'Nội dung gửi email',  # Cột O
            'Địa chỉ gửi mail': 'Địa chỉ gửi email'  # Cột P
        }
        
        # Kiểm tra xem tất cả các cột cần giữ có tồn tại không
        missing_cols = [col for col in columns_to_keep.keys() if col not in df.columns]
        if missing_cols:
            messagebox.showerror("Lỗi", f"Không tìm thấy các cột sau trong file Excel: {missing_cols}")
            return
        
        # Lọc dữ liệu có giá trị "TB" hoặc "DD" trong cột K
        filtered_df = df[df[column_k].isin(['TB', 'DD'])]

        # Chỉ giữ lại các cột cần thiết
        filtered_df = filtered_df[list(columns_to_keep.keys())]
        
        # Đổi tên cột trong file xuất
        filtered_df.columns = list(columns_to_keep.values())

        # Đường dẫn file CSV đầu ra (lưu cùng thư mục với file Excel đầu vào)
        output_path = os.path.splitext(data_path)[0] + "_filtered.csv"
        
        # Xuất ra file CSV
        filtered_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        messagebox.showinfo("Thông báo", f"Dữ liệu đã được xuất thành công ra file: {output_path}")
    except Exception as e:
        messagebox.showerror("Lỗi", f"Đã xảy ra lỗi khi xử lý file: {str(e)}")

# Hàm mở cửa sổ Config khi nhấn phím tắt
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

    label_data_update = tk.Label(frame_config, text="Cập nhật dữ liệu khách hàng:", 
                                font=("Helvetica", 14, "bold"), bg="#e8ecef", fg="#2c3e50")
    label_data_update.grid(row=0, column=0, padx=20, pady=20, sticky="e")

    global entry_data_path
    entry_data_path = tk.Entry(frame_config, width=40, font=("Helvetica", 12), bd=2, relief="sunken", bg="#ffffff")
    entry_data_path.grid(row=0, column=1, padx=20, pady=20)

    btn_choose_data = tk.Button(frame_config, text="Chọn file Data", command=chon_file_data, 
                                font=("Helvetica", 11, "bold"), bg="#27ae60", fg="white", 
                                activebackground="#219653", bd=0, padx=20, pady=10)
    btn_choose_data.grid(row=0, column=2, padx=20, pady=20)

    btn_export_data = tk.Button(frame_config, text="Xuất Data", command=xuat_data, 
                                font=("Helvetica", 11, "bold"), bg="#f39c12", fg="white", 
                                activebackground="#e67e22", bd=0, padx=20, pady=10)
    btn_export_data.grid(row=0, column=3, padx=20, pady=20)

    label_save_path = tk.Label(frame_config, text="Địa chỉ lưu dữ liệu:", 
                              font=("Helvetica", 14, "bold"), bg="#e8ecef", fg="#2c3e50")
    label_save_path.grid(row=1, column=0, padx=20, pady=20, sticky="e")

    global entry_save_path
    entry_save_path = tk.Entry(frame_config, width=40, font=("Helvetica", 12), bd=2, relief="sunken", bg="#ffffff")
    entry_save_path.grid(row=1, column=1, padx=20, pady=20)

    btn_choose_path = tk.Button(frame_config, text="Chọn nơi lưu dữ liệu", command=chon_noi_luu, 
                                font=("Helvetica", 11, "bold"), bg="#27ae60", fg="white", 
                                activebackground="#219653", bd=0, padx=20, pady=10)
    btn_choose_path.grid(row=1, column=2, padx=20, pady=20)

    frame_buttons = tk.Frame(config_window, bg="#e8ecef")
    frame_buttons.pack(pady=20)

    btn_save = tk.Button(frame_buttons, text="Save", command=save_config, 
                         font=("Helvetica", 12, "bold"), bg="#3498db", fg="white", 
                         activebackground="#2980b9", bd=0, padx=20, pady=10)
    btn_save.pack(side=tk.LEFT, padx=20)

    btn_close = tk.Button(frame_buttons, text="Close", command=on_config_close, 
                          font=("Helvetica", 12, "bold"), bg="#e74c3c", fg="white", 
                          activebackground="#c0392b", bd=0, padx=20, pady=10)
    btn_close.pack(side=tk.LEFT, padx=20)

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

frame_title = tk.Frame(root, bg="#e8ecef")
frame_title.pack(pady=20)

label_title = tk.Label(frame_title, text="GỬI EMAIL KHÁCH HÀNG TỰ ĐỘNG", 
                      font=("Helvetica", 24, "bold"), bg="#e8ecef", fg="#2c3e50")
label_title.pack()

frame_top = tk.Frame(root, bg="#e8ecef")
frame_top.pack(pady=50)

label_file_excel = tk.Label(frame_top, text="Chọn file Excel 4 Điểm:", font=("Helvetica", 14, "bold"), bg="#e8ecef", fg="#2c3e50")
label_file_excel.grid(row=0, column=0, padx=20, pady=20, sticky="e")

entry_file_excel = tk.Entry(frame_top, width=60, font=("Helvetica", 12), bd=2, relief="sunken", bg="#ffffff")
entry_file_excel.grid(row=0, column=1, padx=20, pady=20)

btn_chon_file_excel = tk.Button(frame_top, text="Chọn file", command=chon_file_excel, 
                                font=("Helvetica", 11, "bold"), bg="#27ae60", fg="white", 
                                activebackground="#219653", bd=0, padx=20, pady=10)
btn_chon_file_excel.grid(row=0, column=2, padx=20, pady=20)

label_file_txt = tk.Label(frame_top, text="Chọn file TXT dữ liệu tháng:", font=("Helvetica", 14, "bold"), bg="#e8ecef", fg="#2c3e50")
label_file_txt.grid(row=1, column=0, padx=20, pady=20, sticky="e")

entry_file_txt = tk.Entry(frame_top, width=60, font=("Helvetica", 12), bd=2, relief="sunken", bg="#ffffff")
entry_file_txt.grid(row=1, column=1, padx=20, pady=20)

btn_chon_file_txt = tk.Button(frame_top, text="Chọn file", command=chon_file_txt, 
                              font=("Helvetica", 11, "bold"), bg="#27ae60", fg="white", 
                              activebackground="#219653", bd=0, padx=20, pady=10)
btn_chon_file_txt.grid(row=1, column=2, padx=20, pady=20)

frame_bottom = tk.Frame(root, bg="#e8ecef")
frame_bottom.pack(pady=50)

btn_gui = tk.Button(frame_bottom, text="Gửi dữ liệu khách hàng", command=gui_du_lieu, 
                    font=("Helvetica", 14, "bold"), bg="#3498db", fg="white", 
                    activebackground="#2980b9", bd=0, padx=30, pady=15)
btn_gui.pack(side=tk.LEFT, padx=40)

btn_thoat = tk.Button(frame_bottom, text="Thoát", command=thoat, 
                      font=("Helvetica", 14, "bold"), bg="#e74c3c", fg="white", 
                      activebackground="#c0392b", bd=0, padx=30, pady=15)
btn_thoat.pack(side=tk.LEFT, padx=40)

# Chạy chương trình
root.mainloop()