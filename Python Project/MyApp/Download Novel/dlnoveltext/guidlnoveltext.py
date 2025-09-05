import json
from pathlib import Path
from urllib.parse import urlparse
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .functiondlnoveltext import test_scrape  # placeholder test function

DATA_DIR = Path.cwd() / "DataCollection" / "DataNovel"
DATA_DIR.mkdir(parents=True, exist_ok=True)
SETTINGS_FILE = DATA_DIR / "settings.json"
SITES_FILE = DATA_DIR / "saved_sites.json"

def load_json(path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default

def save_json(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

class NovelScraperGUI:
    def __init__(self, root=None):
        self.root = root or tk.Tk()
        self.root.title("Novel Scraper")
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        frm = ttk.Frame(self.root, padding=8)
        frm.pack(fill="both", expand=True)

        # Saved sites (combobox) - show base domains only, supports typing
        ttk.Label(frm, text="Saved sites:").grid(row=0, column=0, sticky="w")
        self.site_var = tk.StringVar()
        self.site_combo = ttk.Combobox(frm, textvariable=self.site_var)
        self.site_combo.grid(row=0, column=1, columnspan=3, sticky="ew", padx=4, pady=2)
        self.site_combo.bind("<<ComboboxSelected>>", self._on_site_selected)

        # URL list of chapters
        ttk.Label(frm, text="Chapter list URL:").grid(row=1, column=0, sticky="w")
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(frm, textvariable=self.url_var)
        self.url_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=4, pady=2)
        self.url_entry.bind("<FocusOut>", lambda e: self._autogen_filename())

        ttk.Button(frm, text="Auto filename", command=self._autogen_filename).grid(row=1, column=3, padx=4)

        # Generated filename + browse
        ttk.Label(frm, text="Save filename (.html):").grid(row=2, column=0, sticky="w")
        self.filename_var = tk.StringVar()
        self.filename_entry = ttk.Entry(frm, textvariable=self.filename_var)
        self.filename_entry.grid(row=2, column=1, sticky="ew", padx=4, pady=2)
        ttk.Button(frm, text="Browse...", command=self._browse_save).grid(row=2, column=2, padx=4)

        # Username / Password (for sites requiring login)
        ttk.Label(frm, text="Username:").grid(row=3, column=0, sticky="w")
        self.user_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.user_var).grid(row=3, column=1, sticky="ew", padx=4)

        ttk.Label(frm, text="Password:").grid(row=3, column=2, sticky="w")
        self.pass_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.pass_var, show="*").grid(row=3, column=3, sticky="ew", padx=4)

        # Test / Save buttons
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=4, column=0, columnspan=4, pady=8, sticky="ew")
        self.use_saved_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(btn_frame, text="Test using saved site (Basic settings)", variable=self.use_saved_var).pack(side="left", padx=4)

        ttk.Button(btn_frame, text="Test", command=self._on_test).pack(side="right", padx=4)
        ttk.Button(btn_frame, text="Save settings", command=self._on_save).pack(side="right", padx=4)

        # Status
        self.status = tk.StringVar()
        ttk.Label(frm, textvariable=self.status, foreground="blue").grid(row=5, column=0, columnspan=4, sticky="w")

        # configure grid weights
        frm.columnconfigure(1, weight=1)
        frm.columnconfigure(3, weight=1)

    def _load_settings(self):
        self.settings = load_json(SETTINGS_FILE, {})
        self.saved_sites = load_json(SITES_FILE, [])
        # populate combobox
        self.site_combo["values"] = self.saved_sites
        # load last settings
        if self.settings:
            self.site_var.set(self.settings.get("site", ""))
            self.url_var.set(self.settings.get("last_url", ""))
            self.filename_var.set(self.settings.get("filename", ""))
            self.user_var.set(self.settings.get("username", ""))
            self.pass_var.set(self.settings.get("password", ""))
        else:
            # defaults
            self.filename_var.set("index.html")

    def _on_site_selected(self, _ev=None):
        # when a saved site selected, set status and optionally fill url with that domain
        site = self.site_var.get()
        self.status.set(f"Selected site {site}")

    def _autogen_filename(self):
        url = self.url_var.get().strip()
        if not url:
            return
        parsed = urlparse(url)
        path = parsed.path.rstrip("/")
        if path and path != "/":
            slug = path.split("/")[-1]
        else:
            slug = parsed.netloc
        filename = slug + ".html"
        self.filename_var.set(filename)

    def _browse_save(self):
        initial = str(DATA_DIR / self.filename_var.get())
        fp = filedialog.asksaveasfilename(defaultextension=".html", initialfile=Path(initial).name, initialdir=str(DATA_DIR))
        if fp:
            p = Path(fp)
            # Keep relative to project if inside, else absolute
            try:
                p = p.relative_to(Path.cwd())
                self.filename_var.set(str(p))
            except Exception:
                self.filename_var.set(str(p))

    def _on_save(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Warning", "Please enter chapter list URL.")
            return
        parsed = urlparse(url)
        if not parsed.scheme:
            messagebox.showwarning("Warning", "Please enter a valid URL (include http/https).")
            return
        base = f"{parsed.scheme}://{parsed.netloc}"
        # update saved sites list (keep unique)
        if base not in self.saved_sites:
            self.saved_sites.insert(0, base)
            self.site_combo["values"] = self.saved_sites
            save_json(SITES_FILE, self.saved_sites)

        # save settings
        self.settings = {
            "site": base,
            "last_url": url,
            "filename": self.filename_var.get(),
            "username": self.user_var.get(),
            "password": self.pass_var.get()
        }
        save_json(SETTINGS_FILE, self.settings)
        self.status.set("Settings saved.")
        messagebox.showinfo("Saved", f"Settings saved to {SETTINGS_FILE}")

    def _on_test(self):
        # Test should use saved site stored in basic settings if option checked
        if self.use_saved_var.get() and self.settings:
            url = self.settings.get("last_url", "")
            username = self.settings.get("username", "")
            password = self.settings.get("password", "")
        else:
            url = self.url_var.get().strip()
            username = self.user_var.get()
            password = self.pass_var.get()

        if not url:
            messagebox.showwarning("Warning", "No URL provided for test.")
            return

        self.status.set("Testing...")
        self.root.update_idletasks()
        ok, info = test_scrape(url, username, password)
        if ok:
            messagebox.showinfo("Test result", f"Success: {info}")
            self.status.set("Test success.")
        else:
            messagebox.showerror("Test result", f"Failed: {info}")
            self.status.set("Test failed.")

if __name__ == "__main__":
    NovelScraperGUI().root.mainloop()