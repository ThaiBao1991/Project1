# -*- coding: utf-8 -*-
"""tools/test_day_nav_loop.py — VÒNG LẶP kiểm tra điều hướng ngày & nút chế độ học.

User báo (ảnh 13/11): bấm "Ngữ pháp" vẫn ra từ vựng; chọn Ngày 1095 lại
hiện Ngày 1. Tool này mô phỏng đúng thao tác của app và CHẠY LẶP nhiều vòng
(ngày ngẫu nhiên có seed cố định) cho tới khi sạch lỗi.

3 khối kiểm tra, mỗi khối lặp N vòng:
  A. Chọn ngày N ⇒ tiêu đề + nội dung đúng N (và ô nhập ngày đồng bộ).
  B. Bấm 4 chế độ (Tất cả/Từ vựng/Ngữ pháp/Hội thoại) ⇒ nội dung LỌC đúng
     (chế độ Ngữ pháp không được lẫn từ vựng, và ngược lại).
  C. Gọi _load_selected_day() lại (mô phỏng auto-sync 5 s) ⇒ KHÔNG nhảy về
     ngày khác.

Cách dùng:
  python tools/test_day_nav_loop.py            # 5 vòng
  python tools/test_day_nav_loop.py --rounds 20
"""
import os
import random
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PASS = [0]
FAIL = [0]
FAILS = []


def ck(name, cond, detail=""):
    if cond:
        PASS[0] += 1
    else:
        FAIL[0] += 1
        FAILS.append(f"{name} — {detail}")
        print(f"[FAIL] {name} — {detail}")


def _make_course(n_days=1260):
    days = []
    for i in range(1, n_days + 1):
        days.append({
            "day": i, "title": f"T{i}", "phase": "P", "level": "N5",
            "topic": f"Topic {i}", "words": [],
            "vocab": [{"word": f"w{i}", "meaning_vi": f"nghĩa {i}"}],
            "sentence_patterns": [{"pattern": f"pat{i}", "meaning_vi": "mẫu"}],
            "common_sentences": [{"sentence": f"com{i}", "meaning_vi": "câu"}],
            "grammar": [{"title": f"NGỮ PHÁP NGÀY {i}", "explanation": "e"}],
            "dialogue": [{"title": f"HỘI THOẠI NGÀY {i}",
                          "turns": [{"speaker": "A", "line_target": f"w{i}"},
                                    {"speaker": "B", "line_target": "ok"}]}],
            "quiz": {"vocab": [{"question": "q", "options": ["a", "b"],
                                "answer_index": 0, "explanation": "e"}]},
        })
    return {"language": "zz_loop", "level": "N5", "days": days}


