"""
course_generator.py — Sinh khóa học chuyên sâu theo ngày bằng Gemini AI.
- Dùng lại cơ chế AccountPool/GeminiCoordinator của AskCpl (api/gemini_safe.py)
- Đọc API key (dạng ENC:) trực tiếp từ settings.json của AskCpl — chỉ đọc,
  không ghi đè trạng thái của ứng dụng kia.
- Mỗi ngày = 1 bài học RICH gồm:
    ≥10 từ vựng chuyên sâu + ≥10 cách dùng câu + ≥10 câu thông dụng
    + 2-3 bài ngữ pháp + trắc nghiệm MỖI LOẠI ≥10 câu (4 loại).
- Chia 2 lần gọi AI/ngày (nội dung, trắc nghiệm) để tránh bị cắt JSON.
"""

import json
import os

from api.gemini_safe import GeminiCoordinator, ErrorKind

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_WORDS_PER_DAY = 10
MIN_VOCAB = 10
MIN_PATTERNS = 10
MIN_SENTENCES = 10
MIN_GRAMMAR = 2
MAX_GRAMMAR = 3
QUIZ_PER_TYPE = 10

QUIZ_CATEGORIES = [
    ("vocab", "Từ vựng"),
    ("pattern", "Cách dùng câu"),
    ("common", "Câu thông dụng"),
    ("grammar", "Ngữ pháp"),
    ("mixed", "Tổng hợp"),   # cho dữ liệu cũ migrate
]

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

