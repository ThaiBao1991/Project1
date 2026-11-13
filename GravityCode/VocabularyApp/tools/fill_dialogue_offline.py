# -*- coding: utf-8 -*-
"""tools/fill_dialogue_offline.py — BỔ SUNG HỘI THOẠI (và quiz) cho ngày còn thiếu.

VÌ SAO CẦN: quota Gemini cạn (197 key/20 account hết quota/ngày) ⇒ các khóa
Trung/Tây/Đức còn thiếu hội thoại (~1.290 bài). Nhưng hội thoại offline
(template từ TỪ CỦA NGÀY) làm được NGAY, **0 quota** ⇒ khóa học "đủ" trước
khi AI kịp ghi đè bằng nội dung tự nhiên hơn.

Cách dùng:
  python tools/fill_dialogue_offline.py --lang tiếng_trung
  python tools/fill_dialogue_offline.py --lang all
"""
from __future__ import annotations

import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai import course_db, offline_content  # noqa: E402
from ai.pipeline_store import (STAGE_DIALOGUE, STAGE_QUIZ_AB,  # noqa: E402
                               STAGE_QUIZ_CD, STATUS_DONE, save_checkpoint)


def fill(lang: str, dry: bool = False) -> dict:
    path = course_db.course_path(lang)
    if not os.path.isfile(path):
        return {"lang": lang, "error": "no_course"}
    with open(path, encoding="utf-8") as f:
        course = json.load(f)
    days = course.get("days") or []
    n_dlg = n_quiz = 0
    for d in days:
        day = int(d.get("day", 0) or 0)
        vocab = [v for v in (d.get("vocab") or []) if isinstance(v, dict)]
        if not vocab:
            continue
        if not (d.get("dialogue") or []):
            d["dialogue"] = offline_content.build_dialogue(
                vocab, topic=d.get("title") or f"Ngày {day}")
            n_dlg += 1
        q = d.get("quiz") or {}
        if not any(q.get(k) for k in ("vocab", "pattern", "common", "grammar", "mixed")):
            d["quiz"] = offline_content.build_quiz(vocab)
            n_quiz += 1
    if dry:
        return {"lang": lang, "days": len(days), "new_dialogue": n_dlg,
                "new_quiz": n_quiz, "written": False}
    course["updated_at"] = __import__("datetime").datetime.now().strftime(
        "%Y-%m-%dT%H:%M:%S")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(course, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)
    for d in days:
        day = int(d.get("day", 0) or 0)
        if d.get("dialogue"):
            save_checkpoint(lang, STAGE_DIALOGUE,
                            {"dialogues": d["dialogue"], "source": "offline"},
                            day=day, status=STATUS_DONE)
        if d.get("quiz"):
            save_checkpoint(lang, STAGE_QUIZ_AB,
                            {"vocab_quiz": (d.get("quiz") or {}).get("vocab", []),
                             "pattern_quiz": (d.get("quiz") or {}).get("pattern", [])},
                            day=day, status=STATUS_DONE)
            save_checkpoint(lang, STAGE_QUIZ_CD,
                            {"common_quiz": (d.get("quiz") or {}).get("common", []),
                             "grammar_quiz": (d.get("quiz") or {}).get("grammar", [])},
                            day=day, status=STATUS_DONE)
    return {"lang": lang, "days": len(days), "new_dialogue": n_dlg,
            "new_quiz": n_quiz, "written": True}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="all")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    cd = os.path.join(BASE, "data", "ai_courses")
    langs = ([args.lang] if args.lang != "all" else
             sorted(s for s in os.listdir(cd)
                    if not s.startswith("_")
                    and os.path.isfile(os.path.join(cd, s, "course.json"))))
    for lg in langs:
        r = fill(lg, dry=args.dry_run)
        print(f"  {r.get('lang'):20} ngày {r.get('days', 0):5} | "
              f"+hội thoại {r.get('new_dialogue', 0):5} | +quiz {r.get('new_quiz', 0):5}"
              + ("" if r.get("written") else "  (DRY-RUN)"), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
