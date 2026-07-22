import sys
import os
from aggregator import aggregate_code
from constants import TEXT_VI, TEXT_EN
import tkinter as tk
from tkinter import filedialog, messagebox

def run_gui():
    """Chạy giao diện người dùng để chọn thư mục dự án."""
    def select_folder():
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            project_path_entry.delete(0, tk.END)
            project_path_entry.insert(0, folder_selected)

    def start_aggregation():
        path = project_path_entry.get().strip()
        if not path:
            messagebox.showwarning("Lỗi", "Vui lòng chọn đường dẫn thư mục dự án.")
            return

        root.destroy() # Đóng cửa sổ GUI

        # Chọn ngôn ngữ (có thể thêm lựa chọn ngôn ngữ vào GUI sau)
        text = TEXT_VI # Mặc định tiếng Việt khi chạy qua GUI

        # Gọi hàm tổng hợp code
        success = aggregate_code(path, text)

        if success:
            messagebox.showinfo(text['app_title'], text['done'])
        else:
            messagebox.showerror(text['app_title'], text['error'])

    root = tk.Tk()
    root.title(TEXT_VI['app_title']) # Tiêu đề ứng dụng
    root.geometry("500x200") # Kích thước cửa sổ
    root.resizable(False, False) # Không cho phép thay đổi kích thước

    # Chọn ngôn ngữ (có thể mở rộng thêm lựa chọn trên GUI nếu muốn)
    text = TEXT_VI # Mặc định tiếng Việt cho GUI

    # Label cho đường dẫn
    path_label = tk.Label(root, text=text['input_project_path'], font=("Arial", 12))
    path_label.pack(pady=10)

    # Entry để nhập/hiển thị đường dẫn
    project_path_entry = tk.Entry(root, width=50, font=("Arial", 10))
    project_path_entry.pack(pady=5)
    project_path_entry.insert(0, os.getcwd()) # Mặc định là thư mục hiện tại

    # Button để chọn thư mục
    select_button = tk.Button(root, text="Chọn Thư Mục", command=select_folder, font=("Arial", 10))
    select_button.pack(pady=5)

    # Nút Start
    start_button = tk.Button(root, text="BẮT ĐẦU TỔNG HỢP", command=start_aggregation, font=("Arial", 12, "bold"))
    start_button.pack(pady=20)

    root.mainloop()


def main():
    print("🚀 PROJECTDUMP")
    print("="*40)

    # Hỏi người dùng có muốn chạy GUI không
    run_mode = input("Bạn có muốn chạy với giao diện đồ họa (GUI)? (y/n): ").strip().lower()

    if run_mode == 'y':
        run_gui()
    else:
        # Code hiện tại để chạy trong terminal
        lang = input("🌐 Chọn ngôn ngữ (en/vi): ").strip().lower()
        text = TEXT_EN if lang == 'en' else TEXT_VI

        if len(sys.argv) > 1:
            project_path = sys.argv[1]
        else:
            project_path = input(text['input_project_path']).strip() or os.getcwd()

        project_path = os.path.abspath(project_path)
        success = aggregate_code(project_path, text)

        if success:
            print(text['done'])
        else:
            print(text['error'])
            sys.exit(1)

if __name__ == "__main__":
    main()