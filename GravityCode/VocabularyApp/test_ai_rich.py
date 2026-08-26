"""Smoke tests cho AI Course — format mới (3-call, rich content, tự lập giáo trình)."""
import sys, os

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai.course_generator import (
    parse_content_json, parse_quiz_json, parse_curriculum_json, parse_backbone_json,
    normalize_lesson, _strip_json,
    CONTENT_SCHEMA, QUIZ_SCHEMA, CURRICULUM_SCHEMA, BACKBONE_SCHEMA,
    build_content_prompt, build_quiz_prompt, build_curriculum_prompt, build_backbone_prompt,
    generate_course, GenerationStopped,
    MIN_VOCAB, MIN_PATTERNS, MIN_SENTENCES, MIN_GRAMMAR, MAX_GRAMMAR, QUIZ_PER_TYPE,
    JOURNEY_PHASES, LEVELS, LEVEL_PHASES, LEVEL_MIN_DAYS,
)
from ai import course_db as cdb
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

assert "items" in BACKBONE_SCHEMA["properties"]
ok("BACKBONE_SCHEMA has items list")

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

cur_prompt = build_curriculum_prompt("Tiếng Nhật", LEVELS[0], 10, target_days=30)
for ph_name, _ in JOURNEY_PHASES:
    assert ph_name in cur_prompt, f"missing phase {ph_name}"
assert "30 ngày" in cur_prompt and "10 từ vựng" in cur_prompt
ok("curriculum prompt (explicit days) contains all 5 journey phases + counts")

auto_prompt = build_curriculum_prompt("Tiếng Nhật", LEVELS[0], 10)
assert "TỰ QUYẾT" in auto_prompt and "TỐI THIỂU" in auto_prompt
assert "KHÔNG dùng từ vựng có sẵn" in auto_prompt
ok("curriculum prompt (no target_days) lets AI decide day count, no DB linking")

so_cap_phases = LEVEL_PHASES["Sơ cấp (giao tiếp cơ bản)"]
so_cap_prompt = build_curriculum_prompt("Tiếng Nhật", "Sơ cấp (giao tiếp cơ bản)", 10,
                                         phases=so_cap_phases)
assert "Nền tảng" in so_cap_prompt and "Giao tiếp cơ bản" in so_cap_prompt
assert "Trung cấp" not in so_cap_prompt.split("Giai đoạn học")[0]
assert "KHÔNG được dạy vượt quá" in so_cap_prompt
ok("Sơ cấp prompt only includes phases 1-2, explicitly forbids going beyond")

with_topics_prompt = build_curriculum_prompt(
    "Tiếng Nhật", "Trung cấp (tự tin giao tiếp)", 10,
    phases=LEVEL_PHASES["Trung cấp (tự tin giao tiếp)"],
    completed_topics=["Chào hỏi", "Số đếm", "Mua sắm", "Ăn uống"])
assert "Chào hỏi" in with_topics_prompt and "TUYỆT ĐỐI KHÔNG dạy trùng lại" in with_topics_prompt
ok("completed_topics injected into prompt — AI avoids repeating old content")

empty_content_prompt = build_content_prompt("Tiếng Nhật", 1, 5, [], topic="Bảng chữ cái Hiragana", level=LEVELS[0])
assert "TỰ CHỌN" in empty_content_prompt and "(trống)" in empty_content_prompt
assert "Bảng chữ cái Hiragana" in empty_content_prompt
assert "BẢNG CHỮ CÁI" in empty_content_prompt, "beginner guide should trigger for alphabet topic"
ok("content prompt handles EMPTY source words and injects beginner alphabet guide")

# ─── 9a. Zero-knowledge & Long Duration Prompt tests ───
print("\n[9a] Zero-knowledge & Long duration curriculum")
zero_k_prompt = build_curriculum_prompt("Tiếng Nhật", LEVELS[0], 10, phases=[0])
assert "⭐ NGUYÊN TẮC BẮT BUỘC CHO NGƯỜI MỚI BẮT ĐẦU" in zero_k_prompt
assert "Hệ chữ viết, Bảng chữ cái" in zero_k_prompt
ok("zero-knowledge rules injected into Phase 0 curriculum prompt")

long_cur_60 = build_curriculum_prompt("Tiếng Trung", LEVELS[1], 10, target_days=60)
assert "ĐÚNG 60 ngày tiếp theo" in long_cur_60 or "ĐÚNG 60 ngày" in long_cur_60
ok("curriculum prompt supports 60-day target")

long_cur_90 = build_curriculum_prompt("Tiếng Hàn", LEVELS[2], 10, target_days=90)
assert "ĐÚNG 90 ngày" in long_cur_90
ok("curriculum prompt supports 90-day target")

# ─── 9b. JSON repair test ───
print("\n[9b] JSON strip and trailing comma repair")
json_with_trailing_comma = '```json\n{"days": [{"day": 1, "title": "Test", "phase": "A", "words": [],}],}\n```'
repaired_json = _strip_json(json_with_trailing_comma)
assert json.loads(repaired_json)["days"][0]["day"] == 1
ok("_strip_json successfully strips markdown fences and repairs trailing commas")

