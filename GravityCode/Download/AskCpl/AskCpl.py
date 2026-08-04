import os
import json
import time
import threading
import sys
import subprocess
import tkinter as tk
from tkinter import Tk, filedialog, messagebox, Button, Label, Frame, StringVar, IntVar, Entry, Text, END, Listbox, Scrollbar, BooleanVar, Checkbutton, Radiobutton, simpledialog, Toplevel, Canvas
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
from roadmap_pipeline import (RoadmapValidationError, atomic_write, load_json_response,
                              render_markdown, render_toc, restore_locked_day_identity,
                              validate_plan, validate_revision)
from adaptive_learning import (default_profile, load_profile, profile_questions,
                               record_learner_feedback, save_profile)
from verified_knowledge import coverage_report, empty_pack, load_pack, validate_pack
from knowledge_pack_importer import import_csv_folder
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
        from tkinter import ttk
        self.auto_ai_notebook = ttk.Notebook(self.tab_auto_ai)
        self.auto_ai_notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        self.sub_tab_keys = ttk.Frame(self.auto_ai_notebook)
        self.sub_tab_roadmap_gen = ttk.Frame(self.auto_ai_notebook)
        self.sub_tab_roadmap_run = ttk.Frame(self.auto_ai_notebook)
        
        self.auto_ai_notebook.add(self.sub_tab_keys, text="🔑 Quản lý API Keys")
        self.auto_ai_notebook.add(self.sub_tab_roadmap_gen, text="🧠 Tạo Roadmap")
        self.auto_ai_notebook.add(self.sub_tab_roadmap_run, text="▶️ Tải Roadmap (Auto AI)")
        
        self.setup_api_keys_tab()
        self.setup_roadmap_gen_tab()
        self.setup_roadmap_run_tab()

    def setup_roadmap_gen_tab(self):
        from tkinter import ttk, scrolledtext
        import tkinter as tk
        saved_generator = self.settings.get("gemini", {}).get("roadmap_generator", {})
        
        # Region 1.0: Mode Selection
        f_mode = tk.Frame(self.sub_tab_roadmap_gen)
        f_mode.pack(fill='x', padx=10, pady=5)
        tk.Label(f_mode, text="Chế độ tạo (Mode):", font=("Arial", 10, "bold"), width=15, anchor='w').pack(side='left')
        self.ai_roadmap_gen_mode_var = tk.StringVar(value=saved_generator.get("gen_mode", "learning"))
        tk.Radiobutton(f_mode, text="Giáo trình (Learning Roadmap)", variable=self.ai_roadmap_gen_mode_var, value="learning", font=("Arial", 10)).pack(side='left', padx=10)
        tk.Radiobutton(f_mode, text="Bách khoa (Wiki/Database)", variable=self.ai_roadmap_gen_mode_var, value="wiki", font=("Arial", 10)).pack(side='left', padx=10)
        
        # Region 1.1: Input
        f_input = tk.Frame(self.sub_tab_roadmap_gen)
        f_input.pack(fill='x', padx=10, pady=5)
        tk.Label(f_input, text="Lĩnh vực / Từ khóa:", font=("Arial", 10, "bold"), width=15, anchor='w').pack(side='left')
        self.ai_roadmap_domain_var = tk.StringVar(value=saved_generator.get("domain", ""))
        tk.Entry(f_input, textvariable=self.ai_roadmap_domain_var, font=("Arial", 10)).pack(side='left', fill='x', expand=True, padx=10)
        
        tk.Button(f_input, text="1. Lên Dàn ý Lõi (Core)", bg="#8e44ad", fg="white", font=("Arial", 10, "bold"),
                  command=lambda: self.roadmap_gen_step1()).pack(side='right')

        # Region 1.2: Context
        f_context = tk.Frame(self.sub_tab_roadmap_gen)
        f_context.pack(fill='x', padx=10, pady=5)
        tk.Label(f_context, text="Yêu cầu bổ sung / Tiêu chuẩn:", font=("Arial", 9), width=25, anchor='nw').pack(side='left', anchor='n')
        self.ai_roadmap_context_text = scrolledtext.ScrolledText(f_context, height=3, font=("Arial", 9))
        self.ai_roadmap_context_text.pack(side='left', fill='x', expand=True, padx=10)
        self.ai_roadmap_context_text.insert("1.0", saved_generator.get("context", ""))

        # Region 1.3: Scale (Time & Days)
        f_scale = tk.Frame(self.sub_tab_roadmap_gen)
        f_scale.pack(fill='x', padx=10, pady=5)
        tk.Label(f_scale, text="Thời lượng học/ngày:", width=20, anchor='w').pack(side='left')
        self.ai_roadmap_time_var = tk.StringVar(value=saved_generator.get("time_per_day", "2 tiếng"))
        tk.Entry(f_scale, textvariable=self.ai_roadmap_time_var, width=15).pack(side='left', padx=5)
        
        tk.Label(f_scale, text="Tổng số ngày mong muốn:", width=20, anchor='w').pack(side='left', padx=(10,0))
        self.ai_roadmap_days_var = tk.StringVar(value=saved_generator.get("days", "Auto"))
        cb_days = ttk.Combobox(f_scale, textvariable=self.ai_roadmap_days_var, values=["Auto", "30", "60", "100", "150", "365", "1000", "3000"], width=10)
        cb_days.pack(side='left', padx=5)

        # Region 1.4: Output Requirements
        f_reqs = tk.LabelFrame(self.sub_tab_roadmap_gen, text="Cấu trúc đầu ra bắt buộc của AI", font=("Arial", 9, "bold"))
        f_reqs.pack(fill='x', padx=10, pady=5)
        
        self.ai_req_time_var = tk.IntVar(value=saved_generator.get("req_time", 0))
        self.ai_req_mat_var = tk.IntVar(value=saved_generator.get("req_mat", 0))
        self.ai_req_step_var = tk.IntVar(value=saved_generator.get("req_step", 1))
        self.ai_req_warn_var = tk.IntVar(value=saved_generator.get("req_warn", 1))
        self.ai_req_check_var = tk.IntVar(value=saved_generator.get("req_check", 1))
        self.ai_req_custom_var = tk.StringVar(value=saved_generator.get("req_custom", ""))
        self.ai_req_sim_check_var = tk.IntVar(value=saved_generator.get("req_sim_check", 1))
        self.ai_req_sim_ratio_var = tk.StringVar(value=str(saved_generator.get("req_sim_ratio", "96")))
        
        f_reqs_row1 = tk.Frame(f_reqs)
        f_reqs_row1.pack(fill='x', padx=5, pady=2)
        tk.Checkbutton(f_reqs_row1, text="Phân bổ thời gian", variable=self.ai_req_time_var).pack(side='left')
        tk.Checkbutton(f_reqs_row1, text="Vật liệu chuẩn bị", variable=self.ai_req_mat_var).pack(side='left', padx=10)
        tk.Checkbutton(f_reqs_row1, text="Từng bước thực hiện", variable=self.ai_req_step_var).pack(side='left')
        
        f_reqs_row2 = tk.Frame(f_reqs)
        f_reqs_row2.pack(fill='x', padx=5, pady=2)
        tk.Checkbutton(f_reqs_row2, text="An toàn/Lỗi thường gặp", variable=self.ai_req_warn_var).pack(side='left')
        tk.Checkbutton(f_reqs_row2, text="Checklist hoàn thành", variable=self.ai_req_check_var).pack(side='left', padx=10)
        
        f_reqs_row3 = tk.Frame(f_reqs)
        f_reqs_row3.pack(fill='x', padx=5, pady=2)
        tk.Checkbutton(f_reqs_row3, text="Kiểm tra trùng lặp tiêu đề (%)", variable=self.ai_req_sim_check_var).pack(side='left')
        tk.Entry(f_reqs_row3, textvariable=self.ai_req_sim_ratio_var, width=5).pack(side='left', padx=5)
        
        tk.Label(f_reqs_row3, text="Yêu cầu khác:").pack(side='left', padx=(10, 2))
        tk.Entry(f_reqs_row3, textvariable=self.ai_req_custom_var, width=25).pack(side='left', fill='x', expand=True, padx=(0, 5))

        # Region 1.5: Reference Files
        self.f_refs_container = tk.Frame(self.sub_tab_roadmap_gen)
        self.f_refs_container.pack(fill='x', padx=10, pady=5)
        
        self.ref_file_vars = []
        
        def add_ref_file(default_val=""):
            if len(self.ref_file_vars) >= 5: return
            f_row = tk.Frame(self.f_refs_container)
            f_row.pack(fill='x', pady=2)
            tk.Label(f_row, text=f"File tham khảo {len(self.ref_file_vars)+1}:", width=15, anchor='w').pack(side='left')
            var = tk.StringVar(value=default_val)
            self.ref_file_vars.append(var)
            tk.Entry(f_row, textvariable=var, state='readonly').pack(side='left', fill='x', expand=True, padx=5)
            
            def select_file():
                from tkinter import filedialog
                f = filedialog.askopenfilename(filetypes=[("Tài liệu roadmap", "*.md *.json *.pdf *.txt"), ("All Files", "*.*")])
                if f: var.set(f)
            tk.Button(f_row, text="Chọn", command=select_file).pack(side='left', padx=2)
            
            def remove_file():
                if len(self.ref_file_vars) > 1:
                    self.ref_file_vars.remove(var)
                    f_row.destroy()
                    # Cập nhật lại label
                    for i, child in enumerate(self.f_refs_container.winfo_children()):
                        if i > 0: # Bỏ qua header
                            child.winfo_children()[0]["text"] = f"File tham khảo {i}:"
            tk.Button(f_row, text="[-]", command=remove_file, fg="red").pack(side='left')
            
        f_ref_header = tk.Frame(self.f_refs_container)
        f_ref_header.pack(fill='x')
        tk.Label(f_ref_header, text="Các File Tham Khảo (Max 5):", font=("Arial", 9, "bold")).pack(side='left')
        tk.Button(f_ref_header, text="[+] Thêm File", command=lambda: add_ref_file(), fg="green").pack(side='left', padx=10)
        
        saved_references = saved_generator.get("reference_files", [])
        for reference in saved_references[:5] if isinstance(saved_references, list) else []:
            add_ref_file(reference)
        if not self.ref_file_vars:
            add_ref_file()

        # Region 2: Settings (Save As)
        f_opts = tk.Frame(self.sub_tab_roadmap_gen)
        f_opts.pack(fill='x', padx=10, pady=5)
        tk.Label(f_opts, text="Lưu file tại:").pack(side='left')
        self.ai_roadmap_save_var = tk.StringVar(value=saved_generator.get("save_dir", ""))
        tk.Entry(f_opts, textvariable=self.ai_roadmap_save_var, state='readonly', width=50).pack(side='left', padx=10)
        tk.Button(f_opts, text="Chọn Thư Mục...", command=self.roadmap_gen_select_dir).pack(side='left')
        tk.Button(f_opts, text="Lưu cấu hình tạo roadmap", command=self.save_roadmap_generator_settings).pack(side='left', padx=8)

        # Region 3: Preview Skeleton
        f_preview = tk.Frame(self.sub_tab_roadmap_gen)
        f_preview.pack(fill='both', expand=True, padx=10, pady=5)
        tk.Label(f_preview, text="Dàn ý Kỹ thuật (JSON) - Chứa Profile và Skeleton:", font=("Arial", 10, "bold")).pack(anchor='w')
        
        self.ai_roadmap_skeleton_text = scrolledtext.ScrolledText(f_preview, height=12, bg="#fffde7", font=("Consolas", 10))
        self.ai_roadmap_skeleton_text.pack(fill='both', expand=True, pady=5)

        # Region 3.5: Step 2 - Nâng cấp Khung
        f_step2 = tk.Frame(self.sub_tab_roadmap_gen)
        f_step2.pack(fill='x', padx=10, pady=5)
        tk.Button(f_step2, text="2. Phản biện & Mở rộng Khung (5 Passes)", bg="#3498db", fg="white", font=("Arial", 10, "bold"),
                  command=lambda: self.roadmap_gen_step2()).pack(side='right')

        # Region 4: Expansion (Step 3)
        f_expand = tk.Frame(self.sub_tab_roadmap_gen)
        f_expand.pack(fill='x', padx=10, pady=10)
        
        self.ai_roadmap_expand_mode = tk.StringVar(value=saved_generator.get("expand_mode", "llm"))
        tk.Radiobutton(f_expand, text="Chẻ bằng Template (Nhanh)", variable=self.ai_roadmap_expand_mode, value="template", font=("Arial", 9, "bold"), fg="#27ae60").pack(side='left')
        tk.Radiobutton(f_expand, text="Chẻ bằng LLM 6-Pass (Master)", variable=self.ai_roadmap_expand_mode, value="llm").pack(side='left', padx=10)

        tk.Button(f_expand, text="3. Sinh Chi Tiết Master & Kiểm định", bg="#e67e22", fg="white", font=("Arial", 10, "bold"),
                  command=lambda: self.roadmap_gen_step3()).pack(side='right')

        # Region 5: Log
        f_log = tk.Frame(self.sub_tab_roadmap_gen)
        f_log.pack(fill='x', padx=10, pady=5)
        tk.Label(f_log, text="Tiến trình chạy:", font=("Arial", 10, "bold")).pack(anchor='w')
        self.ai_roadmap_log_text = scrolledtext.ScrolledText(f_log, height=5, bg="#f4f4f4", font=("Consolas", 9), state='disabled')
        self.ai_roadmap_log_text.pack(fill='x', expand=True)

    def roadmap_gen_select_dir(self):
        from tkinter import filedialog
        d = filedialog.askdirectory()
        if d:
            self.ai_roadmap_save_var.set(d)

    def roadmap_gen_log(self, msg):
        import tkinter as tk
        self.ai_roadmap_log_text.config(state='normal')
        self.ai_roadmap_log_text.insert(tk.END, msg + "\n")
        self.ai_roadmap_log_text.see(tk.END)
        self.ai_roadmap_log_text.config(state='disabled')
        self.root.update_idletasks()

    def roadmap_gen_step1(self):
        import threading
        threading.Thread(target=self._roadmap_gen_step1_thread, daemon=True).start()

    def roadmap_gen_step2(self):
        import threading
        threading.Thread(target=self._roadmap_gen_step2_thread, daemon=True).start()
        
    def _get_active_api_key(self, exclude_keys=None):
        exclude_keys = exclude_keys or set()
        # Always read the persisted state: the API-key manager and roadmap
        # worker can update a key's quota status while a long generation runs.
        gemini_settings = load_settings().get("gemini", {})
        keys = gemini_settings.get("api_keys", [])
        active_keys = [k for k in keys if k.get("status") == "active"]
        
        for ak in active_keys:
            raw_key = ak.get("key", "")
            if raw_key.startswith("ENC:"):
                import base64
                try:
                    dec = base64.b64decode(raw_key[4:]).decode("utf-8")
                except:
                    dec = raw_key
            else:
                dec = raw_key
                
            if dec not in exclude_keys:
                return dec
        return None

    def _set_roadmap_key_status(self, key_value, status, error_msg=""):
        """Persist status in the same model used by the API-key manager."""
        now = int(time.time())
        state = load_settings()
        keys = state.get("gemini", {}).get("api_keys", [])
        changed = False
        for item in keys:
            raw = item.get("key", "")
            if raw.startswith("ENC:"):
                import base64
                try:
                    raw = base64.b64decode(raw[4:]).decode("utf-8")
                except Exception:
                    pass
            if raw != key_value:
                continue
            item["status"] = status
            item["last_check_time"] = now
            item["error_msg"] = error_msg[:120]
            if status == "exhausted":
                item["reset_time"] = now + 86400
                item["next_check_time"] = now + 10800
            elif status == "invalid":
                item["reset_time"] = 0
                item["next_check_time"] = 0
            changed = True
            break
        if changed:
            update_gemini_settings(api_keys=keys)
            self.settings = load_settings()
            try:
                self.root.after(0, self.update_keys_label)
            except Exception:
                pass

    def _clean_json(self, json_str):
        import re
        s = json_str.strip().replace("```json\n", "").replace("```json", "").replace("```", "").strip()
        # Fix missing commas between objects/arrays
        s = re.sub(r'\}\s*\{', '}, {', s)
        s = re.sub(r'\]\s*\[', '], [', s)
        s = re.sub(r'\}\s*\[', '}, [', s)
        s = re.sub(r'\]\s*\{', '], {', s)
        # Fix trailing commas
        s = re.sub(r',\s*\]', ']', s)
        s = re.sub(r',\s*\}', '}', s)
        return s

    def _roadmap_gen_step1_thread(self):
        import tkinter as tk
        import requests, json, os, time

        domain = self.ai_roadmap_domain_var.get().strip()
        ref_files = [v.get().strip() for v in self.ref_file_vars if v.get().strip()]

        if not domain:
            self.roadmap_gen_log("[LỖI] Cần nhập Lĩnh vực / Từ khóa!")
            return

        api_key = self._get_active_api_key()
        if not api_key:
            self.roadmap_gen_log("[LỖI] Không tìm thấy API Key nào đang hoạt động!")
            return

        time_per_day = self.ai_roadmap_time_var.get().strip() or "2 tiếng"
        days_setting = self.ai_roadmap_days_var.get().strip()
        context_text = self.ai_roadmap_context_text.get(1.0, tk.END).strip()

        self.roadmap_gen_log(f"[BƯỚC 1] Bắt đầu phân tích khung cho: '{domain}' ({days_setting} ngày, {time_per_day}/ngày)...")

        # --- Đọc tất cả file tham khảo ---
        ref_content_block = ""
        for i, rf in enumerate(ref_files):
            if os.path.exists(rf):
                try:
                    with open(rf, 'r', encoding='utf-8') as f:
                        rc = f.read()
                    ref_content_block += f"\n--- File tham khảo {i+1}: {os.path.basename(rf)} ---\n{rc[:4000]}\n"
                    self.roadmap_gen_log(f"[INFO] Đã nạp file tham khảo {i+1}: {os.path.basename(rf)}")
                except Exception as e:
                    self.roadmap_gen_log(f"[CẢNH BÁO] Lỗi đọc file {os.path.basename(rf)}: {e}")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}

        # ===================================================
        # NHỊP 1: Sinh Mục lục Giai đoạn (Phase Milestones)
        # ===================================================
        days_instruction = (
            f"Với thời lượng học {time_per_day} mỗi ngày, tự phán đoán số ngày cần thiết để nắm vững toàn bộ lĩnh vực (không giới hạn, tối đa 150 ngày)."
            if days_setting == "Auto"
            else f"Tổng cộng {days_setting} ngày."
        )

        prompt_phase = f"""Bạn là chuyên gia xây dựng giáo trình. Lĩnh vực: {domain}.
Thời lượng học mỗi ngày: {time_per_day}. {days_instruction}
{'Yêu cầu bổ sung: ' + context_text if context_text else ''}
{ref_content_block}

Nhiệm vụ: Chia toàn bộ lộ trình học thành các Giai đoạn (Phase). Mỗi Phase có từ 5-30 ngày.
Yêu cầu trả về JSON theo định dạng sau (CHỈ JSON, không có văn bản thừa):
{{
  "domain_profile": {{
    "persona": "Vai trò chuyên gia",
    "core_books": "Sách/tài liệu nền tảng bắt buộc",
    "supreme_commands": "3 nguyên tắc bất di bất dịch. Bắt buộc có lệnh: KHÔNG TƯƠNG TÁC.",
    "total_days": 60
  }},
  "phases": [
    {{"phase_id": 1, "phase_name": "Tên giai đoạn", "from_day": 1, "to_day": 15, "description": "Mục tiêu phase"}}
  ]
}}"""

        self.roadmap_gen_log("[NHỊP 1] Đang sinh Mục lục Giai đoạn...")
        try:
            resp = requests.post(url, headers=headers,
                json={"contents": [{"parts": [{"text": prompt_phase}]}],
                      "generationConfig": {"temperature": 0.3, "response_mime_type": "application/json"}},
                timeout=45)
            resp.raise_for_status()
            phase_out = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            
            # Clean JSON wrapping and syntax errors
            clean_phase_out = self._clean_json(phase_out)
            phase_data = json.loads(clean_phase_out)
        except Exception as e:
            self.roadmap_gen_log(f"[LỖI NHỊP 1] {e}")
            return

        domain_profile = phase_data.get("domain_profile", {})
        phases = phase_data.get("phases", [])
        total_days_planned = domain_profile.get("total_days", sum(p.get('to_day', 0) - p.get('from_day', 0) + 1 for p in phases))
        self.roadmap_gen_log(f"[NHỊP 1 OK] Đã lên được {len(phases)} Giai đoạn - Tổng dự kiến {total_days_planned} ngày.")

        # ===================================================
        # NHỊP 2: Loop sinh chi tiết từng Giai đoạn
        # ===================================================
        all_skeleton = []
        persona = domain_profile.get('persona', 'chuyên gia')
        core_books = domain_profile.get('core_books', '')
        supreme_commands = domain_profile.get('supreme_commands', 'KHÔNG TƯƠNG TÁC')

        for ph in phases:
            # Làm mới API key trước mỗi phase phòng quota
            api_key = self._get_active_api_key() or api_key
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"

            ph_name = ph.get('phase_name', '')
            from_day = ph.get('from_day', 0)
            to_day = ph.get('to_day', 0)
            ph_desc = ph.get('description', '')
            self.roadmap_gen_log(f"[NHỊP 2] Đang sinh chi tiết Phase '{ph_name}' (Ngày {from_day} → {to_day})...")

            prompt_days = f"""Bạn là {persona}. Lĩnh vực: {domain}.
Giai đoạn: {ph_name} (Mục tiêu: {ph_desc}).
Sách nền tảng: {core_books}.
(⚠️ LỆNH TỐI THƯỢNG: {supreme_commands} | KHÔNG TƯƠNG TÁC)

Nhiệm vụ: Sinh danh sách các bài học cốt lõi từ Ngày {from_day} đến Ngày {to_day} cho Giai đoạn này. KHÔNG CẦN CHI TIẾT SÂU, chỉ cần khung cơ bản.
Yêu cầu trả về JSON MẢNG theo định dạng (CHỈ JSON, không văn bản thừa):
[
  {{"day": {from_day}, "phase": "{ph_name}", "topic": "Tên bài học", "details": ["Từ khóa chính 1", "Từ khóa chính 2"]}}
]
Bắt buộc có đủ từ Ngày {from_day} đến Ngày {to_day}."""

            try:
                resp2 = requests.post(url, headers=headers,
                    json={"contents": [{"parts": [{"text": prompt_days}]}],
                          "generationConfig": {"temperature": 0.35, "response_mime_type": "application/json"}},
                    timeout=60)
                resp2.raise_for_status()
                days_out = resp2.json()["candidates"][0]["content"]["parts"][0]["text"]
                
                # Clean JSON wrapping and syntax errors
                clean_days_out = self._clean_json(days_out)
                days_list = json.loads(clean_days_out)
                
                if isinstance(days_list, list):
                    all_skeleton.extend(days_list)
                    self.roadmap_gen_log(f"[OK] Phase '{ph_name}': {len(days_list)} ngày đã thêm vào Skeleton.")
                else:
                    self.roadmap_gen_log(f"[CẢNH BÁO] Phase '{ph_name}' trả về định dạng không mong đợi, bỏ qua.")
            except Exception as e:
                self.roadmap_gen_log(f"[LỖI NHỊP 2 - Phase '{ph_name}'] {e}")

            # Delay nhỏ tránh rate limit
            if ph != phases[-1]:
                time.sleep(2)

        # Ghép kết quả cuối
        final_json = {"domain_profile": domain_profile, "skeleton": all_skeleton}
        final_text = json.dumps(final_json, ensure_ascii=False, indent=2)

        def _update_ui():
            self.ai_roadmap_skeleton_text.delete(1.0, tk.END)
            self.ai_roadmap_skeleton_text.insert(tk.END, final_text)
        self.root.after(0, _update_ui)

        self.roadmap_gen_log(f"[HOÀN TẤT BƯỚC 1] Đã tạo Dàn ý Lõi gồm {len(all_skeleton)} ngày. Hãy bấm '2. Phản biện & Mở rộng Khung'.")

    def _roadmap_gen_step2_thread(self):
        import tkinter as tk
        import json, os, requests, re
        
        skeleton_text = self.ai_roadmap_skeleton_text.get(1.0, tk.END).strip()
        if not skeleton_text:
            self.roadmap_gen_log("[LỖI] Dàn ý Lõi đang trống. Hãy chạy Bước 1 trước!")
            return
            
        api_key = self._get_active_api_key()
        if not api_key:
            self.roadmap_gen_log("[LỖI] Không tìm thấy API Key nào đang hoạt động!")
            return
            
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        
        # Đọc tham khảo
        ref_files = [v.get().strip() for v in self.ref_file_vars if v.get().strip()]
        ref_content_block = ""
        for i, rf in enumerate(ref_files):
            if os.path.exists(rf):
                try:
                    with open(rf, 'r', encoding='utf-8') as f:
                        ref_content_block += f"\n--- File tham khảo {i+1}: {os.path.basename(rf)} ---\n{f.read()[:4000]}\n"
                except: pass

        self.roadmap_gen_log("[BƯỚC 2] Bắt đầu quá trình Phản biện & Mở rộng Khung (3 Passes)...")
        
        bad_keys = set()
        def call_llm(prompt, p_name=""):
            rc = 0
            while rc < 3:
                cur_key = self._get_active_api_key(exclude_keys=bad_keys)
                if not cur_key:
                    self.roadmap_gen_log(f"[DỪNG] Không còn API Key nào khả dụng để tiếp tục {p_name}!")
                    return None
                    
                cur_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={cur_key}"
                try:
                    resp = requests.post(cur_url, headers=headers, json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.3}}, timeout=60)
                    resp.raise_for_status()
                    return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                except Exception as e:
                    err_str = str(e)
                    if "429" in err_str or "quota" in err_str.lower() or "exhausted" in err_str.lower():
                        self.roadmap_gen_log(f"[QUOTA HẾT] Đổi key... ({p_name})")
                        bad_keys.add(cur_key)
                        time.sleep(3)
                        # Reset retry count because this is a quota issue, we want to try new keys
                        rc = 0
                    else:
                        rc += 1
                        self.roadmap_gen_log(f"[LỖI LLM {p_name}] {e} (Lần {rc}/3)")
                        time.sleep(2)
            return None

        # PASS 1
        self.roadmap_gen_log(">> Pass 1: Tự phản biện, Đa dạng hóa & Chia nhỏ chủ đề...")
        p1_prompt = f"Đây là JSON Dàn ý Lõi hiện tại:\n```json\n{skeleton_text}\n```\nYêu cầu: Hãy đóng vai trò chuyên gia, phân tích xem có chủ đề nào quá lớn cần chẻ nhỏ ra nhiều ngày không? Có kiến thức hiện đại nào đang thiếu không? Hãy sắp xếp lại, chèn thêm các ngày học mới, bổ sung các chủ đề để đa dạng hóa lộ trình. TRẢ VỀ JSON DUY NHẤT (giữ nguyên cấu trúc domain_profile và skeleton, chỉ mở rộng mảng skeleton). (KHÔNG GIẢI THÍCH)"
        out_p1 = call_llm(p1_prompt, "Pass 1")
        if not out_p1: return
        json_v2 = self._clean_json(out_p1)

        # PASS 2
        self.roadmap_gen_log(">> Pass 2: Kiểm duyệt & Ép chuẩn theo File Tham khảo/Skill...")
        p2_prompt = f"Đây là JSON Lộ trình V2 (sau khi mở rộng):\n```json\n{json_v2}\n```\nCác tài liệu chuẩn:\n{ref_content_block}\nYêu cầu: Đối chiếu Lộ trình V2 với tài liệu chuẩn. Sửa lại các chủ đề/details nào vi phạm nguyên tắc sư phạm hoặc an toàn. Đảm bảo 100% tuân thủ các quy tắc tối thượng. TRẢ VỀ JSON DUY NHẤT (giữ nguyên cấu trúc, cập nhật nội dung cho cực chuẩn). (KHÔNG GIẢI THÍCH)"
        out_p2 = call_llm(p2_prompt, "Pass 2")
        if not out_p2: return
        json_v3 = self._clean_json(out_p2)

        # Cập nhật UI JSON
        try:
            parsed_v3 = json.loads(json_v3)
            formatted_v3 = json.dumps(parsed_v3, ensure_ascii=False, indent=2)
            def _update_ui():
                self.ai_roadmap_skeleton_text.delete(1.0, tk.END)
                self.ai_roadmap_skeleton_text.insert(tk.END, formatted_v3)
            self.root.after(0, _update_ui)
        except Exception as e:
            self.roadmap_gen_log(f"[CẢNH BÁO Pass 2] JSON v3 lỗi cú pháp, dùng nguyên bản. Lỗi: {e}")
            formatted_v3 = json_v3

        # PASS 3
        self.roadmap_gen_log(">> Pass 3: Xuất file Mục lục (Markdown TOC)...")
        domain = self.ai_roadmap_domain_var.get().strip() or "Untitled"
        p3_prompt = f"Từ JSON V3 hoàn hảo này:\n```json\n{formatted_v3}\n```\nHãy sinh ra một file Markdown CHỈ chứa Mục Lục (Table of Contents) cực kỳ đẹp mắt, sử dụng heading, danh sách, và bảng biểu nếu cần. Đây sẽ là trang bìa của lộ trình. TRẢ VỀ ĐỊNH DẠNG MARKDOWN."
        out_p3 = call_llm(p3_prompt, "Pass 3")
        if not out_p3: return
        md_toc = out_p3.replace("```markdown", "").replace("```", "").strip()

        # Lưu file
        save_dir = self.ai_roadmap_save_var.get().strip() or os.path.dirname(os.path.abspath(__file__))
        safe_domain = re.sub(r'[^a-zA-Z0-9_\-]', '_', domain)
        out_file = os.path.join(save_dir, f"roadmap_{safe_domain}_auto.md")
        
        try:
            with open(out_file, 'w', encoding='utf-8') as f:
                f.write(md_toc + "\n\n")
            self.roadmap_gen_log(f"[HOÀN TẤT BƯỚC 2] Khung Dàn ý đã nâng cấp lên Master và lưu Mục lục tại: {out_file}")
            self.roadmap_gen_log(f"Hãy bấm '3. Sinh Chi Tiết Master' để viết nội dung bài giảng!")
            os.startfile(out_file)
        except Exception as e:
            self.roadmap_gen_log(f"[LỖI GHI FILE] {e}")

    def roadmap_gen_step3(self):
        import threading
        threading.Thread(target=self._roadmap_gen_step3_thread, daemon=True).start()

    def _roadmap_gen_step3_thread(self):
        import tkinter as tk
        import json, os, time, requests
        
        mode = self.ai_roadmap_expand_mode.get()
        skeleton_text = self.ai_roadmap_skeleton_text.get(1.0, tk.END).strip()
        
        if not skeleton_text:
            self.roadmap_gen_log("[LỖI] Khung chương trình (Preview) đang trống! Hãy chạy Bước 1 trước.")
            return
            
        try:
            skeleton_data = json.loads(skeleton_text)
        except Exception:
            self.roadmap_gen_log("[LỖI] Khung chương trình không đúng định dạng JSON chuẩn. Vui lòng sửa lại!")
            return
            
        if isinstance(skeleton_data, dict):
            domain_profile = skeleton_data.get("domain_profile", {})
            skeleton_list = skeleton_data.get("skeleton", [])
            # Robust fallback: if skeleton is missing, grab the first list
            if not skeleton_list:
                for v in skeleton_data.values():
                    if isinstance(v, list):
                        skeleton_list = v
                        break
        else:
            domain_profile = {}
            skeleton_list = skeleton_data
            
        persona = domain_profile.get("persona", "một chuyên gia")
        core_books = domain_profile.get("core_books", "Không có")
        supreme_commands = domain_profile.get("supreme_commands", "")
        
        commands_block = f"(⚠️ LỆNH TỐI THƯỢNG:\n{supreme_commands}\nQuy tắc chung: KHÔNG TƯƠNG TÁC, in ra toàn bộ nội dung mà không đặt câu đố chờ tôi trả lời.)" if supreme_commands else "(⚠️ LỆNH TỐI THƯỢNG: KHÔNG TƯƠNG TÁC, in ra toàn bộ nội dung mà không đặt câu đố chờ tôi trả lời.)"
            
        domain = self.ai_roadmap_domain_var.get().strip() or "Untitled"
        save_dir = self.ai_roadmap_save_var.get().strip()
        if not save_dir:
            save_dir = os.path.dirname(os.path.abspath(__file__))
            
        import re
        safe_domain = re.sub(r'[^a-zA-Z0-9_\-]', '_', domain)
        out_file = os.path.join(save_dir, f"roadmap_{safe_domain}_auto.md")
        
        self.roadmap_gen_log(f"[BƯỚC 2] Bắt đầu sinh Markdown (Mode: {mode.upper()})...")
        self.roadmap_gen_log(f"-> File đầu ra dự kiến: {out_file}")
        
        # ---------------------------------------------
        # CHẾ ĐỘ 1: TEMPLATE CƠ HỌC (NHANH)
        # ---------------------------------------------
        if mode == "template":
            try:
                with open(out_file, 'w', encoding='utf-8') as f:
                    f.write(f"# Roadmap: {domain}\n\n")
                    f.write(f"> Bối cảnh: {persona}\n> Nền tảng: {core_books}\n\n")
                    
                    for item in skeleton_list:
                        day = item.get("day", 0)
                        phase = item.get("phase", "Chưa có Giai đoạn")
                        topic = item.get("topic", "Chưa có tên")
                        details = item.get("details", [])
                        
                        f.write(f"## Day {day}: {topic} ({phase})\n\n")
                        
                        letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
                        for i, det in enumerate(details):
                            let = letters[i] if i < len(letters) else str(i)
                            f.write(f"### {day}{let}. {det}\n")
                            f.write("<!-- pages: 5 -->\n")
                            f.write(f"**Prompt:**\nĐóng vai trò là {persona}. Hôm nay là Day {day}: {det} (thuộc bài '{topic}').\n")
                            f.write(f"Giai đoạn: {phase}.\n")
                            f.write(f"Sách nền tảng liên quan: {core_books}.\n\n")
                            f.write(f"{commands_block}\n\n")
                            f.write(f"Yêu cầu: Hãy giảng giải thật chi tiết, phân tích khách quan và kèm ví dụ minh họa rõ ràng.\n\n")
                            
                self.roadmap_gen_log(f"[THÀNH CÔNG] Đã lưu file: {out_file}")
                try:
                    os.startfile(out_file)
                except Exception:
                    pass
            except Exception as e:
                self.roadmap_gen_log(f"[LỖI TEMPLATE] {e}")

        # ---------------------------------------------
        # CHẾ ĐỘ 2: LLM BATCHING (THÔNG MINH)
        # ---------------------------------------------
        elif mode == "llm":
            # Lấy API key linh hoạt - refresh trước mỗi batch
            batch_size = 10
            total_days = len(skeleton_list)

            # Kiểm tra file đã tồn tại chưa để chọn append hay ghi mới
            file_exists = os.path.exists(out_file)
            if file_exists:
                self.roadmap_gen_log(f"[INFO] File đã tồn tại, chế độ BỔ SUNG vào cuối file: {out_file}")
                # Đọc ngày cuối cùng đã ghi để skip
                try:
                    import re
                    with open(out_file, 'r', encoding='utf-8') as f:
                        existing = f.read()
                    last_days = re.findall(r'## Day (\d+):', existing)
                    last_day_done = int(last_days[-1]) if last_days else 0
                    skeleton_list = [d for d in skeleton_list if d.get('day', 0) > last_day_done]
                    if not skeleton_list:
                        self.roadmap_gen_log("[INFO] Tất cả các ngày đã có trong file. Không cần bổ sung thêm.")
                        return
                    self.roadmap_gen_log(f"[INFO] Tiếp tục từ Ngày {skeleton_list[0].get('day')} (đã bỏ qua {last_day_done} ngày đã có).")
                    total_days = len(skeleton_list)
                except Exception as e:
                    self.roadmap_gen_log(f"[CẢNH BÁO] Không phân tích được file cũ, sẽ ghi thêm toàn bộ: {e}")
            else:
                with open(out_file, 'w', encoding='utf-8') as f:
                    f.write(f"# Roadmap Chi Tiết: {domain}\n\n")
                    f.write(f"> Bối cảnh: {persona}\n> Nền tảng: {core_books}\n\n")

            bad_keys = set()
            for i in range(0, total_days, batch_size):
                chunk = skeleton_list[i:i+batch_size]
                chunk_json = json.dumps(chunk, ensure_ascii=False, indent=2)

                self.roadmap_gen_log(f"Đang xử lý Batch Day {chunk[0].get('day')} -> Day {chunk[-1].get('day')} (3 Passes)...")

                def call_llm_batch(prompt_text, p_name):
                    rc = 0
                    while rc < 3:
                        try:
                            # Auto-rotate key if needed inside the loop
                            cur_key = self._get_active_api_key(exclude_keys=bad_keys)
                            if not cur_key:
                                self.roadmap_gen_log(f"[DỪNG] Không còn API Key nào khả dụng để tiếp tục {p_name}!")
                                return None
                                
                            b_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={cur_key}"
                            payload = {"contents": [{"parts": [{"text": prompt_text}]}], "generationConfig": {"temperature": 0.4}}
                            resp = requests.post(b_url, headers={"Content-Type": "application/json"}, json=payload, timeout=60)
                            resp.raise_for_status()
                            out = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                            return out
                        except Exception as e:
                            err_str = str(e)
                            if "429" in err_str or "quota" in err_str.lower() or "exhausted" in err_str.lower():
                                self.roadmap_gen_log(f"[QUOTA HẾT] Đổi key... ({p_name})")
                                if cur_key:
                                    bad_keys.add(cur_key)
                                time.sleep(3)
                                rc = 0
                            else:
                                rc += 1
                                self.roadmap_gen_log(f"[LỖI LLM {p_name}] {e} (Lần {rc}/3)")
                                time.sleep(2)
                    return None

                # PASS 4: Draft Prompts
                self.roadmap_gen_log("  -> Pass 4: Sinh nháp kịch bản Prompt...")
                p4_prompt = f"""Tôi đang xây dựng giáo trình lĩnh vực '{domain}'.
Danh sách bài học:
{chunk_json}
Nhiệm vụ: Viết NHÁP danh sách các Lời Yêu Cầu (Prompts) để tôi nạp vào AI (Copilot).
Với mỗi bài học, hãy viết thành cấu trúc:
## Day [X]: [Tên Topic] ([Phase])
### [X]a. [Tên mục nhỏ 1]
<!-- pages: 5 -->
**Prompt:** Đóng vai trò là {persona}. Dạy bài [Tên mục nhỏ]... (lệnh tối thượng: {supreme_commands})"""
                draft = call_llm_batch(p4_prompt, "Pass 4")
                if not draft: return

                # PASS 5: Master Enhancement
                self.roadmap_gen_log("  -> Pass 5: Bơm thêm yêu cầu cấp Master...")
                p5_prompt = f"""Đây là bản nháp các câu Prompt để dạy AI:
{draft}
Nhiệm vụ: Đọc và NÂNG CẤP các câu Prompt này lên cấp độ Master.
- Thêm yêu cầu AI (Copilot) phải đưa ra các "Ví dụ thực tế", "Lỗi thường gặp (Edge cases)", "Mẹo vặt thực tiễn".
- Ép AI phải giải thích thật sâu sắc, không nói hời hợt.
Trữ lại nguyên vẹn cấu trúc (Day, pages, Prompt:)."""
                enhanced = call_llm_batch(p5_prompt, "Pass 5")
                if not enhanced: return

                # PASS 6: Format & Polish
                self.roadmap_gen_log("  -> Pass 6: Đánh bóng & Ép chuẩn Markdown...")
                p6_prompt = f"""Hãy format và đánh bóng bản Prompt siêu việt này:
{enhanced}
BẮT BUỘC tuân thủ chặt chẽ định dạng Markdown sau, KHÔNG bọc ```markdown, KHÔNG giải thích lằng nhằng:
## Day [X]: ...
### [X]a. ...
<!-- pages: [Số] -->
**Prompt:** ..."""
                final_md = call_llm_batch(p6_prompt, "Pass 6")
                if not final_md: return

                md_text = final_md.replace("```markdown\n", "").replace("```markdown", "").replace("```", "")

                with open(out_file, 'a', encoding='utf-8') as f:
                    f.write(md_text + "\n\n")

                self.roadmap_gen_log(f"[OK] Đã ghi xong Batch Day {chunk[0].get('day')} -> {chunk[-1].get('day')}")

                # Delay nhỏ giữa các batch
                if i + batch_size < total_days:
                    self.roadmap_gen_log("-> Sleep 4s để tránh rate limit...")
                    time.sleep(4)

            self.roadmap_gen_log(f"[HOÀN TẤT BATCHING] Đã lưu file: {out_file}")
            try:
                os.startfile(out_file)
            except Exception:
                pass

                    
            self.roadmap_gen_log(f"[HOÀN THÀNH] Toàn bộ Roadmap đã được lưu tại: {out_file}")
            
    # Roadmap Generator V5 -------------------------------------------------
    # These methods deliberately override the older V3/V4 methods above.  The
    # old implementation mixed planning, review and file output in one file;
    # V5 keeps JSON artifacts separate and validates every LLM boundary.
    def roadmap_gen_log(self, msg):
        def write_log():
            try:
                self.ai_roadmap_log_text.config(state='normal')
                self.ai_roadmap_log_text.insert(tk.END, str(msg) + "\n")
                self.ai_roadmap_log_text.see(tk.END)
                self.ai_roadmap_log_text.config(state='disabled')
            except tk.TclError:
                pass
        self.root.after(0, write_log)

    def _roadmap_snapshot(self):
        """Read Tk values on the UI thread before a worker starts."""
        return {
            "gen_mode": getattr(self, 'ai_roadmap_gen_mode_var', tk.StringVar(value="learning")).get().strip(),
            "domain": self.ai_roadmap_domain_var.get().strip(),
            "time_per_day": self.ai_roadmap_time_var.get().strip() or "2 tiếng",
            "days": self.ai_roadmap_days_var.get().strip(),
            "context": self.ai_roadmap_context_text.get("1.0", tk.END).strip(),
            "req_time": self.ai_req_time_var.get(),
            "req_mat": self.ai_req_mat_var.get(),
            "req_step": self.ai_req_step_var.get(),
            "req_warn": self.ai_req_warn_var.get(),
            "req_check": self.ai_req_check_var.get(),
            "req_custom": self.ai_req_custom_var.get().strip(),
            "req_sim_check": self.ai_req_sim_check_var.get(),
            "req_sim_ratio": self.ai_req_sim_ratio_var.get().strip(),
            "refs": [item.get().strip() for item in self.ref_file_vars if item.get().strip()],
            "save_dir": self.ai_roadmap_save_var.get().strip() or os.path.dirname(os.path.abspath(__file__)),
            "skeleton": self.ai_roadmap_skeleton_text.get("1.0", tk.END).strip(),
            "mode": self.ai_roadmap_expand_mode.get(),
        }

    def save_roadmap_generator_settings(self):
        snapshot = self._roadmap_snapshot()
        saved = {
            "gen_mode": snapshot.get("gen_mode", "learning"),
            "domain": snapshot["domain"],
            "time_per_day": snapshot["time_per_day"],
            "days": snapshot["days"],
            "context": snapshot["context"],
            "req_time": snapshot["req_time"],
            "req_mat": snapshot["req_mat"],
            "req_step": snapshot["req_step"],
            "req_warn": snapshot["req_warn"],
            "req_check": snapshot["req_check"],
            "req_custom": snapshot["req_custom"],
            "req_sim_check": snapshot.get("req_sim_check", 1),
            "req_sim_ratio": snapshot.get("req_sim_ratio", "96"),
            "reference_files": snapshot["refs"],
            "save_dir": self.ai_roadmap_save_var.get().strip(),
            "expand_mode": snapshot["mode"],
        }
        update_gemini_settings(roadmap_generator=saved)
        self.settings.setdefault("gemini", {})["roadmap_generator"] = saved
        self.roadmap_gen_log("[ĐÃ LƯU] Đã lưu yêu cầu, tài liệu tham khảo và cấu hình tạo roadmap gần nhất.")

    def _start_roadmap_task(self, worker, snapshot):
        if not hasattr(self, "_roadmap_lock"):
            self._roadmap_lock = threading.Lock()
        if not self._roadmap_lock.acquire(blocking=False):
            self.roadmap_gen_log("[ĐANG CHẠY] Một tác vụ roadmap đang chạy; hãy chờ hoàn tất.")
            return

        def run():
            try:
                worker(snapshot)
            except Exception as exc:
                self.roadmap_gen_log(f"[LỖI ROADMAP] {type(exc).__name__}: {exc}")
            finally:
                self._roadmap_lock.release()
        threading.Thread(target=run, daemon=True).start()

    def _roadmap_artifacts(self, snapshot):
        import re
        safe = re.sub(r'[^a-zA-Z0-9_-]', '_', snapshot["domain"] or "untitled")
        root = os.path.join(snapshot["save_dir"], f"roadmap_{safe}")
        return {
            "skeleton": root + ".skeleton.json",
            "reviewed": root + ".reviewed.json",
            "toc": root + ".toc.md",
            "final": root + ".md",
        }

    def _load_saved_roadmap_plan(self, snapshot, prefer_reviewed=False):
        """Load the last durable generator artifact when the preview is empty."""
        artifacts = self._roadmap_artifacts(snapshot)
        names = ("reviewed", "skeleton") if prefer_reviewed else ("skeleton", "reviewed")
        expected = None if snapshot["days"] == "Auto" else int(snapshot["days"])
        errors = []
        for name in names:
            path = artifacts[name]
            try:
                with open(path, "r", encoding="utf-8") as handle:
                    plan = json.load(handle)
                validate_plan(plan, expected, require_micro=True)
                return plan, path
            except FileNotFoundError:
                continue
            except (OSError, json.JSONDecodeError, RoadmapValidationError) as exc:
                errors.append(f"{path}: {exc}")
        detail = "; ".join(errors[:2]) or "không tìm thấy file skeleton/reviewed"
        raise RoadmapValidationError(f"Không nạp được roadmap đã lưu: {detail}")

    def _show_saved_plan_and_snapshot(self, snapshot, prefer_reviewed=False):
        """Return a snapshot backed by disk, and repopulate the UI preview."""
        plan, path = self._load_saved_roadmap_plan(snapshot, prefer_reviewed)
        snapshot = dict(snapshot)
        snapshot["skeleton"] = json.dumps(plan, ensure_ascii=False, indent=2)
        self._show_skeleton(plan)
        self.roadmap_gen_log(f"[NẠP LẠI] Đã nạp roadmap đã lưu: {path}")
        return snapshot

    def _read_reference_text(self, paths):
        blocks = []
        for path in paths:
            try:
                if path.lower().endswith(".pdf"):
                    import fitz
                    document = fitz.open(path)
                    try:
                        content = "\n".join(page.get_text() for page in document[:min(len(document), 20)])
                    finally:
                        document.close()
                else:
                    with open(path, "r", encoding="utf-8") as handle:
                        content = handle.read()
                # Keep a bounded but useful excerpt from both ends of a file.
                excerpt = content if len(content) <= 12000 else content[:9000] + "\n...[đã rút gọn]...\n" + content[-3000:]
                blocks.append(f"--- Tài liệu: {os.path.basename(path)} ---\n{excerpt}")
            except (OSError, UnicodeError) as exc:
                self.roadmap_gen_log(f"[CẢNH BÁO] Không đọc được tài liệu {os.path.basename(path)}: {exc}")
        return "\n\n".join(blocks)

    def _registry_path(self):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "topics_registry.md")

    def _registry_context(self):
        try:
            with open(self._registry_path(), "r", encoding="utf-8") as handle:
                return handle.read()[-12000:]
        except FileNotFoundError:
            return "(Chưa có topic nào được đăng ký.)"

    def _update_topic_registry(self, plan, roadmap_file):
        """Append only new topic ids after a reviewed plan has passed validation."""
        path = self._registry_path()
        try:
            existing = open(path, "r", encoding="utf-8").read()
        except FileNotFoundError:
            existing = "# Topics registry (AskCpl)\n\n| ID | Topic | Roadmap |\n|---|---|---|\n"
        rows = []
        for item in plan["skeleton"]:
            topic_id, title = item["topic_id"], item["topic"].replace("|", "\\|")
            if f"| {topic_id} |" not in existing:
                rows.append(f"| {topic_id} | {title} | {os.path.basename(roadmap_file)} |")
        if rows:
            atomic_write(path, existing.rstrip() + "\n" + "\n".join(rows) + "\n")

    def _call_roadmap_llm(self, prompt, label, json_mode=True, retries=3):
        import requests
        transient_attempt = 0
        while True:
            key = self._get_active_api_key()
            if not key:
                raise RoadmapValidationError("Không còn API key trạng thái active; hãy kiểm tra Quản lý API Keys.")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={key}"
            config = {"temperature": 0.1, "maxOutputTokens": 8192}
            if json_mode:
                config["responseMimeType"] = "application/json"
            try:
                self.roadmap_gen_log(f"[{label}] Gửi yêu cầu Gemini (retry mạng {transient_attempt}/{retries})...")
                response = requests.post(url, headers={"Content-Type": "application/json"},
                    json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": config}, timeout=60)
                if response.status_code == 429:
                    self._set_roadmap_key_status(key, "exhausted", "HTTP 429 / quota exhausted during roadmap generation")
                    self.roadmap_gen_log(f"[{label}] Key đã chuyển sang exhausted (kiểm tra lại sau 3 giờ); đang tìm key active khác.")
                    continue
                if response.status_code in (400, 401, 403):
                    try:
                        api_message = response.json().get("error", {}).get("message", "")
                    except Exception:
                        api_message = ""
                    if response.status_code in (401, 403) or "API key not valid" in api_message:
                        self._set_roadmap_key_status(key, "invalid", f"HTTP {response.status_code}: {api_message}")
                        self.roadmap_gen_log(f"[{label}] Key bị từ chối và đã chuyển sang invalid; đang tìm key active khác.")
                        continue
                    raise RoadmapValidationError(f"{label} bị HTTP {response.status_code} do request/schema, key vẫn active: {api_message[:160]}")
                if response.status_code >= 500:
                    transient_attempt += 1
                    self.roadmap_gen_log(f"[{label}] Gemini HTTP {response.status_code} tạm thời; key vẫn active ({transient_attempt}/{retries}).")
                    if transient_attempt >= retries:
                        raise RoadmapValidationError(f"{label} gặp Gemini HTTP {response.status_code} sau {retries} lần; thử lại batch sau.")
                    time.sleep(min(2 * transient_attempt, 6))
                    continue
                if response.status_code >= 400:
                    # A non-quota 4xx is deterministic (usually request or
                    # model configuration), so retrying it as a network error
                    # only makes the progress screen appear to run forever.
                    try:
                        api_message = response.json().get("error", {}).get("message", "")
                    except Exception:
                        api_message = response.text[:160]
                    raise RoadmapValidationError(
                        f"{label} bị HTTP {response.status_code}; không retry: {api_message[:160]}"
                    )
                response.raise_for_status()
                payload = response.json()
                candidates = payload.get("candidates", [])
                candidate = candidates[0] if candidates else {}
                parts = candidate.get("content", {}).get("parts", [])
                text = parts[0].get("text", "") if parts else ""
                if not text:
                    raise RoadmapValidationError("Gemini không trả về nội dung có thể dùng.")
                finish_reason = candidate.get("finishReason", "UNKNOWN")
                self.roadmap_gen_log(f"[{label}] Đã nhận {len(text):,} ký tự (finish={finish_reason}); đang kiểm tra định dạng.")
                return text
            except requests.exceptions.Timeout:
                transient_attempt += 1
                self.roadmap_gen_log(f"[{label}] Timeout ({transient_attempt}/{retries}); key vẫn giữ active.")
            except requests.RequestException as exc:
                transient_attempt += 1
                http_status = getattr(getattr(exc, "response", None), "status_code", None)
                status_note = f" HTTP {http_status}" if http_status else ""
                self.roadmap_gen_log(f"[{label}] Lỗi mạng/API: {type(exc).__name__}{status_note} ({transient_attempt}/{retries}); key vẫn giữ active.")
            if transient_attempt >= retries:
                raise RoadmapValidationError(f"{label} lỗi mạng/timeout sau {retries} lần; key không bị đổi trạng thái.")
            time.sleep(min(2 * transient_attempt, 6))

    def _show_skeleton(self, plan):
        formatted = json.dumps(plan, ensure_ascii=False, indent=2)
        def update():
            self.ai_roadmap_skeleton_text.delete("1.0", tk.END)
            self.ai_roadmap_skeleton_text.insert(tk.END, formatted)
        self.root.after(0, update)

    def roadmap_gen_step1(self):
        snapshot = self._roadmap_snapshot()
        if not snapshot["domain"]:
            self.roadmap_gen_log("[LỖI] Cần nhập Lĩnh vực / Từ khóa.")
            return
        self.save_roadmap_generator_settings()
        self._start_roadmap_task(self._roadmap_v5_step1, snapshot)

    def _roadmap_v5_step1(self, snapshot):
        import re
        expected = None if snapshot["days"] == "Auto" else int(snapshot["days"])
        references = self._read_reference_text(snapshot["refs"])
        registry = self._registry_context()
        day_rule = ("Tự chọn tổng 10-3000 Day phù hợp. KHÔNG tiết kiệm Day: mỗi Day chỉ là một buổi 30 phút và có thể cần hàng trăm Day cho một mảng lớn." if expected is None
                    else f"Phải có CHÍNH XÁC {expected} Day.")
        self.roadmap_gen_log("[BƯỚC 1/3 • 1A] Đang lập knowledge map và chia phase (chưa sinh Day)...")
        if snapshot.get("gen_mode") == "wiki":
            map_prompt = f"""Bạn là chuyên gia phân tích dữ liệu Bách khoa toàn thư. Hãy khảo sát và lập danh mục cấu trúc (knowledge map) để trích xuất toàn bộ dữ liệu cho '{snapshot['domain']}'.
Mục tiêu: {day_rule.replace('Day', 'lô bóc tách (Batch)')} (Mỗi lô chứa tối đa 10-20 thực thể).
Ngữ cảnh người dùng: {snapshot['context']}
Tài liệu tham khảo:\n{references}

Trả về JSON DUY NHẤT, NGẮN GỌN, KHÔNG tạo skeleton Day ở bước này: {{"domain_profile":{{"title":"...","total_days":N,"persona":"Chuyên gia phân tích data"}},"coverage":[{{"area":"...","required":true}}],"phases":[{{"id":"phase_id","name":"Tên Module (vd: Tướng Ngụy, Binh chủng, Vũ khí)","days":10,"goal":"Bóc tách toàn bộ thông số ẩn"}}]}}.
Mỗi phase (Module) có từ 5-30 lô bóc tách (được đếm là days); tổng phase.days phải đúng total_days. Coverage phải bao gồm toàn bộ các mảng như: Nhân vật/Tướng, Binh chủng, Vũ khí/Trang bị, Cơ chế, Mẹo... Quy tắc bắt buộc: Mỗi lô bóc tách (day) chỉ xử lý một nhóm 10-20 thực thể cụ thể. LUÔN dùng tiếng Việt."""
        else:
            map_prompt = f"""Bạn là kiến trúc sư giáo trình. Hãy lập knowledge map cho '{snapshot['domain']}'.
Thời lượng: {snapshot['time_per_day']}/ngày. {day_rule}
Ngữ cảnh người dùng: {snapshot['context']}
Tài liệu tham khảo:\n{references}
Topic registry của các roadmap cũ (không lặp lại nếu đã có):\n{registry}

Trả về JSON DUY NHẤT, NGẮN GỌN, KHÔNG tạo skeleton Day ở bước này: {{"domain_profile":{{"title":"...","total_days":N,"persona":"..."}},"coverage":[{{"area":"...","required":true}}],"phases":[{{"id":"phase_id","name":"...","days":10,"goal":"..."}}]}}.
Mỗi phase 5-30 Day; tổng phase.days phải đúng total_days. Coverage phải bao gồm nền tảng, thực hành, lỗi/edge case, testing, hiệu năng/bảo mật nếu phù hợp, công cụ hiện đại, case study và dự án. Quy tắc bắt buộc: Day là MỘT buổi 30 phút, không được đặt một chủ đề/dự án lớn vào một Day; phải phân rã thành nhiều micro-Day. LUÔN dùng tiếng Việt."""
        phase_map = None
        for attempt in range(1, 4):
            try:
                phase_map = load_json_response(self._call_roadmap_llm(map_prompt, f"PASS 1A lần {attempt}"))
                phases = phase_map.get("phases", []) if isinstance(phase_map, dict) else []
                total = sum(item.get("days", 0) for item in phases if isinstance(item, dict))
                target = expected if expected is not None else phase_map.get("domain_profile", {}).get("total_days")
                auto_minimum = 365 if re.search(r'\b0\s*[-–]\s*\d+\s*(?:tuổi|tuoi)\b', snapshot["domain"], re.IGNORECASE) else 10
                if not phases or not isinstance(target, int) or total != target or not auto_minimum <= target <= 3000:
                    raise RoadmapValidationError(f"phase map phải đủ {auto_minimum}-3000 Day và tổng phase.days phải khớp.")
                if any(not isinstance(item.get("days"), int) or not 5 <= item["days"] <= 500 for item in phases):
                    raise RoadmapValidationError("mỗi macro phase phải có 5-500 micro-Day.")
                break
            except RoadmapValidationError as exc:
                self.roadmap_gen_log(f"[PASS 1A • lần {attempt}/3] Chưa dùng được: {exc}. Đang retry...")
                map_prompt += f"\nPhản hồi trước lỗi: {exc}. Trả lại JSON hoàn chỉnh, ngắn gọn."
        else:
            raise RoadmapValidationError("Không tạo được phase map hợp lệ sau 3 lần.")

        # A long Auto roadmap must resume the exact approved phase map rather
        # than asking Gemini for a new total (which could change 365 to 900).
        previous_artifacts = self._roadmap_artifacts(snapshot)
        previous_checkpoint_path = previous_artifacts["skeleton"] + ".progress.json"
        if expected is None:
            try:
                previous_checkpoint = json.loads(open(previous_checkpoint_path, "r", encoding="utf-8").read())
                if (previous_checkpoint.get("domain") == snapshot["domain"]
                        and isinstance(previous_checkpoint.get("phase_map"), dict)
                        and previous_checkpoint.get("skeleton")):
                    phase_map = previous_checkpoint["phase_map"]
                    self.roadmap_gen_log(
                        f"[RESUME] Dùng lại phase map {previous_checkpoint.get('target')} Day và checkpoint "
                        f"{len(previous_checkpoint['skeleton'])} Day; không tạo kế hoạch mới."
                    )
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                pass

        phases = phase_map["phases"]
        target = expected if expected is not None else phase_map["domain_profile"]["total_days"]
        artifacts = self._roadmap_artifacts(snapshot)
        checkpoint_path = artifacts["skeleton"] + ".progress.json"
        all_days = []
        try:
            checkpoint = json.loads(open(checkpoint_path, "r", encoding="utf-8").read())
            if checkpoint.get("domain") == snapshot["domain"] and checkpoint.get("target") == target:
                all_days = checkpoint.get("skeleton", [])
                self.roadmap_gen_log(f"[RESUME] Đã khôi phục {len(all_days)}/{target} micro-Day từ checkpoint.")
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass

        # --- Quét checkpoint tìm tiêu đề trùng; cắt tại Day đó để sinh lại ---
        from difflib import SequenceMatcher as _SM
        _seen_titles: list[str] = []
        _clean_days: list = []
        _dup_from: int | None = None
        
        sim_check_enabled = snapshot.get("req_sim_check", 1)
        try:
            sim_threshold = float(snapshot.get("req_sim_ratio", 96)) / 100.0
        except ValueError:
            sim_threshold = 0.96

        for _item in all_days:
            _title = (_item.get("topic") or "").strip().lower()
            if sim_check_enabled:
                for _prev in _seen_titles:
                    if _SM(None, _title, _prev).ratio() >= sim_threshold:
                        _dup_from = _item["day"]
                        break
            if _dup_from is not None:
                break
            _seen_titles.append(_title)
            _clean_days.append(_item)
        if _dup_from is not None:
            self.roadmap_gen_log(
                f"[RESUME-FIX] Checkpoint có tiêu đề trùng tại Day {_dup_from}; "
                f"cắt về {len(_clean_days)} Day và sinh lại từ Day {_dup_from}."
            )
            all_days = _clean_days
            atomic_write(checkpoint_path, json.dumps(
                {"domain": snapshot["domain"], "target": target,
                 "phase_map": phase_map, "skeleton": all_days},
                ensure_ascii=False, indent=2,
            ))
        # --- Hết quét ---

        start_day = len(all_days) + 1

        local_pdf_sources = [os.path.basename(path) for path in snapshot["refs"] if path.lower().endswith(".pdf")]
        self.roadmap_gen_log(f"[BƯỚC 1/3 • 1A OK] {len(phases)} phase, tổng {target} Day. Bắt đầu sinh skeleton từng phase...")
        phase_start = 1
        for index, phase in enumerate(phases, start=1):
            already_in_phase = max(0, min(len(all_days) - phase_start + 1, phase["days"]))
            remaining, batch_number = phase["days"] - already_in_phase, already_in_phase // 5
            # Five rich micro-days are substantially more reliable than ten
            # when Gemini must return nested JSON lists.
            batch_limit = 5
            while remaining:
                batch_number += 1
                count = min(batch_limit, remaining)
                end_day = start_day + count - 1
                self.roadmap_gen_log(f"[BƯỚC 1/3 • 1B] Macro phase {index}/{len(phases)} • batch {batch_number}: Day {start_day}-{end_day} (đang gọi Gemini)...")
                known_ids = [item["topic_id"] for item in all_days]
                known_titles = [item["topic"] for item in all_days]
                if snapshot.get("gen_mode") == "wiki":
                    phase_prompt = f"""Tạo CHÍNH XÁC {count} LÔ BÓC TÁCH (được gắn nhãn là 'day') cho Module '{phase.get('name')}' của kho dữ liệu '{snapshot['domain']}', từ lô số {start_day}..{end_day}. Mục tiêu: {phase.get('goal')}.
Trả JSON MẢNG, mỗi object: {{"day":N,"topic_id":"snake_case_duy_nhat","topic":"Tiêu đề lô (ví dụ: Tướng Thục từ A-D) (tối đa 80 ký tự)","phase":"{phase.get('name')}","kind":"extraction","estimated_minutes":30,"concrete_project":"Trích xuất chi tiết các thực thể cụ thể (CẦN liệt kê đích danh 10-20 tên thực thể vào đây)","materials":[],"definition_of_done":["Đúng bảng Markdown, không bỏ sót bất kỳ thực thể nào"],"details":["Trích xuất chỉ số Võ, Trí","Trích xuất năng lực ẩn"],"keywords":["tối đa 4 từ khóa"],"prerequisites":[]}}.
ID đã tồn tại: {known_ids}. Mỗi lô (day) BẮT BUỘC phải liệt kê rõ 10-20 tên của các tướng/binh chủng/vũ khí sẽ trích xuất vào trường 'concrete_project'. KHÔNG để chung chung. LUÔN dùng tiếng Việt.
CAM KẾT: trường 'topic' của MỖI lô mới PHẢI khác hoàn toàn với mọi tiêu đề sau đây (TUYỆT ĐỐI KHÔNG lặp lại): {known_titles[-80:] if len(known_titles) > 80 else known_titles}."""
                else:
                    phase_prompt = f"""Tạo CHÍNH XÁC {count} MICRO-DAY cho phase '{phase.get('name')}' của roadmap '{snapshot['domain']}', Day {start_day}..{end_day}. Mục tiêu: {phase.get('goal')}.
Trả JSON MẢNG, mỗi object: {{"day":N,"topic_id":"snake_case_duy_nhat","topic":"tiêu đề micro-Day DUY NHẤT (tối đa 80 ký tự)","phase":"{phase.get('name')}","kind":"lesson|review|capstone","estimated_minutes":30,"concrete_project":"một món đồ/sản phẩm cụ thể","materials":["tối đa 3 vật liệu + số lượng/kích thước"],"definition_of_done":["tối đa 2 tiêu chí kiểm tra"],"details":["tối đa 3 việc nhỏ có thể làm trong 30 phút"],"keywords":["tối đa 4 từ khóa"],"prerequisites":["topic_id đã học trước đó"]}}.
ID đã tồn tại từ phase trước: {known_ids}. prerequisites chỉ được dùng ID trong danh sách này hoặc Day đứng trước ngay trong response; nếu không chắc, dùng []. Không bọc markdown, không thiếu Day, không trùng Day, topic_id không trùng. {"Day cuối cùng của roadmap phải kind='capstone'." if index == len(phases) and remaining == count and len(phases) >= 2 else ""} LUÔN dùng tiếng Việt.
CAM KẾT: trường 'topic' của MỖI Day mới PHẢI khác hoàn toàn với mọi tiêu đề sau đây (đây là danh sách tiêu đề đã tồn tại — TUYỆT ĐỐI KHÔNG được lặp lại hay diễn đạt lại bằng từ ngữ tương tự): {known_titles[-80:] if len(known_titles) > 80 else known_titles}."""
                for attempt in range(1, 4):
                    try:
                        response_text = self._call_roadmap_llm(phase_prompt, f"PASS 1B phase {index}.{batch_number} lần {attempt}")
                        generated = load_json_response(response_text)
                        if not isinstance(generated, list) or [item.get("day") for item in generated if isinstance(item, dict)] != list(range(start_day, end_day + 1)):
                            raise RoadmapValidationError("batch trả về thiếu, trùng hoặc sai thứ tự Day.")
                        known = set(known_ids)
                        for item in generated:
                            if not isinstance(item, dict) or not item.get("topic_id") or item["topic_id"] in known:
                                raise RoadmapValidationError("batch có topic_id rỗng hoặc trùng.")
                            prerequisites = item.get("prerequisites", [])
                            if not isinstance(prerequisites, list) or any(value not in known for value in prerequisites):
                                raise RoadmapValidationError("batch tham chiếu prerequisite chưa học.")
                            known.add(item["topic_id"])
                            # Reference metadata is deterministic local data,
                            # not something the model needs to print in every
                            # JSON object (which previously caused truncation).
                            item["source_files"] = list(local_pdf_sources)
                        all_days.extend(generated)
                        atomic_write(checkpoint_path, json.dumps({
                            "domain": snapshot["domain"], "target": target,
                            "phase_map": phase_map, "skeleton": all_days,
                        }, ensure_ascii=False, indent=2))
                        self.roadmap_gen_log(f"[PASS 1B • Macro {index} • batch {batch_number} OK] Đã nhận {len(generated)} Day; tổng {len(all_days)}/{target}.")
                        if attempt > 1 and batch_limit > 2:
                            batch_limit = max(2, batch_limit // 2)
                            self.roadmap_gen_log(f"[PASS 1B • Macro {index}] JSON vừa cần retry; giữ batch {batch_limit} Day cho các lượt sau để ổn định.")
                        break
                    except RoadmapValidationError as exc:
                        if 'response_text' in locals():
                            debug_path = checkpoint_path + f".invalid_macro{index}_batch{batch_number}.txt"
                            atomic_write(debug_path, response_text)
                        self.roadmap_gen_log(f"[PASS 1B • Macro {index} • batch {batch_number} • lần {attempt}/3] JSON lỗi: {exc}. Retry...")
                        err_str = str(exc)
                        if "trùng nội dung" in err_str:
                            # Gom tất cả tiêu đề hiện tại và ép AI đặt tên khác hẳn
                            forbidden = [item["topic"] for item in all_days]
                            phase_prompt += (
                                f"\nLỖI TRÙNG TIÊU ĐỀ: {exc}. "
                                f"TUYỆT ĐỐI KHÔNG được dùng hoặc paraphrase bất kỳ tiêu đề nào trong danh sách cấm này: {forbidden[-80:] if len(forbidden) > 80 else forbidden}. "
                                "Mỗi 'topic' phải khác biệt rõ ràng — đặt cụ thể theo nội dung hẹp của micro-Day đó, không dùng tên chung chung."
                            )
                        else:
                            phase_prompt += f"\nLỗi trước: {exc}. Trả MẢNG JSON hoàn chỉnh, không cắt ngang."
                else:
                    if count > 1:
                        batch_limit = max(1, count // 2)
                        self.roadmap_gen_log(
                            f"[PASS 1B • Macro {index}] Batch {count} Day vẫn lỗi JSON sau 3 lần; "
                            f"tự giảm xuống batch {batch_limit} Day và tiếp tục từ Day {start_day}."
                        )
                        continue
                    raise RoadmapValidationError(
                        f"Macro phase {index}, Day {start_day} không tạo được JSON hợp lệ sau 3 lần; xem file .invalid_*.txt."
                    )
                remaining -= count
                start_day = end_day + 1
            phase_start += phase["days"]

        plan = {"domain_profile": phase_map["domain_profile"], "coverage": phase_map.get("coverage", []), "skeleton": all_days}
        from roadmap_pipeline import validate_plan
        validate_plan(plan, target, require_micro=True, sim_check_enabled=bool(snapshot.get("req_sim_check", 1)), sim_threshold=sim_threshold)
        atomic_write(artifacts["skeleton"], json.dumps(plan, ensure_ascii=False, indent=2))
        try:
            os.remove(checkpoint_path)
        except OSError:
            pass
        self._show_skeleton(plan)
        self.roadmap_gen_log(f"[✅ BƯỚC 1/3 HOÀN TẤT] JSON skeleton {len(all_days)} Day đã kiểm định và lưu: {artifacts['skeleton']}")
        self.roadmap_gen_log("[TIẾP THEO] JSON đã sẵn sàng. Bấm '2. Phản biện & Mở rộng Khung' để chạy các pass kiểm tra/bổ sung trước khi sinh roadmap cuối.")

    def roadmap_gen_step2(self):
        snapshot = self._roadmap_snapshot()
        if not snapshot["skeleton"]:
            try:
                snapshot = self._show_saved_plan_and_snapshot(snapshot, prefer_reviewed=False)
            except RoadmapValidationError as exc:
                self.roadmap_gen_log(f"[LỖI] Hãy tạo hoặc nạp skeleton trước. {exc}")
                return
        self.save_roadmap_generator_settings()
        self._start_roadmap_task(self._roadmap_v5_step2, snapshot)

    def _roadmap_v5_step2(self, snapshot):
        expected = None if snapshot["days"] == "Auto" else int(snapshot["days"])
        current = load_json_response(snapshot["skeleton"])
        validate_plan(current, expected, require_micro=True)
        references = self._read_reference_text(snapshot["refs"])
        plan_json = json.dumps(current, ensure_ascii=False)
        # Condensed view for reviewer passes: only fields needed for gap analysis.
        # Sending full plan_json (materials/details/done) to reviewers wastes tokens
        # and causes MAX_TOKENS truncation on 150+ Day roadmaps.
        _review_fields = ("day", "topic_id", "topic", "phase", "kind", "prerequisites")
        condensed_plan = {
            "domain_profile": current.get("domain_profile", {}),
            "skeleton": [{k: item[k] for k in _review_fields if k in item}
                         for item in current["skeleton"]],
        }
        condensed_plan_json = json.dumps(condensed_plan, ensure_ascii=False)
        reviews = []
        reviewer_jobs = [
            ("PASS 2/8 Coverage", "Tìm các mảng kiến thức, công nghệ, khái niệm hoặc kỹ năng bị thiếu."),
            ("PASS 3/8 Thực hành", "Tìm thiếu sót về bài tập, dự án, lỗi thực tế, testing, bảo mật và hiệu năng."),
            ("PASS 4/8 Prerequisite", "Tìm prerequisite sai thứ tự, topic quá lớn, vòng phụ thuộc hoặc nội dung trùng."),
            ("PASS 5/8 Red-team", "Đóng vai reviewer khắt khe: tìm nội dung lỗi thời, thiếu case study và tiêu chí nghề nghiệp."),
        ]
        # Never ask Gemini to reprint a 45-150 Day JSON document.  It is
        # likely to be truncated.  Revise one phase at a time, then validate
        # the complete result locally.
        self.roadmap_gen_log("[PASS 6/8] Tích hợp phản biện theo từng phase nhỏ để tránh JSON bị cắt...")
        revised_days = []
        phase_groups = []
        for item in current["skeleton"]:
            if (not phase_groups or phase_groups[-1][0] != item.get("phase")
                    or len(phase_groups[-1][1]) >= 5):
                phase_groups.append((item.get("phase"), [item]))
            else:
                phase_groups[-1][1].append(item)
        reviews_json = json.dumps(reviews, ensure_ascii=False)
        artifacts = self._roadmap_artifacts(snapshot)
        progress_path = artifacts["reviewed"] + ".progress.json"
        import hashlib
        source_digest = hashlib.sha256(plan_json.encode("utf-8")).hexdigest()
        progress = {"domain": snapshot["domain"], "source_digest": source_digest,
                    "reviews": reviews, "revised_days": []}
        try:
            with open(progress_path, "r", encoding="utf-8") as handle:
                saved_progress = json.load(handle)
            if (saved_progress.get("domain") == snapshot["domain"]
                    and saved_progress.get("source_digest") == source_digest):
                progress = saved_progress
                reviews = progress.get("reviews", reviews)
                reviews_json = json.dumps(reviews, ensure_ascii=False)
                self.roadmap_gen_log(f"[RESUME BƯỚC 2] Đã nạp {len(progress.get('revised_days', []))} Day phản biện đã lưu.")
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            pass

        for job_index, (label, task) in enumerate(reviewer_jobs):
            if job_index < len(reviews):
                continue
            self.roadmap_gen_log(f"[{label}] Đang phản biện độc lập...")
            # Use condensed plan to avoid MAX_TOKENS on large roadmaps.
            # If still truncated, retry with first half of days only.
            review_plan = condensed_plan_json
            reviewer_ok = False
            for rev_attempt in range(1, 4):
                try:
                    raw = self._call_roadmap_llm(
                        f"Roadmap JSON (tóm tắt):\n{review_plan}\nTài liệu:\n{references}\n{task}\n"
                        "Chỉ trả JSON {\"gaps\":[{\"id\":\"snake_case\",\"reason\":\"...\",\"suggestion\":\"...\"}],\"warnings\":[\"...\"]}. Không viết lại roadmap.",
                        f"{label} lần {rev_attempt}"
                    )
                    parsed = load_json_response(raw)
                    reviews.append(parsed)
                    progress["reviews"] = reviews
                    atomic_write(progress_path, json.dumps(progress, ensure_ascii=False, indent=2))
                    reviewer_ok = True
                    break
                except RoadmapValidationError as exc:
                    err = str(exc)
                    self.roadmap_gen_log(f"[{label} • lần {rev_attempt}/3] Lỗi: {err}. Retry...")
                    if "MAX_TOKENS" in err or "Expecting value" in err or "hợp lệ" in err:
                        # Truncate the condensed plan to first half of days to shrink input
                        skeleton_half = condensed_plan["skeleton"][:len(condensed_plan["skeleton"]) // 2]
                        review_plan = json.dumps(
                            {"domain_profile": condensed_plan["domain_profile"], "skeleton": skeleton_half},
                            ensure_ascii=False,
                        )
                        self.roadmap_gen_log(f"[{label}] JSON bị cắt (MAX_TOKENS); gửi lại với {len(skeleton_half)} Day đầu.")
                    # else: keep same review_plan, the error might be transient
            if not reviewer_ok:
                self.roadmap_gen_log(f"[{label}] Không phản biện được sau 3 lần; bỏ qua pass này và tiếp tục.")
                reviews.append({"gaps": [], "warnings": [f"Pass {label} bị bỏ qua do lỗi MAX_TOKENS sau 3 lần retry."]})
                progress["reviews"] = reviews
                atomic_write(progress_path, json.dumps(progress, ensure_ascii=False, indent=2))
        reviews_json = json.dumps(reviews, ensure_ascii=False)
        revised_days = progress.get("revised_days", [])
        expected_prefix = current["skeleton"][:len(revised_days)]
        if ([item.get("day") for item in revised_days if isinstance(item, dict)]
                != [item["day"] for item in expected_prefix]
                or [item.get("topic_id") for item in revised_days if isinstance(item, dict)]
                != [item["topic_id"] for item in expected_prefix]):
            self.roadmap_gen_log("[CẢNH BÁO RESUME BƯỚC 2] Checkpoint không khớp skeleton hiện tại; chạy lại phần tích hợp.")
            revised_days = []
            progress["revised_days"] = []
            atomic_write(progress_path, json.dumps(progress, ensure_ascii=False, indent=2))
        completed_days = len(revised_days)
        for phase_index, (phase_name, phase_days) in enumerate(phase_groups, start=1):
            if completed_days >= len(phase_days):
                completed_days -= len(phase_days)
                continue
            if completed_days:
                raise RoadmapValidationError("Checkpoint Bước 2 dừng giữa một nhóm Day; không thể resume an toàn.")
            expected_day_numbers = [item["day"] for item in phase_days]
            expected_ids = [item["topic_id"] for item in phase_days]
            self.roadmap_gen_log(f"[PASS 6/8 • Phase {phase_index}/{len(phase_groups)}] Tích hợp Day {expected_day_numbers[0]}-{expected_day_numbers[-1]}...")
            phase_prompt = f"""Chỉ chỉnh sửa phase JSON nhỏ sau theo các phản biện, không tạo roadmap toàn bộ.
Phase hiện tại: {json.dumps(phase_days, ensure_ascii=False)}
Phản biện: {reviews_json}
Trả JSON MẢNG đầy đủ với ĐÚNG các Day {expected_day_numbers} và ĐÚNG các topic_id {expected_ids}. Giữ mọi kiến thức cũ, bổ sung kiến thức thiếu vào topic/details/keywords; sửa prerequisite nếu cần. Mỗi object bắt buộc có day, topic_id, topic, phase, kind, estimated_minutes (5-30), concrete_project, materials (mảng), definition_of_done (mảng), details (tối đa 3 việc 30 phút), keywords (mảng), prerequisites (mảng). Không trả source_files (ứng dụng tự giữ nguồn gốc từ skeleton). Không bọc Markdown, chỉ JSON, tiếng Việt."""
            for attempt in range(1, 4):
                response_text = None
                try:
                    # Network/API failures must participate in the phase retry
                    # loop too; otherwise one temporary 503 aborts Step 2.
                    response_text = self._call_roadmap_llm(
                        phase_prompt, f"PASS 6 phase {phase_index} lần {attempt}"
                    )
                    candidate_days, restored_ids = restore_locked_day_identity(
                        phase_days, load_json_response(response_text)
                    )
                    if restored_ids:
                        changed_days = ", ".join(str(day) for day, _generated, _saved in restored_ids)
                        self.roadmap_gen_log(
                            f"[PASS 6 • Phase {phase_index}] Gemini đổi topic_id ở Day {changed_days}; "
                            "đã giữ ID gốc để không hỏng prerequisite/registry."
                        )
                    revised_days.extend(candidate_days)
                    progress["revised_days"] = revised_days
                    atomic_write(progress_path, json.dumps(progress, ensure_ascii=False, indent=2))
                    self.roadmap_gen_log(f"[PASS 6/8 • Phase {phase_index} OK] Đã tích hợp {len(candidate_days)} Day.")
                    break
                except RoadmapValidationError as exc:
                    if response_text is not None:
                        debug_path = artifacts["reviewed"] + f".invalid_pass6_phase{phase_index}_attempt{attempt}.txt"
                        atomic_write(debug_path, response_text)
                        self.roadmap_gen_log(f"[PASS 6 • Phase {phase_index} • lần {attempt}/3] JSON lỗi: {exc}. Đã lưu phản hồi để kiểm tra: {debug_path}")
                    else:
                        self.roadmap_gen_log(f"[PASS 6 • Phase {phase_index} • lần {attempt}/3] Lỗi mạng/API: {exc}. Checkpoint vẫn giữ nguyên; sẽ thử lại phase.")
                    phase_prompt += f"\nLỗi ở lần trước: {exc}. Trả lại JSON MẢNG hoàn chỉnh, không giải thích."
                    if attempt < 3:
                        time.sleep(min(2 ** attempt, 8))
            else:
                raise RoadmapValidationError(
                    f"Không tích hợp được phase {phase_index} sau 3 lần. "
                    f"Checkpoint đã giữ Day 1-{len(revised_days)}; mở lại và bấm Bước 2 để tiếp tục."
                )
        revised = dict(current)
        revised["skeleton"] = revised_days
        
        sim_check_enabled = snapshot.get("req_sim_check", 1)
        try:
            sim_threshold = float(snapshot.get("req_sim_ratio", 96)) / 100.0
        except ValueError:
            sim_threshold = 0.96
            
        validate_revision(current, revised, expected, require_micro=True, sim_check_enabled=bool(sim_check_enabled), sim_threshold=sim_threshold)
        atomic_write(artifacts["reviewed"], json.dumps(revised, ensure_ascii=False, indent=2))
        atomic_write(artifacts["toc"], render_toc(revised))
        self._update_topic_registry(revised, artifacts["final"])
        self._show_skeleton(revised)
        try:
            os.remove(progress_path)
        except OSError:
            pass
        self.roadmap_gen_log(f"[✅ BƯỚC 2/3 HOÀN TẤT] JSON đã phản biện/lưu: {artifacts['reviewed']} | TOC: {artifacts['toc']}")
        self.roadmap_gen_log("[TIẾP THEO] Bấm '3. Sinh Chi Tiết Master & Kiểm định' để tạo file Markdown roadmap cuối.")

    def roadmap_gen_step3(self):
        snapshot = self._roadmap_snapshot()
        if not snapshot["skeleton"]:
            try:
                snapshot = self._show_saved_plan_and_snapshot(snapshot, prefer_reviewed=True)
            except RoadmapValidationError as exc:
                self.roadmap_gen_log(f"[LỖI] Hãy chạy Bước 1 và Bước 2 trước. {exc}")
                return
        self.save_roadmap_generator_settings()
        self._start_roadmap_task(self._roadmap_v5_step3, snapshot)

    def _roadmap_v5_step3(self, snapshot):
        expected = None if snapshot["days"] == "Auto" else int(snapshot["days"])
        plan = load_json_response(snapshot["skeleton"])
        validate_plan(plan, expected, require_micro=True)
        artifacts = self._roadmap_artifacts(snapshot)
        
        struct_items = []
        if snapshot.get("req_time"): struct_items.append("phân bổ thời gian")
        if snapshot.get("req_mat"): struct_items.append("vật liệu chuẩn bị")
        if snapshot.get("req_step"): struct_items.append("từng bước thực hiện")
        if snapshot.get("req_warn"): struct_items.append("an toàn/lỗi thường gặp")
        if snapshot.get("req_check"): struct_items.append("checklist hoàn thành")
        if snapshot.get("req_custom"): struct_items.append(snapshot["req_custom"])
        struct_str = ", ".join(struct_items) if struct_items else "tự do (theo ý bạn)"
        
        req_keys = ["concrete_project", "definition_of_done"]
        if snapshot.get("req_time"): req_keys.append("estimated_minutes")
        if snapshot.get("req_mat"): req_keys.append("materials")
        req_keys_str = ", ".join(req_keys)
        
        lessons = []
        if snapshot["mode"] == "template":
            for item in plan["skeleton"]:
                focus = "; ".join(item["details"])
                if snapshot.get("gen_mode") == "wiki":
                    prompt_str = f"LUÔN TRẢ LỜI BẰNG TIẾNG VIỆT. Mục tiêu trích xuất: {item['concrete_project']}. Yêu cầu chi tiết: {focus}. Tiêu chuẩn: {'; '.join(item['definition_of_done'])}. TUYỆT ĐỐI KHÔNG dùng văn xuôi lan man, KHÔNG đóng vai giáo viên. BẮT BUỘC xuất toàn bộ dữ liệu dưới dạng BẢNG MARKDOWN nghiêm ngặt. Không được bỏ sót bất kỳ thực thể nào được liệt kê trong mục tiêu."
                else:
                    prompt_str = f"LUÔN TRẢ LỜI BẰNG TIẾNG VIỆT. Mục tiêu duy nhất: {item['concrete_project']}. Việc nhỏ: {focus}. Hoàn thành khi: {'; '.join(item['definition_of_done'])}. Nếu hệ thống đính kèm văn bản PDF/tài liệu, chỉ dùng phần liên quan làm bằng chứng/hướng dẫn, không tóm tắt toàn bộ tài liệu. Hãy trả lời tối đa 1.000 từ, theo cấu trúc: {struct_str}. Không giảng lý thuyết lan man và không tạo quiz tương tác; nếu có câu hỏi, in đáp án mẫu cùng lúc."
                
                lessons.append({"day": item["day"],
                    "prompt": prompt_str,
                    "exercises": [f"Thực hành {focus}", "Tự kiểm tra edge case và đối chiếu đáp án mẫu"],
                    "tags": ["#roadmap", f"#day{item['day']}", *[f"#{str(tag).replace(' ', '_')}" for tag in item.get("keywords", [])]]})
        else:
            import hashlib
            progress_path = artifacts["final"] + ".progress.json"
            source_digest = hashlib.sha256(
                json.dumps(plan, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest()
            try:
                with open(progress_path, "r", encoding="utf-8") as handle:
                    progress = json.load(handle)
                if progress.get("domain") == snapshot["domain"] and progress.get("source_digest") == source_digest:
                    lessons = progress.get("lessons", [])
                    expected_prefix = [item["day"] for item in plan["skeleton"][:len(lessons)]]
                    if [item.get("day") for item in lessons if isinstance(item, dict)] != expected_prefix:
                        raise RoadmapValidationError("checkpoint Bước 3 không khớp Day của roadmap hiện tại.")
                    self.roadmap_gen_log(f"[RESUME BƯỚC 3] Đã nạp {len(lessons)}/{len(plan['skeleton'])} Day nội dung đã lưu.")
                else:
                    lessons = []
            except FileNotFoundError:
                pass
            start_at = len(lessons)
            for start in range(start_at, len(plan["skeleton"]), 8):
                chunk = plan["skeleton"][start:start + 8]
                self.roadmap_gen_log(f"[BƯỚC 3/3 • Sinh nội dung] Day {chunk[0]['day']}-{chunk[-1]['day']}...")
                if snapshot.get("gen_mode") == "wiki":
                    prompt = f"""Tạo nội dung Bách khoa toàn thư bằng tiếng Việt cho JSON lô bóc tách sau: {json.dumps(chunk, ensure_ascii=False)}
Trả JSON MẢNG đúng số phần tử, mỗi phần {{"day":N,"prompt":"...","exercises":["..."],"tags":["#..."]}}. Trong prompt BẮT BUỘC liệt kê đích danh các thực thể từ {req_keys_str} của Day. Ép AI trả lời bằng BẢNG MARKDOWN nghiêm ngặt, TUYỆT ĐỐI KHÔNG dùng văn xuôi hay văn phong giáo viên. Không được thay thế bằng lý thuyết tổng quát. Không viết dòng heading bắt đầu bằng '## Day'. Không đổi day."""
                else:
                    prompt = f"""Tạo nội dung roadmap bằng tiếng Việt cho JSON micro-Day sau: {json.dumps(chunk, ensure_ascii=False)}
Trả JSON MẢNG đúng số phần tử, mỗi phần {{"day":N,"prompt":"...","exercises":["..."],"tags":["#..."]}}. Trong prompt BẮT BUỘC nêu đúng {req_keys_str} của Day. Nếu module Tải Roadmap đính kèm văn bản PDF/tài liệu, prompt phải yêu cầu dùng đúng đoạn liên quan, không tóm tắt toàn bộ tài liệu. Ép AI trả lời tối đa 1.000 từ, chỉ một buổi 5-30 phút, theo cấu trúc: {struct_str}. Không được thay thế bằng lý thuyết tổng quát; không tạo quiz tương tác chờ trả lời; không viết dòng heading bắt đầu bằng '## Day'. Không đổi day."""
                for attempt in range(1, 4):
                    try:
                        generated = load_json_response(self._call_roadmap_llm(
                            prompt, f"PASS 8 Day {chunk[0]['day']}-{chunk[-1]['day']} lần {attempt}"
                        ))
                        if (not isinstance(generated, list)
                                or {x.get("day") for x in generated if isinstance(x, dict)} != {x["day"] for x in chunk}):
                            raise RoadmapValidationError(
                                f"PASS 8 trả về thiếu/trùng Day cho batch {chunk[0]['day']}-{chunk[-1]['day']}."
                            )
                        break
                    except RoadmapValidationError as exc:
                        self.roadmap_gen_log(
                            f"[BƯỚC 3/3 • Day {chunk[0]['day']}-{chunk[-1]['day']} • lần {attempt}/3] "
                            f"chưa hoàn tất: {exc}. Checkpoint vẫn giữ nguyên."
                        )
                        if attempt == 3:
                            raise RoadmapValidationError(
                                f"Bước 3 dừng tại Day {chunk[0]['day']}-{chunk[-1]['day']}; "
                                f"đã lưu {len(lessons)} Day, mở lại và bấm Bước 3 để tiếp tục."
                            )
                        time.sleep(min(2 ** attempt, 8))
                lessons.extend(generated)
                atomic_write(progress_path, json.dumps({
                    "domain": snapshot["domain"], "source_digest": source_digest,
                    "lessons": lessons,
                }, ensure_ascii=False, indent=2))
        markdown = render_markdown(plan, lessons)
        atomic_write(artifacts["final"], markdown)
        try:
            os.remove(artifacts["final"] + ".progress.json")
        except OSError:
            pass
        self.roadmap_gen_log(f"[✅ BƯỚC 3/3 HOÀN TẤT] Roadmap Markdown cuối đã kiểm định và lưu: {artifacts['final']}")

    def setup_roadmap_run_tab(self):
        gemini_settings = self.settings.get("gemini", {})
        Label(self.sub_tab_roadmap_run, text="🤖 Auto AI - Tải và Sinh Nội Dung Tự Động", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Roadmap File
        f2 = Frame(self.sub_tab_roadmap_run)
        f2.pack(fill='x', padx=20, pady=5)
        Label(f2, text="File Roadmap:", width=15, anchor='w').pack(side='left')
        self.ai_roadmap_var = StringVar(value=gemini_settings.get("last_roadmap", ""))
        Entry(f2, textvariable=self.ai_roadmap_var, state='readonly').pack(side='left', fill='x', expand=True)
        Button(f2, text="Chọn Markdown", command=self.ai_select_roadmap).pack(side='right', padx=5)
        
        # Doc Dir
        f3 = Frame(self.sub_tab_roadmap_run)
        f3.pack(fill='x', padx=20, pady=5)
        Label(f3, text="Thư mục Docs:", width=15, anchor='w').pack(side='left')
        self.ai_doc_var = StringVar(value=gemini_settings.get("last_doc_dir", ""))
        Entry(f3, textvariable=self.ai_doc_var, state='readonly').pack(side='left', fill='x', expand=True)
        Button(f3, text="Chọn thư mục chứa PDF", command=self.ai_select_doc_dir).pack(side='right', padx=5)
        
        # Output Dir
        f4 = Frame(self.sub_tab_roadmap_run)
        f4.pack(fill='x', padx=20, pady=5)
        Label(f4, text="Thư mục Xuất:", width=15, anchor='w').pack(side='left')
        self.ai_out_var = StringVar(value=gemini_settings.get("last_out_dir", ""))
        Entry(f4, textvariable=self.ai_out_var, state='readonly').pack(side='left', fill='x', expand=True)
        Button(f4, text="Chọn Output", command=self.ai_select_out_dir).pack(side='right', padx=5)

        # Adaptive learning control.  The profile lives beside session.json so
        # each exported course keeps its own learner context and privacy scope.
        f_adaptive = Frame(self.sub_tab_roadmap_run)
        f_adaptive.pack(fill='x', padx=20, pady=4)
        self.ai_adaptive_mode_var = IntVar(value=gemini_settings.get("adaptive_mode", 1))
        Checkbutton(f_adaptive, text="🧠 Học thích nghi: dùng Hồ sơ + phản hồi Day trước",
                    variable=self.ai_adaptive_mode_var, fg="#1565c0").pack(side='left')
        Button(f_adaptive, text="Hồ sơ học thích nghi...", command=self.open_adaptive_profile,
               bg="#1565c0", fg="white").pack(side='left', padx=8)
        Button(f_adaptive, text="Ghi phản hồi Day...", command=self.open_day_feedback,
               bg="#6c3483", fg="white").pack(side='left', padx=2)
        Button(f_adaptive, text="Knowledge Pack...", command=self.open_knowledge_pack,
               bg="#13795b", fg="white").pack(side='left', padx=8)
        self.ai_generate_visuals_var = IntVar(value=gemini_settings.get("generate_visuals", 0))
        Checkbutton(f_adaptive, text="Sinh ảnh Gemini khi Day yêu cầu", variable=self.ai_generate_visuals_var,
                    fg="#8e44ad").pack(side='left', padx=10)
        
        # Save Settings
        Button(self.sub_tab_roadmap_run, text="Lưu Cấu Hình AI", command=self.save_ai_settings, bg="#f39c12", fg="white").pack(pady=5)
        
        # Options row
        f_opts = Frame(self.sub_tab_roadmap_run)
        f_opts.pack(fill='x', padx=20, pady=3)
        self.ai_force_restart_var = IntVar(value=0)
        Checkbutton(f_opts, text="🗑️ Xóa session cũ & Chạy lại từ Đầu (Day 1)", variable=self.ai_force_restart_var, fg="red").pack(side='left')
        
        Label(f_opts, text="   HOẶC Bắt đầu từ Day:").pack(side='left')
        self.ai_start_day_var = StringVar(value="")
        Entry(f_opts, textvariable=self.ai_start_day_var, width=5).pack(side='left', padx=5)
        
        self.lbl_session_status = Label(f_opts, text="", fg="#d35400", font=("Arial", 9, "bold"))
        self.lbl_session_status.pack(side='left', padx=10)
        
        # YC5 options row
        f_opts_followup = Frame(self.sub_tab_roadmap_run)
        f_opts_followup.pack(fill='x', padx=20, pady=3)
        self.ai_enable_followup_var = IntVar(value=gemini_settings.get("enable_followup", 1))
        Checkbutton(f_opts_followup, text="Bật hỏi bổ sung (Follow-up) để AI làm rõ thêm (YC5)", 
                    variable=self.ai_enable_followup_var).pack(side='left')
        
        # Follow-up mode: unlimited vs limited
        f_followup_mode = Frame(self.sub_tab_roadmap_run)
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
        f_expand = Frame(self.sub_tab_roadmap_run)
        f_expand.pack(fill='x', padx=20, pady=3)
        Label(f_expand, text="📋 Tạo Roadmap Mở Rộng:", anchor='w').pack(side='left')
        self.ai_pages_per_day_var = StringVar(value="10")
        Entry(f_expand, textvariable=self.ai_pages_per_day_var, width=4).pack(side='left', padx=2)
        Label(f_expand, text="trang/Day").pack(side='left')
        Button(f_expand, text="📋 Tạo roadmap_expanded.md", command=self.expand_roadmap_handler,
               bg="#1565c0", fg="white").pack(side='right', padx=5)
        
        # Output path for expanded roadmap
        f_exp_out = Frame(self.sub_tab_roadmap_run)
        f_exp_out.pack(fill='x', padx=20, pady=2)
        Label(f_exp_out, text="   ↳ Lưu expanded ra:", width=15, anchor='w').pack(side='left')
        self.ai_expanded_out_var = StringVar(value="")
        Entry(f_exp_out, textvariable=self.ai_expanded_out_var, state='readonly').pack(side='left', fill='x', expand=True)
        Button(f_exp_out, text="Chọn", command=self.ai_select_expanded_out).pack(side='right', padx=5)
        Label(f_exp_out, text="(trống = cạnh file roadmap gốc)", fg="gray", font=("Arial", 8)).pack(side='right')
        
        # Action buttons (Start / Stop)
        f_actions = Frame(self.sub_tab_roadmap_run)
        f_actions.pack(pady=10)
        self.btn_ai_start = Button(f_actions, text="▶ Bắt đầu Sinh Tự Động", command=self.start_ai_worker, bg="#2ea043", fg="white", font=("Arial", 12, "bold"), padx=20)
        self.btn_ai_start.pack(side="left", padx=10)
        self.btn_ai_stop = Button(f_actions, text="🛑 Dừng lại", command=self.stop_ai_worker, bg="#e74c3c", fg="white", font=("Arial", 12, "bold"), padx=20, state="disabled")
        self.btn_ai_stop.pack(side="left", padx=10)
        
        # Logs (with scrollbar)
        Label(self.sub_tab_roadmap_run, text="Tiến trình:", font=("Arial", 10, "bold"), anchor='w').pack(fill='x', padx=20)
        f_log = Frame(self.sub_tab_roadmap_run)
        f_log.pack(fill='both', expand=True, padx=20, pady=5)
        log_scroll = Scrollbar(f_log)
        log_scroll.pack(side='right', fill='y')
        self.ai_log = Text(f_log, height=12, state='disabled', bg="#f4f4f4", yscrollcommand=log_scroll.set)
        self.ai_log.pack(fill='both', expand=True)
        log_scroll.config(command=self.ai_log.yview)
        
        self.ai_out_var.trace_add("write", self.check_auto_ai_session)
        self.ai_roadmap_var.trace_add("write", self.check_auto_ai_session)
        self.check_auto_ai_session()
        
    def check_auto_ai_session(self, *args):
        out_dir = self.ai_out_var.get().strip()
        if not out_dir:
            roadmap = self.ai_roadmap_var.get().strip()
            if roadmap and os.path.isfile(roadmap):
                out_dir = os.path.dirname(roadmap)
                
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
            import urllib.parse
            
            with open(session_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    self.lbl_session_status.config(text="Session trống")
                    self.ai_start_day_var.set("")
                    return
                if content.startswith('"') and content.endswith('"'):
                    content = content[1:-1]
                    decoded_bytes = base64.b64decode(content)
                    decoded_latin = decoded_bytes.decode('latin-1')
                    json_str = urllib.parse.unquote(decoded_latin)
                    session_data = json.loads(json_str)
                else:
                    session_data = json.loads(content)
                    
            if not session_data:
                self.lbl_session_status.config(text="Session trống")
                self.ai_start_day_var.set("")
                return
                
            completed_count = sum(1 for item in session_data if item.get("completed") and item.get("followup_complete", True))
            
            if completed_count > 0:
                self.lbl_session_status.config(text=f"Đã lưu: {completed_count}/{len(session_data)} phần. Tự động tiếp tục.")
                self.ai_start_day_var.set("") # Xóa trống để dùng smart resume dựa trên session
            else:
                self.lbl_session_status.config(text="Chưa hoàn thành phần nào")
                self.ai_start_day_var.set("")
                
        except Exception as e:
            if hasattr(self, 'lbl_session_status'):
                self.lbl_session_status.config(text=f"Lỗi đọc: {str(e)[:15]}")
                
    def update_keys_label(self):
        gemini_settings = self.settings.get("gemini", {})
        keys = gemini_settings.get("api_keys", [])
        active = sum(1 for k in keys if k.get("status") == "active")
        if hasattr(self, 'lbl_keys_status'):
            self.lbl_keys_status.config(text=f"Đang có {len(keys)} Key (Hoạt động: {active})")

    def setup_api_keys_tab(self):
        top = self.sub_tab_keys

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
                import json, re
                s = json.dumps(resp_json)
                m = re.search(r'(?:projects/|project_number:)(\d+)', s)
                if m: return m.group(1)
            except Exception:
                pass
            return ""

        # === LOG HELPER (widget defined later, closure works at call-time) ===
        _log_box = [None]  # mutable container cho ScrolledText widget bên dưới
        def log_key(msg):
            import datetime
            ts = datetime.datetime.now().strftime("%H:%M:%S")
            def _do():
                w = _log_box[0]
                if not w:
                    return
                try:
                    w.config(state='normal')
                    w.insert(END, f"[{ts}] {msg}\n")
                    w.see(END)
                    w.config(state='disabled')
                except Exception:
                    pass
            top.after(0, _do)

        # === TREEVIEW ===
        frame_tree = Frame(top)
        frame_tree.pack(side="top", fill="both", expand=True, padx=10, pady=(10, 0))

        columns = ("email", "key", "project_name", "project", "type", "status", "last_check", "reset_time")
        tree = ttk.Treeview(frame_tree, columns=columns, show="headings")
        tree.heading("email", text="Email / Tên")
        tree.heading("key", text="API Key")
        tree.heading("project_name", text="Project Name")
        tree.heading("project", text="Project ID")
        tree.heading("type", text="Loại API")
        tree.heading("status", text="Trạng thái")
        tree.heading("last_check", text="Check lần cuối")
        tree.heading("reset_time", text="Khôi phục sau")

        tree.column("email", width=120)
        tree.column("key", width=200)
        tree.column("project_name", width=120)
        tree.column("project", width=100)
        tree.column("type", width=100)
        tree.column("status", width=95)
        tree.column("last_check", width=120)
        tree.column("reset_time", width=120)

        def tree_sort_column(col, reverse):
            l = [(tree.set(k, col), k) for k in tree.get_children('')]
            l.sort(reverse=reverse)
            for index, (val, k) in enumerate(l):
                tree.move(k, '', index)
            tree.heading(col, command=lambda: tree_sort_column(col, not reverse))

        for col in columns:
            tree.heading(col, command=lambda c=col: tree_sort_column(c, False))

        # Tag màu đỏ cho key trùng project
        tree.tag_configure("dup_project", background="#ffcccc", foreground="#c0392b")

        vsb = ttk.Scrollbar(frame_tree, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(fill="both", expand=True, side="left")
        vsb.pack(fill="y", side="left")

        def edit_key(event=None):
            selected = tree.selection()
            if not selected: return
            idx = int(selected[0])
            gemini_settings = self.settings.get("gemini", {})
            keys = gemini_settings.get("api_keys", [])
            if idx < 0 or idx >= len(keys): return

            k_obj = keys[idx]

            edit_win = Toplevel(self.root)
            edit_win.title("Sửa API Key")
            edit_win.geometry("480x580")
            edit_win.minsize(460, 500)
            edit_win.resizable(True, True)
            edit_win.transient(self.root)
            edit_win.grab_set()
            edit_win.bind("<Escape>", lambda e: edit_win.destroy())

            # --- Frame nút (luôn hiển thị ở cuối, không bị cuộn) ---
            f_btns = Frame(edit_win)
            f_btns.pack(side="bottom", fill="x", padx=20, pady=8)
            Button(f_btns, text="🔍 Kiểm tra", command=lambda: check_new_key(), bg="#f39c12", fg="white", width=12).pack(side="left", padx=5)
            btn_save_edit = Button(f_btns, text="Lưu", command=lambda: do_save(), bg="#27ae60", fg="white", width=8)
            btn_save_edit.pack(side="left", padx=5)
            Button(f_btns, text="Hủy", command=edit_win.destroy, bg="#e74c3c", fg="white", width=8).pack(side="right", padx=5)

            # --- Canvas + Scrollbar cho nội dung ---
            canvas_edit = Canvas(edit_win, borderwidth=0)
            scrollbar_edit = ttk.Scrollbar(edit_win, orient="vertical", command=canvas_edit.yview)
            canvas_edit.configure(yscrollcommand=scrollbar_edit.set)
            scrollbar_edit.pack(side="right", fill="y")
            canvas_edit.pack(side="top", fill="both", expand=True)

            scroll_frame = Frame(canvas_edit)
            canvas_win_id = canvas_edit.create_window((0, 0), window=scroll_frame, anchor="nw")

            def _on_frame_configure(event):
                canvas_edit.configure(scrollregion=canvas_edit.bbox("all"))
                canvas_edit.itemconfig(canvas_win_id, width=canvas_edit.winfo_width())
            scroll_frame.bind("<Configure>", _on_frame_configure)
            canvas_edit.bind("<Configure>", lambda e: canvas_edit.itemconfig(canvas_win_id, width=e.width))

            def _on_mousewheel(event):
                canvas_edit.yview_scroll(int(-1*(event.delta/120)), "units")
            canvas_edit.bind_all("<MouseWheel>", _on_mousewheel)
            edit_win.bind("<Destroy>", lambda e: canvas_edit.unbind_all("<MouseWheel>"))

            # --- Nội dung form bên trong scroll_frame ---
            Label(scroll_frame, text="Nhập API Key:", anchor='w').pack(fill='x', padx=20, pady=(15, 2))
            entry_key = Entry(scroll_frame, width=50)
            entry_key.pack(fill='x', padx=20, pady=2)
            entry_key.insert(0, k_obj.get("key", ""))

            Label(scroll_frame, text="Tên/Email gợi nhớ:", anchor='w').pack(fill='x', padx=20, pady=(10, 2))
            entry_email = Entry(scroll_frame, width=50)
            entry_email.pack(fill='x', padx=20, pady=2)
            entry_email.insert(0, k_obj.get("email", ""))

            Label(scroll_frame, text="Loại API:", anchor='w').pack(fill='x', padx=20, pady=(10, 2))
            from tkinter.ttk import Combobox
            combo_type = Combobox(scroll_frame, values=["GEMINI API", "CLAUDE API", "OPENAI API"], state="readonly")
            combo_type.pack(fill='x', padx=20, pady=2)
            combo_type.set(k_obj.get("type", "GEMINI API"))

            Label(scroll_frame, text="Project Name:", anchor='w').pack(fill='x', padx=20, pady=(10, 2))
            entry_proj_name = Entry(scroll_frame, width=50)
            entry_proj_name.pack(fill='x', padx=20, pady=2)
            entry_proj_name.insert(0, k_obj.get("project_name", ""))

            Label(scroll_frame, text="Project ID (Để phân biệt Quota):", anchor='w').pack(fill='x', padx=20, pady=(10, 2))
            entry_proj = Entry(scroll_frame, width=50)
            entry_proj.pack(fill='x', padx=20, pady=2)
            entry_proj.insert(0, k_obj.get("project_id", ""))

            disp_s = k_obj.get("status", "active")
            if disp_s == "invalid" and k_obj.get("error_msg"):
                disp_s = f"Lỗi: {k_obj.get('error_msg')}"
            status_var = StringVar(value=disp_s)
            lbl_status = Label(scroll_frame, textvariable=status_var, fg="gray", font=("Arial", 10, "bold"))
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
                    _kd = api_key[:8] + "***" + api_key[-4:] if len(api_key) > 12 else api_key[:4] + "***"
                    log_key(f"🔍 Kiểm tra key: {_kd}")
                    try:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
                        log_key(f"   → Gọi API gemini-flash-latest...")
                        headers = {'Content-Type': 'application/json'}
                        payload = {"contents": [{"parts": [{"text": "Hi"}]}], "generationConfig": {"maxOutputTokens": 5}}
                        resp = requests.post(url, headers=headers, json=payload, timeout=15)
                        log_key(f"   ← HTTP {resp.status_code}")
                        if resp.status_code == 200:
                            log_key(f"   ✅ Key hoạt động tốt!")
                            edit_win.after(0, lambda: [status_var.set("✅ Hoạt động (Active)"), lbl_status.config(fg="green")])
                        else:
                            try:
                                rj = resp.json()
                            except Exception:
                                rj = {}
                            msg = rj.get("error", {}).get("message", "Lỗi không xác định")
                            proj = extract_project_id(rj)
                            log_key(f"   Phản hồi: {msg[:120]}")
                            if proj and not entry_proj.get().strip():
                                edit_win.after(0, lambda p=proj: (entry_proj.delete(0, 'end'), entry_proj.insert(0, p)))
                                log_key(f"   ℹ️ Project ID: {proj}")
                            if resp.status_code == 503 or "currently experiencing" in msg.lower() or "overloaded" in msg.lower():
                                log_key(f"   ⏸️ Model quá tải TẠM THỜI. Key vẫn hợp lệ! Thử lại sau vài phút.")
                                edit_win.after(0, lambda: [status_var.set("⏸️ Model tạm quá tải (Key OK)"), lbl_status.config(fg="#e67e22")])
                            elif "Quota" in msg or "exhausted" in msg.lower() or resp.status_code == 429:
                                log_key(f"   ⚠️ Hết Quota!")
                                edit_win.after(0, lambda: [status_var.set("⚠️ Hết Quota (Exhausted)"), lbl_status.config(fg="orange")])
                            else:
                                log_key(f"   ❌ Key lỗi hoặc không hợp lệ.")
                                edit_win.after(0, lambda: [status_var.set(f"❌ Lỗi: {msg[:40]}"), lbl_status.config(fg="red")])
                    except requests.exceptions.ConnectionError as conn_err:
                        log_key(f"   🌐 Lỗi kết nối mạng! (Key có thể vẫn hợp lệ)")
                        log_key(f"      Chi tiết: {str(conn_err)[:150]}")
                        log_key(f"      → Kiểm tra internet, VPN, hoặc thử lại sau.")
                        edit_win.after(0, lambda: [status_var.set("🌐 Lỗi mạng (Key chưa xác định được)"), lbl_status.config(fg="#7f8c8d")])
                    except requests.exceptions.Timeout:
                        log_key(f"   ⏱️ Timeout! Server chưa phản hồi sau 15 giây. Key chưa xác định.")
                        edit_win.after(0, lambda: [status_var.set("⏱️ Timeout (Key chưa xác định)"), lbl_status.config(fg="#7f8c8d")])
                    except Exception as e:
                        log_key(f"   ❌ Exception: {type(e).__name__}: {str(e)[:150]}")
                        edit_win.after(0, lambda: [status_var.set(f"❌ Lỗi: {str(e)[:40]}"), lbl_status.config(fg="red")])
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
                keys[idx]["type"] = combo_type.get()
                keys[idx]["project_name"] = entry_proj_name.get().strip()
                keys[idx]["project_id"] = entry_proj.get().strip()
                keys[idx]["status"] = status_mapped
                keys[idx]["reset_time"] = reset_time
                keys[idx]["next_check_time"] = next_check_time
                keys[idx]["error_msg"] = error_msg
                self.last_added_type = combo_type.get()

                from settings import update_gemini_settings
                update_gemini_settings(api_keys=keys)
                self.settings = load_settings()
                refresh_list()
                edit_win.destroy()

            entry_proj.focus_set()
            edit_win.bind("<Return>", lambda e: do_save())

        tree.bind("<Double-1>", edit_key)

        def refresh_list():
            for item in tree.get_children():
                tree.delete(item)
            gemini_settings = self.settings.get("gemini", {})
            keys = gemini_settings.get("api_keys", [])

            # Tìm project_id trùng trên cùng một email
            project_counts = {}
            for k in keys:
                pid = k.get("project_id", "")
                email = k.get("email", "").strip().lower()
                if pid and email:
                    key_pair = (email, pid)
                    project_counts[key_pair] = project_counts.get(key_pair, 0) + 1
            dup_projects = {pair for pair, cnt in project_counts.items() if cnt > 1}

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
                pname = k.get("project_name", "")
                email = k.get("email", "").strip().lower()
                tag = ("dup_project",) if pid and email and (email, pid) in dup_projects else ()

                tree.insert("", "end", iid=str(idx), values=(
                    k.get("email", ""),
                    masked_key,
                    pname if pname else "-",
                    pid if pid else "-",
                    k.get("type", "GEMINI API"),
                    disp_status,
                    lc_str,
                    rt_str
                ), tags=tag)
            self.update_keys_label()

        def add_key():
            add_win = Toplevel(self.root)
            add_win.title("Thêm API Key Mới")
            add_win.geometry("480x580")
            add_win.minsize(460, 500)
            add_win.resizable(True, True)
            add_win.transient(self.root)
            add_win.grab_set()
            add_win.bind("<Escape>", lambda e: add_win.destroy())

            # --- Frame nút (luôn hiển thị ở cuối, không bị cuộn) ---
            f_btns = Frame(add_win)
            f_btns.pack(side="bottom", fill="x", padx=20, pady=8)

            # --- Canvas + Scrollbar ---
            canvas_add = Canvas(add_win, borderwidth=0)
            scrollbar_add = ttk.Scrollbar(add_win, orient="vertical", command=canvas_add.yview)
            canvas_add.configure(yscrollcommand=scrollbar_add.set)
            scrollbar_add.pack(side="right", fill="y")
            canvas_add.pack(side="top", fill="both", expand=True)

            scroll_frame_add = Frame(canvas_add)
            canvas_add_win_id = canvas_add.create_window((0, 0), window=scroll_frame_add, anchor="nw")

            def _on_add_frame_configure(event):
                canvas_add.configure(scrollregion=canvas_add.bbox("all"))
                canvas_add.itemconfig(canvas_add_win_id, width=canvas_add.winfo_width())
            scroll_frame_add.bind("<Configure>", _on_add_frame_configure)
            canvas_add.bind("<Configure>", lambda e: canvas_add.itemconfig(canvas_add_win_id, width=e.width))

            def _on_add_mousewheel(event):
                canvas_add.yview_scroll(int(-1*(event.delta/120)), "units")
            canvas_add.bind_all("<MouseWheel>", _on_add_mousewheel)
            add_win.bind("<Destroy>", lambda e: canvas_add.unbind_all("<MouseWheel>"))

            # --- Nội dung form ---
            Label(scroll_frame_add, text="Nhập API Key:", anchor='w').pack(fill='x', padx=20, pady=(15, 2))
            entry_key = Entry(scroll_frame_add, width=50)
            entry_key.pack(fill='x', padx=20, pady=2)
            entry_key.focus_set()

            Label(scroll_frame_add, text="Tên/Email gợi nhớ (để trống để tự điền sau):", anchor='w').pack(fill='x', padx=20, pady=(10, 2))
            entry_email = Entry(scroll_frame_add, width=50)
            entry_email.pack(fill='x', padx=20, pady=2)
            entry_email.insert(0, getattr(self, "last_added_email", ""))

            Label(scroll_frame_add, text="Loại API:", anchor='w').pack(fill='x', padx=20, pady=(10, 2))
            from tkinter.ttk import Combobox
            combo_type = Combobox(scroll_frame_add, values=["GEMINI API", "CLAUDE API", "OPENAI API"], state="readonly")
            combo_type.pack(fill='x', padx=20, pady=2)
            combo_type.set(getattr(self, "last_added_type", "GEMINI API"))

            Label(scroll_frame_add, text="Project Name:", anchor='w').pack(fill='x', padx=20, pady=(10, 2))
            entry_proj_name = Entry(scroll_frame_add, width=50)
            entry_proj_name.pack(fill='x', padx=20, pady=2)
            entry_proj_name.insert(0, getattr(self, "last_added_project_name", ""))

            Label(scroll_frame_add, text="Project ID (Để phân biệt Quota):", anchor='w').pack(fill='x', padx=20, pady=(10, 2))
            entry_proj = Entry(scroll_frame_add, width=50)
            entry_proj.pack(fill='x', padx=20, pady=2)
            last_proj = getattr(self, "last_added_project", "")
            if last_proj.isdigit():
                last_proj = str(int(last_proj) + 1)
            entry_proj.insert(0, last_proj)

            status_var = StringVar(value="Chưa kiểm tra trạng thái")
            lbl_status = Label(scroll_frame_add, textvariable=status_var, fg="gray", font=("Arial", 10, "bold"))
            lbl_status.pack(pady=10)

            _check_result = {"project_id": "", "status": "", "done": False}

            def run_check_inner(api_key_raw, on_done=None):
                api_key = decode_key(api_key_raw)
                _kd = api_key[:8] + "***" + api_key[-4:] if len(api_key) > 12 else api_key[:4] + "***"
                log_key(f"🔍 Kiểm tra key mới: {_kd}")
                try:
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
                    log_key(f"   → Gọi API gemini-flash-latest...")
                    headers = {'Content-Type': 'application/json'}
                    payload = {"contents": [{"parts": [{"text": "Hi"}]}], "generationConfig": {"maxOutputTokens": 5}}
                    resp = requests.post(url, headers=headers, json=payload, timeout=15)
                    log_key(f"   ← HTTP {resp.status_code}")
                    if resp.status_code == 200:
                        _check_result["status"] = "active"
                        log_key(f"   ✅ Key hoạt động tốt!")
                        add_win.after(0, lambda: [status_var.set("✅ Hoạt động (Active)"), lbl_status.config(fg="green")])
                    else:
                        try:
                            rj = resp.json()
                        except Exception:
                            rj = {}
                        msg = rj.get("error", {}).get("message", "Lỗi không xác định")
                        proj = extract_project_id(rj)
                        log_key(f"   Phản hồi: {msg[:120]}")
                        if proj:
                            _check_result["project_id"] = proj
                        if proj and not entry_proj.get().strip():
                            add_win.after(0, lambda p=proj: (entry_proj.delete(0, 'end'), entry_proj.insert(0, p)))
                            log_key(f"   ℹ️ Project ID: {proj}")
                        if resp.status_code == 503 or "currently experiencing" in msg.lower() or "overloaded" in msg.lower():
                            _check_result["status"] = "busy"
                            log_key(f"   ⏸️ Model quá tải TẠM THỜI. Key vẫn hợp lệ!")
                            add_win.after(0, lambda: [status_var.set("⏸️ Model tạm quá tải (Key OK)"), lbl_status.config(fg="#e67e22")])
                        elif "Quota" in msg or "exhausted" in msg.lower() or resp.status_code == 429:
                            _check_result["status"] = "exhausted"
                            log_key(f"   ⚠️ Hết Quota!")
                            add_win.after(0, lambda: [status_var.set("⚠️ Hết Quota (Exhausted)"), lbl_status.config(fg="orange")])
                        else:
                            _check_result["status"] = "invalid"
                            _check_result["errmsg"] = msg[:35]
                            log_key(f"   ❌ Key không hợp lệ.")
                            add_win.after(0, lambda: [status_var.set(f"❌ Lỗi: {msg[:40]}"), lbl_status.config(fg="red")])
                except requests.exceptions.ConnectionError as conn_err:
                    _check_result["status"] = "network_error"
                    log_key(f"   🌐 Lỗi kết nối mạng! (Key chưa xác định)")
                    log_key(f"      Chi tiết: {str(conn_err)[:150]}")
                    add_win.after(0, lambda: [status_var.set("🌐 Lỗi mạng (chưa xác định)"), lbl_status.config(fg="#7f8c8d")])
                except requests.exceptions.Timeout:
                    _check_result["status"] = "network_error"
                    log_key(f"   ⏱️ Timeout! Server chưa phản hồi sau 15 giây.")
                    add_win.after(0, lambda: [status_var.set("⏱️ Timeout (chưa xác định)"), lbl_status.config(fg="#7f8c8d")])
                except Exception as e:
                    _check_result["status"] = "invalid"
                    _check_result["errmsg"] = str(e)[:35]
                    log_key(f"   ❌ Exception: {type(e).__name__}: {str(e)[:150]}")
                    add_win.after(0, lambda: [status_var.set(f"❌ Lỗi: {str(e)[:40]}"), lbl_status.config(fg="red")])
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
                    "type": combo_type.get(),
                    "project_name": entry_proj_name.get().strip(),
                    "project_id": entry_proj.get().strip() or _check_result.get("project_id", ""),
                    "status": status_mapped,
                    "reset_time": reset_time,
                    "next_check_time": next_check_time,
                    "last_check_time": int(time.time())
                })

                self.last_added_email = e_val
                self.last_added_project = entry_proj.get().strip()
                self.last_added_project_name = entry_proj_name.get().strip()
                self.last_added_type = combo_type.get()

                from settings import update_gemini_settings
                update_gemini_settings(api_keys=gemini_settings["api_keys"])
                self.settings = load_settings()
                refresh_list()
                add_win.destroy()

            Button(f_btns, text="🔍 Kiểm tra trạng thái", command=check_new_key, bg="#f39c12", fg="white", width=18).pack(side="left", padx=5)
            btn_save = Button(f_btns, text="Lưu", command=do_save, bg="#27ae60", fg="white", width=8)
            btn_save.pack(side="left", padx=5)
            Button(f_btns, text="Hủy", command=add_win.destroy, bg="#e74c3c", fg="white", width=8).pack(side="right", padx=5)
            add_win.bind("<Return>", lambda e: do_save())

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

        def check_all_keys(only_errors=False):
            gemini_settings = self.settings.get("gemini", {})
            keys = gemini_settings.get("api_keys", [])
            if not keys: return

            keys_to_check = keys
            if only_errors:
                keys_to_check = [k for k in keys if k.get("status") not in ["active", "exhausted"]]
                if not keys_to_check:
                    messagebox.showinfo("Thông báo", "Không có key nào bị lỗi để kiểm tra.", parent=top)
                    return

            stop_flag = [False]
            def stop_check():
                stop_flag[0] = True
                btn_check.config(state="disabled", text="⏳ Đang dừng...")
                log_key("🛑 Nhận lệnh dừng, đang đợi kết thúc key hiện tại...")

            # Biến nút check tất cả thành nút Dừng
            btn_check.config(state="normal", text="⏹ Dừng kiểm tra", command=stop_check, bg="#c0392b")
            try:
                btn_check_err.config(state="disabled")
            except NameError:
                pass
            top.update_idletasks()
            log_key(f"🔄 Bắt đầu kiểm tra {len(keys_to_check)} API keys...")

            def run_checks():
                for key_obj in keys_to_check:
                    if stop_flag[0]:
                        break
                    raw_key = key_obj.get("key")
                    if not raw_key: continue
                    email = key_obj.get("email", "Không tên")
                    log_key(f"──────────────────────────────")
                    log_key(f"⏳ Kiểm tra: {email[:50]}")
                    api_key = decode_key(raw_key)
                    try:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
                        log_key(f"   → Gọi API gemini-flash-latest...")
                        headers = {'Content-Type': 'application/json'}
                        payload = {"contents": [{"parts": [{"text": "Hi"}]}], "generationConfig": {"maxOutputTokens": 5}}
                        resp = requests.post(url, headers=headers, json=payload, timeout=15)
                        key_obj["last_check_time"] = int(time.time())
                        log_key(f"   ← HTTP {resp.status_code}")

                        if resp.status_code == 200:
                            now = int(time.time())
                            old_status = key_obj.get("status")
                            next_check = key_obj.get("next_check_time", 0)
                            if old_status == "exhausted" and next_check > now:
                                remain_min = (next_check - now) // 60
                                log_key(f"   ⚠️ API OK nhưng giữ án Exhausted ({remain_min} phút còn lại).")
                            else:
                                key_obj["status"] = "active"
                                key_obj["reset_time"] = 0
                                key_obj["next_check_time"] = 0
                                log_key(f"   ✅ Hoạt động tốt!")
                        else:
                            try:
                                rj = resp.json()
                            except Exception:
                                rj = {}
                            msg = rj.get("error", {}).get("message", "")
                            log_key(f"   Phản hồi API: {msg[:150]}")
                            proj = extract_project_id(rj)
                            if proj:
                                key_obj["project_id"] = proj
                                log_key(f"   ℹ️ Project ID: {proj}")
                            # 503 hoặc model quá tải: KHÔNG đổi status key
                            if resp.status_code == 503 or "currently experiencing" in msg.lower() or "overloaded" in msg.lower():
                                log_key(f"   ⏸️ Model quá tải TẠM THỜI → Key vẫn hợp lệ! (Giữ nguyên status)")
                            elif "Quota" in msg or "exhausted" in msg.lower() or resp.status_code == 429:
                                key_obj["status"] = "exhausted"
                                key_obj["reset_time"] = int(time.time()) + 86400
                                key_obj["next_check_time"] = int(time.time()) + 10800
                                key_obj["error_msg"] = ""
                                log_key(f"   ⚠️ Hết Quota (Exhausted).")
                            else:
                                key_obj["status"] = "invalid"
                                key_obj["error_msg"] = msg[:50]
                                log_key(f"   ❌ Key không hợp lệ.")
                    except requests.exceptions.ConnectionError as conn_err:
                        # Lỗi mạng → KHÔNG đổi status
                        log_key(f"   🌐 Lỗi kết nối mạng! (Key giữ nguyên status cũ)")
                        log_key(f"      {str(conn_err)[:150]}")
                        log_key(f"      → Key có thể vẫn hợp lệ. Kiểm tra internet.")
                    except requests.exceptions.Timeout:
                        log_key(f"   ⏱️ Timeout sau 15s (Key giữ nguyên status cũ)")
                    except Exception as e:
                        key_obj["status"] = "invalid"
                        key_obj["error_msg"] = str(e)[:50]
                        log_key(f"   ❌ Exception: {type(e).__name__}: {str(e)[:150]}")

                    # Cập nhật giao diện và lưu ngay sau mỗi key
                    def update_single():
                        update_gemini_settings(api_keys=keys)
                        self.settings = load_settings()
                        refresh_list()
                    top.after(0, update_single)

                log_key(f"══════════════════════════════")
                if stop_flag[0]:
                    log_key(f"🛑 Đã dừng tiến trình kiểm tra!")
                else:
                    log_key(f"✅ Kiểm tra xong toàn bộ!")
                top.after(0, lambda: update_ui_after_check(keys, stop_flag[0]))

            def update_ui_after_check(keys, stopped):
                update_gemini_settings(api_keys=keys)
                self.settings = load_settings()
                refresh_list()
                btn_check.config(state="normal", text="Kiểm tra tất cả", command=lambda: check_all_keys(False), bg="#f39c12")
                try:
                    btn_check_err.config(state="normal")
                except NameError:
                    pass
                if not stopped:
                    messagebox.showinfo("Hoàn tất", "Đã kiểm tra xong!", parent=top)

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
                        payload = {"contents": [{"parts": [{"text": "Hello. " * 10}]}], "generationConfig": {"maxOutputTokens": 1000}}
                        resp = requests.post(url, headers=headers, json=payload, timeout=10)
                        key_obj["last_check_time"] = int(time.time())

                        if resp.status_code == 200:
                            now = int(time.time())
                            old_status = key_obj.get("status")
                            next_check = key_obj.get("next_check_time", 0)
                            if old_status == "exhausted" and next_check > now:
                                pass # Giữ nguyên trạng thái phạt
                            else:
                                key_obj["status"] = "active"
                                key_obj["reset_time"] = 0
                                key_obj["next_check_time"] = 0
                        else:
                            rj = resp.json()
                            msg = rj.get("error", {}).get("message", "")
                            proj = extract_project_id(rj)
                            if proj:
                                key_obj["project_id"] = proj
                            if "Quota" in msg or "exhausted" in msg.lower() or resp.status_code == 429:
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

        def save_sort_order():
            gemini_settings = self.settings.get("gemini", {})
            keys = gemini_settings.get("api_keys", [])
            if not keys: return
            new_keys = []
            for item in tree.get_children():
                try:
                    idx = int(item)
                    if 0 <= idx < len(keys):
                        new_keys.append(keys[idx])
                except:
                    pass
            from settings import update_gemini_settings
            update_gemini_settings(api_keys=new_keys)
            self.settings = load_settings()
            refresh_list()
            messagebox.showinfo("Hoàn tất", "Đã lưu vị trí thứ tự hiển thị của các API Keys!", parent=top)

        def import_json_handler():
            from tkinter import filedialog, messagebox
            import json
            filepath = filedialog.askopenfilename(
                title="Chọn file JSON chứa API Keys",
                filetypes=[("JSON Files", "*.json")]
            )
            if not filepath: return
            
            try:
                with open(filepath, 'r', encoding='utf-8-sig') as f:
                    new_keys_data = json.load(f)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể đọc file JSON:\n{e}", parent=top)
                return
            
            gemini_settings = self.settings.get("gemini", {})
            existing_keys = gemini_settings.get("api_keys", [])
            
            existing_key_values = set()
            email_counts = {}
            for k in existing_keys:
                raw_k = k.get("key", "")
                existing_key_values.add(decode_key(raw_k))
                existing_key_values.add(raw_k)
                em = k.get("email", "").strip().lower()
                if em:
                    email_counts[em] = email_counts.get(em, 0) + 1
            
            added_count = 0
            for nk in new_keys_data:
                if isinstance(nk, str):
                    nk_val = nk
                    nk_em = "imported@gmail.com"
                    nk_type = "GEMINI API"
                elif isinstance(nk, dict):
                    nk_val = nk.get("key", "")
                    nk_em = nk.get("email", "imported@gmail.com").strip()
                    nk_type = nk.get("type", "GEMINI API")
                else:
                    continue
                
                if not nk_val or nk_val in existing_key_values:
                    continue
                
                em_lower = nk_em.lower()
                current_cnt = email_counts.get(em_lower, 0)
                email_counts[em_lower] = current_cnt + 1
                new_proj_id = str(current_cnt + 1)
                
                existing_keys.append({
                    "key": nk_val,
                    "email": nk_em,
                    "project_id": new_proj_id,
                    "type": nk_type,
                    "status": "Chưa kiểm tra trạng thái",
                    "reset_time": 0,
                    "last_check_time": 0,
                    "next_check_time": 0,
                    "error_msg": ""
                })
                existing_key_values.add(nk_val)
                added_count += 1
            
            if added_count > 0:
                from settings import update_gemini_settings
                update_gemini_settings(api_keys=existing_keys)
                self.settings = load_settings()
                refresh_list()
                messagebox.showinfo("Thành công", f"Đã nhập {added_count} API Keys mới!", parent=top)
            else:
                messagebox.showinfo("Thông báo", "Không có API Key nào mới được thêm (tất cả bị trùng hoặc lỗi).", parent=top)

        btn_frame = Frame(top)
        btn_frame.pack(fill="x", padx=10, pady=10, side="bottom")
        Button(btn_frame, text="Nhập từ JSON", command=import_json_handler, bg="#34495e", fg="white").pack(side="left", padx=5)
        Button(btn_frame, text="Thêm Key", command=add_key, bg="#27ae60", fg="white").pack(side="left", padx=5)
        btn_check = Button(btn_frame, text="Kiểm tra tất cả", command=lambda: check_all_keys(False), bg="#f39c12", fg="white")
        btn_check.pack(side="left", padx=5)
        btn_check_err = Button(btn_frame, text="Kiểm tra key lỗi", command=lambda: check_all_keys(True), bg="#d35400", fg="white")
        btn_check_err.pack(side="left", padx=5)
        btn_auto = Button(btn_frame, text="🔄 Tự động điều chỉnh", command=auto_adjust, bg="#8e44ad", fg="white")
        btn_auto.pack(side="left", padx=5)
        Button(btn_frame, text="Đặt Active", command=set_active, bg="#3498db", fg="white").pack(side="left", padx=5)
        Button(btn_frame, text="Lưu Thứ Tự", command=save_sort_order, bg="#16a085", fg="white").pack(side="left", padx=5)
        Button(btn_frame, text="Xóa Key", command=del_key, bg="#e74c3c", fg="white").pack(side="right", padx=5)

        # === LOG PANEL (packed side=bottom → xuất hiện TRÊN btn_frame) ===
        from tkinter.scrolledtext import ScrolledText as _ST
        frame_log = Frame(top, bd=1, relief="sunken")
        frame_log.pack(side="bottom", fill="x", padx=10, pady=(0, 3))
        _log_hdr = Frame(frame_log, bg="#2c3e50")
        _log_hdr.pack(fill='x')
        Label(_log_hdr, text="📋 Log Kiểm Tra API:", font=("Arial", 9, "bold"), fg="#ecf0f1", bg="#2c3e50", anchor='w').pack(side='left', padx=6, pady=2)
        def _clear_log():
            if _log_box[0]:
                _log_box[0].config(state='normal')
                _log_box[0].delete('1.0', END)
                _log_box[0].config(state='disabled')
        Button(_log_hdr, text="Xóa Log", font=("Arial", 8), command=_clear_log,
               relief="flat", bg="#34495e", fg="#ecf0f1", cursor="hand2", padx=4).pack(side='right', padx=4, pady=2)
        _log_box[0] = _ST(frame_log, height=8, font=("Consolas", 9),
                          bg="#0d1117", fg="#00e676", insertbackground="#00e676",
                          state='disabled', wrap='word', relief='flat')
        _log_box[0].pack(fill='x', pady=0)
        log_key("📋 Log sẵn sàng. Nhấn 'Kiểm tra tất cả' hoặc 'Kiểm tra' từng key để xem tiến độ.")

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

    def _adaptive_output_dir(self):
        out_dir = self.ai_out_var.get().strip()
        if not out_dir:
            messagebox.showerror("Thiếu thư mục xuất", "Hãy chọn Thư mục Xuất trước. Hồ sơ và tiến độ sẽ được lưu riêng tại đó.")
            return ""
        os.makedirs(out_dir, exist_ok=True)
        return out_dir

    def open_adaptive_profile(self):
        out_dir = self._adaptive_output_dir()
        if not out_dir:
            return
        profile = load_profile(out_dir)
        dialog = Toplevel(self.root)
        dialog.title("Hồ sơ học thích nghi")
        dialog.geometry("650x590")
        dialog.transient(self.root)
        dialog.grab_set()
        fields = [
            ("domain", "Chủ đề / lĩnh vực"),
            ("goal", "Mục tiêu đầu ra cụ thể"),
            ("current_level", "Trình độ hiện tại"),
            ("minutes_per_day", "Phút học mỗi ngày"),
            ("available_resources", "Thiết bị, tài liệu, vật liệu sẵn có"),
            ("constraints", "Giới hạn / độ tuổi / an toàn / ngân sách"),
            ("learning_preference", "Cách học mong muốn"),
        ]
        widgets = {}
        for key, label in fields:
            Label(dialog, text=label + ":", anchor="w").pack(fill="x", padx=18, pady=(8, 2))
            if key in {"available_resources", "constraints"}:
                widget = Text(dialog, height=3, wrap="word")
                widget.insert("1.0", str(profile.get(key, "")))
            else:
                widget = Entry(dialog)
                widget.insert(0, str(profile.get(key, "")))
            widget.pack(fill="x", padx=18)
            widgets[key] = widget

        status = Label(dialog, text="", fg="#c0392b", justify="left", wraplength=600)
        status.pack(fill="x", padx=18, pady=8)

        def value_of(key):
            widget = widgets[key]
            return widget.get("1.0", END).strip() if isinstance(widget, Text) else widget.get().strip()

        def save():
            values = default_profile()
            values.update({key: value_of(key) for key, _ in fields})
            try:
                values["minutes_per_day"] = max(5, int(values["minutes_per_day"] or 30))
            except ValueError:
                status.config(text="Phút học mỗi ngày phải là số.")
                return
            saved = save_profile(out_dir, values)
            questions = profile_questions(saved)
            if questions:
                status.config(text="Cần bổ sung trước khi AI cá nhân hóa hoàn toàn:\n" + "\n".join("• " + item["question"] for item in questions))
                return
            self.log_ai("🧠 Đã lưu Course Profile. Lần render kế tiếp sẽ dùng context cá nhân và phản hồi Day trước.")
            dialog.destroy()
            messagebox.showinfo("Đã lưu", "Hồ sơ học đã sẵn sàng. Gemini chỉ hỏi tiếp khi thông tin có thể làm thay đổi Day sau.")

        buttons = Frame(dialog)
        buttons.pack(fill="x", padx=18, pady=10)
        Button(buttons, text="Lưu hồ sơ", command=save, bg="#2ea043", fg="white").pack(side="left")
        Button(buttons, text="Đóng", command=dialog.destroy).pack(side="right")

    def open_day_feedback(self):
        out_dir = self._adaptive_output_dir()
        if not out_dir:
            return
        dialog = Toplevel(self.root)
        dialog.title("Ghi phản hồi sau Day")
        dialog.geometry("590x390")
        dialog.transient(self.root)
        dialog.grab_set()
        Label(dialog, text="Day (ví dụ: Day 1 — Cài Python):", anchor="w").pack(fill="x", padx=18, pady=(15, 2))
        day_entry = Entry(dialog)
        day_entry.pack(fill="x", padx=18)
        Label(dialog, text="Bạn đã làm được gì, lỗi gì, hoặc muốn thay đổi gì?", anchor="w").pack(fill="x", padx=18, pady=(12, 2))
        feedback = Text(dialog, height=9, wrap="word")
        feedback.pack(fill="both", expand=True, padx=18)
        Label(dialog, text="Mức nắm vững (ví dụ: đạt / cần ôn / chưa hiểu):", anchor="w").pack(fill="x", padx=18, pady=(8, 2))
        mastery_entry = Entry(dialog)
        mastery_entry.pack(fill="x", padx=18)

        def save():
            day, note = day_entry.get().strip(), feedback.get("1.0", END).strip()
            if not day or not note:
                messagebox.showerror("Thiếu thông tin", "Cần nhập Day và phản hồi thực tế của bạn.", parent=dialog)
                return
            record_learner_feedback(out_dir, day, note, mastery_entry.get().strip())
            self.log_ai(f"📝 Đã lưu phản hồi {day}. Gemini sẽ dùng nó khi render Day liên quan tiếp theo.")
            dialog.destroy()

        Button(dialog, text="Lưu phản hồi", command=save, bg="#6c3483", fg="white").pack(pady=12)
        
    def open_knowledge_pack(self):
        """Attach a reviewed pack to this course; facts without it stay unverified."""
        out_dir = self._adaptive_output_dir()
        if not out_dir:
            return
        action = messagebox.askyesnocancel(
            "Knowledge Pack",
            "Yes: Chọn knowledge_pack.json đã kiểm chứng.\n"
            "No: Nhập thư mục CSV (sources.csv, heroes.csv, units.csv...).\n"
            "Cancel: Tạo mẫu knowledge_pack.json trống tại Output.",
            parent=self.root,
        )
        if action is True:
            path = filedialog.askopenfilename(title="Chọn Knowledge Pack", filetypes=[("JSON", "*.json")])
            if not path:
                return
        elif action is False:
            folder = filedialog.askdirectory(title="Chọn thư mục CSV Knowledge Pack")
            if not folder:
                return
            path = os.path.join(out_dir, "knowledge_pack.json")
            try:
                import_csv_folder(folder, path, title="Knowledge Pack nhập từ CSV")
            except Exception as exc:
                messagebox.showerror("Không nhập được Pack", str(exc), parent=self.root)
                return
        else:
            path = os.path.join(out_dir, "knowledge_pack.json")
            if not os.path.exists(path):
                with open(path, "w", encoding="utf-8", newline="\n") as handle:
                    json.dump(empty_pack("Knowledge Pack mới"), handle, ensure_ascii=False, indent=2)

        pack = load_pack(path)
        errors = validate_pack(pack)
        if errors:
            messagebox.showerror("Knowledge Pack không hợp lệ", "\n".join(errors[:12]), parent=self.root)
            return
        profile = load_profile(out_dir)
        profile["knowledge_pack_path"] = path
        save_profile(out_dir, profile)
        report = coverage_report(pack)
        summary = ", ".join(
            f"{row['type']}: {row['verified']}/{row['target'] if row['target'] is not None else '?'}"
            for row in report["rows"]
        )
        self.log_ai(f"📚 Đã gắn Knowledge Pack: {path}")
        messagebox.showinfo("Đã gắn Knowledge Pack", "Gemini chỉ được dùng fact có source_id hợp lệ.\n" + summary, parent=self.root)

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
            followup_mode=self.ai_followup_mode_var.get(),
            adaptive_mode=bool(self.ai_adaptive_mode_var.get()),
            generate_visuals=bool(self.ai_generate_visuals_var.get())
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
        
    def stop_ai_worker(self):
        try:
            import auto_ai_worker
            auto_ai_worker.STOP_REQUESTED = True
            if hasattr(self, 'btn_ai_stop'):
                self.btn_ai_stop.config(state="disabled", text="Đang dừng...")
            self.log_ai("🛑 Đã gửi lệnh dừng tiến trình, vui lòng đợi cho đến khi lưu xong session...")
        except Exception as e:
            self.log_ai(f"⚠ Không thể gửi lệnh dừng: {e}")
        
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
        if hasattr(self, 'btn_ai_stop'):
            self.btn_ai_stop.config(state="normal", text="🛑 Dừng lại")
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
                auto_ai_worker.STOP_REQUESTED = False
                auto_ai_worker.run_auto_ai(
                    api_keys, roadmap_path, doc_dir, out_dir, self.log_ai, 
                    force=force, update_keys_cb=update_keys_cb,
                    enable_followup=enable_followup, max_followup=max_followup, start_day=start_day,
                    adaptive_mode=bool(self.ai_adaptive_mode_var.get()),
                    generate_visuals=bool(self.ai_generate_visuals_var.get())
                )
                self.log_ai("🎉 Hoàn thành toàn bộ tiến trình!")
            except Exception as e:
                self.log_ai(f"❌ LỖI NGHIÊM TRỌNG: {str(e)}")
            finally:
                def _enable():
                    self.btn_ai_start.config(state="normal", text="▶ Bắt đầu Sinh Tự Động")
                    if hasattr(self, 'btn_ai_stop'):
                        self.btn_ai_stop.config(state="disabled", text="🛑 Dừng lại")
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
        output_file = filedialog.asksaveasfilename(title="Lưu file mã hóa", defaultextension=".askcpl", filetypes=[("AskCpl Encrypted", "*.askcpl"), ("All Files", "*.*")])
        if not output_file: return
        
        try:
            import crypto_utils
            crypto_utils.encrypt_folder(folder, output_file, pwd)
            messagebox.showinfo("Thành công", f"Đã mã hóa thành công ra file:\n{output_file}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi mã hóa:\n{e}")

    def ex_tool_decrypt(self):
        input_file = filedialog.askopenfilename(title="Chọn file .askcpl", filetypes=[("AskCpl Encrypted", "*.askcpl"), ("All Files", "*.*")])
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
        input_file = filedialog.askopenfilename(title="Chọn file .askcpl bài tập", filetypes=[("AskCpl Encrypted", "*.askcpl"), ("All Files", "*.*")])
        if not input_file: return
        pwd = simpledialog.askstring("Mật khẩu", "Nhập mật khẩu để mở bài tập:", show='*')
        if not pwd: return

        try:
            import crypto_utils, tempfile, os, zipfile, shutil

            temp_dir = os.path.join(tempfile.gettempdir(), "askcpl_workspace")
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)

            # === CHẾ ĐỘ TẢI NHANH: decrypt_to_memory — ưu tiên RAM, tự fallback ra đĩa nếu cần ===
            source, is_memory = crypto_utils.decrypt_to_memory(input_file, pwd)
            if is_memory:
                self._lazy_zip_buffer = source      # io.BytesIO trong RAM
                self.ex_lazy_zip_path = None        # Không có file tạm
            else:
                self._lazy_zip_buffer = None
                self.ex_lazy_zip_path = source      # Đường dẫn temp .zip trên đĩa

            self.ex_current_dir = temp_dir
            self.ex_askcpl_source = input_file
            self.ex_askcpl_password = pwd
            self.ex_deleted_files = set()
            self.btn_save_askcpl.config(state="normal")

            self.ex_lbl_dir.config(text=f"Đang làm việc trên: {os.path.basename(input_file)}")
            self.settings.setdefault("editor", {})
            self.settings["editor"]["ex_dir"] = temp_dir
            update_editor_settings(ex_dir=temp_dir)

            # Giải nén duy nhất file exercises_data.json (cấu hình nhẹ)
            try:
                zf_obj = self._open_lazy_zip()
                if zf_obj:
                    with zf_obj as zf:
                        if 'exercises_data.json' in zf.namelist():
                            zf.extract('exercises_data.json', temp_dir)
            except Exception:
                pass

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
            mode_label = "RAM (Siêu tốc)" if is_memory else "Disk (File lớn)"
            messagebox.showinfo("Đã mở thành công", f"Đã mở bài tập thành công [{mode_label}].\nNhớ bấm 'Lưu lại vào .askcpl' sau khi làm xong!")
        except ValueError as ve:
            messagebox.showerror("Lỗi", str(ve))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Lỗi mở file:\n{e}")

    def _open_lazy_zip(self):
        """Trả về zipfile.ZipFile context manager tự chọn nguồn (BytesIO hoặc đường dẫn).
        Sử dụng dưới dạng:  with self._open_lazy_zip() as zf:  ...
        Trả về None nếu chưa có nguồn zip nào (chế độ thư mục thường).
        """
        import zipfile, os
        buf = getattr(self, '_lazy_zip_buffer', None)
        if buf is not None:
            buf.seek(0)
            return zipfile.ZipFile(buf, 'r')
        path = getattr(self, 'ex_lazy_zip_path', None)
        if path and os.path.exists(path):
            return zipfile.ZipFile(path, 'r')
        return None

    def ex_save_askcpl(self):
        if not hasattr(self, 'ex_askcpl_source') or not self.ex_askcpl_source:
            messagebox.showwarning("Cảnh báo", "Bạn chưa mở file .askcpl nào.")
            return
            
        try:
            import crypto_utils, os
            deleted = getattr(self, 'ex_deleted_files', set())
            buf = getattr(self, '_lazy_zip_buffer', None)
            zip_path = getattr(self, 'ex_lazy_zip_path', None)
            if buf is not None or (zip_path and os.path.exists(zip_path)):
                old_src = buf if buf is not None else zip_path
                crypto_utils.encrypt_from_zip_and_folder(
                    old_src, self.ex_current_dir,
                    self.ex_askcpl_source, self.ex_askcpl_password, deleted)
            else:
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
            # Reset hoàn toàn trạng thái lazy khi mở thư mục thường
            self.ex_lazy_zip_path = None
            self._lazy_zip_buffer = None
            self.ex_deleted_files = set()
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
                fl = fname.lower()
                if not (fl.endswith(".html") and "day" in fl and fl != "index.html" and " exercise.html" not in fl):
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
            files = []
            zf_obj = self._open_lazy_zip()
            if zf_obj:
                with zf_obj as zf:
                    for f in zf.namelist():
                        if '/' not in f: # Root level files
                            fl = f.lower()
                            if fl.endswith(".html") and "day" in fl and fl != "index.html" and " exercise.html" not in fl:
                                files.append(f)
            else:
                for f in os.listdir(self.ex_current_dir):
                    fl = f.lower()
                    if fl.endswith(".html") and "day" in fl and fl != "index.html" and " exercise.html" not in fl:
                        files.append(f)
        except Exception:
            files = []
            
        # Sắp xếp hỗ trợ cả định dạng cũ (day_1) và mới (001_Day)
        import re
        def sort_key(x):
            match = re.match(r"^(\d+)_", x)
            if match:
                return int(match.group(1))
            match = re.search(r"day_(\d+)", x, re.IGNORECASE)
            if match:
                return int(match.group(1)) * 1000
            return 999999
            
        try:
            files.sort(key=sort_key)
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
        
        # --- LAZY EXTRACTION & SCAN ---
        zf_obj = self._open_lazy_zip()
        if zf_obj:
            try:
                with zf_obj as zf:
                    # Tự động giải nén file đang chọn nếu chưa có
                    target_path = os.path.join(self.ex_current_dir, self.ex_current_file)
                    if not os.path.exists(target_path) and self.ex_current_file in zf.namelist():
                        zf.extract(self.ex_current_file, self.ex_current_dir)
                    
                    # Cũng giải nén file archival (nếu có)
                    day_base = os.path.splitext(self.ex_current_file)[0]
                    archival_name = f"exercise/{day_base} exercise.html"
                    archival_path = os.path.join(self.ex_current_dir, archival_name)
                    if not os.path.exists(archival_path) and archival_name in zf.namelist():
                        zf.extract(archival_name, self.ex_current_dir)
            except Exception as e:
                print(f"Lazy extract error: {e}")
        
        # Quét HTML nếu dữ liệu block chưa có (lazy load blocks)
        if self.ex_current_file not in getattr(self, 'ex_blocks_data', {}):
            self.ex_scan_single_file(self.ex_current_file)
            
        self.ex_lbl_current.config(text=f"Đang soạn bài tập cho: {self.ex_current_file}")
        update_editor_settings(ex_file=self.ex_current_file)
        # Reload từ JSON để phản ánh thay đổi từ Web Editor
        self.ex_reload_from_json()
        self.ex_refresh_preview()

    def ex_scan_single_file(self, filename):
        if not self.ex_current_dir: return
        changed = False
        day_base = filename.replace(".html", "")
        
        # 1. Quét archival
        archival_path = os.path.join(self.ex_current_dir, "exercise", f"{day_base} exercise.html")
        if os.path.exists(archival_path):
            try:
                with open(archival_path, "r", encoding="utf-8") as f:
                    html = self._extract_ql_content(f.read())
                if html:
                    self.ex_blocks_data[filename] = [{"type": "wysiwyg", "html": html}]
                    changed = True
            except: pass
            
        # 2. Quét direct
        if not changed:
            direct_path = os.path.join(self.ex_current_dir, filename)
            if os.path.exists(direct_path):
                try:
                    with open(direct_path, "r", encoding="utf-8", errors="ignore") as f:
                        html = self._extract_ql_content(f.read())
                    if html:
                        self.ex_blocks_data[filename] = [{"type": "wysiwyg", "html": html}]
                        changed = True
                except: pass
                
        if changed:
            self.ex_persist_data()
            # Khôi phục vị trí cuộn khi refresh listbox
            if hasattr(self, 'ex_listbox'):
                yview = self.ex_listbox.yview()
                self.ex_refresh_listbox()
                self.ex_listbox.yview_moveto(yview[0])

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
                filename = block.get("filename", "")
                filepath = os.path.join(self.ex_current_dir, "attachments", filename)
                if os.path.exists(filepath):
                    try:
                        os.remove(filepath)
                        if hasattr(self, 'ex_deleted_files'):
                            self.ex_deleted_files.add(f"attachments/{filename}")
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
                    filename = block.get("filename", "")
                    filepath = os.path.join(self.ex_current_dir, "attachments", filename)
                    if os.path.exists(filepath):
                        try:
                            os.remove(filepath)
                            if hasattr(self, 'ex_deleted_files'):
                                self.ex_deleted_files.add(f"attachments/{filename}")
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
        
        # Trong chế độ Lazy: đảm bảo file HTML đã được bung ra thư mục tạm trước khi mở editor
        zf_obj = self._open_lazy_zip()
        if zf_obj:
            try:
                with zf_obj as zf:
                    target_path = os.path.join(self.ex_current_dir, self.ex_current_file)
                    if not os.path.exists(target_path) and self.ex_current_file in zf.namelist():
                        zf.extract(self.ex_current_file, self.ex_current_dir)
                    day_base = os.path.splitext(self.ex_current_file)[0]
                    archival_name = f"exercise/{day_base} exercise.html"
                    archival_path = os.path.join(self.ex_current_dir, archival_name)
                    if not os.path.exists(archival_path) and archival_name in zf.namelist():
                        zf.extract(archival_name, self.ex_current_dir)
            except Exception as e:
                print(f"Advanced editor lazy extract error: {e}")
            
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
