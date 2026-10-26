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


if __name__ == "__main__":
    unittest.main()
