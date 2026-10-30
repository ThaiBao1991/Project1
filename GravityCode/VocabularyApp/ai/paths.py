"""
paths.py — NGUỒN SỰ THẬT DUY NHẤT cho quy tắc đường dẫn/slug.

BUG ĐÃ SỬA (L-67): trước đây có **6 bản copy** của hàm `lang_slug`
(database/database.py, ai/course_db.py, ai/media_store.py, ai/tts_generator.py,
ai/web_ai_bridge.py, web/script.js) — copy-paste cùng quy tắc
`.lower().replace(" ", "_")`. Đổi quy tắc 1 chỗ ⇒ 5 chỗ còn lại lệch ⇒ media
không tìm thấy từ. Giờ: 1 module duy nhất, web lấy cùng bảng từ
`web/paths.js` (sinh tự động bởi `python -m ai.paths --export-js`).

BUG ĐÃ SỬA (split-brain Nhật): dữ liệu thật bị chia 2 nhà —
`data/media/nhật` (444 ngày) và `data/media/tiếng_nhật` (1.260 ngày). Giờ
mọi nơi sinh đường dẫn ĐI QUA `canonical_slug()`: alias ("nhật", "ja", …)
về hết slug chuẩn `tiếng_nhật`. rel_path đã ghi trong manifest KHÔNG đổi
(kiểm tra file theo chuỗi đã lưu), chỉ đường dẫn MỚI dùng slug chuẩn.
"""

import os
import re
import unicodedata

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
WEB_DIR = os.path.join(BASE_DIR, "web")
MEDIA_DIR = os.path.join(DATA_DIR, "media")          # data/media
AUDIO_DIR = os.path.join(DATA_DIR, "audio")          # data/audio
CARDS_DIR = os.path.join(MEDIA_DIR, "_cards")        # data/media/_cards (word-card cache)

# Alias slug (sau lang_slug) → slug chuẩn. Fix: khóa học Nhật từng tồn tại
# dưới 6 tên — "Nhật", "nhat", "Japanese", "ja", "jp", "tiếng Nhật".
JAPANESE_CANONICAL = "tiếng_nhật"
LANG_ALIASES = {
    "nhật": JAPANESE_CANONICAL,
    "nhat": JAPANESE_CANONICAL,
    "tieng_nhat": JAPANESE_CANONICAL,
    "japanese": JAPANESE_CANONICAL,
    "nihongo": JAPANESE_CANONICAL,
    "ja": JAPANESE_CANONICAL,
    "jp": JAPANESE_CANONICAL,
}


def canonical_slug(language: str) -> str:
    """lang_slug + gộp alias về slug chuẩn: 'Nhật'/'ja' → 'tiếng_nhật'.

    'Tiếng Nhật' → lang_slug → 'tiếng_nhật' (không đổi).
    Mọi code sinh đường dẫn MỚI (course/media/audio/json) gọi hàm này
    thay vì lang_slug trần.
    """
    s = lang_slug(language)
    return LANG_ALIASES.get(s, s)


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
    """Danh sách {slug, display} từ các thư mục dữ liệu thực tế.

    Gộp alias theo canonical_slug: 'nhật' và 'tiếng_nhật' khi CÙNG tồn tại
    chỉ còn 1 mục — slug trỏ về thư mục hiệu lực (canonical nếu có,
    không thì thư mục alias cũ), display luôn theo slug chuẩn.
    """
    out_map = {}
    ai = os.path.join(DATA_DIR, "ai_courses")
    if os.path.isdir(ai):
        for slug in sorted(os.listdir(ai)):
            if slug.startswith("_"):
                continue
            if not os.path.isfile(os.path.join(ai, slug, "course.json")):
                continue
            cs = canonical_slug(slug)
            if cs in out_map:
                # canonical đã chiếm chỗ — bỏ alias (0 ngày)
                continue
            phys = cs if os.path.isfile(os.path.join(ai, cs, "course.json")) else slug
            out_map[cs] = {"slug": phys, "display": lang_display(cs)}
    return [out_map[cs] for cs in sorted(out_map)]


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
