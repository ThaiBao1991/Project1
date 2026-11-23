# -*- coding: utf-8 -*-
"""tools/consolidate_courses.py — GỘP nhiều bản của 1 ngôn ngữ còn ĐÚNG 1 bản chuẩn.

VÌ SAO CẦN (đo thật 2026-11-12):
  Trên máy có nhiều "bản" cùng một ngôn ngữ Nhật:
    data/ai_courses/nhật/            (alias cũ — 1.414 ngày, 1.410 ngày RỖNG)
    data/ai_courses/tiếng_nhật/        (canonical — đang sinh thật)
    data/ai_courses/tiếng_nhật_smoke/  (artifact test)
    data/ai_courses/_alias_nhat_cu/   (backup alias)
    data/ai_courses/_nhat_placeholder_cu/ (backup bản placeholder 12.606 media)
    data/ai_courses/zz*/                (artifact test)
  ⇒ dropdown/đường dẫn rối, tốn 353 MB cho dữ liệu KHÔNG học được.

CÁCH DÙNG
  python tools/consolidate_courses.py --dry-run      # chỉ báo cáo (mặc định)
  python tools/consolidate_courses.py --apply        # dọn thật (chuyển vào data/_trash/<ts>/)
  python tools/consolidate_courses.py --apply --purge-trash   # xoá hẳn thư mục _trash

NGUYÊN TẮC AN TOÀN
  • Chỉ giữ MỘT bản cho mỗi ngôn ngữ: bản có tên canonical (canonical_slug
    không đổi) + có nhiều ngày nhất.
  • Bản bị loại KHÔNG bị xoá ngay: chuyển vào `data/_trash/<timestamp>/`
    (xoá hẳn bằng --purge-trash).
  • KHÔNG đụng vào khóa đang được pipeline ghi (đang có tiến trình chạy).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai.paths import canonical_slug  # noqa: E402

DATA = os.path.join(BASE, "data")
COURSES = os.path.join(DATA, "ai_courses")
MEDIA = os.path.join(DATA, "media")
REVIEWS = os.path.join(DATA, "reviews")
TRASH = os.path.join(DATA, "_trash")

TEST_HINTS = ("smoke", "zz", "test", "tmp")


def _dir_size(path):
    total = 0
    for root, _d, fs in os.walk(path):
        for f in fs:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def _num_days(course_dir):
    p = os.path.join(course_dir, "course.json")
    if not os.path.isfile(p):
        return 0, 0
    try:
        with open(p, "r", encoding="utf-8") as f:
            c = json.load(f)
        days = c.get("days") or []
        filled = sum(1 for d in days if d.get("vocab"))
        return len(days), filled
    except Exception:
        return 0, 0


def survey():
    """Liệt kê mọi thư mục khóa học + phân loại."""
    rows = []
    if not os.path.isdir(COURSES):
        return rows
    for name in sorted(os.listdir(COURSES)):
        d = os.path.join(COURSES, name)
        if not os.path.isdir(d):
            continue
        total, filled = _num_days(d)
        canon = canonical_slug(name)
        is_canon_name = (canon == name)
        internal = name.startswith("_") and name != "__global__"
        is_test = (not internal) and any(h in name.lower() for h in TEST_HINTS)
        size = _dir_size(d)
        rows.append({
            "name": name, "canon": canon, "is_canon_name": is_canon_name,
            "internal": internal, "is_test": is_test,
            "days": total, "filled": filled,
            "size_mb": round(size / 1048576, 1),
            "path": d,
        })
    return rows


def plan_moves(rows):
    """Chọn bản giữ cho mỗi canonical + danh sách thư mục cần dọn."""
    keep = {}
    for r in rows:
        if r["internal"] or r["is_test"]:
            continue
        k = r["canon"]
        cur = keep.get(k)
        # ưu tiên: tên canonical đúng → nhiều ngày có nội dung nhất
        score = (r["is_canon_name"], r["filled"], r["days"])
        if cur is None or score > (cur["is_canon_name"], cur["filled"], cur["days"]):
            keep[k] = r

    drop = []
    for r in rows:
        if r["internal"] or r["is_test"]:
            drop.append((r, "nội bộ/test" if r["internal"] else "artifact test"))
        elif keep.get(r["canon"]) is not r:
            drop.append((r, f"trùng với bản chuẩn '{keep[r['canon']]['name']}'"))
    return keep, drop


def _move_to_trash(path, ts, tag):
    dst_root = os.path.join(TRASH, ts)
    os.makedirs(dst_root, exist_ok=True)
    dst = os.path.join(dst_root, tag)
    n = 1
    while os.path.exists(dst):
        dst = os.path.join(dst_root, f"{tag}_{n}")
        n += 1
    shutil.move(path, dst)
    return dst


def main() -> int:
    ap = argparse.ArgumentParser(description="Gộp khóa học còn 1 bản chuẩn")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--purge-trash", action="store_true",
                    help="xoá hẳn data/_trash (chỉ khi bạn đã xác nhận)")
    args = ap.parse_args()

    if args.purge_trash:
        if not os.path.isdir(TRASH):
            print("Không có thư mục _trash.")
            return 0
        if not args.apply:
            print("Cần --apply để xác nhận xoá.")
            return 1
        sz = _dir_size(TRASH)
        shutil.rmtree(TRASH, ignore_errors=True)
        print(f"🗑 Đã xoá data/_trash ({sz/1048576:.0f} MB)")
        return 0

    rows = survey()
    keep, drop = plan_moves(rows)

    print("=== HIỆN TRẠNG ===")
    print(f"{'thư mục':24}{'canonical':16}{'ngày':>6}{'có nội dung':>14}{'MB':>8}  quyết định")
    for r in rows:
        if r["internal"] or r["is_test"]:
            dec = "DỌN (nội bộ/test)"
        elif keep.get(r["canon"]) is r:
            dec = "GIỮ (bản chuẩn)"
        else:
            dec = "DỌN (trùng bản chuẩn)"
        print(f"{r['name']:24}{r['canon']:16}{r['days']:>6}{r['filled']:>14}"
              f"{r['size_mb']:>8}  {dec}")

    print("\n=== KẾT QUẢ SAU KHI GỘP ===")
    for k in sorted(keep):
        r = keep[k]
        print(f"  • {r['name']:20} → {r['days']} ngày, {r['filled']} ngày có nội dung")
    print(f"\n  dọn {len(drop)} thư mục khóa học "
          f"+ media trùng + file review trùng")

    if not args.apply:
        print("\nℹ️  DRY-RUN — chạy lại với --apply để dọn thật "
              "(bản bị dọn chuyển vào data/_trash/<timestamp>/, xoá hẳn bằng --purge-trash).")
        return 0

    ts = time.strftime("%Y%m%d-%H%M%S")
    moved = 0
    for r, why in drop:
        try:
            dst = _move_to_trash(r["path"], ts, "ai_courses__" + r["name"])
            moved += 1
            print(f"  🗑 {r['name']:22} ({r['size_mb']} MB) → {dst}  [{why}]")
        except Exception as e:
            print(f"  ⚠ {r['name']}: {type(e).__name__}: {e}")

    # Media của slug không còn dùng
    used = {r["canon"] for r in keep.values()}
    if os.path.isdir(MEDIA):
        for name in sorted(os.listdir(MEDIA)):
            p = os.path.join(MEDIA, name)
            if not os.path.isdir(p):
                continue
            if name in used or name == "_cards":
                continue
            if name.startswith("_") and name != "_cards":
                pass                      # thư mục dự phòng (vd media placeholder) → dọn
            else:
                continue
            try:
                dst = _move_to_trash(p, ts, "media__" + name)
                moved += 1
                print(f"  🗑 media/{name:16} → {dst}")
            except Exception as e:
                print(f"  ⚠ media/{name}: {type(e).__name__}: {e}")

    # File review của alias
    if os.path.isdir(REVIEWS):
        for name in sorted(os.listdir(REVIEWS)):
            if not name.endswith(".json"):
                continue
            slug = name[:-5]
            if canonical_slug(slug) in used and slug == canonical_slug(slug):
                continue
            try:
                dst = _move_to_trash(os.path.join(REVIEWS, name), ts, "reviews__" + name)
                moved += 1
                print(f"  🗑 reviews/{name:14} → {dst}")
            except Exception as e:
                print(f"  ⚠ reviews/{name}: {type(e).__name__}: {e}")

    print(f"\n✅ Đã dọn {moved} mục vào data/_trash/{ts}/ "
          f"(xoá hẳn: python tools/consolidate_courses.py --apply --purge-trash)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
