"""
course_generator.py — Sinh khóa học chuyên sâu theo ngày bằng Gemini AI.
- Dùng lại cơ chế AccountPool/GeminiCoordinator của AskCpl (api/gemini_safe.py)
- Đọc API key (dạng ENC:) trực tiếp từ settings.json của AskCpl — chỉ đọc,
  không ghi đè trạng thái của ứng dụng kia.
- Khóa học AI là HỆ THỐNG HỌC HOÀN TOÀN ĐỘC LẬP, hoạt động với MỌI ngôn ngữ,
  KHÔNG liên kết gì với danh sách từ vựng người dùng đã nhập:
    AI TOÀN QUYỀN thiết kế giáo trình theo hành trình 5 giai đoạn
    (Nền tảng → Giao tiếp cơ bản → Trung cấp → Cao cấp → Như bản xứ),
    số ngày do AI tự quyết theo trình độ (hoặc người dùng chỉ định).
- Mỗi ngày = 1 bài học RICH gồm:
    ≥10 từ vựng chuyên sâu + ≥10 cách dùng câu + ≥10 câu thông dụng
    + 2-3 bài ngữ pháp + trắc nghiệm MỖI LOẠI ≥10 câu (4 loại).
- 3 loại lần gọi AI: (1) lập giáo trình, (2) nội dung ngày,
  (3) trắc nghiệm ngày — tránh bị cắt JSON, chạy lại được (resumable).
"""

import json
import os
import re
import time
from difflib import SequenceMatcher

from api.gemini_safe import GeminiCoordinator, ErrorKind
from ai.language_profiler import (
    get_or_create_language_profile,
    get_rule_based_fallback_profile,
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_WORDS_PER_DAY = 10
MIN_VOCAB = 10
MIN_PATTERNS = 10
MIN_SENTENCES = 10
MIN_GRAMMAR = 2
MAX_GRAMMAR = 3
QUIZ_PER_TYPE = 10

LEVELS = [
    "⭐ Trọn gói: Từ con số 0 đến Như người bản xứ",
    "1. Vỡ lòng (Bảng chữ cái & Khẩu hình phát âm)",
    "2. Ghép âm & Từ đơn sinh tồn (Tập đọc & Câu ngắn)",
    "3. Sơ cấp (Giao tiếp đời sống cơ bản - A1/A2)",
    "4. Trung cấp (Tự tin diễn đạt & Công sở - B1/B2)",
    "5. Cao cấp (Học thuật, Báo chí, Thuyết trình - C1)",
    "6. Như người bản xứ (Thành ngữ, Tiếng lóng, Văn hóa & Tư duy - C2)",
]
DEFAULT_LEVEL = LEVELS[0]

# Hành trình khóa học 6 tầng: từ CON SỐ 0 → GẦN NHƯ NGƯỜI BẢN XỨ
JOURNEY_PHASES = [
    ("Vỡ lòng chữ cái & phát âm", "hệ chữ viết, bảng chữ cái/ký tự, quy tắc phát âm, thanh điệu, khẩu hình môi/lưỡi"),
    ("Ghép âm & Từ đơn sinh tồn", "ghép vần, từ đơn 1-2 âm tiết, số đếm, đại từ, mẫu câu ngắn 2-3 từ sinh tồn"),
    ("Sơ cấp đời sống", "mua sắm, ăn uống, hỏi đường, gia đình, sở thích, câu đơn & thì hiện tại"),
    ("Trung cấp công việc", "kể chuyện quá khứ/tương lai, liên từ, câu phức, giao tiếp công sở, bày tỏ ý kiến"),
    ("Cao cấp học thuật", "tranh biện, thuyết trình, email chuyên nghiệp, đọc báo chí, câu giả định, bị động"),
    ("Như người bản xứ", "thành ngữ (idioms), tiếng lóng (slang), chơi chữ, ẩn dụ, văn hóa & tư duy bản địa"),
]

# ─── Mỗi level → chỉ dạy phases tương ứng (Hỗ trợ cả tên mới và tên cũ tương thích ngược) ───
LEVEL_PHASES = {
    "⭐ Trọn gói: Từ con số 0 đến Như người bản xứ": [0, 1, 2, 3, 4, 5],
    "1. Vỡ lòng (Bảng chữ cái & Khẩu hình phát âm)": [0],
    "2. Ghép âm & Từ đơn sinh tồn (Tập đọc & Câu ngắn)": [1],
    "3. Sơ cấp (Giao tiếp đời sống cơ bản - A1/A2)": [2],
    "4. Trung cấp (Tự tin diễn đạt & Công sở - B1/B2)": [3],
    "5. Cao cấp (Học thuật, Báo chí, Thuyết trình - C1)": [4],
    "6. Như người bản xứ (Thành ngữ, Tiếng lóng, Văn hóa & Tư duy - C2)": [5],
    # Tương thích ngược với tên cũ
    "Người mới bắt đầu": [0, 1],
    "Sơ cấp (giao tiếp cơ bản)": [1, 2],
    "Trung cấp (tự tin giao tiếp)": [2, 3],
    "Cao cấp (thành thạo học thuật/công việc)": [4],
    "Thành thạo như người bản xứ": [5],
}

LEVEL_MIN_DAYS = {
    "⭐ Trọn gói: Từ con số 0 đến Như người bản xứ": 240,
    "1. Vỡ lòng (Bảng chữ cái & Khẩu hình phát âm)": 15,
    "2. Ghép âm & Từ đơn sinh tồn (Tập đọc & Câu ngắn)": 20,
    "3. Sơ cấp (Giao tiếp đời sống cơ bản - A1/A2)": 50,
    "4. Trung cấp (Tự tin diễn đạt & Công sở - B1/B2)": 60,
    "5. Cao cấp (Học thuật, Báo chí, Thuyết trình - C1)": 55,
    "6. Như người bản xứ (Thành ngữ, Tiếng lóng, Văn hóa & Tư duy - C2)": 35,
    # Tương thích ngược
    "Người mới bắt đầu": 15,
    "Sơ cấp (giao tiếp cơ bản)": 30,
    "Trung cấp (tự tin giao tiếp)": 25,
    "Cao cấp (thành thạo học thuật/công việc)": 25,
    "Thành thạo như người bản xứ": 20,
}


def get_language_native_profile(language: str, coord=None, log_fn=None) -> dict:
    """Xác định danh mục độ khó và số ngày chuẩn BẢN XỨ (C2) bằng AI Dynamic Profiling (kèm cache và fallback)."""
    return get_or_create_language_profile(language, coord=coord, log_fn=log_fn)


def get_language_fsi_profile(language: str) -> dict:
    """Xác định danh mục độ khó FSI (Category I - V) và tính toán số ngày chuẩn
    cùng tỷ trọng phân bổ cho 6 Tầng từ Con số 0 đến Bản xứ."""
    lang_lower = (language or "").lower()

    # Nhóm 4-5: Khó nhất (Tượng hình, Thanh điệu, Kanji/Hanzi, Ngữ pháp ngược, Patchim) -> 420 ngày
    if any(k in lang_lower for k in ["nhật", "japanese", "japan", "nihongo",
                                     "trung", "chinese", "mandarin", "hán", "hoa", "hsk",
                                     "hàn", "korean", "hangul", "topik",
                                     "ả rập", "arabic", "cantonese"]):
        total_days = 420
        category_name = "FSI Category IV/V (Chữ tượng hình, âm tiết & thanh điệu phức tạp)"
        stage_days = [30, 38, 92, 105, 97, 58]  # Tổng 420 ngày
    # Nhóm 3: Phức tạp (Hệ chữ riêng hoặc biến cách nhiều: Nga, Thái, Hy Lạp, Hindi, Ba Lan) -> 360 ngày
    elif any(k in lang_lower for k in ["nga", "russian", "thái", "thai", "hy lạp", "greek",
                                       "hindi", "ba lan", "polish", "thổ nhĩ kỳ", "turkish",
                                       "ukraine", "hebrew"]):
        total_days = 360
        category_name = "FSI Category III/IV (Hệ chữ riêng & nhiều biến cách)"
        stage_days = [25, 35, 80, 90, 80, 50]  # Tổng 360 ngày
    # Nhóm 2: Trung bình (Latinh có chia giống/thì phức tạp: Pháp, Đức, Ý, TBN) -> 320 ngày
    elif any(k in lang_lower for k in ["pháp", "french", "đức", "german", "tây ban nha", "spanish",
                                       "ý", "italian", "bồ đào nha", "portuguese",
                                       "indonesia", "thụy điển", "swedish", "hà lan", "dutch"]):
        total_days = 320
        category_name = "FSI Category II/III (Ngôn ngữ Latinh có chia giống & thì)"
        stage_days = [20, 30, 70, 80, 75, 45]  # Tổng 320 ngày
    # Nhóm 1: Quen thuộc / Latinh phổ thông (Tiếng Anh và các ngôn ngữ khác) -> 240 ngày
    else:
        total_days = 240
        category_name = "FSI Category I (Ngôn ngữ chữ Latinh thông dụng)"
        stage_days = [17, 22, 53, 60, 55, 33]  # Tổng 240 ngày

    stages_info = []
    current_start = 1
    stage_short_tags = [
        "[Vỡ lòng]",
        "[Ghép âm]",
        "[Sơ cấp]",
        "[Trung cấp]",
        "[Cao cấp]",
        "[Bản xứ]",
    ]
    for i, (name, desc) in enumerate(JOURNEY_PHASES):
        days_count = stage_days[i]
        stages_info.append({
            "stage_idx": i,
            "stage_num": i + 1,
            "name": name,
            "tag": stage_short_tags[i],
            "desc": desc,
            "target_days": days_count,
            "start_day": current_start,
            "end_day": current_start + days_count - 1,
        })
        current_start += days_count

    return {
        "language": language,
        "category_name": category_name,
        "total_days": total_days,
        "stage_days": stage_days,
        "stages": stages_info,
    }


def _journey_text() -> str:
    return "\n".join(f"   • Tầng {i} — {name}: {desc}"
                     for i, (name, desc) in enumerate(JOURNEY_PHASES, 1))

QUIZ_CATEGORIES = [
    ("vocab", "Từ vựng"),
    ("pattern", "Cách dùng câu"),
    ("common", "Câu thông dụng"),
    ("grammar", "Ngữ pháp"),
    ("mixed", "Tổng hợp"),   # cho dữ liệu cũ migrate
]

# ─── Schema GIÁO TRÌNH (AI tự lập khi DB thiếu/rỗng từ) ────────────────────────
_CURRICULUM_WORD = {
    "type": "OBJECT",
    "properties": {
        "word": {"type": "STRING"},
        "pronunciation": {"type": "STRING"},
        "meaning_vi": {"type": "STRING"},
    },
    "required": ["word", "pronunciation", "meaning_vi"],
}

CURRICULUM_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "days": {"type": "ARRAY", "items": {
            "type": "OBJECT",
            "properties": {
                "day": {"type": "INTEGER"},
                "title": {"type": "STRING"},
                "phase": {"type": "STRING"},
                "words": {"type": "ARRAY", "items": _CURRICULUM_WORD},
            },
            "required": ["day", "title", "phase", "words"],
        }},
    },
    "required": ["days"],
}

# ─── Schema 1: NỘI DUNG bài học (Gemini structured output) ────────────────────
CONTENT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "vocab": {"type": "ARRAY", "items": {
            "type": "OBJECT",
            "properties": {
                "word": {"type": "STRING"},
                "pronunciation": {"type": "STRING"},
                "part_of_speech": {"type": "STRING"},
                "meaning_vi": {"type": "STRING"},
                "explanation": {"type": "STRING"},
                "example_sentence": {"type": "STRING"},
                "example_meaning_vi": {"type": "STRING"},
            },
            "required": ["word", "pronunciation", "part_of_speech", "meaning_vi",
                         "explanation", "example_sentence", "example_meaning_vi"],
        }},
        "sentence_patterns": {"type": "ARRAY", "items": {
            "type": "OBJECT",
            "properties": {
                "pattern": {"type": "STRING"},
                "meaning_vi": {"type": "STRING"},
                "structure_note": {"type": "STRING"},
                "example_sentence": {"type": "STRING"},
                "example_meaning_vi": {"type": "STRING"},
            },
            "required": ["pattern", "meaning_vi", "structure_note",
                         "example_sentence", "example_meaning_vi"],
        }},
        "common_sentences": {"type": "ARRAY", "items": {
            "type": "OBJECT",
            "properties": {
                "sentence": {"type": "STRING"},
                "meaning_vi": {"type": "STRING"},
                "situation": {"type": "STRING"},
            },
            "required": ["sentence", "meaning_vi", "situation"],
        }},
        "grammar": {"type": "ARRAY", "items": {
            "type": "OBJECT",
            "properties": {
                "title": {"type": "STRING"},
                "explanation": {"type": "STRING"},
                "examples": {"type": "ARRAY", "items": {
                    "type": "OBJECT",
                    "properties": {
                        "sentence": {"type": "STRING"},
                        "meaning_vi": {"type": "STRING"},
                    },
                    "required": ["sentence", "meaning_vi"],
                }},
            },
            "required": ["title", "explanation", "examples"],
        }},
    },
    "required": ["title", "vocab", "sentence_patterns", "common_sentences", "grammar"],
}

# ─── Schema 2: TRẮC NGHIỆM (4 loại, mỗi loại ≥10 câu) ─────────────────────────
_QUIZ_ITEM = {
    "type": "OBJECT",
    "properties": {
        "question": {"type": "STRING"},
        "options": {"type": "ARRAY", "items": {"type": "STRING"}},
        "answer_index": {"type": "INTEGER"},
        "explanation": {"type": "STRING"},
    },
    "required": ["question", "options", "answer_index", "explanation"],
}

# Schema đầy đủ (giữ lại để tương thích)
QUIZ_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "vocab_quiz": {"type": "ARRAY", "items": _QUIZ_ITEM},
        "pattern_quiz": {"type": "ARRAY", "items": _QUIZ_ITEM},
        "common_quiz": {"type": "ARRAY", "items": _QUIZ_ITEM},
        "grammar_quiz": {"type": "ARRAY", "items": _QUIZ_ITEM},
    },
    "required": ["vocab_quiz", "pattern_quiz", "common_quiz", "grammar_quiz"],
}

# Schema tách đôi (Hướng A: giảm output tokens ~50%)
QUIZ_SCHEMA_AB = {
    "type": "OBJECT",
    "properties": {
        "vocab_quiz":   {"type": "ARRAY", "items": _QUIZ_ITEM},
        "pattern_quiz": {"type": "ARRAY", "items": _QUIZ_ITEM},
    },
    "required": ["vocab_quiz", "pattern_quiz"],
}
QUIZ_SCHEMA_CD = {
    "type": "OBJECT",
    "properties": {
        "common_quiz":  {"type": "ARRAY", "items": _QUIZ_ITEM},
        "grammar_quiz": {"type": "ARRAY", "items": _QUIZ_ITEM},
    },
    "required": ["common_quiz", "grammar_quiz"],
}

# ─── Schema 3: BACKBONE — Khung giáo trình bắt buộc (sinh 1 lần / level) ────────
BACKBONE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "items": {"type": "ARRAY", "items": {
            "type": "OBJECT",
            "properties": {
                "id":         {"type": "INTEGER"},
                "category":   {"type": "STRING"},   # VD: PHÁT ÂM / NGỮ PHÁP / GIAO TIẾP / TỪ VỰNG
                "title":      {"type": "STRING"},   # Tên chủ đề ngắn gọn
                "importance": {"type": "STRING"},   # BẮT BUỘC / NÊN HỌC / MỞ RỘNG
            },
            "required": ["id", "category", "title", "importance"],
        }},
    },
    "required": ["items"],
}

# ─── Schema 4: ADAPTATION STAGE (Layer 2) — Thích ứng tên chủ đề cụ thể từng ngôn ngữ ───
ADAPT_STAGE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "topics": {"type": "ARRAY", "items": {
            "type": "OBJECT",
            "properties": {
                "slot_id":    {"type": "INTEGER"},
                "title":      {"type": "STRING"},
                "category":   {"type": "STRING"},
                "importance": {"type": "STRING"},
            },
            "required": ["slot_id", "title"],
        }},
    },
    "required": ["topics"],
}

# ─── Schema 5: GAP INSERTION (Layer 3) — Bổ sung chủ đề đặc thù chèn vào đúng vị trí ────
GAP_INSERT_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "insertions": {"type": "ARRAY", "items": {
            "type": "OBJECT",
            "properties": {
                "after_slot_id": {"type": "INTEGER"},
                "title":         {"type": "STRING"},
                "category":      {"type": "STRING"},
                "importance":    {"type": "STRING"},
            },
            "required": ["after_slot_id", "title"],
        }},
    },
    "required": ["insertions"],
}

# Số item backbone lấy ra làm plan mỗi lần sinh (None = tự động sinh liên tục 100% không ngắt)
BACKBONE_BATCH_SIZE = None



# ─── Nguồn API key (AskCpl) ────────────────────────────────────────────────────

def askcpl_settings_path() -> str:
    """Đường dẫn settings.json của AskCpl (ghi đè được qua app: ai.askcpl_settings_path)."""
    try:
        from settings import load_settings
        custom = (load_settings().get("ai", {}) or {}).get("askcpl_settings_path", "")
        if custom and os.path.exists(custom):
            return custom
    except Exception:
        pass
    default = os.path.normpath(os.path.join(
        BASE_DIR, "..", "Download", "AskCpl", "settings.json"))
    return default


def _load_gemini_keys() -> list:
    """Đọc toàn bộ Gemini API key từ AskCpl settings.json và giải mã ENC:."""
    path = askcpl_settings_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return []
    keys = (data.get("gemini", {}) or {}).get("api_keys", []) or []
    try:
        from settings import decode_token
    except Exception:
        decode_token = lambda s: s  # noqa: E731
    out = []
    for k in keys:
        raw = k.get("key") or ""
        if raw.startswith("ENC:"):
            raw = decode_token(raw)
        if raw:
            item = dict(k)
            item["key"] = raw
            out.append(item)
    return out


def count_available_keys() -> int:
    return len(_load_gemini_keys())


# ─── Prompt ────────────────────────────────────────────────────────────────────

