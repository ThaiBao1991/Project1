#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikTok Download Manager - GUI với CustomTkinter
- Tab 1: Video lỗi (từ Extension) → checkbox tải thủ công / hàng loạt
- Tab 2: Video đã tải (từ Extension DB) → tải lại sang máy khác
- Tab 3: Cài đặt
"""

import sys
import os
import json
import threading
import time
from pathlib import Path
from datetime import datetime

# Auto-install dependencies
def _ensure_lib(pkg, import_as=None):
    try:
        __import__(import_as or pkg)
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

_ensure_lib("customtkinter")

import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

# Add src to path
_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE / "src"))

try:
    from ext_sync import ExtensionSync, get_ext_sync
    from downloader import HybridDownloader
    import yt_dlp.utils as ytutils
    from secret_vault import mask_token, unmask_token
    from viewer_sync import build_viewer_data, deploy_webapp_to_github
    import webbrowser
except ImportError as e:
    messagebox.showerror("Loi import", f"Khong load duoc module:\n{e}")
    sys.exit(1)

# ========== Config ==========
SETTINGS_FILE = _HERE / "settings.json"
DEFAULT_EXT_PATH = r"D:\dlvideott\data\.appdata"
WEBAPP_DIR = _HERE / "webapp"
APP_NAME = "TikTok Download Manager"
VERSION = "1.1.0"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def load_settings() -> dict:
    defaults = {
        "ext_data_path": DEFAULT_EXT_PATH,
        "output_dir": "downloads",
        "rate_limit": "1M",
        "retries": 3,
        "github_user": "",
        "github_repo": "TitokDl",
        "enc_gh_token": "",
        "last_web_url": "",
    }
    # Auto-import config cũ từ myfaveTT_viewer nếu có
    legacy_cfg = Path(r"D:\CompleteCode\Python\tiktok\myfaveTT_viewer\.config.json")
    if not SETTINGS_FILE.exists() and legacy_cfg.exists():
        try:
            old = json.loads(legacy_cfg.read_text(encoding="utf-8"))
            if old.get("github_username"): defaults["github_user"] = old["github_username"]
            if old.get("github_repo"): defaults["github_repo"] = old["github_repo"]
            if old.get("github_token"): defaults["enc_gh_token"] = mask_token(old["github_token"])
            if old.get("last_url"): defaults["last_web_url"] = old["last_url"]
        except Exception:
            pass

    if SETTINGS_FILE.exists():
        try:
            saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            defaults.update(saved)
        except Exception:
            pass
    return defaults


def save_settings(s: dict):
    SETTINGS_FILE.write_text(json.dumps(s, indent=2, ensure_ascii=False), encoding="utf-8")


class TikTokDownloadManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"TikTok Download Manager v{VERSION}")
        self.geometry("940x690")
        self.minsize(800, 560)
        self.settings = load_settings()
        self._stop_flag = threading.Event()
        self._is_downloading = False
        self._failed_items = []
        self._failed_checks = []
        self._downloaded_items = []
        self._downloaded_checks = []
        self._build_ui()
        self.after(200, self._load_ext_data)

    def _build_ui(self):
        # Top bar
        topbar = ctk.CTkFrame(self, height=52, corner_radius=0, fg_color=("#111122", "#0a0a15"))
        topbar.pack(fill="x", side="top")
        ctk.CTkLabel(
            topbar, text="  TikTok Download Manager",
            font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color="#fe2c55"
        ).pack(side="left", padx=12, pady=10)
        self._status_lbl = ctk.CTkLabel(
            topbar, text="San sang...", font=ctk.CTkFont("Segoe UI", 11), text_color="#888888"
        )
        self._status_lbl.pack(side="right", padx=16)

        # Tabs
        self._tabs = ctk.CTkTabview(self, corner_radius=8)
        self._tabs.pack(fill="both", expand=True, padx=10, pady=(6, 10))
        self._tab_f = self._tabs.add("Video loi")
        self._tab_d = self._tabs.add("Da tai (Tai lai)")
        self._tab_w = self._tabs.add("Web Viewer (PWA)")
        self._tab_s = self._tabs.add("Cai dat")
        self._build_tab_failed()
        self._build_tab_downloaded()
        self._build_tab_viewer()
        self._build_tab_settings()

    # ---- TAB FAILED ----
    def _build_tab_failed(self):
        t = self._tab_f

        bar = ctk.CTkFrame(t, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 6))

        def btn(parent, text, cmd, fc="#2f3640", hc="#353b48", w=None):
            kw = dict(text=text, command=cmd, fg_color=fc, hover_color=hc, corner_radius=6)
            if w: kw["width"] = w
            return ctk.CTkButton(parent, **kw)

        btn(bar, "Lam moi", self._reload_failed, w=90).pack(side="left", padx=3)
        btn(bar, "Chon tat ca", lambda: self._sel_all(self._failed_checks, True), w=100).pack(side="left", padx=3)
        btn(bar, "Bo chon", lambda: self._sel_all(self._failed_checks, False), w=80).pack(side="left", padx=3)
        self._btn_dl_sel = btn(bar, "Tai da chon", self._download_selected_failed, fc="#00b894", hc="#00a381", w=120)
        self._btn_dl_sel.pack(side="left", padx=3)
        self._btn_dl_all = btn(bar, "Tai tat ca", self._download_all_failed, fc="#6c5ce7", hc="#5a4dcf", w=100)
        self._btn_dl_all.pack(side="left", padx=3)
        self._btn_stop_f = btn(bar, "Dung", self._stop_download, fc="#e74c3c", hc="#c0392b", w=70)
        self._btn_stop_f.configure(state="disabled")
        self._btn_stop_f.pack(side="left", padx=3)
        btn(bar, "Xoa da chon", self._delete_selected_failed, fc="#d63031", hc="#b71c1c", w=110).pack(side="right", padx=3)

        self._f_count = ctk.CTkLabel(t, text="", font=ctk.CTkFont("Segoe UI", 11), text_color="#fe2c55")
        self._f_count.pack(anchor="w", padx=6, pady=(0, 4))

        self._f_scroll = ctk.CTkScrollableFrame(t, fg_color=("#f0f0f0", "#1a1a2a"), corner_radius=8, height=270)
        self._f_scroll.pack(fill="both", expand=True, pady=(0, 6))

        self._f_prog = ctk.CTkProgressBar(t, height=10, corner_radius=5)
        self._f_prog.set(0)
        self._f_prog.pack(fill="x", padx=2, pady=(0, 4))

        self._f_log = ctk.CTkTextbox(t, height=85, font=ctk.CTkFont("Consolas", 10), state="disabled", corner_radius=6)
        self._f_log.pack(fill="x")

    # ---- TAB DOWNLOADED ----
    def _build_tab_downloaded(self):
        t = self._tab_d

        ctk.CTkLabel(t, text="Video Extension da tai thanh cong - Tai lai sang may khac",
                     font=ctk.CTkFont("Segoe UI", 11), text_color="#888888").pack(anchor="w", padx=4, pady=(0, 4))

        bar = ctk.CTkFrame(t, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 6))

        def btn(parent, text, cmd, fc="#2f3640", hc="#353b48", w=None):
            kw = dict(text=text, command=cmd, fg_color=fc, hover_color=hc, corner_radius=6)
            if w: kw["width"] = w
            return ctk.CTkButton(parent, **kw)

        ctk.CTkLabel(bar, text="Nguon:", font=ctk.CTkFont("Segoe UI", 11)).pack(side="left", padx=4)
        self._src_var = ctk.StringVar(value="Favorites")
        ctk.CTkOptionMenu(bar, values=["Favorites", "Likes", "Ca hai"], variable=self._src_var,
                          width=120, command=lambda _: self._reload_downloaded()).pack(side="left", padx=4)
        btn(bar, "Lam moi", self._reload_downloaded, w=80).pack(side="left", padx=3)
        btn(bar, "Chon tat ca", lambda: self._sel_all(self._downloaded_checks, True), w=100).pack(side="left", padx=3)
        btn(bar, "Bo chon", lambda: self._sel_all(self._downloaded_checks, False), w=80).pack(side="left", padx=3)
        self._btn_re_sel = btn(bar, "Tai lai da chon", self._redownload_selected, fc="#00b894", hc="#00a381", w=130)
        self._btn_re_sel.pack(side="left", padx=3)
        self._btn_re_all = btn(bar, "Tai lai tat ca", self._redownload_all, fc="#6c5ce7", hc="#5a4dcf", w=110)
        self._btn_re_all.pack(side="left", padx=3)
        self._btn_stop_d = btn(bar, "Dung", self._stop_download, fc="#e74c3c", hc="#c0392b", w=70)
        self._btn_stop_d.configure(state="disabled")
        self._btn_stop_d.pack(side="left", padx=3)

        out_row = ctk.CTkFrame(t, fg_color="transparent")
        out_row.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(out_row, text="Luu vao:", font=ctk.CTkFont("Segoe UI", 11)).pack(side="left", padx=4)
        self._out_var = ctk.StringVar(value=self.settings.get("output_dir", "downloads"))
        ctk.CTkEntry(out_row, textvariable=self._out_var, width=380).pack(side="left", padx=4)
        ctk.CTkButton(out_row, text="...", width=40,
                      command=lambda: self._out_var.set(filedialog.askdirectory() or self._out_var.get())
                      ).pack(side="left")

        self._d_count = ctk.CTkLabel(t, text="", font=ctk.CTkFont("Segoe UI", 11), text_color="#00b894")
        self._d_count.pack(anchor="w", padx=6, pady=(0, 4))

        self._d_scroll = ctk.CTkScrollableFrame(t, fg_color=("#f0f0f0", "#1a1a2a"), corner_radius=8, height=230)
        self._d_scroll.pack(fill="both", expand=True, pady=(0, 6))

        self._d_prog = ctk.CTkProgressBar(t, height=10, corner_radius=5)
        self._d_prog.set(0)
        self._d_prog.pack(fill="x", padx=2, pady=(0, 4))

    # ---- TAB WEB VIEWER (PWA) ----
    def _build_tab_viewer(self):
        t = self._tab_w

        # Header card
        header = ctk.CTkFrame(t, fg_color=("#e6e9f0", "#181828"), corner_radius=8)
        header.pack(fill="x", padx=4, pady=(0, 8))
        ctk.CTkLabel(
            header, text="🌐 TikTok Archive Viewer (PWA) — Xem tren Dien thoai",
            font=ctk.CTkFont("Segoe UI", 13, "bold"), text_color="#00b894"
        ).pack(anchor="w", padx=12, pady=(8, 2))
        ctk.CTkLabel(
            header,
            text="Tong hop toan bo kho video (Favorites & Likes) thanh Web App tinh va deploy len GitHub Pages mien phi.\n"
                 "Sau khi deploy, ban chi can mo link tren dien thoai (Chrome/Safari) de tra cuu offline/online.",
            font=ctk.CTkFont("Segoe UI", 10), text_color="#888888", justify="left"
        ).pack(anchor="w", padx=12, pady=(0, 8))

        # Config card
        frm = ctk.CTkFrame(t, corner_radius=8)
        frm.pack(fill="x", padx=4, pady=(0, 8))
        frm.columnconfigure(1, weight=1)

        self._w_user = ctk.StringVar(value=self.settings.get("github_user", ""))
        self._w_repo = ctk.StringVar(value=self.settings.get("github_repo", "TitokDl"))
        plain_tok = unmask_token(self.settings.get("enc_gh_token", ""))
        self._w_token = ctk.StringVar(value=plain_tok)
        self._w_url = ctk.StringVar(value=self.settings.get("last_web_url", ""))
        self._token_show = False

        ctk.CTkLabel(frm, text="GitHub Username:", font=ctk.CTkFont("Segoe UI", 11)).grid(row=0, column=0, padx=12, pady=6, sticky="w")
        ctk.CTkEntry(frm, textvariable=self._w_user, width=280).grid(row=0, column=1, padx=8, pady=6, sticky="w")

        ctk.CTkLabel(frm, text="Ten Repository:", font=ctk.CTkFont("Segoe UI", 11)).grid(row=1, column=0, padx=12, pady=6, sticky="w")
        ctk.CTkEntry(frm, textvariable=self._w_repo, width=280).grid(row=1, column=1, padx=8, pady=6, sticky="w")

        ctk.CTkLabel(frm, text="GitHub Token (PAT):", font=ctk.CTkFont("Segoe UI", 11)).grid(row=2, column=0, padx=12, pady=6, sticky="w")
        
        tok_row = ctk.CTkFrame(frm, fg_color="transparent")
        tok_row.grid(row=2, column=1, padx=8, pady=6, sticky="ew")
        tok_row.columnconfigure(0, weight=1)
        self._ent_tok = ctk.CTkEntry(tok_row, textvariable=self._w_token, show="*", width=320)
        self._ent_tok.grid(row=0, column=0, sticky="ew")
        self._btn_eye = ctk.CTkButton(tok_row, text="Hien", width=50, command=self._toggle_token_visibility)
        self._btn_eye.grid(row=0, column=1, padx=(6, 0))

        ctk.CTkLabel(frm, text="🛡️ Bao mat:", font=ctk.CTkFont("Segoe UI", 10, "bold"), text_color="#00b894").grid(row=3, column=0, padx=12, pady=2, sticky="w")
        ctk.CTkLabel(frm, text="Token duoc ma hoa DPAPI/Vault cuc bo, khong bao gio luu dang plain text tren dia. An toan 100% tren GitHub.",
                     font=ctk.CTkFont("Segoe UI", 9), text_color="#888888").grid(row=3, column=1, padx=8, pady=2, sticky="w")

        # Action bar
        act = ctk.CTkFrame(t, fg_color="transparent")
        act.pack(fill="x", padx=4, pady=(0, 6))

        ctk.CTkButton(act, text="📊 1. Tao data.json", width=140, fg_color="#2f3640", hover_color="#353b48",
                       command=self._on_build_viewer_data).pack(side="left", padx=4)
        self._btn_deploy = ctk.CTkButton(act, text="🚀 2. Deploy GitHub Pages", width=190, fg_color="#00b894", hover_color="#00a381",
                                          command=self._on_deploy_viewer)
        self._btn_deploy.pack(side="left", padx=4)
        ctk.CTkButton(act, text="🌐 3. Mo trang Web", width=130, fg_color="#6c5ce7", hover_color="#5a4dcf",
                       command=self._on_open_viewer_url).pack(side="left", padx=4)

        # URL display
        url_box = ctk.CTkFrame(t, fg_color="transparent")
        url_box.pack(fill="x", padx=4, pady=(0, 4))
        ctk.CTkLabel(url_box, text="URL Web:", font=ctk.CTkFont("Segoe UI", 11, "bold")).pack(side="left", padx=4)
        self._lbl_web_url = ctk.CTkLabel(url_box, textvariable=self._w_url, font=ctk.CTkFont("Consolas", 11), text_color="#25f4ee")
        self._lbl_web_url.pack(side="left", padx=4)

        # Log box
        self._w_log = ctk.CTkTextbox(t, height=210, font=ctk.CTkFont("Consolas", 10), state="disabled", corner_radius=6)
        self._w_log.pack(fill="both", expand=True, padx=4)

    def _toggle_token_visibility(self):
        self._token_show = not self._token_show
        self._ent_tok.configure(show="" if self._token_show else "*")
        self._btn_eye.configure(text="An" if self._token_show else "Hien")

    def _on_build_viewer_data(self):
        ext_p = Path(self._s_ext.get() if hasattr(self, "_s_ext") else self.settings.get("ext_data_path", DEFAULT_EXT_PATH))
        out_f = WEBAPP_DIR / "data.json"
        self._log(self._w_log, "=== BAT DAU TAO DATA.JSON CHO WEB VIEWER ===")
        def _bg():
            try:
                res = build_viewer_data(ext_p, out_f, log=lambda m: self.after(0, lambda: self._log(self._w_log, m)))
                self.after(0, lambda: messagebox.showinfo(
                    "Thanh cong",
                    f"Da tao data.json thanh cong!\n"
                    f"Tac gia: {res['stats']['authors']:,}\n"
                    f"Favorites: {res['stats']['fav']:,}\n"
                    f"Likes: {res['stats']['likes']:,}"
                ))
            except Exception as e:
                self.after(0, lambda: (
                    self._log(self._w_log, f"Loi: {e}"),
                    messagebox.showerror("Loi tao data", str(e))
                ))
        threading.Thread(target=_bg, daemon=True).start()

    def _on_deploy_viewer(self):
        u = self._w_user.get().strip()
        r = self._w_repo.get().strip()
        tok = self._w_token.get().strip()
        if not u or not r or not tok:
            return messagebox.showerror("Thieu thong tin", "Vui long nhap day du Username, Repo va GitHub Token (PAT)!")

        # Luu an toan (ma hoa token)
        self.settings["github_user"] = u
        self.settings["github_repo"] = r
        self.settings["enc_gh_token"] = mask_token(tok)
        save_settings(self.settings)

        ext_p = Path(self._s_ext.get() if hasattr(self, "_s_ext") else self.settings.get("ext_data_path", DEFAULT_EXT_PATH))
        out_f = WEBAPP_DIR / "data.json"

        self._btn_deploy.configure(state="disabled")
        self._log(self._w_log, "\n=== BAT DAU DEPLOY LEN GITHUB PAGES ===")

        def _bg():
            try:
                # 1. Tu dong cap nhat data.json neu chua co hoac muon dong bo moi nhat
                build_viewer_data(ext_p, out_f, log=lambda m: self.after(0, lambda: self._log(self._w_log, m)))
                # 2. Deploy
                url = deploy_webapp_to_github(u, tok, r, WEBAPP_DIR, log=lambda m: self.after(0, lambda: self._log(self._w_log, m)))
                self.settings["last_web_url"] = url
                save_settings(self.settings)
                self.after(0, lambda: (
                    self._w_url.set(url),
                    self._btn_deploy.configure(state="normal"),
                    messagebox.showinfo("Deploy thanh cong", f"Web Viewer da duoc deploy len GitHub Pages!\nURL: {url}")
                ))
            except Exception as e:
                self.after(0, lambda: (
                    self._log(self._w_log, f"❌ Loi Deploy: {e}"),
                    self._btn_deploy.configure(state="normal"),
                    messagebox.showerror("Loi Deploy", str(e))
                ))
        threading.Thread(target=_bg, daemon=True).start()

    def _on_open_viewer_url(self):
        url = self._w_url.get().strip() or f"https://{self._w_user.get().strip()}.github.io/{self._w_repo.get().strip()}/"
        if not url or "None" in url:
            return messagebox.showinfo("Chua co URL", "Vui long deploy len GitHub Pages truoc de co URL!")
        webbrowser.open(url)

    # ---- TAB SETTINGS ----
    def _build_tab_settings(self):
        t = self._tab_s
        frm = ctk.CTkFrame(t, corner_radius=8)
        frm.pack(fill="both", expand=True, padx=8, pady=8)
        frm.columnconfigure(1, weight=1)

        self._s_ext   = ctk.StringVar(value=self.settings.get("ext_data_path", DEFAULT_EXT_PATH))
        self._s_out   = ctk.StringVar(value=self.settings.get("output_dir", "downloads"))
        self._s_rate  = ctk.StringVar(value=self.settings.get("rate_limit", "1M"))
        self._s_retry = ctk.StringVar(value=str(self.settings.get("retries", 3)))

        def make_row(lbl, var, r, browse=None):
            ctk.CTkLabel(frm, text=lbl, font=ctk.CTkFont("Segoe UI", 12), anchor="w"
                         ).grid(row=r, column=0, sticky="w", padx=16, pady=8)
            ent = ctk.CTkEntry(frm, textvariable=var, width=420)
            ent.grid(row=r, column=1, padx=8, pady=8, sticky="ew")
            if browse:
                ctk.CTkButton(frm, text="...", width=40, command=browse
                              ).grid(row=r, column=2, padx=4)

        make_row("Extension Data Path (.appdata):", self._s_ext, 0,
                 lambda: self._s_ext.set(filedialog.askdirectory(title="Chon thu muc .appdata") or self._s_ext.get()))
        make_row("Thu muc tai ve (mac dinh):", self._s_out, 1,
                 lambda: self._s_out.set(filedialog.askdirectory() or self._s_out.get()))
        make_row("Rate limit (vd: 1M, 500K, 0=unlimited):", self._s_rate, 2)
        make_row("So lan thu lai:", self._s_retry, 3)

        ctk.CTkButton(frm, text="Luu cai dat", width=160, fg_color="#00b894", hover_color="#00a381",
                      command=self._save_settings
                      ).grid(row=4, column=0, columnspan=3, pady=16)

        info = ctk.CTkTextbox(frm, height=110, font=ctk.CTkFont("Segoe UI", 10), state="normal", corner_radius=6)
        info.grid(row=5, column=0, columnspan=3, padx=10, sticky="ew")
        info.insert("end",
            "Extension Data Path: Thu muc .appdata cua extension (chua db_*.js va failed_videos.json)\n"
            "  Mac dinh: D:\\dlvideott\\data\\.appdata\n\n"
            "Thu muc tai ve: Khi tai lai (tab 'Da tai'), video luu vao day.\n"
            "  Cau truc: <thu_muc>/Favorites/videos/<id>.mp4 va /Likes/videos/<id>.mp4\n\n"
            "Rate limit: Gioi han bang thong tai. Vi du: 2M = 2MB/s, 0 = khong gioi han."
        )
        info.configure(state="disabled")

    # ==================== DATA LOADING ====================
    def _get_ext(self) -> ExtensionSync:
        p = self._s_ext.get() if hasattr(self, "_s_ext") else self.settings.get("ext_data_path", DEFAULT_EXT_PATH)
        return ExtensionSync(p)

    def _load_ext_data(self):
        threading.Thread(target=self._reload_failed, daemon=True).start()
        threading.Thread(target=self._reload_downloaded, daemon=True).start()

    def _reload_failed(self):
        try:
            items = self._get_ext().load_failed_queue()
            self._failed_items = items
            self.after(0, self._render_failed)
            self._set_status(f"Da tai: {len(items)} video loi")
        except Exception as e:
            self.after(0, lambda: self._log(self._f_log, f"Loi load failed: {e}"))

    def _render_failed(self):
        for w in self._f_scroll.winfo_children():
            w.destroy()
        self._failed_checks = []
        items = self._failed_items
        self._f_count.configure(text=f"{len(items)} video trong danh sach loi/Shop")
        if not items:
            ctk.CTkLabel(self._f_scroll, text="Khong co video nao trong danh sach loi!",
                         text_color="#00b894").pack(pady=20)
            return
        for item in items:
            var = ctk.BooleanVar(value=True)
            self._failed_checks.append(var)
            self._make_failed_row(item, var)

    def _make_failed_row(self, item, var):
        row = ctk.CTkFrame(self._f_scroll, fg_color=("#e8e8e8", "#252535"), corner_radius=6)
        row.pack(fill="x", padx=4, pady=2)
        row.columnconfigure(2, weight=1)
        ctk.CTkCheckBox(row, variable=var, text="", width=24).grid(row=0, column=0, padx=6, pady=4)
        is_shop = item.get("isShop") or "Shop" in str(item.get("errorMessage", ""))
        tag = "SHOP" if is_shop else item.get("errorCode", "ERR")[:8]
        tag_col = "#f0ad4e" if is_shop else "#e74c3c"
        ctk.CTkLabel(row, text=tag, width=65, font=ctk.CTkFont("Segoe UI", 9, "bold"),
                     text_color="white", fg_color=tag_col, corner_radius=4).grid(row=0, column=1, padx=4)
        info = f"@{item.get('author', 'tiktok')}  {item.get('title', '')[:45]}"
        ctk.CTkLabel(row, text=info, font=ctk.CTkFont("Segoe UI", 10), anchor="w"
                     ).grid(row=0, column=2, padx=4, sticky="ew")
        ctk.CTkLabel(row, text=item.get("id", ""), font=ctk.CTkFont("Consolas", 9),
                     text_color="#888888").grid(row=0, column=3, padx=8)

    def _reload_downloaded(self):
        try:
            ext = self._get_ext()
            src = self._src_var.get() if hasattr(self, "_src_var") else "Favorites"
            items = []
            videos = ext._decode_file(ext.files["videos"], ext.var_names["videos"]) or {}
            texts  = ext._decode_file(ext.files["texts"], ext.var_names["texts"]) or {}

            if src in ("Favorites", "Ca hai"):
                dbb = ext._decode_file(ext.files["bookmarked"], ext.var_names["bookmarked"])
                if dbb and isinstance(dbb, dict):
                    for vid_id in dbb.get("downloaded", []):
                        v = videos.get(vid_id, {})
                        items.append({"id": vid_id, "category": "b", "author_id": v.get("authorId", ""),
                                      "title": texts.get(vid_id, "")[:55], "source": "Favorites"})

            if src in ("Likes", "Ca hai"):
                dbl = ext._decode_file(ext.files["likes"], ext.var_names["likes"])
                if dbl and isinstance(dbl, dict):
                    likes_obj = dbl.get("likes", {})
                    for vid_id in likes_obj.get("downloaded", []):
                        v = videos.get(vid_id, {})
                        items.append({"id": vid_id, "category": "l", "author_id": v.get("authorId", ""),
                                      "title": texts.get(vid_id, "")[:55], "source": "Likes"})

            self._downloaded_items = items
            self.after(0, self._render_downloaded)
            self._set_status(f"Da tai: {len(items)} video Extension")
        except Exception as e:
            self.after(0, lambda: self._log(self._d_log, f"Loi load downloaded: {e}"))

    def _render_downloaded(self):
        for w in self._d_scroll.winfo_children():
            w.destroy()
        self._downloaded_checks = []
        items = self._downloaded_items
        self._d_count.configure(text=f"{len(items)} video Extension da tai")
        if not items:
            ctk.CTkLabel(self._d_scroll, text="Chua co video nao.",
                         text_color="#888888").pack(pady=20)
            return
        for item in items:
            var = ctk.BooleanVar(value=False)
            self._downloaded_checks.append(var)
            self._make_dl_row(item, var)

    def _make_dl_row(self, item, var):
        row = ctk.CTkFrame(self._d_scroll, fg_color=("#e8e8e8", "#252535"), corner_radius=6)
        row.pack(fill="x", padx=4, pady=2)
        row.columnconfigure(2, weight=1)
        ctk.CTkCheckBox(row, variable=var, text="", width=24).grid(row=0, column=0, padx=6, pady=4)
        src = item.get("source", "")
        col = "#00b894" if src == "Favorites" else "#6c5ce7"
        ctk.CTkLabel(row, text=src, width=72, font=ctk.CTkFont("Segoe UI", 9, "bold"),
                     text_color="white", fg_color=col, corner_radius=4).grid(row=0, column=1, padx=4)
        title = item.get("title", "") or "(Khong co tieu de)"
        ctk.CTkLabel(row, text=title, font=ctk.CTkFont("Segoe UI", 10), anchor="w"
                     ).grid(row=0, column=2, padx=4, sticky="ew")
        ctk.CTkLabel(row, text=item.get("id", ""), font=ctk.CTkFont("Consolas", 9),
                     text_color="#888888").grid(row=0, column=3, padx=8)

    # ==================== ACTIONS ====================
    def _sel_all(self, checks, val):
        for v in checks: v.set(val)

    def _download_selected_failed(self):
        sel = [self._failed_items[i] for i, v in enumerate(self._failed_checks) if v.get()]
        if not sel: return messagebox.showinfo("Chua chon", "Hay chon it nhat 1 video!")
        self._run_failed(sel)

    def _download_all_failed(self):
        self._run_failed(list(self._failed_items))

    def _run_failed(self, items):
        if self._is_downloading:
            return messagebox.showwarning("Dang tai", "Dung tien trinh hien tai truoc!")
        self._stop_flag.clear()
        self._is_downloading = True
        self._set_dl_state(True)
        threading.Thread(target=self._worker_failed, args=(items,), daemon=True).start()

    def _worker_failed(self, items):
        ext = self._get_ext()
        s = load_settings()
        rl = s.get("rate_limit", "1M")
        dl = HybridDownloader(
            output_dir=s.get("output_dir", "downloads"),
            db_path=str(Path(s.get("output_dir", "downloads")) / "video_index.db"),
            rate_limit=rl, max_retries=int(s.get("retries", 3)))
        total = len(items)
        ok = 0
        remaining = []
        for i, item in enumerate(items):
            if self._stop_flag.is_set():
                remaining.extend(items[i:]); break
            vid_id = str(item.get("id", "")).strip()
            author  = item.get("author", "")
            auth_id = item.get("authorId", "")
            cat     = item.get("category", "b")
            title   = item.get("title", "")
            cover   = item.get("cover", "")
            url = item.get("url") or f"https://www.tiktok.com/@{author}/video/{vid_id}"
            self.after(0, lambda i=i, n=total, v=vid_id, a=author: (
                self._set_status(f"[{i+1}/{n}] Dang tai: {v} (@{a})"),
                self._f_prog.set(i / n)
            ))
            self.after(0, lambda m=f"[{i+1}/{total}] {vid_id} (@{author})": self._log(self._f_log, m))
            vp, cp = ext.get_target_media_paths(vid_id, cat, auth_id)
            if vp.exists() and vp.stat().st_size > 100_000:
                ext.register_downloaded_video(vid_id, auth_id, author, cat, title)
                self.after(0, lambda: self._log(self._f_log, "  Da co file → Dong bo DB"))
                ok += 1; continue
            try:
                res = dl.download_to_custom_path(url, vp, cp, cover)
                if res.success:
                    sz = f"{vp.stat().st_size//(1024*1024)}MB" if vp.exists() else "?"
                    v2 = res.video
                    ext.register_downloaded_video(vid_id, auth_id or (v2.author_id if v2 else ""),
                                                  author or (v2.author if v2 else ""), cat,
                                                  title or (v2.title if v2 else ""),
                                                  v2.create_time if v2 else 0, sz)
                    ok += 1
                    self.after(0, lambda s=sz: self._log(self._f_log, f"  Thanh cong! ({s})"))
                else:
                    remaining.append(item)
                    self.after(0, lambda e=res.error: self._log(self._f_log, f"  That bai: {e}"))
            except Exception as e:
                remaining.append(item)
                self.after(0, lambda e=str(e): self._log(self._f_log, f"  Exception: {e}"))

        # Merge: keep items not in our batch unchanged
        other = [x for x in self._failed_items if x not in items]
        ext.save_failed_queue(remaining + other)
        self.after(0, lambda: (
            self._f_prog.set(1.0),
            self._set_status(f"Xong: {ok}/{total} | Con loi: {len(remaining)}"),
            self._log(self._f_log, f"\n=== {ok}/{total} thanh cong | {len(remaining)} con loi ==="),
            self._finish_dl(), self._reload_failed()
        ))

    def _delete_selected_failed(self):
        ids = {self._failed_items[i].get("id") for i, v in enumerate(self._failed_checks) if v.get()}
        if not ids: return messagebox.showinfo("Chua chon", "Chon it nhat 1 video!")
        if not messagebox.askyesno("Xac nhan", f"Xoa {len(ids)} video khoi danh sach loi?"): return
        ext = self._get_ext()
        ext.save_failed_queue([x for x in self._failed_items if x.get("id") not in ids])
        self._log(self._f_log, f"Da xoa {len(ids)} video khoi danh sach loi.")
        self._reload_failed()

    def _redownload_selected(self):
        sel = [self._downloaded_items[i] for i, v in enumerate(self._downloaded_checks) if v.get()]
        if not sel: return messagebox.showinfo("Chua chon", "Chon it nhat 1 video!")
        self._run_redownload(sel)

    def _redownload_all(self):
        self._run_redownload(list(self._downloaded_items))

    def _run_redownload(self, items):
        if self._is_downloading:
            return messagebox.showwarning("Dang tai", "Dung tien trinh hien tai truoc!")
        out = self._out_var.get() if hasattr(self, "_out_var") else self.settings.get("output_dir", "downloads")
        if not out: return messagebox.showerror("Thieu thu muc", "Chon thu muc luu video!")
        self._stop_flag.clear()
        self._is_downloading = True
        self._set_dl_state(True)
        threading.Thread(target=self._worker_redownload, args=(items, out), daemon=True).start()

    def _worker_redownload(self, items, out_dir):
        s = load_settings()
        dl = HybridDownloader(output_dir=out_dir,
                              db_path=str(Path(out_dir) / "video_index.db"),
                              rate_limit=s.get("rate_limit", "1M"),
                              max_retries=int(s.get("retries", 3)))
        total = len(items); ok = 0
        for i, item in enumerate(items):
            if self._stop_flag.is_set(): break
            vid_id = str(item.get("id", "")).strip()
            src = item.get("source", "Favorites")
            url = f"https://www.tiktok.com/video/{vid_id}"
            self.after(0, lambda i=i, n=total, v=vid_id: (
                self._set_status(f"[{i+1}/{n}] Tai lai: {v}"),
                self._d_prog.set(i / n)
            ))
            self.after(0, lambda m=f"[{i+1}/{total}] {vid_id} ({src})": self._log(self._d_log, m))
            base = Path(out_dir) / ("Likes" if src == "Likes" else "Favorites")
            vp = base / "videos" / f"{vid_id}.mp4"
            cp = base / "covers" / f"{vid_id}.jpg"
            vp.parent.mkdir(parents=True, exist_ok=True)
            cp.parent.mkdir(parents=True, exist_ok=True)
            if vp.exists() and vp.stat().st_size > 100_000:
                ok += 1
                self.after(0, lambda: self._log(self._d_log, "  Da co file → Bo qua"))
                continue
            try:
                res = dl.download_to_custom_path(url, vp, cp)
                if res.success:
                    ok += 1
                    sz = f"{vp.stat().st_size//(1024*1024)}MB" if vp.exists() else "?"
                    self.after(0, lambda s=sz: self._log(self._d_log, f"  Thanh cong! ({s})"))
                else:
                    self.after(0, lambda e=res.error: self._log(self._d_log, f"  That bai: {e}"))
            except Exception as e:
                self.after(0, lambda e=str(e): self._log(self._d_log, f"  Exception: {e}"))
        self.after(0, lambda: (
            self._d_prog.set(1.0),
            self._set_status(f"Tai lai xong: {ok}/{total}"),
            self._log(self._d_log, f"\n=== {ok}/{total} thanh cong ==="),
            self._finish_dl()
        ))

    # ==================== STOP / STATE ====================
    def _stop_download(self):
        self._stop_flag.set()
        self._set_status("Dung... (hoan tat video hien tai)")
        self._log(self._f_log, "Lenh dung da gui, cho video hien tai hoan tat...")
        self._log(self._d_log, "Lenh dung da gui...")

    def _set_dl_state(self, dl: bool):
        for btn in [self._btn_dl_sel, self._btn_dl_all, self._btn_re_sel, self._btn_re_all]:
            btn.configure(state="disabled" if dl else "normal")
        for btn in [self._btn_stop_f, self._btn_stop_d]:
            btn.configure(state="normal" if dl else "disabled")

    def _finish_dl(self):
        self._is_downloading = False
        self._set_dl_state(False)

    # ==================== HELPERS ====================
    def _set_status(self, txt: str):
        self.after(0, lambda: self._status_lbl.configure(text=txt))

    def _log(self, widget: ctk.CTkTextbox, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        widget.configure(state="normal")
        widget.insert("end", f"[{ts}] {msg}\n")
        widget.see("end")
        widget.configure(state="disabled")

    def _save_settings(self):
        self.settings.update({
            "ext_data_path": self._s_ext.get(),
            "output_dir": self._s_out.get(),
            "rate_limit": self._s_rate.get(),
            "retries": int(self._s_retry.get() or "3"),
        })
        if hasattr(self, "_w_user") and self._w_user.get().strip():
            self.settings["github_user"] = self._w_user.get().strip()
        if hasattr(self, "_w_repo") and self._w_repo.get().strip():
            self.settings["github_repo"] = self._w_repo.get().strip()
        if hasattr(self, "_w_token") and self._w_token.get().strip():
            self.settings["enc_gh_token"] = mask_token(self._w_token.get().strip())
        save_settings(self.settings)
        messagebox.showinfo("Da luu", "Cap nhat cai dat thanh cong!\nLam moi du lieu de ap dung.")


def launch_gui():
    app = TikTokDownloadManagerApp()
    app.mainloop()


if __name__ == "__main__":
    launch_gui()
