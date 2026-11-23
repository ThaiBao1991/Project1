# -*- coding: utf-8 -*-
"""tools/test_stop_makeup.py — Test 3 FIX pipeline 2026-11-11 (dừng + bù + âm thanh).

Xem docs/UPGRADE_17.md mục 7.19:
  A. Nút ⏹ Dừng:
     1. _ask_with_retry: kind="stopped" / GenerationStopped → thoát NGAY (không retry 3 lần).
     2. _run_day: stop_check=True → raise TRƯỚC stage đầu tiên (không chạy hết 7 stage).
     3. _run_days_parallel: stop từ đầu → raise NGAY, KHÔNG treo chờ executor (cancel hàng đợi).
     4. run_dialogue_stage: request trả "stopped" → raise NGAY, KHÔNG lưu degraded,
        KHÔNG chạy tiếp media_verify ("đánh dấu sinh bù" khi vừa bấm Dừng).
     5. run_audio_stage: stop giữa chừng → checkpoint PENDING (giữ phần đã sinh), KHÔNG done.
  B. Bù trong cùng run:
     6. _media_pending_days: chỉ lấy ngày PENDING.
     7. _makeup_pending_days: bù ngay trong run · dừng khi Dừng/Hết quota.
  C. Đủ âm thanh:
     8. run_audio_stage: skip phần ĐÃ có ref · sinh audio nghĩa · sinh audio HỘI THOẠI.
     9. run_media_verify_stage: audio nghĩa + audio hội thoại thiếu → mark AUDIO pending.

Chạy: python tools/test_stop_makeup.py   (0 call API thật — mock hết)
"""
import os
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai import course_db                      # noqa: E402
from ai.pipeline_store import (STAGE_AUDIO, STAGE_CONTENT, STAGE_DIALOGUE,   # noqa: E402
                               STAGE_IMAGES, STAGE_MEDIA_VERIFY, STATUS_DONE,
                               STATUS_PENDING, load_checkpoint, save_checkpoint)

LANG = "zz_stop_makeup_test"
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
        self.tts = 0
        self.counters = {}

    def can_call(self, n=1):
        return self.can

    def consume_call(self):
        pass

    def consume_tts(self):
        self.tts += 1


class _StopAfter:
    """stop_check: False cho `first` lần gọi đầu, sau đó luôn True."""

    def __init__(self, first=1):
        self.calls = 0
        self.first = first

    def __call__(self):
        self.calls += 1
        return self.calls > self.first


class _CoordStopped:
    def __init__(self):
        self.calls = 0

    def request(self, prompt, response_schema=None, **kw):
        self.calls += 1
        return {"ok": False, "error": {"kind": "stopped",
                                       "message": "người dùng dừng"}}


