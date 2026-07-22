import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import queue
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, scrolledtext
import pyperclip

# Biến toàn cục để lưu trữ kết quả cấu trúc Excel (phục vụ nút bấm copy lại)
final_excel_result = ""

def scan_directory_multithreaded(root_dir, update_status_func, update_log_func):
    global final_excel_result
    dir_structure = {}
    dir_queue = queue.Queue()
    
    p_root = Path(root_dir)
    dir_queue.put(p_root)
    
    lock = threading.Lock()
    folder_count = 0
    active_threads = 0
    running_tasks = 0

    def worker_task(current_path):
        nonlocal folder_count, active_threads, running_tasks
        
        with lock:
            active_threads += 1
            update_status_func(f"Đang quét... Tìm thấy: {folder_count} folder | Luồng chạy: {active_threads}")
            
        subdirs = []
        try:
            if current_path.exists():
                for entry in current_path.iterdir():
                    try:
                        if entry.is_dir():
                            subdirs.append(entry)
                    except (PermissionError, FileNotFoundError, OSError):
                        continue
                
                update_log_func(f"[Đang quét]: {current_path.name or current_path} ({len(subdirs)} folder con)\n")
            else:
                update_log_func(f"[Lỗi mạng]: Không tìm thấy đường dẫn {current_path}\n")
        except (PermissionError, OSError):
            update_log_func(f"[Bỏ qua - Không thể truy cập]: {current_path.name or current_path}\n")
            subdirs = []
        except Exception as e:
            update_log_func(f"[Lỗi hệ thống]: {current_path.name or current_path} - {str(e)}\n")
            subdirs = []

        with lock:
            dir_structure[str(current_path)] = [str(s) for s in subdirs]
            folder_count += len(subdirs)
            active_threads -= 1
            running_tasks -= 1

        for subdir in subdirs:
            with lock:
                running_tasks += 1
            dir_queue.put(subdir)

    MAX_WORKERS = 16 
    update_log_func(f"--- KHỞI TẠO THREADPOOL: {MAX_WORKERS} LUỒNG (CƠ CHẾ BỎ QUA LỖI BẢO MẬT) ---\n")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        with lock:
            running_tasks += 1
            
        while True:
            try:
                target_path = dir_queue.get(timeout=0.2)
                executor.submit(worker_task, target_path)
            except queue.Empty:
                with lock:
                    if running_tasks == 0:
                        break
                time.sleep(0.1)

    update_log_func("--- QUÉT DỮ LIỆU XONG -> ĐANG SẮP XẾP CÂY THƯ MỤC ---\n")
    
    # Dựng cấu trúc phân cấp Excel
    tree_lines = []
    def _build_excel_output(current_path_str, depth=0):
        subdirs = dir_structure.get(current_path_str, [])
        subdirs.sort(key=lambda x: os.path.basename(x).lower())
        
        for subdir_str in subdirs:
            tabs = "\t" * depth
            name = os.path.basename(subdir_str)
            tree_lines.append(f"{tabs}{name}")
            _build_excel_output(subdir_str, depth + 1)

    root_name = p_root.name if p_root.name else str(p_root)
    tree_lines.append(root_name)
    _build_excel_output(str(p_root), depth=1)

    # Lưu kết quả thô (chứa \t) vào biến toàn cục
    final_excel_result = "\n".join(tree_lines)
    return final_excel_result, folder_count


def start_processing():
    path = entry_path.get().strip()
    if path.startswith('"') and path.endswith('"'):
        path = path[1:-1]
    path = os.path.normpath(path)

    if not path:
        messagebox.showerror("Lỗi", "Vui lòng nhập đường dẫn!")
        return

    # Nhắc nhở nếu dán IP gốc
    if path.startswith(r'\\') and path.count('\\') == 2 and not path.endswith('\\'):
        path += '\\'
    if path.startswith(r'\\') and path.count('\\') < 3:
         messagebox.showwarning("Lưu ý đường dẫn mạng", "Nếu quét địa chỉ IP gốc bị lỗi, bạn nên điền chính xác thư mục được chia sẻ công khai.\nVí dụ: \\\\192.168.40.5\\Data")

    # Khóa các nút điều hướng trong lúc quét
    btn_run.config(state=tk.DISABLED, bg="#95a5a6")
    btn_copy_again.config(state=tk.DISABLED, bg="#95a5a6")
    
    text_log.config(state=tk.NORMAL)
    text_log.delete("1.0", tk.END)
    text_preview.config(state=tk.NORMAL)
    text_preview.delete("1.0", tk.END)
    text_preview.insert(tk.END, "Đang kết nối và quét dữ liệu (Tự động bỏ qua thư mục lỗi)...\n")
    text_preview.config(state=tk.DISABLED)

    def update_status(text):
        label_status.config(text=text, fg="#e67e22")
        root.update_idletasks()

    def update_log(log_text):
        text_log.insert(tk.END, log_text)
        text_log.see(tk.END)
        root.update_idletasks()

    def worker_management_thread():
        try:
            excel_tree, total_folders = scan_directory_multithreaded(
                path, update_status, update_log
            )
            
            # Tự động copy lần đầu tiên
            pyperclip.copy(excel_tree)
            
            # Đẩy kết quả hiển thị trực quan vào ô Preview
            preview_formatted = excel_tree.replace("\t", "    ")
            text_preview.config(state=tk.NORMAL)
            text_preview.delete("1.0", tk.END)
            text_preview.insert(tk.END, preview_formatted)
            text_preview.config(state=tk.DISABLED)
            
            label_status.config(text=f"Hoàn thành! Đã quét và tự động copy {total_folders} thư mục.", fg="#27ae60")
            messagebox.showinfo("Thành công", f"Đã quét xong!\nTổng cộng: {total_folders} thư mục đã nằm trong Clipboard.")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi: {str(e)}")
            label_status.config(text="Quét thất bại.", fg="#c0392b")
        finally:
            btn_run.config(state=tk.NORMAL, bg="#27ae60")
            btn_copy_again.config(state=tk.NORMAL, bg="#2980b9")  # Mở lại nút Copy
            text_log.config(state=tk.DISABLED)

    threading.Thread(target=worker_management_thread, daemon=True).start()


