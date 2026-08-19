import json
import unittest
from pathlib import Path


class LLMReviewerAnalysisArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.analysis_path = (
            Path(__file__).resolve().parents[1]
            / "evaluation"
            / "analysis"
            / "phase2_llm_reviewer_analysis_v1.json"
        )
        self.dimension_allowed = {
            "finding_alignment": {"STRONG", "PARTIAL", "WEAK"},
            "evidence_discipline": {"GROUNDED", "MIXED", "UNSUPPORTED"},
            "category_relevance": {"FOCUSED", "SOME_LEAKAGE", "SIGNIFICANT_LEAKAGE"},
            "severity_calibration": {
                "CALIBRATED",
                "ONE_LEVEL_OFF",
                "MATERIALLY_MISALIGNED",
            },
            "engineering_usefulness": {"HIGH", "MEDIUM", "LOW"},
            "overall_judgment": {"STRONG", "MIXED", "WEAK"},
        }
        self.categories = {
            "Security",
            "Scalability",
            "Reliability",
            "Observability",
            "Cost",
        }

    def test_required_top_level_fields_present(self) -> None:
        with self.analysis_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        for required in [
            "dataset_id",
            "evaluation_artifact",
            "adjudication_artifact",
            "adjudication_version",
            "analysis_version",
            "record_count",
            "dimension_distributions",
            "cross_tabs",
            "descriptive_statistics",
            "observations",
        ]:
            self.assertIn(required, payload)

    def test_record_count_and_dimension_distributions(self) -> None:
        with self.analysis_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        self.assertEqual(payload["record_count"], 25)

        distributions = payload["dimension_distributions"]
        for dimension, allowed_labels in self.dimension_allowed.items():
            self.assertIn(dimension, distributions)
            labels = set(distributions[dimension].keys())
            self.assertEqual(labels, allowed_labels)

            total_count = sum(item["count"] for item in distributions[dimension].values())
            self.assertEqual(total_count, 25)

    def test_cross_tabs_cover_all_categories_and_scenarios(self) -> None:
        with self.analysis_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        cross_tabs = payload["cross_tabs"]

        for key in [
            "overall_judgment_by_category",
            "severity_calibration_by_category",
            "evidence_discipline_by_category",
            "engineering_usefulness_by_category",
        ]:
            self.assertIn(key, cross_tabs)
            self.assertEqual(set(cross_tabs[key].keys()), self.categories)
            for category_payload in cross_tabs[key].values():
                self.assertEqual(category_payload["total"], 5)

        scenario_tab = cross_tabs["overall_judgment_by_scenario"]
        self.assertEqual(len(scenario_tab), 5)
        for scenario_payload in scenario_tab.values():
            self.assertEqual(scenario_payload["total"], 5)

    def test_descriptive_statistics_have_expected_shapes(self) -> None:
        with self.analysis_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        stats = payload["descriptive_statistics"]
        self.assertIn("average_deterministic_score", stats)
        self.assertIn("average_llm_score", stats)
        self.assertIn("average_score_difference_llm_minus_deterministic", stats)

        for dist_key in [
            "deterministic_vote_distribution",
            "llm_vote_distribution",
            "reference_severity_distribution",
            "deterministic_severity_distribution",
            "llm_severity_distribution",
        ]:
            self.assertIn(dist_key, stats)
            self.assertEqual(
                sum(item["count"] for item in stats[dist_key].values()),
                25,
            )


if __name__ == "__main__":
    unittest.main()
