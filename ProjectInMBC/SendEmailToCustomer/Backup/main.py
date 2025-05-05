import tkinter as tk
from tkinter import messagebox
import os
from ult.SendEmail.Guidle.gui import create_main_window, show_send_frame
from ult.SendEmail.Guidle.config import open_config_window
from ult.SendEmail.File.Data.file_data import open_data_window

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
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=lambda: root.destroy() if messagebox.askokcancel("Thoát", "Bạn có chắc chắn muốn thoát?") else None)

    send_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Gửi dữ liệu", menu=send_menu)
    send_menu.add_command(label="Email Tháng", command=lambda: show_send_frame(root, "Tháng"))
    send_menu.add_command(label="Email Ngày", command=lambda: show_send_frame(root, "Ngày"))
    send_menu.add_command(label="Email Tuần", command=lambda: show_send_frame(root, "Tuần"))

    # Tạo frame chính
    frame_buttons = create_main_window(root)
    frame_buttons.pack(pady=50, fill="both", expand=True)

    # Bind phím tắt
    root.bind("<Shift-Alt-S>", lambda event: open_config_window(root))
    root.bind("<Configure>", lambda e: root.title(f"Gửi Dữ Liệu Khách Hàng - {root.winfo_width()}x{root.winfo_height()}"))
    root.bind("<ButtonRelease-1>", lambda e: root.title("Gửi Dữ Liệu Khách Hàng"))

    # Cập nhật lệnh cho nút
    buttons = frame_buttons.winfo_children()
    if len(buttons) == 3:  # Đảm bảo có 3 nút
        for period, button in zip(["Tháng", "Tuần", "Ngày"], buttons):
            button.config(command=lambda p=period: show_send_frame(root, p))

    root.mainloop()

if __name__ == "__main__":
    main()