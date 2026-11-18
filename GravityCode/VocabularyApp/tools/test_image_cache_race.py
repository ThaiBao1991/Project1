# -*- coding: utf-8 -*-
"""tools/test_image_cache_race.py — TEST THẬT bug đa luồng của cache ảnh.

Bug đo thật 17-18/11/2026: `find_images_for_words()` gọi `_save_cache()` KHÔNG
giữ lock trong khi luồng khác `_cache_put` ⇒
    RuntimeError: dictionary changed size during iteration
⇒ mỗi run mất ~3-6 ngày media ở MỌI khóa (day.fail).

Test: 8 luồng ghi cache + 2 luồng lưu cache liên tục vào file TẠM.
Trước khi sửa: gần như chắc chắn nổ RuntimeError.
Sau khi sửa: 0 lỗi, file JSON hợp lệ.

Chạy: python -X utf8 tools/test_image_cache_race.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai import dictionary_image as di  # noqa: E402

tmpdir = tempfile.mkdtemp(prefix="vocab_cache_test_")
di.CACHE_PATH = os.path.join(tmpdir, "image_cache.json")
di._cache = {}
di._cache_dirty = 0

errors = []
stop = threading.Event()


def writer(tid: int):
    try:
        for i in range(600):
            di._cache_put(f"lang{tid}", f"word-{tid}-{i}", {"url": f"u{i}"})
    except Exception as e:
        errors.append(f"writer{tid}: {type(e).__name__}: {e}")


def saver(tid: int):
    try:
        while not stop.is_set():
            di._save_cache()
            time.sleep(0.001)
    except Exception as e:
        errors.append(f"saver{tid}: {type(e).__name__}: {e}")


ths = [threading.Thread(target=writer, args=(i,)) for i in range(8)]
ths += [threading.Thread(target=saver, args=(i,)) for i in range(2)]
for t in ths:
    t.start()
for t in ths[:8]:
    t.join()
stop.set()
for t in ths[8:]:
    t.join()
di._save_cache()

ok = not errors
print(f"writers=8 saver=2 · loi={len(errors)}")
for e in errors[:5]:
    print("  ", e)
if os.path.isfile(di.CACHE_PATH):
    with open(di.CACHE_PATH, encoding="utf-8") as f:
        data = json.load(f)
    print(f"file cache hop le: {len(data)} entry")
else:
    ok = False
    print("KHONG co file cache")
print("PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