def main() -> int:
    rounds = 5
    if "--rounds" in sys.argv:
        rounds = int(sys.argv[sys.argv.index("--rounds") + 1])

    import customtkinter as ctk
    import VocabApp as V
    V.speak_word = lambda *a, **k: None
    if hasattr(V, "play_word_audio"):
        V.play_word_audio = lambda *a, **k: None

    root = ctk.CTk()
    root.geometry("1400x900")
    root.deiconify()
    root.update()

    app = type("AppStub", (), {})()
    app.current_language = "zz_loop"
    app.current_language_display = "Test"
    app.current_language_num_days = 0
    app.available_languages = [{"display": "Test", "slug": "zz_loop", "num_days": 0}]
    app.wait_window = lambda self, w: None
    app.clipboard_clear = lambda: None
    app.clipboard_append = lambda s: None

    # Ưu tiên course THẬT (data/ai_courses/tiếng_nhật/course.json) để tái hiện
    # đúng tình huống của app; không có thì dùng course mẫu.
    real = os.path.join(BASE, "data", "ai_courses", "tiếng_nhật", "course.json")
    course = None
    if os.path.isfile(real):
        try:
            import json as _json
            with open(real, encoding="utf-8") as f:
                course = _json.load(f)
            if not (course.get("days") or []):
                course = None
        except Exception:
            course = None
    if course is None:
        course = _make_course()
    print(f"→ dùng course với {len(course.get('days') or [])} ngày "
          f"({'THẬT' if os.path.isfile(real) else 'MẪU'})")
    # _reload_course() đọc course THẬT từ đĩa ⇒ trong test phải trả course mẫu
    # (nếu không, app mất dữ liệu và mọi case đều fail vì lý do sai).
    V.course_db.get_course = lambda *a, **k: course
    V.course_db.get_progress = lambda *a, **k: {"completed_days": [], "last_day": 1}
    tab = V.StudyTab(root, app)
    tab.pack(fill="both", expand=True)
    root.update()

    # Dùng course mẫu (tránh _reload_course nạp course thật từ đĩa)
    def _reload():
        tab._course = course
        items = []
        for d in course["days"]:
            items.append((d["day"], f"Ngày {d['day']}", "N5", False))
        tab.cb_day.set_items(items)
    _reload()
    try:
        tab.cb_source.set("🤖 Khóa học AI chuyên sâu")
    except Exception:
        pass
    tab._select_day_by_num(1)
    root.update()

    rnd = random.Random(20261113)
    for r in range(rounds):
        # ── A. chọn ngày ──────────────────────────────────────────────────
        for _ in range(6):
            n = rnd.randint(1, len(course["days"]))
            tab._select_day_by_num(n)
            root.update()
            title = tab.lbl_day_title.cget("text")
            body = tab.lesson_text.get("1.0", "end")
            ck(f"[v{r}] chọn ngày {n} ⇒ tiêu đề đúng",
               f"Ngày {n}" in title, title[:80])
            ck(f"[v{r}] chọn ngày {n} ⇒ nội dung đúng ngày",
               f"T{n}" in body or f"w{n}" in body or f"NGÀY {n}" in body,
               body[:80].replace("\n", " "))
            ck(f"[v{r}] ô nhập ngày đồng bộ ({n})",
               str(n) in tab.ent_jump_day.get(), tab.ent_jump_day.get())

        # ── B. nút chế độ học ─────────────────────────────────────────────
        n = rnd.randint(1, len(course["days"]))
        tab._select_day_by_num(n)
        root.update()
        for mode, must_have, must_not in (
                ("full", "TỪ VỰNG", None),
                ("vocab", "TỪ VỰNG", "NGỮ PHÁP"),
                ("grammar", "NGỮ PHÁP", "TỪ VỰNG CHUYÊN SÂU"),
                ("dialogue", "HỘI THOẠI", "TỪ VỰNG CHUYÊN SÂU")):
            tab._load_mode(mode)
            root.update()
            body = tab.lesson_text.get("1.0", "end")
            ck(f"[v{r}] chế độ {mode}: có '{must_have}'",
               must_have in body, body[:110].replace("\n", " "))
            if must_not:
                ck(f"[v{r}] chế độ {mode}: KHÔNG có '{must_not}'",
                   must_not not in body, body[:110].replace("\n", " "))
            ck(f"[v{r}] chế độ {mode}: đúng ngày đang chọn ({n})",
               f"NGÀY {n}" in body, body[:110].replace("\n", " "))

        # ── C. auto-sync (gọi lại _load_selected_day) không nhảy ngày ─────
        before = tab._selected_day_num()
        tab._load_selected_day()
        root.update()
        after = tab._selected_day_num()
        ck(f"[v{r}] auto-sync KHÔNG nhảy ngày ({before} → {after})",
           before == after, f"{before} → {after}")
        tab._reload_course()
        root.update()
        after2 = tab._selected_day_num()
        ck(f"[v{r}] _reload_course KHÔNG nhảy ngày ({before} → {after2})",
           before == after2, f"{before} → {after2}")

    try:
        tab.destroy()
        root.destroy()
    except Exception:
        pass

    print(f"\nKết quả: {PASS[0]} PASS / {FAIL[0]} FAIL (tổng {PASS[0] + FAIL[0]})")
    if FAILS:
        print("\nLỗi còn lại:")
        for f in FAILS[:20]:
            print("  -", f)
    return 1 if FAIL[0] else 0


if __name__ == "__main__":
    sys.exit(main())
