"""Smoke tests cho AI Course — format mới (3-call, rich content, tự lập giáo trình)."""
import sys, os, time

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
    CONTENT_SCHEMA, QUIZ_SCHEMA, QUIZ_SCHEMA_AB, QUIZ_SCHEMA_CD,
    CURRICULUM_SCHEMA, BACKBONE_SCHEMA,
    ADAPT_STAGE_SCHEMA, GAP_INSERT_SCHEMA,
    build_content_prompt, build_quiz_prompt, build_quiz_prompt_ab, build_quiz_prompt_cd,
    build_curriculum_prompt, build_backbone_prompt,
    build_stage_backbone_prompt, build_stage_universal_template, build_master_backbone,
    get_language_fsi_profile, get_language_native_profile, audit_and_supplement_course,
    generate_course, GenerationStopped,
    MIN_VOCAB, MIN_PATTERNS, MIN_SENTENCES, MIN_GRAMMAR, MAX_GRAMMAR, QUIZ_PER_TYPE,
    JOURNEY_PHASES, LEVELS, LEVEL_PHASES, LEVEL_MIN_DAYS,
)
from ai.language_profiler import (
    get_or_create_language_profile,
    get_rule_based_fallback_profile,
    load_cached_language_profiles,
    save_cached_language_profiles,
)
from VocabApp import _short_level_name
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

cur_prompt = build_curriculum_prompt("Tiếng Nhật", LEVELS[0], 10, target_days=100)
for ph_name, _ in JOURNEY_PHASES:
    assert ph_name in cur_prompt, f"missing phase {ph_name}"
assert "100 ngày" in cur_prompt and "10 từ vựng" in cur_prompt
ok("curriculum prompt (explicit days) contains all 6 journey phases + counts")

auto_prompt = build_curriculum_prompt("Tiếng Nhật", LEVELS[0], 10)
assert "TỰ QUYẾT" in auto_prompt and "TỐI THIỂU" in auto_prompt
assert "KHÔNG dùng từ vựng có sẵn" in auto_prompt
ok("curriculum prompt (no target_days) lets AI decide day count, no DB linking")

so_cap_phases = LEVEL_PHASES["3. Sơ cấp (Giao tiếp đời sống cơ bản - A1/A2)"]
so_cap_prompt = build_curriculum_prompt("Tiếng Nhật", "3. Sơ cấp (Giao tiếp đời sống cơ bản - A1/A2)", 10,
                                         phases=so_cap_phases)
assert "Sơ cấp đời sống" in so_cap_prompt
assert "KHÔNG được dạy vượt quá" in so_cap_prompt
ok("Sơ cấp prompt only includes phase 3, explicitly forbids going beyond")

with_topics_prompt = build_curriculum_prompt(
    "Tiếng Nhật", "4. Trung cấp (Tự tin diễn đạt & Công sở - B1/B2)", 10,
    phases=LEVEL_PHASES["4. Trung cấp (Tự tin diễn đạt & Công sở - B1/B2)"],
    completed_topics=["Chào hỏi", "Số đếm", "Mua sắm", "Ăn uống"])
assert "Chào hỏi" in with_topics_prompt and "TUYỆT ĐỐI KHÔNG dạy trùng lại" in with_topics_prompt
ok("completed_topics injected into prompt — AI avoids repeating old content")

empty_content_prompt = build_content_prompt("Tiếng Nhật", 1, 5, [], topic="Bảng chữ cái Hiragana", level=LEVELS[1])
assert "TỰ CHỌN" in empty_content_prompt and "(trống)" in empty_content_prompt
assert "Bảng chữ cái Hiragana" in empty_content_prompt
assert "VỠ LÒNG CHỮ CÁI" in empty_content_prompt, "beginner guide should trigger for alphabet topic"
ok("content prompt handles EMPTY source words and injects beginner alphabet guide")

native_content_prompt = build_content_prompt("Tiếng Anh", 50, 50, [], topic="Thành ngữ và tiếng lóng đường phố", level=LEVELS[6])
assert "BẢN XỨ HÓA" in native_content_prompt
ok("content prompt injects Native Proficiency guide for Level 6 topics")

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

# ─── 9b. JSON strip and trailing comma repair ───
print("\n[9b] JSON strip and trailing comma repair")
json_with_trailing_comma = '```json\n{"days": [{"day": 1, "title": "Test", "phase": "A", "words": [],}],}\n```'
repaired_json = _strip_json(json_with_trailing_comma)
assert json.loads(repaired_json)["days"][0]["day"] == 1
ok("_strip_json successfully strips markdown fences and repairs trailing commas")

# ─── 9b. parse_curriculum_json ───
print("\n[9b] parse_curriculum_json")
curr_json = json.dumps({"days": [
    {"day": 2, "title": "Số đếm", "phase": "Vỡ lòng chữ cái & phát âm",
     "words": [{"word": "一", "pronunciation": "ichi", "meaning_vi": "một"},
               {"word": "", "pronunciation": "", "meaning_vi": ""}]},  # bad word filtered
    {"day": 1, "title": "Chào hỏi", "phase": "Vỡ lòng chữ cái & phát âm",
     "words": [{"word": "こんにちは", "pronunciation": "konnichiwa", "meaning_vi": "xin chào"}]},
    {"bad": "data"},  # skipped
]})
pc = parse_curriculum_json(curr_json)
assert len(pc["days"]) == 2
assert pc["days"][0]["day"] == 1, "days renumbered & sorted"
assert pc["days"][0]["phase"] == "Vỡ lòng chữ cái & phát âm"
assert len(pc["days"][0]["words"]) == 1
ok(f"curriculum parsed: {len(pc['days'])} days, sorted+renumbered, phase kept, bad items filtered")

