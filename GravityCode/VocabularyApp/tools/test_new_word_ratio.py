# -*- coding: utf-8 -*-
"""tools/test_new_word_ratio.py — Test Gói 5.1 (chống AI lặp từ).

Bối cảnh (đo thật 2026-11-12): 24-48 % từ giữa các ngày là TRÙNG ⇒
"1.260 ngày" hoá ra chỉ ~630 từ khác nhau ⇒ học 200+ ngày mà không đủ từ mới.

7 case (mock 0 mạng thật):
  1. _known_words gom đúng từ của các ngày TRƯỚC (không lấy ngày sau).
  2. _known_words giới hạn số lượng (limit) + bỏ từ rỗng.
  3. build_content_prompt có khối "TỪ ĐÃ DÙNG" + yêu cầu ≥N từ MỚI.
  4. Không có known_words ⇒ prompt không có khối đó (giữ prompt gọn).
  5. Pipeline đo tỉ lệ từ mới đúng (checkpoint có new_words/new_word_ratio).
  6. Tỉ lệ thấp ⇒ log cảnh báo "stage.low_new_ratio".
  7. Tỉ lệ ≥ ngưỡng ⇒ KHÔNG cảnh báo.

Chạy: python tools/test_new_word_ratio.py
"""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai import course_db                      # noqa: E402
from ai.pipeline_store import (STAGE_CONTENT, STATUS_DONE,  # noqa: E402
                               load_checkpoint)

LANG = "zz_new_ratio_test"
PASS = [0]
FAIL = [0]
LOGS = []


def ck(name, cond, detail=""):
    if cond:
        PASS[0] += 1
        print(f"[OK] {name}")
    else:
        FAIL[0] += 1
        print(f"[FAIL] {name} — {detail!r}")


class _Log:
    def __init__(self):
        self.warns = []

    def warn(self, event, msg="", **kw):
        self.warns.append((event, msg))

    def event(self, *a, **k):
        pass

    def error(self, *a, **k):
        pass

    def info(self, *a, **k):
        pass

    def context(self, *a, **k):
        pass


