"""
VocabApp.py — Ứng dụng quản lý Học Từ Vựng Đa Ngôn Ngữ
Giao diện: CustomTkinter (Dark theme)
Database : data/*.json
Sync     : GitHub Pages + Google Drive
"""

import sys
import os
import json
import csv
import io
import threading
import webbrowser
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import customtkinter as ctk

# Fix UnicodeEncodeError trên Windows terminal
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", errors="replace").decode("ascii"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from database.database import (
    get_all_vocab, search_vocab, add_vocab, update_vocab,
    delete_vocab, get_stats, get_all_topics, get_all_types, get_all_dates,
    get_available_languages, find_vocab_by_word
)
from settings import load_settings, save_settings, update_github_settings, update_gdrive_settings
from api.github_sync import GitHubSync
from api.gdrive_sync import GDriveSync

# ─── Theme ────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

C = {
    "bg":      "#121212",
    "sidebar": "#1e1e1e",
    "card":    "#2c2c2c",
    "card2":   "#383838",
    "accent":  "#bb86fc",
    "accent2": "#9965f4",
    "text":    "#ffffff",
    "muted":   "#a0a0a0",
    "success": "#03dac6",
    "warn":    "#ffb300",
    "danger":  "#cf6679",
}

WORD_TYPES = ["", "Danh từ (n)", "Động từ (v)", "Tính từ (adj)", "Trạng từ (adv)", "Đại từ (pro)", "Giới từ (prep)", "Khác"]

# ══════════════════════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════════════════════
def lbl(parent, text, size=12, weight="normal", color=None, **kw):
    return ctk.CTkLabel(parent, text=text, text_color=color or C["text"],
                        font=ctk.CTkFont(size=size, weight=weight), **kw)

def sep(parent):
    ctk.CTkFrame(parent, height=1, fg_color=C["card2"]).pack(fill="x", padx=15, pady=6)

def enable_entry_undo(ctk_widget):
    w = ctk_widget._entry if hasattr(ctk_widget, "_entry") else ctk_widget
    w._undo_stack = [""]
    w._redo_stack = []
    
    def on_key(event):
        if event.keysym in ("Control_L", "Control_R", "Shift_L", "Shift_R", "Alt_L", "Alt_R", "Return", "Tab"):
            return
        current = w.get()
        if not w._undo_stack or w._undo_stack[-1] != current:
            w._undo_stack.append(current)
            if len(w._undo_stack) > 50:
                w._undo_stack.pop(0)
            w._redo_stack.clear()
            
    def undo(event):
        if len(w._undo_stack) > 1:
            current = w.get()
            if w._undo_stack[-1] == current:
                w._redo_stack.append(w._undo_stack.pop())
            if w._undo_stack:
                val = w._undo_stack[-1]
                w.delete(0, "end")
                w.insert(0, val)
        return "break"
        
    def redo(event):
        if w._redo_stack:
            val = w._redo_stack.pop()
            w._undo_stack.append(val)
            w.delete(0, "end")
            w.insert(0, val)
        return "break"
        
    w.bind("<KeyRelease>", on_key, add="+")
    w.bind("<Control-z>", undo)
    w.bind("<Control-y>", redo)

def entry(parent, placeholder="", width=440):
    e = ctk.CTkEntry(parent, placeholder_text=placeholder, width=width,
                        fg_color=C["card"], border_color=C["accent"],
                        text_color=C["text"], corner_radius=8)
    enable_entry_undo(e)
    return e

def combo(parent, values, width=200):
    c = ctk.CTkComboBox(parent, values=values, width=width,
                            fg_color=C["card"], border_color=C["accent"],
                            text_color=C["text"], button_color=C["accent"],
                            dropdown_fg_color=C["card2"])
    enable_entry_undo(c)
    return c

def btn(parent, text, color=None, hov=None, w=130, h=36, cmd=None, **kw):
    return ctk.CTkButton(parent, text=text,
                          fg_color=color or C["accent"], hover_color=hov or C["accent2"],
                          width=w, height=h, command=cmd,
                          font=ctk.CTkFont(size=13, weight="bold"), text_color="#121212" if color in [C["accent"], C["success"], C["warn"]] else C["text"], **kw)

# ══════════════════════════════════════════════════════════════════════════════
# Preview Dialog
# ══════════════════════════════════════════════════════════════════════════════
class PreviewDialog(ctk.CTkToplevel):
    def __init__(self, parent, title_text, markdown_text):
        super().__init__(parent)
        self.title("Preview: " + title_text)
        self.geometry("700x500")
        self.configure(fg_color=C["bg"])
        self.grab_set(); self.lift(); self.focus_force()
        
        scroll = ctk.CTkScrollableFrame(self, fg_color=C["bg"])
        scroll.pack(fill="both", expand=True, padx=10, pady=10)
        
        lbl(scroll, title_text, 15, "bold", C["accent"]).pack(anchor="w", pady=(5, 10))
        
        self.render_markdown(scroll, markdown_text)
        
        btn(self, "Đóng", C["card2"], C["danger"], w=100, h=34, cmd=self.destroy).pack(pady=10)
        
    def render_markdown(self, parent, text):
        lines = text.split('\n')
        current_text = []
        in_table = False
        table_lines = []
        
        for line in lines:
            if line.strip().startswith('|') and line.strip().endswith('|'):
                if not in_table:
                    if current_text:
                        self.flush_text(parent, current_text)
                        current_text = []
                    in_table = True
                table_lines.append(line.strip())
            else:
                if in_table:
                    self.flush_table(parent, table_lines)
                    table_lines = []
                    in_table = False
                current_text.append(line)
                
        if in_table:
            self.flush_table(parent, table_lines)
        elif current_text:
            self.flush_text(parent, current_text)

    def flush_text(self, parent, lines):
        text_str = '\n'.join(lines).strip()
        if text_str:
            lbl = ctk.CTkLabel(parent, text=text_str, justify="left", anchor="w", text_color=C["text"], wraplength=640, font=("Consolas", 14))
            lbl.pack(anchor="w", pady=4, padx=5)

    def flush_table(self, parent, table_lines):
        if len(table_lines) < 2:
            return
        headers = [c.strip() for c in table_lines[0].split('|')[1:-1]]
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background=C["card2"], foreground=C["text"], fieldbackground=C["card2"], rowheight=28)
        style.map('Treeview', background=[('selected', C["accent"])])
        style.configure("Treeview.Heading", background=C["card"], foreground=C["accent"], font=('Consolas', 11, 'bold'))

        tree = ttk.Treeview(parent, columns=headers, show='headings', height=min(len(table_lines)-2, 10))
        for h in headers:
            tree.heading(h, text=h)
            tree.column(h, width=120, anchor="w")
            
        for line in table_lines[2:]:
            cols = [c.strip() for c in line.split('|')[1:-1]]
            while len(cols) < len(headers): cols.append("")
            tree.insert('', 'end', values=cols[:len(headers)])
            
        tree.pack(fill="x", padx=5, pady=10)

