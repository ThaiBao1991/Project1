"""Kiểm tra TẤT CẢ model ảnh + các model text có hỗ trợ image không."""
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from ai.course_generator import _load_gemini_keys

PROMPT = ("Flat vector illustration of a red apple, simple shapes, plain background, "
          "educational flashcard style, no text, no watermark.")

MODELS = [
    "gemini-2.5-flash-image",
    "gemini-3.1-flash-image",
    "gemini-3-pro-image",
    "gemini-3-pro-image-preview",
    "gemini-3.1-flash-image-preview",
    "gemini-nano-banana-2.1",
    "gemini-2.0-flash-preview-image",
    "gemini-2.0-flash-exp",
    "gemini-3-flash-image",
]

keys = _load_gemini_keys()
# key từ account gamesvendn (đã biết là OK cho text)
key = None
for k in keys:
    if (k.get("email") or "").strip() == "gamesvendn@gmail.com" and k.get("status") != "invalid":
        key = k
        break
if not key:
    print("no key")
    sys.exit(2)
raw = key.get("key")
print("Dùng key của account gamesvendn@gmail.com\n")

for model in MODELS:
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={raw}")
    try:
        r = requests.post(url, headers={"Content-Type": "application/json"},
                          json={"contents": [{"parts": [{"text": PROMPT}]}],
                                "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}},
                          timeout=180)
        if r.status_code == 200:
            body = r.json()
            parts = (body.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
            imgs = [p for p in parts if p.get("inlineData") or p.get("inline_data")]
            print(f"✅ {model:32s} HTTP 200 — parts={len(parts)} ảnh={len(imgs)}")
            for p in imgs[:1]:
                d = p.get("inlineData") or p.get("inline_data") or {}
                print(f"      mime={d.get('mimeType') or d.get('mime_type')} "
                      f"b64len={len(str(d.get('data','')))}")
        else:
            body = r.json()
            err = body.get("error", {}) if isinstance(body, dict) else {}
            msg = str(err.get("message", "")).replace("\n", " ")
            # rút gọn
            import re as _re
            m = _re.search(r"model: ([^\s*]+)", msg)
            lim = _re.search(r"limit: (\d+)", msg)
            met = _re.search(r"metric: ([^\s*]+)", msg)
            print(f"❌ {model:32s} HTTP {r.status_code} | {err.get('status')} | "
                  f"model_alias={m.group(1) if m else '?'} | "
                  f"metric={(met.group(1).split('/')[-1] if met else '?')} | "
                  f"limit={lim.group(1) if lim else '?'}")
            if not lim:
                print("      msg:", msg[:220])
    except Exception as e:
        print(f"❌ {model:32s} EXC {type(e).__name__}: {str(e)[:120]}")
    time.sleep(2)
