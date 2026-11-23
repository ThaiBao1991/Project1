# -*- coding: utf-8 -*-
"""tools/gh_token.py — lấy token GitHub MỘT LẦN, KHÔNG bật hộp thoại đăng nhập.

VÌ SAO CÓ FILE NÀY (sự cố 17/11/2026):
    Mỗi lần upload, các tool gọi `git credential fill`. Khi Git Credential
    Manager không đọc được credential đã lưu, nó BẬT HỘP THOẠI ĐĂNG NHẬP
    GitHub — và vì chạy nền nhiều tiến trình nên hộp thoại hiện liên tục.

CÁCH LẤY TOKEN (theo thứ tự, dừng ở cái đầu tiên có):
    1. Biến môi trường GITHUB_TOKEN.
    2. File token cục bộ (ngoài repo):
         %LOCALAPPDATA%\\VocabularyApp\\github_token.txt
       (đã lưu 1 lần từ Windows Credential Locker — xem tools/save_gh_token.ps1)
    3. settings.json (AskCpl) — token mã hoá ENC:base64(ngược).
    4. `git credential fill` với GCM_INTERACTIVE=Never + GIT_TERMINAL_PROMPT=0
       (TUYỆT ĐỐI không hiện hộp thoại; hết 15 giây thì bỏ).

Dùng:
    from gh_token import get_token
    tok = get_token()
"""
from __future__ import annotations

import base64
import json
import os
import subprocess

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_FILE = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
    "VocabularyApp", "github_token.txt")


def _from_file(path: str) -> str:
    try:
        if os.path.isfile(path):
            with open(path, encoding="utf-8", errors="ignore") as f:
                t = f.read().strip()
            if t:
                return t
    except Exception:
        pass
    return ""


def _from_settings() -> str:
    for p in (os.path.join(APP_DIR, "..", "Download", "AskCpl", "settings.json"),
              os.path.join(APP_DIR, "settings.json")):
        p = os.path.abspath(p)
        if not os.path.isfile(p):
            continue
        try:
            with open(p, encoding="utf-8") as f:
                d = json.load(f)
            raw = (d.get("github") or {}).get("token") or ""
            if raw.startswith("ENC:"):
                raw = base64.b64decode(raw[4:].encode("utf-8")).decode("utf-8")[::-1]
            if raw:
                return raw
        except Exception:
            continue
    return ""


def _from_git_credential() -> str:
    """Chỉ đọc credential ĐÃ LƯU; không cho phép Git hỏi người dùng."""
    env = dict(os.environ)
    env["GCM_INTERACTIVE"] = "Never"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "echo"
    try:
        p = subprocess.run(["git", "credential", "fill"],
                           input="protocol=https\nhost=github.com\n\n",
                           capture_output=True, text=True, timeout=15,
                           env=env)
        for line in (p.stdout or "").splitlines():
            if line.startswith("password="):
                t = line.split("=", 1)[1].strip()
                if t:
                    return t
    except Exception:
        pass
    return ""


def get_token() -> str:
    """Trả token hoặc chuỗi rỗng. KHÔNG BAO GIỜ hiện hộp thoại đăng nhập."""
    return (os.environ.get("GITHUB_TOKEN", "").strip()
            or _from_file(TOKEN_FILE)
            or _from_settings()
            or _from_git_credential())


def save_token(tok: str) -> str:
    """Lưu token ra file ngoài repo (dùng khi đã có token mới)."""
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, "w", encoding="ascii", errors="ignore") as f:
        f.write(tok.strip())
    return TOKEN_FILE