# ══════════════════════════════════════════════════════════════════════════════
# Table Editor Dialog
# ══════════════════════════════════════════════════════════════════════════════
class TableEditorDialog(ctk.CTkToplevel):
    def __init__(self, parent, target_textbox):
        super().__init__(parent)
        self.title("Tạo / Sửa Bảng (Visual Editor)")
        self.geometry("800x500")
        self.configure(fg_color=C["bg"])
        self.grab_set(); self.lift(); self.focus_force()
        self.target_textbox = target_textbox
        
        self.rows = 3
        self.cols = 2
        self.entries = []
        
        toolbar = ctk.CTkFrame(self, fg_color=C["card"], height=50)
        toolbar.pack(fill="x", padx=10, pady=(10, 0))
        
        btn(toolbar, "+ Dòng", C["accent2"], C["accent"], w=80, h=30, cmd=self.add_row).pack(side="left", padx=5, pady=10)
        btn(toolbar, "- Dòng", C["card2"], C["danger"], w=80, h=30, cmd=self.del_row).pack(side="left", padx=5)
        btn(toolbar, "+ Cột", C["accent2"], C["accent"], w=80, h=30, cmd=self.add_col).pack(side="left", padx=20)
        btn(toolbar, "- Cột", C["card2"], C["danger"], w=80, h=30, cmd=self.del_col).pack(side="left", padx=5)
        
        btn(toolbar, "Chèn Bảng", C["success"], "#018786", w=150, h=30, cmd=self.insert_markdown).pack(side="right", padx=10)
        
        self.grid_frame = ctk.CTkScrollableFrame(self, fg_color=C["bg"])
        self.grid_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.render_grid()

    def render_grid(self):
        old_data = []
        for row in self.entries:
            old_data.append([e.get() for e in row])
            
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
            
        self.entries = []
        for r in range(self.rows):
            row_entries = []
            for c in range(self.cols):
                e = ctk.CTkEntry(self.grid_frame, width=150, fg_color=C["card"], text_color=C["text"])
                if r == 0:
                    e.configure(fg_color=C["card2"], font=ctk.CTkFont(weight="bold"))
                
                if r < len(old_data) and c < len(old_data[r]):
                    e.insert(0, old_data[r][c])
                elif r == 0:
                    e.insert(0, f"Cột {c+1}")
                    
                e.grid(row=r, column=c, padx=2, pady=2, sticky="nsew")
                enable_entry_undo(e)
                row_entries.append(e)
            self.entries.append(row_entries)

    def add_row(self):
        self.rows += 1
        self.render_grid()

    def del_row(self):
        if self.rows > 2:
            self.rows -= 1
            self.render_grid()

    def add_col(self):
        self.cols += 1
        self.render_grid()

    def del_col(self):
        if self.cols > 1:
            self.cols -= 1
            self.render_grid()

    def insert_markdown(self):
        md = []
        for r in range(self.rows):
            row_vals = []
            for c in range(self.cols):
                val = self.entries[r][c].get().strip().replace("|", "\\|")
                row_vals.append(val)
            md.append("| " + " | ".join(row_vals) + " |")
            if r == 0:
                md.append("|" + "|".join(["---"] * self.cols) + "|")
        
        text = "\n" + "\n".join(md) + "\n"
        self.target_textbox.insert("insert", text)
        self.destroy()

