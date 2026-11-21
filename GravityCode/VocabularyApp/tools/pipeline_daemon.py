# -*- coding: utf-8 -*-
"""tools/pipeline_daemon.py — MỘT tiến trình duy nhất giữ pipeline luôn sống.

VÌ SAO: sau khi máy/phiên khởi động lại, các job nền (supervisor bù media,
finalize, cleanup) đều mất; watchdog ở Startup lại bù song song 4 khóa và bù
lại khóa đã upload. Kết quả: tiến độ đứng, đĩa C: tụt, phải khởi động lại tay.

DAEMON NÀY:
  • giữ khoá `pipeline_daemon.lock` (chỉ 1 daemon);
  • chạy 3 con: fill_remaining, finalize --watch, cleanup --watch;
  • con chết ⇒ tự khởi động lại (backoff, không spam);
  • con thoát vì "đã có tiến trình khác giữ khoá" ⇒ chờ 5 phút rồi thử lại;
  • C: < 2,5 GB ⇒ tự chạy cleanup + dọn temp (tối đa 10 phút/lần);
  • xoay log con > 10 MB; ghi `data/logs/pipeline_status.json` mỗi vòng.

DÙNG:
  python -X utf8 tools/pipeline_daemon.py                 # chạy nền (console)
  python -X utf8 tools/pipeline_daemon.py --status        # xem trạng thái
  python -X utf8 tools/pipeline_daemon.py --stop          # dừng daemon + con
  python -X utf8 tools/pipeline_daemon.py --install-startup   # tự chạy khi đăng nhập
  python -X utf8 tools/pipeline_daemon.py --uninstall-startup
  python -X utf8 tools/pipeline_daemon.py --once          # 1 vòng (test)
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proc_lock  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LOG_DIR = os.path.join(BASE, "data", "logs")
LOG = os.path.join(LOG_DIR, "pipeline_daemon.log")
STATUS = os.path.join(LOG_DIR, "pipeline_status.json")
PY = sys.executable
LOCK = "pipeline_daemon"
LOOP_SECONDS = 30
LOG_MAX = 10 * 1024 * 1024
DISK_LOW_GB = 2.5
DISK_CHECK_EVERY = 600

CHILDREN = {
    "fill": ["-X", "utf8", "tools/fill_remaining_after_chinese.py"],
    "finalize": ["-X", "utf8", "tools/finalize_lite.py", "--watch", "--interval", "300"],
    "cleanup": ["-X", "utf8", "tools/cleanup_done_media.py", "--watch", "--interval", "300"],
}


def log(msg: str) -> None:
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def child_log(name: str) -> str:
    return os.path.join(LOG_DIR, f"daemon_{name}.log")


def rotate(path: str) -> None:
    try:
        if os.path.getsize(path) > LOG_MAX:
            os.replace(path, path + ".1")
    except OSError:
        pass


def free_gb(path: str) -> float:
    try:
        return shutil.disk_usage(path).free / (1024 ** 3)
    except Exception:
        return 0.0


def _popen(name: str) -> subprocess.Popen:
    path = child_log(name)
    rotate(path)
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    f = open(path, "a", encoding="utf-8", errors="replace")
    log(f"▶ bật {name} (log: {os.path.relpath(path, BASE)})")
    return subprocess.Popen([PY, *CHILDREN[name]], cwd=BASE,
                            stdout=f, stderr=subprocess.STDOUT,
                            stdin=subprocess.DEVNULL, creationflags=flags)


def write_status(procs: dict, meta: dict) -> None:
    out = {
        "pid": os.getpid(),
        "at": f"{datetime.now():%Y-%m-%d %H:%M:%S}",
        "disk": {"c_gb": round(free_gb("C:\\"), 2), "d_gb": round(free_gb("D:\\"), 2)},
        "children": {},
    }
    for name in CHILDREN:
        p = procs.get(name)
        m = meta.get(name) or {}
        out["children"][name] = {
            "pid": p.pid if (p and p.poll() is None) else 0,
            "alive": bool(p and p.poll() is None),
            "restarts": m.get("restarts", 0),
            "last_exit": m.get("last_exit"),
        }
    tmp = STATUS + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=1)
        os.replace(tmp, STATUS)
    except OSError:
        pass


def disk_guard(meta: dict) -> None:
    c = free_gb("C:\\")
    if c >= DISK_LOW_GB:
        return
    now = time.time()
    if now - meta.get("last_clean", 0) < DISK_CHECK_EVERY:
        return
    meta["last_clean"] = now
    log(f"⚠ C: còn {c:.1f} GB — chạy cleanup + dọn temp")
    for args in (["tools/cleanup_done_media.py", "--once"],
                 ["tools/cleanup_temp.py"]):
        try:
            subprocess.run([PY, "-X", "utf8", *args], cwd=BASE, timeout=1800,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            log(f"   dọn lỗi: {e}")


def supervise_once(procs: dict, meta: dict) -> None:
    now = time.time()
    for name in CHILDREN:
        p = procs.get(name)
        m = meta.setdefault(name, {"restarts": 0, "next_start": 0, "started": 0})
        if p is not None and p.poll() is None:
            continue
        if p is not None:
            rc = p.returncode
            lived = now - (m.get("started") or now)
            m["last_exit"] = {"at": f"{datetime.now():%H:%M:%S}", "code": rc,
                              "lived_s": round(lived)}
            # Thoát nhanh mã 0 ⇒ có tiến trình khác đang giữ khoá (chạy tay).
            if rc == 0 and lived < 20:
                m["next_start"] = now + 300
                log(f"⏸ {name} thoát ngay (đã có tiến trình khác giữ khoá) — thử lại sau 5 phút")
                procs[name] = None
                continue
            m["backoff"] = min(600, (m.get("backoff") or 30) * 2)
            m["next_start"] = now + m["backoff"]
            m["restarts"] = m.get("restarts", 0) + 1
            log(f"↻ {name} dừng (mã {rc}, sống {lived:.0f}s) — thử lại sau {m['backoff']}s")
            procs[name] = None
        if now >= (m.get("next_start") or 0):
            procs[name] = _popen(name)
            m["started"] = now
            m.pop("backoff", None)


def status_pid() -> int:
    try:
        with open(STATUS, encoding="utf-8") as f:
            return int((json.load(f) or {}).get("pid") or 0)
    except Exception:
        return 0


def cmd_status() -> int:
    try:
        with open(STATUS, encoding="utf-8") as f:
            st = json.load(f)
    except Exception:
        st = {}
    pid = proc_lock.holder(LOCK)
    # Lock có thể bị xoá ngoài ý muốn; status JSON vẫn là nguồn dự phòng.
    if not pid:
        cand = int(st.get("pid") or 0)
        if cand and proc_lock.alive(cand):
            pid = cand
    print(f"daemon: {'chạy PID ' + str(pid) if pid else 'KHÔNG chạy'}")
    if st:
        print(f"cập nhật: {st.get('at')} · C: {st.get('disk', {}).get('c_gb')} GB"
              f" · D: {st.get('disk', {}).get('d_gb')} GB")
        for name, c in (st.get("children") or {}).items():
            print(f"  {name:9} pid={c.get('pid') or '-':>6} alive={c.get('alive')}"
                  f" restarts={c.get('restarts')} last_exit={c.get('last_exit')}")
    return 0


def cmd_stop() -> int:
    pid = proc_lock.holder(LOCK)
    if not pid:
        print("daemon không chạy")
        return 0
    try:
        with open(STATUS, encoding="utf-8") as f:
            st = json.load(f)
    except Exception:
        st = {}
    for c in (st.get("children") or {}).values():
        cp = c.get("pid") or 0
        if cp:
            subprocess.run(["taskkill", "/PID", str(cp), "/T", "/F"],
                           capture_output=True)
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)
    print(f"đã dừng daemon PID {pid} và các con")
    return 0


def _startup_paths():
    startup = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows",
                           "Start Menu", "Programs", "Startup")
    return os.path.join(startup, "VocabularyApp_Pipeline.vbs"), \
        os.path.join(BASE, "tools", "pipeline_daemon_task.cmd")


def cmd_install_startup() -> int:
    vbs, cmd = _startup_paths()
    pythonw = os.path.join(os.path.dirname(PY), "pythonw.exe")
    exe = pythonw if os.path.isfile(pythonw) else PY
    with open(cmd, "w", encoding="ascii", errors="replace", newline="\r\n") as f:
        f.write("@echo off\n")
        f.write(f'cd /d "{BASE}"\n')
        f.write(f'"{exe}" -X utf8 tools\\pipeline_daemon.py '
                f'>> data\\logs\\daemon_console.log 2>&1\n')
    os.makedirs(os.path.dirname(vbs), exist_ok=True)
    with open(vbs, "w", encoding="ascii", errors="replace", newline="\r\n") as f:
        f.write("' VocabularyApp - pipeline daemon (media 24/7). ASCII only.\n")
        f.write('Set sh = CreateObject("WScript.Shell")\n')
        f.write(f'sh.Run "cmd /c """ & "{cmd}" & """", 0, False\n')
    print("đã cài tự chạy khi đăng nhập:", vbs)
    print("  lệnh:", cmd)
    return 0


def cmd_uninstall_startup() -> int:
    vbs, _cmd = _startup_paths()
    try:
        os.remove(vbs)
        print("đã xoá:", vbs)
    except OSError:
        print("không có:", vbs)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--stop", action="store_true")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--install-startup", action="store_true")
    ap.add_argument("--uninstall-startup", action="store_true")
    args = ap.parse_args()

    if args.status:
        return cmd_status()
    if args.stop:
        return cmd_stop()
    if args.install_startup:
        return cmd_install_startup()
    if args.uninstall_startup:
        return cmd_uninstall_startup()

    # Nếu lock bị xoá ngoài ý muốn mà daemon cũ vẫn sống (status JSON),
    # không được bật thêm daemon thứ hai.
    sp = status_pid()
    if sp and sp != os.getpid() and proc_lock.alive(sp):
        print(f"daemon đã chạy (PID {sp}, theo status JSON) — thoát")
        return 0
    if not proc_lock.acquire(LOCK):
        print(f"daemon đã chạy (PID {proc_lock.holder(LOCK)}) — thoát")
        return 0
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass

    log("=== PIPELINE DAEMON khởi động ===")
    procs: dict = {}
    meta: dict = {}
    try:
        while True:
            if proc_lock.holder(LOCK) != os.getpid():
                proc_lock.acquire(LOCK)      # tự phục hồi nếu lock bị xoá
            supervise_once(procs, meta)
            disk_guard(meta)
            write_status(procs, meta)
            if args.once:
                break
            time.sleep(LOOP_SECONDS)
    except KeyboardInterrupt:
        log("dừng theo Ctrl+C")
    finally:
        for name, p in procs.items():
            if p and p.poll() is None:
                p.terminate()
        for name, p in procs.items():
            if p:
                try:
                    p.wait(timeout=15)
                except Exception:
                    p.kill()
        try:
            write_status({}, meta)
        except Exception:
            pass
        proc_lock.release(LOCK)
        log("=== PIPELINE DAEMON dừng ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
