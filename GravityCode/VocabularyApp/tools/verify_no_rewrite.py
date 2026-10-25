"""Verify Phase 2: get_course() KHÔNG ghi lại file course.json lớn."""
import hashlib
import os
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)

from ai import course_db
from ai.media_schema import COURSE_FORMAT_VERSION


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


langs = sorted(os.listdir(course_db.COURSES_DIR))
langs = [l for l in langs if not l.startswith("_")
         and os.path.isfile(os.path.join(course_db.COURSES_DIR, l, "course.json"))]

print(f"Courses found: {len(langs)}")
ok = True
for slug in langs:
    p = os.path.join(course_db.COURSES_DIR, slug, "course.json")
    before = sha(p)
    mtime_before = os.path.getmtime(p)
    size = os.path.getsize(p)

    c = course_db.get_course(slug)
    if c is None:
        print(f"  ❌ {slug}: get_course() trả None")
        ok = False
        continue

    after = sha(p)
    mtime_after = os.path.getmtime(p)
    changed = before != after or mtime_before != mtime_after

    days = c.get("days", [])
    v4 = sum(1 for d in days if d.get("format_version") == 4)
    has_ipa = sum(1 for d in days for v in (d.get("vocab") or []) if v.get("ipa"))
    has_dialogue_key = sum(1 for d in days if "dialogue" in d)
    n_vocab = sum(len(d.get("vocab") or []) for d in days)

    flag = "CHANGED ⚠" if changed else "unchanged ✓"
    print(f"  {slug:22s} {size/1e6:6.1f}MB days={len(days):4d} vocab={n_vocab:5d} "
          f"v4days={v4:4d} ipa={has_ipa:5d} dlg_key={has_dialogue_key:4d}  {flag}")
    if changed:
        ok = False

print()
print("RESULT:", "PASS — không file nào bị ghi lại" if ok else "FAIL — có file bị ghi lại")
sys.exit(0 if ok else 1)
