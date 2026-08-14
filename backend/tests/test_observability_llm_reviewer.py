import unittest
from unittest.mock import Mock

from pydantic import ValidationError

from app.reviewers.observability_llm import ObservabilityLLMReviewer
from app.schemas.review import (
    ArchitectureReviewRequest,
    BoardVote,
    ObservabilityReviewerLLMResult,
)
from app.services.llm.provider import LLMProvider, LLMProviderError


class ObservabilityLLMReviewerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.request = ArchitectureReviewRequest(
            application_name="Customer Support Bot",
            frontend="React",
            backend="FastAPI",
            llm="GPT-5.5",
            vector_db="Pinecone",
            embeddings="BGE Large",
            cache="Redis",
            monitoring="Datadog",
            authentication="JWT",
            traffic=30000,
        )

    def test_valid_structured_result_maps_to_observability_category(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = ObservabilityReviewerLLMResult(
            score=8,
            summary="Observability is solid but incident diagnosis can be improved.",
            engineering_reasoning=(
                "Core service metrics exist, but trace correlation and model-call "
                "visibility are incomplete across critical flows."
            ),
            risks=["Cross-service root-cause analysis may be slow during incidents"],
            recommendations=["Add distributed tracing with shared correlation IDs"],
            estimated_impact="Longer mean time to resolution during production failures.",
        )

        reviewer = ObservabilityLLMReviewer(provider, confidence=81)
        category = reviewer.review(self.request)

        self.assertEqual(category.category, "Observability")
        self.assertEqual(category.score, 8)
        self.assertEqual(category.vote, BoardVote.APPROVED_WITH_CONCERNS)
        self.assertEqual(
            category.issues, ["Cross-service root-cause analysis may be slow during incidents"]
        )
        self.assertEqual(
            category.recommendations[0],
            "Add distributed tracing with shared correlation IDs",
        )
        self.assertEqual(category.confidence, 81)

    def test_final_vote_is_derived_deterministically_from_score(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = ObservabilityReviewerLLMResult(
            score=9,
            summary="Strong observability posture.",
            engineering_reasoning=(
                "Metrics, structured logs, tracing, and actionable alerts provide fast "
                "detection and diagnosis."
            ),
            risks=[],
            recommendations=["Continuously tune alert quality and SLO coverage"],
            estimated_impact="Low near-term risk of blind spots during incidents.",
        )

        category = ObservabilityLLMReviewer(provider).review(self.request)

        self.assertEqual(category.score, 9)
        self.assertEqual(category.vote, BoardVote.APPROVED)

    def test_invalid_score_is_rejected(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = {
            "score": 11,
            "summary": "invalid",
            "engineering_reasoning": "invalid",
            "risks": [],
            "recommendations": [],
            "estimated_impact": "invalid",
        }

        with self.assertRaises(ValidationError):
            ObservabilityLLMReviewer(provider).review(self.request)

    def test_provider_errors_are_wrapped_with_observability_context(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.side_effect = LLMProviderError("provider failed")

        with self.assertRaises(LLMProviderError) as ctx:
            ObservabilityLLMReviewer(provider).review(self.request)

        self.assertIn("Observability LLM review failed", str(ctx.exception))

    def test_observability_specific_instruction_is_passed_to_provider(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = ObservabilityReviewerLLMResult(
            score=7,
            summary="Observability has meaningful gaps.",
            engineering_reasoning=(
                "Baseline metrics exist, but logging and alert correlation are too weak "
                "for fast diagnosis."
            ),
            risks=["Noisy telemetry obscures high-priority production signals"],
            recommendations=["Define high-value alerts and normalize log fields"],
            estimated_impact="Slower incident triage and delayed remediation.",
        )

        ObservabilityLLMReviewer(provider).review(self.request)

        provider.generate_structured.assert_called_once()
        kwargs = provider.generate_structured.call_args.kwargs
        self.assertEqual(kwargs["response_model"].__name__, "ObservabilityReviewerLLMResult")
        self.assertIn("distributed tracing", kwargs["system_instruction"])
        self.assertIn("noisy or low-value instrumentation", kwargs["system_instruction"])


if __name__ == "__main__":
    unittest.main()
