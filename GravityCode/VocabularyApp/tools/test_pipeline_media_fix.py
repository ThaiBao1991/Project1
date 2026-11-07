"""tools/test_pipeline_media_fix.py — Test fix pipeline media (2026-11-07).

Bug đã sửa (xem docs/UPGRADE_17.md mục 7.14):
  1. Skip "đã có — bỏ qua" KHÔNG re-attach ref vào lesson ⇒ verify báo
     "thiếu 12 audio" trong CÙNG run với log "bỏ qua" (mâu thuẫn).
  2. Verify mark pending GHI ĐÈ data checkpoint bằng {"pending_reason"}
     ⇒ mất list tracks/images/dialogues đã sinh.
  3. Verify KHÔNG đếm dialogue ⇒ lesson.dialogue=0 bị flush vào course.json,
     checkpoint dialogue vẫn done → skip mãi → hội thoại MẤT vĩnh viễn
     mà DoD vẫn báo all_days_dialogue=true (lừa).
  4. Content sinh lại ĐỔI danh sách từ ⇒ checkpoint media/dialogue stale
     "done" → skip → ref trỏ sai/đứt.

7 case, mock 0 mạng thật:
  1. audio skip re-attach: text khớp từ → audio_ref + vocab_audio gắn lại.
  2. audio skip re-attach: text KHÁC (từ đã đổi) → KHÔNG gắn ref sai.
  3. audio skip re-attach: variant "vi" → meaning_audio_ref.
  4. dialogue skip re-attach: lesson rỗng → ghi lại; đã có → giữ nguyên.
  5. verify: thiếu ref → pending NHƯNG GIỮ data cũ (tracks/images còn).
  6. verify: lesson.dialogue rỗng → mark dialogue pending + log; có → không đụng.
  7. content regen đổi từ → invalidate images/audio/dialogue (pending);
     content GIỐNG từ → giữ done.

Chạy: python tools/test_pipeline_media_fix.py
"""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai import course_db                      # noqa: E402
from ai.pipeline_store import (STAGE_AUDIO, STAGE_CONTENT, STAGE_DIALOGUE,   # noqa: E402
                               STAGE_IMAGES, STATUS_DONE, STATUS_PENDING,
                               load_checkpoint, save_checkpoint)
from ai.pipeline_media import (run_audio_stage, run_dialogue_stage,          # noqa: E402
                               run_media_verify_stage)

LANG = "zz_media_fix_test"
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


def _tracks():
    return [
        {"kind": "vocab", "index": 0, "text": "猫", "ref": "m_a1",
         "variant": "target", "engine": "edge-tts", "file": "x.mp3"},
        {"kind": "vocab", "index": 1, "text": "犬", "ref": "m_a2",
         "variant": "target", "engine": "edge-tts", "file": "y.mp3"},
        {"kind": "vocab", "index": 0, "text": "猫", "ref": "m_vi1",
         "variant": "vi", "engine": "edge-tts", "file": "z.mp3"},
    ]


class _Budget:
    def can_call(self, n=1):
        return True

    def consume_call(self):
        pass

    def consume_tts(self):
        pass


class _Log:
    def warn(self, *a, **k):
        pass

    def event(self, *a, **k):
        pass

    def error(self, *a, **k):
        pass

    def info(self, *a, **k):
        pass


