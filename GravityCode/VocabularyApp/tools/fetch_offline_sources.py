# -*- coding: utf-8 -*-
"""tools/fetch_offline_sources.py — Tải nguồn nội dung OFFLINE (không tốn quota AI).

  1. EDICT2 (JMdict) — từ điển Nhật↔Anh (~7.5 MB) từ edrdg.org
  2. Wiktionary (ja.wiktionary.org) — NGHĨA TIẾNG VIỆT + ví dụ cho từ Nhật
     (API action, KHÔNG cần Gemini) → cache data/offline_src/wiktionary_vi.json

Cách dùng:
  python tools/fetch_offline_sources.py                  # tải EDICT + 1500 từ Wiktionary
  python tools/fetch_offline_sources.py --wiki-limit 300  # nhanh hơn
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai import offline_content  # noqa: E402

SRC = os.path.join(BASE, "data", "offline_src")
EDICT_URL = "http://ftp.edrdg.org/pub/Nihongo/edict2.gz"
WIKI_API = "https://ja.wiktionary.org/w/api.php"


def download_edict():
    os.makedirs(SRC, exist_ok=True)
    path = os.path.join(SRC, "edict2.gz")
    if os.path.isfile(path) and os.path.getsize(path) > 1_000_000:
        print(f"✓ EDICT2 đã có ({os.path.getsize(path)/1048576:.1f} MB)")
        return path
    print(f"⇩ Tải EDICT2 từ {EDICT_URL} …")
    with urllib.request.urlopen(EDICT_URL, timeout=180) as r, open(path, "wb") as f:
        f.write(r.read())
    print(f"✓ EDICT2: {os.path.getsize(path)/1048576:.1f} MB")
    return path


def _wiki_fetch(word: str) -> dict:
    """Nghĩa tiếng Việt cho 1 từ: thử ja.wiktionary (mục 'Tiếng Việt') rồi
    vi.wiktionary (mục 'Tiếng Việt' = Hán Việt của chữ Hán, mục 'Tiếng Nhật')."""
    for dom, heads in (("ja.wiktionary.org", ("Tiếng Việt",)),
                       ("vi.wiktionary.org", ("Tiếng Việt", "Tiếng Nhật"))):
        q = urllib.parse.urlencode({
            "action": "query", "prop": "extracts", "titles": word,
            "format": "json", "explaintext": "1", "redirects": "1"})
        req = urllib.request.Request(f"https://{dom}/w/api.php?{q}",
                                     headers={"User-Agent": "VocabularyApp/1.0 (offline)"})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.loads(r.read().decode("utf-8", "replace"))
        except Exception:
            continue
        pages = (data.get("query") or {}).get("pages") or {}
        for p in pages.values():
            if not isinstance(p, dict):
                continue
            txt = p.get("extract") or ""
            for head in heads:
                pat = (r"==\s*" + re.escape(head) + r"\s*==(.*?)(?=\n== |\Z)")
                m = re.search(pat, txt, re.S)
                if not m:
                    continue
                sec = m.group(1)
                defs = re.findall(r"^(?:\{\{[^}]*\}\}\s*)?(.+)$", sec, re.M)
                defs = [d.strip(" *") for d in defs if d.strip(" *")][:4]
                if defs:
                    return {"vi": "; ".join(defs)[:220]}
    return {}


def fetch_wiktionary(words, limit=1500, delay=0.05):
    cache_path = os.path.join(SRC, "wiktionary_vi.json")
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            cache = json.load(f) or {}
    except Exception:
        cache = {}
    todo = [w for w in words[:limit] if w not in cache]
    print(f"→ Wiktionary: cần tải {len(todo)} từ (đã có {len(cache)})")
    t0 = time.time()
    for i, w in enumerate(todo, 1):
        d = _wiki_fetch(w)
        if d:
            cache[w] = d
        if i % 25 == 0:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False)
            print(f"   {i}/{len(todo)} · cache {len(cache)} · {time.time()-t0:.0f}s")
        time.sleep(delay)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)
    print(f"✓ Wiktionary: cache {len(cache)} từ → {cache_path}")
    return cache


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wiki-limit", type=int, default=1500)
    ap.add_argument("--skip-edict", action="store_true")
    args = ap.parse_args()

    if not args.skip_edict:
        download_edict()
    edict = offline_content.load_edict()
    print(f"EDICT2: {len(edict)} mục")
    if not edict:
        return 1
    words = offline_content.select_words(edict, limit=max(200, args.wiki_limit))
    fetch_wiktionary(words, limit=args.wiki_limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
