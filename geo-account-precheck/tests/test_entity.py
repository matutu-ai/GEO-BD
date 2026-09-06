"""Entity model and EntityResearcher tests."""

from __future__ import annotations

import unittest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from support import load_fixture

from engine.common import FACT, INFERENCE, UNKNOWN
from engine.entity.researcher import EntityResearcher
from engine.models.company import CompanyProfile
from engine.models.entity import EntityProfile, FactValue


class EntityModelTest(unittest.TestCase):
    def test_fact_value_defaults_to_unknown(self) -> None:
        fact = FactValue()
        self.assertEqual(fact.status, UNKNOWN)
        self.assertEqual(fact.confidence, 0)
        self.assertFalse(fact.verified)

    def test_fact_value_supports_explicit_fact(self) -> None:
        fact = FactValue(
            value="冷库设备工程",
            status=FACT,
            confidence=90,
            source="官网",
            source_type="official",
            verified=True,
            last_checked="2026-09-01",
        )
        self.assertEqual(fact.status, FACT)
        self.assertEqual(fact.confidence, 90)

    def test_entity_profile_filters_unknown_values(self) -> None:
        profile = EntityProfile(
            fields={
                "products": [
                    FactValue(value="组合式冷库", status=FACT, source_type="user_provided"),
                    FactValue(value="", status=UNKNOWN),
                    FactValue(value="UNKNOWN", status=UNKNOWN),
                ]
            }
        )
        self.assertEqual(profile.get_values("products"), ["组合式冷库"])
        self.assertTrue(profile.is_known("products"))
        self.assertFalse(profile.is_known("services"))

    def test_count_status_counts_only_populated_values(self) -> None:
        profile = EntityProfile(
            fields={
                "name": [FactValue(value="示例公司", status=FACT, source_type="user_provided")],
                "business": [FactValue(value="", status=UNKNOWN)],
                "products": [FactValue(value="冷库", status=INFERENCE, source_type="user_provided")],
            }
        )
        self.assertEqual(profile.count_status(FACT), 1)
        self.assertEqual(profile.count_status(INFERENCE), 1)


class EntityResearcherTest(unittest.TestCase):
    def setUp(self) -> None:
        self.company = CompanyProfile.from_dict(load_fixture())

    def test_research_keeps_user_input_as_fact_with_source(self) -> None:
        profile = EntityResearcher(mode="offline").research(self.company)
        self.assertEqual(profile.get_value("name"), "示例冷库设备公司")
        self.assertEqual(profile.get_value("business"), "冷库设备工程")
        self.assertEqual(profile.get_values("customers"), ["食品加工", "冷链物流", "医药"])
        item = profile.fields["name"][0]
        self.assertEqual(item.status, FACT)
        self.assertEqual(item.source_type, "user_provided")
        self.assertNotIn("name", profile.missing)
        self.assertNotIn("business", profile.missing)

    def test_missing_fields_are_unknown_and_listed(self) -> None:
        profile = EntityResearcher(mode="offline").research(CompanyProfile.from_dict({"company": {"name": "示例公司"}}))
        self.assertIn("business", profile.missing)
        self.assertIn("products", profile.missing)
        self.assertTrue(profile.fields["reviews"][0].value == "")
        self.assertEqual(profile.fields["reviews"][0].status, UNKNOWN)

    def test_empty_company_never_invents_facts(self) -> None:
        profile = EntityResearcher(mode="offline").research(CompanyProfile.from_dict({}))
        self.assertEqual(profile.get_value("name"), "")
        self.assertIn("name", profile.missing)
        self.assertEqual(profile.fields["name"][0].status, UNKNOWN)


if __name__ == "__main__":
    unittest.main()
