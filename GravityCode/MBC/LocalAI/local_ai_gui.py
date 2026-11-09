"""
Local AI Control Panel (Tkinter Dark Mode)
Quan ly Bat/Tat va cau hinh ket noi cho Local AI (llama.cpp + Dolphin Qwen)
Ho tro: Intel Core Ultra 3 205 (8 threads) + Intel Vulkan
"""
import os
import sys
import time
import subprocess
import threading
import webbrowser
import shutil
import tkinter as tk
from tkinter import ttk, messagebox

# Dinh nghia cac duong dan chuan
BASE_DIR_D = "D:\\LocalAI"
BIN_DIR = os.path.join(BASE_DIR_D, "bin")
MODELS_DIR = os.path.join(BASE_DIR_D, "models")
LLAMA_SERVER_EXE = os.path.join(BIN_DIR, "llama-server.exe")
DOWNLOADS_DIR = os.path.join(os.path.expanduser("~"), "Downloads")

PORT = 8080
API_URL = f"http://127.0.0.1:{PORT}/v1"
WEB_URL = f"http://127.0.0.1:{PORT}"
DEFAULT_API_KEY = "local"

# Mau sac giao dien Dark Mode hien dai
BG_DARK = "#181825"
BG_CARD = "#1e1e2e"
BG_INPUT = "#313244"
TEXT_MAIN = "#cdd6f4"
TEXT_MUTED = "#a6adc8"
ACCENT_BLUE = "#89b4fa"
ACCENT_GREEN = "#a6e3a1"
ACCENT_RED = "#f38ba8"
ACCENT_YELLOW = "#f9e2af"
BORDER_COLOR = "#45475a"

class LocalAIGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Local AI Control Panel - Intel Core Ultra")
        self.root.geometry("540x620")
        self.root.minsize(500, 580)
        self.root.configure(bg=BG_DARK)
        
        self.server_process = None
        self.is_running = False
        
        # Tao thu muc neu chua co
        os.makedirs(MODELS_DIR, exist_ok=True)
        os.makedirs(BIN_DIR, exist_ok=True)
        
        self._build_ui()
        self.refresh_models()
        self._check_downloads_folder(silent=True)
        
        # Xử lý đóng cửa sổ an toàn
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        # 1. Header Card
        header_frame = tk.Frame(self.root, bg=BG_CARD, padx=16, pady=12, highlightthickness=1, highlightbackground=BORDER_COLOR)
        header_frame.pack(fill="x", padx=16, pady=(16, 10))
        
        title_lbl = tk.Label(header_frame, text="🤖 LOCAL AI CONTROL PANEL", font=("Segoe UI", 14, "bold"), fg=ACCENT_BLUE, bg=BG_CARD)
        title_lbl.pack(anchor="w")
        
        sub_lbl = tk.Label(header_frame, text="Tối ưu phần cứng: Intel Core Ultra 3 (8 luồng) + Intel Vulkan", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=BG_CARD)
        sub_lbl.pack(anchor="w", pady=(2, 0))

        # 2. Status & Big Action Button Card
        action_frame = tk.Frame(self.root, bg=BG_CARD, padx=16, pady=16, highlightthickness=1, highlightbackground=BORDER_COLOR)
        action_frame.pack(fill="x", padx=16, pady=6)
        
        status_row = tk.Frame(action_frame, bg=BG_CARD)
        status_row.pack(fill="x", pady=(0, 12))
        
        tk.Label(status_row, text="Trạng thái:", font=("Segoe UI", 10), fg=TEXT_MUTED, bg=BG_CARD).pack(side="left")
        
        self.status_indicator = tk.Label(status_row, text="● ĐÃ TẮT (Offline)", font=("Segoe UI", 10, "bold"), fg=ACCENT_RED, bg=BG_CARD)
        self.status_indicator.pack(side="left", padx=8)

        # Nut Bat/Tat Server
        self.btn_toggle = tk.Button(
            action_frame, 
            text="🟢 BẬT AI SERVER", 
            font=("Segoe UI", 12, "bold"),
            bg="#2ecc71", 
            fg="#ffffff",
            activebackground="#27ae60",
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            pady=8,
            command=self.toggle_server
        )
        self.btn_toggle.pack(fill="x")

        # 3. Model Selector Card
        model_frame = tk.Frame(self.root, bg=BG_CARD, padx=16, pady=12, highlightthickness=1, highlightbackground=BORDER_COLOR)
        model_frame.pack(fill="x", padx=16, pady=6)
        
        model_title_row = tk.Frame(model_frame, bg=BG_CARD)
        model_title_row.pack(fill="x", pady=(0, 6))
        
        tk.Label(model_title_row, text="📦 Chọn Mô Hình (GGUF):", font=("Segoe UI", 10, "bold"), fg=TEXT_MAIN, bg=BG_CARD).pack(side="left")
        
        btn_refresh = tk.Button(model_title_row, text="🔄 Quét lại", font=("Segoe UI", 8), bg=BG_INPUT, fg=TEXT_MAIN, relief="flat", cursor="hand2", command=self.refresh_models)
        btn_refresh.pack(side="right")
        
        self.model_var = tk.StringVar()
        self.model_dropdown = ttk.Combobox(model_frame, textvariable=self.model_var, state="readonly", font=("Segoe UI", 9))
        self.model_dropdown.pack(fill="x", pady=(0, 4))
        self.model_dropdown.bind("<<ComboboxSelected>>", self.on_model_selected)

        # 4. Connection Info Card (Cho AnythingLLM / Cline)
        info_frame = tk.Frame(self.root, bg=BG_CARD, padx=16, pady=12, highlightthickness=1, highlightbackground=BORDER_COLOR)
        info_frame.pack(fill="x", padx=16, pady=6)
        
        tk.Label(info_frame, text="🔑 THÔNG SỐ KẾT NỐI (Dùng cho AnythingLLM / Cline):", font=("Segoe UI", 10, "bold"), fg=ACCENT_YELLOW, bg=BG_CARD).pack(anchor="w", pady=(0, 8))
        
        self.entry_url = self._create_copy_row(info_frame, "Base URL", API_URL)
        self.entry_key = self._create_copy_row(info_frame, "API Key", DEFAULT_API_KEY)
        self.entry_model_name = self._create_copy_row(info_frame, "Model ID", "dolphin-2.9.2-qwen2-7b")

        # 5. Quick Actions Row
        quick_frame = tk.Frame(self.root, bg=BG_DARK)
        quick_frame.pack(fill="x", padx=16, pady=12)
        
        btn_web = tk.Button(quick_frame, text="🌐 Mở Web Chat", font=("Segoe UI", 9, "bold"), bg=BG_INPUT, fg=ACCENT_BLUE, relief="flat", cursor="hand2", padx=10, pady=6, command=self.open_web_chat)
        btn_web.pack(side="left", expand=True, fill="x", padx=(0, 6))
        
        btn_folder = tk.Button(quick_frame, text="📁 Mở Thư Mục Models", font=("Segoe UI", 9), bg=BG_INPUT, fg=TEXT_MAIN, relief="flat", cursor="hand2", padx=10, pady=6, command=self.open_models_folder)
        btn_folder.pack(side="left", expand=True, fill="x", padx=(6, 0))

    def _create_copy_row(self, parent, label_text, default_val):
        row = tk.Frame(parent, bg=BG_CARD)
        row.pack(fill="x", pady=3)
        
        tk.Label(row, text=f"{label_text}:", width=10, anchor="w", font=("Segoe UI", 9), fg=TEXT_MUTED, bg=BG_CARD).pack(side="left")
        
        entry = tk.Entry(row, font=("Segoe UI", 9), bg=BG_INPUT, fg=TEXT_MAIN, relief="flat", insertbackground=TEXT_MAIN)
        entry.insert(0, default_val)
        entry.configure(state="readonly")
        entry.pack(side="left", fill="x", expand=True, padx=(4, 6))
        
        btn_copy = tk.Button(row, text="📋 Copy", font=("Segoe UI", 8), bg=BG_INPUT, fg=ACCENT_BLUE, relief="flat", cursor="hand2", command=lambda: self.copy_to_clipboard(entry.get()))
        btn_copy.pack(side="right")
        return entry

    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        messagebox.showinfo("Đã sao chép", f"Đã chép vào bộ nhớ tạm:\n{text}")

    def refresh_models(self):
        models = [f for f in os.listdir(MODELS_DIR) if f.lower().endswith(".gguf")]
        if models:
            self.model_dropdown["values"] = models
            self.model_var.set(models[0])
            self._update_model_id(models[0])
        else:
            self.model_dropdown["values"] = ["(Chưa có file .gguf trong D:\\LocalAI\\models)"]
            self.model_var.set("(Chưa có file .gguf trong D:\\LocalAI\\models)")

    def on_model_selected(self, event=None):
        selected = self.model_var.get()
        if selected and not selected.startswith("("):
            self._update_model_id(selected)

    def _update_model_id(self, filename):
        # Rut gon ten model lam ID cho de nhin
        clean_name = filename.replace(".Q4_K_M.gguf", "").replace(".gguf", "")
        self.entry_model_name.configure(state="normal")
        self.entry_model_name.delete(0, tk.END)
        self.entry_model_name.insert(0, clean_name)
        self.entry_model_name.configure(state="readonly")

    def _check_downloads_folder(self, silent=False):
        if not os.path.exists(DOWNLOADS_DIR):
            return
        downloaded_ggufs = [f for f in os.listdir(DOWNLOADS_DIR) if f.lower().endswith(".gguf")]
        for f in downloaded_ggufs:
            src = os.path.join(DOWNLOADS_DIR, f)
            dest = os.path.join(MODELS_DIR, f)
            ask = messagebox.askyesno(
                "Phát hiện Model trong Downloads",
                f"Tìm thấy file model mới:\n{f}\n\nBạn có muốn chuyển tự động sang D:\\LocalAI\\models để tiết kiệm ổ C không?"
            )
            if ask:
                try:
                    shutil.move(src, dest)
                    messagebox.showinfo("Thành công", f"Đã chuyển model vào D:\\LocalAI\\models\\{f}")
                    self.refresh_models()
                except Exception as e:
                    messagebox.showerror("Lỗi chuyển file", str(e))

    def toggle_server(self):
        if self.is_running:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        selected_model = self.model_var.get()
        if not selected_model or selected_model.startswith("("):
            # Kiem tra xem co file trong Downloads khong
            self._check_downloads_folder()
            selected_model = self.model_var.get()
            if not selected_model or selected_model.startswith("("):
                messagebox.showwarning("Chưa có Model", "Vui lòng chép file model .gguf vào thư mục:\nD:\\LocalAI\\models\\ trước khi bật server!")
                return
        
        model_full_path = os.path.join(MODELS_DIR, selected_model)
        if not os.path.exists(LLAMA_SERVER_EXE):
            messagebox.showerror("Thiếu bộ chạy", f"Không tìm thấy file llama-server.exe tại:\n{LLAMA_SERVER_EXE}")
            return

        cmd = [
            LLAMA_SERVER_EXE,
            "-m", model_full_path,
            "-c", "8192",
            "-np", "1",
            "-t", "8",
            "--host", "127.0.0.1",
            "--port", str(PORT)
        ]

        self.status_indicator.configure(text="● ĐANG NẠP MODEL VÀO RAM...", fg=ACCENT_YELLOW)
        self.btn_toggle.configure(text="⏳ Đang khởi động...", state="disabled")

        def _run():
            try:
                # Chay an cua so console
                startupinfo = None
                if sys.platform == "win32":
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = subprocess.SW_HIDE

                self.server_process = subprocess.Popen(
                    cmd,
                    cwd=BASE_DIR_D,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    startupinfo=startupinfo,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
                
                # Vong lap cho server nap xong Model vao RAM (toi da 30s)
                import urllib.request
                is_ready = False
                for _ in range(40):
                    if self.server_process.poll() is not None:
                        break
                    try:
                        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/v1/models", timeout=1) as resp:
                            if resp.status == 200:
                                is_ready = True
                                break
                    except Exception:
                        time.sleep(0.5)

                if is_ready:
                    self.is_running = True
                    self.root.after(0, self._update_ui_started)
                else:
                    self.is_running = False
                    self.root.after(0, lambda: self._update_ui_stopped("Khởi động thất bại"))
            except Exception as e:
                self.is_running = False
                self.root.after(0, lambda: messagebox.showerror("Lỗi khởi chạy", str(e)))

        threading.Thread(target=_run, daemon=True).start()

    def _update_ui_started(self):
        self.status_indicator.configure(text=f"● ĐANG CHẠY (Cổng {PORT})", fg=ACCENT_GREEN)
        self.btn_toggle.configure(text="🔴 TẮT AI SERVER", bg=ACCENT_RED, activebackground="#e06c75", state="normal")
        messagebox.showinfo("Đã Bật Local AI", f"Server đã sẵn sàng tại:\n{API_URL}\n\nBạn có thể kết nối từ AnythingLLM, Cline hoặc mở Web Chat!")

    def stop_server(self):
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=3)
            except Exception:
                try:
                    self.server_process.kill()
                except Exception:
                    pass
            self.server_process = None
        
        self.is_running = False
        self._update_ui_stopped()

    def _update_ui_stopped(self, text="● ĐÃ TẮT (Offline)"):
        self.status_indicator.configure(text=text, fg=ACCENT_RED)
        self.btn_toggle.configure(text="🟢 BẬT AI SERVER", bg="#2ecc71", activebackground="#27ae60", state="normal")

    def open_web_chat(self):
        if not self.is_running:
            ans = messagebox.askyesno("Server chưa bật", "Server AI hiện đang tắt. Bạn có muốn bật server ngay bây giờ không?")
            if ans:
                self.start_server()
                self.root.after(2500, lambda: webbrowser.open(WEB_URL))
            return
        webbrowser.open(WEB_URL)

    def open_models_folder(self):
        os.startfile(MODELS_DIR)

    def on_close(self):
        if self.is_running:
            if messagebox.askyesno("Thoát", "Server AI đang chạy. Bạn có muốn tắt server và thoát không?"):
                self.stop_server()
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = LocalAIGUI(root)
    root.mainloop()

