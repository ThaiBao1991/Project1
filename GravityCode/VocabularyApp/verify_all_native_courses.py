"""verify_all_native_courses.py — Script kiểm thử tự động đa tầng & vòng lặp stress test
Kiểm tra toàn diện tất cả các khía cạnh của AI Dynamic Language Profiling và VocabularyApp:
1. Syntax & Import của mọi module
2. Hồ sơ Bản xứ C2 cho 12+ ngôn ngữ toàn cầu
3. Kiểm tra tính toàn vẹn của Cache JSON
4. Kiểm tra sinh Master Backbone quy mô lớn (700 - 1500 ngày)
5. Kiểm tra tính năng Rà soát & Bổ sung (Audit & Supplement)
6. Kiểm tra giao diện headless (Tkinter widget không bị crash)
7. Chạy trọn vẹn test_ai_rich.py
"""

import sys
import os
import json
import time
import tempfile
import shutil

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

passed = 0
failed = 0

def ok(name):
    global passed
    passed += 1
    print(f"  [PASS] {name}")

def fail(name, msg=""):
    global failed
    failed += 1
    print(f"  [FAIL] {name}: {msg}")

print("=" * 60)
print("BẮT ĐẦU VÒNG LẶP KIỂM TRA TOÀN DIỆN HỆ THỐNG")
print("=" * 60)

# ─── VÒNG 1: SYNTAX & COMPILATION CHECK ───
print("\n[VÒNG 1] Kiểm tra cú pháp và import toàn bộ các file...")
modules_to_check = [
    "settings",
    "database.database",
    "ai.course_db",
    "ai.language_profiler",
    "ai.course_generator",
    "api.gemini_safe",
    "VocabApp",
]

for mod in modules_to_check:
    try:
        __import__(mod)
        ok(f"Module '{mod}' import & compile thành công")
    except Exception as e:
        fail(f"Module '{mod}' lỗi import/compile", str(e))

# ─── VÒNG 2: KIỂM TRA 12+ NGÔN NGỮ TOÀN CẦU ───
print("\n[VÒNG 2] Kiểm tra AI Profiler cho 12+ ngôn ngữ lớn trên thế giới...")
from ai.language_profiler import get_or_create_language_profile, get_rule_based_fallback_profile

test_languages = [
    ("Tiếng Anh", 700, 700),
    ("Tiếng Nhật", 1260, 1260),
    ("Tiếng Trung (Mandarin)", 1260, 1260),
    ("Tiếng Hàn (Hangul)", 1260, 1260),
    ("Tiếng Đức", 840, 840),
    ("Tiếng Pháp", 840, 840),
    ("Tiếng Tây Ban Nha", 840, 840),
    ("Tiếng Ý", 840, 840),
    ("Tiếng Nga", 980, 980),
    ("Tiếng Thái", 980, 980),
    ("Tiếng Ả Rập", 1260, 1260),
    ("Tiếng Ba Lan", 980, 980),
]

for lang_name, min_expected, max_expected in test_languages:
    try:
        prof = get_rule_based_fallback_profile(lang_name)
        assert prof["total_days"] == sum(prof["stage_days"]), f"Tổng ngày không khớp tổng stage_days: {prof['total_days']} vs {sum(prof['stage_days'])}"
        assert min_expected <= prof["total_days"] <= max_expected, f"Số ngày {prof['total_days']} không nằm trong khoảng [{min_expected}, {max_expected}]"
        assert len(prof["stages"]) == 6, f"Phải có đúng 6 chặng, thực tế {len(prof['stages'])}"
        assert prof.get("persona"), "Phải có persona"
        assert prof.get("instruction"), "Phải có instruction"
        ok(f"{lang_name}: {prof['total_days']} ngày Bản xứ C2 — 6 Chặng chuẩn ({prof['category_name'][:35]}...)")
    except Exception as e:
        fail(f"Lỗi kiểm tra ngôn ngữ '{lang_name}'", str(e))

# ─── VÒNG 3: KIỂM TRA CACHE JSON VÀ TÍNH NHẤT QUÁN ───
print("\n[VÒNG 3] Kiểm tra Cache JSON và tính nhất quán...")
from ai.language_profiler import load_cached_language_profiles, save_cached_language_profiles

