import json
import unittest
from collections import defaultdict
from pathlib import Path


class LLMReviewerAdjudicationTemplateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adjudication_path = (
            Path(__file__).resolve().parents[1]
            / "evaluation"
            / "adjudication"
            / "phase2_llm_reviewer_adjudication_v1.json"
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

            if record["finding_alignment"] is not None:
                self.assertIn(record["finding_alignment"], self.allowed_finding_alignment)
            if record["evidence_discipline"] is not None:
                self.assertIn(
                    record["evidence_discipline"], self.allowed_evidence_discipline
                )
            if record["category_relevance"] is not None:
                self.assertIn(
                    record["category_relevance"], self.allowed_category_relevance
                )
            if record["severity_calibration"] is not None:
                self.assertIn(
                    record["severity_calibration"], self.allowed_severity_calibration
                )
            if record["engineering_usefulness"] is not None:
                self.assertIn(
                    record["engineering_usefulness"],
                    self.allowed_engineering_usefulness,
                )
            if record["overall_judgment"] is not None:
                self.assertIn(record["overall_judgment"], self.allowed_overall_judgment)

    def test_all_qualitative_fields_are_populated_with_valid_values(self) -> None:
        with self.adjudication_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        for record in payload["records"]:
            self.assertIn(record["finding_alignment"], self.allowed_finding_alignment)
            self.assertIn(
                record["evidence_discipline"],
                self.allowed_evidence_discipline,
            )
            self.assertIn(
                record["category_relevance"],
                self.allowed_category_relevance,
            )
            self.assertIn(
                record["severity_calibration"],
                self.allowed_severity_calibration,
            )
            self.assertIn(
                record["engineering_usefulness"],
                self.allowed_engineering_usefulness,
            )
            self.assertIn(record["overall_judgment"], self.allowed_overall_judgment)
            self.assertEqual(record["reviewer"], "human")


if __name__ == "__main__":
    unittest.main()
