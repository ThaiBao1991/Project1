"""
SKILL TEMPLATE: Python Auto-Install Libraries (Windows Safe + Auto-Heal + Clean Exit)
Dung: Copy doan nay vao dau bat ky file Python Desktop (Tkinter/CustomTkinter) nao,
TRUOC tat ca cac lenh import thu vien ben ngoai.
"""

import os
import sys
import site
import shutil
import importlib
import importlib.metadata
import subprocess
import tkinter as tk

# Cau hinh UTF-8 an toan tren Windows console (bo qua neu chay bang pythonw)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ─── Khai bao thu vien can thiet ─────────────────────────────────────────────
# KEY   = ten module dung trong importlib.import_module()
# VALUE = ten package pip (co the kem version: 'requests>=2.31.0')
REQUIRED_PACKAGES = {
    "customtkinter": "customtkinter>=5.2.0",
    "PIL": "Pillow>=10.0.0",
    "requests": "requests>=2.31.0",
    # Vi du Crypto (ket hop PACKAGE_CONFLICTS + FALLBACK_PACKAGES ben duoi):
    # "Crypto.Cipher": "pycryptodome>=3.19.0",
    #
    # Vi du module nap dong trong runtime (khong import o dau file):
    # "pyxlsb": "pyxlsb>=1.0.10",
    #
    # Vi du Google API:
    # "google.auth": "google-auth>=2.27.0",
}

# Cac goi de xung dot ten thu muc hoa/thuong tren Windows (VD: crypto vs Crypto)
PACKAGE_CONFLICTS = {
    "Crypto": ["crypto", "pycrypto"],
}

# Goi du phong khong trung namespace neu goi chinh bi khoa quyen o thu muc he thong
FALLBACK_PACKAGES = {
    "Crypto.Cipher": ("Cryptodome.Cipher", "pycryptodomex>=3.19.0"),
}

# Ma thoat rieng khi user chu dong dong hop thoai thieu thu vien (de file .bat khong pause thua)
EXIT_MISSING_LIB_DIALOG = 2


def _pip_base_name(pip_spec):
    for sep in ("==", ">=", "<=", "~=", "!=", ">", "<", "["):
        if sep in pip_spec:
            pip_spec = pip_spec.split(sep, 1)[0]
    return pip_spec.strip()


def _quote_pip_spec(spec):
    """Boc ngoac kep de tranh loi CMD/PowerShell hieu nham '>' thanh chuyen huong file."""
    if any(ch in spec for ch in '<>=!~ []"'):
        return f'"{spec}"'
    return spec


