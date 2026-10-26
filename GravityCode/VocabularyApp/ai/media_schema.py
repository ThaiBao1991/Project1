"""
media_schema.py — Schema v5 cho bài học AI của VocabularyApp.

Lịch sử (additive-only, KHÔNG xoá / KHÔNG đổi tên field cũ):
  • v4 : vocab   : + ipa, + phonetic_note, + pos, + image_prompt
        grammar : + pronunciation_focus, + common_mistakes[], + mini_quiz[]
        lesson  : + dialogue[] (roleplay theo ngày & cấp độ)
        lesson  : + media{} (tham chiếu key manifest, KHÔNG nhúng base64)
  • v5 : vocab   : + syllables[], + pitch_accent, + rhymes[], + etymology, + sources[]
        grammar : + references[]
        dialogue: + difficulty, + new_words[], + grammar_used, + kind
        + DIALOGUE_LIMITS{} & validate_dialogue() — ràng buộc hội thoại NGẮN

Nguyên tắc bất di bất dịch:
  • KHÔNG đổi tên / KHÔNG xoá field cũ.
  • `example_sentence` / `example_meaning_vi` / `part_of_speech` vẫn là CANONICAL.
    `example_target` / `example_vi` là ALIAS được TÍNH TOÁN, không do AI sinh.
  • Mọi field mới đều OPTIONAL. Thiếu ⇒ renderer bỏ qua, không lỗi.
  • format_version là metadata quản trị, KHÔNG phải điều kiện render.
  • `sources` KHÔNG do AI sinh — module ai/evidence.py lấp dẫn chứng từ API.
"""

import re

COURSE_FORMAT_VERSION = 5
LEGACY_FORMAT_VERSION = 3

# ─── Ánh xạ POS tiếng Việt → mã ngữ pháp ngắn (fallback khi AI không trả 'pos') ──
_POS_MAP = (
    ("trợ động từ", "aux."),
    ("danh từ", "n."),
    ("động từ", "v."),
    ("tính từ", "adj."),
    ("trạng từ", "adv."),
    ("phó từ", "adv."),
    ("đại từ", "pron."),
    ("số từ", "num."),
    ("liên từ", "conj."),
    ("giới từ", "prep."),
    ("thán từ", "interj."),
)


def pos_from_part_of_speech(pos_vi: str) -> str:
    """'Danh từ' → 'n.' ; trả '' nếu không khớp."""
    t = (pos_vi or "").strip().lower()
    for key, code in _POS_MAP:
        if key in t:
            return code
    return ""


# ─── Gemini structured output — phần MỚI của schema v4 ───────────────────────
# Lưu ý Gemini: `type` phải UPPERCASE; `required` chỉ được chứa key có trong
# `properties`; không dùng anyOf/oneOf/additionalProperties.

MISTAKE_ITEM = {
    "type": "OBJECT",
    "properties": {
        "wrong":  {"type": "STRING"},
        "right":  {"type": "STRING"},
        "why_vi": {"type": "STRING"},
    },
    "required": ["wrong", "right", "why_vi"],
}

# Field mới của 1 mục từ vựng (optional — không đưa vào `required`)
VOCAB_V4_EXTRA = {
    "ipa": {"type": "STRING",
            "description": "Phiên âm quốc tế theo chuẩn IPA, bọc trong hai dấu gạch chéo, ví dụ /kæt/"},
    "phonetic_note": {"type": "STRING",
                      "description": "Mô tả khẩu hình môi/lưỡi/răng và lỗi đọc sai thường gặp của người Việt, 1-3 câu"},
    "pos": {"type": "STRING",
            "description": "Mã ngữ pháp ngắn: n. v. adj. adv. pron. num. conj. prep. interj. aux."},
    "image_prompt": {"type": "STRING",
                     "description": "Prompt TIẾNG ANH 12-25 từ để AI vẽ minh họa cho từ này"},
}

# ─── Schema v5: field MỚI cho từ vựng (optional — KHÔNG đưa vào `required`) ──
# Ghi chú: `syllables`/`pitch_accent` chỉ có nghĩa với ngôn ngữ có âm tiết/thanh.
VOCAB_V5_EXTRA = {
    "syllables": {"type": "ARRAY", "items": {"type": "STRING"},
                  "description": "Các âm tiết của từ, tách bằng dấu gạch nối (chỉ khi ngôn ngữ có âm tiết: JA/KO/ZH/VN)"},
    "pitch_accent": {"type": "STRING",
                     "description": "Trọng âm thanh (chỉ JA/KO/ZH), ví dụ 猫: [0]"},
    "rhymes": {"type": "ARRAY", "items": {"type": "STRING"},
               "description": "2-4 từ nghe giống (rhyme) để luyện phát âm"},
    "etymology": {"type": "STRING",
                  "description": "1-2 câu nguồn gốc từ (Hán-Việt, Latin, tiếng Pháp...) nếu biết chắc"},
}

