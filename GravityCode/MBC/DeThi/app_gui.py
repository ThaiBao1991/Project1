# -*- coding: utf-8 -*-
"""
Giao diện Desktop (GUI) - Hệ Thống Tạo Đề Thi & Đáp Án Tự Động (MBC DeThi)
Phòng Ban: BHCL - Mabuchi Motor Vietnam
Công nghệ: CustomTkinter + ttk.Treeview Dark Mode (Zero-Lag Performance)
Tính năng:
- Chọn thư mục mẹ Source và thư mục xuất KetQua.
- Bảng drill-down 2 cấp: thư mục → từng file PDF với tag màu OK/MISSING/FAILED.
- Panel xem trước câu hỏi: click file → hiện nội dung câu hỏi trong app.
- Vòng lặp tự động (Zero-Error Loop) chạy ngầm trong Thread đến khi 100% file hoàn thành.
- Cơ chế tự động đổi 155 Gemini API Keys từ 17 accounts khi gặp rate limit/exhausted.
- Xuất đề thi và đáp án riêng cho từng thư mục con hoặc tất cả thư mục.
- Nút Gộp toàn bộ đề thi & đáp án chuẩn mẫu REV 13.
- Nhật ký Console thời gian thực (Consolas font, auto-scroll).
"""

import os
import sys
import json
import time
import threading
import queue
import subprocess
from typing import Dict, Any, List, Optional

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk

from auto_question_generator import AutoQuestionGenerator
import exam_word_merger


# Thiết lập giao diện CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Tag màu trạng thái trong Treeview
TAG_OK      = "tag_ok"
TAG_MISSING = "tag_missing"
TAG_FAILED  = "tag_failed"
TAG_FOLDER  = "tag_folder"
TAG_KEY_Q   = "tag_key_q"
TAG_STALE   = "tag_stale"   # PDF đã thay đổi kể từ lần sinh câu hỏi — cần tái tạo


class DeThiApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Mabuchi Motor Vietnam — Hệ Thống Tự Động Tạo Đề Thi & Biểu Đáp Án (REV 13)")
        self.geometry("1380x900")
        self.minsize(1100, 750)

        # Trạng thái chạy
        self.worker_thread: Optional[threading.Thread] = None
        self.stop_requested = False
        self.pause_requested = False
        self.is_running = False
        self._start_time: Optional[float] = None
        self._files_processed_this_run = 0

        # Hàng đợi giao tiếp giữa Worker Thread và GUI Thread
        self.ui_queue = queue.Queue()

        # Đường dẫn cấu hình mặc định
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_path = os.path.join(self.base_dir, "config.json")
        self.source_dir = os.path.join(self.base_dir, "Source")
        self.output_dir = os.path.join(self.base_dir, "KetQua")

        # Đọc config
        self.config_data = self._load_config()
        if "source_dir" in self.config_data:
            s_dir = self.config_data["source_dir"]
            self.source_dir = s_dir if os.path.isabs(s_dir) else os.path.join(self.base_dir, s_dir)
        if "output_dir" in self.config_data:
            o_dir = self.config_data["output_dir"]
            self.output_dir = o_dir if os.path.isabs(o_dir) else os.path.join(self.base_dir, o_dir)

        # Engine Generator
        self.generator: Optional[AutoQuestionGenerator] = None

        # Cache trạng thái từng file để drill-down nhanh
        self._file_status_cache: Dict[str, Dict] = {}  # key: "{folder_slug}/{base_name}"
        self._current_preview_key: Optional[str] = None  # Đang preview file nào

        # Khởi tạo giao diện
        self._setup_ui()

        # Bắt đầu vòng lặp đọc queue định kỳ
        self.after(100, self._process_ui_queue)

        # Tải dữ liệu tiến độ ban đầu
        self.after(300, self._init_generator_and_refresh)

    def _load_config(self) -> Dict[str, Any]:
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _setup_ui(self):
        """Khởi dựng toàn bộ layout."""
        self.grid_columnconfigure(0, weight=1)
        # Row weights:
        #   row 0 = header       (cố định)
        #   row 1 = paths + KPI  (cố định)
        #   row 2 = main panels  (co giãn — weight=1)
        #   row 3 = progress bar (cố định)
        #   row 4 = action btns  (cố định)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=0)
        self.grid_rowconfigure(2, weight=1)  # chỉ row này co giãn
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)

        # ── 1. HEADER ──────────────────────────────────────────────────────────
        header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=("#1f2937", "#111827"))
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_columnconfigure(1, weight=1)

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=20, pady=12)

        lbl_badge = ctk.CTkLabel(
            title_box,
            text="MABUCHI MOTOR VIETNAM • PHÒNG ĐẢM BẢO CHẤT LƯỢNG (BHCL)",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#60a5fa"
        )
        lbl_badge.pack(anchor="w")

        lbl_title = ctk.CTkLabel(
            title_box,
            text="HỆ THỐNG TỰ ĐỘNG TẠO ĐỀ THI & BIỂU ĐÁP ÁN TIÊU CHUẨN KỸ THUẬT",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#ffffff"
        )
        lbl_title.pack(anchor="w")

        # ── 2. PATHS & KPI STATS BAR ───────────────────────────────────────────
        top_card = ctk.CTkFrame(self, corner_radius=10, fg_color=("#374151", "#1f2937"))
        top_card.grid(row=1, column=0, sticky="ew", padx=16, pady=(10, 6))
        top_card.grid_columnconfigure(1, weight=1)

        # Source directory
        lbl_src = ctk.CTkLabel(top_card, text="📁 Thư mục nguồn (Source):", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_src.grid(row=0, column=0, sticky="w", padx=14, pady=(10, 4))

        self.var_source = tk.StringVar(value=self.source_dir)
        self.entry_source = ctk.CTkEntry(top_card, textvariable=self.var_source, height=32)
        self.entry_source.grid(row=0, column=1, sticky="ew", padx=8, pady=(10, 4))

        btn_browse_src = ctk.CTkButton(top_card, text="Chọn Thư Mục", width=110, height=32, command=self._browse_source)
        btn_browse_src.grid(row=0, column=2, padx=(4, 14), pady=(10, 4))

        # Output directory
        lbl_dst = ctk.CTkLabel(top_card, text="📂 Thư mục xuất (KetQua):", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_dst.grid(row=1, column=0, sticky="w", padx=14, pady=(4, 10))

        self.var_output = tk.StringVar(value=self.output_dir)
        self.entry_output = ctk.CTkEntry(top_card, textvariable=self.var_output, height=32)
        self.entry_output.grid(row=1, column=1, sticky="ew", padx=8, pady=(4, 10))

        btn_browse_dst = ctk.CTkButton(top_card, text="Chọn Thư Mục", width=110, height=32, command=self._browse_output)
        btn_browse_dst.grid(row=1, column=2, padx=(4, 14), pady=(4, 10))

        # KPI Summary row
        kpi_frame = ctk.CTkFrame(top_card, fg_color=("#2d3748", "#111827"), corner_radius=8)
        kpi_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=14, pady=(0, 10))
        kpi_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.card_total = self._create_kpi_card(kpi_frame, 0, "TỔNG SỐ TÀI LIỆU PDF", "0", "#38bdf8")
        self.card_done = self._create_kpi_card(kpi_frame, 1, "ĐÃ HOÀN THÀNH (OK)", "0", "#4ade80")
        self.card_missing = self._create_kpi_card(kpi_frame, 2, "CÒN THIếu / CHƯ A LÀM", "0", "#fbbf24")
        self.card_pct = self._create_kpi_card(kpi_frame, 3, "TỶ LỆ HOÀN THÀNH", "0.0%", "#a855f7")

        # ── 3. MAIN SPLIT: TABLE (left) + DETAIL PANEL (right) ─────────────────
        main_split = ctk.CTkFrame(self, fg_color="transparent")
        main_split.grid(row=2, column=0, sticky="nsew", padx=16, pady=4)
        main_split.grid_columnconfigure(0, weight=5)   # Drill-down tree trái
        main_split.grid_columnconfigure(1, weight=6)   # Detail panel (preview + log) phải
        main_split.grid_rowconfigure(0, weight=1)

        # LEFT: Drill-down Treeview (2 cấp: folder > file)
        left_box = ctk.CTkFrame(main_split, corner_radius=10, fg_color=("#374151", "#1f2937"))
        left_box.grid(row=0, column=0, sticky="nsew", padx=(0, 4), pady=0)
        left_box.grid_rowconfigure(1, weight=1)
        left_box.grid_columnconfigure(0, weight=1)

        table_header = ctk.CTkFrame(left_box, fg_color="transparent")
        table_header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))

        lbl_tbl = ctk.CTkLabel(table_header,
                               text="📂 TIỪ ĐỘ TÀI LIỆU (click mở rộng → xem từng file)",
                               font=ctk.CTkFont(size=13, weight="bold"))
        lbl_tbl.pack(side="left")

        btn_expand_all = ctk.CTkButton(table_header, text="▼ Mở Rộng", width=80, height=26,
                                       font=ctk.CTkFont(size=11), fg_color="#4b5563",
                                       hover_color="#374151", command=self._expand_all_folders)
        btn_expand_all.pack(side="right", padx=(2, 0))

        btn_collapse_all = ctk.CTkButton(table_header, text="► Thu Gọn", width=80, height=26,
                                         font=ctk.CTkFont(size=11), fg_color="#4b5563",
                                         hover_color="#374151", command=self._collapse_all_folders)
        btn_collapse_all.pack(side="right", padx=(2, 0))

        btn_refresh_tbl = ctk.CTkButton(table_header, text="🔄", width=40, height=26,
                                        font=ctk.CTkFont(size=11), command=self._refresh_progress)
        btn_refresh_tbl.pack(side="right", padx=(0, 4))

        # Drill-down Treeview styled for dark mode
        tree_container = tk.Frame(left_box, bg="#181e29")
        tree_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        tree_container.grid_rowconfigure(0, weight=1)
        tree_container.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "DeThi.Treeview",
            background="#181e29",
            foreground="#f3f4f6",
            rowheight=28,
            fieldbackground="#181e29",
            font=("Segoe UI", 10),
            borderwidth=0,
            indent=16,
        )
        style.configure(
            "DeThi.Treeview.Heading",
            background="#111827",
            foreground="#93c5fd",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            padding=5
        )
        style.map("DeThi.Treeview",
                  background=[("selected", "#1e3a8a")],
                  foreground=[("selected", "#ffffff")])

        # 2-cấp: folder + file rows
        cols = ("name", "total", "done", "missing", "pct", "status")
        self.tree = ttk.Treeview(tree_container, columns=cols, show="tree headings",
                                 style="DeThi.Treeview", selectmode="browse")
        self.tree.heading("#0",      text="",             anchor="w")
        self.tree.heading("name",    text="Tên File / Thư Mục", anchor="w")
        self.tree.heading("total",   text="Tổng",        anchor="center")
        self.tree.heading("done",    text="Đã Xong",     anchor="center")
        self.tree.heading("missing", text="Thiếu",       anchor="center")
        self.tree.heading("pct",     text="%",            anchor="center")
        self.tree.heading("status",  text="Trạng Thái",  anchor="center")

        self.tree.column("#0",      width=18,  stretch=False)
        self.tree.column("name",    width=200, anchor="w")
        self.tree.column("total",   width=45,  anchor="center")
        self.tree.column("done",    width=55,  anchor="center")
        self.tree.column("missing", width=55,  anchor="center")
        self.tree.column("pct",     width=55,  anchor="center")
        self.tree.column("status",  width=120, anchor="center")

        # Tag màu dòng theo trạng thái
        self.tree.tag_configure(TAG_OK,      foreground="#34d399", font=("Segoe UI", 10))
        self.tree.tag_configure(TAG_MISSING, foreground="#fbbf24", font=("Segoe UI", 10))
        self.tree.tag_configure(TAG_FAILED,  foreground="#f87171", font=("Segoe UI", 10))
        self.tree.tag_configure(TAG_FOLDER,  foreground="#93c5fd", font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure(TAG_KEY_Q,   foreground="#f97316", font=("Segoe UI", 10, "bold"))
        self.tree.tag_configure(TAG_STALE,   foreground="#fb923c", font=("Segoe UI", 10, "bold"))  # Cam = STALE

        scroll_y = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        scroll_x = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        scroll_x.grid(row=1, column=0, sticky="ew")

        # Đăng ký sự kiện click chuột trái - mở preview
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # RIGHT PANEL: phân 2 phần: Preview (trên) + Console Log (dưới)
        right_panel = ctk.CTkFrame(main_split, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(4, 0), pady=0)
        right_panel.grid_rowconfigure(0, weight=4)   # Preview lớn hơn
        right_panel.grid_rowconfigure(1, weight=3)   # Log nhỏ hơn
        right_panel.grid_columnconfigure(0, weight=1)

        # RIGHT-TOP: Preview câu hỏi
        preview_box = ctk.CTkFrame(right_panel, corner_radius=10, fg_color=("#374151", "#1f2937"))
        preview_box.grid(row=0, column=0, sticky="nsew", pady=(0, 4))
        preview_box.grid_rowconfigure(1, weight=1)
        preview_box.grid_columnconfigure(0, weight=1)

        preview_hdr = ctk.CTkFrame(preview_box, fg_color="transparent")
        preview_hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))

        self.lbl_preview_title = ctk.CTkLabel(
            preview_hdr,
            text="📖 XEM TRƯỚC CÂU HỎI (click vào file trong bảng)",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.lbl_preview_title.pack(side="left")

        self.txt_preview = ctk.CTkTextbox(
            preview_box,
            font=("Consolas", 11),
            fg_color=("#181e29", "#0f172a"),
            text_color="#e2e8f0",
            wrap="word",
            corner_radius=8,
            state="disabled"
        )
        self.txt_preview.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        # RIGHT-BOTTOM: Console Log
        right_box = ctk.CTkFrame(right_panel, corner_radius=10, fg_color=("#374151", "#1f2937"))
        right_box.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        right_box.grid_rowconfigure(1, weight=1)
        right_box.grid_columnconfigure(0, weight=1)

        log_header = ctk.CTkFrame(right_box, fg_color="transparent")
        log_header.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))
        lbl_log = ctk.CTkLabel(log_header, text="🖥 NHẬT KÝ THỜI GIAN THỰC (CONSOLE LOGS)",
                               font=ctk.CTkFont(size=13, weight="bold"))
        lbl_log.pack(side="left")

        btn_clear_log = ctk.CTkButton(log_header, text="Xóa Log", width=70, height=26,
                                      font=ctk.CTkFont(size=11), fg_color="#4b5563",
                                      hover_color="#374151", command=self._clear_log)
        btn_clear_log.pack(side="right")

        self.txt_log = ctk.CTkTextbox(
            right_box,
            font=("Consolas", 11),
            fg_color=("#181e29", "#0f172a"),
            text_color="#e2e8f0",
            wrap="word",
            corner_radius=8
        )
        self.txt_log.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))


        # ── 4. PROGRESS & STATUS BAR ───────────────────────────────────────────
        prog_frame = ctk.CTkFrame(self, corner_radius=10, fg_color=("#374151", "#1f2937"))
        prog_frame.grid(row=3, column=0, sticky="ew", padx=16, pady=(6, 6))
        prog_frame.grid_columnconfigure(1, weight=1)

        self.lbl_status_text = ctk.CTkLabel(
            prog_frame,
            text="Trạng thái: Sẵn sàng.",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#93c5fd"
        )
        self.lbl_status_text.grid(row=0, column=0, sticky="w", padx=14, pady=(8, 2))

        self.prog_bar = ctk.CTkProgressBar(prog_frame, height=14, corner_radius=6, progress_color="#10b981")
        self.prog_bar.set(0.0)
        self.prog_bar.grid(row=1, column=0, columnspan=2, sticky="ew", padx=14, pady=(2, 8))

        # ── 5. ACTION BUTTONS BAR ──────────────────────────────────────────────
        btn_bar = ctk.CTkFrame(self, corner_radius=10, fg_color=("#1f2937", "#111827"))
        # Mode selector: Bổ sung / Tiếp tục (Resume) vs Làm lại từ đầu (Fresh)
        mode_box = ctk.CTkFrame(btn_bar, fg_color="transparent")
        mode_box.pack(fill="x", padx=16, pady=(8, 2))

        lbl_mode = ctk.CTkLabel(mode_box, text="⚙ Chế độ chạy:", font=ctk.CTkFont(size=12, weight="bold"), text_color="#cbd5e1")
        lbl_mode.pack(side="left", padx=(0, 8))

        self.seg_run_mode = ctk.CTkSegmentedButton(
            mode_box,
            values=["⚡ Chạy Tiếp Tục / Bổ Sung", "🔄 Làm Lại Từ Đầu"],
            font=ctk.CTkFont(size=11, weight="bold"),
            selected_color="#10b981",
            selected_hover_color="#059669",
            unselected_color="#374151",
            command=self._on_mode_change
        )
        self.seg_run_mode.set("⚡ Chạy Tiếp Tục / Bổ Sung")
        self.seg_run_mode.pack(side="left", padx=4)

        self.lbl_mode_hint = ctk.CTkLabel(
            mode_box,
            text="(Khuyên dùng: Tự động giữ nguyên các file đã xong, chỉ xử lý file mới thêm hoặc còn thiếu)",
            font=ctk.CTkFont(size=11, slant="italic"),
            text_color="#94a3b8"
        )
        self.lbl_mode_hint.pack(side="left", padx=8)

        # Hàng nút 1: Điều khiển chạy
        btn_row1 = ctk.CTkFrame(btn_bar, fg_color="transparent")
        btn_row1.pack(fill="x", padx=12, pady=(8, 2))

        self.btn_start = ctk.CTkButton(
            btn_row1,
            text="🚀 BẮT ĐẦU VÒNG LẶP TỰ ĐỘNG",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            fg_color="#16a34a",
            hover_color="#15803d",
            command=self._start_generation_loop
        )
        self.btn_start.pack(side="left", padx=4)

        self.btn_pause = ctk.CTkButton(
            btn_row1,
            text="⏸ Tạm Dừng",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=38, width=105,
            fg_color="#d97706",
            hover_color="#b45309",
            state="disabled",
            command=self._toggle_pause
        )
        self.btn_pause.pack(side="left", padx=4)

        self.btn_stop = ctk.CTkButton(
            btn_row1,
            text="⏹ Dừng",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=38, width=80,
            fg_color="#dc2626",
            hover_color="#b91c1c",
            state="disabled",
            command=self._stop_generation
        )
        self.btn_stop.pack(side="left", padx=4)

        self.btn_scan_changes = ctk.CTkButton(
            btn_row1,
            text="🔍 Quét File Mới / Đã Sửa",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=38, width=165,
            fg_color="#0369a1",
            hover_color="#075985",
            command=self._scan_for_changes
        )
        self.btn_scan_changes.pack(side="left", padx=(14, 4))

        # Hàng nút 2: Xuất đề và kết quả
        btn_row2 = ctk.CTkFrame(btn_bar, fg_color="transparent")
        btn_row2.pack(fill="x", padx=12, pady=(2, 8))

        self.btn_export_selected = ctk.CTkButton(
            btn_row2,
            text="📑 Xuất Thư Mục Chọn",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            fg_color="#7c3aed",
            hover_color="#6d28d9",
            command=self._export_selected_folder
        )
        self.btn_export_selected.pack(side="left", padx=4)

        self.btn_export_all_single = ctk.CTkButton(
            btn_row2,
            text="📑 Xuất Đề Cả Thư Mục",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=self._export_all_individual
        )
        self.btn_export_all_single.pack(side="left", padx=4)

        self.btn_export_single_files = ctk.CTkButton(
            btn_row2,
            text="📑 Xuất Từng Bản (File Riêng)",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            fg_color="#0d9488",
            hover_color="#0f766e",
            command=self._export_single_files
        )
        self.btn_export_single_files.pack(side="left", padx=4)

        self.btn_export_rutgon = ctk.CTkButton(
            btn_row2,
            text="✨ Xuất 1-A00 Rút Gọn",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            fg_color="#d97706",
            hover_color="#b45309",
            command=self._export_rutgon_1a00
        )
        self.btn_export_rutgon.pack(side="left", padx=4)

        self.btn_merge_all = ctk.CTkButton(
            btn_row2,
            text="📦 GỘP TOÀN BỘ ĐỀ (REV 13)",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            fg_color="#ca8a04",
            hover_color="#a16207",
            text_color="#ffffff",
            command=self._merge_all_exams
        )
        self.btn_merge_all.pack(side="left", padx=(14, 4))

        self.btn_open_folder = ctk.CTkButton(
            btn_row2,
            text="📂 Mở Thư Mục Kết Quả",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=36,
            fg_color="#4b5563",
            hover_color="#374151",
            command=self._open_output_dir
        )
        self.btn_open_folder.pack(side="left", padx=4)

        # btn_inner alias để code cũ tương thích
        btn_inner = btn_row1

        # → Gắn btn_bar vào root window
        btn_bar.grid(row=4, column=0, sticky="ew", padx=0, pady=(0, 6))

    def _create_kpi_card(self, parent, col, title, initial_val, text_color):
        card = ctk.CTkFrame(parent, fg_color="transparent")
        card.grid(row=0, column=col, sticky="ew", padx=10, pady=10)

        lbl_t = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=10, weight="bold"), text_color="#9ca3af")
        lbl_t.pack(anchor="center")

        lbl_v = ctk.CTkLabel(card, text=initial_val, font=ctk.CTkFont(size=20, weight="bold"), text_color=text_color)
        lbl_v.pack(anchor="center", pady=(2, 0))
        return lbl_v

    # ── DRILL-DOWN TREE HELPERS ──────────────────────────────────────────────────

    def _expand_all_folders(self):
        """Mở rộng tất cả folder nodes, lazy-load file children."""
        for iid in self.tree.get_children(""):
            self._ensure_children_loaded(iid)
            self.tree.item(iid, open=True)

    def _collapse_all_folders(self):
        """Thu gọn tất cả folder nodes."""
        for iid in self.tree.get_children(""):
            self.tree.item(iid, open=False)

    def _ensure_children_loaded(self, folder_iid: str):
        """
        Lazy-load: chỉ nạp hàng file-level khi folder được mở rộng.
        Kiểm tra placeholder sentinel "__loading__".
        """
        children = self.tree.get_children(folder_iid)
        if len(children) == 1 and children[0] == f"{folder_iid}::placeholder":
            # Xóa placeholder
            self.tree.delete(f"{folder_iid}::placeholder")
            # Load file children
            self._load_file_children(folder_iid)

    def _load_file_children(self, folder_iid: str):
        """Điền các dòng file-level vào trong folder node.
        Phát hiện: MISSING (chưa làm), OK, INVALID, ERROR, STALE (PDF đã thay đổi).
        """
        if not self.generator:
            return
        try:
            from pdf_extractor import scan_all_sources, get_pdf_file_info
            all_sources = scan_all_sources(self.generator.source_dir, self.generator.folder_order)
            folder_slug = folder_iid.split()[0]
            bank_dir = self.generator.config.get("questions_bank_dir", "KetQua/questions_bank")

            for item in all_sources:
                if item["folder_name"] != folder_iid:
                    continue
                base_name = os.path.splitext(item["filename"])[0]
                pdf_path = item["full_path"]

                # Kiểm tra trạng thái từng file
                json_path = os.path.join(bank_dir, folder_slug, f"{base_name}.json")
                if os.path.exists(json_path):
                    try:
                        with open(json_path, "r", encoding="utf-8") as f:
                            q_data = json.load(f)
                        file_status = q_data.get("status", "MISSING")
                        n_q = len(q_data.get("questions", []))
                        n_key = sum(1 for q in q_data.get("questions", [])
                                    if q.get("is_key") or "◎" in q.get("question_text", ""))

                        # Kiểm tra STALE: PDF đã thay đổi kể từ lần sinh?
                        is_stale = False
                        if file_status == "OK":
                            saved_meta = q_data.get("pdf_metadata", {})
                            if saved_meta and os.path.exists(pdf_path):
                                curr_info = get_pdf_file_info(pdf_path)
                                saved_size = saved_meta.get("file_size_bytes", -1)
                                saved_hash = saved_meta.get("file_hash_short", "")
                                curr_size  = curr_info.get("file_size_bytes", -1)
                                curr_hash  = curr_info.get("file_hash_short", "")
                                if (saved_size > 0 and curr_size > 0 and saved_size != curr_size) or \
                                   (saved_hash and curr_hash and saved_hash != curr_hash):
                                    is_stale = True

                    except Exception:
                        file_status = "ERROR"
                        n_q, n_key, is_stale = 0, 0, False
                else:
                    file_status = "MISSING"
                    n_q, n_key, is_stale = 0, 0, False

                # Tag màu và text trạng thái
                if is_stale:
                    tag = TAG_STALE
                    status_text = "🔄 STALE (PDF đã sửa)"
                elif file_status == "OK":
                    tag = TAG_OK
                    status_text = "✅ OK"
                elif file_status == "INVALID":
                    tag = TAG_FAILED
                    status_text = "⚠ INVALID"
                elif file_status == "ERROR":
                    tag = TAG_FAILED
                    status_text = "❌ ERROR"
                else:
                    tag = TAG_MISSING
                    status_text = "⬜ CHƯA LÀM"

                # Thông tin câu hỏi + ngày sinh
                q_info = ""
                if file_status == "OK" and not is_stale:
                    gen_iso = q_data.get("generated_at_iso", "") if os.path.exists(json_path) else ""
                    gen_short = gen_iso[:10] if gen_iso else ""  # YYYY-MM-DD
                    q_info = f"{n_q}c/◎{n_key}" + (f" | {gen_short}" if gen_short else "")
                elif is_stale:
                    q_info = f"{n_q}c/◎{n_key} | Cần tái tạo!"

                file_iid = f"{folder_iid}::{base_name}"
                self.tree.insert(
                    folder_iid, "end", iid=file_iid,
                    values=(item["filename"], "-",
                            str(n_q) if file_status == "OK" and not is_stale else "-",
                            "-", "-",
                            f"{status_text}  {q_info}".strip()),
                    tags=(tag,)
                )
        except Exception as e:
            self._log(f"⚠ Lỗi load file children: {e}")

    def _on_tree_select(self, event):
        """Xử lý click chọn hàng trong Treeview."""
        selected = self.tree.selection()
        if not selected:
            return
        iid = selected[0]

        # Nếu chọn folder node: lazy-load children
        if "::" not in iid:
            self._ensure_children_loaded(iid)
            return

        # Nếu chọn file node: hiện preview
        parts = iid.split("::")
        if len(parts) != 2:
            return
        folder_iid, base_name = parts[0], parts[1]
        folder_slug = folder_iid.split()[0]
        self._show_question_preview(folder_slug, base_name)

    def _show_question_preview(self, folder_slug: str, base_name: str):
        """Hiện nội dung câu hỏi của file trong panel preview bên phải."""
        if not self.generator:
            return
        bank_dir = self.generator.config.get("questions_bank_dir", "KetQua/questions_bank")
        json_path = os.path.join(bank_dir, folder_slug, f"{base_name}.json")

        self.txt_preview.configure(state="normal")
        self.txt_preview.delete("1.0", "end")

        if not os.path.exists(json_path):
            self.txt_preview.insert("end", f"⚠ File '{base_name}.json' chưa tồn tại trong ngân hàng câu hỏi.\n")
            self.txt_preview.insert("end", "Hệ thống chưa sinh câu hỏi cho tài liệu này.\n")
            self.txt_preview.configure(state="disabled")
            self.lbl_preview_title.configure(text=f"📖 {base_name}.pdf — CHƯA CÓ CÂU HỎI")
            return

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            self.txt_preview.insert("end", f"❌ Lỗi đọc file JSON: {e}\n")
            self.txt_preview.configure(state="disabled")
            return

        status = data.get("status", "MISSING")
        doc_title = data.get("doc_title", "(Chưa có)")
        doc_code = data.get("doc_code", "")
        questions = data.get("questions", [])
        n_key = sum(1 for q in questions if q.get("is_key") or "◎" in q.get("question_text", ""))

        # Tiêu đề preview
        status_icon = "✅" if status == "OK" else "⚠"
        self.lbl_preview_title.configure(
            text=f"📖 {base_name}.pdf — {status_icon} {status} | {len(questions)} câu / ◎{n_key} chủ chốt"
        )

        # Header file
        self.txt_preview.insert("end", f"═" * 60 + "\n")
        self.txt_preview.insert("end", f"📌 Tài liệu: {doc_title}\n")
        if doc_code:
            self.txt_preview.insert("end", f"🗒 Mã số: {doc_code}\n")
        self.txt_preview.insert("end", f"═" * 60 + "\n\n")

        # Nội dung từng câu hỏi
        for q in questions:
            q_num = q.get("question_number", "?")
            is_key = q.get("is_key", False) or "◎" in q.get("question_text", "")
            q_text = q.get("question_text", "").strip().lstrip("◎").strip()
            correct = q.get("correct_answer", "?")
            options = q.get("options", {})
            ref = q.get("reference_note", "")

            prefix = "◎ " if is_key else ""
            key_marker = "  ⭐ CÂU CHỦ CHỐT (bắt buộc đúng)" if is_key else ""
            self.txt_preview.insert("end", f"Câu {q_num}: {prefix}{q_text}{key_marker}\n")

            for opt_key in ["A", "B", "C", "D"]:
                opt_val = options.get(opt_key, "")
                if opt_val:
                    marker = " ✔" if opt_key == correct else ""
                    self.txt_preview.insert("end", f"  {opt_key}. {opt_val}{marker}\n")

            if ref:
                self.txt_preview.insert("end", f"  📎 Nguồn: {ref}\n")
            self.txt_preview.insert("end", "\n")

        self.txt_preview.configure(state="disabled")

    # ── LOGIC XỬ LÝ SỰ KIỆN ────────────────────────────────────────────────────

    def _browse_source(self):
        folder = filedialog.askdirectory(initialdir=self.var_source.get(), title="Chọn thư mục mẹ chứa tài liệu tiêu chuẩn kỹ thuật (Source)")
        if folder:
            self.var_source.set(folder)
            self.source_dir = folder
            self._save_config_dirs()
            self._init_generator_and_refresh()

    def _browse_output(self):
        folder = filedialog.askdirectory(initialdir=self.var_output.get(), title="Chọn thư mục xuất đề thi và đáp án (KetQua)")
        if folder:
            self.var_output.set(folder)
            self.output_dir = folder
            self._save_config_dirs()
            self._init_generator_and_refresh()

    def _save_config_dirs(self):
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                cfg["source_dir"] = self.var_source.get()
                cfg["output_dir"] = self.var_output.get()
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._log(f"⚠ Lỗi cập nhật config.json: {e}")

    def _open_output_dir(self):
        out = self.var_output.get()
        if not os.path.exists(out):
            os.makedirs(out, exist_ok=True)
        if sys.platform == "win32":
            os.startfile(out)
        else:
            subprocess.Popen(["xdg-open", out])

    def _clear_log(self):
        self.txt_log.delete("1.0", "end")

    def _log(self, text: str):
        """Gửi log vào queue an toàn."""
        self.ui_queue.put(("log", text))

    def _init_generator_and_refresh(self):
        """Khởi tạo engine và đọc tiến độ."""
        try:
            self._log("⏳ Đang kết nối engine tự động sinh câu hỏi và đọc kho API keys...")
            self.generator = AutoQuestionGenerator(
                config_path=self.config_path,
                log_fn=lambda msg: self.ui_queue.put(("log", msg))
            )
            self._refresh_progress()
        except Exception as e:
            self._log(f"❌ Lỗi khởi tạo generator: {e}")
            messagebox.showerror("Lỗi Khởi Tạo", f"Không thể tải API keys hoặc file cấu hình:\n{e}")

    def _refresh_progress(self):
        """Cập nhật Treeview và KPI Cards.
        Collapse tất cả folder trước khi rebuild để reset lazy-load placeholder,
        đảm bảo user expand lại sẽ thấy các file mới bổ sung.
        """
        if not self.generator:
            return
        try:
            stat = self.generator.scan_progress()
            self._update_kpi_and_table(stat)
        except Exception as e:
            self._log(f"⚠ Lỗi quét tiến độ: {e}")

    def _update_kpi_and_table(self, stat: Dict[str, Any]):
        total = stat.get("total", 0)
        done = stat.get("done", 0)
        missing = stat.get("missing", 0)
        pct = stat.get("percent", 0.0)

        # Cập nhật KPI
        self.card_total.configure(text=str(total))
        self.card_done.configure(text=str(done))
        self.card_missing.configure(text=str(missing))
        self.card_pct.configure(text=f"{pct:.1f}%")

        if total > 0:
            self.prog_bar.set(done / total)
        else:
            self.prog_bar.set(0.0)

        # Xóa cấu trúc bảng cũ
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Vẽ lại folder-level rows + placeholder sentinel cho lazy-load
        folders_dict = stat.get("folders", {})
        if not self.generator:
            return
        for fn in self.generator.folder_order:
            if fn not in folders_dict:
                continue
            fstat = folders_dict[fn]
            f_total   = fstat["total"]
            f_done    = fstat["done"]
            f_missing = fstat["missing"]
            f_pct     = f"{fstat['percent']:.1f}%"
            has_exam  = fstat.get("exam_docx", False)
            has_ans   = fstat.get("ans_docx", False)

            if f_done == f_total and f_total > 0:
                folder_tag = TAG_OK
            elif f_missing == f_total:
                folder_tag = TAG_MISSING
            else:
                folder_tag = TAG_FOLDER

            if has_exam and has_ans:
                status_docs = "✅ Đã Có (Đề+ĐA)"
            elif has_exam:
                status_docs = "📝 Có Đề Thi"
            else:
                status_docs = "⚪ Chưa xuất"

            # Insert folder node
            self.tree.insert("", "end", iid=fn,
                             values=(fn, f_total, f_done, f_missing, f_pct, status_docs),
                             tags=(folder_tag,), open=False)

            # Thêm placeholder — sẽ bị replace khi user mở rộng
            if f_total > 0:
                self.tree.insert(fn, "end", iid=f"{fn}::placeholder",
                                 values=("  … (click mở rộng để xem từng file)", "", "", "", "", ""),
                                 tags=(TAG_MISSING,))

    def _on_mode_change(self, value: str):
        """Xử lý khi người dùng chuyển đổi chế độ chạy."""
        if value == "🔄 Làm Lại Từ Đầu":
            self.lbl_mode_hint.configure(
                text="(CẢNH BÁO: Sẽ sinh mới và GHI ĐÈ toàn bộ câu hỏi đã làm!)",
                text_color="#f87171"
            )
        else:
            self.lbl_mode_hint.configure(
                text="(Khuyên dùng: Tự động giữ nguyên các file đã xong, chỉ xử lý file mới thêm hoặc còn thiếu)",
                text_color="#94a3b8"
            )

    # ── QUÉT FILE MỚI / STALE ──────────────────────────────────────────────────

    def _scan_for_changes(self):
        """
        Quét toàn bộ Source: phát hiện file PDF mới chưa có câu hỏi
        và file PDF đã bị sửa/cập nhật (STALE) — hiện kết quả popup để user nắm rõ.
        """
        if not self.generator:
            messagebox.showwarning("Chưa Sẵn Sàng", "Engine chưa khởi tạo. Vui lòng thử lại.")
            return

        self._log("🔍 Bắt đầu quét phát hiện file mới / đã sửa trong Source...")
        self.btn_scan_changes.configure(state="disabled", text="⏳ Đang quét...")
        self.update_idletasks()

        try:
            from pdf_extractor import scan_all_sources, get_pdf_file_info
            bank_dir = self.generator.config.get("questions_bank_dir", "KetQua/questions_bank")
            all_sources = scan_all_sources(self.generator.source_dir, self.generator.folder_order)

            new_files = []    # File PDF hoàn toàn mới, chưa có JSON
            stale_files = []  # File PDF đã thay đổi kể từ lần sinh câu hỏi
            ok_files = []     # File đã xong và không thay đổi

            for item in all_sources:
                folder_slug = item["folder_name"].split()[0]
                base_name = os.path.splitext(item["filename"])[0]
                json_path = os.path.join(bank_dir, folder_slug, f"{base_name}.json")

                if not os.path.exists(json_path):
                    new_files.append(item)
                    continue

                try:
                    with open(json_path, "r", encoding="utf-8") as fh:
                        q_data = json.load(fh)
                    if q_data.get("status") != "OK":
                        new_files.append(item)
                        continue

                    # Kiểm tra STALE
                    saved_meta = q_data.get("pdf_metadata", {})
                    if saved_meta and os.path.exists(item["full_path"]):
                        curr = get_pdf_file_info(item["full_path"])
                        if (saved_meta.get("file_size_bytes", -1) != curr.get("file_size_bytes", -1)) or \
                           (saved_meta.get("file_hash_short", "") and
                                saved_meta["file_hash_short"] != curr.get("file_hash_short", "")):
                            stale_files.append(item)
                            continue

                    ok_files.append(item)
                except Exception:
                    new_files.append(item)

            # Cập nhật bảng
            self._refresh_progress()

            # Hiện thị kết quả
            total = len(all_sources)
            summary_lines = [
                f"🔍 Kết Quả Quét — Tổng {total} file PDF:",
                f"",
                f"  ✅ Đã xong và không thay đổi: {len(ok_files)} file",
                f"  ⬜ File mới chưa có câu hỏi:    {len(new_files)} file",
                f"  🔄 PDF đã sửa (STALE):             {len(stale_files)} file",
            ]

            if new_files:
                summary_lines.append(f"")
                summary_lines.append(f"  ⬜ Các file mới (tối đa 10):")
                for item in new_files[:10]:
                    summary_lines.append(f"    • [{item['folder_name'].split()[0]}] {item['filename']}")
                if len(new_files) > 10:
                    summary_lines.append(f"    ... và {len(new_files)-10} file khác.")

            if stale_files:
                summary_lines.append(f"")
                summary_lines.append(f"  🔄 Các file đã sửa (tối đa 10):")
                for item in stale_files[:10]:
                    summary_lines.append(f"    • [{item['folder_name'].split()[0]}] {item['filename']}")
                if len(stale_files) > 10:
                    summary_lines.append(f"    ... và {len(stale_files)-10} file khác.")

            needs_action = len(new_files) + len(stale_files)
            if needs_action > 0:
                summary_lines.append(f"")
                summary_lines.append(f"  ➡ Cần xử lý: {needs_action} file")
                summary_lines.append(f"  ➡ Bấm '🚀 BắT ĐẦU VÒNG LẶP TỰ ĐỘNG' để xử lý tự động.")

            for line in summary_lines:
                self._log(line)

            if needs_action > 0:
                messagebox.showinfo(
                    "🔍 Phát Hiện File Mới / Đã Sửa",
                    "\n".join(summary_lines)
                )
            else:
                messagebox.showinfo(
                    "✅ Kiểm Tra Hoàn Tất",
                    f"Tất cả {len(ok_files)}/{total} file đã có câu hỏi và không có thay đổi mới!\n"
                    f"Hệ thống đang ở trạng thái hoàn chỉnh."
                )

        except Exception as e:
            self._log(f"❌ Lỗi quét: {e}")
            messagebox.showerror("Lỗi", str(e))
        finally:
            self.btn_scan_changes.configure(state="normal", text="🔍 Quét File Mới / Đã Sửa")

    # ── VÒNG LẶP SINH ĐỀ TỰ ĐỘNG (BACKGROUND THREAD) ──────────────────────────

    def _start_generation_loop(self):
        """Khởi động vòng lặp sinh đề ngầm."""
        if self.is_running:
            return

        if not self.generator:
            messagebox.showwarning("Cảnh báo", "Engine chưa khởi tạo xong. Vui lòng thử lại sau vài giây.")
            return

        is_fresh = (self.seg_run_mode.get() == "🔄 Làm Lại Từ Đầu")
        if is_fresh:
            confirm = messagebox.askyesno(
                "Xác Nhận Làm Lại Từ Đầu",
                "CẢNH BÁO:\n\nBạn đang chọn chế độ 'LÀM LẠI TỪ ĐẦU'.\n"
                "Toàn bộ câu hỏi đã hoàn thành trước đó sẽ bị xóa/tạo mới và GHI ĐÈ hoàn toàn.\n\n"
                "Bạn có chắc chắn muốn làm mới toàn bộ không?"
            )
            if not confirm:
                return

        self.force_regenerate = is_fresh
        self.is_running = True
        self.stop_requested = False
        self.pause_requested = False
        self._start_time = time.time()
        self._files_processed_this_run = 0

        self.btn_start.configure(state="disabled")
        self.btn_pause.configure(state="normal", text="⏸ Tạm Dừng")
        self.btn_stop.configure(state="normal")
        self.lbl_status_text.configure(text="Trạng thái: 🚀 Đang chạy vòng lặp tự động (chống dừng)...")

        # Khởi chạy thread
        self.worker_thread = threading.Thread(target=self._worker_loop_task, daemon=True)
        self.worker_thread.start()

    def _toggle_pause(self):
        if not self.is_running:
            return
        self.pause_requested = not self.pause_requested
        if self.pause_requested:
            self.btn_pause.configure(text="▶ Tiếp Tục", fg_color="#16a34a", hover_color="#15803d")
            self.lbl_status_text.configure(text="Trạng thái: ⏸ ĐÃ TẠM DỪNG.")
            self._log("⏸ Đã tạm dừng. Bấm 'Tiếp Tục' để chạy tiếp.")
        else:
            self.btn_pause.configure(text="⏸ Tạm Dừng", fg_color="#d97706", hover_color="#b45309")
            self.lbl_status_text.configure(text="Trạng thái: 🚀 Đang chạy...")
            self._log("▶ Đã tiếp tục vòng lặp.")

    def _stop_generation(self):
        if not self.is_running:
            return
        self.stop_requested = True
        self.lbl_status_text.configure(text="Trạng thái: ⏹ Đang dừng an toàn...")
        self.btn_stop.configure(state="disabled")
        self.btn_pause.configure(state="disabled")

    def _worker_loop_task(self):
        """Hàm thực thi trong Worker Thread."""
        try:
            force_regen = getattr(self, "force_regenerate", False)
            mode_name = "LÀM LẠI TỪ ĐẦU" if force_regen else "CHẠY TIẾP TỤC / BỔ SUNG"

            self._log("═══════════════════════════════════════════════════════════════")
            self._log(f"🚀 KHỞI ĐỘNG VÒNG LẶP SINH ĐỀ TỰ ĐỘNG [{mode_name}]")
            self._log("═══════════════════════════════════════════════════════════════")

            def on_progress(p_dict):
                self.ui_queue.put(("progress", p_dict))

            # Chạy tối đa 10 đợt quét tự động đến khi hoàn tất 100%
            self.generator.run_loop_until_complete(
                max_passes=10,
                stop_check=lambda: self.stop_requested,
                pause_check=lambda: self.pause_requested,
                progress_callback=on_progress,
                force_regenerate=force_regen
            )

        except Exception as e:
            self._log(f"❌ Lỗi trong worker loop: {e}")
        finally:
            self.ui_queue.put(("finish", None))

    def _process_ui_queue(self):
        """Xử lý các thông điệp từ Worker Thread định kỳ 100ms."""
        try:
            while not self.ui_queue.empty():
                msg_type, data = self.ui_queue.get_nowait()
                if msg_type == "log":
                    self.txt_log.insert("end", f"{data}\n")
                    self.txt_log.see("end")

                elif msg_type == "progress":
                    idx = data.get("current_idx", 0)
                    total = data.get("total", 1)
                    curr_file = data.get("current_file", "")
                    curr_folder = data.get("folder_name", "")
                    status = data.get("status", "")
                    done_cnt = data.get("done", 0)

                    if total > 0:
                        self.prog_bar.set(idx / total)

                    # Tính ETA
                    eta_str = ""
                    if self._start_time and idx > 0:
                        elapsed = time.time() - self._start_time
                        rate = elapsed / idx  # s/file
                        remaining = (total - idx) * rate
                        if remaining > 3600:
                            eta_str = f" | ETA ~{remaining/3600:.1f}h"
                        elif remaining > 60:
                            eta_str = f" | ETA ~{remaining/60:.0f}phút"
                        else:
                            eta_str = f" | ETA ~{remaining:.0f}s"

                    status_icon = "✅" if status == "OK" else ("⚠" if status == "INVALID" else ("⏭" if status == "SKIP_OK" else "⚙"))
                    folder_short = curr_folder.split()[0] if curr_folder else ""
                    self.lbl_status_text.configure(
                        text=f"[{idx}/{total}] {status_icon} {curr_file} ({folder_short}) — ✅{done_cnt} đã OK{eta_str}"
                    )

                    # Làm mới thống kê định kỳ
                    if idx % 5 == 0 or status in ("OK", "INVALID"):
                        self._refresh_progress()

                elif msg_type == "finish":
                    self.is_running = False
                    self.btn_start.configure(state="normal")
                    self.btn_pause.configure(state="disabled", text="⏸ Tạm Dừng", fg_color="#d97706")
                    self.btn_stop.configure(state="disabled")
                    self.lbl_status_text.configure(text="Trạng thái: Đã dừng/Hoàn tất.")
                    self._refresh_progress()
                    self._log("🏁 Vòng lặp kết thúc.")
        except Exception:
            pass

        self.after(100, self._process_ui_queue)

    # ── XUẤT ĐỀ & ĐÁP ÁN WORD ─────────────────────────────────────────────────

    def _export_selected_folder(self):
        """Xuất đề thi và đáp án cho 1 thư mục được chọn trong bảng."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Thông báo", "Vui lòng click chọn 1 thư mục tiêu chuẩn trong bảng trước khi xuất.")
            return

        iid = selected[0]
        # Nếu click vào file-level row, lấy folder cha
        folder_name = iid.split("::")[0] if "::" in iid else iid

        self._log(f"📝 Đang xuất Đề thi và Đáp án cho thư mục: {folder_name}...")
        try:
            res = exam_word_merger.export_folder_exam_and_answer(
                folder_name=folder_name,
                config_path=self.config_path,
                output_base_dir=self.var_output.get()
            )
            if "error" in res:
                messagebox.showwarning("Chưa Có Câu Hỏi", res["error"])
                self._log(f"⚠ {res['error']}")
            else:
                self._log(f"✅ ĐÃ XUẤT ĐỀ RIÊNG: {res.get('exam')}")
                self._log(f"✅ ĐÃ XUẤT ĐÁP ÁN RIÊNG: {res.get('answer')} (Tổng {res.get('total_questions')} câu)")
                self._refresh_progress()
                messagebox.showinfo("Thành Công", f"Đã tạo thành công Đề thi và Đáp án cho {folder_name.split()[0]}!\nTổng: {res.get('total_questions')} câu hỏi.")
        except Exception as e:
            self._log(f"❌ Lỗi xuất đề thư mục: {e}")
            messagebox.showerror("Lỗi", f"Không thể xuất file Word:\n{e}")

    def _export_rutgon_1a00(self):
        """Xuất Đề thi và Đáp án rút gọn riêng cho thư mục 1-A00 (loại bỏ ACM/SMI, ngày cố định, đổi đơn vị...)."""
        self._log("✨ Đang tạo Đề thi và Đáp án rút gọn cho thư mục 1-A00 Ban V IT HOA...")
        try:
            from generate_rutgon_1A00 import filter_and_build
            res = filter_and_build()
            self._log(f"✅ ĐÃ XUẤT ĐỀ RÚT GỌN 1-A00: {res['exam_path']}")
            self._log(f"✅ ĐÃ XUẤT ĐÁP ÁN RÚT GỌN 1-A00: {res['ans_path']}")
            self._log(f"📊 Thống kê: Giữ lại {res['total_kept']} câu (trong đó {res['total_key']} câu ◎), loại bỏ {res['total_excluded']} câu.")
            messagebox.showinfo(
                "Xuất Rút Gọn Thành Công",
                f"Đã xuất thành công Đề thi & Đáp án Rút Gọn 1-A00!\n\n"
                f"• Giữ lại: {res['total_kept']} câu ({res['total_key']} câu chủ chốt ◎)\n"
                f"• Loại bỏ: {res['total_excluded']} câu (ACM/SMI, ngày cố định, đổi đơn vị)\n\n"
                f"File lưu tại thư mục KetQua."
            )
        except Exception as e:
            self._log(f"❌ Lỗi xuất đề rút gọn 1-A00: {e}")
            messagebox.showerror("Lỗi", f"Không thể xuất file rút gọn:\n{e}")

    def _export_all_individual(self):
        """Xuất đề thi và đáp án riêng cho toàn bộ các thư mục tiêu chuẩn."""
        self._log("📝 Đang xuất đề thi và đáp án riêng cho TẤT CẢ các thư mục tiêu chuẩn...")
        try:
            results = exam_word_merger.export_all_individual_folders(
                config_path=self.config_path,
                output_base_dir=self.var_output.get()
            )
            success_count = 0
            for fn, res in results.items():
                if "error" not in res:
                    success_count += 1
                    self._log(f"  ✅ {fn.split()[0]}: {res.get('total_questions')} câu → {os.path.basename(res.get('exam'))}")
                else:
                    self._log(f"  ⚪ {fn.split()[0]}: Chưa có câu hỏi OK.")

            self._refresh_progress()
            messagebox.showinfo("Hoàn Tất", f"Đã xuất đề riêng thành công cho {success_count}/{len(results)} thư mục tiêu chuẩn!")
        except Exception as e:
            self._log(f"❌ Lỗi xuất tất cả đề riêng: {e}")
            messagebox.showerror("Lỗi", f"Không thể xuất file Word:\n{e}")

    def _export_single_files(self):
        """Xuất file Word (Đề thi & Đáp án) riêng biệt cho từng bản tiêu chuẩn (từng file PDF)."""
        selected = self.tree.selection()
        if selected:
            folder_name = selected[0]
            self._log(f"📝 Đang xuất file Word riêng từng bản cho thư mục: {folder_name}...")
            try:
                res_list = exam_word_merger.export_all_single_files_by_folder(
                    folder_name=folder_name,
                    config_path=self.config_path,
                    output_base_dir=self.var_output.get()
                )
                if not res_list:
                    messagebox.showwarning("Thông Báo", f"Thư mục {folder_name.split()[0]} chưa có file nào đạt trạng thái OK.")
                    return
                for r in res_list:
                    self._log(f"  ✅ {r['file_name']}: {r['total_questions']} câu → {os.path.basename(r['exam'])} & {os.path.basename(r['answer'])}")
                self._refresh_progress()
                messagebox.showinfo("Thành Công", f"Đã xuất riêng {len(res_list)} bản tiêu chuẩn vào:\nKetQua/{folder_name.split()[0]}/tung_ban/")
            except Exception as e:
                self._log(f"❌ Lỗi xuất từng bản: {e}")
                messagebox.showerror("Lỗi", str(e))
        else:
            ans = messagebox.askyesno(
                "Xuất Tất Cả Các Bản",
                "Bạn chưa chọn thư mục cụ thể. Bạn có muốn xuất file Word riêng biệt cho TẤT CẢ các bản tiêu chuẩn đã hoàn thành của toàn bộ 8 thư mục không?"
            )
            if not ans:
                return
            self._log("📝 Đang xuất file Word riêng biệt cho TẤT CẢ các bản tiêu chuẩn...")
            try:
                all_res = exam_word_merger.export_all_single_files_all_folders(
                    config_path=self.config_path,
                    output_base_dir=self.var_output.get()
                )
                total_files = sum(len(v) for v in all_res.values())
                for fn, r_list in all_res.items():
                    if r_list:
                        self._log(f"  ✅ {fn.split()[0]}: {len(r_list)} bản đã xuất vào tung_ban/")
                self._refresh_progress()
                messagebox.showinfo("Hoàn Tất", f"Đã xuất thành công {total_files} bản tiêu chuẩn riêng biệt!")
            except Exception as e:
                self._log(f"❌ Lỗi xuất tất cả từng bản: {e}")
                messagebox.showerror("Lỗi", str(e))

    def _merge_all_exams(self):
        """Gộp tất cả câu hỏi từ 2-000 đến 9-Z00 thành 1 đề thi và 1 biểu đáp án tổng hợp chuẩn REV 13."""
        self._log("\n📦 BẮT ĐẦU GỘP TOÀN BỘ ĐỀ THI & BIỂU ĐÁP ÁN (CHUẨN REV 13)...")
        try:
            res = exam_word_merger.merge_and_export(
                config_path=self.config_path,
                output_base_dir=self.var_output.get()
            )
            if not res or "error" in res:
                msg = res.get("error", "Chưa có câu hỏi nào đạt trạng thái OK để gộp.")
                messagebox.showwarning("Chưa Có Dữ Liệu", msg)
                self._log(f"⚠ {msg}")
            else:
                exam_path = res.get("exam")
                ans_path = res.get("answer")
                total_q = res.get("total_questions", 0)

                self._log("═══════════════════════════════════════════════════════════════")
                self._log(f"🎉 GỘP THÀNH CÔNG TỔNG HỢP {total_q} CÂU HỎI TRẮC NGHIỆM!")
                self._log(f"   📄 Đề thi tổng hợp: {exam_path}")
                self._log(f"   📋 Đáp án tổng hợp: {ans_path}")
                self._log("═══════════════════════════════════════════════════════════════")

                self._refresh_progress()
                ans = messagebox.askyesno(
                    "Gộp Thành Công!",
                    f"Đã tạo thành công bộ Đề thi và Biểu đáp án tổng hợp!\n\n"
                    f"• Tổng số câu hỏi: {total_q} câu\n"
                    f"• Đề thi: {os.path.basename(exam_path)}\n"
                    f"• Đáp án: {os.path.basename(ans_path)}\n\n"
                    f"Bạn có muốn mở thư mục kết quả ngay không?"
                )
                if ans:
                    self._open_output_dir()
        except Exception as e:
            self._log(f"❌ Lỗi gộp toàn bộ: {e}")
            messagebox.showerror("Lỗi", f"Không thể gộp file Word:\n{e}")


if __name__ == "__main__":
    app = DeThiApp()
    app.mainloop()
