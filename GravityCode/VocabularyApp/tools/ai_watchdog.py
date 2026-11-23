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
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proc_lock  # noqa: E402
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


def integrity() -> None:
    """Gói 9 (17/11): kiểm tra TOÀN VẸN — bắt khóa học bị 0 byte / plan lệch.

    Đo thật: 3 khóa bị mất trắng do 2 tiến trình ghi chung file tmp ⇒ file
    0 byte ⇒ không có gì báo lỗi cho tới khi người dùng mở app. Công cụ này
    chạy mỗi vòng watchdog ⇒ phát hiện NGAY và có thể khôi phục từ backup.
    """
    try:
        p = subprocess.run([sys.executable, "-X", "utf8", "tools/verify_integrity.py"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", cwd=BASE, timeout=1800)
        bad = [ln for ln in (p.stdout or "").splitlines() if ln.strip().startswith("⚠")]
        if bad:
            _log(f"⚠ TOÀN VẸN: {len(bad)} vấn đề — cần khôi phục!")
            for ln in bad[:10]:
                _log("   " + ln.strip()[:160])
        else:
            _log("✅ Toàn vẹn: mọi khóa học OK (days/plan/nghĩa Việt)")
    except Exception as e:
        _log(f"   verify_integrity lỗi: {e}")


WATCHDOG_LOCK = os.path.join(LOG_DIR, "watchdog.lock")


def _pid_alive(pid: int) -> bool:
    try:
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"],
                             capture_output=True, text=True, timeout=25)
        return str(pid) in (out.stdout or "")
    except Exception:
        return False


def acquire_watchdog_lock() -> bool:
    """Chỉ 1 watchdog chạy (Task Scheduler "chạy khi khởi động" + chạy tay
    có thể trùng ⇒ 2 tiến trình cùng ghi course.json ⇒ race)."""
    os.makedirs(LOG_DIR, exist_ok=True)
    if os.path.isfile(WATCHDOG_LOCK):
        try:
            with open(WATCHDOG_LOCK, encoding="utf-8") as f:
                old = int((f.read() or "0").strip() or 0)
        except Exception:
            old = 0
        if old and old != os.getpid() and _pid_alive(old):
            _log(f"⏭ Đã có watchdog khác đang chạy (PID {old}) — thoát.")
            return False
        try:
            os.remove(WATCHDOG_LOCK)
        except OSError:
            pass
    try:
        with open(WATCHDOG_LOCK, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))
    except OSError:
        pass
    return True


def release_watchdog_lock() -> None:
    try:
        with open(WATCHDOG_LOCK, encoding="utf-8") as f:
            if int((f.read() or "0").strip() or 0) == os.getpid():
                os.remove(WATCHDOG_LOCK)
    except Exception:
        pass


def media_lock_busy() -> bool:
    """Job bù media đang chạy? (dùng proc_lock: fill_media / fill_lite / supervisor)

    FIX 2026-11-15 (Gói 7): AI (watchdog) và media (fill_media) CÙNG ghi
    `course.json` của một khóa ⇒ race.
    FIX 2026-11-21: chỉ kiểm `fill_media.lock` là thiếu — supervisor
    (`fill_remaining`) và `fill_lite` dùng lock khác.
    FIX 2026-11-22: lock chuyển sang `D:\\VocabularyAppData\\state\\locks`
    (data/logs từng bị xoá ngoài ý muốn); proc_lock tự đọc cả lock cũ.
    """
    return any(proc_lock.holder(n) for n in
               ("fill_media", "fill_lite", "fill_remaining"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--lang", default="")
    ap.add_argument("--sleep", type=int, default=900, help="nghỉ giữa các vòng (giây)")
    args = ap.parse_args()
    langs = [args.lang] if args.lang else ALL_LANGS
    os.makedirs(LOG_DIR, exist_ok=True)
    if not acquire_watchdog_lock():
        return 0
    _log(f"=== WATCHDOG bắt đầu · khóa: {', '.join(langs)} ===")
    try:
        return _loop(langs, args)
    finally:
        release_watchdog_lock()


def _loop(langs, args) -> int:
    while True:
        t0 = time.time()
        _log("──────── VÒNG: AI + MEDIA XEN KẼ (mỗi khóa) ────────")
        # FIX 2026-11-15: nếu job bù media đang chạy (fill_media giữ lock) ⇒
        # watchdog NHƯỜNG vòng AI để 2 tiến trình không ghi chung course.json.
        if media_lock_busy():
            _log("⏸ Job bù media đang chạy — bỏ qua vòng AI lần này "
                 "(media 0 quota, làm được mọi lúc; AI chờ vòng sau).")
        else:
            for lg in langs:
                # FIX 2026-11-17 (Gói 9): kiểm tra lock media TRƯỚC **MỖI KHÓA**
                # (trước đây chỉ 1 lần đầu vòng ⇒ job media có thể khởi động
                # giữa vòng ⇒ 2 tiến trình cùng ghi course.json của 1 khóa).
                if media_lock_busy():
                    _log(f"⏸ Job bù media đang chạy — bỏ qua AI {lg} "
                         f"(media 0 quota, làm được mọi lúc).")
                    break
                # Timeout 45 phút/khóa: hết quota thì bỏ qua (checkpoint đã lưu,
                # resume được) để watchdog KHÔNG bị kẹt chờ.
                _run([sys.executable, "-X", "utf8", "-m", "ai.pipeline",
                      "--lang", lg, "--stages", "content,quiz_ab,quiz_cd,dialogue",
                      "--days", "9999", "--workers", "4", "--wait-quota",
                      "--max-calls-per-day", "1200"], 45 * 60, f"AI {lg}")
                # (Gói 7) Bước media KHÔNG chạy tuần tự ở đây nữa — nó chạy
                # SONG SONG cho cả 8 khóa ở cuối vòng (xem bên dưới). Chạy tuần tự
                # tốn 8 × 6h = 48h cho 1 vòng ⇒ quá chậm.
        # ── VÒNG BÙ MEDIA SONG SONG (Gói 7) ──────────────────────────────────
        # tools/fill_media.py có LOCK ⇒ không tranh với job media thủ công.
        _run([sys.executable, "-X", "utf8", "tools/fill_media.py",
              "--jobs", "1", "--workers", "1", "--rounds", "1"],
             8 * 3600, "bù media TUẦN TỰ (an toàn đĩa)")
        _log("──────── VÒNG C: VERIFY + THÔNG BÁO ────────")
        verify(langs)
        integrity()
        # Gói 9 (17/11): dọn file .tmp sót (job bị kill) + backup cũ ⇒ giải
        # phóng ~400 MB mỗi lần máy bị tắt/kill.
        _run([sys.executable, "-X", "utf8", "tools/cleanup_temp.py"],
             10 * 60, "dọn file tạm + backup cũ")
        # Kiểm tra "đã đủ chưa" ⇒ TỰ THÔNG BÁO Windows cho người dùng
        try:
            subprocess.run([sys.executable, "-X", "utf8", "tools/check_done.py"],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", cwd=BASE, timeout=1800)
        except Exception as _e:
            _log(f"   check_done lỗi: {_e}")
        _log(f"── xong vòng sau {(time.time()-t0)/60:.1f} phút ──")
        if args.once:
            break
        time.sleep(max(60, args.sleep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
