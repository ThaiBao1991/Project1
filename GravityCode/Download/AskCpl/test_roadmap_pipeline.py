import unittest
import re
from pathlib import Path
from tempfile import TemporaryDirectory

from roadmap_pipeline import (
    RoadmapValidationError,
    atomic_write,
    load_json_response,
    render_markdown,
    restore_locked_day_identity,
    validate_plan,
    validate_revision,
    verify_markdown,
)


def plan(days=3):
    skeleton = []
    for day in range(1, days + 1):
        skeleton.append({
            "day": day,
            "topic_id": f"topic_{day}",
            "topic": f"Chủ đề khác biệt {day}",
            "phase": "Nền tảng" if day < days else "Dự án",
            "kind": "capstone" if day == days else "lesson",
            "details": [f"Nội dung {day}"],
            "keywords": [f"keyword-{day}"],
            "prerequisites": [] if day == 1 else [f"topic_{day - 1}"],
        })
    return {"domain_profile": {"title": "Kiểm thử"}, "skeleton": skeleton}


def micro_plan(days=3):
    data = plan(days)
    for item in data["skeleton"]:
        item.update({
            "estimated_minutes": 30,
            "concrete_project": f"Mô hình cụ thể {item['day']}",
            "materials": ["Bìa carton 1 tấm"],
            "definition_of_done": ["Chụp ảnh sản phẩm đã hoàn thiện"],
        })
    return data


