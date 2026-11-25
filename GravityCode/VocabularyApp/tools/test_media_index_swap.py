# -*- coding: utf-8 -*-
"""tools/test_media_index_swap.py — test tách/gộp manifest theo khóa.

Chạy: python -X utf8 tools/test_media_index_swap.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import media_index_swap as mis  # noqa: E402

FAILS: list[str] = []


def check(name: str, ok: bool, extra: str = "") -> None:
    print(("PASS " if ok else "FAIL ") + name + (f" — {extra}" if extra else ""))
    if not ok:
        FAILS.append(name)


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="vocab_idx_")
    mis.INDEX = os.path.join(tmp, "index.json")
    mis.FULL = os.path.join(tmp, "index_full.json")
    items = {
        "m_a": {"id": "m_a", "lang": "tiếng_nga", "rel_path": "media/x/a.webp"},
        "m_b": {"id": "m_b", "lang": "tiếng_pháp", "rel_path": "media/x/b.webp"},
        "m_c": {"id": "m_c", "lang": "tiếng_nga", "rel_path": "media/x/c.webp"},
    }
    with open(mis.INDEX, "w", encoding="utf-8") as f:
        json.dump({"format_version": 1, "items": items}, f, ensure_ascii=False)

    check("begin trả True", mis.begin("tiếng_nga") is True)
    check("full backup tồn tại", os.path.isfile(mis.FULL))
    with open(mis.INDEX, encoding="utf-8") as f:
        shard = json.load(f)["items"]
    check("shard chỉ còn khóa Nga", set(shard) == {"m_a", "m_c"})
    check("begin lần 2 là no-op", mis.begin("tiếng_nga") is False)

    # giả lập pipeline thêm entry mới rồi gộp
    shard["m_d"] = {"id": "m_d", "lang": "tiếng_nga", "rel_path": "media/x/d.webp"}
    with open(mis.INDEX, "w", encoding="utf-8") as f:
        json.dump({"format_version": 1, "items": shard}, f, ensure_ascii=False)
    check("end trả True", mis.end("tiếng_nga") is True)
    check("đã xoá full backup", not os.path.isfile(mis.FULL))
    with open(mis.INDEX, encoding="utf-8") as f:
        merged = json.load(f)["items"]
    check("gộp đủ 4 entry", set(merged) == {"m_a", "m_b", "m_c", "m_d"})
    check("entry khóa khác còn nguyên",
          merged["m_b"]["rel_path"] == "media/x/b.webp")
    check("end khi không shard là no-op", mis.end("tiếng_nga") is False)

    print(("→ FAIL " + ", ".join(FAILS)) if FAILS else "→ tất cả PASS")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