try:
    cache = load_cached_language_profiles()
    assert isinstance(cache, dict)
    ok(f"Nạp cache thành công, hiện có {len(cache)} ngôn ngữ đã lưu")
    
    # Test lưu và đọc lại
    dummy_key = "__stress_test_lang__"
    cache[dummy_key] = {
        "title": "Stress Test Language",
        "category_name": "Test Category",
        "stage_days": [50, 70, 200, 250, 230, 150],
        "persona": "Tester",
        "instruction": "Do nothing",
        "mandatory_milestones": ["test_m1"]
    }
    save_cached_language_profiles(cache)
    
    reloaded = load_cached_language_profiles()
    assert dummy_key in reloaded
    cached_prof = get_or_create_language_profile(dummy_key)
    assert cached_prof["total_days"] == 950
    assert len(cached_prof["stages"]) == 6
    
    # Dọn dẹp key test
    reloaded.pop(dummy_key, None)
    save_cached_language_profiles(reloaded)
    assert dummy_key not in load_cached_language_profiles()
    ok("Cache read/write/delete và get_or_create_language_profile với cache hoạt động hoàn hảo")
except Exception as e:
    fail("Lỗi kiểm tra Cache", str(e))

# ─── VÒNG 4: STRESS TEST MASTER BACKBONE QUY MÔ LỚN ───
print("\n[VÒNG 4] Stress test Master Backbone quy mô lớn (700 ngày & 1260 ngày)...")
from ai.course_generator import build_master_backbone, build_stage_universal_template

class _MockFastCoord:
    def __init__(self, *args, **kwargs):
        pass

    def request(self, prompt, response_schema=None):
        return {"ok": True, "text": json.dumps({"topics": [], "insertions": []})}

try:
    # Test 700 ngày (Tiếng Anh)
    prof_en = get_rule_based_fallback_profile("Tiếng Anh")
    mb_en = build_master_backbone("Tiếng Anh", prof_en, _MockFastCoord())
    assert len(mb_en["items"]) == 700, f"Mong đợi 700 items, thực tế {len(mb_en['items'])}"
    for idx, item in enumerate(mb_en["items"], 1):
        assert item["id"] == idx, f"ID không tuần tự tại vị trí {idx}"
    assert mb_en["items"][6]["is_review_day"] is True, "Ngày 7 (slot 7 Chặng 1) phải là review day"
    assert mb_en["items"][-1]["is_review_day"] is True, "Ngày cuối cùng phải là Tổng kết chặng"
    ok("Master Backbone 700 ngày: Sinh thành công 100%, ID tuần tự, ôn tập xoắn ốc đúng chuẩn")

    # Test 1260 ngày (Tiếng Nhật)
    prof_jp = get_rule_based_fallback_profile("Tiếng Nhật")
    mb_jp = build_master_backbone("Tiếng Nhật", prof_jp, _MockFastCoord())
    assert len(mb_jp["items"]) == 1260, f"Mong đợi 1260 items, thực tế {len(mb_jp['items'])}"
    assert mb_jp["items"][0]["id"] == 1
    assert mb_jp["items"][-1]["id"] == 1260
    assert mb_jp["items"][-1]["is_review_day"] is True
    ok("Master Backbone 1260 ngày: Sinh thành công 100%, 6 Chặng khép kín hoàn chỉnh")
except Exception as e:
    import traceback
    traceback.print_exc()
    fail("Lỗi stress test Master Backbone", str(e))

# ─── VÒNG 5: KIỂM TRA AUDIT & SUPPLEMENT NÂNG CẤP KHÓA CŨ ───
print("\n[VÒNG 5] Kiểm tra Audit & Supplement nâng cấp khóa cũ...")
from ai.course_generator import audit_and_supplement_course
from ai import course_db as cdb