# Item dẫn chứng cho grammar.references[] (do AI sinh)
REFERENCE_ITEM = {
    "type": "OBJECT",
    "properties": {
        "title":   {"type": "STRING"},
        "url":     {"type": "STRING"},
        "note_vi": {"type": "STRING"},
    },
    "required": ["title", "url"],
}

# Item dẫn chứng cho vocab.sources[] — KHỚP với shape module ai/evidence.py ghi vào
# (title, url, kind, quote, lang, license) để renderer đọc đồng nhất.
EVIDENCE_SOURCE_ITEM = {
    "type": "OBJECT",
    "properties": {
        "title":   {"type": "STRING"},
        "url":     {"type": "STRING"},
        "kind":    {"type": "STRING"},
        "quote":   {"type": "STRING"},
        "lang":    {"type": "STRING"},
        "license": {"type": "STRING"},
    },
    "required": ["title", "url"],
}

# `sources` KHỜI AI sinh (tránh bịa) — module ai/evidence.py lấp từ API rồi ghi vào.
VOCAB_V5_SOURCES = {
    "sources": {"type": "ARRAY", "items": EVIDENCE_SOURCE_ITEM,
                "description": "Dẫn chứng nguồn — do ai/evidence.py lấp từ API, KHÔNG do AI sinh"},
}

# Field mới của 1 bài ngữ pháp (optional)
GRAMMAR_V4_EXTRA = {
    "pronunciation_focus": {"type": "STRING",
                            "description": "1-3 câu về trọng âm / thanh điệu / âm đầu-cuối đặc trưng của cấu trúc này"},
    "common_mistakes": {"type": "ARRAY", "items": MISTAKE_ITEM},
    "mini_quiz": {"type": "ARRAY", "items": {
        "type": "OBJECT",
        "properties": {
            "question": {"type": "STRING"},
            "options": {"type": "ARRAY", "items": {"type": "STRING"}},
            "answer_index": {"type": "INTEGER"},
            "explanation": {"type": "STRING"},
        },
        "required": ["question", "options", "answer_index", "explanation"],
    }},
}

# Schema v5: tài liệu tham khảo cho 1 bài ngữ pháp (optional)
GRAMMAR_V5_EXTRA = {
    "references": {"type": "ARRAY", "items": REFERENCE_ITEM,
                   "description": "Nguồn tham khảo (tên + URL) cho điểm ngữ pháp này"},
}

# ─── Hạn chế hội thoại (đo thật: Anh median 663 ký tự, max 4274 → quá dài) ───
# kind="micro" : hội thoại NGẮN dùng để luyện nói hằng ngày (mặc định)
# kind="scene" : bối cảnh dài hơn, dùng cho ngày ôn tập tổng hợp
DIALOGUE_LIMITS = {
    "max_turns": 6,
    "max_total_chars": 220,
    "max_words_per_line": 8,
    "min_vocab_hits": 1,
    "max_total_chars_scene": 900,
    "max_turns_scene": 12,
}

DIALOGUE_KINDS = ("micro", "scene")

