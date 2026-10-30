"""
course_db.py — Database khóa học AI cho VocabularyApp
Lưu theo kiểu tương tự AskCpl (session.json + dữ liệu JSON từng phần):
  data/ai_courses/<ngon_ngu>/course.json     → toàn bộ bài học theo ngày
  data/ai_courses/<ngon_ngu>/progress.json   → tiến độ học, điểm trắc nghiệm
Ghi file đều dùng kiểu atomic (tmp + os.replace) để không hỏng dữ liệu.
"""

import json

from ai.paths import canonical_slug, lang_slug
import os
import threading
from datetime import datetime

from ai.media_schema import (
    COURSE_FORMAT_VERSION,
    LEGACY_FORMAT_VERSION,
    apply_v4_defaults_in_memory,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COURSES_DIR = os.path.join(BASE_DIR, "data", "ai_courses")

# Khoá ghi file — pipeline chạy nhiều ngày SONG SONG, mỗi ngày ghi course.json
# ⇒ cần serialize để không ghi đè lẫn nhau.
_WRITE_LOCK = threading.RLock()


def _atomic_write(path: str, data: dict):
    with _WRITE_LOCK:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)




def course_dir(language: str) -> str:
    # canonical_slug: 'Nhật'/'ja' → 'tiếng_nhật' — hết split-brain khóa học.
    return os.path.join(COURSES_DIR, canonical_slug(language))


def course_path(language: str) -> str:
    return os.path.join(course_dir(language), "course.json")


def progress_path(language: str) -> str:
    return os.path.join(course_dir(language), "progress.json")


# ─── Course ────────────────────────────────────────────────────────────────────

def get_course(language: str, *, apply_v4: bool = True, persist: bool = None):
    """Trả về dict khóa học hoặc None nếu chưa có.

    Migration 2 tầng:
      • TẦNG A (cấu trúc): grammar dict→list, quiz list→dict, chuẩn hoá level
        → GHI ĐĨA (giữ nguyên hành vi cũ).
      • TẦNG B (v4 mềm): ipa, pos, example_target, example_vi, dialogue, media
        → chỉ setdefault trong RAM, KHÔNG ghi đĩa.

    Lý do Tầng B không ghi đĩa: 8 file course.json = 135 MB đang được track git.
    Backfill đầy đủ sẽ tạo diff ~27 MB → blob git mới vĩnh viễn, không thu hồi
    được, mà không đổi lại giá trị gì (app mới đã có default runtime).

    Args:
        apply_v4: bật lớp soft-default v4 trong bộ nhớ (mặc định True).
        persist:  None = auto (chỉ ghi khi thực sự thay đổi cấu trúc)
                  True  = ép ghi
                  False = không ghi (chế độ chỉ-đọc)
    """
    path = course_path(language)
    if not os.path.exists(path):
        return None
    try:
        # Đọc cũng phải nằm trong khoá: trên Windows, os.replace() sẽ FAIL
        # (Access is denied) nếu đích đang được mở để đọc ở thread khác.
        with _WRITE_LOCK:
            with open(path, "r", encoding="utf-8") as f:
                course = json.load(f)
    except Exception:
        return None
    migrated = False
    for lesson in course.get("days", []):
        if isinstance(lesson.get("grammar"), dict):
            g = lesson["grammar"]
            lesson["grammar"] = [g] if g.get("title") else []
            migrated = True
        lesson.setdefault("grammar", [])
        lesson.setdefault("sentence_patterns", [])
        lesson.setdefault("common_sentences", [])
        if isinstance(lesson.get("quiz"), list):
            lesson["quiz"] = {"mixed": lesson["quiz"]}
            migrated = True
        elif not isinstance(lesson.get("quiz"), dict):
            lesson["quiz"] = {}
            migrated = True
        for key in ("vocab", "pattern", "common", "grammar", "mixed"):
            lesson["quiz"].setdefault(key, [])
        # Tự động chuẩn hóa level theo phase cho từng bài học nếu thiếu hoặc chưa đúng
        phase = lesson.get("phase") or ""
        plow = phase.lower()
        curr_lvl = lesson.get("level") or ""
        if not curr_lvl or ("nền tảng" in plow and "người mới" not in curr_lvl.lower()) or ("giao tiếp cơ bản" in plow and "sơ cấp" not in curr_lvl.lower()):
            if "nền tảng" in plow or "phát âm" in plow or "chữ cái" in plow:
                lesson["level"] = "Người mới bắt đầu (phát âm & chữ cái)"
                migrated = True
            elif "giao tiếp cơ bản" in plow:
                lesson["level"] = "Sơ cấp (giao tiếp cơ bản)"
                migrated = True
            elif "trung cấp" in plow:
                lesson["level"] = "Trung cấp (tự tin giao tiếp)"
                migrated = True
            elif "cao cấp" in plow:
                lesson["level"] = "Cao cấp (chuyên sâu & học thuật)"
                migrated = True
            elif "bản xứ" in plow:
                lesson["level"] = "Như bản xứ (thành thạo mọi ngữ cảnh)"
                migrated = True
            elif not curr_lvl and course.get("level"):
                lesson["level"] = course["level"]
                migrated = True

        # ── TẦNG B: soft-default v4 — bơm vào RAM, KHÔNG set `migrated` ──
        if apply_v4:
            apply_v4_defaults_in_memory(lesson)

    # format_version: KHÔNG bump khi chỉ đọc.
    if course.get("format_version") is None:
        course["format_version"] = LEGACY_FORMAT_VERSION
    course.setdefault("media_manifest", "data/media/index.json")

    if migrated and persist is not False:
        save_course(language, course)
    return course


