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
MEDIA = os.path.join(BASE, "data", "media")
TOTAL = 2520
MIN_FREE = 2.0
WAIT_FREE = 2.3
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


def days_done(slug: str) -> int:
    p = os.path.join(MEDIA, slug)
    if not os.path.isdir(p):
        return 0
    return sum(1 for d in os.listdir(p)
               if os.path.isdir(os.path.join(p, d))
               and os.listdir(os.path.join(p, d)))


def clean_stale() -> None:
    """Dọn temp cũ (không đụng file đang được ghi)."""
    import glob
    import tempfile
    import time as _t
    now = _t.time()
    for p in glob.glob(os.path.join(MEDIA, "index.json.tmp.*")):
        try:
            if now - os.path.getmtime(p) > 600:
                os.remove(p)
        except OSError:
            pass
    for p in glob.glob(os.path.join(BASE, "data", "ai_courses", "*", "course.json.tmp.*")):
        try:
            if now - os.path.getmtime(p) > 600:
                os.remove(p)
        except OSError:
            pass
    for p in glob.glob(os.path.join(tempfile.gettempdir(), "vocab_pages_*")):
        try:
            if now - os.path.getmtime(p) > 3600:
                import shutil
                for dp, _ds, fs in os.walk(p):
                    for f in fs:
                        try:
                            os.chmod(os.path.join(dp, f), 0o666)
                        except OSError:
                            pass
                shutil.rmtree(p, ignore_errors=True)
        except OSError:
            pass


def wait_free() -> None:
    t0 = time.time()
    while free_gb() < WAIT_FREE and time.time() - t0 < 6 * 3600:
        clean_stale()
        try:
            subprocess.run([PY, "-X", "utf8", "tools/cleanup_done_media.py", "--once"],
                           cwd=BASE, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=600)
        except Exception:
            pass
        log(f"đĩa còn {free_gb():.1f} GB — chờ cleanup/finalize")
        time.sleep(300)


def main() -> int:
    if not wait_ready():
        return 1
    log("bắt đầu bù media từng khóa: " + ", ".join(LANGS))
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    failed = []
    for slug in LANGS:
        for attempt in range(1, 121):
            d = days_done(slug)
            if d >= TOTAL:
                break
            wait_free()
            log(f"▶ {slug}: {d}/{TOTAL} — lần {attempt}")
            args = [PY, "-X", "utf8", "tools/fill_lite.py",
                    "--lang", slug, "--min-free-gb", str(MIN_FREE)]
            with open(LOG, "a", encoding="utf-8") as lf:
                r = subprocess.run(args, cwd=BASE, stdout=lf,
                                   stderr=subprocess.STDOUT)
            d2 = days_done(slug)
            log(f"◀ {slug}: {d2}/{TOTAL} (mã {r.returncode})")
            if d2 >= TOTAL:
                break
            if d2 <= d:
                time.sleep(300)
        if days_done(slug) >= TOTAL:
            log(f"✅ {slug}: đủ {TOTAL} ngày")
        else:
            log(f"⚠ {slug}: dừng ở {days_done(slug)}/{TOTAL}")
            failed.append(slug)
            break
    status = "done" if not failed else "partial"
    with open(DONE, "w", encoding="utf-8") as f:
        json.dump({"status": status,
                   "at": f"{datetime.now():%Y-%m-%d %H:%M:%S}",
                   "langs": LANGS,
                   "days": {s: days_done(s) for s in LANGS}}, f,
                  ensure_ascii=False, indent=1)
    return 0 if status == "done" else 1


if __name__ == "__main__":
    sys.exit(main())