# ─── Schema 4: HỘI THOẠI (roleplay) — gọi AI RIÊNG, không gộp vào content ────
# Lý do tách riêng: content v4 thêm ~2.500 token; gộp dialogue sẽ vượt
# max_output_tokens=16384 và tái diễn bug "JSON bị cắt" (projectLog Update 12).
# v5: thêm difficulty / new_words / grammar_used / kind (enum micro|scene).
DIALOGUE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "dialogue": {"type": "ARRAY", "items": {
            "type": "OBJECT",
            "properties": {
                "situation":     {"type": "STRING"},
                "level_tag":     {"type": "STRING", "description": "A1|A2|B1|B2|C1|C2"},
                "title":         {"type": "STRING"},
                "cultural_note": {"type": "STRING",
                                  "description": "TỐI ĐA 1 câu về điểm văn hóa / ngữ cảnh ẩn"},
                # ── v5 ──
                "difficulty":    {"type": "STRING", "description": "CEFR thực tế của hội thoại: A1|A2|B1|B2|C1|C2"},
                "new_words":     {"type": "ARRAY", "items": {"type": "STRING"},
                                  "description": "Các từ MỚI dùng trong hội thoại"},
                "grammar_used":  {"type": "STRING",
                                  "description": "Tên cấu trúc ngữ pháp đã dạy được dùng trong hội thoại"},
                "kind":          {"type": "STRING", "enum": list(DIALOGUE_KINDS),
                                  "description": "micro = hội thoại ngắn luyện nói; scene = bối cảnh dài hơn"},
                "turns": {"type": "ARRAY", "items": {
                    "type": "OBJECT",
                    "properties": {
                        "speaker":     {"type": "STRING"},
                        "line_target": {"type": "STRING"},
                        "line_vi":     {"type": "STRING"},
                        "focus_words": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "emotion":     {"type": "STRING"},
                        "tone":        {"type": "STRING"},
                    },
                    "required": ["speaker", "line_target", "line_vi"],
                }},
            },
            "required": ["situation", "level_tag", "turns"],
        }},
    },
    "required": ["dialogue"],
}

# ─── Ánh xạ phase → level_tag CEFR (để chọn độ dài hội thoại) ────────────────
PHASE_TO_CEFR = {
    0: "A1", 1: "A1", 2: "A2",
    3: "B1", 4: "C1", 5: "C2",
}


def cefr_for_stage(stage_idx) -> str:
    try:
        return PHASE_TO_CEFR.get(int(stage_idx), "A2")
    except (TypeError, ValueError):
        return "A2"


# ─── Tiện ích hội thoại v5 ──────────────────────────────────────────────────

def _split_words(text: str) -> list:
    """Tách câu thành danh sách từ (bỏ khoảng trắng thừa)."""
    return [w for w in re.split(r"\s+", (text or "").strip()) if w]


def _contains_word(line: str, word: str) -> bool:
    """Kiểm tra 1 từ/cụm từ có xuất hiện trong câu (không phân biệt hoa thường)."""
    lw = (line or "").lower()
    ww = (word or "").strip().lower()
    if not lw or not ww:
        return False
    return re.search(r"(?<!\w)" + re.escape(ww) + r"(?!\w)", lw) is not None


def resolve_dialogue_limits(dialogue: dict = None, limits: dict = None) -> dict:
    """Trả về bộ giới hạn áp dụng cho 1 hội thoại.

    - `limits` truyền vào → ghi đè tuyệt đối (dùng để test).
    - Ngược lại chọn theo `kind` của hội thoại: 'scene' → giới hạn scene,
      'micro' (mặc định) → giới hạn ngắn.
    """
    lim = dict(DIALOGUE_LIMITS)
    kind = str((dialogue or {}).get("kind") or "").strip().lower()
    if limits:
        lim.update(limits)
        return lim
    if kind == "scene":
        lim["max_turns"] = lim.get("max_turns_scene", lim["max_turns"])
        lim["max_total_chars"] = lim.get("max_total_chars_scene", lim["max_total_chars"])
    return lim


