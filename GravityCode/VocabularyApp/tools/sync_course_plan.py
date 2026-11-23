# -*- coding: utf-8 -*-
"""tools/sync_course_plan.py — ĐỒNG BỘ `plan` của course.json theo `days` đang có.

BỐI CẢNH (17/11): `build_offline_course.py` chỉ ghi `days` mà quên `plan` ⇒
plan còn số ngày CŨ (259/345/381/450) ⇒ pipeline chỉ xử lý được plan đó ⇒
log "PAUSED 0/0 ngày" / "259/259 ngày" và **media không bù được phần còn lại**.

Tool này CHỈ sửa trường `plan` (không đụng `days`/`vocab`/media) ⇒ an toàn.

Chạy:
  python tools/sync_course_plan.py --lang tiếng_nhật          # xem trước
  python tools/sync_course_plan.py --lang tiếng_nhật --apply  # ghi thật
  python tools/sync_course_plan.py --all --apply               # mọi khóa
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai import course_db  # noqa: E402
from tools.build_offline_course import phase_for_day  # noqa: E402


def _log(m):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {m}", flush=True)


def sync(lang: str, apply: bool) -> dict:
    path = course_db.course_path(lang)
    if not os.path.isfile(path):
        return {"lang": lang, "error": "không có course.json"}
    with open(path, encoding="utf-8") as f:
        course = json.load(f)
    days = course.get("days") or []
    if not days:
        return {"lang": lang, "error": "course rỗng (days=0)"}
    plan = []
    for d in days:
        try:
            n = int(d.get("day", 0))
        except Exception:
            continue
        ph, lvl, _o = phase_for_day(n, len(days))
        plan.append({"day": n,
                     "title": d.get("title") or f"{ph} — Ngày {n}",
                     "phase": ph, "level": lvl,
                     "words": [v.get("word") for v in (d.get("vocab") or [])
                               if isinstance(v, dict)]})
    old_n = len(course.get("plan") or [])
    course["plan"] = plan
    if apply:
        course_db.save_course(lang, course, backup=True)
    return {"lang": lang, "days": len(days), "old_plan": old_n,
            "new_plan": len(plan), "applied": apply}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    CD = os.path.join(BASE, "data", "ai_courses")
    if args.lang:
        langs = [args.lang]
    elif args.all:
        langs = [s for s in sorted(os.listdir(CD))
                 if not s.startswith("_")
                 and os.path.isfile(os.path.join(CD, s, "course.json"))]
    else:
        langs = ["tiếng_nhật"]

    for lg in langs:
        r = sync(lg, args.apply)
        if r.get("error"):
            _log(f"⚠ {lg}: {r['error']}")
        else:
            print(f"  {lg}: days={r['days']} plan {r['old_plan']} → {r['new_plan']}"
                  + ("  ✓ đã ghi" if r["applied"] else "  (dry-run)"), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
