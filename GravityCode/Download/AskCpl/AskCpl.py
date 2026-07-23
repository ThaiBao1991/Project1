import os
import json
import time
import threading
import sys
import subprocess
import tkinter as tk
from tkinter import Tk, filedialog, messagebox, Button, Label, Frame, StringVar, IntVar, Entry, Text, END, Listbox, Scrollbar, BooleanVar, Checkbutton, Radiobutton, simpledialog, Toplevel
from tkinter import ttk


REQUIRED_PACKAGES = {
    'cryptography': 'cryptography==49.0.0',
    'win32com': 'pywin32==306',
    'bs4': 'beautifulsoup4==4.12.3',
    'flask': 'Flask==3.1.3',
    'markdown': 'markdown==3.10.2',
    'requests': 'requests==2.31.0',
    'flask_cors': 'Flask-Cors==6.0.5',
    'google': 'google-genai',
    'fitz': 'PyMuPDF'
}

def check_and_install_packages():
    missing = []
    for module_name, pip_name in REQUIRED_PACKAGES.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(pip_name)
            
    if missing:
        print(f"[*] Đang tự động cài đặt thư viện còn thiếu: {', '.join(missing)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", *missing])
            print("[*] Cài đặt thành công!")
        except Exception as e:
            root = Tk()
            root.withdraw()
            err_win = tk.Toplevel(root)
            err_win.title("Lỗi Thiếu Thư Viện")
            err_win.geometry("550x300")
            Label(err_win, text="Ứng dụng thiếu một số thư viện cần thiết và không thể cài đặt tự động.", fg="red", font=("Arial", 11, "bold")).pack(pady=10)
            Label(err_win, text="Vui lòng copy dòng lệnh dưới đây và dán vào Terminal/CMD để cài đặt:", font=("Arial", 10)).pack(pady=5)
            
            txt = Text(err_win, height=3, width=60, font=("Consolas", 11))
            txt.pack(pady=10)
            cmd = "python -m pip install --user " + " ".join(missing)
            txt.insert(END, cmd)
            txt.config(state="disabled")
            
            Button(err_win, text="Thoát ứng dụng", command=root.destroy, width=15).pack(pady=15)
            root.mainloop()
            sys.exit(1)

check_and_install_packages()

try:
    import win32com.client
except ImportError:
    win32com = None

# Import các module mới
from settings import load_settings, update_github_settings, update_editor_settings, update_gemini_settings
from github_api import GitHubSync
from exercise_builder import save_exercise_to_html, remove_exercise_from_html
from nav_injector import inject_all, rebuild_index, get_day_files
import webbrowser
try:
    from exercise_server import run_server
except ImportError:
    run_server = None

