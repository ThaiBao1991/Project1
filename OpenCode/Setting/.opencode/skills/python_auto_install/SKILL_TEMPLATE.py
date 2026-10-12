"""
SKILL TEMPLATE: Python Auto-Install Libraries
Dung: Copy doan nay vao dau bat ky file Python Desktop nao.
"""

import sys
import subprocess
import tkinter as tk

# ─── Khai bao thu vien can thiet ─────────────────────────────────────────────
# KEY   = ten module dung trong __import__() -- ten import trong code
# VALUE = ten package pip -- co the kem version: 'requests>=2.31.0'
REQUIRED_PACKAGES = {
    'customtkinter': 'customtkinter>=5.2.0',
    'PIL':           'Pillow>=10.0.0',
    'requests':      'requests>=2.31.0',
    # Them thu vien moi vao day:
    # 'module_name': 'pip_package_name>=version',
    #
    # Vi du TTS:
    # 'pyttsx3': 'pyttsx3>=2.90',
    # 'gtts':    'gTTS>=2.3.2',
    # 'pygame':  'pygame>=2.5.0',
    #
    # Vi du Google API:
    # 'google.auth':        'google-auth>=2.27.0',
    # 'google_auth_oauthlib': 'google-auth-oauthlib>=1.2.0',
    # 'googleapiclient':    'google-api-python-client>=2.118.0',
}

def check_and_install_packages():
    missing = []
    for module_name, pip_name in REQUIRED_PACKAGES.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(pip_name)

    if not missing:
        return  # tat ca da co, khong lam gi

    print(f"[*] Dang tu dong cai dat thu vien con thieu: {', '.join(missing)}")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", *missing])
        print("[*] Cai dat thanh cong!")
    except Exception:
        # Tu cai that bai --> hien hop thoai huong dan thu cong
        root = tk.Tk()
        root.withdraw()
        err_win = tk.Toplevel(root)
        err_win.title("Loi Thieu Thu Vien")
        err_win.geometry("580x300")

        tk.Label(
            err_win,
            text="Ung dung thieu thu vien can thiet va khong the tu cai dat.",
            fg="red", font=("Arial", 11, "bold")
        ).pack(pady=10)
        tk.Label(
            err_win,
            text="Vui long copy lenh duoi day va dan vao Terminal/CMD:",
            font=("Arial", 10)
        ).pack(pady=5)

        txt = tk.Text(err_win, height=4, width=65, font=("Consolas", 11))
        txt.pack(pady=10)
        cmd = "python -m pip install --user " + " ".join(missing)
        txt.insert(tk.END, cmd)
        txt.config(state="disabled")

        tk.Button(err_win, text="Thoat ung dung", command=root.destroy, width=15).pack(pady=15)
        root.mainloop()
        sys.exit(1)

# GOI NGAY SAU KHI KHAI BAO -- truoc tat ca import thu vien ngoai
check_and_install_packages()

# --- Import thu vien binh thuong sau day ---
# import customtkinter as ctk
# import requests
# ...
