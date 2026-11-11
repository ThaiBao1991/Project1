# -*- coding: utf-8 -*-
"""tools/reindex_media.py — Dựng lại manifest media từ file thật trên đĩa.

VÌ SAO CẦN (đo thật trên máy, 2026-11-12):
  • `data/media/index.json` có 65.013 entry, nhưng trên đĩa có **77.626
    file** ⇒ **12.655 file "mồ côi"** (đã sinh xong nhưng mất entry manifest
    do race khi ghi index trước đây).
  • File trên đĩa là file ĐÚNG (id = "m_" + hash(rel_path, sha256) — cách
    `media_store.save_*` cũng dùng) ⇒ reindex khôi phục ĐÚNG id mà
    `course.json` đang trỏ tới ⇒ các nút âm thanh/ảnh "mất" sẽ hiện lại.
  • Manifest là file 32.8 MB ⇒ web tải 32.8 MB mỗi lần mở trang.

CÁCH DÙNG
  python tools/reindex_media.py            # backup + reindex
  python tools/reindex_media.py --check    # chỉ báo cáo, KHÔNG ghi

LƯU Ý: quét + SHA-256 toàn bộ file ⇒ chạy 1 lần (vài phút), không chạy mỗi
lần sinh nội dung.
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

from ai import media_store  # noqa: E402


def _count_files():
    n = 0
    if os.path.isdir(media_store.MEDIA_DIR):
        for root, _d, fs in os.walk(media_store.MEDIA_DIR):
            for x in fs:
                if x != "index.json" and not x.endswith(".tmp"):
                    n += 1
    return n


def main() -> int:
    ap = argparse.ArgumentParser(description="Reindex manifest media")
    ap.add_argument("--check", action="store_true", help="chỉ báo cáo, không ghi")
    args = ap.parse_args()

    idx = media_store.INDEX_PATH
    before = 0
    if os.path.isfile(idx):
        try:
            with open(idx, "r", encoding="utf-8") as f:
                before = len((json.load(f) or {}).get("items") or {})
        except Exception:
            before = 0
    files = _count_files()
    print(f"=== Reindex manifest media ===")
    print(f"  file trên đĩa : {files}")
    print(f"  entry manifest: {before}")
    print(f"  file mồ côi   : {max(0, files - before)}")
    if args.check:
        print("  ℹ️  --check: không ghi.")
        return 0

    if os.path.isfile(idx):
        bak = idx + ".bak_reindex"
        try:
            shutil.copy2(idx, bak)
            print(f"  💾 backup: {bak}")
        except Exception as e:
            print(f"  ⚠ không backup được: {e}")

    t0 = time.time()
    res = media_store.reindex(log_fn=lambda m: print(m))
    after = res.get("items", 0)
    print(f"\n  ✅ xong: {res.get('scanned')} file quét · manifest {before} → {after} entry "
          f"({time.time() - t0:.1f}s)")
    print(f"     manifest: {os.path.getsize(idx) / 1048576:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