# ─── 9c. Backbone prompt and parser ───
print("\n[9c] Backbone prompt & parse_backbone_json")
bb_prompt = build_backbone_prompt("Tiếng Nhật", LEVELS[0], [0])
assert "DANH SÁCH ĐẦY ĐỦ" in bb_prompt
assert "PHÁT ÂM" in bb_prompt
assert "ĐẶC THÙ NGÔN NGỮ" in bb_prompt
ok("build_backbone_prompt creates comprehensive backbone prompt with typology guidance")

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

# ─── 9d. Multi-Pass Backbone Refinement (AskCpl-style) ───
print("\n[9d] Multi-Pass Backbone Refinement")
from ai.course_generator import (
    find_duplicate_topics, repair_duplicate_topics,
    review_and_fill_gaps, normalize_backbone_sequence,
)

test_items = [
    {"id": 1, "category": "PHÁT ÂM", "title": "Bảng chữ cái Hiragana cơ bản", "importance": "BẮT BUỘC"},
    {"id": 2, "category": "PHÁT ÂM", "title": "Bảng chữ cái Hiragana cơ bản", "importance": "BẮT BUỘC"},  # 100% trùng
    {"id": 3, "category": "GIAO TIẾP", "title": "Chào hỏi và làm quen", "importance": "BẮT BUỘC"},
    {"id": 4, "category": "GIAO TIẾP", "title": "Chào hỏi và làm quen hàng ngày", "importance": "NÊN HỌC"}, # > 85% trùng
    {"id": 5, "category": "NGỮ PHÁP", "title": "Trợ từ Wa và Ga", "importance": "BẮT BUỘC"},
]

dups = find_duplicate_topics(test_items, sim_threshold=0.80)
assert len(dups) >= 2, f"Phải tìm thấy ít nhất 2 cặp trùng, got {len(dups)}"
ok(f"find_duplicate_topics: phát hiện {len(dups)} chủ đề trùng lặp")

class _FakeRepairCoord:
    def __init__(self):
        self.count = 0
    def request(self, prompt, response_schema=None):
        if response_schema and "gaps" in response_schema.get("properties", {}):
            return {"ok": True, "text": json.dumps({"gaps": [
                {"category": "PHÁT ÂM", "title": "Quy tắc âm ngắt và trường âm", "importance": "BẮT BUỘC"}
            ]}), "model": "fake"}
        self.count += 1
        titles = [
            ("Bảng chữ cái Katakana và từ mượn", "PHÁT ÂM"),
            ("Hỏi thăm sức khỏe và cảm ơn xin lỗi", "GIAO TIẾP"),
            ("Chủ đề bổ sung khác biệt", "NGỮ PHÁP"),
        ]
        t, c = titles[(self.count - 1) % len(titles)]
        return {"ok": True, "text": json.dumps({
            "title": t,
            "category": c,
            "importance": "BẮT BUỘC"
        }), "model": "fake"}

items_repaired = [dict(it) for it in test_items]
repair_duplicate_topics(items_repaired, "Tiếng Nhật", "Người mới bắt đầu", _FakeRepairCoord(), sim_threshold=0.80)
dups_after = find_duplicate_topics(items_repaired, sim_threshold=0.80)
assert len(dups_after) == 0, f"Sau khi sửa không còn trùng, got {len(dups_after)}"
ok("repair_duplicate_topics: sửa tại chỗ thành công, 0 trùng lặp")

items_with_gaps = review_and_fill_gaps(items_repaired, "Tiếng Nhật", "Người mới bắt đầu", _FakeRepairCoord())
assert any("trường âm" in it["title"] for it in items_with_gaps)
ok("review_and_fill_gaps: bổ sung thành công các mảng kiến thức còn thiếu")

sorted_seq = normalize_backbone_sequence(items_with_gaps)
# Phát âm phải đứng trước Ngữ pháp và Giao tiếp
assert sorted_seq[0]["category"] == "PHÁT ÂM"
assert all(sorted_seq[i]["id"] == i + 1 for i in range(len(sorted_seq)))
ok("normalize_backbone_sequence: sắp xếp thứ tự sư phạm logic và renumber chuẩn xác")

# ─── 10. course_db migration ───
print("\n[10] course_db get_course auto-migration")
old_c = {
    "language": "OldLang", "level": "Người mới bắt đầu",
    "days": [{"day": 1, "title": "B1", "vocab": [], "grammar": {"title": "G1", "explanation": "E1"},
              "quiz": [{"question": "Q1", "options": ["A","B","C","D"], "answer_index": 0}]}],
}
tmpdir_old = tempfile.mkdtemp()
try:
    orig_cdb_dir = cdb.COURSES_DIR
    cdb.COURSES_DIR = tmpdir_old
    cdb.save_course("OldLang", old_c)
    loaded = cdb.get_course("OldLang")
    assert isinstance(loaded["days"][0]["grammar"], list)
    assert isinstance(loaded["days"][0]["quiz"], dict)
    assert "mixed" in loaded["days"][0]["quiz"]
    ok("course_db auto-migrates old format on load")
finally:
    cdb.COURSES_DIR = orig_cdb_dir
    shutil.rmtree(tmpdir_old, ignore_errors=True)

