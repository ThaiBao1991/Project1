#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SkillRuleApp - Trung Tâm Quản Lý & Đồng Bộ Kỹ Năng / Quy Chuẩn Toàn Cục
Hệ thống: Google Antigravity & AI Coding Assistants
Giao diện: CustomTkinter 60fps Zero-Lag Dark Mode (Catppuccin Mocha)
"""

import os
import sys
import time
import shutil
import queue
import threading
import subprocess
from datetime import datetime

# Đảm bảo UTF-8 trên Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ─── Tự động kiểm tra và cài đặt thư viện cần thiết ─────────────────────────────
REQUIRED_PACKAGES = {
    'customtkinter': 'customtkinter>=5.2.0',
}

def check_and_install_packages():
    missing = []
    for module_name, pip_name in REQUIRED_PACKAGES.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(pip_name)

    if not missing:
        return

    print(f"[*] Đang tự động cài đặt thư viện cần thiết: {', '.join(missing)}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", *missing])
        print("[*] Cài đặt thành công!")
    except Exception:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        cmd = f"python -m pip install --user {' '.join(missing)}"
        messagebox.showerror(
            "Lỗi Thiếu Thư Viện",
            f"Ứng dụng thiếu thư viện: {', '.join(missing)}\n\n"
            f"Vui lòng mở Terminal và chạy lệnh sau:\n{cmd}"
        )
        sys.exit(1)

check_and_install_packages()

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

# ─── Bảng màu Dark Mode Catppuccin Mocha ─────────────────────────────────────────
PALETTE = {
    "bg": "#181825",            # Base Crust
    "card": "#1e1e2e",          # Surface
    "card_alt": "#24273a",      # Surface Alt
    "border": "#313244",        # Border
    "text": "#cdd6f4",          # Text Main
    "text_muted": "#a6adc8",    # Text Muted
    "accent": "#89b4fa",        # Blue Accent
    "accent_hover": "#b4befe",
    "success": "#a6e3a1",       # Green
    "success_hover": "#94e2d5",
    "warning": "#f9e2af",       # Yellow
    "danger": "#f38ba8",        # Red
    "danger_hover": "#eba0ac",
    "purple": "#cba6f7",        # Mauve / Purple
    "tree_bg": "#181825",
    "tree_fg": "#cdd6f4",
    "tree_select": "#3b4261",
    "tree_header": "#1e1e2e",
    "tree_header_fg": "#89b4fa"
}

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
GRAVITY_CODE_DIR = os.path.dirname(CURRENT_DIR)
USER_HOME = os.path.expanduser("~")
GEMINI_CONFIG_DIR = os.path.join(USER_HOME, ".gemini", "config")
WORKSPACE_AGENTS_DIR = os.path.join(GRAVITY_CODE_DIR, ".agents")

SOURCE_SKILLS = os.path.join(CURRENT_DIR, "skills")
SOURCE_RULES = os.path.join(CURRENT_DIR, "rules")
SYNC_SCRIPT = os.path.join(CURRENT_DIR, "sync_skills_rules.py")


class SkillRuleApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Skill & Rule Hub — Trình Quản Lý & Đồng Bộ Toàn Cục")
        self.geometry("1240 x 780")
        self.minsize(1050, 650)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        self.configure(fg_color=PALETTE["bg"])

        self.items_data = []      # Danh sách toàn bộ items
        self.filtered_items = []  # Danh sách sau khi lọc
        self.selected_item = None
        self.log_queue = queue.Queue()
        self.is_busy = False

        self.setup_ui()
        self.setup_treeview_style()
        self.load_data()
        self.poll_log_queue()

    def setup_ui(self):
        # ── 1. Top Header Bar ──────────────────────────────────────────────
        self.header_frame = ctk.CTkFrame(self, fg_color=PALETTE["card"], corner_radius=10, height=75)
        self.header_frame.pack(fill="x", padx=15, pady=(15, 10))
        self.header_frame.pack_propagate(False)

        # Title & Subtitle
        title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=15, pady=10)

        lbl_title = ctk.CTkLabel(
            title_box,
            text="🧭 SKILL & RULE HUB",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=PALETTE["accent"]
        )
        lbl_title.pack(anchor="w")

        self.lbl_subtitle = ctk.CTkLabel(
            title_box,
            text="Hệ Thống Quản Lý & Đồng Bộ Kỹ Năng / Quy Chuẩn Toàn Cục (GravityCode & ~/.gemini)",
            font=ctk.CTkFont(size=12),
            text_color=PALETTE["text_muted"]
        )
        self.lbl_subtitle.pack(anchor="w")

        # Action Buttons on Header
        btn_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        btn_box.pack(side="right", padx=15, pady=12)

        self.btn_push = ctk.CTkButton(
            btn_box,
            text="🚀 ĐỒNG BỘ TẤT CẢ (Push-All)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2e7d32",
            hover_color="#388e3c",
            width=210,
            height=38,
            command=self.run_push_all
        )
        self.btn_push.pack(side="left", padx=6)

        self.btn_harvest = ctk.CTkButton(
            btn_box,
            text="🔍 QUÉT THU HOẠCH",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#1565c0",
            hover_color="#1976d2",
            width=160,
            height=38,
            command=self.run_harvest
        )
        self.btn_harvest.pack(side="left", padx=6)

        self.btn_add = ctk.CTkButton(
            btn_box,
            text="➕ THÊM MỚI",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#6a1b9a",
            hover_color="#7b1fa2",
            width=120,
            height=38,
            command=self.open_add_dialog
        )
        self.btn_add.pack(side="left", padx=6)

        self.btn_open_folder = ctk.CTkButton(
            btn_box,
            text="📁 MỞ THƯ MỤC",
            font=ctk.CTkFont(size=13),
            fg_color=PALETTE["border"],
            hover_color="#45475a",
            width=120,
            height=38,
            command=lambda: os.startfile(CURRENT_DIR) if sys.platform == "win32" else None
        )
        self.btn_open_folder.pack(side="left", padx=6)

        # ── 2. Search & Filter Bar ─────────────────────────────────────────
        self.filter_frame = ctk.CTkFrame(self, fg_color="transparent", height=42)
        self.filter_frame.pack(fill="x", padx=15, pady=(0, 10))

        # Search Entry
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_data())
        self.entry_search = ctk.CTkEntry(
            self.filter_frame,
            textvariable=self.search_var,
            placeholder_text="🔎 Tìm kiếm theo tên kỹ năng, quy tắc, nội dung...",
            font=ctk.CTkFont(size=13),
            fg_color=PALETTE["card"],
            border_color=PALETTE["border"],
            height=36,
            width=480
        )
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Category Segments
        self.filter_category = "Tất cả"
        self.seg_category = ctk.CTkSegmentedButton(
            self.filter_frame,
            values=["Tất cả", "Kỹ năng (Skills)", "Quy tắc (Rules)"],
            font=ctk.CTkFont(size=12, weight="bold"),
            selected_color=PALETTE["accent"],
            selected_hover_color=PALETTE["accent_hover"],
            unselected_color=PALETTE["card"],
            height=36,
            command=self.on_category_changed
        )
        self.seg_category.set("Tất cả")
        self.seg_category.pack(side="right")

        # ── 3. Main Split View (Left: Tree, Right: Detail) ──────────────────
        self.main_split = ctk.CTkFrame(self, fg_color="transparent")
        self.main_split.pack(fill="both", expand=True, padx=15, pady=0)

        # Left Container (Treeview)
        self.left_pane = ctk.CTkFrame(self.main_split, fg_color=PALETTE["card"], corner_radius=10, width=440)
        self.left_pane.pack(side="left", fill="both", padx=(0, 10))
        self.left_pane.pack_propagate(False)

        # Left Header
        self.lbl_list_count = ctk.CTkLabel(
            self.left_pane,
            text="Danh Sách (0 mục)",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=PALETTE["accent"]
        )
        self.lbl_list_count.pack(anchor="w", padx=12, pady=(10, 6))

        # Treeview Frame
        tree_container = tk.Frame(self.left_pane, bg=PALETTE["tree_bg"])
        tree_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("type", "name", "global_status", "ws_status")
        self.tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show="headings",
            selectmode="browse",
            style="Custom.Treeview"
        )
        self.tree.heading("type", text="Loại")
        self.tree.heading("name", text="Tên Mục")
        self.tree.heading("global_status", text="Global")
        self.tree.heading("ws_status", text="WS")

        self.tree.column("type", width=70, anchor="center")
        self.tree.column("name", width=220, anchor="w")
        self.tree.column("global_status", width=55, anchor="center")
        self.tree.column("ws_status", width=55, anchor="center")

        tree_scroll = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        # Right Container (Detail Viewer)
        self.right_pane = ctk.CTkFrame(self.main_split, fg_color=PALETTE["card"], corner_radius=10)
        self.right_pane.pack(side="right", fill="both", expand=True)

        # Right Pane Header
        self.right_header = ctk.CTkFrame(self.right_pane, fg_color=PALETTE["card_alt"], corner_radius=8, height=65)
        self.right_header.pack(fill="x", padx=12, pady=12)
        self.right_header.pack_propagate(False)

        self.lbl_detail_title = ctk.CTkLabel(
            self.right_header,
            text="Chọn một kỹ năng hoặc quy tắc từ danh sách bên trái",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=PALETTE["text"]
        )
        self.lbl_detail_title.pack(side="left", padx=15, pady=8)

        self.right_btn_box = ctk.CTkFrame(self.right_header, fg_color="transparent")
        self.right_btn_box.pack(side="right", padx=10, pady=10)

        self.btn_copy = ctk.CTkButton(
            self.right_btn_box,
            text="📋 Sao Chép",
            width=90,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color="#313244",
            hover_color="#45475a",
            command=self.copy_content
        )
        self.btn_copy.pack(side="left", padx=4)

        self.btn_open_external = ctk.CTkButton(
            self.right_btn_box,
            text="✏️ Mở File Ngoài",
            width=110,
            height=32,
            font=ctk.CTkFont(size=12),
            fg_color="#313244",
            hover_color="#45475a",
            command=self.open_file_external
        )
        self.btn_open_external.pack(side="left", padx=4)

        # Detail Textbox (Readonly viewer)
        self.txt_content = ctk.CTkTextbox(
            self.right_pane,
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color="#11111b",
            text_color="#cdd6f4",
            corner_radius=8,
            wrap="word"
        )
        self.txt_content.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # ── 4. Bottom Status & Log Bar ─────────────────────────────────────
        self.status_bar = ctk.CTkFrame(self, fg_color=PALETTE["card"], corner_radius=8, height=36)
        self.status_bar.pack(fill="x", padx=15, pady=(8, 12))
        self.status_bar.pack_propagate(False)

        self.lbl_status = ctk.CTkLabel(
            self.status_bar,
            text="Sẵn sàng.",
            font=ctk.CTkFont(size=12),
            text_color=PALETTE["text_muted"]
        )
        self.lbl_status.pack(side="left", padx=12)

        self.lbl_time = ctk.CTkLabel(
            self.status_bar,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=PALETTE["text_muted"]
        )
        self.lbl_time.pack(side="right", padx=12)

    def setup_treeview_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Custom.Treeview",
            background=PALETTE["tree_bg"],
            foreground=PALETTE["tree_fg"],
            fieldbackground=PALETTE["tree_bg"],
            rowheight=30,
            font=("Segoe UI", 10),
            borderwidth=0
        )
        style.configure(
            "Custom.Treeview.Heading",
            background=PALETTE["tree_header"],
            foreground=PALETTE["tree_header_fg"],
            font=("Segoe UI", 10, "bold"),
            borderwidth=0
        )
        style.map(
            "Custom.Treeview",
            background=[("selected", PALETTE["tree_select"])],
            foreground=[("selected", "#ffffff")]
        )
        self.tree.tag_configure("skill_tag", foreground="#89b4fa")
        self.tree.tag_configure("rule_tag", foreground="#cba6f7")

    def load_data(self):
        self.items_data.clear()

        gemini_skills = set(os.listdir(os.path.join(GEMINI_CONFIG_DIR, "skills"))) if os.path.exists(os.path.join(GEMINI_CONFIG_DIR, "skills")) else set()
        gemini_rules = set(os.listdir(os.path.join(GEMINI_CONFIG_DIR, "rules"))) if os.path.exists(os.path.join(GEMINI_CONFIG_DIR, "rules")) else set()

        ws_skills = set(os.listdir(os.path.join(WORKSPACE_AGENTS_DIR, "skills"))) if os.path.exists(os.path.join(WORKSPACE_AGENTS_DIR, "skills")) else set()
        ws_rules = set(os.listdir(os.path.join(WORKSPACE_AGENTS_DIR, "rules"))) if os.path.exists(os.path.join(WORKSPACE_AGENTS_DIR, "rules")) else set()

        # 1. Load Skills
        if os.path.exists(SOURCE_SKILLS):
            for s in sorted(os.listdir(SOURCE_SKILLS)):
                s_path = os.path.join(SOURCE_SKILLS, s)
                if os.path.isdir(s_path):
                    skill_md = os.path.join(s_path, "SKILL.md")
                    if os.path.exists(skill_md):
                        g_st = "✓" if s in gemini_skills else "✗"
                        w_st = "✓" if s in ws_skills else "✗"
                        self.items_data.append({
                            "type": "Skill",
                            "name": s,
                            "path": skill_md,
                            "folder": s_path,
                            "global_status": g_st,
                            "ws_status": w_st
                        })

        # 2. Load Rules
        if os.path.exists(SOURCE_RULES):
            for r in sorted(os.listdir(SOURCE_RULES)):
                r_path = os.path.join(SOURCE_RULES, r)
                if os.path.isfile(r_path) and r.endswith(".md"):
                    g_st = "✓" if r in gemini_rules else "✗"
                    w_st = "✓" if r in ws_rules else "✗"
                    self.items_data.append({
                        "type": "Rule",
                        "name": r,
                        "path": r_path,
                        "folder": SOURCE_RULES,
                        "global_status": g_st,
                        "ws_status": w_st
                    })

        self.filter_data()
        self.update_header_stats()

    def update_header_stats(self):
        skill_cnt = sum(1 for x in self.items_data if x["type"] == "Skill")
        rule_cnt = sum(1 for x in self.items_data if x["type"] == "Rule")
        now_str = datetime.now().strftime("%H:%M:%S")
        self.lbl_subtitle.configure(
            text=f"Tổng số: {skill_cnt} Kỹ Năng (Skills) | {rule_cnt} Quy Tắc (Rules)  —  Cập nhật lúc {now_str}"
        )

    def on_category_changed(self, value):
        self.filter_category = value
        self.filter_data()

    def filter_data(self):
        keyword = self.search_var.get().strip().lower()
        self.tree.delete(*self.tree.get_children())
        self.filtered_items.clear()

        for item in self.items_data:
            # Check Category
            if self.filter_category == "Kỹ năng (Skills)" and item["type"] != "Skill":
                continue
            if self.filter_category == "Quy tắc (Rules)" and item["type"] != "Rule":
                continue

            # Check Keyword
            if keyword:
                if keyword not in item["name"].lower():
                    # Tìm trong nội dung file nếu từ khóa không khớp ở tên
                    try:
                        with open(item["path"], "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read().lower()
                        if keyword not in content:
                            continue
                    except Exception:
                        continue

            self.filtered_items.append(item)
            tag = "skill_tag" if item["type"] == "Skill" else "rule_tag"
            self.tree.insert(
                "",
                "end",
                values=(item["type"], item["name"], item["global_status"], item["ws_status"]),
                tags=(tag,)
            )

        self.lbl_list_count.configure(text=f"Danh Sách ({len(self.filtered_items)} mục)")

        # Auto select first item if available
        if self.filtered_items and not self.selected_item:
            first_id = self.tree.get_children()[0]
            self.tree.selection_set(first_id)
            self.show_item_detail(self.filtered_items[0])

    def on_tree_select(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        item_vals = self.tree.item(sel[0])["values"]
        if not item_vals:
            return
        name = str(item_vals[1])
        for it in self.filtered_items:
            if it["name"] == name:
                self.show_item_detail(it)
                break

    def on_tree_double_click(self, event):
        self.open_file_external()

    def show_item_detail(self, item):
        self.selected_item = item
        prefix = "🛠️ Skill: " if item["type"] == "Skill" else "📜 Rule: "
        self.lbl_detail_title.configure(text=f"{prefix}{item['name']}")

        try:
            with open(item["path"], "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            self.txt_content.configure(state="normal")
            self.txt_content.delete("1.0", "end")
            self.txt_content.insert("1.0", content)
            self.txt_content.configure(state="disabled")
            self.lbl_status.configure(text=f"Đang xem: {item['path']}")
        except Exception as e:
            self.txt_content.configure(state="normal")
            self.txt_content.delete("1.0", "end")
            self.txt_content.insert("1.0", f"Lỗi đọc file: {e}")
            self.txt_content.configure(state="disabled")

    def copy_content(self):
        if not self.selected_item:
            return
        try:
            with open(self.selected_item["path"], "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            self.clipboard_clear()
            self.clipboard_append(content)
            self.lbl_status.configure(text=f"✅ Đã sao chép nội dung '{self.selected_item['name']}' vào Clipboard!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể sao chép: {e}")

    def open_file_external(self):
        if not self.selected_item:
            return
        path = self.selected_item["path"]
        if os.path.exists(path) and sys.platform == "win32":
            os.startfile(path)

    def run_push_all(self):
        if self.is_busy:
            return
        self.is_busy = True
        self.btn_push.configure(state="disabled", text="⏳ Đang đồng bộ...")
        self.lbl_status.configure(text="🚀 Đang thực hiện Push-All ra ~/.gemini/config và .agents...")

        def worker():
            try:
                cmd = [sys.executable, SYNC_SCRIPT, "--push-all"]
                res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
                self.log_queue.put(("push_done", res.stdout))
            except Exception as e:
                self.log_queue.put(("error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def run_harvest(self):
        if self.is_busy:
            return
        self.is_busy = True
        self.btn_harvest.configure(state="disabled", text="⏳ Đang quét...")
        self.lbl_status.configure(text="🔍 Đang rà soát và thu hoạch kỹ năng từ mọi dự án con...")

        def worker():
            try:
                cmd = [sys.executable, SYNC_SCRIPT, "--harvest"]
                res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
                self.log_queue.put(("harvest_done", res.stdout))
            except Exception as e:
                self.log_queue.put(("error", str(e)))

        threading.Thread(target=worker, daemon=True).start()

    def open_add_dialog(self):
        dialog = AddItemDialog(self)
        dialog.grab_set()

    def poll_log_queue(self):
        try:
            while True:
                msg_type, content = self.log_queue.get_nowait()
                self.is_busy = False
                self.btn_push.configure(state="normal", text="🚀 ĐỒNG BỘ TẤT CẢ (Push-All)")
                self.btn_harvest.configure(state="normal", text="🔍 QUÉT THU HOẠCH")

                if msg_type == "push_done":
                    self.load_data()
                    self.lbl_status.configure(text="✨ Đồng bộ toàn cục Push-All thành công 100%!")
                    messagebox.showinfo("Đồng Bộ Thành Công", "Đã cập nhật toàn bộ Skills & Rules vào ~/.gemini/config và .agents!")
                elif msg_type == "harvest_done":
                    self.load_data()
                    self.lbl_status.configure(text="🌾 Đã hoàn tất quét và thu hoạch các dự án!")
                    messagebox.showinfo("Thu Hoạch Hoàn Tất", "Đã quét các dự án con và cập nhật vào SKILL_RULE!")
                elif msg_type == "error":
                    self.lbl_status.configure(text=f"❌ Lỗi: {content}")
                    messagebox.showerror("Lỗi Thực Thi", content)
        except queue.Empty:
            pass

        self.after(200, self.poll_log_queue)


class AddItemDialog(ctk.CTkToplevel):
    def __init__(self, parent: SkillRuleApp):
        super().__init__(parent)
        self.parent = parent
        self.title("➕ Thêm Kỹ Năng Hoặc Quy Tắc Mới")
        self.geometry("540 x 420")
        self.configure(fg_color=PALETTE["bg"])
        self.resizable(False, False)

        lbl_head = ctk.CTkLabel(
            self,
            text="Tạo Mới Kỹ Năng / Quy Tắc Chuẩn",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=PALETTE["accent"]
        )
        lbl_head.pack(padx=20, pady=(20, 10), anchor="w")

        # Choice type
        lbl_type = ctk.CTkLabel(self, text="Chọn Loại:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_type.pack(padx=20, pady=(5, 2), anchor="w")

        self.type_var = tk.StringVar(value="Skill")
        self.seg_type = ctk.CTkSegmentedButton(
            self,
            values=["Skill", "Rule"],
            variable=self.type_var,
            selected_color=PALETTE["accent"],
            selected_hover_color=PALETTE["accent_hover"],
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.seg_type.pack(fill="x", padx=20, pady=(0, 10))

        # Name entry
        lbl_name = ctk.CTkLabel(self, text="Tên Định Danh (ví dụ: my_new_skill hoặc my_rule.md):", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_name.pack(padx=20, pady=(5, 2), anchor="w")

        self.entry_name = ctk.CTkEntry(self, placeholder_text="Tên định danh (chữ thường, gạch dưới)...", height=36)
        self.entry_name.pack(fill="x", padx=20, pady=(0, 10))

        # Description entry
        lbl_desc = ctk.CTkLabel(self, text="Mô Tả / Ngữ Cảnh Kích Hoạt:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_desc.pack(padx=20, pady=(5, 2), anchor="w")

        self.entry_desc = ctk.CTkEntry(self, placeholder_text="Mô tả chức năng...", height=36)
        self.entry_desc.pack(fill="x", padx=20, pady=(0, 20))

        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=10)

        btn_cancel = ctk.CTkButton(
            btn_frame,
            text="Hủy",
            fg_color=PALETTE["border"],
            hover_color="#45475a",
            width=100,
            command=self.destroy
        )
        btn_cancel.pack(side="left")

        btn_save = ctk.CTkButton(
            btn_frame,
            text="💾 Tạo & Lưu Ngay",
            fg_color="#2e7d32",
            hover_color="#388e3c",
            width=160,
            command=self.save_new_item
        )
        btn_save.pack(side="right")

    def save_new_item(self):
        kind = self.type_var.get()
        name = self.entry_name.get().strip()
        desc = self.entry_desc.get().strip() or "Mô tả kỹ năng/quy tắc."

        if not name:
            messagebox.showwarning("Thiếu Thông Tin", "Vui lòng nhập tên định danh!")
            return

        name = name.replace(" ", "_")

        if kind == "Skill":
            skill_dir = os.path.join(SOURCE_SKILLS, name)
            os.makedirs(skill_dir, exist_ok=True)
            skill_md = os.path.join(skill_dir, "SKILL.md")
            content = f"""---
name: {name}
description: {desc}
---

# {name.replace('_', ' ').title()}

## 1. Mục Đích & Tổng Quan
{desc}

## 2. Hướng Dẫn Thực Hiện
...

## 3. Best Practices & Edge Cases
...
"""
            with open(skill_md, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            if not name.endswith(".md"):
                name = f"{name}.md"
            rule_path = os.path.join(SOURCE_RULES, name)
            content = f"""# {name.replace('.md', '').replace('_', ' ').title()} Standards

## 1. Tổng Quan & Phạm Vi Áp Dụng
{desc}

## 2. Quy Chuẩn Kỹ Thuật
- ...

## 3. Checklist Tuân Thủ
- [ ] ...
"""
            with open(rule_path, "w", encoding="utf-8") as f:
                f.write(content)

        # Tự động push-all luôn
        self.destroy()
        self.parent.run_push_all()


if __name__ == "__main__":
    app = SkillRuleApp()
    app.mainloop()

