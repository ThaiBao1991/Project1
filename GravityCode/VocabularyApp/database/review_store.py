"""
review_store.py — Lưu trạng thái ôn tập SRS (SM-2) BỀN theo từng ngôn ngữ.

Bảng `review_state` (JSON, 1 file / ngôn ngữ):
    data/reviews/<slug>.json
    {
      "schema": "vocabapp.review_state.v1",
      "lang": "Tiếng Nhật",
      "slug": "tiếng_nhật",
      "updated_at": "2026-10-22T10:00:00",
      "states": { "<từ>": {ease, interval, reps, lapses, due, last_review, state, streak} },
      "activity": ["2026-10-20", "2026-10-21"]   # các ngày có ôn tập
    }

Nguyên tắc:
  • Thuật toán nằm trong `ai/srs.py` (thuần stdlib) — module này chỉ lo LƯU.
  • Mọi ghi file ATOMIC (tmp + os.replace) + retry PermissionError (Windows).
  • KHÔNG BAO GIỜ raise ra ngoài: hỏng file ⇒ trả rỗng (không mất app).
  • Khoá theo ngôn ngữ để nhiều luồng (GUI + pipeline) không ghi đè nhau.
"""

from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime

from ai.paths import lang_slug
from ai.srs import (GRADES, STATE_NEW, build_queue, is_due, mastery_level,
                    mastery_stats, new_state, review, serialize, deserialize,
                    streak_from_days, longest_streak_from_days, daily_history)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REVIEWS_DIR = os.path.join(BASE_DIR, "data", "reviews")

REVIEW_SCHEMA = "vocabapp.review_state.v1"

# Khoá ghi — theo ngôn ngữ để 2 luồng cùng ngôn ngữ không ghi đè nhau.
_LOCKS: dict = {}
_LOCKS_GUARD = threading.Lock()


def _lock_for(slug: str) -> threading.RLock:
    with _LOCKS_GUARD:
        lk = _LOCKS.get(slug)
        if lk is None:
            lk = threading.RLock()
            _LOCKS[slug] = lk
        return lk


def reviews_dir() -> str:
    return REVIEWS_DIR


def reviews_path(language: str) -> str:
    """data/reviews/<slug>.json"""
    return os.path.join(REVIEWS_DIR, f"{lang_slug(language)}.json")


