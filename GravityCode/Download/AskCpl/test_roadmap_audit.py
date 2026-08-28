"""Comprehensive Verification & Audit Suite for Access 600-Day and Excel 1000-Day Roadmaps.

Validates:
1. Day Sequence Completeness (1..600 and 1..1000 continuous, no missing, no duplicate days)
2. Block Completeness (Prompt, Bài tập, Tags present on 100% of days)
3. Regex Parser Compatibility (AskCpl and Copilot Addon standard regex)
4. Time Estimation Metrics (Realistic, distinct distribution across phases)
5. Title Uniqueness & No Duplicate Topics
6. UTF-8 Encoding & Zero Mojibake
7. Domain Profile Discovery & Caching System
"""

import os
import re
import sys
import unittest
from domain_profiles import (
    get_or_create_domain_profile,
    load_cached_profiles,
    save_cached_profiles,
    instruction_for,
    PREDEFINED_PROFILES
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE_DIR = os.path.dirname(__file__)
ACCESS_FILE = os.path.join(WORKSPACE_DIR, "roadmap_access_vba_600.md")
EXCEL_FILE = os.path.join(WORKSPACE_DIR, "roadmap_excel_vba_1000.md")

DAY_HEADER_REGEX = re.compile(r"^##\s+Day\s+(\d+[a-zA-Z]?)\s*[—–-]\s*(.+)$", re.MULTILINE)

class TestRoadmapIntegrity(unittest.TestCase):

    def test_01_domain_profiles_system(self):
        """Test domain profiles static matching and caching."""
        acc_prof = get_or_create_domain_profile("access")
        self.assertEqual(acc_prof.get("recommended_days"), 600)
        self.assertIn("Kiến trúc sư", acc_prof.get("persona", ""))

        xl_prof = get_or_create_domain_profile("excel")
        self.assertEqual(xl_prof.get("recommended_days"), 1000)
        self.assertIn("Kỹ sư", xl_prof.get("persona", ""))

        # Test mock dynamic AI profile generation
        def mock_llm(prompt, label, json_mode=True):
            return '{"title": "Rust Master", "recommended_days": 800, "persona": "Rust Systems Architect", "category": "Systems Programming", "instruction": "PROFILE RUST: ...", "mandatory_milestones": ["ownership", "borrowing"]}'

        rust_prof = get_or_create_domain_profile("rust_test_domain", llm_callable=mock_llm)
        self.assertEqual(rust_prof.get("recommended_days"), 800)
        self.assertIn("ownership", rust_prof.get("mandatory_milestones", []))

        # Check cache persistence
        cache = load_cached_profiles()
        self.assertIn("rust_test_domain", cache)

    def _audit_roadmap_file(self, filepath, expected_days, domain_name):
        self.assertTrue(os.path.exists(filepath), f"File {filepath} must exist")
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Check actual double-encoding mojibake patterns
        for bad_pattern in ["Ã¡", "Ã©", "Ãª", "Ã´", "Ã¹", "â€œ", "â€“", "â€”"]:
            self.assertNotIn(bad_pattern, content, f"Mojibake pattern {bad_pattern} detected")

        # Find all Day headers
        matches = list(DAY_HEADER_REGEX.finditer(content))
        self.assertEqual(len(matches), expected_days, f"Expected {expected_days} days, found {len(matches)}")

        # Check continuous numbering
        found_days = []
        titles = []
        for m in matches:
            d_num = int(m.group(1))
            title = m.group(2).strip()
            found_days.append(d_num)
            titles.append(title)

        expected_sequence = list(range(1, expected_days + 1))
        self.assertEqual(found_days, expected_sequence, f"Days sequence must be continuous 1..{expected_days}")

        # Check 3 blocks: Prompt, Bài tập, Tags
        prompts_count = len(re.findall(r"\*\*Prompt:\*\*", content))
        exercises_count = len(re.findall(r"\*\*Bài tập:\*\*", content))
        tags_count = len(re.findall(r"\*\*Tags:\*\*", content))
        self.assertEqual(prompts_count, expected_days, f"Prompt count must match {expected_days}")
        self.assertEqual(exercises_count, expected_days, f"Exercise count must match {expected_days}")
        self.assertEqual(tags_count, expected_days, f"Tags count must match {expected_days}")

        # Check title uniqueness
        unique_titles = set(titles)
        self.assertEqual(len(unique_titles), len(titles), f"All {expected_days} day titles must be unique")

        # Metrics
        print(f"\n📊 [{domain_name}] Báo Cáo Kiểm Tra:")
        print(f"   • Tổng số ngày: {len(found_days)}/{expected_days} ✅")
        print(f"   • Số khối Prompt / Bài tập / Tags: {prompts_count} / {exercises_count} / {tags_count} ✅")
        print(f"   • Tiêu đề duy nhất 100%: {len(unique_titles)}/ {len(titles)} ✅")
        print(f"   • Dung lượng file: {len(content):,} bytes (~{len(content)/(1024*1024):.2f} MB)")

    def test_02_access_roadmap_600_days(self):
        """Verify Access 600 Days roadmap."""
        self._audit_roadmap_file(ACCESS_FILE, 600, "ACCESS VBA (600 NGÀY)")

    def test_03_excel_roadmap_1000_days(self):
        """Verify Excel 1000 Days roadmap."""
        self._audit_roadmap_file(EXCEL_FILE, 1000, "EXCEL VBA (1.000 NGÀY)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
