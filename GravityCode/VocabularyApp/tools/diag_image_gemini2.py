"""Thử các model ảnh chưa test + model TTS của Gemini."""
import base64
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from ai.course_generator import _load_gemini_keys

keys = _load_gemini_keys()
key = None
for k in keys:
    if (k.get("email") or "").strip() == "gamesvendn@gmail.com":
        key = k
        break
raw = key.get("key")

PROMPT = ("Flat vector illustration of a red apple, simple shapes, plain background, "
          "educational flashcard style, no text, no watermark.")


def try_image(model):
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={raw}")
    try:
        r = requests.post(url, headers={"Content-Type": "application/json"},
                          json={"contents": [{"parts": [{"text": PROMPT}]}],
                                "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}},
                          timeout=180)
    except Exception as e:
        print(f"❌ {model:34s} EXC {type(e).__name__}: {str(e)[:100]}")
        return
    if r.status_code == 200:
        body = r.json()
        parts = (body.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
        imgs = [p for p in parts if p.get("inlineData") or p.get("inline_data")]
        info = ""
        if imgs:
            d = imgs[0].get("inlineData") or imgs[0].get("inline_data") or {}
            info = f"mime={d.get('mimeType') or d.get('mime_type')} b64len={len(str(d.get('data','')))}"
        print(f"✅ {model:34s} HTTP 200 — parts={len(parts)} ảnh={len(imgs)} {info}")
        if imgs:
            d = imgs[0].get("inlineData") or imgs[0].get("inline_data") or {}
            try:
                out = f"data/media/_probe_{model}.png"
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with open(out, "wb") as f:
                    f.write(base64.b64decode(d.get("data", "")))
                print(f"      saved {out} ({os.path.getsize(out)} bytes)")
            except Exception as e:
                print("      save fail:", e)
    else:
        try:
            body = r.json()
            err = body.get("error", {}) if isinstance(body, dict) else {}
            msg = str(err.get("message", "")).replace("\n", " ")
        except Exception:
            msg = r.text[:200]
        import re as _re
        m = _re.search(r"model: ([^\s*]+)", msg)
        lim = _re.search(r"limit: (\d+)", msg)
        met = _re.search(r"metric: ([^\s*]+)", msg)
        print(f"❌ {model:34s} HTTP {r.status_code} | {err.get('status') if isinstance(err,dict) else '?'} | "
              f"alias={m.group(1) if m else '?'} | "
              f"metric={(met.group(1).split('/')[-1] if met else '?')} | limit={lim.group(1) if lim else '?'}")
        if not lim:
            print("      ", msg[:200])


def try_tts(model, text="Xin chào, đây là bài kiểm tra giọng đọc."):
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent?key={raw}")
    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Kore"}}
            },
        },
    }
    try:
        r = requests.post(url, headers={"Content-Type": "application/json"},
                          json=payload, timeout=180)
    except Exception as e:
        print(f"❌ TTS {model:30s} EXC {type(e).__name__}: {str(e)[:100]}")
        return
    if r.status_code == 200:
        body = r.json()
        parts = (body.get("candidates") or [{}])[0].get("content", {}).get("parts", [])
        aud = [p for p in parts if p.get("inlineData") or p.get("inline_data")]
        info = ""
        if aud:
            d = aud[0].get("inlineData") or aud[0].get("inline_data") or {}
            info = f"mime={d.get('mimeType') or d.get('mime_type')} b64len={len(str(d.get('data','')))}"
            try:
                out = f"data/media/_probe_tts_{model}.pcm"
                os.makedirs(os.path.dirname(out), exist_ok=True)
                with open(out, "wb") as f:
                    f.write(base64.b64decode(d.get("data", "")))
                info += f" saved={os.path.getsize(out)}B"
            except Exception as e:
                info += f" save fail {e}"
        print(f"✅ TTS {model:30s} HTTP 200 — parts={len(parts)} audio={len(aud)} {info}")
    else:
        try:
            body = r.json()
            err = body.get("error", {}) if isinstance(body, dict) else {}
            msg = str(err.get("message", "")).replace("\n", " ")
        except Exception:
            msg = r.text[:250]
        import re as _re
        lim = _re.search(r"limit: (\d+)", msg)
        met = _re.search(r"metric: ([^\s*]+)", msg)
        print(f"❌ TTS {model:30s} HTTP {r.status_code} | "
              f"{err.get('status') if isinstance(err,dict) else '?'} | "
              f"metric={(met.group(1).split('/')[-1] if met else '?')} | limit={lim.group(1) if lim else '?'}")
        if not lim:
            print("      ", msg[:230])


print("═══ MODEL ẢNH (chưa thử) ═══")
for m in ["gemini-3.1-flash-lite-image", "nano-banana-pro-preview",
          "gemini-omni-1.1-flash", "gemini-omni-flash-preview",
          "gemini-4-argon"]:
    try_image(m)
    time.sleep(2)

print("\n═══ MODEL TTS GEMINI ═══")
for m in ["gemini-3.8-flash-tts", "gemini-2.5-flash-preview-tts",
          "gemini-3.1-flash-tts-preview", "gemini-3.8-flash-lite-tts"]:
    try_tts(m)
    time.sleep(2)