# ─── Ghi/đọc atomic ───────────────────────────────────────────────────────────
def _atomic_write(path: str, data: dict) -> bool:
    """Ghi JSON atomic. Trả True nếu thành công. Không raise."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    for attempt in range(10):
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except OSError:
                    pass
            os.replace(tmp, path)
            return True
        except PermissionError:
            # Windows: file đang bị mở đọc ở nơi khác ⇒ thử lại với backoff.
            time.sleep(0.05 * (attempt + 1))
            continue
        except OSError:
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except OSError:
                pass
            return False
    try:
        if os.path.exists(tmp):
            os.remove(tmp)
    except OSError:
        pass
    return False


def _read(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


# ─── API ──────────────────────────────────────────────────────────────────────
def load_all(language: str) -> dict:
    """Trả toàn bộ bảng review_state của 1 ngôn ngữ (dạng raw)."""
    data = _read(reviews_path(language))
    data.setdefault("schema", REVIEW_SCHEMA)
    data.setdefault("lang", language)
    data.setdefault("slug", lang_slug(language))
    states = data.get("states")
    data["states"] = states if isinstance(states, dict) else {}
    act = data.get("activity")
    data["activity"] = act if isinstance(act, list) else []
    return data


def load_states(language: str) -> dict:
    """{từ: state} đã chuẩn hoá (deserialize an toàn)."""
    raw = load_all(language).get("states") or {}
    out = {}
    for k, v in raw.items():
        if not isinstance(v, dict):
            continue
        try:
            out[str(k)] = deserialize(v)
        except Exception:
            continue
    return out


def save_all(language: str, data: dict) -> bool:
    data = dict(data or {})
    data["schema"] = REVIEW_SCHEMA
    data["lang"] = language
    data["slug"] = lang_slug(language)
    data["updated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    return _atomic_write(reviews_path(language), data)


def save_states(language: str, states: dict, activity: list = None) -> bool:
    """Ghi {từ: state} + danh sách ngày có hoạt động."""
    raw = {}
    for k, v in (states or {}).items():
        try:
            raw[str(k)] = serialize(v)
        except Exception:
            continue
    data = load_all(language)
    data["states"] = raw
    if activity is not None:
        data["activity"] = sorted({str(d) for d in activity})
    return save_all(language, data)


def get_state(language: str, word: str) -> dict:
    """State của 1 từ (tạo mới nếu chưa có)."""
    word = (word or "").strip()
    states = load_states(language)
    return states.get(word) or new_state()


def record_review(language: str, word: str, grade: str, relaxed: bool = False,
                  extra: dict = None) -> tuple:
    """Ghi 1 lần ôn. Trả (state, info).

    `extra` = dict thông tin đi kèm (ví dụ nghĩa tiếng Việt) để lưu lại cạnh
    state — giúp GUI hiển thị mà không cần tra course.json.
    """
    word = (word or "").strip()
    if not word:
        raise ValueError("word rỗng")
    if grade not in GRADES:
        raise ValueError(f"grade không hợp lệ: {grade!r}")
    slug = lang_slug(language)
    with _lock_for(slug):
        data = load_all(language)
        raw_states = data.get("states") or {}
        cur = raw_states.get(word)
        try:
            cur = deserialize(cur) if isinstance(cur, dict) else new_state()
        except Exception:
            cur = new_state()
        new_state_obj, info = review(cur, grade, relaxed=relaxed)
        raw_states[word] = serialize(new_state_obj)
        data["states"] = raw_states

        # hoạt động theo ngày
        today = datetime.now().strftime("%Y-%m-%d")
        act = [str(d) for d in (data.get("activity") or [])]
        if today not in act:
            act.append(today)
        data["activity"] = sorted(set(act))

        # thông tin phụ (nghĩa, ví dụ…) — lưu cạnh state
        if extra:
            meta = data.get("meta")
            if not isinstance(meta, dict):
                meta = {}
            meta[word] = {k: v for k, v in extra.items() if v not in (None, "")}
            data["meta"] = meta

        save_all(language, data)
        return new_state_obj, info


def due_queue(language: str, limit: int = 100, now: float = None) -> list:
    """Hàng đợi từ đến hạn (overdue → mới đến hạn → từ chưa học)."""
    return build_queue(load_states(language), now=now, limit=limit)


def is_due_now(language: str, word: str) -> bool:
    return is_due(get_state(language, word))


def stats(language: str) -> dict:
    """Thống kê tổng quan + streak cho 1 ngôn ngữ."""
    states = load_states(language)
    act = load_all(language).get("activity") or []
    base = mastery_stats(states)
    base["streak"] = streak_from_days(act)
    base["longest_streak"] = longest_streak_from_days(act)
    base["activity_days"] = len(act)
    base["language"] = language
    return base


def history(language: str, days: int = 30) -> list:
    """Lịch sử ôn theo ngày (cũ → mới)."""
    return daily_history(load_states(language), days=days)


def reset(language: str) -> bool:
    """Xoá toàn bộ tiến độ ôn tập của 1 ngôn ngữ."""
    with _lock_for(lang_slug(language)):
        return save_all(language, {"states": {}, "activity": [], "meta": {}})


def meta_for(language: str) -> dict:
    m = load_all(language).get("meta")
    return m if isinstance(m, dict) else {}


def sync_from_vocab(language: str, words: list, meaning_map: dict = None) -> int:
    """Đảm bảo mọi từ trong danh sách đều có 1 state (new). Trả số từ mới.

    Dùng khi người dùng mở chế độ ôn tập lần đầu: hàng đợi phải có từ mới.
    """
    meaning_map = meaning_map or {}
    with _lock_for(lang_slug(language)):
        data = load_all(language)
        raw = data.get("states")
        raw = raw if isinstance(raw, dict) else {}
        added = 0
        for w in words or []:
            w = str(w or "").strip()
            if not w:
                continue
            if w not in raw:
                raw[w] = serialize(new_state())
                added += 1
        data["states"] = raw
        if meaning_map:
            meta = data.get("meta")
            meta = meta if isinstance(meta, dict) else {}
            for w, m in meaning_map.items():
                if m and w not in meta:
                    meta[w] = {"meaning_vi": m}
            data["meta"] = meta
        save_all(language, data)
        return added


# ─── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    import argparse

    ap = argparse.ArgumentParser(description="Xem/tác động trạng thái ôn tập SRS")
    ap.add_argument("--lang", required=True)
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()

    if args.reset:
        print("Đã xoá:", reset(args.lang))
    else:
        st = stats(args.lang)
        for k, v in st.items():
            print(f"  {k}: {v}")