def main() -> int:
    course_db.delete_course(LANG)             # dọn data test cũ
    try:
        # ── 1. audio skip re-attach: text khớp → gắn lại ────────────────────
        print("\n=== 1. audio skip re-attach (text khớp) ===")
        save_checkpoint(LANG, STAGE_AUDIO,
                        {"tracks": _tracks(), "generated": 3},
                        day=1, status=STATUS_DONE)
        lesson = {"day": 1, "vocab": [{"word": "猫"}, {"word": "犬"}]}
        LOGS.clear()
        data = run_audio_stage(LANG, 1, lesson, chain=None, log_fn=_log,
                               allow_degraded=True)
        ck("skip log 'đã có — bỏ qua'",
           any("đã có" in l and "bỏ qua" in l for l in LOGS), LOGS)
        ck("audio_ref[0] gắn lại = m_a1",
           lesson["vocab"][0].get("audio_ref") == "m_a1",
           lesson["vocab"][0])
        ck("audio_ref[1] gắn lại = m_a2",
           lesson["vocab"][1].get("audio_ref") == "m_a2",
           lesson["vocab"][1])
        ck("vocab_audio[猫] = m_a1",
           (lesson.get("media", {}).get("vocab_audio") or {}).get("猫") == "m_a1",
           lesson.get("media"))
        ck("meaning_audio_ref (variant vi) = m_vi1",
           lesson["vocab"][0].get("meaning_audio_ref") == "m_vi1",
           lesson["vocab"][0])
        ck("return data giữ tracks (3)",
           len(data.get("tracks") or []) == 3, data)

        # ── 2. audio skip re-attach: text KHÁC → không gắn ref sai ─────────
        print("\n=== 2. audio skip re-attach (từ đã đổi → KHÔNG gắn) ===")
        save_checkpoint(LANG, STAGE_AUDIO,
                        {"tracks": [{"kind": "vocab", "index": 0,
                                     "text": "từ_cũ", "ref": "m_old",
                                     "variant": "target"}],
                         "generated": 1},
                        day=2, status=STATUS_DONE)
        lesson2 = {"day": 2, "vocab": [{"word": "từ_mới"}]}
        run_audio_stage(LANG, 2, lesson2, chain=None, log_fn=_log,
                        allow_degraded=True)
        ck("text khác ⇒ KHÔNG gắn audio_ref cũ",
           not lesson2["vocab"][0].get("audio_ref"), lesson2["vocab"][0])

        # ── 3. dialogue skip re-attach ──────────────────────────────────────
        print("\n=== 3. dialogue skip re-attach ===")
        dlg = [{"situation": "s", "turns": [{"speaker": "A", "line": "x"}]}]
        save_checkpoint(LANG, STAGE_DIALOGUE,
                        {"dialogues": dlg, "generated": 1},
                        day=1, status=STATUS_DONE)
        lesson3 = {"day": 1, "vocab": [{"word": "猫"}], "dialogue": []}
        LOGS.clear()
        run_dialogue_stage(LANG, 1, lesson3, coord=None, log_fn=_log)
        ck("skip log hội thoại", any("Hội thoại" in l for l in LOGS), LOGS)
        ck("lesson.dialogue gắn lại từ checkpoint",
           lesson3.get("dialogue") == dlg, lesson3.get("dialogue"))
        # lesson ĐÃ có dialogue → không đè
        lesson3b = {"day": 1, "dialogue": [{"situation": "cũ"}]}
        run_dialogue_stage(LANG, 1, lesson3b, coord=None, log_fn=_log)
        ck("lesson đã có dialogue → giữ nguyên (không đè)",
           lesson3b["dialogue"][0]["situation"] == "cũ", lesson3b["dialogue"])

        # ── 4. verify: mark pending NHƯNG GIỮ data cũ ───────────────────────
        print("\n=== 4. verify giữ data cũ khi mark pending ===")
        tracks12 = [{"kind": "vocab", "index": i, "text": f"w{i}",
                     "ref": f"m_t{i}", "variant": "target"}
                    for i in range(12)]
        save_checkpoint(LANG, STAGE_AUDIO,
                        {"tracks": tracks12, "generated": 12},
                        day=1, status=STATUS_DONE)
        save_checkpoint(LANG, STAGE_IMAGES,
                        {"images": [{"id": "m_i1"}], "generated": 1},
                        day=1, status=STATUS_DONE)
        lesson4 = {"day": 1,
                   "vocab": [{"word": "猫"}, {"word": "犬"}],   # thiếu ref
                   "dialogue": dlg, "media": {}}
        LOGS.clear()
        run_media_verify_stage(LANG, 1, lesson4, log_fn=_log)
        cpa = load_checkpoint(LANG, STAGE_AUDIO, 1) or {}
        cpi = load_checkpoint(LANG, STAGE_IMAGES, 1) or {}
        ck("audio → pending", cpa.get("status") == STATUS_PENDING, cpa.get("status"))
        ck("audio data GIỮ 12 tracks (không bị ghi đè)",
           len((cpa.get("data") or {}).get("tracks") or []) == 12,
           cpa.get("data"))
        ck("audio có pending_reason", "thiếu" in
           str((cpa.get("data") or {}).get("pending_reason", "")), cpa.get("data"))
        ck("images → pending + GIỮ data images",
           cpi.get("status") == STATUS_PENDING and
           len((cpi.get("data") or {}).get("images") or []) == 1,
           cpi)
        ck("lesson CÓ dialogue ⇒ checkpoint dialogue KHÔNG bị đụng",
           (load_checkpoint(LANG, STAGE_DIALOGUE, 1) or {}).get("status")
           == STATUS_DONE)

        # ── 5. verify: dialogue thiếu → mark pending + log ──────────────────
        print("\n=== 5. verify đếm DIALOGUE ===")
        save_checkpoint(LANG, STAGE_DIALOGUE, {"dialogues": []},
                        day=2, status=STATUS_DONE)
        lesson5 = {"day": 2, "vocab": [{"word": "猫"}], "dialogue": []}
        LOGS.clear()
        run_media_verify_stage(LANG, 2, lesson5, log_fn=_log)
        cpd = load_checkpoint(LANG, STAGE_DIALOGUE, 2) or {}
        ck("dialogue rỗng → pending (sinh bù lần sau)",
           cpd.get("status") == STATUS_PENDING, cpd.get("status"))
        ck("log có 'hội thoại'",
           any("hội thoại" in l for l in LOGS), LOGS)

        # ── 6. content regen ĐỔI từ → invalidate media/dialogue ────────────
        print("\n=== 6. content đổi từ → invalidate checkpoint ===")
        import ai.pipeline as pl
        new_vocab = [{"word": f"moi_{i}"} for i in range(10)]    # ≥ MIN_VOCAB
        course = {"days": [{"day": 1, "title": "T", "phase": "P", "level": "L",
                            "topic": "T", "words": [],
                            "vocab": [{"word": "từ_cũ"}], "quiz": {}}]}
        for stg in (STAGE_IMAGES, STAGE_AUDIO, STAGE_DIALOGUE):
            save_checkpoint(LANG, stg, {"x": 1}, day=1, status=STATUS_DONE)
        orig = pl._ask_with_retry
        pl._ask_with_retry = lambda *a, **k: (True, {"title": "T",
                                                     "vocab": new_vocab}, None)
        try:
            lesson6 = pl._run_day(
                LANG, 1, {"title": "T", "phase": "P", "words": []}, course,
                coord=None, log=_Log(), budget=_Budget(), emit=_log,
                stages=[STAGE_CONTENT], level="L1", allow_degraded=True,
                max_images=10, max_audio=12, chain=None, resume=True,
                save_each_day=False)
        finally:
            pl._ask_with_retry = orig
        ck("_run_day chạy OK với content mới",
           lesson6 is not None and len(lesson6.get("vocab") or []) == 10,
           lesson6 and len(lesson6.get("vocab") or []))
        for stg in (STAGE_IMAGES, STAGE_AUDIO, STAGE_DIALOGUE):
            cp = load_checkpoint(LANG, stg, 1) or {}
            ck(f"{stg}: đổi từ → invalidate = pending",
               cp.get("status") == STATUS_PENDING, cp.get("status"))

        # ── 7. content GIỐNG từ → KHÔNG invalidate ──────────────────────────
        print("\n=== 7. content giống từ → GIỮ checkpoint done ===")
        same_vocab = [{"word": f"same_{i}"} for i in range(10)]
        course7 = {"days": [{"day": 3, "title": "T", "phase": "P", "level": "L",
                             "topic": "T", "words": [],
                             "vocab": [dict(v) for v in same_vocab],
                             "quiz": {}}]}
        for stg in (STAGE_IMAGES, STAGE_AUDIO, STAGE_DIALOGUE):
            save_checkpoint(LANG, stg, {"x": 1}, day=3, status=STATUS_DONE)
        pl._ask_with_retry = lambda *a, **k: (True, {"title": "T",
                                                     "vocab": same_vocab}, None)
        try:
            lesson7 = pl._run_day(
                LANG, 3, {"title": "T", "phase": "P", "words": []}, course7,
                coord=None, log=_Log(), budget=_Budget(), emit=_log,
                stages=[STAGE_CONTENT], level="L1", allow_degraded=True,
                max_images=10, max_audio=12, chain=None, resume=True,
                save_each_day=False)
        finally:
            pl._ask_with_retry = orig
        ck("_run_day chạy OK (giống từ)", lesson7 is not None, lesson7)
        for stg in (STAGE_IMAGES, STAGE_AUDIO, STAGE_DIALOGUE):
            cp = load_checkpoint(LANG, stg, 3) or {}
            ck(f"{stg}: giống từ → GIỮ done",
               cp.get("status") == STATUS_DONE, cp.get("status"))
    finally:
        course_db.delete_course(LANG)         # luôn dọn

    print(f"\nKết quả: {PASS[0]} PASS / {FAIL[0]} FAIL (tổng {PASS[0] + FAIL[0]})")
    return 1 if FAIL[0] else 0


if __name__ == "__main__":
    sys.exit(main())
