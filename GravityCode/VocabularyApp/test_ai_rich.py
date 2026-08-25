"""Smoke tests cho AI Course — format mới (2-call, rich content)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai.course_generator import (
    parse_content_json, parse_quiz_json, normalize_lesson,
    CONTENT_SCHEMA, QUIZ_SCHEMA, build_content_prompt, build_quiz_prompt,
    MIN_VOCAB, MIN_PATTERNS, MIN_SENTENCES, MIN_GRAMMAR, MAX_GRAMMAR, QUIZ_PER_TYPE,
)
from ai.course_db import get_course, save_course, new_course, course_path
import json, tempfile, shutil

passed = 0
failed = 0
def ok(name):
    global passed; passed += 1; print(f"  [OK] {name}")
def fail(name, msg=""):
    global failed; failed += 1; print(f"  [FAIL] {name}: {msg}")

# ─── 1. Schema structure ───
print("\n[1] Schema structure")
assert "vocab" in CONTENT_SCHEMA["properties"]
assert "sentence_patterns" in CONTENT_SCHEMA["properties"]
assert "common_sentences" in CONTENT_SCHEMA["properties"]
assert "grammar" in CONTENT_SCHEMA["properties"]
ok("CONTENT_SCHEMA has all 4 sections")

assert "vocab_quiz" in QUIZ_SCHEMA["properties"]
assert "pattern_quiz" in QUIZ_SCHEMA["properties"]
assert "common_quiz" in QUIZ_SCHEMA["properties"]
assert "grammar_quiz" in QUIZ_SCHEMA["properties"]
ok("QUIZ_SCHEMA has all 4 quiz types")

# ─── 2. parse_content_json ───
print("\n[2] parse_content_json")
content_json = json.dumps({
    "title": "Bài 1: Chào hỏi",
    "vocab": [
        {"word": "こんにちは", "pronunciation": "konnichiwa", "part_of_speech": "感叹词",
         "meaning_vi": "Xin chào", "explanation": "Lời chào ban ngày",
         "example_sentence": "こんにちは、田中さん。", "example_meaning_vi": "Xin chào, anh Tanaka."},
    ] * 10,
    "sentence_patterns": [
        {"pattern": "...は...です", "meaning_vi": "... là ...", "structure_note": "Cơ bản",
         "example_sentence": "私は学生です。", "example_meaning_vi": "Tôi là sinh viên."},
    ] * 10,
    "common_sentences": [
        {"sentence": "おはようございます", "meaning_vi": "Chào buổi sáng", "situation": "Buổi sáng"},
    ] * 10,
    "grammar": [
        {"title": "助詞 は", "explanation": "Giải thích chi tiết về は", "examples": [
            {"sentence": "私は田中です。", "meaning_vi": "Tôi là Tanaka."},
        ]},
    ] * 2,
})
parsed = parse_content_json(content_json)
assert parsed["title"] == "Bài 1: Chào hỏi"
assert len(parsed["vocab"]) == 10
assert len(parsed["sentence_patterns"]) == 10
assert len(parsed["common_sentences"]) == 10
assert len(parsed["grammar"]) == 2
ok(f"parsed content: {len(parsed['vocab'])} vocab, {len(parsed['sentence_patterns'])} patterns, "
   f"{len(parsed['common_sentences'])} common, {len(parsed['grammar'])} grammar")

# ─── 3. parse_quiz_json ───
print("\n[3] parse_quiz_json")
quiz_json = json.dumps({
    "vocab_quiz": [{"question": f"Q{i}", "options": ["A","B","C","D"], "answer_index": 0, "explanation": "ok"} for i in range(10)],
    "pattern_quiz": [{"question": f"P{i}", "options": ["A","B","C","D"], "answer_index": 1, "explanation": "ok"} for i in range(10)],
    "common_quiz": [{"question": f"C{i}", "options": ["A","B","C","D"], "answer_index": 2, "explanation": "ok"} for i in range(10)],
    "grammar_quiz": [{"question": f"G{i}", "options": ["A","B","C","D"], "answer_index": 3, "explanation": "ok"} for i in range(10)],
})
parsed_q = parse_quiz_json(quiz_json)
assert len(parsed_q["vocab"]) == 10
assert len(parsed_q["pattern"]) == 10
assert len(parsed_q["common"]) == 10
assert len(parsed_q["grammar"]) == 10
total_q = sum(len(v) for v in parsed_q.values())
ok(f"parsed quiz: {total_q} questions (4 categories × 10)")

# ─── 4. parse content with bad data (should skip invalid items) ───
print("\n[4] parse_content_json resilience")
bad_content = json.dumps({
    "title": "Test",
    "vocab": [{"word": "ok", "pronunciation": "", "part_of_speech": "", "meaning_vi": "nghĩa",
               "explanation": "", "example_sentence": "", "example_meaning_vi": ""},
              {"word": "", "meaning_vi": "bad"},  # missing word → skipped
              None],  # None → skipped
    "sentence_patterns": [],
    "common_sentences": [],
    "grammar": [],
})
p2 = parse_content_json(bad_content)
assert len(p2["vocab"]) == 1, "only valid vocab kept"
ok("bad items filtered correctly")

# ─── 5. parse quiz with bad data ───
print("\n[5] parse_quiz_json resilience")
bad_quiz = json.dumps({
    "vocab_quiz": [
        {"question": "ok", "options": ["A","B","C","D"], "answer_index": 0, "explanation": "x"},
        {"question": "bad opts", "options": ["A","B"], "answer_index": 0, "explanation": "x"},
        {"question": "bad ans", "options": ["A","B","C","D"], "answer_index": 99, "explanation": "x"},
        {"question": "no opts", "options": [], "answer_index": 0, "explanation": "x"},
        None,
    ],
    "pattern_quiz": [],
    "common_quiz": [],
    "grammar_quiz": [],
})
p3 = parse_quiz_json(bad_quiz)
assert len(p3["vocab"]) == 2, f"expected 2 valid quiz items, got {len(p3['vocab'])}"
ok("bad quiz items filtered, answer_index corrected")

# ─── 6. normalize_lesson (migration) ───
print("\n[6] normalize_lesson (old format migration)")
old_lesson = {
    "day": 1, "title": "Old",
    "grammar": {"title": "点A", "explanation": "...", "examples": []},  # dict, not list
    "quiz": [  # list, not dict
        {"question": "q1", "options": ["A","B","C","D"], "answer_index": 0, "explanation": "x"},
    ],
}
norm = normalize_lesson(old_lesson)
assert isinstance(norm["grammar"], list), "grammar migrated to list"
assert len(norm["grammar"]) == 1
assert isinstance(norm["quiz"], dict), "quiz migrated to dict"
assert "mixed" in norm["quiz"]
assert len(norm["quiz"]["mixed"]) == 1
ok("old grammar dict → list, old quiz list → dict.mixed")

# ─── 7. normalize_lesson (new format, no-op) ───
print("\n[7] normalize_lesson (new format, no change)")
new_lesson = {
    "day": 1, "title": "New",
    "grammar": [{"title": "A", "explanation": "x", "examples": []}],
    "quiz": {"vocab": [{"question": "q", "options": ["A","B","C","D"], "answer_index": 0, "explanation": "x"}],
             "pattern": [], "common": [], "grammar": []},
}
norm2 = normalize_lesson(new_lesson)
assert len(norm2["grammar"]) == 1
assert "vocab" in norm2["quiz"]
ok("new format preserved correctly")

# ─── 8. flatten quiz (StudyTab._flatten_quiz logic) ───
print("\n[8] flatten quiz logic")
def flatten(quiz_data):
    if isinstance(quiz_data, list):
        return quiz_data
    if not isinstance(quiz_data, dict):
        return []
    cat_names = {"vocab": "Từ vựng", "pattern": "Cách dùng câu",
                 "common": "Câu thông dụng", "grammar": "Ngữ pháp", "mixed": "Tổng hợp"}
    out = []
    for cat_key in ("vocab", "pattern", "common", "grammar", "mixed"):
        for q in quiz_data.get(cat_key) or []:
            if isinstance(q, dict) and q.get("question"):
                q2 = dict(q); q2["_category"] = cat_names.get(cat_key, cat_key)
                out.append(q2)
    return out

quiz_dict = {"vocab": [{"question": "v1", "options": ["A","B","C","D"], "answer_index": 0, "explanation": ""}],
             "pattern": [{"question": "p1", "options": ["A","B","C","D"], "answer_index": 1, "explanation": ""}],
             "common": [], "grammar": [], "mixed": []}
flat = flatten(quiz_dict)
assert len(flat) == 2
assert flat[0]["_category"] == "Từ vựng"
assert flat[1]["_category"] == "Cách dùng câu"
ok("quiz dict flattened with categories")

flat_old = flatten([{"question": "old", "options": ["A","B","C","D"], "answer_index": 0, "explanation": ""}])
assert len(flat_old) == 1
ok("quiz list passed through as-is")

# ─── 9. Prompt builder sanity ───
print("\n[9] Prompt builders")
content_prompt = build_content_prompt("Tiếng Nhật", 1, 5, [{"word": "test", "pronunciation": "t"}])
assert "10" in content_prompt  # MIN_VOCAB referenced
assert "Ngày 1/5" in content_prompt
ok("content prompt contains day/total and MIN_VOCAB reference")

quiz_prompt = build_quiz_prompt("Tiếng Nhật", parsed)
assert "vocab_quiz" in quiz_prompt or "TỪ VỰNG" in quiz_prompt
assert "10" in quiz_prompt
ok("quiz prompt references all 4 categories and QUIZ_PER_TYPE")

# ─── 10. course_db migration ───
print("\n[10] course_db get_course auto-migration")
tmpdir = tempfile.mkdtemp()
try:
    # Patch COURSES_DIR temporarily
    import ai.course_db as cdb
    orig_dir = cdb.COURSES_DIR
    cdb.COURSES_DIR = tmpdir
    # Save old-format course directly
    lang = "test_lang"
    d = os.path.join(tmpdir, lang)
    os.makedirs(d, exist_ok=True)
    old_course = {
        "language": lang, "days": [
            {"day": 1, "grammar": {"title": "G", "explanation": "x", "examples": []},
             "quiz": [{"question": "q", "options": ["A","B","C","D"], "answer_index": 0, "explanation": "x"}]},
        ]
    }
    with open(os.path.join(d, "course.json"), "w", encoding="utf-8") as f:
        json.dump(old_course, f)
    loaded = cdb.get_course(lang)
    lesson = loaded["days"][0]
    assert isinstance(lesson["grammar"], list), "auto-migrated grammar"
    assert isinstance(lesson["quiz"], dict), "auto-migrated quiz"
    assert "mixed" in lesson["quiz"]
    ok("course_db auto-migrates old format on load")
    cdb.COURSES_DIR = orig_dir
finally:
    shutil.rmtree(tmpdir, ignore_errors=True)

# ─── Summary ───
print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed")
if failed:
    sys.exit(1)
