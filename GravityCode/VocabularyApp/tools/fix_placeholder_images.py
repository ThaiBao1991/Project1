# -*- coding: utf-8 -*-
"""Bù ảnh THẬT cho từ đang là placeholder — MIỄN PHÍ (Wikipedia/Commons/Openverse).

Vì sao cần: khóa sinh trước khi có fix ảnh lưu `source=placeholder` (chữ cái đầu
trên nền) ⇒ 194/255 từ "không có ảnh". Tool này gọi lại stage T3 (`_stage_dict`
của image_pipeline) cho từng ngày:

  • từ đang là placeholder / thiếu ảnh → tìm ảnh thật (0 API key, 0 tốn quota)
  • ảnh THẬT đã có → GIỮ NGUYÊN (không bao giờ ghi đè)
  • ghi lại course.json atomic (tmp + os.replace) + backup .bak1

Chạy:
    python tools/fix_placeholder_images.py                  # ngôn ngữ mặc định
    python tools/fix_placeholder_images.py "tiếng_nhật" --days 1-24
    python tools/fix_placeholder_images.py --dry-run        # chỉ đếm, không tải
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DEFAULT_LANG = "tiếng_nhật"


def _count(lesson, index):
    """Đếm (real, placeholder, noref) cho vocab của 1 ngày."""
    real = ph = noref = 0
    for v in (lesson.get("vocab") or []):
        ref = v.get("image_ref") or ""
        e = index.get(ref) if ref else None
        if not e:
            noref += 1
        elif e.get("source") == "placeholder":
            ph += 1
        else:
            real += 1
    return real, ph, noref


def _load_index_items():
    from ai import media_store
    idx = media_store.load_index() or {}
    return idx.get("items") or {}


def _parse_days(spec, all_days):
    if not spec:
        return list(all_days)
    lo, _, hi = spec.partition("-")
    lo, hi = int(lo), int(hi or lo)
    return [d for d in all_days if lo <= d <= hi]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("language", nargs="?", default=DEFAULT_LANG)
    ap.add_argument("--days", default="", help="VD: 1-24 (mặc định: mọi ngày)")
    ap.add_argument("--dry-run", action="store_true", help="Chỉ đếm, không tải ảnh")
    ap.add_argument("--refresh-cache", action="store_true",
                    help="Xóa cache ÂM ('không có ảnh' — thường do Wikimedia 429 "
                         "hồi sinh khóa) để ép tìm lại LIVE. An toàn: chỉ xóa "
                         "entry âm, cache ảnh THẬT giữ nguyên.")
    args = ap.parse_args()

    from ai import image_pipeline  # import sau khi sys.path đã thêm app root

    course_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "ai_courses", args.language, "course.json")
    if not os.path.isfile(course_path):
        print(f"❌ Không thấy {course_path}")
        return 1

    # Đọc RAW (không qua course_db để không kích hoạt migration setdefault)
    with open(course_path, "r", encoding="utf-8") as f:
        course = json.load(f)
    days = course.get("days") or []
    targets = _parse_days(args.days, [int(d.get("day") or 0) for d in days])
    day_map = {int(d.get("day") or 0): d for d in days}

    index = _load_index_items()
    before = [0, 0, 0]
    for dn in targets:
        c = _count(day_map[dn], index)
        before = [a + b for a, b in zip(before, c)]
    print(f"🔎 TRƯỚC — {args.language}: {before[0]} ảnh thật · "
          f"{before[1]} placeholder · {before[2]} không ref (trong {len(targets)} ngày)")

    if args.refresh_cache:
        # Cache âm = dictionary_image từng kết luận "từ này KHÔNG có ảnh"
        # (thường do Wikimedia 429 lúc sinh khóa) → chặn tìm lại đến 7 ngày.
        # Xóa các entry âm của đúng các từ trong DAYS ĐANG XỬ LÝ rồi tìm LIVE.
        from ai import dictionary_image as di
        cache = di._load_cache()
        n_purged = 0
        for dn in sorted(targets):
            for v in (day_map[dn].get("vocab") or []):
                k = di._cache_key(args.language, str(v.get("word") or ""))
                e = cache.get(k)
                if isinstance(e, dict) and "__none__" in e:
                    del cache[k]
                    n_purged += 1
        di._cache_dirty = 999      # ép _save_cache() ghi xuống đĩa
        di._save_cache()
        print(f"🧹 Đã xóa {n_purged} cache âm — các từ này sẽ được tìm lại LIVE.")

    if args.dry_run:
        print("--dry-run → dừng ở đây.")
        return 0

    made_total = 0
    for dn in sorted(targets):
        lesson = day_map[dn]
        try:
            entries = image_pipeline.generate_images_for_day(
                args.language, dn, lesson, coord=None, log_fn=print,
                providers=["dict"])       # CHỈ stage từ điển — 0 key, 0 quota
            made_total += len(entries or [])
        except Exception as e:
            print(f"  ⚠️ Ngày {dn}: lỗi bù ảnh — {type(e).__name__}: {e}")

    # Backup + ghi atomic
    bak = course_path + ".bak1"
    try:
        with open(course_path, "r", encoding="utf-8") as fsrc, \
                open(bak, "w", encoding="utf-8") as fdst:
            fdst.write(fsrc.read())
    except Exception as e:
        print(f"  ⚠️ Không backup được ({e}) — vẫn ghi tiếp.")
    tmp = course_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(course, f, ensure_ascii=False, indent=1)
    os.replace(tmp, course_path)

    index = _load_index_items()   # load lại sau khi stage đã ghi manifest
    try:
        from ai import media_store
        media_store.flush_index()  # BẮT BUỘC: stage chỉ đánh dấu "unsaved",
        # nếu không flush thì manifest chưa ghi đĩa → entry mới bị mất khi thoát.
    except Exception as e:
        print(f"  ⚠️ Không flush manifest được ({e}).")
    after = [0, 0, 0]
    for dn in targets:
        c = _count(day_map[dn], index)
        after = [a + b for a, b in zip(after, c)]
    print(f"\n✅ SAU  — {args.language}: {after[0]} ảnh thật · "
          f"{after[1]} placeholder · {after[2]} không ref")
    print(f"   → Bù được {after[0] - before[0]} ảnh thật "
          f"(media entry mới: {made_total}); course.json đã ghi atomic + backup .bak1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
