"""
pipeline_control.py — Trạng thái pipeline DÙNG CHUNG giữa GUI và Dashboard web.

Mục tiêu (Dashboard web localhost — xem UPGRADE_17 §7.16):
  • STOP_EVENT singleton: nút ⏹ ở GUI và nút ⏹ ở web set CÙNG 1 sự kiện
    → pipeline dừng ≤1s (đã fix ở 02817454: stop_check truyền tới request()).
  • LOG buffer ring: mọi dòng log (GUI `_log` ghi vào / run từ web ghi thẳng)
    vào 1 buffer có id tăng dần → dashboard poll `since_id` chỉ nhận dòng MỚI.
  • STATUS: running/source/language/pct/day… → Start bị guard 2 phía:
    GUI đang chạy → web từ chối; web đang chạy → GUI từ chối.

An toàn: server bind 127.0.0.1 (bridge_server) + auth token → không mở LAN.
"""

import threading
import time
from collections import deque

# ── Dừng: 1 sự kiện duy nhất cho cả GUI lẫn web ───────────────────────────
STOP_EVENT = threading.Event()

# ── Log buffer (ring, id tăng dần) ─────────────────────────────────────────
_MAX_LOG_LINES = 2000
_log_lock = threading.Lock()
_log_lines = deque(maxlen=_MAX_LOG_LINES)   # dict {"id", "t", "msg"}
_log_seq = 0


def log_append(msg):
    """Thêm 1 dòng log vào buffer (thread-safe). Trả về dòng vừa ghi."""
    global _log_seq
    try:
        text = str(msg if msg is not None else "")
    except Exception:
        text = repr(msg)
    with _log_lock:
        _log_seq += 1
        line = {"id": _log_seq, "t": time.strftime("%H:%M:%S"), "msg": text}
        _log_lines.append(line)
        return line


def log_snapshot(since_id: int = 0) -> dict:
    """Trả {"lines": [các dòng id > since_id], "last_id": id lớn nhất hiện có}."""
    with _log_lock:
        lines = [dict(x) for x in _log_lines if x["id"] > since_id]
        last_id = _log_seq
    return {"lines": lines, "last_id": last_id}


# ── STATUS dùng chung ──────────────────────────────────────────────────────
_status_lock = threading.Lock()
STATUS = {
    "running": False,
    "source": "",            # "gui" | "web"
    "language": "",
    "level": "",
    "mode": "",
    "pct": 0.0,
    "day": 0,
    "total_days": 0,
    "stage": "",
    "started_at": 0.0,
    "finished_at": 0.0,
    "last_result": None,     # dict nhỏ từ run_pipeline / {"ok","error"}
}


def is_running() -> bool:
    with _status_lock:
        return bool(STATUS["running"])


def set_running(running: bool, source: str = "", language: str = "",
                level: str = "", mode: str = "", total_days: int = 0):
    with _status_lock:
        STATUS["running"] = bool(running)
        if running:
            STATUS["source"] = source or STATUS["source"]
            STATUS["language"] = language
            STATUS["level"] = level
            STATUS["mode"] = mode
            STATUS["pct"] = 0.0
            STATUS["day"] = 0
            STATUS["total_days"] = int(total_days or 0)
            STATUS["stage"] = ""
            STATUS["started_at"] = time.time()
            STATUS["finished_at"] = 0.0
            STATUS["last_result"] = None
        else:
            STATUS["finished_at"] = time.time()


def set_progress(p: dict):
    """Nhận payload từ on_progress của run_pipeline: {pct, stage, day}."""
    if not isinstance(p, dict):
        return
    with _status_lock:
        try:
            STATUS["pct"] = float(p.get("pct", STATUS["pct"]) or 0.0)
        except Exception:
            pass
        if p.get("stage"):
            STATUS["stage"] = str(p["stage"])
        if p.get("day") is not None:
            try:
                STATUS["day"] = int(p["day"])
            except Exception:
                pass
        if p.get("total_days") is not None:
            try:
                STATUS["total_days"] = int(p["total_days"])
            except Exception:
                pass


