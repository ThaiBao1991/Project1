# -*- coding: utf-8 -*-
"""tools/fill_remaining_after_chinese.py — Chờ Trung finalize + enrich xong rồi
bù media cho 6 khóa còn lại (Anh, Hàn, Tây, Đức, Pháp, Nga).

VÌ SAO: `fill_lite.py` chỉ nên chạy một khóa/lúc (RAM ~700 MB). Sau khi Trung
đủ 2.520 + finalize + enrich/deploy xong, mới chạy tiếp 6 khóa còn lại.

CÁCH DÙNG:
  python -X utf8 tools/fill_remaining_after_chinese.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LOG = os.path.join(BASE, "data", "logs", "fill_remaining.log")
FINAL = os.path.join(BASE, "data", "logs", "finalize_done.json")
ENRICH_DONE = os.path.join(BASE, "data", "logs", "enrich_after_finalize_done.json")
DONE = os.path.join(BASE, "data", "logs", "fill_remaining_done.json")
LANGS = ["tiếng_anh", "tiếng_hàn_quốc", "tiếng_tây_ban_nha",
         "tiếng_đức", "tiếng_pháp", "tiếng_nga"]
PY = sys.executable


def log(msg: str) -> None:
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def free_gb() -> float:
    try:
        import shutil
        return shutil.disk_usage(BASE).free / (1024 ** 3)
    except Exception:
        return 0.0


def wait_ready() -> bool:
    log("chờ Trung finalize + enrich/deploy xong …")
    for _ in range(24 * 12):  # tối đa ~24 giờ, quét 5 phút/lần
        fin = load(FINAL).get("tiếng_trung") or {}
        if fin.get("status") == "done" and os.path.isfile(ENRICH_DONE):
            log("Trung đã finalize + enrich xong")
            return True
        time.sleep(300)
    log("⚠ hết thời gian chờ Trung")
    return False


def main() -> int:
    if not wait_ready():
        return 1
    while free_gb() < 6.5:
        log(f"đĩa còn {free_gb():.1f} GB — chờ cleanup_done_media dọn bớt")
        time.sleep(300)
    args = [PY, "-X", "utf8", "tools/fill_lite.py"]
    for s in LANGS:
        args += ["--lang", s]
    log("bắt đầu bù media: " + ", ".join(LANGS))
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as lf:
        r = subprocess.run(args, cwd=BASE, stdout=lf, stderr=subprocess.STDOUT)
    log(f"fill_lite kết thúc (mã {r.returncode})")
    with open(DONE, "w", encoding="utf-8") as f:
        json.dump({"status": "done" if r.returncode == 0 else "failed",
                   "at": f"{datetime.now():%Y-%m-%d %H:%M:%S}",
                   "langs": LANGS}, f, ensure_ascii=False, indent=1)
    return r.returncode


if __name__ == "__main__":
    sys.exit(main())