def build_curriculum_prompt(lang_name: str, level: str, words_per_day: int,
                            target_days: int = None, phases: list = None,
                            completed_topics: list = None,
                            start_day: int = 1) -> str:
    """Prompt yêu cầu AI TỰ LẬP giáo trình, CHỈ dạy phases thuộc level đã chọn.
    target_days=None → AI TỰ QUYẾT số ngày phù hợp (đảm bảo >= min_days cho level).
    phases: list chỉ số phase cần dạy (VD: [0,1] cho Sơ cấp).
    completed_topics: danh sách chủ đề đã học ở level trước (để KHÔNG lặp lại).
    start_day: số ngày bắt đầu đánh số (VD: 1 cho khóa mới, 16 cho chặng tiếp nối)."""
    min_days = LEVEL_MIN_DAYS.get(level, 15)
    phases = phases or list(range(len(JOURNEY_PHASES)))
    phase_names = [JOURNEY_PHASES[i][0] for i in phases if i < len(JOURNEY_PHASES)]
    phase_descs = [JOURNEY_PHASES[i][1] for i in phases if i < len(JOURNEY_PHASES)]

    scope_lines = "\n".join(
        f"   • {name}: {desc}" for name, desc in zip(phase_names, phase_descs))
    phase_rule = (
        f"KHÔNG được dạy vượt quá các giai đoạn này.\n"
        f"Chỉ dạy {len(phases)} giai đoạn tương ứng với trình độ '{level}'."
    )
    
    continuation_note = ""
    if start_day > 1 or completed_topics:
        topics_str = ", ".join(completed_topics[:60]) if completed_topics else "các bài trước"
        continuation_note = (
            f"\n\n⭐ TIẾP NỐI LỘ TRÌNH ĐÃ HỌC (TỪ NGÀY {start_day} TRỞ ĐI):\n"
            f"- Người học ĐÃ HOÀN THÀNH {start_day - 1} ngày trước đó với các chủ đề: {topics_str}.\n"
            f"- Hãy BẮT ĐẦU từ chỗ người học dừng lại, TUYỆT ĐỐI KHÔNG dạy trùng lại các chủ đề trên.\n"
            f"- Mở rộng và nâng cao dần kiến thức theo đúng trình độ '{level}'.\n"
            f"- ĐÁNH SỐ NGÀY TRONG JSON: trường 'day' của mỗi ngày phải đánh số bắt đầu từ {start_day}."
        )

    zero_knowledge_note = ""
    if 0 in phases and start_day == 1:
        zero_knowledge_note = (
            f"\n\n⭐ NGUYÊN TẮC BẮT BUỘC CHO NGƯỜI MỚI BẮT ĐẦU (Giai đoạn Nền tảng):\n"
            f"- Người học là người Việt Nam CHƯA BIẾT GÌ VỀ {lang_name.upper()}.\n"
            f"- Những ngày đầu tiên (Ngày 1 đến Ngày 3-5): BẮT BUỘC tập trung dạy "
            f"Hệ chữ viết, Bảng chữ cái, Bảng phiên âm (như Romaji/Hiragana/Katakana cho tiếng Nhật, "
            f"Pinyin & 4 thanh điệu cho tiếng Trung, Hangul & patchim cho tiếng Hàn, Bảng chữ cái & IPA cho tiếng Anh/Pháp...), "
            f"kèm các ví dụ đơn giản minh họa cách ghép âm và phát âm chuẩn.\n"
            f"- Sau khi vững chữ cái và phát âm, các ngày tiếp theo mới chuyển sang số đếm, "
            f"chào hỏi, đại từ nhân xưng và các từ vựng/mẫu câu sinh tồn giao tiếp cơ bản."
        )

    if target_days:
        days_req = (
            f"Hãy lập giáo trình ĐÚNG {target_days} ngày tiếp theo (bắt đầu từ Ngày {start_day}), "
            f"mỗi ngày ĐÚNG {words_per_day} từ vựng."
        )
    else:
        days_req = (
            f"Hãy TỰ QUYẾT tổng số ngày phù hợp cho chặng này rồi lập giáo trình (bắt đầu từ Ngày {start_day}), "
            f"mỗi ngày ĐÚNG {words_per_day} từ vựng.\n"
            f"TỐI THIỂU {min_days} ngày (trình độ '{level}' cần đủ độ sâu cho "
            f"{', '.join(phase_names)}).\n"
            f"Không được quá ít ngày — phải đủ chỗ để dạy sâu từng chủ đề."
        )
    return (
        f"Bạn là chuyên gia thiết kế giáo trình {lang_name} cho người Việt, "
        f"giống cách người bản xứ dạy người mới.\n\n"
        f"Trình độ: {level}"
        + (f" (hoặc tương đương JLPT/HSK/TOPIK/CEFR)" if level else "")
        + f"\n\nCÁC GIAI ĐOẠN CHỈ DẠY TRONG KHÓA NÀY:\n{scope_lines}\n\n"
        f"{phase_rule}\n\n{days_req}\n\n"
        f"YÊU CẦU:\n"
        f"- Giáo trình do bạn TOÀN QUYỀN thiết kế, KHÔNG dùng từ vựng có sẵn.\n"
        f"- Tiến bộ dần: ngày sau xây trên nền ngày trước, KHÔNG nhảy cóc.\n"
        f"- Mỗi ngày 1 CHỦ ĐỀ rõ ràng (title tiếng Việt).\n"
        f"- field 'phase' = tên giai đoạn (tiếng Việt): "
        f"{', '.join(phase_names)}.\n"
        f"- Từ vựng là những từ người bản xứ THỰC SỬ dụng, không từ cổ/hiếm.\n"
        f"- pronunciation: romaji/pinyin/romanization/IPA tùy ngôn ngữ.\n"
        f"- meaning_vi: nghĩa tiếng Việt ngắn gọn.\n"
        f"- Chỉ trả về JSON, không thêm chữ ngoài JSON."
        f"{zero_knowledge_note}"
        f"{continuation_note}"
    )


def build_content_prompt(lang_name: str, day_num: int, total_days: int, words: list,
                         topic: str = "", level: str = "") -> str:
    lines = [f"- {v.get('word', '')} ({v.get('pronunciation') or 'chưa có phát âm'})"
             f" — nghĩa hiện có: {(v.get('meaning') or '')[:200]}" for v in words]
    word_list = "\n".join(lines) if lines else "(trống)"
    topic_line = f"\nCHỦ ĐỀ BẮT BUỘC của ngày này: {topic}\n" if topic else ""
    level_line = f"\nTrình độ người học: {level}.\n" if level else ""
    auto_pick = ""
    if not words:
        auto_pick = (
            f"\n⚠️ Người học CHƯA có từ sẵn — bạn hãy TỰ CHỌN {MIN_VOCAB} từ vựng quan trọng "
            f"nhất mà một người bản xứ sẽ dạy cho người học ở giai đoạn này "
            f"(theo chủ đề ngày: '{topic}').\n"
        )

    # ── Hướng dẫn sư phạm thích ứng theo từng giai đoạn (Stage-Adaptive Pedagogy) ──
    stage_guide = ""
    t_lower = (topic or "").lower()
    is_stage_1 = any(k in t_lower for k in ["chữ cái", "phát âm", "phiên âm", "bảng chữ", "vỡ lòng", "nhập môn", "khẩu hình", "thanh điệu", "nét viết", "hiragana", "katakana", "hangul", "pinyin", "ipa"]) or (day_num <= 3 and "trọn gói" in (level or "").lower())
    is_stage_2 = any(k in t_lower for k in ["ghép âm", "từ đơn", "sinh tồn", "tập đọc", "số đếm", "đại từ"]) and not is_stage_1
    is_stage_native = any(k in t_lower for k in ["bản xứ", "thành ngữ", "tiếng lóng", "slang", "idiom", "chơi chữ", "văn hóa", "kính ngữ", "sắc thái"])
    is_review_day = "ôn tập" in t_lower or (day_num % 7 == 0)

    if is_review_day:
        stage_guide = (
            "\n🔄 HƯỚNG DẪN ĐẶC BIỆT CHO NGÀY ÔN TẬP TUẦN & TỔNG HỢP THỰC HÀNH ('6 + 1'):\n"
            "- Mục tiêu: Không dạy dồn từ mới rời rạc, mà củng cố và biến kiến thức tuần qua thành phản xạ tự nhiên.\n"
            "- Mẫu câu & Câu thông dụng: Tạo một HỘI THOẠI TÌNH HUỐNG THỰC TẾ (Real-Life Roleplay) dài, nhúng các từ vựng và cấu trúc của 6 ngày trước vào một câu chuyện sống động.\n"
            "- Ngữ pháp: Tổng hợp các cấu trúc cốt lõi của tuần và phân tích các lỗi sai người Việt hay nhầm lẫn.\n"
        )
    elif is_stage_1:
        stage_guide = (
            "\n👄 HƯỚNG DẪN VỠ LÒNG CHỮ CÁI, GIẢI PHẪU KHẨU HÌNH & PHÁT ÂM 3 LỚP (DÀNH CHO NGƯỜI MỚI 0 KIẾN THỨC):\n"
            "- Phần từ vựng: Dạy 5-10 ký tự/chữ cái/âm vị của ngày hôm nay. Trong 'explanation', BẮT BUỘC cung cấp đủ 3 lớp: "
            "(1) Phiên âm chuẩn quốc tế; (2) Giải phẫu khẩu hình: vị trí răng, lưỡi, độ mở môi, thanh quản rung hay không rung; (3) Mẹo nhớ và lưu ý tránh lỗi sai của người Việt.\n"
            "- Phần mẫu câu & câu thông dụng: Dùng các từ/cụm từ ngắn (1-2 âm tiết) minh họa cho ký tự vừa học. KHÔNG dùng câu dài phức tạp khiến người mới bị ngợp.\n"
            "- Phần ngữ pháp: Giảng sâu về cấu trúc hệ chữ viết, quy tắc ghép âm, biến âm, thanh điệu hoặc trọng âm của nhóm chữ vừa học.\n"
        )
    elif is_stage_2:
        stage_guide = (
            "\n💡 HƯỚNG DẪN CHO BÀI GHÉP ÂM & TỪ ĐƠN SINH TỒN:\n"
            "- Tập trung vào ghép các chữ cái đã học thành từ đơn 1-2 âm tiết thông dụng (số đếm, đại từ, chào hỏi sinh tồn).\n"
            "- Mẫu câu và câu thông dụng là các câu ngắn 2-4 từ dễ tạo phản xạ (Tôi là..., Đây là..., Xin chào, Cảm ơn).\n"
        )
    elif is_stage_native:
        stage_guide = (
            "\n🎭 HƯỚNG DẪN CHO BÀI BẢN XỨ HÓA (NATIVE PROFICIENCY & CULTURE NUANCE):\n"
            "- Tập trung vào Thành ngữ (Idioms), Tiếng lóng (Slang), Collocations tự nhiên, sắc thái văn hóa, cách nói hài hước, mỉa mai, nói giảm nói tránh.\n"
            "- Trong giải thích ngữ pháp hoặc từ vựng: BẮT BUỘC chỉ ra sự khác biệt giữa 'Cách nói sách vở/người nước ngoài hay nói' vs 'Cách người bản xứ thực sự nói tự nhiên ngoài đời' kèm lời khuyên văn hóa ngữ cảnh ngầm (High-context culture).\n"
        )
    else:
        stage_guide = (
            "\n🎭 GÓC ĐỐI CHIẾU SẮC THÁI BẢN XỨ:\n"
            "- Trong phần giải thích: Nêu rõ sắc thái ngữ cảnh thực tế (khi nào dùng trang trọng, khi nào dùng thân mật, cách diễn đạt tự nhiên của người bản xứ thay vì dịch thô từ tiếng Việt).\n"
        )

    return (
        f"Bạn là gia sư {lang_name} chuyên nghiệp, dạy người Việt từ gốc đến chuyên sâu như người bản xứ.\n"
        f"Hôm nay là Ngày {day_num}/{total_days} của khóa học.{level_line}{topic_line}"
        f"Từ vựng gốc của ngày này:\n{word_list}\n{auto_pick}{stage_guide}\n"
        f"Hãy tạo bài học hoàn chỉnh dạng JSON, ĐỦ tuyệt đối số lượng như sau:\n\n"
        f"1. title: tên bài học (tiếng Việt) nêu rõ chủ đề nhóm từ.\n\n"
        f"2. vocab: ÍT NHẤT {MIN_VOCAB} từ vựng. Ưu tiên dùng đủ các từ gốc ở trên; "
        f"nếu từ gốc ít hơn {MIN_VOCAB}, BỔ SUNG các từ liên quan cùng chủ đề/giao tiếp "
        f"thông dụng để đạt tối thiểu {MIN_VOCAB} từ. Mỗi từ gồm:\n"
        f"   - pronunciation: cách đọc chuẩn (romaji/pinyin/IPA/romanization tùy ngôn ngữ)\n"
        f"   - part_of_speech: loại từ tiếng Việt\n"
        f"   - meaning_vi: nghĩa tiếng Việt chính xác, tự nhiên\n"
        f"   - explanation: giải thích CHUYÊN SÂU 2-4 câu: sắc thái, cách dùng, kết từ "
        f"thông dụng, khác gì từ đồng nghĩa, mẹo nhớ\n"
        f"   - example_sentence + example_meaning_vi: 1 câu ví dụ thực tế kèm dịch\n\n"
        f"3. sentence_patterns: ÍT NHẤT {MIN_PATTERNS} CÁCH DÙNG CÂU / mẫu câu. Mỗi mẫu gồm:\n"
        f"   - pattern: mẫu câu (đánh dấu phần biến thiên bằng ...)\n"
        f"   - meaning_vi: nghĩa của mẫu\n"
        f"   - structure_note: cấu trúc + cách dùng + lưu ý 1-2 câu\n"
        f"   - example_sentence + example_meaning_vi: ví dụ nhúng từ vựng của bài\n\n"
        f"4. common_sentences: ÍT NHẤT {MIN_SENTENCES} CÂU THÔNG DỤNG giao tiếp thực tế "
        f"(người bản xứ dùng hằng ngày, liên quan chủ đề). Mỗi câu gồm:\n"
        f"   - sentence + meaning_vi + situation: tình huống dùng (VD: chào sếp, mua hàng...)\n\n"
        f"5. grammar: {MIN_GRAMMAR}-{MAX_GRAMMAR} BÀI ngữ pháp hoàn chỉnh. Mỗi bài gồm:\n"
        f"   - title: tên điểm ngữ pháp\n"
        f"   - explanation: giảng chi tiết 5-10 câu: cấu trúc, cách chia, sắc thái, "
        f"phân biệt với mẫu dễ nhầm, lỗi sai thường gặp của người Việt\n"
        f"   - examples: 3-4 câu ví dụ song ngữ (nhúng từ vựng của bài)\n\n"
        f"Chỉ trả về JSON, không thêm chữ nào ngoài JSON."
    )


def build_quiz_prompt(lang_name: str, lesson: dict) -> str:
    """Prompt sinh trắc nghiệm từ bài học đã có (gửi bản tóm lược để gọn) với thiết kế bẫy sư phạm.
    Kept for backward compatibility — internally calls split prompts."""
    return build_quiz_prompt_ab(lang_name, lesson)


def _quiz_trap_rules() -> str:
    """Quy tắc bẫy sư phạm dùng chung cho cả 2 half-prompt."""
    return (
        "QUY TẮC THIẾT KẾ BẪY TRẮC NGHIỆM SƯ PHẠM (4 LỰA CHỌN):\n"
        "1. 1 Đáp án Đúng chuẩn xác 100% về ngữ pháp, phát âm và sắc thái tự nhiên của người bản xứ.\n"
        "2. 1 Bẫy Dịch Thô Tiếng Việt (Word-for-Word Trap): câu sai do thói quen dịch từng chữ từ tiếng Việt sang.\n"
        "3. 1 Bẫy Từ Dễ Nhầm Lẫn (Confusing Pair Trap): nhầm trợ từ, nhầm thì, nhầm từ đồng nghĩa khác sắc thái.\n"
        "4. 1 Bẫy Cấu Trúc Gần Đúng (Near-Grammar Trap): sai trật tự từ hoặc chia sai đuôi động từ.\n"
    )


def build_quiz_prompt_ab(lang_name: str, lesson: dict) -> str:
    """Nửa đầu: chỉ sinh vocab_quiz + pattern_quiz (~20 câu, ~6-8k tokens output)."""
    vocab_lines = [f"- {v['word']} ({v.get('pronunciation', '')}): {v.get('meaning_vi', '')}"
                   for v in lesson.get("vocab", [])]
    pattern_lines = [f"- {p.get('pattern', '')}: {p.get('meaning_vi', '')}"
                     for p in lesson.get("sentence_patterns", [])]
    return (
        f"Bạn là soạn giả đề kiểm tra {lang_name}. Dựa trên NỘI DUNG bài học dưới đây, "
        f"soạn TRẮC NGHIỆM 4 lựa chọn — CHỈ 2 LOẠI sau:\n\n"
        f"=== TỪ VỰNG ===\n{chr(10).join(vocab_lines)}\n\n"
        f"=== CÁCH DÙNG CÂU ===\n{chr(10).join(pattern_lines)}\n\n"
        f"{_quiz_trap_rules()}\n"
        f"YÊU CẦU SỐ LƯỢNG:\n"
        f"- vocab_quiz: ÍT NHẤT {QUIZ_PER_TYPE} câu về TỪ VỰNG / KÝ TỰ "
        f"(chọn nghĩa, chọn cách đọc, chọn chữ cái tương ứng âm thanh...)\n"
        f"- pattern_quiz: ÍT NHẤT {QUIZ_PER_TYPE} câu về MẪU CÂU/CÁCH DÙNG CÂU "
        f"(hoàn thành câu theo mẫu, chọn cấu trúc đúng...)\n"
        f"Mỗi câu: question, options (ĐÚNG 4 lựa chọn, không trùng nhau), answer_index (0-3), "
        f"explanation ngắn 1-2 câu. Đáp án phân bố đều A/B/C/D.\n"
        f"Chỉ trả về JSON với 2 key: vocab_quiz và pattern_quiz. Không thêm chữ nào ngoài JSON."
    )


def build_quiz_prompt_cd(lang_name: str, lesson: dict) -> str:
    """Nửa sau: chỉ sinh common_quiz + grammar_quiz (~20 câu, ~6-8k tokens output)."""
    common_lines = [f"- {s.get('sentence', '')}: {s.get('meaning_vi', '')}"
                    for s in lesson.get("common_sentences", [])]
    grammar_lines = []
    for i, g in enumerate(lesson.get("grammar", []), 1):
        grammar_lines.append(f"- Bài {i}: {g.get('title', '')} — {g.get('explanation', '')[:150]}")
    return (
        f"Bạn là soạn giả đề kiểm tra {lang_name}. Dựa trên NỘI DUNG bài học dưới đây, "
        f"soạn TRẮC NGHIỆM 4 lựa chọn — CHỈ 2 LOẠI sau:\n\n"
        f"=== CÂU THÔNG DỤNG ===\n{chr(10).join(common_lines)}\n\n"
        f"=== NGỮ PHÁP ===\n{chr(10).join(grammar_lines)}\n\n"
        f"{_quiz_trap_rules()}\n"
        f"YÊU CẦU SỐ LƯỢNG:\n"
        f"- common_quiz: ÍT NHẤT {QUIZ_PER_TYPE} câu về CÂU THÔNG DỤNG "
        f"(chọn câu phù hợp tình huống, chọn nghĩa...)\n"
        f"- grammar_quiz: ÍT NHẤT {QUIZ_PER_TYPE} câu về NGỮ PHÁP / QUY TẮC "
        f"(chia đúng, chọn trợ từ, tìm lỗi sai, quy tắc biến âm...)\n"
        f"Mỗi câu: question, options (ĐÚNG 4 lựa chọn, không trùng nhau), answer_index (0-3), "
        f"explanation ngắn 1-2 câu. Đáp án phân bố đều A/B/C/D.\n"
        f"Chỉ trả về JSON với 2 key: common_quiz và grammar_quiz. Không thêm chữ nào ngoài JSON."
    )


# ─── Parse & validate ──────────────────────────────────────────────────────────

def _strip_json(text: str) -> str:
    import re
    raw = (text or "").strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("Không tìm thấy JSON trong phản hồi AI")
    candidate = raw[start:end + 1]
    # Sửa lỗi phổ biến: trailing comma trước dấu đóng } hoặc ]
    repaired = re.sub(r",\s*([}\]])", r"\1", candidate)
    return repaired


def parse_curriculum_json(text: str, start_day: int = 1) -> dict:
    data = json.loads(_strip_json(text))
    days_out = []
    for d in data.get("days") or []:
        if not isinstance(d, dict):
            continue
        try:
            day_num = int(d.get("day", 0))
        except (TypeError, ValueError):
            continue
        if day_num <= 0:
            continue
        words_out = []
        for w in d.get("words") or []:
            if isinstance(w, dict) and str(w.get("word", "")).strip():
                words_out.append({
                    "word": str(w.get("word")).strip(),
                    "pronunciation": str(w.get("pronunciation", "")).strip(),
                    "meaning_vi": str(w.get("meaning_vi", "")).strip(),
                })
        days_out.append({
            "day": day_num,
            "title": str(d.get("title", "")).strip(),
            "phase": str(d.get("phase", "")).strip(),
            "words": words_out,
        })
    if not days_out:
        raise ValueError("Giáo trình trả về không có ngày hợp lệ")
    days_out.sort(key=lambda x: x["day"])
    # Chuẩn hóa lại đánh số start_day .. start_day + N - 1
    for i, d in enumerate(days_out, start_day):
        d["day"] = i
    return {"days": days_out}


# ─── Backbone 3-Layer Universal Curriculum Architecture ────────────────────────

