import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import json
import os
import time
import sys

CONFIG_FILE = "config.json"

class QuotaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("QuotaAntigravity Dashboard")
        self.geometry("450x350")
        self.configure(padx=10, pady=10)
        
        # Initial Data Path
        self.data_path = "quota_data.dat"
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    conf = json.load(f)
                    self.data_path = conf.get("data_path", "")
            except:
                pass
                
        self.setup_ui()
        self.update_loop()

    def setup_ui(self):
        # Header
        top_frame = tk.Frame(self)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(top_frame, text="Đường dẫn Data:").pack(side=tk.LEFT)
        self.path_var = tk.StringVar(value=self.data_path if self.data_path else "Chưa thiết lập...")
        tk.Label(top_frame, textvariable=self.path_var, fg="gray").pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="Chọn", command=self.choose_path).pack(side=tk.RIGHT)

        # Sync button row
        sync_frame = tk.Frame(self)
        sync_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Button(sync_frame, text="🔄 Auto-Sync từ IDE", command=self.sync_from_ide, bg="#0984e3", fg="white").pack(side=tk.LEFT)
        
        tk.Button(sync_frame, text="➕ Thêm Account", command=self.add_account).pack(side=tk.LEFT, padx=5)

        # Treeview
        columns = ("email", "status", "countdown", "models")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=10)
        self.tree.heading("email", text="Email Account")
        self.tree.heading("status", text="Trạng thái")
        self.tree.heading("countdown", text="Đếm ngược (24h)")
        self.tree.heading("models", text="Models OK")
        
        self.tree.column("email", width=160)
        self.tree.column("status", width=80, anchor=tk.CENTER)
        self.tree.column("countdown", width=110, anchor=tk.CENTER)
        self.tree.column("models", width=90, anchor=tk.CENTER)
        
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        # Tags for styling
        self.tree.tag_configure('ready', foreground='green')
        self.tree.tag_configure('wait', foreground='red')

    def choose_path(self):
        filepath = filedialog.askopenfilename(
            title="Chọn thư mục chứa File Data (quota_data.dat)",
            filetypes=[("Data files", "*.dat")]
        )
        if filepath:
            self.data_path = filepath
            if not os.path.exists(self.data_path):
                import base64
                with open(self.data_path, 'w', encoding='utf-8') as f:
                    f.write(base64.b64encode(json.dumps({}, ensure_ascii=False).encode('utf-8')).decode('ascii'))
            self.path_var.set(self.data_path)
            with open(CONFIG_FILE, "w") as f:
                json.dump({"data_path": self.data_path}, f)
            self.refresh_data()

    def sync_from_ide(self):
        if not self.data_path:
            messagebox.showwarning("Lỗi", "Vui lòng chọn file Data trước.")
            return
        try:
            import sync_antigravity
            sys.argv = ["", self.data_path]
            res = sync_antigravity.sync_quota_data(self.data_path)
            if res.get('status') == 'ok':
                messagebox.showinfo("Thành công", res.get('message', 'Đã sync.'))
                self.refresh_data()
            else:
                messagebox.showerror("Lỗi", res.get('message', 'Không rõ lỗi.'))
        except Exception as e:
            messagebox.showerror("Lỗi Exception", str(e))

    def add_account(self):
        messagebox.showinfo(
            "Đăng nhập qua IDE", 
            "Tính năng 'Thêm Account' (OAuth Login) đã được liên kết với Antigravity IDE để lấy thông tin tự động.\n\n"
            "Vui lòng quay lại IDE, mở bảng Quota và ấn nút [➕ Thêm Account] để đăng nhập. Sau đó bấm [🔄 Auto-Sync từ IDE] tại đây để cập nhật."
        )

    def refresh_data(self):
        if not self.data_path or not os.path.exists(self.data_path):
            return

        try:
            import base64
            with open(self.data_path, 'r', encoding='utf-8') as f:
                raw = f.read().strip()
                if raw:
                    decoded = base64.b64decode(raw).decode('utf-8')
                    data = json.loads(decoded)
                else:
                    data = {}
        except Exception as e:
            print(f"Lỗi đọc file: {e}")
            return

        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)

        active_email = ""
        active_path = os.path.join(os.path.dirname(self.data_path), "active_account.txt")
        if os.path.exists(active_path):
            try:
                with open(active_path, "r", encoding="utf-8") as f:
                    active_email = f.read().strip()
            except:
                pass

        now = int(time.time() * 1000)
        
        for email, info in data.items():
            exhausted_until = info.get("exhaustedUntil", 0)
            available_groups = info.get("availableGroups", [])
            models_str = ",".join(available_groups).upper() if available_groups else "-"

            if exhausted_until > now:
                status = "Hết Quota"
                remaining_ms = exhausted_until - now
                hours = remaining_ms // (1000 * 60 * 60)
                mins = (remaining_ms % (1000 * 60 * 60)) // (1000 * 60)
                secs = (remaining_ms % (1000 * 60)) // 1000
                countdown = f"{hours:02d}:{mins:02d}:{secs:02d}"
                tag = 'wait'
            else:
                gemini_percent = 100
                if "groupStatus" in info and "gemini" in info["groupStatus"]:
                    gemini_percent = info["groupStatus"]["gemini"].get("percent", 100)
                status = f"Sẵn sàng ({gemini_percent}%)"
                overall_reset = info.get("overallResetTime", 0)
                if overall_reset > now:
                    remaining_ms = overall_reset - now
                    hours = remaining_ms // (1000 * 60 * 60)
                    mins = (remaining_ms % (1000 * 60 * 60)) // (1000 * 60)
                    secs = (remaining_ms % (1000 * 60)) // 1000
                    countdown = f"{hours:02d}:{mins:02d}:{secs:02d}"
                else:
                    countdown = "-"
                tag = 'ready'
                models_str = "ALL"
            
            display_email = email
            if email == active_email:
                display_email += " (ACTIVE)"
                
            self.tree.insert("", tk.END, values=(display_email, status, countdown, models_str), tags=(tag,))

    def update_loop(self):
        self.refresh_data()
        self.after(1000, self.update_loop)

if __name__ == "__main__":
    app = QuotaApp()
    app.mainloop()
