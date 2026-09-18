import unittest


class RoadmapAutoFixTests(unittest.TestCase):
    def test_topic_id_auto_deduplication(self):
        """Simulate PASS 1B validation logic for duplicate topic_ids."""
        known = {"chuyen_gia_cau_truc_ban_com_tam_sai_gon"}
        start_day = 195
        generated = [
            {
                "day": 195,
                "topic_id": "chuyen_gia_cau_truc_ban_com_tam_sai_gon",
                "topic": "Đỉnh cao dàn dựng bố cục nội dung bản cơm tấm sài gòn chiến lược",
                "prerequisites": ["chuyen_gia_cau_truc_ban_com_tam_sai_gon"]
            }
        ]

        logs = []
        for item in generated:
            _dnum = item.get("day", start_day)
            _raw_tid = (item.get("topic_id") or "").strip()
            if not _raw_tid:
                _raw_tid = f"topic_d{_dnum}"
            if _raw_tid in known:
                _new_tid = f"{_raw_tid}_d{_dnum}"
                logs.append(f"Day {_dnum}: duplicate topic_id -> auto renamed to {_new_tid}")
                _raw_tid = _new_tid
            item["topic_id"] = _raw_tid

            prerequisites = item.get("prerequisites", [])
            if isinstance(prerequisites, list):
                clean_prereqs = [p for p in prerequisites if p in known and p != _raw_tid]
                item["prerequisites"] = clean_prereqs
            else:
                item["prerequisites"] = []
            known.add(item["topic_id"])

        self.assertEqual(generated[0]["topic_id"], "chuyen_gia_cau_truc_ban_com_tam_sai_gon_d195")
        self.assertIn("chuyen_gia_cau_truc_ban_com_tam_sai_gon", generated[0]["prerequisites"])
        self.assertNotIn("chuyen_gia_cau_truc_ban_com_tam_sai_gon_d195", generated[0]["prerequisites"])
        self.assertTrue(len(logs) > 0)
        self.assertIn("chuyen_gia_cau_truc_ban_com_tam_sai_gon_d195", known)

    def test_reconcile_phase_days_scale_up_exact_match(self):
        """Mô phỏng trường hợp PowerPoint: AI sinh 12 phase tổng 960 Day nhưng target yêu cầu 1000 Day."""
        from AskCpl import reconcile_phase_days
        phases = [{"id": f"phase_{i}", "name": f"Module {i}", "days": 80} for i in range(1, 13)] # 12 * 80 = 960
        target = 1000
        ok = reconcile_phase_days(phases, target)
        self.assertTrue(ok)
        self.assertEqual(sum(p["days"] for p in phases), 1000)
        self.assertTrue(all(5 <= p["days"] <= 500 for p in phases))

    def test_reconcile_phase_days_scale_down_exact_match(self):
        """Mô phỏng AI sinh vượt quá số ngày target (ví dụ 1200 Day -> 1000 Day)."""
        from AskCpl import reconcile_phase_days
        phases = [{"id": f"phase_{i}", "name": f"Module {i}", "days": 100} for i in range(1, 13)] # 12 * 100 = 1200
        target = 1000
        ok = reconcile_phase_days(phases, target)
        self.assertTrue(ok)
        self.assertEqual(sum(p["days"] for p in phases), 1000)
        self.assertTrue(all(5 <= p["days"] <= 500 for p in phases))

    def test_reconcile_phase_days_cleans_strings_and_missing_keys(self):
        """Mô phỏng phase có days dạng string, thiếu id, thiếu name."""
        from AskCpl import reconcile_phase_days
        phases = [
            {"name": "Giai đoạn đầu", "days": "75"},
            {"id": "p2", "days": "invalid_number"},
            {"id": "p3", "name": "Thực chiến", "days": 3}  # < 5
        ]
        target = 300
        ok = reconcile_phase_days(phases, target)
        self.assertTrue(ok)
        self.assertEqual(sum(p["days"] for p in phases), 300)
        self.assertTrue(all(5 <= p["days"] <= 500 for p in phases))
        self.assertTrue(all(p.get("id") and p.get("name") for p in phases))

    def test_branching_quiz_all_inclusive_option(self):
        """Kiểm tra logic thêm option toàn diện và format kết quả khi chọn tất cả."""
        raw_options = [
            "Chuyên gia Thiết kế & R&D",
            "Chuyên gia Công nghệ & Gia công CNC",
            "Chuyên gia Tự động hóa & Robot",
            "Chuyên gia Quản lý sản xuất"
        ]
        all_inclusive_text = "🌟 Toàn bộ các định hướng trên (Tích hợp đa năng: Làm chủ toàn diện tất cả các nhánh từ cơ bản đến Master)"
        
        # Test 1: Đảm bảo option toàn diện được thêm vào cuối
        options = [o for o in raw_options if not o.startswith("🌟 Toàn bộ")]
        options.append(all_inclusive_text)
        self.assertEqual(options[-1], all_inclusive_text)
        self.assertEqual(len(options), 5)
        
        # Test 2: Khi chọn option toàn diện, chuỗi sinh ra phải liệt kê trọn vẹn tất cả các nhánh con
        clean_opts = [o for o in raw_options if o != all_inclusive_text]
        formatted = "Học toàn diện và làm chủ 100% tất cả các nhánh: " + "; ".join(clean_opts)
        self.assertIn("Thiết kế & R&D", formatted)
        self.assertIn("Gia công CNC", formatted)
        self.assertIn("Tự động hóa & Robot", formatted)
        self.assertIn("Quản lý sản xuất", formatted)

    def test_render_markdown_auto_heals_missing_exercises_and_tags(self):
        """Kiểm tra render_markdown tự động bù đắp exercises hoặc tags bị rỗng/None mà không crash."""
        from roadmap_pipeline import render_markdown
        plan = {
            "domain_profile": {"title": "Mechanical Engineering Mastery"},
            "skeleton": [
                {
                    "day": 1,
                    "topic": "Tổng quan Cơ khí và Tiêu chuẩn bản vẽ",
                    "keywords": ["cơ_khí", "bản_vẽ", "tiêu_chuẩn"],
                    "source_files": []
                },
                {
                    "day": 2,
                    "topic": "Vật liệu kim loại & Nhiệt luyện",
                    "keywords": ["vật_liệu", "thép", "nhiệt_luyện"],
                    "source_files": []
                }
            ]
        }
        # Day 1 thiếu exercises (None) và tags (empty list)
        # Day 2 thiếu tags (None) và exercises rỗng
        lessons = [
            {
                "day": 1,
                "prompt": "Hướng dẫn chi tiết về đọc bản vẽ cơ khí và tiêu chuẩn ISO.",
                "exercises": None,
                "tags": []
            },
            {
                "day": 2,
                "prompt": "Hướng dẫn chi tiết về các mác thép và xử lý nhiệt luyện.",
                "exercises": [],
                "tags": None
            }
        ]
        md = render_markdown(plan, lessons)
        self.assertIn("## Day 1 — Tổng quan Cơ khí và Tiêu chuẩn bản vẽ", md)
        self.assertIn("**Bài tập:**\n- Thực hành chi tiết: Tổng quan Cơ khí và Tiêu chuẩn bản vẽ", md)
        self.assertIn("**Tags:**\n#roadmap #day1 #cơ_khí #bản_vẽ #tiêu_chuẩn", md)
        self.assertIn("## Day 2 — Vật liệu kim loại & Nhiệt luyện", md)
        self.assertIn("**Bài tập:**\n- Thực hành chi tiết: Vật liệu kim loại & Nhiệt luyện", md)
        self.assertIn("**Tags:**\n#roadmap #day2 #vật_liệu #thép #nhiệt_luyện", md)

    def test_load_json_response_auto_repairs_latex_invalid_escapes(self):
        """Kiểm tra load_json_response tự động sửa các lỗi Invalid escape do công thức LaTeX."""
        from roadmap_pipeline import load_json_response
        raw_llm_output = r'''```json
[
  {
    "day": 1196,
    "prompt": "Tính thuật toán PID: $$u(t) = K_p e(t) + K_i \int e(t)dt + K_d \frac{de(t)}{dt}$$. Áp lực $\sigma = \frac{F}{A}$, độ biến dạng $\Delta L = \alpha L \Delta T$, nhiệt độ $100^\circ\text{C}$, đơn vị $\unit{mm}$ và $\times$ 10.",
    "exercises": ["Thực hành lập trình ESP32 PID"],
    "tags": ["#esp32", "#pid"]
  }
]
```'''
        parsed = load_json_response(raw_llm_output)
        self.assertIsInstance(parsed, list)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["day"], 1196)
        self.assertIn(r"\frac", parsed[0]["prompt"])
        self.assertIn(r"\int", parsed[0]["prompt"])
        self.assertIn(r"\sigma", parsed[0]["prompt"])


if __name__ == "__main__":
    unittest.main()
