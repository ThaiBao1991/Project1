# -*- coding: utf-8 -*-
"""tools/clean_english_vocab.py — Dọn từ vựng tiếng Anh không phù hợp.

VẤN ĐỀ: nguồn từ vựng có lẫn danh từ riêng/địa danh/slang/từ tục
(vd. ngày 650: puerto, shanghai, shitty, singh; 18 ngày khác có từ tục).

CÁCH SỬA:
  • Ngày 650: thay 4 từ bằng từ đúng chủ đề thuê nhà (landlord, deposit,
    shabby, tenant), xoá media ref cũ, tạo lại quiz từ vựng.
  • Các ngày khác: bỏ từ tục khỏi danh sách từ + bỏ câu quiz chứa từ đó.
  • KHÔNG đổi ngày, media của từ khác, mẫu câu/ngữ pháp/hội thoại.

CÁCH DÙNG:
  python -X utf8 tools/clean_english_vocab.py --dry-run
  python -X utf8 tools/clean_english_vocab.py
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CD = os.path.join(BASE, "data", "ai_courses")
SLUG = "tiếng_anh"

PROFANE = re.compile(
    r"\b(shit|shitty|fuck|fucking|fucked|bitch|bitches|cunt|cunts|asshole|"
    r"assholes|dick|dicks|cock|cocks|pussy|nigger|nigga|niggas|whore|slut|"
    r"bastard|bastards|crap|piss|bollocks|wanker|twat|prick)\b", re.I)

# Ngày 650 — chủ đề thuê nhà: thay từ rác bằng từ đúng chủ đề.
D650 = {
    "puerto": {
        "word": "landlord", "pronunciation": "ˈlænd.lɔːrd", "ipa": "/ˈlænd.lɔːrd/",
        "part_of_speech": "Danh từ", "pos": "n.",
        "meaning_vi": "chủ nhà (cho thuê)",
        "explanation": "Người sở hữu nhà/đất và cho người khác thuê.",
        "example_sentence": "The landlord agreed to fix the heating.",
        "example_meaning_vi": "Chủ nhà đồng ý sửa hệ thống sưởi.",
        "example_target": "The landlord agreed to fix the heating.",
        "example_vi": "Chủ nhà đồng ý sửa hệ thống sưởi.",
    },
    "shanghai": {
        "word": "deposit", "pronunciation": "dɪˈpɒz.ɪt", "ipa": "/dɪˈpɒz.ɪt/",
        "part_of_speech": "Danh từ", "pos": "n.",
        "meaning_vi": "tiền đặt cọc",
        "explanation": "Khoản tiền trả trước để giữ chỗ hoặc bảo đảm hợp đồng thuê.",
        "example_sentence": "We paid a two-month deposit for the apartment.",
        "example_meaning_vi": "Chúng tôi đã trả tiền đặt cọc hai tháng cho căn hộ.",
        "example_target": "We paid a two-month deposit for the apartment.",
        "example_vi": "Chúng tôi đã trả tiền đặt cọc hai tháng cho căn hộ.",
    },
    "shitty": {
        "word": "shabby", "pronunciation": "ˈʃæb.i", "ipa": "/ˈʃæb.i/",
        "part_of_speech": "Tính từ", "pos": "adj.",
        "meaning_vi": "tồi tàn, cũ kỹ",
        "explanation": "Miêu tả đồ vật/nhà cửa đã cũ và xuống cấp.",
        "example_sentence": "The apartment looked shabby but affordable.",
        "example_meaning_vi": "Căn hộ trông cũ kỹ nhưng giá phải chăng.",
        "example_target": "The apartment looked shabby but affordable.",
        "example_vi": "Căn hộ trông cũ kỹ nhưng giá phải chăng.",
    },
    "singh": {
        "word": "tenant", "pronunciation": "ˈten.ənt", "ipa": "/ˈten.ənt/",
        "part_of_speech": "Danh từ", "pos": "n.",
        "meaning_vi": "người thuê nhà",
        "explanation": "Người thuê nhà/đất từ chủ sở hữu.",
        "example_sentence": "The tenant signed a one-year lease.",
        "example_meaning_vi": "Người thuê đã ký hợp đồng thuê một năm.",
        "example_target": "The tenant signed a one-year lease.",
        "example_vi": "Người thuê đã ký hợp đồng thuê một năm.",
    },
}


def _replace_item(v: dict, new: dict) -> None:
    for k, val in new.items():
        v[k] = val
    v["image_ref"] = None
    v["audio_ref"] = None
    v["meaning_audio_ref"] = None
    v["image_prompt"] = None
    v["phonetic_note"] = ""
    v["syllables"] = []
    v["pitch_accent"] = ""
    v["rhymes"] = []
    v["etymology"] = ""
    v["sources"] = []


def _vocab_quiz(vocab: list, day: int) -> list:
    rnd = random.Random(f"en|{day}|vocab|v2")
    meanings = [str(v.get("meaning_vi") or "") for v in vocab]
    out = []
    for v in vocab:
        correct = str(v.get("meaning_vi") or "")
        distract = [m for m in meanings if m and m != correct]
        if len(distract) < 3:
            continue
        opts = [correct] + rnd.sample(distract, 3)
        rnd.shuffle(opts)
        out.append({"question": f"Từ 「{v.get('word')}」 có nghĩa là gì?",
                    "options": opts, "answer_index": opts.index(correct),
                    "explanation": f"{v.get('word')} — {correct}",
                    "_gen": True})
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    path = os.path.join(CD, SLUG, "course.json")
    course = json.load(open(path, encoding="utf-8"))
    replaced = removed = quiz_del = 0
    for d in course.get("days") or []:
        n = int(d.get("day") or 0)
        vocab = d.get("vocab") or []
        if n == 650:
            for v in vocab:
                old = str(v.get("word") or "").lower()
                if old in D650:
                    media = d.get("media") or {}
                    va = media.get("vocab_audio") or {}
                    va.pop(v.get("word"), None)
                    _replace_item(v, D650[old])
                    replaced += 1
            q = d.get("quiz") or {}
            q["vocab"] = _vocab_quiz(vocab, n)
            d["quiz"] = q
            continue
        keep = []
        for v in vocab:
            if PROFANE.search(str(v.get("word") or "")):
                media = d.get("media") or {}
                va = media.get("vocab_audio") or {}
                va.pop(v.get("word"), None)
                removed += 1
                continue
            keep.append(v)
        if len(keep) != len(vocab):
            d["vocab"] = keep
            q = d.get("quiz") or {}
            for cat, qs in list(q.items()):
                if not isinstance(qs, list):
                    continue
                nq = [x for x in qs
                      if not PROFANE.search(json.dumps(x, ensure_ascii=False))]
                quiz_del += len(qs) - len(nq)
                q[cat] = nq
    print(f"{SLUG}: thay {replaced} từ ngày 650 | bỏ {removed} từ tục | "
          f"xoá {quiz_del} câu quiz")
    if args.dry_run:
        print("   (DRY-RUN — chưa ghi)")
        return 0
    if not (replaced or removed or quiz_del):
        print("   không có gì để sửa")
        return 0
    course["updated_at"] = __import__("datetime").datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(course, f, ensure_ascii=False, indent=2)
    bak = path + ".bak_vocab"
    if not os.path.isfile(bak):
        try:
            os.replace(path, bak)
        except OSError:
            pass
    os.replace(tmp, path)
    print("   đã ghi course.json")
    import subprocess
    r = subprocess.run([sys.executable, "-X", "utf8",
                        "tools/export_days_keep_media.py", "--lang", SLUG],
                       cwd=BASE)
    return 0 if r.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
