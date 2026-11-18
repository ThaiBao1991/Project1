# -*- coding: utf-8 -*-
"""tools/push_master.py — PUSH NHANH HIỆN TẠI bằng token ThaiBao (không hộp thoại).

VÌ SAO CÓ FILE NÀY (19/11/2026):
    `git push origin master` có thể treo vì Git Credential Manager bật hộp thoại
    đăng nhập (nhất là sau khi đổi tài khoản). Tool này dùng đúng cơ chế của
    `deploy_pages.py`: header `http.https://github.com/.extraheader` qua biến
    môi trường, tài khoản **ThaiBao1991**, không nhúng token vào URL.

Cách dùng:
  python -X utf8 tools/push_master.py
  python -X utf8 tools/push_master.py --branch master --dry-run
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
sys.path.insert(0, os.path.join(BASE, "tools"))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--branch", default="master")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    from gh_token import get_token
    from deploy_pages import _push_env

    tok = get_token()
    if not tok:
        print("⚠ thiếu token GitHub (xem tools/gh_token.py)")
        return 1
    cmd = ["git", "-C", BASE, "push", args.remote, args.branch]
    if args.dry_run:
        cmd.insert(4, "--dry-run")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800,
                       env=_push_env(tok))
    for line in (r.stdout or "").strip().splitlines()[-5:]:
        print(line)
    for line in (r.stderr or "").strip().splitlines()[-5:]:
        print(line)
    print("✓ push xong" if r.returncode == 0 else f"✗ push lỗi (mã {r.returncode})")
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