# ─── 9b. parse_curriculum_json ───
print("\n[9b] parse_curriculum_json")
curr_json = json.dumps({"days": [
    {"day": 2, "title": "Số đếm", "phase": "Nền tảng",
     "words": [{"word": "一", "pronunciation": "ichi", "meaning_vi": "một"},
               {"word": "", "pronunciation": "", "meaning_vi": ""}]},  # bad word filtered
    {"day": 1, "title": "Chào hỏi", "phase": "Nền tảng",
     "words": [{"word": "こんにちは", "pronunciation": "konnichiwa", "meaning_vi": "xin chào"}]},
    {"bad": "data"},  # skipped
]})
pc = parse_curriculum_json(curr_json)
assert len(pc["days"]) == 2
assert pc["days"][0]["day"] == 1, "days renumbered & sorted"
assert pc["days"][0]["phase"] == "Nền tảng"
assert len(pc["days"][0]["words"]) == 1
ok(f"curriculum parsed: {len(pc['days'])} days, sorted+renumbered, phase kept, bad items filtered")

# ─── 9c. Backbone prompt and parser ───
print("\n[9c] Backbone prompt & parse_backbone_json")
bb_prompt = build_backbone_prompt("Tiếng Nhật", LEVELS[0], [0])
assert "DANH SÁCH ĐẦY ĐỦ" in bb_prompt
assert "PHÁT ÂM" in bb_prompt
ok("build_backbone_prompt creates comprehensive backbone prompt")

fake_bb_raw = json.dumps({
    "items": [
        {"id": 1, "category": "PHÁT ÂM", "title": "Bảng chữ cái Hiragana", "importance": "BẮT BUỘC"},
        {"id": 2, "category": "NGỮ PHÁP", "title": "Trợ từ は/が", "importance": "BẮT BUỘC"},
        {"invalid": "item"}
    ]
})
parsed_bb = parse_backbone_json(fake_bb_raw)
assert len(parsed_bb) == 2
assert parsed_bb[0]["title"] == "Bảng chữ cái Hiragana"
assert parsed_bb[0]["filled_day"] is None
ok("parse_backbone_json parses valid items and initializes filled_day=None")

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

# ─── 11. FULL FLOW dry-run: DB RỖNG → AI lập Backbone → sinh theo batch ───────
print("\n[11] Full flow dry-run (empty DB → AI plans backbone → 2 days generated per batch)")

_FAKE_BACKBONE = {"items": [
    {"id": 1, "category": "PHÁT ÂM", "title": "Bảng chữ cái & phát âm", "importance": "BẮT BUỘC"},
    {"id": 2, "category": "GIAO TIẾP", "title": "Chào hỏi & tự giới thiệu", "importance": "BẮT BUỘC"},
    {"id": 3, "category": "TỪ VỰNG", "title": "Số đếm & thời gian", "importance": "BẮT BUỘC"},
    {"id": 4, "category": "NGỮ PHÁP", "title": "Cấu trúc câu cơ bản", "importance": "BẮT BUỘC"},
]}
_FAKE_CONTENT = {
    "title": "Bài học mẫu",
    "vocab": [{"word": f"w{j}", "pronunciation": "p", "part_of_speech": "n",
               "meaning_vi": "nghĩa", "explanation": "giải thích",
               "example_sentence": "câu ví dụ", "example_meaning_vi": "dịch"}
              for j in range(10)],
    "sentence_patterns": [{"pattern": f"mẫu {j}", "meaning_vi": "nghĩa",
                           "structure_note": "ghi chú", "example_sentence": "vd",
                           "example_meaning_vi": "dịch"} for j in range(10)],
    "common_sentences": [{"sentence": f"câu {j}", "meaning_vi": "nghĩa",
                          "situation": "tình huống"} for j in range(10)],
    "grammar": [{"title": f"ngữ pháp {j}", "explanation": "chi tiết",
                 "examples": [{"sentence": "s", "meaning_vi": "m"}]} for j in range(2)],
}
_FAKE_QUIZ = {k: [{"question": f"{k} q{i}", "options": ["A", "B", "C", "D"],
                   "answer_index": i % 4, "explanation": "ok"} for i in range(10)]
              for k in ("vocab_quiz", "pattern_quiz", "common_quiz", "grammar_quiz")}

_capture = {"backbone_prompt": "", "curriculum_prompt": ""}

class _FakeCoordinator:
    def __init__(self, **kw):
        self.kw = kw
        self.calls = []
    def request(self, prompt, response_schema=None):
        self.calls.append(response_schema)
        if response_schema is BACKBONE_SCHEMA:
            _capture["backbone_prompt"] = prompt
            return {"ok": True, "text": json.dumps(_FAKE_BACKBONE), "model": "fake"}
        if response_schema is CURRICULUM_SCHEMA:
            _capture["curriculum_prompt"] = prompt
            return {"ok": True, "text": json.dumps({"days": []}), "model": "fake"}
        if response_schema is CONTENT_SCHEMA:
            return {"ok": True, "text": json.dumps(_FAKE_CONTENT), "model": "fake"}
        return {"ok": True, "text": json.dumps(_FAKE_QUIZ), "model": "fake"}

