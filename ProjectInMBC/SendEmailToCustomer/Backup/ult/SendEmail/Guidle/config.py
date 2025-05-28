import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd

CONFIG_FILE = "config.json"

def load_config():
    """Đọc cấu hình từ config.json"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_config(config):
    """Lưu cấu hình vào config.json"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def open_config_window(root, event=None):
    """Mở cửa sổ nhập mật khẩu để vào config"""
    password_window = tk.Toplevel(root)
    password_window.title("Nhập Password")
    password_window.geometry("300x150")
    password_window.configure(bg="#e8ecef")
    tk.Label(password_window, text="Nhập password:", font=("Helvetica", 12), bg="#e8ecef").pack(pady=10)
    entry_password = tk.Entry(password_window, show="*", font=("Helvetica", 12))
    entry_password.pack(pady=10)
    tk.Button(password_window, text="Xác nhận", command=lambda: check_password(root, entry_password.get(), password_window), 
              font=("Helvetica", 12, "bold"), bg="#3498db", fg="white", padx=20, pady=10).pack(pady=10)

def check_password(root, password, window):
    """Kiểm tra mật khẩu"""
    if password == "bao1991":
        window.destroy()
        show_config_window(root)
    else:
        messagebox.showerror("Lỗi", "Password sai!")
        window.destroy()

def show_config_window(root):
    """Mở cửa sổ cấu hình"""
    config_window = tk.Toplevel(root)
    config_window.title("Config")
    config_window.geometry("400x300")
    config_window.configure(bg="#e8ecef")
    menu_bar = tk.Menu(config_window)
    config_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Config", menu=config_menu)
    config_menu.add_command(label="Config Gửi Email Tự động", command=lambda: [config_window.destroy(), show_email_config_window(root)])
    config_menu.add_command(label="Config Montly Data", command=config_monthly_data)
    config_window.config(menu=menu_bar)

def show_email_config_window(root):
    """Mở cửa sổ config email"""
    email_config_window = tk.Toplevel(root)
    email_config_window.title("Config Gửi Email Khách Hàng")
    email_config_window.geometry("600x400")
    email_config_window.configure(bg="#e8ecef")

    config = load_config()

    frame_origin = tk.Frame(email_config_window, bg="#e8ecef")
    frame_origin.pack(pady=10, fill="x", padx=20)
    tk.Label(frame_origin, text="Địa chỉ lưu data gốc:", font=("Helvetica", 12), bg="#e8ecef").pack(side=tk.LEFT)
    entry_origin = tk.Entry(frame_origin, width=50, font=("Helvetica", 12))
    entry_origin.pack(side=tk.LEFT, padx=10)
    entry_origin.insert(0, config.get("data_origin_path", ""))
    tk.Button(frame_origin, text="Chọn", command=lambda: select_folder(entry_origin), 
              font=("Helvetica", 12, "bold"), bg="#3498db", fg="white", padx=10).pack(side=tk.LEFT)

    frame_temp = tk.Frame(email_config_window, bg="#e8ecef")
    frame_temp.pack(pady=10, fill="x", padx=20)
    tk.Label(frame_temp, text="Địa chỉ lưu data tạm:", font=("Helvetica", 12), bg="#e8ecef").pack(side=tk.LEFT)
    entry_temp = tk.Entry(frame_temp, width=50, font=("Helvetica", 12))
    entry_temp.pack(side=tk.LEFT, padx=10)
    entry_temp.insert(0, config.get("data_temp_path", ""))
    tk.Button(frame_temp, text="Chọn", command=lambda: select_folder(entry_temp), 
              font=("Helvetica", 12, "bold"), bg="#3498db", fg="white", padx=10).pack(side=tk.LEFT)

    frame_data = tk.Frame(email_config_window, bg="#e8ecef")
    frame_data.pack(pady=10, fill="x", padx=20)
    tk.Label(frame_data, text="File Data (Excel):", font=("Helvetica", 12), bg="#e8ecef").pack(side=tk.LEFT)
    entry_data = tk.Entry(frame_data, width=50, font=("Helvetica", 12))
    entry_data.pack(side=tk.LEFT, padx=10)
    entry_data.insert(0, config.get("data_file_path", ""))
    tk.Button(frame_data, text="Chọn", command=lambda: select_file(entry_data), 
              font=("Helvetica", 12, "bold"), bg="#3498db", fg="white", padx=10).pack(side=tk.LEFT)

    tk.Button(email_config_window, text="Xuất Data", command=lambda: xuat_data(entry_data), 
              font=("Helvetica", 12, "bold"), bg="#f39c12", fg="white", padx=20, pady=10).pack(pady=10)

    tk.Button(email_config_window, text="Save", command=lambda: save_email_config(entry_origin.get(), entry_temp.get(), entry_data.get()), 
              font=("Helvetica", 12, "bold"), bg="#27ae60", fg="white", padx=20, pady=10).pack(pady=10)

    tk.Button(email_config_window, text="Quay lại", command=lambda: [email_config_window.destroy(), show_config_window(root)], 
              font=("Helvetica", 12, "bold"), bg="#e74c3c", fg="white", padx=20, pady=10).pack(pady=10)

