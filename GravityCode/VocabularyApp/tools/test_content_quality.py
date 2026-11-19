# -*- coding: utf-8 -*-
"""tools/test_content_quality.py — Test case chất lượng nội dung 8 khóa.

Kiểm tra trên SẢN PHẨM WEB (`web/data/<slug>/day/*.json`) + course.json:

  1. Tiếng Anh không lẫn chữ Hàn/Trung trong BẤT KỲ trường nào.
  2. Tiếng Anh có IPA cho ≥97% từ vựng; `pronunciation` không còn dấu `/`.
  3. Tiếng Anh ngày 1 bắt đầu bằng từ đơn giản (≤5 ký tự, chữ thường).
  4. Tiếng Nhật ngày 1 có bảng Hiragana 46 âm; ngày 2 có Katakana 46 âm.
  5. Mọi ngày của 7 khóa đã enrich có đủ: ≥4 mẫu câu, ≥5 câu thông dụng,
     ≥2 ngữ pháp, ≥1 hội thoại, ≥3 quiz ngữ pháp, ≥3 quiz thông dụng.
  6. Không còn hội thoại template `を 使います` / `は 何ですか`.
  7. Câu/mẫu câu/hội thoại đúng hệ chữ ngôn ngữ đích (dùng validator của
     `tools/enrich_course_content.py`).
  8. Tiếng Trung được đánh dấu PENDING cho tới khi watcher enrich xong.

CÁCH DÙNG:
  python -X utf8 tools/test_content_quality.py
  python -X utf8 tools/test_content_quality.py --lang tiếng_anh
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from tools.enrich_course_content import _valid_target  # noqa: E402

WEB = os.path.join(BASE, "web", "data")
CD = os.path.join(BASE, "data", "ai_courses")
LANGS = ["tiếng_nhật", "tiếng_anh", "tiếng_hàn_quốc", "tiếng_nga",
         "tiếng_pháp", "tiếng_tây_ban_nha", "tiếng_đức"]
PENDING = ["tiếng_trung"]
HANGUL = re.compile(r"[\uac00-\ud7af]")
HAN = re.compile(r"[\u4e00-\u9fff]")
PROFANE = re.compile(
    r"\b(shit|shitty|fuck|fucking|fucked|bitch|bitches|cunt|cunts|asshole|"
    r"assholes|dick|dicks|cock|cocks|pussy|nigger|nigga|niggas|whore|slut|"
    r"bastard|bastards|crap|piss|bollocks|wanker|twat|prick)\b", re.I)
FAILS = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(("PASS " if ok else "FAIL ") + name + ((" — " + detail) if detail else ""))
    if not ok:
        FAILS.append(name)


def load_days(slug: str):
    d = os.path.join(WEB, slug, "day")
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".json"):
            yield fn, json.load(open(os.path.join(d, fn), encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="all")
    args = ap.parse_args()
    langs = LANGS if args.lang == "all" else [args.lang]

    # ── Tiếng Anh ──
    if "tiếng_anh" in langs:
        bad = 0
        total = ipa = slash = 0
        first_words = []
        for fn, j in load_days("tiếng_anh"):
            s = json.dumps(j, ensure_ascii=False)
            if HANGUL.search(s) or HAN.search(s):
                bad += 1
            for v in j.get("vocab") or []:
                total += 1
                if str(v.get("ipa") or "").strip():
                    ipa += 1
                p = str(v.get("pronunciation") or "")
                if p.startswith("/") or p.endswith("/"):
                    slash += 1
            if fn == "0001.json":
                first_words = [str(v.get("word") or "") for v in (j.get("vocab") or [])]
        check("Anh: không lẫn chữ Hàn/Trung", bad == 0, f"{bad} ngày dính")
        check("Anh: IPA ≥97% từ vựng", total > 0 and ipa / total >= 0.97,
              f"{ipa}/{total} = {ipa/max(1,total):.2%}")
        check("Anh: pronunciation không có dấu /", slash == 0, f"{slash} mục")
        prof = 0
        for _fn, j in load_days("tiếng_anh"):
            for v in j.get("vocab") or []:
                if PROFANE.search(str(v.get("word") or "")):
                    prof += 1
        check("Anh: không còn từ tục trong từ vựng", prof == 0, f"{prof} từ")
        check("Anh: ngày 1 từ đơn giản", bool(first_words) and all(
            len(w) <= 5 and w == w.lower() and w.isalpha() for w in first_words),
            str(first_words))

    # ── Tiếng Nhật ──
    if "tiếng_nhật" in langs:
        d1 = json.load(open(os.path.join(WEB, "tiếng_nhật", "day", "0001.json"),
                            encoding="utf-8"))
        d2 = json.load(open(os.path.join(WEB, "tiếng_nhật", "day", "0002.json"),
                            encoding="utf-8"))
        a1 = (d1.get("alphabet") or {}).get("rows") or []
        a2 = (d2.get("alphabet") or {}).get("rows") or []
        k1 = [r.get("kana") for r in a1 if r.get("kana")]
        k2 = [r.get("kana") for r in a2 if r.get("kana")]
        check("Nhật: ngày 1 có 46 Hiragana", len(k1) == 46 and k1[:5] == ["あ", "い", "う", "え", "お"],
              f"{len(k1)} kana")
        check("Nhật: ngày 2 có 46 Katakana", len(k2) == 46 and k2[:5] == ["ア", "イ", "ウ", "エ", "オ"],
              f"{len(k2)} kana")
        kana_ok = all(re.search(r"[\u3040-\u30ff]", str(v.get("word") or ""))
                      for v in (d1.get("vocab") or []))
        check("Nhật: từ vựng ngày 1 dùng kana", kana_ok)

    # ── Cấu trúc nội dung 7 khóa ──
    min_bad = {k: 0 for k in ("pat", "com", "gram", "dia", "qg", "qc")}
    template = 0
    script_bad = 0
    n_days = 0
    for slug in langs:
        for _fn, j in load_days(slug):
            n_days += 1
            if len(j.get("sentence_patterns") or []) < 4:
                min_bad["pat"] += 1
            if len(j.get("common_sentences") or []) < 5:
                min_bad["com"] += 1
            if len(j.get("grammar") or []) < 2:
                min_bad["gram"] += 1
            if len(j.get("dialogue") or []) < 1:
                min_bad["dia"] += 1
            q = j.get("quiz") or {}
            if len(q.get("grammar") or []) < 3:
                min_bad["qg"] += 1
            if len(q.get("common") or []) < 3:
                min_bad["qc"] += 1
            for dl in j.get("dialogue") or []:
                txt = " ".join(str(t.get("line_target") or "") for t in (dl.get("turns") or []))
                if "を 使います" in txt or "は 何ですか" in txt:
                    template += 1
            for p in j.get("sentence_patterns") or []:
                if not _valid_target(slug, p.get("example_sentence")):
                    script_bad += 1
            for c in j.get("common_sentences") or []:
                if not _valid_target(slug, c.get("sentence")):
                    script_bad += 1
            for dl in j.get("dialogue") or []:
                for t in dl.get("turns") or []:
                    if not _valid_target(slug, t.get("line_target")):
                        script_bad += 1
    check("7 khóa: đủ mẫu câu/câu thông dụng/ngữ pháp/hội thoại/quiz",
          all(v == 0 for v in min_bad.values()), f"{n_days} ngày · {min_bad}")
    check("7 khóa: không còn hội thoại template", template == 0, f"{template} mục")
    check("7 khóa: câu đúng hệ chữ ngôn ngữ đích", script_bad == 0, f"{script_bad} mục")

    for slug in PENDING:
        done = os.path.isfile(os.path.join(BASE, "data", "logs",
                                           "enrich_after_finalize_done.json"))
        print(("PASS " if not done else "INFO ") + f"{slug}: "
              + ("đang chờ pipeline/finalize" if not done else "đã enrich xong"))

    print("\n" + ("✅ TẤT CẢ PASS" if not FAILS else f"❌ {len(FAILS)} FAIL: {FAILS}"))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
