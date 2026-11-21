# -*- coding: utf-8 -*-
"""tools/test_pipeline_daemon.py — test logic tự khởi động lại của daemon.

Không chạm pipeline thật: thay CHILDREN bằng lệnh python vô hại và đổi LOG_DIR
sang thư mục tạm.

Chạy: python -X utf8 tools/test_pipeline_daemon.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_daemon as d  # noqa: E402

FAILS: list[str] = []


def check(name: str, ok: bool, extra: str = "") -> None:
    print(("PASS " if ok else "FAIL ") + name + (f" — {extra}" if extra else ""))
    if not ok:
        FAILS.append(name)


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="vocab_daemon_")
    d.LOG_DIR = tmp
    d.LOG = os.path.join(tmp, "daemon.log")
    d.STATUS = os.path.join(tmp, "status.json")
    d.LOOP_SECONDS = 1
    d.DISK_LOW_GB = -1  # tắt disk guard trong test
    d.CHILDREN = {
        "long": ["-c", "import time; time.sleep(30)"],
        "quick": ["-c", "raise SystemExit(0)"],
    }

    procs: dict = {}
    meta: dict = {}
    d.supervise_once(procs, meta)
    check("bật đủ 2 con", all(p is not None for p in procs.values()))
    check("con dài còn sống", procs["long"].poll() is None)

    time.sleep(1.2)
    d.supervise_once(procs, meta)
    check("con thoát mã 0 bị hoãn 5 phút",
          meta["quick"].get("next_start", 0) > time.time() + 200,
          str(meta["quick"].get("next_start", 0) - time.time()))
    check("con thoát mã 0 không bị coi là restart",
          meta["quick"].get("restarts", 0) == 0)

    # Giết con dài ⇒ vòng sau phát hiện, rồi bật lại (bỏ qua backoff trong test).
    procs["long"].kill()
    procs["long"].wait()
    time.sleep(0.3)
    d.supervise_once(procs, meta)
    check("con chết bất thường được restart", meta["long"].get("restarts") == 1)
    meta["long"]["next_start"] = 0
    d.supervise_once(procs, meta)
    check("con được bật lại", procs["long"] is not None
          and procs["long"].poll() is None)

    d.write_status(procs, meta)
    with open(d.STATUS, encoding="utf-8") as f:
        st = json.load(f)
    check("status có disk + children", "disk" in st and "long" in st["children"])
    check("status báo alive", st["children"]["long"]["alive"] is True)

    for p in procs.values():
        if p and p.poll() is None:
            p.kill()
    print(("→ FAIL " + ", ".join(FAILS)) if FAILS else "→ tất cả PASS")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
