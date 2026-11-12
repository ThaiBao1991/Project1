# -*- coding: utf-8 -*-
"""tools/audit_curriculum.py — Audit CHẤT LƯỢNG nội dung + GIÁO TRÌNH mọi khóa.

Trả lời 4 câu hỏi (có số liệu thật):
  1. Nội dung có ĐỦ thông tin để học không? (từ vựng · ngữ pháp · hội thoại ·
     quiz · phát âm · ví dụ)
  2. 200-450 ngày có đủ nội dung MỚI không? (đo tỉ lệ từ TRÙNG LẶP)
  3. Logic sinh AI có đúng giáo trình không? (backbone 6 chặng · plan · mục tiêu)
  4. Người MỚI (từ 0) học được không? (chặng đầu có đúng bảng chữ cái/ngữ âm
     cơ bản, từ tăng dần, ví dụ nối câu không?)

Cách dùng: python tools/audit_curriculum.py [--lang tiếng_anh] [--json]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DATA = os.path.join(BASE, "data")
CD = os.path.join(DATA, "ai_courses")

KANA = re.compile(r"^[぀-ヿ]+$")
PLACEHOLDER = re.compile(r"^単語\d+$")


def _load(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def audit(slug):
    d = os.path.join(CD, slug)
    course = _load(os.path.join(d, "course.json"))
    if not course:
        return None
    days = course.get("days") or []

    # ── 1/2. từ vựng: độ đầy đủ + trùng lặp ────────────────────────────
    seen = set()
    dup = 0
    tot = 0
    fields = {"pronunciation": 0, "ipa": 0, "part_of_speech": 0, "meaning_vi": 0,
              "example_sentence": 0, "example_meaning_vi": 0,
              "phonetic_note": 0, "syllables": 0}
    per_day_dup = []
    for day in days:
        v = day.get("vocab") or []
        dset = set()
        for x in v:
            if not isinstance(x, dict):
                continue
            tot += 1
            w = str(x.get("word") or "").strip()
            if w:
                if w in seen:
                    dup += 1
                seen.add(w)
                dset.add(w)
            for k in fields:
                if x.get(k):
                    fields[k] += 1
        if len(v) != len(dset):
            per_day_dup.append(int(day.get("day", 0)))

    # ── 3. ngữ pháp / hội thoại / quiz ──────────────────────────────────
    g_items = g_ex = g_mini = 0
    dlg = dlg_turns = dlg_focus = 0
    q_items = q_bad = 0
    for day in days:
        for g in (day.get("grammar") or []):
            g_items += 1
            if g.get("examples"):
                g_ex += 1
            if g.get("mini_quiz"):
                g_mini += 1
        for t in (day.get("dialogue") or []):
            dlg += 1
            dlg_turns += len(t.get("turns") or [])
            dlg_focus += sum(1 for x in (t.get("turns") or []) if x.get("focus_words"))
        q = day.get("quiz") or {}
        for k in ("vocab", "pattern", "common", "grammar", "mixed"):
            for item in (q.get(k) or []):
                q_items += 1
                opts = item.get("options") or []
                ai = item.get("answer_index")
                if len(opts) < 2 or not isinstance(ai, int) or not (0 <= ai < len(opts)):
                    q_bad += 1

    # ── 4. giáo trình (backbone + plan) ─────────────────────────────────
    bb = _load(os.path.join(d, "_pipeline", "backbone.json")) or {}
    pl = _load(os.path.join(d, "_pipeline", "plan.json")) or {}
    bb_data = bb.get("data") or {}
    pl_data = pl.get("data") or {}
    # Backbone dùng key "items" (1 mục = 1 ngày, tiền tố là TÊN CHẶNG).
    items = bb_data.get("items") or bb_data.get("stages") or []
    stages = []
    for it in items:
        if isinstance(it, dict):
            title = (it.get("title") or it.get("name") or "").strip()
            tdays = it.get("target_days") or it.get("days") or 1
        else:
            title, tdays = str(it), 1
        ph = title.split("—")[0].strip() if "—" in title else title.strip()
        if stages and stages[-1]["phase"] == ph:
            stages[-1]["days"] += int(tdays or 1)
        else:
            stages.append({"phase": ph, "days": int(tdays or 1)})
    plan_days = pl_data.get("days") or []

    # ── 5. học từ 0: 10 ngày đầu có phải bảng chữ cái/ngữ âm không ──
    first_kana = 0
    first_total = 0
    for day in days[:10]:
        for x in (day.get("vocab") or []):
            w = str(x.get("word") or "").strip()
            if not w:
                continue
            first_total += 1
            if KANA.match(w):
                first_kana += 1

    return {
        "days": len(days),
        "vocab_total": tot,
        "vocab_unique": len(seen),
        "vocab_dup": dup,
        "dup_pct": round(dup * 100.0 / tot, 1) if tot else 0,
        "days_with_internal_dup": len(per_day_dup),
        "fields": fields,
        "grammar_items": g_items,
        "grammar_with_examples": g_ex,
        "grammar_with_mini_quiz": g_mini,
        "dialogues": dlg,
        "dialogue_turns": dlg_turns,
        "dialogue_turns_with_focus": dlg_focus,
        "quiz_items": q_items,
        "quiz_invalid": q_bad,
        "fake_words": sum(1 for _s in seen if PLACEHOLDER.match(_s)),
        "stages": len(stages),
        "stage_titles": [s["phase"] for s in stages],
        "stage_days": [s["days"] for s in stages],
        "plan_days": len(plan_days),
        "plan_total": pl_data.get("total_days"),
        "first10_kana_pct": round(first_kana * 100.0 / first_total, 1) if first_total else 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    slugs = [args.lang] if args.lang else sorted(
        s for s in os.listdir(CD)
        if not s.startswith("_") and os.path.isdir(os.path.join(CD, s))
        and os.path.isfile(os.path.join(CD, s, "course.json")))

    rows = {}
    for s in slugs:
        try:
            a = audit(s)
        except Exception as e:
            print(f"⚠ {s}: {type(e).__name__}: {e}")
            continue
        if a:
            rows[s] = a

    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return 0

    for s, a in rows.items():
        print(f"\n{'=' * 74}\n■ {s}  ·  {a['days']} ngày  ·  giáo trình: "
              f"{a['stages']} chặng  ·  plan {a['plan_days']}/{a['plan_total']} ngày")
        print(f"  TỪ VỰNG: {a['vocab_total']} (unique {a['vocab_unique']}) · "
              f"trùng lặp {a['vocab_dup']} ({a['dup_pct']}%) · "
              f"ngày có từ trùng trong ngày: {a['days_with_internal_dup']} · "
              f"placeholder {a['fake_words']}")
        f = a["fields"]
        n = max(1, a["vocab_total"])
        print("  THÔNG TIN/TỪ: " + " · ".join(
            f"{k} {v} ({round(v * 100.0 / n)}%)" for k, v in f.items()))
        print(f"  NGỮ PHÁP: {a['grammar_items']} mục (có ví dụ {a['grammar_with_examples']}, "
              f"có mini_quiz {a['grammar_with_mini_quiz']})")
        print(f"  HỘI THOẠI: {a['dialogues']} bài · {a['dialogue_turns']} lượt "
              f"(có từ trọng tâm {a['dialogue_turns_with_focus']})")
        print(f"  TRẮC NGHIỆM: {a['quiz_items']} câu (câu lỗi {a['quiz_invalid']})")
        print(f"  HỌC TỪ 0: 10 ngày đầu có {a['first10_kana_pct']}% kana thuần")
        if a["stage_titles"]:
            print("  GIÁO TRÌNH:")
            for t, d in zip(a["stage_titles"], a["stage_days"]):
                print(f"     • {t[:58]:60} {d} ngày")
    return 0


if __name__ == "__main__":
    sys.exit(main())
