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
import re
import threading
import webbrowser
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import subprocess

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

# --- Auto check & install packages (Giống AskCpl) ---
# Bắt buộc: thiếu là app không thể chạy
CRITICAL_PACKAGES = {
    'customtkinter': 'customtkinter>=5.2.0',
    'requests': 'requests>=2.31.0',
}
# Mở rộng: thiếu chỉ làm mất tính năng tương ứng (TTS offline/online, Drive...),
# app vẫn khởi động bình thường. Cài từng gói riêng để 1 gói build lỗi
# (VD pygame trên Python 3.14 chưa có wheel) không chặn các gói còn lại.
OPTIONAL_PACKAGES = {
    'google.auth': 'google-auth>=2.27.0',
    'google_auth_oauthlib': 'google-auth-oauthlib>=1.2.0',
    'googleapiclient': 'google-api-python-client>=2.118.0',
    'webview': 'pywebview>=4.4.1',
    'pyttsx3': 'pyttsx3>=2.90',
    'gtts': 'gTTS>=2.3.2',
    'pygame': 'pygame-ce>=2.5.0',
    # Thêm mới: pipeline media (ảnh WebP) + TTS neural + bridge Web AI
    'edge_tts': 'edge-tts>=7.3',
    'PIL': 'Pillow>=10.0',
    'flask': 'Flask>=3.0',
    'numpy': 'numpy>=1.26',
    'selenium': 'selenium>=4.18',
}

def _import_ok(module_name: str) -> bool:
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def _show_install_error(missing):
    """Hiện cửa sổ lỗi khi thiếu thư viện BẮT BUỘC và thoát."""
    root = tk.Tk()
    root.withdraw()
    err_win = tk.Toplevel(root)
    err_win.title("Lỗi Thiếu Thư Viện")
    err_win.geometry("550x300")
    tk.Label(err_win, text="Ứng dụng thiếu một số thư viện cần thiết và không thể cài đặt tự động.", fg="red", font=("Arial", 11, "bold")).pack(pady=10)
    tk.Label(err_win, text="Vui lòng copy dòng lệnh dưới đây và dán vào Terminal/CMD để cài đặt:", font=("Arial", 10)).pack(pady=5)

    txt = tk.Text(err_win, height=4, width=65, font=("Consolas", 11))
    txt.pack(pady=10)
    cmd = "python -m pip install --user " + " ".join(missing)
    txt.insert(tk.END, cmd)
    txt.config(state="disabled")

    tk.Button(err_win, text="Thoát ứng dụng", command=root.destroy, width=15).pack(pady=15)
    root.mainloop()
    sys.exit(1)

def check_and_install_packages():
    if os.environ.get("VOCABAPP_SKIP_INSTALL"):
        return

    # 1) Thư viện bắt buộc — cài từng cái, fail thì báo lỗi và thoát
    missing = [pip_name for mod, pip_name in CRITICAL_PACKAGES.items() if not _import_ok(mod)]
    if missing:
        safe_print(f"[*] Đang cài thư viện bắt buộc: {', '.join(missing)}")
        for pkg in missing:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "--prefer-binary", pkg])
            except Exception:
                _show_install_error(missing)
                return

    # 2) Thư viện mở rộng — thử cài từng cái, fail thì bỏ qua (app vẫn chạy)
    optional_missing = [pip_name for mod, pip_name in OPTIONAL_PACKAGES.items() if not _import_ok(mod)]
    if optional_missing:
        safe_print(f"[*] Đang cài thư viện mở rộng: {', '.join(optional_missing)}")
        for pkg in optional_missing:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "--prefer-binary", pkg])
            except Exception:
                safe_print(f"[!] Không cài được '{pkg}' — bỏ qua (tính năng liên quan sẽ bị tắt)")
        safe_print("[*] Hoàn tất kiểm tra thư viện.")

check_and_install_packages()

# ─── TTS Hybrid: gTTS (online) → fallback pyttsx3 (offline) ──────────────────
_tts_lock = threading.Lock()  # chặn 2 thread phát âm thanh cùng lúc

def _get_tts_lang_code(lang_name: str) -> str:
    """Map tên ngôn ngữ trong app → mã ngôn ngữ TTS."""
    n = (lang_name or "").lower()
    if any(x in n for x in ["anh", "english"]):   return "en"
    if any(x in n for x in ["nhật", "japan"]):     return "ja"
    if any(x in n for x in ["trung", "chin"]):     return "zh-CN"
    if any(x in n for x in ["việt", "viet"]):      return "vi"
    if any(x in n for x in ["hàn", "korea"]):      return "ko"
    if any(x in n for x in ["pháp", "french"]):    return "fr"
    if any(x in n for x in ["đức", "german"]):     return "de"
    return "en"

def speak_word(word: str, lang_name: str = ""):
    """Đọc từ bằng TTS trên thread riêng (không block UI).
    Thử gTTS trước (cần internet, chất lượng tốt hơn).
    Fallback pyttsx3 nếu không có mạng hoặc gTTS lỗi.
    """
    if not word or not word.strip():
        return
    lang_code = _get_tts_lang_code(lang_name)

    def _run():
        # --- Thử gTTS (online) ---
        try:
            import pygame  # check sớm: nếu máy không có pygame thì đỡ tốn công generate
            import requests as _req
            _req.get("https://www.google.com", timeout=2)  # kiểm tra mạng nhanh
            from gtts import gTTS
            import io as _io
            tts = gTTS(text=word.strip(), lang=lang_code, slow=False)
            buf = _io.BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            with _tts_lock:  # pygame.mixer không dùng đồng thời được từ 2 thread
                pygame.mixer.init()
                pygame.mixer.music.load(buf)
                pygame.mixer.music.play()
            return
        except Exception:
            pass  # fallback xuống pyttsx3

        # --- Fallback pyttsx3 (offline) ---
        with _tts_lock:
            try:
                import pyttsx3
                engine = pyttsx3.init()
                # Thử chọn giọng phù hợp
                voices = engine.getProperty('voices')
                for v in voices:
                    langs = v.languages[0].decode() if (v.languages and isinstance(v.languages[0], bytes)) else ""
                    if lang_code.split("-")[0] in langs:
                        engine.setProperty('voice', v.id)
                        break
                engine.setProperty('rate', 150)
                engine.say(word.strip())
                engine.runAndWait()
                engine.stop()
            except Exception as ex:
                safe_print(f"[TTS] Lỗi pyttsx3: {ex}")

    threading.Thread(target=_run, daemon=True).start()

import customtkinter as ctk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from database.database import (
    get_all_vocab, search_vocab, add_vocab, update_vocab,
    delete_vocab, get_stats, get_all_topics, get_all_types, get_all_dates,
    get_available_languages, find_vocab_by_word
)
from database import review_store
from ai.srs import (GRADES, GRADE_LABELS_VI, STATE_NEW, STATE_LEARNING,
                    STATE_REVIEW, STATE_MASTERED, mastery_level)
from settings import (
    load_settings, save_settings,
    update_github_settings, update_gdrive_settings, update_ai_settings,
    get_active_model_list, _DEFAULT_MODEL_FALLBACKS,
)
from ai.pipeline_store import (load_dead_models, mark_dead_model,
                               reset_dead_model, get_available_models,
                               DEAD_MODEL_COOLDOWN_MINUTES,
                               MAX_FAILURES_BEFORE_DEAD)
from api.gemini_safe import GeminiCoordinator
from api.github_sync import GitHubSync
from api.gdrive_sync import GDriveSync
from ai import course_db
from ai.course_generator import (
    generate_course, GenerationStopped, count_available_keys,
    DEFAULT_WORDS_PER_DAY, DEFAULT_LEVEL, LEVELS,
    LEVEL_PHASES, LEVEL_MIN_DAYS, JOURNEY_PHASES,
)

# ─── Theme ────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

C = {
    # Deep dark background
    "bg":      "#0f0f14",
    "sidebar": "#1a1a24",
    "card":    "#1e1e2a",
    "card2":   "#252536",
    "card3":   "#2d2d42",
    # Accent colors - vibrant purple/blue
    "accent":  "#8b5cf6",
    "accent2": "#7c3aed",
    "accent3": "#6d28d9",
    # Semantic colors
    "text":    "#f8fafc",
    "text2":   "#cbd5e1",
    "muted":   "#94a3b8",
    "success": "#22d3ee",
    "warn":    "#fbbf24",
    "danger":  "#ef4444",
    # Border
    "border":  "#333346",
}

WORD_TYPES = ["", "Danh từ (n)", "Động từ (v)", "Tính từ (adj)", "Trạng từ (adv)", "Đại từ (pro)", "Giới từ (prep)", "Khác"]

# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════
def lbl(parent, text, size=12, weight="normal", color=None, **kw):
    return ctk.CTkLabel(parent, text=text, text_color=color or C["text"],
                        font=ctk.CTkFont(size=size, weight=weight), **kw)

def h1(parent, text, **kw):
    """Heading 1 - large title"""
    return ctk.CTkLabel(parent, text=text, text_color=C["accent"],
                        font=ctk.CTkFont(size=24, weight="bold"), **kw)

def h2(parent, text, **kw):
    """Heading 2 - section title"""
    return ctk.CTkLabel(parent, text=text, text_color=C["text"],
                        font=ctk.CTkFont(size=16, weight="bold"), **kw)

def sep(parent):
    ctk.CTkFrame(parent, height=1, fg_color=C["border"]).pack(fill="x", padx=15, pady=8)

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
                        text_color=C["text"], corner_radius=8, border_width=1)
    enable_entry_undo(e)
    return e

def search_entry(parent, placeholder="Tìm từ, nghĩa, phát âm...", width=300):
    """Specialized search entry with icon-like styling"""
    e = ctk.CTkEntry(parent, placeholder_text=placeholder, width=width,
                        fg_color=C["card"], border_color=C["accent"],
                        text_color=C["text"], corner_radius=20, border_width=1,
                        height=36)
    enable_entry_undo(e)
    return e

def combo(parent, values, width=200):
    c = ctk.CTkComboBox(parent, values=values, width=width,
                            fg_color=C["card"], border_color=C["accent"],
                            text_color=C["text"], button_color=C["accent"],
                            dropdown_fg_color=C["card2"], corner_radius=8)
    enable_entry_undo(c)
    return c

def btn(parent, text, color=None, hov=None, w=130, h=36, cmd=None, primary=False, **kw):
    """Enhanced button with primary/secondary styling"""
    if primary:
        fg = color or C["accent"]
        hover = hov or C["accent2"]
        txt_color = "#ffffff"
    else:
        fg = color or C["card2"]
        hover = hov or C["card3"]
        txt_color = C["text"]
    return ctk.CTkButton(parent, text=text,
                          fg_color=fg, hover_color=hover,
                          width=w, height=h, command=cmd,
                          font=ctk.CTkFont(size=13, weight="bold"), text_color=txt_color, **kw)

def primary_btn(parent, text, w=130, h=38, cmd=None, **kw):
    """Primary action button"""
    return btn(parent, text, color=C["accent"], hov=C["accent2"], w=w, h=h, cmd=cmd, primary=True, **kw)