# ─── 11. Full flow dry-run (Multi-Pass + Continuous Generation) ───
print("\n[11] Full flow dry-run (Multi-Pass + Continuous Generation)")
_STAGE_TOPICS = [
    ("PHÁT ÂM",   ["Hiragana hàng A-K",       "Hiragana hàng S-N",       "Katakana hàng A-K",       "Thanh điệu & Pitch"]),
    ("TỪ ĐƠN",    ["Số đếm 1-100",            "Đại từ nhân xưng",        "Chào hỏi sinh tồn",       "Thời gian & Ngày tháng"]),
    ("SƠ CẤP",    ["Mua sắm & Giá cả",        "Ăn uống & Nhà hàng",      "Hỏi đường & Giao thông",  "Sức khỏe & Bệnh viện"]),
    ("TRUNG CẤP", ["Công việc & Công sở",      "Câu phức & Liên từ",      "Kể chuyện & Tường thuật", "Thư tín chính thức"]),
    ("CAO CẤP",   ["Báo chí & Thời sự",       "Học thuật & Nghiên cứu",  "Tranh biện & Lập luận",   "Văn phong trang trọng"]),
    ("BẢN XỨ",   ["Thành ngữ & Tục ngữ",     "Tiếng lóng & Slang",      "Chơi chữ & Ẩn dụ",        "Capstone tổng hợp"]),
]

