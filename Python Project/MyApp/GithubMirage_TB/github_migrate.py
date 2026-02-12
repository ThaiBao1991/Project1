import os
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import threading
from pathlib import Path

class GitHubMigratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GitHub Repository Migrator")
        self.root.geometry("900x700")
        self.root.configure(bg="#2b2b2b")
        
        # Biến lưu trữ
        self.current_directory = tk.StringVar(value=os.getcwd())
        self.current_remote_var = tk.StringVar()
        self.new_remote_var = tk.StringVar()
        
        self.setup_ui()
        self.detect_current_git()
    
    def setup_ui(self):
        # Header
        header_frame = tk.Frame(self.root, bg="#1e1e1e", height=80)
        header_frame.pack(fill="x", padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🚀 GitHub Repository Migrator",
            font=("Arial", 20, "bold"),
            fg="#61dafb",
            bg="#1e1e1e"
        )
        title_label.pack(side="left", padx=20, pady=20)
        
        # Nút Start
        start_button = tk.Button(
            header_frame,
            text="▶️ START MIGRATION",
            font=("Arial", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            command=self.start_migration,
            relief="flat",
            padx=25,
            pady=12,
            cursor="hand2"
        )
        start_button.pack(side="right", padx=20, pady=20)
        
        # Main content frame
        main_frame = tk.Frame(self.root, bg="#2b2b2b")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Current Directory Section
        dir_frame = tk.LabelFrame(
            main_frame,
            text=" Working Directory ",
            font=("Arial", 12, "bold"),
            bg="#2b2b2b",
            fg="#ffa726",
            relief="solid",
            borderwidth=1
        )
        dir_frame.pack(fill="x", pady=(0, 15))
        
        # Frame chứa directory entry và nút browse
        dir_input_frame = tk.Frame(dir_frame, bg="#2b2b2b")
        dir_input_frame.pack(fill="x", padx=10, pady=10)
        
        dir_label = tk.Label(
            dir_input_frame,
            text="Current Folder:",
            font=("Arial", 10),
            bg="#2b2b2b",
            fg="#ffffff"
        )
        dir_label.pack(anchor="w", pady=(0, 5))
        
        # Entry hiển thị đường dẫn hiện tại
        dir_entry = tk.Entry(
            dir_input_frame,
            textvariable=self.current_directory,
            font=("Arial", 10),
            bg="#3c3c3c",
            fg="#ffffff",
            relief="flat",
            insertbackground="#61dafb"
        )
        dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Nút Browse
        browse_button = tk.Button(
            dir_input_frame,
            text="📁 Browse",
            font=("Arial", 10),
            bg="#2196F3",
            fg="white",
            command=self.browse_directory,
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2"
        )
        browse_button.pack(side="right")
        
        # Nút Refresh để cập nhật Git info
        refresh_button = tk.Button(
            dir_input_frame,
            text="🔄 Refresh Git Info",
            font=("Arial", 10),
            bg="#9C27B0",
            fg="white",
            command=self.detect_current_git,
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2"
        )
        refresh_button.pack(side="right", padx=(0, 10))
        
        # Current Remote Section
        current_frame = tk.LabelFrame(
            main_frame,
            text=" Current GitHub Remote ",
            font=("Arial", 12, "bold"),
            bg="#2b2b2b",
            fg="#61dafb",
            relief="solid",
            borderwidth=1
        )
        current_frame.pack(fill="x", pady=(0, 15))
        
        current_label = tk.Label(
            current_frame,
            text="Git Remote URL:",
            font=("Arial", 10),
            bg="#2b2b2b",
            fg="#ffffff"
        )
        current_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Entry hiển thị Git hiện tại (readonly)
        self.current_remote_entry = tk.Entry(
            current_frame,
            textvariable=self.current_remote_var,
            font=("Arial", 10),
            bg="#3c3c3c",
            fg="#cccccc",
            relief="flat",
            state="readonly",
            insertbackground="#61dafb"
        )
        self.current_remote_entry.pack(fill="x", padx=10, pady=(0, 10))
        
        # Hiển thị thông tin thêm về repository
        self.repo_info_label = tk.Label(
            current_frame,
            text="",
            font=("Arial", 9),
            bg="#2b2b2b",
            fg="#888888",
            anchor="w"
        )
        self.repo_info_label.pack(fill="x", padx=10, pady=(0, 10))
        
        # New Remote Section
        new_frame = tk.LabelFrame(
            main_frame,
            text=" New GitHub Remote ",
            font=("Arial", 12, "bold"),
            bg="#2b2b2b",
            fg="#4CAF50",
            relief="solid",
            borderwidth=1
        )
        new_frame.pack(fill="x", pady=(0, 15))
        
        new_label = tk.Label(
            new_frame,
            text="New Git Remote URL:",
            font=("Arial", 10),
            bg="#2b2b2b",
            fg="#ffffff"
        )
        new_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Frame cho URL input và nút Paste
        url_input_frame = tk.Frame(new_frame, bg="#2b2b2b")
        url_input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Entry nhập Git mới
        self.new_remote_entry = tk.Entry(
            url_input_frame,
            textvariable=self.new_remote_var,
            font=("Arial", 10),
            bg="#3c3c3c",
            fg="#ffffff",
            relief="flat",
            insertbackground="#61dafb"
        )
        self.new_remote_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        # Nút Paste từ clipboard
        paste_button = tk.Button(
            url_input_frame,
            text="📋 Paste",
            font=("Arial", 10),
            bg="#FF9800",
            fg="white",
            command=self.paste_from_clipboard,
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2"
        )
        paste_button.pack(side="right")
        
        # Thêm placeholder
        self.add_url_placeholder()
        
        # Các mẫu URL GitHub phổ biến
        url_templates_frame = tk.Frame(new_frame, bg="#2b2b2b")
        url_templates_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        templates_label = tk.Label(
            url_templates_frame,
            text="Quick Templates:",
            font=("Arial", 9),
            bg="#2b2b2b",
            fg="#888888"
        )
        templates_label.pack(side="left", padx=(0, 10))
        
        # Tạo các nút template
        templates = [
            ("HTTPS", "https://github.com/username/repo.git"),
            ("SSH", "git@github.com:username/repo.git")
        ]
        
        for template_name, template_url in templates:
            btn = tk.Button(
                url_templates_frame,
                text=template_name,
                font=("Arial", 8),
                bg="#37474F",
                fg="white",
                command=lambda url=template_url: self.set_template_url(url),
                relief="flat",
                padx=10,
                pady=3,
                cursor="hand2"
            )
            btn.pack(side="left", padx=2)
        
        # Migration Options
        options_frame = tk.LabelFrame(
            main_frame,
            text=" Migration Options ",
            font=("Arial", 12, "bold"),
            bg="#2b2b2b",
            fg="#ffa726",
            relief="solid",
            borderwidth=1
        )
        options_frame.pack(fill="x", pady=(0, 15))
        
        self.migration_method = tk.IntVar(value=1)
        
        # Frame cho radio buttons
        radio_frame = tk.Frame(options_frame, bg="#2b2b2b")
        radio_frame.pack(fill="x", padx=10, pady=10)
        
        option1 = tk.Radiobutton(
            radio_frame,
            text="✅ Keep Git History (Change URL only)",
            variable=self.migration_method,
            value=1,
            font=("Arial", 10),
            bg="#2b2b2b",
            fg="#4CAF50",
            selectcolor="#2b2b2b",
            activebackground="#2b2b2b",
            activeforeground="#4CAF50",
            cursor="hand2"
        )
        option1.pack(anchor="w", pady=5)
        
        option1_desc = tk.Label(
            radio_frame,
            text="   • Safe method, keeps all commit history",
            font=("Arial", 9),
            bg="#2b2b2b",
            fg="#888888"
        )
        option1_desc.pack(anchor="w", padx=20)
        
        option2 = tk.Radiobutton(
            radio_frame,
            text="🔄 Start Fresh (Delete .git folder)",
            variable=self.migration_method,
            value=2,
            font=("Arial", 10),
            bg="#2b2b2b",
            fg="#FF9800",
            selectcolor="#2b2b2b",
            activebackground="#2b2b2b",
            activeforeground="#FF9800",
            cursor="hand2"
        )
        option2.pack(anchor="w", pady=5)
        
        option2_desc = tk.Label(
            radio_frame,
            text="   • Deletes history, starts with clean repository",
            font=("Arial", 9),
            bg="#2b2b2b",
            fg="#888888"
        )
        option2_desc.pack(anchor="w", padx=20)
        
        # Additional Options
        additional_frame = tk.Frame(options_frame, bg="#2b2b2b")
        additional_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.push_after_var = tk.BooleanVar(value=True)
        push_check = tk.Checkbutton(
            additional_frame,
            text="Push to new remote after migration",
            variable=self.push_after_var,
            font=("Arial", 9),
            bg="#2b2b2b",
            fg="#ffffff",
            selectcolor="#2b2b2b",
            activebackground="#2b2b2b",
            activeforeground="#ffffff",
            cursor="hand2"
        )
        push_check.pack(side="left", padx=(0, 20))
        
        self.backup_var = tk.BooleanVar(value=True)
        backup_check = tk.Checkbutton(
            additional_frame,
            text="Create backup before migration",
            variable=self.backup_var,
            font=("Arial", 9),
            bg="#2b2b2b",
            fg="#ffffff",
            selectcolor="#2b2b2b",
            activebackground="#2b2b2b",
            activeforeground="#ffffff",
            cursor="hand2"
        )
        backup_check.pack(side="left")
        
        # Console Output
        console_frame = tk.LabelFrame(
            main_frame,
            text=" Console Output ",
            font=("Arial", 12, "bold"),
            bg="#2b2b2b",
            fg="#cccccc",
            relief="solid",
            borderwidth=1
        )
        console_frame.pack(fill="both", expand=True)
        
        # Toolbar cho console
        console_toolbar = tk.Frame(console_frame, bg="#2b2b2b")
        console_toolbar.pack(fill="x", padx=5, pady=(5, 0))
        
        clear_button = tk.Button(
            console_toolbar,
            text="🗑️ Clear",
            font=("Arial", 8),
            bg="#f44336",
            fg="white",
            command=self.clear_console,
            relief="flat",
            padx=10,
            pady=2,
            cursor="hand2"
        )
        clear_button.pack(side="left")
        
        save_button = tk.Button(
            console_toolbar,
            text="💾 Save Log",
            font=("Arial", 8),
            bg="#2196F3",
            fg="white",
            command=self.save_log,
            relief="flat",
            padx=10,
            pady=2,
            cursor="hand2"
        )
        save_button.pack(side="left", padx=5)
        
        self.console_text = scrolledtext.ScrolledText(
            console_frame,
            height=10,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#cccccc",
            insertbackground="#ffffff",
            relief="flat"
        )
        self.console_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Status Bar
        self.status_bar = tk.Label(
            self.root,
            text="Ready • Select a Git repository to begin",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#1e1e1e",
            fg="#61dafb",
            font=("Arial", 9)
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Bind Enter key to start migration
        self.root.bind('<Return>', lambda e: self.start_migration())
        
        # Bind directory change
        self.current_directory.trace('w', self.on_directory_changed)
    
    def add_url_placeholder(self):
        """Thêm placeholder cho URL input"""
        self.new_remote_entry.insert(0, "https://github.com/username/new-repository.git")
        self.new_remote_entry.configure(fg="#888888")
        
        def on_entry_click(event):
            if self.new_remote_entry.get() == "https://github.com/username/new-repository.git":
                self.new_remote_entry.delete(0, tk.END)
                self.new_remote_entry.configure(fg="#ffffff")
        
        def on_focusout(event):
            if self.new_remote_entry.get() == "":
                self.new_remote_entry.insert(0, "https://github.com/username/new-repository.git")
                self.new_remote_entry.configure(fg="#888888")
        
        self.new_remote_entry.bind('<FocusIn>', on_entry_click)
        self.new_remote_entry.bind('<FocusOut>', on_focusout)
    
    def set_template_url(self, template_url):
        """Đặt URL từ template"""
        self.new_remote_entry.delete(0, tk.END)
        self.new_remote_entry.insert(0, template_url)
        self.new_remote_entry.configure(fg="#ffffff")
        self.log_message(f"✓ Template URL set: {template_url}", "info")
    
    def paste_from_clipboard(self):
        """Paste từ clipboard"""
        try:
            clipboard_text = self.root.clipboard_get()
            if clipboard_text:
                self.new_remote_entry.delete(0, tk.END)
                self.new_remote_entry.insert(0, clipboard_text)
                self.new_remote_entry.configure(fg="#ffffff")
                self.log_message("✓ Pasted from clipboard", "info")
        except:
            self.log_message("⚠️ No text in clipboard", "warning")
    
    def browse_directory(self):
        """Mở dialog chọn thư mục"""
        selected_dir = filedialog.askdirectory(
            title="Select Git Repository Folder",
            initialdir=self.current_directory.get()
        )
        
        if selected_dir:
            self.current_directory.set(selected_dir)
            self.detect_current_git()
    
    def on_directory_changed(self, *args):
        """Xử lý khi thư mục thay đổi"""
        self.detect_current_git()
    
    def get_repo_info(self, repo_path):
        """Lấy thông tin chi tiết về repository"""
        try:
            # Kiểm tra branch hiện tại
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            branch = result.stdout.strip() if result.returncode == 0 else "Unknown"
            
            # Kiểm tra số lượng commit
            result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            commit_count = result.stdout.strip() if result.returncode == 0 else "?"
            
            # Kiểm tra dung lượng .git folder
            git_dir = os.path.join(repo_path, ".git")
            if os.path.exists(git_dir):
                total_size = 0
                for dirpath, dirnames, filenames in os.walk(git_dir):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        total_size += os.path.getsize(fp) if os.path.exists(fp) else 0
                size_mb = total_size / (1024 * 1024)
                size_str = f"{size_mb:.1f} MB"
            else:
                size_str = "N/A"
            
            return {
                "branch": branch,
                "commits": commit_count,
                "size": size_str
            }
        except:
            return {"branch": "Unknown", "commits": "?", "size": "N/A"}
    
    def detect_current_git(self):
        """Phát hiện Git remote hiện tại trong thư mục được chọn"""
        repo_path = self.current_directory.get()
        
        if not repo_path or not os.path.exists(repo_path):
            self.current_remote_var.set("Please select a valid directory")
            self.repo_info_label.config(text="")
            return
        
        try:
            git_dir = os.path.join(repo_path, ".git")
            
            if not os.path.exists(git_dir):
                self.current_remote_var.set("No Git repository found in selected directory")
                self.repo_info_label.config(text="")
                self.log_message(f"⚠️ No Git repository found in: {repo_path}", "warning")
                return
            
            # Lấy thông tin remote
            result = subprocess.run(
                ["git", "remote", "-v"],
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                if lines:
                    # Lấy URL từ dòng đầu tiên
                    parts = lines[0].split()
                    if len(parts) > 1:
                        url = parts[1]
                        self.current_remote_var.set(url)
                        
                        # Lấy thông tin repository
                        repo_info = self.get_repo_info(repo_path)
                        info_text = f"Branch: {repo_info['branch']} • Commits: {repo_info['commits']} • Git Size: {repo_info['size']}"
                        self.repo_info_label.config(text=info_text)
                        
                        self.log_message(f"✅ Found Git repository in: {os.path.basename(repo_path)}", "success")
                        self.log_message(f"   Remote URL: {url}", "info")
                        self.log_message(f"   {info_text}", "info")
                    else:
                        self.current_remote_var.set("Invalid remote format")
                        self.repo_info_label.config(text="")
            else:
                self.current_remote_var.set("No remote configured")
                repo_info = self.get_repo_info(repo_path)
                info_text = f"Branch: {repo_info['branch']} • Commits: {repo_info['commits']} • Git Size: {repo_info['size']}"
                self.repo_info_label.config(text=info_text)
                self.log_message(f"ℹ️ Git repository found but no remote configured", "info")
                
        except Exception as e:
            self.current_remote_var.set(f"Error: {str(e)}")
            self.repo_info_label.config(text="")
            self.log_message(f"❌ Error detecting Git: {e}", "error")
    
    def log_message(self, message, message_type="info"):
        """Hiển thị message trong console"""
        colors = {
            "info": "#cccccc",
            "success": "#4CAF50",
            "warning": "#ffa726",
            "error": "#f44336",
            "command": "#61dafb"
        }
        
        color = colors.get(message_type, "#cccccc")
        
        self.console_text.insert(tk.END, f"{message}\n", message_type)
        self.console_text.tag_config(message_type, foreground=color)
        self.console_text.see(tk.END)
        self.root.update()
    
    def clear_console(self):
        """Xóa nội dung console"""
        self.console_text.delete(1.0, tk.END)
        self.log_message("Console cleared", "info")
    
    def save_log(self):
        """Lưu log ra file"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="git_migration_log.txt"
        )
        
        if file_path:
            try:
                with open(file_path, "w") as f:
                    f.write(self.console_text.get(1.0, tk.END))
                self.log_message(f"✅ Log saved to: {file_path}", "success")
            except Exception as e:
                self.log_message(f"❌ Error saving log: {e}", "error")
    
    def update_status(self, message):
        """Cập nhật status bar"""
        self.status_bar.config(text=message)
        self.root.update()
    
    def create_backup(self, repo_path):
        """Tạo backup của repository"""
        backup_dir = os.path.join(repo_path, "backup_git_migration")
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{backup_dir}_{timestamp}"
        
        try:
            os.makedirs(backup_path, exist_ok=True)
            
            # Copy .git folder
            git_source = os.path.join(repo_path, ".git")
            if os.path.exists(git_source):
                shutil.copytree(git_source, os.path.join(backup_path, ".git"))
            
            # Copy remote URL info
            with open(os.path.join(backup_path, "remote_info.txt"), "w") as f:
                f.write(f"Original Remote URL: {self.current_remote_var.get()}\n")
                f.write(f"Backup Time: {timestamp}\n")
            
            self.log_message(f"✅ Backup created at: {backup_path}", "success")
            return backup_path
            
        except Exception as e:
            self.log_message(f"⚠️ Failed to create backup: {e}", "warning")
            return None
    
    def run_git_command(self, command, show_output=True):
        """Chạy lệnh Git và trả về kết quả"""
        repo_path = self.current_directory.get()
        
        try:
            self.log_message(f"$ {' '.join(command)}", "command")
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=repo_path
            )
            
            if show_output and result.stdout:
                self.log_message(result.stdout.strip())
            if show_output and result.stderr:
                self.log_message(result.stderr.strip(), "warning")
            
            return result.returncode == 0, result.stdout, result.stderr
            
        except Exception as e:
            self.log_message(f"❌ Command failed: {e}", "error")
            return False, "", str(e)
    
    def migrate_with_history(self, new_url):
        """Di chuyển với giữ lại lịch sử"""
        repo_path = self.current_directory.get()
        self.log_message(f"\n📦 Repository: {os.path.basename(repo_path)}", "info")
        self.log_message("🔄 Starting migration with history preservation...", "info")
        
        # Tạo backup nếu được chọn
        if self.backup_var.get():
            self.log_message("📂 Creating backup...")
            self.create_backup(repo_path)
        
        # Lấy remote name
        success, stdout, stderr = self.run_git_command(["git", "remote"], False)
        if not success:
            return False
        
        remotes = stdout.strip().split('\n')
        remote_name = "origin" if "origin" in remotes else remotes[0] if remotes else "origin"
        
        # Đổi URL remote
        self.log_message(f"Changing remote '{remote_name}' URL...")
        success, stdout, stderr = self.run_git_command(
            ["git", "remote", "set-url", remote_name, new_url]
        )
        
        if success:
            self.log_message("✅ Remote URL changed successfully!", "success")
            
            # Verify new remote
            self.log_message("\nVerifying new remote configuration:")
            self.run_git_command(["git", "remote", "-v"])
            
            # Update current remote display
            self.current_remote_var.set(new_url)
            
            # Push nếu được chọn
            if self.push_after_var.get():
                self.log_message("\n📤 Pushing to new remote...")
                push_success, stdout, stderr = self.run_git_command(
                    ["git", "push", "-u", remote_name, "--all"]
                )
                if push_success:
                    self.log_message("✅ Successfully pushed to new remote!", "success")
                else:
                    self.log_message("⚠️ Push failed, you can push manually later", "warning")
            
            self.log_message("\n🎉 Migration completed successfully!", "success")
            self.log_message(f"New repository: {new_url}", "info")
            
            return True
        else:
            self.log_message("❌ Failed to change remote URL", "error")
            return False
    
    def migrate_fresh_start(self, new_url):
        """Xóa .git và bắt đầu mới"""
        repo_path = self.current_directory.get()
        self.log_message(f"\n📦 Repository: {os.path.basename(repo_path)}", "info")
        self.log_message("🔄 Starting fresh migration (deleting .git)...", "info")
        
        # Xác nhận
        confirm = messagebox.askyesno(
            "⚠️ WARNING - Delete Git History",
            "This will DELETE ALL Git history and start fresh.\n"
            "All commit history will be PERMANENTLY LOST!\n\n"
            "Are you ABSOLUTELY sure you want to continue?\n\n"
            "Recommended: Use 'Keep Git History' option instead."
        )
        
        if not confirm:
            self.log_message("❌ Migration cancelled by user", "warning")
            return False
        
        # Tạo backup nếu được chọn
        if self.backup_var.get():
            self.log_message("📂 Creating backup...")
            self.create_backup(repo_path)
        
        try:
            # Lưu remote cũ (chỉ để log)
            self.run_git_command(["git", "remote", "-v"], False)
            
            # Xóa .git folder
            self.log_message("Deleting .git folder...")
            git_dir = os.path.join(repo_path, ".git")
            if os.path.exists(git_dir):
                shutil.rmtree(git_dir)
                self.log_message("✅ .git folder deleted", "success")
            else:
                self.log_message("⚠️ .git folder not found", "warning")
                return False
            
            # Khởi tạo lại Git
            self.log_message("Initializing new Git repository...")
            self.run_git_command(["git", "init"])
            
            # Thêm remote mới
            self.log_message(f"Adding new remote: {new_url}")
            self.run_git_command(["git", "remote", "add", "origin", new_url])
            
            # Thêm tất cả files
            self.log_message("Adding all files...")
            self.run_git_command(["git", "add", "."])
            
            # Tạo commit đầu tiên
            self.log_message("Creating initial commit...")
            self.run_git_command(["git", "commit", "-m", "Initial commit - migrated to new repository"])
            
            # Update current remote display
            self.current_remote_var.set(new_url)
            
            # Push nếu được chọn
            if self.push_after_var.get():
                self.log_message("\n📤 Pushing to new remote...")
                push_success, stdout, stderr = self.run_git_command(
                    ["git", "push", "-u", "origin", "main"]
                )
                if not push_success:
                    # Thử với master branch
                    self.run_git_command(["git", "push", "-u", "origin", "master"])
            
            self.log_message("\n🎉 Fresh migration completed successfully!", "success")
            self.log_message(f"New repository: {new_url}", "info")
            
            return True
            
        except Exception as e:
            self.log_message(f"❌ Error during fresh migration: {e}", "error")
            return False
    
    def start_migration_thread(self):
        """Chạy migration trong thread riêng để không block GUI"""
        # Lấy thông tin từ GUI
        repo_path = self.current_directory.get()
        new_url = self.new_remote_var.get().strip()
        
        # Kiểm tra thư mục
        if not repo_path or not os.path.exists(repo_path):
            messagebox.showerror("Error", "Please select a valid directory")
            return
        
        # Kiểm tra Git repository
        git_dir = os.path.join(repo_path, ".git")
        if not os.path.exists(git_dir):
            messagebox.showerror("Error", "No Git repository found in selected directory")
            return
        
        # Kiểm tra URL
        if not new_url or new_url == "https://github.com/username/new-repository.git":
            messagebox.showerror("Error", "Please enter a valid new GitHub URL")
            return
        
        # Kiểm tra URL format
        if not (new_url.startswith("https://") or new_url.startswith("git@")):
            messagebox.showerror("Error", "Invalid URL format. Use HTTPS or SSH format.")
            return
        
        # Xóa console cũ
        self.console_text.delete(1.0, tk.END)
        
        # Hiển thị thông tin bắt đầu
        self.log_message("=" * 60, "info")
        self.log_message(f"GIT MIGRATION STARTED", "success")
        self.log_message(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "info")
        self.log_message(f"From: {self.current_remote_var.get()}", "info")
        self.log_message(f"To: {new_url}", "info")
        self.log_message("=" * 60, "info")
        
        # Chọn phương pháp
        method = self.migration_method.get()
        
        # Chạy migration
        if method == 1:  # Keep history
            success = self.migrate_with_history(new_url)
        else:  # Fresh start
            success = self.migrate_fresh_start(new_url)
        
        # Hiển thị kết quả
        if success:
            self.update_status("✅ Migration completed successfully!")
            messagebox.showinfo("Success", 
                "Migration completed successfully!\n\n"
                f"Repository moved to: {new_url}\n"
                "Check console for details.")
        else:
            self.update_status("❌ Migration failed")
            messagebox.showerror("Error", 
                "Migration failed!\n\n"
                "Check console for error details.\n"
                "Your original repository should still be intact.")
    
    def start_migration(self):
        """Bắt đầu quá trình migration"""
        self.update_status("Starting migration...")
        
        # Chạy trong thread riêng
        thread = threading.Thread(target=self.start_migration_thread)
        thread.daemon = True
        thread.start()

import datetime  # Thêm import datetime

def main():
    root = tk.Tk()
    
    # Đặt icon cho ứng dụng (nếu có file icon)
    try:
        root.iconbitmap(default='icon.ico')
    except:
        pass
    
    app = GitHubMigratorApp(root)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()

if __name__ == "__main__":
    # Kiểm tra Git
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
    except:
        print("❌ Git is not installed. Please install Git first.")
        print("Download from: https://git-scm.com/downloads")
        sys.exit(1)
    
    main()