def main() -> int:
    course_db.delete_course(LANG)
    import ai.pipeline as pl
    from ai.course_generator import build_content_prompt

    # ── 1/2. _known_words ─────────────────────────────────────────────────
    print("\n=== 1-2. _known_words gom từ ngày trước ===")
    course = {"days": [
        {"day": 1, "vocab": [{"word": "猫"}, {"word": "犬"}]},
        {"day": 2, "vocab": [{"word": "車"}, {"word": ""}]},
        {"day": 3, "vocab": [{"word": "水"}]},
    ]}
    kw = pl._known_words(course, 3)
    ck("gom từ ngày 1-2", set(kw) == {"猫", "犬", "車"}, kw)
    ck("KHÔNG lấy từ ngày 3 (>= day_num)", "水" not in kw, kw)
    ck("bỏ từ rỗng", "" not in kw, kw)
    kw2 = pl._known_words(course, 3, limit=2)
    ck("giới hạn limit", len(kw2) == 2, kw2)

    # ── 3/4. prompt ───────────────────────────────────────────────────────
    print("\n=== 3-4. prompt yêu cầu từ mới ===")
    p = build_content_prompt("tiếng Nhật", 5, 1260, [], topic="T", level="L1",
                             phase="Vỡ lòng", known_words=["猫", "犬"],
                             min_new=pl.MIN_NEW_WORDS_PER_DAY)
    ck("có khối 'CÁC TỪ ĐÃ DÙNG'", "CÁC TỪ ĐÃ DÙNG" in p, "")
    ck(f"yêu cầu ≥ {pl.MIN_NEW_WORDS_PER_DAY} từ mới",
       f"ÍT NHẤT {pl.MIN_NEW_WORDS_PER_DAY} từ" in p, "")
    ck("có giới hạn số từ lặp", "TỐI ĐA" in p, "")
    p2 = build_content_prompt("tiếng Nhật", 5, 1260, [], topic="T", level="L1",
                              phase="Vỡ lòng")
    ck("không có khối khi không truyền known_words",
       "CÁC TỪ ĐÃ DÙNG" not in p2, "")

    # ── 5/6/7. đo tỉ lệ từ mới trong pipeline ───────────────────────────
    print("\n=== 5-7. pipeline đo tỉ lệ từ mới ===")
    course2 = {"days": [{"day": 1, "vocab": [{"word": "猫"}, {"word": "犬"}]}],
               "plan": [{"day": 2, "title": "T2", "phase": "P"}]}
    log = _Log()

    class _Coord:
        def __init__(self, words):
            self.words = words

        def request(self, prompt, response_schema=None, **kw):
            # 10 từ: 2 từ cũ + 8 từ mới ⇒ tỉ lệ mới = 80 %
            vs = [{"word": w, "pronunciation": "x", "meaning_vi": "y",
                   "part_of_speech": "n", "ipa": "/x/", "explanation": "e",
                   "example_sentence": "s", "example_meaning_vi": "m"}
                  for w in self.words]
            return {"ok": True, "text": '{"title":"T","vocab":%s,"grammar":[],'
                                     '"sentence_patterns":[],"common_sentences":[]}'
                                     % (vs and str(vs).replace("'", '"').replace("True", "true"))}

    # Dùng JSON thật cho chắc chắn
    import json as _json
    words = ["猫", "犬"] + [f"w{i}" for i in range(8)]

    class _Coord2:
        def request(self, prompt, response_schema=None, **kw):
            payload = {"title": "T2",
                       "vocab": [{"word": w, "pronunciation": "x", "meaning_vi": "y",
                                  "part_of_speech": "n", "ipa": "/x/",
                                  "explanation": "e", "example_sentence": "s",
                                  "example_meaning_vi": "m"} for w in words],
                       "grammar": [], "sentence_patterns": [], "common_sentences": []}
            return {"ok": True, "text": _json.dumps(payload, ensure_ascii=False)}

    pl._run_day(LANG, 2, course2["plan"][0], course2, coord=_Coord2(), log=log,
                budget=pl.PipelineBudget() if hasattr(pl, "PipelineBudget") else None,
                emit=lambda m: None, stages=[STAGE_CONTENT], level="L1",
                allow_degraded=True, max_images=0, max_audio=12, chain=None,
                resume=True, save_each_day=False)
    cp = load_checkpoint(LANG, STAGE_CONTENT, 2) or {}
    d = cp.get("data") or {}
    ck("checkpoint có new_words", "new_words" in d, list(d.keys())[:6])
    ck("new_words = 8 (từ mới)", d.get("new_words") == 8, d.get("new_words"))
    ck("new_word_ratio = 0.8", abs(float(d.get("new_word_ratio") or 0) - 0.8) < 0.01,
       d.get("new_word_ratio"))
    ck("KHÔNG cảnh báo khi tỉ lệ cao",
       not any(e == "stage.low_new_ratio" for e, _m in log.warns), log.warns)

    # Case tỉ lệ thấp: 8 từ cũ + 2 từ mới ⇒ 20 % ⇒ phải cảnh báo
    log2 = _Log()
    words2 = ["猫", "犬", "車", "水", "山", "川", "海", "空"] + ["新1", "新2"]

    class _Coord3:
        def request(self, prompt, response_schema=None, **kw):
            payload = {"title": "T3",
                       "vocab": [{"word": w, "pronunciation": "x", "meaning_vi": "y",
                                  "part_of_speech": "n", "ipa": "/x/",
                                  "explanation": "e", "example_sentence": "s",
                                  "example_meaning_vi": "m"} for w in words2],
                       "grammar": [], "sentence_patterns": [], "common_sentences": []}
            return {"ok": True, "text": _json.dumps(payload, ensure_ascii=False)}

    class _B:
        counters = {}

        def can_call(self, n=1):
            return True

        def consume_call(self):
            pass

        def consume_tts(self):
            pass

    course3 = {"days": [{"day": 1, "vocab": [{"word": w} for w in words2[:8]]}],
               "plan": [{"day": 3, "title": "T3", "phase": "P"}]}
    pl._run_day(LANG, 3, course3["plan"][0], course3, coord=_Coord3(), log=log2,
                budget=_B(), emit=lambda m: None, stages=[STAGE_CONTENT],
                level="L1", allow_degraded=True, max_images=0, max_audio=12,
                chain=None, resume=True, save_each_day=False)
    ck("cảnh báo khi tỉ lệ từ mới thấp",
       any(e == "stage.low_new_ratio" for e, _m in log2.warns), log2.warns)

    course_db.delete_course(LANG)
    print(f"\nKết quả: {PASS[0]} PASS / {FAIL[0]} FAIL (tổng {PASS[0] + FAIL[0]})")
    return 1 if FAIL[0] else 0


if __name__ == "__main__":
    sys.exit(main())
