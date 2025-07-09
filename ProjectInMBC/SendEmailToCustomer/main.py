import tkinter as tk
from tkinter import messagebox
import os
from ult.SendEmail.Guidle.gui import create_main_window, show_send_frame
from ult.SendEmail.Guidle.config import open_config_window
from ult.SendEmail.File.Data.file_data import open_data_window
from ult.SendEmail.File.email import open_email_window

def main():
    root = tk.Tk()
    root.title("Gửi Dữ Liệu Khách Hàng")
    root.geometry("1200x600")
    root.configure(bg="#e8ecef")

    # Load icon
    icon_path = "LogoMabuchiWhite.png"
    if os.path.exists(icon_path):
        try:
            icon = tk.PhotoImage(file=icon_path)
            root.iconphoto(True, icon)
        except tk.TclError as e:
            print(f"Lỗi khi load icon {icon_path}: {e}")
    else:
        print(f"Không tìm thấy file {icon_path} trong thư mục hiện tại.")

    # Menu
    menu_bar = tk.Menu(root)
    root.config(menu=menu_bar)
    
    file_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="File", menu=file_menu)
    file_menu.add_command(label="Data", command=lambda: open_data_window(root))
    file_menu.add_command(label="Email", command=lambda: open_email_window(root))
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=lambda: root.destroy() if messagebox.askokcancel("Thoát", "Bạn có chắc chắn muốn thoát?") else None)

    send_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Gửi dữ liệu", menu=send_menu)
    send_menu.add_command(label="Email Tháng", command=lambda: show_send_frame(root, "Tháng"))
    send_menu.add_command(label="Email Ngày", command=lambda: show_send_frame(root, "Ngày"))
    send_menu.add_command(label="Email Tuần", command=lambda: show_send_frame(root, "Tuần"))


    # Bind phím tắt
    root.bind("<Shift-Alt-S>", lambda event: open_config_window(root))
    root.bind("<Configure>", lambda e: root.title(f"Gửi Dữ Liệu Khách Hàng - {root.winfo_width()}x{root.winfo_height()}"))
    root.bind("<ButtonRelease-1>", lambda e: root.title("Gửi Dữ Liệu Khách Hàng"))

    # Cập nhật lệnh cho nút 
    btn_email_month, btn_email_week, btn_email_day, btn_monthly = create_main_window(root)

    # Gán lệnh cho các nút
    btn_email_month.config(command=lambda: show_send_frame(root, "Tháng"))
    btn_email_week.config(command=lambda: show_send_frame(root, "Tuần"))
    btn_email_day.config(command=lambda: show_send_frame(root, "Ngày"))
    btn_monthly.config(command=lambda: messagebox.showinfo("Thông báo", "Chức năng Gửi Monthly đang phát triển!"))

    root.mainloop()

if __name__ == "__main__":
    main()