def build_stage_universal_template(stage_idx: int, target_days: int) -> list:
    """Tạo Khung Template phổ quát (Layer 1) cho Chặng stage_idx gồm đúng target_days slots.
    Bảo đảm quy tắc Ôn tập xoắn ốc '6+1' vào ngày 7, 14, 21, 28... và ngày Tổng kết chặng ở slot cuối."""
    STAGE_POOLS = {
        0: [
            ("CHỮ VIẾT", "Tổng quan ngôn ngữ, nguồn gốc & hệ thống chữ viết"),
            ("CHỮ VIẾT", "Bảng chữ cái & Âm vị cơ bản — Nhóm 1 (Nguyên âm cốt lõi)"),
            ("CHỮ VIẾT", "Bảng chữ cái & Âm vị cơ bản — Nhóm 2 (Phụ âm hàng đầu)"),
            ("CHỮ VIẾT", "Bảng chữ cái & Âm vị cơ bản — Nhóm 3 (Phụ âm mở rộng)"),
            ("CHỮ VIẾT", "Bảng chữ cái & Âm vị cơ bản — Nhóm 4 (Phụ âm kết thúc / Ký tự đặc biệt)"),
            ("PHÁT ÂM", "Hệ thống phiên âm quốc tế & Ký âm La-tinh (IPA / Transliteration)"),
            ("ÔN TẬP TUẦN", "ÔN TẬP TUẦN 1: Nhận dạng ký tự & Phát âm khẩu hình chuẩn"),
            ("PHÁT ÂM", "Thanh điệu, Trọng âm từ & Ngữ điệu câu (Pitch Accent / Tones / Stress)"),
            ("PHÁT ÂM", "Quy tắc biến âm, Âm ngắt, Âm kéo dài & Trường âm"),
            ("PHÁT ÂM", "Chữ ghép, Âm đôi & Âm tiết phức hợp (Yōon / Diphthongs / Ligatures)"),
            ("CHỮ VIẾT", "Hệ chữ thứ 2 hoặc Chữ in hoa / Từ mượn ngoại lai — Phần 1"),
            ("CHỮ VIẾT", "Hệ chữ thứ 2 hoặc Chữ in hoa / Từ mượn ngoại lai — Phần 2"),
            ("CHỮ VIẾT", "Hệ chữ tượng hình / Bộ thủ căn bản hoặc Quy tắc đánh dấu phụ"),
            ("ÔN TẬP TUẦN", "ÔN TẬP TUẦN 2: Phân biệt âm vị & Luyện viết chữ cái lưu loát"),
            ("CHỮ VIẾT", "Dấu câu, Quy tắc viết hoa & Trình bày văn bản"),
            ("CHỮ VIẾT", "Phương pháp gõ bàn phím, Bộ gõ điện tử & Nhập liệu (IME / Keyboard)"),
            ("PHÁT ÂM", "Phân biệt các cặp âm dễ nhầm lẫn — Nhóm 1"),
            ("PHÁT ÂM", "Phân biệt các cặp âm dễ nhầm lẫn — Nhóm 2"),
            ("PHÁT ÂM", "Nhịp điệu câu nói, Độ dài âm tiết & Tốc độ phát âm tự nhiên"),
            ("PHÁT ÂM", "Quy tắc nối âm, Liên âm & Nuốt âm trong văn nói đời thường"),
            ("ÔN TẬP TUẦN", "ÔN TẬP TUẦN 3: Shadowing & Luyện nghe phản xạ âm vị"),
            ("TỪ ĐƠN", "Hệ thống chữ số, Số đếm căn bản & Đơn vị đo lường sơ đẳng"),
            ("PHÁT ÂM", "Khắc phục lỗi phát âm đặc trưng người Việt hay mắc"),
            ("TỪ ĐƠN", "Từ gốc ngoại lai, Từ mượn quốc tế quen thuộc"),
            ("CHỮ VIẾT", "Kỹ thuật đọc nhanh & Nhận diện ký tự tức thì (Sight Recognition)"),
            ("CHỮ VIẾT", "Quy tắc bút thuận, Thứ tự nét viết & Luyện chữ đẹp"),
            ("CHỮ VIẾT", "Phương pháp tra từ điển & Kỹ thuật ghi nhớ chữ cái (Mnemonics)"),
            ("ÔN TẬP TUẦN", "ÔN TẬP TUẦN 4: Kiểm tra tổng hợp kỹ năng nhận diện & Viết chữ"),
            ("PHÁT ÂM", "Luyện tập ngữ điệu câu hỏi, câu khẳng định & câu cảm thán"),
            ("ÔN TẬP TUẦN", "TỔNG KẾT CHẶNG 1: Đánh giá toàn diện năng lực phát âm & Chữ viết"),
        ],
        1: [
            ("TỪ ĐƠN", "Số đếm từ 1 đến 100 & Các phép tính cơ bản"),
            ("TỪ ĐƠN", "Đại từ nhân xưng (Tôi, Bạn, Anh ấy, Cô ấy, Chúng tôi, Họ)"),
            ("GIAO TIẾP", "Chào hỏi sinh tồn, Tạm biệt, Cảm ơn & Xin lỗi"),
            ("TỪ ĐƠN", "Thời gian: Giờ giấc, Buổi trong ngày & Thứ ngày tháng"),
            ("TỪ ĐƠN", "Màu sắc cơ bản & Hình khối xung quanh"),
            ("TỪ ĐƠN", "Gia đình & Xưng hô giữa các thế hệ"),
            ("ÔN TẬP TUẦN", "ÔN TẬP TUẦN 1: Luyện phản xạ ghép từ & Chào hỏi sinh tồn"),
            ("TỪ ĐƠN", "Đồ vật cá nhân & Vật dụng trong phòng"),
            ("TỪ ĐƠN", "Nghề nghiệp phổ biến & Nơi làm việc"),
            ("TỪ ĐƠN", "Thực phẩm sinh tồn, Rau củ quả & Đồ uống hàng ngày"),
            ("TỪ ĐƠN", "Động từ sinh tồn cơ bản: Ăn, Uống, Đi, Đến, Mua, Xem"),
            ("NGỮ PHÁP", "Cấu trúc câu đơn khẳng định S-V-O & Trợ từ cốt lõi"),
            ("NGỮ PHÁP", "Cấu trúc câu phủ định & Trợ từ nghi vấn căn bản"),
            ("ÔN TẬP TUẦN", "ÔN TẬP TUẦN 2: Luyện đặt câu đơn & Mẫu câu khẳng định/phủ định"),
            ("MẪU CÂU", "Đại từ chỉ định không gian: Đây, Đó, Kia, Đâu (This/That/Here/There)"),
            ("MẪU CÂU", "Câu hỏi nghi vấn Wh-: Cái gì? (What?) & Ai? (Who?)"),
            ("MẪU CÂU", "Câu hỏi nghi vấn Wh-: Ở đâu? (Where?) & Khi nào? (When?)"),
            ("MẪU CÂU", "Câu hỏi nghi vấn Wh-: Tại sao? (Why?) & Thế nào? (How?)"),
            ("TỪ ĐƠN", "Số đếm hàng trăm, hàng nghìn & Đơn vị tiền tệ thanh toán"),
            ("MẪU CÂU", "Hỏi giá tiền & Mua đồ sinh tồn đơn giản"),
            ("ÔN TẬP TUẦN", "ÔN TẬP TUẦN 3: Đặt câu hỏi nghi vấn & Giao dịch mua bán đơn giản"),
            ("TỪ ĐƠN", "Tính từ cơ bản chỉ kích thước, trạng thái & cảm xúc"),
            ("NGỮ PHÁP", "Mẫu câu miêu tả tính chất với Tính từ"),
            ("TỪ ĐƠN", "Vị trí không gian: Trên, Dưới, Trong, Ngoài, Trước, Sau"),
            ("MẪU CÂU", "Mẫu câu chỉ sự tồn tại: Có cái gì ở đâu (There is / There are)"),
            ("GIAO TIẾP", "Giới thiệu bản thân căn bản (Tên, Tuổi, Quốc tịch, Nghề nghiệp)"),
            ("GIAO TIẾP", "Các câu khẩu lệnh & Hướng dẫn sinh tồn trong lớp học/nơi công cộng"),
            ("ÔN TẬP TUẦN", "ÔN TẬP TUẦN 4: Giới thiệu bản thân & Miêu tả không gian xung quanh"),
            ("GIAO TIẾP", "Từ đệm, Cụm từ phản hồi tự nhiên & Phép lịch sự tối thiểu"),
            ("TỪ ĐƠN", "Phương tiện đi lại sinh tồn (Xe buýt, Tàu, Taxi, Đi bộ)"),
            ("MẪU CÂU", "Hỏi và chỉ địa điểm đơn giản (Nhà vệ sinh, Ga tàu, Khách sạn)"),
            ("NGỮ PHÁP", "Động từ chỉ ý muốn: Muốn làm gì / Cần cái gì"),
            ("GIAO TIẾP", "Xin phép & Yêu cầu giúp đỡ khẩn cấp (Help, Excuse me)"),
            ("TỪ ĐƠN", "Các bộ phận cơ bản trên cơ thể con người"),
            ("ÔN TẬP TUẦN", "ÔN TẬP TUẦN 5: Xử lý tình huống khẩn cấp & Xin trợ giúp sinh tồn"),
            ("NGỮ PHÁP", "Tổng hợp các mẫu câu đơn và từ nối căn bản"),
            ("GIAO TIẾP", "Thực hành hội thoại sinh tồn hoàn chỉnh 3 phút"),
            ("ÔN TẬP TUẦN", "TỔNG KẾT CHẶNG 2: Đánh giá toàn diện năng lực giao tiếp sinh tồn"),
        ],
        2: [
            # ── Nhóm 1: Mua sắm, Ăn uống, Di chuyển ──
            ("GIAO TIẾP", "Mua sắm: Hỏi size, thử đồ, mặc cả & chính sách đổi trả"),
            ("GIAO TIẾP", "Siêu thị: Tìm hàng hóa trên kệ, so sánh sản phẩm & thanh toán tự động"),
            ("GIAO TIẾP", "Chợ truyền thống & Ẩm thực đường phố: Mặc cả & mua đồ tươi sống"),
            ("GIAO TIẾP", "Nhà hàng: Đặt bàn, xem menu, gọi món & yêu cầu đặc biệt"),
            ("GIAO TIẾP", "Nhà hàng: Thanh toán, tách hóa đơn & văn hóa tiền tip"),
            ("GIAO TIẾP", "Ẩm thực: Mô tả hương vị, kết cấu món ăn & Gợi ý món ngon cho bạn bè"),
            ("GIAO TIẾP", "Giao thông: Mua vé tàu/xe, hỏi tuyến đường & chuyển tuyến"),
            ("GIAO TIẾP", "Hỏi đường chi tiết: Rẽ trái, rẽ phải, đi thẳng, đối diện, cạnh bên"),
            ("GIAO TIẾP", "Sân bay & Ga tàu: Thủ tục check-in, kiểm tra hành lý & lên tàu bay"),
            ("GIAO TIẾP", "Di chuyển nâng cao: Thuê xe, dùng bản đồ GPS & xử lý tình huống lạc đường"),
            # ── Nhóm 2: Thời tiết, Sức khỏe, Nhà ở ──
            ("TỪ VỰNG CHỦ ĐỀ", "Thời tiết, mùa trong năm, nhiệt độ & dự báo thời tiết"),
            ("GIAO TIẾP", "Sức khỏe: Miêu tả triệu chứng bệnh, đau ốm tại nhà thuốc/phòng khám"),
            ("GIAO TIẾP", "Bệnh viện: Đặt lịch khám, nhận thuốc theo toa & thủ tục bảo hiểm y tế"),
            ("GIAO TIẾP", "Nhà ở: Tìm phòng trọ, hỏi giá thuê, tiền cọc & tiện ích đi kèm"),
            ("GIAO TIẾP", "Nhà ở nâng cao: Mô tả phòng, đồ nội thất & tự trang trí không gian sống"),
            ("GIAO TIẾP", "Sinh hoạt: Lịch thu gom rác, sử dụng thiết bị điện gia dụng & nội quy"),
            ("GIAO TIẾP", "Khẩn cấp: Gọi cảnh sát, gọi cứu thương & báo cháy nhanh chóng"),
            # ── Nhóm 3: Giải trí, Văn hóa, Kết bạn ──
            ("TỪ VỰNG CHỦ ĐỀ", "Sở thích cá nhân, hoạt động giải trí cuối tuần & thói quen hàng ngày"),
            ("TỪ VỰNG CHỦ ĐỀ", "Các môn thể thao, rèn luyện sức khỏe & lối sống lành mạnh"),
            ("TỪ VỰNG CHỦ ĐỀ", "Âm nhạc: Thể loại, nhạc cụ & kể về nghệ sĩ/ban nhạc yêu thích"),
            ("TỪ VỰNG CHỦ ĐỀ", "Điện ảnh: Thể loại phim, tóm tắt cốt truyện & đánh giá phim ngắn"),
            ("TỪ VỰNG CHỦ ĐỀ", "Sách & Đọc: Thể loại sách, giới thiệu cuốn sách hay & thói quen đọc"),
            ("GIAO TIẾP", "Giải trí tập thể: Rạp chiếu phim, nhà hát, karaoke & câu lạc bộ"),
            ("GIAO TIẾP", "Thiên nhiên & hoạt động ngoài trời: Công viên, leo núi, picnic"),
            ("GIAO TIẾP", "Lễ hội địa phương, ngày kỷ niệm & sự kiện cộng đồng đặc sắc"),
            ("GIAO TIẾP", "Kết bạn người bản địa: Hỏi thông tin liên lạc & giữ kết nối mạng xã hội"),
            ("GIAO TIẾP", "Du lịch: Đặt phòng khách sạn, check-in, check-out & dịch vụ phòng"),
            ("GIAO TIẾP", "Địa danh nổi tiếng: Mua vé tham quan & thuê hướng dẫn viên địa phương"),
            # ── Nhóm 4: Quan hệ xã hội, Cảm xúc ──
            ("GIAO TIẾP", "Biểu đạt cảm xúc tự nhiên: Vui mừng, buồn bã, lo lắng & tức giận"),
            ("GIAO TIẾP", "Miêu tả ngoại hình, vóc dáng & phong cách ăn mặc của người khác"),
            ("GIAO TIẾP", "Miêu tả tính cách, phẩm chất & thái độ sống của bạn bè/đồng nghiệp"),
            ("GIAO TIẾP", "Mời mọc, rủ rê bạn bè tham gia sự kiện & cách nhận lời/từ chối khéo"),
            ("GIAO TIẾP", "Khen ngợi người khác & cách đáp lại lời khen một cách tự nhiên"),
            ("GIAO TIẾP", "Thăm nhà bạn bè: Nghi thức mang quà, chào chủ nhà & cảm ơn bữa ăn"),
            ("GIAO TIẾP", "Lễ tặng quà: Sinh nhật, lễ tết truyền thống & quà cảm ơn ý nghĩa"),
            ("GIAO TIẾP", "Làm đẹp & chăm sóc cá nhân: Cắt tóc, làm móng & spa thư giãn"),
            ("TỪ VỰNG CHỦ ĐỀ", "Thời trang & phong cách: Xu hướng, mix đồ & mua sắm trực tuyến"),
            # ── Nhóm 5: Ngữ pháp cốt lõi A1-A2 ──
            ("NGỮ PHÁP", "Thì Quá khứ đơn: Kể lại trải nghiệm chuyến đi & các sự việc đã qua"),
            ("NGỮ PHÁP", "Thì Quá khứ tiếp diễn: Mô tả hành động đang diễn ra trong quá khứ"),
            ("NGỮ PHÁP", "Thì Tương lai gần & Tương lai đơn: Diễn đạt dự định và kế hoạch"),
            ("NGỮ PHÁP", "Cấu trúc So sánh hơn & So sánh nhất giữa hai hoặc nhiều đối tượng"),
            ("NGỮ PHÁP", "Thể Khả năng: Diễn đạt những việc mình có thể hoặc không thể làm"),
            ("NGỮ PHÁP", "Thể Mệnh lệnh & Lời yêu cầu lịch sự trong giao tiếp hàng ngày"),
            ("NGỮ PHÁP", "Thể Cấm đoán nhẹ nhàng & Lời khuyên nên/không nên làm gì"),
            ("NGỮ PHÁP", "Liên từ nguyên nhân & kết quả (Bởi vì, Do đó, Vì vậy)"),
            ("NGỮ PHÁP", "Liên từ thời gian: Trước khi, Sau khi, Trong khi & Kể từ khi"),
            ("NGỮ PHÁP", "Mệnh đề quan hệ căn bản: Người mà, Thứ mà (who, which, that)"),
            ("NGỮ PHÁP", "Trạng từ chỉ tần suất & thói quen: Luôn, Thường, Đôi khi, Hiếm khi"),
            ("NGỮ PHÁP", "Câu hỏi gián tiếp: Bạn biết không..., Tôi tự hỏi liệu..."),
            ("NGỮ PHÁP", "Thì Hiện tại tiếp diễn vs Hiện tại đơn: Phân biệt sắc thái"),
            ("NGỮ PHÁP", "Động từ khuyết thiếu nâng cao: Should, Must, Might & Would trong các tình huống"),
            # ── Nhóm 6: Cuộc sống số, Ngân hàng, Bưu điện ──
            ("GIAO TIẾP", "Ngân hàng: Mở tài khoản, rút tiền ATM & chuyển khoản trực tuyến"),
            ("GIAO TIẾP", "Bưu điện: Gửi bưu kiện trong nước & quốc tế, theo dõi trạng thái"),
            ("GIAO TIẾP", "Học tiếng tại trường địa phương: Đăng ký khóa học, hỏi lịch học & học phí"),
            ("GIAO TIẾP", "Cuộc sống số: Dùng điện thoại thông minh, cài app & kết nối Wi-Fi công cộng"),
            ("GIAO TIẾP", "Đặt hàng trực tuyến: Tìm sản phẩm, thanh toán online & theo dõi giao hàng"),
            ("TỪ VỰNG CHỦ ĐỀ", "Vật nuôi & thú cưng: Mô tả, chăm sóc & đưa đến phòng khám thú y"),
            # ── Nhóm 7: Kỹ năng học ngôn ngữ & Văn hóa so sánh ──
            ("VĂN HOÁ", "Phân biệt văn phong thân mật vs lịch sự trong tình huống thực tế"),
            ("VĂN HOÁ", "Khám phá văn hóa bản địa: Phong tục tập quán & điều cần tránh"),
            ("VĂN HOÁ", "Quy tắc ứng xử nơi công cộng & lối sống văn minh đô thị"),
            ("NGỮ PHÁP", "Kể chuyện ngắn & chia sẻ kinh nghiệm cuối tuần với bạn bè"),
            ("NGỮ PHÁP", "Phương pháp cải thiện kỹ năng nghe: Podcast, nhạc & phim có phụ đề"),
            ("NGỮ PHÁP", "Diễn đạt sự đồng ý & không đồng ý một cách lịch sự và tự nhiên"),
            ("NGỮ PHÁP", "Tổng hợp A1-A2: Luyện đối thoại toàn diện 10 phút về chủ đề tự chọn"),
            # ── Nhóm 8: Bổ sung mở rộng A2 ──
            ("GIAO TIẾP", "Môi trường & Thiên nhiên: Bảo vệ môi trường, tái chế rác thải & sống xanh"),
            ("GIAO TIẾP", "Cộng đồng & Tình nguyện: Tham gia hoạt động xã hội & từ thiện địa phương"),
            ("TỪ VỰNG CHỦ ĐỀ", "Nấu ăn tại nhà: Nguyên liệu, dụng cụ bếp & công thức đơn giản"),
            ("GIAO TIẾP", "Dịch vụ công cộng: Văn phòng chính quyền, làm thủ tục giấy tờ"),
            ("TỪ VỰNG CHỦ ĐỀ", "Khoa học & Khám phá: Vũ trụ, thiên nhiên & các phát minh đơn giản"),
            ("GIAO TIẾP", "Mạng xã hội & Nội dung số: Đăng bài, bình luận & chia sẻ an toàn"),
            ("GIAO TIẾP", "Trò chơi điện tử & Giải trí số: Từ vựng gaming & thể thao điện tử"),
            ("TỪ VỰNG CHỦ ĐỀ", "Tài chính cá nhân: Quản lý chi tiêu, tiết kiệm & mục tiêu tài chính"),
            ("TỪ VỰNG CHỦ ĐỀ", "Giáo dục & Học tập: Đại học, ngành học, bằng cấp & cơ hội học bổng"),
            ("GIAO TIẾP", "Phương tiện truyền thông: Đọc báo, xem tin tức & thảo luận thời sự"),
            ("TỪ VỰNG CHỦ ĐỀ", "Khí hậu & Thời tiết cực đoan: Bão, lũ lụt, hạn hán & ứng phó thảm họa"),
            ("GIAO TIẾP", "Nha khoa & Thẩm mỹ: Đặt lịch khám, mô tả vấn đề & chăm sóc sức khỏe"),
            ("GIAO TIẾP", "Hỏi thăm sức khỏe người thân & Diễn đạt quan tâm chân thành"),
            ("TỪ VỰNG CHỦ ĐỀ", "Nhà hàng chuyên đề: Buffet, fast food, fine dining & ăn chay"),
            ("GIAO TIẾP", "Tham quan bảo tàng, triển lãm & di tích lịch sử văn hóa"),
            # ── Nhóm 9: Trải nghiệm & Hoạt động thực tế A2+ ──
            ("GIAO TIẾP", "Du lịch biển & Hoạt động thể thao dưới nước: Lặn biển, chèo thuyền"),
            ("GIAO TIẾP", "Du lịch núi & Cắm trại dã ngoại: Chuẩn bị lều trại & an toàn sinh tồn"),
            ("GIAO TIẾP", "Khách sạn Homestay: Trải nghiệm sống cùng người bản địa & văn hóa địa phương"),
            ("GIAO TIẾP", "Mua sắm đồ lưu niệm & Đặc sản vùng miền làm quà cho gia đình"),
            ("GIAO TIẾP", "Cuộc sống về đêm & Khám phá phố đi bộ, chợ đêm ẩm thực"),
            ("TỪ VỰNG CHỦ ĐỀ", "Văn hóa trà & Cà phê: Các loại đồ uống, cách pha chế & văn hóa quán xá"),
            ("GIAO TIẾP", "Sự kiện âm nhạc ngoài trời & Lễ hội pháo hoa: Mua vé & trải nghiệm"),
            ("TỪ VỰNG CHỦ ĐỀ", "Nông nghiệp & Vùng quê: Mùa màng, đồng ruộng & đời sống nông thôn"),
            ("GIAO TIẾP", "Hỏi ý kiến & Nhờ bạn bè tư vấn trước khi đưa ra quyết định quan trọng"),
            ("GIAO TIẾP", "Kể lại một kỷ niệm đáng nhớ thời thơ ấu bằng các câu đơn giản"),
        ],
        3: [
            # ── Nhóm 1: Xin việc & Văn phòng căn bản ──
            ("GIAO TIẾP", "Phỏng vấn xin việc: Giới thiệu bản thân & trình bày thế mạnh chuyên môn"),
            ("GIAO TIẾP", "Phỏng vấn xin việc: Trả lời câu hỏi về kinh nghiệm & lý do ứng tuyển"),
            ("GIAO TIẾP", "Phỏng vấn xin việc: Hỏi ngược nhà tuyển dụng & đàm phán mức lương"),
            ("TỪ VỰNG CHỦ ĐỀ", "Cơ cấu tổ chức công ty, các phòng ban & chức danh công việc"),
            ("GIAO TIẾP", "Ngày đầu đi làm: Tự giới thiệu với đồng nghiệp & học nội quy công ty"),
            ("GIAO TIẾP", "Giao tiếp công sở hàng ngày: Chào hỏi, bàn giao việc & nhờ hỗ trợ"),
            ("GIAO TIẾP", "Viết Email công việc: Cấu trúc chuẩn, tiêu đề, lời chào & kết thư"),
            ("GIAO TIẾP", "Viết Email công việc: Đính kèm tài liệu, xác nhận thông tin & hẹn phản hồi"),
            ("GIAO TIẾP", "Viết Email từ chối lịch sự & Đề xuất phương án thay thế"),
            ("GIAO TIẾP", "Điện thoại công việc: Nhận cuộc gọi, chuyển máy & ghi lại lời nhắn"),
            # ── Nhóm 2: Họp hành, Thuyết trình & Đàm phán ──
            ("GIAO TIẾP", "Chuẩn bị họp: Gửi agenda, chuẩn bị tài liệu & đặt phòng họp"),
            ("GIAO TIẾP", "Họp nội bộ: Báo cáo tiến độ dự án, chỉ số KPI & khó khăn phát sinh"),
            ("GIAO TIẾP", "Thuyết trình ý tưởng: Mở đầu, dẫn dắt luận điểm & chuyển ý mượt mà"),
            ("GIAO TIẾP", "Thuyết trình ý tưởng: Trình bày giải pháp, dự toán kinh phí & kết luận"),
            ("GIAO TIẾP", "Thuyết trình: Xử lý câu hỏi khó & phản biện thuyết phục từ khán giả"),
            ("GIAO TIẾP", "Thảo luận nhóm: Bày tỏ quan điểm đồng tình, trung lập hoặc phản bác lịch sự"),
            ("GIAO TIẾP", "Đàm phán thương mại: Thỏa thuận giá cả, điều khoản giao hàng & chiết khấu"),
            ("GIAO TIẾP", "Đàm phán nâng cao: Chiến thuật BATNA & nghệ thuật đề xuất win-win"),
            ("GIAO TIẾP", "Viết biên bản cuộc họp (Meeting Minutes) & tổng kết hành động (Action Items)"),
            # ── Nhóm 3: Xử lý vấn đề & Dịch vụ ──
            ("GIAO TIẾP", "Xử lý sự cố: Tiếp nhận khiếu nại khách hàng & đưa ra phương án bồi thường"),
            ("GIAO TIẾP", "Dịch vụ khách hàng nâng cao: Quy trình leo thang & chính sách bảo hành"),
            ("GIAO TIẾP", "Quản lý phàn nàn qua email: Xin lỗi chuyên nghiệp & cam kết giải quyết"),
            ("GIAO TIẾP", "IT & Công nghệ: Mô tả sự cố kỹ thuật & yêu cầu hỗ trợ IT helpdesk"),
            # ── Nhóm 4: Quản lý & Chiến lược ──
            ("TỪ VỰNG CHỦ ĐỀ", "Quản lý dự án: Lập kế hoạch, phân công nhiệm vụ & theo dõi tiến độ"),
            ("TỪ VỰNG CHỦ ĐỀ", "Marketing & Truyền thông: Chiến dịch quảng cáo, phân tích đối thủ & KPI"),
            ("TỪ VỰNG CHỦ ĐỀ", "Tài chính cơ bản: Đọc báo cáo P&L, ngân sách phòng ban & chi phí vận hành"),
            ("TỪ VỰNG CHỦ ĐỀ", "Nhân sự: Quy trình tuyển dụng, đào tạo nhân viên mới & đánh giá hiệu suất"),
            ("TỪ VỰNG CHỦ ĐỀ", "Logistics & Vận chuyển: Đặt lịch giao hàng, theo dõi đơn & xử lý kho bãi"),
            ("TỪ VỰNG CHỦ ĐỀ", "Thương mại điện tử: Quản lý gian hàng online, chiến lược giá & đánh giá"),
            ("TỪ VỰNG CHỦ ĐỀ", "Phân tích SWOT: Điểm mạnh, điểm yếu, cơ hội & thách thức của doanh nghiệp"),
            ("TỪ VỰNG CHỦ ĐỀ", "Phân tích dữ liệu kinh doanh: Đọc Dashboard & trình bày xu hướng hàng tuần"),
            # ── Nhóm 5: Mạng lưới chuyên nghiệp ──
            ("GIAO TIẾP", "LinkedIn & mạng xã hội chuyên nghiệp: Tối ưu hồ sơ & networking hiệu quả"),
            ("GIAO TIẾP", "Xây dựng mạng lưới chuyên nghiệp: Gặp gỡ tại hội thảo & tiếp nối sau sự kiện"),
            ("GIAO TIẾP", "Đạo đức nghề nghiệp & văn hóa công sở quốc tế"),
            ("GIAO TIẾP", "Giao tiếp đa văn hóa trong môi trường làm việc quốc tế"),
            ("GIAO TIẾP", "Quản lý thời gian & ưu tiên công việc: Kỹ thuật Eisenhower Matrix"),
            ("GIAO TIẾP", "Phản hồi feedback xây dựng & kế hoạch cải thiện chuyên môn cá nhân"),
            # ── Nhóm 6: Ngữ pháp B1-B2 nâng cao ──
            ("NGỮ PHÁP", "Kính ngữ & khiêm nhường ngữ chuyên sâu trong giao tiếp với đối tác"),
            ("NGỮ PHÁP", "Câu điều kiện loại 1 & 2: Diễn đạt giả định và dự báo khả năng"),
            ("NGỮ PHÁP", "Câu điều kiện loại 3: Phân tích rủi ro & phản tư tình huống đã qua"),
            ("NGỮ PHÁP", "Thể Bị động chuyên ngành: Văn bản hành chính & báo cáo kỹ thuật"),
            ("NGỮ PHÁP", "Thể Sai khiến: Yêu cầu, phân công & ủy quyền trong quản lý"),
            ("NGỮ PHÁP", "Liên từ nâng cao: Tương phản (tuy nhiên, mặc dù), nhượng bộ, bổ sung luận cứ"),
            ("NGỮ PHÁP", "Mệnh đề quan hệ rút gọn & Cụm danh từ phức hợp trong văn bản chuyên ngành"),
            ("NGỮ PHÁP", "Cấu trúc đảo ngữ & nhấn mạnh: Not only..but also, Hardly...when"),
            ("NGỮ PHÁP", "Thì Hoàn thành hiện tại trong báo cáo tiến độ & hồi ký dự án"),
            ("NGỮ PHÁP", "Từ viết tắt & thuật ngữ doanh nghiệp quốc tế thông dụng (B2B, ROI, CRM)"),
            # ── Nhóm 7: Hợp đồng, Pháp lý & Báo cáo ──
            ("HỌC THUẬT", "Hợp đồng & điều khoản pháp lý cơ bản: Đọc hiểu & đặt câu hỏi luật sư"),
            ("HỌC THUẬT", "Viết báo cáo phân tích ngắn: Cấu trúc, dẫn chứng & kết luận kiến nghị"),
            ("HỌC THUẬT", "Viết tóm tắt điều hành (Executive Summary) cho dự án/báo cáo quan trọng"),
            ("HỌC THUẬT", "Thuật ngữ ngoại ngữ chuyên ngành: Y tế, pháp luật, kỹ thuật & tài chính"),
            ("HỌC THUẬT", "Kỹ năng thuyết phục & ảnh hưởng trong giao tiếp kinh doanh"),
            ("HỌC THUẬT", "Tổng hợp B1-B2: Mô phỏng buổi làm việc hoàn chỉnh với đối tác quốc tế"),
            # ── Nhóm 8: Bổ sung mở rộng B2 ──
            ("GIAO TIẾP", "Nghiên cứu thị trường: Thiết kế khảo sát & phân tích phản hồi khách hàng"),
            ("GIAO TIẾP", "Quản lý khủng hoảng truyền thông: Xử lý scandal & phát ngôn công khai"),
            ("GIAO TIẾP", "Sáng tạo & Đổi mới: Brainstorming, Design Thinking & Lean Startup"),
            ("GIAO TIẾP", "Hội thảo & Sự kiện doanh nghiệp: Tổ chức, dẫn chương trình & follow-up"),
            ("GIAO TIẾP", "Bán hàng & Telesales: Kịch bản gọi điện, xử lý từ chối & chốt đơn"),
            ("TỪ VỰNG CHỦ ĐỀ", "Pháp lý doanh nghiệp: Đăng ký kinh doanh, thuế & bảo vệ quyền sở hữu trí tuệ"),
            ("GIAO TIẾP", "Lãnh đạo & Quản lý nhóm: Động lực, giải quyết xung đột & xây dựng team"),
            ("TỪ VỰNG CHỦ ĐỀ", "Xuất nhập khẩu thực tế: Chứng từ hải quan, vận đơn & L/C"),
            ("GIAO TIẾP", "Coaching & Mentoring: Đặt câu hỏi khai thác tiềm năng & phản hồi phát triển"),
            ("TỪ VỰNG CHỦ ĐỀ", "Khởi nghiệp & Huy động vốn: Pitch deck, term sheet & vòng gọi vốn"),
            ("GIAO TIẾP", "Giao dịch bất động sản: Thuê, mua, thế chấp & thuật ngữ hợp đồng nhà đất"),
            ("GIAO TIẾP", "Hội nghị quốc tế: Thủ tục visa, giao thức ngoại giao & tiệc chiêu đãi"),
            ("NGỮ PHÁP", "Văn phong học thuật vs văn phong kinh doanh: Chuyển đổi linh hoạt"),
            ("NGỮ PHÁP", "Viết lại câu phức tạp thành câu rõ ràng & ngược lại (paraphrasing)"),
            ("NGỮ PHÁP", "Nhận biết & sửa lỗi ngữ pháp thường gặp của người Việt học ngoại ngữ"),
            ("HỌC THUẬT", "Đề xuất cải tiến quy trình & Quản lý thay đổi trong tổ chức"),
            ("HỌC THUẬT", "Phân tích chuỗi giá trị & Tối ưu hóa hiệu suất vận hành doanh nghiệp"),
            ("HỌC THUẬT", "Đọc hiểu tình huống kinh doanh thực tế (Business Case Study) & Phân tích chiến lược"),
            ("HỌC THUẬT", "Văn hóa sáng tạo trong doanh nghiệp: Tư duy phản biện & khuyến khích ý tưởng mới"),
            ("HỌC THUẬT", "Phân tích cạnh tranh ngành: Porter's Five Forces & Blue Ocean Strategy"),
            ("HỌC THUẬT", "Quản trị rủi ro doanh nghiệp: Nhận diện, đánh giá & kế hoạch ứng phó"),
            ("HỌC THUẬT", "Tài chính doanh nghiệp nâng cao: Định giá công ty, M&A & cơ cấu vốn"),
            ("HỌC THUẬT", "Kinh tế hành vi: Tại sao con người quyết định phi lý & ứng dụng trong marketing"),
            ("HỌC THUẬT", "Tổ chức học tập: Knowledge Management & chia sẻ kiến thức trong doanh nghiệp"),
            ("HỌC THUẬT", "Chuyển đổi số doanh nghiệp: Roadmap, OKR & đo lường hiệu quả số hóa"),
            ("HỌC THUẬT", "Phúc lợi nhân viên & Employer Branding: Thu hút & giữ chân nhân tài"),
            ("HỌC THUẬT", "Đạo đức AI & Trách nhiệm dữ liệu trong môi trường kinh doanh hiện đại"),
            ("HỌC THUẬT", "Kinh doanh bền vững: ESG, Carbon Footprint & Báo cáo phát triển bền vững"),
            ("HỌC THUẬT", "Phân tích xu hướng ngành trong 5-10 năm tới & Cơ hội cho doanh nghiệp"),
            # ── Nhóm 9: Chuyên sâu B2+ Vận hành & Quốc tế hóa ──
            ("HỌC THUẬT", "Mô hình Kinh tế tuần hoàn (Circular Economy) & Tái tạo tài nguyên"),
            ("HỌC THUẬT", "Tự động hóa quy trình & Ứng dụng Robotics trong chuỗi cung ứng hiện đại"),
            ("HỌC THUẬT", "An ninh chuỗi cung ứng toàn cầu & Quản lý gián đoạn kinh doanh"),
            ("HỌC THUẬT", "Đổi mới mở (Open Innovation) & Hợp tác chiến lược giữa các tập đoàn"),
            ("HỌC THUẬT", "Tối ưu hóa phễu bán hàng (Sales Funnel) & Tăng tỷ lệ chuyển đổi khách hàng"),
            ("HỌC THUẬT", "Xây dựng trải nghiệm khách hàng (Customer Experience - CX) xuất sắc"),
            ("HỌC THUẬT", "Văn hóa doanh nghiệp định hướng dữ liệu (Data-driven Culture)"),
            ("HỌC THUẬT", "Quản trị danh mục đầu tư dự án (Project Portfolio Management)"),
            ("HỌC THUẬT", "Phát triển sản phẩm mới: Từ ý tưởng sơ khai đến thương mại hóa toàn diện"),
            ("HỌC THUẬT", "Chiến lược định giá sản phẩm đa tầng (Tiered & Dynamic Pricing Strategy)"),
            ("HỌC THUẬT", "Giao tiếp trong tình huống chia tay đồng nghiệp, sa thải & chuyển giao công việc"),
            ("HỌC THUẬT", "Thuế quan quốc tế, chuyển giá (Transfer Pricing) & tuân thủ pháp luật thuế"),
            ("HỌC THUẬT", "Hệ thống quản lý chất lượng (ISO / Lean Six Sigma) trong sản xuất & dịch vụ"),
            ("HỌC THUẬT", "Nghệ thuật trình bày dữ liệu bằng đồ họa & Biểu đồ trực quan (Data Storytelling)"),
            ("HỌC THUẬT", "Kỹ năng phản biện báo cáo tài chính & Phát hiện điểm bất thường trong số liệu"),
            ("HỌC THUẬT", "Mạng lưới đối tác phân phối quốc tế (Global Channel Partner Management)"),
            ("HỌC THUẬT", "Quản lý quan hệ nhà đầu tư (Investor Relations - IR) & Báo cáo thường niên"),
            ("HỌC THUẬT", "Đàm phán giải quyết tranh chấp hợp đồng kinh tế ngoài tòa án (Mediation)"),
        ],
        4: [
            # ── Nhóm 1: Truyền thông & Báo chí ──
            ("HỌC THUẬT", "Đọc hiểu tin tức thời sự, chính trị xã hội & bình luận báo chí"),
            ("HỌC THUẬT", "Phân tích cấu trúc bài viết xã luận & nhận diện lập trường tác giả"),
            ("HỌC THUẬT", "Đọc hiểu bài phóng sự điều tra & phân biệt sự kiện vs ý kiến"),
            ("HỌC THUẬT", "Phân tích truyền thông xã hội: Nhận biết tin giả (fake news) & thông tin lệch lạc"),
            ("HỌC THUẬT", "Viết bài báo ngắn: Cấu trúc 5W1H & lối viết trực tiếp của báo chí"),
            # ── Nhóm 2: Kinh tế & Tài chính học thuật ──
            ("HỌC THUẬT", "Phân tích biểu đồ, xu hướng thị trường & số liệu thống kê kinh tế"),
            ("HỌC THUẬT", "Kinh tế vĩ mô: GDP, lạm phát, thất nghiệp & chính sách tiền tệ"),
            ("HỌC THUẬT", "Kinh tế vi mô: Cung cầu, co giãn giá & thị trường độc quyền"),
            ("HỌC THUẬT", "Thuật ngữ tài chính đầu tư: Chứng khoán, cổ phiếu, trái phiếu & quỹ ETF"),
            ("HỌC THUẬT", "Phân tích báo cáo tài chính doanh nghiệp: Balance Sheet, P&L & Cash Flow"),
            ("HỌC THUẬT", "Thương mại quốc tế: Xuất nhập khẩu, thuế quan, hiệp định FTA & WTO"),
            # ── Nhóm 3: Khoa học, Công nghệ & Môi trường ──
            ("HỌC THUẬT", "Thuyết trình chuyên đề khoa học, công nghệ & chuyển đổi số"),
            ("HỌC THUẬT", "Trí tuệ nhân tạo & Dữ liệu lớn: Khái niệm, ứng dụng & tác động xã hội"),
            ("HỌC THUẬT", "Môi trường & Biến đổi khí hậu: Thuật ngữ khoa học & Mục tiêu phát thải"),
            ("HỌC THUẬT", "Năng lượng tái tạo: Điện mặt trời, điện gió & lộ trình phát triển xanh"),
            ("HỌC THUẬT", "Y tế công cộng: Dịch bệnh, vaccine, hệ thống y tế & chính sách sức khỏe"),
            ("HỌC THUẬT", "Giáo dục so sánh: Hệ thống giáo dục các nước & xu hướng học tập toàn cầu"),
            # ── Nhóm 4: Triết học, Đạo đức & Xã hội ──
            ("HỌC THUẬT", "Nghệ thuật tranh biện logic: Xây dựng luận điểm, luận cứ & phản biện ngụy biện"),
            ("HỌC THUẬT", "Diễn đạt các khái niệm triết học, đạo đức học & giá trị nhân văn"),
            ("HỌC THUẬT", "Xã hội học: Bất bình đẳng, đa dạng văn hóa & xu hướng nhân khẩu học"),
            ("HỌC THUẬT", "Tâm lý học xã hội: Hành vi đám đông, thiên kiến nhận thức & ra quyết định"),
            ("HỌC THUẬT", "Đạo đức kinh doanh: CSR, phát triển bền vững & quản trị doanh nghiệp tốt"),
            # ── Nhóm 5: Văn học, Nghệ thuật & Văn hóa ──
            ("HỌC THUẬT", "Đọc hiểu tác phẩm văn học cổ điển & phân tích tâm lý nhân vật"),
            ("HỌC THUẬT", "Phân tích thơ: Hình ảnh ẩn dụ, nhịp điệu & thông điệp tầng sâu"),
            ("HỌC THUẬT", "Lịch sử nghệ thuật: Các trường phái hội họa & ảnh hưởng văn hóa"),
            ("HỌC THUẬT", "Điện ảnh học thuật: Ngôn ngữ điện ảnh, đạo diễn danh tiếng & phê bình phim"),
            ("HỌC THUẬT", "Âm nhạc cổ điển: Nhạc cụ giao hưởng, nhạc sĩ vĩ đại & cấu trúc bản nhạc"),
            ("HỌC THUẬT", "Kiến trúc & Thiết kế đô thị: Phong cách kiến trúc & quy hoạch thành phố"),
            # ── Nhóm 6: Viết học thuật & Tu từ học ──
            ("HỌC THUẬT", "Kỹ thuật viết bài luận học thuật (Academic Essay): Dàn ý & Thesis Statement"),
            ("HỌC THUẬT", "Viết luận phân tích: Trình bày bằng chứng, trích dẫn & APA/MLA citation"),
            ("HỌC THUẬT", "Viết luận lập luận: Phản biện phản đề & củng cố lập trường của tác giả"),
            ("HỌC THUẬT", "Cấu trúc câu đảo ngữ & kỹ thuật nhấn mạnh tu từ trong văn bản cao cấp"),
            ("HỌC THUẬT", "Các biện pháp tu từ: So sánh, ẩn dụ, liệt kê, câu hỏi tu từ & phúng dụ"),
            ("HỌC THUẬT", "Kỹ năng đọc nhanh học thuật: Skimming, scanning & ghi chú Cornell"),
            ("HỌC THUẬT", "Thuyết trình học thuật: Ngôn ngữ học thuật trang trọng vs thông thường"),
            # ── Nhóm 7: Pháp lý & Ngoại giao ──
            ("HỌC THUẬT", "Văn bản pháp lý: Thuật ngữ hợp đồng thương mại, quyền lợi & trách nhiệm"),
            ("HỌC THUẬT", "Pháp luật quốc tế: Nhân quyền, luật điều ước & tổ chức quốc tế (UN, WTO)"),
            ("HỌC THUẬT", "Ngoại giao quốc tế: Ngôn ngữ ngoại giao, thông cáo báo chí & tuyên bố chung"),
            ("HỌC THUẬT", "Chính trị so sánh: Hệ thống chính phủ, bầu cử & chính sách công"),
            # ── Nhóm 8: Ngữ pháp C1 nâng cao ──
            ("NGỮ PHÁP", "Cấu trúc câu phức hợp C1: Nhiều mệnh đề lồng nhau & quan hệ ngữ nghĩa"),
            ("NGỮ PHÁP", "Văn phong học thuật trang trọng vs văn phong báo chí thông thường"),
            ("NGỮ PHÁP", "Độ chính xác từ vựng học thuật: Từ đồng nghĩa học thuật & từ collocation"),
            ("NGỮ PHÁP", "Trích dẫn gián tiếp & trực tiếp trong văn bản học thuật"),
            ("NGỮ PHÁP", "Câu điều kiện hỗn hợp & Lối diễn đạt phỏng đoán học thuật (Hedging)"),
            # ── Nhóm 9: Chuyên ngành cụ thể ──
            ("HỌC THUẬT", "Khoa học máy tính & Lập trình: Thuật ngữ tiếng Anh chuyên ngành IT"),
            ("HỌC THUẬT", "Y học & Sinh học: Hệ cơ quan người, bệnh lý & công nghệ y tế"),
            ("HỌC THUẬT", "Vật lý & Thiên văn học: Vũ trụ, hạt cơ bản & thuyết tương đối"),
            ("HỌC THUẬT", "Lịch sử thế giới: Sự kiện trọng đại, nguyên nhân & ảnh hưởng đến hiện tại"),
            ("HỌC THUẬT", "Địa lý & Địa chính trị: Tài nguyên, quyền lực & xung đột quốc tế"),
            ("HỌC THUẬT", "Tổng hợp C1: Tranh biện chuyên đề học thuật toàn diện 15 phút"),
            # ── Nhóm 10: Bổ sung mở rộng C1 ──
            ("HỌC THUẬT", "Nhân học văn hóa: Nghiên cứu dân tộc học & Quan sát thực địa"),
            ("HỌC THUẬT", "Ngôn ngữ học ứng dụng: Phân tích diễn ngôn & Chiến lược giao tiếp"),
            ("HỌC THUẬT", "Phân tích phim nghệ thuật: Kỹ thuật làm phim, biểu tượng & ý nghĩa"),
            ("HỌC THUẬT", "Văn học thực nghiệm & Hậu hiện đại: Kỹ thuật tường thuật phi tuyến"),
            ("HỌC THUẬT", "Ngôn ngữ chính thống vs ngôn ngữ thiểu số: Bảo tồn & Phục hồi ngôn ngữ"),
            ("HỌC THUẬT", "Triết học ngôn ngữ: Ngữ nghĩa, Ngữ dụng & Hành vi lời nói (Speech Acts)"),
            ("HỌC THUẬT", "Hệ thống tư pháp so sánh: Common Law vs Civil Law & Trọng tài quốc tế"),
            ("HỌC THUẬT", "Thống kê & Nghiên cứu khoa học: Thiết kế thí nghiệm & Diễn giải kết quả"),
            ("HỌC THUẬT", "Tâm lý ngôn ngữ: Quá trình học ngôn ngữ thứ hai & Tiếp thu ngôn ngữ"),
            ("HỌC THUẬT", "Truyền thông đa phương tiện: Phân tích quảng cáo, hình ảnh & âm thanh"),
            ("HỌC THUẬT", "Chính sách công & Phân tích luật: Từ đề xuất đến triển khai thực tế"),
            ("HỌC THUẬT", "Quan hệ quốc tế: Lý thuyết Realism, Liberalism & Constructivism"),
            ("NGỮ PHÁP", "Phân tích văn bản học thuật C1+: Cấu trúc lập luận & chiến lược thuyết phục"),
            ("NGỮ PHÁP", "Phong cách học: Formal, Semi-formal, Informal trong các thể loại văn bản"),
            ("NGỮ PHÁP", "Hiện tượng ngữ pháp đặc thù: Ellipsis, Anaphora & Discourse Markers"),
            ("NGỮ PHÁP", "Chiến lược từ vựng C1: Word family, Prefix/Suffix & Etymology"),
            ("HỌC THUẬT", "Toán học & Thống kê trong nghiên cứu xã hội: Đọc hiểu & trình bày số liệu"),
            ("HỌC THUẬT", "Phân tích chính sách giáo dục: Cải cách, tiêu chuẩn & kết quả học tập"),
            ("HỌC THUẬT", "Văn hóa doanh nghiệp & Quản lý đa thế hệ (Gen X, Millennial, Gen Z)"),
            ("HỌC THUẬT", "Ngôn ngữ hòa giải & Giải quyết tranh chấp phi bạo lực"),
            ("HỌC THUẬT", "Địa chính trị năng lượng: Dầu mỏ, khí đốt & cạnh tranh quyền lực"),
            ("HỌC THUẬT", "Lý thuyết trò chơi (Game Theory) & Ứng dụng trong kinh tế & chiến lược"),
            ("HỌC THUẬT", "Phân tích văn học so sánh: Tác phẩm xuyên văn hóa & Dịch thuật văn học"),
            ("HỌC THUẬT", "Bảo tàng học & Di sản văn hóa: Bảo tồn, trưng bày & phổ biến kiến thức"),
            ("HỌC THUẬT", "Đổi mới xã hội: Kinh tế chia sẻ, Fintech & Tác động đến cộng đồng"),
            ("HỌC THUẬT", "Giải quyết vấn đề phức tạp: Tư duy hệ thống & Phân tích nhân quả đa chiều"),
            ("HỌC THUẬT", "Khoa học thần kinh nhận thức: Trí nhớ, chú ý & Tối ưu hóa học tập"),
            ("HỌC THUẬT", "Phát triển bền vững đô thị: Smart City, Hạ tầng xanh & Quy hoạch tương lai"),
            ("HỌC THUẬT", "Ngôn ngữ trong khủng hoảng: Diễn ngôn chiến tranh, thiên tai & đại dịch"),
            ("HỌC THUẬT", "Phân tích xu hướng văn hóa toàn cầu: Globalization, Glocalization & Hybridization"),
            ("HỌC THUẬT", "Tư duy phê phán nâng cao C1: Nhận biết lỗi lập luận & Xây dựng phản biện"),
            ("HỌC THUẬT", "Kinh tế văn hóa: Giá trị nghệ thuật, thị trường sáng tạo & quyền tác giả"),
            ("HỌC THUẬT", "Dân chủ số & Không gian mạng: Tự do ngôn luận, kiểm duyệt & an ninh mạng"),
            # ── Nhóm 11: Mở rộng Chuyên đề Học thuật Đỉnh cao C1 ──
            ("HỌC THUẬT", "Đạo đức sinh học (Bioethics): Chỉnh sửa gen, nhân bản & công nghệ tế bào gốc"),
            ("HỌC THUẬT", "Vật lý lượng tử & Máy tính lượng tử: Nguyên lý chồng chập & tiềm năng tương lai"),
            ("HỌC THUẬT", "Khảo cổ học & Cổ nhân học: Nguồn gốc loài người & các nền văn minh đã mất"),
            ("HỌC THUẬT", "Ngôn ngữ học lịch sử: Sự biến đổi ngữ âm, ngữ nghĩa qua hàng ngàn năm"),
            ("HỌC THUẬT", "Kinh tế phát triển: Bẫy thu nhập trung bình & chiến lược tăng trưởng bền vững"),
            ("HỌC THUẬT", "Luật sở hữu trí tuệ quốc tế: Bằng sáng chế, thương hiệu & bản quyền tác phẩm"),
            ("HỌC THUẬT", "Tâm lý học thần kinh: Cơ chế của cảm xúc, trực giác và hành vi ra quyết định"),
            ("HỌC THUẬT", "Văn hóa hậu hiện đại & Nghệ thuật khái niệm (Conceptual Art): Giải mã tác phẩm"),
            ("HỌC THUẬT", "Địa chính trị không gian vũ trụ: Vệ tinh, trạm không gian & luật vũ trụ quốc tế"),
            ("HỌC THUẬT", "Ngữ nghĩa học nhận thức (Cognitive Semantics): Cách bộ não gán nghĩa cho thế giới"),
            ("HỌC THUẬT", "Đô thị học & Lịch sử hình thành các siêu đô thị toàn cầu (Megacities)"),
            ("HỌC THUẬT", "Hệ thống an sinh xã hội so sánh: Mô hình Bắc Âu, Anglo-Saxon & Đông Á"),
        ],
        5: [
            # ── Nhóm 1: Thành ngữ, Slang & Ngôn ngữ phi chính thức ──
            ("THÀNH NGỮ & SLANG", "Thành ngữ dân gian phổ biến (Idioms): Nguồn gốc, ý nghĩa & cách dùng tự nhiên"),
            ("THÀNH NGỮ & SLANG", "Thành ngữ về cảm xúc: Vui, buồn, tức giận, sợ hãi & yêu thương"),
            ("THÀNH NGỮ & SLANG", "Thành ngữ về công việc, tiền bạc & thành công trong sự nghiệp"),
            ("THÀNH NGỮ & SLANG", "Thành ngữ về thiên nhiên, thực phẩm & động vật"),
            ("THÀNH NGỮ & SLANG", "Tiếng lóng giới trẻ đương đại, thuật ngữ Gen Z & văn hóa Internet"),
            ("THÀNH NGỮ & SLANG", "Tiếng lóng đường phố, hip-hop & subculture đô thị"),
            ("THÀNH NGỮ & SLANG", "Từ viết tắt, emoji ý nghĩa & lingo mạng xã hội thực dụng"),
            ("THÀNH NGỮ & SLANG", "Tiếng lóng nghề nghiệp: Y tế, pháp luật, kỹ thuật & thị trường tài chính"),
            ("THÀNH NGỮ & SLANG", "Cụm từ cố định (Fixed Phrases) & Collocations chuẩn người bản ngữ"),
            ("THÀNH NGỮ & SLANG", "Phrasal Verbs thông dụng nhất & cách dùng tự nhiên trong đối thoại"),
            ("THÀNH NGỮ & SLANG", "Phrasal Verbs chuyên nghiệp: Kinh doanh, học thuật & giao tiếp trang trọng"),
            # ── Nhóm 2: Văn hóa, Ngữ cảnh cao & Giao tiếp ẩn ──
            ("VĂN HOÁ", "Văn hóa giao tiếp ngữ cảnh cao (High-context): Đọc hiểu ý ngầm & tinh tế"),
            ("VĂN HOÁ", "Lối nói ẩn dụ (Metaphor), hoán dụ (Metonymy) & biểu tượng văn hóa"),
            ("VĂN HOÁ", "Nghệ thuật nói giảm, nói tránh (Euphemism) trong tình huống nhạy cảm"),
            ("VĂN HOÁ", "Sự im lặng trong văn hóa: Khi nào yên lặng = đồng ý, phản đối hay tôn trọng"),
            ("VĂN HOÁ", "Ngôn ngữ lịch sự bậc cao: Khiêm tốn thực sự vs khiêm tốn giả tạo"),
            ("VĂN HOÁ", "Tương tác xã hội phi ngôn ngữ: Cử chỉ, ánh mắt, khoảng cách & nụ cười"),
            ("VĂN HOÁ", "Ngôn ngữ biểu cảm trong tình bạn, tình yêu & mối quan hệ sâu sắc"),
            ("VĂN HOÁ", "Phương ngữ & khẩu ngữ đặc trưng theo từng vùng miền địa lý"),
            ("VĂN HOÁ", "Giọng địa phương: Phân biệt trọng âm, tốc độ & đặc điểm phát âm vùng miền"),
            ("VĂN HOÁ", "Văn hóa tranh cãi & Phản biện: Lịch sự hay thẳng thắn — khi nào phù hợp?"),
            # ── Nhóm 3: Hài hước, Chơi chữ & Nghệ thuật ngôn từ ──
            ("THÀNH NGỮ & SLANG", "Nghệ thuật khôi hài (Humor): Cấu trúc câu đùa & timing đúng lúc"),
            ("THÀNH NGỮ & SLANG", "Châm biếm (Sarcasm) & mỉa mai (Irony): Nhận biết & sử dụng an toàn"),
            ("THÀNH NGỮ & SLANG", "Chơi chữ (Puns & Wordplay): Đồng âm, đa nghĩa & câu đố ngôn ngữ"),
            ("THÀNH NGỮ & SLANG", "Câu chuyện hài người bản xứ kể: Tại sao buồn cười & bài học văn hóa"),
            # ── Nhóm 4: Văn học, Thơ ca & Nghệ thuật bản ngữ ──
            ("VĂN HOÁ", "Thơ ca & Ca dao: Vần điệu, hình ảnh & thông điệp tầng sâu"),
            ("VĂN HOÁ", "Ca từ âm nhạc hiện đại: Phân tích bài hát phổ biến & ý nghĩa ẩn"),
            ("VĂN HOÁ", "Văn học đương đại: Tác giả nổi bật, xu hướng & thế giới quan"),
            ("VĂN HOÁ", "Điển cố & điển tích cổ: Nguồn gốc văn học & cách người bản xứ dùng hàng ngày"),
            ("VĂN HOÁ", "Tục ngữ (Proverbs) & triết lý dân gian phản ánh tâm thức dân tộc"),
            ("VĂN HOÁ", "Nghệ thuật hùng biện (Rhetoric): Thuyết phục, kể chuyện & gây xúc cảm"),
            # ── Nhóm 5: Tư duy bản ngữ & Phong cách viết cao cấp ──
            ("VĂN HOÁ", "Tư duy bằng ngoại ngữ: Từ dịch trong đầu sang suy nghĩ trực tiếp"),
            ("VĂN HOÁ", "Phong cách viết người bản xứ: Ngắn gọn, súc tích & tự nhiên"),
            ("VĂN HOÁ", "Từ điển văn hóa: Các khái niệm không có từ tương đương trong tiếng Việt"),
            ("VĂN HOÁ", "Ngôn ngữ cảm xúc nâng cao: Biểu đạt 'buồn', 'nhớ nhà', 'cô đơn' đúng chuẩn bản ngữ"),
            ("VĂN HOÁ", "Phong cách kể chuyện (Storytelling): Mở đầu gây sốc, tình huống & cao trào"),
            # ── Nhóm 6: Đặc thù ngôn ngữ theo nghề & tình huống ──
            ("THÀNH NGỮ & SLANG", "Ngôn ngữ thể thao: Bình luận trực tiếp, mô tả pha bóng & cảm xúc khán đài"),
            ("THÀNH NGỮ & SLANG", "Ngôn ngữ ẩm thực cao cấp: Mô tả Michelin, phê bình ẩm thực & nấu ăn"),
            ("THÀNH NGỮ & SLANG", "Ngôn ngữ chính trị & vận động: Slogan, diễn văn & cách tiếp cận cử tri"),
            ("THÀNH NGỮ & SLANG", "Ngôn ngữ khoa học phổ thông: Giải thích khái niệm khoa học cho người bình thường"),
            ("THÀNH NGỮ & SLANG", "Ngôn ngữ quảng cáo & marketing: Tagline, call-to-action & copywriting"),
            # ── Nhóm 7: Capstone & Tổng hợp Bản xứ ──
            ("HỌC THUẬT", "Phương pháp học bản ngữ: Immersion, input comprehensible & output có chủ đích"),
            ("HỌC THUẬT", "Xây dựng thói quen nói bản ngữ: Shadowing người bản xứ thực tế mỗi ngày"),
            ("HỌC THUẬT", "Đồ án Capstone — Phần 1: Chọn đề tài & thu thập tư liệu nguyên bản bản ngữ"),
            ("HỌC THUẬT", "Đồ án Capstone — Phần 2: Phân tích ngôn ngữ chuyên sâu & biên dịch đối chiếu"),
            ("HỌC THUẬT", "Đồ án Capstone — Phần 3: Thuyết trình hoàn chỉnh dự án bằng ngoại ngữ thuần thục"),
            ("HỌC THUẬT", "Tự đánh giá năng lực C2: Bài kiểm tra chuẩn hóa & lộ trình duy trì bản ngữ"),
            # ── Nhóm 8: Bổ sung mở rộng C2 ──
            ("VĂN HOÁ", "Nghệ thuật trò chuyện bậc cao: Dẫn dắt chủ đề & chuyển ý linh hoạt"),
            ("VĂN HOÁ", "Ngôn ngữ thân mật đặc trưng nhóm: Biệt ngữ bạn thân, gia đình & đồng nghiệp lâu năm"),
            ("VĂN HOÁ", "Giao tiếp thế hệ: Khác biệt ngôn ngữ giữa người trẻ & người lớn tuổi"),
            ("THÀNH NGỮ & SLANG", "Thành ngữ thể thao & thành ngữ quân sự phổ biến trong văn nói thường ngày"),
            ("VĂN HOÁ", "Lịch sự ngôn ngữ qua các thời kỳ: Ngôn ngữ thay đổi thế nào theo thời gian"),
            ("VĂN HOÁ", "Ký ức văn hóa: Sự kiện lịch sử & cách người bản xứ nhắc đến chúng hàng ngày"),
            ("HỌC THUẬT", "Viết tường thuật bản ngữ: Hồi ký, Phóng sự & Tản văn cá nhân"),
            # ── Nhóm 9: Đỉnh cao Bản ngữ & Tinh hoa Văn hóa C2 ──
            ("VĂN HOÁ", "Văn hóa trà đạo, thưởng rượu & nghi thức ẩm thực cung đình truyền thống"),
            ("VĂN HOÁ", "Triết lý sống phương Đông & phương Tây: Vô thường, Khắc kỷ & Chánh niệm trong ngôn từ"),
            ("VĂN HOÁ", "Tiếng địa phương miền biển vs miền núi: Ngữ điệu & kho từ vựng dân gian độc đáo"),
            ("VĂN HOÁ", "Văn học thiếu nhi & truyện cổ tích kinh điển: Cội nguồn biểu tượng văn hóa dân tộc"),
            ("HỌC THUẬT", "Nghệ thuật đối đáp phong nhã & Ứng khẩu thơ văn trong giao tiếp thượng lưu"),
        ],
    }

    base_pool = STAGE_POOLS.get(stage_idx, STAGE_POOLS[0])
    slots = []
    for i in range(1, target_days + 1):
        is_last_day = (i == target_days)
        is_spiral_day = (i % 7 == 0) and not is_last_day

        if is_last_day:
            cat = "ÔN TẬP TUẦN"
            name = f"TỔNG KẾT CHẶNG {stage_idx + 1}: Đánh giá toàn diện năng lực và kiến thức Chặng {stage_idx + 1}"
            is_rev = True
        elif is_spiral_day:
            cat = "ÔN TẬP TUẦN"
            week_num = i // 7
            name = f"ÔN TẬP TUẦN {week_num}: Tổng hợp thực hành, phản xạ đối thoại & xử lý tình huống thực tế"
            is_rev = True
        else:
            pool_idx = (i - 1) % len(base_pool)
            cat, name = base_pool[pool_idx]
            cycle_num = (i - 1) // len(base_pool)
            if cycle_num > 0:
                name = f"{name} (Phần {cycle_num + 1})"
            if "ÔN TẬP" in name or "TỔNG KẾT" in name:
                cat = "TỪ VỰNG CHỦ ĐỀ" if stage_idx <= 2 else "GIAO TIẾP"
                name = f"Chủ đề ứng dụng thực hành số {i}: Mở rộng vốn từ và cấu trúc diễn đạt"
            is_rev = False

        slots.append({
            "slot_id": i,
            "stage_idx": stage_idx,
            "generic_name": name,
            "category": cat,
            "importance": "BẮT BUỘC",
            "is_review_day": is_rev,
            "is_ai_inserted": False,
            "needs_retry": False,
            "filled_day": None
        })

    return slots


