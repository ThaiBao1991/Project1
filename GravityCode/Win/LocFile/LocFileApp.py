"""
LocFileApp - Ứng dụng lọc file siêu tốc trên Windows.
- Duyệt đệ quy toàn bộ thư mục con bằng os.scandir
- Bộ lọc: Ngày sửa đổi, Kích thước file, Định dạng/Nhóm file, Từ khóa tên file
- Xử lý đa luồng (Multi-threading), không giật lag UI (Zero-Lag ttk.Treeview Dark Theme)
- Hỗ trợ sắp xếp cột, chọn nhiều file, mở file hàng loạt bằng ứng dụng mặc định (os.startfile)
- Mở thư mục chứa file trong Windows Explorer
"""

import sys
import os
import time
import subprocess
import threading
import queue
from datetime import datetime, timedelta

# Đảm bảo terminal Windows không bị lỗi UnicodeEncodeError khi in log tiếng Việt
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ─── Khai báo và tự động kiểm tra thư viện cần thiết ─────────────────────────────
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
    except Exception as e:
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
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk

# ─── Bảng màu Dark Mode đồng bộ & Tối ưu hiệu năng ─────────────────────────
PALETTE = {
    "bg": "#181825",            # Nền tối chính (Catppuccin Mocha Crust/Base)
    "card": "#1e1e2e",          # Nền khung điều khiển (Surface)
    "card_alt": "#24273a",      # Nền thẻ nổi bật
    "border": "#313244",        # Viền nhẹ nhàng
    "text": "#cdd6f4",          # Màu chữ chính
    "text_muted": "#a6adc8",    # Màu chữ chú thích
    "accent": "#89b4fa",        # Màu xanh nhấn mạnh
    "accent_hover": "#b4befe",  # Hover màu nhấn
    "success": "#a6e3a1",       # Màu xanh lá thành công
    "success_hover": "#94e2d5",
    "danger": "#f38ba8",        # Màu đỏ hủy/dừng
    "danger_hover": "#eba0ac",
    "tree_bg": "#181825",       # Nền Treeview
    "tree_fg": "#cdd6f4",       # Chữ Treeview
    "tree_select": "#3b4261",   # Màu dòng được chọn
    "tree_header": "#1e1e2e",   # Nền tiêu đề cột
    "tree_header_fg": "#89b4fa" # Chữ tiêu đề cột
}

# ─── Tiện ích định dạng dung lượng & thời gian ──────────────────────────────
def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def parse_date_str(date_str: str):
    date_str = date_str.strip()
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass
    return None

# ─── Nhóm định dạng file phổ biến ───────────────────────────────────────────
EXTENSION_GROUPS = {
    "Tất cả file (*.*)": None,
    "Tài liệu (.pdf, .docx, .xlsx, .pptx, .txt, .csv)": {
        ".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".txt", ".csv", ".rtf", ".odt"
    },
    "Hình ảnh (.png, .jpg, .jpeg, .gif, .webp, .svg, .bmp)": {
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".ico", ".tiff", ".psd"
    },
    "Video (.mp4, .mkv, .avi, .mov, .wmv, .flv, .webm)": {
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v", ".3gp"
    },
    "Âm thanh (.mp3, .wav, .flac, .aac, .m4a, .ogg)": {
        ".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg", ".wma"
    },
    "File nén (.zip, .rar, .7z, .tar, .gz, .iso)": {
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso"
    },
    "Mã nguồn (.py, .js, .html, .css, .json, .cpp, .java, .sql)": {
        ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".json", ".cpp", ".c", ".h",
        ".cs", ".java", ".sql", ".sh", ".bat", ".xml", ".yaml", ".yml", ".md"
    },
    "Tùy chỉnh đuôi file...": "custom"
}

