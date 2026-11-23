# -*- coding: utf-8 -*-
"""tools/watch_media.py — Theo dõi tiến độ bù media (chạy liên tục, Ctrl+C để thoát).

Cách dùng:
  python tools/watch_media.py --lang tiếng_nhật        # theo dõi 1 khóa
  python tools/watch_media.py                          # tất cả khóa
  python tools/watch_media.py --interval 20             # 20 giây/lần
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

DATA = os.path.join(BASE, "data")
CD = os.path.join(DATA, "ai_courses")


def _manifest():
    try:
        with open(os.path.join(DATA, "media", "index.json"), encoding="utf-8") as f:
            return (json.load(f) or {}).get("items") or {}
    except Exception:
        return {}


def _stats(slug, items):
    cp = os.path.join(CD, slug, "course.json")
    if not os.path.isfile(cp):
        return None
    try:
        with open(cp, encoding="utf-8") as f:
            c = json.load(f)
    except Exception:
        return None
    days = c.get("days") or []
    tot = len(days)
    n_img = n_aud = n_mean = n_dlg = 0
    for d in days:
        for v in (d.get("vocab") or []):
            if not isinstance(v, dict):
                continue
            if v.get("image_ref") in items:
                n_img += 1
            if v.get("audio_ref") in items:
                n_aud += 1
            if v.get("meaning_audio_ref") in items:
                n_mean += 1
        dm = (d.get("media") or {}).get("dialogue_audio") or {}
        for i, dl in enumerate(d.get("dialogue") or []):
            if (dm.get(str(i)) or dl.get("audio_ref")) in items:
                n_dlg += 1
    return {"days": tot, "img": n_img, "aud": n_aud, "mean": n_mean, "dlg": n_dlg}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="")
    ap.add_argument("--interval", type=int, default=30)
    args = ap.parse_args()

    slugs = [args.lang] if args.lang else sorted(
        s for s in os.listdir(CD)
        if not s.startswith("_") and os.path.isfile(os.path.join(CD, s, "course.json")))
    print("=== Theo dõi media (Ctrl+C để dừng) ===")
    try:
        while True:
            items = _manifest()
            print(f"\n[{time.strftime('%H:%M:%S')}] manifest: {len(items)} entry")
            for s in slugs:
                st = _stats(s, items)
                if not st:
                    continue
                print(f"  {s:20} ngày {st['days']:5} | ảnh {st['img']:6} | "
                      f"audio {st['aud']:6} | nghĩa {st['mean']:6} | hội thoại {st['dlg']:5}")
            time.sleep(max(5, args.interval))
    except KeyboardInterrupt:
        print("\nĐã dừng theo dõi.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