def validate_dialogue(dialogue: dict, vocab_words: list, limits: dict = None) -> dict:
    """Kiểm tra hội thoại có đáp ứng giới hạn NGẮN + ĐƠN GIẢN không.

    Trả về: {"ok": bool, "errors": [...], "stats": {...}}
    - Số lượt ≤ max_turns
    - Tổng ký tự (line_target) ≤ max_total_chars
    - Mỗi lượt ≤ max_words_per_line từ
    - Có ≥ min_vocab_hits từ của ngày xuất hiện trong line_target
    """
    errors = []
    lim = resolve_dialogue_limits(dialogue, limits)
    max_turns = int(lim.get("max_turns", 6))
    max_chars = int(lim.get("max_total_chars", 220))
    max_wpl = int(lim.get("max_words_per_line", 8))
    min_hits = int(lim.get("min_vocab_hits", 1))

    turns = [t for t in ((dialogue or {}).get("turns") or []) if isinstance(t, dict)]
    lines = [str(t.get("line_target") or "").strip() for t in turns]
    word_counts = [len(_split_words(l)) for l in lines]
    total_chars = sum(len(l) for l in lines)
    max_line_words = max(word_counts) if word_counts else 0

    # Từ của ngày có xuất hiện trong hội thoại không
    vocab_clean = [str(w).strip() for w in (vocab_words or []) if str(w or "").strip()]
    hits = {}
    for w in vocab_clean:
        c = sum(1 for l in lines if _contains_word(l, w))
        if c:
            hits[w] = c
    n_hits = len(hits)

    # Lượt không chứa từ nào của ngày (đưa vào stats, KHÔNG làm fail)
    turns_without_vocab = 0
    if vocab_clean:
        for l in lines:
            if not any(_contains_word(l, w) for w in vocab_clean):
                turns_without_vocab += 1

    if not turns:
        errors.append("Hội thoại không có lượt nào (turns rỗng).")
    if len(turns) > max_turns:
        errors.append(f"Quá số lượt: {len(turns)} lượt > tối đa {max_turns}.")
    if total_chars > max_chars:
        errors.append(f"Quá tổng ký tự: {total_chars} > tối đa {max_chars}.")
    if max_line_words > max_wpl:
        errors.append(f"Có lượt quá dài: {max_line_words} từ > tối đa {max_wpl} từ/lượt.")
    if n_hits < min_hits:
        errors.append(f"Thiếu từ vựng của ngày: chỉ khớp {n_hits} từ, cần ≥ {min_hits}.")

    return {
        "ok": not errors,
        "errors": errors,
        "stats": {
            "kind": str((dialogue or {}).get("kind") or "micro"),
            "turns": len(turns),
            "max_turns": max_turns,
            "total_chars": total_chars,
            "max_total_chars": max_chars,
            "max_words_per_line": max_line_words,
            "max_words_allowed": max_wpl,
            "vocab_hits": n_hits,
            "min_vocab_hits": min_hits,
            "matched_words": sorted(hits.keys()),
            "turns_without_vocab": turns_without_vocab,
        },
    }


# ─── Migration mềm (soft default) — bơm field v4/v5 vào RAM, KHÔNG ghi đĩa ───
def apply_defaults_in_memory(lesson: dict) -> dict:
    """Bơm default v4/v5 cho 1 lesson. TUYỆT ĐỐI KHÔNG gọi save_course() ở đây.

    Lý do không ghi đĩa: 8 file course.json = 135 MB đang được track git.
    Backfill đầy đủ sẽ tạo diff ~27 MB → blob git mới vĩnh viễn, không thu hồi
    được, mà không đổi lại giá trị gì (app mới đã có default runtime).
    """
    if not isinstance(lesson, dict):
        return lesson

    lesson.setdefault("dialogue", [])
    lesson.setdefault("media", {})
    lesson.setdefault("format_version", LEGACY_FORMAT_VERSION)

    for v in lesson.get("vocab") or []:
        if not isinstance(v, dict):
            continue
        if not v.get("ipa"):
            v["ipa"] = v.get("pronunciation") or ""
        if not v.get("pos"):
            v["pos"] = pos_from_part_of_speech(v.get("part_of_speech", ""))
        if not v.get("example_target"):
            v["example_target"] = v.get("example_sentence") or ""
        if not v.get("example_vi"):
            v["example_vi"] = v.get("example_meaning_vi") or ""
        v.setdefault("phonetic_note", "")
        v.setdefault("image_prompt", None)
        v.setdefault("image_ref", None)
        v.setdefault("audio_ref", None)
        # ── v5 ──
        v.setdefault("syllables", [])
        v.setdefault("pitch_accent", "")
        v.setdefault("rhymes", [])
        v.setdefault("etymology", "")
        v.setdefault("sources", [])

    for g in lesson.get("grammar") or []:
        if not isinstance(g, dict):
            continue
        g.setdefault("pronunciation_focus", "")
        g.setdefault("common_mistakes", [])
        g.setdefault("mini_quiz", [])
        # ── v5 ──
        g.setdefault("references", [])

    for d in lesson.get("dialogue") or []:
        if not isinstance(d, dict):
            continue
        d.setdefault("cultural_note", "")
        d.setdefault("audio_ref", None)
        d.setdefault("turns", [])
        # ── v5 ──
        d.setdefault("difficulty", "")
        d.setdefault("new_words", [])
        d.setdefault("grammar_used", "")
        d.setdefault("kind", "micro")

    return lesson


# Alias tương thích ngược — import cũ vẫn chạy được
apply_v4_defaults_in_memory = apply_defaults_in_memory