tmp_course_dir = tempfile.mkdtemp()
orig_course_dir = cdb.COURSES_DIR
try:
    cdb.COURSES_DIR = tmp_course_dir
    # Tạo khóa Tiếng Anh cũ 240 ngày phân bổ theo chuẩn FSI cũ (17, 22, 53, 60, 55, 33)
    from ai.course_generator import get_language_fsi_profile
    fsi_old_en = get_language_fsi_profile("Tiếng Anh")
    c_old = cdb.new_course("TestEnglishOld", [], 10)
    old_items = []
    d_counter = 1
    for s_idx, st in enumerate(fsi_old_en["stages"]):
        for _ in range(st["target_days"]):
            old_items.append({
                "id": d_counter,
                "title": f"Bài cũ #{d_counter}",
                "stage_idx": s_idx,
                "filled_day": d_counter
            })
            d_counter += 1
    c_old["backbone"] = {"level": "⭐ Trọn gói", "items": old_items}
    c_old["days"] = [{"day": i, "title": f"Bài cũ #{i}"} for i in range(1, 241)]
    cdb.save_course("TestEnglishOld", c_old)

    res_audit = audit_and_supplement_course("TestEnglishOld", level="⭐ Trọn gói", coordinator_cls=_MockFastCoord)
    assert res_audit["ok"] is True
    assert res_audit["old_total"] == 240
    assert res_audit["new_total"] == 700, f"new_total phải là 700 ngày bản xứ, thực tế {res_audit['new_total']}"
    assert res_audit["added_count"] == 460, f"Phải bổ sung thêm +460 ngày, thực tế {res_audit['added_count']}"

    c_up = cdb.get_course("TestEnglishOld")
    items_up = c_up["backbone"]["items"]
    assert len(items_up) == 700
    # 240 ngày đầu phải giữ nguyên filled_day
    for i in range(240):
        assert items_up[i]["filled_day"] == i + 1
    # 460 ngày sau phải có filled_day = None
    for i in range(240, 700):
        assert items_up[i]["filled_day"] is None
    ok("Audit & Supplement: Nâng cấp khóa Tiếng Anh cũ 240 ngày lên 700 ngày bản xứ thành công 100%")
except Exception as e:
    import traceback
    traceback.print_exc()
    fail("Lỗi Audit & Supplement", str(e))
finally:
    cdb.COURSES_DIR = orig_course_dir
    shutil.rmtree(tmp_course_dir, ignore_errors=True)

# ─── VÒNG 6: KIỂM TRA GIAO DIỆN (WIDGET INTEGRITY) ───
print("\n[VÒNG 6] Kiểm tra giao diện và cấu trúc widget trong VocabApp...")
try:
    from VocabApp import CourseGenerationDialog, _short_level_name
    # Kiểm tra map level sang badge chặng
    assert _short_level_name("", "Vỡ lòng chữ cái & phát âm") == "Vỡ lòng"
    assert _short_level_name("", "Như người bản xứ") == "Bản xứ"
    ok("_short_level_name: nhận diện chính xác huy hiệu chặng")
    
    # Kiểm tra các tùy chọn trong CourseGenerationDialog DURATION_OPTIONS
    # Dùng inspection trên class hoặc code
    import inspect
    src = inspect.getsource(CourseGenerationDialog.__init__)
    assert "Tự động (AI suy luận số ngày chuẩn Bản xứ C2)" in src
    ok("CourseGenerationDialog: Tùy chọn 'Tự động (AI suy luận số ngày chuẩn Bản xứ C2)' đã xuất hiện trong UI")
except Exception as e:
    fail("Lỗi kiểm tra giao diện", str(e))

# ─── VÒNG 7: CHẠY TRỌN VẸN TEST_AI_RICH.PY ───
print("\n[VÒNG 7] Chạy toàn bộ 63 bài kiểm thử test_ai_rich.py...")
import subprocess
ret = subprocess.run([sys.executable, os.path.join(BASE_DIR, "test_ai_rich.py")], capture_output=True, text=True, encoding="utf-8")
if ret.returncode == 0 and "Results: 63 passed, 0 failed" in ret.stdout:
    ok("test_ai_rich.py: Toàn bộ 63/63 bài kiểm thử chạy thành công 100%")
else:
    fail("test_ai_rich.py thất bại", ret.stderr or ret.stdout)

# ─── TỔNG KẾT ───
print("\n" + "=" * 60)
print(f"KẾT QUẢ CUỐI CÙNG: {passed} PASSED, {failed} FAILED")
print("=" * 60)

if failed > 0:
    sys.exit(1)
sys.exit(0)
