import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import subprocess
import shutil

class GitManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Git Repository Manager")
        self.root.geometry("700x550")
        
        self.current_folder = tk.StringVar()
        self.current_remote = tk.StringVar()
        self.new_remote_url = tk.StringVar()
        self.delete_history = tk.BooleanVar(value=False)
        self.action_option = tk.StringVar(value="replace_only")
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Folder selection
        ttk.Label(main_frame, text="Chọn thư mục:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        self.folder_entry = ttk.Entry(folder_frame, textvariable=self.current_folder, width=60)
        self.folder_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(folder_frame, text="Browse", command=self.browse_folder).pack(side=tk.LEFT)
        
        # Current remote info
        ttk.Label(main_frame, text="Git remote hiện tại:").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        # Sử dụng Text widget thay vì Entry để hiển thị nhiều dòng nếu cần
        self.remote_text = tk.Text(main_frame, height=3, width=70, state='normal')
        self.remote_text.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Thêm scrollbar cho remote text
        remote_scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.remote_text.yview)
        remote_scrollbar.grid(row=3, column=3, sticky=(tk.N, tk.S))
        self.remote_text.config(yscrollcommand=remote_scrollbar.set)
        
        # New remote URL
        ttk.Label(main_frame, text="Link Git mới:").grid(row=4, column=0, sticky=tk.W, pady=5)
        
        self.new_remote_entry = ttk.Entry(main_frame, textvariable=self.new_remote_url, width=70)
        self.new_remote_entry.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Tùy chọn", padding="10")
        options_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Delete history checkbox
        ttk.Checkbutton(options_frame, text="Xóa lịch sử (xóa .git và tạo lại từ đầu)", 
                       variable=self.delete_history).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # Action options
        ttk.Label(options_frame, text="Chọn hành động:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(options_frame, text="Chỉ thay thế remote", 
                       variable=self.action_option, value="replace_only").grid(row=2, column=0, sticky=tk.W)
        ttk.Radiobutton(options_frame, text="Thay thế và Pull (ép từ remote mới xuống)", 
                       variable=self.action_option, value="pull").grid(row=3, column=0, sticky=tk.W)
        ttk.Radiobutton(options_frame, text="Thay thế và Push (đẩy code lên remote mới)", 
                       variable=self.action_option, value="push").grid(row=4, column=0, sticky=tk.W)
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="Thay thế Git", command=self.replace_git, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Làm mới", command=self.refresh_remote_info, width=20).pack(side=tk.LEFT, padx=5)
        
        # Status text
        self.status_text = tk.Text(main_frame, height=8, width=80)
        self.status_text.grid(row=8, column=0, columnspan=3, pady=10)
        
        # Scrollbar for status text
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.status_text.yview)
        scrollbar.grid(row=8, column=3, sticky=(tk.N, tk.S))
        self.status_text.config(yscrollcommand=scrollbar.set)
        
    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.current_folder.set(folder_selected)
            self.refresh_remote_info()
            
    def refresh_remote_info(self):
        folder = self.current_folder.get()
        self.remote_text.config(state='normal')
        self.remote_text.delete(1.0, tk.END)
        
        if not folder or not os.path.exists(folder):
            self.remote_text.insert(tk.END, "Vui lòng chọn thư mục hợp lệ")
            self.remote_text.config(state='disabled')
            return
            
        # Kiểm tra xem có phải git repository không
        git_dir = os.path.join(folder, '.git')
        if not os.path.exists(git_dir):
            self.remote_text.insert(tk.END, "Thư mục chưa được khởi tạo Git (không tìm thấy thư mục .git)")
            self.remote_text.config(state='disabled')
            return
        
        try:
            # Sử dụng git remote -v để lấy tất cả remote
            result = subprocess.run(
                ['git', '-C', folder, 'remote', '-v'],
                capture_output=True,
                text=True,
                check=False,
                encoding='utf-8'
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Phân tích kết quả để hiển thị đẹp hơn
                remotes = {}
                for line in result.stdout.strip().split('\n'):
                    parts = line.split()
                    if len(parts) >= 3:
                        name = parts[0]
                        url = parts[1]
                        action = parts[2] if len(parts) > 2 else ''
                        
                        if name not in remotes:
                            remotes[name] = {'fetch': '', 'push': ''}
                        
                        if '(fetch)' in action:
                            remotes[name]['fetch'] = url
                        elif '(push)' in action:
                            remotes[name]['push'] = url
                
                # Hiển thị thông tin remote
                display_text = ""
                for name, urls in remotes.items():
                    display_text += f"Remote: {name}\n"
                    if urls['fetch']:
                        display_text += f"  Fetch URL: {urls['fetch']}\n"
                    if urls['push']:
                        display_text += f"  Push URL: {urls['push']}\n"
                    display_text += "-" * 50 + "\n"
                
                self.remote_text.insert(tk.END, display_text)
                
                # Lấy URL của origin (nếu có) để hiển thị trong ô nhập liệu
                if 'origin' in remotes and remotes['origin']['fetch']:
                    self.new_remote_url.set(remotes['origin']['fetch'])
                
            else:
                # Thử lệnh git remote get-url origin để kiểm tra
                result_origin = subprocess.run(
                    ['git', '-C', folder, 'remote', 'get-url', 'origin'],
                    capture_output=True,
                    text=True,
                    check=False,
                    encoding='utf-8'
                )
                
                if result_origin.returncode == 0:
                    self.remote_text.insert(tk.END, f"Remote origin: {result_origin.stdout.strip()}")
                    self.new_remote_url.set(result_origin.stdout.strip())
                else:
                    # Kiểm tra xem có remote nào không
                    result_list = subprocess.run(
                        ['git', '-C', folder, 'remote'],
                        capture_output=True,
                        text=True,
                        check=False,
                        encoding='utf-8'
                    )
                    
                    if result_list.stdout.strip():
                        remotes_list = result_list.stdout.strip().split('\n')
                        self.remote_text.insert(tk.END, f"Có remote nhưng không lấy được URL:\n")
                        self.remote_text.insert(tk.END, f"Danh sách remote: {', '.join(remotes_list)}")
                    else:
                        self.remote_text.insert(tk.END, "Đã khởi tạo Git nhưng chưa có remote nào")
                        
        except Exception as e:
            self.remote_text.insert(tk.END, f"Lỗi khi kiểm tra remote: {str(e)}")
        
        self.remote_text.config(state='disabled')
            
    def log_status(self, message):
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.root.update()
        
    def run_git_command(self, command, cwd=None):
        """Run git command and return result"""
        try:
            # Tách command nếu là string
            if isinstance(command, str):
                import shlex
                command_list = shlex.split(command)
            else:
                command_list = command
                
            result = subprocess.run(
                command_list,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=False,
                encoding='utf-8'
            )
            return result
        except Exception as e:
            return type('Result', (), {'returncode': 1, 'stdout': '', 'stderr': str(e)})()
            
    def replace_git(self):
        folder = self.current_folder.get()
        new_remote = self.new_remote_url.get().strip()
        
        if not folder or not os.path.exists(folder):
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục hợp lệ")
            return
            
        if not new_remote:
            messagebox.showerror("Lỗi", "Vui lòng nhập link Git mới")
            return
            
        # Kiểm tra xem có phải git repository không
        git_dir = os.path.join(folder, '.git')
        if not os.path.exists(git_dir) and not self.delete_history.get():
            messagebox.showerror("Lỗi", "Thư mục không phải là Git repository. Vui lòng chọn 'Xóa lịch sử' để khởi tạo mới.")
            return
            
        # Confirm action
        action_text = {
            "replace_only": "chỉ thay thế remote",
            "pull": "thay thế và pull",
            "push": "thay thế và push"
        }
        
        history_text = "và XÓA lịch sử" if self.delete_history.get() else "và GIỮ lịch sử"
        
        confirm = messagebox.askyesno(
            "Xác nhận",
            f"Bạn có chắc muốn thay thế Git?\n"
            f"Thư mục: {folder}\n"
            f"Remote mới: {new_remote}\n"
            f"Hành động: {action_text[self.action_option.get()]}\n"
            f"Tùy chọn: {history_text}"
        )
        
        if not confirm:
            return
            
        self.status_text.delete(1.0, tk.END)
        self.log_status("Bắt đầu quá trình thay thế Git...")
        
        # Step 1: Handle history deletion if selected
        if self.delete_history.get():
            self.log_status("Đang xóa lịch sử Git cũ...")
            if os.path.exists(git_dir):
                try:
                    # Thử xóa bằng shutil trước
                    shutil.rmtree(git_dir, ignore_errors=True)
                    self.log_status("Đã xóa thư mục .git cũ")
                except Exception as e:
                    self.log_status(f"Lỗi khi xóa .git: {str(e)}")
                    messagebox.showerror("Lỗi", f"Không thể xóa .git: {str(e)}")
                    return
            
            # Initialize new git repository
            self.log_status("Đang khởi tạo Git mới...")
            result = self.run_git_command("git init", cwd=folder)
            if result.returncode != 0:
                self.log_status(f"Lỗi khi git init: {result.stderr}")
                return
                
            # Add all files
            self.log_status("Đang thêm files...")
            result = self.run_git_command("git add .", cwd=folder)
            if result.returncode != 0:
                self.log_status(f"Lỗi khi git add: {result.stderr}")
                return
                
            # Commit
            self.log_status("Đang commit...")
            result = self.run_git_command('git commit -m "Initial commit"', cwd=folder)
            if result.returncode != 0:
                self.log_status(f"Lỗi khi commit: {result.stderr}")
                # Không return ở đây vì có thể không có file để commit
                self.log_status("Tiếp tục quá trình...")
        
        # Step 2: Add or update remote
        self.log_status("Đang cập nhật remote...")
        
        # Kiểm tra remote hiện tại
        result = self.run_git_command("git remote", cwd=folder)
        remotes = result.stdout.strip().split('\n') if result.stdout.strip() else []
        
        if 'origin' in remotes:
            # Thử lấy URL của origin hiện tại
            result_url = self.run_git_command("git remote get-url origin", cwd=folder)
            if result_url.returncode == 0:
                self.log_status(f"Remote origin hiện tại: {result_url.stdout.strip()}")
            
            # Xóa remote origin cũ
            self.log_status("Đang xóa remote origin cũ...")
            result = self.run_git_command("git remote remove origin", cwd=folder)
            if result.returncode != 0:
                self.log_status(f"Cảnh báo khi xóa remote: {result.stderr}")
        
        # Thêm remote mới
        self.log_status(f"Đang thêm remote mới: {new_remote}")
        result = self.run_git_command(f"git remote add origin {new_remote}", cwd=folder)
        if result.returncode != 0:
            self.log_status(f"Lỗi khi thêm remote: {result.stderr}")
            messagebox.showerror("Lỗi", f"Không thể thêm remote: {result.stderr}")
            return
            
        self.log_status(f"Đã thêm remote thành công: {new_remote}")
        
        # Step 3: Perform additional actions based on selection
        action = self.action_option.get()
        
        if action == "pull":
            self.log_status("Đang pull từ remote...")
            
            # Fetch từ remote
            self.log_status("Đang fetch...")
            result = self.run_git_command("git fetch origin", cwd=folder)
            if result.returncode != 0:
                self.log_status(f"Lỗi khi fetch: {result.stderr}")
            else:
                # Thử reset về remote master/main
                branches = ['master', 'main']
                pulled = False
                
                for branch in branches:
                    self.log_status(f"Thử reset về origin/{branch}...")
                    result = self.run_git_command(f"git reset --hard origin/{branch}", cwd=folder)
                    if result.returncode == 0:
                        self.log_status(f"Pull thành công từ origin/{branch}")
                        pulled = True
                        break
                
                if not pulled:
                    self.log_status("Không thể pull. Remote có thể trống hoặc không có nhánh master/main.")
                    
        elif action == "push":
            self.log_status("Đang push lên remote...")
            
            # Xác định nhánh hiện tại
            result = self.run_git_command("git branch --show-current", cwd=folder)
            current_branch = result.stdout.strip() if result.stdout.strip() else "master"
            
            # Push lên remote
            self.log_status(f"Đang push nhánh {current_branch} lên origin...")
            result = self.run_git_command(f"git push -u origin {current_branch}", cwd=folder)
            
            if result.returncode == 0:
                self.log_status("Push thành công")
            else:
                self.log_status(f"Lỗi khi push: {result.stderr}")
                # Thử push với force nếu lỗi
                if "failed to push" in result.stderr.lower():
                    retry = messagebox.askyesno("Xác nhận", "Push thất bại. Bạn có muốn thử push với --force?")
                    if retry:
                        result = self.run_git_command(f"git push -u origin {current_branch} --force", cwd=folder)
                        if result.returncode == 0:
                            self.log_status("Push force thành công")
                        else:
                            self.log_status(f"Lỗi khi push force: {result.stderr}")
                
        self.log_status("Quá trình thay thế Git hoàn tất!")
        self.refresh_remote_info()
        messagebox.showinfo("Thành công", "Đã thay thế Git thành công!")

def main():
    root = tk.Tk()
    app = GitManagerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()