def migrate_course(language: str, to_version: int = COURSE_FORMAT_VERSION,
                   backfill: bool = False, log_fn=print) -> dict:
    """Nâng cấp 1 khóa học lên version đích.

    backfill=False (mặc định): chỉ đánh dấu version, KHÔNG ghi lại 135 MB.
    backfill=True: ghi đầy đủ field v4 — dùng khi thực sự cần.
    """
    course = get_course(language, apply_v4=True, persist=False)
    if not course:
        return {"ok": False, "reason": "not_found", "language": language}
    if not backfill:
        course["format_version"] = to_version
        save_course(language, course)
        log_fn(f"✅ {language}: đánh dấu format_version={to_version} (không backfill)")
        return {"ok": True, "written": True, "backfilled": False,
                "days": len(course.get("days", []))}
    for lesson in course.get("days", []):
        apply_v4_defaults_in_memory(lesson)
        lesson["format_version"] = to_version
    course["format_version"] = to_version
    save_course(language, course)
    log_fn(f"✅ {language}: backfill đầy đủ field v4 cho "
           f"{len(course.get('days', []))} ngày")
    return {"ok": True, "written": True, "backfilled": True,
            "days": len(course.get("days", []))}


def save_course(language: str, course: dict, backup: bool = False):
    """Ghi khóa học (atomic).

    backup=True → tạo bản .bak1..bak5 trước khi ghi (chỉ dùng khi thao tác
    nguy hiểm như force_new / migrate). Mặc định KHÔNG backup vì 8 file
    21 MB × 5 bản = ~840 MB không cần thiết cho mỗi lần lưu.
    """
    course["updated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    path = course_path(language)
    if backup:
        from ai.pipeline_store import rotate_backup
        rotate_backup(path)
    _atomic_write(path, course)


def new_course(language: str, vocabs: list, words_per_day: int) -> dict:
    """Tạo khung khóa học mới (chưa có nội dung ngày)."""
    return {
        "language": language,
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "words_per_day": words_per_day,
        "total_words": len(vocabs),
        "total_days": max(1, -(-len(vocabs) // max(words_per_day, 1))),
        "source_vocab_ids": [v.get("id") for v in vocabs],
        "days": [],
    }


def upsert_day(language: str, lesson: dict) -> bool:
    """Chèn/thay thế 1 ngày trong khóa học và lưu ngay (resumable).
    Trả về False nếu khóa học chưa tồn tại."""
    course = get_course(language)
    if course is None:
        return False
    day_num = int(lesson.get("day", 0))
    days = [d for d in course.get("days", []) if int(d.get("day", 0)) != day_num]
    days.append(lesson)
    days.sort(key=lambda d: int(d.get("day", 0)))
    course["days"] = days
    save_course(language, course)
    return True


def delete_course(language: str) -> bool:
    """Xóa toàn bộ thư mục khóa học của ngôn ngữ."""
    d = course_dir(language)
    if os.path.exists(d):
        import shutil
        shutil.rmtree(d, ignore_errors=True)
        return True
    return False


def list_course_languages() -> list:
    """Liệt kê các ngôn ngữ đã có khóa học AI."""
    langs = []
    if os.path.exists(COURSES_DIR):
        for name in sorted(os.listdir(COURSES_DIR)):
            if os.path.exists(os.path.join(COURSES_DIR, name, "course.json")):
                langs.append(name)
    return langs


# ─── Progress ──────────────────────────────────────────────────────────────────

DEFAULT_PROGRESS = {"completed_days": [], "quiz_scores": {}, "last_day": 1}


def get_progress(language: str) -> dict:
    path = progress_path(language)
    if not os.path.exists(path):
        return json.loads(json.dumps(DEFAULT_PROGRESS))
    try:
        with _WRITE_LOCK:
            with open(path, "r", encoding="utf-8") as f:
                p = json.load(f)
        base = json.loads(json.dumps(DEFAULT_PROGRESS))
        base.update(p if isinstance(p, dict) else {})
        return base
    except Exception:
        return json.loads(json.dumps(DEFAULT_PROGRESS))


def save_progress(language: str, progress: dict):
    progress["updated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    _atomic_write(progress_path(language), progress)


def mark_day_completed(language: str, day: int, score: int = None):
    """Đánh dấu hoàn thành 1 ngày + lưu điểm quiz (giữ điểm cao nhất)."""
    p = get_progress(language)
    if day not in p["completed_days"]:
        p["completed_days"].append(day)
        p["completed_days"].sort()
    if score is not None:
        key = str(day)
        old = p["quiz_scores"].get(key)
        if old is None or score > old.get("score", -1):
            p["quiz_scores"][key] = {
                "score": score,
                "at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            }
    p["last_day"] = day
    save_progress(language, p)


def reset_progress(language: str):
    save_progress(language, json.loads(json.dumps(DEFAULT_PROGRESS)))


# ─── CLI: python -m ai.course_db --migrate "Tiếng Anh" [--backfill] ──────────
if __name__ == "__main__":
    import argparse
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="Công cụ bảo trì khóa học AI")
    ap.add_argument("--migrate", metavar="LANGUAGE", help="Tên ngôn ngữ cần migrate")
    ap.add_argument("--backfill", action="store_true",
                    help="Ghi đầy đủ field v4 xuống đĩa (mặc định: chỉ đánh dấu version)")
    ap.add_argument("--list", action="store_true", help="Liệt kê khóa học có sẵn")
    args = ap.parse_args()

    if args.list:
        for name in sorted(os.listdir(COURSES_DIR)) if os.path.isdir(COURSES_DIR) else []:
            if os.path.isfile(os.path.join(COURSES_DIR, name, "course.json")):
                print(" -", name)
    if args.migrate:
        r = migrate_course(args.migrate, backfill=args.backfill)
        print(r)
        sys.exit(0 if r.get("ok") else 1)
    if not args.list:
        ap.print_help()