# ─── Lớp Lõi Quét File Đệ Quy Siêu Tốc (Fast File Scanner) ────────────────────
class FileScannerEngine:
    """Quét thư mục bằng os.scandir kết hợp thuật toán ngăn xếp để tránh tràn stack."""
    def __init__(self, root_dir: str, filters: dict, result_queue: queue.Queue, stop_event: threading.Event):
        self.root_dir = root_dir
        self.filters = filters
        self.result_queue = result_queue
        self.stop_event = stop_event
        self.scanned_folders = 0
        self.scanned_files = 0
        self.matched_files = 0
        self.total_size_bytes = 0

    def run(self):
        start_time = time.perf_counter()
        stack = [self.root_dir]
        last_progress_time = 0

        while stack and not self.stop_event.is_set():
            current_dir = stack.pop()
            self.scanned_folders += 1

            try:
                # Quét nhanh không theo symlink để tránh vòng lặp vô hạn
                with os.scandir(current_dir) as entries:
                    for entry in entries:
                        if self.stop_event.is_set():
                            break

                        try:
                            # Nếu là thư mục con, đẩy vào ngăn xếp để duyệt tiếp
                            if entry.is_dir(follow_symlinks=False):
                                stack.append(entry.path)
                                continue

                            # Nếu là file, kiểm tra thuộc tính
                            if entry.is_file(follow_symlinks=False):
                                self.scanned_files += 1
                                stat = entry.stat(follow_symlinks=False)
                                
                                # Kiểm tra bộ lọc
                                if self._matches_filter(entry.name, stat):
                                    self.matched_files += 1
                                    self.total_size_bytes += stat.st_size
                                    
                                    self.result_queue.put({
                                        "type": "file",
                                        "name": entry.name,
                                        "mtime": stat.st_mtime,
                                        "mtime_str": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                                        "size": stat.st_size,
                                        "size_str": format_file_size(stat.st_size),
                                        "folder": os.path.normpath(current_dir),
                                        "full_path": os.path.normpath(entry.path),
                                    })

                        except (PermissionError, FileNotFoundError, OSError):
                            continue

            except (PermissionError, FileNotFoundError, OSError):
                continue

            # Cập nhật tiến độ định kỳ mỗi 80ms
            now = time.perf_counter()
            if now - last_progress_time > 0.08:
                last_progress_time = now
                self.result_queue.put({
                    "type": "progress",
                    "folders": self.scanned_folders,
                    "files": self.scanned_files,
                    "matched": self.matched_files,
                    "total_size": self.total_size_bytes,
                    "elapsed": now - start_time
                })

        elapsed = time.perf_counter() - start_time
        self.result_queue.put({
            "type": "done",
            "cancelled": self.stop_event.is_set(),
            "folders": self.scanned_folders,
            "files": self.scanned_files,
            "matched": self.matched_files,
            "total_size": self.total_size_bytes,
            "elapsed": elapsed
        })

    def _matches_filter(self, filename: str, stat) -> bool:
        # 1. Lọc từ khóa tên file
        keyword = self.filters.get("keyword")
        if keyword and keyword.lower() not in filename.lower():
            return False

        # 2. Lọc đuôi file
        allowed_exts = self.filters.get("extensions")
        if allowed_exts:
            _, ext = os.path.splitext(filename)
            if ext.lower() not in allowed_exts:
                return False

        # 3. Lọc kích thước
        min_size = self.filters.get("min_size")
        if min_size is not None and stat.st_size < min_size:
            return False

        max_size = self.filters.get("max_size")
        if max_size is not None and stat.st_size > max_size:
            return False

        # 4. Lọc ngày chỉnh sửa
        min_mtime = self.filters.get("min_mtime")
        if min_mtime is not None and stat.st_mtime < min_mtime:
            return False

        max_mtime = self.filters.get("max_mtime")
        if max_mtime is not None and stat.st_mtime > max_mtime:
            return False

        return True


