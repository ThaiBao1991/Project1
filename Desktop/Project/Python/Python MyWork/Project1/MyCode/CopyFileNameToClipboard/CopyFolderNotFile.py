import os
import shutil
import threading
from pathlib import Path
from tkinter import *
from tkinter import ttk, filedialog, messagebox

class FolderStructureCopier:
    def __init__(self, root):
        self.root = root
        self.root.title("Copy Cấu Trúc Thư Mục")
        self.root.geometry("800x600")
        
        # Biến lưu đường dẫn
        self.source_path = StringVar()
        self.dest_path = StringVar()
        self.is_copying = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Frame chọn thư mục
        select_frame = ttk.LabelFrame(self.root, text="Chọn thư mục", padding=10)
        select_frame.pack(fill="x", padx=10, pady=5)
        
        # Thư mục gốc
        ttk.Label(select_frame, text="Thư mục gốc:").grid(row=0, column=0, sticky="w", pady=5)
        ttk.Entry(select_frame, textvariable=self.source_path, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(select_frame, text="Chọn", command=self.select_source).grid(row=0, column=2)
        
        # Thư mục đích
        ttk.Label(select_frame, text="Thư mục đích:").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(select_frame, textvariable=self.dest_path, width=50).grid(row=1, column=1, padx=5)
        ttk.Button(select_frame, text="Chọn", command=self.select_dest).grid(row=1, column=2)
        
        # Button Start
        self.start_btn = ttk.Button(select_frame, text="BẮT ĐẦU COPY", command=self.start_copy)
        self.start_btn.grid(row=2, column=1, pady=10)
        
        # Frame hiển thị tiến trình
        progress_frame = ttk.LabelFrame(self.root, text="Tiến trình copy", padding=10)
        progress_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Thanh tiến trình
        self.progress_bar = ttk.Progressbar(progress_frame, length=400, mode='determinate')
        self.progress_bar.pack(pady=5)
        
        # Label % hoàn thành
        self.percent_label = ttk.Label(progress_frame, text="0%")
        self.percent_label.pack()
        
        # Frame hiển thị các thư mục đã copy
        list_frame = ttk.LabelFrame(progress_frame, text="Các thư mục đã copy:", padding=10)
        list_frame.pack(fill="both", expand=True, pady=10)
        
        # Tạo canvas và scrollbar cho danh sách thư mục
        canvas_frame = Frame(list_frame)
        canvas_frame.pack(fill="both", expand=True)
        
        self.canvas = Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Label trạng thái
        self.status_label = ttk.Label(self.root, text="Sẵn sàng...", relief="sunken", anchor="w")
        self.status_label.pack(fill="x", padx=10, pady=5)
        
    def select_source(self):
        path = filedialog.askdirectory(title="Chọn thư mục gốc")
        if path:
            self.source_path.set(path)
            
    def select_dest(self):
        path = filedialog.askdirectory(title="Chọn thư mục đích")
        if path:
            self.dest_path.set(path)
            
    def clear_folder_list(self):
        """Xóa danh sách thư mục hiện tại"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
    def add_folder_to_list(self, folder_path, status="Đã copy"):
        """Thêm thư mục vào danh sách đã copy"""
        frame = Frame(self.scrollable_frame)
        frame.pack(fill="x", pady=2)
        
        # Icon/Status
        status_label = Label(frame, text="✓", fg="green", font=("Arial", 12, "bold"))
        status_label.pack(side="left", padx=5)
        
        # Tên thư mục
        folder_name = os.path.basename(folder_path) if folder_path != self.source_path.get() else "[Thư mục gốc]"
        Label(frame, text=f"{folder_name} -> {folder_path}", anchor="w").pack(side="left", padx=5)
        
        # Cập nhật canvas
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.yview_moveto(1.0)  # Scroll xuống cuối
        
    def copy_structure(self):
        """Copy cấu trúc thư mục"""
        source = self.source_path.get()
        dest = self.dest_path.get()
        
        if not source or not dest:
            self.root.after(0, lambda: messagebox.showerror("Lỗi", "Vui lòng chọn đầy đủ thư mục!"))
            self.root.after(0, self.reset_ui)
            return
            
        if not os.path.exists(source):
            self.root.after(0, lambda: messagebox.showerror("Lỗi", "Thư mục gốc không tồn tại!"))
            self.root.after(0, self.reset_ui)
            return
            
        try:
            # Tạo thư mục đích nếu chưa tồn tại
            os.makedirs(dest, exist_ok=True)
            
            # Đếm tổng số thư mục
            total_folders = 0
            for root, dirs, files in os.walk(source):
                if self.is_copying:  # Kiểm tra nếu người dùng hủy
                    total_folders += len(dirs)
            
            copied_folders = 0
            
            # Copy cấu trúc thư mục
            for root, dirs, files in os.walk(source):
                if not self.is_copying:
                    break
                    
                # Tính đường dẫn tương đối
                relative_path = os.path.relpath(root, source)
                
                # Nếu là thư mục gốc thì không cần thêm relative path
                if relative_path == ".":
                    target_dir = dest
                else:
                    target_dir = os.path.join(dest, relative_path)
                
                # Tạo thư mục tại đích
                if not os.path.exists(target_dir):
                    os.makedirs(target_dir, exist_ok=True)
                    self.root.after(0, lambda p=target_dir: self.add_folder_to_list(p))
                
                # Tạo các thư mục con
                for dir_name in dirs:
                    if not self.is_copying:
                        break
                    source_subdir = os.path.join(root, dir_name)
                    dest_subdir = os.path.join(target_dir, dir_name)
                    
                    if not os.path.exists(dest_subdir):
                        os.makedirs(dest_subdir, exist_ok=True)
                        self.root.after(0, lambda p=dest_subdir: self.add_folder_to_list(p))
                    
                    copied_folders += 1
                    
                    # Cập nhật tiến trình
                    if total_folders > 0:
                        progress = (copied_folders / total_folders) * 100
                        self.root.after(0, lambda p=progress: self.update_progress(p, copied_folders, total_folders))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Lỗi", f"Có lỗi xảy ra:\n{str(e)}"))
        finally:
            if self.is_copying:
                self.root.after(0, self.copy_complete)
            else:
                self.root.after(0, self.copy_cancelled)
                
    def update_progress(self, percent, current, total):
        """Cập nhật thanh tiến trình"""
        self.progress_bar['value'] = percent
        self.percent_label.config(text=f"{percent:.1f}% ({current}/{total} thư mục)")
        self.status_label.config(text=f"Đang copy... {current}/{total} thư mục")
        self.root.update_idletasks()
        
    def start_copy(self):
        """Bắt đầu quá trình copy"""
        if not self.source_path.get() or not self.dest_path.get():
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn đầy đủ thư mục!")
            return
            
        # Kiểm tra thư mục đích có phải là thư mục con của thư mục gốc không
        try:
            if os.path.commonpath([self.source_path.get(), self.dest_path.get()]) == self.source_path.get():
                if not messagebox.askyesno("Cảnh báo", 
                    "Thư mục đích nằm trong thư mục gốc! Điều này có thể tạo vòng lặp vô hạn.\n"
                    "Bạn có chắc muốn tiếp tục?"):
                    return
        except:
            pass
        
        self.is_copying = True
        self.clear_folder_list()
        self.progress_bar['value'] = 0
        self.percent_label.config(text="0%")
        self.start_btn.config(state="disabled")
        self.status_label.config(text="Đang khởi tạo...")
        
        # Chạy trong thread riêng
        thread = threading.Thread(target=self.copy_structure)
        thread.daemon = True
        thread.start()
        
    def copy_complete(self):
        """Kết thúc copy thành công"""
        self.is_copying = False
        self.start_btn.config(state="normal")
        self.status_label.config(text="Hoàn thành copy cấu trúc thư mục!")
        self.progress_bar['value'] = 100
        self.percent_label.config(text="100%")
        messagebox.showinfo("Thành công", "Đã copy xong cấu trúc thư mục!")
        
    def copy_cancelled(self):
        """Hủy copy"""
        self.is_copying = False
        self.start_btn.config(state="normal")
        self.status_label.config(text="Đã hủy copy!")
        
    def reset_ui(self):
        """Reset UI về trạng thái ban đầu"""
        self.is_copying = False
        self.start_btn.config(state="normal")
        self.progress_bar['value'] = 0
        self.percent_label.config(text="0%")
        self.status_label.config(text="Sẵn sàng...")

if __name__ == "__main__":
    root = Tk()
    app = FolderStructureCopier(root)
    root.mainloop()