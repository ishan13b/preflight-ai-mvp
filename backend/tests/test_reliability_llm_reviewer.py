import unittest
from unittest.mock import Mock

from pydantic import ValidationError

from app.reviewers.reliability_llm import ReliabilityLLMReviewer
from app.schemas.review import (
    ArchitectureReviewRequest,
    BoardVote,
    ReliabilityReviewerLLMResult,
)
from app.services.llm.provider import LLMProvider, LLMProviderError


class ReliabilityLLMReviewerTests(unittest.TestCase):
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

    def test_valid_structured_result_maps_to_reliability_category(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = ReliabilityReviewerLLMResult(
            score=8,
            summary="Reliability is generally acceptable with notable failure-path gaps.",
            engineering_reasoning=(
                "Core services are replicated, but retry and fallback strategies are "
                "incomplete for upstream model and retrieval failures."
            ),
            risks=["Provider failures may trigger cascading timeouts"],
            recommendations=["Define bounded retries and fallback responses"],
            estimated_impact="Intermittent outages can cause elevated error rates.",
        )

        reviewer = ReliabilityLLMReviewer(provider, confidence=82)
        category = reviewer.review(self.request)

        self.assertEqual(category.category, "Reliability")
        self.assertEqual(category.score, 8)
        self.assertEqual(category.vote, BoardVote.APPROVED_WITH_CONCERNS)
        self.assertEqual(
            category.issues, ["Provider failures may trigger cascading timeouts"]
        )
        self.assertEqual(
            category.recommendations[0], "Define bounded retries and fallback responses"
        )
        self.assertEqual(category.confidence, 82)

    def test_final_vote_is_derived_deterministically_from_score(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = ReliabilityReviewerLLMResult(
            score=9,
            summary="Strong resilience posture.",
            engineering_reasoning=(
                "Critical paths have explicit timeout, retry, and degradation behavior "
                "with limited single points of failure."
            ),
            risks=[],
            recommendations=["Keep failure-injection tests in CI"],
            estimated_impact="Low near-term risk of prolonged service disruption.",
        )

        category = ReliabilityLLMReviewer(provider).review(self.request)

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
            ReliabilityLLMReviewer(provider).review(self.request)

    def test_provider_errors_are_wrapped_with_reliability_context(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.side_effect = LLMProviderError("provider failed")

        with self.assertRaises(LLMProviderError) as ctx:
            ReliabilityLLMReviewer(provider).review(self.request)

        self.assertIn("Reliability LLM review failed", str(ctx.exception))

    def test_reliability_specific_instruction_is_passed_to_provider(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = ReliabilityReviewerLLMResult(
            score=7,
            summary="Reliability concerns are present.",
            engineering_reasoning=(
                "Queue durability and fallback behavior are partially specified."
            ),
            risks=["Recovery behavior after provider outages is underspecified"],
            recommendations=["Define replay and restoration procedures"],
            estimated_impact="Longer recovery times after upstream incidents.",
        )

        ReliabilityLLMReviewer(provider).review(self.request)

        provider.generate_structured.assert_called_once()
        kwargs = provider.generate_structured.call_args.kwargs
        self.assertEqual(kwargs["response_model"].__name__, "ReliabilityReviewerLLMResult")
        self.assertIn("single points of failure", kwargs["system_instruction"])
        self.assertIn("theoretically possible failures", kwargs["system_instruction"])


if __name__ == "__main__":
    unittest.main()