class AskCplApp:
    def __init__(self, root):
        if run_server:
            threading.Thread(target=run_server, daemon=True).start()
        self.root = root
        self.root.title("Copilot Addon Manager")
        self.root.state('zoomed')
        
        # Load settings
        self.settings = load_settings()
        
        # Tạo Notebook (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Tabs
        self.tab_word = ttk.Frame(self.notebook)
        self.tab_github = ttk.Frame(self.notebook)
        self.tab_exercise = ttk.Frame(self.notebook)
        self.tab_config_index = ttk.Frame(self.notebook)
        self.tab_note = ttk.Frame(self.notebook)
        self.tab_auto_ai = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_auto_ai, text="🤖 Auto AI")
        self.notebook.add(self.tab_word, text="Xuất Word")
        self.notebook.add(self.tab_github, text="Upload GitHub")
        self.notebook.add(self.tab_exercise, text="Trình Tạo Bài Tập")
        self.notebook.add(self.tab_note, text="📝 Trình Tạo Note")
        self.notebook.add(self.tab_config_index, text="⚙️ Config Index")
        
        self.setup_tab_auto_ai()
        self.setup_tab_word()
        self.setup_tab_github()
        self.setup_tab_exercise()
        self.setup_tab_note()
        self.setup_tab_config_index()
        
    # --- TAB 0: AUTO AI ---
    def setup_tab_auto_ai(self):
        Label(self.tab_auto_ai, text="🤖 Auto AI - Sinh HTML tự động từ PDF", font=("Arial", 14, "bold")).pack(pady=10)
        
        gemini_settings = self.settings.get("gemini", {})
        
        # API Keys Manager
        f1 = Frame(self.tab_auto_ai)
        f1.pack(fill='x', padx=20, pady=5)
        Label(f1, text="Gemini API Keys:", width=15, anchor='w').pack(side='left')
        self.lbl_keys_status = Label(f1, text="Đang tải...", fg="blue")
        self.lbl_keys_status.pack(side='left', padx=10)
        Button(f1, text="🔑 Quản lý API Keys...", command=self.open_api_key_manager, bg="#8e44ad", fg="white").pack(side='right')
        self.update_keys_label()
        
        # Roadmap File
        f2 = Frame(self.tab_auto_ai)
        f2.pack(fill='x', padx=20, pady=5)
        Label(f2, text="File Roadmap:", width=15, anchor='w').pack(side='left')
        self.ai_roadmap_var = StringVar(value=gemini_settings.get("last_roadmap", ""))
        Entry(f2, textvariable=self.ai_roadmap_var, state='readonly').pack(side='left', fill='x', expand=True)
        Button(f2, text="Chọn Markdown", command=self.ai_select_roadmap).pack(side='right', padx=5)
        
        # Doc Dir
        f3 = Frame(self.tab_auto_ai)
        f3.pack(fill='x', padx=20, pady=5)
        Label(f3, text="Thư mục Docs:", width=15, anchor='w').pack(side='left')
        self.ai_doc_var = StringVar(value=gemini_settings.get("last_doc_dir", ""))
        Entry(f3, textvariable=self.ai_doc_var, state='readonly').pack(side='left', fill='x', expand=True)
        Button(f3, text="Chọn thư mục chứa PDF", command=self.ai_select_doc_dir).pack(side='right', padx=5)
        
        # Output Dir
        f4 = Frame(self.tab_auto_ai)
        f4.pack(fill='x', padx=20, pady=5)
        Label(f4, text="Thư mục Xuất:", width=15, anchor='w').pack(side='left')
        self.ai_out_var = StringVar(value=gemini_settings.get("last_out_dir", ""))
        Entry(f4, textvariable=self.ai_out_var, state='readonly').pack(side='left', fill='x', expand=True)
        Button(f4, text="Chọn Output", command=self.ai_select_out_dir).pack(side='right', padx=5)
        
        # Save Settings
        Button(self.tab_auto_ai, text="Lưu Cấu Hình AI", command=self.save_ai_settings, bg="#f39c12", fg="white").pack(pady=5)
        
        # Options row
        f_opts = Frame(self.tab_auto_ai)
        f_opts.pack(fill='x', padx=20, pady=3)
        self.ai_force_restart_var = IntVar(value=0)
        Checkbutton(f_opts, text="🗑️ Xóa session cũ & Chạy lại từ Đầu (Day 1)", variable=self.ai_force_restart_var, fg="red").pack(side='left')
        
        Label(f_opts, text="   HOẶC Bắt đầu từ Day:").pack(side='left')
        self.ai_start_day_var = StringVar(value="")
        Entry(f_opts, textvariable=self.ai_start_day_var, width=5).pack(side='left', padx=5)
        
        self.lbl_session_status = Label(f_opts, text="", fg="#d35400", font=("Arial", 9, "bold"))
        self.lbl_session_status.pack(side='left', padx=10)
        
        # YC5 options row
        f_opts_followup = Frame(self.tab_auto_ai)
        f_opts_followup.pack(fill='x', padx=20, pady=3)
        self.ai_enable_followup_var = IntVar(value=gemini_settings.get("enable_followup", 1))
        Checkbutton(f_opts_followup, text="Bật hỏi bổ sung (Follow-up) để AI làm rõ thêm (YC5)", 
                    variable=self.ai_enable_followup_var).pack(side='left')
        
        # Follow-up mode: unlimited vs limited
        f_followup_mode = Frame(self.tab_auto_ai)
        f_followup_mode.pack(fill='x', padx=40, pady=2)
        self.ai_followup_mode_var = StringVar(value=gemini_settings.get("followup_mode", "unlimited"))
        
        rb_unlimited = Radiobutton(f_followup_mode, text="Hỏi đến khi AI xác nhận hoàn thành  (Khuyến nghị)",
                                   variable=self.ai_followup_mode_var, value="unlimited",
                                   fg="#27ae60", font=("Arial", 9, "bold"))
        rb_unlimited.pack(side='left')
        
        rb_limited = Radiobutton(f_followup_mode, text="Hỏi tối đa:",
                                 variable=self.ai_followup_mode_var, value="limited")
        rb_limited.pack(side='left', padx=(15, 2))
        
        self.ai_max_followup_var = StringVar(value=str(gemini_settings.get("max_followup", 3)))
        self.entry_max_followup = Entry(f_followup_mode, textvariable=self.ai_max_followup_var, width=4)
        self.entry_max_followup.pack(side='left', padx=2)
        Label(f_followup_mode, text="lượt").pack(side='left')
        
        def _toggle_followup_entry(*args):
            if self.ai_followup_mode_var.get() == "limited":
                self.entry_max_followup.config(state='normal')
            else:
                self.entry_max_followup.config(state='disabled')
        self.ai_followup_mode_var.trace_add("write", _toggle_followup_entry)
        _toggle_followup_entry()  # set initial state

        
        # Expand roadmap section
        f_expand = Frame(self.tab_auto_ai)
        f_expand.pack(fill='x', padx=20, pady=3)
        Label(f_expand, text="📋 Tạo Roadmap Mở Rộng:", anchor='w').pack(side='left')
        self.ai_pages_per_day_var = StringVar(value="10")
        Entry(f_expand, textvariable=self.ai_pages_per_day_var, width=4).pack(side='left', padx=2)
        Label(f_expand, text="trang/Day").pack(side='left')
        Button(f_expand, text="📋 Tạo roadmap_expanded.md", command=self.expand_roadmap_handler,
               bg="#1565c0", fg="white").pack(side='right', padx=5)
        
        # Output path for expanded roadmap
        f_exp_out = Frame(self.tab_auto_ai)
        f_exp_out.pack(fill='x', padx=20, pady=2)
        Label(f_exp_out, text="   ↳ Lưu expanded ra:", width=15, anchor='w').pack(side='left')
        self.ai_expanded_out_var = StringVar(value="")
        Entry(f_exp_out, textvariable=self.ai_expanded_out_var, state='readonly').pack(side='left', fill='x', expand=True)
        Button(f_exp_out, text="Chọn", command=self.ai_select_expanded_out).pack(side='right', padx=5)
        Label(f_exp_out, text="(trống = cạnh file roadmap gốc)", fg="gray", font=("Arial", 8)).pack(side='right')
        
        # Start button
        self.btn_ai_start = Button(self.tab_auto_ai, text="▶ Bắt đầu Sinh Tự Động", command=self.start_ai_worker, bg="#2ea043", fg="white", font=("Arial", 12, "bold"), padx=20)
        self.btn_ai_start.pack(pady=10)
        
        # Logs (with scrollbar)
        Label(self.tab_auto_ai, text="Tiến trình:", font=("Arial", 10, "bold"), anchor='w').pack(fill='x', padx=20)
        f_log = Frame(self.tab_auto_ai)
        f_log.pack(fill='both', expand=True, padx=20, pady=5)
        log_scroll = Scrollbar(f_log)
        log_scroll.pack(side='right', fill='y')
        self.ai_log = Text(f_log, height=12, state='disabled', bg="#f4f4f4", yscrollcommand=log_scroll.set)
        self.ai_log.pack(fill='both', expand=True)
        log_scroll.config(command=self.ai_log.yview)
        
        self.ai_out_var.trace_add("write", self.check_auto_ai_session)
        self.check_auto_ai_session()
        
    def check_auto_ai_session(self, *args):
        out_dir = self.ai_out_var.get()
        if not out_dir or not os.path.isdir(out_dir):
            if hasattr(self, 'lbl_session_status'):
                self.lbl_session_status.config(text="")
            return
            
        session_file = os.path.join(out_dir, "session.json")
        if not os.path.exists(session_file):
            self.lbl_session_status.config(text="Chưa có dữ liệu session")
            self.ai_start_day_var.set("")
            return
            
        try:
            import base64
            import re
            
            with open(session_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    self.lbl_session_status.config(text="Session trống")
                    self.ai_start_day_var.set("")
                    return
                if content.startswith('"') and content.endswith('"'):
                    content = content[1:-1]
                    decoded_str = base64.b64decode(content).decode('utf-8')
                    session_data = json.loads(decoded_str)
                else:
                    session_data = json.loads(content)
                    
            if not session_data:
                self.lbl_session_status.config(text="Session trống")
                self.ai_start_day_var.set("")
                return
                
            last_completed_day = -1
            incomplete_day = -1
            
            for item in session_data:
                m = re.search(r'Day\s+(\d+)', item.get("day", ""), re.IGNORECASE)
                if not m: continue
                d_num = int(m.group(1))
                
                if item.get("completed"):
                    if item.get("followup_complete", True):
                        if d_num > last_completed_day:
                            last_completed_day = d_num
                    else:
                        incomplete_day = d_num
                        
            if incomplete_day > 0:
                self.lbl_session_status.config(text=f"Đang dang dở tại: Day {incomplete_day}")
                self.ai_start_day_var.set(str(incomplete_day))
            elif last_completed_day > 0:
                self.lbl_session_status.config(text=f"Hoàn thành gần nhất: Day {last_completed_day}")
                self.ai_start_day_var.set(str(last_completed_day + 1))
            else:
                self.lbl_session_status.config(text="Chưa có hoàn thành nào")
                self.ai_start_day_var.set("")
                
        except Exception as e:
            if hasattr(self, 'lbl_session_status'):
                self.lbl_session_status.config(text="Lỗi đọc session")
                
    def update_keys_label(self):
        gemini_settings = self.settings.get("gemini", {})
        keys = gemini_settings.get("api_keys", [])
        active = sum(1 for k in keys if k.get("status") == "active")
        self.lbl_keys_status.config(text=f"Đang có {len(keys)} Key (Hoạt động: {active})")

    def open_api_key_manager(self):
        top = Toplevel(self.root)
        top.title("Quản lý API Keys (Multi-Key)")
        top.geometry("980x440")
        top.transient(self.root)
        top.grab_set()

        from tkinter import ttk, messagebox
        import datetime
        import time
        import requests
        import threading
        import re as _re

        # === HELPER: extract raw key (decode ENC: if needed) ===
        def decode_key(raw_key):
            if raw_key.startswith("ENC:"):
                try:
                    import base64
                    return base64.b64decode(raw_key[4:]).decode("utf-8")
                except Exception:
                    return raw_key
            return raw_key

        # === HELPER: extract project ID from error response ===
        def extract_project_id(resp_json):
            try:
                details = resp_json.get("error", {}).get("details", [])
                for d in details:
                    consumer = d.get("consumer", "")
                    if consumer.startswith("projects/"):
                        return consumer.replace("projects/", "")
            except Exception:
                pass
            return ""

        # === TREEVIEW ===
        columns = ("email", "key", "project", "status", "last_check", "reset_time")
        tree = ttk.Treeview(top, columns=columns, show="headings")
        tree.heading("email", text="Email / Tên")
        tree.heading("key", text="API Key")
        tree.heading("project", text="Project ID")
        tree.heading("status", text="Trạng thái")
        tree.heading("last_check", text="Check lần cuối")
        tree.heading("reset_time", text="Khôi phục sau")

        tree.column("email", width=120)
        tree.column("key", width=200)
        tree.column("project", width=120)
        tree.column("status", width=95)
        tree.column("last_check", width=120)
        tree.column("reset_time", width=120)

        # Tag màu đỏ cho key trùng project
        tree.tag_configure("dup_project", background="#ffcccc", foreground="#c0392b")

        vsb = ttk.Scrollbar(top, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(fill="both", expand=True, padx=10, pady=(10, 0), side="left")
        vsb.pack(fill="y", pady=(10, 0), side="left")

        def edit_key(event=None):
            selected = tree.selection()
            if not selected: return
            idx = int(selected[0])
            gemini_settings = self.settings.get("gemini", {})
            keys = gemini_settings.get("api_keys", [])
            if idx < 0 or idx >= len(keys): return

            k_obj = keys[idx]

            edit_win = Toplevel(top)
            edit_win.title("Sửa API Key")
            edit_win.geometry("460x310")
            edit_win.transient(top)
            edit_win.grab_set()
            edit_win.bind("<Escape>", lambda e: edit_win.destroy())

            Label(edit_win, text="Nhập API Key:", anchor='w').pack(fill='x', padx=20, pady=(15, 2))
            entry_key = Entry(edit_win, width=50)
            entry_key.pack(fill='x', padx=20, pady=2)
            entry_key.insert(0, k_obj.get("key", ""))

            Label(edit_win, text="Tên/Email gợi nhớ:", anchor='w').pack(fill='x', padx=20, pady=(10, 2))
            entry_email = Entry(edit_win, width=50)
            entry_email.pack(fill='x', padx=20, pady=2)
            entry_email.insert(0, k_obj.get("email", ""))

            disp_s = k_obj.get("status", "active")
            if disp_s == "invalid" and k_obj.get("error_msg"):
                disp_s = f"Lỗi: {k_obj.get('error_msg')}"
            status_var = StringVar(value=disp_s)
            lbl_status = Label(edit_win, textvariable=status_var, fg="gray", font=("Arial", 10, "bold"))
            lbl_status.pack(pady=10)

            def check_new_key():
                api_key = decode_key(entry_key.get().strip())
                if not api_key:
                    messagebox.showerror("Lỗi", "Vui lòng nhập API Key trước khi kiểm tra!", parent=edit_win)
                    return
                status_var.set("Đang kiểm tra...")
                lbl_status.config(fg="blue")
                edit_win.update_idletasks()

                def run_check():
                    try:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
                        headers = {'Content-Type': 'application/json'}
                        payload = {"contents": [{"parts": [{"text": "Hello"}]}]}
                        resp = requests.post(url, headers=headers, json=payload, timeout=10)
                        if resp.status_code == 200:
                            edit_win.after(0, lambda: [status_var.set("Hoạt động (Active)"), lbl_status.config(fg="green")])
                        else:
                            msg = resp.json().get("error", {}).get("message", "Lỗi không xác định")
                            proj = extract_project_id(resp.json())
                            if proj:
                                keys[idx]["project_id"] = proj
                            if "Quota" in msg or "exhausted" in msg.lower():
                                edit_win.after(0, lambda: [status_var.set("Hết Quota (Exhausted)"), lbl_status.config(fg="orange")])
                            else:
                                edit_win.after(0, lambda: [status_var.set(f"Lỗi: {msg[:35]}"), lbl_status.config(fg="red")])
                    except Exception as e:
                        edit_win.after(0, lambda: [status_var.set(f"Lỗi: {str(e)[:35]}"), lbl_status.config(fg="red")])
                threading.Thread(target=run_check, daemon=True).start()

            def do_save():
                k_val = entry_key.get().strip()
                e_val = entry_email.get().strip()
                if not k_val:
                    messagebox.showerror("Lỗi", "Vui lòng nhập API Key!", parent=edit_win)
                    return

                for i, k in enumerate(keys):
                    if i != idx and k.get("key") == k_val:
                        messagebox.showerror("Lỗi", "API Key này đã tồn tại trong danh sách!", parent=edit_win)
                        return

                cur_status = status_var.get()
                status_mapped = k_obj.get("status", "active")
                reset_time = k_obj.get("reset_time", 0)
                next_check_time = k_obj.get("next_check_time", 0)
                error_msg = k_obj.get("error_msg", "")

                if "Exhausted" in cur_status:
                    status_mapped = "exhausted"
                    reset_time = int(time.time()) + 86400
                    next_check_time = int(time.time()) + 10800
                elif "Lỗi" in cur_status:
                    status_mapped = "invalid"
                    error_msg = cur_status.replace("Lỗi: ", "")
                elif "Active" in cur_status:
                    status_mapped = "active"
                    reset_time = 0
                    next_check_time = 0
                    error_msg = ""

                keys[idx]["key"] = k_val
                keys[idx]["email"] = e_val
                keys[idx]["status"] = status_mapped
                keys[idx]["reset_time"] = reset_time
                keys[idx]["next_check_time"] = next_check_time
                keys[idx]["error_msg"] = error_msg

                from settings import update_gemini_settings
                update_gemini_settings(api_keys=keys)
                self.settings = load_settings()
                refresh_list()
                edit_win.destroy()

            f_btns = Frame(edit_win)
            f_btns.pack(fill="x", padx=20, pady=5)
            Button(f_btns, text="🔍 Kiểm tra", command=check_new_key, bg="#f39c12", fg="white", width=12).pack(side="left", padx=5)
            Button(f_btns, text="Lưu", command=do_save, bg="#27ae60", fg="white", width=8).pack(side="left", padx=5)
            Button(f_btns, text="Hủy", command=edit_win.destroy, bg="#e74c3c", fg="white", width=8).pack(side="right", padx=5)

        tree.bind("<Double-1>", edit_key)

        def refresh_list():
            for item in tree.get_children():
                tree.delete(item)
            gemini_settings = self.settings.get("gemini", {})
            keys = gemini_settings.get("api_keys", [])

            # Tìm project_id trùng
            project_counts = {}
            for k in keys:
                pid = k.get("project_id", "")
                if pid:
                    project_counts[pid] = project_counts.get(pid, 0) + 1
            dup_projects = {pid for pid, cnt in project_counts.items() if cnt > 1}

            for idx, k in enumerate(keys):
                masked_key = k.get("key", "")
                if len(masked_key) > 10:
                    masked_key = masked_key[:4] + "*" * (len(masked_key)-8) + masked_key[-4:]

                rt = k.get("reset_time", 0)
                rt_str = datetime.datetime.fromtimestamp(rt).strftime('%Y-%m-%d %H:%M') if rt > 0 else "-"

                lc = k.get("last_check_time", 0)
                lc_str = datetime.datetime.fromtimestamp(lc).strftime('%Y-%m-%d %H:%M') if lc > 0 else "-"

                disp_status = k.get("status", "active")
                if disp_status == "invalid" and k.get("error_msg"):
                    disp_status = f"invalid: {k.get('error_msg')}"

                pid = k.get("project_id", "")
                tag = ("dup_project",) if pid and pid in dup_projects else ()

                tree.insert("", "end", iid=str(idx), values=(
                    k.get("email", ""),
                    masked_key,
                    pid if pid else "-",
                    disp_status,
                    lc_str,
                    rt_str
                ), tags=tag)
            self.update_keys_label()

        def add_key():
            add_win = Toplevel(top)
            add_win.title("Thêm API Key Mới")
            add_win.geometry("460x310")
            add_win.transient(top)
            add_win.grab_set()
            add_win.bind("<Escape>", lambda e: add_win.destroy())

            Label(add_win, text="Nhập API Key:", anchor='w').pack(fill='x', padx=20, pady=(15, 2))
            entry_key = Entry(add_win, width=50)
            entry_key.pack(fill='x', padx=20, pady=2)
            entry_key.focus_set()

            Label(add_win, text="Tên/Email gợi nhớ (để trống để tự điền sau):", anchor='w').pack(fill='x', padx=20, pady=(10, 2))
            entry_email = Entry(add_win, width=50)
            entry_email.pack(fill='x', padx=20, pady=2)

            status_var = StringVar(value="Chưa kiểm tra trạng thái")
            lbl_status = Label(add_win, textvariable=status_var, fg="gray", font=("Arial", 10, "bold"))
            lbl_status.pack(pady=10)

            _check_result = {"project_id": "", "status": "", "done": False}

            def run_check_inner(api_key_raw, on_done=None):
                api_key = decode_key(api_key_raw)
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
                    headers = {'Content-Type': 'application/json'}
                    payload = {"contents": [{"parts": [{"text": "Hello"}]}]}
                    resp = requests.post(url, headers=headers, json=payload, timeout=10)
                    if resp.status_code == 200:
                        _check_result["status"] = "active"
                        add_win.after(0, lambda: [status_var.set("Hoạt động (Active)"), lbl_status.config(fg="green")])
                    else:
                        rj = resp.json()
                        msg = rj.get("error", {}).get("message", "Lỗi không xác định")
                        proj = extract_project_id(rj)
                        _check_result["project_id"] = proj
                        if "Quota" in msg or "exhausted" in msg.lower():
                            _check_result["status"] = "exhausted"
                            add_win.after(0, lambda: [status_var.set("Hết Quota (Exhausted)"), lbl_status.config(fg="orange")])
                        else:
                            _check_result["status"] = "invalid"
                            _check_result["errmsg"] = msg[:35]
                            add_win.after(0, lambda: [status_var.set(f"Lỗi: {msg[:35]}"), lbl_status.config(fg="red")])
                except Exception as e:
                    _check_result["status"] = "invalid"
                    _check_result["errmsg"] = str(e)[:35]
                    add_win.after(0, lambda: [status_var.set(f"Lỗi: {str(e)[:35]}"), lbl_status.config(fg="red")])
                _check_result["done"] = True
                if on_done:
                    add_win.after(0, on_done)

            def check_new_key():
                api_key_raw = entry_key.get().strip()
                if not api_key_raw:
                    messagebox.showerror("Lỗi", "Vui lòng nhập API Key trước khi kiểm tra!", parent=add_win)
                    return
                _check_result["done"] = False
                status_var.set("Đang kiểm tra...")
                lbl_status.config(fg="blue")
                add_win.update_idletasks()
                threading.Thread(target=run_check_inner, args=(api_key_raw,), daemon=True).start()

            def do_save():
                k_val = entry_key.get().strip()
                e_val = entry_email.get().strip() or "(chưa đặt tên)"
                if not k_val:
                    messagebox.showerror("Lỗi", "Vui lòng nhập API Key!", parent=add_win)
                    return

                # Nếu chưa kiểm tra → tự động check trước khi lưu
                if not _check_result["done"]:
                    _check_result["done"] = False
                    status_var.set("Đang tự động kiểm tra trước khi lưu...")
                    lbl_status.config(fg="blue")
                    btn_save.config(state="disabled", text="Đang kiểm tra...")
                    add_win.update_idletasks()
                    def after_check():
                        btn_save.config(state="normal", text="Lưu")
                        _do_save_inner(k_val, e_val)
                    threading.Thread(target=run_check_inner, args=(k_val, after_check), daemon=True).start()
                    return
                _do_save_inner(k_val, e_val)

            def _do_save_inner(k_val, e_val):
                cur_status = _check_result.get("status", "active")
                status_mapped = "active"
                reset_time = 0
                next_check_time = 0

                if cur_status == "exhausted":
                    status_mapped = "exhausted"
                    reset_time = int(time.time()) + 86400
                    next_check_time = int(time.time()) + 10800
                elif cur_status == "invalid":
                    status_mapped = "invalid"

                gemini_settings = self.settings.get("gemini", {})
                if "api_keys" not in gemini_settings:
                    gemini_settings["api_keys"] = []

                for k_obj in gemini_settings["api_keys"]:
                    if k_obj.get("key") == k_val:
                        messagebox.showerror("Lỗi", "API Key này đã tồn tại trong danh sách!", parent=add_win)
                        return

                error_msg = _check_result.get("errmsg", "") if status_mapped == "invalid" else ""

                gemini_settings["api_keys"].append({
                    "error_msg": error_msg,
                    "key": k_val,
                    "email": e_val,
                    "project_id": _check_result.get("project_id", ""),
                    "status": status_mapped,
                    "reset_time": reset_time,
                    "next_check_time": next_check_time,
                    "last_check_time": int(time.time())
                })

                from settings import update_gemini_settings
                update_gemini_settings(api_keys=gemini_settings["api_keys"])
                self.settings = load_settings()
                refresh_list()
                add_win.destroy()

            f_btns = Frame(add_win)
            f_btns.pack(fill="x", padx=20, pady=5)
            Button(f_btns, text="🔍 Kiểm tra trạng thái", command=check_new_key, bg="#f39c12", fg="white", width=18).pack(side="left", padx=5)
            btn_save = Button(f_btns, text="Lưu", command=do_save, bg="#27ae60", fg="white", width=8)
            btn_save.pack(side="left", padx=5)
            Button(f_btns, text="Hủy", command=add_win.destroy, bg="#e74c3c", fg="white", width=8).pack(side="right", padx=5)

        def del_key():
            selected = tree.selection()
            if not selected: return
            if not messagebox.askyesno("Xác nhận", "Xóa Key này?", parent=top): return
            idx = int(selected[0])
            gemini_settings = self.settings.get("gemini", {})
            keys = gemini_settings.get("api_keys", [])
            if 0 <= idx < len(keys):
                keys.pop(idx)
                update_gemini_settings(api_keys=keys)
                self.settings = load_settings()
                refresh_list()

        def check_all_keys():
            gemini_settings = self.settings.get("gemini", {})
            keys = gemini_settings.get("api_keys", [])
            if not keys: return

            btn_check.config(state="disabled", text="Đang kiểm tra...")
            top.update_idletasks()

            def run_checks():
                for key_obj in keys:
                    raw_key = key_obj.get("key")
                    if not raw_key: continue
                    api_key = decode_key(raw_key)
                    try:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
                        headers = {'Content-Type': 'application/json'}
                        payload = {"contents": [{"parts": [{"text": "Hello"}]}]}
                        resp = requests.post(url, headers=headers, json=payload, timeout=10)
                        key_obj["last_check_time"] = int(time.time())

                        if resp.status_code == 200:
                            key_obj["status"] = "active"
                            key_obj["reset_time"] = 0
                            key_obj["next_check_time"] = 0
                        else:
                            rj = resp.json()
                            msg = rj.get("error", {}).get("message", "")
                            proj = extract_project_id(rj)
                            if proj:
                                key_obj["project_id"] = proj
                            if "Quota" in msg or "exhausted" in msg.lower():
                                key_obj["status"] = "exhausted"
                                key_obj["reset_time"] = int(time.time()) + 86400
                                key_obj["next_check_time"] = int(time.time()) + 10800
                                key_obj["error_msg"] = ""
                            else:
                                key_obj["status"] = "invalid"
                                key_obj["error_msg"] = msg[:35]
                    except Exception as e:
                        key_obj["status"] = "invalid"
                        key_obj["error_msg"] = str(e)[:35]

                top.after(0, update_ui_after_check, keys)

            def update_ui_after_check(keys):
                update_gemini_settings(api_keys=keys)
                self.settings = load_settings()
                refresh_list()
                btn_check.config(state="normal", text="Kiểm tra tất cả")
                messagebox.showinfo("Hoàn tất", "Đã kiểm tra xong toàn bộ API Keys!", parent=top)

            threading.Thread(target=run_checks, daemon=True).start()

        def auto_adjust():
            """Check tất cả key, lấy project ID từ error, tô đỏ key trùng project."""
            gemini_settings = self.settings.get("gemini", {})
            keys = gemini_settings.get("api_keys", [])
            if not keys: return

            btn_auto.config(state="disabled", text="Đang điều chỉnh...")
            top.update_idletasks()

            def run_adjust():
                for key_obj in keys:
                    raw_key = key_obj.get("key")
                    if not raw_key: continue
                    api_key = decode_key(raw_key)
                    try:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
                        headers = {'Content-Type': 'application/json'}
                        payload = {"contents": [{"parts": [{"text": "Hello"}]}]}
                        resp = requests.post(url, headers=headers, json=payload, timeout=10)
                        key_obj["last_check_time"] = int(time.time())

                        if resp.status_code == 200:
                            key_obj["status"] = "active"
                            key_obj["reset_time"] = 0
                        else:
                            rj = resp.json()
                            msg = rj.get("error", {}).get("message", "")
                            proj = extract_project_id(rj)
                            if proj:
                                key_obj["project_id"] = proj
                            if "Quota" in msg or "exhausted" in msg.lower():
                                key_obj["status"] = "exhausted"
                                key_obj["reset_time"] = int(time.time()) + 86400
                                key_obj["next_check_time"] = int(time.time()) + 10800
                            else:
                                key_obj["status"] = "invalid"
                                key_obj["error_msg"] = msg[:35]
                    except Exception as e:
                        key_obj["status"] = "invalid"
                        key_obj["error_msg"] = str(e)[:35]

                # Tìm project ID trùng
                project_counts = {}
                for k in keys:
                    pid = k.get("project_id", "")
                    if pid:
                        project_counts[pid] = project_counts.get(pid, 0) + 1
                dup_count = sum(1 for cnt in project_counts.values() if cnt > 1)

                top.after(0, done_adjust, keys, dup_count)

            def done_adjust(keys, dup_count):
                update_gemini_settings(api_keys=keys)
                self.settings = load_settings()
                refresh_list()
                btn_auto.config(state="normal", text="🔄 Tự động điều chỉnh")
                active_c = sum(1 for k in keys if k.get("status") == "active")
                exhaust_c = sum(1 for k in keys if k.get("status") == "exhausted")
                msg = f"✅ Hoàn tất!\n• {active_c} key Active\n• {exhaust_c} key Hết Quota"
                if dup_count > 0:
                    msg += f"\n• ⚠ {dup_count} Project ID bị TRÙNG — đã tô đỏ trong danh sách, bạn hãy tự xóa bớt."
                messagebox.showinfo("Tự động điều chỉnh xong", msg, parent=top)

            threading.Thread(target=run_adjust, daemon=True).start()

        def set_active():
            selected = tree.selection()
            if not selected: return
            idx = int(selected[0])
            gemini_settings = self.settings.get("gemini", {})
            keys = gemini_settings.get("api_keys", [])
            keys[idx]["status"] = "active"
            keys[idx]["reset_time"] = 0
            keys[idx]["next_check_time"] = 0
            update_gemini_settings(api_keys=keys)
            self.settings = load_settings()
            refresh_list()

        btn_frame = Frame(top)
        btn_frame.pack(fill="x", padx=10, pady=10, side="bottom")
        Button(btn_frame, text="Thêm Key Mới", command=add_key, bg="#27ae60", fg="white").pack(side="left", padx=5)
        btn_check = Button(btn_frame, text="Kiểm tra tất cả", command=check_all_keys, bg="#f39c12", fg="white")
        btn_check.pack(side="left", padx=5)
        btn_auto = Button(btn_frame, text="🔄 Tự động điều chỉnh", command=auto_adjust, bg="#8e44ad", fg="white")
        btn_auto.pack(side="left", padx=5)
        Button(btn_frame, text="Đặt Active", command=set_active, bg="#3498db", fg="white").pack(side="left", padx=5)
        Button(btn_frame, text="Xóa Key", command=del_key, bg="#e74c3c", fg="white").pack(side="right", padx=5)


        refresh_list()

    def expand_roadmap_handler(self):
        roadmap_path = self.ai_roadmap_var.get()
        doc_dir = self.ai_doc_var.get()
        if not roadmap_path or not doc_dir:
            messagebox.showerror("Lỗi", "Vui lòng chọn File Roadmap và Thư mục Docs trước!")
            return
        try:
            ppd = int(self.ai_pages_per_day_var.get())
            if ppd < 1: ppd = 5
        except ValueError:
            ppd = 10

        # Dùng custom path nếu user đã chọn, ngược lại dùng mặc định cạnh file gốc
        custom_out = self.ai_expanded_out_var.get().strip()
        if custom_out:
            out_md = custom_out if custom_out.endswith('.md') else os.path.join(custom_out, "roadmap_expanded.md")
        else:
            base_dir = os.path.dirname(roadmap_path)
            out_md = os.path.join(base_dir, "roadmap_expanded.md")

        self.log_ai(f"\n📋 Bắt đầu tạo roadmap mở rộng ({ppd} trang/Day)...")

        def run():
            try:
                import importlib, roadmap_expander
                importlib.reload(roadmap_expander)
                ok = roadmap_expander.expand_roadmap(
                    roadmap_path, doc_dir, out_md,
                    pages_per_day=ppd, log_callback=self.log_ai
                )
                if ok:
                    self.log_ai(f"\n✅ Đã tạo: {out_md}")
                    # Tự động cập nhật trường Roadmap sang file mới
                    def _switch():
                        self.ai_roadmap_var.set(out_md)
                        # Lưu settings luôn
                        update_gemini_settings(
                            last_roadmap=out_md,
                            last_doc_dir=self.ai_doc_var.get(),
                            last_out_dir=self.ai_out_var.get()
                        )
                        self.settings = load_settings()
                        self.log_ai("   ✔ Đã tự động đặt roadmap_expanded.md làm nguồn dữ liệu.")
                        self.log_ai("   ↦ Nhấn '▶ Bắt đầu Sinh Tự Động' để AI xử lý toàn bộ!")
                        # Hỏi có muốn chạy ngay
                        if messagebox.askyesno(
                            "Bắt đầu AI ngay?",
                            f"Roadmap mở rộng đã sẵn sàng ({out_md}).\n\nBắt đầu chạy AI ngay bây giờ không?"
                        ):
                            self.start_ai_worker()
                    self.root.after(0, _switch)
            except Exception as e:
                self.log_ai(f"❌ Lỗi tạo roadmap: {e}")
        threading.Thread(target=run, daemon=True).start()

    def ai_select_roadmap(self):
        fp = filedialog.askopenfilename(title="Chọn file Roadmap", filetypes=[("Markdown files", "*.md")])
        if fp: self.ai_roadmap_var.set(fp)
        
    def ai_select_doc_dir(self):
        d = filedialog.askdirectory(title="Chọn thư mục chứa tài liệu PDF gốc")
        if d: self.ai_doc_var.set(d)
        
    def ai_select_expanded_out(self):
        fp = filedialog.asksaveasfilename(title="Chọn nơi lưu roadmap mở rộng", defaultextension=".md", filetypes=[("Markdown files", "*.md")])
        if fp: self.ai_expanded_out_var.set(fp)
        
    def ai_select_out_dir(self):
        d = filedialog.askdirectory(title="Chọn thư mục xuất (session.json & html)")
        if d: self.ai_out_var.set(d)
        
    def save_ai_settings(self):
        try:
            max_f = int(self.ai_max_followup_var.get())
        except ValueError:
            max_f = 3
            
        update_gemini_settings(
            last_roadmap=self.ai_roadmap_var.get(),
            last_doc_dir=self.ai_doc_var.get(),
            last_out_dir=self.ai_out_var.get(),
            enable_followup=bool(self.ai_enable_followup_var.get()),
            max_followup=max_f,
            followup_mode=self.ai_followup_mode_var.get()
        )
        self.settings = load_settings()
        messagebox.showinfo("Thành công", "Đã lưu cấu hình Auto AI!")
        
    def log_ai(self, msg):
        def _log():
            self.ai_log.config(state='normal')
            self.ai_log.insert(END, msg + "\n")
            self.ai_log.see(END)
            self.ai_log.config(state='disabled')
        self.root.after(0, _log)
        
    def start_ai_worker(self):
        gemini_settings = self.settings.get("gemini", {})
        api_keys = gemini_settings.get("api_keys", [])
        
        roadmap_path = self.ai_roadmap_var.get()
        doc_dir = self.ai_doc_var.get()
        out_dir = self.ai_out_var.get()
        
        if not api_keys or not roadmap_path or not doc_dir or not out_dir:
            messagebox.showerror("Lỗi", "Vui lòng thêm ít nhất 1 API Key, chọn File Roadmap, Thư mục Docs, và Thư mục Xuất!")
            return
            
        self.btn_ai_start.config(state="disabled", text="⏳ Đang xử lý...")
        force = bool(self.ai_force_restart_var.get())
        
        try:
            start_day = int(self.ai_start_day_var.get().strip())
        except ValueError:
            start_day = 0
            
        enable_followup = bool(self.ai_enable_followup_var.get())
        if self.ai_followup_mode_var.get() == "unlimited":
            max_followup = 999
        else:
            try:
                max_followup = int(self.ai_max_followup_var.get())
            except ValueError:
                max_followup = 3
        
        def update_keys_cb(new_keys):
            from settings import update_gemini_settings
            update_gemini_settings(api_keys=new_keys)
            self.settings = load_settings()
            self.root.after(0, self.update_keys_label)
            
        def run():
            try:
                import importlib, auto_ai_worker
                importlib.reload(auto_ai_worker)
                auto_ai_worker.run_auto_ai(
                    api_keys, roadmap_path, doc_dir, out_dir, self.log_ai, 
                    force=force, update_keys_cb=update_keys_cb,
                    enable_followup=enable_followup, max_followup=max_followup, start_day=start_day
                )
                self.log_ai("🎉 Hoàn thành toàn bộ tiến trình!")
            except Exception as e:
                self.log_ai(f"❌ LỖI NGHIÊM TRỌNG: {str(e)}")
            finally:
                def _enable():
                    self.btn_ai_start.config(state="normal", text="▶ Bắt đầu Sinh Tự Động")
                self.root.after(0, _enable)
                
        threading.Thread(target=run, daemon=True).start()

    # --- TAB 1: XUẤT WORD ---
    def setup_tab_word(self):
        Label(self.tab_word, text="Chuyển đổi dữ liệu JSON thành Word", font=("Arial", 14, "bold")).pack(pady=20)
        btn = Button(self.tab_word, text="Chọn file JSON & Tạo Word", bg="#0078d4", fg="white", font=("Arial", 12), command=self.json_to_word, padx=20, pady=10)
        btn.pack(pady=10)
        Label(self.tab_word, text="(Hỗ trợ giữ nguyên định dạng bảng biểu, in đậm của Copilot)", fg="gray").pack(pady=10)

    def json_to_word(self):
        if not win32com:
            messagebox.showerror("Lỗi", "Chưa cài đặt thư viện pywin32. Hãy chạy lệnh: python -m pip install --user pywin32==306")
            return

        json_path = filedialog.askopenfilename(
            title="Chọn file JSON tải từ Add-on",
            filetypes=[("JSON files", "*.json")]
        )
        
        if not json_path:
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể đọc file JSON:\n{e}")
            return

        if not isinstance(data, list) or len(data) == 0:
            messagebox.showerror("Lỗi", "Dữ liệu JSON trống hoặc không đúng định dạng.")
            return

        base_dir = os.path.dirname(os.path.abspath(__file__))
        temp_dir = os.path.join(base_dir, "temp_htmls")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        print("Đang khởi động MS Word...")
        try:
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            word.DisplayAlerts = False
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể khởi động MS Word:\n{e}")
            return

        output_docx = os.path.join(base_dir, f"KhoaHoc_Copilot_{int(time.time())}.docx")

        try:
            doc = word.Documents.Add()
            doc.SaveAs(output_docx)
            
            for idx, item in enumerate(data):
                day_title = item.get("day", f"Day {idx+1}")
                html_content = item.get("html", "")
                
                temp_html_path = os.path.join(temp_dir, f"temp_{idx}.html")
                full_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{day_title}</title>
</head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; padding: 20px;">
<h1 style="color: #0078d4; text-align: center; border-bottom: 2px solid #0078d4; padding-bottom: 10px;">{day_title}</h1>
{html_content}
</body>
</html>"""
                with open(temp_html_path, 'w', encoding='utf-8') as f:
                    f.write(full_html)
                
                word.Selection.EndKey(Unit=6) 
                if idx > 0:
                    word.Selection.InsertBreak(Type=7)
                    
                word.Selection.Collapse(Direction=0)
                print(f"Đang gộp: {day_title}...")
                word.Selection.InsertFile(FileName=temp_html_path, ConfirmConversions=False, Link=False, Attachment=False)
                time.sleep(0.5)
                doc.Save()
                
            doc.Close()
            messagebox.showinfo("Thành công", f"Đã xuất file Word thành công tại:\n{output_docx}")
            os.startfile(output_docx)
            
        except Exception as e:
            messagebox.showerror("Lỗi quá trình tạo Word", str(e))
        finally:
            try:
                word.Quit()
            except:
                pass

    # --- TAB 2: GITHUB SYNC ---
    def setup_tab_github(self):
        Label(self.tab_github, text="Cấu hình GitHub", font=("Arial", 12, "bold")).pack(pady=5)
        
        f1 = Frame(self.tab_github)
        f1.pack(fill='x', padx=20, pady=5)
        Label(f1, text="Username:", width=10, anchor='w').pack(side='left')
        self.entry_gh_user = Entry(f1)
        self.entry_gh_user.pack(side='left', fill='x', expand=True)
        self.entry_gh_user.insert(0, self.settings["github"].get("username", ""))
        
        f2 = Frame(self.tab_github)
        f2.pack(fill='x', padx=20, pady=5)
        Label(f2, text="Token:", width=10, anchor='w').pack(side='left')
        self.entry_gh_token = Entry(f2, show="*")
        self.entry_gh_token.pack(side='left', fill='x', expand=True)
        self.entry_gh_token.insert(0, self.settings["github"].get("token", ""))
        
        Button(self.tab_github, text="Lưu Cấu Hình", command=self.save_github_settings).pack(pady=5)
        
        ttk.Separator(self.tab_github, orient='horizontal').pack(fill='x', pady=10)
        
        Label(self.tab_github, text="Upload Thư Mục (HTML)", font=("Arial", 12, "bold")).pack(pady=5)
        
        f3 = Frame(self.tab_github)
        f3.pack(fill='x', padx=20, pady=5)
        self.gh_folder_var = StringVar()
        Entry(f3, textvariable=self.gh_folder_var, state='readonly').pack(side='left', fill='x', expand=True)
        Button(f3, text="Chọn Thư Mục", command=self.select_gh_folder).pack(side='right', padx=5)
        
        f4 = Frame(self.tab_github)
        f4.pack(fill='x', padx=20, pady=5)
        Label(f4, text="Tên Repo:", width=10, anchor='w').pack(side='left')
        self.entry_gh_repo = Entry(f4)
        self.entry_gh_repo.pack(side='left', fill='x', expand=True)
        
        Button(self.tab_github, text="Đẩy lên GitHub", bg="#2ea043", fg="white", font=("Arial", 10, "bold"), command=self.upload_to_github).pack(pady=10)
        
        self.gh_log = Text(self.tab_github, height=8, state='disabled')
        self.gh_log.pack(fill='both', expand=True, padx=20, pady=5)

    def save_github_settings(self):
        user = self.entry_gh_user.get().strip()
        token = self.entry_gh_token.get().strip()
        update_github_settings(username=user, token=token)
        self.settings = load_settings()
        messagebox.showinfo("Thành công", "Đã lưu cài đặt GitHub an toàn!")

    def select_gh_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục tải về từ Addon")
        if folder:
            self.gh_folder_var.set(folder)
            repo_name = os.path.basename(folder).replace(" ", "-")
            self.entry_gh_repo.delete(0, END)
            self.entry_gh_repo.insert(0, repo_name)

    def log_gh(self, msg):
        self.gh_log.config(state='normal')
        self.gh_log.insert(END, msg + "\n")
        self.gh_log.see(END)
        self.gh_log.config(state='disabled')

    def upload_to_github(self):
        user = self.entry_gh_user.get().strip()
        token = self.entry_gh_token.get().strip()
        repo = self.entry_gh_repo.get().strip()
        folder = self.gh_folder_var.get()
        
        if not user or not token:
            messagebox.showerror("Lỗi", "Vui lòng nhập GitHub Username và Token!")
            return
        if not folder or not repo:
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục và nhập tên Repo!")
            return
            
        def run():
            gh = GitHubSync(user, token, repo, self.log_gh)
            self.log_gh("--- Bắt đầu Upload ---")
            gh.upload_folder(folder)
            self.log_gh("--- Kết thúc ---")
            
        threading.Thread(target=run, daemon=True).start()

    # --- TAB 3: BÀI TẬP (INTERACTIVE BUILDER) ---
    def setup_tab_exercise(self):
        editor_settings = self.settings.get("editor", {})
        self.ex_current_dir = editor_settings.get("ex_dir", "")
        self.ex_current_file = editor_settings.get("ex_file", "")
        self.ex_blocks_data = {} # format: { "day_1.html": [{"type": "text", "content": "..."}, ...] }
        self.ex_selected_file = ""
        
        pw = ttk.PanedWindow(self.tab_exercise, orient='horizontal')
        pw.pack(fill='both', expand=True, padx=5, pady=5)
        
        # --- LEFT FRAME ---
        left_frame = Frame(pw, width=200)
        pw.add(left_frame, weight=1)
        
        f_buttons = Frame(left_frame)
        f_buttons.pack(fill='x', pady=5)
        
        Button(f_buttons, text="1. Chọn Thư Mục HTML", command=self.ex_select_dir).pack(fill='x', pady=2)
        Button(f_buttons, text="Mở File .askcpl", command=self.ex_open_askcpl, bg="#f39c12", fg="white").pack(fill='x', pady=2)
        
        self.btn_save_askcpl = Button(f_buttons, text="Lưu lại vào .askcpl", command=self.ex_save_askcpl, bg="#27ae60", fg="white", state="disabled")
        self.btn_save_askcpl.pack(fill='x', pady=2)
        
        Label(f_buttons, text="--- Công cụ ---", fg="gray").pack(pady=2)
        Button(f_buttons, text="Mã hóa Thư mục -> .askcpl", command=self.ex_tool_encrypt).pack(fill='x', pady=2)
        Button(f_buttons, text="Giải mã .askcpl -> Thư mục", command=self.ex_tool_decrypt).pack(fill='x', pady=2)
        
        self.ex_lbl_dir = Label(left_frame, text=self.ex_current_dir if self.ex_current_dir else "Chưa chọn", fg="blue", wraplength=180)
        self.ex_lbl_dir.pack(fill='x')
        
        Label(left_frame, text="Danh sách Ngày:").pack(anchor='w', pady=(10,0))
        
        scroll_l = Scrollbar(left_frame)
        scroll_l.pack(side='right', fill='y')
        self.ex_listbox = Listbox(left_frame, yscrollcommand=scroll_l.set, exportselection=False)
        self.ex_listbox.pack(side='left', fill='both', expand=True)
        scroll_l.config(command=self.ex_listbox.yview)
        self.ex_listbox.bind("<<ListboxSelect>>", self.ex_on_day_select)
        self.ex_listbox.bind("<Double-1>", self.ex_on_day_double_click)
        
        # --- RIGHT FRAME ---
        right_frame = Frame(pw)
        pw.add(right_frame, weight=3)
        
        self.ex_lbl_current = Label(right_frame, text=f"Đang soạn bài tập cho: {self.ex_current_file}" if self.ex_current_file else "Chưa chọn ngày nào", font=("Arial", 12, "bold"))
        self.ex_lbl_current.pack(pady=5)
        
        f_mode = Frame(right_frame)
        f_mode.pack(fill='x', padx=5, pady=2)
        Label(f_mode, text="Chế độ xuất:").pack(side='left')
        self.ex_combo_mode = ttk.Combobox(f_mode, values=["Nhúng trực tiếp (Mặc định)", "Lưu trữ (Thư mục exercise)"], state="readonly", width=30)
        self.ex_combo_mode.current(0)
        self.ex_combo_mode.pack(side='left', padx=5)
        
        # Add Block Frame
        add_frame = ttk.LabelFrame(right_frame, text="Thêm Khối Nội Dung (Block)")
        add_frame.pack(fill='x', padx=5, pady=5)
        
        f_type = Frame(add_frame)
        f_type.pack(fill='x', pady=2)
        Label(f_type, text="Loại:").pack(side='left')
        self.ex_combo_type = ttk.Combobox(f_type, values=["Văn bản", "Mã nguồn (Code)", "File đính kèm"], state="readonly", width=15)
        self.ex_combo_type.current(0)
        self.ex_combo_type.pack(side='left', padx=5)
        self.ex_combo_type.bind("<<ComboboxSelected>>", self.ex_on_type_change)
        
        self.ex_lbl_lang = Label(f_type, text="Ngôn ngữ:")
        self.ex_combo_lang = ttk.Combobox(f_type, values=["python", "javascript", "html", "css", "sql", "java", "cpp", "csharp", "bash", "json"], width=10)
        self.ex_combo_lang.current(0)
        
        self.ex_text_content = Text(add_frame, height=5)
        self.ex_text_content.pack(fill='x', padx=5, pady=2)
        
        self.ex_btn_file = Button(add_frame, text="Chọn File (RAR, ZIP, PY...)", command=self.ex_select_attachment)
        self.ex_lbl_file = Label(add_frame, text="", fg="green")
        
        Button(add_frame, text="➕ Thêm Block Này", command=self.ex_add_block, bg="#0078d4", fg="white").pack(pady=5)
        Button(add_frame, text="🖊 Mở Trình Soạn Nâng Cao (Trình duyệt)", command=self.ex_open_advanced_editor, bg="#f39c12", fg="white", font=("Arial", 10, "bold")).pack(pady=(0, 5))
        
        # Preview Frame
        preview_frame = ttk.LabelFrame(right_frame, text="Các Block Đã Thêm (Preview)")
        preview_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.ex_text_preview = Text(preview_frame, state='disabled', bg="#f0f0f0")
        self.ex_text_preview.pack(fill='both', expand=True, padx=5, pady=5)
        
        bottom_frame = Frame(right_frame)
        bottom_frame.pack(fill='x', pady=5)
        Button(bottom_frame, text="Xóa Block Cuối", command=self.ex_remove_last_block).pack(side='left', padx=5)
        Button(bottom_frame, text="Xóa Tất Cả", command=self.ex_clear_blocks, fg="red").pack(side='left', padx=5)
        Button(bottom_frame, text="🔄 Tải lại", command=lambda: (self.ex_reload_from_json(), self.ex_refresh_preview()),
               bg="#5c2d91", fg="white", font=("Arial", 9)).pack(side='left', padx=5)
        
        Button(bottom_frame, text="Lưu & Nhúng HTML", command=self.ex_save_html, bg="#2ea043", fg="white", font=("Arial", 10, "bold")).pack(side='right', padx=5)
        self.ex_check_complete_var = BooleanVar()
        Checkbutton(bottom_frame, text="Xác nhận hoàn thành", variable=self.ex_check_complete_var, font=("Arial", 10, "bold"), fg="#2ea043").pack(side='right', padx=10)
        
        self.ex_update_ui_state()

        if self.ex_current_dir:
            self.ex_refresh_listbox()
            if self.ex_current_file:
                items = self.ex_listbox.get(0, END)
                for i, item in enumerate(items):
                    if item.endswith(self.ex_current_file):
                        self.ex_listbox.selection_set(i)
                        self.ex_listbox.see(i)
                        self.ex_reload_from_json()
                        self.ex_refresh_preview()
                        break

    def ex_tool_encrypt(self):
        folder = filedialog.askdirectory(title="Chọn thư mục cần mã hóa")
        if not folder: return
        pwd = simpledialog.askstring("Mật khẩu", "Nhập mật khẩu để bảo vệ file:", show='*')
        if not pwd: return
        output_file = filedialog.asksaveasfilename(title="Lưu file mã hóa", defaultextension=".askcpl", filetypes=[("AskCpl Encrypted", "*.askcpl")])
        if not output_file: return
        
        try:
            import crypto_utils
            crypto_utils.encrypt_folder(folder, output_file, pwd)
            messagebox.showinfo("Thành công", f"Đã mã hóa thành công ra file:\n{output_file}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi mã hóa:\n{e}")

    def ex_tool_decrypt(self):
        input_file = filedialog.askopenfilename(title="Chọn file .askcpl", filetypes=[("AskCpl Encrypted", "*.askcpl")])
        if not input_file: return
        pwd = simpledialog.askstring("Mật khẩu", "Nhập mật khẩu để giải mã:", show='*')
        if not pwd: return
        output_folder = filedialog.askdirectory(title="Chọn thư mục để lưu kết quả giải mã")
        if not output_folder: return
        
        try:
            import crypto_utils
            crypto_utils.decrypt_file(input_file, output_folder, pwd)
            messagebox.showinfo("Thành công", f"Đã giải mã thành công ra thư mục:\n{output_folder}")
        except ValueError as ve:
            messagebox.showerror("Lỗi", str(ve))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi giải mã:\n{e}")

    def ex_open_askcpl(self):
        input_file = filedialog.askopenfilename(title="Chọn file .askcpl bài tập", filetypes=[("AskCpl Encrypted", "*.askcpl")])
        if not input_file: return
        pwd = simpledialog.askstring("Mật khẩu", "Nhập mật khẩu để mở bài tập:", show='*')
        if not pwd: return
        
        try:
            import crypto_utils
            import tempfile
            import os
            temp_dir = os.path.join(tempfile.gettempdir(), "askcpl_workspace")
            # dọn dẹp thư mục tạm cũ nếu có
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)
            
            crypto_utils.decrypt_file(input_file, temp_dir, pwd)
            
            self.ex_current_dir = temp_dir
            self.ex_askcpl_source = input_file
            self.ex_askcpl_password = pwd
            self.btn_save_askcpl.config(state="normal")
            
            self.ex_lbl_dir.config(text=f"Đang làm việc trên: {os.path.basename(input_file)}")
            self.settings.setdefault("editor", {})
            self.settings["editor"]["ex_dir"] = temp_dir
            update_editor_settings(ex_dir=temp_dir)
            
            json_path = os.path.join(self.ex_current_dir, "exercises_data.json")
            if os.path.exists(json_path):
                try:
                    import json
                    with open(json_path, "r", encoding="utf-8") as f:
                        self.ex_blocks_data = json.load(f)
                except Exception:
                    self.ex_blocks_data = {}
            else:
                self.ex_blocks_data = {}
                
            self.ex_refresh_listbox()
            import threading
            threading.Thread(target=self.ex_scan_archival_to_json, daemon=True).start()
            messagebox.showinfo("Thành công", "Đã mở file bài tập thành công. Nhớ bấm 'Lưu lại vào .askcpl' sau khi làm xong!")
        except ValueError as ve:
            messagebox.showerror("Lỗi", str(ve))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi mở file:\n{e}")

    def ex_save_askcpl(self):
        if not hasattr(self, 'ex_askcpl_source') or not self.ex_askcpl_source:
            messagebox.showwarning("Cảnh báo", "Bạn chưa mở file .askcpl nào.")
            return
            
        try:
            import crypto_utils
            crypto_utils.encrypt_folder(self.ex_current_dir, self.ex_askcpl_source, self.ex_askcpl_password)
            messagebox.showinfo("Thành công", f"Đã lưu các thay đổi lại vào file:\n{self.ex_askcpl_source}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi lưu file:\n{e}")

    def ex_select_dir(self):
        folder = filedialog.askdirectory(title="Chọn thư mục chứa các file day_x.html")
        if folder:
            self.ex_current_dir = folder
            self.ex_askcpl_source = ""
            self.ex_askcpl_password = ""
            if hasattr(self, 'btn_save_askcpl'):
                self.btn_save_askcpl.config(state="disabled")
                
            self.ex_lbl_dir.config(text=folder)
            update_editor_settings(ex_dir=folder)
            
            # Load exercises_data.json if exists
            json_path = os.path.join(self.ex_current_dir, "exercises_data.json")
            if os.path.exists(json_path):
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        self.ex_blocks_data = json.load(f)
                except Exception:
                    self.ex_blocks_data = {}
            else:
                self.ex_blocks_data = {}
                
            self.ex_refresh_listbox()
            # Chạy scan trong background thread để không block UI
            import threading
            threading.Thread(target=self.ex_scan_archival_to_json, daemon=True).start()

    def ex_scan_archival_to_json(self):
        """Quét thư mục exercise/ và day_X.html để bổ sung vào exercises_data.json.
        Chạy trong background thread — không được gọi trực tiếp UI từ đây."""
        if not self.ex_current_dir:
            return
        changed = False
        # Snapshot để tránh race condition nếu user đổi thư mục trong lúc scan
        current_dir = self.ex_current_dir

        # --- Scan 1: Archival files trong thư mục exercise/ (file nhỏ, đọc nhanh) ---
        exercise_dir = os.path.join(current_dir, "exercise")
        if os.path.exists(exercise_dir):
            for fname in os.listdir(exercise_dir):
                if not fname.endswith(" exercise.html"):
                    continue
                day_base = fname.replace(" exercise.html", "")
                day_key = day_base + ".html"
                if self.ex_blocks_data.get(day_key):
                    continue
                archival_path = os.path.join(exercise_dir, fname)
                try:
                    with open(archival_path, "r", encoding="utf-8") as f:
                        file_content = f.read()
                    html = self._extract_ql_content(file_content)
                    if html:
                        self.ex_blocks_data[day_key] = [{"type": "wysiwyg", "html": html}]
                        changed = True
                except Exception as e:
                    print(f"[Scan] Lỗi đọc {fname}: {e}")

        # --- Scan 2: Direct-embedded trong day_X.html ---
        # Tối ưu: đọc chunk 4KB đầu file để kiểm tra marker trước khi đọc full
        MARKER = "<!-- EXERCISE START -->"
        try:
            for fname in os.listdir(current_dir):
                if not (fname.startswith("day_") and fname.endswith(".html")):
                    continue
                if self.ex_blocks_data.get(fname):
                    continue
                html_path = os.path.join(current_dir, fname)
                try:
                    # Bước 1: Đọc nhanh 4KB đầu file — kiểm tra có exercise không
                    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
                        head = f.read(4096)
                    if MARKER not in head:
                        # Kiểm tra cuối file (marker có thể nằm gần </body>)
                        file_size = os.path.getsize(html_path)
                        if file_size > 8192:
                            with open(html_path, "rb") as fb:
                                fb.seek(max(0, file_size - 4096))
                                tail = fb.read().decode("utf-8", errors="ignore")
                            if MARKER not in tail:
                                continue  # Không có exercise, bỏ qua
                        else:
                            continue
                    # Bước 2: Đọc full file để extract nội dung
                    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
                        file_content = f.read()
                    html = self._extract_ql_content(file_content)
                    if html:
                        self.ex_blocks_data[fname] = [{"type": "wysiwyg", "html": html}]
                        changed = True
                except Exception:
                    pass
        except Exception:
            pass

        if changed:
            json_path = os.path.join(current_dir, "exercises_data.json")
            try:
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(self.ex_blocks_data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            # Cập nhật UI an toàn từ background thread
            if hasattr(self, 'root'):
                self.root.after(0, self.ex_refresh_listbox)
            else:
                self.after(0, self.ex_refresh_listbox)

    def _extract_ql_content(self, content):
        """Trích xuất nội dung bên trong div.ql-editor từ file exercise HTML."""
        start_marker = "<!-- EXERCISE START -->"
        end_marker = "<!-- EXERCISE END -->"
        if start_marker not in content or end_marker not in content:
            return ""
        start_idx = content.find(start_marker) + len(start_marker)
        end_idx = content.find(end_marker)
        ex_html = content[start_idx:end_idx]

        marker = '<div class="ql-editor">'
        if marker not in ex_html:
            # Thử class cũ
            if '<div class="exercise-body ql-editor"' in ex_html:
                body_start = ex_html.find('<div class="exercise-body ql-editor"')
                body_start = ex_html.find('>', body_start) + 1
                body_end = ex_html.rfind('</div>')
                body_end = ex_html.rfind('</div>', 0, body_end)
                return ex_html[body_start:body_end].strip()
            return ""

        body_start = ex_html.find(marker) + len(marker)
        # Depth tracking để tìm đúng </div> đóng tương ứng
        depth = 1
        pos = body_start
        body_end = len(ex_html)
        while pos < len(ex_html):
            next_open = ex_html.find('<div', pos)
            next_close = ex_html.find('</div>', pos)
            if next_close == -1:
                break
            if next_open != -1 and next_open < next_close:
                depth += 1
                pos = next_open + 4
            else:
                depth -= 1
                if depth == 0:
                    body_end = next_close
                    break
                pos = next_close + 6
        return ex_html[body_start:body_end].strip()

    def ex_refresh_listbox(self):
        self.ex_listbox.delete(0, END)
        if not self.ex_current_dir:
            return
            
        try:
            files = [f for f in os.listdir(self.ex_current_dir) if f.startswith("day_") and f.endswith(".html")]
        except FileNotFoundError:
            files = []
        # Sort by day number
        try:
            files.sort(key=lambda x: int(x.split("_")[1].split(".")[0]))
        except:
            files.sort()
            
        for f in files:
            # Check if has blocks
            has_data = len(self.ex_blocks_data.get(f, [])) > 0
            mark = "✅ " if has_data else "❌ "
            self.ex_listbox.insert(END, mark + f)

    def ex_on_day_select(self, event):
        sel = self.ex_listbox.curselection()
        if not sel:
            return
        item = self.ex_listbox.get(sel[0])
        self.ex_current_file = item[2:] # Bỏ 2 ký tự icon
        self.ex_lbl_current.config(text=f"Đang soạn bài tập cho: {self.ex_current_file}")
        update_editor_settings(ex_file=self.ex_current_file)
        # Reload từ JSON để phản ánh thay đổi từ Web Editor
        self.ex_reload_from_json()
        self.ex_refresh_preview()

    def ex_reload_from_json(self):
        """Đọc lại exercises_data.json từ đĩa. Gọi sau khi Web Editor có thể đã cập nhật."""
        if not self.ex_current_dir:
            return
        json_path = os.path.join(self.ex_current_dir, "exercises_data.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    self.ex_blocks_data = json.load(f)
            except Exception:
                pass
        self.ex_refresh_listbox()

    def ex_on_day_double_click(self, event):
        if not self.ex_current_file or not self.ex_current_dir:
            return
        file_path = os.path.join(self.ex_current_dir, self.ex_current_file)
        if os.path.exists(file_path):
            webbrowser.open(f"file://{os.path.abspath(file_path)}")

    def ex_on_type_change(self, event):
        self.ex_update_ui_state()
        
    def ex_update_ui_state(self):
        b_type = self.ex_combo_type.get()
        if b_type == "Văn bản":
            self.ex_lbl_lang.pack_forget()
            self.ex_combo_lang.pack_forget()
            self.ex_btn_file.pack_forget()
            self.ex_lbl_file.pack_forget()
            self.ex_text_content.pack(fill='x', padx=5, pady=2)
        elif b_type == "Mã nguồn (Code)":
            self.ex_lbl_lang.pack(side='left', padx=(10,2))
            self.ex_combo_lang.pack(side='left')
            self.ex_btn_file.pack_forget()
            self.ex_lbl_file.pack_forget()
            self.ex_text_content.pack(fill='x', padx=5, pady=2)
        elif b_type == "File đính kèm":
            self.ex_lbl_lang.pack_forget()
            self.ex_combo_lang.pack_forget()
            self.ex_text_content.pack_forget()
            self.ex_btn_file.pack(pady=5)
            self.ex_lbl_file.pack()

    def ex_select_attachment(self):
        fp = filedialog.askopenfilename()
        if fp:
            self.ex_selected_file = fp
            self.ex_lbl_file.config(text=os.path.basename(fp))

    def ex_add_block(self):
        if not self.ex_current_file:
            messagebox.showwarning("Lỗi", "Vui lòng chọn một Ngày (day_x.html) ở danh sách bên trái trước!")
            return
            
        b_type_str = self.ex_combo_type.get()
        block = {}
        if b_type_str == "Văn bản":
            content = self.ex_text_content.get("1.0", END).strip()
            if not content: return
            block = {"type": "text", "content": content}
            self.ex_text_content.delete("1.0", END)
            
        elif b_type_str == "Mã nguồn (Code)":
            content = self.ex_text_content.get("1.0", END).rstrip() # Giữ khoảng trắng đầu dòng
            if not content: return
            block = {"type": "code", "language": self.ex_combo_lang.get(), "content": content}
            self.ex_text_content.delete("1.0", END)
            
        elif b_type_str == "File đính kèm":
            if not self.ex_selected_file: return
            filename = os.path.basename(self.ex_selected_file)
            block = {"type": "file", "filepath": self.ex_selected_file, "filename": filename}
            self.ex_selected_file = ""
            self.ex_lbl_file.config(text="")
            
        if self.ex_current_file not in self.ex_blocks_data:
            self.ex_blocks_data[self.ex_current_file] = []
            
        self.ex_blocks_data[self.ex_current_file].append(block)
        self.ex_persist_data()
        self.ex_refresh_preview()
        self.ex_refresh_listbox() # Cập nhật icon ✅

    def ex_remove_last_block(self):
        if self.ex_current_file in self.ex_blocks_data and self.ex_blocks_data[self.ex_current_file]:
            block = self.ex_blocks_data[self.ex_current_file].pop()
            if block.get("type") == "file":
                filepath = os.path.join(self.ex_current_dir, "attachments", block.get("filename", ""))
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                    except:
                        pass
            self.ex_persist_data()
            self.ex_refresh_preview()
            self.ex_refresh_listbox()

    def ex_clear_blocks(self):
        if messagebox.askyesno("Xác nhận", "Xóa toàn bộ block và gỡ bài tập khỏi HTML?"):
            # Xóa bài tập khỏi file HTML và index.html
            if self.ex_current_dir and self.ex_current_file:
                target_html = os.path.join(self.ex_current_dir, self.ex_current_file)
                remove_exercise_from_html(target_html, self.ex_current_dir)
                
            blocks = self.ex_blocks_data.get(self.ex_current_file, [])
            for block in blocks:
                if block.get("type") == "file":
                    filepath = os.path.join(self.ex_current_dir, "attachments", block.get("filename", ""))
                    if os.path.exists(filepath):
                        try:
                            os.remove(filepath)
                        except:
                            pass
            self.ex_blocks_data[self.ex_current_file] = []
            self.ex_persist_data()
            self.ex_refresh_preview()
            self.ex_refresh_listbox()

    def ex_refresh_preview(self):
        self.ex_text_preview.config(state='normal')
        self.ex_text_preview.delete("1.0", END)
        
        blocks = self.ex_blocks_data.get(self.ex_current_file, [])
        if not blocks:
            self.ex_text_preview.insert(END, "(Chưa có block nào)")
        else:
            for idx, b in enumerate(blocks):
                self.ex_text_preview.insert(END, f"--- BLOCK {idx+1} [{b['type'].upper()}] ---\n")
                if b['type'] == 'text':
                    self.ex_text_preview.insert(END, b['content'] + "\n\n")
                elif b['type'] == 'code':
                    self.ex_text_preview.insert(END, f"Ngôn ngữ: {b['language']}\n")
                    # Chỉ hiện 3 dòng đầu preview
                    lines = b['content'].split('\n')
                    preview_lines = "\n".join(lines[:3]) + ("\n..." if len(lines) > 3 else "")
                    self.ex_text_preview.insert(END, preview_lines + "\n\n")
                elif b['type'] == 'file':
                    self.ex_text_preview.insert(END, f"File: {b['filename']}\n\n")
                elif b['type'] == 'wysiwyg':
                    # Block được tạo từ Web Editor (Quill)
                    import re as _re
                    plain = _re.sub(r'<[^>]+>', '', b.get('html', ''))
                    plain = plain.strip()
                    preview_lines = "\n".join(plain.splitlines()[:5])
                    if len(plain.splitlines()) > 5:
                        preview_lines += "\n..."
                    self.ex_text_preview.insert(END, "[Nội dung từ Trình Soạn Thảo Nâng Cao]\n")
                    self.ex_text_preview.insert(END, preview_lines + "\n\n")
                    
        self.ex_text_preview.config(state='disabled')

    def ex_persist_data(self):
        # Lưu vào json tạm để không mất
        if self.ex_current_dir:
            json_path = os.path.join(self.ex_current_dir, "exercises_data.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(self.ex_blocks_data, f, ensure_ascii=False, indent=2)

    def ex_save_html(self, silent=False):
        if not self.ex_current_file:
            return
            
        blocks = self.ex_blocks_data.get(self.ex_current_file, [])
        if not blocks:
            messagebox.showinfo("Báo cáo", "Ngày này không có bài tập nào.")
            return
            
        target_html = os.path.join(self.ex_current_dir, self.ex_current_file)
        is_completed = self.ex_check_complete_var.get()
        mode_val = "archival" if self.ex_combo_mode.current() == 1 else "direct"
        
        success, msg = save_exercise_to_html(target_html, blocks, self.ex_current_dir, is_completed, mode=mode_val)
        if success:
            if not silent:
                messagebox.showinfo("Thành công", f"Đã lưu {len(blocks)} khối vào {self.ex_current_file} thành công!")
        else:
            if not silent:
                messagebox.showerror("Lỗi", msg)

    def ex_open_advanced_editor(self):
        if not self.ex_current_file:
            messagebox.showwarning("Lỗi", "Vui lòng chọn một Ngày (day_x.html) ở danh sách bên trái trước!")
            return
        if not self.ex_current_dir:
            return
            
        # TỰ ĐỘNG LƯU BLOCKS NẾU CÓ ĐỂ WEB EDITOR ĐỌC ĐƯỢC
        blocks = getattr(self, 'ex_blocks_data', {}).get(self.ex_current_file, [])
        if blocks:
            self.ex_save_html(silent=True)

        # --- Tự động phát hiện mode đúng từ file thực tế trên đĩa ---
        day_base = os.path.splitext(self.ex_current_file)[0]
        archival_path = os.path.join(self.ex_current_dir, "exercise", f"{day_base} exercise.html")
        direct_path = os.path.join(self.ex_current_dir, self.ex_current_file)

        EXERCISE_MARKER = "<!-- EXERCISE START -->"
        detected_mode = None

        if os.path.exists(archival_path):
            # Archival file tồn tại → bài tập được lưu ở đây
            detected_mode = "archival"
        elif os.path.exists(direct_path):
            # Kiểm tra day_X.html có nhúng exercise không (đọc head+tail để tiết kiệm)
            try:
                with open(direct_path, 'r', encoding='utf-8', errors='ignore') as f:
                    head = f.read(4096)
                has_marker = EXERCISE_MARKER in head
                if not has_marker:
                    fsize = os.path.getsize(direct_path)
                    if fsize > 8192:
                        with open(direct_path, 'rb') as fb:
                            fb.seek(max(0, fsize - 4096))
                            tail = fb.read().decode('utf-8', errors='ignore')
                        has_marker = EXERCISE_MARKER in tail
                if has_marker:
                    detected_mode = "direct"
            except Exception:
                pass

        # Nếu không tìm thấy bài tập nào → dùng mode từ combo box (tạo mới)
        mode_val = detected_mode if detected_mode else (
            "archival" if self.ex_combo_mode.current() == 1 else "direct"
        )
        
        import urllib.parse
        encoded_dir = urllib.parse.quote(self.ex_current_dir)
        encoded_day = urllib.parse.quote(self.ex_current_file)
        
        import time
        v = int(time.time())
        server_settings = self.settings.get("server", {})
        host = server_settings.get("host", "127.0.0.1")
        port = server_settings.get("port", 5678)
        url = f"http://{host}:{port}/editor?day={encoded_day}&target_dir={encoded_dir}&mode={mode_val}&v={v}"
        webbrowser.open(url)

    # --- TAB 4: TẠO NOTE HTML ---
    def setup_tab_note(self):
        editor_settings = self.settings.get("editor", {})
        self.note_current_dir = editor_settings.get("note_dir", "")
        self.note_current_file = editor_settings.get("note_file", "")
        
        pw = ttk.PanedWindow(self.tab_note, orient='horizontal')
        pw.pack(fill='both', expand=True, padx=5, pady=5)
        
        # --- LEFT FRAME ---
        left_frame = Frame(pw, width=250)
        pw.add(left_frame, weight=1)
        
        Button(left_frame, text="📁 Chọn Thư Mục Lưu Note", command=self.note_select_dir, bg="#0078d4", fg="white").pack(fill='x', pady=5)
        self.note_lbl_dir = Label(left_frame, text=self.note_current_dir if self.note_current_dir else "Chưa chọn", fg="blue", wraplength=230)
        self.note_lbl_dir.pack(fill='x')
        
        f_filter = Frame(left_frame)
        f_filter.pack(fill='x', pady=5)
        Label(f_filter, text="Lọc (ẩn) file chứa:").pack(side='left')
        self.note_var_filter = StringVar(value=self.settings.get("editor", {}).get("note_filter", ""))
        Entry(f_filter, textvariable=self.note_var_filter, width=15).pack(side='left', fill='x', expand=True, padx=2)
        Button(f_filter, text="Lưu", command=self.note_save_filter).pack(side='right')
        
        Label(left_frame, text="Danh sách Note (HTML):").pack(anchor='w', pady=(10,0))
        
        scroll_l = Scrollbar(left_frame)
        scroll_l.pack(side='right', fill='y')
        self.note_listbox = Listbox(left_frame, yscrollcommand=scroll_l.set, exportselection=False)
        self.note_listbox.pack(side='left', fill='both', expand=True)
        scroll_l.config(command=self.note_listbox.yview)
        self.note_listbox.bind("<Double-1>", self.note_on_double_click)
        self.note_listbox.bind("<<ListboxSelect>>", self.note_on_select)
        
        # Init listbox
        if self.note_current_dir:
            self.note_refresh_list()
            if self.note_current_file:
                items = self.note_listbox.get(0, END)
                for i, item in enumerate(items):
                    if item == self.note_current_file:
                        self.note_listbox.selection_set(i)
                        self.note_listbox.see(i)
                        break
        
        # --- RIGHT FRAME ---
        right_frame = Frame(pw)
        pw.add(right_frame, weight=3)
        
        Label(right_frame, text="📝 Trình Tạo Note Độc Lập", font=("Arial", 16, "bold"), fg="#333").pack(pady=(10, 5))
        Label(right_frame, text="Tạo và chỉnh sửa các file HTML ghi chú với trình soạn thảo Rich Text (Quill).\nTính năng này hoạt động độc lập, không liên quan đến index hay lộ trình học.", fg="#666", justify="center").pack(pady=(0, 20))
        
        add_frame = ttk.LabelFrame(right_frame, text="Tạo Note Mới")
        add_frame.pack(fill='x', padx=20, pady=10)
        
        f_name = Frame(add_frame)
        f_name.pack(fill='x', padx=10, pady=15)
        Label(f_name, text="Tên Note:").pack(side='left')
        self.entry_note_name = Entry(f_name, width=40)
        self.entry_note_name.pack(side='left', padx=10)
        Label(f_name, text=".html", fg="gray").pack(side='left')
        
        Button(f_name, text="➕ Tạo & Mở Soạn Thảo", command=self.note_create_new, bg="#2ea043", fg="white", font=("Arial", 10, "bold")).pack(side='left', padx=15)
        
        action_frame = ttk.LabelFrame(right_frame, text="Thao Tác File Đã Chọn")
        action_frame.pack(fill='x', padx=20, pady=10)
        
        Button(action_frame, text="🖊 Mở Trình Soạn Nâng Cao", command=self.note_open_editor, bg="#f39c12", fg="white", font=("Arial", 10, "bold")).pack(side='left', padx=10, pady=15)
        Button(action_frame, text="🌐 Xem trên Trình Duyệt", command=self.note_view_browser, bg="#0078d4", fg="white").pack(side='left', padx=10, pady=15)
        Button(action_frame, text="🗑 Xóa", command=self.note_delete, bg="#da3633", fg="white").pack(side='left', padx=10, pady=15)
        Button(action_frame, text="🔄 Làm mới danh sách", command=self.note_refresh_list).pack(side='left', padx=10, pady=15)

    def note_select_dir(self):
        folder = filedialog.askdirectory(title="Chọn thư mục chứa Note")
        if folder:
            self.note_current_dir = folder
            self.note_lbl_dir.config(text=folder)
            update_editor_settings(note_dir=folder)
            self.note_refresh_list()
            
    def note_save_filter(self):
        self.settings.setdefault("editor", {})
        self.settings["editor"]["note_filter"] = self.note_var_filter.get()
        update_editor_settings(note_filter=self.note_var_filter.get())
        self.note_refresh_list()

    def note_refresh_list(self):
        self.note_listbox.delete(0, END)
        if not self.note_current_dir or not os.path.exists(self.note_current_dir): return
        
        filter_str = self.note_var_filter.get().strip().lower()
        exclude_words = [x.strip() for x in filter_str.split(",") if x.strip()]
        
        try:
            files = []
            for f in os.listdir(self.note_current_dir):
                if os.path.isfile(os.path.join(self.note_current_dir, f)):
                    fl = f.lower()
                    if fl.endswith(".html"):
                        if not exclude_words:
                            files.append(f)
                        else:
                            if not any(word in fl for word in exclude_words):
                                files.append(f)
            files.sort()
            for f in files:
                self.note_listbox.insert(END, f)
        except Exception as e:
            pass

    def note_on_select(self, event):
        sel = self.note_listbox.curselection()
        if not sel: return
        filename = self.note_listbox.get(sel[0])
        self.note_current_file = filename
        update_editor_settings(note_file=filename)

    def note_on_double_click(self, event):
        self.note_open_editor()

    def note_create_new(self):
        if not self.note_current_dir:
            messagebox.showwarning("Lỗi", "Vui lòng chọn thư mục lưu Note trước!")
            return
        name = self.entry_note_name.get().strip()
        if not name:
            messagebox.showwarning("Lỗi", "Vui lòng nhập tên Note!")
            return
        
        import re
        name = re.sub(r'[\\\\/*?:"<>|]', "", name)
        if not name.endswith(".html"):
            name += ".html"
            
        file_path = os.path.join(self.note_current_dir, name)
        if not os.path.exists(file_path):
            blank_html = "<!-- EXERCISE START -->\n<div class=\"ql-editor\"></div>\n<!-- EXERCISE END -->"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(blank_html)
                
        self.note_refresh_list()
        self.entry_note_name.delete(0, END)
        self._open_note_in_editor(name)

    def note_open_editor(self):
        sel = self.note_listbox.curselection()
        if not sel:
            messagebox.showwarning("Lỗi", "Vui lòng chọn một Note trong danh sách!")
            return
        filename = self.note_listbox.get(sel[0])
        self._open_note_in_editor(filename)
        
    def _open_note_in_editor(self, filename):
        import urllib.parse
        encoded_dir = urllib.parse.quote(self.note_current_dir)
        encoded_file = urllib.parse.quote(filename)
        
        import time
        v = int(time.time())
        server_settings = self.settings.get("server", {})
        host = server_settings.get("host", "127.0.0.1")
        port = server_settings.get("port", 5678)
        url = f"http://{host}:{port}/editor?day={encoded_file}&target_dir={encoded_dir}&mode=standalone&v={v}"
        import webbrowser
        webbrowser.open(url)

    def note_view_browser(self):
        sel = self.note_listbox.curselection()
        if not sel: return
        filename = self.note_listbox.get(sel[0])
        file_path = os.path.join(self.note_current_dir, filename)
        if os.path.exists(file_path):
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(file_path)}")

    def note_delete(self):
        sel = self.note_listbox.curselection()
        if not sel:
            messagebox.showwarning("Lỗi", "Vui lòng chọn một Note để xóa!")
            return
        filename = self.note_listbox.get(sel[0])
        file_path = os.path.join(self.note_current_dir, filename)
        
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc chắn muốn xóa vĩnh viễn file:\n{filename}\n(Và cả các file đính kèm nếu có)?"):
            try:
                if os.path.exists(file_path):
                    # Parse and delete attachments
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    import re
                    attachments = re.findall(r'attachments/([^"\'\s<>]+)', content)
                    for att in attachments:
                        att_path = os.path.join(self.note_current_dir, "attachments", att)
                        if os.path.exists(att_path):
                            try:
                                os.remove(att_path)
                            except Exception:
                                pass
                    os.remove(file_path)
                self.note_refresh_list()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa file: {e}")



    # --- TAB 4: CONFIG INDEX ---
    def setup_tab_config_index(self):
        self.ci_current_dir = ""
        self.ci_watching = False
        self.ci_known_files = set()

        # Header
        Label(self.tab_config_index, text="⚙️ Config Index — Tái tạo Điều Hướng HTML",
              font=("Arial", 14, "bold")).pack(pady=(15, 5))
        Label(self.tab_config_index,
              text="Chọn thư mục chứa các file day_X.html để inject thanh điều hướng (← →) vào từng trang.",
              fg="gray", wraplength=600).pack(pady=(0, 10))

        # Chọn thư mục
        f1 = Frame(self.tab_config_index)
        f1.pack(fill='x', padx=20, pady=5)
        self.ci_dir_var = StringVar()
        Entry(f1, textvariable=self.ci_dir_var, state='readonly', width=60).pack(side='left', fill='x', expand=True)
        Button(f1, text="Chọn Thư Mục", command=self.ci_select_dir, bg="#0078d4", fg="white").pack(side='right', padx=5)

        # Thống kê
        self.ci_lbl_stats = Label(self.tab_config_index, text="", fg="#0078d4", font=("Arial", 10))
        self.ci_lbl_stats.pack(pady=3)

        # Listbox danh sách file
        lf = ttk.LabelFrame(self.tab_config_index, text="Danh sách file phát hiện")
        lf.pack(fill='both', expand=True, padx=20, pady=5)

        scroll_ci = Scrollbar(lf)
        scroll_ci.pack(side='right', fill='y')
        self.ci_listbox = Listbox(lf, yscrollcommand=scroll_ci.set, font=("Consolas", 9))
        self.ci_listbox.pack(side='left', fill='both', expand=True)
        scroll_ci.config(command=self.ci_listbox.yview)

        # Nút hành động
        btn_frame = Frame(self.tab_config_index)
        btn_frame.pack(fill='x', padx=20, pady=8)
        Button(btn_frame, text="🔄 Tái tạo index.html",
               command=self.ci_rebuild_index, bg="#5c2d91", fg="white",
               font=("Arial", 10, "bold"), padx=10).pack(side='left', padx=5)
        Button(btn_frame, text="🔗 Inject Navigation vào tất cả Day files",
               command=self.ci_inject_nav, bg="#2ea043", fg="white",
               font=("Arial", 10, "bold"), padx=10).pack(side='left', padx=5)
        Button(btn_frame, text="🚀 Tất Cả (Index + Nav)",
               command=self.ci_do_all, bg="#c4a000", fg="white",
               font=("Arial", 10, "bold"), padx=10).pack(side='left', padx=5)

        # Auto-Watch
        watch_frame = Frame(self.tab_config_index)
        watch_frame.pack(fill='x', padx=20, pady=(0, 5))
        self.ci_watch_btn = Button(
            watch_frame,
            text="👁️ Bật Auto-Watch (Tự động inject khi có file mới)",
            command=self.ci_toggle_watch,
            bg="#555", fg="white", font=("Arial", 10, "bold"), padx=10
        )
        self.ci_watch_btn.pack(side='left', padx=5)
        self.ci_watch_lbl = Label(watch_frame, text="● Đang tắt", fg="#999", font=("Arial", 10))
        self.ci_watch_lbl.pack(side='left', padx=8)

        # Log
        log_lf = ttk.LabelFrame(self.tab_config_index, text="Log")
        log_lf.pack(fill='x', padx=20, pady=(0, 10))
        self.ci_log = Text(log_lf, height=8, state='disabled', bg="#1e1e2e", fg="#a0f0a0",
                           font=("Consolas", 9))
        self.ci_log.pack(fill='both', expand=True, padx=5, pady=5)

    def ci_select_dir(self):
        folder = filedialog.askdirectory(title="Chọn thư mục chứa các file day_X.html")
        if not folder:
            return
        self.ci_current_dir = folder
        self.ci_dir_var.set(folder)
        self.ci_refresh_list()

    def ci_refresh_list(self):
        self.ci_listbox.delete(0, END)
        folder = self.ci_current_dir
        if not folder:
            return
        day_files = get_day_files(folder)
        if not day_files:
            self.ci_lbl_stats.config(text="❌ Không tìm thấy file day_X.html nào!", fg="red")
            return

        total = day_files[-1][0]
        found_days = {d for d, _ in day_files}
        missing = [d for d in range(1, total + 1) if d not in found_days]

        self.ci_lbl_stats.config(
            text=f"✅ {len(day_files)} file tìm thấy | Day 1 → Day {total} | Thiếu: {len(missing)} file",
            fg="#2ea043" if not missing else "#c4a000"
        )

        for day_num, fname in day_files:
            self.ci_listbox.insert(END, f"  Day {day_num:>4}  →  {fname}")

        if missing:
            self.ci_listbox.insert(END, "")
            self.ci_listbox.insert(END, f"  ⚠️  File bị thiếu: Day {', '.join(map(str, missing[:15]))}{'...' if len(missing) > 15 else ''}")

    def ci_log_msg(self, msg):
        self.ci_log.config(state='normal')
        self.ci_log.insert(END, msg + "\n")
        self.ci_log.see(END)
        self.ci_log.config(state='disabled')

    def ci_rebuild_index(self):
        if not self.ci_current_dir:
            messagebox.showwarning("Chưa chọn thư mục", "Vui lòng chọn thư mục trước!")
            return
        def run():
            rebuild_index(self.ci_current_dir, self.ci_log_msg)
        threading.Thread(target=run, daemon=True).start()

    def ci_inject_nav(self):
        if not self.ci_current_dir:
            messagebox.showwarning("Chưa chọn thư mục", "Vui lòng chọn thư mục trước!")
            return
        def run():
            self.ci_log_msg("--- Bắt đầu Inject Navigation ---")
            result = inject_all(self.ci_current_dir, self.ci_log_msg)
            self.ci_log_msg(f"--- Hoàn tất: {result['success']} thành công / {result['failed']} thất bại ---")
        threading.Thread(target=run, daemon=True).start()

    def ci_toggle_watch(self):
        if not self.ci_current_dir:
            messagebox.showwarning("Chưa chọn thư mục", "Vui lòng chọn thư mục trước!")
            return
        self.ci_watching = not self.ci_watching
        if self.ci_watching:
            # Init known files
            self.ci_known_files = {f for _, f in get_day_files(self.ci_current_dir)}
            self.ci_watch_btn.config(bg="#c0392b", text="⏹ Tắt Auto-Watch")
            self.ci_watch_lbl.config(text="● Đang theo dõi...", fg="#2ecc71")
            self.ci_log_msg("[Watch] Bat dau theo doi thu muc: " + self.ci_current_dir)
            self.ci_watch_poll()
        else:
            self.ci_watch_btn.config(bg="#555", text="👁️ Bật Auto-Watch (Tự động inject khi có file mới)")
            self.ci_watch_lbl.config(text="● Đang tắt", fg="#999")
            self.ci_log_msg("[Watch] Dung theo doi.")

    def ci_watch_poll(self):
        if not self.ci_watching:
            return
        current_files = {f for _, f in get_day_files(self.ci_current_dir)}
        new_files = current_files - self.ci_known_files
        if new_files:
            self.ci_log_msg(f"[Watch] Phat hien {len(new_files)} file moi: {', '.join(sorted(new_files))}")
            self.ci_known_files = current_files
            def run():
                inject_all(self.ci_current_dir, self.ci_log_msg)
                rebuild_index(self.ci_current_dir, self.ci_log_msg)
                self.ci_refresh_list()
            threading.Thread(target=run, daemon=True).start()
        # Poll lai sau 3 giay
        self.root.after(3000, self.ci_watch_poll)

    def ci_do_all(self):
        if not self.ci_current_dir:
            messagebox.showwarning("Chưa chọn thư mục", "Vui lòng chọn thư mục trước!")
            return
        def run():
            self.ci_log_msg("=== Bat dau: Tai tao Index + Inject Navigation ===")
            rebuild_index(self.ci_current_dir, self.ci_log_msg)
            result = inject_all(self.ci_current_dir, self.ci_log_msg)
            self.ci_log_msg(f"=== Hoan tat! {result['success']} file da duoc cap nhat ===")
        threading.Thread(target=run, daemon=True).start()


if __name__ == "__main__":
    root = Tk()
    app = AskCplApp(root)
    root.mainloop()