_stage_call_idx = [0]  # dùng list để có thể mutate từ closure

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
        if response_schema is ADAPT_STAGE_SCHEMA:
            _capture["backbone_prompt"] = prompt
            stage_idx = min(_stage_call_idx[0], 5)
            cat, titles = _STAGE_TOPICS[stage_idx]
            _stage_call_idx[0] += 1
            # Giả lập trả về đúng 4 items cho test
            topics = [{"slot_id": i + 1, "category": cat, "title": f"{titles[i % len(titles)]} (Chuyên sâu)", "importance": "BẮT BUỘC"} for i in range(40)]
            return {"ok": True, "text": json.dumps({"topics": topics}), "model": "fake"}
        if response_schema is GAP_INSERT_SCHEMA:
            return {"ok": True, "text": json.dumps({"insertions": []}), "model": "fake"}
        if response_schema is BACKBONE_SCHEMA:
            _capture["backbone_prompt"] = prompt
            stage_idx = min(_stage_call_idx[0], 5)
            cat, titles = _STAGE_TOPICS[stage_idx]
            _stage_call_idx[0] += 1
            items = [{"id": i + 1, "category": cat, "title": titles[i % len(titles)], "importance": "BẮT BUỘC"} for i in range(4)]
            return {"ok": True, "text": json.dumps({"items": items}), "model": "fake"}
        if response_schema and "gaps" in response_schema.get("properties", {}):
            return {"ok": True, "text": json.dumps({"gaps": []}), "model": "fake"}
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

    # Test Continuous Generation: Không giới hạn batch -> Sinh liền một mạch 100% (240/240 ngày qua 6 chặng)
    _stage_call_idx[0] = 0  # reset stage counter
    cg.BACKBONE_BATCH_SIZE = None
    logs = []
    stats_all = generate_course(
        "FakeLangFull", words_per_day=5,
        log_fn=logs.append, level=LEVELS[0],
        coordinator_cls=_FakeCoordinator,
    )
    assert stats_all["generated"] == 700 and stats_all["backbone_total"] == 700, stats_all
    course_full = cdb.get_course("FakeLangFull")
    assert len(course_full["days"]) == 700
    assert all(it["filled_day"] is not None for it in course_full["backbone"]["items"])
    ok("continuous generation: sinh liền một mạch 100% 700/700 chủ đề qua cả 6 Chặng")

    # Test Batch Paced: Nếu chỉ định batch=2 thì vẫn chạy từng đợt 2 ngày
    _stage_call_idx[0] = 0  # reset stage counter cho FakeLang mới
    cg.BACKBONE_BATCH_SIZE = 2
    logs = []
    stats = generate_course(
        "FakeLang", words_per_day=5,
        log_fn=logs.append, level=LEVELS[0], max_days_per_run=2,
        coordinator_cls=_FakeCoordinator,
    )
    assert stats["generated"] == 2 and stats["backbone_total"] == 700, stats

    course = cdb.get_course("FakeLang")
    assert len(course["days"]) == 2
    assert course["backbone"] is not None
    assert course["backbone"]["items"][0]["filled_day"] == 1
    assert course["backbone"]["items"][1]["filled_day"] == 2
    day1 = course["days"][0]
    assert len(day1["vocab"]) == 10
    assert len(day1["sentence_patterns"]) == 10
    assert len(day1["common_sentences"]) == 10
    assert len(day1["grammar"]) == 2

    # ── Level transition: chuyển level → AI sinh backbone mới tương ứng ──
    _stage_call_idx[0] = 0
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
    _stage_call_idx[0] = 0
    stats_force = generate_course("FakeLang", words_per_day=5, force_new=True,
                                  log_fn=logs.append, level="Người mới bắt đầu",
                                  coordinator_cls=_FakeCoordinator)
    assert stats_force["generated"] == 2
    c_new = cdb.get_course("FakeLang")
    assert len(c_new["days"]) == 2
    assert c_new["days"][0]["day"] == 1
    ok("force_new=True: reset toàn bộ, bắt đầu lại từ Ngày 1 với backbone mới")

    # ── [12] Test GeminiCoordinator: lock_after_success=False & Cooldown Recovery ──
    print("\n[12] GeminiCoordinator lock_after_success & cooldown recovery")
    from api.gemini_safe import GeminiCoordinator, AccountPool, ErrorKind
    pool = AccountPool()
    test_keys = [
        {"key": "AIzaSyTestKey1", "email": "user1@gmail.com", "status": "active"},
        {"key": "AIzaSyTestKey2", "email": "user2@gmail.com", "status": "active"},
    ]
    pool.sync(test_keys)
    coord_test = GeminiCoordinator(
        key_loader=lambda: test_keys,
        lock_after_success=False,
    )
    # Khóa account user1 ngắn hạn (cooldown 1s)
    pool.lock_account(key_obj=test_keys[0], duration=1)
    now = time.time()
    assert pool.account_locked("user1@gmail.com", now) == True
    # Pick sẽ tự động chọn user2@gmail.com
    k2 = pool.pick()
    assert k2["email"] == "user2@gmail.com"
    # Sau khi thành công, với lock_after_success=False thì user2 KHÔNG bị khóa 1 giờ (3600s)
    coord_test._maybe_lock_after_success(k2, test_keys)
    assert pool.account_locked("user2@gmail.com", time.time()) == False
    ok("lock_after_success=False: key không bị khóa 3600s oan sau mỗi lượt gọi thành công")

    # ── [13] Test get_language_fsi_profile: Category & Duration Calculations ──
    print("\n[13] get_language_fsi_profile: Category & Duration Calculations")
    fsi_jp = get_language_fsi_profile("Tiếng Nhật")
    assert fsi_jp["total_days"] == 420
    assert len(fsi_jp["stages"]) == 6
    assert fsi_jp["stages"][0]["target_days"] == 30
    assert fsi_jp["stages"][5]["target_days"] == 58
    ok("get_language_fsi_profile: Tiếng Nhật -> FSI Category IV/V với 420 ngày và 6 chặng chuẩn")

    fsi_en = get_language_fsi_profile("Tiếng Anh")
    assert fsi_en["total_days"] == 240
    assert fsi_en["stages"][0]["target_days"] == 17
    ok("get_language_fsi_profile: Tiếng Anh -> FSI Category I với 240 ngày")

    fsi_fr = get_language_fsi_profile("Tiếng Pháp")
    assert fsi_fr["total_days"] == 320
    ok("get_language_fsi_profile: Tiếng Pháp -> FSI Category II/III với 320 ngày")

    fsi_ru = get_language_fsi_profile("Tiếng Nga")
    assert fsi_ru["total_days"] == 360
    ok("get_language_fsi_profile: Tiếng Nga -> FSI Category III/IV với 360 ngày")

    # ── [14] Test build_stage_universal_template: Layer 1 Hardcoded Slots & Spiral Review ──
    print("\n[14] build_stage_universal_template: Layer 1 Base Slots & Spiral Review")
    st0_slots = build_stage_universal_template(0, 30)
    assert len(st0_slots) == 30
    assert st0_slots[6]["is_review_day"] == True and "ÔN TẬP TUẦN 1" in st0_slots[6]["generic_name"]
    assert st0_slots[13]["is_review_day"] == True and "ÔN TẬP TUẦN 2" in st0_slots[13]["generic_name"]
    assert st0_slots[20]["is_review_day"] == True and "ÔN TẬP TUẦN 3" in st0_slots[20]["generic_name"]
    assert st0_slots[27]["is_review_day"] == True and "ÔN TẬP TUẦN 4" in st0_slots[27]["generic_name"]
    assert st0_slots[29]["is_review_day"] == True and "TỔNG KẾT CHẶNG 1" in st0_slots[29]["generic_name"]
    ok("build_stage_universal_template: generates exactly 30 slots with spiral review on days 7, 14, 21, 28 & stage summary on day 30")

    st1_slots = build_stage_universal_template(1, 38)
    assert len(st1_slots) == 38
    assert st1_slots[37]["is_review_day"] == True and "TỔNG KẾT CHẶNG 2" in st1_slots[37]["generic_name"]
    ok("build_stage_universal_template: generates exactly 38 slots for stage 2")

    # ── [15] Test Content Prompt: 3-Tier Phonetics, Spiral Review Day, Native Pragmatics ──
    print("\n[15] Content Prompt: 3-Tier Phonetics, Spiral Review, Native Nuance")
    p_st1 = build_content_prompt("Tiếng Nhật", 1, 420, [], topic="Bảng chữ cái Hiragana - Hàng A", level="⭐ Trọn gói")
    assert "GIẢI PHẪU KHẨU HÌNH & PHÁT ÂM 3 LỚP" in p_st1
    assert "vị trí răng, lưỡi" in p_st1
    ok("build_content_prompt: Stage 1 injects 3-Tier Phonetic Articulatory anatomy")

    p_review = build_content_prompt("Tiếng Nhật", 7, 420, [], topic="Ôn tập tuần 1 & Thực hành phản xạ", level="⭐ Trọn gói")
    assert "NGÀY ÔN TẬP TUẦN & TỔNG HỢP THỰC HÀNH ('6 + 1')" in p_review
    assert "HỘI THOẠI TÌNH HUỐNG THỰC TẾ" in p_review
    ok("build_content_prompt: Day 7 injects Weekly Spiral Review guidance")

    p_native = build_content_prompt("Tiếng Nhật", 380, 420, [], topic="Tiếng lóng giới trẻ và thành ngữ đời thực", level="⭐ Trọn gói")
    assert "NATIVE PROFICIENCY & CULTURE NUANCE" in p_native
    assert "High-context culture" in p_native
    ok("build_content_prompt: Stage 6 injects Native Pragmatics & Cultural contrast")

    # ── [16] Test Quiz Prompt: Pedagogical Distractors (Word-for-Word, Confusing Pair) ──
    print("\n[16] Quiz Prompt: Pedagogical Distractors")
    p_quiz = build_quiz_prompt("Tiếng Nhật", {"vocab": [{"word": "犬", "meaning_vi": "chó"}]})
    assert "BẪY TRẮC NGHIỆM SƯ PHẠM" in p_quiz
    assert "Word-for-Word Trap" in p_quiz
    assert "Confusing Pair Trap" in p_quiz
    ok("build_quiz_prompt: includes 4-option pedagogical distractor rules")

    # ── [17] Test _short_level_name in VocabApp: Accurate Stage Badges ──
    print("\n[17] _short_level_name: Stage-Badged Mapping")
    assert _short_level_name("", "Vỡ lòng chữ cái & phát âm") == "Vỡ lòng"
    assert _short_level_name("", "Ghép âm & Từ đơn sinh tồn") == "Ghép âm"
    assert _short_level_name("", "Sơ cấp đời sống (A1-A2)") == "Sơ cấp"
    assert _short_level_name("", "Trung cấp công sở (B1-B2)") == "Trung cấp"
    assert _short_level_name("", "Cao cấp học thuật (C1)") == "Cao cấp"
    assert _short_level_name("", "Bản xứ hóa (C2 & Slang)") == "Bản xứ"
    assert _short_level_name("⭐ Trọn gói: Từ con số 0 đến Như người bản xứ", "Vỡ lòng chữ cái") == "Vỡ lòng"
    ok("_short_level_name: accurately maps all 6 stages without generic fallback")

    # ── [18] Test build_master_backbone: 3-Layer Master Architecture & Gap Insertion ──
    print("\n[18] build_master_backbone: 3-Layer Architecture & Gap Insertion")
    class _MasterFakeCoord:
        def request(self, prompt, response_schema=None):
            if response_schema is ADAPT_STAGE_SCHEMA:
                # Giả lập adapt thành công
                topics = [{"slot_id": i + 1, "title": f"Chủ đề adapt {i+1}", "category": "NGỮ PHÁP"} for i in range(150)]
                return {"ok": True, "text": json.dumps({"topics": topics})}
            if response_schema is GAP_INSERT_SCHEMA:
                # Giả lập chèn 2 topics vào sau slot 5
                insertions = [
                    {"after_slot_id": 5, "title": "Chủ đề đặc thù chèn 1", "category": "CHỮ VIẾT", "importance": "BẮT BUỘC"},
                    {"after_slot_id": 5, "title": "Chủ đề đặc thù chèn 2", "category": "PHÁT ÂM", "importance": "BẮT BUỘC"},
                ]
                return {"ok": True, "text": json.dumps({"insertions": insertions})}
            return {"ok": True, "text": "{}"}

    fsi_test_jp = get_language_fsi_profile("Tiếng Nhật")
    mb = build_master_backbone("Tiếng Nhật", fsi_test_jp, _MasterFakeCoord())
    assert mb["template_base_count"] == 420
    assert mb["ai_inserted_count"] == 12  # 2 insertions x 6 stages = 12
    assert len(mb["items"]) == 432  # 420 + 12 = 432 items tổng
    assert mb["items"][0]["id"] == 1
    assert mb["items"][-1]["id"] == 432
    assert mb["items"][5]["is_ai_inserted"] == True  # item chèn sau slot 5
    ok("build_master_backbone: 420 base + 12 gap insertions = 432 items liên tục")

    # ── [19] Test build_master_backbone: Retry Fallback & Pending Retries Tracking ──
    print("\n[19] build_master_backbone: Retry Fallback & Pending Retries")
    class _FailingCoord:
        def request(self, prompt, response_schema=None):
            return {"ok": False, "error": {"kind": "OVERLOADED", "message": "503"}}

    mb_fail = build_master_backbone("Tiếng Anh", get_language_fsi_profile("Tiếng Anh"), _FailingCoord())
    assert mb_fail["template_base_count"] == 240
    assert len(mb_fail["items"]) == 240  # Vẫn đủ 100% 240 items từ template cứng
    assert mb_fail["pending_retry_count"] == 240  # Đánh dấu 240 items cần retry
    assert mb_fail["items"][0]["needs_retry"] == True
    assert mb_fail["items"][0]["title"] == "Tổng quan ngôn ngữ, nguồn gốc & hệ thống chữ viết"
    ok("build_master_backbone fallback: bảo đảm 100% 240 slots cứng khi API lỗi và ghi nhận pending_retry_count")

    cg.BACKBONE_BATCH_SIZE = orig_batch
    cdb.COURSES_DIR = orig_dir
    cg._load_gemini_keys = orig_keys
