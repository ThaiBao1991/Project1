"""
test_slug_canonical.py — Phase 3: canonical slug + get_available_languages gộp alias.

Dữ liệu test nằm trong TEMP (monkeypatch DATA_DIR/COURSES_DIR) — không đụng data thật.

Chạy: python tools/test_slug_canonical.py
"""
import json
import os
import sys
import tempfile

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from ai import paths as P  # noqa: E402
from ai import course_db  # noqa: E402
import database.database as db  # noqa: E402

PASSED = []


def ok(name):
    PASSED.append(name)
    print(f"[OK] {name}")
    return PASSED


# ── 1. canonical_slug cơ bản ──
assert P.canonical_slug("Nhật") == "tiếng_nhật"
assert P.canonical_slug("nhat") == "tiếng_nhật"
assert P.canonical_slug("JA") == "tiếng_nhật"
assert P.canonical_slug("Tiếng Nhật") == "tiếng_nhật"   # lang_slug là đủ
assert P.canonical_slug("Tiếng Anh") == "tiếng_anh"     # ngôn ngữ khác không đổi
ok("canonical_slug: alias (Nhật/nhat/japanese/ja/jp) → 'tiếng_nhật'")

# ── 2. course_db + media_store + database dùng canonical ──
assert os.path.basename(course_db.course_dir("Nhật")) == "tiếng_nhật"
from ai import media_store  # noqa: E402

with tempfile.TemporaryDirectory() as tmp:
    # Monkeypatch DATA_DIR cả 3 module về tmp — kiểm tra đường dẫn sinh ra
    old_p_data, old_db_data = P.DATA_DIR, db.DATA_DIR
    old_media, old_cours = media_store.MEDIA_DIR, course_db.COURSES_DIR
    try:
        P.DATA_DIR = tmp
        db.DATA_DIR = tmp
        media_store.MEDIA_DIR = os.path.join(tmp, "media")
        course_db.COURSES_DIR = os.path.join(tmp, "ai_courses")

        assert os.path.basename(course_db.course_dir("nhat")) == "tiếng_nhật"
        rel = media_store.rel_path_for("Nhật", 1, "x.webp")
        assert rel == "media/tiếng_nhật/d0001/x.webp", rel
        jp = db._get_json_path("nhật")
        assert os.path.basename(jp) == "tiếng_nhật.json", jp
        ok("course_dir/media rel_path/_get_json_path: 'Nhật' → slug chuẩn, hết lệch tên")
    finally:
        P.DATA_DIR, db.DATA_DIR = old_p_data, old_db_data
        media_store.MEDIA_DIR, course_db.COURSES_DIR = old_media, old_cours

# ── 3. get_available_languages: gộp Nhật + tiếng_nhật → 1 entry ──
with tempfile.TemporaryDirectory() as tmp:
    old_db_data = db.DATA_DIR
    db.DATA_DIR = tmp
    try:
        ai = os.path.join(tmp, "ai_courses")
        for slug in ("nhật", "tiếng_nhật", "tiếng_anh"):
            d = os.path.join(ai, slug)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "course.json"), "w", encoding="utf-8") as f:
                json.dump({"language": "Tiếng Nhật" if slug != "tiếng_anh" else "English"},
                          f, ensure_ascii=False)
        got = db.get_available_languages()
        # Format mới: list dict {display, slug, num_days} (App sắp xếp theo num_days)
        assert all(set(x) >= {"display", "slug", "num_days"} for x in got), got
        assert [x["display"] for x in got] == ["English", "Tiếng Nhật"], got
        ok("get_available_languages: alias 'nhật' bị gộp — dropdown còn 2 mục chuẩn")
    finally:
        db.DATA_DIR = old_db_data

# ── 4. alias KHÔNG có canonical → vẫn hiện (không mất khóa học) ──
with tempfile.TemporaryDirectory() as tmp:
    old_db_data = db.DATA_DIR
    db.DATA_DIR = tmp
    try:
        ai = os.path.join(tmp, "ai_courses")
        d = os.path.join(ai, "nhật")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(ai, "nhật", "course.json"), "w", encoding="utf-8") as f:
            json.dump({"language": "Nhật"}, f, ensure_ascii=False)
        got = db.get_available_languages()
        assert [x["display"] for x in got] == ["Tiếng Nhật"], got   # display từ slug chuẩn
        ok("alias không có canonical vẫn hiện nhưng display theo slug chuẩn")
    finally:
        db.DATA_DIR = old_db_data

# ── 5. file vocab trùng canonical file → chỉ 1 entry ──
with tempfile.TemporaryDirectory() as tmp:
    old_db_data = db.DATA_DIR
    db.DATA_DIR = tmp
    try:
        for name in ("nhật", "tiếng_nhật"):
            with open(os.path.join(tmp, f"{name}.json"), "w", encoding="utf-8") as f:
                json.dump({"vocabularies": [{"word": "あ"}]}, f, ensure_ascii=False)
        got = db.get_available_languages()
        assert [x["display"] for x in got] == ["Tiếng Nhật"], got
        ok("vocab file alias nhật.json + canonical tiếng_nhật.json → chỉ hiển thị 1")
    finally:
        db.DATA_DIR = old_db_data

# ── 6. web_slug_table: dedupe alias ──
with tempfile.TemporaryDirectory() as tmp:
    old_p_data = P.DATA_DIR
    P.DATA_DIR = tmp
    try:
        ai = os.path.join(tmp, "ai_courses")
        for slug in ("nhật", "tiếng_nhật"):
            d = os.path.join(ai, slug)
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, "course.json"), "w", encoding="utf-8").write("{}")
        rows = P.web_slug_table()
        assert len(rows) == 1 and rows[0]["slug"] == "tiếng_nhật", rows
        ok("web_slug_table (paths.js): alias bị bỏ, slug trỏ thư mục chuẩn")
    finally:
        P.DATA_DIR = old_p_data

print(f"\nKet qua: {len(PASSED)}/6 PASS")
if len(PASSED) < 6:
    sys.exit(1)
