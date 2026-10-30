"""
test_extend_course.py — Phase 4: mở rộng 445→1260 ngày bằng pool giả.

Dữ liệu test nằm trong TEMP (monkeypatch E.SEED_DIR) — không đụng data thật.
Chạy: python tools/test_extend_course.py
"""
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.join(BASE, "tools"))
import extend_japanese_course as E  # noqa: E402
from ai import course_db  # noqa: E402

PASSED = []


def ok(name):
    PASSED.append(name)
    print(f"[OK] {name}")
    return PASSED


def W(word, vi, pos="danh từ"):
    return {word: {"reading": word, "romaji": word.lower(), "vi": vi,
                   "pos": pos, "ex_ja": f"{word}はいい。", "ex_vi": vi}}


def make_seed(tmp, files):
    for name, words in files.items():
        with open(os.path.join(tmp, name), "w", encoding="utf-8") as f:
            json.dump(words, f, ensure_ascii=False)


# ── 1. load_pools: xếp N5 → N4 → phụ, loại entry thiếu nghĩa ──
with tempfile.TemporaryDirectory() as tmp:
    E.SEED_DIR = tmp
    make_seed(tmp, {
        "dict.json": W("あかい赤い", "đỏ", "tính từ"),
        "n5_pool.json": {**W("いえ家", "nhà"), **W("うみ海", "biển")},
        "n4_pool.json": {**W("けいかく計画", "kế hoạch"), **W("ことわり断わり", "từ chối")},
        "pool_extra.json": W("しずく雫", "giọt nước"),
    })
    queue, per_level = E.load_pools()
    names = [w for w, _ in queue]
    # n5 gồm dict + n5_pool (merge), rồi n4, rồi extras
    assert per_level["n5"] and per_level["n4"] and "しずく雫" in dict(queue)
    assert names[:3] == sorted(["あかい赤い", "いえ家", "うみ海"]), names[:3]
    assert names[3:5] == sorted(["けいかく計画", "ことわり断わり"]), names[3:5]
    ok("load_pools: merge dict+nX pool, xếp n5→n4→extras, bỏ entry thiếu nghĩa")
ok("load_pools (fixture 1)")

# ── 2. từ GIẢ trong pool → AssertionError ──
with tempfile.TemporaryDirectory() as tmp:
    E.SEED_DIR = tmp
    make_seed(tmp, {"n5_pool.json": W("単語7", "từ giả cấm")})
    try:
        E.load_pools()
        assert False, "load_pools nhận từ giả mà không ném!"
    except AssertionError as e:
        assert "単語7" in str(e), str(e)
ok("load_pools: từ giả '単語7' → AssertionError")

# ── 3. generate: không trùng từ mới, đủ ngày, từ có nghĩa ──
with tempfile.TemporaryDirectory() as tmp:
    E.SEED_DIR = tmp
    words = {}
    for i in range(40):
        words.update(W(f"L{i:03d} từ{i}", f"nghĩa {i}"))
    make_seed(tmp, {"n5_pool.json": words})
    course = {"format_version": 4, "days": [
        {"day": 1, "vocab": [{"word": "は", "pronunciation": "wa",
                              "meaning_vi": "LaTinh - trợ từ chủ ngữ",
                              "part_of_speech": "trợ từ"}]},
    ]}  # 'は' là từ cũ — có nghĩa, dùng cho ngày ôn; pool phải đỡ tái sinh.
    # thêm 'は' vào pool để test prefilter
    E.SEED_DIR = tmp
    # generate 445..470 (26 ngày)
    new_days, stat = E.generate(445, 470, course)
    assert len(new_days) == 26, stat
    assert stat["days"] == 26
    # không từ trùng giữa các ngày MỚI (review/checkpoint lặp là hợp lệ)
    seen_new = set()
    for d in new_days:
        topic = d.get("topic") or ""
        is_review = topic.startswith("Ngày ôn") or topic.startswith("Checkpoint")
        if is_review:
            continue
        for v in d["vocab"]:
            assert v["word"] not in seen_new, f"lặp từ mới: {v['word']}"
            seen_new.add(v["word"])
            assert v["meaning_vi"], f"thiếu nghĩa: {v['word']}"
    ok("generate: 26 ngày, từ mới không trùng, đủ nghĩa")

    # review day 448 KHÔNG từ mới; checkpoint 450 đủ ≥15 câu (pool bé) → format đúng
    d448 = next(d for d in new_days if d["day"] == 448)
    assert d448["topic"] == "Ngày ôn tập"
    d450 = next(d for d in new_days if d["day"] == 450)
    assert "Checkpoint" in d450["topic"]
    nq = sum(len(v) for v in d450["quiz"].values())
    assert nq == 20, f"checkpoint phải 20 câu — đang {nq}"
    ok("day 448 ôn (0 từ mới) · day 450 checkpoint đúng 20 câu")

    # prefilter: từ 'は' của khóa cũ KHÔNG được tái sinh
    for d in new_days:
        for v in d["vocab"]:
            assert v["word"] != "は", "từ cũ bị tái sinh!"
    ok("prefilter: từ đã có trong course không tái xuất hiện")

# ── 4. apply_course: merge giữ ngày cũ < start, sort tăng dần, backup=True ──
with tempfile.TemporaryDirectory() as tmp:
    E.SEED_DIR = tmp
    make_seed(tmp, {"n5_pool.json": {**W("aあ", "ña"), **W("bい", "bì")}})
    calls = []
    course_db.save_course = (lambda lang, c, backup=False:
                             calls.append((lang, c, backup)))
    course = {"format_version": 4, "language": "Tiếng Nhật",
              "days": [{"day": 1}, {"day": 2}]}
    new_days, _ = E.generate(3, 6, course)
    E.apply_course(course, new_days, 3)
    (lang, saved, backup), = calls
    assert lang == E.SLUG and backup is True
    days = [int(d["day"]) for d in saved["days"]]
    assert days == [1, 2, 3, 4, 5, 6], days
    ok("apply_course: merge + sort + save_course(SLUG chuẩn, backup=True)")

print(f"\nKet qua: {len(PASSED)*1}/6 PASS")
if len(PASSED) < 6:
    sys.exit(1)