# ══════════════════════════════════════════════════════════════════════════════
# VocabFormDialog — Thêm / Sửa từ vựng
# ══════════════════════════════════════════════════════════════════════════════
class VocabFormDialog(ctk.CTkToplevel):
    def __init__(self, parent, vocab: dict = None):
        super().__init__(parent)
        self.app = parent
        self.vocab = vocab
        self.result = None
        is_edit = vocab is not None

        self.title("Sửa Từ Vựng" if is_edit else "Thêm Từ Vựng Mới")
        self.geometry("750x650")
        self.configure(fg_color=C["bg"])
        self.grab_set(); self.lift(); self.focus_force()

        self.bottom_frame = ctk.CTkFrame(self, fg_color=C["card"], height=60, corner_radius=0)
        self.bottom_frame.pack(side="bottom", fill="x")
        self.bottom_frame.pack_propagate(False)

        scroll = ctk.CTkScrollableFrame(self, fg_color=C["bg"])
        scroll.pack(side="top", fill="both", expand=True, padx=20, pady=15)

        def field(label_text, widget_fn):
            lbl(scroll, label_text, 12, "bold", C["accent"], anchor="w").pack(anchor="w", pady=(10,2))
            w = widget_fn()
            w.pack(fill="x", expand=True)
            return w

        # Từ vựng & Phát âm
        self.e_word  = field("Từ vựng *", lambda: entry(scroll, "Nhập từ vựng..."))
        self.e_pron  = field("Phát âm / Romaji / Pinyin", lambda: entry(scroll, "Cách đọc..."))

        # Nghĩa — dùng Textbox nhiều dòng
        row_mean = ctk.CTkFrame(scroll, fg_color="transparent")
        row_mean.pack(fill="x", pady=(10,2))
        lbl(row_mean, "Nghĩa của từ *", 12, "bold", C["accent"], anchor="w").pack(side="left")
        btn(row_mean, "👁 Preview", C["card2"], C["accent2"], w=90, h=24, cmd=lambda: PreviewDialog(self, "Nghĩa của từ", self.e_mean.get("1.0", "end"))).pack(side="left", padx=(15, 5))
        btn(row_mean, "▦ Tạo Bảng", C["card2"], C["accent2"], w=90, h=24, cmd=lambda: TableEditorDialog(self, self.e_mean)).pack(side="left")
        self.e_mean = ctk.CTkTextbox(scroll, height=100, fg_color=C["card"], border_color=C["accent"], text_color=C["text"], border_width=1, corner_radius=8, font=("Consolas", 14))
        self.e_mean.pack(fill="x", expand=True)
        self.e_mean._textbox.configure(undo=True, maxundo=-1, autoseparators=True)

        # Phân loại
        row1 = ctk.CTkFrame(scroll, fg_color="transparent")
        row1.pack(anchor="w", pady=(10,0))
        lbl(row1, "Loại từ", 12, "bold", C["accent"]).grid(row=0, column=0, sticky="w", padx=(0,30))
        self.e_type = combo(row1, WORD_TYPES)
        self.e_type.grid(row=1, column=0, padx=(0,20))
        lbl(row1, "Chủ đề", 12, "bold", C["accent"]).grid(row=0, column=1, sticky="w")
        self.e_topic = combo(row1, [], 200)
        self.e_topic.set("") # Clear default text
        self.e_topic.grid(row=1, column=1)

        # Date Tag
        self.e_date = field("Tag Ngày Học", lambda: combo(scroll, [], width=440))
        self.e_date.set("") # Clear default text

        # Mẫu câu
        row_ex = ctk.CTkFrame(scroll, fg_color="transparent")
        row_ex.pack(fill="x", pady=(10,2))
        lbl(row_ex, "Mẫu câu ví dụ", 12, "bold", C["accent"], anchor="w").pack(side="left")
        btn(row_ex, "👁 Preview", C["card2"], C["accent2"], w=90, h=24, cmd=lambda: PreviewDialog(self, "Mẫu câu ví dụ", self.e_ex.get("1.0", "end"))).pack(side="left", padx=(15, 5))
        btn(row_ex, "▦ Tạo Bảng", C["card2"], C["accent2"], w=90, h=24, cmd=lambda: TableEditorDialog(self, self.e_ex)).pack(side="left")
        self.e_ex = ctk.CTkTextbox(scroll, height=80, fg_color=C["card"], border_color=C["accent"], text_color=C["text"], border_width=1, corner_radius=8, font=("Consolas", 14))
        self.e_ex.pack(fill="x", expand=True)
        self.e_ex._textbox.configure(undo=True, maxundo=-1, autoseparators=True)
        
        lbl(scroll, "Nghĩa mẫu câu", 12, "bold", C["accent"], anchor="w").pack(anchor="w", pady=(10,2))
        self.e_ex_mean = ctk.CTkTextbox(scroll, height=80, fg_color=C["card"], border_color=C["accent"], text_color=C["text"], border_width=1, corner_radius=8, font=("Consolas", 14))
        self.e_ex_mean.pack(fill="x", expand=True)
        self.e_ex_mean._textbox.configure(undo=True, maxundo=-1, autoseparators=True)

        # MP3 Audio
        lbl(scroll, "File MP3 Phát âm (local path)", 12, "bold", C["accent"], anchor="w").pack(anchor="w", pady=(10,2))
        mp3_row = ctk.CTkFrame(scroll, fg_color="transparent"); mp3_row.pack(anchor="w")
        self.e_mp3_path = ctk.CTkEntry(mp3_row, placeholder_text="Chọn file MP3...", width=480, fg_color=C["card"], border_color=C["accent"], text_color=C["text"])
        self.e_mp3_path.pack(side="left", padx=(0,8))
        btn(mp3_row, "Chọn", C["card2"], C["accent"], w=100, h=34, cmd=lambda: self._browse(self.e_mp3_path, [("MP3","*.mp3"),("All","*")])).pack(side="left")

        lbl(scroll, "  Google Drive ID (sẽ có sau khi sync)", 11, color=C["muted"], anchor="w").pack(anchor="w")
        self.e_mp3_id = entry(scroll, "ID Drive...", width=580)
        self.e_mp3_id.pack(anchor="w")

        # Video / MP4 (Optional)
        lbl(scroll, "File MP4 / Video (Optional)", 12, "bold", C["accent"], anchor="w").pack(anchor="w", pady=(10,2))
        mp4_row = ctk.CTkFrame(scroll, fg_color="transparent"); mp4_row.pack(anchor="w")
        self.e_mp4_path = ctk.CTkEntry(mp4_row, placeholder_text="Chọn file MP4...", width=480, fg_color=C["card"], border_color=C["accent"], text_color=C["text"])
        self.e_mp4_path.pack(side="left", padx=(0,8))
        btn(mp4_row, "Chọn", C["card2"], C["accent"], w=100, h=34, cmd=lambda: self._browse(self.e_mp4_path, [("MP4","*.mp4"),("All","*")])).pack(side="left")

        lbl(scroll, "  Google Drive ID (sẽ có sau khi sync)", 11, color=C["muted"], anchor="w").pack(anchor="w")
        self.e_mp4_id = entry(scroll, "ID Drive...", width=580)
        self.e_mp4_id.pack(anchor="w")

        # Ghi chú
        row_note = ctk.CTkFrame(scroll, fg_color="transparent")
        row_note.pack(fill="x", pady=(10,2))
        lbl(row_note, "Ghi chú cá nhân", 12, "bold", C["accent"], anchor="w").pack(side="left")
        btn(row_note, "👁 Preview", C["card2"], C["accent2"], w=90, h=24, cmd=lambda: PreviewDialog(self, "Ghi chú cá nhân", self.e_note.get("1.0", "end"))).pack(side="left", padx=(15, 5))
        btn(row_note, "▦ Tạo Bảng", C["card2"], C["accent2"], w=90, h=24, cmd=lambda: TableEditorDialog(self, self.e_note)).pack(side="left")
        self.e_note = ctk.CTkTextbox(scroll, height=80, fg_color=C["card"], border_color=C["accent"], text_color=C["text"], border_width=1, corner_radius=8, font=("Consolas", 14))
        self.e_note.pack(fill="x", expand=True)
        self.e_note._textbox.configure(undo=True, maxundo=-1, autoseparators=True)

        # Buttons
        btn_row = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        btn_row.pack(pady=9)
        btn(btn_row, "Lưu", C["success"], "#018786", w=160, h=42, cmd=self._save).pack(side="left", padx=(0,10))
        btn(btn_row, "Hủy", C["card2"], C["danger"], w=120, h=42, cmd=self.destroy).pack(side="left")

        # Paste Markdown Intercept
        def _is_md_table(text):
            """True nếu clipboard chứa Markdown table (pipe-separated, từ Gemini/ChatGPT/GitHub)"""
            lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
            if not lines:
                return False
            pipe_lines = [l for l in lines if l.startswith('|') and l.endswith('|')]
            return len(pipe_lines) >= 1 and (len(pipe_lines) / len(lines)) >= 0.5

        def _ensure_md_separator(text):
            """Đảm bảo Markdown table có dòng |---|---| sau header; tự chèn nếu thiếu"""
            lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
            if len(lines) < 2:
                return '\n'.join(lines)
            line2_clean = lines[1].replace('-', '').replace('|', '').replace(':', '').replace(' ', '')
            already_has_sep = (line2_clean == '' and '---' in lines[1])
            if already_has_sep:
                return '\n'.join(lines)
            headers = [c.strip() for c in lines[0].split('|')[1:-1]]
            sep_row = '|' + '|'.join([' --- '] * len(headers)) + '|'
            return '\n'.join([lines[0], sep_row] + lines[1:])

        def _detect_csv_delim(text):
            """Tự động phát hiện delimiter (dấu , hay ;) trong CSV"""
            try:
                dialect = csv.Sniffer().sniff(text[:2048], delimiters=',;')
                return dialect.delimiter
            except Exception:
                # Đếm thủ công nếu Sniffer thất bại
                sample = text.strip().split('\n')[:3]
                n_comma = sum(l.count(',') for l in sample)
                n_semi  = sum(l.count(';') for l in sample)
                return ';' if n_semi > n_comma else ','

        def _is_csv_table(text):
            """True nếu text là CSV/SSV nhiều dòng nhất quán (không phải Markdown, không phải Tab)"""
            lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
            if len(lines) < 2:
                return False
            # Bỏ qua nếu đã là Markdown hoặc Tab
            if _is_md_table(text) or '\t' in text:
                return False
            try:
                delim = _detect_csv_delim(text)
                rows = list(csv.reader(io.StringIO(text.strip()), delimiter=delim))
                if len(rows) < 2:
                    return False
                col_counts = [len(r) for r in rows]
                # Tất cả dòng cùng số cột và >= 2 cột
                return len(set(col_counts)) == 1 and col_counts[0] >= 2
            except Exception:
                return False

        def _csv_to_md_table(text):
            """Convert CSV/SSV sang Markdown table (hỗ trợ ô có dấu phẩy trong ngoặc kép)"""
            delim = _detect_csv_delim(text)
            rows = list(csv.reader(io.StringIO(text.strip()), delimiter=delim))
            if not rows:
                return text
            md = []
            for i, row in enumerate(rows):
                # Escape pipe trong nội dung ô, bỏ dấu ngoặc kép thừa
                cells = [c.strip().replace('|', '\\|') for c in row]
                md.append('| ' + ' | '.join(cells) + ' |')
                if i == 0:
                    md.append('|' + '|'.join([' --- '] * len(cells)) + '|')
            return '\n'.join(md)

        def on_paste(event, textbox):
            try:
                clip = self.clipboard_get()

                # Trường hợp 1: Markdown table (từ Gemini AI, ChatGPT, GitHub...)
                if _is_md_table(clip):
                    normalized = _ensure_md_separator(clip)
                    textbox.insert('insert', '\n' + normalized + '\n')
                    return 'break'

                # Trường hợp 2: Tab-separated (từ Excel, Google Sheets...)
                if '\t' in clip and '\n' in clip:
                    lines = clip.strip().split('\n')
                    md = []
                    for i, line in enumerate(lines):
                        cells = [c.strip() for c in line.split('\t')]
                        md.append('| ' + ' | '.join(cells) + ' |')
                        if i == 0:
                            md.append('|' + '|'.join(['---'] * len(cells)) + '|')
                    textbox.insert('insert', '\n'.join(md) + '\n')
                    return 'break'

                # Trường hợp 3: CSV / SSV (dấu , hoặc ;, hỗ trợ ô có ngoặc kép)
                if _is_csv_table(clip):
                    md_text = _csv_to_md_table(clip)
                    textbox.insert('insert', '\n' + md_text + '\n')
                    return 'break'

                # Còn lại: paste bình thường (không chặn)
            except Exception:
                pass

        self.e_mean._textbox.bind('<<Paste>>', lambda e: on_paste(e, self.e_mean))
        self.e_ex._textbox.bind('<<Paste>>', lambda e: on_paste(e, self.e_ex))
        self.e_note._textbox.bind('<<Paste>>', lambda e: on_paste(e, self.e_note))

        lang = self.app.current_language
        all_topics = get_all_topics(lang)
        all_dates = get_all_dates(lang)
        all_types = list(dict.fromkeys(WORD_TYPES + get_all_types(lang)))

        self.setup_autocomplete(self.e_type, all_types)
        self.setup_autocomplete(self.e_topic, all_topics)
        self.setup_autocomplete(self.e_date, all_dates)

        if is_edit:
            self._fill(vocab)
        else:
            if hasattr(self.app, 'last_topic') and self.app.last_topic:
                self.e_topic.set(self.app.last_topic)
            if hasattr(self.app, 'last_date_tag') and self.app.last_date_tag:
                self.e_date.set(self.app.last_date_tag)

    def setup_autocomplete(self, combo_widget, all_values):
        combo_widget.configure(values=all_values[:5])
        
        def on_key_release(event):
            if event.keysym in ['Up', 'Down', 'Left', 'Right', 'Return', 'Escape', 'Tab']:
                return
            
            typed = combo_widget.get()
            if not typed:
                combo_widget.configure(values=all_values[:5])
                return
                
            filtered = [v for v in all_values if typed.lower() in v.lower()][:5]
            if filtered:
                combo_widget.configure(values=filtered)
                # Mở dropdown tự động
                if hasattr(combo_widget, "_dropdown_menu"):
                    combo_widget._dropdown_menu.open()
                    if hasattr(combo_widget, "_entry"):
                        combo_widget._entry.focus_set()
            else:
                combo_widget.configure(values=[])
                if hasattr(combo_widget, "_dropdown_menu"):
                    combo_widget._dropdown_menu.close()
                    
        if hasattr(combo_widget, "_entry"):
            combo_widget._entry.bind("<KeyRelease>", on_key_release)

    def _browse(self, entry_w, ftypes):
        path = filedialog.askopenfilename(filetypes=ftypes)
        if path:
            entry_w.delete(0, "end")
            entry_w.insert(0, path)

    def _fill(self, v):
        def se(w, val): w.delete(0, "end"); w.insert(0, val or "")
        se(self.e_word, v.get("word"))
        se(self.e_pron, v.get("pronunciation"))
        # e_mean là Textbox, dùng insert thay vì se()
        self.e_mean.delete("1.0", "end")
        self.e_mean.insert("1.0", v.get("meaning") or "")
        self.e_type.set(v.get("word_type", ""))
        self.e_topic.set(v.get("topic", ""))
        self.e_date.set(v.get("date_tag", ""))
        self.e_ex.insert("1.0", v.get("example", ""))
        self.e_ex_mean.insert("1.0", v.get("example_meaning", ""))
        se(self.e_mp3_path, v.get("mp3_local_path"))
        se(self.e_mp3_id, v.get("mp3_gdrive_id"))
        se(self.e_mp4_path, v.get("mp4_local_path"))
        se(self.e_mp4_id, v.get("mp4_gdrive_id"))
        self.e_note.insert("1.0", v.get("note", ""))

    def _save(self):
        word = self.e_word.get().strip()
        meaning = self.e_mean.get("1.0", "end").strip()
        if not word or not meaning:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Từ vựng và Nghĩa!", parent=self)
            return

        self.result = {
            "word": word,
            "pronunciation": self.e_pron.get().strip(),
            "meaning": meaning,
            "word_type": self.e_type.get().strip(),
            "topic": self.e_topic.get().strip(),
            "date_tag": self.e_date.get().strip(),
            "example": self.e_ex.get("1.0", "end").strip(),
            "example_meaning": self.e_ex_mean.get("1.0", "end").strip(),
            "mp3_local_path": self.e_mp3_path.get().strip(),
            "mp3_gdrive_id": self.e_mp3_id.get().strip(),
            "mp4_local_path": self.e_mp4_path.get().strip(),
            "mp4_gdrive_id": self.e_mp4_id.get().strip(),
            "note": self.e_note.get("1.0", "end").strip(),
        }
        
        # Lưu lại Chủ đề và Tag Ngày Học dùng cho lần sau
        self.app.last_topic = self.result["topic"]
        self.app.last_date_tag = self.result["date_tag"]
        
        self.destroy()

