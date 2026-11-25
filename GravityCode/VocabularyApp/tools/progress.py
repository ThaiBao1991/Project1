# -*- coding: utf-8 -*-
"""tools/progress.py — báo cáo tiến độ pipeline (chỉ đọc, không khoá).

Chạy: python -X utf8 tools/progress.py
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proc_lock  # noqa: E402
import statefile  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MEDIA = os.path.join(BASE, "data", "media")
TOTAL = 2520
LANGS = ["tiếng_nhật", "tiếng_trung", "tiếng_anh", "tiếng_hàn_quốc",
         "tiếng_tây_ban_nha", "tiếng_đức", "tiếng_pháp", "tiếng_nga"]


def days(slug: str) -> list[str]:
    p = os.path.join(MEDIA, slug)
    if not os.path.isdir(p):
        return []
    return [d for d in os.listdir(p)
            if os.path.isdir(os.path.join(p, d)) and os.listdir(os.path.join(p, d))]


def rate_recent() -> float:
    """Ngày/giờ, đo theo mtime của thư mục ngày trong 60 phút gần nhất."""
    cut = time.time() - 3600
    n = 0
    for slug in LANGS:
        p = os.path.join(MEDIA, slug)
        if not os.path.isdir(p):
            continue
        for d in os.listdir(p):
            dp = os.path.join(p, d)
            try:
                if os.path.isdir(dp) and os.listdir(dp) and os.path.getmtime(dp) >= cut:
                    n += 1
            except OSError:
                pass
    return float(n)


def main() -> int:
    fin = statefile.load("finalize_done.json")
    clean = statefile.load("cleanup_done_media.json")
    done = {s for s, v in fin.items() if (v or {}).get("status") == "done"}
    done |= set(clean)

    print(f"TIẾN ĐỘ {time.strftime('%Y-%m-%d %H:%M:%S')}")
    if os.path.isfile(os.path.join(MEDIA, "index_full.json")):
        print("⚠ manifest đang ở chế độ SHARD (chỉ khóa đang làm) — gộp bằng: "
              "python -X utf8 tools\\media_index_swap.py end")
    print(f"{'khóa':22}{'media':>10}  {'%':>6}  trạng thái")
    remaining = 0
    current = ""
    cur_days = 0
    for slug in LANGS:
        had = days(slug)
        n = len(had)
        if slug in done and n == 0:
            print(f"{slug:22}{'—':>10}  {'100':>6}  ✅ đã upload, local đã dọn")
            continue
        if n == 0:
            print(f"{slug:22}{'0/2520':>10}  {0:>6}  ⏸ chưa chạy")
            remaining += TOTAL
            continue
        pct = n * 100.0 / TOTAL
        state = "✅ đủ, chờ finalize" if n >= TOTAL else "🟢 đang bù"
        print(f"{slug:22}{f'{n}/2520':>10}  {pct:>6.1f}  {state}")
        if n < TOTAL:
            remaining += TOTAL - n
            if not current:
                current, cur_days = slug, n

    r = rate_recent()
    print(f"\ncòn {remaining} ngày", end="")
    if r:
        print(f" · tốc độ {r:.0f} ngày/giờ ⇒ ~{remaining / r:.1f} giờ (~{remaining / r / 24:.1f} ngày)")
    else:
        print(" (chưa đo được tốc độ)")
    if current:
        left = TOTAL - cur_days
        eta = time.strftime("%d/%m %H:%M", time.localtime(time.time() + (left / r if r else 0) * 3600))
        print(f"khóa hiện tại: {current} {cur_days}/{TOTAL} (còn {left})" + (f" ⇒ xong ~{eta}" if r else ""))

    try:
        print(f"đĩa: C {shutil.disk_usage('C:\\').free/1e9:.1f} GB · "
              f"D {shutil.disk_usage('D:\\').free/1e9:.1f} GB")
    except OSError:
        pass

    pid = proc_lock.holder("pipeline_daemon")
    names = ("fill_remaining", "finalize_watch", "cleanup_watch", "fill_lite")
    alive = {n: proc_lock.holder(n) for n in names}
    print(f"daemon: {'PID ' + str(pid) if pid else 'KHÔNG chạy'}")
    print("job: " + " · ".join(f"{n}={p or '-'}" for n, p in alive.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
