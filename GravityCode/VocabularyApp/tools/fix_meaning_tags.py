# -*- coding: utf-8 -*-
"""tools/fix_meaning_tags.py — Sửa nghĩa tiếng Việt bị dính hậu tố ngôn ngữ.

BỐI CẢNH (đo thật 14/11): khóa **tiếng Nhật** có 792 nghĩa dạng
    "konpeito (por: ...)"  /  "smetana (rus:)"
- 134 nghĩa SAU KHI CẮT hậu tố ⇒ rỗng ⇒ không học được
- 244 nghĩa còn lại ⇒ không phải tiếng Việt (ví dụ "smetana" = kem Nga)
⇒ người học tiếng Nhật gặp từ không hiểu nghĩa.

CÁCH SỬA:
  ① Cắt hậu tố "(xxx: ...)" (tiếng nào cũng được).
  ② Từ nào sau khi cắt mà rỗng / không phải tiếng Việt ⇒ DỊCH LẠI bằng
     dịch lô 25 từ/request (0 quota, ~300 từ/giây).
  ③ Ghi lại course.json (atomic) + checkpoint content.

Chạy:
  python tools/fix_meaning_tags.py --lang tiếng_nhật          # xem trước
  python tools/fix_meaning_tags.py --lang tiếng_nhật --apply  # ghi thật
  python tools/fix_meaning_tags.py --all --apply               # mọi khóa
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai import course_db  # noqa: E402

# Hậu tố nguồn: "(rus: ...)" "(eng: ...)" ... (mọi mã ngôn ngữ)
TAG = re.compile(
    r"\s*\((rus|eng|deu|fra|spa|ita|kor|zho|vie|jpn|por|nld|pol|tur|dan|gre|heb|hin|ces|nor|swe|fin|ind|thai)\s*:[^)]*\)",
    re.IGNORECASE)
# Nghĩa tiếng Việt: có ít nhất 1 ký tự Việt (có dấu hoặc không dấu đặc trưng)
VI = re.compile(r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđĐÀÁẢÃẠĂÂÈÉÊÌÍÒÓÔƠÙÚƯĐ]")
LATIN_ONLY = re.compile(r"^[A-Za-zÀ-ÿĀ-ſ' \-]+$")


def _log(m):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {m}", flush=True)


def is_vietnamese(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    if VI.search(t):
        return True
    # chỉ chữ Latin ⇒ coi như không phải tiếng Việt
    return not LATIN_ONLY.match(t)


def clean(text: str) -> str:
    """Bỏ hậu tố (xxx: ...) và khoảng trắng thừa."""
    s = TAG.sub("", text or "")
    s = re.sub(r"\s{2,}", " ", s).strip(" ,;·-–—")
    return s


def translate_batch(words, src="auto"):
    """Dịch lô sang tiếng Việt (dùng lại hàm của fetch_offline_words)."""
    sys.path.insert(0, os.path.join(BASE, "tools"))
    try:
        from fetch_offline_words import _translate_batch
        return _translate_batch(words, src=src)
    except Exception as e:
        _log(f"⚠ không dịch được: {e}")
        return [""] * len(words)


def fix_language(lang: str, apply: bool) -> dict:
    path = course_db.course_path(lang)
    if not os.path.isfile(path):
        return {"lang": lang, "error": "không có course.json"}
    _log(f"đọc {os.path.basename(path)} …")
    with open(path, encoding="utf-8") as f:
        course = json.load(f)
    days = course.get("days") or []

    n_tag = n_fixed = n_need_tr = 0
    need = []          # (day, vocab, word)
    for d in days:
        for v in (d.get("vocab") or []):
            if not isinstance(v, dict):
                continue
            raw = str(v.get("meaning_vi") or "")
            has_tag = bool(TAG.search(raw))
            s = clean(raw) if has_tag else raw.strip()
            w = str(v.get("word") or "").strip()
            if has_tag:
                n_tag += 1
            if has_tag and is_vietnamese(s):
                v["meaning_vi"] = s
                n_fixed += 1
                continue
            # Nghĩa gốc là FALLBACK (rỗng hoặc đúng bằng từ) ⇒ dịch lại được
            # với bất kỳ bản dịch nào khác rỗng (vd "smetana" → "kem").
            is_fallback = (not s) or (s == w)
            # Nghĩa gốc CÓ nội dung nhưng toàn chữ Latin dài ≥ 6 ký tự và
            # không có dấu Việt ⇒ khả năng cao là nghĩa sai tiếng khác
            # ("smetana", "konpeito"). Nhưng tiếng Việt KHÔNG DẤU ("ba",
            # "to", "co", "khong") phải được giữ nguyên.
            suspect = (not is_fallback and len(s) >= 6
                       and not VI.search(s) and LATIN_ONLY.match(s))
            if (is_fallback or suspect) and w:
                need.append((d.get("day"), v, w, is_fallback))
    _log(f"  {lang}: {n_tag} nghĩa có hậu tố · cắt xong {n_fixed} "
         f"· cần dịch lại {len(need)}")

    if need and apply:
        iso = {"tiếng_nhật": "ja"}.get(lang, "auto")
        words = [w for _d, _v, w, _f in need]
        out = []
        t0 = time.time()
        for i in range(0, len(words), 25):
            chunk = words[i:i + 25]
            res = translate_batch(chunk, src=iso)
            # retry lô nào thiếu (API dịch hay lỗi mạng/rate-limit)
            for attempt in range(3):
                miss = [j for j, r in enumerate(res) if not (r or "").strip()]
                if not miss:
                    break
                time.sleep(1.5 * (attempt + 1))
                sub = translate_batch([chunk[j] for j in miss], src="auto")
                for j, r in zip(miss, sub):
                    res[j] = r
            out.extend(res)
            if (i // 25) % 20 == 0:
                _log(f"    dịch {min(i+25, len(words))}/{len(words)} "
                     f"({time.time()-t0:.0f}s)")
        n_tr = 0
        for (day, v, w, is_fb), tr in zip(need, out):
            tr = (tr or "").strip()
            # Nghĩa gốc là fallback ⇒ nhận bất kỳ bản dịch khác rỗng nào
            # (kể cả không dấu: "smetana" → "kem", "アイレン" → "Airen").
            # Nghĩa gốc có nội dung ⇒ chỉ nhận bản dịch CÓ dấu Việt.
            ok = bool(tr) and (tr != w) and (is_fb or suspect or is_vietnamese(tr))
            if ok:
                v["meaning_vi"] = tr
                n_tr += 1
            else:
                v["meaning_vi"] = clean(v.get("meaning_vi") or "") or w
        _log(f"  dịch lại được {n_tr}/{len(need)} từ")

    if apply and (n_fixed or need):
        course_db.save_course(lang, course, backup=True)
        # Đồng bộ checkpoint content (để pipeline không sinh lại cũ)
        try:
            from ai.pipeline_store import (STAGE_CONTENT, STATUS_DONE,
                                           save_checkpoint)
            for d in days:
                save_checkpoint(lang, STAGE_CONTENT,
                                {"title": d.get("title", ""),
                                 "vocab": d.get("vocab") or [],
                                 "sentence_patterns": [], "common_sentences": [],
                                 "grammar": d.get("grammar") or [],
                                 "source": d.get("source", "offline")},
                                day=d.get("day"), status=STATUS_DONE)
            _log("  ✓ đã đồng bộ checkpoint content")
        except Exception as e:
            _log(f"  ⚠ checkpoint: {e}")
        _log(f"  ✓ đã ghi {lang}")
    return {"lang": lang, "tag": n_tag, "cleaned": n_fixed,
            "retranslate": len(need), "days": len(days)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    CD = os.path.join(BASE, "data", "ai_courses")
    if args.lang:
        langs = [args.lang]
    elif args.all:
        langs = [s for s in sorted(os.listdir(CD))
                 if not s.startswith("_") and
                 os.path.isfile(os.path.join(CD, s, "course.json"))]
    else:
        langs = ["tiếng_nhật"]

    for lg in langs:
        r = fix_language(lg, args.apply)
        if r.get("error"):
            _log(f"⚠ {lg}: {r['error']}")
        else:
            print(f"  {lg}: tag={r['tag']} đã sạch={r['cleaned']} "
                  f"cần dịch={r['retranslate']} / {r['days']} ngày", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