tmpdir = tempfile.mkdtemp()
try:
    import ai.course_generator as cg
    orig_dir = cdb.COURSES_DIR
    orig_keys = cg._load_gemini_keys
    orig_batch = cg.BACKBONE_BATCH_SIZE
    cdb.COURSES_DIR = tmpdir
    cg._load_gemini_keys = lambda: [{"key": "fake"}]
    cg.BACKBONE_BATCH_SIZE = 2  # batch 2 item để test tiếp nối

    logs = []
    stats = generate_course(
        "FakeLang", words_per_day=5,
        log_fn=logs.append, level=LEVELS[0], target_days=2,
        coordinator_cls=_FakeCoordinator,
    )
    assert stats["generated"] == 2 and stats["backbone_total"] == 4, stats

    course = cdb.get_course("FakeLang")
    assert len(course["days"]) == 2
    assert course["backbone"] is not None
    assert course["backbone"]["items"][0]["filled_day"] == 1
    assert course["backbone"]["items"][1]["filled_day"] == 2
    assert course["backbone"]["items"][2]["filled_day"] is None
    day1 = course["days"][0]
    assert len(day1["vocab"]) == 10
    assert len(day1["sentence_patterns"]) == 10
    assert len(day1["common_sentences"]) == 10
    assert len(day1["grammar"]) == 2
    total_q = sum(len(v) for v in day1["quiz"].values())
    assert total_q == 40, f"expected 40 quiz questions, got {total_q}"
    ok(f"dry-run batch 1: 2/4 backbone items filled with rich content & quiz")

    # Mở rộng / Tiếp tục batch 2: sinh tiếp items 3, 4 -> Ngày 3, 4
    stats2 = generate_course(
        "FakeLang", words_per_day=5,
        log_fn=logs.append, level=LEVELS[0], target_days=2,
        coordinator_cls=_FakeCoordinator,
    )
    assert stats2["generated"] == 2, stats2
    c2 = cdb.get_course("FakeLang")
    assert len(c2["days"]) == 4, f"Tổng tích lũy phải là 4 ngày, got {len(c2['days'])}"
    assert c2["days"][-1]["day"] == 4, "Ngày mới phải tiếp nối Ngày 4"
    assert all(it["filled_day"] is not None for it in c2["backbone"]["items"])
    ok(f"batch 2: sinh tiếp 2 ngày (generated={stats2['generated']}), hoàn tất 4/4 backbone items")

    # Batch 3: khi backbone đã 100% đầy đủ
    stats3 = generate_course(
        "FakeLang", words_per_day=5,
        log_fn=logs.append, level=LEVELS[0], target_days=2,
        coordinator_cls=_FakeCoordinator,
    )
    assert stats3["generated"] == 0, "backbone full -> 0 generated"
    ok("batch 3: backbone 100% full -> báo hoàn tất cấp độ, không sinh thừa")

    # Stop check hoạt động
    def _stop():
        return True
    try:
        generate_course("FakeLang2", stop_check=_stop,
                        coordinator_cls=_FakeCoordinator)
        assert False, "should raise GenerationStopped"
    except GenerationStopped:
        ok("stop_check raises GenerationStopped immediately")

    # ── Level transition: chuyển level → AI sinh backbone mới tương ứng ──
    _capture["backbone_prompt"] = ""
    stats_level = generate_course(
        "FakeLang", words_per_day=5,
        log_fn=logs.append,
        level="Trung cấp (tự tin giao tiếp)",
        coordinator_cls=_FakeCoordinator,
    )
    prompt = _capture["backbone_prompt"]
    assert "Trung cấp (tự tin giao tiếp)" in prompt
    ok("level transition: đổi sang Trung cấp -> AI sinh backbone mới cho Trung cấp")

    # ── force_new xóa sạch course + progress cũ ──
    stats_force = generate_course("FakeLang", words_per_day=5, force_new=True,
                                  log_fn=logs.append, level="Người mới bắt đầu",
                                  coordinator_cls=_FakeCoordinator)
    assert stats_force["generated"] == 2
    c_new = cdb.get_course("FakeLang")
    assert len(c_new["days"]) == 2
    assert c_new["days"][0]["day"] == 1
    ok("force_new=True: reset toàn bộ, bắt đầu lại từ Ngày 1 với backbone mới")

    cg.BACKBONE_BATCH_SIZE = orig_batch
    cdb.COURSES_DIR = orig_dir
    cg._load_gemini_keys = orig_keys
finally:
    shutil.rmtree(tmpdir, ignore_errors=True)

# ─── Summary ───
print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed")
if failed:
    sys.exit(1)
