---
name: python_auto_install
description: >
  Pattern tu dong kiem tra, tu sua xung dot (Windows NTFS case-collision nhu crypto vs Crypto),
  va cai dat thu vien Python khi khoi dong ung dung Desktop (Tkinter/CustomTkinter), kem chuan
  thoat sach Python + CMD va file .bat click-la-chay.
  Trigger: khi can them thu vien moi vao du an Python co GUI, xu ly ImportError / ModuleNotFoundError
  dù da pip install, tao file .bat khoi chay, hoac xu ly loi dong cua so nhung Python/CMD van chay.
---

# Skill: Python Auto-Install Libraries & Clean Windows Launcher

## Muc dich

Dam bao ung dung Python Desktop luon tu khoi chay thanh cong ngay lan dau tren moi may Windows:
- Khong yeu cau nguoi dung cai `pip` thu cong.
- **Tu dong sua loi xung dot goi / chu hoa-thuong tren Windows** (dien hinh: `crypto` vs `pycryptodome` / `Crypto`).
- **Boc ngoac kep chuan** trong lenh cai thu cong de tranh loi chuyen huong file `>` trong CMD/PowerShell.
- **Thoat sach triet de** ca Tkinter, tien trinh Python va cua so CMD khi dong app.

---

## Pattern chuan (Copy-paste vao dau file Python)

Xem file `SKILL_TEMPLATE.py` trong cung thu muc.

---

## Quy tac khai bao REQUIRED_PACKAGES / PACKAGE_CONFLICTS / FALLBACK_PACKAGES

| Tinh huong | Cach khai bao |
|---|---|
| Module import trung ten pip | `"requests": "requests>=2.31.0"` |
| Module khac ten pip | `"PIL": "Pillow>=10.0.0"` |
| Module co namespace dai | `"google.auth": "google-auth>=2.27.0"` |
| Package co extras | `"qrcode": "qrcode[pil]>=7.4.2"` |
| Module nap dong trong runtime (khong import o dau file) | Van phai khai bao! VD: `"pyxlsb": "pyxlsb>=1.0.10"` cho `pd.read_excel(..., engine="pyxlsb")` |
| Goi de xung dot ten hoa/thuong tren Windows | Dung `PACKAGE_CONFLICTS = {"Crypto": ["crypto", "pycrypto"]}` + `FALLBACK_PACKAGES = {"Crypto.Cipher": ("Cryptodome.Cipher", "pycryptodomex>=3.19.0")}` |

> NOTE: KEY trong `REQUIRED_PACKAGES` phai la chuoi ma `importlib.import_module(KEY)` thanh cong khi da cai.
> Sai: `'google-auth'` (dau `-`) -> Dung: `'google.auth'`

---

## Cac bay thuc te tren Windows & cach phong tranh bat buoc

