import json
import unittest
from collections import defaultdict
from pathlib import Path


class LLMReviewerAdjudicationTemplatePhase21Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.adjudication_path = (
            Path(__file__).resolve().parents[1]
            / "evaluation"
            / "adjudication"
            / "phase2_1_llm_reviewer_adjudication_v1.json"
        )
        self.allowed_categories = {
            "Security",
            "Scalability",
            "Reliability",
            "Observability",
            "Cost",
        }
        self.allowed_reference_severities = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        self.allowed_finding_alignment = {"STRONG", "PARTIAL", "WEAK"}
        self.allowed_evidence_discipline = {"GROUNDED", "MIXED", "UNSUPPORTED"}
        self.allowed_category_relevance = {
            "FOCUSED",
            "SOME_LEAKAGE",
            "SIGNIFICANT_LEAKAGE",
        }
        self.allowed_severity_calibration = {
            "CALIBRATED",
            "ONE_LEVEL_OFF",
            "MATERIALLY_MISALIGNED",
        }
        self.allowed_engineering_usefulness = {"HIGH", "MEDIUM", "LOW"}
        self.allowed_overall_judgment = {"STRONG", "MIXED", "WEAK"}

    def test_required_top_level_metadata_exists(self) -> None:
        with self.adjudication_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        self.assertIn("dataset_id", payload)
        self.assertIn("evaluation_artifact", payload)
        self.assertIn("adjudication_version", payload)
        self.assertIn("evaluation_dimensions", payload)
        self.assertIn("records", payload)

    def test_exactly_25_records_and_full_scenario_category_coverage(self) -> None:
        with self.adjudication_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        records = payload["records"]
        self.assertEqual(len(records), 25)

        scenario_to_categories: dict[str, set[str]] = defaultdict(set)
        for record in records:
            scenario_to_categories[record["scenario_id"]].add(record["category"])

        self.assertEqual(len(scenario_to_categories), 5)
        for categories in scenario_to_categories.values():
            self.assertEqual(categories, self.allowed_categories)

    def test_record_metadata_fields_and_enum_constraints(self) -> None:
        with self.adjudication_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        for record in payload["records"]:
            for required in [
                "scenario_id",
                "scenario_name",
                "category",
                "reference_severity",
                "llm_severity",
                "deterministic_severity",
                "llm_score",
                "deterministic_score",
                "finding_alignment",
                "evidence_discipline",
                "category_relevance",
                "severity_calibration",
                "engineering_usefulness",
                "overall_judgment",
                "notes",
                "reviewer",
                "llm_evidence_basis",
                "llm_severity_hint",
                "llm_confidence",
                "llm_category_relevance_note",
                "llm_score_rationale",
                "llm_severity_rationale",
            ]:
                self.assertIn(required, record)

            self.assertIn(record["category"], self.allowed_categories)
            self.assertIn(record["reference_severity"], self.allowed_reference_severities)
            self.assertIn(record["llm_severity"], self.allowed_reference_severities)
            self.assertIn(
                record["deterministic_severity"],
                self.allowed_reference_severities,
            )
            self.assertIsInstance(record["llm_score"], int)
            self.assertIsInstance(record["deterministic_score"], int)
            self.assertIn(record["finding_alignment"], self.allowed_finding_alignment)
            self.assertIn(record["evidence_discipline"], self.allowed_evidence_discipline)
            self.assertIn(record["category_relevance"], self.allowed_category_relevance)
            self.assertIn(record["severity_calibration"], self.allowed_severity_calibration)
            self.assertIn(
                record["engineering_usefulness"],
                self.allowed_engineering_usefulness,
            )
            self.assertIn(record["overall_judgment"], self.allowed_overall_judgment)
            self.assertEqual(record["reviewer"], "human")

            for maybe_list in [
                record["llm_evidence_basis"],
                record["llm_severity_hint"],
                record["llm_confidence"],
                record["llm_category_relevance_note"],
            ]:
                self.assertTrue(maybe_list is None or isinstance(maybe_list, list))

            self.assertTrue(
                record["llm_score_rationale"] is None
                or isinstance(record["llm_score_rationale"], str)
            )
            self.assertTrue(
                record["llm_severity_rationale"] is None
                or isinstance(record["llm_severity_rationale"], str)
            )


if __name__ == "__main__":
    unittest.main()
