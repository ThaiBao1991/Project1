# -*- coding: utf-8 -*-
"""tools/media_index_swap.py — thu gọn manifest media theo 1 ngôn ngữ.

VÌ SAO: `data/media/index.json` hiện **333 MB / 606.418 entry** cho cả 8 khóa.
`media_store` nạp cả file vào RAM ⇒ riêng nó đã ~900 MB RSS (máy chỉ 7,3 GB).
Trong khi pipeline chỉ làm 1 khóa, không cần entry của 7 khóa đã xong.

CÁCH LÀM (không sửa media_store):
  begin <slug>:  đổi tên index.json → index_full.json, ghi index.json mới chỉ
                 chứa entry của <slug>  ⇒ pipeline nạp ~40 MB thay vì 333 MB.
  end <slug>:    gộp entry của index.json (shard) trở lại index_full.json,
                 ghi đè index.json, xoá index_full.json.
  status:        đang ở chế độ shard hay không.

An toàn: nếu crash giữa chừng, `index_full.json` vẫn còn; chạy `end` để khôi phục.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA = os.path.join(BASE, "data", "media")
INDEX = os.path.join(MEDIA, "index.json")
FULL = os.path.join(MEDIA, "index_full.json")


def _log(m: str) -> None:
    print(m, flush=True)


def _write(path: str, data: dict) -> None:
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, path)


def begin(slug: str) -> bool:
    """Tạo shard cho <slug>. Trả True nếu vừa chuyển, False nếu đã ở shard."""
    if os.path.isfile(FULL):
        _log(f"• đang ở chế độ shard ({os.path.basename(FULL)} tồn tại) — bỏ qua begin")
        return False
    if not os.path.isfile(INDEX):
        _log("✗ không thấy index.json")
        return False
    t0 = time.time()
    data = json.load(open(INDEX, encoding="utf-8"))
    items = data.get("items") or {}
    keep = {k: v for k, v in items.items()
            if str((v or {}).get("lang") or "") == slug}
    out = {"format_version": data.get("format_version", 1),
           "items": keep,
           "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    tmp = INDEX + f".shard.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(INDEX, FULL)          # rename tức thì, không copy 333 MB
    os.replace(tmp, INDEX)
    _log(f"✓ shard {slug}: {len(keep)}/{len(items)} entry · "
         f"{os.path.getsize(INDEX)/1e6:.1f} MB (full {os.path.getsize(FULL)/1e6:.0f} MB) · "
         f"{time.time()-t0:.1f}s")
    return True


def end(slug: str = "") -> bool:
    """Gộp shard trở lại full."""
    if not os.path.isfile(FULL):
        _log("• không ở chế độ shard — không cần gộp")
        return False
    t0 = time.time()
    shard = json.load(open(INDEX, encoding="utf-8")).get("items") or {}
    full_data = json.load(open(FULL, encoding="utf-8"))
    full_items = full_data.get("items") or {}
    full_items.update(shard)          # shard mới hơn ⇒ thắng
    full_data["items"] = full_items
    full_data["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    _write(INDEX, full_data)
    os.remove(FULL)
    _log(f"✓ gộp shard{' ' + slug if slug else ''}: {len(shard)} entry · "
         f"tổng {len(full_items)} · {os.path.getsize(INDEX)/1e6:.0f} MB · "
         f"{time.time()-t0:.1f}s")
    return True


def status() -> None:
    shard = os.path.isfile(FULL)
    _log(f"chế độ: {'SHARD' if shard else 'FULL'}")
    for p in (INDEX, FULL):
        if os.path.isfile(p):
            _log(f"  {os.path.basename(p):18} {os.path.getsize(p)/1e6:8.1f} MB")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["begin", "end", "status"])
    ap.add_argument("slug", nargs="?", default="")
    a = ap.parse_args()
    if a.cmd == "begin":
        if not a.slug:
            _log("✗ begin cần <slug>"); return 1
        begin(a.slug); return 0
    if a.cmd == "end":
        end(a.slug); return 0
    status(); return 0


if __name__ == "__main__":
    sys.exit(main())