class RoadmapPipelineTests(unittest.TestCase):
    def test_valid_plan_and_markdown(self):
        data = plan()
        validate_plan(data, 3)
        lessons = [
            {"day": day, "prompt": f"Luôn trả lời bằng tiếng Việt. Day {day}.", "exercises": ["Thực hành"], "tags": ["#test"]}
            for day in range(1, 4)
        ]
        output = render_markdown(data, lessons)
        verify_markdown(output, 3)

    def test_rejects_duplicate_or_missing_days(self):
        data = plan()
        data["skeleton"][2]["day"] = 2
        with self.assertRaisesRegex(RoadmapValidationError, "trùng"):
            validate_plan(data, 3)

    def test_rejects_missing_prerequisite(self):
        data = plan()
        data["skeleton"][1]["prerequisites"] = ["does_not_exist"]
        with self.assertRaisesRegex(RoadmapValidationError, "prerequisite"):
            validate_plan(data, 3)

    def test_rejects_future_prerequisite(self):
        data = plan()
        data["skeleton"][0]["prerequisites"] = ["topic_2"]
        with self.assertRaisesRegex(RoadmapValidationError, "học trước"):
            validate_plan(data, 3)

    def test_rejects_near_duplicate_topic(self):
        data = plan()
        data["skeleton"][1]["topic"] = data["skeleton"][0]["topic"]
        with self.assertRaisesRegex(RoadmapValidationError, "trùng nội dung"):
            validate_plan(data, 3)

    def test_rejects_revision_that_deletes_old_topic(self):
        old, new = plan(), plan()
        new["skeleton"][1]["topic_id"] = "new_topic"
        with self.assertRaisesRegex(RoadmapValidationError, "mất topic"):
            validate_revision(old, new, 3)

    def test_rejects_invalid_markdown_sections(self):
        markdown = "## Day 1 — A\n**Prompt:**\nx\n"
        with self.assertRaises(RoadmapValidationError):
            verify_markdown(markdown, 1)

    def test_rejects_multiphase_plan_without_capstone(self):
        data = plan()
        data["skeleton"][-1]["kind"] = "lesson"
        with self.assertRaisesRegex(RoadmapValidationError, "capstone"):
            validate_plan(data, 3)

    def test_rejects_mojibake_output(self):
        markdown = "## Day 1 — A\n**Prompt:**\nÃƒ\n\n**Bài tập:**\n- x\n\n**Tags:**\n#x\n"
        with self.assertRaisesRegex(RoadmapValidationError, "encoding"):
            verify_markdown(markdown, 1)

    def test_micro_day_requires_30_minute_budget_and_deliverable(self):
        data = micro_plan()
        validate_plan(data, 3, require_micro=True)
        data["skeleton"][0]["estimated_minutes"] = 45
        with self.assertRaisesRegex(RoadmapValidationError, "estimated_minutes"):
            validate_plan(data, 3, require_micro=True)

    def test_micro_day_rejects_vague_deliverable(self):
        data = micro_plan()
        data["skeleton"][0]["concrete_project"] = "Tìm hiểu về đồ chơi"
        with self.assertRaisesRegex(RoadmapValidationError, "chung chung"):
            validate_plan(data, 3, require_micro=True)

    def test_loader_pattern_ignores_day_heading_inside_prompt(self):
        markdown = "## Day 1 — Hợp lệ\n**Prompt:**\nKhông tạo ## Day 2: heading giả.\n\n## Day 2 — Hợp lệ\n"
        parts = re.split(r'\n## (Day \d+[a-z]?\s+—\s+[^\n]+)\n', "\n" + markdown)
        self.assertEqual(parts[1::2], ["Day 1 — Hợp lệ", "Day 2 — Hợp lệ"])

    def test_json_loader_handles_prefix_and_conservative_trailing_comma(self):
        self.assertEqual(load_json_response("Đây là JSON: {\"ok\": true,}"), {"ok": True})

    def test_json_loader_rejects_truncated_answer(self):
        with self.assertRaises(RoadmapValidationError):
            load_json_response('[{\"day\": 353, \"topic_id\": \"dang_do')

    def test_revision_restores_locked_topic_ids_and_sources(self):
        existing = [
            {"day": 1, "topic_id": "nam_cam", "source_files": ["tai_lieu.pdf"]},
            {"day": 2, "topic_id": "banh_xe", "source_files": []},
        ]
        revised, changes = restore_locked_day_identity(existing, [
            {"day": 1, "topic_id": "nam_cham", "topic": "Đã sửa nội dung"},
            {"day": 2, "topic_id": "banh_xe", "topic": "Đã sửa nội dung"},
        ])
        self.assertEqual(revised[0]["topic_id"], "nam_cam")
        self.assertEqual(revised[0]["source_files"], ["tai_lieu.pdf"])
        self.assertEqual(changes, [(1, "nam_cham", "nam_cam")])

    def test_atomic_write_preserves_previous_file_on_failure(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "roadmap.md"
            atomic_write(path, "bản cũ")
            self.assertEqual(path.read_text(encoding="utf-8"), "bản cũ")
            atomic_write(path, "bản mới")
    def test_tech_tree_domain_detection(self):
        from domain_profiles import instruction_for, is_tech_tree_domain
        self.assertTrue(is_tech_tree_domain("Thiên công khai vật & Khôi phục văn minh từ số 0"))
        self.assertTrue(is_tech_tree_domain("Reboot civilization tech tree"))
        self.assertFalse(is_tech_tree_domain("Học lập trình Python cơ bản"))
        
        rule = instruction_for("Thiên công khai vật")
        self.assertIn("PROFILE TECH TREE", rule)
        self.assertIn("Đồ đá", rule)
        self.assertIn("Silic", rule)

    def test_generated_civilization_roadmap_integrity(self):
        roadmap_path = Path(__file__).parent / "roadmap_thien_cong_khai_vat.md"
        self.assertTrue(roadmap_path.exists(), "File roadmap_thien_cong_khai_vat.md phải tồn tại")
        content = roadmap_path.read_text(encoding="utf-8")
        
        # Đếm số ngày
        headings = re.findall(r"(?m)^## Day\s+(\d+)\s+—\s+.+$", content)
        total_days = len(headings)
        self.assertEqual(total_days, 465)
        self.assertEqual([int(h) for h in headings], list(range(1, total_days + 1)))
        
        # Kiểm tra đầy đủ khối
        verify_markdown(content, total_days)
        
        # Kiểm tra nội dung tiếng Việt có dấu
        self.assertIn("LUÔN TRẢ LỜI BẰNG TIẾNG VIỆT", content)
        self.assertIn("Sinh Tồn Chiến Tranh", content)
        self.assertIn("Đồ Đá", content)
        self.assertIn("Thời Kỳ Kim Khí", content)
        self.assertIn("Đo Lường Chuẩn Xác", content)
        self.assertIn("Bán Dẫn", content)
        self.assertIn("Máy Tính", content)

    def test_auto_heal_prerequisites_int_mapping_and_safe_join(self):
        """Simulate PASS 6D prerequisite auto-heal when AI outputs integer Day numbers."""
        revised_days = [
            {"day": 1, "topic_id": "intro_python", "topic": "Nhập môn Python", "prerequisites": []},
            {"day": 2, "topic_id": "vars_types", "topic": "Biến và kiểu dữ liệu", "prerequisites": [1]},
            {"day": 3, "topic_id": "control_flow", "topic": "Cấu trúc rẽ nhánh", "prerequisites": ["2", 999, "invalid_id"]},
        ]
        valid_topic_ids = set(d.get("topic_id", "") for d in revised_days if d.get("topic_id"))
        first_day_map = {d["topic_id"]: d["day"] for d in revised_days if d.get("topic_id")}
        day_to_id_map = {d["day"]: d["topic_id"] for d in revised_days if d.get("day") and d.get("topic_id")}

        prereq_fixed_days = []
        for d in revised_days:
            curr_day = d.get("day", 0)
            curr_id = d.get("topic_id", "")
            prereqs = d.get("prerequisites", [])
            cleaned = []
            removed = []
            for p in prereqs:
                target_id = p
                if isinstance(p, int) or (isinstance(p, str) and p.strip().isdigit()):
                    p_int = int(p)
                    if p_int in day_to_id_map and p_int < curr_day:
                        target_id = day_to_id_map[p_int]

                if (isinstance(target_id, str) and target_id in valid_topic_ids 
                        and target_id != curr_id and first_day_map.get(target_id, 0) < curr_day):
                    if target_id not in cleaned:
                        cleaned.append(target_id)
                else:
                    removed.append(p)

            if cleaned != prereqs:
                d["prerequisites"] = cleaned
                if removed:
                    prereq_fixed_days.append((curr_day, removed))

        self.assertEqual(revised_days[1]["prerequisites"], ["intro_python"])
        self.assertEqual(revised_days[2]["prerequisites"], ["vars_types"])
        log_str = ", ".join(f"Day {day} ({', '.join(map(str, bads))})" for day, bads in prereq_fixed_days)
        self.assertIn("Day 3 (999, invalid_id)", log_str)

    def test_auto_heal_micro_fields(self):
        """Verify normalize_micro_fields clamps minutes and fixes all defective micro fields."""
        from roadmap_pipeline import normalize_micro_fields
        defective_item = {
            "day": 1,
            "topic_id": "topic_1",
            "topic": "Xử lý dữ liệu lớn",
            "phase": "Core",
            "kind": "lesson",
            "details": [],
            "keywords": [],
            "prerequisites": [],
            "estimated_minutes": 45,  # Out of bounds (>30)
            "concrete_project": "tìm hiểu tổng quan về Pandas",  # Starts with vague word
            "materials": [],  # Empty materials
            "definition_of_done": None,  # None definition_of_done
        }
        healed, fixes = normalize_micro_fields(defective_item, 1)
        # Check estimated_minutes clamped to 30
        self.assertEqual(healed["estimated_minutes"], 30)
        # Check vague prefix replaced with 'Thực hành'
        self.assertTrue(healed["concrete_project"].startswith("Thực hành"))
        # Check materials populated
        self.assertTrue(len(healed["materials"]) > 0)
        # Check definition_of_done populated
        self.assertTrue(len(healed["definition_of_done"]) > 0)
        # Check details populated
        self.assertTrue(len(healed["details"]) > 0)

        # Verify it now passes validate_plan with require_micro=True
        test_plan = {
            "domain_profile": {"title": "Test Domain"},
            "skeleton": [healed],
        }
        validate_plan(test_plan, 1, require_micro=True)

        # Verify validate_plan with auto_heal_micro=True heals in-place
        raw_defective = {
            "day": 1,
            "topic_id": "topic_1",
            "topic": "Xử lý dữ liệu lớn",
            "phase": "Core",
            "kind": "lesson",
            "details": ["Chi tiết"],
            "keywords": ["kw"],
            "prerequisites": [],
            "estimated_minutes": 60,
            "concrete_project": "Một dự án hoàn chỉnh",
            "materials": ["Sách"],
            "definition_of_done": ["Xong"],
        }
        test_plan_2 = {"domain_profile": {"title": "Test"}, "skeleton": [raw_defective]}
        validate_plan(test_plan_2, 1, require_micro=True, auto_heal_micro=True)
        self.assertEqual(raw_defective["estimated_minutes"], 30)


if __name__ == "__main__":
    unittest.main()

