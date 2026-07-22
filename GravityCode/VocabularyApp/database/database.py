"""
database.py — Quản lý dữ liệu JSON cho VocabularyApp
Hỗ trợ đa ngôn ngữ bằng cách lưu mỗi ngôn ngữ thành 1 file JSON riêng trong thư mục data/
"""

import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def _get_json_path(language: str) -> str:
    # Ví dụ: "Tiếng Anh" -> "tieng_anh.json" hoặc giữ nguyên tuỳ cấu hình.
    # Để đơn giản, thay thế khoảng trắng và viết thường.
    filename = language.strip().lower().replace(" ", "_") + ".json"
    if not filename or filename == ".json":
        filename = "default.json"
    return os.path.join(DATA_DIR, filename)


# ─── Load / Save ───────────────────────────────────────────────────────────────

def load_data(language: str) -> dict:
    """Đọc toàn bộ data từ file JSON của ngôn ngữ tương ứng."""
    path = _get_json_path(language)
    if not os.path.exists(path):
        return {"vocabularies": [], "last_updated": ""}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"vocabularies": [], "last_updated": ""}


def save_data(language: str, data: dict):
    """Ghi toàn bộ data xuống file JSON."""
    path = _get_json_path(language)
    data["last_updated"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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
    langs = []
    for f in os.listdir(DATA_DIR):
        if f.endswith(".json"):
            # Lấy tên file bỏ đuôi .json, viết hoa chữ cái đầu (VD: english.json -> English)
            name = f[:-5].replace("_", " ").title()
            langs.append(name)
    return langs
