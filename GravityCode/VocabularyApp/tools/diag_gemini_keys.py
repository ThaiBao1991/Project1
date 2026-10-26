"""Chẩn đoán pool Gemini key: phân loại theo lỗi, không tiêu tốn quota nhiều."""
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

import requests
from ai.course_generator import _load_gemini_keys

URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"

keys = _load_gemini_keys()
print(f"Tổng key: {len(keys)}\n")

# Gom theo account
by_acct = {}
for k in keys:
    acct = (k.get("email") or "?").strip()
    by_acct.setdefault(acct, []).append(k)
print(f"Số account: {len(by_acct)}")
for a, ks in sorted(by_acct.items()):
    print(f"  {a:32s} {len(ks):3d} key  status={[x.get('status') for x in ks][:3]}")
print()

results = {"ok": [], "429": [], "dead": [], "403": [], "400_other": [], "err": []}
for i, k in enumerate(keys):
    raw = k.get("key") or ""
    email = k.get("email") or "?"
    try:
        r = requests.post(URL + f"?key={raw}",
                          headers={"Content-Type": "application/json"},
                          json={"contents": [{"parts": [{"text": "Hi"}]}],
                                "generationConfig": {"maxOutputTokens": 8}},
                          timeout=60)
        code = r.status_code
        msg = ""
        try:
            body = r.json()
            err = body.get("error", {}) if isinstance(body, dict) else {}
            msg = str(err.get("message", ""))[:150]
        except Exception:
            msg = r.text[:120]
        if code == 200:
            results["ok"].append(email)
            tag = "OK"
        elif code == 429:
            results["429"].append(email)
            tag = "429"
        elif code in (401, 403):
            if "service account" in msg.lower() or "deleted" in msg.lower():
                results["dead"].append(email)
                tag = "DEAD"
            else:
                results["403"].append(email)
                tag = "403"
        elif code == 400:
            results["400_other"].append(email)
            tag = "400"
        else:
            results["err"].append((email, code, msg))
            tag = f"ERR{code}"
    except Exception as e:
        results["err"].append((email, "EXC", str(e)[:80]))
        tag = "EXC"
    print(f"  [{i+1:2d}/{len(keys)}] {email:32s} {tag:6s} {msg[:110]}")
    time.sleep(0.5)

print("\n=== TỔNG KẾT ===")
for k, v in results.items():
    if isinstance(v, list) and v and isinstance(v[0], str):
        from collections import Counter
        c = Counter(v)
        print(f"{k:10s} {sum(c.values()):3d}  {dict(c)}")
    else:
        print(f"{k:10s} {len(v):3d}")
