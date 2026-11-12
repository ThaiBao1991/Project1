# -*- coding: utf-8 -*-
"""tools/translate_vi.py — Tạo NGHĨA TIẾNG VIỆT cho từ vựng offline (không tốn quota Gemini).

VÌ SAO: Wiktionary tiếng Nhật chỉ có mục "Tiếng Việt" cho rất ít từ (đo thật:
3/1.200) ⇒ nghĩa tiếng Việt còn thiếu cho ~2.000 từ của khóa Nhật.

CÁCH LÀM: dịch gloss TIẾNG ANH (EDICT) → tiếng Việt theo LÔ 25 từ/request
(endpoint dịch không chính thức của Google — dùng 1 lần, có delay, cache vĩnh
viễn ⇒ sau đó KHÔNG cần gọi lại). Kết quả cache:
`data/offline_src/vi_meanings.json` = {từ: {"vi": "nghĩa tiếng Việt"}}

Cách dùng:
  python tools/translate_vi.py --limit 2000        # dịch tối đa 2.000 từ
  python tools/translate_vi.py --limit 2000 --apply
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai import offline_content as oc  # noqa: E402

OUT = os.path.join(oc.SRC_DIR, "vi_meanings.json")
API = "https://translate.googleapis.com/translate_a/single"
BATCH = 25


def _translate(texts):
    """Dịch lô (dùng \n làm dấu phân tách)."""
    q = urllib.parse.urlencode({
        "client": "gtx", "sl": "en", "tl": "vi", "dt": "t",
        "q": "\n".join(texts)})
    req = urllib.request.Request(f"{API}?{q}",
                                 headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = json.loads(r.read().decode("utf-8", "replace"))
    out = []
    for seg in (data[0] or []):
        out.append((seg[0] or "").replace("\n", " ").strip())
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=2000)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    edict = oc.load_edict()
    if not edict:
        print("⚠ Chưa có EDICT — chạy tools/fetch_offline_sources.py")
        return 1
    words = oc.select_words(edict, limit=max(400, args.limit))
    try:
        with open(OUT, "r", encoding="utf-8") as f:
            cache = json.load(f) or {}
    except Exception:
        cache = {}

    todo = []
    for w in words[:args.limit]:
        if w in cache:
            continue
        g = (edict.get(w) or {}).get("glosses") or []
        if not g:
            continue
        todo.append((w, g[0]))
    print(f"→ cần dịch {len(todo)} từ (đã có {len(cache)})")

    t0 = time.time()
    done = 0
    for i in range(0, len(todo), BATCH):
        chunk = todo[i:i + BATCH]
        try:
            res = _translate([c[1] for c in chunk])
        except Exception as e:
            print(f"  ⚠ lô {i//BATCH} lỗi: {type(e).__name__}: {e}")
            time.sleep(2)
            continue
        for (w, _en), vi in zip(chunk, res):
            if vi:
                cache[w] = {"vi": vi[:220]}
        done += len(chunk)
        if (i // BATCH) % 5 == 0:
            with open(OUT, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False)
            print(f"  {done}/{len(todo)} · cache {len(cache)} · {time.time()-t0:.0f}s")
        time.sleep(0.6)          # tôn trọng, tránh bị chặn
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)
    print(f"✓ xong: {len(cache)} từ có nghĩa tiếng Việt → {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
