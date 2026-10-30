"""
tools/extend_japanese_course.py — MỞ RỘNG KHÓA NHẬT 445 → 1.260 NGÀY (0 API).

Cùng canonical slug với recovery: SLUG = canonical_slug('nhật'). Sau khi
tools/recover_japanese_course.py đã ghi 444 ngày thật (từ manifest), tool này
sinh tiếp phần còn lại THUẦN CPU (< 60s) từ pool từ vựng JLPT.

Nguồn pool: mọi file JSON trong data/seed/ja/:
    • dict.json              → seed mặc định (ch/shared recovery + pool N5)
    • n5_pool.json … n1_pool.json → pool theo level, vào đúng chặng
    • pool_<tên>.json khác   → nối vào cuối hàng chờ
Định dạng entry (giống seed recovery):
    {"giải pháp": {"reading": "かいほう", "romaji": "kaihō", "vi": "giải pháp",
                   "pos": "danh từ", "ex_ja": "…", "ex_vi": "…"}}

Quy tắc (theo plan Phase 4):
  • KHÔNG lặp từ trong phần mở rộng: từ đã có trong khóa học bị loại khỏi
    hàng chờ; mỗi từ mới chạm đúng 1 lần.
  • Ngày %7==0  → NGÀY ÔN: 10 từ lặp (lấy từ ~6 ngày trước), KHÔNG từ mới.
  • Ngày %30==0 → CHECKPOINT: 20 câu trắc nghiệm (10 vocab + 10 cách dùng).
  • 6 chặng theo (day-1)//210 → N5 / N5+ / N4 / N3 / N2 / N1.
  • assertion chặn từ giả (単語N / tangoN / "Nghĩa từ vựng số") TRƯỚC KHI GHI.
  • Hết hàng chờ → các ngày còn lại thành ngày ôn (không bịa từ).

Cú pháp:
  python tools/extend_japanese_course.py --status      # báo pool/thiếu
  python tools/extend_japanese_course.py --dry-run     # in 3 ngày mẫu, 0 ghi
  python tools/extend_japanese_course.py --apply       # GHI course (backup)
  percent chạy --to-day 500                            # dừng sớm để test
"""
import argparse
import json
import os
import random
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(BASE, "tools"))
from recover_japanese_course import build_quiz_offline, is_fake_word  # noqa: E402

from ai import course_db  # noqa: E402
from ai.paths import canonical_slug  # noqa: E402

SLUG = canonical_slug("nhật")           # 'tiếng_nhật' — 1 nhà với recovery
SEED_DIR = os.path.join(BASE, "data", "seed", "ja")
TARGET_DAYS = 1260
START_DAY_DEFAULT = 445                 # sau 444 ngày recovery
RNG_SEED = 20261027                     # cố định — chạy lại cho ra đúng y

# Index chặng = (day-1)//210
PHASES = (
    ("Mở lòng — kana & N5", "JLPT N5"),
    ("N5 trôi chảy", "JLPT N5"),
    ("N4 — đời thường", "JLPT N4"),
    ("N3 — báo chí & công sở", "JLPT N3"),
    ("N2 — chuyên sâu", "JLPT N2"),
    ("N1 — cao thượng & kính ngữ", "JLPT N1"),
)
LEVEL_FILES = ("n1_pool.json", "n2_pool.json", "n3_pool.json",
               "n4_pool.json", "n5_pool.json")


