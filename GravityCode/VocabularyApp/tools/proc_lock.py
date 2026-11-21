# -*- coding: utf-8 -*-
"""tools/proc_lock.py — khoá theo tên tiến trình (PID + phát hiện PID chết).

VÌ SAO: nhiều tool chạy nền (supervisor, finalize, cleanup, watchdog) từng chạy
trùng nhau sau khi máy khởi động lại ⇒ 2 job cùng pack/upload/xoá một khóa.
Mỗi tool chỉ cần `acquire("tên")`, nếu đã có tiến trình sống giữ khoá thì thoát.

Đặc điểm:
  • Lock chứa PID; PID không còn sống ⇒ tự coi là lock rác và ghi đè.
  • Không cần quyền admin, không cần thư viện ngoài (psutil nếu có).
  • `holder(name)` cho biết PID đang giữ khoá (0 nếu trống).
"""
from __future__ import annotations

import os
import subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCK_DIR = os.path.join(BASE, "data", "logs")


def path(name: str) -> str:
    return os.path.join(LOCK_DIR, f"{name}.lock")


def _alive(pid: int) -> bool:
    if not pid:
        return False
    try:
        import psutil
        return psutil.pid_exists(pid)
    except Exception:
        pass
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"],
                             capture_output=True, text=True, timeout=20)
        return str(pid) in (out.stdout or "")
    except Exception:
        return False


def holder(name: str) -> int:
    """PID đang giữ khoá và còn sống; 0 nếu trống/lock rác."""
    try:
        with open(path(name), encoding="utf-8") as f:
            pid = int((f.read() or "0").strip() or 0)
    except Exception:
        return 0
    return pid if _alive(pid) else 0


def acquire(name: str) -> bool:
    """True nếu giành được khoá; False nếu tiến trình khác đang giữ."""
    os.makedirs(LOCK_DIR, exist_ok=True)
    p = path(name)
    old = holder(name)
    if old and old != os.getpid():
        return False
    try:
        if os.path.isfile(p):
            os.remove(p)
    except OSError:
        pass
    try:
        with open(p, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    except OSError:
        return True          # không ghi được lock thì vẫn chạy
    return True


def release(name: str) -> None:
    p = path(name)
    try:
        with open(p, encoding="utf-8") as f:
            pid = int((f.read() or "0").strip() or 0)
        if pid == os.getpid():
            os.remove(p)
    except Exception:
        pass
