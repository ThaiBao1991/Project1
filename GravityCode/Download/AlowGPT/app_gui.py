"""
GUI Application for AlowGPT - DPI/SNI Fragmentation Proxy, OpenCode & VSCode Integration
Built with standard Tkinter/TTK (No external dependencies)
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import os
import atexit
import threading
import time
import urllib.request
import urllib.error
from core_engine import AlowGPTProxyServer, SystemProxyManager, VSCodeConfigHelper, CF_WORKER_TEMPLATE

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULT_CONFIG = {
    "port": 7070,
    "mode": "sni_fragment",
    "cf_worker_url": "https://testconnectgpt.gamesvendn02.workers.dev",
    "chunk_size": 40,
    "delay_ms": 30,
    "auto_system_proxy": True,
    "bypass_domains": [
        "chatgpt.com",
        "oaistatic.com",
        "oaiusercontent.com",
        "openai.com",
        "api.openai.com",
        "claude.ai",
        "anthropic.com",
        "api.anthropic.com",
        "deepseek.com",
        "api.deepseek.com",
        "groq.com",
        "api.groq.com"
    ]
}

class AlowGPTApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AlowGPT - Công Cụ Vượt Chặn Trend Micro & Cấu Hình OpenCode / VSCode")
        self.geometry("820x680")
        self.minsize(740, 580)

        # Set modern color palette
        self.bg_color = "#f4f6f9"
        self.card_bg = "#ffffff"
        self.primary_color = "#2563eb"
        self.success_color = "#16a34a"
        self.danger_color = "#dc2626"
        self.purple_color = "#7c3aed"
        self.configure(bg=self.bg_color)

        self.config_data = self.load_config()
        self.proxy_server = None

        self._setup_style()
        self._build_ui()

        # Register exit handlers to guarantee proxy restoration
        atexit.register(self._on_exit_cleanup)
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)

        # Append initial ready log
        self.log_message("Chào mừng bạn đến với AlowGPT! Hỗ trợ OpenCode & VSCode.", "INFO")
        self.log_message("Nhấn 'BẬT PROXY' hoặc dùng Tab 'OpenCode & VSCode' để bắt đầu.", "SUCCESS")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in DEFAULT_CONFIG.items():
                        if k not in data:
                            data[k] = v
                    return data
            except Exception as e:
                print(f"Lỗi đọc config.json: {e}")
        return DEFAULT_CONFIG.copy()

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log_message(f"Không thể lưu cấu hình: {e}", "ERROR")

    def _setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TNotebook", background=self.bg_color, borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[14, 8])
        style.map("TNotebook.Tab", background=[("selected", "#ffffff")], foreground=[("selected", self.primary_color)])

        style.configure("Card.TFrame", background=self.card_bg, relief="flat")
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), background=self.card_bg, foreground="#1e293b")
        style.configure("SubHeader.TLabel", font=("Segoe UI", 9), background=self.card_bg, foreground="#64748b")
        style.configure("TCheckbutton", font=("Segoe UI", 10), background=self.card_bg)
        style.configure("TRadiobutton", font=("Segoe UI", 10), background=self.card_bg)

    def _build_ui(self):
        # 1. Top Card: Main Controls & Status
        top_card = tk.Frame(self, bg=self.card_bg, bd=0, highlightthickness=1, highlightbackground="#e2e8f0", padx=16, pady=14)
        top_card.pack(fill="x", padx=16, pady=(16, 8))

        # Status row
        status_frame = tk.Frame(top_card, bg=self.card_bg)
        status_frame.pack(fill="x", pady=(0, 10))

        self.status_dot = tk.Label(status_frame, text="●", font=("Segoe UI", 18), fg=self.danger_color, bg=self.card_bg)
        self.status_dot.pack(side="left", padx=(0, 6))

        self.status_text = tk.Label(status_frame, text="Trạng Thái: ĐÃ TẮT", font=("Segoe UI", 12, "bold"), fg="#334155", bg=self.card_bg)
        self.status_text.pack(side="left")

        # Port Configuration in Header
        port_frame = tk.Frame(status_frame, bg=self.card_bg)
        port_frame.pack(side="right")

        tk.Label(port_frame, text="Cổng Proxy (Port):", font=("Segoe UI", 10, "bold"), bg=self.card_bg, fg="#334155").pack(side="left", padx=(0, 6))
        self.port_var = tk.StringVar(value=str(self.config_data.get("port", 7070)))
        self.port_entry = ttk.Entry(port_frame, textvariable=self.port_var, width=8, font=("Consolas", 10))
        self.port_entry.pack(side="left", padx=(0, 10))

        # Main Action Button (Toggle ON/OFF)
        btn_frame = tk.Frame(top_card, bg=self.card_bg)
        btn_frame.pack(fill="x", pady=(0, 6))

        self.toggle_btn = tk.Button(
            btn_frame,
            text="🚀  BẬT PROXY VƯỢT CHẶN",
            font=("Segoe UI", 12, "bold"),
            bg=self.success_color,
            fg="#ffffff",
            activebackground="#15803d",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=10,
            command=self.toggle_proxy
        )
        self.toggle_btn.pack(fill="x")

        # System Proxy Checkbox
        self.auto_sys_var = tk.BooleanVar(value=self.config_data.get("auto_system_proxy", True))
        self.sys_check = ttk.Checkbutton(
            top_card,
            text="Tự động áp dụng Proxy cho toàn hệ thống Windows (Chrome, Edge, VSCode tự động nhận)",
            variable=self.auto_sys_var,
            style="TCheckbutton",
            command=self._on_sys_check_changed
        )
        self.sys_check.pack(anchor="w", pady=(8, 0))

        # 2. Tabs Container (Notebook)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=8)

        # Build individual tabs
        self._build_tab_opencode()
        self._build_tab_mode()
        self._build_tab_domains()
        self._build_tab_log()

    def _build_tab_opencode(self):
        tab = tk.Frame(self.notebook, bg=self.card_bg, padx=16, pady=16)
        self.notebook.add(tab, text=" ⚡ OpenCode & VSCode ")

        # Section 1: VSCode 1-Click Auto Setup
        sec1 = tk.LabelFrame(tab, text=" 🛠️ Cấu Hình Tự Động Cho VSCode ", font=("Segoe UI", 10, "bold"), bg=self.card_bg, padx=12, pady=10)
        sec1.pack(fill="x", pady=(0, 14))

        tk.Label(
            sec1,
            text="Tự động thêm cấu hình Proxy vào file settings.json của VSCode để toàn bộ extension (OpenCode, Copilot, Cline) vượt qua Trend Micro:",
            font=("Segoe UI", 9),
            fg="#475569",
            bg=self.card_bg,
            wraplength=700,
            justify="left"
        ).pack(anchor="w", pady=(0, 8))

        btn_row = tk.Frame(sec1, bg=self.card_bg)
        btn_row.pack(fill="x")

        tk.Button(
            btn_row,
            text="⚡  Tự Động Áp Dụng Proxy Vào VSCode",
            font=("Segoe UI", 9, "bold"),
            bg="#dbeafe",
            fg=self.primary_color,
            relief="groove",
            cursor="hand2",
            padx=12,
            pady=6,
            command=self._apply_vscode_proxy
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            btn_row,
            text="📋  Copy Mẫu Cấu Hình VSCode Settings (JSON)",
            font=("Segoe UI", 9),
            bg="#f1f5f9",
            relief="groove",
            cursor="hand2",
            padx=10,
            pady=6,
            command=self._copy_vscode_json
        ).pack(side="left")

        # Section 2: OpenCode API Base URL
        sec2 = tk.LabelFrame(tab, text=" 🌐 Cấu Hình Cho OpenCode / Continue / Cline ", font=("Segoe UI", 10, "bold"), bg=self.card_bg, padx=12, pady=10)
        sec2.pack(fill="x", pady=(0, 14))

        tk.Label(sec2, text="Đường dẫn API Base URL để dán vào OpenCode:", font=("Segoe UI", 9, "bold"), bg=self.card_bg).pack(anchor="w", pady=(0, 4))

        url_box = tk.Frame(sec2, bg=self.card_bg)
        url_box.pack(fill="x", pady=(0, 8))

        self.opencode_base_url_var = tk.StringVar(value=self.get_current_opencode_url())
        self.base_url_entry = ttk.Entry(url_box, textvariable=self.opencode_base_url_var, font=("Consolas", 10))
        self.base_url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Button(
            url_box,
            text="📋  Copy Base URL",
            font=("Segoe UI", 9, "bold"),
            bg=self.primary_color,
            fg="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            command=self._copy_opencode_url
        ).pack(side="right")

        # Section 3: Live API Test
        sec3 = tk.LabelFrame(tab, text=" 🧪 Kiểm Thử Kết Nối OpenCode (Live API Test) ", font=("Segoe UI", 10, "bold"), bg=self.card_bg, padx=12, pady=10)
        sec3.pack(fill="both", expand=True)

        test_row = tk.Frame(sec3, bg=self.card_bg)
        test_row.pack(fill="x", pady=(0, 6))

        tk.Label(test_row, text="API Key (sk-...):", font=("Segoe UI", 9, "bold"), bg=self.card_bg).pack(side="left", padx=(0, 6))
        self.test_key_var = tk.StringVar()
        self.test_key_entry = ttk.Entry(test_row, textvariable=self.test_key_var, show="*", width=28, font=("Consolas", 9))
        self.test_key_entry.pack(side="left", padx=(0, 10))

        tk.Label(test_row, text="Model:", font=("Segoe UI", 9, "bold"), bg=self.card_bg).pack(side="left", padx=(0, 6))
        self.test_model_var = tk.StringVar(value="gpt-4o-mini")
        model_combo = ttk.Combobox(test_row, textvariable=self.test_model_var, values=["gpt-4o-mini", "gpt-4o", "o3-mini", "claude-3-5-sonnet", "deepseek-chat"], width=16)
        model_combo.pack(side="left", padx=(0, 10))

        self.test_btn = tk.Button(
            test_row,
            text="🧪  Gửi Test Prompt",
            font=("Segoe UI", 9, "bold"),
            bg=self.purple_color,
            fg="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            command=self._run_opencode_test
        )
        self.test_btn.pack(side="left")

        # Result box
        self.test_result_text = tk.Text(sec3, height=4, font=("Consolas", 9), bg="#f8fafc", bd=1, relief="solid")
        self.test_result_text.pack(fill="both", expand=True, pady=(4, 0))
        self.test_result_text.insert("end", "Kết quả kiểm thử API sẽ hiển thị tại đây sau khi bạn bấm 'Gửi Test Prompt'...")

    def get_current_opencode_url(self):
        worker_url = self.config_data.get("cf_worker_url", "").strip().rstrip("/")
        if worker_url:
            return f"{worker_url}/v1"
        port = self.config_data.get("port", 7070)
        return f"http://127.0.0.1:{port}/v1"

    def _apply_vscode_proxy(self):
        try:
            port = int(self.port_var.get().strip())
        except ValueError:
            port = 7070

        success, msg = VSCodeConfigHelper.apply_proxy_to_vscode(port=port)
        if success:
            messagebox.showinfo("Thành Công", msg + "\n\nKhởi động lại VSCode hoặc reload window (Ctrl+R) để áp dụng ngay!")
            self.log_message(f"Đã tự động cấu hình Proxy cho VSCode (127.0.0.1:{port}).", "SUCCESS")
        else:
            messagebox.showerror("Lỗi", msg)
            self.log_message(f"Lỗi cấu hình VSCode: {msg}", "ERROR")

    def _copy_vscode_json(self):
        try:
            port = int(self.port_var.get().strip())
        except ValueError:
            port = 7070

        snippet = f'"{{"http.proxy": "http://127.0.0.1:{port}", "http.proxyStrictSSL": false}}"'
        formatted = json.dumps({"http.proxy": f"http://127.0.0.1:{port}", "http.proxyStrictSSL": False}, indent=4)
        self.clipboard_clear()
        self.clipboard_append(formatted)
        messagebox.showinfo("Đã Copy", "Đã copy cấu hình JSON vào Clipboard!\nBạn có thể dán vào settings.json của VSCode.")
        self.log_message("Đã copy mẫu cấu hình VSCode settings.json vào Clipboard.", "INFO")

    def _copy_opencode_url(self):
        url = self.opencode_base_url_var.get().strip()
        self.clipboard_clear()
        self.clipboard_append(url)
        messagebox.showinfo("Đã Copy", f"Đã copy Base URL:\n{url}\n\nDán vào phần cài đặt Base URL trong OpenCode!")
        self.log_message(f"Đã copy OpenCode Base URL: {url}", "INFO")

    def _run_opencode_test(self):
        key = self.test_key_var.get().strip()
        if not key:
            messagebox.showwarning("Thiếu API Key", "Vui lòng nhập API Key (sk-...) để kiểm thử!")
            return

        base_url = self.opencode_base_url_var.get().strip().rstrip("/")
        model = self.test_model_var.get().strip()

        self.test_btn.config(state="disabled", text="⏳ Đang gửi...")
        self.test_result_text.delete("1.0", "end")
        self.test_result_text.insert("end", f"Đang gửi request kiểm thử tới: {base_url}/chat/completions ...\n")

        def test_thread():
            try:
                target_endpoint = f"{base_url}/chat/completions"
                payload = json.dumps({
                    "model": model,
                    "messages": [{"role": "user", "content": "Xin chào! Bạn là mô hình gì? Trả lời ngắn gọn 1 câu."}],
                    "max_tokens": 60
                }).encode("utf-8")

                req = urllib.request.Request(
                    target_endpoint,
                    data=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {key}",
                        "User-Agent": "OpenCode-Tester/1.0"
                    }
                )

                start_t = time.time()
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    elapsed = time.time() - start_t
                    reply = data["choices"][0]["message"]["content"]
                    result_str = f"✅ KẾT NỐI THÀNH CÔNG ({elapsed:.2f}s)!\nPhản hồi từ AI ({model}):\n{reply}"
                    self.after(0, self._show_test_result, result_str, "SUCCESS")
            except Exception as e:
                err_msg = f"❌ LỖI KẾT NỐI: {e}\n(Vui lòng kiểm tra lại API Key hoặc đảm bảo Cloudflare Worker đang hoạt động)"
                self.after(0, self._show_test_result, err_msg, "ERROR")

        threading.Thread(target=test_thread, daemon=True).start()

    def _show_test_result(self, text: str, level: str):
        self.test_btn.config(state="normal", text="🧪  Gửi Test Prompt")
        self.test_result_text.delete("1.0", "end")
        self.test_result_text.insert("end", text)
        self.log_message(f"Kết quả kiểm thử OpenCode API: {level}", level)

    def _build_tab_mode(self):
        tab = tk.Frame(self.notebook, bg=self.card_bg, padx=16, pady=16)
        self.notebook.add(tab, text=" ⚙️ Thiết Lập Chế Độ ")

        # Mode Selection
        self.mode_var = tk.StringVar(value=self.config_data.get("mode", "sni_fragment"))

        lbl = tk.Label(tab, text="Chọn Phương Thức Vượt Chặn:", font=("Segoe UI", 11, "bold"), bg=self.card_bg, fg="#1e293b")
        lbl.pack(anchor="w", pady=(0, 10))

        # Mode 1: SNI Fragment
        rb1 = ttk.Radiobutton(
            tab,
            text="Chế độ 1: Phân mảnh gói tin SNI (Mặc định - 100% Thuần máy, không cần server ngoài)",
            value="sni_fragment",
            variable=self.mode_var,
            style="TRadiobutton",
            command=self._on_mode_changed
        )
        rb1.pack(anchor="w", pady=(0, 4))

        desc1 = tk.Label(
            tab,
            text="   ↳ Cắt đôi gói tin SSL Handshake khiến Trend Micro không đọc được domain 'chatgpt.com'.",
            font=("Segoe UI", 9),
            fg="#64748b",
            bg=self.card_bg
        )
        desc1.pack(anchor="w", pady=(0, 10))

        # Advanced Settings for Mode 1
        self.m1_frame = tk.LabelFrame(tab, text=" Tùy Chỉnh Phân Mảnh ", font=("Segoe UI", 9, "bold"), bg=self.card_bg, padx=12, pady=8)
        self.m1_frame.pack(fill="x", padx=16, pady=(0, 16))

        row1 = tk.Frame(self.m1_frame, bg=self.card_bg)
        row1.pack(fill="x", pady=4)
        tk.Label(row1, text="Kích thước cắt (Chunk size byte):", font=("Segoe UI", 9), bg=self.card_bg).pack(side="left")
        self.chunk_var = tk.IntVar(value=self.config_data.get("chunk_size", 40))
        ttk.Spinbox(row1, from_=10, to=100, textvariable=self.chunk_var, width=6).pack(side="left", padx=8)

        tk.Label(row1, text="Độ trễ giữa 2 mảnh (Delay ms):", font=("Segoe UI", 9), bg=self.card_bg).pack(side="left", padx=(16, 0))
        self.delay_var = tk.IntVar(value=self.config_data.get("delay_ms", 30))
        ttk.Spinbox(row1, from_=5, to=200, textvariable=self.delay_var, width=6).pack(side="left", padx=8)

        # Mode 2: Cloudflare Worker
        rb2 = ttk.Radiobutton(
            tab,
            text="Chế độ 2: Cloudflare Worker Relay (Vượt chặn 100% cho API & Web)",
            value="cf_worker",
            variable=self.mode_var,
            style="TRadiobutton",
            command=self._on_mode_changed
        )
        rb2.pack(anchor="w", pady=(8, 4))

        # Worker Frame
        self.m2_frame = tk.LabelFrame(tab, text=" Cấu Hình Cloudflare Worker ", font=("Segoe UI", 9, "bold"), bg=self.card_bg, padx=12, pady=8)
        self.m2_frame.pack(fill="x", padx=16, pady=(0, 10))

        url_row = tk.Frame(self.m2_frame, bg=self.card_bg)
        url_row.pack(fill="x", pady=4)
        tk.Label(url_row, text="URL Worker của bạn:", font=("Segoe UI", 9, "bold"), bg=self.card_bg).pack(side="left")
        self.cf_url_var = tk.StringVar(value=self.config_data.get("cf_worker_url", "https://testconnectgpt.gamesvendn02.workers.dev"))
        self.cf_entry = ttk.Entry(url_row, textvariable=self.cf_url_var, font=("Consolas", 9))
        self.cf_entry.pack(side="left", fill="x", expand=True, padx=8)

        btn_copy = tk.Button(
            self.m2_frame,
            text="📋  Copy Mã Nguồn Worker Mẫu (Dán vào dash.cloudflare.com)",
            font=("Segoe UI", 9, "bold"),
            bg="#f1f5f9",
            fg=self.primary_color,
            relief="groove",
            cursor="hand2",
            padx=10,
            pady=4,
            command=self._copy_worker_code
        )
        btn_copy.pack(anchor="w", pady=6)

        self._update_mode_ui_state()

    def _build_tab_domains(self):
        tab = tk.Frame(self.notebook, bg=self.card_bg, padx=16, pady=16)
        self.notebook.add(tab, text=" 🌐 Danh Sách Tên Miền ")

        desc = tk.Label(
            tab,
            text="Các tên miền dưới đây sẽ được kích hoạt cơ chế vượt chặn khi bạn truy cập:",
            font=("Segoe UI", 9),
            fg="#475569",
            bg=self.card_bg
        )
        desc.pack(anchor="w", pady=(0, 8))

        # List and controls
        content_frame = tk.Frame(tab, bg=self.card_bg)
        content_frame.pack(fill="both", expand=True)

        self.domain_listbox = tk.Listbox(content_frame, font=("Consolas", 10), bd=1, relief="solid", selectmode="single")
        self.domain_listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=self.domain_listbox.yview)
        scrollbar.pack(side="left", fill="y")
        self.domain_listbox.config(yscrollcommand=scrollbar.set)

        # Load domains
        for d in self.config_data.get("bypass_domains", []):
            self.domain_listbox.insert("end", d)

        # Buttons on right
        btn_box = tk.Frame(content_frame, bg=self.card_bg, padx=12)
        btn_box.pack(side="left", fill="y")

        self.new_domain_var = tk.StringVar()
        ttk.Entry(btn_box, textvariable=self.new_domain_var, width=20, font=("Consolas", 9)).pack(pady=(0, 6))

        tk.Button(
            btn_box, text="➕ Thêm Tên Miền", font=("Segoe UI", 9), bg="#e2e8f0", relief="flat", cursor="hand2", command=self._add_domain
        ).pack(fill="x", pady=2)

        tk.Button(
            btn_box, text="➖ Xóa Đã Chọn", font=("Segoe UI", 9), bg="#fee2e2", fg=self.danger_color, relief="flat", cursor="hand2", command=self._delete_domain
        ).pack(fill="x", pady=2)

        tk.Button(
            btn_box, text="🔄 Đặt Lại Mặc Định", font=("Segoe UI", 9), bg="#e2e8f0", relief="flat", cursor="hand2", command=self._reset_domains
        ).pack(fill="x", pady=(16, 2))

    def _build_tab_log(self):
        tab = tk.Frame(self.notebook, bg=self.card_bg, padx=12, pady=12)
        self.notebook.add(tab, text=" 📜 Nhật Ký Hoạt Động (Live Log) ")

        top_log = tk.Frame(tab, bg=self.card_bg)
        top_log.pack(fill="x", pady=(0, 6))

        tk.Label(top_log, text="Ghi nhận hoạt động truyền tải mạng:", font=("Segoe UI", 9, "bold"), bg=self.card_bg, fg="#475569").pack(side="left")

        tk.Button(
            top_log, text="🗑️ Xóa Log", font=("Segoe UI", 8), bg="#f1f5f9", relief="groove", cursor="hand2", command=self._clear_log
        ).pack(side="right")

        self.log_text = scrolledtext.ScrolledText(tab, font=("Consolas", 9), bg="#0f172a", fg="#f8fafc", insertbackground="white", bd=0)
        self.log_text.pack(fill="both", expand=True)

        # Tags for colored logs
        self.log_text.tag_config("INFO", foreground="#38bdf8")
        self.log_text.tag_config("SUCCESS", foreground="#4ade80")
        self.log_text.tag_config("WARNING", foreground="#fbbf24")
        self.log_text.tag_config("ERROR", foreground="#f87171")

    def log_message(self, message: str, level: str = "INFO"):
        timestamp = time.strftime("%H:%M:%S")
        formatted = f"[{timestamp}] [{level}] {message}\n"
        self.after(0, self._append_log_threadsafe, formatted, level)

    def _append_log_threadsafe(self, text: str, level: str):
        try:
            self.log_text.insert("end", text, level)
            self.log_text.see("end")
        except Exception:
            pass

    def _clear_log(self):
        self.log_text.delete("1.0", "end")

    def _on_mode_changed(self):
        self._update_mode_ui_state()
        self._sync_config_from_ui()

    def _update_mode_ui_state(self):
        mode = self.mode_var.get()
        if mode == "sni_fragment":
            for child in self.m1_frame.winfo_children():
                for sub in child.winfo_children():
                    try:
                        sub.configure(state="normal")
                    except Exception:
                        pass
            self.cf_entry.configure(state="disabled")
        else:
            self.cf_entry.configure(state="normal")

    def _on_sys_check_changed(self):
        self._sync_config_from_ui()
        if self.proxy_server and self.proxy_server.is_running:
            port = int(self.port_var.get().strip())
            if self.auto_sys_var.get():
                SystemProxyManager.set_system_proxy(port=port)
                self.log_message("Đã kích hoạt Windows System Proxy.", "INFO")
            else:
                SystemProxyManager.unset_system_proxy()
                self.log_message("Đã tắt Windows System Proxy.", "WARNING")

    def _copy_worker_code(self):
        self.clipboard_clear()
        self.clipboard_append(CF_WORKER_TEMPLATE)
        messagebox.showinfo("Đã Copy", "Đã copy mã nguồn Worker vào Clipboard!\nBạn chỉ cần tạo Worker trên Cloudflare và dán mã này vào.")
        self.log_message("Đã copy mã nguồn Cloudflare Worker mẫu vào Clipboard.", "INFO")

    def _add_domain(self):
        domain = self.new_domain_var.get().strip().lower()
        if domain:
            if domain not in self.domain_listbox.get(0, "end"):
                self.domain_listbox.insert("end", domain)
                self.new_domain_var.set("")
                self._sync_config_from_ui()
                self.log_message(f"Đã thêm tên miền bypass: {domain}", "INFO")

    def _delete_domain(self):
        selected = self.domain_listbox.curselection()
        if selected:
            val = self.domain_listbox.get(selected[0])
            self.domain_listbox.delete(selected[0])
            self._sync_config_from_ui()
            self.log_message(f"Đã xóa tên miền bypass: {val}", "INFO")

    def _reset_domains(self):
        self.domain_listbox.delete(0, "end")
        for d in DEFAULT_CONFIG["bypass_domains"]:
            self.domain_listbox.insert("end", d)
        self._sync_config_from_ui()
        self.log_message("Đã khôi phục danh sách tên miền mặc định.", "INFO")

    def _sync_config_from_ui(self):
        try:
            self.config_data["port"] = int(self.port_var.get().strip())
        except ValueError:
            self.config_data["port"] = 7070

        self.config_data["mode"] = self.mode_var.get()
        self.config_data["cf_worker_url"] = self.cf_url_var.get().strip()
        self.config_data["chunk_size"] = self.chunk_var.get()
        self.config_data["delay_ms"] = self.delay_var.get()
        self.config_data["auto_system_proxy"] = self.auto_sys_var.get()
        self.config_data["bypass_domains"] = list(self.domain_listbox.get(0, "end"))
        self.save_config()
        self.opencode_base_url_var.set(self.get_current_opencode_url())

    def toggle_proxy(self):
        if self.proxy_server and self.proxy_server.is_running:
            self.stop_proxy()
        else:
            self.start_proxy()

    def start_proxy(self):
        self._sync_config_from_ui()
        port = self.config_data["port"]
        mode = self.config_data["mode"]
        chunk_size = self.config_data["chunk_size"]
        delay_ms = self.config_data["delay_ms"]
        domains = self.config_data["bypass_domains"]
        cf_url = self.config_data["cf_worker_url"]

        self.proxy_server = AlowGPTProxyServer(
            host="127.0.0.1",
            port=port,
            mode=mode,
            chunk_size=chunk_size,
            delay_ms=delay_ms,
            bypass_domains=domains,
            cf_worker_url=cf_url,
            log_callback=self.log_message
        )

        success = self.proxy_server.start()
        if success:
            self.status_dot.config(fg=self.success_color)
            self.status_text.config(text=f"Trạng Thái: ĐANG BẬT (127.0.0.1:{port})", fg=self.success_color)
            self.toggle_btn.config(
                text="⏹️  TẮT PROXY (HOÀN TRẢ MẠNG GỐC)",
                bg=self.danger_color,
                activebackground="#b91c1c"
            )
            self.port_entry.config(state="disabled")

            if self.auto_sys_var.get():
                SystemProxyManager.set_system_proxy(port=port)
                self.log_message(f"Đã tự động gán System Proxy Windows -> 127.0.0.1:{port}", "SUCCESS")
        else:
            messagebox.showerror("Lỗi Khởi Động", f"Không thể khởi động Proxy trên cổng {port}!\nVui lòng đổi sang cổng khác (ví dụ: 7071, 7890, 8899).")

    def stop_proxy(self):
        if self.proxy_server:
            self.proxy_server.stop()
            self.proxy_server = None

        SystemProxyManager.unset_system_proxy()
        self.status_dot.config(fg=self.danger_color)
        self.status_text.config(text="Trạng Thái: ĐÃ TẮT", fg="#334155")
        self.toggle_btn.config(
            text="🚀  BẬT PROXY VƯỢT CHẶN",
            bg=self.success_color,
            activebackground="#15803d"
        )
        self.port_entry.config(state="normal")
        self.log_message("Đã tắt Proxy và khôi phục cấu hình mạng mặc định.", "WARNING")

    def _on_exit_cleanup(self):
        """Always restore Windows system proxy to normal on exit."""
        SystemProxyManager.unset_system_proxy()
        if self.proxy_server:
            self.proxy_server.stop()

    def _on_window_close(self):
        self._on_exit_cleanup()
        self.destroy()


def run_app():
    app = AlowGPTApp()
    app.mainloop()

if __name__ == "__main__":
    run_app()
