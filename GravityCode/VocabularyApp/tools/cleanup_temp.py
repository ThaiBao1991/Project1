# -*- coding: utf-8 -*-
"""tools/cleanup_temp.py — DỌN file tạm & backup cũ (chạy sau mỗi vòng watchdog).

BỐI CẢNH (đo thật 17/11): sau khi tắt máy / kill job cứng còn sót:
  • file `.tmp*` (ghi dở)            — vô dụng, chỉ gây rối
  • `course.json.bak1..5` mỗi khóa  — **1.057 MB** (14 % toàn bộ data/)
⇒ giảm BACKUP_KEEP và dọn file tmp cũ (KHÔNG đụng file của tiến trình đang
chạy — nhận biết qua hậu tố PID trong tên file).

Chạy:
  python tools/cleanup_temp.py            # dọn (mặc định)
  python tools/cleanup_temp.py --dry-run  # chỉ xem
  python tools/cleanup_temp.py --keep-backups 3
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA = os.path.join(BASE, "data")
# file tmp do pipeline tạo: "<name>.tmp" hoặc "<name>.tmp.<pid>.<tid>"
TMP_RE = re.compile(r"\.tmp(\.\d+\.\d+)?$")


def _pid_alive(pid: int) -> bool:
    try:
        import subprocess
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"],
                             capture_output=True, text=True, timeout=20)
        return str(pid) in (out.stdout or "")
    except Exception:
        return False


def _tmp_in_use(path: str) -> bool:
    """File tmp của tiến trình đang sống ⇒ không xoá."""
    m = re.search(r"\.tmp\.(\d+)\.\d+$", os.path.basename(path))
    if not m:
        return False
    try:
        return _pid_alive(int(m.group(1)))
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--keep-backups", type=int, default=2)
    ap.add_argument("--min-age-min", type=int, default=10,
                    help="chỉ xoá file tmp cũ hơn số phút này")
    args = ap.parse_args()

    now = time.time()
    freed = 0
    n_files = 0
    n_bak = 0

    for root, _dirs, files in os.walk(DATA):
        for fn in files:
            fp = os.path.join(root, fn)
            try:
                size = os.path.getsize(fp)
            except OSError:
                continue
            # 1) file .tmp (ghi dở) — bỏ qua file của tiến trình đang chạy
            if TMP_RE.search(fn):
                if _tmp_in_use(fp):
                    continue
                try:
                    if now - os.path.getmtime(fp) < args.min_age_min * 60:
                        continue
                except OSError:
                    continue
                n_files += 1
                freed += size
                if not args.dry_run:
                    try:
                        os.remove(fp)
                    except OSError:
                        pass
                continue
            # 2) backup .bak1..N — giữ N bản mới nhất
            m = re.match(r"^(.*)\.bak(\d+)$", fn)
            if m:
                n = int(m.group(2))
                if n > args.keep_backups:
                    n_bak += 1
                    freed += size
                    if not args.dry_run:
                        try:
                            os.remove(fp)
                        except OSError:
                            pass

    print(f"[{datetime.now().strftime('%H:%M:%S')}] dọn: {n_files} file .tmp + "
          f"{n_bak} backup cũ · giải phóng {freed/1024/1024:.1f} MB"
          + ("  (dry-run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
