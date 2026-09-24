# -*- coding: utf-8 -*-
"""
Module: question_browser.py
Mục đích: Cửa sổ popup để duyệt, xem, chỉnh sửa và xuất câu hỏi từ questions_bank.
Giao diện 3 vùng:
  - Trái  : Danh sách câu hỏi (checkbox chọn/bỏ, filter theo thư mục)
  - Giữa  : Xem chi tiết câu hỏi đang chọn
  - Phải  : Form chỉnh sửa inline (nội dung, 4 lựa chọn, đáp án, toggle ◎)
Nút "📤 Xuất Word từ câu đã chọn" → lưu JSON sửa riêng → build exam/answer doc.
"""

import os
import sys
import json
import glob
import copy
import re
import threading
from typing import List, Dict, Any, Optional

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk

try:
    from exam_word_merger import build_exam_doc, build_answer_doc
except ImportError:
    build_exam_doc = None
    build_answer_doc = None

try:
    from generate_rutgon import should_exclude_question, parse_requirements_text
except ImportError:
    should_exclude_question = None
    parse_requirements_text = None

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BANK_BASE = os.path.join(ROOT_DIR, "KetQua", "questions_bank")
OUTPUT_DIR = os.path.join(ROOT_DIR, "KetQua")
CONFIG_PATH = os.path.join(ROOT_DIR, "config.json")

ORANGE = "#f97316"
GREEN = "#10b981"
BLUE = "#3b82f6"
RED = "#ef4444"
DARK_BG = "#0f172a"
CARD_BG = "#1e293b"
PANEL_BG = "#1f2937"
TEXT_MAIN = "#f1f5f9"
TEXT_DIM = "#94a3b8"


