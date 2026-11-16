# -*- coding: utf-8 -*-
"""tools/verify_integrity.py — KIỂM TRA TOÀN VẸN 8+ khóa học (chạy định kỳ).

Bắt được những lỗi đã xảy ra thật (17/11):
  • `course.json` 0 byte / JSON hỏng        ⇒ MẤT TRẮNG khóa học
  • `plan` lệch với `days`                  ⇒ pipeline "PAUSED 0/0 ngày"
  • `days` rỗng trong khi khóa đã có dữ liệu
  • media ref trỏ tới file KHÔNG tồn tại    ⇒ app không hiện ảnh/âm thanh
  • ngày thiếu vocab / nghĩa Việt

Chạy:
  python tools/verify_integrity.py            # báo cáo (exit 1 nếu có lỗi)
  python tools/verify_integrity.py --quiet    # chỉ in dòng lỗi
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

CD = os.path.join(BASE, "data", "ai_courses")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    problems = []
    rows = []
    for slug in sorted(os.listdir(CD)):
        if slug.startswith("_"):
            continue
        p = os.path.join(CD, slug, "course.json")
        if not os.path.isfile(p):
            continue
        size = os.path.getsize(p)
        try:
            with open(p, encoding="utf-8") as f:
                c = json.load(f)
        except Exception as e:
            problems.append(f"{slug}: course.json KHÔNG ĐỌC ĐƯỢC "
                            f"({type(e).__name__}: {e}) — file {size} byte")
            continue
        if size < 100:
            problems.append(f"{slug}: course.json chỉ {size} byte (rỗng/hỏng)")
        days = c.get("days") or []
        plan = c.get("plan") or []
        if not days:
            problems.append(f"{slug}: KHÔNG CÓ NGÀY NÀO (days=0)")
            continue
        if len(plan) != len(days):
            problems.append(f"{slug}: plan {len(plan)} ≠ days {len(days)}")
        n_words = n_vi = n_img = n_aud = 0
        empty_days = 0
        for d in days:
            v = d.get("vocab") or []
            if not v:
                empty_days += 1
            for x in v:
                if not isinstance(x, dict):
                    continue
                n_words += 1
                if x.get("meaning_vi"):
                    n_vi += 1
                if x.get("image_ref"):
                    n_img += 1
                if x.get("audio_ref"):
                    n_aud += 1
        if empty_days:
            problems.append(f"{slug}: {empty_days}/{len(days)} ngày KHÔNG có từ vựng")
        if n_words and n_vi / n_words < 0.95:
            problems.append(f"{slug}: chỉ {n_vi}/{n_words} từ có nghĩa Việt")
        rows.append((slug, len(days), len(plan), n_words, n_vi, n_img, n_aud))

    if not args.quiet:
        print(f"KIỂM TRA TOÀN VẸN {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'khóa học':18}{'ngày':>6}{'plan':>6}{'từ':>8}{'nghĩa VI':>10}"
              f"{'có ảnh':>9}{'có audio':>10}")
        for r in rows:
            print(f"{r[0]:18}{r[1]:>6}{r[2]:>6}{r[3]:>8}{r[4]:>10}{r[5]:>9}{r[6]:>10}")
        print(f"\n→ {len(rows)} khóa học · {len(problems)} vấn đề")
    for p in problems:
        print("  ⚠ " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