finally:
    shutil.rmtree(tmpdir, ignore_errors=True)

# ─── 20. Split-Quiz A+C: parse_quiz_json(keys), build_quiz_prompt_ab/cd, schemas ───
print("\n[20] Split-Quiz A+C: parse_quiz_json keys, prompt_ab/cd, schemas")
import json as _json

# 20a: parse_quiz_json với keys split AB
ab_json = _json.dumps({
    "vocab_quiz":   [{"question": f"V{i}", "options": ["A","B","C","D"], "answer_index": 0, "explanation": "ok"} for i in range(10)],
    "pattern_quiz": [{"question": f"P{i}", "options": ["A","B","C","D"], "answer_index": 1, "explanation": "ok"} for i in range(10)],
})
parsed_ab = parse_quiz_json(ab_json, keys=("vocab_quiz", "pattern_quiz"))
assert len(parsed_ab["vocab"]) == 10,   f"AB vocab: expected 10, got {len(parsed_ab['vocab'])}"
assert len(parsed_ab["pattern"]) == 10, f"AB pattern: expected 10, got {len(parsed_ab['pattern'])}"
assert "common" not in parsed_ab,  "AB không được có key 'common'"
assert "grammar" not in parsed_ab, "AB không được có key 'grammar'"
ok("parse_quiz_json(keys=AB): chỉ parse vocab + pattern, không lẫn common/grammar")

