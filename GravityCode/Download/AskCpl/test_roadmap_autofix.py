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


if __name__ == "__main__":
    unittest.main()
