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

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_WORDS_PER_DAY = 10
MIN_VOCAB = 10
MIN_PATTERNS = 10
MIN_SENTENCES = 10
MIN_GRAMMAR = 2
MAX_GRAMMAR = 3
QUIZ_PER_TYPE = 10

LEVELS = [
    "Người mới bắt đầu",
    "Sơ cấp (giao tiếp cơ bản)",
    "Trung cấp (tự tin giao tiếp)",
    "Cao cấp (thành thạo học thuật/công việc)",
    "Thành thạo như người bản xứ",
]
DEFAULT_LEVEL = LEVELS[0]

# ─── Mỗi level → chỉ dạy phases tương ứng (KHÔNG nhồi tất cả 5 giai đoạn) ───
LEVEL_PHASES = {
    "Người mới bắt đầu":          [0],            # chỉ Nền tảng
    "Sơ cấp (giao tiếp cơ bản)":  [0, 1],         # Nền tảng + Giao tiếp cơ bản
    "Trung cấp (tự tin giao tiếp)":[1, 2],         # Giao tiếp + Trung cấp
    "Cao cấp (thành thạo học thuật/công việc)":[2, 3],  # Trung cấp + Cao cấp
    "Thành thạo như người bản xứ": [3, 4],         # Cao cấp + Bản xứ
}

LEVEL_MIN_DAYS = {
    "Người mới bắt đầu":           15,
    "Sơ cấp (giao tiếp cơ bản)":   30,
    "Trung cấp (tự tin giao tiếp)": 25,
    "Cao cấp (thành thạo học thuật/công việc)": 25,
    "Thành thạo như người bản xứ":  20,
}

# Hành trình khóa học: từ CON SỐ 0 → GẦN NHƯ NGƯỜI BẢN XỨ (5 giai đoạn)
JOURNEY_PHASES = [
    ("Nền tảng", "hệ chữ viết + phát âm, chào hỏi, giới thiệu, số đếm, thời gian, "
                 "đại từ nhân xưng — những thứ sống còn đầu tiên"),
    ("Giao tiếp cơ bản", "mua sắm, ăn uống, hỏi đường, gia đình, sở thích, "
                         "ngữ pháp câu đơn + thì hiện tại"),
    ("Trung cấp", "kể chuyện quá khứ, kế hoạch tương lai, gọi điện, đặt lịch, "
                  "ý kiến cá nhân, lời đề nghị/mời mọc"),
    ("Cao cấp", "tranh luận, thuyết trình, email công việc, đọc tin tức, "
                "câu phức, giả định, bị động, thành ngữ thông dụng"),
    ("Như bản xứ", "slang, chơi chữ, văn phong trang trọng/thân mật, ẩn dụ, "
                   "nét tế nhị trong giao tiếp, đùa cợt tự nhiên"),
]


