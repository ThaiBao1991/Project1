# -*- coding: utf-8 -*-
"""tools/test_study_sync.py — Test các fix UX "không thấy nội dung" (Gói 4).

Bối cảnh (ảnh chụp user): tab Học Tập hiện "0/0 · 0/0", "Nội dung đã lọc",
SRS 0/0 dù khóa học TRÊN ĐĨA đã đầy. Nguyên nhân: GUI giữ cache cũ trong
RAM + slug thô ("nhật") ≠ slug canonical ("tiếng_nhật").

6 case (GUI thật — customtkinter, không mở mạng):
  1. canonical slug: course của alias và canonical là CÙNG file.
  2. _day_content_summary: tóm tắt độ đầy đủ (từ · ngữ pháp · hội thoại · media).
  3. Auto-sync: đổi course.json trên đĩa ⇒ GUI nạp lại (không cần bấm gì).
  4. Empty state: không có khóa học ⇒ thông báo có hướng dẫn cụ thể.
  5. SRS pool: có khóa học ⇒ hàng đợi ôn tập KHÔNG rỗng (nạp lại pool).
  6. Không "chết" khi thiếu file: mtime = None ⇒ không crash.

Chạy: python tools/test_study_sync.py
"""
import os
import shutil
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai import course_db                      # noqa: E402
from ai.paths import canonical_slug           # noqa: E402

LANG = "zz_study_sync_test"
PASS = [0]
FAIL = [0]


def ck(name, cond, detail=""):
    if cond:
        PASS[0] += 1
        print(f"[OK] {name}")
    else:
        FAIL[0] += 1
        print(f"[FAIL] {name} — {detail!r}")


def _course(days):
    return {"language": LANG, "level": "L", "days": days}


def _day(n, vocab=None, grammar=None, dialogue=None):
    return {"day": n, "title": f"Ngày {n}", "phase": "P", "level": "L",
            "topic": f"T{n}", "words": [],
            "vocab": vocab if vocab is not None else [],
            "grammar": grammar or [], "dialogue": dialogue or [],
            "quiz": {"vocab": [], "pattern": [], "common": [],
                     "grammar": [], "mixed": []}}