class QuestionBrowser(ctk.CTkToplevel):
    """Cửa sổ trình duyệt và chỉnh sửa câu hỏi."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("🔍 Trình Duyệt & Chỉnh Sửa Câu Hỏi — MBC DeThi")
        self.geometry("1500x900")
        self.minsize(1200, 700)
        ctk.set_appearance_mode("dark")

        # ── Dữ liệu nội bộ ──────────────────────────────────────────────────
        self._all_q_items: List[Dict] = []      # [{folder, fname, q_data, checked, edited}]
        self._filtered_items: List[Dict] = []   # subset sau khi filter
        self._current_item: Optional[Dict] = None
        self._selected_idx: Optional[int] = None  # index trong _filtered_items

        self._config: Dict = self._load_config()
        self._available_folders: List[str] = self._get_available_folders()
        self._selected_file_filter: str = "(Tất cả file)"
        self._combo_files: Optional[ctk.CTkComboBox] = None

        # ── Xây dựng UI ─────────────────────────────────────────────────────
        self._build_ui()

        # Tải dữ liệu ngay
        self.after(100, self._load_all_questions)

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _load_config(self) -> Dict:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _get_available_folders(self) -> List[str]:
        if not os.path.isdir(BANK_BASE):
            return []
        return sorted([
            d for d in os.listdir(BANK_BASE)
            if os.path.isdir(os.path.join(BANK_BASE, d))
        ])

    def _load_all_questions(self, folders: Optional[List[str]] = None):
        """Đọc tất cả JSON từ questions_bank và nạp vào danh sách."""
        self._all_q_items.clear()
        target_folders = folders or self._available_folders

        global_counter = 0
        for folder_name in target_folders:
            bank_dir = os.path.join(BANK_BASE, folder_name)
            if not os.path.isdir(bank_dir):
                continue
            json_files = sorted(glob.glob(os.path.join(bank_dir, "*.json")))
            for jf in json_files:
                fname = os.path.basename(jf)
                try:
                    with open(jf, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    continue

                doc_title = data.get("doc_title", fname.replace(".json", ""))
                doc_code  = data.get("doc_code", "")

                for q in data.get("questions", []):
                    global_counter += 1
                    item = {
                        "global_idx": global_counter,
                        "folder":     folder_name,
                        "fname":      fname,
                        "doc_title":  doc_title,
                        "doc_code":   doc_code,
                        "q_data":     copy.deepcopy(q),
                        "q_edited":   copy.deepcopy(q),   # bản có thể bị sửa
                        "checked":    True,
                        "file_data":  data,               # gốc cho build_exam_doc
                    }
                    self._all_q_items.append(item)

        self._update_combo_files()
        self._apply_filter()
        self._update_status_bar()
        self._log(f"✅ Đã nạp {len(self._all_q_items)} câu hỏi từ {len(target_folders)} thư mục.")

    # ── Xây dựng UI ─────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        # Header
        self._build_header()

        # Main 3-panel
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=1, column=0, sticky="nsew", padx=10, pady=4)
        main.grid_columnconfigure(0, weight=3)   # Danh sách
        main.grid_columnconfigure(1, weight=4)   # Xem
        main.grid_columnconfigure(2, weight=4)   # Sửa
        main.grid_rowconfigure(0, weight=1)

        self._build_list_panel(main)
        self._build_view_panel(main)
        self._build_edit_panel(main)

        # Footer status + log
        self._build_footer()

    def _build_header(self):
        hdr = ctk.CTkFrame(self, corner_radius=0, fg_color=(PANEL_BG, "#111827"))
        hdr.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        hdr.grid_columnconfigure(1, weight=1)

        lbl = ctk.CTkLabel(hdr,
            text="🔍  TRÌNH DUYỆT & CHỈNH SỬA CÂU HỎI — Mabuchi Motor Vietnam",
            font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color="#60a5fa")
        lbl.pack(side="left", padx=20, pady=10)

        # Nút Mở File JSON tùy chỉnh / file rút gọn
        btn_open_file = ctk.CTkButton(
            hdr, text="📂 Mở File Rút Gọn JSON...",
            width=175, height=30,
            fg_color="#0891b2", hover_color="#0e7490",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=self._open_custom_json
        )
        btn_open_file.pack(side="left", padx=(10, 0))

        # Bộ lọc thư mục & file riêng
        filter_box = ctk.CTkFrame(hdr, fg_color="transparent")
        filter_box.pack(side="right", padx=16, pady=6)

        # Chọn file riêng
        lbl_file = ctk.CTkLabel(filter_box, text="📄 File riêng:", font=ctk.CTkFont(size=11, weight="bold"), text_color="#38bdf8")
        lbl_file.pack(side="left", padx=(0, 4))

        self._combo_files = ctk.CTkComboBox(
            filter_box, width=170, height=30,
            values=["(Tất cả file)"],
            font=ctk.CTkFont(size=11),
            command=self._on_single_file_filter_changed
        )
        self._combo_files.set("(Tất cả file)")
        self._combo_files.pack(side="left", padx=(0, 10))

        lbl_f = ctk.CTkLabel(filter_box, text="📂 Thư mục:", font=ctk.CTkFont(size=11, weight="bold"))
        lbl_f.pack(side="left", padx=(0, 6))

        self._folder_vars: Dict[str, tk.BooleanVar] = {}
        self._folder_checks: List = []

        # Scrollable frame cho checkbox thư mục
        folder_scroll = ctk.CTkScrollableFrame(filter_box, orientation="horizontal",
                                               height=38, fg_color="transparent", width=420)
        folder_scroll.pack(side="left")

        for fn in self._available_folders:
            var = tk.BooleanVar(value=True)
            self._folder_vars[fn] = var
            cb = ctk.CTkCheckBox(folder_scroll, text=fn, variable=var,
                                 font=ctk.CTkFont(size=10), width=130,
                                 command=self._on_folder_filter_changed)
            cb.pack(side="left", padx=4)
            self._folder_checks.append(cb)

        btn_reload = ctk.CTkButton(filter_box, text="🔄 Tải Lại", width=75, height=30,
                                   fg_color="#374151", hover_color="#4b5563",
                                   command=self._reload_with_filter)
        btn_reload.pack(side="left", padx=(8, 0))

    def _build_list_panel(self, parent):
        """Panel trái: danh sách câu hỏi với checkbox."""
        box = ctk.CTkFrame(parent, corner_radius=10, fg_color=(PANEL_BG, CARD_BG))
        box.grid(row=0, column=0, sticky="nsew", padx=(0, 4))
        box.grid_rowconfigure(3, weight=1)
        box.grid_columnconfigure(0, weight=1)

        # Tiêu đề + search
        hdr = ctk.CTkFrame(box, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))

        ctk.CTkLabel(hdr, text="📋 DANH SÁCH CÂU HỎI",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="left")

        # Toolbar: chọn tất cả / bỏ tất cả
        tbar = ctk.CTkFrame(box, fg_color="transparent")
        tbar.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 4))

        btn_all = ctk.CTkButton(tbar, text="✅ Chọn tất cả", width=95, height=26,
                                fg_color="#1d4ed8", hover_color="#1e40af",
                                font=ctk.CTkFont(size=10),
                                command=self._select_all)
        btn_all.pack(side="left", padx=(0, 2))

        btn_none = ctk.CTkButton(tbar, text="☐ Bỏ chọn", width=80, height=26,
                                 fg_color="#374151", hover_color="#4b5563",
                                 font=ctk.CTkFont(size=10),
                                 command=self._deselect_all)
        btn_none.pack(side="left", padx=2)

        btn_key = ctk.CTkButton(tbar, text="◎ Chỉ chủ chốt", width=95, height=26,
                                fg_color="#7c3aed", hover_color="#6d28d9",
                                font=ctk.CTkFont(size=10),
                                command=self._select_key_only)
        btn_key.pack(side="left", padx=2)

        # Box yêu cầu lọc tự nhiên — chiều cao CỐ ĐỊNH để không đẩy tree xuống
        prompt_card = ctk.CTkFrame(box, fg_color=DARK_BG, corner_radius=8, height=120)
        prompt_card.grid(row=2, column=0, sticky="ew", padx=8, pady=(2, 4))
        prompt_card.grid_columnconfigure(0, weight=1)
        prompt_card.grid_propagate(False)  # Quan trọng: không để con kéo giãn prompt_card

        p_lbl_row = ctk.CTkFrame(prompt_card, fg_color="transparent")
        p_lbl_row.pack(fill="x", padx=6, pady=(4, 2))
        ctk.CTkLabel(
            p_lbl_row,
            text="⚡ Nhập Yêu Cầu Rút Gọn (NLP Prompt):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#60a5fa"
        ).pack(side="left")

        self._txt_prompt_req = ctk.CTkTextbox(
            prompt_card, height=58, font=("Consolas", 10),
            fg_color="#181e29", text_color="#f1f5f9"
        )
        self._txt_prompt_req.pack(fill="x", padx=6, pady=(0, 2))
        self._txt_prompt_req.insert("1.0", "- Các câu hỏi thuộc về phần 1-A00\n- Không đưa vào câu hỏi ngày tháng cố định, ACM, SMI, đổi đơn vị...")

        p_btn_row = ctk.CTkFrame(prompt_card, fg_color="transparent")
        p_btn_row.pack(fill="x", padx=6, pady=(2, 4))

        btn_run_prompt = ctk.CTkButton(
            p_btn_row, text="⚡ Phân Tích & Tự Động Lọc",
            height=26, font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#059669", hover_color="#047857",
            command=self._apply_prompt_requirements
        )
        btn_run_prompt.pack(side="left", padx=(0, 4))

        btn_clear_prompt = ctk.CTkButton(
            p_btn_row, text="Xóa", width=50, height=26,
            font=ctk.CTkFont(size=10), fg_color="#374151",
            command=lambda: self._txt_prompt_req.delete("1.0", "end")
        )
        btn_clear_prompt.pack(side="left")

        # Treeview list — đặt minheight để không bị prompt_card đẩy ra
        tree_frame = tk.Frame(box, bg="#0f172a", height=200)
        tree_frame.grid(row=3, column=0, sticky="nsew", padx=8, pady=(0, 8))
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("QB.Treeview",
                         background="#0f172a", foreground="#f1f5f9",
                         rowheight=26, fieldbackground="#0f172a",
                         font=("Segoe UI", 9), borderwidth=0)
        style.configure("QB.Treeview.Heading",
                         background="#1e293b", foreground="#93c5fd",
                         font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("QB.Treeview",
                  background=[("selected", "#1e3a8a")],
                  foreground=[("selected", "#ffffff")])

        cols = ("sel", "idx", "folder", "qtext")
        self._list_tree = ttk.Treeview(tree_frame, columns=cols, show="headings",
                                       style="QB.Treeview", selectmode="browse")
        self._list_tree.heading("sel",    text="✓",   anchor="center")
        self._list_tree.heading("idx",    text="STT", anchor="center")
        self._list_tree.heading("folder", text="Thư Mục", anchor="w")
        self._list_tree.heading("qtext",  text="Nội Dung Câu Hỏi", anchor="w")

        self._list_tree.column("sel",    width=28,  anchor="center", stretch=False)
        self._list_tree.column("idx",    width=40,  anchor="center", stretch=False)
        self._list_tree.column("folder", width=100, anchor="w",      stretch=False)
        self._list_tree.column("qtext",  width=250, anchor="w")

        self._list_tree.tag_configure("key_q",    foreground="#f97316", font=("Segoe UI", 9, "bold"))
        self._list_tree.tag_configure("normal_q", foreground="#e2e8f0")
        self._list_tree.tag_configure("checked",  background="#1e3a5f")
        self._list_tree.tag_configure("unchecked", background="#1a1f2e")

        sb_y = ttk.Scrollbar(tree_frame, orient="vertical",   command=self._list_tree.yview)
        sb_x = ttk.Scrollbar(tree_frame, orient="horizontal", command=self._list_tree.xview)
        self._list_tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        self._list_tree.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")

        self._list_tree.bind("<<TreeviewSelect>>", self._on_list_select)
        self._list_tree.bind("<space>", self._on_space_toggle)
        self._list_tree.bind("<Double-1>", self._on_space_toggle)

    def _build_view_panel(self, parent):
        """Panel giữa: xem chi tiết câu hỏi."""
        box = ctk.CTkFrame(parent, corner_radius=10, fg_color=(PANEL_BG, CARD_BG))
        box.grid(row=0, column=1, sticky="nsew", padx=4)
        box.grid_rowconfigure(1, weight=1)
        box.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(box, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))

        self._lbl_view_title = ctk.CTkLabel(hdr,
            text="📖 XEM CHI TIẾT CÂU HỎI (click câu trong danh sách)",
            font=ctk.CTkFont(size=12, weight="bold"))
        self._lbl_view_title.pack(side="left")

        self._txt_view = ctk.CTkTextbox(box,
            font=("Consolas", 11), fg_color=(DARK_BG, "#0a0f1a"),
            text_color=TEXT_MAIN, wrap="word", corner_radius=8, state="disabled")
        self._txt_view.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    def _build_edit_panel(self, parent):
        """Panel phải: form chỉnh sửa câu hỏi."""
        box = ctk.CTkFrame(parent, corner_radius=10, fg_color=(PANEL_BG, CARD_BG))
        box.grid(row=0, column=2, sticky="nsew", padx=(4, 0))
        box.grid_rowconfigure(0, weight=1)
        box.grid_columnconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(box, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        scroll.grid_columnconfigure(0, weight=1)

        def lbl(text, row, color=TEXT_DIM):
            ctk.CTkLabel(scroll, text=text, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=color, anchor="w").grid(
                row=row, column=0, sticky="w", padx=8, pady=(6, 1))

        def entry(row, height=60):
            tb = ctk.CTkTextbox(scroll, height=height, font=("Segoe UI", 11),
                                fg_color=DARK_BG, text_color=TEXT_MAIN,
                                corner_radius=6, wrap="word")
            tb.grid(row=row, column=0, sticky="ew", padx=8, pady=(0, 4))
            return tb

        lbl("✏ NỘI DUNG CÂU HỎI:", 0, "#60a5fa")
        self._edit_question = entry(1, height=90)

        lbl("A:", 2)
        self._edit_a = entry(3, height=50)
        lbl("B:", 4)
        self._edit_b = entry(5, height=50)
        lbl("C:", 6)
        self._edit_c = entry(7, height=50)
        lbl("D:", 8)
        self._edit_d = entry(9, height=50)

        lbl("✅ ĐÁP ÁN ĐÚNG:", 10, "#4ade80")
        self._ans_var = tk.StringVar(value="A")
        ans_row = ctk.CTkFrame(scroll, fg_color="transparent")
        ans_row.grid(row=11, column=0, sticky="ew", padx=8, pady=(0, 8))
        for opt in ["A", "B", "C", "D"]:
            ctk.CTkRadioButton(ans_row, text=opt, variable=self._ans_var, value=opt,
                               font=ctk.CTkFont(size=13, weight="bold"),
                               radiobutton_width=18, radiobutton_height=18).pack(side="left", padx=8)

        lbl("◎ CÂU CHỦ CHỐT:", 12, ORANGE)
        self._key_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(scroll, text="Đánh dấu là câu chủ chốt (◎)",
                        variable=self._key_var, font=ctk.CTkFont(size=12)).grid(
            row=13, column=0, sticky="w", padx=12, pady=(0, 8))

        # Nút Lưu chỉnh sửa
        btn_save_edit = ctk.CTkButton(scroll, text="💾 Lưu chỉnh sửa câu này",
                                      height=36, fg_color="#059669", hover_color="#047857",
                                      font=ctk.CTkFont(size=12, weight="bold"),
                                      command=self._save_current_edit)
        btn_save_edit.grid(row=14, column=0, sticky="ew", padx=8, pady=(4, 2))

        btn_reset = ctk.CTkButton(scroll, text="↩ Khôi phục gốc",
                                  height=30, fg_color="#374151", hover_color="#4b5563",
                                  font=ctk.CTkFont(size=11),
                                  command=self._reset_current_edit)
        btn_reset.grid(row=15, column=0, sticky="ew", padx=8, pady=(2, 12))

    def _build_footer(self):
        footer = ctk.CTkFrame(self, corner_radius=0, fg_color=(PANEL_BG, "#111827"))
        footer.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        footer.grid_columnconfigure(1, weight=1)

        # Trái: status text
        self._lbl_status = ctk.CTkLabel(footer, text="Đang tải...",
                                        font=ctk.CTkFont(size=11), text_color="#93c5fd")
        self._lbl_status.grid(row=0, column=0, sticky="w", padx=14, pady=4)

        # Giữa: log mini
        self._lbl_log = ctk.CTkLabel(footer, text="", font=ctk.CTkFont(size=10),
                                     text_color=TEXT_DIM)
        self._lbl_log.grid(row=0, column=1, sticky="w", padx=8, pady=4)

        # Phải: nút xuất
        btn_bar = ctk.CTkFrame(footer, fg_color="transparent")
        btn_bar.grid(row=0, column=2, sticky="e", padx=10, pady=6)

        btn_export_quick = ctk.CTkButton(btn_bar,
            text="⚡ Xuất Nhanh Tổng Hợp Rút Gọn",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36, fg_color="#059669", hover_color="#047857",
            command=self._export_quick_tong_hop)
        btn_export_quick.pack(side="left", padx=4)

        btn_export = ctk.CTkButton(btn_bar,
            text="📤 Xuất Word từ câu đã chọn",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36, fg_color="#7c3aed", hover_color="#6d28d9",
            command=self._export_selected)
        btn_export.pack(side="left", padx=4)

        btn_export_all = ctk.CTkButton(btn_bar,
            text="📦 Xuất Tất Cả (có chỉnh sửa)",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36, fg_color="#1d4ed8", hover_color="#1e40af",
            command=self._export_all_edited)
        btn_export_all.pack(side="left", padx=4)

        btn_close = ctk.CTkButton(btn_bar, text="✖ Đóng", width=80, height=36,
                                  fg_color="#4b5563", hover_color="#374151",
                                  command=self.destroy)
        btn_close.pack(side="left", padx=4)

    # ── Logic filter & update list ───────────────────────────────────────────

    def _on_folder_filter_changed(self):
        pass  # filter sẽ apply khi click Tải Lại

    def _reload_with_filter(self):
        selected_folders = [fn for fn, var in self._folder_vars.items() if var.get()]
        if not selected_folders:
            messagebox.showwarning("Chú ý", "Vui lòng chọn ít nhất 1 thư mục!")
            return
        self._load_all_questions(selected_folders)

    def _apply_filter(self):
        selected_folders = [fn for fn, var in self._folder_vars.items() if var.get()]
        sel_file = getattr(self, "_selected_file_filter", "(Tất cả file)")

        filtered = []
        for it in self._all_q_items:
            # Lọc theo thư mục (hỗ trợ so khớp linh hoạt slug hoặc tên đầy đủ)
            if selected_folders:
                it_f = str(it.get("folder", "")).strip()
                it_slug = it_f.split()[0] if it_f else ""
                matched = any(
                    it_f == sf or it_slug == sf or sf in it_f or it_f in sf or it_slug == sf.split()[0]
                    for sf in selected_folders
                )
                # Nếu câu hỏi thuộc thư mục đặc biệt không nằm trong danh mục quét ban đầu (vd File_Rieng, RutGon)
                if not matched and it_f not in self._available_folders and it_slug not in self._available_folders:
                    matched = True  # Cho phép hiển thị file tùy chỉnh người dùng vừa mở
                if not matched:
                    continue

            # Lọc theo file riêng lẻ
            if sel_file != "(Tất cả file)" and it.get("fname") != sel_file:
                continue
            filtered.append(it)

        self._filtered_items = filtered
        self._rebuild_list_tree()
        self._update_status_bar()

    def _update_combo_files(self):
        fnames = sorted(list(set(it["fname"] for it in self._all_q_items if it.get("fname"))))
        vals = ["(Tất cả file)"] + fnames
        if hasattr(self, "_combo_files") and self._combo_files:
            self._combo_files.configure(values=vals)
            self._combo_files.set("(Tất cả file)")
            self._selected_file_filter = "(Tất cả file)"

    def _on_single_file_filter_changed(self, choice: str):
        self._selected_file_filter = choice
        self._apply_filter()
        self._log(f"📄 Đang lọc theo file: {choice}")

    def _open_custom_json(self):
        """Mở trực tiếp file JSON bất kỳ (file rút gọn đã xuất hoặc file trong questions_bank)."""
        fpath = filedialog.askopenfilename(
            title="Mở File Câu Hỏi JSON",
            initialdir=OUTPUT_DIR,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not fpath:
            return

        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)

            self._all_q_items.clear()
            global_counter = 0

            # Trường hợp 1: File tổng hợp rút gọn có key "files"
            if isinstance(data, dict) and "files" in data:
                file_list = data["files"]
                for fd in file_list:
                    doc_title = fd.get("doc_title", "Tài liệu")
                    doc_code = fd.get("doc_code", "")
                    fname = fd.get("file_name") or fd.get("pdf_filename") or "file.json"
                    raw_folder = fd.get("folder_name") or fd.get("folder") or "RutGon"
                    # Lấy slug thư mục ngắn (ví dụ "1-A00")
                    folder_slug = raw_folder.split()[0] if raw_folder else "RutGon"
                    for q in fd.get("questions", []):
                        global_counter += 1
                        self._all_q_items.append({
                            "global_idx": global_counter,
                            "folder": folder_slug,
                            "folder_display": raw_folder,
                            "fname": fname,
                            "doc_title": doc_title,
                            "doc_code": doc_code,
                            "q_data": copy.deepcopy(q),
                            "q_edited": copy.deepcopy(q),
                            "checked": True,
                            "file_data": fd
                        })

            # Trường hợp 2: List các file_data
            elif isinstance(data, list):
                for fd in data:
                    doc_title = fd.get("doc_title", "Tài liệu")
                    doc_code = fd.get("doc_code", "")
                    fname = fd.get("file_name") or fd.get("pdf_filename") or "file.json"
                    raw_folder = fd.get("folder_name") or fd.get("folder") or "RutGon"
                    folder_slug = raw_folder.split()[0] if raw_folder else "RutGon"
                    for q in fd.get("questions", []):
                        global_counter += 1
                        self._all_q_items.append({
                            "global_idx": global_counter,
                            "folder": folder_slug,
                            "folder_display": raw_folder,
                            "fname": fname,
                            "doc_title": doc_title,
                            "doc_code": doc_code,
                            "q_data": copy.deepcopy(q),
                            "q_edited": copy.deepcopy(q),
                            "checked": True,
                            "file_data": fd
                        })

            # Trường hợp 3: Single file JSON tiêu chuẩn có key "questions"
            elif isinstance(data, dict) and "questions" in data:
                fname = os.path.basename(fpath)
                parent_dir = os.path.basename(os.path.dirname(fpath))
                raw_folder = data.get("folder_name") or parent_dir or "File_Rieng"
                folder_slug = raw_folder.split()[0] if raw_folder else "File_Rieng"
                doc_title = data.get("doc_title", fname)
                doc_code = data.get("doc_code", "")
                for q in data.get("questions", []):
                    global_counter += 1
                    self._all_q_items.append({
                        "global_idx": global_counter,
                        "folder": folder_slug,
                        "folder_display": raw_folder,
                        "fname": fname,
                        "doc_title": doc_title,
                        "doc_code": doc_code,
                        "q_data": copy.deepcopy(q),
                        "q_edited": copy.deepcopy(q),
                        "checked": True,
                        "file_data": data
                    })

            # Đảm bảo các thư mục của file vừa nạp đều được tick chọn
            loaded_folders = set(it["folder"] for it in self._all_q_items)
            for lf in loaded_folders:
                if lf in self._folder_vars:
                    self._folder_vars[lf].set(True)

            self._selected_file_filter = "(Tất cả file)"
            self._update_combo_files()
            self._apply_filter()
            self._update_status_bar()
            self._log(f"📂 Đã nạp {len(self._all_q_items)} câu hỏi từ file: {os.path.basename(fpath)}")
            messagebox.showinfo("Thành Công", f"Đã nạp {len(self._all_q_items)} câu hỏi từ:\n{os.path.basename(fpath)}")

        except Exception as e:
            self._log(f"❌ Lỗi nạp file JSON: {e}")
            messagebox.showerror("Lỗi", f"Không thể mở file JSON:\n{e}")

    def _apply_prompt_requirements(self):
        """Phân tích văn bản yêu cầu của người dùng và tự động chọn/bỏ chọn câu hỏi."""
        text = self._txt_prompt_req.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Chú ý", "Vui lòng nhập hoặc dán nội dung yêu cầu vào khung text!")
            return

        if parse_requirements_text is None or should_exclude_question is None:
            messagebox.showerror("Lỗi", "Không tìm thấy module parse_requirements_text!")
            return

        parsed = parse_requirements_text(text)
        target_folders = parsed.get("folders")

        # Nếu prompt có đề cập thư mục cụ thể (vd 1-A00), cập nhật checkbox thư mục
        if target_folders:
            for fn, var in self._folder_vars.items():
                var.set(fn in target_folders)

        kept_count = 0
        excluded_count = 0

        for it in self._all_q_items:
            # Nếu item thuộc thư mục bị bỏ qua bởi prompt
            if target_folders and it["folder"] not in target_folders:
                it["checked"] = False
                excluded_count += 1
                continue

            q = it["q_edited"]
            fname = it["fname"]
            exclude, reason = should_exclude_question(
                fname, q,
                extra_exclude_keywords=parsed.get("extra_exclude_keywords"),
                exclude_acm_smi=parsed.get("exclude_acm_smi", True),
                exclude_dates=parsed.get("exclude_dates", True),
                exclude_conversions=parsed.get("exclude_conversions", True),
                exclude_ncc_sheet=parsed.get("exclude_ncc_sheet", True),
            )
            it["checked"] = not exclude
            if exclude:
                excluded_count += 1
            else:
                kept_count += 1

        self._apply_filter()
        self._update_status_bar()
        self._log(f"⚡ Đã lọc theo yêu cầu: Giữ lại {kept_count} câu (✓), Bỏ chọn {excluded_count} câu (☐)")
        messagebox.showinfo(
            "Kết Quả Phân Tích & Lọc Tự Động",
            f"🎉 Đã tự động phân tích yêu cầu và lọc câu hỏi:\n\n"
            f"• Số câu ĐẠT tiêu chí (Đã tick ✓): {kept_count} câu\n"
            f"• Số câu BỊ LOẠI (Bỏ tick ☐): {excluded_count} câu\n\n"
            f"Bây giờ bạn có thể duyệt qua từng câu hỏi trong bảng, tick/bỏ tick hoặc chỉnh sửa trực tiếp, rồi bấm '⚡ Xuất Nhanh Tổng Hợp Rút Gọn'!"
        )

    def _export_quick_tong_hop(self):
        """Xuất nhanh ra DE THI TONG HOP RUT GON.docx và DAP AN TONG HOP RUT GON.docx."""
        checked = [it for it in self._filtered_items if it["checked"]]
        if not checked:
            messagebox.showwarning("Chú ý", "Chưa chọn câu nào! Hãy đánh dấu ✓ các câu muốn xuất.")
            return

        if build_exam_doc is None or build_answer_doc is None:
            messagebox.showerror("Lỗi", "Không tìm thấy module exam_word_merger!")
            return

        exam_path = os.path.join(OUTPUT_DIR, "DE THI TONG HOP RUT GON.docx")
        ans_path = os.path.join(OUTPUT_DIR, "DAP AN TONG HOP RUT GON.docx")
        json_path = os.path.join(OUTPUT_DIR, "DE THI TONG HOP RUT GON_questions.json")

        def _run():
            try:
                file_data_list = self._build_file_data_list(checked)
                config = dict(self._config)
                exam_settings = dict(config.get("exam_settings", {}))
                exam_settings["title"] = "BÀI TEST NHẬN ĐỊNH TƯ CÁCH NHÂN VIÊN VÀ ĐỘI TRƯỞNG - TỔNG HỢP RÚT GỌN"
                exam_settings["revision"] = "BẢN RÚT GỌN CHỌN LỌC"
                config["exam_settings"] = exam_settings

                # Ghi JSON
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump({
                        "exam_title": exam_settings["title"],
                        "total_questions": len(checked),
                        "files": file_data_list
                    }, f, ensure_ascii=False, indent=2)

                exam_doc = build_exam_doc(config, file_data_list)
                exam_doc.save(exam_path)

                ans_doc = build_answer_doc(config, file_data_list)
                ans_doc.save(ans_path)

                total_q = sum(len(fd.get("questions", [])) for fd in file_data_list)
                self._log(f"✅ Đã xuất {total_q} câu → {os.path.basename(exam_path)}")
                messagebox.showinfo("Thành công",
                    f"🎉 Đã xuất thành công Tổng Hợp Rút Gọn!\n\n"
                    f"• Số câu: {total_q} câu\n"
                    f"• Đề thi: DE THI TONG HOP RUT GON.docx\n"
                    f"• Đáp án: DAP AN TONG HOP RUT GON.docx\n"
                    f"• File JSON lưu lại: DE THI TONG HOP RUT GON_questions.json\n\n"
                    f"Lưu tại thư mục KetQua.")
            except Exception as e:
                self._log(f"❌ Lỗi xuất: {e}")
                messagebox.showerror("Lỗi", f"Xuất thất bại:\n{e}")

        threading.Thread(target=_run, daemon=True).start()
        self._log(f"⏳ Đang xuất nhanh {len(checked)} câu hỏi...")

    def _rebuild_list_tree(self):
        self._list_tree.delete(*self._list_tree.get_children())
        for i, item in enumerate(self._filtered_items):
            q = item["q_edited"]
            qt = q.get("question_text", "")
            is_key = q.get("is_key", False) or "◎" in qt
            checked = item["checked"]
            short_text = qt[:60].replace("\n", " ") + ("…" if len(qt) > 60 else "")
            chk_mark = "✓" if checked else "☐"
            tag = ("key_q",) if is_key else ("normal_q",)
            bg_tag = ("checked",) if checked else ("unchecked",)
            self._list_tree.insert("", "end", iid=str(i),
                                   values=(chk_mark, item["global_idx"], item["folder"], short_text),
                                   tags=tag + bg_tag)
        # Buộc Tkinter re-render Treeview ngay lập tức
        self._list_tree.update_idletasks()

    def _update_status_bar(self):
        total   = len(self._filtered_items)
        checked = sum(1 for it in self._filtered_items if it["checked"])
        edited  = sum(1 for it in self._filtered_items
                      if it["q_data"] != it["q_edited"])
        key_q   = sum(1 for it in self._filtered_items
                      if it["q_edited"].get("is_key") or "◎" in it["q_edited"].get("question_text", ""))
        self._lbl_status.configure(
            text=f"Tổng: {total} câu  |  Đã chọn: {checked}  |  Đã sửa: {edited}  |  Chủ chốt ◎: {key_q}")

    def _log(self, msg: str):
        self._lbl_log.configure(text=msg)

    # ── Sự kiện danh sách ───────────────────────────────────────────────────

    def _on_list_select(self, event=None):
        sel = self._list_tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        self._selected_idx = idx
        self._current_item = self._filtered_items[idx]
        self._show_view(self._current_item)
        self._load_edit_form(self._current_item)

    def _on_space_toggle(self, event=None):
        """Toggle checkbox khi nhấn Space hoặc Double-click."""
        sel = self._list_tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        item = self._filtered_items[idx]
        item["checked"] = not item["checked"]
        chk = "✓" if item["checked"] else "☐"
        bg_tag = "checked" if item["checked"] else "unchecked"
        q = item["q_edited"]
        is_key = q.get("is_key", False) or "◎" in q.get("question_text", "")
        tag = "key_q" if is_key else "normal_q"
        self._list_tree.item(str(idx), values=(chk, item["global_idx"], item["folder"],
                              q.get("question_text", "")[:60]),
                              tags=(tag, bg_tag))
        self._update_status_bar()

    def _select_all(self):
        for item in self._filtered_items:
            item["checked"] = True
        self._rebuild_list_tree()
        self._update_status_bar()

    def _deselect_all(self):
        for item in self._filtered_items:
            item["checked"] = False
        self._rebuild_list_tree()
        self._update_status_bar()

    def _select_key_only(self):
        for item in self._filtered_items:
            q = item["q_edited"]
            item["checked"] = q.get("is_key", False) or "◎" in q.get("question_text", "")
        self._rebuild_list_tree()
        self._update_status_bar()

    # ── View panel ──────────────────────────────────────────────────────────

    def _show_view(self, item: Dict):
        q = item["q_edited"]
        qt = q.get("question_text", "")
        opts = q.get("options", {})
        correct = q.get("correct_answer", "?")
        is_key = q.get("is_key", False) or "◎" in qt
        ref = q.get("reference_note", "")

        self._lbl_view_title.configure(
            text=f"📖 [{item['folder']}] {item['doc_code']} — {item['doc_title'][:50]}")

        self._txt_view.configure(state="normal")
        self._txt_view.delete("1.0", "end")

        badge = "◎ [CÂU CHỦ CHỐT]" if is_key else "[ câu thường ]"
        lines = [
            f"{'='*60}",
            f"{badge}",
            f"{'='*60}",
            f"\n❓ CÂU HỎI:\n{qt}\n",
            f"  A. {opts.get('A', '')}",
            f"  B. {opts.get('B', '')}",
            f"  C. {opts.get('C', '')}",
            f"  D. {opts.get('D', '')}",
            f"\n✅ ĐÁP ÁN ĐÚNG: {correct}",
            f"\n📌 Tham chiếu: {ref}" if ref else "",
            f"\n📂 File: {item['fname']} | Thư mục: {item['folder']}",
        ]
        self._txt_view.insert("end", "\n".join(lines))
        self._txt_view.configure(state="disabled")

    # ── Edit panel ──────────────────────────────────────────────────────────

    def _load_edit_form(self, item: Dict):
        q = item["q_edited"]
        opts = q.get("options", {})

        def _set(tb, text):
            tb.delete("1.0", "end")
            tb.insert("end", text)

        _set(self._edit_question, q.get("question_text", ""))
        _set(self._edit_a, opts.get("A", ""))
        _set(self._edit_b, opts.get("B", ""))
        _set(self._edit_c, opts.get("C", ""))
        _set(self._edit_d, opts.get("D", ""))
        self._ans_var.set(q.get("correct_answer", "A"))
        is_key = q.get("is_key", False) or "◎" in q.get("question_text", "")
        self._key_var.set(is_key)

    def _save_current_edit(self):
        if self._current_item is None:
            messagebox.showinfo("Thông báo", "Chưa chọn câu hỏi nào để lưu!")
            return
        q = self._current_item["q_edited"]

        def _get(tb):
            return tb.get("1.0", "end").strip()

        qt = _get(self._edit_question)
        is_key = self._key_var.get()
        if is_key and not qt.startswith("◎"):
            qt = "◎ " + qt.lstrip("◎ ")
        elif not is_key and qt.startswith("◎"):
            qt = qt.lstrip("◎ ").strip()

        q["question_text"]  = qt
        q["options"]["A"]   = _get(self._edit_a)
        q["options"]["B"]   = _get(self._edit_b)
        q["options"]["C"]   = _get(self._edit_c)
        q["options"]["D"]   = _get(self._edit_d)
        q["correct_answer"] = self._ans_var.get()
        q["is_key"]         = is_key

        # Cập nhật lại view
        self._show_view(self._current_item)

        # Cập nhật lại dòng trong tree
        if self._selected_idx is not None:
            item = self._current_item
            chk = "✓" if item["checked"] else "☐"
            bg_tag = "checked" if item["checked"] else "unchecked"
            tag = "key_q" if is_key else "normal_q"
            self._list_tree.item(str(self._selected_idx),
                                  values=(chk, item["global_idx"], item["folder"],
                                          qt[:60] + ("…" if len(qt) > 60 else "")),
                                  tags=(tag, bg_tag))

        self._update_status_bar()
        self._log(f"💾 Đã lưu chỉnh sửa câu {self._current_item['global_idx']}.")

    def _reset_current_edit(self):
        if self._current_item is None:
            return
        self._current_item["q_edited"] = copy.deepcopy(self._current_item["q_data"])
        self._load_edit_form(self._current_item)
        self._show_view(self._current_item)
        self._log(f"↩ Đã khôi phục câu {self._current_item['global_idx']} về gốc.")

    # ── Xuất Word ───────────────────────────────────────────────────────────

    def _build_file_data_list(self, items: List[Dict]) -> List[Dict]:
        """
        Gom các item đã chọn thành list file_data tương thích build_exam_doc.
        Mỗi file gốc được gom lại, dùng q_edited thay cho q_data gốc.
        """
        from collections import OrderedDict
        files_map: OrderedDict = OrderedDict()  # key: (folder, fname)
        for item in items:
            key = (item["folder"], item["fname"])
            if key not in files_map:
                base = dict(item["file_data"])
                base["questions"] = []
                files_map[key] = base
            files_map[key]["questions"].append(item["q_edited"])
        return list(files_map.values())

    def _export_selected(self):
        checked = [it for it in self._filtered_items if it["checked"]]
        if not checked:
            messagebox.showwarning("Chú ý", "Chưa chọn câu nào! Hãy đánh dấu ✓ các câu muốn xuất.")
            return
        self._do_export(checked, prefix="TuyChon")

    def _export_all_edited(self):
        self._do_export(self._filtered_items, prefix="ToanBo_CoSuaChuu")

    def _do_export(self, items: List[Dict], prefix: str = "Export"):
        if build_exam_doc is None or build_answer_doc is None:
            messagebox.showerror("Lỗi", "Không tìm thấy module exam_word_merger!")
            return

        # Hỏi nơi lưu
        exam_path = filedialog.asksaveasfilename(
            title="Lưu file Đề Thi",
            initialdir=OUTPUT_DIR,
            initialfile=f"{prefix}_DeThi.docx",
            defaultextension=".docx",
            filetypes=[("Word Document", "*.docx")]
        )
        if not exam_path:
            return
        ans_path = exam_path.replace("_DeThi.docx", "_DapAn.docx")
        if "_DeThi" not in exam_path:
            ans_path = exam_path.replace(".docx", "_DapAn.docx")

        def _run():
            try:
                file_data_list = self._build_file_data_list(items)
                config = dict(self._config)

                # Ghi JSON bản sửa
                edited_json_path = exam_path.replace(".docx", "_edited.json")
                with open(edited_json_path, "w", encoding="utf-8") as f:
                    json.dump(file_data_list, f, ensure_ascii=False, indent=2)

                exam_doc = build_exam_doc(config, file_data_list)
                exam_doc.save(exam_path)

                ans_doc = build_answer_doc(config, file_data_list)
                ans_doc.save(ans_path)

                total_q = sum(len(fd.get("questions", [])) for fd in file_data_list)
                self._log(f"✅ Đã xuất {total_q} câu → {os.path.basename(exam_path)}")
                messagebox.showinfo("Thành công",
                    f"Đã xuất {total_q} câu hỏi!\n"
                    f"• Đề thi: {os.path.basename(exam_path)}\n"
                    f"• Đáp án: {os.path.basename(ans_path)}\n"
                    f"• JSON bản sửa: {os.path.basename(edited_json_path)}")
            except Exception as e:
                self._log(f"❌ Lỗi xuất: {e}")
                messagebox.showerror("Lỗi", f"Xuất thất bại:\n{e}")

        threading.Thread(target=_run, daemon=True).start()
        self._log(f"⏳ Đang xuất {len(items)} câu hỏi...")


# ── Dialog Rút Gọn Tùy Chỉnh (gắn vào app_gui) ─────────────────────────────

# ── Dialog Rút Gọn Tùy Chỉnh (gắn vào app_gui) ─────────────────────────────

class RutGonDialog(ctk.CTkToplevel):
    """
    Dialog chọn thư mục + cấu hình tiêu chí lọc + nhập từ khóa loại trừ để xuất bản rút gọn tùy chỉnh.
    Áp dụng linh hoạt cho mọi thư mục tiêu chuẩn hiện tại và tương lai.
    """

    def __init__(self, parent=None, available_folders: Optional[List[str]] = None,
                 on_confirm_callback=None, log_fn=None):
        super().__init__(parent)
        self.title("✨ Xuất Đề Thi & Đáp Án Rút Gọn Tùy Chỉnh")
        self.geometry("720x640")
        self.minsize(640, 560)

        self._callback = on_confirm_callback
        self._log = log_fn or print
        self._folder_vars: Dict[str, tk.BooleanVar] = {}

        # Nếu không truyền danh sách folders, tự quét từ questions_bank
        if not available_folders:
            if os.path.isdir(BANK_BASE):
                available_folders = sorted([
                    d for d in os.listdir(BANK_BASE)
                    if os.path.isdir(os.path.join(BANK_BASE, d))
                ])
            else:
                available_folders = []

        self._build(available_folders)

    def _build(self, available_folders: List[str]):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # header: cố định
        self.grid_rowconfigure(1, weight=1)  # scroll area: EXPAND để lấp đầy
        self.grid_rowconfigure(2, weight=0)  # btn_bar: cố định ở đáy

        # 1. Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(16, 8))
        ctk.CTkLabel(
            header,
            text="✨ CÀI ĐẶT RÚT GỌN NỘI DUNG ĐỀ THI & BIỂU ĐÁP ÁN",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#60a5fa"
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text="Áp dụng lọc câu hỏi thông minh theo các tiêu chuẩn kỹ thuật bất kỳ",
            font=ctk.CTkFont(size=11, slant="italic"),
            text_color=TEXT_DIM
        ).pack(anchor="w", pady=(2, 0))

        # 2. Main scrollable content
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=0)
        scroll.grid_columnconfigure(0, weight=1)

        # A. Chọn thư mục
        folder_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=8)
        folder_card.pack(fill="x", pady=(0, 10))
        folder_card.grid_columnconfigure(0, weight=1)

        f_hdr = ctk.CTkFrame(folder_card, fg_color="transparent")
        f_hdr.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(
            f_hdr,
            text="📂 1. Chọn thư mục tiêu chuẩn cần rút gọn:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#93c5fd"
        ).pack(side="left")

        btn_box = ctk.CTkFrame(f_hdr, fg_color="transparent")
        btn_box.pack(side="right")
        ctk.CTkButton(
            btn_box, text="Chọn hết", width=65, height=24,
            font=ctk.CTkFont(size=10), fg_color="#3b82f6",
            command=self._select_all_folders
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            btn_box, text="Bỏ hết", width=55, height=24,
            font=ctk.CTkFont(size=10), fg_color="#4b5563",
            command=self._deselect_all_folders
        ).pack(side="left", padx=2)

        f_list = ctk.CTkFrame(folder_card, fg_color="transparent")
        f_list.pack(fill="x", padx=12, pady=(0, 10))
        f_list.grid_columnconfigure((0, 1), weight=1)

        for i, fn in enumerate(available_folders):
            var = tk.BooleanVar(value=True)
            self._folder_vars[fn] = var
            r = i // 2
            c = i % 2
            ctk.CTkCheckBox(
                f_list, text=fn, variable=var,
                font=ctk.CTkFont(size=11)
            ).grid(row=r, column=c, sticky="w", padx=6, pady=3)

        # B. Tiêu chuẩn lọc (Filter Criteria)
        crit_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=8)
        crit_card.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            crit_card,
            text="⚙ 2. Các tiêu chí loại bỏ câu hỏi (Tùy chọn lọc):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#93c5fd"
        ).pack(anchor="w", padx=12, pady=(10, 6))

        self.var_exclude_acm = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            crit_card,
            text="🚫 Loại bỏ câu hỏi liên quan đến phần mềm ACM / SMI",
            variable=self.var_exclude_acm,
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=16, pady=3)

        self.var_exclude_dates = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            crit_card,
            text="🚫 Loại bỏ câu hỏi ngày tháng cố định (ngày ban hành đầu tiên, lịch sử cải đính theo ngày...)",
            variable=self.var_exclude_dates,
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=16, pady=3)

        self.var_exclude_conv = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            crit_card,
            text="🚫 Loại bỏ câu hỏi hoán đổi đơn vị đo (kgf sang Newton, hoán đổi trọng lượng/lực...)",
            variable=self.var_exclude_conv,
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=16, pady=3)

        self.var_exclude_ncc = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            crit_card,
            text="🚫 Loại bỏ câu hỏi về quy định đặt mã số sheet / mẫu thiết định khi thêm nhà cung cấp",
            variable=self.var_exclude_ncc,
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=16, pady=(3, 10))

        # C. Từ khóa loại trừ thêm (Custom Keywords)
        kw_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=8)
        kw_card.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            kw_card,
            text="📝 3. Yêu cầu / Từ khóa loại trừ bổ sung (mỗi dòng một cụm từ):",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#93c5fd"
        ).pack(anchor="w", padx=12, pady=(10, 4))

        self._txt_keywords = ctk.CTkTextbox(
            kw_card, height=80,
            font=("Consolas", 11),
            fg_color=DARK_BG, text_color=TEXT_MAIN
        )
        self._txt_keywords.pack(fill="x", padx=12, pady=(0, 10))

        # D. Tên file xuất
        name_card = ctk.CTkFrame(scroll, fg_color=CARD_BG, corner_radius=8)
        name_card.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(
            name_card,
            text="📄 4. Tên file Word xuất:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#93c5fd"
        ).pack(anchor="w", padx=12, pady=(10, 4))

        self.var_file_name_mode = tk.StringVar(value="TONG_HOP")
        r1 = ctk.CTkRadioButton(
            name_card,
            text="Tổng hợp rút gọn (DE THI TONG HOP RUT GON.docx & DAP AN TONG HOP RUT GON.docx)",
            variable=self.var_file_name_mode,
            value="TONG_HOP",
            font=ctk.CTkFont(size=11)
        )
        r1.pack(anchor="w", padx=16, pady=3)

        r2 = ctk.CTkRadioButton(
            name_card,
            text="Theo tên thư mục (Ví dụ: 1-A00_RutGon_DeThi.docx)",
            variable=self.var_file_name_mode,
            value="FOLDER",
            font=ctk.CTkFont(size=11)
        )
        r2.pack(anchor="w", padx=16, pady=3)

        custom_box = ctk.CTkFrame(name_card, fg_color="transparent")
        custom_box.pack(fill="x", padx=16, pady=(3, 10))

        r3 = ctk.CTkRadioButton(
            custom_box,
            text="Tùy chỉnh tiền tố:",
            variable=self.var_file_name_mode,
            value="CUSTOM",
            font=ctk.CTkFont(size=11)
        )
        r3.pack(side="left", padx=(0, 8))

        self._entry_prefix = ctk.CTkEntry(
            custom_box,
            font=ctk.CTkFont(size=11), height=28, width=200
        )
        self._entry_prefix.insert(0, "DeThiRutGon")
        self._entry_prefix.pack(side="left")

        # 3. Bottom Button bar — cố định ở đáy, không expand
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.grid(row=2, column=0, sticky="ew", padx=20, pady=(8, 14))

        self.btn_confirm = ctk.CTkButton(
            btn_bar, text="🚀 BẮT ĐẦU RÚT GỌN & XUẤT WORD",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=40, fg_color="#16a34a", hover_color="#15803d",
            command=self._on_confirm
        )
        self.btn_confirm.pack(side="left", padx=4)

        ctk.CTkButton(
            btn_bar, text="✖ Đóng", width=80, height=40,
            font=ctk.CTkFont(size=12),
            fg_color="#374151", hover_color="#4b5563",
            command=self.destroy
        ).pack(side="left", padx=4)

    def _select_all_folders(self):
        for var in self._folder_vars.values():
            var.set(True)

    def _deselect_all_folders(self):
        for var in self._folder_vars.values():
            var.set(False)

    def _on_confirm(self):
        folders = [fn for fn, var in self._folder_vars.items() if var.get()]
        if not folders:
            messagebox.showwarning("Chú ý", "Vui lòng chọn ít nhất 1 thư mục tiêu chuẩn!")
            return

        raw_kw = self._txt_keywords.get("1.0", "end").strip()
        keywords = [kw.strip() for kw in raw_kw.splitlines() if kw.strip()]

        mode = self.var_file_name_mode.get()
        if mode == "TONG_HOP":
            prefix = "TONG_HOP"
        elif mode == "FOLDER":
            prefix = folders[0].split()[0] if len(folders) == 1 else "RutGon"
        else:
            prefix = self._entry_prefix.get().strip() or "DeThiRutGon"

        opts = {
            "folders": folders,
            "extra_exclude_keywords": keywords,
            "exclude_acm_smi": self.var_exclude_acm.get(),
            "exclude_dates": self.var_exclude_dates.get(),
            "exclude_conversions": self.var_exclude_conv.get(),
            "exclude_ncc_sheet": self.var_exclude_ncc.get(),
            "output_prefix": prefix,
        }

        # Nếu có callback tùy chỉnh từ caller
        if self._callback:
            self.destroy()
            self._callback(opts)
            return

        # Thực thi trực tiếp qua generate_rutgon
        self.btn_confirm.configure(state="disabled", text="⏳ Đang xử lý lọc & xuất Word...")
        self.update_idletasks()

        def run_thread():
            try:
                import generate_rutgon
                res = generate_rutgon.filter_and_build(
                    folders=opts["folders"],
                    extra_exclude_keywords=opts["extra_exclude_keywords"],
                    exclude_acm_smi=opts["exclude_acm_smi"],
                    exclude_dates=opts["exclude_dates"],
                    exclude_conversions=opts["exclude_conversions"],
                    exclude_ncc_sheet=opts["exclude_ncc_sheet"],
                    output_prefix=opts["output_prefix"],
                    log_fn=self._log
                )
                self.after(0, lambda: self._on_success(res))
            except Exception as e:
                err_msg = str(e)
                self.after(0, lambda: self._on_error(err_msg))

        threading.Thread(target=run_thread, daemon=True).start()

    def _on_success(self, res: Dict[str, Any]):
        self.destroy()
        messagebox.showinfo(
            "Xuất Rút Gọn Thành Công",
            f"🎉 Đã xuất thành công Đề thi & Đáp án Rút Gọn!\n\n"
            f"• Số câu giữ lại: {res['total_kept']} câu ({res['total_key']} câu chủ chốt ◎)\n"
            f"• Số câu bị loại: {res['total_excluded']} câu\n"
            f"• Đề thi: {os.path.basename(res['exam_path'])}\n"
            f"• Đáp án: {os.path.basename(res['ans_path'])}\n\n"
            f"Đã lưu tại thư mục KetQua."
        )

    def _on_error(self, err_msg: str):
        self.btn_confirm.configure(state="normal", text="🚀 BẮT ĐẦU RÚT GỌN & XUẤT WORD")
        messagebox.showerror("Lỗi Rút Gọn", f"Không thể xuất file rút gọn:\n{err_msg}")



# ── Entry point để test độc lập ─────────────────────────────────────────────

if __name__ == "__main__":
    root = ctk.CTk()
    root.withdraw()
    browser = QuestionBrowser(root)
    browser.grab_set()
    root.mainloop()
