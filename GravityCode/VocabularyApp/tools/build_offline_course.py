# -*- coding: utf-8 -*-
"""tools/build_offline_course.py — Dựng khóa học Nhật KHÔNG CẦN Gemini.

Lợi ích: quota Gemini cạn (197 key/20 account hết quota/ngày) ⇒ không sinh
được nội dung bằng AI. Tool này dựng nội dung từ nguồn OFFLINE:
  • 92 kana (46 hiragana + 46 katakana) — bảng chữ cái, có IPA + nghĩa Việt
  • EDICT2 (JMdict) — từ vựng, xếp theo độ khó tăng dần (1 kana → 2 kanji)
  • Wiktionary cache — nghĩa TIẾNG VIỆT (không tốn quota AI)
  • Bảng ngữ pháp N5→N3 tự soạn (ai/offline_grammar.py)
  • Hội thoại micro 4 lượt + trắc nghiệm đảo nghĩa (template)

Kết quả ghi ĐÚNG định dạng course.json + checkpoint (content/quiz/dialogue) để
pipeline/media chạy tiếp (bù ảnh + âm thanh) và web hiển thị ngay.

Cách dùng:
  python tools/fetch_wiktionary_vi.py --limit 1200     # 1) tải nghĩa Việt (nền)
  python tools/build_offline_course.py --lang tiếng_nhật --days 200
  python tools/build_offline_course.py --lang tiếng_nhật --days 200 --apply
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai import course_db, offline_content, offline_grammar  # noqa: E402
from ai.pipeline_store import (STAGE_CONTENT, STAGE_DIALOGUE,  # noqa: E402
                               STAGE_QUIZ_AB, STAGE_QUIZ_CD, STATUS_DONE,
                               save_checkpoint)

WORDS_PER_DAY = 10
KANA_DAYS = 10          # 10 ngày đầu: bảng chữ cái (92 kana / 10 từ)

# 6 chặng giáo trình (N5 → "như người bản xứ"). Tỉ lệ ngày chuẩn hoá theo tổng
# số ngày yêu cầu ⇒ mở rộng 1.260 → 2.520+ ngày vẫn đúng tỉ lệ chặng.
PHASES = (
    ("Vỡ lòng chữ cái & phát âm", 60),
    ("Ghép âm & Từ đơn sinh tồn", 90),
    ("Sơ cấp đời sống", 280),
    ("Trung cấp công việc", 350),
    ("Cao cấp học thuật", 300),
    ("Như người bản xứ", 180),
)
LEVELS = ("N5", "N5", "N4", "N3", "N2", "N1")


def phase_for_day(day: int, total_days: int) -> tuple:
    """(tên chặng, cấp độ, thứ tự chặng) cho ngày N theo tỉ lệ 6 chặng."""
    total_w = sum(x[1] for x in PHASES)
    acc = 0
    for i, (name, w) in enumerate(PHASES, 1):
        acc += max(1, round(w * max(1, total_days) / total_w))
        if day <= acc:
            return name, LEVELS[i - 1], i
    return PHASES[-1][0], LEVELS[-1], len(PHASES)


def build_days(days: int, wiki: dict, edict: dict) -> list:
    kana = offline_content.build_kana_vocab()
    words = offline_content.select_words(edict, limit=max(60, days * WORDS_PER_DAY))
    out = []
    for d in range(1, days + 1):
        _ph, _lvl, _ord = phase_for_day(d, days)
        if d <= KANA_DAYS:
            chunk = kana[(d - 1) * WORDS_PER_DAY:(d - 1) * WORDS_PER_DAY + WORDS_PER_DAY]
            phase = f"{_ph} (offline)"
            title = f"Bảng chữ cái — Ngày {d}"
        else:
            i = (d - KANA_DAYS - 1) * WORDS_PER_DAY
            chunk = words[i:i + WORDS_PER_DAY]
            phase = f"{_ph} (offline)"
            title = f"{_ph} — Ngày {d}"
        vocab = []
        for w in chunk:
            if isinstance(w, dict):
                vocab.append(w)
            else:
                info = edict.get(w) or {}
                vocab.append(offline_content.build_vocab_item(w, info, wiki))
        gram = offline_grammar.grammar_for_day(d)
        dlg = offline_content.build_dialogue(vocab, topic=title)
        quiz = offline_content.build_quiz(vocab)
        out.append({
            "day": d, "title": title, "phase": phase, "level": _lvl,
            "topic": title, "words": [v.get("word") for v in vocab],
            "format_version": 4, "vocab": vocab,
            "sentence_patterns": [], "common_sentences": [],
            "grammar": gram, "dialogue": dlg,
            "quiz": quiz, "source": "offline",
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="tiếng_nhật")
    ap.add_argument("--days", type=int, default=200)
    ap.add_argument("--apply", action="store_true", help="ghi thật (mặc định: dry-run)")
    args = ap.parse_args()

    t0 = time.time()
    edict = offline_content.load_edict()
    print(f"EDICT2: {len(edict)} mục")
    if not edict:
        print("⚠ Chưa có data/offline_src/edict2.gz — chạy tools/fetch_offline_sources.py")
        return 1
    wiki = offline_content.load_wiki_cache()
    print(f"Wiktionary cache: {len(wiki)} từ có nghĩa tiếng Việt")

    day_list = build_days(args.days, wiki, edict)
    n_words = sum(len(d["vocab"]) for d in day_list)
    n_uniq = len({v["word"] for d in day_list for v in d["vocab"]})
    n_vi = sum(1 for d in day_list for v in d["vocab"]
               if v.get("meaning_vi") and not str(v["meaning_vi"]).startswith("[EN]"))
    n_quiz = sum(sum(len(x) for x in (d.get("quiz") or {}).values()) for d in day_list)
    n_dlg = sum(len(d.get("dialogue") or []) for d in day_list)
    print(f"\n=== DRY-RUN ===")
    print(f"  ngày        : {len(day_list)}")
    print(f"  từ vựng    : {n_words} (unique {n_uniq})")
    print(f"  nghĩa Việt  : {n_vi}/{n_words} ({n_vi * 100 // max(1, n_words)}%)")
    print(f"  trắc nghiệm : {n_quiz} câu · hội thoại: {n_dlg} bài")
    print(f"  thời gian   : {time.time() - t0:.1f}s")
    for d in day_list[:3] + day_list[-1:]:
        v = d["vocab"][0] if d["vocab"] else {}
        print(f"   · ngày {d['day']:3} | {v.get('word','?'):6} | "
              f"{str(v.get('meaning_vi'))[:38]}")

    if not args.apply:
        print("\nℹ️  DRY-RUN — thêm --apply để ghi vào course.json + checkpoint.")
        return 0

    course = course_db.get_course(args.lang) or {}
    course.setdefault("language", args.lang)
    course["level"] = course.get("level") or "N5"
    course["source"] = "offline"
    old = {int(d.get("day", 0)): d for d in (course.get("days") or [])}
    merged = []
    for d in day_list:
        prev = old.get(d["day"])
        if prev and prev.get("source") != "offline":
            # giữ bản AI (đã sinh, có media) — chỉ dùng lại khi ngày đó chưa
            # có nội dung nguồn offline (để lần chạy sau có nghĩa Việt mới
            # thì cập nhật được).
            d = dict(prev)
        merged.append(d)
    for d in old.values():
        if int(d.get("day", 0)) > len(day_list):
            merged.append(d)
    merged.sort(key=lambda d: int(d.get("day", 0)))
    course["days"] = merged
    course["total_days"] = len(merged)
    course_db.save_course(args.lang, course, backup=True)

    for d in day_list:
        save_checkpoint(args.lang, STAGE_CONTENT,
                        {"title": d["title"], "vocab": d["vocab"],
                         "sentence_patterns": [], "common_sentences": [],
                         "grammar": d["grammar"], "source": "offline"},
                        day=d["day"], status=STATUS_DONE)
        save_checkpoint(args.lang, STAGE_QUIZ_AB,
                        {"vocab_quiz": d["quiz"]["vocab"],
                         "pattern_quiz": d["quiz"]["pattern"]},
                        day=d["day"], status=STATUS_DONE)
        save_checkpoint(args.lang, STAGE_QUIZ_CD,
                        {"common_quiz": [], "grammar_quiz": []},
                        day=d["day"], status=STATUS_DONE)
        save_checkpoint(args.lang, STAGE_DIALOGUE,
                        {"dialogues": d["dialogue"], "source": "offline"},
                        day=d["day"], status=STATUS_DONE)
    print(f"\n✅ Đã ghi {len(merged)} ngày vào {course_db.course_path(args.lang)} "
          f"(+ checkpoint content/quiz/dialogue)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