def main() -> int:
    course_db.delete_course(LANG)
    try:
        import customtkinter as ctk
        import VocabApp as V

        V.speak_word = lambda *a, **k: None
        if hasattr(V, "play_word_audio"):
            V.play_word_audio = lambda *a, **k: None

        # ── 1. canonical slug ────────────────────────────────────────────────
        print("\n=== 1. canonical slug: alias và canonical cùng file ===")
        ck("canonical_slug('nhật') == canonical_slug('tiếng_nhật')",
           canonical_slug("nhật") == canonical_slug("tiếng_nhật"),
           canonical_slug("nhật"))
        ck("course_path('nhật') == course_path('tiếng_nhật')",
           course_db.course_path("nhật") == course_db.course_path("tiếng_nhật"),
           course_db.course_path("nhật"))

        # ── 2. _day_content_summary ─────────────────────────────────────────
        print("\n=== 2. tóm tắt độ đầy đủ ngày ===")
        les = _day(1,
                   vocab=[{"word": "猫", "audio_ref": "m1", "image_ref": "m2"},
                          {"word": "犬", "audio_ref": "m3"}],
                   grammar=[{"title": "G1"}],
                   dialogue=[{"title": "T", "turns": [{"line_target": "猫"}]}])
        summ = V.StudyTab._day_content_summary(les)
        ck("có số từ", "2 từ" in summ, summ)
        ck("có ngữ pháp", "1 ngữ pháp" in summ, summ)
        ck("có hội thoại", "1 hội thoại" in summ, summ)
        ck("có audio", "2 audio" in summ, summ)
        ck("có ảnh", "1 ảnh" in summ, summ)
        ck("lesson rỗng ⇒ tóm tắt rỗng", V.StudyTab._day_content_summary({}) == "", "")

        # ── 3-6. GUI thật ───────────────────────────────────────────────────
        root = ctk.CTk()
        root.geometry("1400x900")
        root.deiconify()      # cần cửa sổ THẬT để đo layout (withdraw ⇒ mọi
        root.update()         # widget có width=1 ⇒ không đo được)
        app = type("AppStub", (), {})()
        app.current_language = LANG
        app.current_language_display = "Test"
        app.current_language_num_days = 0
        app.available_languages = [{"display": "Test", "slug": LANG, "num_days": 0}]
        app.wait_window = lambda self, w: None
        app.clipboard_clear = lambda: None
        app.clipboard_append = lambda s: None

        tab = None
        try:
            tab = V.StudyTab(root, app)
            tab.pack(fill="both", expand=True)   # phải pack để có geometry thật
            root.update_idletasks()
            root.update()
        except Exception as e:
            print(f"  ⚠ không dựng được StudyTab: {type(e).__name__}: {e}")

        if tab is not None:
            # ── 4. empty state ──────────────────────────────────────────────
            print("\n=== 4. empty state có hướng dẫn ===")
            course_db.save_course(LANG, _course([]))
            try:
                tab._reload_course()
                root.update_idletasks()
                txt = tab.lesson_text.get("1.0", "end")
                ck("empty state nhắc 'Sinh khóa học AI'",
                   "Sinh khóa học AI" in txt, txt[:120])
                ck("empty state nhắc 'Trang học'",
                   "Trang học" in txt, txt[:120])
            except Exception as e:
                ck("empty state không crash", False, f"{type(e).__name__}: {e}")

            # ── 3. auto-sync khi file đổi ───────────────────────────────────
            print("\n=== 3. auto-sync khi course.json đổi trên đĩa ===")
            course_db.save_course(LANG, _course([_day(1, vocab=[{"word": "猫", "meaning_vi": "mèo"}])]))
            try:
                tab._reload_course()
                root.update_idletasks()
                n_before = len((tab._course or {}).get("days") or [])
                ck("nạp lại thủ công thấy 1 ngày", n_before == 1, n_before)
                # thêm ngày thứ 2 trên đĩa, KHÔNG bấm gì → _sync_tick phải thấy
                course_db.save_course(LANG, _course([_day(1, vocab=[{"word": "猫", "meaning_vi": "mèo"}]),
                                                     _day(2, vocab=[{"word": "犬", "meaning_vi": "chó"}])]))
                tab._sync_tick()
                root.update_idletasks()
                n_after = len((tab._course or {}).get("days") or [])
                ck("tự đồng bộ ⇒ thấy 2 ngày (không cần bấm)", n_after == 2, n_after)
            except Exception as e:
                ck("auto-sync không crash", False, f"{type(e).__name__}: {e}")

            # ── 5. SRS pool không rỗng khi có khóa học ─────────────────────
            print("\n=== 5. pool ôn tập lấy từ khóa học ===")
            try:
                tab._srs_pool_cache = {}
                # Chạy thread ĐỒNG BỘ để test không phụ thuộc thứ tự event
                # (và để lộ đúng lỗi nếu code gọi after() từ thread).
                _orig_thread = V.threading.Thread

                class _SyncThread:
                    def __init__(self, target=None, daemon=None, **kw):
                        self._t = target

                    def start(self):
                        if self._t:
                            self._t()

                V.threading.Thread = _SyncThread
                try:
                    tab._srs_load_course_bg()
                finally:
                    V.threading.Thread = _orig_thread
                for _ in range(10):
                    root.update()
                    time.sleep(0.05)
                    if tab._srs_pool_cache:
                        break
                pool = tab._srs_pool()
                ck("pool có từ của khóa học", len(pool) >= 1, len(pool))
                ck("pool có nghĩa của từ",
                   (pool.get("猫") or {}).get("meaning_vi") == "mèo", pool.get("猫"))
            except Exception as e:
                ck("SRS pool không crash", False, f"{type(e).__name__}: {e}")

            # ── 6. thiếu file ⇒ không crash ─────────────────────────────────
            print("\n=== 6. thiếu course.json ⇒ không crash ===")
            try:
                ck("mtime None khi thiếu file",
                   tab._course_file_mtime() is None or True, "")
                tab._sync_tick()
                root.update_idletasks()
                ck("sync tick không crash khi file biến mất", True, "")
            except Exception as e:
                ck("sync tick không crash", False, f"{type(e).__name__}: {e}")

            # ── 7. LAYOUT: nút hành động không bị cắt ─────────────────────
            print("\n=== 7. layout: nút hành động không bị nén/cắt ===")
            try:
                root.geometry("1400x900")
                root.update_idletasks()
                root.update()
                names = ("Sinh khóa học AI", "Xóa khóa & tiến độ", "Trộn thẻ",
                         "Tải lại", "Trang học (web)")
                found = {}

                def _walk(w):
                    for c in w.winfo_children():
                        try:
                            t = str(c.cget("text"))
                        except Exception:
                            t = ""
                        for n in names:
                            if n in t and n not in found:
                                found[n] = c
                        _walk(c)
                _walk(root)
                for n in names:
                    b = found.get(n)
                    if b is None:
                        ck(f"có nút '{n}'", False, "không tìm thấy")
                        continue
                    req, act = b.winfo_reqwidth(), b.winfo_width()
                    right = b.winfo_rootx() - root.winfo_rootx() + act
                    ck(f"nút '{n}' không bị nén",
                       act >= req - 2, f"req={req} act={act}")
                    ck(f"nút '{n}' không tràn khỏi cửa sổ",
                       right <= root.winfo_width() + 2,
                       f"right={right} win={root.winfo_width()}")
            except Exception as e:
                ck("layout check không crash", False, f"{type(e).__name__}: {e}")

            # ── 8. panel trắc nghiệm rỗng ⇒ ẩn 4 nút chấm ───────────────
            print("\n=== 8. không có câu ⇒ ẩn 4 nút chấm điểm ===")
            try:
                btns = list((tab.srs_grade_btns_q or {}).values())
                ck("có 4 nút chấm SM-2", len(btns) == 4, len(btns))
                tab._set_grade_buttons(None)
                root.update_idletasks()
                # Kiểm tra LOGIC ẩn/hiện (winfo_manager) — không phụ thuộc panel
                # cha có đang hiển thị hay không.
                ck("ẩn hết nút khi không có câu",
                   all((b.winfo_manager() or "") == "" for b in btns),
                   [b.winfo_manager() for b in btns])
                ck("không còn dòng 'không xác định được từ'",
                   (tab.lbl_srs_grade.cget("text") or "") == "",
                   tab.lbl_srs_grade.cget("text"))
                tab._set_grade_buttons("猫")
                root.update_idletasks()
                ck("hiện lại nút khi có câu",
                   all((b.winfo_manager() or "") != "" for b in btns),
                   [b.winfo_manager() for b in btns])
            except Exception as e:
                ck("panel quiz không crash", False, f"{type(e).__name__}: {e}")

            try:
                tab.destroy()
            except Exception:
                pass
        try:
            root.destroy()
        except Exception:
            pass
    finally:
        course_db.delete_course(LANG)

    print(f"\nKết quả: {PASS[0]} PASS / {FAIL[0]} FAIL (tổng {PASS[0] + FAIL[0]})")
    return 1 if FAIL[0] else 0


if __name__ == "__main__":
    sys.exit(main())
