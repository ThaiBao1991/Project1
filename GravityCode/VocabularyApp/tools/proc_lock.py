# -*- coding: utf-8 -*-
"""tools/proc_lock.py — khoá theo tên tiến trình (PID + phát hiện PID chết).

VÌ SAO: nhiều tool chạy nền (supervisor, finalize, cleanup, watchdog) từng chạy
trùng nhau sau khi máy khởi động lại ⇒ 2 job cùng pack/upload/xoá một khóa.

VÌ SAO LOCK Ở D:: `data/logs/*.lock` từng bị xoá ngoài ý muốn (cùng hiện tượng
với các file `*_done.json`), làm mất tác dụng chống trùng. Lock nay nằm ở
`D:\\VocabularyAppData\\state\\locks` (ổ dữ liệu, state ở đây đã bền qua nhiều
lần restart). Vẫn ĐỌC được lock cũ trong `data/logs` để nâng cấp không gián đoạn.

API:
  proc_lock.acquire("fill_lite") -> bool   (True nếu giành được)
  proc_lock.release("fill_lite")
  proc_lock.holder("fill_lite")  -> pid (0 nếu trống)
"""
from __future__ import annotations

import os
import subprocess

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEGACY_DIR = os.path.join(BASE, "data", "logs")
LOCK_DIR = os.environ.get("VOCAB_LOCK_DIR") or r"D:\VocabularyAppData\state\locks"


def _dir() -> str:
    try:
        os.makedirs(LOCK_DIR, exist_ok=True)
        return LOCK_DIR
    except OSError:
        os.makedirs(LEGACY_DIR, exist_ok=True)
        return LEGACY_DIR


def path(name: str) -> str:
    return os.path.join(_dir(), f"{name}.lock")


def legacy_path(name: str) -> str:
    return os.path.join(LEGACY_DIR, f"{name}.lock")


def _read(p: str) -> int:
    try:
        with open(p, encoding="utf-8") as f:
            return int((f.read() or "0").strip() or 0)
    except Exception:
        return 0


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


def _write(p: str, pid: int) -> None:
    try:
        with open(p, "w", encoding="utf-8") as f:
            f.write(str(pid))
    except OSError:
        pass


def alive(pid: int) -> bool:
    return _alive(pid)


def holder(name: str) -> int:
    """PID đang giữ khoá và còn sống; 0 nếu trống/lock rác.

    Tự "di cư" lock cũ trong `data/logs` sang thư mục mới nếu còn sống.
    """
    pid = _read(path(name))
    if _alive(pid):
        return pid
    old = _read(legacy_path(name))
    if _alive(old):
        _write(path(name), old)
        try:
            os.remove(legacy_path(name))
        except OSError:
            pass
        return old
    return 0


def acquire(name: str) -> bool:
    """True nếu giành được khoá; False nếu tiến trình khác đang giữ."""
    os.makedirs(_dir(), exist_ok=True)
    old = holder(name)
    if old and old != os.getpid():
        return False
    for p in (path(name), legacy_path(name)):
        try:
            if os.path.isfile(p):
                os.remove(p)
        except OSError:
            pass
    _write(path(name), os.getpid())
    return True


def release(name: str) -> None:
    for p in (path(name), legacy_path(name)):
        if _read(p) == os.getpid():
            try:
                os.remove(p)
            except OSError:
                pass
