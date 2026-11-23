# -*- coding: utf-8 -*-
"""tools/test_statefile.py — kiểm tra kho trạng thái 2 bản (chống mất file).

Chạy: python -X utf8 tools/test_statefile.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import statefile  # noqa: E402

FAILS: list[str] = []


def check(name: str, ok: bool, extra: str = "") -> None:
    print(("PASS " if ok else "FAIL ") + name + (f" — {extra}" if extra else ""))
    if not ok:
        FAILS.append(name)


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        statefile.CANON = os.path.join(tmp, "canon")
        statefile.LEGACY = os.path.join(tmp, "legacy")
        statefile.HIST = os.path.join(statefile.CANON, "history")
        name = "finalize_done.json"
        canon = os.path.join(statefile.CANON, name)
        legacy = os.path.join(statefile.LEGACY, name)

        statefile.save(name, {"a": {"status": "done"}})
        check("save tạo bản chính", os.path.isfile(canon))
        check("save tạo bản sao", os.path.isfile(legacy))
        check("snapshot lịch sử", os.path.isdir(statefile.HIST)
              and len(os.listdir(statefile.HIST)) >= 1)

        # Mất bản chính → đọc vẫn ra dữ liệu và tự dựng lại bản chính.
        os.remove(canon)
        got = statefile.load(name)
        check("mất bản chính vẫn đọc được", got.get("a", {}).get("status") == "done")
        check("tự phục hồi bản chính", os.path.isfile(canon))

        # Mất bản sao → đọc vẫn ra dữ liệu và tự dựng lại bản sao.
        os.remove(legacy)
        got = statefile.load(name)
        check("mất bản sao vẫn đọc được", got.get("a", {}).get("status") == "done")
        check("tự phục hồi bản sao", os.path.isfile(legacy))

        # Bản cũ hơn không được ghi đè bản mới hơn (so sánh `at`, không dùng mtime).
        with open(legacy, "w", encoding="utf-8") as f:
            json.dump({"a": {"status": "stale"}}, f)
        os.utime(canon, (1, 1))
        got = statefile.load(name)
        check("bản không có 'at' không đè canon", got.get("a", {}).get("status") == "done")

        # Bản có `at` mới hơn thì thắng, kể cả khi mtime cũ.
        with open(legacy, "w", encoding="utf-8") as f:
            json.dump({"a": {"status": "newer", "at": "2030-01-01 00:00:00"}}, f)
        got = statefile.load(name)
        check("'at' mới hơn thắng", got.get("a", {}).get("status") == "newer")

        # Ghi nhiều lần không hỏng JSON và giữ nguyên khóa khác.
        statefile.save(name, {"a": {"status": "done"}, "b": {"status": "done"}})
        with open(canon, encoding="utf-8") as f:
            disk = json.load(f)
        check("ghi nhiều khóa", set(disk) == {"a", "b"})

    print(("→ FAIL " + ", ".join(FAILS)) if FAILS else "→ tất cả PASS")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