def main() -> int:
    course_db.delete_course(LANG)
    import ai.pipeline as pl
    import ai.pipeline_media as pm
    try:
        # ══ A1. _ask_with_retry: stopped → NGAY, không retry ═══════════════
        print("\n=== A1. _ask_with_retry dừng ngay (kind=stopped) ===")
        c = _CoordStopped()
        raised = None
        try:
            pl._ask_with_retry(c, "p", None, lambda t: t, _Log(),
                               STAGE_CONTENT, _Budget(), 3)
        except pl.GenerationStopped:
            raised = "stopped"
        except Exception as e:
            raised = f"{type(e).__name__}: {e}"
        ck("kind=stopped → GenerationStopped", raised == "stopped", raised)
        ck("chỉ gọi ĐÚNG 1 lần (không retry 3)", c.calls == 1, c.calls)

        # ══ A1b. exception GenerationStopped từ coord → propagate ══════════
        print("\n=== A1b. coord.request ném GenerationStopped → propagate ===")

        class _CoordRaise:
            def __init__(self):
                self.calls = 0

            def request(self, *a, **k):
                self.calls += 1
                raise pl.GenerationStopped()

        c2 = _CoordRaise()
        raised2 = None
        try:
            pl._ask_with_retry(c2, "p", None, lambda t: t, _Log(),
                               STAGE_CONTENT, _Budget(), 3)
        except pl.GenerationStopped:
            raised2 = "stopped"
        except Exception as e:
            raised2 = f"{type(e).__name__}: {e}"
        ck("exception GenerationStopped → propagate", raised2 == "stopped", raised2)
        ck("không retry sau exception", c2.calls == 1, c2.calls)

        # ══ A2. _run_day: stop TRƯỚC stage đầu ═════════════════════════════
        print("\n=== A2. _run_day raise trước khi chạy stage ===")
        course = {"days": [{"day": 1, "title": "T", "phase": "P", "level": "L",
                            "topic": "T", "words": [],
                            "vocab": [{"word": "猫"}], "quiz": {}}],
                  "plan": [{"day": 1, "title": "T", "phase": "P"}]}
        raised3 = None
        try:
            pl._run_day(LANG, 1, course["plan"][0], course, coord=None,
                        log=_Log(), budget=_Budget(), emit=_log,
                        stages=[STAGE_CONTENT], level="L1",
                        allow_degraded=True, max_images=10, max_audio=12,
                        chain=None, resume=True, save_each_day=False,
                        stop_check=lambda: True)
        except pl.GenerationStopped:
            raised3 = "stopped"
        except Exception as e:
            raised3 = f"{type(e).__name__}: {e}"
        ck("stop_check=True → GenerationStopped ngay", raised3 == "stopped", raised3)

        # ══ A3. _run_days_parallel: dừng KHÔNG treo + finally save ═════════
        print("\n=== A3. _run_days_parallel stop từ đầu → raise, không treo ===")
        t0 = time.time()
        raised4 = None
        try:
            pl._run_days_parallel(
                LANG, [{"day": 1}, {"day": 2}], course, None, _Log(), _Budget(),
                _log, [STAGE_CONTENT], "L1", True, 10, 12, None, True,
                2, lambda *a, **k: None, lambda: True, t0, 999, workers=2)
        except pl.GenerationStopped:
            raised4 = "stopped"
        except Exception as e:
            raised4 = f"{type(e).__name__}: {e}"
        ck("parallel stop → GenerationStopped", raised4 == "stopped", raised4)
        ck("không treo (<10s) — trả về ngay", time.time() - t0 < 10,
           round(time.time() - t0, 1))

        # ══ A4. dialogue: stopped → raise, KHÔNG checkpoint degraded ═══════
        print("\n=== A4. run_dialogue_stage dừng ngay (không nuốt) ===")
        lesson = {"day": 5, "title": "Bài 5", "topic": "giao tiếp",
                  "vocab": [{"word": "猫", "meaning_vi": "mèo",
                             "pronunciation": "neko"}]}
        raised5 = None
        LOGS.clear()
        try:
            pm.run_dialogue_stage(LANG, 5, lesson, coord=_CoordStopped(),
                                  log_fn=_log, level="A1", budget=_Budget())
        except pl.GenerationStopped:
            raised5 = "stopped"
        except Exception as e:
            raised5 = f"{type(e).__name__}: {e}"
        ck("request stopped → GenerationStopped", raised5 == "stopped", raised5)
        cpd = load_checkpoint(LANG, STAGE_DIALOGUE, 5)
        ck("KHÔNG lưu checkpoint (không degraded/skip)",
           cpd is None or cpd.get("status") not in ("degraded", "skipped"),
           cpd and cpd.get("status"))
        ck("KHÔNG log 'sinh bù lần sau'",
           not any("bù" in l and "sau" in l for l in LOGS), LOGS)

        # ══ A5. audio: stop giữa chừng → PENDING, không synth tiếp ═════════
        print("\n=== A5. run_audio_stage dừng giữa chừng → PENDING ===")
        import ai.tts_generator as tts

        synth_calls = []

        def _synth_fail(*a, **k):
            synth_calls.append(a[1] if len(a) > 1 else "?")
            raise AssertionError("synth phải KHÔNG chạy khi đã dừng")

        orig_syn, orig_q = tts.synthesize, tts.tts_quota_remaining
        tts.synthesize, tts.tts_quota_remaining = _synth_fail, (lambda: 999)
        lesson5 = {"day": 6, "vocab": [{"word": "猫", "meaning_vi": "mèo"}],
                   "dialogue": [{"title": "T6",
                                 "turns": [{"speaker": "A", "line": "xin chào"}]}]}
        raised6 = None
        try:
            pm.run_audio_stage(LANG, 6, lesson5, chain=None, log_fn=_log,
                               budget=_Budget(), allow_degraded=True,
                               stop_check=_StopAfter(first=1))
        except pl.GenerationStopped:
            raised6 = "stopped"
        except Exception as e:
            raised6 = f"{type(e).__name__}: {e}"
        finally:
            tts.synthesize, tts.tts_quota_remaining = orig_syn, orig_q
        cpa = load_checkpoint(LANG, STAGE_AUDIO, 6) or {}
        ck("dừng → GenerationStopped", raised6 == "stopped", raised6)
        ck("checkpoint PENDING (giữ phần đã sinh, không done)",
           cpa.get("status") == STATUS_PENDING, cpa.get("status"))
        ck("KHÔNG synth thêm khi dừng", not synth_calls, synth_calls)

        # ══ C8a. audio: skip phần ĐÃ có ref + sinh phần thiếu ═════════════
        print("\n=== C8. audio: skip từ đã đủ · sinh nghĩa · sinh HỘI THOẠI ===")
        import ai.media_store as ms
        import settings as settings_mod

        orig_ls = settings_mod.load_settings
        settings_mod.load_settings = lambda: {"media": {"tts_bilingual_mode": True}}
        orig_sa = ms.save_audio

        def _fake_save(language, day, name, data, **kw):
            return {"id": f"m_fake_{name}", "rel_path": f"media/{language}/{name}.mp3"}

        ms.save_audio = _fake_save

        def _synth_ok(language, text, stage_idx=None, coord=None, log_fn=None,
                      voice=None):
            synth_calls.append(text)
            return {"path": os.path.abspath(__file__), "engine": "edge-tts",
                    "voice": voice or ""}

        tts.synthesize = _synth_ok
        synth_calls.clear()
        lesson8 = {"day": 7,
                   "vocab": [
                       {"word": "猫", "meaning_vi": "mèo",
                        "audio_ref": "m_jp1", "meaning_audio_ref": "m_vi1"},
                       {"word": "犬", "meaning_vi": "chó"}],
                   "dialogue": [{"title": "T7",
                                 "turns": [{"speaker": "A", "line": "こんにちは"},
                                           {"speaker": "B", "line": "こんにちは"}]}]}
        try:
            data8 = pm.run_audio_stage(LANG, 7, lesson8, chain=None, log_fn=_log,
                                       budget=_Budget(), allow_degraded=True)
        finally:
            tts.synthesize, tts.tts_quota_remaining = orig_syn, orig_q
            ms.save_audio = orig_sa
            settings_mod.load_settings = orig_ls
        ck("từ ĐÃ đủ ref → KHÔNG TTS lại (không có '猫')",
           "猫" not in synth_calls, synth_calls)
        ck("từ thiếu → TTS ('犬')", "犬" in synth_calls, synth_calls)
        ck("sinh audio NGHĨA ('chó')", "chó" in synth_calls, synth_calls)
        ck("sinh audio HỘI THOẠI (nối các lượt)",
           any("こんにちは" in t for t in synth_calls), synth_calls)
        ck("từ thiếu nhận audio_ref mới",
           str(lesson8["vocab"][1].get("audio_ref", "")).startswith("m_fake_"),
           lesson8["vocab"][1])
        ck("từ thiếu nhận meaning_audio_ref",
           str(lesson8["vocab"][1].get("meaning_audio_ref", "")).startswith("m_fake_"),
           lesson8["vocab"][1])
        ck("từ ĐÃ đủ GIỮ ref cũ (m_jp1)",
           lesson8["vocab"][0].get("audio_ref") == "m_jp1",
           lesson8["vocab"][0])
        ck("media.dialogue_audio[0] gắn",
           str((lesson8.get("media") or {}).get("dialogue_audio", {})
               .get("0", "")).startswith("m_fake_"),
           lesson8.get("media"))
        ck("dialogue[0].audio_ref gắn",
           str(lesson8["dialogue"][0].get("audio_ref", "")).startswith("m_fake_"),
           lesson8["dialogue"][0])
        cpa7 = load_checkpoint(LANG, STAGE_AUDIO, 7) or {}
        ck("checkpoint DONE + có dialogue_tracks (1)",
           cpa7.get("status") == STATUS_DONE and
           len((cpa7.get("data") or {}).get("dialogue_tracks") or []) == 1,
           cpa7.get("status"))

        # ══ C8b. skip re-attach: dialogue audio gắn lại theo TITLE ════════
        print("\n=== C8b. audio skip → re-attach dialogue theo TITLE ===")
        lesson8b = {"day": 7,
                    "vocab": [{"word": "猫", "meaning_vi": "mèo"},
                              {"word": "犬", "meaning_vi": "chó"}],
                    "dialogue": [{"title": "T7", "turns": []}]}
        pm.run_audio_stage(LANG, 7, lesson8b, chain=None, log_fn=_log,
                           budget=_Budget(), allow_degraded=True)
        ck("skip → dialogue audio ref gắn lại (title khớp)",
           str((lesson8b.get("media") or {}).get("dialogue_audio", {})
               .get("0", "")).startswith("m_fake_"),
           lesson8b.get("media"))
        # 猫: ref cũ đến từ run trước, KHÔNG nằm trong checkpoint tracks của
        # run này → reattach không tìm thấy (đúng — verify sẽ mark pending).
        # 犬: có track trong checkpoint (sinh ở C8) → phải gắn lại được.
        ck("skip → audio_ref từ CÓ track trong ckpt gắn lại (犬)",
           str(lesson8b["vocab"][1].get("audio_ref", "")).startswith("m_fake_"),
           lesson8b["vocab"][1])
        lesson8c = {"day": 7, "vocab": [],
                    "dialogue": [{"title": "TITLE_MỚI", "turns": []}]}
        pm.run_audio_stage(LANG, 7, lesson8c, chain=None, log_fn=_log,
                           budget=_Budget(), allow_degraded=True)
        ck("title ĐỔI → KHÔNG gắn ref cũ",
           not lesson8c["dialogue"][0].get("audio_ref"),
           lesson8c["dialogue"][0])

        # ══ C9. verify: audio nghĩa + audio hội thoại thiếu → pending ══════
        print("\n=== C9. verify đếm audio NGHĨA + audio HỘI THOẠI ===")
        settings_mod.load_settings = lambda: {"media": {"tts_bilingual_mode": True}}
        save_checkpoint(LANG, STAGE_AUDIO, {"tracks": []}, day=8,
                        status=STATUS_DONE)
        lesson9 = {"day": 8,
                   "vocab": [{"word": "猫", "meaning_vi": "mèo",
                              "audio_ref": "m_a"}],     # thiếu meaning_audio_ref
                   "dialogue": [{"title": "T8", "turns": []}],  # thiếu audio
                   "media": {}}
        LOGS.clear()
        try:
            pm.run_media_verify_stage(LANG, 8, lesson9, log_fn=_log)
        finally:
            settings_mod.load_settings = orig_ls
        cpa9 = load_checkpoint(LANG, STAGE_AUDIO, 8) or {}
        ck("audio nghĩa + audio hội thoại thiếu → AUDIO pending",
           cpa9.get("status") == STATUS_PENDING, cpa9.get("status"))
        ck("pending_reason có 'thiếu'",
           "thiếu" in str((cpa9.get("data") or {}).get("pending_reason", "")),
           cpa9.get("data"))
        ck("log nêu rõ 'audio nghĩa'/'audio hội thoại'",
           any(("audio nghĩa" in l) and ("audio hội thoại" in l) for l in LOGS),
           LOGS[-1:])

        # ══ B6. _media_pending_days ════════════════════════════════════════
        print("\n=== B6. _media_pending_days chỉ lấy ngày PENDING ===")
        course6 = {"days": [{"day": 1}, {"day": 2}, {"day": 3}],
                   "plan": [{"day": 1, "title": "A"},
                            {"day": 2, "title": "B"},
                            {"day": 3, "title": "C"}]}
        save_checkpoint(LANG, STAGE_AUDIO, {}, day=1, status=STATUS_PENDING)
        save_checkpoint(LANG, STAGE_DIALOGUE, {}, day=2, status=STATUS_PENDING)
        save_checkpoint(LANG, STAGE_AUDIO, {}, day=3, status=STATUS_DONE)
        pend = pl._media_pending_days(
            LANG, course6, [STAGE_IMAGES, STAGE_AUDIO, STAGE_DIALOGUE,
                            STAGE_MEDIA_VERIFY])
        ck("pending = [1, 2] (day3 done → loại)",
           pend == [1, 2], pend)

        # ══ B7. _makeup_pending_days: bù NGAY trong run ═══════════════════
        print("\n=== B7. makeup: bù ngay · dừng khi Dừng / hết quota ===")
        calls = []
        orig_rd = pl._run_day

        def _fake_run_day(language, dn, pday, course, coord, log, budget, emit,
                          stages, *a, **k):
            calls.append(dn)
            # Bù xong → MỌI stage media của ngày này done (nếu chỉ ghi audio,
            # ngày còn dialogue pending → pass sau lại lấy ra → lặp vô hạn).
            for stg in (STAGE_IMAGES, STAGE_AUDIO, STAGE_DIALOGUE):
                save_checkpoint(language, stg, {"tracks": []}, day=dn,
                                status=STATUS_DONE)
            return {"day": dn}

        pl._run_day = _fake_run_day
        try:
            n = pl._makeup_pending_days(
                LANG, course6,
                [STAGE_IMAGES, STAGE_AUDIO, STAGE_DIALOGUE, STAGE_MEDIA_VERIFY],
                None, _Log(), _Budget(), _log, "L1", True, 10, 12, None, True,
                lambda: False, False, time.time(), 999, max_passes=2)
            ck("bù ngay trong run: gọi _run_day cho [1, 2]", calls == [1, 2], calls)
            ck("trả về số ngày đã bù = 2", n == 2, n)

            # Dừng → không bù
            save_checkpoint(LANG, STAGE_AUDIO, {}, day=1, status=STATUS_PENDING)
            calls.clear()
            n2 = pl._makeup_pending_days(
                LANG, course6,
                [STAGE_IMAGES, STAGE_AUDIO, STAGE_DIALOGUE, STAGE_MEDIA_VERIFY],
                None, _Log(), _Budget(), _log, "L1", True, 10, 12, None, True,
                lambda: True, False, time.time(), 999, max_passes=2)
            ck("đã bấm Dừng → KHÔNG bù (0 gọi)", calls == [] and n2 == 0,
               (calls, n2))

            # Hết quota → dừng êm, không exception
            n3 = pl._makeup_pending_days(
                LANG, course6,
                [STAGE_IMAGES, STAGE_AUDIO, STAGE_DIALOGUE, STAGE_MEDIA_VERIFY],
                None, _Log(), _Budget(can=False), _log, "L1", True, 10, 12,
                None, True, lambda: False, False, time.time(), 999,
                max_passes=2)
            ck("hết quota → dừng êm (0 gọi, không exception)",
               calls == [] and n3 == 0, (calls, n3))
        finally:
            pl._run_day = orig_rd

        # ══ B8. INTEGRATION: run_pipeline tự bù TRONG run ══════════════════
        print("\n=== B8. run_pipeline: day loop + makeup → audio bù 2 lần ===")
        LANG2 = "zz_makeup_run_test"
        course_db.delete_course(LANG2)
        try:
            course_db.save_course(LANG2, {
                "days": [{"day": 1, "title": "Bài 1", "phase": "N5", "level": "L",
                          "topic": "Tò mò", "words": ["猫"],
                          "vocab": [{"word": "猫", "meaning_vi": "mèo"}],
                          "quiz": {}}],
                "level": "L"})
            # Ngày 1 bị verify đánh dấu PENDING (thiếu audio) TRƯỚC run
            save_checkpoint(LANG2, STAGE_AUDIO, {"tracks": []}, day=1,
                            status=STATUS_PENDING)

            audio_calls = []

            def _fake_audio(language, day, lesson, chain, log_fn=print, **kw):
                audio_calls.append(day)
                if len(audio_calls) == 1:
                    # Lần 1 (day loop): vẫn thiếu → giữ PENDING (như thật)
                    save_checkpoint(language, STAGE_AUDIO, {"tracks": []},
                                    day=day, status=STATUS_PENDING)
                    return {}
                # Lần 2 (pass bù): bù xong → DONE
                save_checkpoint(language, STAGE_AUDIO, {"tracks": []},
                                day=day, status=STATUS_DONE)
                return {"generated": 1}

            class _Prov:
                coord = None

                @staticmethod
                def available():
                    return True, "fake"

            class _Chain:
                providers = [_Prov()]

            orig_ra = pm.run_audio_stage
            pm.run_audio_stage = _fake_audio
            try:
                res8 = pl.run_pipeline(
                    LANG2, stages=[STAGE_AUDIO], chain=_Chain(),
                    budget=_Budget(), workers=1, level="L", mode="full")
            finally:
                pm.run_audio_stage = orig_ra
            ck("run_pipeline chạy bình thường (không exception)",
               isinstance(res8, dict), res8)
            ck("audio stage gọi 2 lần: day loop (1) + PASS BÙ (1)",
               audio_calls == [1, 1], audio_calls)
            cp8 = load_checkpoint(LANG2, STAGE_AUDIO, 1) or {}
            ck("sau run: audio checkpoint DONE (đã bù trong run)",
               cp8.get("status") == STATUS_DONE, cp8.get("status"))
        finally:
            course_db.delete_course(LANG2)
            try:
                import glob as _g
                for _f in _g.glob(os.path.join(
                        BASE, "data", "logs", "zz_makeup_run_*")):
                    os.remove(_f)
            except Exception:
                pass
    finally:
        course_db.delete_course(LANG)

    print(f"\nKết quả: {PASS[0]} PASS / {FAIL[0]} FAIL (tổng {PASS[0] + FAIL[0]})")
    return 1 if FAIL[0] else 0


if __name__ == "__main__":
    sys.exit(main())
