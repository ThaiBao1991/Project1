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

    def ck(name, cond):
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

    print()
    print(f"KẾT QUẢ: {16 + 1 + 7 - len(fails)}/{16 + 1 + 7} pass")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
