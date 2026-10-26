"""
diag_srs.py — Mô phỏng SRS (SM-2) cho 20 từ trong 30 ngày, in tiến trình thuộc.

Kiểm chứng thực tế:
    1. 20 từ học trong 30 ngày → in bảng tiến trình mastery từng ngày
    2. Queue ôn tập (quá hạn / đến hạn / mới), lịch sử 30 ngày, streak
    3. 12 phép kiểm tra edge-case (assert) trên chính module ai.srs

Chạy:  python tools\\diag_srs.py
"""

import json
import os
import random
import sys
import time
from collections import defaultdict
from datetime import date, datetime, timedelta

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE not in sys.path:
    sys.path.insert(0, BASE)

from ai import srs  # noqa: E402

# ─── Tham số mô phỏng ────────────────────────────────────────────────────────
N_WORDS = 20
SIM_DAYS = 30
SEED = 20261022
STEP = 600                 # lưới thời gian 10 phút (đủ để bắt bước học 1 phút)
MAX_REVIEWS_PER_CARD_PER_DAY = 4
JITTER = 0.9 * STEP        # người dùng ôn trễ hơn hạn một chút

rng = random.Random(SEED)
NOW = time.time()
T0 = NOW - SIM_DAYS * srs.DAY

# 20 từ: 4 nhóm độ khó khác nhau
DIFFS = {}
for i in range(N_WORDS):
    group = i % 4                      # 0 dễ, 1 khá dễ, 2 khó, 3 rất khó
    DIFFS[f"w{i + 1:02d}"] = (0.05, 0.18, 0.35, 0.55)[group]


def pick_grade(state, key):
    """Mô phỏng người học: nhớ được thì good/easy, quên thì again."""
    diff = DIFFS[key]
    lapses = state.get("lapses", 0)
    interval = float(state.get("interval") or 0.0)
    p_recall = 0.94 - 0.50 * diff - 0.02 * lapses
    p_recall = min(max(p_recall, 0.35), 0.97)
    if rng.random() >= p_recall:
        return "again"
    if interval >= 21:
        weights = (0.05, 0.17, 0.78)      # hard, easy, good
    elif interval >= 7:
        weights = (0.07, 0.22, 0.71)
    else:
        weights = (0.10, 0.13, 0.77)
    return rng.choices(("hard", "easy", "good"), weights=weights, k=1)[0]


def run_simulation():
    """Chạy mô phỏng 30 ngày, trả về states + bảng tiến trình từng ngày."""
    states = {k: srs.new_state(T0) for k in DIFFS}
    per_card_day = defaultdict(int)
    daily_counts = defaultdict(int)
    progression = [{
        "date": datetime.fromtimestamp(T0).date(),
        "reviews": 0,
        "stats": srs.mastery_stats(states),   # trạng thái trước khi học: 20 từ "new"
    }]

    for day in range(SIM_DAYS):
        day_start = T0 + day * srs.DAY
        day_end = day_start + srs.DAY
        day_key = datetime.fromtimestamp(day_start).date()
        t = day_start
        while t <= min(day_end, NOW):
            for key in list(states.keys()):
                st = states[key]
                if float(st["due"]) > t:
                    continue
                if per_card_day[(key, day_key)] >= MAX_REVIEWS_PER_CARD_PER_DAY:
                    continue
                review_at = t + rng.uniform(0.05, 1.0) * JITTER
                grade = pick_grade(st, key)
                states[key], _info = srs.review(st, grade, now=review_at)
                per_card_day[(key, day_key)] += 1
                daily_counts[day_key] += 1
            t += STEP
        stats = srs.mastery_stats(states)
        progression.append({
            "date": day_key,
            "reviews": daily_counts.get(day_key, 0),
            "stats": stats,
        })
    return states, progression, daily_counts


def print_progression(progression):
    print("=== TIẾN TRÌNH MASTERY (20 từ / 30 ngày) ===")
    print(f"{'ngày':<12}{'ôn':>5}{'new':>6}{'learn':>7}{'review':>8}{'master':>8}"
          f"{'%':>8}{'ease':>8}{'int(g)':>9}{'due':>6}")
    for idx, row in enumerate(progression):
        s = row["stats"]
        label = f"{row['date'].isoformat()}" + (" (trước)" if idx == 0 else "")
        print(f"{label:<12}{row['reviews']:>5}{s['new']:>6}{s['learning']:>7}"
              f"{s['review']:>8}{s['mastered']:>8}{s['mastery_pct']:>8.1f}"
              f"{s['avg_ease']:>8.2f}{s['avg_interval_days']:>9.2f}{s['due_today']:>6}")


