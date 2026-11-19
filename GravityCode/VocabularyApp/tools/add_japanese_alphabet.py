# -*- coding: utf-8 -*-
"""tools/add_japanese_alphabet.py — Thêm bảng Hiragana/Katakana cho 2 ngày đầu.

VẤN ĐỀ: người mới vào khóa Nhật gặp ngay từ vựng あい/うえ… nhưng chưa có bài
giới thiệu hệ chữ cái. Công cụ này thêm section `alphabet` (web render thành
lưới 5 cột) vào:
  • Ngày 1: Hiragana 46 âm cơ bản.
  • Ngày 2: Katakana 46 âm cơ bản.

KHÔNG đổi vocab / media / ngày. Chạy lại nhiều lần vẫn idempotent (skip nếu
`alphabet` đã có).

CÁCH DÙNG:
  python -X utf8 tools/add_japanese_alphabet.py --dry-run
  python -X utf8 tools/add_japanese_alphabet.py
"""
from __future__ import annotations

import argparse
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CD = os.path.join(BASE, "data", "ai_courses")
SLUG = "tiếng_nhật"

HIRAGANA = [
    [("あ", "a"), ("い", "i"), ("う", "u"), ("え", "e"), ("お", "o")],
    [("か", "ka"), ("き", "ki"), ("く", "ku"), ("け", "ke"), ("こ", "ko")],
    [("さ", "sa"), ("し", "shi"), ("す", "su"), ("せ", "se"), ("そ", "so")],
    [("た", "ta"), ("ち", "chi"), ("つ", "tsu"), ("て", "te"), ("と", "to")],
    [("な", "na"), ("に", "ni"), ("ぬ", "nu"), ("ね", "ne"), ("の", "no")],
    [("は", "ha"), ("ひ", "hi"), ("ふ", "fu"), ("へ", "he"), ("ほ", "ho")],
    [("ま", "ma"), ("み", "mi"), ("む", "mu"), ("め", "me"), ("も", "mo")],
    [("や", "ya"), None, ("ゆ", "yu"), None, ("よ", "yo")],
    [("ら", "ra"), ("り", "ri"), ("る", "ru"), ("れ", "re"), ("ろ", "ro")],
    [("わ", "wa"), None, None, None, ("を", "wo")],
    [("ん", "n"), None, None, None, None],
]
KATAKANA = [
    [("ア", "a"), ("イ", "i"), ("ウ", "u"), ("エ", "e"), ("オ", "o")],
    [("カ", "ka"), ("キ", "ki"), ("ク", "ku"), ("ケ", "ke"), ("コ", "ko")],
    [("サ", "sa"), ("シ", "shi"), ("ス", "su"), ("セ", "se"), ("ソ", "so")],
    [("タ", "ta"), ("チ", "chi"), ("ツ", "tsu"), ("テ", "te"), ("ト", "to")],
    [("ナ", "na"), ("ニ", "ni"), ("ヌ", "nu"), ("ネ", "ne"), ("ノ", "no")],
    [("ハ", "ha"), ("ヒ", "hi"), ("フ", "fu"), ("ヘ", "he"), ("ホ", "ho")],
    [("マ", "ma"), ("ミ", "mi"), ("ム", "mu"), ("メ", "me"), ("モ", "mo")],
    [("ヤ", "ya"), None, ("ユ", "yu"), None, ("ヨ", "yo")],
    [("ラ", "ra"), ("リ", "ri"), ("ル", "ru"), ("レ", "re"), ("ロ", "ro")],
    [("ワ", "wa"), None, None, None, ("ヲ", "wo")],
    [("ン", "n"), None, None, None, None],
]


def _rows(grid: list) -> list:
    out = []
    for row in grid:
        for cell in row:
            if cell is None:
                out.append({"kana": "", "romaji": ""})
            else:
                out.append({"kana": cell[0], "romaji": cell[1]})
    return out


def _alphabet(title: str, note: str, script: str, grid: list) -> dict:
    return {"title": title, "note": note, "script": script, "rows": _rows(grid)}


HIRA = _alphabet(
    "Bảng chữ cái Hiragana — 46 âm cơ bản",
    "Học thuộc 46 chữ Hiragana trước khi ghép từ. Đọc từ trái sang phải; "
    "mỗi ô là chữ · romaji. Âm đục (が/ざ/だ/ば/ぱ) và âm ngắt sẽ học ở bài sau.",
    "Hiragana", HIRAGANA)
KATA = _alphabet(
    "Bảng chữ cái Katakana — 46 âm cơ bản",
    "Katakana dùng cho từ ngoại lai, tên người/nước ngoài và nhấn mạnh. "
    "Học theo đúng thứ tự 5 cột như Hiragana; âm đục học ở bài sau.",
    "Katakana", KATAKANA)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    path = os.path.join(CD, SLUG, "course.json")
    course = json.load(open(path, encoding="utf-8"))
    changed = 0
    for d in course.get("days") or []:
        n = int(d.get("day") or 0)
        if n == 1 and not d.get("alphabet"):
            d["alphabet"] = HIRA
            changed += 1
        elif n == 2 and not d.get("alphabet"):
            d["alphabet"] = KATA
            changed += 1
    print(f"{SLUG}: thêm alphabet cho {changed} ngày")
    if args.dry_run:
        print("   (DRY-RUN — chưa ghi)")
        return 0
    if not changed:
        print("   đã có alphabet — không ghi")
        return 0
    course["updated_at"] = __import__("datetime").datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(course, f, ensure_ascii=False, indent=2)
    bak = path + ".bak_alpha"
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
