import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, filedialog, scrolledtext
import threading
import json
import os
import time
import sys
from typing import List, Dict
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_manager import ConfigManager, ModelInfo
from key_manager import APIKey, ErrorKind


class OpencodeConfigApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.title("OpenCode Config Manager - Antigravity Style")
        self.geometry("1300x850")
        self.minsize(1100, 750)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.create_widgets()
        self.load_initial_data()

    def create_widgets(self):
        # Header
        header = ctk.CTkFrame(self, height=60, corner_radius=0)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        title = ctk.CTkLabel(header, text="⚙️ OpenCode Config Manager (Antigravity Style)", font=ctk.CTkFont(size=22, weight="bold"))
        title.pack(side="left", padx=20, pady=10)

        refresh_btn = ctk.CTkButton(header, text="🔄 Refresh All", command=self.refresh_all, width=130, height=35)
        refresh_btn.pack(side="right", padx=20, pady=10)

        # Tabview
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        # Tabs
        self.tab_models = self.tabview.add("🤖 Models")
        self.tab_keys = self.tabview.add("🔑 API Keys (Advanced)")
        self.tab_skills = self.tabview.add("🎯 Skills")
        self.tab_rules = self.tabview.add("📋 Rules")
        self.tab_guide = self.tabview.add("📚 Guide")

        self.setup_models_tab()
        self.setup_keys_tab()
        self.setup_skills_tab()
        self.setup_rules_tab()
        self.setup_guide_tab()

        # Status bar
        self.status_var = ctk.StringVar(value="Ready")
        status_bar = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w", font=ctk.CTkFont(size=11))
        status_bar.pack(fill="x", padx=10, pady=(0, 10))

    # ========== MODELS TAB ==========
    def setup_models_tab(self):
        toolbar = ctk.CTkFrame(self.tab_models)
        toolbar.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(toolbar, text="Filter:").pack(side="left", padx=5)
        self.model_filter = ctk.CTkComboBox(toolbar, values=["All", "Free Only", "Paid Only", "Vision Capable", "Free + Vision"],
                                            command=self.filter_models, width=150)
        self.model_filter.pack(side="left", padx=5)
        self.model_filter.set("Free Only")

        ctk.CTkButton(toolbar, text="🔍 Check Model", command=self.check_selected_model).pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="✅ Set as Default", command=self.set_default_model).pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="🧪 Test Model", command=self.test_model).pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="📊 Show Stats", command=self.show_call_stats).pack(side="left", padx=5)

        list_frame = ctk.CTkFrame(self.tab_models)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.model_tree = ctk.CTkScrollableFrame(list_frame)
        self.model_tree.pack(fill="both", expand=True, padx=5, pady=5)

        self.model_rows = []
        self.all_models = []

    # ========== API KEYS TAB (Advanced - Antigravity Style) ==========
    def setup_keys_tab(self):
        # Provider selector
        provider_frame = ctk.CTkFrame(self.tab_keys)
        provider_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(provider_frame, text="Provider:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        self.provider_combo = ctk.CTkComboBox(provider_frame, values=["google", "openrouter", "deepseek", "groq"],
                                              command=self.on_provider_change, width=150)
        self.provider_combo.pack(side="left", padx=5)
        self.provider_combo.set("google")

        ctk.CTkButton(provider_frame, text="➕ Add Key", command=self.add_key_dialog).pack(side="left", padx=5)
        ctk.CTkButton(provider_frame, text="🗑️ Remove Selected", command=self.remove_selected_key).pack(side="left", padx=5)
        ctk.CTkButton(provider_frame, text="🧪 Test Selected", command=self.test_selected_key).pack(side="left", padx=5)
        ctk.CTkButton(provider_frame, text="🌐 Get Key", command=self.open_provider_site).pack(side="left", padx=5)
        ctk.CTkButton(provider_frame, text="📊 Account Health", command=self.show_account_health).pack(side="left", padx=5)

        # Key list with details
        self.keys_list = ctk.CTkScrollableFrame(self.tab_keys)
        self.keys_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.key_items = []

        # Stats panel
        stats_frame = ctk.CTkFrame(self.tab_keys)
        stats_frame.pack(fill="x", padx=10, pady=10)

        self.stats_labels = {}
        for label in ["Total Calls Today", "Accounts", "Active Keys", "Exhausted Keys", "Invalid Keys", "Budget Used"]:
            frame = ctk.CTkFrame(stats_frame)
            frame.pack(side="left", expand=True, fill="x", padx=5, pady=5)
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=10), text_color="gray").pack()
            lbl = ctk.CTkLabel(frame, text="0", font=ctk.CTkFont(size=18, weight="bold"))
            lbl.pack()
            self.stats_labels[label] = lbl

    def on_provider_change(self, value: str):
        self.load_keys_for_provider(value)

    def load_keys_for_provider(self, provider: str):
        keys = self.config_manager.load_keys(provider)
        self.after(0, lambda: self.display_keys(provider, keys))

    def display_keys(self, provider: str, keys: List[Dict]):
        for widget in self.keys_list.winfo_children():
            widget.destroy()
        self.key_items = []

        if not keys:
            ctk.CTkLabel(self.keys_list, text=f"Chưa có key cho {provider}. Click 'Add Key' để thêm.", text_color="gray").pack(pady=20)
            self.update_stats({})
            return

        # Header
        header_frame = ctk.CTkFrame(self.keys_list)
        header_frame.pack(fill="x", padx=2, pady=2)
        headers = ["✓", "Email", "Project ID", "Status", "Calls Today", "Account Calls", "Cooldown", "Last Check", "Error"]
        widths = [30, 180, 120, 80, 80, 100, 100, 120, 250]
        for i, (h, w) in enumerate(zip(headers, widths)):
            lbl = ctk.CTkLabel(header_frame, text=h, font=ctk.CTkFont(weight="bold"), width=w, anchor="w")
            lbl.grid(row=0, column=i, padx=3, pady=2, sticky="w")
        header_frame.grid_columnconfigure(8, weight=1)

        stats = {"total": 0, "accounts": set(), "active": 0, "exhausted": 0, "invalid": 0, "budget": 0}
        now = int(time.time())

        for idx, k in enumerate(keys):
            key_obj = APIKey(
                key=k.get("key", ""),
                email=k.get("email", "unknown"),
                project_id=k.get("project_id", ""),
                status=k.get("status", "active"),
                cooldown_until=k.get("cooldown_until", 0),
                reset_time=k.get("reset_time", 0),
                next_check_time=k.get("next_check_time", 0),
                last_check_time=k.get("last_check_time", 0),
                today_calls=k.get("today_calls", 0),
                today_account_calls=k.get("today_account_calls", 0),
                call_date=k.get("call_date", ""),
                error_msg=k.get("error_msg", "")
            )

            row_frame = ctk.CTkFrame(self.keys_list)
            row_frame.pack(fill="x", padx=2, pady=1)

            var = tk.BooleanVar()
            chk = ctk.CTkCheckBox(row_frame, text="", variable=var, width=25)
            chk.grid(row=0, column=0, padx=3, pady=2)

            # Email
            email_color = "green" if key_obj.status == "active" else ("orange" if key_obj.status == "exhausted" else "red")
            lbl_email = ctk.CTkLabel(row_frame, text=key_obj.email, width=widths[1], anchor="w", text_color=email_color)
            lbl_email.grid(row=0, column=1, padx=3, pady=2, sticky="w")

            # Project ID
            lbl_proj = ctk.CTkLabel(row_frame, text=key_obj.project_id or "-", width=widths[2], anchor="w", text_color="gray")
            lbl_proj.grid(row=0, column=2, padx=3, pady=2, sticky="w")

            # Status
            status_text = {"active": "✅ Active", "exhausted": "⚠ Exhausted", "invalid": "❌ Invalid"}.get(key_obj.status, key_obj.status)
            lbl_status = ctk.CTkLabel(row_frame, text=status_text, width=widths[3], anchor="w", text_color=email_color)
            lbl_status.grid(row=0, column=3, padx=3, pady=2, sticky="w")

            # Calls today
            lbl_calls = ctk.CTkLabel(row_frame, text=str(key_obj.today_calls), width=widths[4], anchor="w")
            lbl_calls.grid(row=0, column=4, padx=3, pady=2, sticky="w")

            # Account calls
            lbl_acct = ctk.CTkLabel(row_frame, text=str(key_obj.today_account_calls), width=widths[5], anchor="w")
            lbl_acct.grid(row=0, column=5, padx=3, pady=2, sticky="w")

            # Cooldown
            cd_text = ""
            if key_obj.cooldown_until > now:
                remaining = (key_obj.cooldown_until - now) // 60
                cd_text = f"{remaining}m"
            lbl_cd = ctk.CTkLabel(row_frame, text=cd_text, width=widths[6], anchor="w", text_color="orange" if cd_text else "gray")
            lbl_cd.grid(row=0, column=6, padx=3, pady=2, sticky="w")

            # Last check
            lc_text = time.strftime("%H:%M:%S", time.localtime(key_obj.last_check_time)) if key_obj.last_check_time else "-"
            lbl_lc = ctk.CTkLabel(row_frame, text=lc_text, width=widths[7], anchor="w", text_color="gray", font=ctk.CTkFont(family="Consolas", size=11))
            lbl_lc.grid(row=0, column=7, padx=3, pady=2, sticky="w")

            # Error
            err_text = key_obj.error_msg[:50] + "..." if len(key_obj.error_msg) > 50 else key_obj.error_msg
            lbl_err = ctk.CTkLabel(row_frame, text=err_text, width=widths[8], anchor="w", text_color="red" if err_text else "gray")
            lbl_err.grid(row=0, column=8, padx=3, pady=2, sticky="w")

            row_frame.grid_columnconfigure(8, weight=1)

            self.key_items.append((var, key_obj, row_frame))

            # Stats
            stats["total"] += key_obj.today_calls
            stats["accounts"].add(key_obj.email.lower())
            if key_obj.status == "active":
                stats["active"] += 1
            elif key_obj.status == "exhausted":
                stats["exhausted"] += 1
            elif key_obj.status == "invalid":
                stats["invalid"] += 1
            stats["budget"] += key_obj.today_account_calls

        self.update_stats(stats)

    def update_stats(self, stats: Dict):
        self.stats_labels["Total Calls Today"].configure(text=str(stats.get("total", 0)))
        self.stats_labels["Accounts"].configure(text=str(len(stats.get("accounts", set()))))
        self.stats_labels["Active Keys"].configure(text=str(stats.get("active", 0)))
        self.stats_labels["Exhausted Keys"].configure(text=str(stats.get("exhausted", 0)))
        self.stats_labels["Invalid Keys"].configure(text=str(stats.get("invalid", 0)))
        self.stats_labels["Budget Used"].configure(text=str(stats.get("budget", 0)))

    def add_key_dialog(self):
        provider = self.provider_combo.get()
        dialog = AddKeyDialog(self, provider)
        result = dialog.get_result()
        if result:
            key, email, project_id = result
            self.config_manager.add_key(provider, key, email, project_id)
            self.load_keys_for_provider(provider)
            messagebox.showinfo("Success", f"Đã thêm key cho {email} ({provider})")

    def remove_selected_key(self):
        provider = self.provider_combo.get()
        selected = [(var, key_obj) for var, key_obj, _ in self.key_items if var.get()]
        if not selected:
            messagebox.showwarning("Warning", "Chưa chọn key nào")
            return
        if messagebox.askyesno("Confirm", f"Xóa {len(selected)} key?"):
            for _, key_obj in selected:
                self.config_manager.remove_key(provider, key_obj)
            self.load_keys_for_provider(provider)

    def test_selected_key(self):
        provider = self.provider_combo.get()
        selected = [(var, key_obj) for var, key_obj, _ in self.key_items if var.get()]
        if not selected:
            messagebox.showwarning("Warning", "Chưa chọn key nào")
            return
        key_obj = selected[0][1]
        self.status_var.set(f"Testing {key_obj.email} ({provider})...")
        threading.Thread(target=self._test_key_thread, args=(provider, key_obj), daemon=True).start()

    def _test_key_thread(self, provider: str, key_obj: APIKey):
        try:
            result = self.config_manager.test_key(provider, key_obj)
            if result.get("ok"):
                self.after(0, lambda: messagebox.showinfo("Test Result", f"✅ Key {key_obj.email} hoạt động!\nModel: {result.get('model', 'N/A')}"))
            else:
                err = result.get("error", {})
                self.after(0, lambda: messagebox.showerror("Test Failed", f"❌ Key {key_obj.email} failed:\n{err.get('message', 'Unknown error')}"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.after(0, lambda: self.status_var.set("Ready"))

    def open_provider_site(self):
        provider = self.provider_combo.get()
        urls = {
            "google": "https://aistudio.google.com/apikey",
            "openrouter": "https://openrouter.ai/keys",
            "deepseek": "https://platform.deepseek.com/api_keys",
            "groq": "https://console.groq.com/keys"
        }
        webbrowser.open(urls.get(provider, "https://google.com"))

    def show_account_health(self):
        provider = self.provider_combo.get()
        pool = self.config_manager.get_key_pool(provider)
        issues = pool.account_health_check()
        if issues:
            messagebox.showwarning("⚠ Account Health Issues", "\n\n".join(issues))
        else:
            messagebox.showinfo("Account Health", "✅ Tất cả account đều tuân thủ quy tắc (≤2 key/account)")

    def show_call_stats(self):
        stats = get_today_call_stats()
        msg = f"📊 Thống kê hôm nay ({stats['date']}):\n"
        msg += f"  Tổng calls: {stats['total']:,}\n"
        for acct, calls in stats.get('accounts', {}).items():
            msg += f"  - {acct}: {calls:,} calls\n"
        messagebox.showinfo("Call Stats", msg)

    # ========== SKILLS TAB ==========
    def setup_skills_tab(self):
        toolbar = ctk.CTkFrame(self.tab_skills)
        toolbar.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(toolbar, text="➕ Add Skill Folder", command=self.add_skill_folder).pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="📝 Create New Skill", command=self.create_new_skill).pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="🗑️ Remove Selected", command=self.remove_skill).pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="📖 View SKILL.md", command=self.view_skill_md).pack(side="left", padx=5)

        self.skills_list = ctk.CTkScrollableFrame(self.tab_skills)
        self.skills_list.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.skill_items = []

    # ========== RULES TAB ==========
    def setup_rules_tab(self):
        toolbar = ctk.CTkFrame(self.tab_rules)
        toolbar.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(toolbar, text="💾 Save Rules", command=self.save_rules).pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="🔄 Reload", command=self.load_rules).pack(side="left", padx=5)
        ctk.CTkButton(toolbar, text="📄 Open workflow_rules.md", command=self.open_workflow_rules).pack(side="left", padx=5)

        self.rules_editor = ctk.CTkTextbox(self.tab_rules, font=ctk.CTkFont(family="Consolas", size=13))
        self.rules_editor.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # ========== GUIDE TAB ==========
    def setup_guide_tab(self):
        guide_text = """
# 📚 OpenCode Free Models & Setup Guide (Antigravity Style)

## 🎯 Provider: opencode (Built-in)
Model free thực sự (đã test):
- nemotron-3-ultra-free ⭐ Mạnh nhất
- nemotron-3.5-lightning-free ⚡ Nhanh
- longcat-2.5-preview-free
- mimo-v2.6-flash-free
- muse-spark-1.3-contributor-free
- space-bunny-free
- step-5-preview-free
- big-pickle (free)

❌ KHÔNG free: gemini-*, gpt-*, claude-*, grok-*, qwen-*, deepseek-* (trên provider opencode)

## 🌐 Provider: Google AI Studio (Free Tier Thực Sự)
**Cách lấy key:** https://aistudio.google.com/apikey

Model free có vision:
- gemini-3.8-flash ⭐ Mới nhất
- gemini-3.5-flash-lite
- gemini-3.1-flash-lite
- gemini-2.5-flash
- gemini-2.5-flash-lite
- Gemma 3/4 (1B, 4B, 12B, 27B)

Giới hạn: 15 RPM, 1.5M tokens/ngày

## 🔄 Provider: OpenRouter (Nhiều Model Free)
**Cách lấy key:** https://openrouter.ai/keys

Model free có vision (có `:free` suffix):
- google/gemma-4-26b-a4b-it:free
- google/gemma-4-31b-it:free
- nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free
- nvidia/nemotron-3-super-120b-a12b:free
- nvidia/nemotron-3-ultra-550b-a55b:free
- openai/gpt-oss-20b:free
- openai/gpt-oss-120b:free

## 🐳 Provider: DeepSeek
**Cách lấy key:** https://platform.deepseek.com/api_keys

Free tier: 50 requests/ngày, 1M tokens
Model: deepseek-chat (V3), deepseek-reasoner (R1)
Cũng có qua OpenRouter: deepseek/deepseek-chat:free

## ⚡ Provider: Groq (Speed King)
**Cách lấy key:** https://console.groq.com/keys

Free tier: Rất hào phóng
Model free: llama-3.3-70b, llama-3.1-8b, qwen-2.5-32b, gemma-7b-it

## 🛡️ Anti-Ban Protection (Tự động trong Key Manager)
1. **Pacing**: 3.5-5.0s + jitter 0.5-1.5s giữa các call
2. **Per-Account Gap**: ≥ 8s giữa 2 call cùng account
3. **Key Rotation**: Round-robin account, luân phiên key
4. **Cooldown**: 
   - 429 Daily → Khóa account 60 phút
   - 429 Rate → Cooldown theo retryDelay (không khóa vĩnh viễn)
   - Model restriction → Khóa account, xoay key
5. **Daily Budget**: 1000 calls/account/ngày (an toàn < 1500 RPD Google)
6. **Max 3 account attempts** per request để tránh đốt pool
7. **Network Keep-Alive**: Tự chờ mạng hồi phục 10 phút
8. **Key Encoding**: ENC: format (reverse + base64) bảo mật
9. **Account Health Check**: Cảnh báo nếu >2 key/account

## 💡 Cách dùng Tab API Keys:
1. Chọn Provider (Google/OpenRouter/DeepSeek/Groq)
2. Add Key: Nhập key, email, project ID
3. Key sẽ được mã hóa ENC: khi lưu
4. Test key trước khi dùng
5. Hệ thống tự động xoay key khi hết quota
        """

        self.guide_textbox = ctk.CTkTextbox(self.tab_guide, font=ctk.CTkFont(family="Consolas", size=12))
        self.guide_textbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.guide_textbox.insert("1.0", guide_text)
        self.guide_textbox.configure(state="disabled")

    # ========== COMMON METHODS ==========
    def load_initial_data(self):
        self.refresh_all()

    def refresh_all(self):
        self.status_var.set("Loading...")
        threading.Thread(target=self._refresh_all_thread, daemon=True).start()

    def _refresh_all_thread(self):
        self.load_models()
        self.load_skills()
        self.load_rules()
        self.load_keys_for_provider("google")
        self.after(0, lambda: self.status_var.set("Ready"))

    # Models
    def load_models(self):
        models = self.config_manager.get_all_models_with_status()
        self.all_models = models
        self.after(0, lambda: self.display_models(models))

    def display_models(self, models: List[ModelInfo]):
        for widget in self.model_tree.winfo_children():
            widget.destroy()
        self.model_rows = []

        header_frame = ctk.CTkFrame(self.model_tree)
        header_frame.pack(fill="x", padx=2, pady=2)
        headers = ["✓", "Model ID", "Provider", "Free", "Vision", "Notes"]
        widths = [40, 300, 100, 60, 60, 400]
        for i, (h, w) in enumerate(zip(headers, widths)):
            lbl = ctk.CTkLabel(header_frame, text=h, font=ctk.CTkFont(weight="bold"), width=w, anchor="w")
            lbl.grid(row=0, column=i, padx=5, pady=2, sticky="w")
        header_frame.grid_columnconfigure(1, weight=1)
        header_frame.grid_columnconfigure(5, weight=1)

        for idx, model in enumerate(models):
            row_frame = ctk.CTkFrame(self.model_tree)
            row_frame.pack(fill="x", padx=2, pady=1)

            var = tk.BooleanVar()
            chk = ctk.CTkCheckBox(row_frame, text="", variable=var, width=30)
            chk.grid(row=0, column=0, padx=5, pady=2)

            lbl_id = ctk.CTkLabel(row_frame, text=model.id, width=widths[1], anchor="w", font=ctk.CTkFont(family="Consolas", size=11))
            lbl_id.grid(row=0, column=1, padx=5, pady=2, sticky="w")

            lbl_prov = ctk.CTkLabel(row_frame, text=model.provider, width=widths[2], anchor="w")
            lbl_prov.grid(row=0, column=2, padx=5, pady=2, sticky="w")

            free_text = "✅ Free" if model.is_free else "❌ Paid"
            free_color = "green" if model.is_free else "red"
            lbl_free = ctk.CTkLabel(row_frame, text=free_text, width=widths[3], anchor="w", text_color=free_color)
            lbl_free.grid(row=0, column=3, padx=5, pady=2, sticky="w")

            vision_text = "👁️ Yes" if model.supports_vision else "❌ No"
            vision_color = "green" if model.supports_vision else "gray"
            lbl_vis = ctk.CTkLabel(row_frame, text=vision_text, width=widths[4], anchor="w", text_color=vision_color)
            lbl_vis.grid(row=0, column=4, padx=5, pady=2, sticky="w")

            lbl_notes = ctk.CTkLabel(row_frame, text=model.notes, width=widths[5], anchor="w", text_color="gray")
            lbl_notes.grid(row=0, column=5, padx=5, pady=2, sticky="w")

            row_frame.grid_columnconfigure(1, weight=1)
            row_frame.grid_columnconfigure(5, weight=1)

            self.model_rows.append((var, model, row_frame))

    def filter_models(self, value: str):
        if value == "All":
            filtered = self.all_models
        elif value == "Free Only":
            filtered = [m for m in self.all_models if m.is_free]
        elif value == "Paid Only":
            filtered = [m for m in self.all_models if not m.is_free]
        elif value == "Vision Capable":
            filtered = [m for m in self.all_models if m.supports_vision]
        elif value == "Free + Vision":
            filtered = [m for m in self.all_models if m.is_free and m.supports_vision]
        else:
            filtered = self.all_models
        self.display_models(filtered)

    def get_selected_model(self) -> ModelInfo:
        for var, model, _ in self.model_rows:
            if var.get():
                return model
        return None

    def check_selected_model(self):
        model = self.get_selected_model()
        if model:
            msg = f"Model: {model.id}\nProvider: {model.provider}\nFree: {'Yes' if model.is_free else 'No'}\nVision: {'Yes' if model.supports_vision else 'No'}\nNotes: {model.notes}"
            messagebox.showinfo("Model Info", msg)
        else:
            messagebox.showwarning("Warning", "No model selected")

    def set_default_model(self):
        model = self.get_selected_model()
        if model:
            self.config_manager.set_current_model(model.id)
            messagebox.showinfo("Success", f"Default model set to: {model.id}")
            self.status_var.set(f"Default model: {model.id}")
        else:
            messagebox.showwarning("Warning", "No model selected")

    def test_model(self):
        model = self.get_selected_model()
        if not model:
            messagebox.showwarning("Warning", "No model selected")
            return
        self.status_var.set(f"Testing {model.id}...")
        threading.Thread(target=self._test_model_thread, args=(model.id,), daemon=True).start()

    def _test_model_thread(self, model_id: str):
        try:
            result = self.config_manager.run_opencode(["run", "ping", "-m", model_id])
            if result.returncode == 0:
                self.after(0, lambda: messagebox.showinfo("Test Result", f"✅ {model_id} works!\n\nOutput: {result.stdout[:200]}"))
            else:
                self.after(0, lambda: messagebox.showerror("Test Failed", f"❌ {model_id} failed:\n{result.stderr[:500]}"))
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.after(0, lambda: self.status_var.set("Ready"))

    # Skills
    def load_skills(self):
        skills = self.config_manager.list_skills()
        self.after(0, lambda: self.display_skills(skills))

    def display_skills(self, skills: List[Dict]):
        for widget in self.skills_list.winfo_children():
            widget.destroy()
        self.skill_items = []

        for skill in skills:
            frame = ctk.CTkFrame(self.skills_list)
            frame.pack(fill="x", padx=5, pady=3)

            var = tk.BooleanVar()
            chk = ctk.CTkCheckBox(frame, text="", variable=var, width=30)
            chk.pack(side="left", padx=5)

            info = ctk.CTkLabel(frame, text=f"📦 {skill['name']}", font=ctk.CTkFont(weight="bold"), anchor="w")
            info.pack(side="left", padx=10, fill="x", expand=True)

            desc = ctk.CTkLabel(frame, text=skill['description'][:80] + "..." if len(skill['description']) > 80 else skill['description'],
                                text_color="gray", anchor="w")
            desc.pack(side="left", padx=10, fill="x", expand=True)

            path_lbl = ctk.CTkLabel(frame, text=skill['path'], text_color="gray", font=ctk.CTkFont(size=11), anchor="w")
            path_lbl.pack(side="left", padx=10, fill="x", expand=True)

            self.skill_items.append((var, skill, frame))

    def add_skill_folder(self):
        folder = filedialog.askdirectory(title="Select Skills Folder")
        if folder:
            skills_json = self.config_manager.opencode_setting / "skills.json"
            data = {"entries": []}
            if skills_json.exists():
                with open(skills_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            if not any(e["path"] == folder for e in data["entries"]):
                data["entries"].append({"path": folder})
                with open(skills_json, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                self.load_skills()
                messagebox.showinfo("Success", f"Added skills folder: {folder}")

    def create_new_skill(self):
        dialog = ctk.CTkInputDialog(text="Enter skill name:", title="New Skill")
        name = dialog.get_input()
        if name:
            skills_dir = self.config_manager.opencode_setting / "skills" / name
            skills_dir.mkdir(parents=True, exist_ok=True)
            skill_md = skills_dir / "SKILL.md"
            template = f"""# Skill: {name}

# Mô tả skill này làm gì

## Trigger
Khi nào skill được kích hoạt

## Workflow
1. Bước 1
2. Bước 2

## References
- File/script tham khảo
"""
            skill_md.write_text(template, encoding='utf-8')
            self.load_skills()
            messagebox.showinfo("Success", f"Created skill: {name}\nEdit {skill_md}")

    def remove_skill(self):
        selected = [(var, skill) for var, skill, _ in self.skill_items if var.get()]
        if not selected:
            messagebox.showwarning("Warning", "No skill selected")
            return
        if messagebox.askyesno("Confirm", f"Remove {len(selected)} skill(s)?"):
            for _, skill in selected:
                import shutil
                shutil.rmtree(skill['path'], ignore_errors=True)
            self.load_skills()

    def view_skill_md(self):
        selected = [(var, skill) for var, skill, _ in self.skill_items if var.get()]
        if not selected:
            messagebox.showwarning("Warning", "No skill selected")
            return
        for _, skill in selected:
            skill_md = Path(skill['path']) / "SKILL.md"
            if skill_md.exists():
                content = skill_md.read_text(encoding='utf-8')
                self.show_text_window(f"SKILL.md - {skill['name']}", content)

    # Rules
    def load_rules(self):
        content = self.config_manager.load_rules()
        self.rules_editor.delete("1.0", "end")
        self.rules_editor.insert("1.0", content)

    def save_rules(self):
        content = self.rules_editor.get("1.0", "end-1c")
        self.config_manager.save_rules(content)
        messagebox.showinfo("Success", "Rules saved!")

    def open_workflow_rules(self):
        workflow_file = self.config_manager.opencode_setting / "rules" / "workflow_rules.md"
        if workflow_file.exists():
            content = workflow_file.read_text(encoding='utf-8')
            self.show_text_window("workflow_rules.md", content)
        else:
            messagebox.showwarning("Warning", "File not found")

    def show_text_window(self, title: str, content: str):
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry("800x600")
        txt = ctk.CTkTextbox(win, font=ctk.CTkFont(family="Consolas", size=13))
        txt.pack(fill="both", expand=True, padx=10, pady=10)
        txt.insert("1.0", content)
        txt.configure(state="disabled")


class AddKeyDialog(ctk.CTkToplevel):
    def __init__(self, parent, provider):
        super().__init__(parent)
        self.title(f"Add API Key - {provider}")
        self.geometry("500x300")
        self.result = None
        self.transient(parent)
        self.grab_set()

        ctk.CTkLabel(self, text=f"Add {provider.upper()} API Key", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=15)

        # Key
        f_key = ctk.CTkFrame(self)
        f_key.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f_key, text="API Key:", width=80).pack(side="left")
        self.key_entry = ctk.CTkEntry(f_key, show="*", width=350)
        self.key_entry.pack(side="left", padx=5)

        # Email
        f_email = ctk.CTkFrame(self)
        f_email.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f_email, text="Email/Name:", width=80).pack(side="left")
        self.email_entry = ctk.CTkEntry(f_email, width=350)
        self.email_entry.pack(side="left", padx=5)
        self.email_entry.insert(0, f"account_{int(time.time())}")

        # Project ID
        f_proj = ctk.CTkFrame(self)
        f_proj.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(f_proj, text="Project ID:", width=80).pack(side="left")
        self.proj_entry = ctk.CTkEntry(f_proj, width=350)
        self.proj_entry.pack(side="left", padx=5)

        # Help
        urls = {
            "google": "https://aistudio.google.com/apikey",
            "openrouter": "https://openrouter.ai/keys",
            "deepseek": "https://platform.deepseek.com/api_keys",
            "groq": "https://console.groq.com/keys"
        }
        ctk.CTkLabel(self, text=f"Lấy key tại: {urls.get(provider, '')}", text_color="blue", cursor="hand2").pack(pady=5)

        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(btn_frame, text="Save", command=self.on_ok).pack(side="left", padx=5, expand=True)
        ctk.CTkButton(btn_frame, text="Cancel", command=self.on_cancel).pack(side="right", padx=5, expand=True)

    def on_ok(self):
        key = self.key_entry.get().strip()
        email = self.email_entry.get().strip()
        project_id = self.proj_entry.get().strip()
        if not key:
            messagebox.showwarning("Warning", "API Key không được để trống")
            return
        if not email:
            messagebox.showwarning("Warning", "Email/Name không được để trống")
            return
        self.result = (key, email, project_id)
        self.destroy()

    def on_cancel(self):
        self.destroy()

    def get_result(self):
        self.wait_window()
        return self.result


def main():
    app = OpencodeConfigApp()
    app.mainloop()


if __name__ == "__main__":
    main()