def print_details(states, daily_counts):
    print("\n=== TRẠNG THÁI CUỐI 20 TỪ ===")
    for key in sorted(states):
        st = states[key]
        level = srs.mastery_level(st)
        due_iso = datetime.fromtimestamp(st["due"]).isoformat(timespec="seconds")
        print(f"  {key}  {level:<9} int={st['interval']:>8.2f}d  ease={st['ease']:>4.2f}  "
              f"reps={st['reps']:>2} lapses={st['lapses']:>2}  streak={st['streak']:>2}  due={due_iso}")

    print("\n=== HÀNG ĐỢI ÔN TẬP (10 đầu) ===")
    queue = srs.build_queue(states, limit=10)
    if not queue:
        print("  (rỗng)")
    for i, item in enumerate(queue, 1):
        print(f"  {i:>2}. {item['key']}  state={item['state']:<9} "
              f"quá hạn={item['overdue_days']:>6.2f} ngày  due={datetime.fromtimestamp(item['due']).date()}")

    print("\n=== LỊCH SỬ 10 NGÀY GẦN NHẤT (theo last_review) ===")
    for row in srs.daily_history(states, days=10):
        bar = "█" * min(row["reviews"], 40)
        print(f"  {row['date']}  {row['reviews']:>3} lần ôn  {bar}")

    active_days = [r["date"] for r in srs.daily_history(states, days=SIM_DAYS) if r["reviews"] > 0]
    true_days = sorted(daily_counts.keys())
    print(f"\n  daily_history (last_review): streak={srs.streak_from_days(active_days)} ngày, "
          f"ngày có học={len(active_days)}/{SIM_DAYS}")
    print(f"  thực tế trong sim (mọi lần ôn): streak={srs.streak_from_days(true_days)} ngày, "
          f"ngày có học={len(true_days)}/{SIM_DAYS}, "
          f"tổng lần ôn={sum(daily_counts.values())}")


results = []


