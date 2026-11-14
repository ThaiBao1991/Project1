# -*- coding: utf-8 -*-
"""tools/test_media_manifest.py — Test manifest media (Gói 7/8, 2026-11-14).

Bảo vệ 2 lỗi đã gặp thật:
  1. `save_index` dùng CHUNG tên file `.tmp` cho mọi process ⇒ 2 process ghi
     đồng thời ⇒ file JSON chứa 2 document nối liền ⇒ `json.load` lỗi
     "Extra data" ⇒ **toàn bộ media biến mất khỏi app** (đo thật: manifest
     86 MB hỏng ⇒ mọi khóa báo "ảnh 0.0 %").
  2. `load_index` nuốt lỗi và trả index RỖNG ⇒ app mất media mà không báo.

Test:
  A. Tên file tmp PHẢI DUY NHẤT theo PID/thread.
  B. Manifest hỏng ⇒ tự khôi phục (file dự phòng hoặc reindex) — KHÔNG
     được trả về index rỗng.
  C. `save_index` + `load_index` giữ nguyên entry (round-trip).
  D. `reindex()` dựng lại manifest từ file thật trên đĩa.

Chạy:  python tools/test_media_manifest.py
"""
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    from ai import media_store

    results = []

    def ck(name, cond, detail=""):
        results.append((name, bool(cond), detail))

    # ── A. tên tmp duy nhất ────────────────────────────────────────────────
    tmp_dir = tempfile.mkdtemp(prefix="vocab_manifest_")
    orig_path = media_store.INDEX_PATH
    orig_media = media_store.MEDIA_DIR
    orig_cache = media_store._index_cache
    try:
        media_store.MEDIA_DIR = tmp_dir        # reindex trong test chỉ quét
        media_store.INDEX_PATH = os.path.join(tmp_dir, "index.json")
        media_store._index_cache = None

        idx = {"format_version": 1, "items": {"m_a": {"id": "m_a", "type": "image"}}}
        media_store.save_index(idx)

        # Tên tmp phải chứa PID (và thread) ⇒ 2 process không trùng file.
        src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "ai", "media_store.py"),
                   encoding="utf-8").read()
        has_pid = ("tmp.{os.getpid()}" in src) or ("tmp.{pid}" in src)
        ck("save_index dùng tên tmp DUY NHẤT theo PID", has_pid,
           "không thấy PID trong tên tmp" if not has_pid else "")
        leftovers = [f for f in os.listdir(tmp_dir) if ".tmp." in f]
        ck("không còn file tmp sót lại", not leftovers, f"sót: {leftovers}")

        # ── C. round-trip ───────────────────────────────────────────────────
        media_store._index_cache = None
        got = media_store.load_index()
        ck("round-trip giữ nguyên entry", "m_a" in (got.get("items") or {}),
           f"items={list((got.get('items') or {}).keys())}")

        # ── B. manifest hỏng ⇒ tự khôi phục ────────────────────────────────
        # Tạo 1 file media thật trong thư mục tạm ⇒ reindex dựng lại được.
        os.makedirs(os.path.join(tmp_dir, "tiếng_nhật", "d0001"), exist_ok=True)
        with open(os.path.join(tmp_dir, "tiếng_nhật", "d0001", "word_00_x.webp"),
                  "wb") as f:
            f.write(b"x" * 32)
        with open(media_store.INDEX_PATH, "w", encoding="utf-8") as f:
            f.write('{"items": {"m_a": {}}}')     # JSON 1
            f.write('{"items": {"m_b": {}}}')     # JSON 2 nối liền ⇒ HỎNG
        media_store._index_cache = None
        recovered = media_store.load_index()
        items = recovered.get("items") or {}
        ck("manifest hỏng ⇒ tự khôi phục (không rỗng)", len(items) > 0,
           f"items={len(items)}")
    finally:
        media_store.INDEX_PATH = orig_path
        media_store.MEDIA_DIR = orig_media
        media_store._index_cache = orig_cache
        shutil.rmtree(tmp_dir, ignore_errors=True)

    # ── D. reindex từ đĩa (thư mục TẠM — không quét cả 158k file thật) ──
    try:
        tmp_media = tempfile.mkdtemp(prefix="vocab_media_")
        os.makedirs(os.path.join(tmp_media, "tiếng_nhật", "d0001"), exist_ok=True)
        for i, name in enumerate(("word_00_aaa.webp", "audio_00_bbb.mp3")):
            with open(os.path.join(tmp_media, "tiếng_nhật", "d0001", name),
                      "wb") as f:
                f.write(b"x" * 64)
        orig_media = media_store.MEDIA_DIR
        orig_index = media_store.INDEX_PATH
        media_store.MEDIA_DIR = tmp_media
        media_store.INDEX_PATH = os.path.join(tmp_media, "index.json")
        media_store._index_cache = None
        res = media_store.reindex(log_fn=lambda *a: None)
        ck("reindex() dựng lại manifest từ đĩa",
           res.get("items", 0) == 2, f"items={res.get('items')}")
        media_store.MEDIA_DIR = orig_media
        media_store.INDEX_PATH = orig_index
        media_store._index_cache = None
        shutil.rmtree(tmp_media, ignore_errors=True)
    except Exception as e:
        ck("reindex() dựng lại manifest từ đĩa", False,
           f"{type(e).__name__}: {e}")

    print("\n" + "=" * 62)
    ok = 0
    for name, passed, detail in results:
        mark = "PASS" if passed else "FAIL"
        if passed:
            ok += 1
        print(f"[{mark}] {name}" + (f"  — {detail}" if detail else ""))
    print("=" * 62)
    print(f"→ {ok}/{len(results)} PASS")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
