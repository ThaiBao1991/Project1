# -*- coding: utf-8 -*-
"""tools/test_course_recovery.py — Test Gói 2 (khôi phục & bảo toàn khóa học).

Xem docs/UPGRADE_17.md mục 7.20. 8 case, mock 0 mạng thật:
  1. RESUME: checkpoint quiz "done" nhưng course.json chưa có ⇒ khôi phục quiz.
  2. Content fail ⇒ skeleton ngày rỗng bị XOÁ khỏi course (web không hiện
     ngày trống).
  3. run_pipeline bị DỪNG ⇒ course.json VẪN được flush (không mất ngày đã xong).
  4. canonical_slug: pipeline_dir / audio_dir / reviews_path của ALIAS
     ("ja", "nhật") trùng slug chuẩn ⇒ hết split-brain.
  5. Call hội thoại ĐƯỢC tính vào ngân sách (consume_call +1).
  6. Ảnh: max_images <= 0 ⇒ phủ hết số từ của ngày (không còn 2 từ trống).
  7. verify: giới hạn số lần đánh dấu "sinh bù" ⇒ pass bù hội tụ (không đốt
     quota vô hạn).
  8. course_db.update_day: chỉ sửa 1 ngày, KHÔNG ghi đè phần khác.

Chạy: python tools/test_course_recovery.py
"""
import os
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai import course_db                      # noqa: E402
from ai.pipeline_store import (STAGE_AUDIO, STAGE_CONTENT, STAGE_DIALOGUE,  # noqa: E402
                               STAGE_IMAGES, STAGE_QUIZ_AB, STAGE_QUIZ_CD,
                               STATUS_DONE, STATUS_PENDING, load_checkpoint,
                               save_checkpoint)

LANG = "zz_recovery_test"
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


def _log(m):
    LOGS.append(str(m))


class _Log:
    def warn(self, *a, **k):
        pass

    def event(self, *a, **k):
        pass

    def error(self, *a, **k):
        pass

    def info(self, *a, **k):
        pass

    def context(self, *a, **k):
        pass


class _Budget:
    def __init__(self, can=True):
        self.can = can
        self.calls = 0
        self.tts = 0
        self.counters = {}

    def can_call(self, n=1):
        return self.can

    def consume_call(self):
        self.calls += 1

    def consume_tts(self):
        self.tts += 1


class _CoordOk:
    """Coordinator trả về hội thoại hợp lệ (1 hội thoại, 2 lượt)."""

    def __init__(self):
        self.calls = 0

    def request(self, prompt, response_schema=None, **kw):
        self.calls += 1
        # Schema thật: key "dialogue" (KHÔNG phải "dialogues"), ≥2 lượt.
        return {"ok": True, "text": '{"dialogue":[{"title":"T","situation":"S",'
                                  '"level_tag":"A1",'
                                  '"turns":[{"speaker":"A","line_target":"猫"},'
                                  '{"speaker":"B","line_target":"犬"}]}]}'}


