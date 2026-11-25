# -*- coding: utf-8 -*-
"""tools/fill_lite.py — BÙ MEDIA CHẾ ĐỘ NHẸ: 1 khóa × 1 luồng, RAM có trần.

VÌ SAO CÓ FILE NÀY (yêu cầu 18/11/2026):
    `fill_media.py --jobs 4 --workers 2` chiếm ~1,2-1,5 GB RAM và ~20 % CPU
    (4 tiến trình `ai.pipeline`, mỗi tiến trình giữ manifest + course trong RAM).
    Người dùng cần máy vẫn nhẹ: chỉ ~1/3 RAM và CPU thấp.

CÁCH LÀM:
    • Chạy TUẦN TỰ từng khóa (đúng thứ tự ưu tiên Nhật → Trung → Anh → …).
    • Mỗi khóa 1 tiến trình `ai.pipeline --workers 1` (không đa luồng).
    • Giám sát RAM tiến trình con; vượt `--mem-mb` (mặc định 700 MB) thì
      terminate rồi chạy lại — checkpoint theo ngày nên KHÔNG mất tiến độ.
    • Hạ ưu tiên Below Normal để Windows vẫn mượt.
    • Dừng khi đĩa < 6 GB.

Cách dùng:
  python -X utf8 tools/fill_lite.py                    # tất cả khóa
  python -X utf8 tools/fill_lite.py --lang tiếng_nhật
  python -X utf8 tools/fill_lite.py --mem-mb 600
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LANGS = ["tiếng_nhật", "tiếng_trung", "tiếng_anh", "tiếng_hàn_quốc",
         "tiếng_tây_ban_nha", "tiếng_đức", "tiếng_pháp", "tiếng_nga"]
LOCK_PATH = os.path.join(BASE, "data", "logs", "fill_lite.lock")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proc_lock  # noqa: E402
import meminfo  # noqa: E402
LOG_PATH = os.path.join(BASE, "data", "logs", "fill_lite.log")
MEDIA = os.path.join(BASE, "data", "media")


def log(msg: str) -> None:
    line = f"[{datetime.now():%H:%M:%S}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def days_done(slug: str) -> int:
    root = os.path.join(MEDIA, slug)
    n = 0
    if os.path.isdir(root):
        for d in os.listdir(root):
            p = os.path.join(root, d)
            if os.path.isdir(p) and os.listdir(p):
                n += 1
    return n


def first_missing(slug: str) -> int:
    """Ngày nhỏ nhất chưa có media (1..2520) — để pipeline không quét lại từ đầu."""
    root = os.path.join(MEDIA, slug)
    have = set()
    if os.path.isdir(root):
        for d in os.listdir(root):
            p = os.path.join(root, d)
            if os.path.isdir(p) and os.listdir(p):
                try:
                    have.add(int(d.lstrip("d")))
                except ValueError:
                    pass
    for i in range(1, 2521):
        if i not in have:
            return i
    return 2520


def free_gb() -> float:
    import shutil
    return shutil.disk_usage(BASE).free / (1024 ** 3)


def set_low_priority(pid: int | None = None) -> None:
    try:
        import psutil
        p = psutil.Process(pid) if pid else psutil.Process()
        p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass


def run_once(slug: str, mem_mb: int, workers: int,
             from_day: int = 1, min_free_gb: float = 6.0) -> tuple[int, int]:
    """Chạy 1 lần pipeline cho 1 khóa. Trả (returncode, số lần bị kill vì RAM)."""
    cmd = [sys.executable, "-X", "utf8", "-m", "ai.pipeline",
           "--lang", slug, "--stages", "images,audio,media_verify",
           "--days", "9999", "--max-calls-per-day", "999999",
           "--max-calls-per-language", "999999",
           "--from-day", str(max(1, from_day)),
           "--workers", str(workers)]
    proc = subprocess.Popen(cmd, cwd=BASE, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    set_low_priority(proc.pid)
    kills = 0
    over = 0
    while True:
        rc = proc.poll()
        if rc is not None:
            return rc, kills
        rss_mb = meminfo.rss_mb(proc.pid)
        if rss_mb > mem_mb:
            over += 1
            log(f"   ⚠ {slug}: RAM {rss_mb:.0f} MB > {mem_mb} MB (lần {over}/2)")
            if over >= 2:
                log(f"   ⇒ khởi động lại tiến trình (giữ checkpoint)")
                kills += 1
                proc.terminate()
                try:
                    proc.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    proc.kill()
                return -9, kills
        else:
            over = 0
        if free_gb() < min_free_gb:
            log(f"   ⛔ đĩa còn {free_gb():.1f} GB (< {min_free_gb:g} GB) — dừng khóa {slug}")
            proc.terminate()
            try:
                proc.wait(timeout=15)
            except subprocess.TimeoutExpired:
                proc.kill()
            return -8, kills
        time.sleep(10)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", action="append", default=[])
    ap.add_argument("--mem-mb", type=int, default=450)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--max-passes", type=int, default=60,
                    help="số lần chạy lại tối đa cho 1 khóa")
    ap.add_argument("--min-free-gb", type=float, default=6.0,
                    help="dừng khi đĩa trống dưới mức này (GB)")
    args = ap.parse_args()

    if not proc_lock.acquire("fill_lite"):
        log(f"⚠ đã có fill_lite chạy (PID {proc_lock.holder('fill_lite')}) — thoát")
        return 0
    set_low_priority()
    log(f"BẮT ĐẦU chế độ nhẹ · RAM trần {args.mem_mb} MB · "
        f"workers={args.workers} · đĩa {free_gb():.1f} GB · "
        f"ngưỡng dừng {args.min_free_gb:g} GB")

    targets = list(dict.fromkeys(args.lang)) if args.lang else list(LANGS)
    try:
        for slug in targets:
            if free_gb() < args.min_free_gb:
                log(f"⛔ đĩa còn {free_gb():.1f} GB (< {args.min_free_gb:g} GB) — dừng toàn bộ")
                break
            t0 = time.time()
            log(f"▶ {slug}: {days_done(slug)}/2520 ngày có media")
            stall = 0
            for p in range(args.max_passes):
                before = days_done(slug)
                if before >= 2520:
                    break
                rc, kills = run_once(slug, args.mem_mb, args.workers,
                                     first_missing(slug), args.min_free_gb)
                after = days_done(slug)
                log(f"   pass {p+1}: {before} → {after}/2520 "
                    f"(mã {rc}, kill RAM {kills}, {time.time()-t0:.0f}s)")
                if after >= 2520:
                    break
                if after <= before:
                    stall += 1
                    if stall >= 2:
                        log(f"   ⚠ {slug}: 2 pass không tăng — bỏ qua khóa này")
                        break
                    time.sleep(20)
                else:
                    stall = 0
                if rc == -8:
                    break
            log(f"◀ {slug} xong: {days_done(slug)}/2520 ngày "
                f"({(time.time()-t0)/3600:.2f} giờ)")
    finally:
        proc_lock.release("fill_lite")
    log("HOÀN TẤT CHẾ ĐỘ NHẸ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
