import tkinter as tk
import os
from tkinter import messagebox
from ult.SendEmail.Guidle.gui import create_main_window, show_send_frame
from ult.SendEmail.Guidle.config import open_config_window
from ult.SendEmail.File.Data.file_data import open_data_window
from ult.SendEmail.File.email import open_email_window
from ult.FileMontlyData.Guidle.GuiMontlyData import open_gui_monthly_data
from ult.FileMontlyData.File.file_data_montlydata import open_data_montly_window
import shutil
import sys

def get_datasetc_path():
    if hasattr(sys, "_MEIPASS"):
        # Khi chạy từ .exe
        current_base_path = os.path.dirname(sys.executable)
        src_datasetc_path = os.path.join(sys._MEIPASS, "DATASETC")
    else:
        # Khi chạy script Python bình thường
        current_base_path = os.getcwd()
        src_datasetc_path = os.path.join(current_base_path, "DATASETC")

    # Đường dẫn đích mà bạn muốn DATASETC tồn tại bên ngoài .exe
    dst_datasetc_path = os.path.join(current_base_path, "DATASETC")

    # Kiểm tra nếu thư mục DATASETC bên ngoài đã tồn tại
    if not os.path.exists(dst_datasetc_path):
        print(f"Thư mục DATASETC chưa tồn tại tại {dst_datasetc_path}. Đang sao chép dữ liệu mẫu...")
        try:
            # shutil.copytree sẽ sao chép toàn bộ thư mục, bao gồm các thư mục con và tệp con
            shutil.copytree(src_datasetc_path, dst_datasetc_path)
            print("Sao chép thành công DATASETC.")
        except FileExistsError:
            pass
        except Exception as e:
            print(f"Lỗi khi sao chép DATASETC: {e}. Có thể DATASETC trống hoặc có vấn đề về quyền.")
    
    return dst_datasetc_path

get_datasetc_path()


def extract_datasetc_if_needed(force_overwrite=False):
    target_dir = os.path.join(os.getcwd(), "DATASETC")
    if hasattr(sys, "_MEIPASS"):
        source_dir = os.path.join(sys._MEIPASS, "DATASETC")
    else:
        return
    if not os.path.exists(target_dir):
        shutil.copytree(source_dir, target_dir)
    elif force_overwrite:
        # Ghi đè toàn bộ DATASETC ngoài bằng bản trong exe
        shutil.rmtree(target_dir)
        shutil.copytree(source_dir, target_dir)
    else:
        # Bổ sung các file còn thiếu (không ghi đè file đã có)
        for root, dirs, files in os.walk(source_dir):
            rel_path = os.path.relpath(root, source_dir)
            dest_root = os.path.join(target_dir, rel_path)
            os.makedirs(dest_root, exist_ok=True)
            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(dest_root, file)
                if not os.path.exists(dst_file):
                    shutil.copy2(src_file, dst_file)

extract_datasetc_if_needed()

def get_logo_path():
    if hasattr(sys, "_MEIPASS"):
        src_icon = os.path.join(sys._MEIPASS, "CollecterData", "LogoMabuchiWhite.png")
        current_exe_dir = os.path.dirname(sys.executable)
        dst_dir = os.path.join(current_exe_dir, "CollecterData")
        os.makedirs(dst_dir, exist_ok=True)  # Đảm bảo thư mục tồn tại
        dst_icon = os.path.join(dst_dir, "LogoMabuchiWhite.png")
        try:
            shutil.copyfile(src_icon, dst_icon)
        except Exception:
            print(f"Lỗi sao chép icon từ {src_icon} đến {dst_icon}. Sử dụng icon mặc định.")
        return dst_icon
    else:
        return os.path.join(os.getcwd(), "CollecterData", "LogoMabuchiWhite.png")

def main():
    root = tk.Tk()
    root.title("Gửi Dữ Liệu Khách Hàng")
    root.geometry("1200x600")
    root.configure(bg="#e8ecef")

    # Load icon
    icon_path = get_logo_path()
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

     # Thêm menu Gửi Monthly
    monthly_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Gửi Monthly", menu=monthly_menu)
    monthly_menu.add_command(label="Data Montly", command=lambda: open_data_montly_window(root))
    monthly_menu.add_command(label="Gửi Monthly Data", command=lambda: open_gui_monthly_data(root))
    
    # Bind phím tắt
    root.bind("<Shift-Alt-S>", lambda event: open_config_window(root))
    root.bind("<Configure>", lambda e: root.title(f"Gửi Dữ Liệu Khách Hàng - {root.winfo_width()}x{root.winfo_height()}"))
    root.bind("<ButtonRelease-1>", lambda e: root.title("Gửi Dữ Liệu Khách Hàng"))

    # Cập nhật lệnh cho nút 
    btn_email_month, btn_email_week, btn_email_day, btn_monthly = create_main_window(root)

    # Gán lệnh cho các nút
    btn_email_month.config(command=lambda: show_send_frame(root, "MONTH"))
    btn_email_week.config(command=lambda: show_send_frame(root, "WEEK"))
    btn_email_day.config(command=lambda: show_send_frame(root, "DAY"))
    # btn_monthly.config(command=lambda: messagebox.showinfo("Thông báo", "Chức năng Gửi Monthly đang phát triển!"))
    btn_monthly.config(command=lambda: open_gui_monthly_data(root, parent_window=root))
    
    root.mainloop()

if __name__ == "__main__":
    main()