# -*- coding: utf-8 -*-
"""tools/fill_media.py — BÙ MEDIA (ảnh + audio từ/nghĩa + audio hội thoại) cho
mọi khóa học, chạy SONG SONG nhiều ngôn ngữ.

Vì sao cần tool riêng (đo thật 14/11):
  • Job `ai.pipeline --stages images,audio,media_verify` tuần tự 8 khóa mất
    ~2-3 GIỜ nhưng chỉ bù được vài chục ngày/khóa (media là I/O-bound: TTS +
    tải ảnh Wikipedia), trong khi còn ~17.000 ngày thiếu.
  • Chạy 8 khóa SONG SONG (1 tiến trình/khóa) ⇒ nhanh gấp ~6-8.
  • Manifest `data/media/index.json` dùng chung ⇒ đã sửa `_upsert_index` để
    ĐỌC ĐĨA + MERGE trước khi ghi (không còn mất entry khi nhiều process ghi).

Cách dùng:
  python tools/fill_media.py                       # tất cả khóa, ưu tiên chặng 1-2
  python tools/fill_media.py --lang tiếng_nhật     # 1 khóa
  python tools/fill_media.py --all-days            # tới hết (chậm, ~20h/khóa)
  python tools/fill_media.py --jobs 4              # 4 khóa song song
  python tools/fill_media.py --dry-run             # chỉ in kế hoạch
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import threading
import time
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Thứ tự ưu tiên: tiếng Nhật trước (ngôn ngữ chính), rồi các khóa còn lại.
LANGS = [
    "tiếng_nhật", "tiếng_trung", "tiếng_anh", "tiếng_hàn_quốc",
    "tiếng_tây_ban_nha", "tiếng_đức", "tiếng_pháp", "tiếng_nga",
]

# Ngày ưu tiên (chặng 1-2 = người học dùng trước) — ưu tiên tuyệt đối.
PRIORITY_DAYS = 600

# ── LOCK: chỉ 1 job bù media chạy tại 1 thời điểm ───────────────────────────
# 2 job media cùng chạy ⇒ tranh ghi `data/media/index.json` + `course.json`
# (đo thật 14/11: WinError 32 + mất entry manifest). Dùng file lock chứa PID.
LOCK_PATH = os.path.join(BASE, "data", "logs", "fill_media.lock")

_print_lock = threading.Lock()


def _pid_alive(pid: int) -> bool:
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


def acquire_lock() -> bool:
    """Giữ 1 job media tại 1 thời điểm. Trả False nếu đã có job khác."""
    os.makedirs(os.path.dirname(LOCK_PATH), exist_ok=True)
    if os.path.isfile(LOCK_PATH):
        try:
            with open(LOCK_PATH, encoding="utf-8") as f:
                old = int((f.read() or "0").strip() or 0)
        except Exception:
            old = 0
        if old and old != os.getpid() and _pid_alive(old):
            log(f"⏭ Đã có job bù media khác đang chạy (PID {old}) — bỏ qua.")
            return False
        try:
            os.remove(LOCK_PATH)
        except OSError:
            pass
    try:
        with open(LOCK_PATH, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    except OSError:
        return True          # không ghi được lock thì vẫn chạy (bỏ qua)
    return True


def release_lock() -> None:
    try:
        with open(LOCK_PATH, encoding="utf-8") as f:
            if int((f.read() or "0").strip() or 0) == os.getpid():
                os.remove(LOCK_PATH)
    except Exception:
        pass


def log(msg: str) -> None:
    with _print_lock:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def free_gb() -> float:
    try:
        import shutil
        return shutil.disk_usage(BASE).free / (1024 ** 3)
    except Exception:
        return 999.0


def run_media(lang: str, to_day: int | None, workers: int) -> int:
    """Chạy 1 khóa: bù media. Trả mã thoát."""
    cmd = [sys.executable, "-X", "utf8", "-m", "ai.pipeline", "--lang", lang,
           "--stages", "images,audio,media_verify",
           "--days", "9999",
           "--max-calls-per-day", "999999",
           "--max-calls-per-language", "999999",
           "--workers", str(workers)]
    if to_day:
        cmd += ["--to-day", str(to_day)]
    log(f"▶ media {lang}" + (f" (≤{to_day})" if to_day else ""))
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", cwd=BASE, timeout=14 * 3600)
        tail = [x for x in (p.stdout or "").splitlines() if x.strip()][-3:]
        for x in tail:
            log(f"   {x.strip()[:140]}")
        err = [x for x in (p.stderr or "").splitlines() if x.strip()][-2:]
        for x in err:
            log(f"   ⚠ {x.strip()[:140]}")
        return p.returncode
    except subprocess.TimeoutExpired:
        log(f"   ⏱ media {lang} hết giờ")
        return -1


def worker(lang: str, to_day: int | None, workers: int, rounds: int) -> None:
    for r in range(rounds):
        run_media(lang, to_day, workers)
        if free_gb() < 6.0:
            log(f"⛔ Dừng: disk còn {free_gb():.1f} GB (< 6 GB)")
            return
        if to_day:
            break                      # vòng 1 chỉ làm chặng 1-2
        to_day = None                 # vòng 2+: tới hết
    log(f"◀ {lang} xong")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", action="append", default=[],
                    help="giới hạn các khóa (lặp lại được: --lang A --lang B)")
    ap.add_argument("--jobs", type=int, default=3, help="số khóa chạy song song")
    ap.add_argument("--workers", type=int, default=2, help="luồng/ngày trong 1 khóa")
    ap.add_argument("--all-days", action="store_true",
                    help="bù tới hết (mặc định: chặng 1-2 trước)")
    ap.add_argument("--rounds", type=int, default=2)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    # `--lang` lặp lại được ⇒ giữ đúng thứ tự, bỏ trùng.
    targets = list(dict.fromkeys(args.lang)) if args.lang else list(LANGS)
    targets = [t for t in targets if t]
    if args.dry_run:
        for t in targets:
            print(f"  media {t} (≤{None if args.all_days else PRIORITY_DAYS}) "
                  f"jobs={args.jobs} workers={args.workers}")
        return 0

    log(f"bù media: {len(targets)} khóa · {args.jobs} song song · "
        f"disk còn {free_gb():.1f} GB")
    if not acquire_lock():
        return 0
    to_day = None if args.all_days else PRIORITY_DAYS
    threads: list[threading.Thread] = []
    sem = threading.Semaphore(max(1, args.jobs))
    results: dict[str, int] = {}

    def run(lang: str):
        with sem:
            results[lang] = worker(lang, to_day, args.workers, args.rounds)

    try:
        for t in targets:
            th = threading.Thread(target=run, args=(t,), daemon=False)
            th.start()
            threads.append(th)
        for th in threads:
            th.join()
    finally:
        release_lock()
    log("HOÀN TẤT bù media: " + ", ".join(f"{k}={v}" for k, v in results.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
