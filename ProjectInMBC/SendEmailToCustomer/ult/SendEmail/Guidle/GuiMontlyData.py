import tkinter as tk
from tkinter import filedialog, messagebox

def open_gui_monthly_data(root):
    window = tk.Toplevel(root)
    window.title("Gửi Monthly Data")
    window.geometry("600x300")
    window.configure(bg="#e8ecef")

    tk.Label(window, text="Giao diện Gửi Monthly Data", font=("Helvetica", 16, "bold"), bg="#e8ecef").pack(pady=20)

    # Thêm các widget cần thiết cho Monthly Data ở đây
    # Ví dụ: nút chọn file, nhập thông tin, ...

    tk.Button(window, text="Đóng", command=window.destroy, bg="#3498db", fg="white", font=("Helvetica", 12, "bold")).pack(pady=20)