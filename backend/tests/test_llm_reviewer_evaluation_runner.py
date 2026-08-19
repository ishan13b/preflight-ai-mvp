import json
import tempfile
import unittest
from pathlib import Path

from app.services.llm.provider import LLMProvider, LLMProviderError
from evaluation.models import ReviewerStatus, ReviewerType, load_reference_dataset
from evaluation.runner import LLMReviewerEvaluationRunner


class _MockLLMProvider(LLMProvider):
    def __init__(self) -> None:
        self.calls = 0

    def generate_structured(
        self,
        *,
        system_instruction: str,
        user_input: str,
        response_model: type,
    ) -> object:
        self.calls += 1
        return {
            "score": 8,
            "summary": "Mocked LLM summary",
            "engineering_reasoning": "Mocked LLM reasoning",
            "findings": [
                {
                    "statement": "Mocked LLM risk",
                    "evidence_basis": "INFERRED_RISK",
                    "severity_hint": "MEDIUM",
                }
            ],
            "recommendations": ["Mocked LLM recommendation"],
            "estimated_impact": "Mocked LLM impact",
            "score_rationale": "Mocked score rationale.",
            "severity_rationale": "Mocked severity rationale.",
        }


class _PartiallyFailingLLMProvider(LLMProvider):
    def generate_structured(
        self,
        *,
        system_instruction: str,
        user_input: str,
        response_model: type,
    ) -> object:
        if "Reliability reviewer" in system_instruction:
            raise RuntimeError("simulated reliability provider failure")
        return {
            "score": 8,
            "summary": "Mocked LLM summary",
            "engineering_reasoning": "Mocked LLM reasoning",
            "findings": [
                {
                    "statement": "Mocked LLM risk",
                    "evidence_basis": "INFERRED_RISK",
                    "severity_hint": "MEDIUM",
                }
            ],
            "recommendations": ["Mocked LLM recommendation"],
            "estimated_impact": "Mocked LLM impact",
            "score_rationale": "Mocked score rationale.",
            "severity_rationale": "Mocked severity rationale.",
        }


class _DiagnosticsFailingLLMProvider(LLMProvider):
    def generate_structured(
        self,
        *,
        system_instruction: str,
        user_input: str,
        response_model: type,
    ) -> object:
        if "Scalability reviewer" in system_instruction:
            raise LLMProviderError(
                "OpenAI structured generation failed.",
                diagnostics={
                    "exception_class": "ValidationError",
                    "validation_errors": [
                        {
                            "loc": ["findings", "0", "statement"],
                            "msg": "NOT_SPECIFIED finding statements must explicitly signal uncertainty.",
                            "type": "value_error",
                        }
                    ],
                },
            )
        return {
            "score": 8,
            "summary": "Mocked LLM summary",
            "engineering_reasoning": "Mocked LLM reasoning",
            "findings": [
                {
                    "statement": "Mocked LLM risk",
                    "evidence_basis": "INFERRED_RISK",
                    "severity_hint": "MEDIUM",
                }
            ],
            "recommendations": ["Mocked LLM recommendation"],
            "estimated_impact": "Mocked LLM impact",
            "score_rationale": "Mocked score rationale.",
            "severity_rationale": "Mocked severity rationale.",
        }


class LLMReviewerEvaluationRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dataset_path = (
            Path(__file__).resolve().parents[1]
            / "evaluation"
            / "fixtures"
            / "llm_reviewer_reference_dataset.json"
        )

    def test_fixture_loading(self) -> None:
        dataset = load_reference_dataset(self.dataset_path)
        self.assertEqual(dataset.dataset_id, "preflight-phase2-llm-reviewer-reference-v1")
        self.assertEqual(len(dataset.scenarios), 5)
        self.assertEqual(len(dataset.categories), 5)

    def test_deterministic_reviewers_execute_for_all_records(self) -> None:
        runner = LLMReviewerEvaluationRunner(
            dataset_path=self.dataset_path,
            include_llm=False,
        )
        artifact = runner.run()

        self.assertEqual(artifact.total_records, 25)
        deterministic_statuses = [
            record.deterministic_result.status for record in artifact.records
        ]
        self.assertTrue(all(status == ReviewerStatus.SUCCESS for status in deterministic_statuses))

    def test_normalized_record_representation_contains_expected_fields(self) -> None:
        provider = _MockLLMProvider()
        runner = LLMReviewerEvaluationRunner(
            dataset_path=self.dataset_path,
            llm_provider=provider,
            include_llm=True,
        )
        artifact = runner.run()
        first = artifact.records[0]

        self.assertTrue(first.scenario_id)
        self.assertIn(first.category, {"Security", "Scalability", "Reliability", "Observability", "Cost"})
        self.assertEqual(first.deterministic_result.reviewer_type, ReviewerType.DETERMINISTIC)
        self.assertEqual(first.llm_result.reviewer_type, ReviewerType.LLM)
        self.assertIsNotNone(first.deterministic_result.raw_result)
        self.assertIsNotNone(first.llm_result.raw_result)
        self.assertGreaterEqual(len(first.reference_findings), 1)
        llm_raw = first.llm_result.raw_result or {}
        self.assertIn("llm_structured_result", llm_raw)
        structured = llm_raw["llm_structured_result"]
        self.assertIn("findings", structured)
        self.assertIn("score_rationale", structured)
        self.assertIn("severity_rationale", structured)

    def test_llm_failure_isolated_per_category(self) -> None:
        runner = LLMReviewerEvaluationRunner(
            dataset_path=self.dataset_path,
            llm_provider=_PartiallyFailingLLMProvider(),
            include_llm=True,
        )
        artifact = runner.run()

        reliability_failures = [
            record
            for record in artifact.records
            if record.category == "Reliability"
            and record.llm_result.status == ReviewerStatus.FAILED
        ]
        non_reliability_llm = [
            record.llm_result.status
            for record in artifact.records
            if record.category != "Reliability"
        ]

        self.assertEqual(len(reliability_failures), 5)
        self.assertTrue(all(status == ReviewerStatus.SUCCESS for status in non_reliability_llm))

    def test_output_artifact_structure_and_write(self) -> None:
        provider = _MockLLMProvider()
        runner = LLMReviewerEvaluationRunner(
            dataset_path=self.dataset_path,
            llm_provider=provider,
            include_llm=True,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "evaluation-artifact.json"
            written_path = runner.run_and_write(output_path)

            self.assertEqual(written_path, output_path)
            self.assertTrue(output_path.exists())

            with output_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)

            self.assertIn("dataset_id", payload)
            self.assertIn("dataset_version", payload)
            self.assertIn("run_metadata", payload)
            self.assertIn("records", payload)
            self.assertEqual(payload["scenario_count"], 5)
            self.assertEqual(payload["category_count"], 5)
            self.assertEqual(payload["total_records"], 25)

    def test_failed_llm_records_include_error_diagnostics_when_available(self) -> None:
        runner = LLMReviewerEvaluationRunner(
            dataset_path=self.dataset_path,
            llm_provider=_DiagnosticsFailingLLMProvider(),
            include_llm=True,
        )
        artifact = runner.run()

        failed_scalability = [
            record
            for record in artifact.records
            if record.category == "Scalability"
            and record.llm_result.status == ReviewerStatus.FAILED
        ]
        self.assertEqual(len(failed_scalability), 5)

        for record in failed_scalability:
            raw = record.llm_result.raw_result or {}
            diagnostics = raw.get("error_diagnostics")
            self.assertIsInstance(diagnostics, dict)
            assert isinstance(diagnostics, dict)
            self.assertEqual(diagnostics.get("exception_class"), "ValidationError")
            self.assertIn("validation_errors", diagnostics)

    def test_mocked_llm_path_makes_no_real_openai_calls(self) -> None:
        provider = _MockLLMProvider()
        runner = LLMReviewerEvaluationRunner(
            dataset_path=self.dataset_path,
            llm_provider=provider,
            include_llm=True,
        )
        artifact = runner.run()

        self.assertEqual(artifact.total_records, 25)
        self.assertEqual(provider.calls, 25)


if __name__ == "__main__":
    unittest.main()
