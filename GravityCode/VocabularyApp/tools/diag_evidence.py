"""
diag_evidence.py — Kiểm tra thật module ai/evidence.py (evidence cho từ vựng).

Chạy:
    python tools\\diag_evidence.py

In ra: số nguồn tìm được, URL, có IPA không, có etymology không, thời gian,
       hành vi cache, và hành vi lọc URL chết của tầng AI.
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai import evidence                                    # noqa: E402
from ai.evidence import (attach_to_lesson, cache_get, cache_key,  # noqa: E402
                         cache_put, fetch_wikipedia, fetch_wiktionary,
                         gather, load_cache, save_cache, verify_url)

CASES = [
    ("cat", "en", "con mèo"),
    ("water", "en", "nước"),
    ("猫", "ja", "con mèo"),
    ("犬", "ja", "con chó"),
]


def line(ch="-", n=78):
    print(ch * n)


def show(title):
    print()
    line("=")
    print(title)
    line("=")


def test_fetch_layer():
    show("1) Lớp fetch: Wikipedia + Wiktionary")
    print(f"{'từ':10s} {'ngôn ngữ':9s} {'wiki':6s} {'wiki URL':46s} "
          f"{'wikt':6s} {'ipa':22s} {'etym':6s} {'ref':4s}")
    for word, lang, _m in CASES:
        t0 = time.time()
        wp = fetch_wikipedia(word, lang)
        wt = fetch_wiktionary(word, lang)
        dt = time.time() - t0
        ipa = (wt.get("ipa") or ["—"])[0]
        ety = "có" if wt.get("etymology") else "không"
        nref = len(wt.get("references") or [])
        print(f"{word:10s} {lang:9s} {'OK' if wp.get('has_data') else '—':6s} "
              f"{(wp.get('url') or '—')[:46]:46s} "
              f"{'OK' if wt.get('has_data') else '—':6s} {ipa[:22]:22s} "
              f"{ety:6s} {nref:<4d} ({dt:.1f}s)")
    return


def test_verify_url():
    show("2) verify_url — URL sống / URL chết")
    for u in ("https://en.wikipedia.org/wiki/Cat",
              "https://ja.wikipedia.org/wiki/%E3%83%8D%E3%82%B3",
              "https://example.com/definitely-not-here-404",
              "not-a-url"):
        t0 = time.time()
        ok = verify_url(u)
        print(f"  {str(ok):5s} ({time.time()-t0:4.1f}s)  {u}")


def test_gather():
    show("3) gather() — chuỗi 4 nguồn")
    for word, lang, meaning in CASES:
        t0 = time.time()
        res = gather(word, lang, meaning, log_fn=None, use_cache=False)
        dt = time.time() - t0
        kinds = ",".join(s.get("kind", "") for s in res.get("sources", []))
        print(f"  {word:10s} [{lang}] nguồn={len(res.get('sources', [])):d} "
              f"({kinds}) ipa={len(res.get('ipa', [])):d} "
              f"etym={'có' if res.get('etymology') else 'không':6s} "
              f"conf={res.get('confidence'):6s} refs={len(res.get('wiktionary_references', [])):d} "
              f"({dt:.1f}s)")
        for s in res.get("sources", []):
            print(f"       - {s.get('kind'):12s} {s.get('title')[:24]:24s} {s.get('url')}")
    return


def test_cache():
    show("4) Cache bền — ghi / đọc / TTL")
    key = cache_key("en", "cat")
    n_entries = len(load_cache())
    print(f"  file      : {evidence.CACHE_PATH}")
    print(f"  entries   : {n_entries}")
    print(f"  key       : {key}")
    t0 = time.time()
    got = cache_get(key)
    print(f"  cache_get : {'HIT' if got is not None else 'MISS'} ({time.time()-t0:.3f}s)")
    if got:
        print(f"             nguồn={len(got.get('sources', []))} "
              f"fetched_at={got.get('fetched_at')}")
    # ghi entry rỗng vào key RIÊNG (không đụng dữ liệu thật) rồi đọc lại
    scratch = cache_key("en", "__diag_empty__")
    cache_put(scratch, {})
    print(f"  cache_put(scratch, {{}}) → cache_get = {cache_get(scratch)!r} "
          f"(giữ luôn ⇒ không hỏi lại)")
    save_cache()
    print(f"  save_cache(): OK ({os.path.getsize(evidence.CACHE_PATH)} bytes)")

    # TTL: entry cũ hơn 30 ngày ⇒ phải MISS
    st = evidence._cache_state()
    ttl_key = cache_key("en", "__diag_ttl__")
    st["entries"][ttl_key] = {"word": "x", "sources": []}
    st["stamps"][ttl_key] = (datetime.now(timezone.utc)
                              - timedelta(days=31)).isoformat()
    print(f"  TTL 31 ngày  → cache_get = {cache_get(ttl_key)!r} (phải là None)")
    st["entries"].pop(ttl_key, None)
    st["stamps"].pop(ttl_key, None)

    # dọn rác
    st = evidence._cache_state()
    st["entries"].pop(scratch, None)
    st["stamps"].pop(scratch, None)
    save_cache()


def test_fail_guard():
    show("5) Chống cache độc: lỗi mạng KHÔNG được ghi vào cache")
    word = f"__diag_offline_{int(time.time())}__"   # từ duy nhất ⇒ không dính cache
    key = cache_key("en", word)
    orig_get = evidence.requests.get

    def boom(*a, **k):
        raise ConnectionError("giả lập mất mạng")

    evidence.requests.get = boom            # requests.get hỏng ⇒ mất mạng thật
    try:
        res = gather(word, "en", use_cache=True)
    finally:
        evidence.requests.get = orig_get
    print(f"  gather() khi mất mạng  → fetch_failed={res.get('fetch_failed')} "
          f"nguồn={len(res.get('sources', []))}")
    print(f"  cache có entry sai?     → {cache_get(key) is not None} "
          f"(phải là False)")
    st = evidence._cache_state()
    st["entries"].pop(key, None)
    st["stamps"].pop(key, None)
    save_cache()


def test_ai_layer():
    show("6) Tầng AI — verify URL còn sống (URL giả bị loại)")

    def fake_ai(word=None, lang=None, meaning_vi=None, **kw):
        return {"sources": [
            {"title": "Wikipedia (thật)", "url": "https://en.wikipedia.org/wiki/Cat",
             "kind": "wikipedia", "quote": "The cat is a domesticated carnivore."},
            {"title": "URL chết", "url": "https://example.com/no-such-page-xyz-404",
             "kind": "web", "quote": "trang không tồn tại"},
            {"title": "URL giả", "url": "https://this-domain-does-not-exist-zzz.invalid/x",
             "kind": "web", "quote": "tên miền không có"},
        ]}

    t0 = time.time()
    base = gather("cat", "en", "con mèo", use_cache=False)
    res = gather("cat", "en", "con mèo", use_ai=fake_ai, use_cache=False)
    dt = time.time() - t0
    ai_urls = {"https://en.wikipedia.org/wiki/Cat",
               "https://example.com/no-such-page-xyz-404",
               "https://this-domain-does-not-exist-zzz.invalid/x"}
    alive = [s for s in res["sources"] if s.get("url") in ai_urls]
    print(f"  AI trả 3 URL (1 thật, 2 chết) → URL AI còn sống: {len(alive)} "
          f"(bỏ {len(ai_urls)-len(alive)}) — tổng nguồn {len(base['sources'])} → "
          f"{len(res['sources'])} ({dt:.1f}s)")
    for s in alive:
        print(f"     - GIỮ  {s.get('kind'):12s} {s.get('url')}")
    for s in res["sources"]:
        if s.get("url") not in ai_urls:
            print(f"     - nền  {s.get('kind'):12s} {s.get('url')}")


def test_attach():
    show("7) attach_to_lesson — ghi vào lesson['vocab']")
    lesson = {
        "day": 1,
        "vocab": [
            {"word": "cat", "pronunciation": "/kæt/", "meaning_vi": "con mèo",
             "ipa": "/kæt/"},
            {"word": "dog", "pronunciation": "/dɒɡ/", "meaning_vi": "con chó"},
            {"word": "bird", "pronunciation": "/bɜːd/", "meaning_vi": "con chim"},
        ],
    }
    t0 = time.time()
    st = attach_to_lesson(lesson, "en", log_fn=None)
    dt = time.time() - t0
    print(f"  stats={st}  ({dt:.1f}s)")
    for v in lesson["vocab"]:
        print(f"   - {v['word']:6s} sources={len(v.get('sources', [])):d} "
              f"ipa_ev={v.get('ipa_ev', '')!r:14s} "
              f"etym={('có' if v.get('etymology') else 'không')}")
    print("  chạy lần 2 (cache):", end=" ")
    t0 = time.time()
    st2 = attach_to_lesson(lesson, "en", log_fn=None)
    print(f"{st2} ({time.time()-t0:.2f}s)")


test_fetch_layer()
test_verify_url()
test_gather()
test_cache()
test_fail_guard()
test_ai_layer()
test_attach()

show("KẾT QUẢ")
ok = len(load_cache())
print(f"  cache entries : {ok}")
print(f"  cache file    : {evidence.CACHE_PATH}")
print("  xem chi tiết  : python -m ai.evidence --word cat --lang en")