def status_snapshot() -> dict:
    with _status_lock:
        st = dict(STATUS)
    st["stop_requested"] = STOP_EVENT.is_set()
    if st["running"] and st["started_at"]:
        st["elapsed_s"] = max(0, int(time.time() - st["started_at"]))
    else:
        st["elapsed_s"] = 0
    return st


def request_stop() -> bool:
    """Yêu cầu DỪNG (từ web). Trả True nếu đang có run để dừng."""
    running = is_running()
    STOP_EVENT.set()
    if running:
        log_append("⏹ Dashboard: yêu cầu DỪNG — pipeline sẽ dừng trong ≤1s.")
    else:
        log_append("⏹ Dashboard: Dừng khi chưa có run nào (đã set stop event).")
    return running


# ── Start từ web ───────────────────────────────────────────────────────────
def _run_pipeline(language: str, opts: dict):
    """Tách riêng để TEST mock (không gọi mạng thật)."""
    from ai.pipeline import run_pipeline
    return run_pipeline(language,
                        stop_check=STOP_EVENT.is_set,
                        log_fn=log_append,
                        on_progress=set_progress,
                        allow_degraded=True,
                        workers=4,
                        **opts)


def _runner(language: str, opts: dict, source: str):
    res = None
    try:
        res = _run_pipeline(language, opts)
        log_append(f"🏁 Dashboard: {res.get('status', '?').upper()} — "
                   f"{res.get('days_done', 0)}/{res.get('total_days', 0)} ngày, "
                   f"calls={res.get('calls', 0)}, ảnh={res.get('images', 0)}.")
    except Exception as e:
        log_append(f"❌ Dashboard: lỗi run pipeline: {type(e).__name__}: {e}")
        res = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    finally:
        # Giữ lại vài trường chính (JSON-able), bỏ phần nặng
        small = None
        if isinstance(res, dict):
            small = {k: res.get(k) for k in
                     ("ok", "status", "days_done", "total_days", "calls",
                      "images", "errors") if k in res}
        with _status_lock:
            STATUS["running"] = False
            STATUS["finished_at"] = time.time()
            STATUS["last_result"] = small
        STOP_EVENT.clear()   # không để trạng thái dừng dính sang run sau


def start_pipeline(language: str, *, words_per_day: int = 10,
                   level: str = None, target_days: int = None,
                   mode: str = "full", force_new: bool = False,
                   media: bool = True, source: str = "web"):
    """Khởi chạy pipeline trong thread nền. Trả (ok, reason)."""
    language = str(language or "").strip()
    if not language:
        return False, "missing_language"
    with _status_lock:
        if STATUS["running"]:
            return False, f"already_running:{STATUS['source'] or '?'}"
        STATUS.update(running=True, source=source or "web",
                      language=language, level=level or "",
                      mode=mode, pct=0.0, day=0,
                      total_days=int(target_days or 0), stage="",
                      started_at=time.time(), finished_at=0.0,
                      last_result=None)
    STOP_EVENT.clear()   # start mới luôn bỏ lệnh dừng cũ
    log_append(f"▶ Dashboard: bắt đầu sinh '{language}' "
               f"(level={level or 'mặc định'}, {words_per_day} từ/ngày, "
               f"target={target_days or 'toàn khóa'}, mode={mode}"
               f"{', force_new' if force_new else ''}).")
    opts = {
        "words_per_day": int(words_per_day or 10),
        "level": level,
        "target_days": int(target_days) if target_days else None,
        "full": True,
        "mode": mode if mode in ("full", "media", "enrich") else "full",
        "force_new": bool(force_new),
        "media": bool(media),
    }
    threading.Thread(target=_runner, args=(language, opts, source or "web"),
                     name="dash-pipeline", daemon=True).start()
    return True, "started"