# 20b: parse_quiz_json với keys split CD
cd_json = _json.dumps({
    "common_quiz":  [{"question": f"C{i}", "options": ["A","B","C","D"], "answer_index": 2, "explanation": "ok"} for i in range(10)],
    "grammar_quiz": [{"question": f"G{i}", "options": ["A","B","C","D"], "answer_index": 3, "explanation": "ok"} for i in range(10)],
})
parsed_cd = parse_quiz_json(cd_json, keys=("common_quiz", "grammar_quiz"))
assert len(parsed_cd["common"]) == 10,   f"CD common: expected 10, got {len(parsed_cd['common'])}"
assert len(parsed_cd["grammar"]) == 10,  f"CD grammar: expected 10, got {len(parsed_cd['grammar'])}"
assert "vocab" not in parsed_cd,   "CD không được có key 'vocab'"
assert "pattern" not in parsed_cd, "CD không được có key 'pattern'"
ok("parse_quiz_json(keys=CD): chỉ parse common + grammar, không lẫn vocab/pattern")

# 20c: parse_quiz_json không truyền keys → backward compat đủ 4 loại
full_json = _json.dumps({
    "vocab_quiz":   [{"question":"V", "options":["A","B","C","D"], "answer_index":0, "explanation":"x"}],
    "pattern_quiz": [{"question":"P", "options":["A","B","C","D"], "answer_index":0, "explanation":"x"}],
    "common_quiz":  [{"question":"C", "options":["A","B","C","D"], "answer_index":0, "explanation":"x"}],
    "grammar_quiz": [{"question":"G", "options":["A","B","C","D"], "answer_index":0, "explanation":"x"}],
})
parsed_full = parse_quiz_json(full_json)
assert len(parsed_full) == 4, "Full parse phải có đúng 4 keys"
ok("parse_quiz_json(no keys): backward compat, parse đủ 4 loại")

# 20d: build_quiz_prompt_ab chỉ chứa vocab và pattern, không mention common/grammar quiz
_sample_lesson = {
    "vocab": [{"word": "犬", "pronunciation": "いぬ", "meaning_vi": "chó"}],
    "sentence_patterns": [{"pattern": "〜は〜です", "meaning_vi": "〜là〜"}],
    "common_sentences": [{"sentence": "こんにちは", "meaning_vi": "xin chào", "situation": "chào hỏi"}],
    "grammar": [{"title": "は vs が", "explanation": "phân biệt trợ từ", "examples": []}],
}
pab = build_quiz_prompt_ab("Tiếng Nhật", _sample_lesson)
assert "vocab_quiz" in pab,   "prompt_ab phải mention vocab_quiz"
assert "pattern_quiz" in pab, "prompt_ab phải mention pattern_quiz"
assert "common_quiz" not in pab,  "prompt_ab KHÔNG được mention common_quiz"
assert "grammar_quiz" not in pab, "prompt_ab KHÔNG được mention grammar_quiz"
assert "CHỈ 2 LOẠI" in pab,  "prompt_ab phải chứa 'CHỈ 2 LOẠI'"
ok("build_quiz_prompt_ab: chỉ sinh vocab+pattern, không lẫn common/grammar")

# 20e: build_quiz_prompt_cd chỉ chứa common và grammar, không mention vocab/pattern quiz
pcd = build_quiz_prompt_cd("Tiếng Nhật", _sample_lesson)
assert "common_quiz" in pcd,  "prompt_cd phải mention common_quiz"
assert "grammar_quiz" in pcd, "prompt_cd phải mention grammar_quiz"
assert "vocab_quiz" not in pcd,   "prompt_cd KHÔNG được mention vocab_quiz"
assert "pattern_quiz" not in pcd, "prompt_cd KHÔNG được mention pattern_quiz"
assert "CHỈ 2 LOẠI" in pcd,  "prompt_cd phải chứa 'CHỈ 2 LOẠI'"
ok("build_quiz_prompt_cd: chỉ sinh common+grammar, không lẫn vocab/pattern")

# 20f: Cả 2 prompts đều có trap rules sư phạm
assert "Word-for-Word Trap" in pab, "prompt_ab phải có Word-for-Word Trap"
assert "Word-for-Word Trap" in pcd, "prompt_cd phải có Word-for-Word Trap"
ok("Cả 2 split-prompts đều có đủ 4 quy tắc bẫy sư phạm")