def select_folder(entry):
    """Chọn thư mục và cập nhật entry"""
    folder_path = filedialog.askdirectory(title="Chọn thư mục")
    if folder_path:
        entry.delete(0, tk.END)
        entry.insert(0, folder_path)

def select_file(entry):
    """Chọn file Excel và cập nhật entry"""
    file_path = filedialog.askopenfilename(
        title="Chọn file Excel",
        filetypes=[("Excel files", "*.xlsx *.xls")]
    )
    if file_path:
        entry.delete(0, tk.END)
        entry.insert(0, file_path)

def xuat_data(entry_data):
    """Xuất dữ liệu từ file Excel với cột được chọn"""
    data_path = entry_data.get()
    if not data_path:
        messagebox.showwarning("Cảnh báo", "Vui lòng chọn file Data trước khi xuất!")
        return

    column_window = tk.Toplevel()
    column_window.title("Chọn cột để xuất")
    column_window.geometry("400x200")
    column_window.configure(bg="#e8ecef")
    column_window.lift()
    column_window.grab_set()

    frame_start = tk.Frame(column_window, bg="#e8ecef")
    frame_start.pack(pady=10, fill="x", padx=20)
    tk.Label(frame_start, text="Cột bắt đầu (số từ 0):", font=("Helvetica", 12), bg="#e8ecef").pack(side=tk.LEFT)
    entry_start = tk.Entry(frame_start, width=10, font=("Helvetica", 12))
    entry_start.pack(side=tk.LEFT, padx=10)

    frame_end = tk.Frame(column_window, bg="#e8ecef")
    frame_end.pack(pady=10, fill="x", padx=20)
    tk.Label(frame_end, text="Cột kết thúc (số từ 0):", font=("Helvetica", 12), bg="#e8ecef").pack(side=tk.LEFT)
    entry_end = tk.Entry(frame_end, width=10, font=("Helvetica", 12))
    entry_end.pack(side=tk.LEFT, padx=10)

    def confirm_export():
        try:
            df = pd.read_excel(data_path, header=1)
            num_columns = len(df.columns)
            start_col = entry_start.get().strip()
            end_col = entry_end.get().strip()

            if not start_col and not end_col:
                output_df = df
            else:
                if not start_col:
                    messagebox.showwarning("Cảnh báo", "Vui lòng nhập cột bắt đầu!")
                    return
                try:
                    start_idx = int(start_col)
                    if start_idx < 0:
                        messagebox.showerror("Lỗi", "Cột bắt đầu phải là số không âm!")
                        return
                    if start_idx >= num_columns:
                        messagebox.showerror("Lỗi", f"Cột bắt đầu vượt quá số cột ({num_columns})!")
                        return
                except ValueError:
                    messagebox.showerror("Lỗi", "Cột bắt đầu phải là số nguyên!")
                    return

                if end_col:
                    try:
                        end_idx = int(end_col)
                        if end_idx < 0:
                            messagebox.showerror("Lỗi", "Cột kết thúc phải là số không âm!")
                            return
                        if end_idx >= num_columns:
                            messagebox.showerror("Lỗi", f"Cột kết thúc vượt quá số cột ({num_columns})!")
                            return
                        if end_idx < start_idx:
                            messagebox.showerror("Lỗi", "Cột kết thúc phải lớn hơn hoặc bằng cột bắt đầu!")
                            return
                    except ValueError:
                        messagebox.showerror("Lỗi", "Cột kết thúc phải là số nguyên!")
                        return
                    output_df = df.iloc[:, start_idx:end_idx + 1]
                else:
                    output_df = df.iloc[:, start_idx:]

            output_path = os.path.splitext(data_path)[0] + "_filtered.csv"
            output_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            messagebox.showinfo("Thông báo", f"Dữ liệu đã được xuất thành công ra file: {output_path}")
            column_window.destroy()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Đã xảy ra lỗi khi xử lý file: {str(e)}")

    tk.Button(column_window, text="Xác nhận", command=confirm_export, 
              font=("Helvetica", 12, "bold"), bg="#27ae60", fg="white", padx=20, pady=10).pack(pady=20)

def save_email_config(origin_path, temp_path, data_path):
    """Lưu cấu hình email"""
    config = load_config()
    config["data_origin_path"] = origin_path
    config["data_temp_path"] = temp_path
    config["data_file_path"] = data_path
    save_config(config)
    messagebox.showinfo("Thông báo", "Đã lưu cấu hình thành công!")

def config_monthly_data():
    """Placeholder cho config dữ liệu tháng"""
    messagebox.showinfo("Config", "Config Montly Data (Chưa triển khai chi tiết)")