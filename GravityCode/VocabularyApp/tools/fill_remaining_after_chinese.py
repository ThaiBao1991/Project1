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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statefile  # noqa: E402
import proc_lock  # noqa: E402
import media_index_swap  # noqa: E402

FINAL_NAME = "finalize_done.json"
ENRICH_NAME = "enrich_after_finalize_done.json"
DONE_NAME = "fill_remaining_done.json"
FINAL = statefile.path(FINAL_NAME)
ENRICH_DONE = statefile.path(ENRICH_NAME)
DONE = statefile.path(DONE_NAME)
LOCK = os.path.join(BASE, "data", "logs", "fill_remaining.lock")
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
        fin = statefile.load(FINAL_NAME).get("tiếng_trung") or {}
        if fin.get("status") == "done" and statefile.load(ENRICH_NAME):
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


def _run_all() -> int:
    if not wait_ready():
        return 1
    log("bắt đầu bù media từng khóa: " + ", ".join(LANGS))
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    # Khóa đã upload xong thì bỏ qua: cleanup đã xoá media local nên
    # days_done = 0 — nếu không chặn sẽ bù lại từ đầu (lỗi đo thật 21/11).
    fin = statefile.load(FINAL_NAME)
    uploaded = {s for s, v in fin.items() if (v or {}).get("status") == "done"}
    uploaded |= set(statefile.load("cleanup_done_media.json"))
    failed = []
    for slug in LANGS:
        if slug in uploaded:
            log(f"⏭ {slug}: đã upload xong — bỏ qua (không bù lại media local)")
            continue
        for attempt in range(1, 121):
            d = days_done(slug)
            if d >= TOTAL:
                break
            # Chỉ nạp manifest của khóa đang làm (333 MB → ~40 MB) để giảm RAM.
            try:
                media_index_swap.begin(slug)
            except Exception as e:
                log(f"⚠ shard manifest lỗi: {e}")
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
            # Gộp shard trở lại manifest đầy đủ để finalize/publish thấy đủ entry.
            try:
                media_index_swap.end(slug)
            except Exception as e:
                log(f"⚠ gộp manifest lỗi: {e}")
        else:
            log(f"⚠ {slug}: dừng ở {days_done(slug)}/{TOTAL}")
            failed.append(slug)
            break
    status = "done" if not failed else "partial"
    statefile.save(DONE_NAME, {"status": status,
                               "at": f"{datetime.now():%Y-%m-%d %H:%M:%S}",
                               "langs": LANGS,
                               "days": {s: days_done(s) for s in LANGS}})
    return 0 if status == "done" else 1


def main() -> int:
    """Khoá `fill_remaining.lock` để không có 2 supervisor chạy song song."""
    if not proc_lock.acquire("fill_remaining"):
        return 0
    try:
        return _run_all()
    finally:
        proc_lock.release("fill_remaining")


if __name__ == "__main__":
    sys.exit(main())
