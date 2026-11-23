# -*- coding: utf-8 -*-
"""tools/cleanup_done_media.py — Dọn media cục bộ SAU KHI đã upload GitHub.

VÌ SAO: 8 khóa × ~0,5–1 GB media + cache TTS làm đầy đĩa, khiến `fill_lite.py`
dừng ở ngưỡng 6 GB. Sau khi `finalize_lite.py` pack → upload API → Pages →
verify xong (trạng thái `done`), bản media trên GitHub là bản chính; bản local
chỉ tốn đĩa.

CÔNG CỤ NÀY:
  • chờ `data/logs/finalize_done.json` báo `done`;
  • kiểm tra `web/data/<slug>/index.json` đủ 2.520 ngày;
  • xoá `data/media/<slug>`, `data/audio/<slug>`, `data/ai_courses/<slug>/_pipeline`;
  • GIỮ `course.json`, `web/data/<slug>` (nội dung chữ trên Pages).

CÁCH DÙNG:
  python -X utf8 tools/cleanup_done_media.py --once
  python -X utf8 tools/cleanup_done_media.py --watch --interval 300
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statefile  # noqa: E402
import proc_lock  # noqa: E402

STATE_NAME = "finalize_done.json"
CLEAN_NAME = "cleanup_done_media.json"
STATE = statefile.path(STATE_NAME)
CLEAN = statefile.path(CLEAN_NAME)
LOG = os.path.join(BASE, "data", "logs", "cleanup_done_media.log")
WEB = os.path.join(BASE, "web", "data")
PUBLISH = os.path.join(BASE, "publish")


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


def save(path: str, data: dict) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, path)


def _size(p: str) -> int:
    if os.path.isfile(p):
        return os.path.getsize(p)
    total = 0
    for dp, _d, fs in os.walk(p):
        for f in fs:
            try:
                total += os.path.getsize(os.path.join(dp, f))
            except OSError:
                pass
    return total


def web_days(slug: str) -> int:
    p = os.path.join(WEB, slug, "index.json")
    try:
        with open(p, encoding="utf-8") as f:
            return len((json.load(f) or {}).get("days") or [])
    except Exception:
        return 0


def cleanup_one(slug: str, dry: bool) -> int:
    if os.path.isdir(os.path.join(PUBLISH, slug)):
        log(f"{slug}: publish/ còn tồn tại — chờ finalize xong")
        return 0
    if web_days(slug) < 2520:
        log(f"{slug}: web/data chưa đủ 2.520 ngày — bỏ qua")
        return 0
    targets = [
        os.path.join(BASE, "data", "media", slug),
        os.path.join(BASE, "data", "audio", slug),
        os.path.join(BASE, "data", "ai_courses", slug, "_pipeline"),
    ]
    freed = 0
    for p in targets:
        if not os.path.exists(p):
            continue
        sz = _size(p)
        freed += sz
        if dry:
            log(f"[DRY] xoá {os.path.relpath(p, BASE)} ({sz/1e6:.1f} MB)")
        else:
            shutil.rmtree(p, ignore_errors=True)
            log(f"xoá {os.path.relpath(p, BASE)} ({sz/1e6:.1f} MB)")
    return freed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--interval", type=int, default=300)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass

    def one_round() -> int:
        st = load(STATE)
        cleaned = load(CLEAN)
        n = 0
        for slug, info in st.items():
            if (info or {}).get("status") != "done" or slug in cleaned:
                continue
            freed = cleanup_one(slug, args.dry_run)
            if freed or args.dry_run:
                if not args.dry_run:
                    cleaned[slug] = {
                        "at": f"{datetime.now():%Y-%m-%d %H:%M:%S}",
                        "freed_mb": round(freed / 1e6, 1),
                    }
                    statefile.save(CLEAN_NAME, cleaned)
                n += 1
        return n

    if args.once or not args.watch:
        n = one_round()
        log(f"một lượt: dọn {n} khóa")
        return 0
    if not proc_lock.acquire("cleanup_watch"):
        log("⏸ đã có watcher cleanup chạy — thoát")
        return 0
    log(f"watch dọn media đã finalize (mỗi {args.interval}s)")
    try:
        while True:
            one_round()
            time.sleep(max(60, args.interval))
    finally:
        proc_lock.release("cleanup_watch")


if __name__ == "__main__":
    sys.exit(main())
