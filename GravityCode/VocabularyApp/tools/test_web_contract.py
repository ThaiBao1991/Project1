# -*- coding: utf-8 -*-
"""tools/test_web_contract.py — Test contract cho UI học trên điện thoại.

Kiểm tra nhanh các thành phần then chốt của bản web mới:
  • Ô nhập ngày nhanh + nút ←/→ (không còn <select> 2.520 dòng).
  • Lazy-load từ vựng theo view (`ensureVocabLoaded`).
  • Nhớ ngày/ngôn ngữ/view (`saveLastDay`, `vocabapp_last_state_v1`).
  • Prefetch ngày kế bên (`prefetchDay`).
  • Bảng chữ cái Nhật (`.alphabet-grid`).
  • Service worker đã tăng version.

CÁCH DÙNG:
  python -X utf8 tools/test_web_contract.py
"""
from __future__ import annotations

import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(BASE, "web")
FAILS = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS " if ok else "FAIL ") + name + ((" — " + detail) if detail else ""))
    if not ok:
        FAILS.append(name)


def read(name: str) -> str:
    with open(os.path.join(WEB, name), encoding="utf-8") as f:
        return f.read()


def main() -> int:
    html = read("index.html")
    js = read("script.js")
    css = read("style.css")
    sw = read("sw.js")

    check("HTML có ô nhập ngày nhanh", 'id="course-day-input"' in html)
    check("HTML có nút ngày trước/sau",
          'id="course-day-prev"' in html and 'id="course-day-next"' in html)
    check("HTML không còn select 2.520 dòng", 'id="course-day-select"' not in html)
    check("JS có lazy-load từ vựng", "ensureVocabLoaded" in js)
    check("JS có nhớ ngày/ngôn ngữ", "saveLastDay" in js and "vocabapp_last_state_v1" in js)
    check("JS có prefetch ngày kế bên", "prefetchDay" in js)
    check("JS có chống race đổi ngôn ngữ",
          "courseLoadToken" in js and "courseRenderToken" in js)
    check("JS có render phần lõi trước",
          "course-rest-loading" in js and "requestIdleCallback(renderRest" in js)
    check("CSS có lưới bảng chữ cái", ".alphabet-grid" in css and ".kana-cell" in css)
    check("CSS có day-picker", ".day-picker" in css and "#course-day-input" in css)
    m = re.search(r'const VERSION\s*=\s*"(vocab-v\d+)"', sw)
    check("Service worker có version mới", bool(m), m.group(1) if m else "?")

    print("\n" + ("✅ TẤT CẢ PASS" if not FAILS else f"❌ {len(FAILS)} FAIL: {FAILS}"))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
