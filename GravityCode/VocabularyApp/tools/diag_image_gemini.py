"""Chẩn đoán lỗi thật của Gemini image generation theo từng key."""
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = __import__("os").path.dirname(__import__("os").path.abspath(__file__))
sys.path.insert(0, BASE)

import requests
from ai.course_generator import _load_gemini_keys

URL = ("https://generativelanguage.googleapis.com/v1beta/models/"
       "gemini-2.5-flash-image:generateContent")

PROMPT = ("Flat vector illustration of a red apple, simple shapes, plain background, "
          "educational flashcard style, no text, no watermark.")

keys = _load_gemini_keys()
# lấy 1 key/account
seen = set()
picked = []
for k in keys:
    a = (k.get("email") or "").strip()
    if a in seen:
        continue
    seen.add(a)
    picked.append(k)

print(f"Thử {len(picked)} key (1/account) với model gemini-2.5-flash-image\n")
for k in picked:
    raw = k.get("key") or ""
    acct = (k.get("email") or "?").strip()
    try:
        r = requests.post(URL + f"?key={raw}",
                          headers={"Content-Type": "application/json"},
                          json={"contents": [{"parts": [{"text": PROMPT}]}],
                                "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}},
                          timeout=180)
        print(f"--- {acct} : HTTP {r.status_code} ---")
        try:
            body = r.json()
        except Exception:
            print("   non-JSON:", r.text[:200])
            continue
        if r.status_code == 200:
            parts = (body.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
            has_img = any(p.get("inlineData") or p.get("inline_data") for p in parts)
            txt = ""
            for p in parts:
                if p.get("text"):
                    txt = p["text"][:200]
                    break
            print(f"   OK — có ảnh: {has_img} | parts={len(parts)} | text={txt!r}")
        else:
            err = body.get("error", {}) if isinstance(body, dict) else {}
            print("   status:", err.get("status"))
            print("   msg   :", str(err.get("message", ""))[:400])
            det = err.get("details")
            if det:
                print("   details:", str(det)[:300])
    except Exception as e:
        print(f"--- {acct} : EXC {type(e).__name__}: {str(e)[:150]}")
    time.sleep(1)
