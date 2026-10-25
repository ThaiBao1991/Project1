"""
srs.py — Module SRS (Spaced Repetition) thuần thuật toán, quản lý lịch ôn tập.

Thuật toán: SM-2 (SuperMemo 2) — biến thể 4 nút (again / hard / good / easy)
nhưng giữ đúng công thức lõi của SM-2:

    • Hệ số độ khó EF (ease) ∈ [EASE_MIN, EASE_MAX] = [1.3, 2.8], mặc định 2.5
    • Nhớ đúng ⇒ interval (ngày) *= ease
    • Quên (again) ⇒ reps = 0, lapses += 1, ease -= 0.2, lùi về bước học 1 phút
    • Interval bị chặn trần MAX_INTERVAL (365 ngày)

Module THUẦN stdlib: KHÔNG import tkinter, KHÔNG import VocabApp, KHÔNG đụng DB.
Dùng được cả cho desktop lẫn web (API/server).
"""

from __future__ import annotations

import json
import sys
import time
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence, Tuple

# ─── Hằng số thuật toán ──────────────────────────────────────────────────────
DAY = 86400                  # số giây trong 1 ngày
EASE_MIN = 1.3               # ease thấp nhất (dễ quên)
EASE_MAX = 2.8               # ease cao nhất (dễ nhớ)
EASE_DEFAULT = 2.5           # ease khởi tạo
LEARNING_STEPS = [1, 10]     # bước học (phút): 1 phút → 10 phút
GRADUATING_INTERVAL = 1      # ngày — khi bước học hoàn tất
EASY_INTERVAL = 4            # ngày — nhấn "easy" ngay từ đầu
MAX_INTERVAL = 365           # ngày — trần interval
RELAXED_MULTIPLIER = 1.3     # lịch "ngắn" (người bận) = lịch chuẩn * 1.3

# Ngưỡng coi là đã "thuộc" — đạt mastered khi interval >= 21 ngày VÀ reps >= 4
MASTERED_INTERVAL_DAYS = 21
MASTERED_REPS = 4

# ─── Nút đánh giá ────────────────────────────────────────────────────────────
GRADES = ("again", "hard", "good", "easy")
GRADE_LABELS_VI = {
    "again": "😵 Quên hẳn",
    "hard": "😕 Khó",
    "good": "🙂 Được",
    "easy": "😎 Rất dễ",
}

STATE_NEW = "new"
STATE_LEARNING = "learning"
STATE_REVIEW = "review"
STATE_MASTERED = "mastered"


# ─── Tiện ích nội bộ ────────────────────────────────────────────────────────
def _now(now: Optional[float] = None) -> float:
    """Thời điểm hiện tại (epoch giây); nếu truyền `now` thì dùng luôn."""
    return time.time() if now is None else float(now)


def _clamp_ease(ease: float) -> float:
    """Kẹp ease trong [EASE_MIN, EASE_MAX] và làm tròn 2 chữ số (tránh 2.3000000000000003)."""
    return round(min(max(float(ease), EASE_MIN), EASE_MAX), 2)


def _iso(ts: float) -> str:
    """Chuyển timestamp → chuỗi ISO-8601 giờ địa phương."""
    return datetime.fromtimestamp(float(ts)).isoformat(timespec="seconds")


