"""
paths.py — NGUỒN SỰ THẬT DUY NHẤT cho quy tắc đường dẫn/slug.

BUG ĐÃ SỬA (L-67): trước đây có **6 bản copy** của hàm `lang_slug`
(database/database.py, ai/course_db.py, ai/media_store.py, ai/tts_generator.py,
ai/web_ai_bridge.py, web/script.js) — copy-paste cùng quy tắc
`.lower().replace(" ", "_")`. Đổi quy tắc 1 chỗ ⇒ 5 chỗ còn lại lệch ⇒ media
không tìm thấy từ. Giờ: 1 module duy nhất, web lấy cùng bảng từ
`web/paths.js` (sinh tự động bởi `python -m ai.paths --export-js`).
"""

import os
import re
import unicodedata

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
WEB_DIR = os.path.join(BASE_DIR, "web")


def lang_slug(language: str) -> str:
    """'Tiếng Nhật' → 'tiếng_nhật'.

    Quy tắc DUY NHẤT:
      1. strip
      2. lower
      3. khoảng trắng → gạch dưới
    GIỮ NGUYÊN chữ tiếng Việt (có dấu) — vì tên thư mục media/audio dùng
    đúng slug này.
    """
    s = (language or "").strip().lower()
    s = re.sub(r"\s+", "_", s)
    return s


def lang_display(slug: str) -> str:
    """'tiếng_nhật' → 'Tiếng Nhật' (dùng khi hiển thị)."""
    s = (slug or "").replace("_", " ").strip()
    return " ".join(w[:1].upper() + w[1:] for w in s.split(" ") if w)


def vocab_json_path(language: str) -> str:
    """Đường dẫn file từ vựng nhập tay: data/<slug>.json"""
    return os.path.join(DATA_DIR, f"{lang_slug(language)}.json")


def course_dir(language: str) -> str:
    """data/ai_courses/<slug>/"""
    return os.path.join(DATA_DIR, "ai_courses", lang_slug(language))


def media_dir(language: str) -> str:
    """data/media/<slug>/"""
    return os.path.join(DATA_DIR, "media", lang_slug(language))


def audio_dir(language: str) -> str:
    """data/audio/<slug>/"""
    return os.path.join(DATA_DIR, "audio", lang_slug(language))


def day_media_dir(language: str, day: int) -> str:
    """data/media/<slug>/d0001/"""
    return os.path.join(media_dir(language), f"d{int(day):04d}")


# ─── Bảng tra cứu cho web (sinh ra web/paths.js) ─────────────────────────────
def web_slug_table() -> list:
    """Danh sách {slug, display} từ các thư mục dữ liệu thực tế."""
    out = []
    ai = os.path.join(DATA_DIR, "ai_courses")
    if os.path.isdir(ai):
        for slug in sorted(os.listdir(ai)):
            if slug.startswith("_"):
                continue
            if os.path.isfile(os.path.join(ai, slug, "course.json")):
                out.append({"slug": slug, "display": lang_display(slug)})
    return out


def export_js(path: str = None) -> str:
    """Sinh web/paths.js từ cùng bảng quy tắc (1 nguồn sự thật)."""
    import json
    path = path or os.path.join(WEB_DIR, "paths.js")
    rows = web_slug_table()
    lines = [
        "// paths.js — SINH TỰ ĐỘNG bởi `python -m ai.paths --export-js`.",
        "// Nguồn sự thật duy nhất: ai/paths.py. KHÔNG sửa tay.",
        "const VOCAB_SLUG = (s) => String(s || '').trim().toLowerCase().replace(/\\s+/g, '_');",
        "const VOCAB_LANGS = " + json.dumps(rows, ensure_ascii=False) + ";",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--export-js" in sys.argv:
        p = export_js()
        print("Đã sinh:", p)
    else:
        print("lang_slug('Tiếng Nhật') =", lang_slug("Tiếng Nhật"))
        print("lang_display('tiếng_nhật') =", lang_display("tiếng_nhật"))
        print("Bảng web:", web_slug_table())
