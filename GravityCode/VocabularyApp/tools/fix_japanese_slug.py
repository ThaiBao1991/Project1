"""
tools/fix_japanese_slug.py — DỌN SPLIT-BRAIN 日本 trên đĩa (chạy trên máy chính).

Mạng lưới dữ liệu thật hiện tại:
  • data/ai_courses/nhật/           khóa học 444 ngày (alias)
  • data/ai_courses/tiếng_nhật/      khóa học 1.260 ngày (canonical)
  • data/nhật.json                  vocab nhập tay 60 từ (alias)
  • data/tiếng_nhật.json             vocab nhập tay canonical

Tool làm đúng 2 việc (AN TOÀN, KHÔNG XÓA):
    1. ARCHIVE: data/ai_courses/nhật → data/ai_courses/_archive/nhật-<ts>/
     (copy nguyên vẹn; KHÔNG xoá bản gốc)
  2. MERGE VỌC: data/nhật.json → data/tiếng_nhật.json
     • gộp theo từ (bỏ từ đã trùng word), giữ nghĩa đã có
     • backup bản gốc tiếng_nhật.json trước khi ghi (atomic, có .bak-<ts>)
  Ý nghĩa: dropdown web/app chỉ còn canonical 'tiếng_nhật' (code đã canonicalize).

Cú pháp:
  python tools/fix_japanese_slug.py            # DRY-RUN (không đổi gì)
  python tools/fix_japanese_slug.py --apply    # thực thi thật (backup + atomic)
"""
import argparse
import json
import os
import shutil
import sys
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai.paths import DATA_DIR  # noqa: E402

ALIAS = "nhật"
CANON = "tiếng_nhật"


def archive_alias_course(apply_changes: bool) -> str:
    """Di chuyển data/ai_courses/nhật → _archive/. Trả mô tả thao tác."""
    src = os.path.join(DATA_DIR, "ai_courses", ALIAS)
    canon_c = os.path.join(DATA_DIR, "ai_courses", CANON)
    if not os.path.isdir(src):
        return f"• {ALIAS}/ không tồn tại — bỏ qua archive."
    if not os.path.isdir(canon_c):
        return f"⛔ {CANON}/ không tồn tại — KHÔNG archive khi chưa có bản canonical!"
    dst_root = os.path.join(DATA_DIR, "ai_courses", "_archive")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = os.path.join(dst_root, f"{ALIAS}-{stamp}")
    if apply_changes:
        os.makedirs(dst_root, exist_ok=True)
        shutil.copytree(src, dst)
        print(f"📦 Đã copy {src} → {dst}")
    return (f"• archive: {ALIAS}/ → _archive/{ALIAS}-{stamp}/ "
            f"{'[APPLIED]' if apply_changes else '[dry-run — chưa move]'}")


def merge_vocabs(apply_changes: bool) -> str:
    """Gộp data/nhật.json vào data/tiếng_nhật.json (theo word, backup + atomic)."""
    src = os.path.join(DATA_DIR, f"{ALIAS}.json")
    dst = os.path.join(DATA_DIR, f"{CANON}.json")
    if not os.path.isfile(src):
        return f"• {ALIAS}.json không tồn tại — bỏ qua merge vocab."
    with open(src, "r", encoding="utf-8") as f:
        sdata = json.load(f)
    src_vocab = sdata.get("vocabularies") or []

    ddata = {}
    if os.path.isfile(dst):
        with open(dst, "r", encoding="utf-8") as f:
            ddata = json.load(f)
        if not isinstance(ddata, dict):
            return f"⛔ {CANON}.json không phải dict — dừng để tránh ghi đè dữ liệu."
    dst_vocab = ddata.get("vocabularies") or []

    have = {v.get("word") for v in dst_vocab if isinstance(v, dict)}
    adds = [v for v in src_vocab if isinstance(v, dict) and v.get("word") not in have]
    out = dst_vocab + adds
    msg = (f"• merge vocab: {ALIAS}.json ({len(src_vocab)} từ) → {CANON}.json "
           f"(+{len(adds)} mới, tổng {len(out)}) "
           f"{'[APPLIED]' if apply_changes else '[dry-run — chưa ghi]'}")
    if apply_changes and adds:
        if os.path.isfile(dst):
            bak = dst + ".bak-" + datetime.now().strftime("%Y%m%d-%H%M%S")
            shutil.copy2(dst, bak)
            print(f"💾 Backup: {bak}")
        ddata["vocabularies"] = out
        ddata["last_updated"] = datetime.now().isoformat(timespec="seconds")
        tmp = dst + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(ddata, f, ensure_ascii=False, indent=2)
        os.replace(tmp, dst)
    return msg


def main():
    ap = argparse.ArgumentParser(prog="fix_japanese_slug")
    ap.add_argument("--apply", action="store_true", help="Thực thi thật (mặc định dry-run)")
    args = ap.parse_args()

    print("== Dọn split-brain slug Nhật ==")
    print(archive_alias_course(args.apply))
    print(merge_vocabs(args.apply))
    if not args.apply:
        print("\n[chỉ dry-run] Chạy `--apply` để thực thi (đều có backup, không xoá).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