def ghost_btn(parent, text, w=110, h=34, cmd=None, **kw):
    """Ghost button - subtle secondary action"""
    return btn(parent, text, color=C["card2"], hov=C["card3"], w=w, h=h, cmd=cmd, **kw)

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
        raw_headers = [c.strip() for c in table_lines[0].split('|')[1:-1]]
        # Dedupe header (Treeview crash nếu column id trùng nhau)
        headers, seen = [], {}
        for h in raw_headers:
            if h in seen:
                seen[h] += 1
                headers.append(f"{h} ({seen[h] + 1})")
            else:
                seen[h] = 0
                headers.append(h)
        if not headers:
            return
        
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
# Writing Practice Dialogs
# ══════════════════════════════════════════════════════════════════════════════
def run_webview_practice(word):
    import tempfile
    
    # Tách ký tự an toàn bằng json.dumps (chống vỡ JS khi từ chứa " \ < >...)
    chars_json = json.dumps([c for c in word if not c.isspace()])
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Luyện viết</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: sans-serif; background: #1e1e1e; color: #fff;
               display: flex; flex-direction: column; align-items: center;
               padding: 20px 15px; min-height: 100vh; }}
        h2 {{ color: #bb86fc; margin-bottom: 10px; font-size: 1.3rem; }}
        .practice-wrap {{ position: relative; width: 280px; height: 280px;
            border-radius: 12px; overflow: hidden; box-shadow: 0 2px 14px rgba(0,0,0,.5);
            cursor: crosshair; }}
        .practice-wrap canvas {{ position: absolute; top: 0; left: 0; }}
        #bg-c  {{ z-index: 1; }}
        #draw-c {{ z-index: 2; }}
        .controls {{ display: flex; gap: 10px; align-items: center;
                    flex-wrap: wrap; justify-content: center; margin-top: 14px; }}
        button {{ padding: 9px 16px; font-size: 15px; cursor: pointer; border: none;
                 border-radius: 6px; background: #383838; color: #fff; }}
        button:hover {{ background: #bb86fc; color: #111; }}
        #btn-score {{ background: #03dac6; color: #111; font-weight: bold; }}
        .score-ring {{ width: 100px; height: 100px; border-radius: 50%;
            border: 6px solid #bb86fc; display: none; align-items: center;
            justify-content: center; margin: 14px auto 4px;
            font-size: 1.6rem; font-weight: bold; color: #bb86fc;
            transition: border-color .4s, color .4s; }}
        #score-msg {{ text-align: center; font-size: .9rem; color: #a0a0a0;
                     margin-bottom: 6px; }}
        #indicator {{ font-weight: bold; min-width: 42px; text-align: center; }}
        .hint {{ font-size: .8rem; color: #888; margin-top: 10px; text-align: center; }}
    </style>
</head>
<body>
    <h2>✏️ Luyện viết — Có chấm điểm</h2>
    <div class="practice-wrap">
        <canvas id="ref-c" width="280" height="280" style="display:none;"></canvas>
        <canvas id="bg-c"  width="280" height="280"></canvas>
        <canvas id="draw-c" width="280" height="280"></canvas>
    </div>
    <div class="controls">
        <button id="btn-prev">⬅️</button>
        <span id="indicator">1/1</span>
        <button id="btn-next">➡️</button>
        <button id="btn-clear">🗑️ Xóa</button>
    </div>
    <div class="score-ring" id="score-ring"><span id="sv">0%</span></div>
    <p id="score-msg"></p>
    <div class="controls" style="margin-top:10px;">
        <button id="btn-score">⭐ Chấm điểm</button>
    </div>
    <p class="hint">Vẽ đè lên chữ mờ rồi nhấn ⭐ Chấm điểm</p>
    <script>
    const chars = {chars_json};
    let idx = 0;
    const W = 280, H = 280;
    const refC  = document.getElementById('ref-c');
    const bgC   = document.getElementById('bg-c');
    const drawC = document.getElementById('draw-c');
    const rCtx  = refC.getContext('2d', {{willReadFrequently:true}});
    const bCtx  = bgC.getContext('2d');
    const dCtx  = drawC.getContext('2d', {{willReadFrequently:true}});
    let drawing = false, lx=0, ly=0;

    function render() {{
        if (!chars.length) return;
        document.getElementById('indicator').textContent = (idx+1)+'/'+chars.length;
        document.getElementById('score-ring').style.display = 'none';
        document.getElementById('score-msg').textContent = '';
        const ch = chars[idx];
        // Reference canvas
        rCtx.clearRect(0,0,W,H); rCtx.fillStyle='white'; rCtx.fillRect(0,0,W,H);
        rCtx.save(); rCtx.fillStyle='black'; rCtx.shadowColor='black'; rCtx.shadowBlur=6;
        const fs = Math.floor(W*0.72);
        rCtx.font='normal '+fs+'px "Noto Sans","MS Gothic","Meiryo","Arial Unicode MS",sans-serif';
        rCtx.textAlign='center'; rCtx.textBaseline='middle'; rCtx.fillText(ch,W/2,H/2);
        rCtx.restore();
        // BG canvas (faint)
        bCtx.clearRect(0,0,W,H); bCtx.fillStyle='white'; bCtx.fillRect(0,0,W,H);
        bCtx.globalAlpha=0.10; bCtx.drawImage(refC,0,0); bCtx.globalAlpha=1;
        // Clear draw
        dCtx.clearRect(0,0,W,H);
    }}
    render();

    function score() {{
        const rd=rCtx.getImageData(0,0,W,H).data, dd=dCtx.getImageData(0,0,W,H).data;
        let rp=0,up=0,ol=0;
        for(let i=0;i<W*H;i++){{
            const x=i*4;
            if(rd[x]+rd[x+1]+rd[x+2]<450) rp++;
            if(dd[x+3]>30) up++;
            if(rd[x]+rd[x+1]+rd[x+2]<450 && dd[x+3]>30) ol++;
        }}
        if(!rp||!up) return 0;
        const rec=ol/rp, pre=ol/up;
        if(rec+pre===0) return 0;
        return Math.round(2*rec*pre/(rec+pre)*100);
    }}

    document.getElementById('btn-score').onclick=()=>{{
        const s=score();
        const ring=document.getElementById('score-ring');
        const sv=document.getElementById('sv');
        const sm=document.getElementById('score-msg');
        sv.textContent=s+'%';
        let c,msg;
        if(s>=85){{c='#03dac6';msg='🌟 Xuất sắc! Chữ rất chuẩn!';}}
        else if(s>=70){{c='#bb86fc';msg='✅ Tốt! Cần luyện thêm một chút.';}}
        else if(s>=50){{c='#ffb300';msg='👍 Khá ổn! Hãy thử lại nhé.';}}
        else{{c='#cf6679';msg='💪 Hãy luyện thêm! Thử lại nào.';}}
        ring.style.borderColor=c; sv.style.color=c;
        ring.style.display='flex'; sm.textContent=msg;
    }};
    document.getElementById('btn-clear').onclick=()=>{{
        dCtx.clearRect(0,0,W,H);
        document.getElementById('score-ring').style.display='none';
        document.getElementById('score-msg').textContent='';
    }};
    document.getElementById('btn-prev').onclick=()=>{{ if(idx>0){{idx--;render();}} }};
    document.getElementById('btn-next').onclick=()=>{{ if(idx<chars.length-1){{idx++;render();}} }};

    function getPos(e){{
        const r=drawC.getBoundingClientRect();
        const sx=W/r.width, sy=H/r.height;
        const src=e.touches?e.touches[0]:e;
        return {{x:(src.clientX-r.left)*sx, y:(src.clientY-r.top)*sy}};
    }}
    function stroke(x,y){{
        dCtx.beginPath(); dCtx.moveTo(lx,ly); dCtx.lineTo(x,y);
        dCtx.strokeStyle='#1a1a2e'; dCtx.lineWidth=20;
        dCtx.lineCap='round'; dCtx.lineJoin='round'; dCtx.stroke();
        lx=x; ly=y;
    }}
    drawC.addEventListener('mousedown',e=>{{drawing=true;const p=getPos(e);lx=p.x;ly=p.y;}});
    drawC.addEventListener('mousemove',e=>{{if(!drawing)return;const p=getPos(e);stroke(p.x,p.y);}});
    drawC.addEventListener('mouseup',()=>drawing=false);
    drawC.addEventListener('mouseout',()=>drawing=false);
    drawC.addEventListener('touchstart',e=>{{e.preventDefault();drawing=true;const p=getPos(e);lx=p.x;ly=p.y;}},{{passive:false}});
    drawC.addEventListener('touchmove',e=>{{e.preventDefault();if(!drawing)return;const p=getPos(e);stroke(p.x,p.y);}},{{passive:false}});
    drawC.addEventListener('touchend',()=>drawing=false);
    </script>
</body>
</html>"""
    
    script_py = f"""
import webview
import sys, os
html_content = {repr(html)}
webview.create_window("Luyện viết", html=html_content, width=400, height=550)
webview.start()
try:
    os.remove(sys.argv[0])  # tự dọn temp script
except OSError:
    pass
sys.exit(0)
"""
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(script_py)
        script_path = f.name
        
    subprocess.Popen([sys.executable, script_path])


class CanvasPracticeDialog(ctk.CTkToplevel):
    def __init__(self, parent, word):
        super().__init__(parent)
        self.title("Luyện viết (Bảng nháp)")
        self.geometry("400x550")
        self.configure(fg_color=C["bg"])
        self.grab_set(); self.lift(); self.focus_force()
        self._chars = word.replace(" ", "")
        self._idx = 0
        
        lbl(self, "Bảng nháp (Tự do)", 16, "bold", C["accent"]).pack(pady=(15, 5))
        lbl(self, "Vẽ tự do, không kiểm tra nét", 12, "normal", C["muted"]).pack(pady=(0, 10))
        
        self.canvas = tk.Canvas(self, width=300, height=300, bg="white", highlightthickness=0)
        self.canvas.pack(pady=10)
        
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        
        self.last_x = 0
        self.last_y = 0
        
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(pady=10)
        
        btn(controls, "⬅️", C["card2"], C["border"] if "border" in C else "#444", w=40, h=30, cmd=self.prev_char).pack(side="left", padx=5)
        self.lbl_idx = lbl(controls, "1/1", 14, "bold", C["text"])
        self.lbl_idx.pack(side="left", padx=15)
        btn(controls, "➡️", C["card2"], C["border"] if "border" in C else "#444", w=40, h=30, cmd=self.next_char).pack(side="left", padx=5)
        btn(controls, "Xóa bảng", C["card2"], C["danger"], w=80, h=30, cmd=self.clear_board).pack(side="left", padx=15)
        
        self.render_char()
        
    def render_char(self):
        if not self._chars: return
        self.lbl_idx.configure(text=f"{self._idx + 1}/{len(self._chars)}")
        self.clear_board()
        
    def prev_char(self):
        if self._idx > 0:
            self._idx -= 1
            self.render_char()
            
    def next_char(self):
        if self._idx < len(self._chars) - 1:
            self._idx += 1
            self.render_char()

    def start_draw(self, event):
        self.last_x = event.x
        self.last_y = event.y
        
    def draw(self, event):
        self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, fill="#333333", width=20, capstyle=tk.ROUND, smooth=True)
        self.last_x = event.x
        self.last_y = event.y
        
    def clear_board(self):
        self.canvas.delete("all")
        if self._chars:
            char = self._chars[self._idx]
            self.canvas.create_text(150, 150, text=char, font=("Arial", 200, "normal"), fill="#e0e0e0")

class PracticeChoiceDialog(ctk.CTkToplevel):
    def __init__(self, parent, word):
        super().__init__(parent)
        self.title("Chọn chế độ luyện viết")
        self.geometry("350x220")
        self.configure(fg_color=C["bg"])
        self.grab_set(); self.lift(); self.focus_force()
        self._word = word
        
        lbl(self, "Luyện viết chữ", 16, "bold", C["accent"]).pack(pady=(20, 15))
        
        btn(self, "Có chấm điểm (Chữ Hán/Kanji)", C["accent"], C["accent2"], w=250, h=40, cmd=self.mode_hanzi).pack(pady=8)
        btn(self, "Bảng nháp (Tự do)", C["card2"], C["border"] if "border" in C else "#444", w=250, h=40, cmd=self.mode_canvas).pack(pady=8)
        
    def mode_hanzi(self):
        self.destroy()
        run_webview_practice(self._word)
        
    def mode_canvas(self):
        self.destroy()
        CanvasPracticeDialog(self.master, self._word)

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

        # Từ vựng & Phát âm — có nút 🔊 TTS
        word_row = ctk.CTkFrame(scroll, fg_color="transparent")
        word_row.pack(fill="x", pady=(10,2))
        lbl(word_row, "Từ vựng *", 12, "bold", C["accent"], anchor="w").pack(side="left")
        btn(word_row, "🔊", C["card2"], C["accent"], w=44, h=24,
            cmd=lambda: speak_word(self.e_word.get().strip(), self.app.current_language)
        ).pack(side="left", padx=(10,0))
        self.e_word = entry(scroll, "Nhập từ vựng...")
        self.e_word.pack(fill="x", expand=True)
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
        
        # Xây dựng danh sách hiển thị: "Tiếng Nhật (1260 ngày)"
        display_values = []
        for l in self.app.available_languages:
            if l["num_days"] > 0:
                display_values.append(f"{l['display']} ({l['num_days']} ngày)")
            else:
                display_values.append(l["display"])
        self.cb_lang_main = combo(tb, display_values, width=200)
        # Tìm index của ngôn ngữ hiện tại
        current_idx = 0
        for i, l in enumerate(self.app.available_languages):
            if l["slug"] == self.app.current_language:
                current_idx = i
                break
        self.cb_lang_main.set(display_values[current_idx])
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
        btn(self.action_row, "✏️ Luyện viết", C["success"], "#018786", w=120, h=36, cmd=self._practice_write).pack(side="left", padx=10)
        btn(self.action_row, "🔊 Đọc", C["card2"], C["accent"], w=90, h=36,
            cmd=lambda: speak_word(
                self._selected.get("word", "") if self._selected else "",
                self.app.current_language
            )
        ).pack(side="left", padx=4)

    def _on_lang_change(self, choice: str):
        """choice là chuỗi hiển thị như 'Tiếng Nhật (1260 ngày)' hoặc 'Tiếng Anh'."""
        # Tìm slug tương ứng
        for l in self.app.available_languages:
            if l["num_days"] > 0:
                display = f"{l['display']} ({l['num_days']} ngày)"
            else:
                display = l["display"]
            if display == choice:
                self.app.set_language(l["slug"])
                return
        # Nếu không tìm thấy, dùng trực tiếp choice làm slug
        self.app.set_language(choice)

    def refresh_filters(self):
        lang = self.app.current_language  # Đây là slug (ví dụ: "tiếng_nhật")
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
            # Tự động tạo slug từ tên
            from ai.paths import lang_slug
            slug = lang_slug(lang)
            self.app.set_language(slug)

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

    def _practice_write(self):
        if not self._selected: return
        word = self._selected.get("word", "")
        PracticeChoiceDialog(self.app, word)

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

        sep(scroll)

        # ── AI Model Settings ──
        lbl(scroll, "Cài Đặt Model AI (Gemini)", 15, "bold", C["accent"]).pack(anchor="w", pady=(10,4))
        lbl(scroll, "Quản lý danh sách model, benchmark tốc độ và tự động cập nhật khi Google đổi model", 12, color=C["muted"]).pack(anchor="w", pady=2)
        btn(scroll, "⚙️ Cài Đặt & Khám Phá Model AI", C["accent"], C["accent2"], w=260, h=36,
            cmd=lambda: ModelSettingsDialog(self.app)).pack(anchor="w", pady=8)

        sep(scroll)

        # ── Bridge Web AI (Chrome addon) ──
        lbl(scroll, "🌐 Bridge Web AI (Chrome Addon)", 15, "bold", C["accent"]).pack(anchor="w", pady=(10,4))
        lbl(scroll, "Bật bridge để addon VocabAIExtractor lấy nội dung + ảnh minh họa từ "
                    "Gemini/ChatGPT/Copilot. Sau đó load unpacked thư mục "
                    "addon/VocabAIExtractor trong Chrome.", 12, color=C["muted"]).pack(anchor="w", pady=2)

        br_row = ctk.CTkFrame(scroll, fg_color="transparent"); br_row.pack(anchor="w", pady=6)
        self.btn_bridge = btn(br_row, "▶ Bật Bridge (5690)", C["success"], "#018786",
                              w=170, h=34, cmd=self._toggle_bridge)
        self.btn_bridge.pack(side="left", padx=(0,10))
        btn(br_row, "📋 Copy Token", C["card2"], C["accent"], w=140, h=34,
            cmd=self._copy_bridge_token).pack(side="left")

        self.lbl_bridge = lbl(scroll, "Trạng thái: Đang tắt", 12, color=C["muted"])
        self.lbl_bridge.pack(anchor="w", pady=4)

        tok_frame = ctk.CTkFrame(scroll, fg_color=C["card2"])
        tok_frame.pack(fill="x", pady=(4, 14))
        lbl(tok_frame, "Token bridge:", 12, color=C["muted"]).pack(side="left", padx=12, pady=8)
        self.lbl_bridge_token = lbl(tok_frame, "-", 12, "bold", C["accent"])
        self.lbl_bridge_token.pack(side="left")

        sep(scroll)

        # ── Media / Ảnh minh họa ──
        lbl(scroll, "🖼️ Ảnh Minh Họa & Media", 15, "bold", C["accent"]).pack(anchor="w", pady=(10,4))
        _ms = load_settings().get("media", {}) or {}
        self.media_providers = combo(scroll, ["web, dict, placeholder", "dict, placeholder",
                                             "web, dict, placeholder, gemini"],
                                    width=280)
        try:
            self.media_providers.set(", ".join(_ms.get("image_providers") or ["web", "dict", "placeholder"]))
        except Exception:
            pass
        self.media_providers.pack(anchor="w", pady=2)
        lbl(scroll, "Chuỗi nguồn ảnh (cao → thấp). 'dict' = Wikipedia/Wiktionary/Commons (0 key, luôn dùng được).",
            11, color=C["muted"]).pack(anchor="w", pady=2)

        self.media_sync_langs = entry(scroll, "Ngôn ngữ sync media lên web (csv, ví dụ: tiếng_anh,nhật)")
        self.media_sync_langs.insert(0, ",".join(_ms.get("sync_langs") or []))
        self.media_sync_langs.pack(anchor="w", pady=2)
        lbl(scroll, "Để trống = không sync media lên GitHub Pages (tiết kiệm dung lượng repo).",
            11, color=C["muted"]).pack(anchor="w", pady=2)

        btn(scroll, "💾 Lưu Cài Đặt Media", C["accent"], C["accent2"], w=200, h=34,
            cmd=self._save_media_settings).pack(anchor="w", pady=10)

    # ── Bridge Web AI ──────────────────────────────────────────────────────
    def _toggle_bridge(self):
        from ai.web_ai_bridge import get_bridge, stop_bridge
        b = get_bridge()
        if b is not None and getattr(self, "_bridge_on", False):
            stop_bridge()
            self._bridge_on = False
            self.btn_bridge.configure(text="▶ Bật Bridge (5690)")
            self.lbl_bridge.configure(text="Trạng thái: Đã tắt", text_color=C["muted"])
            self.lbl_bridge_token.configure(text="-")
            return
        b = get_bridge()
        if b is None:
            self.lbl_bridge.configure(text="Trạng thái: Không khởi động được (thiếu Flask?)",
                                     text_color=C["danger"])
            return
        self._bridge_on = True
        self.btn_bridge.configure(text="⏹ Tắt Bridge")
        self.lbl_bridge.configure(text=f"Trạng thái: ĐANG CHẠY tại http://127.0.0.1:{b.port}",
                                  text_color=C["success"])
        self.lbl_bridge_token.configure(text=b.token)

    def _copy_bridge_token(self):
        from ai.web_ai_bridge import get_bridge
        b = get_bridge()
        if b is None:
            messagebox.showwarning("Bridge", "Bridge chưa bật. Bấm 'Bật Bridge' trước.", parent=self.app)
            return
        self.app.clipboard_clear()
        self.app.clipboard_append(b.token)
        self.lbl_bridge_token.configure(text=b.token)
        messagebox.showinfo("Bridge", f"Đã copy token:\n{b.token}", parent=self.app)

    def _save_media_settings(self):
        from settings import update_ai_settings
        providers = [p.strip() for p in (self.media_providers.get() or "").split(",") if p.strip()]
        langs = [l.strip() for l in (self.media_sync_langs.get() or "").split(",") if l.strip()]
        try:
            update_ai_settings(media_providers=providers)
        except Exception:
            pass
        s = load_settings()
        s.setdefault("media", {})
        s["media"]["image_providers"] = providers
        s["media"]["sync_langs"] = langs
        from settings import save_settings
        save_settings(s)
        messagebox.showinfo("Thành công", f"Đã lưu:\n• Nguồn ảnh: {', '.join(providers)}\n"
                                             f"• Sync media: {', '.join(langs) or '(không)'}", parent=self.app)

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
        if self._syncing:
            return
        if not self._gdrive.is_authenticated():
            messagebox.showwarning("Chưa kết nối", "Vui lòng kết nối Google Drive trước!", parent=self.app)
            return
        self._syncing = True
        threading.Thread(target=self._do_drive_sync_safe, daemon=True).start()

    def _do_drive_sync_safe(self):
        try:
            self._do_drive_sync()
        except Exception as e:
            self._log(f"❌ Lỗi upload Drive: {e}")
        finally:
            self._syncing = False

    def _do_drive_sync(self):
        self._log("Bắt đầu upload Google Drive...")
        folders = self._gdrive.ensure_folders()
        
        # Duyệt qua các từ vựng của ngôn ngữ hiện tại
        vocabs = get_all_vocab(self.app.current_language)
        count = 0
        total = max(len(vocabs), 1)  # tránh chia 0 nếu danh sách rỗng
        for i, v in enumerate(vocabs):
            if v.get("mp3_local_path") and not v.get("mp3_gdrive_id"):
                updates = self._gdrive.sync_vocab_media(v, folders)
                if updates:
                    update_vocab(self.app.current_language, v["id"], updates)
                    count += 1
            # Cập nhật progress qua self.after (tkinter không thread-safe)
            self.after(0, lambda p=(i+1)/total: self.progress.set(p))
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
# Tab: Hoc Tap (Tu hoc / Khoa hoc AI)
# ══════════════════════════════════════════════════════════════════════════════
SOURCE_SELF = "📖 Từ vựng tự học"
SOURCE_AI = "🤖 Khóa học AI chuyên sâu"
SOURCE_SRS = "🔁 Ôn tập SM-2 (lặp lại ngắt quãng)"

# (grade, nhãn, màu nền, màu hover) cho 4 nút đánh giá SM-2
SRS_GRADE_STYLE = (
    ("again", "😵 Quên", "#cf6679", "#b04a5a"),
    ("hard",  "😕 Khó", "#ffb300", "#d18f00"),
    ("good",  "🙂 Được", "#03dac6", "#018786"),
    ("easy",  "😎 Dễ", "#bb86fc", "#9965f4"),
)

# Nhãn trạng thái thuộc (dùng cho cả GUI lẫn web)
SRS_STATE_LABEL = {
    STATE_NEW: "🆕 Mới",
    STATE_LEARNING: "📖 Đang học",
    STATE_REVIEW: "🔁 Đang ôn",
    STATE_MASTERED: "🏆 Đã thuộc",
}


# ══════════════════════════════════════════════════════════════════════════════
# Dialog: Cài Đặt & Tự Khám Phá Model AI
# ══════════════════════════════════════════════════════════════════════════════
class ModelSettingsDialog(ctk.CTkToplevel):
    """Dialog cấu hình thứ tự ưu tiên model AI và tự động quét/benchmark model mới từ Google API."""

    _TIER_META = {
        "S": {"badge": "🔴 S", "color": "#e74c3c", "score_bonus": 500},
        "A": {"badge": "🟠 A", "color": "#e67e22", "score_bonus": 300},
        "B": {"badge": "🟡 B", "color": "#f1c40f", "score_bonus": 100},
        "C": {"badge": "⚪ C", "color": "#95a5a6", "score_bonus":   0},
    }

    @staticmethod
    def _infer_tier(name):
        n = name.lower()
        if "3.5" in n or "3-ultra" in n:
            return "S"
        if "3-flash" in n or "3.0" in n or "flash-latest" in n:
            return "A"
        if "lite" in n or "3.1" in n:
            return "B"
        return "C"

    def __init__(self, parent):
        super().__init__(parent)
        import threading
        from tkinter import ttk
        self._thread = None
        self._stop_flag = [False]

        # Nạp cấu hình hiện tại
        _st = load_settings()
        _saved = _st.get("ai", {}).get("model_priority", [])
        if not _saved:
            _saved = [
                {"name": m, "enabled": True, "tier": self._infer_tier(m), "note": "", "latency_ms": 0}
                for m in _DEFAULT_MODEL_FALLBACKS
            ]
        self._models = [dict(m) for m in _saved]

        # Window
        self.title("⚙️  Cài Đặt & Tự Khám Phá Model AI — VocabularyApp")
        self.geometry("780x600")
        self.minsize(680, 520)
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=C["bg"])
        self.bind("<Escape>", lambda e: self.destroy())

        # Header
        hdr = ctk.CTkFrame(self, fg_color=C["sidebar"], height=52, corner_radius=0)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        lbl(hdr, "⚙️  Cài Đặt Model AI", 14, "bold", C["accent"]).pack(side="left", padx=14, pady=8)
        lbl(hdr, "Sắp xếp thứ tự ưu tiên fallback — Model đứng đầu được thử trước",
            10, color=C["muted"]).pack(side="left", padx=4)

        # Treeview
        from tkinter import ttk as _ttk
        tree_frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=8)
        tree_frame.pack(fill="both", expand=True, padx=14, pady=(10, 4))

        cols = ("order", "tier", "name", "note", "latency", "enabled")
        style = _ttk.Style()
        style.theme_use("clam")
        style.configure("ModelDark.Treeview",
                        background="#1e1e1e", foreground="#ffffff",
                        fieldbackground="#1e1e1e", rowheight=28,
                        borderwidth=0, font=("Consolas", 10))
        style.configure("ModelDark.Treeview.Heading",
                        background="#2c2c2c", foreground="#bb86fc",
                        font=("Arial", 10, "bold"), relief="flat")
        style.map("ModelDark.Treeview", background=[("selected", "#3a3a5c")])

        self._tree = _ttk.Treeview(tree_frame, columns=cols, show="headings",
                                   selectmode="browse", height=12,
                                   style="ModelDark.Treeview")
        for col, txt, w in [("order", "#", 36), ("tier", "Tier", 62),
                             ("name", "Tên Model", 235), ("note", "Ghi chú", 200),
                             ("latency", "Độ trễ", 80), ("enabled", "Trạng thái", 90)]:
            self._tree.heading(col, text=txt)
            self._tree.column(col, width=w, anchor="center" if col in ("order","tier","latency","enabled") else "w",
                              stretch=(col == "name"))

        vsb = _ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(fill="both", expand=True, side="left")
        vsb.pack(fill="y", side="left")

        self._refresh_tree()

        # Control buttons
        ctrl = ctk.CTkFrame(self, fg_color="transparent")
        ctrl.pack(fill="x", padx=14, pady=2)
        _bc = {"width": 88, "height": 30, "corner_radius": 6}
        btn(ctrl, "↑ Lên",           C["card2"], C["accent"],  **_bc, cmd=self._move_up).pack(side="left", padx=2)
        btn(ctrl, "↓ Xuống",         C["card2"], C["accent"],  **_bc, cmd=self._move_down).pack(side="left", padx=2)
        btn(ctrl, "☑/☒ Bật/Tắt",    C["card2"], C["warn"],    **_bc, cmd=self._toggle_enabled).pack(side="left", padx=2)
        btn(ctrl, "🔀 Xếp theo Điểm",C["card2"], C["success"], **_bc, cmd=self._auto_sort).pack(side="left", padx=2)
        btn(ctrl, "↩ Mặc định",      C["card2"], C["muted"],   **_bc, cmd=self._reset_default).pack(side="left", padx=2)

        # Discover row
        disc = ctk.CTkFrame(self, fg_color="transparent")
        disc.pack(fill="x", padx=14, pady=(2, 4))
        self._btn_discover = btn(disc, "🔍 Auto Discover & Đánh giá",
                                 C["success"], "#018786", width=210, height=34,
                                 cmd=self._do_discover)
        self._btn_discover.pack(side="left", padx=2)
        self._btn_stop = btn(disc, "⏹ Dừng", C["card2"], C["danger"],
                             width=80, height=34, cmd=lambda: self._stop_flag.__setitem__(0, True))
        self._btn_stop.pack(side="left", padx=2)
        self._btn_stop.configure(state="disabled")
        lbl(disc, "← Tự quét model mới nhất từ Google API rồi đo tốc độ & xếp hạng",
            9, color=C["muted"]).pack(side="left", padx=8)

        # Log panel
        log_frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=6)
        log_frame.pack(fill="x", padx=14, pady=(0, 4))
        lbl(log_frame, "📋 Log:", 9, "bold", C["text"]).pack(anchor="w", padx=8, pady=(4, 0))
        self._log_box = ctk.CTkTextbox(log_frame, height=90, fg_color="#0d1117",
                                       text_color="#00e676", font=("Consolas", 9),
                                       state="disabled")
        self._log_box.pack(fill="x", padx=4, pady=(0, 4))

        # ── Dead Model Status Panel ──
        dead_frame = ctk.CTkFrame(self, fg_color=C["card"], corner_radius=6)
        dead_frame.pack(fill="x", padx=14, pady=(0, 4))
        lbl(dead_frame, "🚫 Model Bị Khóa (Cooldown)", 9, "bold", C["warn"]).pack(anchor="w", padx=8, pady=(4, 0))
        dead_ctrl = ctk.CTkFrame(dead_frame, fg_color="transparent")
        dead_ctrl.pack(fill="x", padx=8, pady=(0, 4))
        self._dead_box = ctk.CTkTextbox(dead_frame, height=60, fg_color="#1a1a1a",
                                        text_color="#ffb300", font=("Consolas", 9),
                                        state="disabled")
        self._dead_box.pack(fill="x", padx=4, pady=(0, 4))
        btn(dead_ctrl, "🔄 Làm Mới", C["card2"], C["accent"], width=80, height=26,
            cmd=self._refresh_dead_models).pack(side="left", padx=2)
        btn(dead_ctrl, "🔓 Mở Khóa Tất Cả", C["card2"], C["success"], width=110, height=26,
            cmd=self._reset_all_dead).pack(side="left", padx=2)
        lbl(dead_ctrl, f"Khóa {DEAD_MODEL_COOLDOWN_MINUTES} phút sau {MAX_FAILURES_BEFORE_DEAD} lần lỗi",
            8, color=C["muted"]).pack(side="right", padx=4)

        # Bottom buttons
        bot = ctk.CTkFrame(self, fg_color=C["sidebar"], height=52, corner_radius=0)
        bot.pack(fill="x", side="bottom")
        bot.pack_propagate(False)
        btn(bot, "💾 Lưu & Áp dụng", C["success"], "#018786",
            width=160, height=36, cmd=self._save_and_close).pack(side="left", padx=12, pady=8)
        btn(bot, "Đóng (không lưu)", C["card2"], C["muted"],
            width=140, height=36, cmd=self.destroy).pack(side="left", padx=4)
        lbl(bot, "💡 Mẹo: Auto Discover → Xếp theo Điểm → Lưu & Áp dụng",
            9, color=C["muted"]).pack(side="right", padx=12)

        self._log_msg("📋 Dialog sẵn sàng. Nhấn '🔍 Auto Discover & Đánh giá' để quét model mới nhất.")
        # Hiển thị trạng thái model bị khóa ban đầu
        self.after(100, self._refresh_dead_models)

    # ── helpers ──

    def _log_msg(self, msg):
        def _do():
            try:
                self._log_box.configure(state="normal")
                self._log_box.insert("end", msg + "\n")
                self._log_box.see("end")
                self._log_box.configure(state="disabled")
            except Exception:
                pass
        self.after(0, _do)

    def _refresh_dead_models(self):
        """Hiển thị danh sách model đang bị khóa cooldown."""
        try:
            dead_info = {}
            # Lấy từ in-memory tracking trong GeminiCoordinator
            # Nếu có coordinator đang chạy, lấy từ đó; ngược lại đọc từ file
            try:
                from ai.pipeline_store import load_dead_models as _ldm
                dead_raw = _ldm(self.app.current_language if hasattr(self, 'app') else 'Tiếng Nhật')
            except Exception:
                dead_raw = {}
            lines = []
            if not dead_raw:
                lines.append("✅ Không có model nào đang bị khóa.")
            else:
                import time
                now = time.time()
                for model, info in dead_raw.items():
                    if not isinstance(info, dict):
                        continue
                    until = info.get("until", 0)
                    fail_count = info.get("fail_count", 0)
                    status = info.get("status", "warning")
                    reason = info.get("reason", "")
                    if until <= now:
                        lines.append(f"✅ {model}: đã hết hạn cooldown (đã sẵn sàng)")
                        continue
                    wait_s = int(until - now)
                    mins = wait_s // 60
                    secs = wait_s % 60
                    icon = "🔴" if status == "dead" else "🟡"
                    lines.append(f"{icon} {model}: khóa {mins}p{secs:02d}s (lỗi {fail_count}x: {reason})")
            self._dead_box.configure(state="normal")
            self._dead_box.delete("1.0", "end")
            self._dead_box.insert("1.0", "\n".join(lines))
            self._dead_box.configure(state="disabled")
            self._log_msg("🔄 Đã làm mới trạng thái model bị khóa.")
        except Exception as e:
            self._log_msg(f"❌ Lỗi làm mới model khóa: {e}")

    def _reset_all_dead(self):
        """Mở khóa tất cả model đang bị cooldown."""
        try:
            from ai.pipeline_store import load_dead_models as _ldm, save_dead_models as _sdm
            lang = getattr(self, 'app', None)
            lang_name = lang.current_language if lang else 'Tiếng Nhật'
            dead = _ldm(lang_name)
            reset_count = 0
            for model in list(dead.keys()):
                dead[model] = {"until": 0, "fail_count": 0, "status": "active",
                               "reason": "reset by user", "reset_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
                reset_count += 1
            _sdm(lang_name, dead)
            self._refresh_dead_models()
            self._log_msg(f"🔓 Đã mở khóa {reset_count} model.")
        except Exception as e:
            self._log_msg(f"❌ Lỗi mở khóa model: {e}")

    def _latency_str(self, ms):
        if ms <= 0: return "—"
        return f"{ms}ms" if ms < 1000 else f"{ms/1000:.1f}s"

    def _refresh_tree(self):
        self._tree.delete(*self._tree.get_children())
        for i, m in enumerate(self._models, 1):
            tier  = m.get("tier", self._infer_tier(m["name"]))
            badge = self._TIER_META.get(tier, self._TIER_META["C"])["badge"]
            lat   = self._latency_str(m.get("latency_ms", 0))
            en    = "✅ Bật" if m.get("enabled", True) else "☒ Tắt"
            tag   = "en" if m.get("enabled", True) else "dis"
            self._tree.insert("", "end", iid=str(i - 1),
                              values=(i, badge, m["name"], m.get("note", ""), lat, en),
                              tags=(tag,))
        self._tree.tag_configure("en",  foreground="#e0e0ff")
        self._tree.tag_configure("dis", foreground="#555577")

    def _sel_idx(self):
        sel = self._tree.selection()
        return int(sel[0]) if sel else None

    def _move_up(self):
        idx = self._sel_idx()
        if idx is None or idx == 0: return
        self._models[idx - 1], self._models[idx] = self._models[idx], self._models[idx - 1]
        self._refresh_tree()
        self._tree.selection_set(str(idx - 1))

    def _move_down(self):
        idx = self._sel_idx()
        if idx is None or idx >= len(self._models) - 1: return
        self._models[idx], self._models[idx + 1] = self._models[idx + 1], self._models[idx]
        self._refresh_tree()
        self._tree.selection_set(str(idx + 1))

    def _toggle_enabled(self):
        idx = self._sel_idx()
        if idx is None: return
        self._models[idx]["enabled"] = not self._models[idx].get("enabled", True)
        self._refresh_tree()
        self._tree.selection_set(str(idx))

    def _auto_sort(self):
        def _score(m):
            ms2 = m.get("latency_ms", 0)
            tb  = self._TIER_META.get(m.get("tier", "C"), self._TIER_META["C"])["score_bonus"]
            return tb + (1000 / ms2 if ms2 > 0 else 0)
        self._models.sort(key=_score, reverse=True)
        self._refresh_tree()
        self._log_msg("🔀 Đã xếp theo điểm (Tier + Tốc độ).")

    def _reset_default(self):
        from tkinter import messagebox as _mb
        if not _mb.askyesno("Xác nhận", "Khôi phục danh sách model mặc định?", parent=self):
            return
        self._models = [
            {"name": n, "enabled": True, "tier": self._infer_tier(n), "note": "", "latency_ms": 0}
            for n in _DEFAULT_MODEL_FALLBACKS
        ]
        self._refresh_tree()
        self._log_msg("↩ Đã khôi phục danh sách model mặc định.")

    def _save_and_close(self):
        update_ai_settings(model_priority=[dict(m) for m in self._models])
        self._log_msg("💾 Đã lưu cấu hình model!")
        self.after(300, self.destroy)

    # ── Auto Discover ──

    def _do_discover(self):
        import threading
        self._stop_flag[0] = False
        self._btn_discover.configure(state="disabled", text="⏳ Đang quét...")
        self._btn_stop.configure(state="normal")

        def _run():
            try:
                self._discover_inner()
            except Exception as ex:
                self._log_msg(f"❌ Lỗi discover: {ex}")
            finally:
                self.after(0, lambda: self._btn_discover.configure(state="normal", text="🔍 Auto Discover & Đánh giá"))
                self.after(0, lambda: self._btn_stop.configure(state="disabled"))

        threading.Thread(target=_run, daemon=True).start()

    def _discover_inner(self):
        import time, requests as _req, json as _json
        from ai.course_generator import _load_gemini_keys

        # Lấy API key đầu tiên đang active
        all_keys = _load_gemini_keys()
        now = time.time()
        active_key = None
        for k in all_keys:
            if k.get("status", "active") == "active" and k.get("cooldown_until", 0) <= now:
                raw = k.get("key", "")
                if raw:
                    active_key = raw
                    break

        if not active_key:
            self._log_msg("❌ Không tìm thấy API key active. Kiểm tra settings AskCpl.")
            return

        # Bước 1: lấy danh sách model từ Google API
        self._log_msg("🌐 Bước 1: Gọi GET /v1beta/models để lấy danh sách model...")
        try:
            resp = _req.get(
                f"https://generativelanguage.googleapis.com/v1beta/models?key={active_key}&pageSize=100",
                timeout=20)
            if resp.status_code != 200:
                self._log_msg(f"⚠ API trả về HTTP {resp.status_code}: {resp.text[:120]}")
                return
            raw_list = resp.json().get("models", [])
        except Exception as e:
            self._log_msg(f"❌ Không gọi được API: {e}")
            return

        discovered = []
        for m in raw_list:
            mname = m.get("name", "").replace("models/", "")
            if "generateContent" not in m.get("supportedGenerationMethods", []):
                continue
            n = mname.lower()
            if "flash" not in n and "gemini" not in n:
                continue
            if any(x in n for x in ("embed", "vision", "imagen", "thinking", "image",
                                     "transcribe", "audio", "tts", "robotics")):
                continue
            discovered.append(mname)

        self._log_msg(f"✅ Tìm thấy {len(discovered)} model khả dụng: "
                      f"{', '.join(discovered[:5])}{'...' if len(discovered) > 5 else ''}")
        if not discovered:
            return

        # Bước 2: Benchmark
        self._log_msg(f"⏱ Bước 2: Benchmark {len(discovered)} model (prompt 'Hi', maxTokens=5)...")
        payload = {"contents": [{"parts": [{"text": "Hi"}]}],
                   "generationConfig": {"maxOutputTokens": 5}}
        results = {}
        for mname in discovered:
            if self._stop_flag[0]:
                self._log_msg("🛑 Người dùng yêu cầu dừng.")
                break
            url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
                   f"{mname}:generateContent?key={active_key}")
            try:
                t0 = time.time()
                r = _req.post(url, json=payload,
                              headers={"Content-Type": "application/json"}, timeout=15)
                ms = int((time.time() - t0) * 1000)
                if r.status_code == 200:
                    results[mname] = ms
                    self._log_msg(f"  ✅ {mname}: {ms}ms")
                elif r.status_code == 429:
                    results[mname] = -2
                    self._log_msg(f"  ⚠ {mname}: Rate limit (429) — key OK")
                elif r.status_code in (404, 400):
                    results[mname] = -3
                    self._log_msg(f"  ✗ {mname}: HTTP {r.status_code} — không truy cập được")
                else:
                    results[mname] = -1
                    self._log_msg(f"  ✗ {mname}: HTTP {r.status_code}")
            except Exception as ex:
                results[mname] = -1
                self._log_msg(f"  ✗ {mname}: {ex}")
            time.sleep(0.5)

        # Bước 3: Cập nhật danh sách
        self._log_msg("🔄 Bước 3: Cập nhật danh sách model trong UI...")
        existing = {m["name"] for m in self._models}
        for mname, ms in results.items():
            tier = self._infer_tier(mname)
            note_suffix = (f"({ms}ms)" if ms > 0 else
                           "(Rate limit)" if ms == -2 else
                           "(Không truy cập)" if ms == -3 else "(Lỗi)")
            if mname in existing:
                for m in self._models:
                    if m["name"] == mname:
                        m["latency_ms"] = max(ms, 0)
                        m["tier"] = tier
                        m["note"] = f"Tier {tier} — {note_suffix}"
                        break
            else:
                self._models.append({
                    "name": mname, "enabled": ms > 0, "tier": tier,
                    "note": f"[Mới] Tier {tier} — {note_suffix}",
                    "latency_ms": max(ms, 0)
                })

        # Auto-sort sau discover
        def _score(m):
            ms2 = m.get("latency_ms", 0)
            tb  = self._TIER_META.get(m.get("tier", "C"), self._TIER_META["C"])["score_bonus"]
            return tb + (1000 / ms2 if ms2 > 0 else 0)
        self._models.sort(key=_score, reverse=True)
        self.after(0, self._refresh_tree)
        self._log_msg(f"✅ Hoàn tất! {len(results)} model được đánh giá và xếp hạng tự động.")


class CourseGenerationDialog(ctk.CTkToplevel):
    """Dialog sinh khóa học AI: chọn số từ/ngày, chạy nền, log tiến độ."""

    def __init__(self, parent, app, on_finished):
        super().__init__(parent)
        self.app = app
        self.on_finished = on_finished
        self._stop_event = threading.Event()
        self._running = False

        self.title("Sinh khóa học AI chuyên sâu")
        self.geometry("680x580")
        self.configure(fg_color=C["bg"])
        self.grab_set(); self.lift(); self.focus_force()

        lang = app.current_language
        lbl(self, f"🤖 Khóa học AI riêng cho: {lang}", 16, "bold", C["accent"]).pack(pady=(15, 2))
        lbl(self, "Hệ thống học ĐỘC LẬP hoàn toàn — không liên kết danh sách từ vựng chính",
            11, color=C["muted"]).pack()
        lbl(self, "AI toàn quyền thiết kế giáo trình: tự quyết số ngày + chủ đề + từ vựng, "
                  "đi từ con số 0 đến gần người bản xứ", 12, color=C["success"]).pack(pady=(4, 8))

        n_keys = count_available_keys()
        key_color = C["success"] if n_keys else C["danger"]
        lbl(self, f"🔑 Gemini API keys tìm thấy (AskCpl): {n_keys}", 12,
            color=key_color).pack(pady=(4, 8))

        opt1 = ctk.CTkFrame(self, fg_color="transparent")
        opt1.pack(fill="x", padx=20)
        lbl(opt1, "Số từ mỗi ngày:", 13).pack(side="left", padx=(0, 8))
        # ⚠ CTkComboBox yêu cầu values là CHUỖI (int làm crash DropdownMenu .ljust)
        self.cb_wpd = combo(opt1, ["5", "10", "15", "20"], width=70)
        self.cb_wpd.set("10")
        self.cb_wpd.pack(side="left")

        lbl(opt1, "   Trình độ mục tiêu:", 13).pack(side="left", padx=(14, 8))
        self.cb_level = combo(opt1, LEVELS, width=330)
        self.cb_level.set(DEFAULT_LEVEL)
        self.cb_level.configure(command=lambda _c: self._update_level_info())
        self.cb_level.pack(side="left")

        self.lbl_level_info = lbl(opt1, "", 11, color=C["success"])
        self.lbl_level_info.pack(side="left", padx=(10, 0))
        self._update_level_info()

        opt2 = ctk.CTkFrame(self, fg_color="transparent")
        opt2.pack(fill="x", padx=20, pady=(8, 0))
        lbl(opt2, "Thời lượng / Lộ trình:", 13).pack(side="left", padx=(0, 8))
        self.DURATION_OPTIONS = [
            "Tự động (AI suy luận số ngày chuẩn Bản xứ C2)",
            "15 ngày (Khóa Nhập môn & Sinh tồn)",
            "30 ngày (Khóa Tiêu chuẩn - Giao tiếp cơ bản)",
            "45 ngày (Khóa Mở rộng - Tự tin giao tiếp)",
            "60 ngày (Khóa Chuyên sâu - Toàn diện)",
            "90 ngày (Khóa Nâng cao - Thành thạo)",
        ]
        self.cb_duration = combo(opt2, self.DURATION_OPTIONS, width=285)
        self.cb_duration.set(self.DURATION_OPTIONS[0])
        self.cb_duration.pack(side="left")

        self.var_force = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(opt2, text="Làm lại từ đầu (xóa khóa cũ)",
                        variable=self.var_force, fg_color=C["accent"]).pack(side="right")

        # Tùy chọn pipeline media (ảnh minh họa + audio + hội thoại)
        opt3 = ctk.CTkFrame(self, fg_color="transparent")
        opt3.pack(fill="x", padx=20, pady=(6, 0))
        self.var_media = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(opt3, text="🖼️🔊 Sinh ảnh minh họa + âm thanh + hội thoại (pipeline tự trị)",
                        variable=self.var_media, fg_color=C["accent"]).pack(side="left")
        self.var_rebuild = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(opt3, text="↻ Sinh lại nội dung (thêm IPA / khẩu hình phát âm)",
                        variable=self.var_rebuild, fg_color=C["accent"]).pack(side="left", padx=(14, 0))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(pady=10)
        self.btn_start = btn(btn_row, "▶ Tiếp tục / Bắt đầu sinh", C["success"], "#018786",
                             w=190, h=38, cmd=self._start)
        self.btn_start.pack(side="left", padx=(0, 10))

        self.btn_supplement = btn(btn_row, "🔍 Rà soát & Bổ sung", "#1e88e5", "#1565c0",
                                  w=180, h=38, cmd=self._supplement)
        self.btn_supplement.pack(side="left", padx=(0, 10))

        self.btn_stop = btn(btn_row, "⏹ Dừng", C["card2"], C["danger"], w=90, h=38,
                            cmd=lambda: self._stop_event.set())
        self.btn_stop.pack(side="left")
        self.btn_stop.configure(state="disabled")

        btn(btn_row, "⚙️ Cài đặt Model", C["card2"], C["accent"], w=145, h=38,
            cmd=lambda: ModelSettingsDialog(self)).pack(side="left", padx=(10, 0))

        # ── MỞ TRỰC TIẾP GEMINI / GROK (đường lùi an toàn, 0 chi phí) ──
        # Copy prompt vào clipboard + mở tab ⇒ người dùng tự dán & Enter.
        # KHÔNG dùng deep-link ?q= (các dịch vụ không hỗ trợ ổn định).
        self.ai_platform = ctk.StringVar(value="gemini")
        ai_row = ctk.CTkFrame(self, fg_color="transparent")
        ai_row.pack(pady=(0, 4))
        lbl(ai_row, "Tra cứu nhanh bằng AI web:", 12, color=C["muted"]).pack(
            side="left", padx=(0, 8))
        self.ai_platform_box = ctk.CTkComboBox(
            ai_row, values=["gemini", "grok", "chatgpt", "claude", "copilot",
                           "perplexity", "deepseek", "aistudio"],
            variable=self.ai_platform, width=130, height=30)
        self.ai_platform_box.pack(side="left", padx=(0, 8))
        btn(ai_row, "🔎 Mở & copy prompt", C["card2"], C["accent"], w=175, h=32,
            cmd=self._open_ai_web).pack(side="left", padx=(0, 8))
        lbl(ai_row, "ℹ️ Copy prompt → mở tab → dán & Enter (không tự động hoá để tránh vi phạm ToS)",
            11, color=C["muted"]).pack(side="left")

        self.progress = ctk.CTkProgressBar(self, progress_color=C["accent"], height=8)
        self.progress.pack(fill="x", padx=20, pady=(0, 6))
        self.progress.set(0)

        self.log_box = ctk.CTkTextbox(self, height=260, fg_color=C["card"],
                                      text_color=C["text"], font=("Consolas", 12))
        self.log_box.pack(fill="both", expand=True, padx=20, pady=(0, 15))
        self.log_box.configure(state="disabled")

        self._log("🧭 Hành trình 6 tầng bản xứ hóa: Vỡ lòng → Ghép âm → "
                  "Sơ cấp → Trung cấp → Cao cấp → Như bản xứ.")
        try:
            from ai.language_profiler import get_or_create_language_profile
            prof = get_or_create_language_profile(lang)
            self._log(f"🧠 Định danh AI: {prof.get('category_name', lang)}.")
            self._log(f"🎯 Lộ trình Bản xứ C2 khuyến nghị: {prof.get('total_days', 700)} ngày (6 Chặng chuyên sâu).")
            if prof.get("persona"):
                self._log(f"👤 Mục tiêu: {prof['persona']}.")
        except Exception:
            pass
        # Hiển thị số ngày và tiến độ Backbone trong lộ trình tích lũy
        try:
            from ai import course_db as _cdb
            _oc = _cdb.get_course(app.current_language)
            if _oc and _oc.get("days"):
                _nd = len(_oc["days"])
                _lv = _oc.get("level", "")
                _bb = _oc.get("backbone") or {}
                _bb_items = _bb.get("items") or []
                _bb_filled = len([it for it in _bb_items if it.get("filled_day") is not None])
                self._log(f"📊 Lộ trình hiện có: {_nd} ngày đã sinh (cấp độ: {_lv}).")
                if _bb_items:
                    self._log(f"🦴 Khung giáo trình Backbone: {_bb_filled}/{len(_bb_items)} chủ đề hoàn thành ({'%.0f' % (100*_bb_filled/len(_bb_items))}%).")
                self._log(f"   ✔️ Sinh tiếp sẽ bắt đầu từ Ngày {_nd + 1} — giữ nguyên toàn bộ lịch sử học.")
                self._log("   🔍 Bấm 'Rà soát & Bổ sung' để tự động kiểm tra và thêm các chặng còn thiếu.")
                self._log("   🔁 Chỉ chọn 'Làm lại từ đầu' khi muốn XÓA HOÀN TOÀN và tạo mới.")
            else:
                self._log("   Khóa học thiết kế từ gốc: Ngày 1-3 tập trung bảng chữ cái, phát âm, "
                          "sau đó nâng cao dần theo lộ trình.")
        except Exception:
            self._log("   Khóa học thiết kế từ gốc: Ngày 1-3 tập trung bảng chữ cái, phát âm, "
                      "sau đó nâng cao dần theo lộ trình.")
        self._log("   Mỗi ngày: ≥10 từ chuyên sâu · ≥10 mẫu câu · ≥10 câu thông dụng · "
                  "2-3 bài ngữ pháp · trắc nghiệm 4 loại × ≥10 câu.")
        self._log("⏱ Lưu ý: ~1-3 phút/ngày, khóa dài có thể mất nhiều phút — "
                  "bấm Dừng bất kỳ lúc nào, chạy lại sẽ tiếp tục chỗ đang dở.")
        if not n_keys:
            self._log("⚠️ Chưa thấy API key! Kiểm tra file settings.json của AskCpl.")
        # Hiển thị danh sách model đang ưu tiên
        try:
            active_models = get_active_model_list()
            self._log(f"🤖 Model ưu tiên: {' → '.join(active_models[:3])}"
                      f"{'...' if len(active_models) > 3 else ''}")
            self._log("   (Nhấn ⚙️ Cài đặt Model để thêm/tắt/sắp xếp thứ tự model)")
        except Exception:
            pass

    def _update_level_info(self):
        level = self.cb_level.get() or DEFAULT_LEVEL
        phase_idx = LEVEL_PHASES.get(level, [])
        min_d = LEVEL_MIN_DAYS.get(level, 15)
        phase_names = [JOURNEY_PHASES[i][0] for i in phase_idx if i < len(JOURNEY_PHASES)]
        if "trọn gói" in level.lower():
            from ai.course_generator import get_language_native_profile
            fsi = get_language_native_profile(self.app.current_language)
            total_d = fsi.get('total_days', 0)
            lang_lower = (self.app.current_language or "").lower()
            is_hard = any(k in lang_lower for k in ["nhật", "japanese", "japan", "nihongo",
                                                     "trung", "chinese", "mandarin", "hán",
                                                     "hàn", "korean", "hangul",
                                                     "ả rập", "arabic"])
            if total_d >= 1000 and is_hard:
                text = (f"→ {fsi['category_name']}: ~{total_d} ngày Bản xứ C2 (6 chặng) — "
                        f"⚠️ Khuyên dùng: chia thành các khóa 30/60/90 ngày")
                text_color = C["warn"]
            else:
                text = f"→ {fsi['category_name']}: ~{fsi['total_days']} ngày Bản xứ C2 (6 chặng)"
                text_color = C["success"]
        else:
            text = f"→ {', '.join(phase_names)} · tối thiểu {min_d} ngày"
            text_color = C["success"]
        self.lbl_level_info.configure(text=text, text_color=text_color)

    def _log(self, msg):
        def _append():
            self.log_box.configure(state="normal")
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.after(0, _append)

    def _open_ai_web(self):
        """Mở Gemini/Grok/... : copy prompt vào clipboard + mở tab.

        Cơ chế AN TOÀN: KHÔNG tự động gõ/click (đã có bằng chứng Google trả
        CAPTCHA /sorry/index và Grok có tos-gate khi truy cập tự động) ⇒ chỉ
        copy + mở tab, người dùng tự dán & Enter.
        """
        try:
            from ai import web_ai_urls
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không tải được module web_ai_urls: {e}", parent=self)
            return

        plat = (self.ai_platform.get() or "gemini").strip()
        lang = self.app.current_language
        # Prompt: ưu tiên từ của ngày đang học, không thì prompt tổng quát
        prompt = ""
        try:
            course = course_db.get_course(lang) or {}
            lesson = None
            for d in course.get("days", []):
                v = d.get("vocab") or []
                if v:
                    lesson = d
                    break
            if lesson:
                ws = [str(x.get("word") or "") for x in lesson["vocab"][:12] if x.get("word")]
                prompt = web_ai_urls.build_course_prompt(
                    lang, lesson.get("title") or lesson.get("topic") or "", ws)
        except Exception:
            prompt = ""
        if not prompt:
            prompt = web_ai_urls.build_lookup_prompt(
                lang, extra="Hãy cho tôi một bài học từ vựng ngắn gọn cho chủ đề này.")

        res = web_ai_urls.open_platform(plat, prompt, log_fn=self._log)
        if not res.get("ok"):
            messagebox.showerror("Không mở được", res.get("error", "Lỗi không rõ"), parent=self)
            return
        self._log(f"{res.get('label')}: đã mở tab và "
                  f"{'copy prompt' if res.get('copied') else 'KHÔNG copy được prompt'}.")
        if res.get("copied"):
            messagebox.showinfo(
                res.get("label", "AI web"),
                f"Đã mở {res.get('label')} và COPY prompt vào clipboard.\n\n"
                "Bấm Ctrl+V trong ô chat rồi Enter.\n"
                "(Không tự động gõ để tránh vi phạm điều khoản dịch vụ.)",
                parent=self)

    def _parse_target_days(self) -> int | None:
        val = self.cb_duration.get() or ""
        m = re.search(r"(\d+)\s*ngày", val)
        if m:
            return int(m.group(1))
        return None

    def _supplement(self):
        """Rà soát và tự động bổ sung chặng/chủ đề thiếu cho khóa học hiện có."""
        if self._running:
            return
        level = self.cb_level.get() or DEFAULT_LEVEL
        self._running = True
        self._stop_event.clear()
        self.btn_start.configure(state="disabled")
        self.btn_supplement.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.progress.set(0)

        def _worker():
            try:
                from ai.course_generator import audit_and_supplement_course
                res = audit_and_supplement_course(
                    self.app.current_language,
                    level=level,
                    log_fn=self._log,
                    stop_check=self._stop_event.is_set,
                )
                self.after(0, lambda: self._done(success=res.get("ok", False)))
            except GenerationStopped:
                self._log("⏹ Đã dừng rà soát theo yêu cầu.")
                self.after(0, lambda: self._done(success=False))
            except Exception as e:
                self._log(f"❌ Lỗi rà soát: {e}")
                self.after(0, lambda: self._done(success=False))

        threading.Thread(target=_worker, daemon=True).start()

    def _start(self):
        if self._running:
            return
        try:
            wpd = int(self.cb_wpd.get())
        except ValueError:
            wpd = DEFAULT_WORDS_PER_DAY
        level = self.cb_level.get() or DEFAULT_LEVEL
        target_days = self._parse_target_days()

        self._running = True
        self._stop_event.clear()
        self.btn_start.configure(state="disabled")
        self.btn_supplement.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.progress.set(0)

        def _on_day_done(day, total, lesson):
            frac = day / max(total, 1)
            self.after(0, lambda f=frac: self.progress.set(f))

        def _worker():
            try:
                if self.var_media.get():
                    # Đường pipeline tự trị: sinh content + quiz + ẢNH + AUDIO + HỘI THOẠI
                    from ai.pipeline import run_pipeline
                    res = run_pipeline(
                        self.app.current_language,
                        words_per_day=wpd,
                        level=level,
                        full=True,
                        mode=("enrich" if self.var_rebuild.get() else "media"),
                        target_days=target_days,
                        force_new=self.var_force.get(),
                        allow_degraded=True,
                        media=True,
                        workers=4,
                        log_fn=self._log,
                        stop_check=self._stop_event.is_set,
                        on_progress=lambda p: self.after(
                            0, lambda: self.progress.set(
                                max(0.0, min(1.0, p.get("pct", 0) / 100.0)))),
                    )
                    self._log(f"🏁 {res['status'].upper()}: {res['days_done']}/{res['total_days']} ngày, "
                              f"calls={res['calls']}, ảnh={res['images']}. "
                              f"DoD={res['definition_of_done']['met']}")
                    self.after(0, lambda: self._done(success=res.get("ok", False)))
                    return
                result = generate_course(
                    self.app.current_language, words_per_day=wpd,
                    force_new=self.var_force.get(),
                    log_fn=self._log,
                    on_day_done=_on_day_done,
                    stop_check=self._stop_event.is_set,
                    level=level,
                    target_days=target_days,
                )
                self._log(f"🏁 Hoàn tất: {result['generated']} ngày mới, "
                          f"{result['skipped']} bỏ qua, {result['failed']} lỗi.")
                self.after(0, lambda: self._done(success=result["generated"] > 0))
            except GenerationStopped:
                self._log("⏹ Đã dừng theo yêu cầu. Chạy lại sẽ tiếp tục từ chỗ đang dở.")
                self.after(0, lambda: self._done(success=True))
            except Exception as e:
                self._log(f"❌ Lỗi không mong muốn: {e}")
                self.after(0, lambda: self._done(success=False))

        threading.Thread(target=_worker, daemon=True).start()

    def _done(self, success):
        self._running = False
        self.btn_start.configure(state="normal")
        self.btn_supplement.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        if success:
            self.on_finished()


def _short_level_name(level_name: str, phase_name: str = "") -> str:
    """Rút gọn tên cấp độ chuẩn xác theo 6 Tầng sư phạm:
    [Vỡ lòng] -> [Ghép âm] -> [Sơ cấp] -> [Trung cấp] -> [Cao cấp] -> [Bản xứ]"""
    plow = (phase_name or "").lower()

    # 1. Ưu tiên xét theo Phase thực tế của bài học
    if "vỡ lòng" in plow or "bảng chữ" in plow or "chữ cái" in plow or "khẩu hình" in plow or "nền tảng" in plow:
        return "Vỡ lòng"
    if "ghép âm" in plow or "từ đơn" in plow or "sinh tồn" in plow or "tập đọc" in plow:
        return "Ghép âm"
    if "sơ cấp" in plow or "giao tiếp cơ bản" in plow or "đời sống" in plow:
        return "Sơ cấp"
    if "trung cấp" in plow or "công việc" in plow or "công sở" in plow or "tự tin" in plow:
        return "Trung cấp"
    if "cao cấp" in plow or "học thuật" in plow or "báo chí" in plow:
        return "Cao cấp"
    if "bản xứ" in plow or "slang" in plow or "thành ngữ" in plow:
        return "Bản xứ"

    # 2. Xét theo level_name nếu phase trống
    low = (level_name or "").lower()
    if "vỡ lòng" in low or "bảng chữ cái" in low or "người mới" in low or "bắt đầu" in low:
        return "Vỡ lòng"
    if "ghép âm" in low or "từ đơn" in low:
        return "Ghép âm"
    if "sơ cấp" in low:
        return "Sơ cấp"
    if "trung cấp" in low:
        return "Trung cấp"
    if "cao cấp" in low:
        return "Cao cấp"
    if "bản xứ" in low:
        return "Bản xứ"
    return level_name[:10] if level_name else ""


class DaySelectorDialog(ctk.CTkToplevel):
    """Cửa sổ chọn ngày siêu tốc (High-Performance Treeview), tìm kiếm tức thì và phân nhóm theo Cấp độ."""

    def __init__(self, parent, course, progress, on_select_day):
        super().__init__(parent)
        self.course = course or {}
        self.progress = progress or {}
        self.on_select_day = on_select_day
        self.title("📑 Toàn Bộ Lộ Trình Khóa Học AI")
        self.geometry("820x620")
        self.minsize(700, 480)
        self.configure(fg_color=C["bg"])
        self.transient(parent)
        self.grab_set()

        # Header tiêu đề & tổng quan
        top = ctk.CTkFrame(self, fg_color=C["sidebar"], height=54, corner_radius=0)
        top.pack(fill="x")
        top.pack_propagate(False)
        lbl(top, "📑 Toàn Bộ Lộ Trình Khóa Học AI", 16, "bold", C["accent"]).pack(side="left", padx=16)

        days_all = self.course.get("days", [])
        done_set = set(self.progress.get("completed_days", []))
        self.lbl_stats = lbl(top, f"Tổng số: {len(days_all)} ngày · Đã hoàn thành {len(done_set)}/{len(days_all)}", 12, color=C["muted"])
        self.lbl_stats.pack(side="right", padx=16)

        # Ô Tìm kiếm nhanh
        search_box = ctk.CTkFrame(self, fg_color="transparent", height=44)
        search_box.pack(fill="x", padx=16, pady=(10, 6))
        self.var_search = tk.StringVar(value="")
        self.var_search.trace_add("write", lambda *_: self._filter_tree())
        self.ent_search = ctk.CTkEntry(
            search_box, textvariable=self.var_search,
            placeholder_text="🔍 Tìm kiếm nhanh theo số ngày, chủ đề, trình độ, ngữ pháp...",
            fg_color=C["card"], text_color=C["text"], font=("Segoe UI", 13), height=36
        )
        self.ent_search.pack(side="left", fill="x", expand=True, padx=(0, 8))
        btn(search_box, "Xóa lọc", C["card2"], C["text"], w=80, h=36,
            cmd=lambda: self.var_search.set("")).pack(side="right")

        # Khung bảng Treeview siêu tốc
        table_frame = ctk.CTkFrame(self, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        style = ttk.Style()
        style.theme_use("default")
        style.configure("DayList.Treeview", background=C["card"], foreground=C["text"],
                        fieldbackground=C["card"], rowheight=32, borderwidth=0, font=("Segoe UI", 11))
        style.map('DayList.Treeview', background=[('selected', "#3700B3")], foreground=[('selected', '#FFFFFF')])
        style.configure("DayList.Treeview.Heading", background=C["card2"], foreground=C["accent"],
                        font=('Segoe UI', 11, 'bold'), borderwidth=0)

        cols = [("day", "Ngày", 80), ("level", "Trình độ", 110), ("phase", "Giai đoạn", 130),
                ("topic", "Chủ đề bài học", 350), ("status", "Trạng thái", 110)]

        self.tree = ttk.Treeview(table_frame, style="DayList.Treeview", show='headings', columns=[c[0] for c in cols])
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        for col_id, col_name, width in cols:
            self.tree.heading(col_id, text=col_name, anchor="center" if col_id in ("day", "status") else "w")
            self.tree.column(col_id, width=width, anchor="center" if col_id in ("day", "status") else "w")

        self.tree.bind("<Double-1>", lambda _e: self._on_choose_selected())
        self.tree.bind("<Return>", lambda _e: self._on_choose_selected())

        # Action bar bottom
        bottom_bar = ctk.CTkFrame(self, fg_color=C["sidebar"], height=50, corner_radius=0)
        bottom_bar.pack(fill="x")
        bottom_bar.pack_propagate(False)

        lbl(bottom_bar, "💡 Mẹo: Nhấp đúp vào dòng để vào học ngay lập tức", 12, color=C["muted"]).pack(side="left", padx=16)
        btn(bottom_bar, "Học ngày đã chọn ➔", C["success"], "#018786", w=170, h=34,
            cmd=self._on_choose_selected).pack(side="right", padx=16, pady=8)

        self._filter_tree()
        self.ent_search.focus_set()

    def _filter_tree(self):
        self.tree.delete(*self.tree.get_children())
        days = sorted(self.course.get("days", []), key=lambda d: int(d.get("day", 0)))
        if not days:
            return

        query = self.var_search.get().strip().lower()
        done_set = set(self.progress.get("completed_days", []))
        scores = self.progress.get("quiz_scores", {})
        default_lvl = self.course.get("level", "")

        for d in days:
            day_num = int(d.get("day", 0))
            topic = (d.get("topic") or d.get("title") or "—").strip()
            phase = (d.get("phase") or "").strip()
            lvl = (d.get("level") or default_lvl or "").strip()
            short_lvl = _short_level_name(lvl, phase)

            if query:
                search_text = f"ngày {day_num} {day_num} {topic} {phase} {lvl} {short_lvl}".lower()
                if query not in search_text:
                    continue

            is_done = day_num in done_set
            score = scores.get(str(day_num), {}).get("score")
            st_text = f"✅ Xong ({score}%)" if (is_done and score is not None) else ("✅ Xong" if is_done else "⏳ Chưa")

            self.tree.insert("", "end", iid=str(day_num), values=(
                f"Ngày {day_num}",
                f"[{short_lvl}]" if short_lvl else "—",
                phase or "—",
                topic,
                st_text
            ))

    def _on_choose_selected(self):
        sel = self.tree.selection()
        if not sel:
            return
        try:
            day_num = int(sel[0])
            self.on_select_day(day_num)
            self.destroy()
        except ValueError:
            pass


class ScrollableDayDropdown(ctk.CTkFrame):
    """Thanh chọn ngày tùy biến siêu tốc (Ultra-Fast C-Engine Listbox), kéo chuột mượt mà và tìm kiếm tức thì."""

    def __init__(self, parent, on_select, width=320, height=34):
        super().__init__(parent, fg_color=C["card"], border_color=C["accent"], border_width=1, corner_radius=8, width=width, height=height)
        self.pack_propagate(False)
        self.on_select = on_select
        self._current_text = "—"
        self._items = []  # list of tuples: (day_num, full_label, short_lvl, is_done)
        self._filtered_items = []
        self._popup = None

        # Text label
        self.lbl_text = ctk.CTkLabel(
            self, text="—", font=("Segoe UI", 12),
            text_color=C["text"], anchor="w", cursor="hand2"
        )
        self.lbl_text.pack(side="left", fill="both", expand=True, padx=(10, 2))

        # Arrow indicator
        self.lbl_arrow = ctk.CTkLabel(
            self, text="▾", font=("Segoe UI", 14, "bold"),
            text_color=C["accent"], width=24, cursor="hand2"
        )
        self.lbl_arrow.pack(side="right", padx=(0, 6))

        # Click handlers
        for w in (self, self.lbl_text, self.lbl_arrow):
            w.bind("<Button-1>", lambda _e: self.toggle_dropdown())
            w.bind("<Enter>", lambda _e: self.configure(border_color=C["accent2"]))
            w.bind("<Leave>", lambda _e: self.configure(border_color=C["accent"]))

    def set_items(self, items: list):
        """items: list of (day_num, full_label, short_lvl, is_done)"""
        self._items = items

    def set(self, text: str):
        self._current_text = text
        disp = text if len(text) <= 38 else text[:35] + "..."
        self.lbl_text.configure(text=disp)

    def get(self) -> str:
        return self._current_text

    def toggle_dropdown(self):
        if self._popup and self._popup.winfo_exists():
            self._close_popup()
            return
        self.open_dropdown()

    def open_dropdown(self):
        if not self._items:
            return
        if self._popup and self._popup.winfo_exists():
            self._close_popup()

        self.update_idletasks()
        rx = self.winfo_rootx()
        ry = self.winfo_rooty() + self.winfo_height() + 2
        w = max(self.winfo_width(), 420)
        h = 320

        top = self.winfo_toplevel()
        self._popup = ctk.CTkToplevel(top)
        self._popup.withdraw()
        self._popup.overrideredirect(True)
        self._popup.geometry(f"{w}x{h}+{rx}+{ry}")
        self._popup.configure(fg_color=C["card2"])

        container = ctk.CTkFrame(self._popup, fg_color=C["card"], border_color=C["accent"], border_width=1, corner_radius=8)
        container.pack(fill="both", expand=True)

        # Search bar
        search_frame = ctk.CTkFrame(container, fg_color="transparent", height=38)
        search_frame.pack(fill="x", padx=6, pady=(6, 4))
        search_frame.pack_propagate(False)

        var_filter = tk.StringVar(value="")
        ent_filter = ctk.CTkEntry(
            search_frame, textvariable=var_filter,
            placeholder_text="🔍 Gõ số ngày hoặc tên chủ đề để lọc nhanh...",
            fg_color=C["sidebar"], text_color=C["text"],
            font=("Segoe UI", 12), height=30, corner_radius=6
        )
        ent_filter.pack(fill="both", expand=True)

        # List frame with native Listbox + Scrollbar (0 lag, instant 60fps)
        list_frame = ctk.CTkFrame(container, fg_color=C["sidebar"], corner_radius=6)
        list_frame.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        sb = ttk.Scrollbar(list_frame, orient="vertical")
        sb.pack(side="right", fill="y")

        lb = tk.Listbox(
            list_frame, bg=C["sidebar"], fg=C["text"],
            selectbackground=C["accent"], selectforeground="#000000",
            activestyle="none", font=("Segoe UI", 11),
            highlightthickness=0, borderwidth=0,
            yscrollcommand=sb.set, height=10
        )
        lb.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
        sb.config(command=lb.yview)

        def _update_listbox(*_):
            lb.delete(0, "end")
            q = var_filter.get().strip().lower()
            self._filtered_items = []
            selected_idx = 0

            for item in self._items:
                day_num, full_label, short_lvl, is_done = item
                if q:
                    st = f"ngày {day_num} {day_num} {full_label} {short_lvl}".lower()
                    if q not in st:
                        continue
                self._filtered_items.append(item)
                lb.insert("end", f"  {full_label}")
                # BUG ĐÃ SỬA (L-U): so khớp SUBSTRING "Ngày 1" cũng khớp "Ngày 11"
                # ⇒ highlight sai ngày trong dropdown. Giờ: regex có ranh giới số.
                if re.search(rf"Ngày\s+{re.escape(str(day_num))}(?!\d)",
                             self._current_text):
                    selected_idx = len(self._filtered_items) - 1

            if self._filtered_items:
                lb.selection_set(selected_idx)
                lb.see(selected_idx)

        var_filter.trace_add("write", _update_listbox)
        _update_listbox()

        def _on_select_item(event=None):
            sel = lb.curselection()
            if sel and sel[0] < len(self._filtered_items):
                day_num, full_label, _short_lvl, _is_done = self._filtered_items[sel[0]]
                self._choose(day_num, full_label)

        lb.bind("<Double-Button-1>", _on_select_item)
        lb.bind("<Return>", _on_select_item)
        ent_filter.bind("<Return>", _on_select_item)
        ent_filter.bind("<Down>", lambda _e: (lb.focus_set(), lb.selection_set(0) if not lb.curselection() else None))

        def _on_focus_out(event=None):
            if self._popup and self._popup.winfo_exists():
                x, y = self._popup.winfo_pointerxy()
                px = self._popup.winfo_rootx()
                py = self._popup.winfo_rooty()
                pw = self._popup.winfo_width()
                ph = self._popup.winfo_height()
                if not (px <= x <= px + pw and py <= y <= py + ph):
                    self._close_popup()

        self._popup.bind("<FocusOut>", _on_focus_out)
        self._popup.bind("<Escape>", lambda _e: self._close_popup())
        self._popup.deiconify()
        self._popup.lift()
        ent_filter.focus_set()

    def _choose(self, day_num: int, label: str):
        self.set(label)
        self._close_popup()
        if self.on_select:
            self.on_select(day_num)

    def _close_popup(self):
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
            self._popup = None


class StudyTab(ctk.CTkFrame):
    """Tab học tập: flashcard từ vựng tự học + khóa học AI theo ngày + trắc nghiệm."""

    def __init__(self, parent, app):
        super().__init__(parent, fg_color=C["bg"])
        self.app = app
        self._cards = []
        self._card_idx = 0
        self._flipped = False
        self._course = None
        self._quiz = None
        self._building_quiz = False
        # SRS (SM-2)
        self._srs_queue = []
        self._srs_idx = 0
        self._srs_revealed = False
        self._srs_pool_cache = {}
        self._current_lesson = None
        self._build()
        # CTk chặn bind_all → bind trên cửa sổ chính (vẫn nhận phím từ mọi widget con)
        self.winfo_toplevel().bind("<KeyPress>", self._on_global_key, add="+")

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build(self):
        # ── Header hiện đại ──
        head = ctk.CTkFrame(self, fg_color=C["sidebar"], height=64, corner_radius=0)
        head.pack(fill="x"); head.pack_propagate(False)

        head_inner = ctk.CTkFrame(head, fg_color="transparent")
        head_inner.pack(fill="both", expand=True, padx=16, pady=8)

        # Left: Nguồn học
        lbl(head_inner, "Nguồn học:", 13, "bold", C["accent"]).pack(side="left", padx=(0, 8))
        self.cb_source = combo(head_inner, [SOURCE_SELF, SOURCE_AI, SOURCE_SRS], width=220)
        self.cb_source.set(SOURCE_SELF)
        self.cb_source.configure(command=lambda _c: self._on_source_change())
        self.cb_source.pack(side="left", padx=(0, 16))

        # Middle: Tìm kiếm từ vựng (trong toàn bộ khóa học)
        lbl(head_inner, "🔍 Tra cứu từ:", 13, "bold", C["muted"]).pack(side="left", padx=(16, 6))
        self.ent_search = search_entry(head_inner, placeholder="Nhập từ cần tra cứu...", width=260)
        self.ent_search.pack(side="left", padx=(0, 8))
        self.ent_search.bind("<KeyRelease>", lambda _e: self._on_search_change())
        self.ent_search.bind("<Return>", lambda _e: self._select_searched_word())

        # Right: Nút hành động
        btn(head, "🔀 Trộn thẻ", C["card2"], C["accent"], w=100, h=32,
            cmd=self._shuffle_cards).pack(side="right", padx=3)

        btn(head, "🤖 Sinh khóa học AI", C["success"], "#018786", w=150, h=32,
            cmd=self._open_generation).pack(side="right", padx=3)
        btn(head, "🗑️ Xóa khóa & tiến độ", C["card2"], C["danger"], w=150, h=32,
            cmd=self._delete_course).pack(side="right", padx=3)

        # ── Khung Flashcard (Từ vựng tự học) ──
        self.flash_frame = ctk.CTkFrame(self, fg_color="transparent")

        self.card = ctk.CTkFrame(self.flash_frame, fg_color=C["card"],
                                 corner_radius=16, border_width=1, border_color=C["accent"])
        self.card.pack(fill="both", expand=True, padx=40, pady=(25, 10))

        self.fc_counter = lbl(self.card, "0 / 0", 13, color=C["muted"])
        self.fc_counter.pack(anchor="ne", padx=15, pady=(10, 0))
        self.fc_word = lbl(self.card, "", 46, "bold", C["accent"])
        self.fc_word.pack(pady=(35, 5))
        self.fc_pron = lbl(self.card, "", 20, color=C["muted"])
        self.fc_pron.pack(pady=(0, 10))
        self.fc_back = ctk.CTkLabel(self.card, text="", justify="left", anchor="nw",
                                    wraplength=760, font=("Consolas", 16),
                                    text_color=C["text"])
        self.fc_back.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        nav = ctk.CTkFrame(self.flash_frame, fg_color="transparent")
        nav.pack(pady=(4, 18))
        btn(nav, "⬅️ Trước", C["card2"], C["accent"], w=110, h=40, cmd=self._prev_card).pack(side="left", padx=5)
        btn(nav, "🔊 Đọc", C["card2"], C["accent"], w=100, h=40, cmd=self._speak_current).pack(side="left", padx=5)
        btn(nav, "🔄 Lật thẻ", C["accent"], C["accent2"], w=130, h=40, cmd=self._flip_card).pack(side="left", padx=5)
        btn(nav, "Sau ➡️", C["card2"], C["accent"], w=110, h=40, cmd=self._next_card).pack(side="left", padx=5)
        lbl(nav, "(← → lật trang · Space lật thẻ)", 11, color=C["muted"]).pack(side="left", padx=14)

        # ── Khung Khóa học AI ──
        self.course_frame = ctk.CTkFrame(self, fg_color="transparent")

        ctop = ctk.CTkFrame(self.course_frame, fg_color="transparent", height=44)
        ctop.pack(fill="x", padx=14, pady=(8, 0))

        # Day selector section
        btn(ctop, "◀ Trước", C["card2"], C["accent"], w=68, h=32, cmd=self._prev_day).pack(side="left", padx=(0, 4))

        lbl(ctop, "Ngày:", 13, color=C["accent"]).pack(side="left", padx=(2, 2))
        self.ent_jump_day = ctk.CTkEntry(ctop, width=46, height=32, font=("Segoe UI", 12, "bold"), justify="center")
        self.ent_jump_day.pack(side="left", padx=(2, 2))
        self.ent_jump_day.bind("<Return>", lambda _e: self._on_jump_day())
        self.lbl_total_days = lbl(ctop, "/ 0", 12, color=C["muted"])
        self.lbl_total_days.pack(side="left", padx=(0, 4))
        btn(ctop, "➔", C["card2"], C["accent"], w=36, h=32, cmd=self._on_jump_day).pack(side="left", padx=(0, 6))

        self.cb_day = ScrollableDayDropdown(ctop, on_select=self._select_day_by_num, width=320, height=32)
        self.cb_day.pack(side="left")
        btn(ctop, "Sau ▶", C["card2"], C["accent"], w=68, h=32, cmd=self._next_day).pack(side="left", padx=(4, 8))
        btn(ctop, "📑 Danh sách", C["card2"], C["accent"], w=160, h=32,
            cmd=self._open_day_selector_dialog).pack(side="left", padx=(0, 8))
        btn(ctop, "📚 Dẫn chứng", C["card2"], C["accent"], w=130, h=32,
            cmd=self._run_evidence_for_day).pack(side="left", padx=(0, 8))
        self.lbl_day_status = lbl(ctop, "", 12, color=C["success"])
        self.lbl_day_status.pack(side="left", padx=4)

        # Progress bar under header
        prog_frame = ctk.CTkFrame(self.course_frame, fg_color="transparent", height=30)
        prog_frame.pack(fill="x", padx=14, pady=(4, 2))
        prog_frame.pack_propagate(False)
        self.lbl_prog_info = lbl(prog_frame, "Khóa học chưa được tải", 12, color=C["muted"])
        self.lbl_prog_info.pack(side="left", padx=8)
        self.progress_bar = ctk.CTkProgressBar(prog_frame, width=200)
        self.progress_bar.pack(side="right", padx=8)
        self.progress_bar.set(0)

        cbody = ctk.CTkFrame(self.course_frame, fg_color="transparent")
        cbody.pack(fill="both", expand=True, padx=14, pady=6)

        # Left: Lesson content
        left_panel = ctk.CTkFrame(cbody, fg_color=C["card"], corner_radius=12, border_width=1, border_color=C["border"])
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))

        left_header = ctk.CTkFrame(left_panel, fg_color=C["card2"], corner_radius=8)
        left_header.pack(fill="x", padx=12, pady=8)
        self.lbl_day_title = lbl(left_header, "Không có bài học nào", 16, "bold", C["accent"])
        self.lbl_day_title.pack(side="left", padx=12, pady=6)
        self.lbl_day_status2 = lbl(left_header, "", 11, color=C["warn"])
        self.lbl_day_status2.pack(side="right", padx=12, pady=6)

        self.lesson_text = ctk.CTkTextbox(left_panel, fg_color=C["card"], text_color=C["text"],
                                          font=("Segoe UI", 13), wrap="word", corner_radius=8)
        self.lesson_text.pack(side="left", fill="both", expand=True, padx=8, pady=(0, 8))
        self.lesson_text.configure(state="disabled")

        # Right: Quiz panel
        quiz_box = ctk.CTkFrame(cbody, fg_color=C["card"], corner_radius=12, border_width=1, border_color=C["border"], width=370)
        quiz_box.pack(side="right", fill="y", padx=(0, 0))
        quiz_box.pack_propagate(False)

        q_header = ctk.CTkFrame(quiz_box, fg_color=C["card2"], corner_radius=8)
        q_header.pack(fill="x", padx=12, pady=8)
        self.quiz_lbl_num = lbl(q_header, "Trắc nghiệm", 14, "bold", C["accent"])
        self.quiz_lbl_num.pack(anchor="w", padx=14, pady=(10, 2))
        self.quiz_lbl_day = lbl(q_header, "", 11, color=C["muted"])
        self.quiz_lbl_day.pack(anchor="w", padx=14, pady=(0, 8))

        self.quiz_question = ctk.CTkLabel(quiz_box, text="", justify="left", anchor="nw",
                                          wraplength=330, font=("Segoe UI", 14),
                                          text_color=C["text"])
        self.quiz_question.pack(anchor="w", padx=14, pady=(0, 8))
        self.quiz_var = tk.StringVar(value="")
        self.quiz_radios = []
        self.quiz_opts_frame = ctk.CTkFrame(quiz_box, fg_color="transparent")
        self.quiz_opts_frame.pack(fill="x", padx=14)
        self.quiz_feedback = ctk.CTkLabel(quiz_box, text="", justify="left", anchor="nw",
                                          wraplength=330, font=("Segoe UI", 12),
                                          text_color=C["muted"])
        self.quiz_feedback.pack(anchor="w", padx=14, pady=(8, 4))

        # ── Hàng đánh giá SRS (SM-2) — chấm mức nhớ của từ vựng đang luyện ──
        self.srs_grade_frame = ctk.CTkFrame(quiz_box, fg_color="transparent")
        self.srs_grade_frame.pack(fill="x", padx=14, pady=(6, 2))
        self.lbl_srs_grade = lbl(self.srs_grade_frame, "", 11, color=C["muted"])
        self.lbl_srs_grade.pack(anchor="w", pady=(0, 3))
        self.srs_grade_btns_q = {}
        grow = ctk.CTkFrame(self.srs_grade_frame, fg_color="transparent")
        grow.pack(fill="x")
        for gname, glabel, gcolor, ghov in SRS_GRADE_STYLE:
            gb = btn(grow, glabel, gcolor, ghov, w=78, h=30,
                     cmd=(lambda g=gname: self._grade_current_word(g)))
            gb.pack(side="left", padx=2)
            gb.configure(state="disabled")
            self.srs_grade_btns_q[gname] = gb

        qbtn_row = ctk.CTkFrame(quiz_box, fg_color="transparent")
        qbtn_row.pack(side="bottom", pady=12)
        self.btn_confirm = btn(qbtn_row, "✅ Chốt đáp án", C["success"], "#018786",
                                w=140, h=36, cmd=self._confirm_answer)
        self.btn_confirm.pack(side="left", padx=4)
        self.btn_next_q = btn(qbtn_row, "Câu tiếp ➡️", C["card2"], C["accent"],
                              w=120, h=36, cmd=self._next_question)
        self.btn_next_q.pack(side="left", padx=4)
        self.btn_next_q.configure(state="disabled")

        # ── Khung Ôn tập SRS (SM-2) ────────────────────────────────────────────
        self.srs_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._build_srs()

        # ── Thanh trạng thái dưới cùng ──
        bottom = ctk.CTkFrame(self, fg_color=C["sidebar"], height=34, corner_radius=0)
        bottom.pack(fill="x"); bottom.pack_propagate(False)
        self.lbl_bottom = lbl(bottom, "", 11, color=C["muted"])
        self.lbl_bottom.pack(side="left", padx=14, pady=7)

        self._on_source_change(initial=True)

    # ── Tìm kiếm từ vựng ─────────────────────────────────────────────────────
    def _on_search_change(self):
        """Xử lý khi người dùng gõ tìm kiếm từ."""
        query = self.ent_search.get().strip()
        if not query:
            self._clear_search_results()
            return
        self._search_words(query)

    def _search_words(self, query: str):
        """Tìm kiếm từ vựng trong toàn bộ dữ liệu (tự học + khóa học AI)."""
        try:
            # Tìm trong database từ vựng tự học
            from database.database import search_vocab
            results = search_vocab(self.app.current_language, query)
        except Exception:
            results = []

        # Tìm trong khóa học AI
        try:
            course = course_db.get_course(self.app.current_language, apply_v4=False, persist=False) or {}
            for d in course.get("days", []):
                for v in d.get("vocab", []):
                    if isinstance(v, dict):
                        w = str(v.get("word") or "")
                        if query.lower() in w.lower() or query.lower() in str(v.get("meaning_vi") or "").lower():
                            results.append({
                                "word": w,
                                "pronunciation": v.get("pronunciation", ""),
                                "meaning_vi": v.get("meaning_vi", ""),
                                "part_of_speech": v.get("part_of_speech", ""),
                                "source": f"Ngày {d.get('day', 0)}",
                                "example": v.get("example_sentence", ""),
                                "example_meaning": v.get("example_meaning_vi", ""),
                            })
        except Exception:
            pass

        self._display_search_results(results)

    def _display_search_results(self, results: list):
        """Hiển thị kết quả tìm kiếm trong một popup."""
        self._clear_search_results()

        if not results:
            self._show_search_empty()
            return

        # Tạo popup hiển thị kết quả
        self._search_popup = ctk.CTkToplevel(self)
        self._search_popup.title("Kết quả tra cứu từ")
        self._search_popup.geometry("500x400")
        self._search_popup.configure(fg_color=C["bg"])
        self._search_popup.transient(self.winfo_toplevel())
        self._search_popup.grab_set()

        # Header
        hdr = ctk.CTkFrame(self._search_popup, fg_color=C["sidebar"], height=44, corner_radius=0)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        lbl(hdr, f"Kết quả: {len(results)} từ", 14, "bold", C["accent"]).pack(side="left", padx=16, pady=10)
        btn(hdr, "Đóng", C["card2"], C["accent"], w=70, h=28, cmd=self._search_popup.destroy).pack(side="right", padx=12, pady=8)

        # Scrollable list
        list_frame = ctk.CTkScrollableFrame(self._search_popup, fg_color=C["card"], corner_radius=8)
        list_frame.pack(fill="both", expand=True, padx=12, pady=10)

        for item in results[:50]:  # Giới hạn 50 kết quả
            item_frame = ctk.CTkFrame(list_frame, fg_color=C["card2"], corner_radius=6)
            item_frame.pack(fill="x", padx=8, pady=4)

            word_lbl = lbl(item_frame, item["word"], 15, "bold", C["text"])
            word_lbl.pack(anchor="w", padx=12, pady=(8, 0))

            pron_lbl = lbl(item_frame, item.get("pronunciation", ""), 12, color=C["muted"])
            pron_lbl.pack(anchor="w", padx=12, pady=(0, 2))

            mean_lbl = lbl(item_frame, item.get("meaning_vi", ""), 13, color=C["success"])
            mean_lbl.pack(anchor="w", padx=12, pady=(0, 2))

            source_lbl = lbl(item_frame, item.get("source", ""), 10, color=C["muted"])
            source_lbl.pack(anchor="w", padx=12, pady=(0, 8))

            # Nút chọn từ này để học
            btn(item_frame, "📖 Chọn", C["accent"], C["accent2"], w=70, h=26,
                cmd=lambda w=item["word"]: self._select_searched_word(w)).pack(side="right", padx=8, pady=4)

    def _clear_search_results(self):
        """Đóng popup tìm kiếm nếu có."""
        if hasattr(self, '_search_popup') and self._search_popup and self._search_popup.winfo_exists():
            self._search_popup.destroy()
            self._search_popup = None

    def _show_search_empty(self):
        """Hiển thị thông báo không tìm thấy."""
        self._search_popup = ctk.CTkToplevel(self)
        self._search_popup.title("Kết quả tra cứu từ")
        self._search_popup.geometry("400x200")
        self._search_popup.configure(fg_color=C["bg"])
        self._search_popup.transient(self.winfo_toplevel())
        self._search_popup.grab_set()

        hdr = ctk.CTkFrame(self._search_popup, fg_color=C["sidebar"], height=44, corner_radius=0)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        lbl(hdr, "Kết quả tra cứu", 14, "bold", C["accent"]).pack(side="left", padx=16, pady=10)
        btn(hdr, "Đóng", C["card2"], C["accent"], w=70, h=28, cmd=self._search_popup.destroy).pack(side="right", padx=12, pady=8)

        body = ctk.CTkFrame(self._search_popup, fg_color=C["card"], corner_radius=8)
        body.pack(fill="both", expand=True, padx=12, pady=10)
        lbl(body, "Không tìm thấy từ nào khớp", 14, color=C["muted"]).pack(expand=True)

    def _select_searched_word(self, word: str = None):
        """Chọn một từ từ kết quả tìm kiếm để xem chi tiết."""
        if not word:
            # Lấy từ hiện đang nhập trong ô tìm kiếm
            word = self.ent_search.get().strip()
        if not word:
            return

        self._clear_search_results()

        # Tìm trong khóa học AI
        try:
            course = course_db.get_course(self.app.current_language, apply_v4=False, persist=False) or {}
            for d in course.get("days", []):
                for v in d.get("vocab", []):
                    if isinstance(v, dict) and v.get("word") == word:
                        # Chuyển đến ngày chứa từ này
                        day_num = d.get("day", 0)
                        self.cb_day.set(f"Ngày {day_num}")
                        self._select_day_by_num(day_num)
                        return
        except Exception:
            pass

        # Nếu không tìm thấy trong khóa học AI, hiển thị thông báo chi tiết từ
        self._show_word_detail(word)

    def _show_word_detail(self, word: str):
        """Hiển thị chi tiết một từ vựng."""
        self._clear_search_results()

        detail_popup = ctk.CTkToplevel(self)
        detail_popup.title(f"Chi tiết: {word}")
        detail_popup.geometry("500x400")
        detail_popup.configure(fg_color=C["bg"])
        detail_popup.transient(self.winfo_toplevel())
        detail_popup.grab_set()

        hdr = ctk.CTkFrame(detail_popup, fg_color=C["sidebar"], height=44, corner_radius=0)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        lbl(hdr, word, 16, "bold", C["accent"]).pack(side="left", padx=16, pady=10)
        btn(hdr, "Đóng", C["card2"], C["accent"], w=70, h=28, cmd=detail_popup.destroy).pack(side="right", padx=12, pady=8)

        body = ctk.CTkScrollableFrame(detail_popup, fg_color=C["card"], corner_radius=8)
        body.pack(fill="both", expand=True, padx=12, pady=10)

        # Tìm thông tin từ
        found_word = None
        try:
            course = course_db.get_course(self.app.current_language, apply_v4=False, persist=False) or {}
            for d in course.get("days", []):
                for v in d.get("vocab", []):
                    if isinstance(v, dict) and v.get("word") == word:
                        found_word = v
                        found_day = d.get("day", 0)
                        break
                if found_word:
                    break
        except Exception:
            pass

        if found_word:
            lbl(body, "Phát âm:", 12, "bold", C["muted"]).pack(anchor="w", padx=12, pady=(10, 0))
            lbl(body, found_word.get("pronunciation", ""), 14, color=C["text"]).pack(anchor="w", padx=12, pady=(0, 8))

            lbl(body, "Nghĩa:", 12, "bold", C["muted"]).pack(anchor="w", padx=12, pady=(0, 0))
            lbl(body, found_word.get("meaning_vi", ""), 14, color=C["success"]).pack(anchor="w", padx=12, pady=(0, 8))

            if found_word.get("ipa"):
                lbl(body, "IPA:", 12, "bold", C["muted"]).pack(anchor="w", padx=12, pady=(8, 0))
                lbl(body, found_word["ipa"], 13, color=C["warn"]).pack(anchor="w", padx=12, pady=(0, 8))

            if found_word.get("example_sentence"):
                lbl(body, "Câu mẫu:", 12, "bold", C["muted"]).pack(anchor="w", padx=12, pady=(8, 0))
                lbl(body, found_word["example_sentence"], 13, color=C["text2"]).pack(anchor="w", padx=12, pady=(0, 2))
                lbl(body, found_word.get("example_meaning_vi", ""), 12, color=C["muted"]).pack(anchor="w", padx=12, pady=(0, 8))

            lbl(body, f"Ngày: {found_day}", 11, color=C["muted"]).pack(anchor="w", padx=12, pady=(8, 0))
        else:
            lbl(body, "Không tìm thấy chi tiết từ này trong khóa học hiện tại.", 13, color=C["muted"]).pack(expand=True)

        btn(body, "Đóng", C["card2"], C["accent"], w=100, h=32, cmd=detail_popup.destroy).pack(pady=12)

    # ── Khung Ôn tập SRS (SM-2) ────────────────────────────────────────────
    def _build_srs(self):
        top = ctk.CTkFrame(self.srs_frame, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(8, 0))
        self.lbl_srs_stats = lbl(top, "", 13, color=C["accent"])
        self.lbl_srs_stats.pack(side="left", padx=6)
        btn(top, "▶ Ôn tập", C["success"], "#018786", w=110, h=32,
            cmd=self._srs_start).pack(side="right", padx=3)
        btn(top, "⏭ Bỏ qua", C["card2"], C["accent"], w=96, h=32,
            cmd=self._srs_skip).pack(side="right", padx=3)
        btn(top, "↻ Ôn lại từ đầu", C["card2"], C["accent"], w=140, h=32,
            cmd=self._srs_restart).pack(side="right", padx=3)
        btn(top, "🗑️ Xoá tiến độ ôn", C["card2"], C["danger"], w=150, h=32,
            cmd=self._srs_clear).pack(side="right", padx=3)

        self.srs_card = ctk.CTkFrame(self.srs_frame, fg_color=C["card"],
                                     corner_radius=16, border_width=1,
                                     border_color=C["accent"])
        self.srs_card.pack(fill="both", expand=True, padx=40, pady=18)
        self.srs_counter = lbl(self.srs_card, "0 / 0", 13, color=C["muted"])
        self.srs_counter.pack(anchor="ne", padx=15, pady=(10, 0))
        self.srs_word = lbl(self.srs_card, "", 44, "bold", C["accent"])
        self.srs_word.pack(pady=(26, 4))
        self.srs_pron = lbl(self.srs_card, "", 18, color=C["muted"])
        self.srs_pron.pack(pady=(0, 6))
        self.srs_mean = ctk.CTkLabel(self.srs_card, text="", justify="center",
                                     wraplength=720, font=("Segoe UI", 16),
                                     text_color=C["text"])
        self.srs_mean.pack(pady=(0, 6))
        self.srs_meta = lbl(self.srs_card, "", 12, color=C["muted"])
        self.srs_meta.pack(pady=(0, 6))
        btn(self.srs_card, "🔄 Xem nghĩa / Ẩn", C["card2"], C["accent"],
            w=190, h=36, cmd=self._srs_flip).pack(pady=(0, 12))

        grow = ctk.CTkFrame(self.srs_frame, fg_color="transparent")
        grow.pack(fill="x", padx=40, pady=(0, 18))
        self.srs_grade_btns = {}
        for gname, glabel, gcolor, ghov in SRS_GRADE_STYLE:
            gb = btn(grow, glabel, gcolor, ghov, w=160, h=44,
                     cmd=(lambda g=gname: self._srs_grade(g)))
            gb.pack(side="left", padx=5)
            self.srs_grade_btns[gname] = gb

    def _srs_pool(self):
        """{từ: {meaning_vi, pronunciation, ipa}} — gộp từ vựng tự học + khóa học AI."""
        pool = {}
        for v in self._cards or []:
            if not isinstance(v, dict):
                continue
            w = str(v.get("word") or "").strip()
            if not w:
                continue
            pool[w] = {
                "meaning_vi": v.get("meaning") or v.get("meaning_vi") or "",
                "pronunciation": v.get("pronunciation") or "",
                "ipa": v.get("ipa") or "",
            }
        for w, info in (self._srs_pool_cache or {}).items():
            pool.setdefault(w, dict(info))
        return pool

    def _srs_load_course_bg(self):
        """Nạp từ vựng khóa học AI ở luồng nền (không block UI)."""
        lang = self.app.current_language

        def _work():
            pool = {}
            try:
                course = course_db.get_course(lang, apply_v4=False, persist=False) or {}
                for d in course.get("days") or []:
                    for v in d.get("vocab") or []:
                        if not isinstance(v, dict):
                            continue
                        w = str(v.get("word") or "").strip()
                        if not w:
                            continue
                        pool.setdefault(w, {
                            "meaning_vi": v.get("meaning_vi") or "",
                            "pronunciation": v.get("pronunciation") or "",
                            "ipa": v.get("ipa") or "",
                        })
            except Exception:
                pool = {}

            def _done():
                self._srs_pool_cache = pool
                self.refresh_srs_stats()
                if self._srs_queue:
                    self._srs_show()
            try:
                self.after(0, _done)
            except Exception:
                pass

        threading.Thread(target=_work, daemon=True).start()

    def refresh_srs_stats(self):
        """Cập nhật dòng thống kê SRS (đến hạn / streak / đã thuộc)."""
        try:
            st = review_store.stats(self.app.current_language)
        except Exception:
            return
        pool_size = len(self._srs_pool())
        self.lbl_srs_stats.configure(
            text=(f"📊 Đến hạn: {st.get('due_today', 0)} · 🔁 Streak: "
                  f"{st.get('streak', 0)} ngày (kỷ lục {st.get('longest_streak', 0)}) · "
                  f"🏆 Đã thuộc: {st.get('mastered', 0)}/{st.get('total', 0)} · "
                  f"📈 ease TB: {st.get('avg_ease', 0)}"))

    def _srs_start(self):
        lang = self.app.current_language
        pool = self._srs_pool()
        if not pool:
            self.lbl_srs_stats.configure(
                text="⚠ Chưa có từ vựng nào để ôn. Thêm từ ở tab Danh Sách Từ Vựng "
                     "hoặc mở khóa học AI.")
            return
        try:
            review_store.sync_from_vocab(
                lang, list(pool.keys()),
                {w: (info.get("meaning_vi") or "") for w, info in pool.items()})
            queue = review_store.due_queue(lang, limit=60)
        except Exception as e:
            messagebox.showerror("Lỗi ôn tập", f"Không tải được hàng đợi ôn tập:\n{e}",
                                 parent=self)
            return
        if not queue:
            self.lbl_srs_stats.configure(
                text="✅ Không có từ nào đến hạn lúc này. Hẹn ôn lại sau nhé!")
            self.srs_word.configure(text="🎉")
            self.srs_mean.configure(text="Chưa có từ đến hạn. Bấm ▶ Ôn tập sau nhé.")
            self.srs_pron.configure(text="")
            self.srs_meta.configure(text="")
            self._srs_set_buttons(False)
            return
        self._srs_queue = [q["key"] for q in queue]
        self._srs_idx = 0
        self._srs_revealed = False
        self._srs_show()
        self.refresh_srs_stats()

    def _srs_set_buttons(self, enabled: bool):
        for b in (self.srs_grade_btns or {}).values():
            try:
                b.configure(state="normal" if enabled else "disabled")
            except Exception:
                pass

    def _srs_show(self):
        lang = self.app.current_language
        if not self._srs_queue or self._srs_idx >= len(self._srs_queue):
            self.srs_counter.configure(text=f"{len(self._srs_queue)} / {len(self._srs_queue)}")
            self.srs_word.configure(text="🎉 Xong rồi!")
            self.srs_mean.configure(
                text="Bạn đã ôn hết hàng đợi hôm nay. Quay lại sau khi tới hạn nhé!")
            self.srs_pron.configure(text="")
            self.srs_meta.configure(text="")
            self._srs_set_buttons(False)
            return
        word = self._srs_queue[self._srs_idx]
        info = self._srs_pool().get(word) or {}
        st = review_store.get_state(lang, word)
        self.srs_counter.configure(text=f"{self._srs_idx + 1} / {len(self._srs_queue)}")
        self.srs_word.configure(text=word)
        pron = str(info.get("pronunciation") or "")
        ipa = str(info.get("ipa") or "")
        self.srs_pron.configure(
            text=(f"/{pron}/" if pron else "")
                 + (f"    🔊 {ipa}" if ipa and ipa != pron else ""))
        self.srs_mean.configure(
            text=(info.get("meaning_vi") or "—") if self._srs_revealed else "••••••  (bấm Xem nghĩa)")
        lv = mastery_level(st)
        try:
            from datetime import datetime as _dt
            due_txt = _dt.fromtimestamp(float(st.get("due") or 0)).strftime("%d/%m %H:%M")
        except Exception:
            due_txt = "—"
        self.srs_meta.configure(
            text=(f"{SRS_STATE_LABEL.get(lv, lv)} · hẹn ôn {due_txt} · "
                  f"ease {float(st.get('ease') or 2.5):.2f} · "
                  f"đã ôn {int(st.get('reps') or 0)} lần"))
        self._srs_update_previews(word)
        self._srs_set_buttons(True)

    def _srs_update_previews(self, word):
        """Ghi lên nút phỏng đoán khoảng cách lần ôn kế tiếp (SM-2)."""
        try:
            from ai.srs import review as _review
            st = review_store.get_state(self.app.current_language, word)
            for gname, glabel, _c, _h in SRS_GRADE_STYLE:
                _new, info = _review(st, gname)
                days = info.get("next_review_in_days", 0)
                if days < 1:
                    txt = f"{glabel}\n({int(round(days * 1440))} phút)"
                else:
                    txt = f"{glabel}\n({days:g} ngày)"
                try:
                    self.srs_grade_btns[gname].configure(text=txt)
                except Exception:
                    pass
        except Exception:
            pass

    def _srs_grade(self, grade):
        if not self._srs_queue or self._srs_idx >= len(self._srs_queue):
            return
        lang = self.app.current_language
        word = self._srs_queue[self._srs_idx]
        info = self._srs_pool().get(word) or {}
        try:
            _st, rinfo = review_store.record_review(
                lang, word, grade,
                extra={"meaning_vi": info.get("meaning_vi") or ""})
        except Exception as e:
            messagebox.showerror("Lỗi ôn tập", f"Không lưu được lần ôn:\n{e}", parent=self)
            return
        nxt = rinfo.get("next_review_in_days", 0)
        when = (f"{int(round(nxt * 1440))} phút" if nxt < 1 else f"{nxt:g} ngày")
        self.srs_meta.configure(
            text=f"✅ {rinfo.get('label', '')} · lần ôn kế tiếp sau {when}")
        self._srs_idx += 1
        self._srs_revealed = False
        self._srs_show()
        self.refresh_srs_stats()

    def _srs_skip(self):
        if not self._srs_queue or self._srs_idx >= len(self._srs_queue):
            return
        self._srs_idx += 1
        self._srs_revealed = False
        self._srs_show()

    def _srs_flip(self):
        self._srs_revealed = not self._srs_revealed
        self._srs_show()

    def _srs_restart(self):
        lang = self.app.current_language
        if not messagebox.askyesno(
                "Ôn lại từ đầu",
                f"Xoá toàn bộ tiến độ ôn tập của '{lang}' và bắt đầu lại?",
                parent=self):
            return
        try:
            review_store.reset(lang)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)
            return
        self._srs_queue = []
        self._srs_idx = 0
        self.refresh_srs_stats()
        self._srs_start()

    def _srs_clear(self):
        lang = self.app.current_language
        if not messagebox.askyesno(
                "Xoá tiến độ ôn",
                f"Xoá toàn bộ lịch ôn tập (SM-2) của '{lang}'?",
                parent=self):
            return
        try:
            review_store.reset(lang)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e), parent=self)
            return
        self._srs_queue = []
        self._srs_idx = 0
        self.srs_word.configure(text="")
        self.srs_mean.configure(text="")
        self.srs_pron.configure(text="")
        self.srs_meta.configure(text="")
        self.srs_counter.configure(text="0 / 0")
        self._srs_set_buttons(False)
        self.refresh_srs_stats()

    # ── Điều hướng chung ─────────────────────────────────────────────────────
    def refresh_language(self):
        """Gọi khi đổi ngôn ngữ ở tab khác."""
        self._cards = list(get_all_vocab(self.app.current_language))
        self._card_idx = 0
        self._flipped = False
        self._render_card()
        self._reload_course()
        self._srs_pool_cache = {}
        self.refresh_srs_stats()

    def _on_source_change(self, initial=False):
        src = self.cb_source.get()
        print(f"[DEBUG] _on_source_change: src='{src}'")
        if not initial:
            self._cards = list(get_all_vocab(self.app.current_language))
            self._card_idx = 0
            self._flipped = False
        if src == SOURCE_AI:
            self.flash_frame.pack_forget()
            self.course_frame.pack(fill="both", expand=True)
            self._reload_course()
        elif src == SOURCE_SRS:
            self.flash_frame.pack_forget()
            self.course_frame.pack_forget()
            self.srs_frame.pack(fill="both", expand=True)
            self.refresh_srs_stats()
            self._srs_load_course_bg()
        else:
            self.course_frame.pack_forget()
            self.srs_frame.pack_forget()
            self.flash_frame.pack(fill="both", expand=True)
            self._render_card()

    # ── Tìm kiếm từ vựng ─────────────────────────────────────────────────────
    def _on_search_change(self):
        """Xử lý khi người dùng gõ tìm kiếm từ."""
        query = self.ent_search.get().strip()
        if not query:
            self._clear_search_results()
            return
        self._search_words(query)

    def _search_words(self, query: str):
        """Tìm kiếm từ vựng trong toàn bộ dữ liệu (tự học + khóa học AI)."""
        try:
            from database.database import search_vocab
            results = search_vocab(self.app.current_language, query)
        except Exception:
            results = []

        # Tìm trong khóa học AI
        try:
            course = course_db.get_course(self.app.current_language, apply_v4=False, persist=False) or {}
            for d in course.get("days", []):
                for v in d.get("vocab", []):
                    if isinstance(v, dict):
                        w = str(v.get("word") or "")
                        if query.lower() in w.lower() or query.lower() in str(v.get("meaning_vi") or "").lower():
                            results.append({
                                "word": w,
                                "pronunciation": v.get("pronunciation", ""),
                                "meaning_vi": v.get("meaning_vi", ""),
                                "part_of_speech": v.get("part_of_speech", ""),
                                "source": f"Ngày {d.get('day', 0)}",
                                "example": v.get("example_sentence", ""),
                                "example_meaning": v.get("example_meaning_vi", ""),
                            })
        except Exception:
            pass

        self._display_search_results(results)

    def _display_search_results(self, results: list):
        """Hiển thị kết quả tìm kiếm trong một popup."""
        self._clear_search_results()

        if not results:
            self._show_search_empty()
            return

        self._search_popup = ctk.CTkToplevel(self)
        self._search_popup.title("Kết quả tra cứu từ")
        self._search_popup.geometry("520x420")
        self._search_popup.configure(fg_color=C["bg"])
        self._search_popup.transient(self.winfo_toplevel())
        self._search_popup.grab_set()

        hdr = ctk.CTkFrame(self._search_popup, fg_color=C["sidebar"], height=44, corner_radius=0)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        lbl(hdr, f"Kết quả: {len(results)} từ", 14, "bold", C["accent"]).pack(side="left", padx=16, pady=10)
        btn(hdr, "Đóng", C["card2"], C["accent"], w=70, h=28, cmd=self._search_popup.destroy).pack(side="right", padx=12, pady=8)

        list_frame = ctk.CTkScrollableFrame(self._search_popup, fg_color=C["card"], corner_radius=8)
        list_frame.pack(fill="both", expand=True, padx=12, pady=10)

        for item in results[:50]:
            item_frame = ctk.CTkFrame(list_frame, fg_color=C["card2"], corner_radius=6)
            item_frame.pack(fill="x", padx=8, pady=4)

            word_lbl = lbl(item_frame, item["word"], 15, "bold", C["text"])
            word_lbl.pack(anchor="w", padx=12, pady=(8, 0))

            pron_lbl = lbl(item_frame, item.get("pronunciation", ""), 12, color=C["muted"])
            pron_lbl.pack(anchor="w", padx=12, pady=(0, 2))

            mean_lbl = lbl(item_frame, item.get("meaning_vi", ""), 13, color=C["success"])
            mean_lbl.pack(anchor="w", padx=12, pady=(0, 2))

            source_lbl = lbl(item_frame, item.get("source", ""), 10, color=C["muted"])
            source_lbl.pack(anchor="w", padx=12, pady=(0, 8))

            btn(item_frame, "📖 Chọn", C["accent"], C["accent2"], w=70, h=26,
                cmd=lambda w=item["word"]: self._select_searched_word(w)).pack(side="right", padx=8, pady=4)
            btn(item_frame, "➕ Ôn tập", C["success"], "#018786", w=70, h=26,
                cmd=lambda w=item["word"]: self._add_to_review(w)).pack(side="right", padx=4, pady=4)

    def _clear_search_results(self):
        """Đóng popup tìm kiếm nếu có."""
        if hasattr(self, '_search_popup') and self._search_popup and self._search_popup.winfo_exists():
            self._search_popup.destroy()
            self._search_popup = None

    def _show_search_empty(self):
        """Hiển thị thông báo không tìm thấy."""
        self._search_popup = ctk.CTkToplevel(self)
        self._search_popup.title("Kết quả tra cứu từ")
        self._search_popup.geometry("400x200")
        self._search_popup.configure(fg_color=C["bg"])
        self._search_popup.transient(self.winfo_toplevel())
        self._search_popup.grab_set()

        hdr = ctk.CTkFrame(self._search_popup, fg_color=C["sidebar"], height=44, corner_radius=0)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        lbl(hdr, "Kết quả tra cứu", 14, "bold", C["accent"]).pack(side="left", padx=16, pady=10)
        btn(hdr, "Đóng", C["card2"], C["accent"], w=70, h=28, cmd=self._search_popup.destroy).pack(side="right", padx=12, pady=8)

        body = ctk.CTkFrame(self._search_popup, fg_color=C["card"], corner_radius=8)
        body.pack(fill="both", expand=True, padx=12, pady=10)
        lbl(body, "Không tìm thấy từ nào khớp", 14, color=C["muted"]).pack(expand=True)

    def _select_searched_word(self, word: str = None):
        """Chọn một từ từ kết quả tìm kiếm để xem chi tiết."""
        if not word:
            word = self.ent_search.get().strip()
        if not word:
            return

        self._clear_search_results()

        try:
            course = course_db.get_course(self.app.current_language, apply_v4=False, persist=False) or {}
            for d in course.get("days", []):
                for v in d.get("vocab", []):
                    if isinstance(v, dict) and v.get("word") == word:
                        day_num = d.get("day", 0)
                        self.cb_day.set(f"Ngày {day_num}")
                        self._select_day_by_num(day_num)
                        self._switch_to_ai_source()
                        return
        except Exception:
            pass

        self._show_word_detail(word)

    def _switch_to_ai_source(self):
        """Chuyển sang tab Khóa học AI."""
        self.cb_source.set(SOURCE_AI)
        self._on_source_change()

    def _show_word_detail(self, word: str):
        """Hiển thị chi tiết một từ vựng."""
        self._clear_search_results()

        detail_popup = ctk.CTkToplevel(self)
        detail_popup.title(f"Chi tiết: {word}")
        detail_popup.geometry("500x400")
        detail_popup.configure(fg_color=C["bg"])
        detail_popup.transient(self.winfo_toplevel())
        detail_popup.grab_set()

        hdr = ctk.CTkFrame(detail_popup, fg_color=C["sidebar"], height=44, corner_radius=0)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        lbl(hdr, word, 16, "bold", C["accent"]).pack(side="left", padx=16, pady=10)
        btn(hdr, "Đóng", C["card2"], C["accent"], w=70, h=28, cmd=detail_popup.destroy).pack(side="right", padx=12, pady=8)

        body = ctk.CTkScrollableFrame(detail_popup, fg_color=C["card"], corner_radius=8)
        body.pack(fill="both", expand=True, padx=12, pady=10)

        found_word = None
        try:
            course = course_db.get_course(self.app.current_language, apply_v4=False, persist=False) or {}
            for d in course.get("days", []):
                for v in d.get("vocab", []):
                    if isinstance(v, dict) and v.get("word") == word:
                        found_word = v
                        found_day = d.get("day", 0)
                        break
                if found_word:
                    break
        except Exception:
            pass

        if found_word:
            lbl(body, "Phát âm:", 12, "bold", C["muted"]).pack(anchor="w", padx=12, pady=(10, 0))
            lbl(body, found_word.get("pronunciation", ""), 14, color=C["text"]).pack(anchor="w", padx=12, pady=(0, 8))

            lbl(body, "Nghĩa:", 12, "bold", C["muted"]).pack(anchor="w", padx=12, pady=(0, 0))
            lbl(body, found_word.get("meaning_vi", ""), 14, color=C["success"]).pack(anchor="w", padx=12, pady=(0, 8))

            if found_word.get("ipa"):
                lbl(body, "IPA:", 12, "bold", C["muted"]).pack(anchor="w", padx=12, pady=(8, 0))
                lbl(body, found_word["ipa"], 13, color=C["warn"]).pack(anchor="w", padx=12, pady=(0, 8))

            if found_word.get("example_sentence"):
                lbl(body, "Câu mẫu:", 12, "bold", C["muted"]).pack(anchor="w", padx=12, pady=(8, 0))
                lbl(body, found_word["example_sentence"], 13, color=C["text2"]).pack(anchor="w", padx=12, pady=(0, 2))
                lbl(body, found_word.get("example_meaning_vi", ""), 12, color=C["muted"]).pack(anchor="w", padx=12, pady=(0, 8))

            lbl(body, f"Ngày: {found_day}", 11, color=C["muted"]).pack(anchor="w", padx=12, pady=(8, 0))
        else:
            lbl(body, "Không tìm thấy chi tiết từ này trong khóa học hiện tại.", 13, color=C["muted"]).pack(expand=True)

        btn_row = ctk.CTkFrame(body, fg_color="transparent")
        btn_row.pack(pady=12)
        btn(btn_row, "➕ Thêm vào ôn tập", C["success"], "#018786", w=140, h=32,
            cmd=lambda: self._add_to_review(word)).pack(side="left", padx=5)
        btn(btn_row, "Đóng", C["card2"], C["accent"], w=80, h=32,
            cmd=detail_popup.destroy).pack(side="left", padx=5)

    def _add_to_review(self, word: str):
        """Thêm từ vào danh sách ôn tập SM-2."""
        try:
            from database.review_store import sync_from_vocab, due_queue
            lang = self.app.current_language
            meaning = ""
            try:
                course = course_db.get_course(lang, apply_v4=False, persist=False) or {}
                for d in course.get("days", []):
                    for v in d.get("vocab", []):
                        if isinstance(v, dict) and v.get("word") == word:
                            meaning = v.get("meaning_vi", "")
                            break
                    if meaning:
                        break
            except Exception:
                pass

            sync_from_vocab(lang, [word], {word: meaning})
            queue = due_queue(lang, limit=1)
            print(f"[DEBUG] Đã thêm từ '{word}' vào ôn tập. Queue: {len(queue)}")
            self.lbl_bottom.configure(text=f"✅ Đã thêm '{word}' vào danh sách ôn tập.", text_color=C["success"])
            self.after(3000, lambda: self.lbl_bottom.configure(text="", text_color=C["muted"]))
        except Exception as e:
            print(f"[DEBUG] Lỗi thêm vào ôn tập: {e}")
            self.lbl_bottom.configure(text=f"❌ Lỗi thêm vào ôn tập: {e}", text_color=C["danger"])
            self.after(3000, lambda: self.lbl_bottom.configure(text="", text_color=C["muted"]))

    # ── Flashcard: Từ vựng tự học ────────────────────────────────────────────
    def _render_card(self):
        if not self._cards:
            self.fc_word.configure(text="Chưa có từ vựng")
            self.fc_pron.configure(text="")
            self.fc_back.configure(text="Hãy thêm từ vựng ở tab Danh Sách Từ Vựng.")
            self.fc_counter.configure(text="0 / 0")
            return
        self._card_idx %= len(self._cards)
        v = self._cards[self._card_idx]
        if not self._flipped:
            self.fc_word.configure(text=str(v.get("word") or ""))
            self.fc_pron.configure(text=f"/{v.get('pronunciation')}/" if v.get("pronunciation") else "")
            self.fc_back.configure(text="")
        else:
            parts = [f"📌 Nghĩa: {v.get('meaning') or '—'}"]
            if v.get("word_type"):
                parts.append(f"🏷️ Loại: {v['word_type']}")
            if v.get("example"):
                parts.append(f"\n💬 Ví dụ:\n{v['example']}")
                if v.get("example_meaning"):
                    parts.append(f"   → {v['example_meaning']}")
            if v.get("note"):
                parts.append(f"\n📝 Ghi chú: {v['note']}")
            self.fc_back.configure(text="\n".join(parts))
        self.fc_counter.configure(text=f"{self._card_idx + 1} / {len(self._cards)}")

    def _flip_card(self):
        self._flipped = not self._flipped
        self._render_card()

    def _prev_card(self):
        if self._cards:
            self._card_idx = (self._card_idx - 1) % len(self._cards)
            self._flipped = False
            self._render_card()

    def _next_card(self):
        if self._cards:
            self._card_idx = (self._card_idx + 1) % len(self._cards)
            self._flipped = False
            self._render_card()

    def _shuffle_cards(self):
        import random
        if self._cards:
            random.shuffle(self._cards)
            self._card_idx = 0
            self._flipped = False
            self._render_card()

    def _speak_current(self):
        if self._cards:
            v = self._cards[self._card_idx % len(self._cards)]
            speak_word(v.get("word", ""), self.app.current_language)

    def _on_global_key(self, event):
        # Phím tắt chỉ áp dụng khi tab này hiển thị và không đang gõ chữ
        if not self.winfo_ismapped():
            return
        try:
            if self.app.tabview.get() != "🎓 Học Tập":
                return
        except Exception:
            return
        w = self.focus_get()
        if isinstance(w, (tk.Entry, tk.Text)) or (w is not None and hasattr(w, "_entry")):
            return
        if self.cb_source.get() != SOURCE_SELF:
            return
        if event.keysym == "Left":
            self._prev_card()
        elif event.keysym == "Right":
            self._next_card()
        elif event.keysym == "space":
            self._flip_card()
            return "break"

    # ── Khóa học AI ──────────────────────────────────────────────────────────
    def _reload_course(self):
        lang = self.app.current_language
        self._course = course_db.get_course(lang)
        prog = course_db.get_progress(lang)
        days = sorted(int(d.get("day", 0)) for d in (self._course or {}).get("days", []))
        if not days:
            self.cb_day.set_items([])
            self.cb_day.set("—")
            self.lbl_total_days.configure(text="/ 0")
            self.ent_jump_day.delete(0, "end")
            self.lbl_day_status.configure(text="")
            self.lbl_day_title.configure(text="Không có bài học nào")
            self.lbl_prog_info.configure(text="Chưa có khóa học AI. Bấm 🤖 Sinh khóa học AI để tạo.")
            self.progress_bar.set(0)
            self._set_lesson_text("Chưa có khóa học AI.\n\n"
                                  "Bấm nút 🤖 Sinh khóa học AI ở góc trên phải để tạo "
                                  "khóa học chuyên sâu theo ngày (từ vựng + ngữ pháp + trắc nghiệm).")
            self._reset_quiz_widgets()
            return
        items = []
        done = set(prog.get("completed_days", []))
        days_by_num = {int(d.get("day", 0)): d for d in (self._course or {}).get("days", [])}
        default_lvl = (self._course or {}).get("level", "")
        for d in days:
            lesson = days_by_num.get(d) or {}
            topic = (lesson.get("topic") or lesson.get("title") or "").strip()
            lvl = lesson.get("level") or default_lvl or ""
            phase = lesson.get("phase") or ""
            short_lvl = _short_level_name(lvl, phase)
            tag = f"[{short_lvl}] " if short_lvl else ""
            lb = f"Ngày {d} {tag}· {topic[:28]}" if topic else f"Ngày {d} {tag}"
            if d in done:
                lb += " ✅"
            items.append((d, lb, short_lvl, d in done))
        self.cb_day.set_items(items)
        self.lbl_total_days.configure(text=f"/ {len(days)}")
        last = prog.get("last_day") if prog.get("last_day") in days else days[0]
        self._select_day_by_num(last)
        total = len(days)
        level_str = (self._course or {}).get("level", "")
        level_info = f" · trình độ: {level_str}" if level_str else ""
        self.lbl_bottom.configure(
            text=f"Khóa học AI '{lang}'{level_info}: {total} ngày · "
                 f"hoàn thành {len(done)}/{total}. "
                 f"Dữ liệu lưu tại data/ai_courses/")
        # Cập nhật progress bar
        pct = len(done) / total if total > 0 else 0
        self.progress_bar.set(pct)
        self.lbl_prog_info.configure(
            text=f"Tiến độ: {len(done)}/{total} ngày · {pct*100:.0f}%")

    def _select_day_by_num(self, day_num: int):
        for item in self.cb_day._items:
            if item[0] == day_num:
                self.cb_day.set(item[1])
                break
        self._load_selected_day()

    def _on_jump_day(self):
        val = self.ent_jump_day.get().strip()
        if not val:
            return
        try:
            day_num = int(val)
            days = sorted(int(d.get("day", 0)) for d in (self._course or {}).get("days", []))
            if not days:
                return
            if day_num in days:
                self._select_day_by_num(day_num)
            else:
                messagebox.showwarning("Thông báo", f"Không tìm thấy Ngày {day_num}.\nKhóa học hiện có các ngày: {days[0]} → {days[-1]}.")
        except ValueError:
            messagebox.showwarning("Thông báo", "Vui lòng nhập một số ngày hợp lệ (ví dụ: 48).")

    def _prev_day(self):
        days = sorted(int(d.get("day", 0)) for d in (self._course or {}).get("days", []))
        if not days:
            return
        curr = self._selected_day_num() or days[0]
        if curr in days:
            idx = days.index(curr)
            prev_day = days[(idx - 1) % len(days)]
            self._select_day_by_num(prev_day)

    def _next_day(self):
        days = sorted(int(d.get("day", 0)) for d in (self._course or {}).get("days", []))
        if not days:
            return
        curr = self._selected_day_num() or days[0]
        if curr in days:
            idx = days.index(curr)
            next_day = days[(idx + 1) % len(days)]
            self._select_day_by_num(next_day)

    def _open_day_selector_dialog(self):
        if not self._course or not self._course.get("days"):
            messagebox.showinfo("Thông báo", "Chưa có ngày học nào trong khóa học AI.")
            return
        prog = course_db.get_progress(self.app.current_language)
        DaySelectorDialog(self.winfo_toplevel(), self._course, prog, self._select_day_by_num)

    def _selected_day_num(self):
        txt = self.cb_day.get()
        m = re.search(r"Ngày\s+(\d+)", txt)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                pass
        return None

    def _get_day_lesson(self, day):
        for d in (self._course or {}).get("days", []):
            if int(d.get("day", -1)) == day:
                return d
        return None

    def _load_selected_day(self):
        day = self._selected_day_num()
        days = sorted(int(d.get("day", 0)) for d in (self._course or {}).get("days", []))
        self.lbl_total_days.configure(text=f"/ {len(days)}")
        if day is not None:
            self.ent_jump_day.delete(0, "end")
            self.ent_jump_day.insert(0, str(day))
        lesson = self._get_day_lesson(day) if day else None
        if not lesson:
            self._current_lesson = None
            self._set_lesson_text("Không có dữ liệu ngày này.")
            self._reset_quiz_widgets()
            self.lbl_day_title.configure(text="Không có bài học nào")
            self.lbl_day_status2.configure(text="")
            self.progress_bar.set(0)
            return
        self._current_lesson = lesson
        self._render_lesson_text(lesson)
        self._update_day_status(day)
        self._start_quiz(day, lesson.get("quiz") or {})
        # Cập nhật tiêu đề ngày và progress bar
        self.lbl_day_title.configure(text=f"Ngày {day} — {lesson.get('title', '')}")
        prog = course_db.get_progress(self.app.current_language)
        done = set(prog.get("completed_days", []))
        total = len(days)
        pct = len(done) / total if total > 0 else 0
        self.progress_bar.set(pct)
        self.lbl_prog_info.configure(
            text=f"Tiến độ: {len(done)}/{total} ngày · {pct*100:.0f}%")
        # Cập nhật trạng thái ngày trong label nhỏ
        if day in done:
            self.lbl_day_status2.configure(text="✅ Hoàn thành", text_color=C["success"])
        else:
            self.lbl_day_status2.configure(text="⏳ Chưa hoàn thành", text_color=C["warn"])

    def _update_day_status(self, day):
        prog = course_db.get_progress(self.app.current_language)
        if day in prog.get("completed_days", []):
            s = prog.get("quiz_scores", {}).get(str(day), {}).get("score")
            self.lbl_day_status.configure(
                text=f"✅ Đã hoàn thành" + (f" — điểm cao nhất: {s}%" if s is not None else ""),
                text_color=C["success"])
        else:
            self.lbl_day_status.configure(text="⏳ Chưa hoàn thành", text_color=C["warn"])

    def _set_lesson_text(self, content):
        self.lesson_text.configure(state="normal")
        self.lesson_text.delete("1.0", "end")
        self.lesson_text.insert("1.0", content)
        self.lesson_text.configure(state="disabled")

    def _render_lesson_text(self, lesson):
        lines = [f"📚 NGÀY {lesson.get('day', '?')} — {(lesson.get('title') or '').upper()}"]
        meta = []
        lvl = lesson.get("level") or (self._course or {}).get("level") or ""
        if lvl:
            meta.append(f"🎯 Cấp độ: {lvl}")
        if lesson.get("phase"):
            meta.append(f"🏷️ Giai đoạn: {lesson['phase']}")
        topic = (lesson.get("topic") or "").strip()
        if topic and topic != (lesson.get("title") or "").strip():
            meta.append(f"📌 Chủ đề: {topic}")
        if meta:
            lines += ["  |  ".join(meta), "-" * 60]
        lines += ["=" * 60, ""]

        lines.append("🔤 TỪ VỰNG CHUYÊN SÂU")
        lines.append("-" * 60)
        media_index = self._media_index()
        for i, v in enumerate(lesson.get("vocab", []), 1):
            ipa = v.get("ipa") or v.get("pronunciation") or ""
            ipa_ev = v.get("ipa_ev") or ""
            lines.append(f"{i}. {v.get('word', '')}"
                         + (f"  [{v['pronunciation']}]" if v.get("pronunciation") else "")
                         + (f"  🔊 {ipa}" if ipa and ipa != v.get("pronunciation") else "")
                         + (f"  📖 {ipa_ev}" if ipa_ev and ipa_ev != ipa else "")
                         + (f" ({v['part_of_speech']})" if v.get("part_of_speech") else "")
                         + (f"  <{v['pos']}>" if v.get("pos") else ""))
            # Ảnh minh họa
            img_path = self._media_file(media_index, v.get("image_ref"))
            if img_path:
                lines.append(f"   🖼️ Ảnh: {img_path}")
            lines.append(f"   Nghĩa: {v.get('meaning_vi') or '—'}")
            if v.get("phonetic_note"):
                lines.append(f"   👄 Khẩu hình: {v['phonetic_note']}")
            if v.get("explanation"):
                lines.append(f"   Giải thích: {v['explanation']}")
            if v.get("example_sentence"):
                lines.append(f"   💬 {v['example_sentence']}")
                if v.get("example_meaning_vi"):
                    lines.append(f"      → {v['example_meaning_vi']}")
            # Audio
            audio = self._media_file(media_index, v.get("audio_ref"))
            if audio:
                lines.append(f"   🔊 Audio: {audio}")
            # Dẫn chứng (Wikipedia/Wiktionary)
            for s in (v.get("sources") or []):
                if not isinstance(s, dict):
                    continue
                title = s.get("title") or s.get("kind") or "nguồn"
                url = s.get("url") or ""
                lic = s.get("license") or ""
                line = f"   📚 Nguồn: {title}"
                if url:
                    line += f" — {url}"
                if lic:
                    line += f" ({lic})"
                lines.append(line)
                if s.get("quote"):
                    lines.append(f"      “{s['quote'][:160]}”")
            if v.get("etymology"):
                lines.append(f"   🏛️ Từ nguyên: {v['etymology'][:200]}")
            lines.append("")

        patterns = lesson.get("sentence_patterns") or []
        if patterns:
            lines.append("📝 CÁCH DÙNG CÂU / MẪU CÂU")
            lines.append("-" * 60)
            for i, p in enumerate(patterns, 1):
                lines.append(f"{i}. {p.get('pattern', '')} — {p.get('meaning_vi', '')}")
                if p.get("structure_note"):
                    lines.append(f"   {p['structure_note']}")
                if p.get("example_sentence"):
                    lines.append(f"   💬 {p['example_sentence']}")
                    if p.get("example_meaning_vi"):
                        lines.append(f"      → {p['example_meaning_vi']}")
                lines.append("")

        common = lesson.get("common_sentences") or []
        if common:
            lines.append("💬 CÂU THÔNG DỤNG GIAO TIẾP")
            lines.append("-" * 60)
            for i, s in enumerate(common, 1):
                lines.append(f"{i}. {s.get('sentence', '')} — {s.get('meaning_vi', '')}")
                if s.get("situation"):
                    lines.append(f"   📌 Tình huống: {s['situation']}")
            lines.append("")

        grammar_items = lesson.get("grammar") or []
        if isinstance(grammar_items, dict):
            grammar_items = [grammar_items] if grammar_items.get("title") else []
        if grammar_items:
            lines.append("📐 NGỮ PHÁP")
            lines.append("-" * 60)
            for gi, g in enumerate(grammar_items, 1):
                lines.append(f"  Bài {gi}: {g.get('title', '')}")
                if g.get("explanation"):
                    lines.append(f"  {g['explanation']}")
                for ex in g.get("examples", []):
                    lines.append(f"    💬 {ex.get('sentence', '')}")
                    if ex.get("meaning_vi"):
                        lines.append(f"       → {ex['meaning_vi']}")
                if g.get("pronunciation_focus"):
                    lines.append(f"  👄 Phát âm: {g['pronunciation_focus']}")
                for m in g.get("common_mistakes", []):
                    lines.append(f"  ❌ {m.get('wrong', '')}")
                    lines.append(f"  ✅ {m.get('right', '')}")
                    if m.get("why_vi"):
                        lines.append(f"     ↳ {m['why_vi']}")
                if g.get("mini_quiz"):
                    lines.append("  🧠 Kiểm tra nhanh:")
                    for q in g["mini_quiz"]:
                        opts = q.get("options") or []
                        lines.append(f"     • {q.get('question', '')}")
                        for oi, o in enumerate(opts):
                            lines.append(f"       {chr(65 + oi)}. {o}")
                        if q.get("explanation"):
                            lines.append(f"       → {q['explanation']}")
                lines.append("")

        # ── HỘI THOẠI (roleplay) ──────────────────────────────────────────
        dialogues = lesson.get("dialogue") or []
        if dialogues:
            lines.append("💬 HỘI THOẠI (ROLEPLAY)")
            lines.append("-" * 60)
            for di, dlg in enumerate(dialogues):
                lines.append(f"  ▶ {dlg.get('title') or f'Kịch bản {di+1}'}"
                             + (f"  [{dlg.get('level_tag')}]" if dlg.get("level_tag") else ""))
                if dlg.get("situation"):
                    lines.append(f"    📌 {dlg['situation']}")
                d_audio = self._media_file(media_index, dlg.get("audio_ref"))
                if d_audio:
                    lines.append(f"    🔊 Audio cả đoạn: {d_audio}")
                for t in dlg.get("turns", []):
                    lines.append(f"    {t.get('speaker', 'A')}: {t.get('line_target', '')}")
                    if t.get("line_vi"):
                        lines.append(f"       → {t['line_vi']}")
                    if t.get("tone") or t.get("emotion"):
                        lines.append(f"       🎭 {t.get('emotion', '')} {t.get('tone', '')}".rstrip())
                    if t.get("focus_words"):
                        lines.append(f"       🔍 Từ trọng tâm: {', '.join(t['focus_words'])}")
                if dlg.get("cultural_note"):
                    lines.append(f"    🌏 {dlg['cultural_note']}")
                lines.append("")

        self._set_lesson_text("\n".join(lines))

    # ── Dẫn chứng (Wikipedia/Wiktionary) ───────────────────────────────────
    def _run_evidence_for_day(self):
        """Tra dẫn chứng cho ngày đang xem (chạy nền, không block UI)."""
        day = self._selected_day_num()
        lesson = self._get_day_lesson(day) if day else None
        if not lesson:
            messagebox.showinfo("Không có dữ liệu",
                                "Hãy chọn một ngày có bài học trước khi tra dẫn chứng.",
                                parent=self)
            return
        lang = self.app.current_language
        self.lbl_bottom.configure(text="📚 Đang tra dẫn chứng (Wikipedia/Wiktionary)…")

        def _work():
            try:
                from ai.pipeline_evidence import run_evidence_stage
                run_evidence_stage(lang, day, lesson, log_fn=lambda m: None,
                                   force=True)
            except Exception as e:
                def _err():
                    self.lbl_bottom.configure(
                        text=f"⚠ Lỗi tra dẫn chứng: {type(e).__name__}: {e}")
                try:
                    self.after(0, _err)
                except Exception:
                    pass
                return

            def _done():
                try:
                    course_db.save_course(lang, self._course)
                except Exception:
                    pass
                if self._current_lesson:
                    self._render_lesson_text(self._current_lesson)
                self.lbl_bottom.configure(
                    text=f"📚 Đã tra dẫn chứng cho Ngày {day} "
                         f"(dữ liệu lưu trong data/ai_courses/).")
            try:
                self.after(0, _done)
            except Exception:
                pass

        threading.Thread(target=_work, daemon=True).start()

    # ── Media helpers ──────────────────────────────────────────────────────
    def _media_index(self):
        """Manifest media (cache 1 lần / 30s)."""
        import time
        now = time.time()
        if getattr(self, "_media_idx_ts", 0) + 30 > now:
            return getattr(self, "_media_idx_cache", None) or {}
        try:
            from ai import media_store
            self._media_idx_cache = media_store.load_index()
            self._media_idx_ts = now
        except Exception:
            self._media_idx_cache = {}
            self._media_idx_ts = now
        return self._media_idx_cache

    def _media_file(self, index, ref):
        """Đường dẫn file media tuyệt đối theo ref, hoặc '' nếu không có."""
        if not ref or not index:
            return ""
        entry = (index.get("items") or {}).get(ref)
        if not entry:
            return ""
        rel = entry.get("rel_path") or ""
        if not rel:
            return ""
        try:
            from ai import media_store
            path = media_store.abs_path_for(rel)
        except Exception:
            return ""
        import os
        return path if os.path.isfile(path) else ""

    # ── Trắc nghiệm ──────────────────────────────────────────────────────────
    def _reset_quiz_widgets(self):
        self._quiz = None
        self.quiz_lbl_num.configure(text="Trắc nghiệm")
        self.quiz_question.configure(text="Chưa có câu hỏi.")
        self.quiz_feedback.configure(text="", text_color=C["muted"])
        self._clear_quiz_options()
        self.btn_confirm.configure(state="disabled")
        self.btn_next_q.configure(state="disabled")
        self._set_grade_buttons(None)

    def _set_grade_buttons(self, word):
        """Bật/tắt 4 nút đánh giá SM-2 theo từ vựng của câu hỏi hiện tại."""
        try:
            for b in (self.srs_grade_btns_q or {}).values():
                b.configure(state="normal" if word else "disabled")
        except Exception:
            pass
        try:
            if word:
                st = review_store.get_state(self.app.current_language, word)
                lv = mastery_level(st)
                self.lbl_srs_grade.configure(
                    text=f"🧠 Nhớ từ '{word}'? ({SRS_STATE_LABEL.get(lv, lv)})")
            else:
                self.lbl_srs_grade.configure(text="🧠 Không xác định được từ của câu này")
        except Exception:
            pass

    def _current_quiz_vocab_word(self):
        """Từ vựng mà câu trắc nghiệm hiện tại đang hỏi (None nếu không khớp)."""
        qz = self._quiz
        if not qz:
            return None
        try:
            q = qz["questions"][qz["idx"]]
        except (IndexError, KeyError, TypeError):
            return None
        low = str(q.get("question") or "").lower()
        if not low:
            return None
        for v in ((self._current_lesson or {}).get("vocab") or []):
            if not isinstance(v, dict):
                continue
            w = str(v.get("word") or "").strip()
            if w and len(w) >= 2 and w.lower() in low:
                return w
        return None

    def _grade_current_word(self, grade):
        """Ghi 1 lần ôn SM-2 cho từ vựng của câu trắc nghiệm đang xem."""
        word = self._current_quiz_vocab_word()
        if not word:
            self.lbl_srs_grade.configure(text="⚠ Câu này không hỏi từ cụ thể nào")
            return
        meaning = ""
        for v in ((self._current_lesson or {}).get("vocab") or []):
            if isinstance(v, dict) and str(v.get("word") or "").strip() == word:
                meaning = v.get("meaning_vi") or ""
                break
        try:
            _st, rinfo = review_store.record_review(
                self.app.current_language, word, grade,
                extra={"meaning_vi": meaning})
        except Exception as e:
            messagebox.showerror("Lỗi ôn tập", f"Không lưu được lần ôn:\n{e}", parent=self)
            return
        nxt = rinfo.get("next_review_in_days", 0)
        when = (f"{int(round(nxt * 1440))} phút" if nxt < 1 else f"{nxt:g} ngày")
        self.lbl_srs_grade.configure(
            text=f"✅ '{word}': {rinfo.get('label', '')} · ôn lại sau {when}")
        self._set_grade_buttons(word)
        self.app.update_stats()

    def _clear_quiz_options(self):
        for r in self.quiz_radios:
            r.destroy()
        self.quiz_radios = []
        self.quiz_var.set("")

    def _start_quiz(self, day, quiz_data):
        questions = self._flatten_quiz(quiz_data)
        self._quiz = {"day": day, "questions": questions, "idx": 0,
                      "correct": 0, "answered": False}
        if not questions:
            self._reset_quiz_widgets()
            self.quiz_question.configure(text="Ngày này chưa có câu trắc nghiệm.")
            return
        self._render_question()

    def _flatten_quiz(self, quiz_data):
        """Chuyển quiz dict 4 loại (mới) hoặc list (cũ) thành danh sách phẳng."""
        if isinstance(quiz_data, list):
            return quiz_data
        if not isinstance(quiz_data, dict):
            return []
        cat_names = {"vocab": "Từ vựng", "pattern": "Cách dùng câu",
                     "common": "Câu thông dụng", "grammar": "Ngữ pháp",
                     "mixed": "Tổng hợp"}
        out = []
        for cat_key in ("vocab", "pattern", "common", "grammar", "mixed"):
            items = quiz_data.get(cat_key) or []
            for q in items:
                if isinstance(q, dict) and q.get("question"):
                    q2 = dict(q)
                    q2["_category"] = cat_names.get(cat_key, cat_key)
                    out.append(q2)
        return out

    def _render_question(self):
        qz = self._quiz
        qs = qz["questions"]
        q = qs[qz["idx"]]
        cat = q.get("_category", "")
        cat_label = f"  · {cat}" if cat else ""
        self.quiz_lbl_num.configure(text=f"❓ Câu {qz['idx'] + 1}/{len(qs)}"
                                         f"{cat_label}  (đúng: {qz['correct']})")
        self.quiz_question.configure(text=q["question"])
        self._clear_quiz_options()
        self.quiz_feedback.configure(text="", text_color=C["muted"])
        for i, opt in enumerate(q["options"]):
            rb = ctk.CTkRadioButton(self.quiz_opts_frame, text=f"{chr(65 + i)}. {opt}",
                                    variable=self.quiz_var, value=str(i),
                                    fg_color=C["accent"], text_color=C["text"],
                                    font=("Arial", 13))
            rb.pack(anchor="w", pady=3)
            self.quiz_radios.append(rb)
        self.btn_confirm.configure(state="normal")
        self.btn_next_q.configure(state="disabled")
        self._set_grade_buttons(self._current_quiz_vocab_word())

    def _confirm_answer(self):
        qz = self._quiz
        if not qz or qz["answered"]:
            return
        choice = self.quiz_var.get()
        if choice == "":
            self.quiz_feedback.configure(text="⚠️ Hãy chọn một đáp án!", text_color=C["warn"])
            return
        q = qz["questions"][qz["idx"]]
        correct = int(choice) == int(q.get("answer_index", 0))
        if correct:
            qz["correct"] += 1
            fb = f"✅ Chính xác!\n💡 {q.get('explanation', '')}"
            self.quiz_feedback.configure(text=fb, text_color=C["success"])
        else:
            ans_letter = chr(65 + int(q.get("answer_index", 0)))
            fb = (f"❌ Sai rồi! Đáp án đúng: {ans_letter}. {q['options'][int(q.get('answer_index', 0))]}\n"
                  f"💡 {q.get('explanation', '')}")
            self.quiz_feedback.configure(text=fb, text_color=C["danger"])
        qz["answered"] = True
        self.btn_confirm.configure(state="disabled")
        self.btn_next_q.configure(state="normal")
        self.quiz_lbl_num.configure(text=f"❓ Câu {qz['idx'] + 1}/{len(qz['questions'])}"
                                         f"  (đúng: {qz['correct']})")

    def _next_question(self):
        qz = self._quiz
        if not qz:
            return
        if not qz["answered"]:
            return
        qz["idx"] += 1
        qz["answered"] = False
        if qz["idx"] >= len(qz["questions"]):
            self._finish_quiz()
        else:
            self._render_question()

    def _finish_quiz(self):
        qz = self._quiz
        total = len(qz["questions"])
        score = round(qz["correct"] / max(total, 1) * 100)
        course_db.mark_day_completed(self.app.current_language, qz["day"], score)
        msg = (f"🏆 HOÀN THÀNH NGÀY {qz['day']}!\n"
               f"Kết quả: {qz['correct']}/{total} câu đúng — {score}%\n"
               f"{'🌟 Xuất sắc!' if score >= 85 else '👍 Cố gắng thêm nhé!'}\n"
               f"(Tiến độ đã được lưu)")
        self.quiz_question.configure(text="🎉 Hoàn thành!")
        self._clear_quiz_options()
        self.quiz_feedback.configure(text=msg, text_color=C["accent"] if score >= 85 else C["warn"])
        self.btn_confirm.configure(state="disabled")
        self.btn_next_q.configure(state="disabled")
        self.quiz_lbl_num.configure(text=f"✅ Ngày {qz['day']} — {score}%")
        self._update_day_status(qz["day"])

    # ── Sinh / xóa khóa học ──────────────────────────────────────────────────
    def _open_generation(self):
        # KHÔNG chặn khi DB rỗng: AI tự lập toàn bộ giáo trình từ con số 0.
        dlg = CourseGenerationDialog(self.app, self.app, on_finished=self.refresh_language)
        self.app.wait_window(dlg)

    def _delete_course(self):
        lang = self.app.current_language
        if not course_db.get_course(lang):
            messagebox.showinfo("Chưa có gì để xóa", f"Ngôn ngữ '{lang}' chưa có khóa học AI.", parent=self)
            return
        if messagebox.askyesno("Xác nhận xóa",
                               f"Xóa toàn bộ khóa học AI và tiến độ của '{lang}'?",
                               parent=self.app):
            course_db.delete_course(lang)
            self._reload_course()

# ══════════════════════════════════════════════════════════════════════════════
# Main App
# ══════════════════════════════════════════════════════════════════════════════
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Vocabulary App - Học Từ Vựng")
        self.geometry("1100x700")
        self.configure(fg_color=C["bg"])

        self.available_languages = get_available_languages()  # list of dict: {display, slug, num_days}
        if not self.available_languages:
            self.available_languages = [{"display": "English", "slug": "english", "num_days": 0}]
        # Chọn ngôn ngữ có số ngày lớn nhất (mặc định là Tiếng Nhật 1260 ngày)
        self.available_languages.sort(key=lambda x: x["num_days"], reverse=True)
        self.current_language = self.available_languages[0]["slug"]
        self.last_topic = ""
        self.last_date_tag = ""

        # Tabs
        self.tabview = ctk.CTkTabview(self, fg_color=C["sidebar"], segmented_button_fg_color=C["card2"], segmented_button_selected_color=C["accent"], segmented_button_selected_hover_color=C["accent2"])
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_list = self.tabview.add("Danh Sách Từ Vựng")
        self.tab_study = self.tabview.add("🎓 Học Tập")
        self.tab_sync = self.tabview.add("Đồng Bộ & Cài Đặt")

        # Init views
        self.view_list = VocabListTab(self.tab_list, self)
        self.view_list.pack(fill="both", expand=True)

        self.view_study = StudyTab(self.tab_study, self)
        self.view_study.pack(fill="both", expand=True)

        self.view_sync = SettingsSyncTab(self.tab_sync, self)
        self.view_sync.pack(fill="both", expand=True)

        self.set_language(self.current_language)

    def set_language(self, lang_slug: str):
        """lang_slug là slug của ngôn ngữ (ví dụ: "tiếng_nhật", "tiếng_anh")."""
        # Tìm thông tin ngôn ngữ từ available_languages
        lang_info = None
        for l in self.available_languages:
            if l["slug"] == lang_slug:
                lang_info = l
                break
        if not lang_info:
            # Nếu không tìm thấy, dùng lang_slug làm display
            lang_info = {"display": lang_slug.replace("_", " ").title(), "slug": lang_slug, "num_days": 0}
        
        self.current_language = lang_slug
        self.current_language_display = lang_info["display"]
        self.current_language_num_days = lang_info["num_days"]
        
        # Cập nhật dropdown trong VocabListTab
        display_values = [f"{l['display']} ({l['num_days']} ngày)" if l['num_days'] > 0 else l['display'] for l in self.available_languages]
        self.view_list.cb_lang_main.configure(values=display_values)
        
        # Tìm index hiện tại
        current_display = f"{lang_info['display']} ({lang_info['num_days']} ngày)" if lang_info['num_days'] > 0 else lang_info['display']
        self.view_list.cb_lang_main.set(current_display)
        
        self.view_list.refresh_filters()
        self.view_list.refresh()
        try:
            self.view_study.refresh_language()
        except Exception:
            pass

    def update_stats(self):
        """Làm mới các chỉ số hiển thị (SRS streak / đến hạn, thống kê từ vựng)."""
        try:
            self.view_study.refresh_srs_stats()
        except Exception:
            pass
        try:
            self.view_list.refresh()
        except Exception:
            pass

if __name__ == "__main__":
    app = App()
    app.mainloop()
