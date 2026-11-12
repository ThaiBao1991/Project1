# -*- coding: utf-8 -*-
"""tools/test_offline_content.py — Test nguồn nội dung OFFLINE (Gói 6, 2026-11-12).

Lý do: quota Gemini cạn (197 key/20 account hết quota/ngày) ⇒ cần nội dung
KHÔNG cần AI: EDICT (từ điển) + Wiktionary (nghĩa tiếng Việt) + bảng ngữ pháp
tự soạn + hội thoại/trắc nghiệm template.

7 case (không gọi mạng — dùng cache sẵn có):
  1. Bảng chữ cái: đúng 92 kana, có IPA + nghĩa + mẹo phát âm.
  2. EDICT đọc được (nếu đã tải) + từ Nhật thật.
  3. Từ được xếp TỪ THẤP LÊN CAO: 0 kanji → 1 kanji → 2 kanji.
  4. build_offline_day(1) = bảng chữ cái, có vocab + grammar + dialogue + quiz.
  5. Ngày sau = từ vựng, đủ field v4 (word/pronunciation/ipa/meaning_vi/example).
  6. Quiz hợp lệ: có đáp án trong khoảng options.
  7. Hội thoại có ≥ 2 lượt và dùng từ của ngày.
"""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai import offline_content as oc  # noqa: E402

PASS = [0]
FAIL = [0]


def ck(name, cond, detail=""):
    if cond:
        PASS[0] += 1
        print(f"[OK] {name}")
    else:
        FAIL[0] += 1
        print(f"[FAIL] {name} — {detail!r}")


def main() -> int:
    print("\n=== 1. bảng chữ cái ===")
    rows = oc.KANA_ROWS
    ck("92 kana (46 hira + 46 kata)", len(rows) == 92, len(rows))
    ck("mỗi kana có romaji + IPA + nghĩa Việt + mẹo",
       all(r[1] and r[2] and r[3] and r[4] for r in rows), "")
    kv = oc.build_kana_vocab()
    ck("vocab kana đủ field v4",
       all(k.get("word") and k.get("ipa") and k.get("meaning_vi") for k in kv), "")

    print("\n=== 2-3. EDICT + thứ tự độ khó ===")
    edict = oc.load_edict()
    if not edict:
        ck("EDICT đã tải", False, "chạy tools/fetch_offline_sources.py")
    else:
        ck("EDICT đọc được (>10.000 mục)", len(edict) > 10000, len(edict))
        pool = oc.select_words(edict, limit=300)
        ck("có từ chọn", len(pool) > 50, len(pool))
        seq = [oc.difficulty(w, (edict.get(w) or {}).get("reading") or "")
               for w in pool[:60]]
        ck("thứ tự TĂNG DẦN độ khó (không lùi)",
           all(seq[i] <= seq[i + 1] for i in range(len(seq) - 1)),
           seq[:12])
        ck("bắt đầu bằng từ 0 kanji (kana thuần)",
           all(oc.difficulty(w, (edict.get(w) or {}).get("reading") or "")[0] == 0
               for w in pool[:5]), pool[:5])

    print("\n=== 4-7. sinh 1 ngày offline ===")
    d1 = oc.build_offline_day(1)
    ck("ngày 1 = bảng chữ cái", "chữ cái" in d1["title"], d1["title"])
    ck("ngày 1 có vocab 10 từ", len(d1["vocab"]) == 10, len(d1["vocab"]))
    ck("ngày 1 có ngữ pháp", len(d1["grammar"]) >= 1, len(d1["grammar"]))
    ck("ngày 1 có hội thoại", len(d1["dialogue"]) == 1, len(d1["dialogue"]))
    ck("ngày 1 có quiz", len(d1["quiz"]["vocab"]) >= 4, len(d1["quiz"]["vocab"]))

    d12 = oc.build_offline_day(12)
    ck("ngày 12 = từ vựng (không phải kana)", "Từ vựng" in d12["title"], d12["title"])
    v = d12["vocab"][0] if d12["vocab"] else {}
    ck("từ có field v4 đầy đủ",
       all(v.get(k) for k in ("word", "pronunciation", "ipa", "meaning_vi",
                              "example_sentence", "example_meaning_vi")),
       list(v.keys()))
    ck("nghĩa có nội dung", len(v.get("meaning_vi") or "") > 2, v.get("meaning_vi"))

    qs = d12["quiz"]["vocab"]
    ok_q = all(0 <= q.get("answer_index", -1) < len(q.get("options") or [])
               and len(q.get("options") or []) >= 2 for q in qs)
    ck("quiz hợp lệ (đáp án trong khoảng)", ok_q, qs[:1])
    dl = (d12["dialogue"] or [{}])[0]
    ck("hội thoại ≥ 2 lượt", len(dl.get("turns") or []) >= 2, len(dl.get("turns") or []))
    words_in_lesson = {x["word"] for x in d12["vocab"]}
    turns_text = " ".join(t.get("line_target", "") for t in (dl.get("turns") or []))
    ck("hội thoại dùng từ của ngày",
       any(w in turns_text for w in words_in_lesson), turns_text[:80])

    print(f"\nKết quả: {PASS[0]} PASS / {FAIL[0]} FAIL (tổng {PASS[0] + FAIL[0]})")
    return 1 if FAIL[0] else 0


if __name__ == "__main__":
    sys.exit(main())