def build_stage_adapt_prompt(lang_name: str, stage_info: dict, fsi_profile: dict, slots: list) -> str:
    """Prompt yêu cầu AI thích ứng (Adapt) tên chủ đề từ Generic Slots sang chủ đề cụ thể của ngôn ngữ."""
    s_num = stage_info["stage_num"]
    s_name = stage_info["name"]
    s_desc = stage_info["desc"]

    slots_brief = [
        {"slot_id": s["slot_id"], "generic_name": s["generic_name"], "category": s["category"]}
        for s in slots
    ]
    slots_json_str = json.dumps(slots_brief, ensure_ascii=False, indent=2)

    return (
        f"Bạn là chuyên gia thiết kế giáo trình {lang_name} theo chuẩn quốc tế.\n\n"
        f"CHẶNG MỤC TIÊU: Chặng {s_num}/6 — {s_name} ({len(slots)} ngày)\n"
        f"Phạm vi kiến thức: {s_desc}\n"
        f"Đặc thù ngôn ngữ: {fsi_profile['category_name']}\n\n"
        f"DANH SÁCH {len(slots)} KHUNG CHỦ ĐỀ PHỔ QUÁT CẦN ADAPT:\n"
        f"```json\n{slots_json_str}\n```\n\n"
        f"NHIỆM VỤ:\n"
        f"Hãy chuyển đổi (Adapt) từng generic_name trong danh sách trên thành TIÊU ĐỀ BÀI HỌC CỤ THỂ, "
        f"CHÍNH XÁC cho {lang_name} theo đúng chuẩn quốc tế (JLPT/HSK/TOPIK/CEFR).\n\n"
        f"QUY TẮC BẮT BUỘC:\n"
        f"1. Trả về ĐÚNG {len(slots)} items tương ứng với từng slot_id (từ 1 đến {len(slots)}).\n"
        f"2. Giữ nguyên ý nghĩa của các ngày [ÔN TẬP TUẦN] và [TỔNG KẾT CHẶNG] nhưng cụ thể hóa nội dung ôn cho {lang_name}.\n"
        f"3. title: Tiêu đề rõ ràng, sư phạm bằng tiếng Việt (kèm thuật ngữ gốc của {lang_name} nếu có, ví dụ: 'Hiragana hàng A (あ, い, う, え, お)').\n"
        f"4. category: Giữ nguyên hoặc tinh chỉnh cho chuẩn nhất.\n"
        f"5. importance: BẮT BUỘC.\n"
        f"6. Chỉ trả về JSON theo đúng schema, không thêm bất kỳ văn bản nào ngoài JSON."
    )