# ══════════════════════════════════════════════════════════════════════════════
# Tab: Danh Sach
# ══════════════════════════════════════════════════════════════════════════════
class VocabListTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg"])
        self.app = app
        self._selected = None
        self._selected_row = None
        self._orig_bg = None
        self._build()

    def _build(self):
        # ── Toolbar ──
        tb = ctk.CTkFrame(self, fg_color=C["sidebar"], height=58, corner_radius=0)
        tb.pack(fill="x"); tb.pack_propagate(False)

        lbl(tb, "Ngôn Ngữ:", 14, color=C["accent"]).pack(side="left", padx=(14,4))
        self.cb_lang_main = combo(tb, self.app.available_languages, width=150)
        self.cb_lang_main.set(self.app.current_language)
        self.cb_lang_main.configure(command=self._on_lang_change)
        self.cb_lang_main.pack(side="left", padx=(0,12))

        btn(tb, "+ Ngôn Ngữ Mới", C["card2"], C["accent"], w=130, h=34, cmd=self._add_lang).pack(side="left", padx=3)
        
        lbl(tb, "Tìm kiếm:", 14, color=C["accent"]).pack(side="left", padx=(20,4))
        self.sv = ctk.StringVar()
        self.sv.trace_add("write", lambda *_: self.refresh())
        ctk.CTkEntry(tb, textvariable=self.sv, placeholder_text="Tìm từ, nghĩa, phát âm...", width=200, height=34, fg_color=C["card"], border_color=C["accent"], text_color=C["text"]).pack(side="left", padx=(0,12))

        btn(tb, "+ Thêm Từ", C["success"], "#018786", w=100, h=34, cmd=self._add).pack(side="right", padx=14)

        # ── Filter row ──
        fr = ctk.CTkFrame(self, fg_color=C["card2"], height=40, corner_radius=0)
        fr.pack(fill="x"); fr.pack_propagate(False)
        lbl(fr, "Lọc:", 11, color=C["muted"]).pack(side="left", padx=12)
        
        self.cb_type = combo(fr, ["Tất cả"], width=130)
        self.cb_type.configure(command=lambda _: self.refresh())
        self.cb_type.pack(side="left", padx=6)
        
        self.cb_topic = combo(fr, ["Tất cả chủ đề"], width=130)
        self.cb_topic.configure(command=lambda _: self.refresh())
        self.cb_topic.pack(side="left", padx=6)
        
        self.cb_date = combo(fr, ["Tất cả ngày"], width=130)
        self.cb_date.configure(command=lambda _: self.refresh())
        self.cb_date.pack(side="left", padx=6)

        self.lbl_count = lbl(fr, "0 từ", 11, color=C["muted"])
        self.lbl_count.pack(side="right", padx=14)

        # ── Treeview Table ──
        table_frame = ctk.CTkFrame(self, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Vocab.Treeview", background=C["card"], foreground=C["text"], fieldbackground=C["card"], rowheight=32, borderwidth=0)
        style.map('Vocab.Treeview', background=[('selected', "#3700B3")])
        style.configure("Vocab.Treeview.Heading", background=C["card2"], foreground=C["accent"], font=('Arial', 11, 'bold'), borderwidth=0)

        self.tree = ttk.Treeview(table_frame, style="Vocab.Treeview", show='headings')
        
        # Scrollbar
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        
        # Columns setup
        COLS = [("word", "Từ Vựng", 150), ("pron", "Phát Âm", 120), ("mean", "Nghĩa", 180), 
                ("type", "Loại", 90), ("topic", "Chủ đề", 120), ("date", "Ngày học", 90), 
                ("mp3", "MP3", 50), ("ex", "Mẫu câu", 150)]
        
        self.tree["columns"] = [c[0] for c in COLS]
        for col_id, col_name, width in COLS:
            self.tree.heading(col_id, text=col_name, anchor="w")
            self.tree.column(col_id, width=width, anchor="w")

        # Bind events
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self.tree.bind("<Double-1>", self._on_tree_double)

        self._current_vocabs = [] # Store vocabs for easy access

        # ── Action panel duoi (hien khi chon tu) ──
        self.action_panel = ctk.CTkFrame(self, fg_color=C["card"], height=54, corner_radius=0)
        self.action_panel.pack(fill="x"); self.action_panel.pack_propagate(False)

        self.lbl_hint = lbl(self.action_panel, "   Click chọn một từ vựng   |   Double-click để sửa nhanh", 11, color=C["muted"])
        self.lbl_hint.pack(side="left", padx=16, pady=14)

        self.action_row = ctk.CTkFrame(self.action_panel, fg_color="transparent")
        self.lbl_sel_word = lbl(self.action_row, "", 13, "bold", C["accent"])
        self.lbl_sel_word.pack(side="left", padx=(12,20))

        btn(self.action_row, "Sửa", C["warn"], "#d97706", w=90, h=36, cmd=self._edit).pack(side="left", padx=4)
        btn(self.action_row, "Xóa", C["danger"], "#b91c1c", w=90, h=36, cmd=self._delete).pack(side="left", padx=4)

    def _on_lang_change(self, choice):
        self.app.set_language(choice)

    def refresh_filters(self):
        lang = self.app.current_language
        topics = ["Tất cả chủ đề"] + get_all_topics(lang)
        types = ["Tất cả"] + get_all_types(lang)
        dates = ["Tất cả ngày"] + get_all_dates(lang)
        
        self.cb_topic.configure(values=topics)
        self.cb_topic.set("Tất cả chủ đề")
        
        self.cb_type.configure(values=types)
        self.cb_type.set("Tất cả")
        
        self.cb_date.configure(values=dates)
        self.cb_date.set("Tất cả ngày")

    def refresh(self):
        q = self.sv.get()
        t_type = self.cb_type.get(); t_type = "" if t_type == "Tất cả" else t_type
        t_topic = self.cb_topic.get(); t_topic = "" if t_topic == "Tất cả chủ đề" else t_topic
        t_date = self.cb_date.get(); t_date = "" if t_date == "Tất cả ngày" else t_date
        
        vocabs = search_vocab(self.app.current_language, q, t_type, t_topic, t_date)
        self._render(vocabs)
        self.lbl_count.configure(text=f"{len(vocabs)} từ")
        self._selected = None
        self._selected_row = None
        self.action_row.pack_forget()
        self.lbl_hint.pack(side="left", padx=16, pady=14)

    def _render(self, vocabs):
        self._current_vocabs = vocabs
        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insert new data
        for i, v in enumerate(vocabs):
            val_word = str(v.get("word") or "")
            val_pron = str(v.get("pronunciation") or "")
            val_mean = str(v.get("meaning") or "").replace('\n', ' ')
            if len(val_mean) > 35: val_mean = val_mean[:32] + "..."
            val_type = str(v.get("word_type") or "")
            val_topic = str(v.get("topic") or "")
            val_date = str(v.get("date_tag") or "")
            val_mp3 = "OK" if v.get("mp3_gdrive_id") else "-"
            val_ex = str(v.get("example") or "").replace('\n', ' ')
            if len(val_ex) > 30: val_ex = val_ex[:27] + "..."

            # Alternate background tags
            tag = 'even' if i % 2 == 0 else 'odd'
            self.tree.insert('', 'end', text=str(i), values=(val_word, val_pron, val_mean, val_type, val_topic, val_date, val_mp3, val_ex), tags=(tag,))
            
        self.tree.tag_configure('even', background=C["card"])
        self.tree.tag_configure('odd', background=C["card2"])

    def _on_tree_select(self, event):
        selected_items = self.tree.selection()
        if not selected_items: return
        item_id = selected_items[0]
        idx_str = self.tree.item(item_id, 'text')
        if not idx_str: return
        idx = int(idx_str)
        if idx < len(self._current_vocabs):
            vocab = self._current_vocabs[idx]
            self._selected = vocab
            self.lbl_hint.pack_forget()
            mean_short = str(vocab.get('meaning') or '').replace('\n', ' ')
            if len(mean_short) > 30: mean_short = mean_short[:27] + "..."
            self.lbl_sel_word.configure(text=f"{vocab.get('word', '')} ({mean_short})")
            self.action_row.pack(side="left", fill="both", expand=True, padx=4, pady=8)

    def _on_tree_double(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region not in ("cell", "tree"):
            return
        self._on_tree_select(event)
        if self._selected:
            self._edit()

    def _add_lang(self):
        d = ctk.CTkInputDialog(text="Nhập tên ngôn ngữ mới (VD: Tiếng Hàn, Tiếng Tây Ban Nha):", title="Thêm ngôn ngữ")
        lang = d.get_input()
        if lang and lang.strip():
            lang = lang.strip()
            self.app.set_language(lang)

    def _add(self):
        if not self.app.current_language: return
        d = VocabFormDialog(self.app)
        self.app.wait_window(d)
        if not d.result:
            return

        new_word = d.result.get("word", "").strip()
        existing = find_vocab_by_word(self.app.current_language, new_word)

        if existing:
            # Từ đã tồn tại — hiện dialog hỏi người dùng
            answer = messagebox.askyesnocancel(
                "Từ đã tồn tại",
                f"❌ Từ vựng \"{new_word}\" đã có trong danh sách!\n\n"
                f"✅ Yes  → Mở form sửa từ này (dữ liệu bạn vừa nhập sẽ được giữ lại)\n"
                f"⚠️  No  → Vẫn thêm mới (từ trùng)\n"
                f"❌ Cancel → Hủy",
                parent=self.app
            )
            if answer is True:
                # Mở form sửa, pre-fill với dữ liệu người dùng vừa nhập
                merged = dict(existing)   # lấy dữ liệu cũ làm nền
                merged.update(d.result)   # ghi đè với dữ liệu mới nhập
                edit_dialog = VocabFormDialog(self.app, merged)
                self.app.wait_window(edit_dialog)
                if edit_dialog.result:
                    update_vocab(self.app.current_language, existing["id"], edit_dialog.result)
                    self.refresh_filters()
                    self.refresh()
                    self.app.update_stats()
            elif answer is False:
                # Vẫn thêm trùng lập
                add_vocab(self.app.current_language, d.result)
                self.refresh_filters()
                self.refresh()
                self.app.update_stats()
            # answer is None → Cancel, không làm gì
        else:
            # Từ mới hoàn toàn
            add_vocab(self.app.current_language, d.result)
            self.refresh_filters()
            self.refresh()
            self.app.update_stats()

    def _edit(self):
        if not self._selected: return
        d = VocabFormDialog(self.app, self._selected)
        self.app.wait_window(d)
        if d.result:
            update_vocab(self.app.current_language, self._selected["id"], d.result)
            self._selected = None
            self.refresh_filters()
            self.refresh()
            self.app.update_stats()

    def _delete(self):
        if not self._selected: return
        word = self._selected.get("word", "")
        if messagebox.askyesno("Xác nhận xóa", f"Xóa từ vựng này?\n\n{word}", parent=self.app):
            delete_vocab(self.app.current_language, self._selected["id"])
            self._selected = None
            self.refresh_filters()
            self.refresh()
            self.app.update_stats()

# ══════════════════════════════════════════════════════════════════════════════
# Tab: Cai Dat & Dong Bo
# ══════════════════════════════════════════════════════════════════════════════
class SettingsSyncTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg"])
        self.app = app
        self._gdrive = GDriveSync()
        self._syncing = False
        self._build()

    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color=C["bg"])
        scroll.pack(fill="both", expand=True, padx=30, pady=20)

        # ── Sync Section ──
        lbl(scroll, "Đồng Bộ Lên GitHub Pages", 17, "bold", C["accent"]).pack(anchor="w", pady=(0,4))
        
        btn(scroll, "Bắt Đầu Đồng Bộ", C["success"], "#018786", w=200, h=48, cmd=self._start_sync).pack(anchor="w", pady=10)
        
        self.progress = ctk.CTkProgressBar(scroll, progress_color=C["accent"], height=6)
        self.progress.pack(fill="x", pady=(0,10))
        self.progress.set(0)

        self.log_box = ctk.CTkTextbox(scroll, height=150, fg_color=C["card"], text_color=C["text"])
        self.log_box.pack(fill="both", expand=True, pady=(4,10))
        self.log_box.configure(state="disabled")
        
        url_frame = ctk.CTkFrame(scroll, fg_color=C["card2"])
        url_frame.pack(fill="x", pady=(0,14))
        lbl(url_frame, "Web URL:", 12, color=C["muted"]).pack(side="left", padx=12, pady=8)
        self.lbl_url = lbl(url_frame, load_settings().get("github", {}).get("pages_url", "-"), 12, "bold", C["accent"])
        self.lbl_url.pack(side="left")
        btn(url_frame, "Mở", C["card"], C["accent"], w=70, h=28, cmd=lambda: webbrowser.open(self.lbl_url.cget("text"))).pack(side="right", padx=8)

        sep(scroll)

        # ── GitHub Config ──
        lbl(scroll, "Cài Đặt GitHub", 15, "bold", C["accent"]).pack(anchor="w", pady=(10,4))
        s = load_settings()["github"]
        
        self.e_user = entry(scroll, "Username GitHub"); self.e_user.insert(0, s.get("username","")); self.e_user.pack(anchor="w", pady=2)
        self.e_token = ctk.CTkEntry(scroll, placeholder_text="Token (ghp_...)", width=440, fg_color=C["card"], border_color=C["accent"], text_color=C["text"], show="*")
        self.e_token.insert(0, s.get("token","")); self.e_token.pack(anchor="w", pady=2)
        
        self.e_repo = entry(scroll, "Tên Repository (mặc định: VocabularyApp)"); self.e_repo.insert(0, s.get("repo_name","VocabularyApp")); self.e_repo.pack(anchor="w", pady=2)

        btn(scroll, "Lưu GitHub", C["accent"], C["accent2"], w=150, h=34, cmd=self._save_github).pack(anchor="w", pady=10)

        sep(scroll)

        # ── Drive Config ──
        lbl(scroll, "Cài Đặt Google Drive (Audio)", 15, "bold", C["accent"]).pack(anchor="w", pady=(10,4))
        self.lbl_drive_status = lbl(scroll, "Trạng thái: " + ("Đã kết nối" if self._gdrive.is_authenticated() else "Chưa kết nối"), 12, color=C["success"] if self._gdrive.is_authenticated() else C["muted"])
        self.lbl_drive_status.pack(anchor="w", pady=4)

        btn_row_gd = ctk.CTkFrame(scroll, fg_color="transparent"); btn_row_gd.pack(anchor="w")
        btn(btn_row_gd, "Kết Nối Drive", C["accent"], C["accent2"], w=150, h=34, cmd=self._connect_drive).pack(side="left", padx=(0,10))
        btn(btn_row_gd, "Upload MP3 Drive", C["warn"], "#d97706", w=150, h=34, cmd=self._sync_drive).pack(side="left")

    def _log(self, msg: str):
        def _append():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, _append)

    def _save_github(self):
        update_github_settings(username=self.e_user.get().strip(), token=self.e_token.get().strip(), repo_name=self.e_repo.get().strip() or "VocabularyApp")
        messagebox.showinfo("Thành công", "Đã lưu cài đặt GitHub", parent=self.app)

    def _connect_drive(self):
        def do_auth():
            ok = self._gdrive.authenticate(log_fn=self._log)
            self.after(0, lambda: self.lbl_drive_status.configure(text="Trạng thái: " + ("Đã kết nối" if ok else "Lỗi kết nối")))
        threading.Thread(target=do_auth, daemon=True).start()

    def _sync_drive(self):
        if not self._gdrive.is_authenticated():
            messagebox.showwarning("Chưa kết nối", "Vui lòng kết nối Google Drive trước!", parent=self.app)
            return
        threading.Thread(target=self._do_drive_sync, daemon=True).start()

    def _do_drive_sync(self):
        self._log("Bắt đầu upload Google Drive...")
        folders = self._gdrive.ensure_folders()
        
        # Duyệt qua các từ vựng của ngôn ngữ hiện tại
        vocabs = get_all_vocab(self.app.current_language)
        count = 0
        for i, v in enumerate(vocabs):
            if v.get("mp3_local_path") and not v.get("mp3_gdrive_id"):
                updates = self._gdrive.sync_vocab_media(v, folders)
                if updates:
                    update_vocab(self.app.current_language, v["id"], updates)
                    count += 1
            self.progress.set((i+1)/len(vocabs))
        self._log(f"Hoàn tất upload Google Drive ({count} files)!")

    def _start_sync(self):
        if self._syncing: return
        s = load_settings()["github"]
        if not s.get("username") or not s.get("token"):
            messagebox.showwarning("Lỗi", "Vui lòng nhập GitHub Username và Token", parent=self.app)
            return
        
        self._syncing = True
        self.progress.set(0)
        self.log_box.configure(state="normal"); self.log_box.delete("1.0","end"); self.log_box.configure(state="disabled")
        threading.Thread(target=self._do_github_sync, args=(s,), daemon=True).start()

    def _do_github_sync(self, settings):
        try:
            gh = GitHubSync(settings["username"], settings["token"], settings["repo_name"])
            
            def p(msg): self._log(msg)
            
            ok = gh.full_sync(log_fn=p)
            if ok:
                url = gh.get_pages_url()
                update_github_settings(pages_url=url)
                self.after(0, lambda: self.lbl_url.configure(text=url))
        except Exception as e:
            self._log(f"Lỗi: {str(e)}")
        finally:
            self._syncing = False
            self.after(0, lambda: self.progress.set(1.0))