def check(name, ok, detail=""):
    """Ghi kết quả 1 phép kiểm tra."""
    results.append((name, bool(ok), detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{(' — ' + detail) if detail else ''}")


def run_checks(states):
    print("\n=== 12 PHÉP KIỂM TRA EDGE-CASE ===")

    # 1. ease luôn nằm trong [1.3, 2.8]
    bad = [k for k, v in states.items() if not (srs.EASE_MIN <= v["ease"] <= srs.EASE_MAX)]
    check("ease luôn trong [1.3, 2.8]", not bad, f"{len(states)} từ")

    # 2. interval không vượt trần 365 ngày
    bad = [k for k, v in states.items() if v["interval"] > srs.MAX_INTERVAL]
    check("interval <= MAX_INTERVAL (365 ngày)", not bad)

    # 3. due == last_review + interval * DAY
    worst = 0.0
    for k, v in states.items():
        if v["last_review"] is None:
            continue
        worst = max(worst, abs(v["due"] - (v["last_review"] + v["interval"] * srs.DAY)))
    check("due == last_review + interval*DAY", worst < 1e-6, f"sai số tối đa {worst:.2e}s")

    # 4. lịch relaxed ngắn hơn đúng hệ số 1.3
    st = srs.new_state(0)
    norm, _ = srs.review(st, "good", now=0)
    lax, _ = srs.review(st, "good", now=0, relaxed=True)
    ratio = lax["interval"] / norm["interval"]
    check("relaxed = chuẩn * 1.3", abs(ratio - srs.RELAXED_MULTIPLIER) < 1e-12,
          f"tỉ lệ {ratio!r}")

    # 5. relaxed cũng bị chặn trần MAX_INTERVAL
    big = dict(srs.new_state(0), interval=300.0, state="review", reps=5)
    _, info = srs.review(big, "easy", now=0, relaxed=True)
    check("relaxed vẫn <= MAX_INTERVAL", info["interval_days"] <= srs.MAX_INTERVAL,
          f"interval={info['interval_days']}")

    # 6. again: reps=0, lapses+1, ease-0.2, về bước học 1 phút
    st0 = srs.new_state(0)
    st1, info1 = srs.review(st0, "again", now=0)
    ok = (st1["reps"] == 0 and st1["lapses"] == 1 and st1["streak"] == 0
          and abs(st1["ease"] - 2.3) < 1e-12
          and abs(st1["interval"] - srs.LEARNING_STEPS[0] / 60.0) < 1e-12
          and st1["state"] == "learning")
    check("again → reps=0, lapses+1, ease-0.2, 1 phút, learning", ok,
          f"ease={st1['ease']}, interval={st1['interval']:.6f}d")

    # 7. ease chạm sàn 1.3 khi quên liên tục
    st = srs.new_state(0)
    for _ in range(20):
        st, _ = srs.review(st, "again", now=0)
    check("ease kẹp sàn EASE_MIN=1.3", abs(st["ease"] - srs.EASE_MIN) < 1e-9, f"ease={st['ease']}")

    # 8. ease chạm trần 2.8 khi toàn easy
    st = srs.new_state(0)
    for _ in range(20):
        st, _ = srs.review(st, "easy", now=0)
    check("ease kẹp trần EASE_MAX=2.8", abs(st["ease"] - srs.EASE_MAX) < 1e-9, f"ease={st['ease']}")

    # 9. mốc interval của "good": 0 → 10 phút → 1 ngày → 3 ngày → nhân ease
    st = srs.new_state(0)
    st, i1 = srs.review(st, "good", now=0); v1 = st["interval"]
    st, i2 = srs.review(st, "good", now=0); v2 = st["interval"]
    st, i3 = srs.review(st, "good", now=0); v3 = st["interval"]
    st, i4 = srs.review(st, "good", now=0); v4 = st["interval"]
    ok = (abs(v1 - 10 / 60) < 1e-12 and abs(v2 - 1) < 1e-12
          and abs(v3 - 3) < 1e-12
          and abs(v4 - 3 * st["ease"]) < 1e-12)
    check("good: 10p → 1d → 3d → ×ease", ok,
          f"{v1:.4f}/{v2:.2f}/{v3:.2f}/{v4:.2f}")

    # 10. easy trên từ mới → GRADUATING (1 ngày), còn lại → EASY_INTERVAL (4 ngày)
    fresh, i_fresh = srs.review(srs.new_state(0), "easy", now=0)
    learned = dict(srs.new_state(0), interval=0.0, state="learning", reps=1, last_review=0.0)
    _l, i_learned = srs.review(learned, "easy", now=0)
    ok = (abs(i_fresh["interval_days"] - srs.GRADUATING_INTERVAL) < 1e-9
          and abs(i_learned["interval_days"] - srs.EASY_INTERVAL) < 1e-9)
    check("easy: mới→1 ngày, đang học→4 ngày", ok,
          f"{i_fresh['interval_days']} / {i_learned['interval_days']}")

    # 11. serialize/deserialize giữ nguyên dữ liệu, JSON-safe
    sample = states[sorted(states)[0]]
    ser = srs.serialize(sample)
    txt = json.dumps(ser, ensure_ascii=False)
    back = srs.deserialize(json.loads(txt))
    same = True
    for k in sample:
        a, b = sample[k], back[k]
        if a is None or b is None:
            same = same and (a is None and b is None)
        elif isinstance(a, (int, float)):
            same = same and abs(float(a) - float(b)) < 1e-3
        else:
            same = same and (a == b)
    check("serialize → JSON → deserialize giữ nguyên", same, txt[:78])

    # 12. queue: quá hạn đứng đầu và sắp theo due tăng dần
    q = srs.build_queue(states, limit=100)
    overdue = [i for i in q if i["overdue_days"] > 0]
    ordered = all(q[i]["due"] <= q[i + 1]["due"] for i in range(len(overdue) - 1))
    first_new = next((i for i, it in enumerate(q) if it["state"] == "new"), len(q))
    groups_ok = all(it["overdue_days"] > 0 for it in q[:len(overdue)])
    check("queue: quá hạn trước, due tăng dần, 'new' cuối",
          ordered and groups_ok and all(it["state"] != "new" for it in q[:first_new]),
          f"{len(q)} mục, {len(overdue)} quá hạn")

    # 13. streak tính đúng (chuỗi hôm nay / hôm qua)
    today = date.today()
    y1, y2, y3 = today - timedelta(days=1), today - timedelta(days=2), today - timedelta(days=3)
    check("streak: 3 ngày liên tiếp = 3",
          srs.streak_from_days([y3.isoformat(), y2.isoformat(), y1.isoformat()]) == 3)
    check("streak: không học 2 ngày = 0",
          srs.streak_from_days([(today - timedelta(days=5)).isoformat()]) == 0)
    check("streak: hôm nay chưa học, hôm qua có = 1",
          srs.streak_from_days([y1.isoformat()]) == 1)


def main():
    print("=" * 92)
    print("DIAG SRS — SM-2 (SuperMemo 2) | seed", SEED)
    print("=" * 92)
    states, progression, daily_counts = run_simulation()
    print_progression(progression)
    print_details(states, daily_counts)
    run_checks(states)

    failed = [r for r in results if not r[1]]
    print(f"\n=== TỔNG KẾT: {len(results) - len(failed)}/{len(results)} phép kiểm tra PASS ===")
    if failed:
        for name, _ok, detail in failed:
            print(f"  FAIL: {name} {detail}")
        sys.exit(1)


if __name__ == "__main__":
    main()
