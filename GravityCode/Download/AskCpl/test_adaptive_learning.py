import tempfile
import unittest

from adaptive_learning import (
    build_day_context,
    default_profile,
    default_state,
    load_profile,
    load_state,
    profile_questions,
    record_learner_feedback,
    record_generated_lesson,
    save_profile,
    lesson_to_markdown,
    validate_lesson,
)


class AdaptiveLearningTests(unittest.TestCase):
    def test_profile_round_trip_and_intake_questions(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertGreaterEqual(len(profile_questions(default_profile())), 4)
            profile = save_profile(directory, {"domain": "Python", "goal": "Tạo ứng dụng", "minutes_per_day": 45})
            self.assertEqual(load_profile(directory)["minutes_per_day"], 45)
            self.assertEqual(profile["domain"], "Python")

    def test_context_includes_relevant_feedback_not_full_roadmap(self):
        profile = default_profile()
        profile.update({"domain": "Python", "goal": "CLI", "current_level": "Biết biến"})
        state = default_state()
        state["learner_feedback"] = {"1": "Lỗi ModuleNotFoundError"}
        text = build_day_context(profile, state, "Day 2 — import", "Dạy import", ["python_docs.pdf"])
        self.assertIn("ModuleNotFoundError", text)
        self.assertIn("python_docs.pdf", text)

    def test_lesson_validation_and_feedback(self):
        lesson = {
            "lesson_markdown": "# Bài", "learning_objectives": ["Biết"], "deliverable": "main.py",
            "completion_check": ["Chạy được"], "review_summary": "Không", "clarifying_questions": [],
            "visual_plan": {"needed": False, "purpose": "", "prompts": []}, "source_usage": ["docs"],
        }
        self.assertEqual(validate_lesson(lesson), [])
        lesson["visual_assets"] = ["assets/day_1/visual_01.png"]
        self.assertIn("assets/day_1/visual_01.png", lesson_to_markdown(lesson))
        state = default_state()
        record_generated_lesson(state, "Day 1 — Test", lesson)
        self.assertIn("1", state["generated_days"])
        with tempfile.TemporaryDirectory() as directory:
            record_learner_feedback(directory, "Day 1 — Test", "Đã chạy được", "đạt")
            self.assertEqual(load_state(directory)["mastery"]["1"], "đạt")


if __name__ == "__main__":
    unittest.main()