def build_stage_gap_insert_prompt(lang_name: str, stage_info: dict, fsi_profile: dict, adapted_slots: list) -> str:
    """Prompt yêu cầu AI rà soát xem còn chủ đề đặc thù quan trọng nào của ngôn ngữ bị thiếu không,
    và chỉ định chèn SAU slot_id nào để đảm bảo tính sư phạm logic."""
    s_num = stage_info["stage_num"]
    s_name = stage_info["name"]

    current_titles = [f"Slot {s['slot_id']}: {s.get('title', s.get('generic_name', ''))} ({s['category']})" for s in adapted_slots]
    titles_str = "\n".join(current_titles)

    return (
        f"Bạn là chuyên gia thẩm định giáo trình {lang_name}.\n\n"
        f"CHẶNG: Chặng {s_num}/6 — {s_name}\n"
        f"ĐẶC THÙ NGÔN NGỮ: {fsi_profile['category_name']}\n\n"
        f"DANH SÁCH CÁC CHỦ ĐỀ HIỆN TẠI TRONG CHẶNG:\n{titles_str}\n\n"
        f"NHIỆM VỤ:\n"
        f"Rà soát đối chiếu với chuẩn quốc tế của {lang_name}. Nếu phát hiện còn thiếu những chủ đề ĐẶC THÙ RẤT QUAN TRỌNG "
        f"(ví dụ: bộ thủ chữ Hán, thanh điệu đặc biệt, quy tắc biến âm phức tạp, trợ từ trọng điểm...) mà danh sách trên chưa có:\n"
        f"- Hãy đề xuất TỐI ĐA 3-8 chủ đề bổ sung.\n"
        f"- Với mỗi chủ đề bổ sung, BẮT BUỘC chỉ định `after_slot_id` (chèn sau slot nào để hợp lý nhất về mặt sư phạm).\n"
        f"- Nếu danh sách đã đầy đủ và không cần thêm gì, trả về `\"insertions\": []`.\n\n"
        f"Chỉ trả về JSON theo schema, không thêm lời dẫn."
    )