def main() -> int:
    course_db.delete_course(LANG)
    import ai.pipeline as pl
    import ai.pipeline_media as pm
    try:
        # ══ 1. RESUME: khôi phục quiz từ checkpoint ═══════════════════════
        print("\n=== 1. RESUME khôi phục quiz từ checkpoint ===")
        course = {"days": [{"day": 1, "title": "T1", "phase": "P", "level": "L",
                            "topic": "T", "words": [],
                            "vocab": [{"word": "猫", "meaning_vi": "mèo"}],
                            "quiz": {"vocab": [], "pattern": [], "common": [],
                                     "grammar": [], "mixed": []}}],
                  "plan": [{"day": 1, "title": "T1", "phase": "P"}]}
        save_checkpoint(LANG, STAGE_CONTENT,
                        {"title": "T1", "vocab": [{"word": "猫", "meaning_vi": "mèo"}]},
                        day=1, status=STATUS_DONE)
        save_checkpoint(LANG, STAGE_QUIZ_AB,
                        {"vocab_quiz": [{"question": "q", "options": ["a", "b"],
                                          "answer_index": 0, "explanation": "e"}],
                         "pattern_quiz": []},
                        day=1, status=STATUS_DONE)
        save_checkpoint(LANG, STAGE_QUIZ_CD,
                        {"common_quiz": [{"question": "q2", "options": ["c", "d"],
                                          "answer_index": 1, "explanation": "e2"}],
                         "grammar_quiz": []},
                        day=1, status=STATUS_DONE)
        lesson = pl._run_day(LANG, 1, course["plan"][0], course, coord=None,
                             log=_Log(), budget=_Budget(), emit=_log,
                             stages=[STAGE_QUIZ_AB, STAGE_QUIZ_CD], level="L1",
                             allow_degraded=True, max_images=0, max_audio=12,
                             chain=None, resume=True, save_each_day=False)
        ck("quiz vocab khôi phục từ checkpoint",
           len((lesson or {}).get("quiz", {}).get("vocab") or []) == 1,
           (lesson or {}).get("quiz"))
        ck("quiz common khôi phục từ checkpoint",
           len((lesson or {}).get("quiz", {}).get("common") or []) == 1,
           (lesson or {}).get("quiz"))

        # ══ 2. Content fail ⇒ xoá skeleton ngày rỗng ══════════════════════
        print("\n=== 2. Content fail ⇒ xoá skeleton rỗng ===")
        course2 = {"days": [], "plan": [{"day": 2, "title": "T2", "phase": "P"}]}

        class _CoordFail:
            def request(self, *a, **k):
                return {"ok": False, "error": {"kind": "invalid", "message": "x"}}

        out = pl._run_day(LANG, 2, course2["plan"][0], course2, coord=_CoordFail(),
                           log=_Log(), budget=_Budget(), emit=_log,
                           stages=[STAGE_CONTENT], level="L1", allow_degraded=True,
                           max_images=0, max_audio=12, chain=None, resume=True,
                           save_each_day=False)
        ck("content fail ⇒ trả None", out is None, out)
        ck("skeleton rỗng ĐÃ bị xoá khỏi days", not course2.get("days"),
           course2.get("days"))

        # ══ 3. run_pipeline bị DỪNG ⇒ course.json vẫn flush ════════════════
        print("\n=== 3. Dừng ⇒ course.json vẫn được flush ===")
        course3 = {"days": [{"day": 1, "title": "T1", "phase": "P", "level": "L",
                             "topic": "T", "words": [],
                             "vocab": [{"word": "猫"}], "quiz": {}}],
                   "plan": [{"day": 1, "title": "T1", "phase": "P"}]}
        course_db.save_course(LANG, course3)
        res3 = pl.run_pipeline(LANG, stages=[STAGE_AUDIO], chain=None,
                               budget=_Budget(), workers=1, level="L",
                               mode="full", stop_check=lambda: True)
        saved = course_db.get_course(LANG, persist=False) or {}
        ck("run dừng ⇒ status paused/ok", res3.get("status") in ("paused", "done"),
           res3.get("status"))
        ck("course.json VẪN tồn tại sau khi dừng", bool(saved.get("days")),
           list((saved or {}).keys()))

        # ══ 4. canonical_slug thống nhất ═══════════════════════════════════
        print("\n=== 4. canonical_slug: alias → cùng đường dẫn chuẩn ===")
        from ai.paths import canonical_slug
        import ai.pipeline_store as pst
        import ai.tts_generator as tts
        from database import review_store as rs
        ck("pipeline_dir('ja') == pipeline_dir('tiếng_nhật')",
           pst.pipeline_dir("ja") == pst.pipeline_dir("tiếng_nhật"),
           pst.pipeline_dir("ja"))
        ck("pipeline_dir('nhật') == pipeline_dir('tiếng_nhật')",
           pst.pipeline_dir("nhật") == pst.pipeline_dir("tiếng_nhật"),
           pst.pipeline_dir("nhật"))
        ck("audio_dir('ja') == audio_dir('tiếng_nhật')",
           tts.audio_dir("ja") == tts.audio_dir("tiếng_nhật"), tts.audio_dir("ja"))
        ck("reviews_path('nhật') == reviews_path('tiếng_nhật')",
           rs.reviews_path("nhật") == rs.reviews_path("tiếng_nhật"),
           rs.reviews_path("nhật"))
        ck("course_path('nhật') == course_path('tiếng_nhật')",
           course_db.course_path("nhật") == course_db.course_path("tiếng_nhật"),
           course_db.course_path("nhật"))

        # ══ 5. Call hội thoại tính vào ngân sách ═══════════════════════════
        print("\n=== 5. Call hội thoại ĐƯỢC tính quota ===")
        import ai.tts_generator as tts_mod
        lesson5 = {"day": 9, "phase": "P", "title": "T9",
                   "vocab": [{"word": "猫", "meaning_vi": "mèo"}],
                   "dialogue": [{"title": "T9",
                                 "turns": [{"speaker": "A", "line_target": "猫"}]}]}
        budget5 = _Budget()
        pm.run_dialogue_stage(LANG, 9, lesson5, coord=_CoordOk(), log_fn=_log,
                              level="L1", budget=budget5)
        ck("call hội thoại đã consume_call (+1)", budget5.calls >= 1, budget5.calls)
        cp5 = load_checkpoint(LANG, STAGE_DIALOGUE, 9) or {}
        ck("checkpoint dialogue done + có hội thoại",
           cp5.get("status") == STATUS_DONE and
           len((cp5.get("data") or {}).get("dialogues") or []) == 1,
           cp5.get("status"))

        # ══ 6. Ảnh: max_images <= 0 ⇒ phủ hết số từ ═══════════════════════
        print("\n=== 6. max_images<=0 ⇒ phủ hết số từ ===")
        import ai.image_pipeline as ip
        calls = {"n": 0}
        orig_gen = ip.generate_images_for_day

        def _fake_gen(language, day, lesson, **kw):
            calls["n"] = kw.get("max_images")
            for v in (lesson.get("vocab") or []):
                v["image_ref"] = "m_img"
            return [{"id": "m_img"}] * len(lesson.get("vocab") or [])

        ip.generate_images_for_day = _fake_gen
        try:
            lesson6 = {"day": 10, "vocab": [{"word": f"w{i}"} for i in range(12)]}
            pm.run_images_stage(LANG, 10, lesson6, chain=None, log_fn=_log,
                                max_images=0, allow_degraded=True)
        finally:
            ip.generate_images_for_day = orig_gen
        ck("max_images=0 ⇒ cap = số từ (12)", calls.get("n") == 12, calls)

        # ══ 7. verify: giới hạn số lần đánh dấu bù ════════════════════════
        print("\n=== 7. verify: pass bù hội tụ (giới hạn số lần) ===")
        save_checkpoint(LANG, STAGE_DIALOGUE, {"dialogues": []}, day=11,
                        status=STATUS_DONE)
        lesson7 = {"day": 11, "vocab": [], "dialogue": []}
        for i in range(pm.MAX_PENDING_MAKES + 2):
            pm.run_media_verify_stage(LANG, 11, lesson7, log_fn=_log)
        cp7 = load_checkpoint(LANG, STAGE_DIALOGUE, 11) or {}
        cnt = int((cp7.get("data") or {}).get("pending_count") or 0)
        ck(f"số lần đánh dấu bù ≤ {pm.MAX_PENDING_MAKES}",
           cnt <= pm.MAX_PENDING_MAKES, cnt)
        ck("checkpoint KHÔNG còn PENDING (đã dừng đốt quota)",
           cp7.get("status") != STATUS_PENDING, cp7.get("status"))

        # ══ 8. update_day: chỉ sửa 1 ngày, không ghi đè phần khác ═════════
        print("\n=== 8. update_day chỉ sửa 1 ngày ===")
        course8 = {"days": [{"day": 1, "vocab": [{"word": "a"}]},
                            {"day": 2, "vocab": [{"word": "b"}]}]}
        course_db.save_course(LANG, course8)
        course_db.update_day(LANG, 2, {"day": 2, "vocab": [{"word": "b2"}]})
        after8 = course_db.get_course(LANG, persist=False) or {}
        d1 = (after8.get("days") or [{}])[0]
        d2 = (after8.get("days") or [{}, {}])[1]
        ck("ngày 1 giữ nguyên", (d1.get("vocab") or [{}])[0].get("word") == "a",
           d1.get("vocab"))
        ck("ngày 2 đã cập nhật",
           (d2.get("vocab") or [{}])[0].get("word") == "b2", d2.get("vocab"))
    finally:
        course_db.delete_course(LANG)

    print(f"\nKết quả: {PASS[0]} PASS / {FAIL[0]} FAIL (tổng {PASS[0] + FAIL[0]})")
    return 1 if FAIL[0] else 0


if __name__ == "__main__":
    sys.exit(main())