def _journey_text() -> str:
    return "\n".join(f"   • Giai đoạn {i} — {name}: {desc}"
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
            f"Hãy lập giáo trình ĐÚNG {max(target_days, min_days)} ngày tiếp theo (bắt đầu từ Ngày {start_day}), "
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
            f"nhất mà một người bản xứ sẽ dạy trước cho người mới học ở giai đoạn này "
            f"(theo chủ đề ngày nếu có).\n"
        )
    special_guide = ""
    t_lower = (topic or "").lower()
    if any(k in t_lower for k in ["chữ cái", "phát âm", "phiên âm", "bảng chữ", "nhập môn"]) or day_num <= 3:
        special_guide = (
            "\n💡 LƯU Ý CHO BÀI NHẬP MÔN / BẢNG CHỮ CÁI / PHÁT ÂM:\n"
            "- Trong phần từ vựng: Hãy chú trọng giải thích cách đọc, quy tắc phát âm, "
            "vị trí đặt lưỡi/môi, thanh điệu và mẹo nhớ mặt chữ.\n"
            "- Trong phần ngữ pháp: Giảng chi tiết về cấu trúc hệ chữ viết, quy tắc ghép âm và biến âm (nếu có).\n"
        )
    return (
        f"Bạn là gia sư {lang_name} chuyên nghiệp, dạy người Việt từ gốc đến chuyên sâu.\n"
        f"Hôm nay là Ngày {day_num}/{total_days} của khóa học.{level_line}{topic_line}"
        f"Từ vựng gốc của ngày này:\n{word_list}\n{auto_pick}{special_guide}\n"
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
    """Prompt sinh trắc nghiệm từ bài học đã có (gửi bản tóm lược để gọn)."""
    vocab_lines = [f"- {v['word']} ({v.get('pronunciation', '')}): {v.get('meaning_vi', '')}"
                   for v in lesson.get("vocab", [])]
    pattern_lines = [f"- {p.get('pattern', '')}: {p.get('meaning_vi', '')}"
                     for p in lesson.get("sentence_patterns", [])]
    common_lines = [f"- {s.get('sentence', '')}: {s.get('meaning_vi', '')}"
                    for s in lesson.get("common_sentences", [])]
    grammar_lines = []
    for i, g in enumerate(lesson.get("grammar", []), 1):
        grammar_lines.append(f"- Bài {i}: {g.get('title', '')} — {g.get('explanation', '')[:150]}")
    return (
        f"Bạn là soạn giả đề kiểm tra {lang_name}. Dựa trên NỘI DUNG bài học dưới đây, "
        f"soạn TRẮC NGHIỆM 4 lựa chọn theo ĐÚNG yêu cầu số lượng:\n\n"
        f"=== TỪ VỰNG ===\n{chr(10).join(vocab_lines)}\n\n"
        f"=== CÁCH DÙNG CÂU ===\n{chr(10).join(pattern_lines)}\n\n"
        f"=== CÂU THÔNG DỤNG ===\n{chr(10).join(common_lines)}\n\n"
        f"=== NGỮ PHÁP ===\n{chr(10).join(grammar_lines)}\n\n"
        f"YÊU CẦU:\n"
        f"- vocab_quiz: ÍT NHẤT {QUIZ_PER_TYPE} câu về TỪ VỰNG (chọn nghĩa, chọn cách đọc, "
        f"chọn từ đúng chỗ trống...)\n"
        f"- pattern_quiz: ÍT NHẤT {QUIZ_PER_TYPE} câu về MẪU CÂU/CÁCH DÙNG CÂU (hoàn thành câu "
        f"theo mẫu, chọn cấu trúc đúng...)\n"
        f"- common_quiz: ÍT NHẤT {QUIZ_PER_TYPE} câu về CÂU THÔNG DỤNG (chọn câu phù hợp tình "
        f"huống, chọn nghĩa...)\n"
        f"- grammar_quiz: ÍT NHẤT {QUIZ_PER_TYPE} câu về NGỮ PHÁP (chia đúng, chọn trợ từ, "
        f"tìm lỗi sai...)\n"
        f"Mỗi câu: question, options (ĐÚNG 4 lựa chọn, không trùng nhau), answer_index (0-3), "
        f"explanation ngắn 1-2 câu vì sao đúng. Đáp án phân bố đều các vị trí A/B/C/D.\n"
        f"Chỉ trả về JSON, không thêm chữ nào ngoài JSON."
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


# ─── Backbone: Khung giáo trình bắt buộc ────────────────────────────────────────

def build_backbone_prompt(lang_name: str, level: str, phases: list = None) -> str:
    """Prompt yêu cầu AI tạo TOÀN BỘ khung giáo trình bắt buộc cho level này.
    Backbone = danh sách đầy đủ các chủ đề/điểm ngữ pháp/tình huống PHẢI dạy,
    để khi điền hết backbone → người học đã đủ kiến thức cho cấp độ đó."""
    phases = phases or list(range(len(JOURNEY_PHASES)))
    phase_names = [JOURNEY_PHASES[i][0] for i in phases if i < len(JOURNEY_PHASES)]
    phase_descs = [JOURNEY_PHASES[i][1] for i in phases if i < len(JOURNEY_PHASES)]
    scope = "\n".join(f"   • {n}: {d}" for n, d in zip(phase_names, phase_descs))

    return (
        f"Bạn là chuyên gia thiết kế giáo trình {lang_name} theo chuẩn quốc tế "
        f"(JLPT/HSK/TOPIK/CEFR) cho người học Việt Nam.\n\n"
        f"Cấp độ: {level}\n"
        f"Các giai đoạn học trong cấp độ này:\n{scope}\n\n"
        f"NHIỆM VỤ: Lập DANH SÁCH ĐẦY ĐỦ tất cả chủ đề, điểm ngữ pháp, tình huống giao tiếp "
        f"BẮT BUỘC phải dạy để người học hoàn thành cấp độ '{level}'.\n\n"
        f"QUY TẮC:\n"
        f"- Mỗi item là 1 ngày học (title = tên chủ đề, category = loại kiến thức).\n"
        f"- Phân loại category theo: PHÁT ÂM / CHỮ VIẾT / NGỮ PHÁP / TỪ VỰNG THEO CHỦ ĐỀ / GIAO TIẾP / VĂN HOÁ\n"
        f"- importance: BẮT BUỘC (nền tảng không thể bỏ) | NÊN HỌC (quan trọng) | MỞ RỘNG (bổ sung)\n"
        f"- Đảm bảo đủ các mảng: phát âm/chữ viết, ngữ pháp cốt lõi, từ vựng theo chủ đề đời sống, "
        f"tình huống giao tiếp thực tế, điểm văn hoá.\n"
        f"- Số lượng item phải đủ để bao quát TOÀN BỘ kiến thức cần thiết cho cấp độ này "
        f"(không được quá ít — phải đủ như một giáo trình hoàn chỉnh).\n"
        f"- Sắp xếp theo thứ tự logic học: nền tảng trước, phức tạp sau.\n"
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
    if any(k in cat for k in ("PHÁT ÂM", "CHỮ VIẾT", "ALPHABET", "BẢNG CHỮ", "PHIÊN ÂM")):
        if phase_indices and 0 in phase_indices:
            return JOURNEY_PHASES[0][0]
    if any(k in cat for k in ("VĂN HOÁ", "SLANG", "THÀNH NGỮ", "BẢN XỨ")):
        if phase_indices:
            return JOURNEY_PHASES[phase_indices[-1]][0]
    if phase_indices:
        # Nếu có từ 2 phase trở lên, xếp ngữ pháp/giao tiếp vào phase sau
        if len(phase_indices) > 1 and any(k in cat for k in ("GIAO TIẾP", "TRUNG CẤP", "NÂNG CAO")):
            return JOURNEY_PHASES[phase_indices[1]][0]
        return JOURNEY_PHASES[phase_indices[0]][0]
    return "Nền tảng"


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


def parse_quiz_json(text: str) -> dict:
    data = json.loads(_strip_json(text))
    return {
        "vocab": _clean_quiz_list(data.get("vocab_quiz")),
        "pattern": _clean_quiz_list(data.get("pattern_quiz")),
        "common": _clean_quiz_list(data.get("common_quiz")),
        "grammar": _clean_quiz_list(data.get("grammar_quiz")),
    }


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


# ─── Vòng lặp sinh khóa học ────────────────────────────────────────────────────

class GenerationStopped(Exception):
    """Người dùng bấm Dừng giữa chừng."""


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
        parser = {"quiz": parse_quiz_json}.get(kind, parse_content_json)
        what = {"quiz": "trắc nghiệm"}.get(kind, "nội dung")
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
    phase_indices = LEVEL_PHASES.get(level, list(range(len(JOURNEY_PHASES))))
    backbone = course.get("backbone")
    backbone_level = (backbone or {}).get("level", "")
    need_backbone = (
        not backbone
        or backbone_level != level
        or not backbone.get("items")
    )
    if need_backbone:
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
        log_fn(f"✅ Khung giáo trình Backbone hoàn thiện: {len(bb_items)} chủ đề chuẩn mực — "
               + " | ".join(f"{c} ({n})" for c, n in cats.items()))

    # Thống kê tiến độ backbone
    bb_items = backbone["items"]
    filled = [it for it in bb_items if it.get("filled_day") is not None]
    unfilled = [it for it in bb_items if it.get("filled_day") is None]
    log_fn(f"📊 Tiến độ Backbone: {len(filled)}/{len(bb_items)} chủ đề đã học "
           f"({'%.0f' % (100*len(filled)/len(bb_items))}%) — còn {len(unfilled)} chủ đề.")
    if not unfilled:
        log_fn(f"🎉 Đã hoàn thành toàn bộ {len(bb_items)} chủ đề bắt buộc của cấp độ '{level}'! "
               f"Hãy nâng lên cấp độ tiếp theo hoặc chọn 'Làm lại từ đầu'.")
        return {"generated": 0, "skipped": 0, "failed": 0,
                "total_days": len(bb_items), "backbone_filled": len(bb_items), "backbone_total": len(bb_items)}

    # ── Bước 1: XÁC ĐỊNH PLAN từ Backbone (Chạy tự động liên tục không ngắt 15 ngày) ───
    if max_days_per_run is not None:
        batch = unfilled[:max_days_per_run]
    elif BACKBONE_BATCH_SIZE is not None:
        batch = unfilled[:BACKBONE_BATCH_SIZE]
    else:
        batch = unfilled

    log_fn(f"📋 Đợt sinh này: {len(batch)} chủ đề (Ngày {start_day}..{start_day+len(batch)-1}): "
           + " | ".join(it["title"] for it in batch[:4])
           + ("..." if len(batch) > 4 else ""))

    plan = []
    for i, it in enumerate(batch):
        plan.append({
            "day": start_day + i,
            "title": it["title"],
            "phase": _backbone_phase(it["category"], phase_indices),
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

    done_days = {int(d.get("day", 0)) for d in course.get("days", [])
                 if isinstance(d.get("quiz"), dict)
                 and any(d["quiz"].get(k) for k in ("vocab", "pattern", "common", "grammar", "mixed"))}

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

        # ── Lần gọi 1: nội dung bài học ──
        log_fn(f"🤖 Ngày {idx} / tổng {total_all} ngày: sinh nội dung "
               f"(nền: {len(seed_words)} từ của giáo trình)...")
        res, content = _ask(build_content_prompt(language, idx, total_all, seed_words,
                                                 topic=pday.get("title", ""), level=level),
                            CONTENT_SCHEMA, "content")
        if content is None:
            log_fn(f"❌ Ngày {idx}: không sinh được nội dung. Chạy lại sẽ thử lại ngày này.")
            failed += 1
            continue

        # ── Lần gọi 2: trắc nghiệm 4 loại ──
        log_fn(f"🧪 Ngày {idx}: sinh trắc nghiệm 4 loại × {QUIZ_PER_TYPE} câu...")
        res2, quiz = _ask(build_quiz_prompt(language, content), QUIZ_SCHEMA, "quiz")
        if quiz is None:
            log_fn(f"❌ Ngày {idx}: không sinh được trắc nghiệm. Chạy lại sẽ thử lại ngày này.")
            failed += 1
            continue

        lesson = dict(content)
        lesson["day"] = idx
        lesson["topic"] = pday.get("title", "")
        lesson["phase"] = pday.get("phase", "")
        lesson["words"] = [w.get("word", "") for w in seed_words]
        lesson["model"] = (res or {}).get("model", "")
        lesson["quiz"] = quiz
        generated += 1
        done_days.add(idx)

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