# -*- coding: utf-8 -*-
"""Smoke test GUI: mở TỪNG dialog + App chính (không cần bấm chuỗi) để bắt
crash lúc khởi tạo — đúng lớp bug "CTkButton got multiple values for width"
đã từng làm ModelSettingsDialog sập khi bấm.

Chạy:  python tools/test_gui_smoke.py

Mỗi case: tạo widget → update_idletasks → destroy. Lỗi → PASS/FAIL rõ ràng.
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

    # Chặn side-effect âm thanh/mạng khi dialog tự phát audio khi mở
    V.speak_word = lambda *a, **k: None
    if hasattr(V, "play_word_audio"):
        V.play_word_audio = lambda *a, **k: None

    results = []

    def try_make(name, fn):
        dlg = None
        try:
            dlg = fn()
            root.update_idletasks()
            results.append((name, True, ""))
        except Exception as e:
            results.append((name, False, f"{type(e).__name__}: {e}"))
            traceback.print_exc()
        finally:
            try:
                if dlg is not None:
                    dlg.destroy()
            except Exception:
                pass
            try:
                root.update_idletasks()
            except Exception:
                pass

    items = [{"word": "日本語", "reading": "にほんご", "meaning": "tiếng Nhật",
              "pronunciation": "", "image_path": "", "examples": [],
              "example_sentence": "", "part_of_speech": ""}]
    app_stub = type("AppStub", (), {"current_language": "tiếng_nhật",
                                    "wait_window": lambda self, w: None})()

    # ── 12 dialog class ──────────────────────────────────────────────────────
    # VocabFormDialog nhận parent = App thật (self.app) → cần cửa sổ có
    # current_language như call-site thật: VocabFormDialog(self.app).
    class _AppWnd(ctk.CTk):
        current_language = "tiếng_nhật"

        def wait_window(self, w):
            pass

    app_wnd = _AppWnd()
    app_wnd.withdraw()

    try_make("PreviewDialog", lambda: V.PreviewDialog(root, "Tiêu đề", "# MD **đậm**"))
    try_make("GrammarDetailDialog", lambda: V.GrammarDetailDialog(
        root, [{"kind": "pattern", "pattern": "〜たいです",
                "meaning_vi": "muốn làm gì"}], idx=0,
        lang_name="tiếng_nhật"))
    try_make("_KeyEditDialog (mới)", lambda: V._KeyEditDialog(root))
    try_make("_KeyEditDialog (sửa)", lambda: V._KeyEditDialog(
        root, {"key": "ENC:abc", "email": "a@gmail.com"}))
    try_make("ApiKeyManagerDialog", lambda: V.ApiKeyManagerDialog(root))
    try_make("MediaViewerDialog", lambda: V.MediaViewerDialog(root, items, idx=0))
    try_make("CanvasPracticeDialog", lambda: V.CanvasPracticeDialog(root, "日本語"))
    try_make("PracticeChoiceDialog", lambda: V.PracticeChoiceDialog(root, "日本語"))
    try_make("TableEditorDialog", lambda: V.TableEditorDialog(
        root, ctk.CTkTextbox(root)))
    try_make("VocabFormDialog (thêm)", lambda: V.VocabFormDialog(app_wnd))
    try_make("VocabFormDialog (sửa)", lambda: V.VocabFormDialog(
        app_wnd, {"word": "水", "meaning": "nước"}))
    try_make("ModelSettingsDialog", lambda: V.ModelSettingsDialog(root))
    try_make("CourseGenerationDialog", lambda: V.CourseGenerationDialog(
        root, app_stub, on_finished=lambda: None))
    try_make("DaySelectorDialog", lambda: V.DaySelectorDialog(
        root, {"days": [{"day": 1, "title": "Ngày 1"}]},
        {"completed_days": []}, on_select_day=lambda d: None))

    # ── App chính: build toàn bộ tab (StudyTab, SettingsSyncTab, ...) ───────
    app = None
    try:
        app = V.App()
        app.withdraw()
        app.update_idletasks()
        results.append(("App() — build toàn bộ tab", True, ""))
    except Exception as e:
        results.append(("App() — build toàn bộ tab", False,
                        f"{type(e).__name__}: {e}"))
        traceback.print_exc()
    finally:
        try:
            if app is not None:
                app.destroy()
        except Exception:
            pass

    try:
        app_wnd.destroy()
    except Exception:
        pass
    try:
        root.destroy()
    except Exception:
        pass

    print()
    fails = 0
    for name, ok, msg in results:
        print(("PASS " if ok else "FAIL ") + name + ("" if ok else "  ← " + msg))
        if not ok:
            fails += 1
    print(f"\nKẾT QUẢ: {len(results) - fails}/{len(results)} pass")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
