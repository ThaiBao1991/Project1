# -*- coding: utf-8 -*-
"""tools/verify_courses.py — Báo cáo ĐỘ ĐẦY ĐỦ của mọi khóa học (Gói 4).

Đo trên `course.json` + manifest media thật (không đo checkpoint):
  • ngày có nội dung / rỗng
  • từ vựng, ngữ pháp, hội thoại, quiz
  • ảnh (image_ref có file thật), audio từ, audio NGHĨA, audio HỘI THOẠI
  • nội dung "placeholder" (từ dạng 単語10 / tango10 — dấu hiệu dữ liệu giả)

Cách dùng:
  python tools/verify_courses.py                 # tất cả khóa
  python tools/verify_courses.py --lang tiếng_anh
  python tools/verify_courses.py --json          # xuất JSON
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

PAT_FAKE = re.compile(r"^単語\d+$")


def _load_manifest():
    p = os.path.join(DATA, "media", "index.json")
    try:
        with open(p, "r", encoding="utf-8") as f:
            return (json.load(f) or {}).get("items") or {}
    except Exception:
        return {}


def _file_ok(items, ref):
    """ref có tồn tại trong manifest VÀ file thật còn trên đĩa."""
    if not ref:
        return False
    e = items.get(ref)
    if not e:
        return False
    rp = e.get("rel_path") or ""
    if not rp:
        return False
    return os.path.isfile(os.path.join(DATA, rp))


def verify(slug, items):
    cp = os.path.join(CD, slug, "course.json")
    if not os.path.isfile(cp):
        return None
    with open(cp, encoding="utf-8") as f:
        c = json.load(f)
    days = c.get("days") or []
    st = {"days": len(days), "empty_days": 0, "vocab": 0, "fake_words": 0,
          "grammar": 0, "dialogue": 0, "dialogue_turns": 0, "quiz": 0,
          "with_image": 0, "with_audio": 0, "with_mean_audio": 0,
          "with_dialogue_audio": 0, "dialogue_no_audio": 0}
    for d in days:
        v = d.get("vocab") or []
        if not v:
            st["empty_days"] += 1
        st["vocab"] += len(v)
        for x in v:
            if PAT_FAKE.match(str(x.get("word") or "").strip()):
                st["fake_words"] += 1
            if _file_ok(items, x.get("image_ref")):
                st["with_image"] += 1
            if _file_ok(items, x.get("audio_ref")):
                st["with_audio"] += 1
            if _file_ok(items, x.get("meaning_audio_ref")):
                st["with_mean_audio"] += 1
        st["grammar"] += len(d.get("grammar") or [])
        q = d.get("quiz") or {}
        st["quiz"] += sum(len(q.get(k) or []) for k in
                          ("vocab", "pattern", "common", "grammar", "mixed"))
        dl = d.get("dialogue") or []
        st["dialogue"] += len(dl)
        dmap = (d.get("media") or {}).get("dialogue_audio") or {}
        for i, x in enumerate(dl):
            st["dialogue_turns"] += len(x.get("turns") or [])
            if _file_ok(items, dmap.get(str(i)) or x.get("audio_ref")):
                st["with_dialogue_audio"] += 1
            else:
                st["dialogue_no_audio"] += 1
    return st


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    items = _load_manifest()
    slugs = [args.lang] if args.lang else sorted(
        d for d in os.listdir(CD)
        if not d.startswith("_") and os.path.isdir(os.path.join(CD, d)))

    rows = []
    for slug in slugs:
        try:
            st = verify(slug, items)
        except Exception as e:
            print(f"⚠ {slug}: {type(e).__name__}: {e}")
            continue
        if st:
            rows.append((slug, st))

    if args.json:
        print(json.dumps({s: st for s, st in rows}, ensure_ascii=False, indent=2))
        return 0

    hdr = (f"{'khóa học':18}{'ngày':>6}{'rỗng':>6}{'vocab':>7}{'giả':>6}"
           f"{'ngữ pháp':>9}{'hội thoại':>10}{'lượt':>6}{'quiz':>7}"
           f"{'ảnh':>7}{'au từ':>8}{'au nghĩa':>10}{'au hội thoại':>14}")
    print(hdr)
    print("-" * len(hdr))
    tot = {"days": 0, "vocab": 0, "fake_words": 0, "quiz": 0, "with_image": 0,
           "with_audio": 0, "with_mean_audio": 0, "with_dialogue_audio": 0}
    for slug, st in rows:
        print(f"{slug:18}{st['days']:>6}{st['empty_days']:>6}{st['vocab']:>7}"
              f"{st['fake_words']:>6}{st['grammar']:>9}{st['dialogue']:>10}"
              f"{st['dialogue_turns']:>6}{st['quiz']:>7}{st['with_image']:>7}"
              f"{st['with_audio']:>8}{st['with_mean_audio']:>10}"
              f"{st['with_dialogue_audio']:>14}")
        for k in tot:
            tot[k] += st[k]
    print("-" * len(hdr))
    print(f"{'TỔNG':18}{'':>6}{'':>6}{tot['vocab']:>7}{tot['fake_words']:>6}"
          f"{'':>9}{'':>10}{'':>6}{tot['quiz']:>7}{tot['with_image']:>7}"
          f"{tot['with_audio']:>8}{tot['with_mean_audio']:>10}"
          f"{tot['with_dialogue_audio']:>14}")
    print(f"\n(cột 'giả' = số từ dạng 単語N ⇒ nội dung sinh tự động, KHÔNG học được)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
