# -*- coding: utf-8 -*-
"""tools/fetch_offline_words.py — Dựng NGUỒN TỪ VỰNG cho MỌI ngôn ngữ (không tốn quota AI).

Nguồn cho mỗi ngôn ngữ:
  • TỪ: `wordfreq.top_n_list(lang)` — tần suất thật (Google Books) ⇒ xếp từ đúng
    thứ tự ưu tiên, và cho ta **nguồn tần suất** mà trước đây thiếu.
  • NGHĨA: Wiktionary (en.wiktionary.org) — mục "== <Ngôn ngữ đích> ==" ⇒ gloss
    tiếng Anh; sau đó `tools/translate_vi.py` dịch sang tiếng Việt (cache 1 lần).
  • KANA (riêng cho Nhật): dùng EDICT/JMdict như `ai/offline_content.py`.

Kết quả cache: `data/offline_src/words_<iso>.json`
  = {"<từ>": {"gloss": "<tiếng Anh>", "reading": "<đọc>", "pos": "<loại từ>"}}

Cách dùng:
  python tools/fetch_offline_words.py --lang fr --limit 3000
  python tools/fetch_offline_words.py --lang all --limit 3000
"""
from __future__ import annotations

import argparse
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

SRC = os.path.join(BASE, "data", "offline_src")
WIKI = "https://en.wiktionary.org/w/api.php"

# iso → (tên mục Wiktionary, độ dài tối thiểu, ngôn ngữ dùng kana?)
LANGS = {
    "en": ("English", 3, False),
    "fr": ("French", 3, False),
    "de": ("German", 3, False),
    "es": ("Spanish", 3, False),
    "it": ("Italian", 3, False),
    "pt": ("Portuguese", 3, False),
    "ru": ("Russian", 3, False),
    "vi": ("Vietnamese", 3, False),
    "ko": ("Korean", 2, False),
    "zh": ("Chinese", 2, False),
    "ja": ("Japanese", 2, True),
}

STOP = set("""the a an of to in and or is are was were be been being for on at by
with from as it this that these those you your we our they their he she his her i me my
not no so if then than but which who whom whose what when where why how all any both each
few more most other some such only own same too very can will just should now""".split())


def _cache_path(iso):
    return os.path.join(SRC, f"words_{iso}.json")


def _words(iso, limit):
    from wordfreq import top_n_list
    raw = top_n_list(iso, int(limit * 4))
    minlen = LANGS.get(iso, ("English", 3, False))[1]
    out, seen = [], set()
    for w in raw:
        w = (w or "").strip()
        if not w or w in seen or len(w) < minlen:
            continue
        if w.lower() in STOP:
            continue
        if re.fullmatch(r"[\W\d_]+", w):
            continue
        seen.add(w)
        out.append(w)
        if len(out) >= limit:
            break
    return out


