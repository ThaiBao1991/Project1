# -*- coding: utf-8 -*-
"""tools/export_days_keep_media.py — Xuất `web/data/<slug>/day/*.json` từ
course.json mà GIỮ NGUYÊN `media_map` đang có (không đóng gói lại media).

VÌ SAO CẦN (2026-11-19): sau khi bổ sung mẫu câu / câu thông dụng / hội thoại /
quiz, chỉ phần CHỮ thay đổi. `publish_online.py --pack` sẽ nén lại 85 gói media
(~782 MB cho tiếng Nhật) — rất chậm và không cần thiết. Công cụ này:
  • đọc course.json đã enrich;
  • lấy `media_map` từ file web cũ của từng ngày (nguồn chính xác đang chạy);
  • ghi lại day/*.json + index.json (giữ nguyên `months`/zip của web cũ).

CÁCH DÙNG:
  python -X utf8 tools/export_days_keep_media.py --lang tiếng_nhật
  python -X utf8 tools/export_days_keep_media.py --lang tiếng_nhật --dry-run
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

CD = os.path.join(BASE, "data", "ai_courses")
WEB_DATA = os.path.join(BASE, "web", "data")


def _log(msg: str) -> None:
    print(msg, flush=True)


def export(slug: str, dry: bool = False) -> dict:
    src = os.path.join(CD, slug, "course.json")
    if not os.path.isfile(src):
        return {"slug": slug, "error": "no_course"}
    with open(src, encoding="utf-8") as f:
        course = json.load(f)
    days = course.get("days") or []
    out_dir = os.path.join(WEB_DATA, slug)
    day_dir = os.path.join(out_dir, "day")
    idx_path = os.path.join(out_dir, "index.json")

    old_index = {}
    if os.path.isfile(idx_path):
        try:
            with open(idx_path, encoding="utf-8") as f:
                old_index = json.load(f) or {}
        except Exception:
            old_index = {}
    old_months = old_index.get("months") or []
    if not dry:
        os.makedirs(day_dir, exist_ok=True)

    index = {"slug": slug, "level": course.get("level", ""),
             "total_days": len(days), "days": [], "months": old_months}
    written = kept = 0
    for d in days:
        try:
            n = int(d.get("day", 0))
        except Exception:
            continue
        # Giữ media_map cũ (ref → rel_path) — KHÔNG đụng tới gói media.
        media_map = {}
        old_day = os.path.join(day_dir, f"{n:04d}.json")
        if os.path.isfile(old_day):
            try:
                with open(old_day, encoding="utf-8") as f:
                    media_map = (json.load(f) or {}).get("media_map") or {}
                kept += 1
            except Exception:
                media_map = {}

        lesson = {k: v for k, v in d.items() if k != "media"}
        media = d.get("media") or {}
        lesson["media"] = {
            "vocab_audio": media.get("vocab_audio") or {},
            "dialogue_audio": media.get("dialogue_audio") or {},
        }
        lesson["media_map"] = media_map

        mkey = f"{n // 30 + 1:02d}"
        index["days"].append({
            "day": n,
            "title": d.get("title", ""),
            "phase": d.get("phase", ""),
            "level": d.get("level", ""),
            "month": mkey,
            "n_vocab": len(d.get("vocab") or []),
            "n_quiz": sum(len(v) for v in (d.get("quiz") or {}).values()
                          if isinstance(v, list)),
        })
        if not dry:
            with open(old_day, "w", encoding="utf-8") as f:
                json.dump(lesson, f, ensure_ascii=False, separators=(",", ":"))
            written += 1

    if not dry:
        with open(idx_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, separators=(",", ":"))
    _log(f"{slug}: {written if not dry else len(days)} ngày ghi"
         f" · {kept} ngày giữ media_map cũ"
         f" · months {len(old_months)}" + ("  (DRY-RUN)" if dry else ""))
    return {"slug": slug, "days": len(days), "written": written,
            "kept_media_map": kept, "months": len(old_months)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    r = export(args.lang, dry=args.dry_run)
    if r.get("error"):
        _log(f"LỖI: {r['error']}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
