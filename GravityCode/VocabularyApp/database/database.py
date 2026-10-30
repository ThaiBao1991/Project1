"""
database.py — Quản lý dữ liệu JSON cho VocabularyApp
Hỗ trợ đa ngôn ngữ bằng cách lưu mỗi ngôn ngữ thành 1 file JSON riêng trong thư mục data/
"""

import json
import os
import shutil
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def _get_json_path(language: str) -> str:
    # BUG ĐÃ SỬA (L-67): quy tắc slug giờ nằm Ở 1 NGUỒN DUY NHẤT (ai/paths.py).
    # Trước đây copy-paste ở 6 chỗ ⇒ đổi 1 chỗ là 5 chỗ lệch.
    # BUG ĐÃ SỬA (split-brain): 'Nhật' → canonical 'tiếng_nhật'.
    from ai.paths import canonical_slug
    filename = canonical_slug(language) + ".json"
    if not filename or filename == ".json":
        filename = "default.json"
    return os.path.join(DATA_DIR, filename)


# ─── Load / Save ───────────────────────────────────────────────────────────────

def load_data(language: str) -> dict:
    """�ọc toàn bộ data từ file JSON của ngôn ngữ tương ứng.

    BUG ĐÃ SỬA (L-E): trước đây nuốt mọi exception và trả về list RỖNG ⇒
    lần `add_vocab`/`update_vocab` kế tiếp sẽ GHI ĐÈ file bằng 1 từ duy nhất,
    xoá vĩnh viễn toàn bộ từ vựng. Giờ:
      • file hỏng → sao lưu `.corrupt-<ts>.bak` rồi NÉM lỗi
        (caller bắt lỗi ⇒ KHÔNG ghi đè dữ liệu).
      • file không hợp lệ (không phải dict) → cũng ném lỗi.
    """
    path = _get_json_path(language)
    if not os.path.exists(path):
        return {"vocabularies": [], "last_updated": ""}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        _backup_corrupt(path)
        raise ValueError(
            f"File dữ liệu '{os.path.basename(path)}' bị hỏng — đã sao lưu, "
            f"KHÔNG ghi đè. Hãy sửa hoặc khôi phục file gốc. ({e})") from e
    if not isinstance(data, dict):
        _backup_corrupt(path)
        raise ValueError(
            f"File dữ liệu '{os.path.basename(path)}' không hợp lệ — đã sao lưu, "
            f"KHÔNG ghi đè.")
    # Đảm bảo luôn có key bắt buộc, tránh KeyError ở caller
    data.setdefault("vocabularies", [])
    data.setdefault("last_updated", "")
    return data


def _backup_corrupt(path: str) -> str:
    """Sao lưu file JSON hỏng trước khi caller ném lỗi."""
    try:
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        bak = f"{path}.corrupt-{ts}.bak"
        shutil.copy2(path, bak)
        return bak
    except Exception:
        return ""


