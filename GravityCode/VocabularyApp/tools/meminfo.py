# -*- coding: utf-8 -*-
"""tools/meminfo.py — đọc RAM (RSS) của 1 tiến trình, KHÔNG cần psutil.

VÌ SAO: máy này không cài psutil ⇒ guard RAM trong `fill_lite` bị tắt âm thầm
(`ps = None`), nên `ai.pipeline` phình lên ~958 MB. Module này dùng
`psapi.GetProcessMemoryInfo` qua ctypes (có sẵn trên Windows), và tự dùng
psutil nếu được cài.

API:
  meminfo.rss_mb(pid) -> float (0.0 nếu không đọc được)
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes


class _PMC(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def rss_mb(pid: int) -> float:
    if not pid:
        return 0.0
    try:
        import psutil
        return psutil.Process(pid).memory_info().rss / (1024 ** 2)
    except Exception:
        pass
    try:
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        # PROCESS_QUERY_INFORMATION | PROCESS_VM_READ
        h = k32.OpenProcess(0x0400 | 0x0010, False, int(pid))
        if not h:
            return 0.0
        try:
            pmc = _PMC()
            pmc.cb = ctypes.sizeof(pmc)
            ok = psapi.GetProcessMemoryInfo(h, ctypes.byref(pmc), pmc.cb)
            return (pmc.WorkingSetSize / (1024 ** 2)) if ok else 0.0
        finally:
            k32.CloseHandle(h)
    except Exception:
        return 0.0