def build_master_backbone(language: str, fsi: dict, coord, log_fn=None, stop_check=None) -> dict:
    """Lập Master Backbone hoàn chỉnh cho toàn bộ 6 Chặng theo Kiến trúc 3 Lớp:
    - Layer 1: Universal Template Slots (Đảm bảo số lượng sàn cứng không bao giờ thiếu)
    - Layer 2: AI Adaptation (Adapt sang tên cụ thể từng ngôn ngữ, retry 2 lần + fallback)
    - Layer 3: AI Gap Insertion (Chèn các chủ đề đặc thù vào đúng vị trí sư phạm after_slot_id)
    """
    if log_fn is None:
        log_fn = print

    master_items = []
    pending_retries = 0
    total_base_slots = 0
    total_ai_inserted = 0

    log_fn(f"🦴 [Pass 1 • Khung Giáo Trình Master 3 Lớp] Bắt đầu thiết kế toàn bộ 6 Chặng chuẩn {fsi['category_name']}...")
    log_fn(f"   📋 Sàn kiến thức tối thiểu chuẩn quốc tế: {fsi['total_days']} ngày qua 6 Chặng.")

    for s_idx, st in enumerate(fsi["stages"]):
        if stop_check and stop_check():
            raise GenerationStopped()

        target_days = st["target_days"]
        total_base_slots += target_days
        log_fn(f"\n   ▶ [Chặng {st['stage_num']}/6] '{st['name']}' — Khởi tạo {target_days} slots nền tảng...")

        # Layer 1: Universal Template Slots
        base_slots = build_stage_universal_template(s_idx, target_days)

        # Layer 2: AI Adaptation (Thích ứng ngôn ngữ)
        adapted_slots = []
        adapt_success = False
        for attempt in range(1, 3):
            if stop_check and stop_check():
                raise GenerationStopped()
            log_fn(f"     ✦ Layer 2: AI đang đặt tên chuyên sâu cho {target_days} chủ đề (Lần {attempt}/2)...")
            res_adapt = coord.request(
                build_stage_adapt_prompt(language, st, fsi, base_slots),
                response_schema=ADAPT_STAGE_SCHEMA
            )
            if res_adapt.get("ok"):
                try:
                    data = json.loads(_strip_json(res_adapt.get("text", "")))
                    topics_list = data.get("topics", [])
                    if isinstance(topics_list, list) and len(topics_list) > 0:
                        topics_map = {}
                        for t in topics_list:
                            if isinstance(t, dict) and "slot_id" in t and "title" in t:
                                topics_map[int(t["slot_id"])] = t

                        for slot in base_slots:
                            s_id = slot["slot_id"]
                            item_copy = dict(slot)
                            if s_id in topics_map:
                                t_info = topics_map[s_id]
                                item_copy["title"] = str(t_info.get("title", slot["generic_name"])).strip()
                                if t_info.get("category"):
                                    item_copy["category"] = str(t_info["category"]).strip()
                            else:
                                item_copy["title"] = slot["generic_name"]
                            adapted_slots.append(item_copy)

                        adapt_success = True
                        log_fn(f"     ✓ Layer 2 thành công: Đã chuyển ngữ 100% {len(adapted_slots)} chủ đề Chặng {st['stage_num']}.")
                        break
                except Exception as e:
                    log_fn(f"     ⚠ Layer 2 JSON parse lỗi ({e}), thử lại...")

        if not adapt_success:
            log_fn(f"     ⚠️ Layer 2 AI không phản hồi sau 2 lần thử. Áp dụng Fallback Template gốc & Ghi chú hoàn thiện sau.")
            adapted_slots = []
            for slot in base_slots:
                item_copy = dict(slot)
                item_copy["title"] = slot["generic_name"]
                item_copy["needs_retry"] = True
                adapted_slots.append(item_copy)
            pending_retries += len(adapted_slots)

        # Layer 3: Gap Insertion (AI bổ sung đặc thù vào đúng vị trí sau slot chỉ định)
        if adapt_success:
            log_fn(f"     ✦ Layer 3: AI rà soát lỗ hổng kiến thức đặc thù & chèn vào đúng vị trí sư phạm...")
            res_gap = coord.request(
                build_stage_gap_insert_prompt(language, st, fsi, adapted_slots),
                response_schema=GAP_INSERT_SCHEMA
            )
            if res_gap.get("ok"):
                try:
                    gdata = json.loads(_strip_json(res_gap.get("text", "")))
                    ins_list = gdata.get("insertions", [])
                    if isinstance(ins_list, list) and ins_list:
                        ins_by_slot = {}
                        for ins in ins_list:
                            if isinstance(ins, dict) and ins.get("title"):
                                aft = int(ins.get("after_slot_id", len(adapted_slots)))
                                ins_by_slot.setdefault(aft, []).append(ins)

                        merged = []
                        for slot in adapted_slots:
                            merged.append(slot)
                            s_id = slot["slot_id"]
                            if s_id in ins_by_slot:
                                for ins_item in ins_by_slot[s_id]:
                                    merged.append({
                                        "slot_id": s_id,
                                        "stage_idx": s_idx,
                                        "generic_name": ins_item.get("title", ""),
                                        "title": ins_item.get("title", ""),
                                        "category": ins_item.get("category", slot["category"]),
                                        "importance": ins_item.get("importance", "NÊN HỌC"),
                                        "is_review_day": False,
                                        "is_ai_inserted": True,
                                        "needs_retry": False,
                                        "filled_day": None
                                    })
                                    total_ai_inserted += 1
                        adapted_slots = merged
                        log_fn(f"     ✓ Layer 3: Đã bổ sung thành công {len(ins_list)} chủ đề trọng điểm đặc thù vào đúng vị trí.")
                except Exception as e:
                    log_fn(f"     ⚠ Layer 3 Gap review pass: {e}")

        master_items.extend(adapted_slots)

    # Đánh số id liên tục từ 1 đến N
    for i, it in enumerate(master_items, 1):
        it["id"] = i

    log_fn(f"\n✅ MASTER BACKBONE HOÀN THIỆN XUẤT SẮC:")
    log_fn(f"   • Tổng số ngày thực tế: {len(master_items)} ngày (Template cứng: {total_base_slots} + AI bổ sung: {total_ai_inserted}).")
    log_fn(f"   • Số chủ đề cần hoàn thiện sau (pending retries): {pending_retries}.")

    return {
        "level": "⭐ Trọn gói: Từ con số 0 đến Như người bản xứ",
        "fsi_category": fsi["category_name"],
        "template_base_count": total_base_slots,
        "ai_inserted_count": total_ai_inserted,
        "pending_retry_count": pending_retries,
        "total_target_days": len(master_items),
        "items": master_items
    }
    return repaired


def parse_curriculum_json(text: str, start_day: int = 1) -> dict:
    data = json.loads(_strip_json(text))
    days_out = []
    for d in data.get("days") or []:
        if not isinstance(d, dict):
            continue
        try:
            day_num = int(d.get("day", 0))
        except (TypeError, ValueError):
            continue
        if day_num <= 0:
            continue
        words_out = []
        for w in d.get("words") or []:
            if isinstance(w, dict) and str(w.get("word", "")).strip():
                words_out.append({
                    "word": str(w.get("word")).strip(),
                    "pronunciation": str(w.get("pronunciation", "")).strip(),
                    "meaning_vi": str(w.get("meaning_vi", "")).strip(),
                })
        days_out.append({
            "day": day_num,
            "title": str(d.get("title", "")).strip(),
            "phase": str(d.get("phase", "")).strip(),
            "words": words_out,
        })
    if not days_out:
        raise ValueError("Giáo trình trả về không có ngày hợp lệ")
    days_out.sort(key=lambda x: x["day"])
    # Chuẩn hóa lại đánh số start_day .. start_day + N - 1
    for i, d in enumerate(days_out, start_day):
        d["day"] = i
    return {"days": days_out}


# ─── Backbone: Khung giáo trình bắt buộc ────────────────────────────────────────

def build_stage_backbone_prompt(lang_name: str, stage_info: dict, fsi_profile: dict,
                                completed_topics: list = None) -> str:
    """Prompt yêu cầu AI tạo khung giáo trình chi tiết cho 1 Chặng cụ thể (Stage).
    Đảm bảo mỗi Chặng có chiều sâu tối đa, tự động chèn ngày Ôn tập xoắn ốc (ngày thứ 7, 14, 21...),
    và triệt tiêu hoàn toàn trùng lặp với các chặng trước."""
    s_num = stage_info["stage_num"]
    s_name = stage_info["name"]
    s_desc = stage_info["desc"]
    target_days = stage_info["target_days"]
    start_day = stage_info["start_day"]

    typology_note = (
        f"⭐ ĐẶC THÙ NGÔN NGỮ {lang_name.upper()} ({fsi_profile['category_name']}):\n"
        f"- Phải bám sát chuẩn quốc tế tương ứng (JLPT N5-N1 / HSK 1-6 / TOPIK I-II / CEFR A1-C2).\n"
        f"- Cần đúng {target_days} chủ đề cho Chặng {s_num} ('{s_name}') bắt đầu đánh số ngày từ {start_day}."
    )

    spiral_note = (
        f"🔄 NGUYÊN TẮC ÔN TẬP XOẮN ỐC ('6 + 1'):\n"
        f"- Cứ mỗi 6 bài học mới, ngày thứ 7 (ví dụ: ngày 7, 14, 21, 28... trong chu kỳ) "
        f"BẮT BUỘC phải là 1 bài 'ÔN TẬP TUẦN & TỔNG HỢP THỰC HÀNH' (Category: 'ÔN TẬP TUẦN') "
        f"nhằm nhúng toàn bộ kiến thức của tuần trước vào bối cảnh tình huống hội thoại thực tế."
    )

    avoid_note = ""
    if completed_topics:
        top_list = ", ".join(f"'{t}'" for t in completed_topics[-25:])
        avoid_note = f"\n⚠️ TUYỆT ĐỐI KHÔNG LẶP LẠI các chủ đề đã dạy ở chặng trước: {top_list}."

    return (
        f"Bạn là chuyên gia thiết kế giáo trình {lang_name} theo chuẩn quốc tế.\n\n"
        f"CHẶNG MỤC TIÊU: Chặng {s_num}/6 — {s_name}\n"
        f"Phạm vi kiến thức: {s_desc}\n"
        f"Số lượng bài học yêu cầu: ĐÚNG {target_days} chủ đề chi tiết (đánh số ngày từ Ngày {start_day} đến Ngày {start_day + target_days - 1}).\n\n"
        f"{typology_note}\n\n"
        f"{spiral_note}\n"
        f"{avoid_note}\n\n"
        f"NHIỆM VỤ: Lập DANH SÁCH ĐẦY ĐỦ tất cả {target_days} chủ đề bài học chi tiết của Chặng {s_num}.\n\n"
        f"QUY TẮC:\n"
        f"- Mỗi item là 1 ngày học độc lập (title = tên chủ đề rõ ràng bằng tiếng Việt, category = loại kiến thức).\n"
        f"- Phân loại category: PHÁT ÂM / CHỮ VIẾT / TỪ VỰNG CHỦ ĐỀ / MẪU CÂU / GIAO TIẾP / NGỮ PHÁP / ÔN TẬP TUẦN / THÀNH NGỮ & SLANG / VĂN HOÁ\n"
        f"- importance: BẮT BUỘC\n"
        f"- id: số thứ tự liên tục bắt đầu từ {start_day}.\n"
        f"- Chỉ trả về JSON, không thêm chữ nào ngoài JSON."
    )


def build_backbone_prompt(lang_name: str, level: str, phases: list = None) -> str:
    """Prompt yêu cầu AI tạo TOÀN BỘ khung giáo trình bắt buộc cho level này.
    Tự động nhận diện typology của ngôn ngữ (chữ tượng hình vs Latin vs thanh điệu)
    và lập danh sách chủ đề theo chuẩn quốc tế từ con số 0 đến cấp độ mong muốn."""
    phases = phases or list(range(len(JOURNEY_PHASES)))
    phase_names = [JOURNEY_PHASES[i][0] for i in phases if i < len(JOURNEY_PHASES)]
    phase_descs = [JOURNEY_PHASES[i][1] for i in phases if i < len(JOURNEY_PHASES)]
    scope = "\n".join(f"   • Tầng {i+1} — {n}: {d}" for i, (n, d) in enumerate(zip(phase_names, phase_descs)))

    fsi = get_language_fsi_profile(lang_name)
    typology_guide = (
        f"⭐ ĐẶC BIỆT LƯU Ý VỀ ĐẶC THÙ NGÔN NGỮ {lang_name.upper()} ({fsi['category_name']}):\n"
        f"- Nếu là ngôn ngữ dùng hệ chữ tượng hình/âm tiết (Tiếng Nhật, Tiếng Trung, Tiếng Hàn, Tiếng Nga, Tiếng Thái...): "
        f"Các ngày đầu tiên của Tầng Vỡ lòng BẮT BUỘC phải quy hoạch chi tiết từng bảng chữ (Hiragana/Katakana/Kanji cơ bản cho Nhật, Pinyin & 4 thanh điệu cho Trung, Hangul & Patchim cho Hàn), quy tắc ghép vần, biến âm.\n"
        f"- Nếu là ngôn ngữ chữ Latinh (Tiếng Anh, Tiếng Pháp, Tiếng Đức, Tiếng Tây Ban Nha...): "
        f"Tập trung vào hệ thống phiên âm quốc tế IPA, trọng âm, quy tắc giống (đực/cái), mạo từ và chia động từ căn bản.\n"
        f"- Tầng Cao cấp & Bản xứ: BẮT BUỘC quy hoạch đầy đủ các chủ đề về Thành ngữ (Idioms), Tiếng lóng (Slang), Cụm kết hợp tự nhiên (Collocations), Kính ngữ/Thân mật, Lối nói ẩn dụ, Chơi chữ, và Văn hóa giao tiếp thực tế."
    )

    min_items = LEVEL_MIN_DAYS.get(level, 15)
    density_note = f"- SỐ LƯỢNG ITEM BẮT BUỘC: Cấp độ '{level}' cần TỐI THIỂU {min_items} chủ đề (phân bổ đều cho các tầng kiến thức yêu cầu ở trên) để đảm bảo bao quát 100% chuẩn quốc tế và không bị sơ sài."

    return (
        f"Bạn là chuyên gia thiết kế giáo trình {lang_name} hàng đầu theo chuẩn quốc tế "
        f"(CEFR / JLPT / HSK / TOPIK) cho người học Việt Nam.\n\n"
        f"Cấp độ mục tiêu: {level}\n"
        f"Các tầng kiến thức cần bao quát trong cấp độ này:\n{scope}\n\n"
        f"{typology_guide}\n\n"
        f"NHIỆM VỤ: Lập DANH SÁCH ĐẦY ĐỦ tất cả chủ đề, điểm ngữ pháp, phát âm, từ vựng theo chủ đề, "
        f"tình huống giao tiếp BẮT BUỘC phải dạy để người học từ con số 0 hoàn thành cấp độ '{level}'.\n\n"
        f"QUY TẮC:\n"
        f"- Mỗi item là 1 ngày học độc lập (title = tên chủ đề rõ ràng bằng tiếng Việt, category = loại kiến thức).\n"
        f"- Phân loại category theo: PHÁT ÂM / CHỮ VIẾT / TỪ VỰNG CHỦ ĐỀ / MẪU CÂU / GIAO TIẾP / NGỮ PHÁP / ÔN TẬP TUẦN / THÀNH NGỮ & SLANG / VĂN HOÁ\n"
        f"- importance: BẮT BUỘC (nền tảng không thể bỏ) | NÊN HỌC (quan trọng) | MỞ RỘNG (bổ sung)\n"
        f"{density_note}\n"
        f"- Sắp xếp theo thứ tự lũy tiến: Vỡ lòng trước -> Ghép âm -> Câu đơn -> Câu phức -> Học thuật -> Bản xứ.\n"
        f"- id: số thứ tự liên tục bắt đầu từ 1.\n"
        f"- Chỉ trả về JSON, không thêm chữ nào ngoài JSON."
    )


def parse_backbone_json(text: str) -> list:
    """Parse và validate backbone JSON từ AI. Trả về list items hợp lệ."""
    data = json.loads(_strip_json(text))
    items_raw = data.get("items") or []
    out = []
    for i, item in enumerate(items_raw, 1):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        if not title:
            continue
        out.append({
            "id": i,  # renumber để đảm bảo liên tục
            "category": str(item.get("category", "TỔNG HỢP")).strip(),
            "title": title,
            "importance": str(item.get("importance", "BẮT BUỘC")).strip(),
            "filled_day": None,  # None = chưa được sinh nội dung
        })
    if not out:
        raise ValueError("Backbone trả về không có item hợp lệ")
    return out