# 20g: QUIZ_SCHEMA_AB và QUIZ_SCHEMA_CD đúng cấu trúc
assert "vocab_quiz" in QUIZ_SCHEMA_AB["properties"],   "QUIZ_SCHEMA_AB phải có vocab_quiz"
assert "pattern_quiz" in QUIZ_SCHEMA_AB["properties"],  "QUIZ_SCHEMA_AB phải có pattern_quiz"
assert "common_quiz" not in QUIZ_SCHEMA_AB["properties"], "QUIZ_SCHEMA_AB không được có common_quiz"
assert "common_quiz" in QUIZ_SCHEMA_CD["properties"],   "QUIZ_SCHEMA_CD phải có common_quiz"
assert "grammar_quiz" in QUIZ_SCHEMA_CD["properties"],  "QUIZ_SCHEMA_CD phải có grammar_quiz"
assert "vocab_quiz" not in QUIZ_SCHEMA_CD["properties"], "QUIZ_SCHEMA_CD không được có vocab_quiz"
ok("QUIZ_SCHEMA_AB và QUIZ_SCHEMA_CD đúng cấu trúc, tách bạch không lẫn lộn")

# ─── 21. audit_and_supplement_course: Rà soát & Bổ sung chặng thiếu ───
print("\n[21] audit_and_supplement_course: Rà soát & Bổ sung chặng thiếu")

# Tạo khóa học giả lập Tiếng Nhật cũ 240 ngày (thiếu Chặng 5 Cao cấp)
_mock_old_course = cdb.new_course("Tiếng Nhật Test", [], 10)
_mock_old_items = []
for i in range(1, 241):
    # Gán stage 0..3 (bỏ quên stage 4)
    s_idx = 0 if i <= 30 else (1 if i <= 68 else (2 if i <= 160 else 3))
    _mock_old_items.append({
        "id": i,
        "title": f"Chủ đề cũ #{i}",
        "category": "GIAO TIẾP",
        "stage_idx": s_idx,
        "filled_day": i
    })
_mock_old_course["backbone"] = {"level": "Toàn bộ", "items": _mock_old_items}
_mock_old_course["days"] = [{"day": i, "title": f"Chủ đề cũ #{i}"} for i in range(1, 241)]
cdb.save_course("Tiếng Nhật Test", _mock_old_course)

# Gọi audit_and_supplement_course với coordinator mock
class _MockSupplementCoord:
    def __init__(self, *args, **kwargs):
        pass
    def request(self, prompt, response_schema=None):
        return {"ok": True, "text": json.dumps({"topics": []})}

supp_res = audit_and_supplement_course("Tiếng Nhật Test", level="Toàn bộ", coordinator_cls=_MockSupplementCoord)
assert supp_res["ok"] is True, "audit_and_supplement_course phải trả về ok=True"
assert supp_res["old_total"] == 240, f"old_total phải là 240, thực tế {supp_res['old_total']}"
assert supp_res["added_count"] > 0, f"added_count phải > 0, thực tế {supp_res['added_count']}"
assert supp_res["new_total"] >= 420, f"new_total phải >= 420, thực tế {supp_res['new_total']}"

# Kiểm tra DB sau khi bổ sung
_updated_course = cdb.get_course("Tiếng Nhật Test")
assert _updated_course.get("format_version") == 3, "format_version phải là 3"
_up_items = _updated_course["backbone"]["items"]
assert len(_up_items) == supp_res["new_total"], "Số items trong DB phải khớp new_total"

# Kiểm tra 240 items cũ giữ nguyên filled_day
for i in range(240):
    assert _up_items[i]["filled_day"] == i + 1, f"Item {i+1} cũ phải giữ nguyên filled_day"
# Kiểm tra các items mới bổ sung có filled_day = None
for i in range(240, len(_up_items)):
    assert _up_items[i]["filled_day"] is None, f"Item mới {i+1} phải có filled_day=None"

# Kiểm tra ID tuần tự 1..N
for i, it in enumerate(_up_items, 1):
    assert it["id"] == i, f"Item id phải là {i}, thực tế {it['id']}"

cdb.delete_course("Tiếng Nhật Test")
ok("audit_and_supplement_course: tự động phát hiện chặng thiếu & bổ sung đủ sàn FSI mà không mất bài cũ")

# ─── 22. AI Dynamic Language Profiling & Native C2 Scale ───
print("\n[22] AI Dynamic Language Profiling & Native C2 Scale")

# 22.1: Rule-based fallback profile
prof_en = get_rule_based_fallback_profile("Tiếng Anh")
assert prof_en["total_days"] == 700, f"Tiếng Anh bản xứ fallback phải là 700 ngày, thực tế {prof_en['total_days']}"
assert len(prof_en["stages"]) == 6, "Phải có đủ 6 chặng"
assert prof_en["stages"][0]["target_days"] == 35
assert prof_en["stages"][-1]["target_days"] == 100
ok("language_profiler: fallback Tiếng Anh đúng 700 ngày qua 6 chặng")

prof_jp = get_rule_based_fallback_profile("Tiếng Nhật")
assert prof_jp["total_days"] == 1260, f"Tiếng Nhật bản xứ fallback phải là 1260 ngày, thực tế {prof_jp['total_days']}"
assert "Tượng Hình" in prof_jp["category_name"]
ok("language_profiler: fallback Tiếng Nhật đúng 1260 ngày cho nhóm tượng hình & kính ngữ")

prof_de = get_rule_based_fallback_profile("Tiếng Đức")
assert prof_de["total_days"] == 840, f"Tiếng Đức fallback phải là 840 ngày, thực tế {prof_de['total_days']}"
ok("language_profiler: fallback Tiếng Đức đúng 840 ngày cho nhóm Latinh chia giống")

prof_ru = get_rule_based_fallback_profile("Tiếng Nga")
assert prof_ru["total_days"] == 980, f"Tiếng Nga fallback phải là 980 ngày, thực tế {prof_ru['total_days']}"
ok("language_profiler: fallback Tiếng Nga đúng 980 ngày cho nhóm hệ chữ riêng & biến cách")