def load_pools() -> tuple:
    """Hàng chờ từ vựng ĐÃ XẾP theo chặng: N5 → N4 → N3 → N2 → N1 → phụ.

    Trả (queue, per_level) — queue là list (word, info); per_level để --status.
    """
    per_level = {}
    queue = []

    def _read(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"⚠ Bỏ qua file seed lỗi {os.path.basename(path)}: {e}")
            return {}
        if isinstance(data, dict) and "vocabularies" in data:
            return {v.get("word"): {k: vv for k, vv in v.items() if k != "word"}
                    for v in data.get("vocabularies") or []
                    if isinstance(v, dict) and v.get("word")}
        return data if isinstance(data, dict) else {}

    def _clean(words, source):
        out = {}
        for w, info in words.items():
            if not w or not isinstance(info, dict) or not (info.get("vi") or "").strip():
                continue
            if is_fake_word(str(w)):
                raise AssertionError(f"Pool chứa từ GIẢ: {w!r} ({source})")
            out[w] = info
        return out

    # 1) dict.json → mặc định (N5/N4 đầu)
    dpath = os.path.join(SEED_DIR, "dict.json")
    if os.path.isfile(dpath):
        per_level["n5"] = _clean(_read(dpath), "dict.json")

    # 2) pool theo level (n5 → n1)
    for lvl in ("n5", "n4", "n3", "n2", "n1"):
        p = os.path.join(SEED_DIR, f"{lvl}_pool.json")
        if os.path.isfile(p):
            got = _clean(_read(p), f"{lvl}_pool.json")
            per_level[lvl] = dict(per_level.get(lvl) or {}, **got)

    # 3) pool khác (pool_<tên>.json — không phải nX_pool.json) → phần phụ cuối
    extras = {}
    try:
        dir_files = os.listdir(SEED_DIR)
    except OSError:
        dir_files = []
    for name in sorted(dir_files):
        if not name.lower().startswith("pool_"):
            continue
        p = os.path.join(SEED_DIR, name)
        if os.path.isfile(p):
            extras.update(_clean(_read(p), name))

    for lvl in ("n5", "n4", "n3", "n2", "n1"):
        for w in sorted(per_level.get(lvl, {})):
            queue.append((w, per_level[lvl][w]))
    for w in sorted(extras):
        if all(w not in per_level.get(l, {}) for l in ("n5", "n4", "n3", "n2", "n1")):
            queue.append((w, extras[w]))
    return queue, per_level


def _distractors(word, info, pool) -> list:
    """Nghĩa của từ CÙNG pos — tối đa 3, đủ làm options sai."""
    post = str(info.get("pos") or "")
    out = []
    for w2, inf2 in pool.items():
        if w2 == word:
            continue
        vi2 = (inf2.get("vi") or "").strip()
        if vi2 and vi2 != info.get("vi") and str(inf2.get("pos") or "") == post:
            out.append(vi2)
    return out


def quiz_20(prev_words, pool) -> dict:
    """20 câu checkpoint: 10 vocab + 10 pattern/common từ ~15 từ gần nhất."""
    ws = [w for w in prev_words[-15:] if (pool.get(w) or {}).get("vi")]
    vq, pq, cq = [], [], []
    for i, w in enumerate(ws):
        info = pool[w]
        dist = _distractors(w, info, pool)
        if len(dist) < 3:
            continue
        opts = dist[:3] + [info["vi"]]
        random.Random(f"{RNG_SEED}|chk20|{w}|{i}").shuffle(opts)
        item = {"question": f"Từ '{w}' ({info.get('reading') or '?'}) "
                            f"nghĩa là gì?",
                "options": opts,
                "answer_index": opts.index(info["vi"]),
                "explanation": f"{w} = {info['vi']}"}
        if len(vq) < 10:
            vq.append(item)
        elif len(cq) + len(vq) + len(pq) < 20:
            cq.append(item)
        ex = info.get("ex_ja") or ""
        if ex and len(pq) < 10:
            blanked = ex.replace(w, "____") if w in ex else ex
            pq.append({"question": f"「{blanked}」 — đúng nhất là câu nào?",
                       "options": opts,
                       "answer_index": opts.index(info["vi"]),
                       "explanation": f"{w} = {info['vi']}."})
    return {"vocab": vq, "pattern": pq, "common": cq,
            "grammar": []} if len(vq) + len(pq) + len(cq) >= 15 else \
           {"vocab": vq + cq, "pattern": pq, "common": [], "grammar": []}