def _backbone_phase(category: str, phase_indices: list) -> str:
    """Ánh xạ category của backbone item sang phase tương ứng trong JOURNEY_PHASES."""
    cat = (category or "").upper()
    if any(k in cat for k in ("CHỮ VIẾT", "ALPHABET", "BẢNG CHỮ", "KÝ TỰ", "NÉT VIẾT")):
        if phase_indices and 0 in phase_indices:
            return JOURNEY_PHASES[0][0]
    if any(k in cat for k in ("PHÁT ÂM", "PHIÊN ÂM", "GHÉP ÂM", "THANH ĐIỆU", "IPA", "ROMANIZATION")):
        if phase_indices and 0 in phase_indices:
            return JOURNEY_PHASES[0][0]
        if phase_indices and 1 in phase_indices:
            return JOURNEY_PHASES[1][0]
    if any(k in cat for k in ("VĂN HOÁ", "SLANG", "THÀNH NGỮ", "BẢN XỨ", "IDIOM", "ẨN DỤ", "CHƠI CHỮ")):
        if phase_indices and 5 in phase_indices:
            return JOURNEY_PHASES[5][0]
        if phase_indices:
            return JOURNEY_PHASES[phase_indices[-1]][0]
    if any(k in cat for k in ("HỌC THUẬT", "BÁO CHÍ", "TRANH BIỆN", "THUYẾT TRÌNH", "CAO CẤP")):
        if phase_indices and 4 in phase_indices:
            return JOURNEY_PHASES[4][0]
    if any(k in cat for k in ("CÔNG SỞ", "LIÊN TỪ", "CÂU PHỨC", "TRUNG CẤP", "KỂ CHUYỆN")):
        if phase_indices and 3 in phase_indices:
            return JOURNEY_PHASES[3][0]
    if any(k in cat for k in ("SƠ CẤP", "CÂU ĐƠN", "MUA SẮM", "ĂN UỐNG", "HỎI ĐƯỜNG")):
        if phase_indices and 2 in phase_indices:
            return JOURNEY_PHASES[2][0]
    if any(k in cat for k in ("TỪ ĐƠN", "SINH TỒN", "SỐ ĐẾM", "ĐẠI TỪ")):
        if phase_indices and 1 in phase_indices:
            return JOURNEY_PHASES[1][0]

    # Mặc định lấy phase đầu tiên trong scope
    if phase_indices:
        return JOURNEY_PHASES[phase_indices[0]][0]
    return JOURNEY_PHASES[0][0]


def _normalize_title(text: str) -> str:
    """Chuẩn hóa tiêu đề để so khớp độ tương đồng."""
    t = (text or "").lower()
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def find_duplicate_topics(items: list, sim_threshold: float = 0.85) -> list:
    """Tìm các cặp topic có độ tương đồng >= sim_threshold bằng SequenceMatcher (kiểu AskCpl).
    Trả về list tuple: (dup_index, dup_id, orig_id, dup_title, orig_title, category)"""
    dups = []
    seen = []
    for i, it in enumerate(items):
        t1 = _normalize_title(it.get("title", ""))
        if not t1:
            continue
        is_dup = False
        for orig_idx, orig_it in seen:
            t2 = _normalize_title(orig_it.get("title", ""))
            ratio = SequenceMatcher(None, t1, t2).ratio()
            if ratio >= sim_threshold:
                dups.append((i, it.get("id", i + 1), orig_it.get("id", orig_idx + 1),
                             it.get("title", ""), orig_it.get("title", ""), it.get("category", "TỔNG HỢP")))
                is_dup = True
                break
        if not is_dup:
            seen.append((i, it))
    return dups


def repair_duplicate_topics(items: list, lang_name: str, level: str, coord,
                            sim_threshold: float = 0.85, max_rounds: int = 3,
                            log_fn=print, stop_check=None) -> list:
    """[Pass 1C] Tự động phát hiện và gọi AI thay thế tại chỗ các chủ đề bị trùng lặp."""
    for r in range(1, max_rounds + 1):
        if stop_check and stop_check():
            raise GenerationStopped()
        dups = find_duplicate_topics(items, sim_threshold=sim_threshold)
        if not dups:
            break
        log_fn(f"🔄 [Pass 1C • Vòng {r}/{max_rounds}] Phát hiện {len(dups)} chủ đề tương đồng >= {int(sim_threshold*100)}%; đang tự động sửa tại chỗ...")
        for idx, dup_id, orig_id, dup_title, orig_title, cat in dups:
            if stop_check and stop_check():
                raise GenerationStopped()
            prompt = (
                f"Bạn là chuyên gia giáo trình {lang_name} cấp độ '{level}'.\n"
                f"Chủ đề '{dup_title}' (Category '{cat}') bị trùng nội dung với chủ đề #{orig_id}: '{orig_title}'.\n\n"
                f"NHIỆM VỤ: Hãy tạo DUY NHẤT 1 CHỦ ĐỀ MỚI HOÀN TOÀN KHÁC BIỆT cho cấp độ '{level}' thuộc category '{cat}' mà CHƯA TỪNG DẠY.\n"
                f"CẤM TUYỆT ĐỐI không dùng lại hoặc diễn đạt tương tự: '{orig_title}'.\n"
                f"Trả JSON duy nhất: {{\"title\": \"tên chủ đề mới khác biệt (tiếng Việt)\", \"category\": \"{cat}\", \"importance\": \"BẮT BUỘC\"}}"
            )
            repair_schema = {
                "type": "OBJECT",
                "properties": {
                    "title": {"type": "STRING"},
                    "category": {"type": "STRING"},
                    "importance": {"type": "STRING"},
                },
                "required": ["title", "category", "importance"],
            }
            try:
                res = coord.request(prompt, response_schema=repair_schema)
                if res.get("ok"):
                    data = json.loads(_strip_json(res.get("text", "")))
                    new_title = str(data.get("title", "")).strip()
                    if new_title and new_title.lower() != dup_title.lower():
                        items[idx]["title"] = new_title
                        if data.get("category"):
                            items[idx]["category"] = str(data["category"]).strip()
                        log_fn(f"  ✓ Đã sửa chủ đề #{dup_id}: '{dup_title}' → '{new_title}'")
            except Exception as e:
                log_fn(f"  ⚠ Lỗi sửa chủ đề #{dup_id}: {e}")
    return items


def review_and_fill_gaps(items: list, lang_name: str, level: str, coord,
                         log_fn=print, stop_check=None) -> list:
    """[Pass 2] Đóng vai trò Chuyên gia Sư phạm rà soát lỗ hổng kiến thức và bổ sung chủ đề thiếu."""
    if stop_check and stop_check():
        raise GenerationStopped()
    log_fn("🔍 [Pass 2 • Gap Review] Đang rà soát đối chiếu toàn diện chuẩn kiến thức quốc tế...")
    titles_summary = [{"id": it["id"], "category": it["category"], "title": it["title"]} for it in items]
    prompt = (
        f"Bạn là Chuyên gia Thẩm định Giáo trình {lang_name} theo chuẩn quốc tế (JLPT/HSK/CEFR/TOPIK).\n"
        f"Cấp độ: {level}\n"
        f"Danh sách {len(items)} chủ đề hiện có:\n{json.dumps(titles_summary, ensure_ascii=False)}\n\n"
        f"NHIỆM VỤ: Hãy rà soát xem có mảng kiến thức, điểm ngữ pháp bắt buộc, kỹ năng phát âm, "
        f"hay tình huống giao tiếp thiết yếu nào BỊ THIẾU để hoàn thành chuẩn cấp độ '{level}' không.\n"
        f"Nếu có thiếu sót quan trọng, trả về tối đa 2-5 chủ đề BỔ SUNG để lấp đầy lỗ hổng.\n"
        f"Nếu đã đầy đủ, trả về mảng gaps rỗng [].\n"
        f"Trả JSON: {{\"gaps\": [{{\"category\": \"NGỮ PHÁP / GIAO TIẾP / PHÁT ÂM / TỪ VỰNG\", \"title\": \"tên chủ đề bổ sung\", \"importance\": \"BẮT BUỘC\"}}]}}"
    )
    gap_schema = {
        "type": "OBJECT",
        "properties": {
            "gaps": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "category": {"type": "STRING"},
                        "title": {"type": "STRING"},
                        "importance": {"type": "STRING"},
                    },
                    "required": ["category", "title", "importance"],
                }
            }
        },
        "required": ["gaps"],
    }
    try:
        res = coord.request(prompt, response_schema=gap_schema)
        if res.get("ok"):
            data = json.loads(_strip_json(res.get("text", "")))
            gaps = data.get("gaps") or []
            added = 0
            for g in gaps:
                if not isinstance(g, dict):
                    continue
                t = str(g.get("title", "")).strip()
                if not t:
                    continue
                if any(_normalize_title(it.get("title", "")) == _normalize_title(t) for it in items):
                    continue
                items.append({
                    "id": len(items) + 1,
                    "category": str(g.get("category", "NGỮ PHÁP")).strip(),
                    "title": t,
                    "importance": str(g.get("importance", "BẮT BUỘC")).strip(),
                    "filled_day": None,
                })
                added += 1
            if added > 0:
                log_fn(f"  ✓ Đã bổ sung {added} chủ đề trọng điểm còn thiếu sau khi thẩm định.")
            else:
                log_fn("  ✓ Khung giáo trình đã đạt độ bao phủ chuẩn xác, không có lỗ hổng lớn.")
    except Exception as e:
        log_fn(f"  ⚠ Thẩm định gap bỏ qua do lỗi: {e}")
    return items


def normalize_backbone_sequence(items: list, phase_indices: list = None) -> list:
    """[Pass 3] Sắp xếp các chủ đề theo thứ tự logic sư phạm: Nền tảng phát âm/chữ viết -> Từ vựng/Số đếm -> Ngữ pháp cốt lõi -> Giao tiếp -> Nâng cao/Văn hóa."""
    def _cat_weight(cat: str) -> int:
        c = (cat or "").upper()
        if any(k in c for k in ("PHÁT ÂM", "CHỮ VIẾT", "ALPHABET", "BẢNG CHỮ", "PHIÊN ÂM")):
            return 0
        if any(k in c for k in ("TỪ VỰNG", "TỪ LOẠI", "SỐ ĐẾM", "ĐẠI TỪ")):
            return 1
        if any(k in c for k in ("NGỮ PHÁP", "CẤU TRÚC")):
            return 2
        if any(k in c for k in ("GIAO TIẾP", "HỘI THOẠI", "TÌNH HUỐNG", "MUA SẮM")):
            return 3
        if any(k in c for k in ("VĂN HOÁ", "SLANG", "THÀNH NGỮ", "BẢN XỨ", "MỞ RỘNG")):
            return 4
        return 2

    sorted_items = sorted(items, key=lambda it: (_cat_weight(it.get("category", "")), it.get("id", 0)))
    for i, it in enumerate(sorted_items, 1):
        it["id"] = i
    return sorted_items


def _clean_quiz_list(items) -> list:
    out = []
    for q in items or []:
        if not isinstance(q, dict):
            continue
        opts = [str(o).strip() for o in (q.get("options") or []) if str(o).strip()][:4]
        ans = q.get("answer_index")
        if not (str(q.get("question", "")).strip() and len(opts) == 4):
            continue
        if not isinstance(ans, int) or not (0 <= ans < len(opts)):
            ans = 0
        out.append({
            "question": str(q["question"]).strip(),
            "options": opts,
            "answer_index": ans,
            "explanation": str(q.get("explanation", "")).strip(),
        })
    return out


def parse_content_json(text: str) -> dict:
    data = json.loads(_strip_json(text))
    if not isinstance(data.get("title"), str) or not data["title"].strip():
        raise ValueError("Thiếu title")

    clean_vocab = []
    for v in data.get("vocab") or []:
        if isinstance(v, dict) and str(v.get("word", "")).strip():
            clean_vocab.append({
                "word": str(v.get("word", "")).strip(),
                "pronunciation": str(v.get("pronunciation", "")).strip(),
                "part_of_speech": str(v.get("part_of_speech", "")).strip(),
                "meaning_vi": str(v.get("meaning_vi", "")).strip(),
                "explanation": str(v.get("explanation", "")).strip(),
                "example_sentence": str(v.get("example_sentence", "")).strip(),
                "example_meaning_vi": str(v.get("example_meaning_vi", "")).strip(),
            })

    clean_patterns = []
    for p in data.get("sentence_patterns") or []:
        if isinstance(p, dict) and str(p.get("pattern", "")).strip():
            clean_patterns.append({
                "pattern": str(p.get("pattern", "")).strip(),
                "meaning_vi": str(p.get("meaning_vi", "")).strip(),
                "structure_note": str(p.get("structure_note", "")).strip(),
                "example_sentence": str(p.get("example_sentence", "")).strip(),
                "example_meaning_vi": str(p.get("example_meaning_vi", "")).strip(),
            })

    clean_common = []
    for s in data.get("common_sentences") or []:
        if isinstance(s, dict) and str(s.get("sentence", "")).strip():
            clean_common.append({
                "sentence": str(s.get("sentence", "")).strip(),
                "meaning_vi": str(s.get("meaning_vi", "")).strip(),
                "situation": str(s.get("situation", "")).strip(),
            })

    clean_grammar = []
    for g in data.get("grammar") or []:
        if not (isinstance(g, dict) and str(g.get("title", "")).strip()):
            continue
        examples = []
        for ex in g.get("examples") or []:
            if isinstance(ex, dict) and str(ex.get("sentence", "")).strip():
                examples.append({
                    "sentence": str(ex.get("sentence", "")).strip(),
                    "meaning_vi": str(ex.get("meaning_vi", "")).strip(),
                })
        clean_grammar.append({
            "title": str(g["title"]).strip(),
            "explanation": str(g.get("explanation", "")).strip(),
            "examples": examples,
        })

    return {
        "title": data["title"].strip(),
        "vocab": clean_vocab,
        "sentence_patterns": clean_patterns,
        "common_sentences": clean_common,
        "grammar": clean_grammar,
    }


def parse_quiz_json(text: str, keys: tuple = None) -> dict:
    """Parse JSON trắc nghiệm từ AI.
    - keys=None → parse đầy đủ 4 loại (tương thích ngược).
    - keys=("vocab_quiz","pattern_quiz") → chỉ parse 2 loại đó (dùng cho split A/B).
    - keys=("common_quiz","grammar_quiz") → chỉ parse 2 loại đó (dùng cho split C/D).
    Luôn trả về dict với key viết tắt: vocab, pattern, common, grammar.
    """
    _KEY_MAP = {
        "vocab_quiz":   "vocab",
        "pattern_quiz": "pattern",
        "common_quiz":  "common",
        "grammar_quiz": "grammar",
    }
    data = json.loads(_strip_json(text))
    if keys is None:
        keys = ("vocab_quiz", "pattern_quiz", "common_quiz", "grammar_quiz")
    return {_KEY_MAP[k]: _clean_quiz_list(data.get(k)) for k in keys}


def normalize_lesson(lesson: dict) -> dict:
    """Chuyển bài học định dạng CŨ (grammar là dict, quiz là list) sang định dạng mới."""
    if not isinstance(lesson, dict):
        return lesson
    # grammar: dict cũ → list mới
    if isinstance(lesson.get("grammar"), dict):
        lesson["grammar"] = [lesson["grammar"]] if lesson["grammar"].get("title") else []
    lesson.setdefault("grammar", [])
    lesson.setdefault("sentence_patterns", [])
    lesson.setdefault("common_sentences", [])
    # quiz: list cũ → dict 4 loại (để vào 'mixed')
    if isinstance(lesson.get("quiz"), list):
        lesson["quiz"] = {"mixed": lesson["quiz"]}
    elif not isinstance(lesson.get("quiz"), dict):
        lesson["quiz"] = {}
    for key in ("vocab", "pattern", "common", "grammar", "mixed"):
        lesson["quiz"].setdefault(key, [])
    return lesson


class GenerationStopped(Exception):
    """Người dùng bấm Dừng giữa chừng."""


def audit_and_supplement_course(language: str, level: str = None, coord=None,
                                log_fn=None, stop_check=None, coordinator_cls=None) -> dict:
    """Rà soát và tự động bổ sung các chặng / chủ đề còn thiếu cho khóa học hiện có trong DB:
    - Giữ nguyên 100% các ngày đã học / đã sinh trong DB (không mất dữ liệu cũ).
    - Đối chiếu với Chuẩn Quốc Tế FSI (6 Chặng, đủ số ngày tối thiểu).
    - Tự động bổ sung các chặng bị thiếu (0 ngày) hoặc thiếu số lượng vào Master Backbone.
    - Cập nhật format_version = 3, total_days và lưu lại vào DB.
    """
    from ai import course_db
    if log_fn is None:
        log_fn = print

    course = course_db.get_course(language)
    if not course:
        log_fn(f"ℹ️ Chưa có khóa học '{language}' trong DB. Khởi tạo khóa học mới...")
        return {"ok": False, "reason": "not_found", "added_count": 0}

    # Khởi tạo coordinator nếu cần
    if coord is None:
        keys = _load_gemini_keys()
        if not keys:
            log_fn("⚠️ Chưa thấy API key. Dùng chế độ Template chuẩn để bổ sung...")
        cls = coordinator_cls or GeminiCoordinator
        coord = cls(
            key_loader=_load_gemini_keys, log_fn=log_fn,
            temperature=0.35, max_output_tokens=16384, timeout=180,
            lock_after_success=False
        )

    fsi = get_language_native_profile(language, coord=coord, log_fn=log_fn)
    backbone = course.get("backbone") or {}
    bb_items = backbone.get("items") or []

    # Nếu khóa cũ chưa có backbone items nhưng đã có days:
    if not bb_items and course.get("days"):
        log_fn("🔄 Khóa cũ chưa có backbone: Khởi tạo backbone từ các ngày hiện có...")
        bb_items = []
        for d in course.get("days", []):
            d_num = int(d.get("day", len(bb_items) + 1))
            bb_items.append({
                "id": d_num,
                "title": d.get("title", f"Bài học ngày {d_num}"),
                "category": "TỔNG HỢP",
                "importance": "BẮT BUỘC",
                "stage_idx": 0,
                "filled_day": d_num
            })

    old_total = len(bb_items)
    log_fn(f"🔍 [Audit & Bổ Sung] Bắt đầu rà soát khóa '{language}' ({old_total} chủ đề hiện có)...")
    log_fn(f"   📋 Chuẩn Bản Xứ C2 ({fsi['category_name']}): Yêu cầu {fsi['total_days']} ngày qua 6 Chặng.")

    stages_added = []
    added_total = 0

    for s_idx, st in enumerate(fsi["stages"]):
        if stop_check and stop_check():
            raise GenerationStopped()

        target_days = st["target_days"]
        # Đếm số item hiện có của chặng này
        existing_stage_items = [
            it for it in bb_items
            if it.get("stage_idx") == s_idx or (it.get("stage_idx") is None and st["name"] in (it.get("category", "") or ""))
        ]
        count_exist = len(existing_stage_items)

        if count_exist == 0:
            # Chặng bị thiếu hoàn toàn (0 ngày) -> Bổ sung 100% target_days
            needed = target_days
            log_fn(f"\n   ▶ Phát hiện thiếu hoàn toàn Chặng {st['stage_num']}/6: '{st['name']}' (0/{target_days} ngày) → Đang bổ sung +{needed} ngày...")
            base_slots = build_stage_universal_template(s_idx, needed)
            st_items = []
            try:
                res_adapt = coord.request(
                    build_stage_adapt_prompt(language, st, fsi, base_slots),
                    response_schema=ADAPT_STAGE_SCHEMA
                )
                if res_adapt.get("ok"):
                    data = json.loads(_strip_json(res_adapt.get("text", "")))
                    topics_list = data.get("topics", [])
                    topics_map = {int(t["slot_id"]): t for t in topics_list if isinstance(t, dict) and "slot_id" in t and "title" in t}
                    for slot in base_slots:
                        s_id = slot["slot_id"]
                        item_copy = dict(slot)
                        if s_id in topics_map:
                            t_info = topics_map[s_id]
                            item_copy["title"] = str(t_info.get("title", slot["generic_name"])).strip()
                            if t_info.get("category"):
                                item_copy["category"] = str(t_info["category"]).strip()
                        else:
                            item_copy["title"] = slot["generic_name"]
                        st_items.append(item_copy)
                else:
                    st_items = [dict(s) for s in base_slots]
            except Exception:
                st_items = [dict(s) for s in base_slots]

            for offset, item in enumerate(st_items):
                item["id"] = len(bb_items) + 1 + offset
                item["stage_idx"] = s_idx
                item["filled_day"] = None

            bb_items.extend(st_items)
            added_total += len(st_items)
            stages_added.append((st["name"], len(st_items)))
            log_fn(f"     ✓ Đã bổ sung thành công Chặng {st['stage_num']}/6: +{len(st_items)} ngày.")

        elif count_exist < target_days:
            # Chặng bị hụt ngày -> Bổ sung đúng phần chênh lệch để đạt 100% chuẩn FSI
            needed = target_days - count_exist
            log_fn(f"\n   ▶ Phát hiện Chặng {st['stage_num']}/6: '{st['name']}' bị hụt ngày ({count_exist}/{target_days} ngày) → Đang bổ sung +{needed} ngày...")
            base_slots = build_stage_universal_template(s_idx, target_days)
            # Lấy các slot chưa có
            supp_slots = base_slots[count_exist:count_exist + needed]
            for slot in supp_slots:
                slot["slot_id"] = len(supp_slots)
            st_items = []
            try:
                res_adapt = coord.request(
                    build_stage_adapt_prompt(language, st, fsi, supp_slots),
                    response_schema=ADAPT_STAGE_SCHEMA
                )
                if res_adapt.get("ok"):
                    data = json.loads(_strip_json(res_adapt.get("text", "")))
                    topics_list = data.get("topics", [])
                    topics_map = {int(t["slot_id"]): t for t in topics_list if isinstance(t, dict) and "slot_id" in t and "title" in t}
                    for slot in supp_slots:
                        s_id = slot["slot_id"]
                        item_copy = dict(slot)
                        if s_id in topics_map:
                            t_info = topics_map[s_id]
                            item_copy["title"] = str(t_info.get("title", slot["generic_name"])).strip()
                        else:
                            item_copy["title"] = slot["generic_name"]
                        st_items.append(item_copy)
                else:
                    st_items = [dict(s) for s in supp_slots]
            except Exception:
                st_items = [dict(s) for s in supp_slots]

            for offset, item in enumerate(st_items):
                item["id"] = len(bb_items) + 1 + offset
                item["stage_idx"] = s_idx
                item["filled_day"] = None

            bb_items.extend(st_items)
            added_total += len(st_items)
            stages_added.append((st["name"], len(st_items)))
            log_fn(f"     ✓ Đã bổ sung thành công Chặng {st['stage_num']}/6: +{len(st_items)} ngày.")

    # Đánh số ID tuần tự 1..N
    for i, it in enumerate(bb_items, 1):
        it["id"] = i

    backbone["items"] = bb_items
    course["backbone"] = backbone
    course["total_days"] = len(bb_items)
    course["format_version"] = 3
    if level and not course.get("level"):
        course["level"] = level
    course_db.save_course(language, course)

    filled_count = len([it for it in bb_items if it.get("filled_day") is not None])
    unfilled_count = len(bb_items) - filled_count

    log_fn(f"\n🎉 [KẾT QUẢ RÀ SOÁT & BỔ SUNG]")
    log_fn(f"   • Số chủ đề cũ được giữ nguyên 100%: {old_total} ngày.")
    log_fn(f"   • Số chủ đề mới được bổ sung thêm: +{added_total} ngày.")
    log_fn(f"   • Tổng lộ trình mới sau khi bổ sung: {len(bb_items)} ngày (đã học: {filled_count}, còn lại: {unfilled_count}).")
    if stages_added:
        log_fn("   • Các chặng đã bổ sung: " + " | ".join(f"{name} (+{n})" for name, n in stages_added))
    else:
        log_fn("   • Khóa học hiện tại đã đầy đủ và đạt chuẩn tối đa!")

    return {
        "ok": True,
        "old_total": old_total,
        "new_total": len(bb_items),
        "added_count": added_total,
        "filled_count": filled_count,
        "unfilled_count": unfilled_count,
        "stages_added": stages_added,
    }


