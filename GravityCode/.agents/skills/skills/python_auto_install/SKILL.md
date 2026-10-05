---
name: python_auto_install
description: >
  Pattern tu dong kiem tra va cai dat thu vien Python khi khoi dong ung dung.
  Neu cai tu dong that bai -> hien hop thoai huong dan nguoi dung cai thu cong.
  Ap dung cho moi du an Python Desktop (Tkinter, CustomTkinter).
  Trigger: khi can them thu vien moi vao du an Python co GUI, hoac khi xu ly ImportError thieu thu vien.
---

# Skill: Python Auto-Install Libraries

## Muc dich

Dam bao ung dung Python luon hoat dong ngay khi chay lan dau, khong yeu cau nguoi dung cai pip thu cong.
Pattern nay da duoc chuan hoa va dung trong:
- `AskCpl.py` lines 12-56
- `VocabApp.py` lines 33-76

---

## Pattern chuan (Copy-paste vao dau file Python)

Xem file SKILL_TEMPLATE.py trong cung thu muc.

---

## Quy tac khai bao REQUIRED_PACKAGES

| Tinh huong | Cach khai bao |
|---|---|
| Module import trung ten pip | 'requests': 'requests>=2.31.0' |
| Module khac ten pip | 'PIL': 'Pillow>=10.0.0' |
| Module co namespace dai | 'google.auth': 'google-auth>=2.27.0' |
| Package co extras | 'qrcode': 'qrcode[pil]>=7.4.2' |

> NOTE: KEY phai la chuoi ma __import__(KEY) khong raise ImportError khi da cai.
> Sai: 'google-auth' (dung dau -)  ->  Dung: 'google.auth'

---

## Vi tri dat code trong file

`
import sys          <- stdlib luon ok
import subprocess   <- stdlib luon ok
import tkinter      <- stdlib luon ok

REQUIRED_PACKAGES = { ... }
def check_and_install_packages(): ...
check_and_install_packages()   <- GOI NGAY DAY

import customtkinter   <- import thu vien ngoai SAU khi da auto-install
`

KHONG import thu vien ngoai TRUOC khi goi check_and_install_packages().

---

## Them thu vien moi vao du an dang co san

1. Sua REQUIRED_PACKAGES trong file Python chinh - them 1 dong.
2. Sua requirements.txt (neu co) - them pip_name>=version.
3. Khong can them bat ky logic cai dat nao khac.

---

## Edge cases da xu ly

- Cai thanh cong: In log, tiep tuc chay app binh thuong.
- Cai that bai (khong co quyen, proxy...): Hien hop thoai voi lenh pip de user copy.
- User dong hop thoai: sys.exit(1) - khong de app chay do.
- Da cai du: Ham return ngay, khong goi pip (khong cham startup).

---

## Du an hien dang dung pattern nay

| Du an | File | Lines |
|---|---|---|
| AskCpl | AskCpl.py | 12-56 |
| VocabularyApp | VocabApp.py | 33-76 |