def _can_import_requirement(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        fallback = FALLBACK_PACKAGES.get(module_name)
        if fallback:
            try:
                importlib.import_module(fallback[0])
                return True
            except ImportError:
                return False
        return False


def _refresh_import_paths(in_venv):
    if not in_venv:
        try:
            user_site = site.getusersitepackages()
            if user_site and os.path.isdir(user_site) and user_site not in sys.path:
                sys.path.append(user_site)
        except Exception:
            pass
    importlib.invalidate_caches()


def _collect_site_dirs():
    dirs = []
    try:
        user_site = site.getusersitepackages()
        if user_site:
            dirs.append(user_site)
    except Exception:
        pass
    try:
        dirs.extend(site.getsitepackages())
    except Exception:
        pass
    for p in sys.path:
        if p and os.path.basename(p).lower() == "site-packages":
            dirs.append(p)
    seen = set()
    result = []
    for d in dirs:
        norm = os.path.normcase(os.path.abspath(d))
        if norm not in seen and os.path.isdir(d):
            seen.add(norm)
            result.append(d)
    return result


def _heal_windows_package_conflict(module_name, pip_spec):
    """Tu phat hien & sua loi xung dot goi / sai chu hoa-thuong tren Windows."""
    if sys.platform != "win32":
        return False

    top_pkg = module_name.split(".")[0]
    conflict_pkgs = list(PACKAGE_CONFLICTS.get(top_pkg, []))
    target_base = _pip_base_name(pip_spec)

    found_conflicts = []
    for pkg in conflict_pkgs:
        try:
            importlib.metadata.distribution(pkg)
            found_conflicts.append(pkg)
        except importlib.metadata.PackageNotFoundError:
            pass

    wrong_case_dirs = []
    for sp in _collect_site_dirs():
        try:
            for entry in os.listdir(sp):
                full_path = os.path.join(sp, entry)
                if os.path.isdir(full_path) and entry.lower() == top_pkg.lower() and entry != top_pkg:
                    wrong_case_dirs.append(full_path)
        except OSError:
            pass

    if not found_conflicts and not wrong_case_dirs:
        return False

    print(
        f"[*] Phat hien xung dot goi/chu hoa-thuong cho '{top_pkg}' "
        f"(conflicts={found_conflicts}, dirs={wrong_case_dirs}). Dang tu dong sua..."
    )

    to_uninstall = []
    for pkg in found_conflicts + [target_base]:
        if pkg not in to_uninstall:
            try:
                importlib.metadata.distribution(pkg)
                to_uninstall.append(pkg)
            except importlib.metadata.PackageNotFoundError:
                pass

    if to_uninstall:
        subprocess.run(
            [sys.executable, "-m", "pip", "uninstall", "-y", *to_uninstall],
            check=False,
        )

    for bad_dir in wrong_case_dirs:
        if os.path.exists(bad_dir):
            shutil.rmtree(bad_dir, ignore_errors=True)

    importlib.invalidate_caches()
    return True


def _show_manual_install_dialog(missing_packages, error_detail=""):
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    user_flag = "" if in_venv else "--user "
    quoted_pkgs = " ".join(_quote_pip_spec(p) for p in missing_packages)
    cmd = f"python -m pip install {user_flag}{quoted_pkgs}"
    try:
        root = tk.Tk()
        root.withdraw()
        err_win = tk.Toplevel(root)
        err_win.title("Loi Thieu Thu Vien")
        err_win.geometry("640x360")

        def close_dialog():
            try:
                root.quit()
            except Exception:
                pass
            try:
                root.destroy()
            except Exception:
                pass

        err_win.protocol("WM_DELETE_WINDOW", close_dialog)

        tk.Label(
            err_win,
            text="Ung dung thieu thu vien can thiet va khong the tu cai dat.",
            fg="red",
            font=("Arial", 11, "bold"),
        ).pack(pady=(12, 4))

        if error_detail:
            tk.Label(
                err_win,
                text=f"Chi tiet: {str(error_detail)[:220]}",
                fg="#555555",
                font=("Arial", 9),
                wraplength=600,
                justify="left",
            ).pack(pady=(0, 6))

        tk.Label(
            err_win,
            text="Vui long copy lenh duoi day (da boc ngoac kep) va dan vao Terminal/CMD:",
            font=("Arial", 10),
        ).pack(pady=4)

        txt = tk.Text(err_win, height=4, width=72, font=("Consolas", 10))
        txt.pack(pady=8, padx=12)
        txt.insert(tk.END, cmd)
        txt.config(state="disabled")

        btn_frame = tk.Frame(err_win)
        btn_frame.pack(pady=10)

        copy_status = tk.Label(err_win, text="", fg="green", font=("Arial", 9))
        copy_status.pack()

        def copy_cmd():
            err_win.clipboard_clear()
            err_win.clipboard_append(cmd)
            err_win.update()
            copy_status.config(text="Da sao chep lenh vao clipboard!")

        tk.Button(btn_frame, text="Sao chep lenh", command=copy_cmd, width=15).pack(side=tk.LEFT, padx=8)
        tk.Button(btn_frame, text="Thoat ung dung", command=close_dialog, width=15).pack(side=tk.LEFT, padx=8)

        root.mainloop()
    except tk.TclError:
        print(f"[!] Khong the tu cai dat thu vien ({error_detail}). Chay thu cong: {cmd}", file=sys.stderr)


def check_and_install_packages():
    missing_items = [
        (mod, pip_spec)
        for mod, pip_spec in REQUIRED_PACKAGES.items()
        if not _can_import_requirement(mod)
    ]

    if not missing_items:
        return  # Tat ca da co, khong lam gi

    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    pip_base_cmd = [sys.executable, "-m", "pip", "install"]
    if not in_venv:
        pip_base_cmd.append("--user")

    missing_specs = [pip_spec for _, pip_spec in missing_items]
    print(f"[*] Dang tu dong cai dat thu vien con thieu: {', '.join(missing_specs)}")

    try:
        for mod, pip_spec in missing_items:
            _heal_windows_package_conflict(mod, pip_spec)

        subprocess.check_call(pip_base_cmd + missing_specs)
        _refresh_import_paths(in_venv)

        still_missing = []
        for mod, pip_spec in missing_items:
            if _can_import_requirement(mod):
                continue
            fallback = FALLBACK_PACKAGES.get(mod)
            if fallback:
                fb_mod, fb_pip = fallback
                print(f"[*] '{mod}' van chua import duoc, thu goi du phong: {fb_pip}")
                try:
                    subprocess.check_call(pip_base_cmd + [fb_pip])
                    _refresh_import_paths(in_venv)
                    importlib.import_module(fb_mod)
                    continue
                except Exception:
                    pass
            still_missing.append(pip_spec)

        if still_missing:
            raise ImportError(f"Da chay pip nhung van khong the import: {', '.join(still_missing)}")

        print("[*] Cai dat thu vien thanh cong!")
    except Exception as exc:
        _show_manual_install_dialog(missing_specs, exc)
        sys.exit(EXIT_MISSING_LIB_DIALOG)


# GOI NGAY SAU KHI KHAI BAO -- truoc tat ca import thu vien ngoai
# check_and_install_packages()

# --- Mau thoat sach Tkinter + Python + CMD ---
# def main():
#     root = tk.Tk()
#     app = App(root)
#
#     def on_close():
#         try:
#             root.quit()
#         except Exception:
#             pass
#         try:
#             root.destroy()
#         except Exception:
#             pass
#
#     root.protocol("WM_DELETE_WINDOW", on_close)
#     try:
#         root.mainloop()
#     except KeyboardInterrupt:
#         on_close()
#     finally:
#         try:
#             if root.winfo_exists():
#                 root.destroy()
#         except Exception:
#             pass
#     sys.exit(0)
