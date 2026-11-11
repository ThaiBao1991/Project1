# -*- coding: utf-8 -*-
"""tools/rebuild_course_from_checkpoints.py — Dựng lại `course.json` từ checkpoint.

VÌ SAO CẦN (đo thật trên máy, 2026-11-12):
  • `data/ai_courses/tiếng_nhật/_pipeline/days/` có **1.260 ngày** đã sinh
    xong (content + quiz_ab + quiz_cd = "done") — đã tốn quota Gemini.
  • Nhưng `data/ai_courses/tiếng_nhật/course.json` **KHÔNG tồn tại** ⇒ web
    KHÔNG hiển thị được 1.260 ngày này (checkpoint có, course.json không).
  • `data/ai_courses/nhật/course.json` lại là khóa cũ: 1.414 ngày mà
    **1.410 ngày rỗng** (thiếu key "vocab") ⇒ web hiện ngày trống.
  ⇒ Tool này dựng `course.json` canonical TỪ CHECKPOINT (0 call AI, 0 quota).

CÁCH DÙNG
  python tools/rebuild_course_from_checkpoints.py --lang nhật --dry-run
  python tools/rebuild_course_from_checkpoints.py --lang nhật --apply

Mặc định `--dry-run` (chỉ báo cáo, KHÔNG ghi). `--apply` sẽ:
  1. sao lưu `course.json` hiện tại (rotate .bak1..bak5),
  2. dựng lại `days[]` từ checkpoint,
  3. ghi atomic (tmp + os.replace).

TÙY CHỌN
  --keep-empty     giữ luôn ngày không có checkpoint content (mặc định: bỏ)
  --lang <slug>    chỉ 1 ngôn ngữ (mặc định: mọi ngôn ngữ có checkpoint)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai import course_db                      # noqa: E402
from ai.paths import canonical_slug          # noqa: E402
from ai.pipeline_store import (STAGE_CONTENT, STAGE_QUIZ_AB,  # noqa: E402
                               STAGE_QUIZ_CD, load_checkpoint)


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _plan_map(language):
    """{day: {title, phase, ...}} từ plan.json (global)."""
    from ai.pipeline_store import STAGE_PLAN, load_checkpoint as _lc
    cp = _lc(language, STAGE_PLAN) or {}
    data = cp.get("data") or {}
    out = {}
    for d in (data.get("days") or []):
        try:
            out[int(d.get("day", 0))] = d
        except Exception:
            continue
    return out, data


def rebuild(language, *, keep_empty=False, apply=False, log=print):
    slug = canonical_slug(language)
    course_path = course_db.course_path(language)
    from ai.pipeline_store import pipeline_dir
    days_dir = os.path.join(pipeline_dir(language), "days")

    plan, plan_data = _plan_map(language)
    existing = _read_json(course_path) or {}
    if not existing:
        existing = course_db.new_course(language, [], 10)
    existing.setdefault("days", [])
    level = existing.get("level") or ""

    # index ngày cũ theo day (để giữ media/dialogue đã có trong course cũ)
    old_by_day = {}
    for d in existing.get("days") or []:
        try:
            old_by_day[int(d.get("day", 0))] = d
        except Exception:
            continue

    built, skipped, no_vocab, no_quiz = [], [], 0, 0
    n_vocab = n_quiz = 0
    if os.path.isdir(days_dir):
        for name in sorted(os.listdir(days_dir)):
            if not name.startswith("d"):
                continue
            try:
                dn = int(name[1:])
            except ValueError:
                continue
            cp = load_checkpoint(language, STAGE_CONTENT, dn) or {}
            data = cp.get("data") or {}
            if cp.get("status") != "done" or not (data.get("vocab") or []):
                no_vocab += 1
                skipped.append(dn)
                continue
            p = plan.get(dn) or {}
            old = old_by_day.get(dn) or {}
            lesson = {
                "day": dn,
                "title": data.get("title") or p.get("title") or old.get("title", ""),
                "phase": p.get("phase") or old.get("phase", ""),
                "level": level or old.get("level", ""),
                "topic": p.get("title") or old.get("topic", ""),
                "words": p.get("words") or old.get("words") or [],
                "format_version": 4,
                "vocab": data.get("vocab") or [],
                "sentence_patterns": data.get("sentence_patterns") or [],
                "common_sentences": data.get("common_sentences") or [],
                "grammar": data.get("grammar") or [],
                "quiz": {"vocab": [], "pattern": [], "common": [],
                         "grammar": [], "mixed": []},
                "media": dict(old.get("media") or {}),
            }
            if old.get("dialogue"):
                lesson["dialogue"] = old["dialogue"]
            if old.get("is_review_day"):
                lesson["is_review_day"] = True
            # quiz từ checkpoint (nếu có)
            for stage, keys in ((STAGE_QUIZ_AB, ("vocab", "pattern")),
                                (STAGE_QUIZ_CD, ("common", "grammar"))):
                qcp = load_checkpoint(language, stage, dn) or {}
                qd = qcp.get("data") or {}
                for k in keys:
                    for raw_key in (f"{k}_quiz", k):
                        if qd.get(raw_key):
                            lesson["quiz"][k] = qd[raw_key]
                            break
            nq = sum(len(v) for v in lesson["quiz"].values())
            n_quiz += nq
            n_vocab += len(lesson["vocab"])
            if not nq:
                no_quiz += 1
            built.append(lesson)

    # giữ ngày cũ có nội dung thật nhưng KHÔNG có checkpoint (vd đã xoá ckpt)
    if keep_empty:
        for d in existing.get("days") or []:
            try:
                dn = int(d.get("day", 0))
            except Exception:
                continue
            if dn in {x["day"] for x in built}:
                continue
            if d.get("vocab"):
                built.append(d)

    built.sort(key=lambda x: x["day"])
    report = {
        "slug": slug,
        "course_path": course_path,
        "days_built": len(built),
        "days_old": len(existing.get("days") or []),
        "days_no_checkpoint": len(skipped),
        "days_without_quiz": no_quiz,
        "vocab_total": n_vocab,
        "quiz_total": n_quiz,
        "plan_days": plan_data.get("total_days"),
        "bytes": len(json.dumps(built, ensure_ascii=False)),
    }
    log(f"  [{slug}] ngày dựng={len(built)} (cũ {report['days_old']}) · "
        f"vocab={n_vocab} · câu hỏi={n_quiz} · thiếu checkpoint={len(skipped)}")
    if apply:
        existing["days"] = built
        existing["total_days"] = len(built)
        if plan_data.get("days"):
            existing["plan"] = plan_data["days"]
            existing["total_days"] = plan_data.get("total_days", len(built))
        course_db.save_course(language, existing, backup=True)
        log(f"  ✅ Đã ghi {course_path}")
    else:
        log(f"  ℹ️  DRY-RUN — chưa ghi. Thêm --apply để ghi file.")
    return report


def _unescape(s: str) -> str:
    """Cho phép truyền slug tiếng Việt qua command line của PowerShell 5.1
    (console encoding làm hỏng tham số) — dùng dạng ``\\u1ebfng_nh\\u1ea3t``."""
    if s and "\\u" in s:
        try:
            return s.encode("ascii", "backslashreplace").decode("unicode_escape")
        except Exception:
            return s
    return s


def main() -> int:
    ap = argparse.ArgumentParser(description="Dựng lại course.json từ checkpoint")
    ap.add_argument("--lang", default="", help="ngôn ngữ (bỏ trống = mọi ngôn ngữ)")
    ap.add_argument("--apply", action="store_true", help="ghi thật (mặc định: dry-run)")
    ap.add_argument("--dry-run", action="store_true",
                    help="no-op (mặc định đã là dry-run)")
    ap.add_argument("--keep-empty", action="store_true",
                    help="giữ ngày cũ có vocab nhưng không có checkpoint")
    args = ap.parse_args()
    args.lang = _unescape(args.lang)

    t0 = time.time()
    langs = []
    if args.lang:
        langs = [args.lang]
    else:
        from ai.paths import COURSES_DIR
        for d in sorted(os.listdir(COURSES_DIR)):
            if os.path.isdir(os.path.join(COURSES_DIR, d, "_pipeline", "days")):
                langs.append(d)
    print(f"=== Dựng course.json từ checkpoint ({'GHI FILE' if args.apply else 'DRY-RUN'}) ===")
    reports = []
    for lg in langs:
        try:
            reports.append(rebuild(lg, keep_empty=args.keep_empty, apply=args.apply))
        except Exception as e:
            print(f"  ⚠ {lg}: {type(e).__name__}: {e}")
    if reports:
        print("\n=== Tổng ===")
        for r in reports:
            print(f"  {r['slug']:18} ngày={r['days_built']:5} vocab={r['vocab_total']:6} "
                  f"câu hỏi={r['quiz_total']:6} thiếu ckpt={r['days_no_checkpoint']:5} "
                  f"({r['bytes']/1048576:.1f} MB)")
    print(f"\n⏱ {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
