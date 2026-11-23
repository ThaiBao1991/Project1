# -*- coding: utf-8 -*-
"""tools/reconcile_manifest.py — Bù các ref media_map còn thiếu vào manifest.

VẤN ĐỀ (audit 19/11/2026):
  • `web/data/*/day/*.json` có 76.770 ref không còn trong
    `data/media/index.json` (chủ yếu Trung/Nhật sau khi cleanup xoá `_pipeline`).
  • Nếu pack lại, `publish_online._day_media_map` sẽ thiếu các ref này ⇒ mất media.

CÁCH SỬA (không ghi đè manifest đang được pipeline ghi):
  • Quét `media_map` của web, tạo overlay `data/media/webmap_overlay.json`
    chỉ chứa các ref thiếu / khác rel_path.
  • `publish_online._manifest_days()` đọc thêm overlay (ưu tiên overlay).
  • Audit cũng tính overlay ⇒ hết báo missing.

CÁCH DÙNG:
  python -X utf8 tools/reconcile_manifest.py --dry-run
  python -X utf8 tools/reconcile_manifest.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MEDIA = os.path.join(BASE, "data", "media")
WEB = os.path.join(BASE, "web", "data")
OVERLAY = os.path.join(MEDIA, "webmap_overlay.json")
LANGS = ["tiếng_nhật", "tiếng_anh", "tiếng_hàn_quốc", "tiếng_nga",
         "tiếng_pháp", "tiếng_tây_ban_nha", "tiếng_đức", "tiếng_trung"]


def _mime(rel: str) -> tuple[str, str]:
    e = os.path.splitext(rel)[1].lower()
    if e in (".webp", ".png", ".jpg", ".jpeg", ".gif"):
        return "image", {".webp": "image/webp", ".png": "image/png",
                         ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                         ".gif": "image/gif"}[e]
    if e in (".mp3", ".wav", ".ogg", ".opus", ".m4a"):
        return "audio", {".mp3": "audio/mpeg", ".wav": "audio/wav",
                         ".ogg": "audio/ogg", ".opus": "audio/opus",
                         ".m4a": "audio/mp4"}[e]
    return "file", "application/octet-stream"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    print("đọc manifest …", flush=True)
    with open(os.path.join(MEDIA, "index.json"), encoding="utf-8") as f:
        man = json.load(f)
    base = {}
    for ref, e in (man.get("items") or {}).items():
        if isinstance(e, dict) and e.get("lang") and e.get("day"):
            base.setdefault((e["lang"], int(e["day"])), {})[ref] = e.get("rel_path") or ""
    old = {}
    if os.path.isfile(OVERLAY):
        try:
            with open(OVERLAY, encoding="utf-8") as f:
                old = (json.load(f) or {}).get("items") or {}
        except Exception:
            old = {}
    overlay = dict(old)
    added = changed = 0
    for slug in LANGS:
        d = os.path.join(WEB, slug, "day")
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if not fn.endswith(".json"):
                continue
            try:
                j = json.load(open(os.path.join(d, fn), encoding="utf-8"))
            except Exception:
                continue
            day = int(j.get("day") or fn.split(".")[0])
            for ref, rel in (j.get("media_map") or {}).items():
                if not ref or not rel:
                    continue
                cur = (base.get((slug, day)) or {}).get(ref)
                if cur == rel or (ref in overlay and overlay[ref].get("rel_path") == rel
                                  and overlay[ref].get("lang") == slug
                                  and int(overlay[ref].get("day") or 0) == day):
                    continue
                typ, mime = _mime(rel)
                overlay[ref] = {"id": ref, "lang": slug, "day": day,
                                "rel_path": rel, "type": typ, "kind": typ,
                                "mime": mime, "bytes": 0, "sha256": "",
                                "source": "web_media_map"}
                if cur is None:
                    added += 1
                else:
                    changed += 1
    print(f"ref mới: {added} | ref đổi rel_path: {changed} | overlay tổng: {len(overlay)}")
    if args.dry_run:
        return 0
    data = {"generated_at": f"{datetime.now():%Y-%m-%d %H:%M:%S}",
            "source": "web/data/*/day/*.json media_map",
            "items": overlay}
    tmp = OVERLAY + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, OVERLAY)
    print(f"✓ ghi {OVERLAY} ({os.path.getsize(OVERLAY)/1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
