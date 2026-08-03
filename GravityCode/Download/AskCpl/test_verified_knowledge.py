import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from knowledge_pack_importer import import_csv_folder
from verified_knowledge import (
    build_fact_context,
    coverage_report,
    empty_pack,
    validate_fact_claims,
    validate_pack,
)


def sample_pack():
    pack = empty_pack("Sango sample")
    pack["game_version"] = "Sango VII bản gốc"
    pack["sources"] = [{
        "id": "cn_ali213_heroes", "title": "Danh sách tướng (Trung)",
        "url": "https://example.test/heroes", "language": "zh-CN", "game_version": "bản gốc",
    }]
    pack["entities"]["heroes"] = [{
        "id": "hero_demo", "name": "Tướng mẫu", "stats": {"str": 80},
        "source_ids": ["cn_ali213_heroes"], "verification_status": "verified",
    }]
    pack["coverage_targets"] = {"heroes": 2}
    return pack


class VerifiedKnowledgeTests(unittest.TestCase):
    def test_full_catalogue_is_blocked_when_target_coverage_is_missing(self):
        report = coverage_report(sample_pack(), "liệt kê toàn bộ tướng")
        self.assertTrue(report["requested_all"])
        self.assertFalse(report["complete"])

    def test_context_contains_only_verified_entities_and_warns_on_coverage(self):
        pack = sample_pack()
        pack["entities"]["heroes"].append({"id": "unverified", "name": "Không được dùng", "verification_status": "candidate", "source_ids": []})
        context, _ = build_fact_context(pack, "toàn bộ tướng")
        self.assertIn("hero_demo", context)
        self.assertNotIn("unverified", context)
        self.assertIn("not available", context)

    def test_claim_cannot_reference_unknown_entity_or_wrong_source(self):
        pack = sample_pack()
        invalid = {"factual_claims": [{"entity_id": "made_up", "source_ids": ["cn_ali213_heroes"], "claim": "x"}]}
        self.assertTrue(validate_fact_claims(invalid, pack))
        valid = {"factual_claims": [{"entity_id": "hero_demo", "source_ids": ["cn_ali213_heroes"], "claim": "Dữ kiện cần đối chiếu"}]}
        self.assertEqual(validate_fact_claims(valid, pack), [])

    def test_csv_import_requires_sources_for_verified_entities(self):
        with TemporaryDirectory() as temp:
            folder = Path(temp, "csv")
            folder.mkdir()
            Path(folder, "sources.csv").write_text("id,title,url\ns1,Nguồn,https://example.test\n", encoding="utf-8")
            Path(folder, "heroes.csv").write_text(
                "id,name,source_ids,verification_status\nh1,Tướng mẫu,s1,verified\n", encoding="utf-8"
            )
            output = Path(temp, "pack.json")
            pack = import_csv_folder(str(folder), str(output))
            self.assertEqual(validate_pack(pack), [])
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["entities"]["heroes"][0]["id"], "h1")


if __name__ == "__main__":
    unittest.main()