def save_data(language: str, data: dict):
    """Ghi toàn bộ data xuống file JSON (atomic: ghi file tạm rồi replace,
    tránh hỏng file nếu app bị crash giữa lúc ghi)."""
    path = _get_json_path(language)
    data["last_updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


# ─── CRUD ──────────────────────────────────────────────────────────────────────

def _next_id(vocabularies: list) -> int:
    return max((v.get("id", 0) for v in vocabularies), default=0) + 1


def get_all_vocab(language: str) -> list:
    return load_data(language)["vocabularies"]


def get_vocab(language: str, vocab_id: int):
    for v in get_all_vocab(language):
        if v.get("id") == vocab_id:
            return v
    return None


def add_vocab(language: str, data: dict) -> int:
    db = load_data(language)
    new_id = _next_id(db["vocabularies"])
    vocab = {
        "id": new_id,
        "word": data.get("word", "").strip(),
        "pronunciation": data.get("pronunciation", "").strip(),
        "meaning": data.get("meaning", "").strip(),
        "example": data.get("example", "").strip(),
        "example_meaning": data.get("example_meaning", "").strip(),
        "word_type": data.get("word_type", "").strip(),
        "topic": data.get("topic", "").strip(),
        "date_tag": data.get("date_tag", "").strip(),
        "mp3_local_path": data.get("mp3_local_path", "").strip(),
        "mp3_gdrive_id": data.get("mp3_gdrive_id", "").strip(),
        "mp4_local_path": data.get("mp4_local_path", "").strip(),
        "mp4_gdrive_id": data.get("mp4_gdrive_id", "").strip(),
        "note": data.get("note", "").strip(),
        "created_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
    }
    db["vocabularies"].append(vocab)
    save_data(language, db)
    return new_id


def update_vocab(language: str, vocab_id: int, data: dict) -> bool:
    db = load_data(language)
    for i, v in enumerate(db["vocabularies"]):
        if v.get("id") == vocab_id:
            db["vocabularies"][i].update({
                "word": data.get("word", v.get("word")).strip(),
                "pronunciation": data.get("pronunciation", v.get("pronunciation")).strip(),
                "meaning": data.get("meaning", v.get("meaning")).strip(),
                "example": data.get("example", v.get("example")).strip(),
                "example_meaning": data.get("example_meaning", v.get("example_meaning")).strip(),
                "word_type": data.get("word_type", v.get("word_type")).strip(),
                "topic": data.get("topic", v.get("topic")).strip(),
                "date_tag": data.get("date_tag", v.get("date_tag")).strip(),
                "mp3_local_path": data.get("mp3_local_path", v.get("mp3_local_path")).strip(),
                "mp3_gdrive_id": data.get("mp3_gdrive_id", v.get("mp3_gdrive_id")).strip(),
                "mp4_local_path": data.get("mp4_local_path", v.get("mp4_local_path")).strip(),
                "mp4_gdrive_id": data.get("mp4_gdrive_id", v.get("mp4_gdrive_id")).strip(),
                "note": data.get("note", v.get("note")).strip(),
                "updated_at": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            })
            save_data(language, db)
            return True
    return False


def delete_vocab(language: str, vocab_id: int) -> bool:
    db = load_data(language)
    before = len(db["vocabularies"])
    db["vocabularies"] = [v for v in db["vocabularies"] if v.get("id") != vocab_id]
    if len(db["vocabularies"]) < before:
        save_data(language, db)
        return True
    return False


def find_vocab_by_word(language: str, word: str):
    """Tìm từ vựng theo tên (case-insensitive). Trả về dict nếu tìm thấy, None nếu không."""
    word_lower = word.strip().lower()
    for v in get_all_vocab(language):
        if v.get("word", "").strip().lower() == word_lower:
            return v
    return None


# ─── Search ────────────────────────────────────────────────────────────────────

def search_vocab(language: str, query: str, type_filter: str = "", topic_filter: str = "", date_filter: str = "") -> list:
    """Tim kiem qua word, meaning, example, note, pronunciation."""
    vocabs = get_all_vocab(language)
    q = query.strip().lower()
    results = []
    for v in vocabs:
        if type_filter and v.get("word_type", "") != type_filter:
            continue
        if topic_filter and v.get("topic", "") != topic_filter:
            continue
        if date_filter and v.get("date_tag", "") != date_filter:
            continue
        if q:
            haystack = " ".join([
                v.get("word", ""),
                v.get("meaning", ""),
                v.get("example", ""),
                v.get("note", ""),
                v.get("pronunciation", ""),
            ]).lower()
            if q not in haystack:
                continue
        results.append(v)
    return results


# ─── Stats & Helpers ───────────────────────────────────────────────────────────

def get_stats(language: str) -> dict:
    vocabs = get_all_vocab(language)
    return {
        "total": len(vocabs),
        "topics": len({v.get("topic") for v in vocabs if v.get("topic")}),
        "word_types": len({v.get("word_type") for v in vocabs if v.get("word_type")}),
        "with_mp3": sum(1 for v in vocabs if v.get("mp3_gdrive_id")),
    }


def get_all_topics(language: str) -> list:
    return sorted({v.get("topic", "") for v in get_all_vocab(language) if v.get("topic")})

def get_all_types(language: str) -> list:
    return sorted({v.get("word_type", "") for v in get_all_vocab(language) if v.get("word_type")})

def get_all_dates(language: str) -> list:
    return sorted({v.get("date_tag", "") for v in get_all_vocab(language) if v.get("date_tag")})

def get_available_languages() -> list:
    """Danh sách ngôn ngữ thật sự có dữ liệu.

    BUG ĐÃ SỬA (L-A): trước đây quét MỌI `data/*.json` ⇒ các file hệ thống
    (blocked_accounts.json, blocked_keys.json, language_profiles_cache.json,
    tts_quota.json, tts_voices.json) bị hiện thành "ngôn ngữ" ⇒ dropdown có 13 mục
    thay vì 8. Giờ chỉ nhận:
      • data/ai_courses/<slug>/course.json  (khóa học AI)
      • data/<slug>.json có chứa "vocabularies" (từ vựng nhập tay)
    BUG ĐÃ SỬA (split-brain): entry có cùng canonical_slug chỉ hiện 1 lần —
    khóa học AI chiếm chỗ trước, file vocab canonical tiếp theo; alias
    ("nhật", …) trùng → ẨN. Dropdown hết 2 mục "Nhật"/"Tiếng Nhật".
    """
    from ai.paths import LANG_ALIASES, canonical_slug, lang_display, lang_slug
    chosen = {}   # canonical_slug → display name (ưu tiên bản canonical)

    # 1. Khóa học AI (data/ai_courses/*/course.json)
    ai_courses_dir = os.path.join(DATA_DIR, "ai_courses")
    if os.path.isdir(ai_courses_dir):
        for folder in sorted(os.listdir(ai_courses_dir)):
            cpath = os.path.join(ai_courses_dir, folder, "course.json")
            if not os.path.isfile(cpath):
                continue
            cs = canonical_slug(folder)
            if cs in chosen:
                continue          # canonical đã chiếm chỗ — ẩn alias học trùng
            display_name = ""
            try:
                with open(cpath, "r", encoding="utf-8") as fp:
                    cdata = json.load(fp)
                display_name = (cdata.get("language") or "").strip()
            except Exception:
                pass
            if not display_name:
                display_name = lang_display(cs)
            # display vẫn là tên alias (VD course.json ghi "Nhật") → đổi sang
            # tên chuẩn để dropdown không còn 2 cách viết cho 1 ngôn ngữ.
            dslug = canonical_slug(display_name)
            if dslug == cs and lang_slug(display_name) in LANG_ALIASES:
                display_name = lang_display(cs)
            chosen[cs] = display_name

    # 2. File từ vựng nhập tay — CHỈ file có key "vocabularies"
    if os.path.isdir(DATA_DIR):
        for f in sorted(os.listdir(DATA_DIR)):
            if not f.endswith(".json") or f == "index.json":
                continue
            path = os.path.join(DATA_DIR, f)
            if not os.path.isfile(path):
                continue
            try:
                with open(path, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
            except Exception:
                continue
            if not isinstance(data, dict) or "vocabularies" not in data:
                continue          # file hệ thống → bỏ qua
            cs = canonical_slug(f[:-5])
            if cs in chosen:
                # khóa học AI của cùng canonical đã có — file vocab trùng lặp → bỏ
                continue
            chosen[cs] = lang_display(cs)

    return [chosen[cs] for cs in sorted(chosen)]


