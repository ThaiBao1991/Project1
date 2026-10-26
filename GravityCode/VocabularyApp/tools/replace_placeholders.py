"""
replace_placeholders.py — Thay ảnh PLACEHOLDER bằng ảnh thật (Wikipedia/Commons).

Bối cảnh: các run đầu gọi Wikipedia với 36 request đồng thời ⇒ bị Wikimedia
rate-limit ⇒ toàn bộ ảnh thành placeholder. Sau khi thêm throttle
(`ai/dictionary_image.py::_throttle`, semaphore 4 + 0.2 s) thì 10/10 ảnh thật.

Cách chạy:
  python tools/replace_placeholders.py --lang tiếng_anh --dry-run
  python tools/replace_placeholders.py --all
"""
import argparse
import json
import os
import sys
import threading
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
os.chdir(BASE)

from ai import course_db, media_store, pipeline_store as pst
from ai.pipeline_media import run_images_stage
from ai.providers import ProviderChain

PLACEHOLDER_MAX = 2000      # file < 2KB = placeholder

ap = argparse.ArgumentParser()
ap.add_argument("--lang", help="slug hoặc tên ngôn ngữ")
ap.add_argument("--all", action="store_true", help="mọi ngôn ngữ")
ap.add_argument("--dry-run", action="store_true")
ap.add_argument("--workers", type=int, default=6)
ap.add_argument("--limit", type=int, default=0, help="giới hạn số ngày/lượt")
args = ap.parse_args()

idx = media_store.load_index()
items = idx.get("items", {})

# ảnh placeholder theo (lang_slug, day)
ph_days = {}
for e in items.values():
    if e.get("type") != "image":
        continue
    if e.get("source") != "placeholder":
        continue
    rel = e.get("rel_path") or ""
    parts = rel.split("/")
    if len(parts) < 3:
        continue
    slug, daydir = parts[1], parts[2]
    try:
        day = int(daydir[1:])
    except ValueError:
        continue
    ph_days.setdefault(slug, set()).add(day)

langs = []
if args.all:
    langs = sorted(ph_days.keys())
elif args.lang:
    langs = [args.lang]
else:
    ap.print_help()
    sys.exit(1)

chain = ProviderChain.default(log_fn=None)
total_fixed = 0

for slug in langs:
    path = os.path.join(course_db.COURSES_DIR, slug, "course.json")
    if not os.path.isfile(path):
        continue
    course = course_db.get_course(slug, apply_v4=False, persist=False)
    if not course:
        continue
    lang = course.get("language") or slug
    days = {int(d.get("day", 0)): d for d in course.get("days", [])}
    todo = sorted(ph_days.get(slug, set()))
    if args.limit:
        todo = todo[:args.limit]
    if not todo:
        print(f"  {slug:20s} không có ảnh placeholder")
        continue
    print(f"\n=== {slug} ({lang}) — {len(todo)} ngày có placeholder ===")
    fixed = 0
    t0 = time.time()
    for dnum in todo:
        lesson = days.get(dnum)
        if not lesson:
            continue
        # xoá ref cũ (placeholder) để stage chạy lại
        for v in lesson.get("vocab") or []:
            if isinstance(v, dict):
                v["image_ref"] = None
        # bỏ checkpoint images để chạy lại
        try:
            p = pst.day_stage_path(slug, dnum, pst.STAGE_IMAGES)
            if os.path.isfile(p):
                os.remove(p)
        except Exception:
            pass
        if args.dry_run:
            fixed += 1
            continue
        # Đánh dấu stage images = PENDING và xoá ref cũ ⇒ PIPELINE (6 luồng
        # song song) sẽ sinh lại ảnh thật nhanh hơn nhiều so với tuần tự.
        for v in lesson.get("vocab") or []:
            if isinstance(v, dict):
                v["image_ref"] = None
        try:
            pst.save_checkpoint(slug, pst.STAGE_IMAGES,
                                {"pending_reason": "replace placeholder"},
                                day=dnum, status=pst.STATUS_PENDING)
        except Exception:
            pass
        fixed += 1
        total_fixed += 1
        if fixed % 50 == 0:
            course_db.save_course(slug, course)
            print(f"    ... đã đánh dấu {fixed} ngày ({time.time()-t0:.0f}s)")
    if not args.dry_run:
        course_db.save_course(slug, course)
    print(f"  → {fixed} ảnh thật trong {time.time()-t0:.0f}s")

print(f"\nTỔNG: {total_fixed} ảnh thật đã tạo")
if args.dry_run:
    print("DRY-RUN: không ghi gì.")
