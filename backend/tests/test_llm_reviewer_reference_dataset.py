import json
import unittest
from pathlib import Path


class LLMReviewerReferenceDatasetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dataset_path = (
            Path(__file__).resolve().parents[1]
            / "evaluation"
            / "fixtures"
            / "llm_reviewer_reference_dataset.json"
        )
        self.required_categories = {
            "Security",
            "Scalability",
            "Reliability",
            "Observability",
            "Cost",
        }
        self.required_finding_fields = {
            "finding",
            "evidence_basis",
            "expected_severity",
            "importance",
            "why_it_matters",
            "recommendation_focus",
        }
        self.allowed_severities = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        self.allowed_importance = {"MAJOR_ISSUE", "MINOR_ISSUE", "ACCEPTABLE"}
        self.allowed_evidence_basis = {
            "OBSERVED",
            "NOT_SPECIFIED",
            "INFERRED_RISK",
        }

    def test_dataset_is_loadable(self) -> None:
        with self.dataset_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        self.assertIsInstance(payload, dict)
        self.assertEqual(
            payload["dataset_id"],
            "preflight-phase2-llm-reviewer-reference-v1",
        )
        self.assertGreaterEqual(len(payload["scenarios"]), 5)

    def test_each_scenario_contains_all_five_categories(self) -> None:
        with self.dataset_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        for scenario in payload["scenarios"]:
            category_expectations = scenario["category_expectations"]
            self.assertEqual(set(category_expectations.keys()), self.required_categories)

    def test_fixture_structure_and_required_fields(self) -> None:
        with self.dataset_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        for scenario in payload["scenarios"]:
            self.assertIn("scenario_id", scenario)
            self.assertIn("architecture_source_id", scenario)
            self.assertIn("architecture", scenario)

            architecture = scenario["architecture"]
            for field in [
                "application_name",
                "frontend",
                "backend",
                "llm",
                "vector_db",
                "embeddings",
                "cache",
                "monitoring",
                "authentication",
                "traffic",
            ]:
                self.assertIn(field, architecture)

            for category_name, category_payload in scenario[
                "category_expectations"
            ].items():
                self.assertIn(category_name, self.required_categories)
                findings = category_payload["expected_findings"]
                self.assertGreaterEqual(len(findings), 1)

                for finding in findings:
                    self.assertEqual(
                        set(finding.keys()),
                        self.required_finding_fields,
                    )
                    self.assertIn(
                        finding["evidence_basis"],
                        self.allowed_evidence_basis,
                    )
                    self.assertIn(finding["expected_severity"], self.allowed_severities)
                    self.assertIn(finding["importance"], self.allowed_importance)


if __name__ == "__main__":
    unittest.main()