def generate_course(language: str,
                    words_per_day: int = DEFAULT_WORDS_PER_DAY,
                    force_new: bool = False, log_fn=print,
                    on_day_done=None, stop_check=None,
                    level: str = DEFAULT_LEVEL, target_days: int = None,
                    max_days_per_run: int = None,
                    coordinator_cls=None) -> dict:
    """Sinh khóa học rich theo ngày. Mỗi ngày xong lưu ngay (resumable)."""
    from ai import course_db

    if stop_check and stop_check():
        raise GenerationStopped()

    old_course = course_db.get_course(language)
    if force_new:
        if old_course:
            log_fn(f"🗑️ Xóa toàn bộ khóa để tạo mới.")
        course_db.delete_course(language)
        course_db.reset_progress(language)
        course = None
    else:
        course = old_course

    if course is None:
        course = course_db.new_course(language, [], max(int(words_per_day or 1), 1))
        course["level"] = level
        course_db.save_course(language, course)

    existing_day_nums = {int(d.get("day", 0)) for d in course.get("days", [])}
    start_day = (max(existing_day_nums) + 1) if existing_day_nums else 1
    wpd = max(int(words_per_day or DEFAULT_WORDS_PER_DAY), 1)

    keys = _load_gemini_keys()
    if not keys:
        log_fn("❌ Không tìm thấy Gemini API key nào trong settings.json của AskCpl!")
        return {"generated": 0, "skipped": 0, "failed": 0, "total_days": 0}
    log_fn(f"🔑 Đã nạp {len(keys)} Gemini API key từ AskCpl (xoay vòng tự động).")

    coord_cls = coordinator_cls or GeminiCoordinator
    coord = coord_cls(key_loader=_load_gemini_keys, log_fn=log_fn,
                      temperature=0.35, max_output_tokens=16384, timeout=180,
                      lock_after_success=False)

    def _ask(prompt, schema, kind):
        """Gọi AI, parse lỗi thì thử lại 1 lần."""
        _PARSERS = {
            "quiz_ab": lambda t: parse_quiz_json(t, keys=("vocab_quiz", "pattern_quiz")),
            "quiz_cd": lambda t: parse_quiz_json(t, keys=("common_quiz", "grammar_quiz")),
            "quiz":    parse_quiz_json,
        }
        parser = _PARSERS.get(kind, parse_content_json)
        _WHAT = {"quiz": "trắc nghiệm", "quiz_ab": "trắc nghiệm A/B", "quiz_cd": "trắc nghiệm C/D"}
        what = _WHAT.get(kind, "nội dung")
        for attempt in (1, 2):
            if stop_check and stop_check():
                raise GenerationStopped()
            res = coord.request(prompt, response_schema=schema)
            if not res.get("ok"):
                err = res.get("error", {})
                ek = err.get("kind", "?")
                if ek == ErrorKind.NO_KEY:
                    raise RuntimeError("Hết key khả dụng (cooldown/quota). Chạy lại sau.")
                log_fn(f"⚠ {what}: lần {attempt} lỗi [{ek}]: {err.get('message', '')[:120]}")
                continue
            try:
                return res, parser(res.get("text", ""))
            except (ValueError, json.JSONDecodeError) as e:
                log_fn(f"⚠ {what}: lần {attempt} JSON hỏng ({e}), thử lại...")
                continue
        return None, None

    # ── Bước 0: ĐẢM BẢO BACKBONE (Khung giáo trình bắt buộc chuẩn Multi-Pass kiểu AskCpl) ───
    fsi = get_language_native_profile(language, coord=coord, log_fn=log_fn)
    is_full_journey = ("trọn gói" in (level or "").lower()) or (level == LEVELS[0])
    phase_indices = LEVEL_PHASES.get(level, list(range(len(JOURNEY_PHASES))))
    backbone = course.get("backbone")
    backbone_level = (backbone or {}).get("level", "")
    need_backbone = (
        not backbone
        or backbone_level != level
        or not backbone.get("items")
    )

    def _get_item_phase(it):
        s_idx = it.get("stage_idx")
        if s_idx is not None and isinstance(s_idx, int) and 0 <= s_idx < len(JOURNEY_PHASES):
            return JOURNEY_PHASES[s_idx][0]
        cat = (it.get("category") or "").upper()
        if any(k in cat for k in ("CHỮ VIẾT", "ALPHABET", "BẢNG CHỮ", "KÝ TỰ", "NÉT VIẾT", "PHÁT ÂM", "KHẨU HÌNH")):
            return JOURNEY_PHASES[0][0]
        if any(k in cat for k in ("GHÉP ÂM", "TỪ ĐƠN", "SINH TỒN", "SỐ ĐẾM", "ĐẠI TỪ")):
            return JOURNEY_PHASES[1][0]
        if any(k in cat for k in ("SƠ CẤP", "CÂU ĐƠN", "MUA SẮM", "ĂN UỐNG", "HỎI ĐƯỜNG", "ĐỜI SỐNG")):
            return JOURNEY_PHASES[2][0]
        if any(k in cat for k in ("CÔNG SỞ", "LIÊN TỪ", "CÂU PHỨC", "TRUNG CẤP", "KỂ CHUYỆN", "CÔNG VIỆC")):
            return JOURNEY_PHASES[3][0]
        if any(k in cat for k in ("HỌC THUẬT", "BÁO CHÍ", "TRANH BIỆN", "THUYẾT TRÌNH", "CAO CẤP")):
            return JOURNEY_PHASES[4][0]
        if any(k in cat for k in ("VĂN HOÁ", "SLANG", "THÀNH NGỮ", "BẢN XỨ", "IDIOM", "ẨN DỤ", "CHƠI CHỮ")):
            return JOURNEY_PHASES[5][0]
        return _backbone_phase(it.get("category", ""), phase_indices)

    if need_backbone:
        if is_full_journey:
            backbone = build_master_backbone(language, fsi, coord, log_fn=log_fn, stop_check=stop_check)
            if not backbone or not backbone.get("items"):
                log_fn("❌ Không lập được Master Backbone. Chạy lại để thử lại.")
                return {"generated": 0, "skipped": 0, "failed": 0, "total_days": 0}
            bb_items = backbone["items"]
        else:
            log_fn(f"🦴 [Pass 1 • Khung Giáo Trình] AI đang thiết kế toàn bộ chủ đề cốt lõi cấp độ '{level}'...")
            bb_items = None
            for attempt in (1, 2):
                if stop_check and stop_check():
                    raise GenerationStopped()
                res_bb = coord.request(
                    build_backbone_prompt(language, level, phase_indices),
                    response_schema=BACKBONE_SCHEMA)
                if not res_bb.get("ok"):
                    log_fn(f"⚠ Backbone: lần {attempt} lỗi, thử lại...")
                    continue
                try:
                    bb_items = parse_backbone_json(res_bb.get("text", ""))
                    break
                except (ValueError, json.JSONDecodeError) as e:
                    log_fn(f"⚠ Backbone JSON hỏng ({e}), thử lại...")
                    continue
            if not bb_items:
                log_fn("❌ Không lập được backbone. Chạy lại để thử lại.")
                return {"generated": 0, "skipped": 0, "failed": 0, "total_days": 0}

            # Pass 1C: SequenceMatcher Quét & Auto-Repair Trùng Lặp
            bb_items = repair_duplicate_topics(bb_items, language, level, coord, log_fn=log_fn, stop_check=stop_check)

            # Pass 2: Rà soát & Bổ sung Lỗ hổng Kiến thức (Gap Review)
            bb_items = review_and_fill_gaps(bb_items, language, level, coord, log_fn=log_fn, stop_check=stop_check)

            # Pass 3: Sắp xếp theo Chuỗi Tiền đề Sư phạm (Prerequisite Order)
            bb_items = normalize_backbone_sequence(bb_items, phase_indices)

            backbone = {"level": level, "items": bb_items}

        course["backbone"] = backbone
        course_db.save_course(language, course)

        cats = {}
        for it in bb_items:
            cats[it["category"]] = cats.get(it["category"], 0) + 1
        log_fn(f"✅ Khung giáo trình Master hoàn thiện: {len(bb_items)} chủ đề chuẩn mực — "
               + " | ".join(f"{c} ({n})" for c, n in cats.items()))
    else:
        # Nếu đã có backbone và đang ở chế độ Trọn Gói -> Rà soát bổ sung chặng thiếu
        if is_full_journey:
            audit_and_supplement_course(
                language, level=level, coord=coord,
                log_fn=log_fn, stop_check=stop_check
            )
            course = course_db.get_course(language)
            backbone = course.get("backbone") or {}

    bb_items = backbone.get("items") or []
    filled = [it for it in bb_items if it.get("filled_day") is not None]
    unfilled = [it for it in bb_items if it.get("filled_day") is None]

    log_fn(f"📊 Tiến độ Backbone: {len(filled)}/{len(bb_items)} chủ đề đã học "
           f"({'%.0f' % (100*len(filled)/len(bb_items))}%) — còn {len(unfilled)} chủ đề.")
    if not unfilled:
        log_fn(f"🎉 Đã hoàn thành toàn bộ {len(bb_items)} chủ đề bắt buộc của cấp độ '{level}'! "
               f"Hãy nâng lên cấp độ tiếp theo hoặc chọn 'Làm lại từ đầu'.")
        return {"generated": 0, "skipped": 0, "failed": 0,
                "total_days": len(bb_items), "backbone_filled": len(bb_items), "backbone_total": len(bb_items)}

    # ── Bước 1: XÁC ĐỊNH PLAN từ Backbone (Chạy tự động liên tục không ngắt) ───
    if max_days_per_run is not None:
        batch = unfilled[:max_days_per_run]
    elif BACKBONE_BATCH_SIZE is not None:
        batch = unfilled[:BACKBONE_BATCH_SIZE]
    else:
        batch = unfilled

    log_fn(f"📋 Đợt sinh này: {len(batch)} chủ đề (Ngày {start_day}..{start_day+len(batch)-1} trong tổng {len(bb_items)} ngày): "
           + " | ".join(it["title"] for it in batch[:4])
           + ("..." if len(batch) > 4 else ""))

    plan = []
    for i, it in enumerate(batch):
        plan.append({
            "day": start_day + i,
            "title": it["title"],
            "phase": _get_item_phase(it),
            "words": [],
            "backbone_id": it["id"],
        })

    # ── Bước 2: SINH TỪNG NGÀY ─────────────────────────────────────────────────
    existing_plan = {int(p.get("day", 0)): p for p in (course.get("plan") or [])}
    for pday in plan:
        existing_plan[int(pday.get("day", 0))] = pday
    full_plan = sorted(existing_plan.values(), key=lambda x: x["day"])

    course["plan"] = full_plan
    course["total_days"] = len(full_plan)
    course["level"] = level
    course["format_version"] = 3
    if not course.get("words_per_day"):
        course["words_per_day"] = wpd
    course_db.save_course(language, course)

    # Ngày có quiz đầy đủ (tất cả 4 loại) → bỏ qua hoàn toàn
    done_days = {int(d.get("day", 0)) for d in course.get("days", [])
                 if isinstance(d.get("quiz"), dict)
                 and any(d["quiz"].get(k) for k in ("vocab", "pattern", "common", "grammar", "mixed"))}
    # Ngày có content đã lưu nhưng quiz=None hoặc quiz rỗng → resume: chỉ gọi lại quiz
    content_saved_days = {
        int(d.get("day", 0)): d
        for d in course.get("days", [])
        if d.get("_content_only")  # cờ đánh dấu partial save
        and int(d.get("day", 0)) not in done_days
    }

    total_all = len(full_plan)
    generated = skipped = failed = 0
    for pday in plan:
        if stop_check and stop_check():
            raise GenerationStopped()
        idx = int(pday.get("day", 0))
        if idx in done_days:
            skipped += 1
            log_fn(f"⏭️ Ngày {idx} (trong tổng {total_all} ngày lộ trình): đã có sẵn, bỏ qua.")
            continue

        seed_words = [{"word": w.get("word", ""),
                       "pronunciation": w.get("pronunciation", ""),
                       "meaning": w.get("meaning_vi", "")}
                      for w in (pday.get("words") or [])]

        # ── Lần gọi 1: nội dung bài học (bỏ qua nếu đã lưu partial) ──
        if idx in content_saved_days:
            # Resume: đã có content, chỉ cần gọi lại quiz
            saved_partial = content_saved_days[idx]
            content = {k: v for k, v in saved_partial.items()
                       if k not in ("day", "topic", "phase", "level", "words",
                                    "model", "quiz", "_content_only")}
            res = None
            log_fn(f"♻️ Ngày {idx}: đã có content (partial save), chỉ sinh lại trắc nghiệm...")
        else:
            log_fn(f"🤖 Ngày {idx} / tổng {total_all} ngày: sinh nội dung "
                   f"(nền: {len(seed_words)} từ của giáo trình)...")
            res, content = _ask(build_content_prompt(language, idx, total_all, seed_words,
                                                     topic=pday.get("title", ""), level=level),
                                CONTENT_SCHEMA, "content")
            if content is None:
                log_fn(f"❌ Ngày {idx}: không sinh được nội dung. Chạy lại sẽ thử lại ngày này.")
                failed += 1
                continue

            # ── Hướng C: Lưu content ngay (partial save) trước khi gọi quiz ──
            partial_lesson = dict(content)
            partial_lesson["day"] = idx
            partial_lesson["topic"] = pday.get("title", "")
            partial_lesson["phase"] = pday.get("phase", "")
            partial_lesson["level"] = level
            partial_lesson["words"] = [w.get("word", "") for w in seed_words]
            partial_lesson["model"] = (res or {}).get("model", "")
            partial_lesson["quiz"] = {"vocab": [], "pattern": [], "common": [], "grammar": []}
            partial_lesson["_content_only"] = True  # cờ partial
            if "days" not in course:
                course["days"] = []
            course["days"] = [d for d in course["days"] if int(d.get("day", 0)) != idx] + [partial_lesson]
            course["days"].sort(key=lambda x: int(x.get("day", 0)))
            course_db.save_course(language, course)
            content_saved_days[idx] = partial_lesson  # cập nhật in-memory

        # ── Hướng A: Lần gọi 2a — quiz nửa đầu: vocab + pattern ──
        log_fn(f"🧪 Ngày {idx}: sinh trắc nghiệm A/B (từ vựng + mẫu câu) × {QUIZ_PER_TYPE} câu...")
        res2a, quiz_ab = _ask(build_quiz_prompt_ab(language, content), QUIZ_SCHEMA_AB, "quiz_ab")
        if quiz_ab is None:
            log_fn(f"⚠️ Ngày {idx}: không sinh được trắc nghiệm A/B. Chạy lại sẽ thử lại (content đã lưu).")
            failed += 1
            continue

        # ── Hướng A: Lần gọi 2b — quiz nửa sau: common + grammar ──
        log_fn(f"🧪 Ngày {idx}: sinh trắc nghiệm C/D (câu thông dụng + ngữ pháp) × {QUIZ_PER_TYPE} câu...")
        res2b, quiz_cd = _ask(build_quiz_prompt_cd(language, content), QUIZ_SCHEMA_CD, "quiz_cd")
        if quiz_cd is None:
            log_fn(f"⚠️ Ngày {idx}: không sinh được trắc nghiệm C/D. Chạy lại sẽ thử lại (content đã lưu).")
            failed += 1
            continue

        # Gộp quiz từ 2 lần gọi
        quiz = {
            "vocab":   quiz_ab.get("vocab", []),
            "pattern": quiz_ab.get("pattern", []),
            "common":  quiz_cd.get("common", []),
            "grammar": quiz_cd.get("grammar", []),
        }

        lesson = dict(content)
        lesson["day"] = idx
        lesson["topic"] = pday.get("title", "")
        lesson["phase"] = pday.get("phase", "")
        lesson["level"] = level
        lesson["words"] = [w.get("word", "") for w in seed_words]
        lesson["model"] = (res or {}).get("model", "")
        lesson["quiz"] = quiz
        # Xóa cờ partial khi lesson đã hoàn chỉnh
        lesson.pop("_content_only", None)
        generated += 1
        done_days.add(idx)
        content_saved_days.pop(idx, None)

        # Cập nhật cả in-memory days và backbone
        if "days" not in course:
            course["days"] = []
        course["days"] = [d for d in course["days"] if int(d.get("day", 0)) != idx] + [lesson]
        course["days"].sort(key=lambda x: int(x.get("day", 0)))

        # Đánh dấu backbone item này đã được fill
        bb_id = pday.get("backbone_id")
        if bb_id is not None and course.get("backbone") and course["backbone"].get("items"):
            for it in course["backbone"]["items"]:
                if it["id"] == bb_id:
                    it["filled_day"] = idx
                    break

        course_db.save_course(language, course)

        phase_tag = f" [{lesson['phase']}]" if lesson["phase"] else ""
        log_fn(f"✅ Ngày {idx}{phase_tag} xong: {lesson['title']} | "
               f"{len(lesson['vocab'])} từ · {len(lesson['sentence_patterns'])} mẫu câu · "
               f"{len(lesson['common_sentences'])} câu thông dụng · "
               f"{len(lesson['grammar'])} bài ngữ pháp · "
               f"{sum(len(v) for v in quiz.values())} câu trắc nghiệm")

        if on_day_done:
            try:
                on_day_done(idx, total_all, lesson)
            except Exception:
                pass

        time.sleep(0.3)

    total_bb = len((course.get("backbone") or {}).get("items") or [])
    filled_now = len([it for it in (course.get("backbone") or {}).get("items", [])
                      if it.get("filled_day") is not None])
    if total_bb:
        log_fn(f"📊 Tổng kết: {filled_now}/{total_bb} chủ đề hoàn thành "
               f"({'%.0f' % (100*filled_now/total_bb)}%)")
        if filled_now >= total_bb and total_bb > 0:
            log_fn(f"🎉 Hoàn thành trọn vẹn 100% tất cả {total_bb} chủ đề của cấp độ '{level}'!")
    return {"generated": generated, "skipped": skipped, "failed": failed,
            "total_days": total_bb or len(plan),
            "backbone_filled": filled_now, "backbone_total": total_bb}