def click_copy_again():
    """Hàm xử lý riêng khi người dùng nhấn nút Copy lại kết quả"""
    if final_excel_result:
        pyperclip.copy(final_excel_result)
        messagebox.showinfo("Clipboard", "Đã copy lại cấu trúc chuẩn ô Excel vào bộ nhớ tạm!")
    else:
        messagebox.showwarning("Thông báo", "Chưa có dữ liệu kết quả để copy. Vui lòng quét thư mục trước!")


# --- GIAO DIỆN ĐƯỢC THIẾT KẾ LẠI ---
root = tk.Tk()
root.title("Copy Cấu Trúc Thư Mục Excel - Bản Nâng Cấp Thêm Nút Copy")
root.geometry("1000x650")

# Khung trên: Nhập liệu
frame_top = tk.Frame(root, padx=10, pady=10)
frame_top.pack(fill=tk.X)

label_path = tk.Label(frame_top, text="Dán đường dẫn thư mục thường hoặc ổ mạng vào đây:")
label_path.pack(anchor=tk.W, pady=(0, 5))

entry_path = tk.Entry(frame_top, font=("Segoe UI", 10))
entry_path.pack(fill=tk.X, side=tk.LEFT, expand=True, ipady=4)

btn_run = tk.Button(
    frame_top, text="🔍 Bắt đầu quét", command=start_processing,
    bg="#27ae60", fg="white", font=("Segoe UI", 9, "bold"), padx=15
)
btn_run.pack(side=tk.RIGHT, padx=(10, 0))

# Khung giữa: Thanh Trạng thái dòng chữ nhanh
frame_status = tk.Frame(root, padx=10)
frame_status.pack(fill=tk.X)
label_status = tk.Label(frame_status, text="Trạng thái: Sẵn sàng.", font=("Segoe UI", 9, "italic"), fg="#7f8c8d", anchor=tk.W)
label_status.pack(fill=tk.X)

# Khung dưới: Chia đôi màn hình (Log và Preview)
frame_main = tk.Frame(root, padx=10, pady=10)
frame_main.pack(fill=tk.BOTH, expand=True)

frame_main.columnconfigure(0, weight=1)
frame_main.columnconfigure(1, weight=1)
frame_main.rowconfigure(0, weight=1)

# Cột trái - Log
frame_left = tk.Frame(frame_main)
frame_left.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
label_log = tk.Label(frame_left, text="⚡ TIẾN TRÌNH QUÉT (LOG DEBUG):", fg="#a19182", font=("Segoe UI", 9, "bold"))
label_log.pack(anchor=tk.W, pady=(0, 5))
text_log = scrolledtext.ScrolledText(frame_left, wrap=tk.NONE, font=("Consolas", 9), state=tk.DISABLED, bg="#2c3e50", fg="#ecf0f1")
text_log.pack(fill=tk.BOTH, expand=True)

# Cột phải - Preview & Nút bấm tác vụ phụ
frame_right = tk.Frame(frame_main)
frame_right.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

# Khung tiêu đề phụ để chứa cả Label và Nút Copy thẳng hàng
frame_right_title = tk.Frame(frame_right)
frame_right_title.pack(fill=tk.X, pady=(0, 5))

label_preview = tk.Label(frame_right_title, text="📋 PREVIEW KẾT QUẢ EXCEL:", fg="#27ae60", font=("Segoe UI", 9, "bold"))
label_preview.pack(side=tk.LEFT, anchor=tk.W)

# Nút Bấm Copy mới được thêm vào đây
btn_copy_again = tk.Button(
    frame_right_title, text="📋 Copy lại cấu trúc", command=click_copy_again,
    bg="#2980b9", fg="white", font=("Segoe UI", 8, "bold"), padx=10, pady=2
)
btn_copy_again.pack(side=tk.RIGHT)

text_preview = scrolledtext.ScrolledText(frame_right, wrap=tk.NONE, font=("Consolas", 9), state=tk.DISABLED, bg="#f8f9fa", fg="#2c3e50")
text_preview.pack(fill=tk.BOTH, expand=True)

root.mainloop()