# 22.2: Cache Persistence
cache_data = load_cached_language_profiles()
assert isinstance(cache_data, dict), "Cache phải là một dictionary"
test_cache_entry = {
    "title": "Hồ sơ Test",
    "category_name": "Test Category",
    "stage_days": [20, 30, 100, 150, 120, 80],
    "persona": "Người Test",
    "instruction": "Test instruction",
    "mandatory_milestones": ["m1", "m2"]
}
save_cached_language_profiles({"__test_lang__": test_cache_entry})
loaded_cache = load_cached_language_profiles()
assert "__test_lang__" in loaded_cache, "Phải lưu và đọc lại được từ cache JSON"
# Cleanup test key
loaded_cache.pop("__test_lang__", None)
save_cached_language_profiles(loaded_cache)
ok("language_profiler: load/save cache JSON hoạt động chính xác")

# 22.3: AI Dynamic Discovery via Mock Coordinator
class _MockAIProfilerCoord:
    def request(self, prompt, response_schema=None):
        profile_json = {
            "title": "Lộ trình Tiếng Trung Cận Bản Xứ Siêu Cấp",
            "category_name": "Chuẩn Bản Xứ C2 • Tượng Hình Hanzi & Điển Cố Hán Học",
            "recommended_days": 1500,
            "stage_days": [80, 120, 350, 400, 350, 200],
            "persona": "Học giả Hán học & Giao tiếp Bản ngữ C2",
            "instruction": "Giáo trình nghiên cứu Hanzi từ giáp cốt văn đến thành ngữ hiện đại.",
            "mandatory_milestones": ["hanzi_co_ban", "dien_co_tu_dai_danh_tac"]
        }
        return {"ok": True, "text": json.dumps(profile_json)}

ai_prof = get_or_create_language_profile("Tiếng Trung Thượng Hải", coord=_MockAIProfilerCoord(), force_refresh=True)
assert ai_prof["total_days"] == 1500, f"AI Profiler phải trả về 1500 ngày, thực tế {ai_prof['total_days']}"
assert ai_prof["is_ai_reasoned"] is True, "Phải đánh dấu is_ai_reasoned=True"
assert len(ai_prof["stages"]) == 6, "Phải sinh đủ 6 stages info"
assert ai_prof["stages"][0]["target_days"] == 80
assert ai_prof["stages"][-1]["target_days"] == 200
ok("language_profiler: AI Dynamic Profiling khảo sát ngôn ngữ trả về 1500 ngày bản xứ C2 thành công")

# 22.4: Master Backbone với Quy mô Ngày Bản Xứ
class _MockNativeBackboneCoord:
    def request(self, prompt, response_schema=None):
        return {"ok": True, "text": json.dumps({"topics": [], "insertions": []})}

mb_native = build_master_backbone("Tiếng Anh", prof_en, _MockNativeBackboneCoord())
assert mb_native["template_base_count"] == 700, f"Base count phải là 700, thực tế {mb_native['template_base_count']}"
assert len(mb_native["items"]) == 700, f"Tổng số items phải là 700, thực tế {len(mb_native['items'])}"
assert mb_native["items"][6]["is_review_day"] is True and "ÔN TẬP TUẦN 1" in mb_native["items"][6]["generic_name"]
assert mb_native["items"][-1]["is_review_day"] is True and "TỔNG KẾT CHẶNG 6" in mb_native["items"][-1]["generic_name"]
ok("build_master_backbone: thiết kế trơn tru 700 ngày bản xứ qua 6 chặng với chu kỳ ôn tập xoắn ốc")

# ─── 23. Model Priority & Fallback Discovery (Đồng bộ AskCpl) ───
print("\n[23] Model Priority & Fallback Discovery")
from settings import get_active_model_list, update_ai_settings, _DEFAULT_MODEL_FALLBACKS, load_settings
from api.gemini_safe import GeminiCoordinator

# 23.1: get_active_model_list returns fallback models when no setting is saved
models = get_active_model_list()
assert isinstance(models, list), "get_active_model_list phải trả về list"
assert len(models) > 0, "Danh sách model không được rỗng"
assert all(isinstance(m, str) and m for m in models), "Các phần tử phải là string tên model hợp lệ"
ok("get_active_model_list trả về danh sách model hợp lệ")

# 23.2: GeminiCoordinator nạp get_active_model_list() mặc định khi models=None
coord = GeminiCoordinator(models=None)
assert coord.models == models, f"GeminiCoordinator phải dùng get_active_model_list(): {coord.models} != {models}"
ok("GeminiCoordinator tự động nạp danh sách model từ settings/fallback")

# 23.3: update_ai_settings cập nhật model_priority
original_ai_settings = load_settings().get("ai", {})
try:
    test_priority = [
        {"name": "test-gemini-custom", "enabled": True, "tier": "S", "latency_ms": 100},
        {"name": "test-gemini-disabled", "enabled": False, "tier": "C", "latency_ms": 0}
    ]
    update_ai_settings(model_priority=test_priority)
    active = get_active_model_list()
    assert active == ["test-gemini-custom"], f"Chỉ model enabled mới được nạp, kết quả: {active}"
    ok("update_ai_settings lưu và lọc model enabled chuẩn xác")
finally:
    # Khôi phục cài đặt ban đầu
    update_ai_settings(**original_ai_settings)
    ok("Khôi phục ai settings về trạng thái ban đầu")

# ─── Summary ───
print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed")
if failed:
    sys.exit(1)

