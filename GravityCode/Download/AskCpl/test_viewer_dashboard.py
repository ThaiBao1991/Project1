import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from auto_ai_worker import create_viewer


class ViewerDashboardTests(unittest.TestCase):
    def test_index_embeds_a_readable_day_lesson_not_just_menu(self):
        session = [{
            "day": "Day 1 — Chiến thuật mẫu",
            "html": "<h2>Thông số cần nhớ</h2><p>Sát thương cơ bản: 42.</p>",
            "adaptive_lesson": {
                "source_usage": [],
                "clarifying_questions": ["Bạn đang chơi bản nào?"],
                "visual_assets": [],
            },
        }]
        with TemporaryDirectory() as temp_dir:
            create_viewer(temp_dir, session)
            output = Path(temp_dir, "index.html").read_text(encoding="utf-8")
            self.assertIn('class="dashboard"', output)
            self.assertIn("Thông số cần nhớ", output)
            self.assertIn("Sát thương cơ bản: 42.", output)
            self.assertIn("Chưa có nguồn kiểm chứng đính kèm", output)
            self.assertIn("Bạn đang chơi bản nào?", output)
            self.assertEqual(len(list(Path(temp_dir).glob("001_*.html"))), 1)

    def test_create_viewer_skips_rewriting_existing_days(self):
        with TemporaryDirectory() as temp_dir:
            # First pass: create Day 1 and Day 2
            session = [
                {
                    "day": "Day 1 — Giới thiệu",
                    "html": "<p>Nội dung Day 1</p>",
                    "_needs_disk_write": True,
                },
                {
                    "day": "Day 2 — Căn bản",
                    "html": "<p>Nội dung Day 2</p>",
                    "_needs_disk_write": True,
                },
            ]
            create_viewer(temp_dir, session)
            day1_files = list(Path(temp_dir).glob("001_*.html"))
            self.assertEqual(len(day1_files), 1)
            day1_path = day1_files[0]
            mtime_initial = day1_path.stat().st_mtime_ns

            # Second pass: simulate Day 3 is newly generated, Day 1 and Day 2 already exist
            session.append({
                "day": "Day 3 — Nâng cao",
                "html": "<p>Nội dung Day 3</p>",
                "_needs_disk_write": True,
            })
            # Day 1 and 2 don't have _needs_disk_write flag
            create_viewer(temp_dir, session)

            # Day 1 file should NOT have been re-written
            mtime_after = day1_path.stat().st_mtime_ns
            self.assertEqual(mtime_initial, mtime_after, "Day 1 file should not have been overwritten!")

            # Day 3 file should exist
            day3_files = list(Path(temp_dir).glob("003_*.html"))
            self.assertEqual(len(day3_files), 1)


if __name__ == "__main__":
    unittest.main()
