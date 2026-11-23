# -*- coding: utf-8 -*-
"""tools/test_atomic_write.py — Test lớp bug "2 tiến trình ghi chung file".

BỐI CẢNH (17/11): `_atomic_write` / `atomic_write_json` / `save_index` dùng
tên file `.tmp` **CỐ ĐỊNH** ⇒ 2 tiến trình ghi cùng file:
    P1 mở tmp ("w" ⇒ truncate) rồi ghi lớn
    P2 mở tmp ("w" ⇒ truncate) cắt ngang dữ liệu đang ghi của P1
⇒ file cuối = JSON cụt / **0 byte** ⇒ MẤT TRẮNG khóa học (đã xảy ra: 3 khóa
0 byte, manifest "Extra data").

Test:
  A. Tên tmp PHẢI DUY NHẤT theo PID + thread (kiểm tra mã nguồn).
  B. 2 PROCESS thật ghi cùng file song song ⇒ file luôn JSON hợp lệ,
     không 0 byte, không "Extra data" (chạy nhiều vòng).
  C. `save_course` KHÔNG ghi đè khóa học đã có dữ liệu bằng bản rỗng.

Chạy:  python tools/test_atomic_write.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)


def _writer_script(path: str, tag: str, rounds: int) -> str:
    """Script con: ghi file liên tục bằng atomic write (tmp riêng theo PID)."""
    return f'''
import json, os, sys
sys.path.insert(0, {BASE!r})
from ai import course_db
path = {path!r}
payload = {{"tag": {tag!r}, "blob": ["x" * 200 for _ in range(300)]}}
for _ in range({rounds}):
    course_db._atomic_write(path, payload)
'''


def main() -> int:
    from ai import course_db

    results = []

    def ck(name, cond, detail=""):
        results.append((name, bool(cond), detail))

    # ── A. tên tmp duy nhất theo PID + thread ───────────────────────────────
    src = open(os.path.join(BASE, "ai", "course_db.py"), encoding="utf-8").read()
    src2 = open(os.path.join(BASE, "ai", "pipeline_store.py"), encoding="utf-8").read()
    src3 = open(os.path.join(BASE, "ai", "media_store.py"), encoding="utf-8").read()
    a1 = "tmp.{os.getpid()}" in src
    a2 = "tmp.{os.getpid()}" in src2
    a3 = "tmp.{os.getpid()}" in src3
    ck("course_db dùng tmp duy nhất theo PID", a1)
    ck("pipeline_store dùng tmp duy nhất theo PID", a2)
    ck("media_store dùng tmp duy nhất theo PID", a3)

    # ── B. 2 process ghi cùng file ⇒ luôn JSON hợp lệ ────────────────────
    tmp = tempfile.mkdtemp(prefix="vocab_atomic_")
    target = os.path.join(tmp, "course.json")
    script_a = os.path.join(tmp, "wa.py")
    script_b = os.path.join(tmp, "wb.py")
    open(script_a, "w", encoding="utf-8").write(_writer_script(target, "A", 40))
    open(script_b, "w", encoding="utf-8").write(_writer_script(target, "B", 40))

    ok_all = True
    bad = ""
    for _round in range(4):
        pa = subprocess.Popen([sys.executable, "-X", "utf8", script_a])
        pb = subprocess.Popen([sys.executable, "-X", "utf8", script_b])
        pa.wait(); pb.wait()
        try:
            size = os.path.getsize(target)
            with open(target, encoding="utf-8") as f:
                data = json.load(f)
            # File phải JSON hợp lệ, KHÔNG rỗng, và là 1 trong 2 bản ghi.
            if size <= 0 or not isinstance(data, dict) or data.get("tag") not in ("A", "B"):
                ok_all = False
                bad = f"vòng {_round}: size={size} data={str(data)[:60]}"
                break
        except Exception as e:
            ok_all = False
            bad = f"vòng {_round}: {type(e).__name__}: {e}"
            break
    ck("2 process ghi cùng file ⇒ JSON luôn hợp lệ", ok_all, bad)

    # dọn
    try:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    except Exception:
        pass

    # ── C. save_course không ghi đè bằng bản rỗng ─────────────────────────
    try:
        tmp2 = tempfile.mkdtemp(prefix="vocab_course_")
        orig_dir = course_db.COURSES_DIR
        course_db.COURSES_DIR = tmp2
        lang = "tiếng_test"
        # tạo khóa học có dữ liệu
        course_db.save_course(lang, {"days": [{"day": 1, "vocab": [
            {"word": "水", "meaning_vi": "nước"}]}], "plan": [{"day": 1}]})
        p = course_db.course_path(lang)
        size_before = os.path.getsize(p)
        # thử ghi bản RỖNG
        course_db.save_course(lang, {"days": []})
        size_after = os.path.getsize(p)
        kept = size_after == size_before and size_after > 0
        ck("save_course KHÔNG ghi đè bằng bản rỗng", kept,
           f"{size_before} → {size_after}")
        course_db.COURSES_DIR = orig_dir
        try:
            import shutil
            shutil.rmtree(tmp2, ignore_errors=True)
        except Exception:
            pass
    except Exception as e:
        ck("save_course KHÔNG ghi đè bằng bản rỗng", False,
           f"{type(e).__name__}: {e}")

    print("\n" + "=" * 62)
    ok = 0
    for name, passed, detail in results:
        mark = "PASS" if passed else "FAIL"
        if passed:
            ok += 1
        print(f"[{mark}] {name}" + (f"  — {detail}" if detail else ""))
    print("=" * 62)
    print(f"→ {ok}/{len(results)} PASS")
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