def _to_date(value: Any) -> Optional[date]:
    """Chuẩn hoá nhiều kiểu ngày về datetime.date (str 'YYYY-MM-DD' / date / datetime)."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        raw = value.strip()[:10]
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


# ─── Trạng thái ──────────────────────────────────────────────────────────────
def new_state(now: Optional[float] = None) -> Dict[str, Any]:
    """Tạo state mới cho một từ chưa học lần nào."""
    t = _now(now)
    return {
        "ease": EASE_DEFAULT,
        "interval": 0.0,
        "reps": 0,
        "lapses": 0,
        "due": t,
        "last_review": None,
        "state": STATE_NEW,
        "streak": 0,
    }


def deserialize(d: Dict[str, Any]) -> Dict[str, Any]:
    """Chuẩn hoá dict lưu trữ (JSON) về state đầy đủ, an toàn với thiếu/sai kiểu."""
    if not isinstance(d, dict):
        raise TypeError("state phải là dict")
    out = new_state()
    for key in ("ease", "interval", "reps", "lapses", "due", "last_review", "state", "streak"):
        if d.get(key) is not None:
            out[key] = d[key]
    out["ease"] = _clamp_ease(out["ease"])
    out["interval"] = max(0.0, float(out["interval"]))
    out["reps"] = int(out["reps"])
    out["lapses"] = int(out["lapses"])
    out["streak"] = int(out["streak"])
    out["due"] = float(out["due"])
    out["last_review"] = None if out["last_review"] is None else float(out["last_review"])
    if out["state"] not in (STATE_NEW, STATE_LEARNING, STATE_REVIEW):
        out["state"] = STATE_REVIEW if out["reps"] > 0 else STATE_NEW
    return out


def serialize(state: Dict[str, Any]) -> Dict[str, Any]:
    """Xuất state ra dict JSON-safe (chỉ int / float / str / None)."""
    st = deserialize(state)
    return {
        "ease": round(float(st["ease"]), 2),
        "interval": round(float(st["interval"]), 9),
        "reps": int(st["reps"]),
        "lapses": int(st["lapses"]),
        "due": round(float(st["due"]), 6),
        "last_review": None if st["last_review"] is None else round(float(st["last_review"]), 6),
        "state": str(st["state"]),
        "streak": int(st["streak"]),
    }


# ─── Lõi thuật toán SM-2 ─────────────────────────────────────────────────────
def review(
    state: Dict[str, Any],
    grade: str,
    now: Optional[float] = None,
    relaxed: bool = False,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Ôn một từ theo SM-2. Trả về (new_state, info).

    grade: "again" | "hard" | "good" | "easy"
    relaxed: True ⇒ nhân interval thêm RELAXED_MULTIPLIER (lịch ngắn cho người bận).
             Hệ số được áp TRƯỚC khi tính `due` để due luôn khớp interval.
    """
    if grade not in GRADES:
        raise ValueError(f"grade không hợp lệ: {grade!r} (chọn trong {GRADES})")

    t = _now(now)
    st = deserialize(state)
    prev_interval = float(st["interval"])
    prev_state = str(st["state"])
    ease = float(st["ease"])
    reps = int(st["reps"])
    lapses = int(st["lapses"])
    streak = int(st["streak"])

    if grade == "again":
        # Quên hẳn ⇒ reset chuỗi, giảm ease, lùi về bước học đầu tiên (1 phút).
        reps = 0
        lapses += 1
        ease -= 0.2
        interval = LEARNING_STEPS[0] / 60.0
        new_state_name = STATE_LEARNING
        streak = 0

    elif grade == "hard":
        # Khó ⇒ giảm ease nhẹ, nhân interval 1.2 (tối thiểu 1 ngày).
        ease -= 0.15
        interval = max(1.0, prev_interval * 1.2) if prev_interval > 0 else 1.0
        new_state_name = STATE_REVIEW
        reps += 1
        streak += 1

    elif grade == "good":
        # Đúng ⇒ đi tiếp bước học / nhân ease, hoặc nhảy lên 1 & 3 ngày ở các mốc.
        if prev_interval == 0:
            interval = LEARNING_STEPS[1] / 60.0            # bước học thứ 2 (10 phút)
        elif prev_interval < 1:
            interval = float(GRADUATING_INTERVAL)          # tốt nghiệp bước học → 1 ngày
        elif prev_interval == 1:
            interval = 3.0                                 # mốc 1 ngày → 3 ngày
        else:
            interval = prev_interval * ease                # lõi SM-2: I(n) = I(n-1) * EF
        new_state_name = STATE_REVIEW
        reps += 1
        streak += 1

    else:  # "easy"
        # Rất dễ ⇒ nhân interval * ease * 1.3 rồi mới tăng ease (thứ tự theo spec).
        if prev_interval == 0:
            interval = float(GRADUATING_INTERVAL) if prev_state == STATE_NEW else float(EASY_INTERVAL)
        else:
            interval = prev_interval * ease * 1.3
        ease += 0.15
        new_state_name = STATE_REVIEW
        reps += 1
        streak += 1

    ease = _clamp_ease(ease)
    interval = max(0.0, float(interval))
    if relaxed:
        interval *= RELAXED_MULTIPLIER
    interval = min(interval, float(MAX_INTERVAL))
    due = t + interval * DAY

    new_st = {
        "ease": ease,
        # Giữ nguyên độ chính xác float ⇒ due == last_review + interval*DAY tuyệt đối.
        "interval": interval,
        "reps": reps,
        "lapses": lapses,
        "due": due,
        "last_review": t,
        "state": new_state_name,
        "streak": streak,
    }
    info = {
        "interval_days": round(interval, 6),
        "due_iso": _iso(due),
        "ease": ease,
        "label": GRADE_LABELS_VI[grade],
        "next_review_in_days": round(interval, 2),
        "next_review_in_minutes": round(interval * 1440.0, 1),
        "grade": grade,
        "state": new_state_name,
    }
    return new_st, info