### 1. Bay Windows NTFS Case-Collision (`crypto` vs `Crypto`)
- **Hien tuong**: `pip install pycryptodome` bao thanh cong (`Requirement already satisfied`), nhung `from Crypto.Cipher import AES` van bao `ModuleNotFoundError: No module named 'Crypto'`.
- **Nguyen nhan**: Tren may tung cai nham goi cu `crypto` (tao thu muc chu thuong `site-packages\crypto\`). Windows NTFS khong phan biet hoa/thuong nen `pip` giai nen `pycryptodome` vao luon thu muc `crypto\` chu thuong. Trong khi do bo `import` cua Python tren Windows lai **phan biet hoa/thuong** (`Crypto` != `crypto`).
- **Cach xu ly tu dong (Auto-Heal)**:
  1. Quet cac thu muc `site-packages` (user & system) tim thu muc co `entry.lower() == top_pkg.lower()` nhung `entry != top_pkg`, va kiem tra `importlib.metadata.distribution()` cho cac goi xung dot (`crypto`, `pycrypto`).
  2. Go bo goi xung dot + goi bi cai lech (`pip uninstall -y crypto pycrypto pycryptodome`).
  3. Xoa thu muc sai chu hoa (`shutil.rmtree(bad_dir, ignore_errors=True)`).
  4. Cai lai sach `pycryptodome` + goi `importlib.invalidate_caches()` + kiem tra import lai.
  5. **Fallback chong khoa quyen**: Neu thu muc `crypto\` nam o system `site-packages` khong co quyen Admin de xoa, tu dong cai **`pycryptodomex`** va import qua `Cryptodome` (`try: from Crypto... except ImportError: from Cryptodome...`).

### 2. Bay thieu ngoac kep `>=` trong lenh CMD / PowerShell
- **Sai**: `python -m pip install --user pycryptodome>=3.19.0`
  -> Khi dan vao CMD, ky tu `>` bi hieu la **chuyen huong xuat file**, tao ra file rac ten `3.19.0` trong thu muc hien tai va bo qua rang buoc phien ban!
- **Dung**: Luon boc ngoac kep cho moi spec co `<`, `>`, `=`, `!`, `~`, `[`, `]`, hoac khoang trang:
  `python -m pip install --user "pycryptodome>=3.19.0"`

### 3. Bay `--user` trong Virtualenv & First-Run `sys.path`
- Trong `venv` (`sys.prefix != sys.base_prefix`), `pip install --user` se bao loi. Chi truyen `--user` khi **khong** o trong venv.
- Tren may moi chua tung co user `site-packages`, thu muc nay chua co trong `sys.path` luc Python khoi dong. Sau khi `pip install --user` thanh cong, **bat buoc** them `site.getusersitepackages()` vao `sys.path` (neu ton tai) va goi `importlib.invalidate_caches()` de import duoc ngay trong lan chay dau tien.

### 4. Bay dong cua so nhung Python & CMD van chay ngam
- **Trong Tkinter (`main()` va hop thoai loi)**:
  - Luon gan `WM_DELETE_WINDOW` goi **ca hai** `root.quit()` (dung `mainloop`) va `root.destroy()` (giai phong Tcl/Tk).
  - Ket thuc `main()` bang `sys.exit(0)` (va bat `KeyboardInterrupt`).
  - Khi nguoi dung chu dong dong hop thoai bao thieu thu vien, thoat bang ma rieng `EXIT_MISSING_LIB_DIALOG = 2` (khac ma crash `1`).
- **Trong file `.bat` khoi chay (phai luu CRLF `\r\n`)**:
  - Dung `chcp 65001 >nul` va `cd /d "%~dp0"` de an toan voi duong dan co dau cach.
  - Kiem tra Python bang `python --version >nul 2>&1` (KHONG chi dung `where python` vi Microsoft Store stub `WindowsApps\python.exe` van khop `where` nhung tra ma loi `9009`), fallback sang `py -3` va `py`.
  - **Tranh dau ngoac `)` khong escape trong khoi `if (...)`** (CMD se dong som khoi `if` va chay nham lenh `pause`/`exit` ben duoi) — uu tien dung `goto :LABEL`.
  - Khi `EXIT_CODE` la `0` (thoat app binh thuong) hoac `2` (da dong hop thoai thieu thu vien) -> `exit /b 0` de **dong luon cua so CMD ngay lap tuc**, chi `pause` khi gap crash bat thuong (ma loi khac).

---

## Mau file `.bat` chuan (CRLF)

```bat
@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
title Ten Ung Dung

set "PYTHON_CMD="
python --version >nul 2>&1 && set "PYTHON_CMD=python"
if not defined PYTHON_CMD py -3 --version >nul 2>&1 && set "PYTHON_CMD=py -3"
if not defined PYTHON_CMD py --version >nul 2>&1 && set "PYTHON_CMD=py"

if not defined PYTHON_CMD goto :NO_PYTHON

%PYTHON_CMD% "%~dp0main.py"
set "EXIT_CODE=%ERRORLEVEL%"

if "%EXIT_CODE%"=="0" exit /b 0
if "%EXIT_CODE%"=="2" exit /b 0

echo [LOI] Chuong trinh dung voi ma loi: %EXIT_CODE%
pause
exit /b %EXIT_CODE%

:NO_PYTHON
echo [LOI] Khong tim thay Python 3 tren may tinh nay!
pause
exit /b 1
```

---

## Du an hien dang dung pattern nay

| Du an | File | Ghi chu |
|---|---|---|
| AskCpl | `AskCpl.py` | Pattern co ban |
| VocabularyApp | `VocabApp.py` | Pattern co ban |
| File Encrypt | `main.py`, `Encrypt.py`, `Run_File_Encrypt.bat` | Full auto-heal `crypto`/`Crypto` + `pycryptodomex` fallback + clean exit |
