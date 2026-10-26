"""Liệt kê model Gemini còn sống + kiểm tra model nào sinh được ảnh."""
import json
import os
import sys

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

r = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={raw}&pageSize=1000",
                 timeout=60)
print("HTTP", r.status_code)
if r.status_code != 200:
    print(r.text[:400])
    sys.exit(1)
data = r.json()
models = data.get("models", [])
print(f"Tổng model: {len(models)}\n")

print(f"{'name':48s} {'methods':46s} {'in':>6s} {'out':>6s}")
print("-" * 112)
img_candidates = []
for m in sorted(models, key=lambda x: x.get("name", "")):
    name = m.get("name", "").split("/")[-1]
    meth = ",".join(m.get("supportedGenerationMethods", []))
    lim = m.get("inputTokenLimit") or 0
    out = m.get("outputTokenLimit") or 0
    print(f"{name:48s} {meth[:46]:46s} {lim:6d} {out:6d}")
    if "generateContent" in meth:
        img_candidates.append(name)

print("\nModel hỗ trợ generateContent:", len(img_candidates))
print(", ".join(img_candidates))