def _wiki(word, section):
    """Gloss tiếng Anh từ Wiktionary (1 request/từ — CHẬM, chỉ dùng khi cần)."""
    q = urllib.parse.urlencode({
        "action": "query", "prop": "extracts", "titles": word,
        "format": "json", "explaintext": "1", "redirects": "1"})
    req = urllib.request.Request(f"{WIKI}?{q}",
                                 headers={"User-Agent": "VocabularyApp/1.0 (offline)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        return {}
    pages = (data.get("query") or {}).get("pages") or {}
    for p in pages.values():
        if not isinstance(p, dict):
            continue
        txt = p.get("extract") or ""
        best = ""
        for m in re.finditer(r"(?m)^==\s*" + re.escape(section) + r"\s*==\s*$", txt):
            body = txt[m.end():]
            nxt = re.search(r"(?m)^==[^=]", body)
            body = body[:nxt.start()] if nxt else body
            if len(body) > len(best):
                best = body
        if not best:
            continue
        sub = re.search(r"(?m)^===\s*(Noun|Verb|Adjective|Adverb|Pronoun|Determiner|Preposition|Interjection|Article)\s*===\s*\n(.*?)(?=\n===|\Z)",
                        best, re.S)
        if sub:
            defs = [d.strip(" *") for d in sub.group(2).split("\n") if d.strip(" *")]
            defs = [d for d in defs if not d.startswith("=")][:3]
            if defs:
                return {"gloss": "; ".join(defs)[:220]}
    return {}


TRANSLATE = "https://translate.googleapis.com/translate_a/single"


def _translate_batch(words, src="auto"):
    """Dịch lô từ sang tiếng Việt (1 request cho 25 từ) — nhanh gấp ~50× so với
    gọi Wiktionary từng từ (đo thật: 231 từ/giờ ⇒ 26.000 từ mất 4,6 ngày)."""
    out = []
    for i in range(0, len(words), 25):
        chunk = words[i:i + 25]
        q = urllib.parse.urlencode({"client": "gtx", "sl": src, "tl": "vi",
                                   "dt": "t", "q": "\n".join(chunk)})
        req = urllib.request.Request(f"{TRANSLATE}?{q}",
                                     headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                data = json.loads(r.read().decode("utf-8", "replace"))
            # API dịch CẢ LÔ thành 1 đoạn nhiều dòng ⇒ phải tách theo "\n"
            # (lấy segment[0] đơn lẽ chỉ nhận 1/25 từ — lỗi đo được).
            text = ""
            for s in (data[0] or []):
                text += (s[0] or "")
            segs = [x.strip() for x in text.split("\n")]
        except Exception:
            segs = []
        while len(segs) < len(chunk):
            segs.append("")
        out.extend(segs[:len(chunk)])
        time.sleep(0.5)
    return out


def build(iso, limit, delay=0.12):
    """Dựng nguồn từ cho ngôn ngữ: wordfreq (tần suất) + DỊCH LÔ sang Việt.

    Nhanh: 25 từ/request (đo thật: gọi Wiktionary từng từ chỉ được 231 từ/giờ;
    dịch lô ⇒ ~3.000 từ/phút).
    """
    section, _minlen, _kana = LANGS.get(iso, ("English", 3, False))
    path = _cache_path(iso)
    try:
        with open(path, "r", encoding="utf-8") as f:
            cache = json.load(f) or {}
    except Exception:
        cache = {}
    words = _words(iso, limit)
    todo = [w for w in words if w not in cache]
    print(f"→ {iso}: cần dịch {len(todo)} từ (đã có {len(cache)})")
    t0 = time.time()
    done = 0
    for i in range(0, len(todo), 25):
        chunk = todo[i:i + 25]
        # Dịch bằng MÃ ngôn ngữ (sl=ko/ru/zh/...) — dùng "auto" KHÔNG nhận
        # Hàn/Nga (đo được: 25.025 từ duyệt ⇒ 0 từ có nghĩa Việt).
        vi = _translate_batch(chunk, src=iso if iso != "en" else "auto")
        if not any(vi):
            vi = _translate_batch(chunk, src="auto")
        for w, v in zip(chunk, vi):
            if v:
                cache[w] = {"vi": v[:220], "gloss": v[:220]}
        done += len(chunk)
        if (i // 25) % 20 == 0:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False)
            print(f"   {done}/{len(todo)} · cache {len(cache)} · {time.time()-t0:.0f}s")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False)
    print(f"✓ {iso}: {len(cache)} từ → {path}")
    return cache


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="ja")
    ap.add_argument("--limit", type=int, default=3000)
    args = ap.parse_args()
    os.makedirs(SRC, exist_ok=True)
    targets = list(LANGS) if args.lang == "all" else [args.lang]
    for iso in targets:
        if iso not in LANGS:
            print(f"⚠ chưa hỗ trợ '{iso}' (có: {', '.join(LANGS)})")
            continue
        build(iso, args.limit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