def build_lesson(day: int, take_next, pool_lookup, recent, review_only=False):
    """Sinh 1 lesson cho `day`.

    take_next(n)  → list (word, info) từ hàng chờ (sẽ tự skip trùng)
    pool_lookup   → {word: info} toàn bộ pool (tra đủ nghĩa cho từ lặp lại)
    recent        → list từ mới đã dùng gần nhất (mới nhất sau)
    review_only   → ép ngày ôn (hết pool)
    """
    pi = min(5, max(0, (day - 1) // 210))
    phase_name, level = PHASES[pi]
    is_checkpoint = (day % 30 == 0)
    # %30 đè lên %7: checkpoint nuốt cả ngày ôn (không từ mới)
    is_review = review_only or (day % 7 == 0) or is_checkpoint
    rng = random.Random(f"{RNG_SEED}|day{day}")

    lesson = {"day": day, "title": "", "phase": phase_name, "level": level,
              "topic": "", "format_version": 4,
              "vocab": [],
              "quiz": {"vocab": [], "pattern": [], "common": [], "grammar": []}}

    # ── Vocab ──
    if is_review:
        ws = list(dict.fromkeys(recent))[:10]      # lặp từ gần nhất, KHÔNG mới
        lesson["topic"] = "Ngày ôn tập"
        if is_checkpoint:
            lesson["topic"] = "Checkpoint tổng ôn"
        rng = random.Random(f"{RNG_SEED}|review|{day}")
        if len(ws) > 10:
            ws = rng.sample(ws, 10)
    else:
        got = take_next(10)
        ws = [w for w, _ in got]
        lesson["topic"] = f"10 từ mới — {phase_name}"

    for w in ws:
        info = pool_lookup.get(w) or {}
        lesson["vocab"].append({
            "word": w,
            "pronunciation": info.get("reading") or "",
            "ipa": info.get("romaji") or "",
            "part_of_speech": info.get("pos") or "",
            "meaning_vi": info.get("vi") or "",
            "explanation": "",
            "example_sentence": info.get("ex_ja") or "",
            "example_meaning_vi": info.get("ex_vi") or "",
            "image_ref": "",
            "audio_ref": "",
        })

    # ── Quiz ──
    if is_checkpoint:
        lesson["quiz"] = quiz_20(list(recent) or ws, pool_lookup)
        total = sum(len(v) for v in lesson["quiz"].values())
        if total < 20:
            lesson["topic"] += f" (câu hỏi: {total})"
    else:
        lesson["quiz"] = build_quiz_offline(ws, pool_lookup)

    lesson["title"] = (f"Ngày {day} — {lesson['topic'] or phase_name}")
    return lesson


def generate(start_day: int, to_day: int, course: dict) -> tuple:
    """Loop ngày start→to_day. Trả (new_days, stat)."""
    queue, _ = load_pools()
    pool_lookup = {w: info for w, info in queue}

    existing, existing_info = [], {}
    for d in (course.get("days") or []):
        for v in d.get("vocab") or []:
            w = str(v.get("word") or "").strip()
            if w:
                existing.append(w)
                if isinstance(v, dict) and v.get("meaning_vi"):
                    # chuẩn hoá shape course → seed để tra chung với pool
                    existing_info[w] = {
                        "reading": v.get("pronunciation") or "",
                        "romaji": v.get("ipa") or "",
                        "vi": v.get("meaning_vi") or "",
                        "pos": v.get("part_of_speech") or v.get("pos") or "",
                        "ex_ja": v.get("example_sentence") or "",
                        "ex_vi": v.get("example_meaning_vi") or "",
                    }
    # tra nghĩa: pool (mở rộng) + từ có sẵn của khóa (review)
    info_lookup = dict(existing_info)
    info_lookup.update(pool_lookup)

    # loại từ đã có khỏi hàng chờ — mỗi từ mới chạm đúng 1 lần
    queue = [(w, i) for w, i in queue if w not in existing]

    seen_words = set(existing)
    ptr = [0]  # chỉ số hàng chờ

    def take_next(n):
        got = []
        while ptr[0] < len(queue) and len(got) < n:
            w, info = queue[ptr[0]]
            ptr[0] += 1
            if w in seen_words:         # trùng với 444 ngày thật → bỏ luôn
                continue
            got.append((w, info))
            seen_words.add(w)           # trùng NGÀY khác cũng bị chặn
        return got

    # nền ôn xa trước khi mở rộng — chỉ từ CÓ nghĩa (tránh vocab rỗng ngày ôn)
    recent = [w for w in existing[-24:]
              if (existing_info.get(w) or {}).get("meaning_vi")]
    new_days, stat = [], {"days": 0, "vocab": 0, "quiz": 0, "review": 0,
                          "checkpoint": 0, "pool_left": 0}

    for day in range(max(1, start_day), to_day + 1):
        if day > TARGET_DAYS:
            break
        lesson = build_lesson(day, take_next, info_lookup, recent,
                              review_only=(ptr[0] >= len(queue)))
        if lesson["topic"].startswith("Ngày ôn"):
            stat["review"] += 1
        elif "Checkpoint" in (lesson["topic"] or ""):
            stat["checkpoint"] += 1
        stat["days"] += 1
        stat["vocab"] += len(lesson["vocab"])
        stat["quiz"] += sum(len(v) for v in lesson["quiz"].values())
        for v in lesson["vocab"]:
            assert not is_fake_word(v["word"]), \
                f"Từ GIẢ lọt vào d{day:04d}: {v['word']!r}"
            if v["meaning_vi"]:
                recent.append(v["word"])
        new_days.append(lesson)

    stat["pool_left"] = max(0, len(queue) - ptr[0])
    return new_days, stat


def apply_course(course: dict, new_days: list, start_day: int) -> str:
    """Ghép ngày mới vào course (thay ngày ≥ start_day) + ghi backup."""
    old_days = [d for d in course.get("days") or []
                if int(d.get("day") or 0) < start_day]
    merged = old_days + new_days
    merged.sort(key=lambda d: int(d.get("day") or 0))
    course["days"] = merged
    course.setdefault("format_version", 5)
    course_db.save_course(SLUG, course, backup=True)
    return (f"💾 Đã ghi khóa học: {len(old_days)} ngày cũ + "
            f"{len(new_days)} ngày mới = {len(merged)} ngày "
            f"(SLUG='{SLUG}', có backup).")


def cmd_status(course):
    queue, per_level = load_pools()
    existing_words = []
    seen = set()
    for d in course.get("days") or []:
        for v in d.get("vocab") or []:
            w = str(v.get("word") or "").strip()
            if w and w not in seen:
                seen.add(w)
                existing_words.append(w)
    max_day = max((int(d.get("day") or 0) for d in course.get("days") or []),
                  default=0)
    need = max(0, TARGET_DAYS - max_day) * 10
    print(f"🗓 Khóa học hiện tại  : max_day={max_day} (thiếu "
          f"{TARGET_DAYS - max_day} ngày = {need} slot)")
    print(f"🔤 Từ đã có          : {len(existing_words)}")
    print(f"📚 Pool (đã xếp chặng): {len(queue)} = " +
          " ".join(f"{l}:{len(v)}" for l, v in per_level.items() if v))
    trùng = sum(1 for w, _ in queue if w in seen)
    print(f"♻️  Trùng đã có       : {trùng} (tự lọc khi sinh)")
    missing = max(0, need - (len(queue) - trùng))
    print(f"❓ Thiếu pool         : {missing}" +
          (" → soạn thêm nX_pool.json" if missing > 0 else ""))


def main():
    ap = argparse.ArgumentParser(prog="extend_japanese_course")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--start-day", type=int, default=START_DAY_DEFAULT)
    ap.add_argument("--to-day", type=int, default=TARGET_DAYS)
    args = ap.parse_args()

    course = course_db.get_course(SLUG, apply_v4=False, persist=False) or {}
    max_day = max((int(d.get("day") or 0) for d in course.get("days") or []),
                  default=0)

    if args.status:
        cmd_status(course)
        return 0

    if max_day >= TARGET_DAYS and not args.dry_run:
        print(f"⚠ Khóa học đã có {max_day} ngày ≥ [{TARGET_DAYS}]. "
              f"Chạy recovery trước (tools/recover_japanese_course.py) "
              f"hoặc dùng --start-day lớn hơn.")
        return 1

    new_days, stat = generate(args.start_day, args.to_day, course)

    if args.dry_run:
        for ld in (args.to_day,) if False else (445, 448, 450):
            if ld < args.start_day or ld > args.to_day:
                continue
            lesson = next((d for d in new_days if d["day"] == ld), None)
            if not lesson:
                continue
            print(f"\n=== NGÀY {lesson['day']} — {lesson['title']} ===")
            for v in lesson["vocab"][:4]:
                print(f"  {v['word']:12} [{v['pronunciation'] or '—'}] "
                      f"{v['meaning_vi'] or '—'}")
            nq = sum(len(v) for v in lesson["quiz"].values())
            print(f"  … {len(lesson['vocab'])} vocab · {nq}-câu quiz")
        return 0

    msg = apply_course(course, new_days, args.start_day)
    print("\n📊 Thống kê mở rộng:")
    print(f"   · ngày mới    : {stat['days']} (tới {args.to_day})")
    print(f"   · slot vocab   : {stat['vocab']}")
    print(f"   · câu quiz      : {stat['quiz']}")
    print(f"   · ngày ôn       : {stat['review']} · checkpoint: {stat['checkpoint']}")
    print(f"   · pool còn dư   : {stat['pool_left']} từ")
    print("   " + msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
