"""
course_db.py — Database khóa học AI cho VocabularyApp
Lưu theo kiểu tương tự AskCpl (session.json + dữ liệu JSON từng phần):
  data/ai_courses/<ngon_ngu>/course.json     → toàn bộ bài học theo ngày
  data/ai_courses/<ngon_ngu>/progress.json   → tiến độ học, điểm trắc nghiệm
Ghi file đều dùng kiểu atomic (tmp + os.replace) để không hỏng dữ liệu.
"""

import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COURSES_DIR = os.path.join(BASE_DIR, "data", "ai_courses")


def _atomic_write(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def lang_slug(language: str) -> str:
    """'Tiếng Nhật' → 'tiếng_nhật' (khớp quy tắc đặt tên file của database.py)."""
    return (language or "").strip().lower().replace(" ", "_")


def course_dir(language: str) -> str:
    return os.path.join(COURSES_DIR, lang_slug(language))


def course_path(language: str) -> str:
    return os.path.join(course_dir(language), "course.json")


def progress_path(language: str) -> str:
    return os.path.join(course_dir(language), "progress.json")


# ─── Course ────────────────────────────────────────────────────────────────────

def get_course(language: str):
    """Trả về dict khóa học hoặc None nếu chưa có.
    Tự migrate định dạng cũ (grammar=dict, quiz=list) sang mới."""
    path = course_path(language)
    if not os.path.exists(path):
        return None
    try:
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
    if migrated:
        save_course(language, course)
    return course


def save_course(language: str, course: dict):
    course["updated_at"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    _atomic_write(course_path(language), course)


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
