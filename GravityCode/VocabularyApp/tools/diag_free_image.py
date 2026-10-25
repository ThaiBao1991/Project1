"""Thử nguồn ảnh MIỄN PHÍ không cần key + voice Gemini TTS."""
import base64
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from ai.course_generator import _load_gemini_keys

OUT = "data/media/_probe"
os.makedirs(OUT, exist_ok=True)


def try_pollinations():
    print("═══ POLLINATIONS.AI (free, no key) ═══")
    url = ("https://image.pollinations.ai/prompt/"
           "Flat%20vector%20illustration%20of%20a%20red%20apple%2C%20simple%20shapes%2C%20"
           "plain%20background%2C%20educational%20flashcard%20style%2C%20no%20text")
    for params in ({"width": 512, "height": 512, "nologo": "true", "seed": 42},
                   {"width": 512, "height": 512, "model": "flux"}):
        try:
            r = requests.get(url, params=params, timeout=120,
                             headers={"User-Agent": "Mozilla/5.0"})
            ct = r.headers.get("content-type", "")
            print(f"  params={list(params)} → HTTP {r.status_code} ct={ct} len={len(r.content)}")
            if r.status_code == 200 and ct.startswith("image/"):
                p = os.path.join(OUT, "pollinations.png")
                with open(p, "wb") as f:
                    f.write(r.content)
                print(f"  ✅ saved {p} ({os.path.getsize(p)} bytes)")
                return True
            else:
                print("  body:", r.text[:200])
        except Exception as e:
            print("  EXC", type(e).__name__, str(e)[:120])
        time.sleep(1)
    return False


def try_openverse():
    print("\n═══ OPENVERSE (free, no key) ═══")
    for q in ("apple fruit", "cat"):
        try:
            r = requests.get("https://api.openverse.org/v1/images/",
                             params={"q": q, "page_size": 5, "license_type": "commercial"},
                             timeout=45, headers={"User-Agent": "VocabularyApp/1.0"})
            print(f"  q={q!r} → HTTP {r.status_code}")
            if r.status_code == 200:
                d = r.json()
                n = d.get("result_count")
                for it in (d.get("results") or [])[:3]:
                    print(f"    - {it.get('title')!r} lic={it.get('license')} "
                          f"src={(it.get('thumbnail') or it.get('url') or '')[:80]}")
                if d.get("results"):
                    it = d["results"][0]
                    u = it.get("thumbnail") or it.get("url")
                    ir = requests.get(u, timeout=45, headers={"User-Agent": "Mozilla/5.0"})
                    if ir.status_code == 200 and ir.headers.get("content-type", "").startswith("image/"):
                        p = os.path.join(OUT, f"openverse_{q.split()[0]}.jpg")
                        with open(p, "wb") as f:
                            f.write(ir.content)
                        print(f"    ✅ saved {p} ({os.path.getsize(p)} bytes) "
                              f"credit={it.get('creator')!r} license={it.get('license')}")
        except Exception as e:
            print("  EXC", type(e).__name__, str(e)[:120])


def try_wikimedia():
    print("\n═══ WIKIPEDIA / WIKTIONARY pageimages ═══")
    for host, word in (("en.wikipedia.org", "Apple"), ("en.wiktionary.org", "apple"),
                       ("ja.wikipedia.org", "猫"), ("vi.wikipedia.org", "Mèo")):
        try:
            r = requests.get(f"https://{host}/w/api.php",
                             params={"action": "query", "prop": "pageimages",
                                     "titles": word, "format": "json",
                                     "pithumbsize": 400, "redirects": 1},
                             timeout=30, headers={"User-Agent": "VocabularyApp/1.0 (edu)"})
            d = r.json()
            pages = (d.get("query") or {}).get("pages") or {}
            for _pid, pg in pages.items():
                th = pg.get("thumbnail")
                print(f"  {host:22s} {word!r:8s} → HTTP {r.status_code} "
                      f"pageid={pg.get('pageid')} thumb={(th or {}).get('source','—')[:95]}")
        except Exception as e:
            print("  EXC", type(e).__name__, str(e)[:100])
        time.sleep(0.5)


def try_gemini_tts_voices():
    print("\n═══ GEMINI TTS — thử nhiều voice / ngôn ngữ ═══")
    keys = _load_gemini_keys()
    key = None
    for k in keys:
        if (k.get("email") or "").strip() == "gamesvendn@gmail.com":
            key = k
            break
    raw = key.get("key")
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"gemini-3.8-flash-tts:generateContent?key={raw}")
    tests = [
        ("Kore", "Xin chào, đây là tiếng Việt.", "vi"),
        ("Puck", "これは日本語のテストです。", "ja"),
        ("Charon", "这是中文测试。", "zh"),
        ("Fenrir", "이것은 한국어 테스트입니다.", "ko"),
        ("Aoede", "Bonjour, ceci est un test.", "fr"),
        ("Sadaltager", "Guten Tag, dies ist ein Test.", "de"),
        ("Kore", "Hello, this is English.", "en"),
    ]
    for voice, text, tag in tests:
        payload = {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
            },
        }
        try:
            r = requests.post(url, headers={"Content-Type": "application/json"},
                              json=payload, timeout=120)
            if r.status_code == 200:
                body = r.json()
                parts = (body.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
                aud = [p for p in parts if p.get("inlineData") or p.get("inline_data")]
                size = 0
                if aud:
                    d = aud[0].get("inlineData") or aud[0].get("inline_data") or {}
                    size = len(str(d.get("data", "")))
                print(f"  ✅ voice={voice:12s} [{tag}] audio={len(aud)} b64len={size}")
            else:
                body = r.json()
                err = body.get("error", {})
                print(f"  ❌ voice={voice:12s} [{tag}] HTTP {r.status_code} "
                      f"{str(err.get('message',''))[:120]}")
        except Exception as e:
            print(f"  EXC {voice}: {type(e).__name__} {str(e)[:100]}")
        time.sleep(1)


try_pollinations()
try_openverse()
try_wikimedia()
try_gemini_tts_voices()
