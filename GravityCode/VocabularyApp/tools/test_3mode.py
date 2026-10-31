# -*- coding: utf-8 -*-
"""Test 3 nút chế độ KHÔNG CẦN GUI: _render_lesson_text lọc section theo _study_mode.

Chạy:  python tools/test_3mode.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

COURSE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "data", "ai_courses", "tiếng_nhật", "course.json")


class _Stub:
    """Mô phỏng StudyTab — chỉ có phần render text (không tạo widget Tk)."""
    _study_mode = "full"
    _course = None

    def _media_index(self):
        return {}

    def _media_file(self, media_index, ref):
        return ""

    def _set_lesson_text(self, content):
        self.out = content


def render(lesson, mode):
    from VocabApp import StudyTab
    s = _Stub()
    s._study_mode = mode
    StudyTab._render_lesson_text(s, lesson)
    return s.out


def main():
    if not os.path.isfile(COURSE):
        print(f"[SKIP] Không thấy {COURSE}")
        return 0
    c = json.load(open(COURSE, encoding="utf-8"))
    lesson = next(d for d in c["days"] if int(d.get("day")) == 1)
    fails = []
    total = [0]

    def ck(name, cond):
        total[0] += 1
        print(("PASS " if cond else "FAIL ") + name)
        if not cond:
            fails.append(name)

    full = render(lesson, "full")
    ck("full có TỪ VỰNG", "TỪ VỰNG CHUYÊN SÂU" in full)
    ck("full có MẪU CÂU", "CÁCH DÙNG CÂU" in full)
    ck("full có NGỮ PHÁP", "📐 NGỮ PHÁP" in full)
    ck("full có HỘI THOẠI", "HỘI THOẠI (ROLEPLAY)" in full)
    ck("full không có banner lọc", "nội dung đã lọc" not in full)

    voc = render(lesson, "vocab")
    ck("vocab có TỪ VỰNG", "TỪ VỰNG CHUYÊN SÂU" in voc)
    ck("vocab KHÔNG có ngữ pháp", "📐 NGỮ PHÁP" not in voc)
    ck("vocab KHÔNG có hội thoại", "HỘI THOẠI (ROLEPLAY)" not in voc)
    ck("vocab có banner", "CHẾ ĐỘ TỪ VỰNG" in voc)

    gra = render(lesson, "grammar")
    ck("grammar có MẪU CÂU", "CÁCH DÙNG CÂU" in gra)
    ck("grammar có NGỮ PHÁP", "📐 NGỮ PHÁP" in gra)
    ck("grammar KHÔNG có từ vựng", "TỪ VỰNG CHUYÊN SÂU" not in gra)
    ck("grammar KHÔNG có hội thoại", "HỘI THOẠI (ROLEPLAY)" not in gra)

    dlg = render(lesson, "dialogue")
    ck("dialogue có HỘI THOẠI", "HỘI THOẠI (ROLEPLAY)" in dlg)
    ck("dialogue KHÔNG có từ vựng", "TỪ VỰNG CHUYÊN SÂU" not in dlg)
    ck("dialogue KHÔNG có ngữ pháp", "📐 NGỮ PHÁP" not in dlg)

    # Panel hội thoại: số lượt = tổng turns của các dialogue
    turns = []
    for d in (lesson.get("dialogue") or []):
        for t in (d.get("turns") or []):
            if str(t.get("line_target") or "").strip():
                turns.append(t)
    ck(f"panel hội thoại có {len(turns)} lượt (>0)", len(turns) > 0)

    # Method GUI tồn tại
    from VocabApp import StudyTab
    for m in ("_load_mode", "_sync_dlg_panel", "_dlg_play_turn",
              "_dlg_play_all", "_dlg_move", "_dlg_stop", "_dlg_step"):
        ck(f"StudyTab.{m} tồn tại", hasattr(StudyTab, m))

    # ── Panel chọn được (📚10 dòng · 📖 ngữ pháp click → chi tiết) ──────────
    for m in ("_render_vocab_panel", "_render_vocab_rows", "_render_grammar_rows",
              "_open_grammar_dialog", "_media_ring"):
        ck(f"StudyTab.{m} tồn tại", hasattr(StudyTab, m))

    from VocabApp import GrammarDetailDialog
    for m in ("_render", "_move", "_speak_first"):
        ck(f"GrammarDetailDialog.{m} tồn tại", hasattr(GrammarDetailDialog, m))

    # Panel ẩn khi ở chế độ hội thoại (dlg_panel đảm nhiệm)
    class _FakeStrip:
        def __init__(self):
            self.forgot = False

        def winfo_children(self):
            return []

        def pack_forget(self):
            self.forgot = True

    s = _Stub()
    s._study_mode = "dialogue"
    s.media_strip = _FakeStrip()
    s._img_refs = {}
    s._media_cards = {}
    s._update_media_cover = lambda les: None
    StudyTab._render_vocab_panel(s, {"day": 1})
    ck("vocab panel ẩn khi chế độ hội thoại", s.media_strip.forgot)

    # GrammarDetailDialog._render: pattern + grammar đầy đủ (không cần GUI)
    class _FakeBox:
        def configure(self, **kw):
            pass

        def delete(self, *a):
            pass

        def insert(self, pos, text):
            self.text = text

    class _FakeLbl:
        def configure(self, **kw):
            pass

    d = object.__new__(GrammarDetailDialog)
    d._lang = "tiếng_nhật"
    d.body = _FakeBox()
    d.lbl_pos = _FakeLbl()
    d._items = [{
        "kind": "pattern", "pattern": "〜たいです", "meaning_vi": "muốn làm gì",
        "structure_note": "động từ stem + たい",
        "example_sentence": "水が飲みたいです", "example_meaning_vi": "tôi muốn uống nước",
    }, {
        "kind": "grammar", "title": "Bài 1: て形",
        "explanation": "Dùng để nối câu, hỏi xin phép.",
        "examples": [{"sentence": "食べてください", "meaning_vi": "xin hãy ăn"}],
        "common_mistakes": [{"wrong": "食べてだ", "right": "食べて",
                             "why_vi": "không dùng だ sau て"}],
        "mini_quiz": [{"question": "Chọn đúng:", "options": ["飲んで", "飲って"],
                       "explanation": "う→んで"}],
    }]
    d._idx = 0
    d._render()
    ck("dialog pattern: hiện cấu trúc + nghĩa VI",
       "〜たいです" in d.body.text and "muốn làm gì" in d.body.text)
    ck("dialog pattern: hiện ví dụ JP + VI",
       "水が飲みたいです" in d.body.text and "tôi muốn uống nước" in d.body.text)
    d._idx = 1
    d._render()
    ck("dialog grammar: title + giải thích",
       "Bài 1" in d.body.text and "て形" in d.body.text)
    ck("dialog grammar: ví dụ + lỗi sai + mini-quiz",
       "食べてください" in d.body.text and "❌" in d.body.text and "🧠" in d.body.text)
    d._move(+1)
    ck("_move wrap-around 2 mục → về pattern", d._idx == 0)

    # ── Mục C: log đổi key/account AI (dễ nhìn theo dõi xoay vòng) ──────────
    try:
        from types import SimpleNamespace
        from api.gemini_safe import GeminiCoordinator
        logs = []
        coord = GeminiCoordinator(models=["gemini-test"], log_fn=logs.append,
                                  key_loader=lambda: [])
        fake_pool = SimpleNamespace(_keys=[{"email": "a@gmail.com", "key": "k1"},
                                           {"email": "b@gmail.com", "key": "k2"}])
        coord._log_key_pick(fake_pool, fake_pool._keys[0], "a@gmail.com")
        ck("log key lần đầu: '🔑 Đang dùng' + [key 1/2]",
           len(logs) == 1 and "Đang dùng key của account: a@gmail.com" in logs[0]
           and "[key 1/2]" in logs[0])
        coord._log_key_pick(fake_pool, fake_pool._keys[0], "a@gmail.com")
        ck("log cùng account → KHÔNG log thêm (không spam)", len(logs) == 1)
        coord._log_key_pick(fake_pool, fake_pool._keys[1], "b@gmail.com")
        ck("log đổi account: '🔄 Đổi sang' + [key 2/2]",
           len(logs) == 2 and "Đổi sang account: b@gmail.com" in logs[1]
           and "[key 2/2]" in logs[1])
    except Exception as e:
        ck(f"test log key (lỗi: {e})", False)

    print()
    print(f"KẾT QUẢ: {total[0] - len(fails)}/{total[0]} pass")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