# ─── Giao Diện Ứng Dụng (LocFile App GUI) ───────────────────────────────────
class LocFileApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("LocFile - Ứng Dụng Lọc File Siêu Tốc Windows")
        self.geometry("1150x760")
        self.minsize(920, 600)
        ctk.set_appearance_mode("Dark")
        self.configure(fg_color=PALETTE["bg"])

        # Quản lý luồng quét
        self.scanner_thread = None
        self.stop_event = threading.Event()
        self.result_queue = queue.Queue()
        self.is_scanning = False

        # Lưu trữ dữ liệu bảng kết quả để phục vụ sắp xếp
        self.all_items = {}  # iid -> dict data
        self.sort_state = {"column": "mtime", "reverse": True}

        # Khởi tạo giao diện
        self._setup_styles()
        self._build_ui()
        self._bind_shortcuts()

    def _setup_styles(self):
        """Cấu hình Treeview Dark Mode theo chuẩn C-Engine Zero-Lag."""
        style = ttk.Style()
        style.theme_use("clam")

        # Cấu hình bảng Treeview
        style.configure(
            "Custom.Treeview",
            background=PALETTE["tree_bg"],
            foreground=PALETTE["tree_fg"],
            fieldbackground=PALETTE["tree_bg"],
            borderwidth=0,
            font=("Segoe UI", 10),
            rowheight=26
        )
        style.map(
            "Custom.Treeview",
            background=[("selected", PALETTE["tree_select"])],
            foreground=[("selected", "#ffffff")]
        )

        # Cấu hình thanh tiêu đề cột (Headers)
        style.configure(
            "Custom.Treeview.Heading",
            background=PALETTE["tree_header"],
            foreground=PALETTE["tree_header_fg"],
            font=("Segoe UI", 10, "bold"),
            borderwidth=1,
            relief="flat",
            padding=(6, 4)
        )
        style.map(
            "Custom.Treeview.Heading",
            background=[("active", PALETTE["card_alt"])],
            foreground=[("active", "#ffffff")]
        )

        # Cấu hình Scrollbar
        style.configure(
            "Custom.Vertical.TScrollbar",
            background=PALETTE["card"],
            troughcolor=PALETTE["bg"],
            bordercolor=PALETTE["bg"],
            arrowcolor=PALETTE["text_muted"],
            relief="flat"
        )
        style.configure(
            "Custom.Horizontal.TScrollbar",
            background=PALETTE["card"],
            troughcolor=PALETTE["bg"],
            bordercolor=PALETTE["bg"],
            arrowcolor=PALETTE["text_muted"],
            relief="flat"
        )

    def _build_ui(self):
        # ─── 1. Khung chọn Thư mục gốc (Root Folder) ────────────────────────
        folder_card = ctk.CTkFrame(self, fg_color=PALETTE["card"], corner_radius=8, border_width=1, border_color=PALETTE["border"])
        folder_card.pack(fill="x", padx=14, pady=(12, 6))

        lbl_folder = ctk.CTkLabel(folder_card, text="📁 Thư mục gốc:", font=("Segoe UI", 12, "bold"), text_color=PALETTE["accent"])
        lbl_folder.pack(side="left", padx=(12, 8), pady=10)

        self.entry_root = ctk.CTkEntry(
            folder_card,
            placeholder_text="Chọn hoặc dán đường dẫn thư mục cần quét (Ví dụ: D:\\DuLieu hoặc C:\\Users)...",
            font=("Segoe UI", 11),
            fg_color=PALETTE["bg"],
            border_color=PALETTE["border"],
            text_color=PALETTE["text"]
        )
        self.entry_root.pack(side="left", fill="x", expand=True, padx=4, pady=10)

        btn_browse = ctk.CTkButton(
            folder_card,
            text="Chọn Thư Mục...",
            width=130,
            command=self._on_browse_folder,
            fg_color=PALETTE["accent"],
            hover_color=PALETTE["accent_hover"],
            text_color="#11111b",
            font=("Segoe UI", 11, "bold")
        )
        btn_browse.pack(side="left", padx=4, pady=10)

        btn_paste = ctk.CTkButton(
            folder_card,
            text="Dán",
            width=60,
            command=self._on_paste_path,
            fg_color=PALETTE["card_alt"],
            hover_color=PALETTE["border"],
            text_color=PALETTE["text"],
            font=("Segoe UI", 11)
        )
        btn_paste.pack(side="left", padx=(4, 12), pady=10)

        # ─── 2. Khung Bộ lọc tìm kiếm (Filter Options) ──────────────────────
        filter_card = ctk.CTkFrame(self, fg_color=PALETTE["card"], corner_radius=8, border_width=1, border_color=PALETTE["border"])
        filter_card.pack(fill="x", padx=14, pady=6)

        # Hàng 1: Ngày sửa đổi (Date Modified)
        row1 = ctk.CTkFrame(filter_card, fg_color="transparent")
        row1.pack(fill="x", padx=12, pady=(10, 5))

        lbl_date = ctk.CTkLabel(row1, text="🕒 Ngày sửa đổi:", font=("Segoe UI", 11, "bold"), width=110, anchor="w", text_color=PALETTE["text"])
        lbl_date.pack(side="left")

        self.var_date_quick = ctk.StringVar(value="Tất cả thời gian")
        self.cb_date_quick = ctk.CTkComboBox(
            row1,
            values=["Tất cả thời gian", "Hôm nay", "3 ngày qua", "7 ngày qua", "30 ngày qua", "90 ngày qua", "Năm nay", "Tùy chỉnh khoảng ngày"],
            variable=self.var_date_quick,
            command=self._on_date_preset_changed,
            width=180,
            font=("Segoe UI", 11),
            fg_color=PALETTE["bg"],
            border_color=PALETTE["border"]
        )
        self.cb_date_quick.pack(side="left", padx=(0, 10))

        self.lbl_from_date = ctk.CTkLabel(row1, text="Từ:", font=("Segoe UI", 11), text_color=PALETTE["text_muted"])
        self.lbl_from_date.pack(side="left", padx=(0, 4))
        self.entry_date_from = ctk.CTkEntry(row1, placeholder_text="YYYY-MM-DD", width=110, font=("Segoe UI", 11), fg_color=PALETTE["bg"], border_color=PALETTE["border"])
        self.entry_date_from.pack(side="left", padx=(0, 10))

        self.lbl_to_date = ctk.CTkLabel(row1, text="Đến:", font=("Segoe UI", 11), text_color=PALETTE["text_muted"])
        self.lbl_to_date.pack(side="left", padx=(0, 4))
        self.entry_date_to = ctk.CTkEntry(row1, placeholder_text="YYYY-MM-DD", width=110, font=("Segoe UI", 11), fg_color=PALETTE["bg"], border_color=PALETTE["border"])
        self.entry_date_to.pack(side="left", padx=(0, 15))

        # Thêm lọc từ khóa trong tên file
        lbl_kw = ctk.CTkLabel(row1, text="Tên file chứa:", font=("Segoe UI", 11, "bold"), text_color=PALETTE["text"])
        lbl_kw.pack(side="left", padx=(10, 6))
        self.entry_keyword = ctk.CTkEntry(row1, placeholder_text="Tìm theo từ khóa tên file...", font=("Segoe UI", 11), fg_color=PALETTE["bg"], border_color=PALETTE["border"])
        self.entry_keyword.pack(side="left", fill="x", expand=True)

        # Hàng 2: Kích thước file (File Size) & Định dạng file (Extension)
        row2 = ctk.CTkFrame(filter_card, fg_color="transparent")
        row2.pack(fill="x", padx=12, pady=(5, 10))

        lbl_size = ctk.CTkLabel(row2, text="⚖️ Dung lượng:", font=("Segoe UI", 11, "bold"), width=110, anchor="w", text_color=PALETTE["text"])
        lbl_size.pack(side="left")

        self.var_size_quick = ctk.StringVar(value="Tất cả dung lượng")
        self.cb_size_quick = ctk.CTkComboBox(
            row2,
            values=["Tất cả dung lượng", "< 1 MB", "1 MB - 10 MB", "10 MB - 100 MB", "> 100 MB", "Tùy chỉnh dung lượng"],
            variable=self.var_size_quick,
            command=self._on_size_preset_changed,
            width=180,
            font=("Segoe UI", 11),
            fg_color=PALETTE["bg"],
            border_color=PALETTE["border"]
        )
        self.cb_size_quick.pack(side="left", padx=(0, 10))

        self.lbl_size_min = ctk.CTkLabel(row2, text="Min (MB):", font=("Segoe UI", 11), text_color=PALETTE["text_muted"])
        self.lbl_size_min.pack(side="left", padx=(0, 4))
        self.entry_size_min = ctk.CTkEntry(row2, placeholder_text="0", width=65, font=("Segoe UI", 11), fg_color=PALETTE["bg"], border_color=PALETTE["border"])
        self.entry_size_min.pack(side="left", padx=(0, 10))

        self.lbl_size_max = ctk.CTkLabel(row2, text="Max (MB):", font=("Segoe UI", 11), text_color=PALETTE["text_muted"])
        self.lbl_size_max.pack(side="left", padx=(0, 4))
        self.entry_size_max = ctk.CTkEntry(row2, placeholder_text="100", width=65, font=("Segoe UI", 11), fg_color=PALETTE["bg"], border_color=PALETTE["border"])
        self.entry_size_max.pack(side="left", padx=(0, 15))

        lbl_ext = ctk.CTkLabel(row2, text="Loại file:", font=("Segoe UI", 11, "bold"), text_color=PALETTE["text"])
        lbl_ext.pack(side="left", padx=(10, 6))

        self.var_ext_group = ctk.StringVar(value="Tất cả file (*.*)")
        self.cb_ext_group = ctk.CTkComboBox(
            row2,
            values=list(EXTENSION_GROUPS.keys()),
            variable=self.var_ext_group,
            command=self._on_ext_group_changed,
            width=240,
            font=("Segoe UI", 11),
            fg_color=PALETTE["bg"],
            border_color=PALETTE["border"]
        )
        self.cb_ext_group.pack(side="left", padx=(0, 6))

        self.entry_custom_ext = ctk.CTkEntry(
            row2,
            placeholder_text="Nhập đuôi: pdf, docx, png...",
            width=160,
            font=("Segoe UI", 11),
            fg_color=PALETTE["bg"],
            border_color=PALETTE["border"]
        )
        self.entry_custom_ext.pack(side="left", fill="x", expand=True)

        self._update_filter_field_states()

        # ─── 3. Khung nút chức năng chính (Action Toolbar) ──────────────────
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=14, pady=(4, 6))

        self.btn_scan = ctk.CTkButton(
            toolbar,
            text="🔍 LỌC FILE (Quét)",
            width=150,
            height=34,
            command=self._start_scan,
            fg_color=PALETTE["accent"],
            hover_color=PALETTE["accent_hover"],
            text_color="#11111b",
            font=("Segoe UI", 12, "bold")
        )
        self.btn_scan.pack(side="left", padx=(0, 8))

        self.btn_stop = ctk.CTkButton(
            toolbar,
            text="⏹️ Dừng",
            width=90,
            height=34,
            command=self._stop_scan,
            fg_color=PALETTE["danger"],
            hover_color=PALETTE["danger_hover"],
            text_color="#11111b",
            font=("Segoe UI", 11, "bold"),
            state="disabled"
        )
        self.btn_stop.pack(side="left", padx=(0, 16))

        self.btn_open_selected = ctk.CTkButton(
            toolbar,
            text="🚀 Mở File Đã Chọn",
            width=140,
            height=34,
            command=self._open_selected_files,
            fg_color=PALETTE["card_alt"],
            hover_color=PALETTE["border"],
            text_color=PALETTE["text"],
            font=("Segoe UI", 11, "bold")
        )
        self.btn_open_selected.pack(side="left", padx=(0, 8))

        self.btn_open_folder = ctk.CTkButton(
            toolbar,
            text="📂 Mở Thư Mục Chứa",
            width=150,
            height=34,
            command=self._open_file_location,
            fg_color=PALETTE["card_alt"],
            hover_color=PALETTE["border"],
            text_color=PALETTE["text"],
            font=("Segoe UI", 11)
        )
        self.btn_open_folder.pack(side="left", padx=(0, 8))

        self.btn_select_all = ctk.CTkButton(
            toolbar,
            text="Chọn Tất Cả (Ctrl+A)",
            width=140,
            height=34,
            command=self._select_all_items,
            fg_color=PALETTE["card_alt"],
            hover_color=PALETTE["border"],
            text_color=PALETTE["text"],
            font=("Segoe UI", 11)
        )
        self.btn_select_all.pack(side="left", padx=(0, 8))

        self.btn_clear = ctk.CTkButton(
            toolbar,
            text="Xóa Bảng",
            width=90,
            height=34,
            command=self._clear_results,
            fg_color=PALETTE["card_alt"],
            hover_color=PALETTE["border"],
            text_color=PALETTE["text_muted"],
            font=("Segoe UI", 11)
        )
        self.btn_clear.pack(side="right")

        # ─── 4. Bảng hiển thị kết quả (Results Table - ttk.Treeview) ────────
        table_container = ctk.CTkFrame(self, fg_color=PALETTE["card"], corner_radius=8, border_width=1, border_color=PALETTE["border"])
        table_container.pack(fill="both", expand=True, padx=14, pady=6)

        # Thanh cuộn
        vsb = ttk.Scrollbar(table_container, orient="vertical", style="Custom.Vertical.TScrollbar")
        hsb = ttk.Scrollbar(table_container, orient="horizontal", style="Custom.Horizontal.TScrollbar")

        columns = ("name", "mtime", "size", "folder")
        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show="headings",
            selectmode="extended",
            style="Custom.Treeview",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set
        )

        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)

        # Định cấu hình cột và sắp xếp khi click
        self.tree.heading("name", text="Tên File", anchor="w", command=lambda: self._sort_column("name"))
        self.tree.heading("mtime", text="Ngày Sửa Đổi ▼", anchor="w", command=lambda: self._sort_column("mtime"))
        self.tree.heading("size", text="Dung Lượng", anchor="e", command=lambda: self._sort_column("size"))
        self.tree.heading("folder", text="Đường Dẫn Thư Mục", anchor="w", command=lambda: self._sort_column("folder"))

        self.tree.column("name", width=320, minwidth=180, anchor="w")
        self.tree.column("mtime", width=160, minwidth=140, anchor="w")
        self.tree.column("size", width=110, minwidth=90, anchor="e")
        self.tree.column("folder", width=460, minwidth=250, anchor="w")

        # Layout Treeview và Scrollbars
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(2, 0), pady=(2, 0))
        vsb.grid(row=0, column=1, sticky="ns", pady=(2, 0))
        hsb.grid(row=1, column=0, sticky="ew", padx=(2, 0))

        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        # Sự kiện click và phím tắt trên bảng
        self.tree.bind("<Double-Button-1>", lambda e: self._open_selected_files())
        self.tree.bind("<Return>", lambda e: self._open_selected_files())
        self.tree.bind("<Button-3>", self._show_context_menu)

        # Context Menu chuột phải
        self.context_menu = tk.Menu(self, tearoff=0, bg=PALETTE["card_alt"], fg=PALETTE["text"], activebackground=PALETTE["accent"], activeforeground="#11111b", bd=1)
        self.context_menu.add_command(label="Mở File", command=self._open_selected_files)
        self.context_menu.add_command(label="Mở Thư Mục Chứa (Explorer)", command=self._open_file_location)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Sao Chép Đường Dẫn Đầy Đủ", command=self._copy_paths_to_clipboard)
        self.context_menu.add_command(label="Sao Chép Tên File", command=self._copy_names_to_clipboard)

        # ─── 5. Thanh trạng thái & Tiến trình (Status Bar) ───────────────────
        status_bar = ctk.CTkFrame(self, fg_color=PALETTE["card"], corner_radius=6, height=36, border_width=1, border_color=PALETTE["border"])
        status_bar.pack(fill="x", padx=14, pady=(2, 10))

        self.lbl_status = ctk.CTkLabel(
            status_bar,
            text="Sẵn sàng. Hãy chọn thư mục gốc và nhấn [Lọc File].",
            font=("Segoe UI", 10),
            text_color=PALETTE["text_muted"]
        )
        self.lbl_status.pack(side="left", padx=12, pady=4)

        self.lbl_selection = ctk.CTkLabel(
            status_bar,
            text="Đang chọn: 0 file",
            font=("Segoe UI", 10, "bold"),
            text_color=PALETTE["accent"]
        )
        self.lbl_selection.pack(side="right", padx=12, pady=4)

        self.tree.bind("<<TreeviewSelect>>", self._on_tree_selection_changed)

    def _bind_shortcuts(self):
        """Đăng ký các phím tắt tiện dụng."""
        self.bind("<Control-a>", lambda e: self._select_all_items())
        self.bind("<Control-A>", lambda e: self._select_all_items())
        self.bind("<F5>", lambda e: self._start_scan())

    # ─── Xử lý Tương tác Filter Form ───────────────────────────────────────
    def _on_browse_folder(self):
        folder = filedialog.askdirectory(title="Chọn Thư Mục Gốc Cần Quét")
        if folder:
            self.entry_root.delete(0, "end")
            self.entry_root.insert(0, os.path.normpath(folder))

    def _on_paste_path(self):
        try:
            clipboard = self.clipboard_get().strip().strip('"').strip("'")
            if os.path.isdir(clipboard):
                self.entry_root.delete(0, "end")
                self.entry_root.insert(0, os.path.normpath(clipboard))
            else:
                messagebox.showinfo("Thông Báo", "Nội dung trong clipboard không phải là một đường dẫn thư mục hợp lệ.")
        except Exception:
            pass

    def _on_date_preset_changed(self, choice):
        now = datetime.now()
        if choice == "Hôm nay":
            today_str = now.strftime("%Y-%m-%d")
            self.entry_date_from.delete(0, "end")
            self.entry_date_from.insert(0, today_str)
            self.entry_date_to.delete(0, "end")
            self.entry_date_to.insert(0, today_str)
        elif choice == "3 ngày qua":
            self.entry_date_from.delete(0, "end")
            self.entry_date_from.insert(0, (now - timedelta(days=3)).strftime("%Y-%m-%d"))
            self.entry_date_to.delete(0, "end")
            self.entry_date_to.insert(0, now.strftime("%Y-%m-%d"))
        elif choice == "7 ngày qua":
            self.entry_date_from.delete(0, "end")
            self.entry_date_from.insert(0, (now - timedelta(days=7)).strftime("%Y-%m-%d"))
            self.entry_date_to.delete(0, "end")
            self.entry_date_to.insert(0, now.strftime("%Y-%m-%d"))
        elif choice == "30 ngày qua":
            self.entry_date_from.delete(0, "end")
            self.entry_date_from.insert(0, (now - timedelta(days=30)).strftime("%Y-%m-%d"))
            self.entry_date_to.delete(0, "end")
            self.entry_date_to.insert(0, now.strftime("%Y-%m-%d"))
        elif choice == "90 ngày qua":
            self.entry_date_from.delete(0, "end")
            self.entry_date_from.insert(0, (now - timedelta(days=90)).strftime("%Y-%m-%d"))
            self.entry_date_to.delete(0, "end")
            self.entry_date_to.insert(0, now.strftime("%Y-%m-%d"))
        elif choice == "Năm nay":
            self.entry_date_from.delete(0, "end")
            self.entry_date_from.insert(0, f"{now.year}-01-01")
            self.entry_date_to.delete(0, "end")
            self.entry_date_to.insert(0, now.strftime("%Y-%m-%d"))
        elif choice == "Tất cả thời gian":
            self.entry_date_from.delete(0, "end")
            self.entry_date_to.delete(0, "end")

        self._update_filter_field_states()

    def _on_size_preset_changed(self, choice):
        if choice == "< 1 MB":
            self.entry_size_min.delete(0, "end")
            self.entry_size_min.insert(0, "0")
            self.entry_size_max.delete(0, "end")
            self.entry_size_max.insert(0, "1")
        elif choice == "1 MB - 10 MB":
            self.entry_size_min.delete(0, "end")
            self.entry_size_min.insert(0, "1")
            self.entry_size_max.delete(0, "end")
            self.entry_size_max.insert(0, "10")
        elif choice == "10 MB - 100 MB":
            self.entry_size_min.delete(0, "end")
            self.entry_size_min.insert(0, "10")
            self.entry_size_max.delete(0, "end")
            self.entry_size_max.insert(0, "100")
        elif choice == "> 100 MB":
            self.entry_size_min.delete(0, "end")
            self.entry_size_min.insert(0, "100")
            self.entry_size_max.delete(0, "end")
        elif choice == "Tất cả dung lượng":
            self.entry_size_min.delete(0, "end")
            self.entry_size_max.delete(0, "end")

        self._update_filter_field_states()

    def _on_ext_group_changed(self, choice):
        val = EXTENSION_GROUPS.get(choice)
        if val == "custom":
            self.entry_custom_ext.configure(state="normal")
            self.entry_custom_ext.focus_set()
        else:
            self.entry_custom_ext.delete(0, "end")
            self.entry_custom_ext.configure(state="disabled")

    def _update_filter_field_states(self):
        # Trạng thái ngày
        if self.var_date_quick.get() == "Tùy chỉnh khoảng ngày":
            self.entry_date_from.configure(state="normal")
            self.entry_date_to.configure(state="normal")
        elif self.var_date_quick.get() == "Tất cả thời gian":
            self.entry_date_from.configure(state="disabled")
            self.entry_date_to.configure(state="disabled")
        else:
            self.entry_date_from.configure(state="normal")
            self.entry_date_to.configure(state="normal")

        # Trạng thái kích thước
        if self.var_size_quick.get() == "Tất cả dung lượng":
            self.entry_size_min.configure(state="disabled")
            self.entry_size_max.configure(state="disabled")
        else:
            self.entry_size_min.configure(state="normal")
            self.entry_size_max.configure(state="normal")

    # ─── Thu thập và Kiểm tra tính hợp lệ của Bộ Lọc ───────────────────────
    def _collect_filters(self):
        filters = {}

        # 1. Từ khóa tên file
        kw = self.entry_keyword.get().strip()
        if kw:
            filters["keyword"] = kw

        # 2. Định dạng file
        ext_choice = self.var_ext_group.get()
        group_val = EXTENSION_GROUPS.get(ext_choice)
        if group_val == "custom":
            custom_input = self.entry_custom_ext.get().strip()
            if custom_input:
                # Chuẩn hóa: tách bởi phẩy hoặc khoảng trắng, thêm dấu chấm nếu thiếu
                cleaned_exts = set()
                for item in custom_input.replace(",", " ").split():
                    item = item.strip().lower()
                    if item:
                        if not item.startswith("."):
                            item = "." + item
                        cleaned_exts.add(item)
                if cleaned_exts:
                    filters["extensions"] = cleaned_exts
        elif isinstance(group_val, set):
            filters["extensions"] = group_val

        # 3. Kích thước (MB -> bytes)
        min_size_str = self.entry_size_min.get().strip()
        if min_size_str:
            try:
                filters["min_size"] = int(float(min_size_str) * 1024 * 1024)
            except ValueError:
                messagebox.showerror("Lỗi Nhập Liệu", "Dung lượng Min phải là con số hợp lệ (MB)!")
                return None

        max_size_str = self.entry_size_max.get().strip()
        if max_size_str:
            try:
                filters["max_size"] = int(float(max_size_str) * 1024 * 1024)
            except ValueError:
                messagebox.showerror("Lỗi Nhập Liệu", "Dung lượng Max phải là con số hợp lệ (MB)!")
                return None

        # 4. Ngày tháng
        from_str = self.entry_date_from.get().strip()
        if from_str:
            dt_from = parse_date_str(from_str)
            if not dt_from:
                messagebox.showerror("Lỗi Định Dạng Ngày", f"Ngày bắt đầu '{from_str}' không hợp lệ! Vui lòng dùng định dạng YYYY-MM-DD.")
                return None
            filters["min_mtime"] = dt_from.timestamp()

        to_str = self.entry_date_to.get().strip()
        if to_str:
            dt_to = parse_date_str(to_str)
            if not dt_to:
                messagebox.showerror("Lỗi Định Dạng Ngày", f"Ngày kết thúc '{to_str}' không hợp lệ! Vui lòng dùng định dạng YYYY-MM-DD.")
                return None
            # Tính đến hết ngày (23:59:59)
            dt_to_end = dt_to.replace(hour=23, minute=59, second=59)
            filters["max_mtime"] = dt_to_end.timestamp()

        return filters

    # ─── Điều Khiển Quét Đa Luồng (Multi-threading Controller) ─────────────
    def _start_scan(self):
        if self.is_scanning:
            return

        root_folder = self.entry_root.get().strip()
        if not root_folder:
            messagebox.showwarning("Cảnh Báo", "Vui lòng chọn hoặc nhập đường dẫn Thư mục gốc cần quét!")
            self.entry_root.focus_set()
            return

        if not os.path.isdir(root_folder):
            messagebox.showerror("Lỗi Thư Mục", f"Thư mục không tồn tại hoặc không thể truy cập:\n{root_folder}")
            return

        filters = self._collect_filters()
        if filters is None:
            return

        # Làm sạch bảng trước khi quét mới
        self._clear_results()

        # Thiết lập cờ trạng thái
        self.is_scanning = True
        self.stop_event.clear()
        while not self.result_queue.empty():
            try:
                self.result_queue.get_nowait()
            except queue.Empty:
                break

        self.btn_scan.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.lbl_status.configure(text=f"Đang quét đệ quy: {root_folder} ...", text_color=PALETTE["accent"])

        # Khởi chạy luồng chạy ngầm
        engine = FileScannerEngine(root_folder, filters, self.result_queue, self.stop_event)
        self.scanner_thread = threading.Thread(target=engine.run, daemon=True)
        self.scanner_thread.start()

        # Bắt đầu vòng lặp cập nhật UI từ Queue
        self.after(30, self._process_queue_batch)

    def _stop_scan(self):
        if self.is_scanning:
            self.stop_event.set()
            self.lbl_status.configure(text="Đang gửi lệnh dừng quét...", text_color=PALETTE["danger"])
            self.btn_stop.configure(state="disabled")

    def _process_queue_batch(self):
        """Xử lý hàng đợi theo đợt để đảm bảo UI mượt 60fps không bị giật lag."""
        batch_limit = 200
        items_processed = 0

        while items_processed < batch_limit:
            try:
                msg = self.result_queue.get_nowait()
            except queue.Empty:
                break

            msg_type = msg.get("type")
            if msg_type == "file":
                iid = str(len(self.all_items) + 1)
                self.all_items[iid] = msg
                self.tree.insert("", "end", iid=iid, values=(
                    msg["name"],
                    msg["mtime_str"],
                    msg["size_str"],
                    msg["folder"]
                ))
                items_processed += 1

            elif msg_type == "progress":
                matched = msg["matched"]
                scanned = msg["files"]
                folders = msg["folders"]
                elapsed = msg["elapsed"]
                self.lbl_status.configure(
                    text=f"⏳ Đang quét: {folders:,} thư mục | {scanned:,} file | Tìm thấy: {matched:,} file ({elapsed:.1f}s)",
                    text_color=PALETTE["accent"]
                )

            elif msg_type == "done":
                self.is_scanning = False
                self.btn_scan.configure(state="normal")
                self.btn_stop.configure(state="disabled")

                matched = msg["matched"]
                scanned = msg["files"]
                folders = msg["folders"]
                elapsed = msg["elapsed"]
                total_size_str = format_file_size(msg["total_size"])
                status_prefix = "⏹️ Đã dừng" if msg.get("cancelled") else "✅ Hoàn tất"

                self.lbl_status.configure(
                    text=f"{status_prefix}: Tìm thấy {matched:,} file ({total_size_str}) / Đã quét {scanned:,} file trong {folders:,} thư mục ({elapsed:.2f} giây).",
                    text_color=PALETTE["success"] if not msg.get("cancelled") else PALETTE["danger"]
                )
                return

        # Tiếp tục chu kỳ sau nếu vẫn còn quét hoặc queue còn dữ liệu
        if self.is_scanning or not self.result_queue.empty():
            self.after(30, self._process_queue_batch)

    # ─── Thao Tác Với Dòng Kết Quả (File Actions) ───────────────────────────
    def _get_selected_file_paths(self):
        selected_iids = self.tree.selection()
        paths = []
        for iid in selected_iids:
            data = self.all_items.get(iid)
            if data and "full_path" in data:
                paths.append(data["full_path"])
        return paths

    def _open_selected_files(self):
        """Mở các file được chọn bằng ứng dụng mặc định của Windows (os.startfile)."""
        paths = self._get_selected_file_paths()
        if not paths:
            messagebox.showinfo("Thông Báo", "Vui lòng chọn ít nhất một file trong bảng để mở!")
            return

        # Bảo vệ hệ thống: Cảnh báo nếu mở cùng lúc quá nhiều file
        if len(paths) > 10:
            confirm = messagebox.askyesno(
                "Xác Nhận Mở Hàng Loạt",
                f"Bạn đang chuẩn bị mở đồng thời {len(paths)} file bằng ứng dụng mặc định.\n\n"
                "Việc này có thể chiếm nhiều RAM hoặc mở nhiều cửa sổ cùng lúc.\n"
                "Bạn có chắc chắn muốn tiếp tục không?"
            )
            if not confirm:
                return

        opened_count = 0
        failed_count = 0
        for p in paths:
            try:
                os.startfile(p)
                opened_count += 1
            except Exception as err:
                failed_count += 1

        if failed_count > 0:
            messagebox.showwarning("Kết Quả", f"Đã mở {opened_count} file. Có {failed_count} file không thể mở được.")

    def _open_file_location(self):
        """Mở thư mục chứa và bôi đậm file trong Windows Explorer."""
        paths = self._get_selected_file_paths()
        if not paths:
            messagebox.showinfo("Thông Báo", "Vui lòng chọn file cần mở thư mục vị trí!")
            return

        # Giới hạn mở tối đa 5 cửa sổ Explorer để tránh treo máy
        to_open = paths[:5]
        for p in to_open:
            norm_p = os.path.normpath(p)
            if os.path.exists(norm_p):
                subprocess.Popen(f'explorer /select,"{norm_p}"')
            elif os.path.exists(os.path.dirname(norm_p)):
                os.startfile(os.path.dirname(norm_p))

        if len(paths) > 5:
            messagebox.showinfo("Ghi Chú", f"Đã mở vị trí của 5 file đầu tiên (trong tổng số {len(paths)} file được chọn).")

    def _copy_paths_to_clipboard(self):
        paths = self._get_selected_file_paths()
        if not paths:
            return
        text = "\n".join(paths)
        self.clipboard_clear()
        self.clipboard_append(text)
        self.lbl_status.configure(text=f"📋 Đã sao chép {len(paths)} đường dẫn vào Clipboard.", text_color=PALETTE["accent"])

    def _copy_names_to_clipboard(self):
        selected_iids = self.tree.selection()
        names = []
        for iid in selected_iids:
            data = self.all_items.get(iid)
            if data:
                names.append(data["name"])
        if names:
            text = "\n".join(names)
            self.clipboard_clear()
            self.clipboard_append(text)
            self.lbl_status.configure(text=f"📋 Đã sao chép {len(names)} tên file vào Clipboard.", text_color=PALETTE["accent"])

    def _select_all_items(self):
        all_iids = self.tree.get_children()
        if all_iids:
            self.tree.selection_set(all_iids)

    def _clear_results(self):
        self.tree.delete(*self.tree.get_children())
        self.all_items.clear()
        self.lbl_selection.configure(text="Đang chọn: 0 file")
        if not self.is_scanning:
            self.lbl_status.configure(text="Bảng kết quả đã được làm sạch.", text_color=PALETTE["text_muted"])

    def _on_tree_selection_changed(self, event):
        count = len(self.tree.selection())
        self.lbl_selection.configure(text=f"Đang chọn: {count:,} file")

    def _show_context_menu(self, event):
        # Chọn item dưới con trỏ chuột nếu chưa được chọn
        iid = self.tree.identify_row(event.y)
        if iid:
            if iid not in self.tree.selection():
                self.tree.selection_set(iid)
            self.context_menu.post(event.x_root, event.y_root)

    # ─── Sắp Xếp Cột Bảng Kết Quả (Intelligent Column Sorting) ─────────────
    def _sort_column(self, col: str):
        """Sắp xếp thông minh dựa trên giá trị gốc (kích thước theo bytes, ngày theo timestamp)."""
        if self.sort_state["column"] == col:
            self.sort_state["reverse"] = not self.sort_state["reverse"]
        else:
            self.sort_state["column"] = col
            self.sort_state["reverse"] = False

        reverse = self.sort_state["reverse"]

        # Cập nhật ký hiệu mũi tên trên tiêu đề cột
        col_titles = {
            "name": "Tên File",
            "mtime": "Ngày Sửa Đổi",
            "size": "Dung Lượng",
            "folder": "Đường Dẫn Thư Mục"
        }
        for c, title in col_titles.items():
            if c == col:
                arrow = " ▲" if not reverse else " ▼"
                self.tree.heading(c, text=f"{title}{arrow}")
            else:
                self.tree.heading(c, text=title)

        # Lấy danh sách item kèm giá trị gốc để sort
        items_to_sort = []
        for iid in self.tree.get_children():
            data = self.all_items.get(iid, {})
            if col == "name":
                val = data.get("name", "").lower()
            elif col == "mtime":
                val = data.get("mtime", 0.0)
            elif col == "size":
                val = data.get("size", 0)
            elif col == "folder":
                val = data.get("folder", "").lower()
            else:
                val = ""
            items_to_sort.append((val, iid))

        items_to_sort.sort(key=lambda x: x[0], reverse=reverse)

        # Di chuyển lại vị trí trên Treeview
        for index, (_, iid) in enumerate(items_to_sort):
            self.tree.move(iid, "", index)


# ─── Điểm Khởi Chạy Ứng Dụng (Main Entry Point) ────────────────────────────
if __name__ == "__main__":
    app = LocFileApp()
    app.mainloop()