# ══════════════════════════════════════════════════════════════════════════════
# Main App
# ══════════════════════════════════════════════════════════════════════════════
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Vocabulary App - Học Từ Vựng")
        self.geometry("1100x700")
        self.configure(fg_color=C["bg"])

        self.available_languages = get_available_languages()
        if not self.available_languages:
            self.available_languages = ["English"]
        self.current_language = self.available_languages[0]
        self.last_topic = ""
        self.last_date_tag = ""

        # Tabs
        self.tabview = ctk.CTkTabview(self, fg_color=C["sidebar"], segmented_button_fg_color=C["card2"], segmented_button_selected_color=C["accent"], segmented_button_selected_hover_color=C["accent2"])
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_list = self.tabview.add("Danh Sách Từ Vựng")
        self.tab_sync = self.tabview.add("Đồng Bộ & Cài Đặt")

        # Init views
        self.view_list = VocabListTab(self.tab_list, self)
        self.view_list.pack(fill="both", expand=True)

        self.view_sync = SettingsSyncTab(self.tab_sync, self)
        self.view_sync.pack(fill="both", expand=True)

        self.set_language(self.current_language)

    def set_language(self, lang):
        self.current_language = lang
        if lang not in self.available_languages:
            self.available_languages.append(lang)
            self.view_list.cb_lang_main.configure(values=self.available_languages)
        self.view_list.cb_lang_main.set(lang)
        self.view_list.refresh_filters()
        self.view_list.refresh()

    def update_stats(self):
        # Refresh UI nếu cần update text hiển thị theo count
        pass

if __name__ == "__main__":
    app = App()
    app.mainloop()
