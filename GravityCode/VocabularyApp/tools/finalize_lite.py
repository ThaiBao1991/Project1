# -*- coding: utf-8 -*-
"""tools/finalize_lite.py — TỰ ĐỘNG ĐÓNG GÓI + ĐẨY + DEPLOY khi 1 khóa bù xong.

BỐI CẢNH (18/11/2026):
    `tools/fill_lite.py` chạy TUẦN TỰ từng khóa ở chế độ nhẹ. Mỗi khóa xong
    phải làm 4 bước nặng tay: pack → upload API → publish pages → deploy.
    Người dùng cần job tự chạy qua đêm mà không phải canh.

CÁCH LÀM:
    • Theo dõi `data/logs/fill_lite.log`, tìm dòng `◀ <slug> xong: 2520/2520`.
    • Khóa nào đủ 2520 ngày và chưa làm → chạy lần lượt:
        1. publish_online.py --pack --lang <slug>
        2. upload_media_api.py --lang <slug>
        3. publish_online.py --pages
        4. deploy_pages.py
        5. xoá publish/<slug> (giải phóng đĩa)
    • Trạng thái lưu ở `data/logs/finalize_done.json` → không làm lại.
    • Lỗi: thử lại tối đa 3 lần, cách 10 phút; ghi log rõ ràng.
    • Hạ ưu tiên Below Normal.

Cách dùng:
  python -X utf8 tools/finalize_lite.py --watch          # chạy nền, canh mãi
  python -X utf8 tools/finalize_lite.py --once           # làm 1 lượt rồi thoát
  python -X utf8 tools/finalize_lite.py --lang tiếng_trung --once
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

LOG_PATH = os.path.join(BASE, "data", "logs", "finalize_lite.log")
FILL_LOG = os.path.join(BASE, "data", "logs", "fill_lite.log")
STATE = os.path.join(BASE, "data", "logs", "finalize_done.json")
MEDIA = os.path.join(BASE, "data", "media")
PUBLISH = os.path.join(BASE, "publish")
DONE_RE = re.compile(r"◀\s+(.+?)\s+xong:\s+(\d+)/2520")


def log(msg: str) -> None:
    line = f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}"
    print(line, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def set_low_priority() -> None:
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        pass


def load_state() -> dict:
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}


def save_state(st: dict) -> None:
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp, STATE)


def days_done(slug: str) -> int:
    root = os.path.join(MEDIA, slug)
    n = 0
    if os.path.isdir(root):
        for d in os.listdir(root):
            p = os.path.join(root, d)
            if os.path.isdir(p) and os.listdir(p):
                n += 1
    return n


def completed_from_log() -> list[str]:
    """Các khóa đã ghi '◀ slug xong: 2520/2520' trong fill_lite.log."""
    out = []
    try:
        with open(FILL_LOG, encoding="utf-8", errors="replace") as f:
            for line in f:
                m = DONE_RE.search(line)
                if m and int(m.group(2)) >= 2520:
                    out.append(m.group(1).strip())
    except OSError:
        pass
    return out


def run(cmd: list[str], timeout: int = 7200) -> tuple[int, str]:
    log("   $ " + " ".join(cmd[1:]))
    try:
        p = subprocess.run(cmd, cwd=BASE, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        tail = (p.stdout or "").strip().splitlines()[-6:]
        err = (p.stderr or "").strip().splitlines()[-3:]
        for line in tail:
            log("     " + line)
        for line in err:
            log("     ! " + line)
        return p.returncode, p.stdout or ""
    except subprocess.TimeoutExpired:
        log(f"     ! quá thời gian {timeout}s")
        return -1, ""
    except Exception as e:
        log(f"     ! {e}")
        return -1, ""


def finalize(slug: str) -> bool:
    py = sys.executable
    log(f"▶ FINALIZE {slug}")
    # Giảm dung lượng audio trước khi pack (48/64 → 32 kbps mono).
    # SKIP_SHRINK=1 dùng khi đã nén riêng để tránh quét lại toàn bộ.
    if os.environ.get("SKIP_SHRINK") != "1":
        rc, _ = run([py, "-X", "utf8", "tools/shrink_audio.py",
                     "--lang", slug, "--workers", "2"], timeout=7200)
        if rc != 0:
            log(f"⚠ {slug}: nén audio lỗi (mã {rc}) — tiếp tục pack")
    else:
        log("   bỏ qua nén audio (SKIP_SHRINK=1)")
    rc, _ = run([py, "-X", "utf8", "tools/publish_online.py",
                 "--pack", "--lang", slug])
    if rc != 0:
        log(f"✗ {slug}: pack lỗi (mã {rc})")
        return False
    rc, _ = run([py, "-X", "utf8", "tools/upload_media_api.py",
                 "--lang", slug])
    if rc != 0:
        log(f"✗ {slug}: upload lỗi (mã {rc})")
        return False
    rc, _ = run([py, "-X", "utf8", "tools/publish_online.py", "--pages"])
    if rc != 0:
        log(f"✗ {slug}: pages lỗi (mã {rc})")
        return False
    rc, _ = run([py, "-X", "utf8", "tools/deploy_pages.py"], timeout=3600)
    if rc != 0:
        log(f"✗ {slug}: deploy lỗi (mã {rc})")
        return False
    try:
        import shutil
        shutil.rmtree(os.path.join(PUBLISH, slug), ignore_errors=True)
    except Exception:
        pass
    log(f"✅ {slug}: đã pack + upload + deploy xong")
    return True


def one_round(explicit: list[str] | None = None) -> int:
    st = load_state()
    todo = []
    if explicit:
        todo = [s for s in explicit if st.get(s, {}).get("status") != "done"]
    else:
        for slug in completed_from_log():
            if st.get(slug, {}).get("status") == "done":
                continue
            if days_done(slug) >= 2520:
                todo.append(slug)
    if not todo:
        return 0
    n_ok = 0
    for slug in dict.fromkeys(todo):
        ok = False
        for attempt in range(1, 4):
            if finalize(slug):
                ok = True
                break
            log(f"   ↻ thử lại {slug} lần {attempt}/3 sau 10 phút")
            time.sleep(600)
        st[slug] = {"status": "done" if ok else "failed",
                    "at": f"{datetime.now():%Y-%m-%d %H:%M:%S}"}
        save_state(st)
        n_ok += 1 if ok else 0
    return n_ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", action="append", default=[])
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--interval", type=int, default=300,
                    help="giây giữa 2 lần quét khi --watch")
    args = ap.parse_args()
    set_low_priority()
    if args.lang:
        log(f"finalize thủ công: {args.lang}")
        one_round(args.lang)
        return 0
    if args.once:
        n = one_round()
        log(f"lượt này xong {n} khóa")
        return 0
    log("BẮT ĐẦU canh fill_lite.log (Ctrl+C để dừng)")
    while True:
        try:
            one_round()
        except Exception as e:
            log(f"⚠ lỗi vòng quét: {e}")
        time.sleep(max(60, args.interval))


if __name__ == "__main__":
    sys.exit(main())
