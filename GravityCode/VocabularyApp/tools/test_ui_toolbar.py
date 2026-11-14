# -*- coding: utf-8 -*-
"""tools/test_ui_toolbar.py — Test UI Gói 7 (2026-11-14).

Kiểm tra:
  1. Thanh công cụ có ĐÚNG 6 nút, NHÓM rõ ràng (Học / Khóa học / Nguy hiểm).
  2. Mỗi nút có TOOLTIP (người dùng không biết nút nào làm gì).
  3. Nút "Xóa" viền đỏ (dễ nhận là hành động phá huỷ).
  4. Panel RỖNG bị ẨN (media_strip / dlg_panel) thay vì hiện khung trống.
  5. Nhãn trạng thái dùng từ rõ nghĩa ("Chưa học ngày này" không phải
     "Chưa hoàn thành" — gây hiểu nhầm app lỗi).
  6. Không crash khi dựng StudyTab.

Chạy:  python tools/test_ui_toolbar.py
"""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    import customtkinter as ctk

    root = ctk.CTk()
    root.withdraw()

    import VocabApp as V

    V.speak_word = lambda *a, **k: None
    if hasattr(V, "play_word_audio"):
        V.play_word_audio = lambda *a, **k: None

    results = []

    def check(name, cond, detail=""):
        results.append((name, bool(cond), detail))

    # ── Dựng StudyTab với app stub ─────────────────────────────────────────
    app_stub = type("AppStub", (), {
        "current_language": "tiếng_nhật",
        "wait_window": lambda self, w: None,
        "available_languages": [],
        "set_language": lambda self, s: None,
    })()

    tab = None
    try:
        tab = V.StudyTab(root, app_stub)
        root.update_idletasks()
        check("StudyTab dựng được", True)
    except Exception as e:
        check("StudyTab dựng được", False, f"{type(e).__name__}: {e}")
        traceback.print_exc()
        root.destroy()
        _report(results)
        return 1

    # ── 1) Thu thập nút trong thanh công cụ ─────────────────────────────────
    # Thanh công cụ là frame con trực tiếp của tab, chứa các nút.
    buttons = []
    for w in tab.winfo_children():
        for c in w.winfo_children():
            if isinstance(c, ctk.CTkButton):
                buttons.append(c)
            if isinstance(c, ctk.CTkFrame):
                for c2 in c.winfo_children():
                    if isinstance(c2, ctk.CTkButton):
                        buttons.append(c2)
                    elif isinstance(c2, ctk.CTkFrame):
                        for c3 in c2.winfo_children():
                            if isinstance(c3, ctk.CTkButton):
                                buttons.append(c3)
    texts = [str(b.cget("text")) for b in buttons]
    toolbar = [t for t in texts if any(k in t for k in
               ("Trang học", "Lộ trình", "Trộn thẻ", "Sinh AI", "Tải lại", "Xóa"))]
    check("Thanh công cụ có 6 nút hành động", len(toolbar) == 6,
          f"thực tế {len(toolbar)}: {toolbar}")

    # ── 2) Nhãn phải NGẮN (không còn "🤖 Sinh khóa học AI" 170px) ──────────
    long_labels = [t for t in toolbar if len(t) > 16]
    check("Nhãn nút ngắn gọn (≤16 ký tự)", not long_labels, f"dài: {long_labels}")

    # ── 3) Tooltip gắn cho mừi nút ────────────────────────────────────────
    # CTkButton bind vào CANVAS nội bộ (CTkBaseClass.bind → self._canvas.bind)
    # và KHÔNG trả về giá trị ⇒ phải kiểm tra trực tiếp canvas.
    no_bind = []
    for b in buttons:
        t = str(b.cget("text"))
        if t not in toolbar:
            continue
        try:
            scr = b._canvas.bind("<Enter>")
        except Exception:
            scr = None
        if not scr:
            no_bind.append(t)
    check("Mọi nút hành động có tooltip (bind Enter)", not no_bind,
          f"thiếu: {no_bind}")

    # ── 4) Nút Xóa viền đỏ ─────────────────────────────────────────────────
    del_btns = [b for b in buttons if "Xóa" in str(b.cget("text"))]
    if del_btns:
        bw = int(del_btns[0].cget("border_width") or 0)
        bc = str(del_btns[0].cget("border_color") or "")
        check("Nút Xóa có viền đỏ (cảnh báo phá huỷ)", bw >= 1 and "ef4444" in bc.lower(),
              f"width={bw} color={bc}")
    else:
        check("Nút Xóa có viền đỏ", False, "không tìm thấy nút Xóa")

    # ── 5) Panel rỗng bị ẩn ────────────────────────────────────────────────
    # CTkScrollableFrame (CTk 6.0) hiển thị qua `_parent_canvas` được GRID
    # trong frame cha ⇒ phải kiểm tra grid của canvas, không phải pack.
    try:
        ms = tab.media_strip
        canvas = getattr(ms, "_parent_canvas", None)
        if canvas is None:
            check("Panel rỗng được ẨN (media_strip)", False, "không tìm _parent_canvas")
        else:
            _lesson = {"day": 1, "title": "T", "vocab": [
                {"word": "水", "meaning_vi": "nước", "image_ref": "", "audio_ref": ""}]}
            tab._render_vocab_panel(_lesson)
            root.update_idletasks()
            shown = bool(canvas.grid_info())
            tab._render_vocab_panel(None)
            root.update_idletasks()
            hidden = not canvas.grid_info()
            check("Panel rỗng được ẨN (media_strip)", hidden and shown,
                  f"có nội dung hiện={shown}, rỗng ẩn={hidden}")
    except Exception as e:
        check("Panel rỗng được ẨN (media_strip)", False, f"{type(e).__name__}: {e}")

    # ── 6) Nhãn trạng thái rõ nghĩa ────────────────────────────────────────
    try:
        import ai.course_db as course_db
        orig = course_db.get_progress
        course_db.get_progress = lambda lang: {"completed_days": [], "quiz_scores": {}}
        V.course_db.get_progress = course_db.get_progress
        tab.lbl_day_status.configure(text="")
        tab._update_day_status(1)
        txt = str(tab.lbl_day_status.cget("text"))
        check("Nhãn trạng thái nói rõ (không 'Chưa hoàn thành')",
              "Chưa hoàn thành" not in txt and len(txt) > 0, f"text={txt!r}")
        course_db.get_progress = orig
        V.course_db.get_progress = orig
    except Exception as e:
        check("Nhãn trạng thái nói rõ", False, f"{type(e).__name__}: {e}")

    try:
        tab.destroy()
    except Exception:
        pass
    root.destroy()
    _report(results)
    return 0 if all(r[1] for r in results) else 1


def _report(results):
    print("\n" + "=" * 62)
    ok = 0
    for name, passed, detail in results:
        mark = "PASS" if passed else "FAIL"
        if passed:
            ok += 1
        print(f"[{mark}] {name}" + (f"  — {detail}" if detail else ""))
    print("=" * 62)
    print(f"→ {ok}/{len(results)} PASS")
    if ok < len(results):
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
