import os
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from auto_ai_worker import create_viewer, save_session


class HtmlContentIntegrityTests(unittest.TestCase):
    def test_save_session_strips_html_to_prevent_ram_bloat(self):
        """Rule 3.5: session.json must NOT contain raw HTML or completed raw_responses."""
        session = [{
            "day": "Day 1 — Test Lambda",
            "html": "<div class=\"main-section\">Nội dung bài học mẫu về Lambda đệ quy</div>",
            "raw_responses": ["Response turn 1", "Response turn 2"],
            "completed": True,
            "followup_complete": True,
            "timestamp": 123456789,
        }]
        with TemporaryDirectory() as temp_dir:
            save_session(session, temp_dir)
            session_file = Path(temp_dir, "session.json")
            self.assertTrue(session_file.exists())
            data = json.loads(session_file.read_text(encoding="utf-8"))
            self.assertEqual(len(data), 1)
            self.assertNotIn("html", data[0])
            self.assertNotIn("raw_responses", data[0])
            self.assertEqual(data[0]["day"], "Day 1 — Test Lambda")
            self.assertTrue(data[0]["completed"])

    def test_create_viewer_writes_real_content_and_recovers_on_resume(self):
        """Verify that create_viewer writes full HTML and recovers content from file on resume."""
        sample_html = "<div class=\"main-section\"><p>Công thức Lambda Excel chuyên sâu</p></div>"
        session_in_memory = [{
            "day": "Day 1 — Test Lambda",
            "html": sample_html,
            "completed": True,
            "followup_complete": True,
            "timestamp": 123456789,
        }]
        with TemporaryDirectory() as temp_dir:
            # First pass: in-memory run writes standalone HTML file
            create_viewer(temp_dir, session_in_memory)
            html_files = list(Path(temp_dir).glob("001_*.html"))
            self.assertEqual(len(html_files), 1)
            content = html_files[0].read_text(encoding="utf-8")
            self.assertIn("Công thức Lambda Excel chuyên sâu", content)
            self.assertIn('<div class="content"><div class="main-section"><p>Công thức Lambda Excel chuyên sâu</p></div></div>', content)

            # Save session to disk (which strips html)
            save_session(session_in_memory, temp_dir)

            # Second pass: simulating restart/resume by loading stripped session.json
            loaded_session = json.loads(Path(temp_dir, "session.json").read_text(encoding="utf-8"))
            self.assertNotIn("html", loaded_session[0])

            # create_viewer should recover content from the existing HTML file on disk
            create_viewer(temp_dir, loaded_session)
            index_html = Path(temp_dir, "index.html").read_text(encoding="utf-8")
            self.assertIn("Công thức Lambda Excel chuyên sâu", index_html)


if __name__ == "__main__":
    unittest.main()
