# -*- coding: utf-8 -*-
"""tools/enrich_after_finalize.py — Chờ pipeline bù media xong (finalize done)
rồi mới bổ sung nội dung giao tiếp cho khóa đó, xuất web và deploy.

VÌ SAO CẦN: `ai.pipeline` flush `course.json` mỗi ~10 ngày. Nếu enrich trong
lúc pipeline đang chạy, lần flush sau sẽ ghi đè mất nội dung vừa bổ sung.
Vì vậy chỉ chạy sau khi `tools/finalize_lite.py` đã pack/upload/deploy xong
(trạng thái `done` trong `data/logs/finalize_done.json`).

CÁCH DÙNG:
  python -X utf8 tools/enrich_after_finalize.py --lang tiếng_trung
  python -X utf8 tools/enrich_after_finalize.py --lang tiếng_trung --interval 300
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

STATE = os.path.join(BASE, "data", "logs", "finalize_done.json")
LOG = os.path.join(BASE, "data", "logs", "enrich_after_finalize.log")
DONE = os.path.join(BASE, "data", "logs", "enrich_after_finalize_done.json")
PY = sys.executable


def log(msg: str) -> None:
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_state() -> dict:
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def set_low_priority() -> None:
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass


def run(step: str, args: list[str], timeout: int = 7200) -> bool:
    log(f"▶ {step}: {' '.join(args)}")
    r = subprocess.run([PY, "-X", "utf8", *args], cwd=BASE,
                       capture_output=True, text=True, timeout=timeout)
    out = (r.stdout or "").strip().splitlines()
    err = (r.stderr or "").strip().splitlines()
    for line in out[-8:]:
        log("   " + line)
    for line in err[-5:]:
        log("   ! " + line)
    if r.returncode != 0:
        log(f"✗ {step} lỗi (mã {r.returncode})")
        return False
    log(f"✓ {step} xong")
    return True


def wait_finalized(slug: str, interval: int, max_hours: float) -> bool:
    t0 = time.time()
    while time.time() - t0 < max_hours * 3600:
        st = load_state().get(slug) or {}
        status = st.get("status")
        if status == "done":
            log(f"{slug}: finalize đã done lúc {st.get('at', '?')}")
            return True
        if status == "failed":
            log(f"⚠ {slug}: finalize báo failed — dừng để tránh ghi đè/đụng độ")
            return False
        time.sleep(interval)
    log(f"⚠ {slug}: hết thời gian chờ ({max_hours} giờ)")
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="tiếng_trung")
    ap.add_argument("--interval", type=int, default=300)
    ap.add_argument("--max-hours", type=float, default=24.0)
    args = ap.parse_args()
    slug = args.lang

    set_low_priority()
    log(f"chờ finalize xong cho {slug} (quét mỗi {args.interval}s) …")
    if not wait_finalized(slug, args.interval, args.max_hours):
        return 1

    steps = [
        ("enrich", ["tools/enrich_course_content.py", "--lang", slug]),
        ("export web", ["tools/export_days_keep_media.py", "--lang", slug]),
        ("deploy pages", ["tools/deploy_pages.py"]),
        ("verify online", ["tools/verify_online.py"]),
    ]
    for name, a in steps:
        if not run(name, a):
            return 1

    os.makedirs(os.path.dirname(DONE), exist_ok=True)
    with open(DONE, "w", encoding="utf-8") as f:
        json.dump({"slug": slug,
                   "at": f"{datetime.now():%Y-%m-%d %H:%M:%S}",
                   "status": "done"}, f, ensure_ascii=False, indent=1)
    log(f"🎉 {slug}: enrich + export + deploy + verify hoàn tất")
    return 0


if __name__ == "__main__":
    sys.exit(main())
