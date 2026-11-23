# -*- coding: utf-8 -*-
"""tools/test_proc_lock.py — test khoá tiến trình theo tên.

Chạy: python -X utf8 tools/test_proc_lock.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proc_lock  # noqa: E402

FAILS: list[str] = []


def check(name: str, ok: bool, extra: str = "") -> None:
    print(("PASS " if ok else "FAIL ") + name + (f" — {extra}" if extra else ""))
    if not ok:
        FAILS.append(name)


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="vocab_lock_")
    proc_lock.LOCK_DIR = tmp
    name = "test_lock"

    check("acquire lần 1", proc_lock.acquire(name))
    check("holder = pid hiện tại", proc_lock.holder(name) == os.getpid())

    # Tiến trình khác phải bị từ chối.
    code = (
        "import sys; sys.path.insert(0, r'%s'); import proc_lock; "
        "proc_lock.LOCK_DIR = r'%s'; print(proc_lock.acquire('%s'))"
        % (os.path.dirname(os.path.abspath(__file__)), tmp, name)
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True,
                         text=True, timeout=60).stdout.strip()
    check("tiến trình khác bị chặn", out.endswith("False"), out)

    proc_lock.release(name)
    check("release xoá lock", proc_lock.holder(name) == 0)

    # Lock rác (PID chết) phải bị ghi đè.
    with open(os.path.join(tmp, name + ".lock"), "w", encoding="utf-8") as f:
        f.write("999999")
    check("lock rác bị ghi đè", proc_lock.acquire(name))
    proc_lock.release(name)

    # File lock còn nhưng PID đã chết ⇒ holder = 0.
    with open(os.path.join(tmp, name + ".lock"), "w", encoding="utf-8") as f:
        f.write("999999")
    check("holder bỏ qua PID chết", proc_lock.holder(name) == 0)
    try:
        os.remove(os.path.join(tmp, name + ".lock"))
    except OSError:
        pass

    print(("→ FAIL " + ", ".join(FAILS)) if FAILS else "→ tất cả PASS")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