def build_content_prompt(lang_name: str, day_num: int, total_days: int, words: list) -> str:
    lines = [f"- {v.get('word', '')} ({v.get('pronunciation') or 'chưa có phát âm'})"
             f" — nghĩa hiện có: {(v.get('meaning') or '')[:200]}" for v in words]
    word_list = "\n".join(lines)
    return (
        f"Bạn là gia sư {lang_name} chuyên nghiệp, dạy người Việt từ gốc đến chuyên sâu.\n"
        f"Hôm nay là Ngày {day_num}/{total_days} của khóa học. Từ vựng gốc của ngày này:\n"
        f"{word_list}\n\n"
        f"Hãy tạo bài học hoàn chỉnh dạng JSON, ĐỦ absolute số lượng như sau:\n\n"
        f"1. title: tên bài học (tiếng Việt) nêu rõ chủ đề nhóm từ.\n\n"
        f"2. vocab: ÍT NHẤT {MIN_VOCAB} từ vựng. Ưu tiên dùng đủ các từ gốc ở trên; "
        f"nếu từ gốc ít hơn {MIN_VOCAB}, BỔ SUNG các từ liên quan cùng chủ đề/giao tiếp "
        f"thông dụng để đạt tối thiểu {MIN_VOCAB} từ. Mỗi từ gồm:\n"
        f"   - pronunciation: cách đọc chuẩn (romaji/pinyin/IPA tùy ngôn ngữ)\n"
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
    raw = (text or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("Không tìm thấy JSON trong phản hồi AI")
    return raw[start:end + 1]


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


def generate_course(language: str, vocabs: list, words_per_day: int = DEFAULT_WORDS_PER_DAY,
                    force_new: bool = False, log_fn=print,
                    on_day_done=None, stop_check=None) -> dict:
    """Sinh khóa học rich theo ngày. Mỗi ngày xong lưu ngay (resumable).

    Trả về: {"generated": n, "skipped": n, "failed": n, "total_days": n}
    """
    from ai import course_db

    if stop_check and stop_check():
        raise GenerationStopped()

    course = None if force_new else course_db.get_course(language)
    if course is None:
        course = course_db.new_course(language, vocabs, words_per_day)
        course_db.save_course(language, course)

    words_per_day = max(int(words_per_day or DEFAULT_WORDS_PER_DAY), 1)
    chunks = [vocabs[i:i + words_per_day] for i in range(0, len(vocabs), words_per_day)]
    total_days = len(chunks)
    course["total_days"] = total_days
    course["format_version"] = 2
    course_db.save_course(language, course)

    done_days = {int(d.get("day", 0)) for d in course.get("days", [])
                 if isinstance(d.get("quiz"), dict)}

    keys = _load_gemini_keys()
    if not keys:
        log_fn("❌ Không tìm thấy Gemini API key nào trong settings.json của AskCpl!")
        return {"generated": 0, "skipped": 0, "failed": 0, "total_days": total_days}
    log_fn(f"🔑 Đã nạp {len(keys)} Gemini API key từ AskCpl (xoay vòng tự động).")

    coord = GeminiCoordinator(key_loader=_load_gemini_keys, log_fn=log_fn,
                              temperature=0.35, max_output_tokens=16384, timeout=180)

    def _ask(prompt, schema, what):
        """Gọi AI, parse lỗi thì thử lại 1 lần. Trả về (res, parsed) hoặc (None, None)."""
        parser = parse_quiz_json if what == "quiz" else parse_content_json
        for attempt in (1, 2):
            if stop_check and stop_check():
                raise GenerationStopped()
            res = coord.request(prompt, response_schema=schema)
            if not res.get("ok"):
                err = res.get("error", {})
                kind = err.get("kind", "?")
                if kind == ErrorKind.NO_KEY:
                    raise RuntimeError("Hết key khả dụng (cooldown/quota). Chạy lại sau.")
                log_fn(f"⚠ {what}: lần {attempt} lỗi [{kind}]: {err.get('message', '')[:120]}")
                continue
            try:
                return res, parser(res.get("text", ""))
            except (ValueError, json.JSONDecodeError) as e:
                log_fn(f"⚠ {what}: lần {attempt} JSON hỏng ({e}), thử lại...")
                continue
        return None, None

    generated = skipped = failed = 0
    for idx, chunk in enumerate(chunks, start=1):
        if stop_check and stop_check():
            raise GenerationStopped()
        if idx in done_days:
            skipped += 1
            log_fn(f"⏭️ Ngày {idx}/{total_days}: đã có sẵn, bỏ qua.")
            continue

        # ── Lần gọi 1: nội dung bài học ──
        log_fn(f"🤖 Ngày {idx}/{total_days}: sinh nội dung ({len(chunk)} từ gốc)...")
        res, content = _ask(build_content_prompt(language, idx, total_days, chunk),
                            CONTENT_SCHEMA, "nội dung")
        if content is None:
            log_fn(f"❌ Ngày {idx}: không sinh được nội dung. Chạy lại sẽ thử lại ngày này.")
            failed += 1
            continue

        # ── Lần gọi 2: trắc nghiệm 4 loại ──
        log_fn(f"🧪 Ngày {idx}: sinh trắc nghiệm 4 loại × {QUIZ_PER_TYPE} câu...")
        res2, quiz = _ask(build_quiz_prompt(language, content), QUIZ_SCHEMA, "trắc nghiệm")
        if quiz is None:
            log_fn(f"❌ Ngày {idx}: không sinh được trắc nghiệm. Chạy lại sẽ thử lại ngày này.")
            failed += 1
            continue

        lesson = dict(content)
        lesson["day"] = idx
        lesson["words"] = [v.get("word", "") for v in chunk]
        lesson["model"] = (res or {}).get("model", "")
        lesson["quiz"] = quiz
        course_db.upsert_day(language, lesson)
        generated += 1
        done_days.add(idx)
        log_fn(f"✅ Ngày {idx} xong: {lesson['title']} | "
               f"{len(lesson['vocab'])} từ · {len(lesson['sentence_patterns'])} mẫu câu · "
               f"{len(lesson['common_sentences'])} câu thông dụng · "
               f"{len(lesson['grammar'])} bài ngữ pháp · "
               f"{sum(len(v) for v in quiz.values())} câu trắc nghiệm")
        if on_day_done:
            try:
                on_day_done(idx, total_days, lesson)
            except Exception:
                pass

    return {"generated": generated, "skipped": skipped, "failed": failed,
            "total_days": total_days}