def is_due(state: Dict[str, Any], now: Optional[float] = None) -> bool:
    """Từ đã tới hạn ôn chưa (now >= due)."""
    t = _now(now)
    if not isinstance(state, dict):
        return False
    due = float(state.get("due") or 0.0)
    return t >= due


# ─── Hàng đợi ôn tập ─────────────────────────────────────────────────────────
def build_queue(
    states: Dict[str, Dict[str, Any]],
    now: Optional[float] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Dựng hàng đợi ôn tập. Thứ tự:
        1. Quá hạn (due < now)      — sắp theo due tăng dần (quá hạn lâu nhất lên đầu)
        2. Mới đến hạn (trong ~24h)  — sắp theo due tăng dần
        3. Từ "new" (chưa học lần nào)
    Từ chưa tới hạn (> 24h) bị loại khỏi hàng đợi.
    """
    t = _now(now)
    limit = int(limit)
    if limit <= 0:
        return []

    overdue: List[Dict[str, Any]] = []
    due_now: List[Dict[str, Any]] = []
    fresh: List[Dict[str, Any]] = []

    for key, raw in (states or {}).items():
        if not isinstance(raw, dict):
            continue
        due = float(raw.get("due") or 0.0)
        sstate = raw.get("state") or STATE_NEW
        never_seen = sstate == STATE_NEW and not raw.get("last_review")
        item = {
            "key": key,
            "due": due,
            "state": sstate,
            "overdue_days": 0.0,
        }
        if never_seen:
            fresh.append(item)
        elif due < t:
            item["overdue_days"] = round((t - due) / DAY, 4)
            overdue.append(item)
        elif due <= t + DAY:
            due_now.append(item)
        # còn lại: chưa tới hạn → không đưa vào hàng đợi

    overdue.sort(key=lambda it: it["due"])
    due_now.sort(key=lambda it: it["due"])
    fresh.sort(key=lambda it: it["due"])
    return (overdue + due_now + fresh)[:limit]


# ─── Mức độ thuộc ───────────────────────────────────────────────────────────
def mastery_level(state: Dict[str, Any]) -> str:
    """Phân loại: new | learning | review | mastered."""
    if not isinstance(state, dict):
        return STATE_NEW
    reps = int(state.get("reps") or 0)
    last_review = state.get("last_review")
    if not last_review and reps == 0:
        return STATE_NEW
    interval = float(state.get("interval") or 0.0)
    if interval >= MASTERED_INTERVAL_DAYS and reps >= MASTERED_REPS:
        return STATE_MASTERED
    if state.get("state") == STATE_LEARNING:
        return STATE_LEARNING
    return STATE_REVIEW


def mastery_stats(states: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Thống kê tổng quan thuộc/đến hạn cho toàn bộ từ đang học."""
    items = [(k, v) for k, v in (states or {}).items() if isinstance(v, dict)]
    total = len(items)
    counts = {STATE_NEW: 0, STATE_LEARNING: 0, STATE_REVIEW: 0, STATE_MASTERED: 0}
    easies: List[float] = []
    intervals: List[float] = []
    due_today = 0
    t = _now()
    for _key, v in items:
        counts[mastery_level(v)] += 1
        easies.append(float(v.get("ease") if v.get("ease") is not None else EASE_DEFAULT))
        intervals.append(float(v.get("interval") or 0.0))
        if is_due(v, t):
            due_today += 1
    return {
        "total": total,
        "new": counts[STATE_NEW],
        "learning": counts[STATE_LEARNING],
        "review": counts[STATE_REVIEW],
        "mastered": counts[STATE_MASTERED],
        "mastery_pct": round(counts[STATE_MASTERED] * 100.0 / total, 1) if total else 0.0,
        "due_today": due_today,
        "avg_ease": round(sum(easies) / len(easies), 2) if easies else 0.0,
        "avg_interval_days": round(sum(intervals) / len(intervals), 2) if intervals else 0.0,
    }


# ─── Chuỗi ngày học & lịch sử ───────────────────────────────────────────────
def streak_from_days(days_with_activity: Sequence[Any]) -> int:
    """
    Chuỗi ngày học liên tiếp hiện tại. Nhận list "YYYY-MM-DD" hoặc datetime.date.
    Chuỗi tính từ hôm nay; nếu hôm nay chưa học thì lùi về hôm qua.
    """
    dates = set()
    for value in days_with_activity or []:
        d = _to_date(value)
        if d is not None:
            dates.add(d)
    if not dates:
        return 0
    today = date.today()
    if today in dates:
        cur = today
    elif (today - timedelta(days=1)) in dates:
        cur = today - timedelta(days=1)
    else:
        return 0
    count = 0
    while cur in dates:
        count += 1
        cur -= timedelta(days=1)
    return count


def longest_streak_from_days(days_with_activity: Sequence[Any]) -> int:
    """Chuỗi ngày học liên tiếp dài nhất trong lịch sử (bổ trợ cho streak hiện tại)."""
    dates = sorted({d for d in (_to_date(v) for v in (days_with_activity or [])) if d is not None})
    best = 0
    run = 0
    prev: Optional[date] = None
    for d in dates:
        run = run + 1 if prev is not None and d - prev == timedelta(days=1) else 1
        best = max(best, run)
        prev = d
    return best


def daily_history(states: Dict[str, Dict[str, Any]], days: int = 30) -> List[Dict[str, Any]]:
    """
    Lịch sử ôn theo ngày (cũ → mới), đủ `days` ngày, ngày không có thì reviews = 0.
    Nguồn dữ liệu: `last_review` của mỗi state (mỗi từ chỉ tính 1 lần ở ngày ôn gần nhất).
    """
    days = max(1, int(days))
    today = date.today()
    counts: Dict[date, int] = {}
    for _key, v in (states or {}).items():
        if not isinstance(v, dict):
            continue
        last_review = v.get("last_review")
        if last_review is None:
            continue
        try:
            d = datetime.fromtimestamp(float(last_review)).date()
        except (ValueError, OSError, OverflowError):
            continue
        counts[d] = counts.get(d, 0) + 1
    history: List[Dict[str, Any]] = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        history.append({"date": d.isoformat(), "reviews": counts.get(d, 0)})
    return history


# ─── Demo ────────────────────────────────────────────────────────────────────
def _demo() -> None:
    """Demo: chuỗi grade again → good → good → easy → good, bắt đầu từ 1 ngày trước."""
    # Console Windows mặc định cp1252 → ép UTF-8 để in được tiếng Việt + emoji.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    chain = ["again", "good", "good", "easy", "good"]
    t = time.time() - DAY          # bắt đầu hôm qua
    state = new_state(t)
    print("=== DEMO SM-2 — chuỗi again → good → good → easy → good (bắt đầu 1 ngày trước) ===")
    print(f"{'lần':>4}  {'grade':<6} {'interval':>12}  {'due':<26} {'ease':>5} {'state':<9} label")
    for i, g in enumerate(chain, 1):
        state, info = review(state, g, now=t)
        interval_txt = f"{info['interval_days']:.4f} ngày"
        print(
            f"{i:>4}  {g:<6} {interval_txt:>12}  {info['due_iso']:<26} "
            f"{info['ease']:>5.2f} {info['state']:<9} {info['label']}"
        )
        # lần ôn sau diễn ra đúng lúc đến hạn
        t = state["due"]
    print("\nState cuối (JSON-safe):")
    print(json.dumps(serialize(state), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    _demo()
