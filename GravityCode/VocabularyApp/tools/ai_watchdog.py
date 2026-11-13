# -*- coding: utf-8 -*-
"""tools/ai_watchdog.py — VÒNG LẶP 24/7: AI làm phần CẦN AI, offline làm phần KHÔNG cần AI.

Quota Gemini reset 00:00 giờ VN mỗi ngày ⇒ thay vì chạy 1 lần rồi dừng,
watchdog lặp vô hạn:
  Vòng A (CẦN AI — nội dung tự nhiên): content · quiz · hội thoại · ngữ pháp
        → `--wait-quota`: hết quota thì NGỦ chờ reset rồi chạy tiếp.
  Vòng B (KHÔNG cần AI — 0 quota): ảnh (Wikipedia) + audio (edge-TTS) + verify
        → bù media cho những ngày AI vừa sinh.
  Vòng C: verify + ghi báo cáo độ đầy đủ.

Mỗi vòng ghi log ra `data/logs/watchdog.log` + `data/logs/watchdog_status.txt`.

Cách dùng:
  python tools/ai_watchdog.py                  # lặp vô hạn (nền)
  python tools/ai_watchdog.py --once           # 1 vòng rồi thoát
  python tools/ai_watchdog.py --lang tiếng_nhật
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ALL_LANGS = ["tiếng_nhật", "tiếng_trung", "tiếng_anh", "tiếng_hàn_quốc",
              "tiếng_nga", "tiếng_pháp", "tiếng_trung", "tiếng_tây_ban_nha",
              "tiếng_đức"]
LOG_DIR = os.path.join(BASE, "data", "logs")
STATUS = os.path.join(LOG_DIR, "watchdog_status.txt")


def _log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def _run(cmd, timeout, label):
    _log(f"▶ {label}")
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout, cwd=BASE)
        out = (p.stdout or "") + (p.stderr or "")
        tail = [x for x in out.splitlines()
                if any(k in x for k in ("PAUSED", "DONE", "đã xử lý", "Pass bù",
                                       "DoD", "đang chờ", "Chờ ngân sách"))][-4:]
        for x in tail:
            _log("   " + x.strip()[:150])
        return p.returncode
    except subprocess.TimeoutExpired:
        _log(f"   ⏱ {label}: hết {timeout/3600:.1f}h → chuyển khóa sau")
        return -1


def verify(langs):
    out = []
    for lg in langs:
        p = subprocess.run([sys.executable, "-X", "utf8", "tools/verify_courses.py",
                            "--lang", lg], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", cwd=BASE)
        for line in (p.stdout or "").splitlines():
            if line.strip().startswith(lg[:12]):
                out.append(line.strip())
    if out:
        with open(STATUS, "w", encoding="utf-8") as f:
            f.write(f"cập nhật {datetime.now().isoformat(timespec='seconds')}\n")
            f.write("\n".join(out) + "\n")
        for line in out:
            _log("   " + line)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--lang", default="")
    ap.add_argument("--sleep", type=int, default=900, help="nghỉ giữa các vòng (giây)")
    args = ap.parse_args()
    langs = [args.lang] if args.lang else ALL_LANGS
    os.makedirs(LOG_DIR, exist_ok=True)
    _log(f"=== WATCHDOG bắt đầu · khóa: {', '.join(langs)} ===")
    while True:
        t0 = time.time()
        _log("──────── VÒNG: AI + MEDIA XEN KẼ (mỗi khóa) ────────")
        for lg in langs:
            # Timeout 45 phút/khóa: hết quota thì bỏ qua (checkpoint đã lưu,
            # resume được) để watchdog KHÔNG bị kẹt chờ.
            # XEN KẼ: sau khi thử AI cho khóa này → bù media NGAY cho khóa này
            # (không đợi hết 9 khóa) ⇒ "phần không cần AI thì tiếp tục liền".
            _run([sys.executable, "-X", "utf8", "-m", "ai.pipeline",
                  "--lang", lg, "--stages", "content,quiz_ab,quiz_cd,dialogue",
                  "--days", "9999", "--workers", "4", "--wait-quota",
                  "--max-calls-per-day", "1200"], 45 * 60, f"AI {lg}")
            _run([sys.executable, "-X", "utf8", "-m", "ai.pipeline",
                  "--lang", lg, "--stages", "images,audio,media_verify",
                  "--days", "9999", "--workers", "2"], 6 * 3600, f"media {lg}")
        _log("──────── VÒNG C: VERIFY ────────")
        verify(langs)
        _log(f"── xong vòng sau {(time.time()-t0)/60:.1f} phút ──")
        if args.once:
            break
        time.sleep(max(60, args.sleep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
