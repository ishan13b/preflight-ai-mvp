import unittest
from unittest.mock import Mock

from pydantic import ValidationError

from app.reviewers.cost_llm import CostLLMReviewer
from app.schemas.review import (
    ArchitectureReviewRequest,
    BoardVote,
    CostReviewerLLMResult,
)
from app.services.llm.provider import LLMProvider, LLMProviderError


class CostLLMReviewerTests(unittest.TestCase):
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

    def test_valid_structured_result_maps_to_cost_category(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = CostReviewerLLMResult(
            score=8,
            summary="Cost profile is manageable with clear optimization headroom.",
            engineering_reasoning=(
                "Inference and retrieval are primary cost drivers, but caching and "
                "batching can reduce repeated expensive work."
            ),
            risks=["High-volume model calls may dominate monthly spend"],
            recommendations=["Apply cache-first retrieval for repeated query patterns"],
            estimated_impact="Cloud spend may rise faster than traffic without controls.",
        )

        reviewer = CostLLMReviewer(provider, confidence=80)
        category = reviewer.review(self.request)

        self.assertEqual(category.category, "Cost")
        self.assertEqual(category.score, 8)
        self.assertEqual(category.vote, BoardVote.APPROVED_WITH_CONCERNS)
        self.assertEqual(
            category.issues, ["High-volume model calls may dominate monthly spend"]
        )
        self.assertEqual(
            category.recommendations[0],
            "Apply cache-first retrieval for repeated query patterns",
        )
        self.assertEqual(category.confidence, 80)

    def test_final_vote_is_derived_deterministically_from_score(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = CostReviewerLLMResult(
            score=9,
            summary="Strong cost posture for expected usage.",
            engineering_reasoning=(
                "Major spend drivers are understood, with practical controls for "
                "token usage and scaling efficiency."
            ),
            risks=[],
            recommendations=["Keep usage budgets and alerts calibrated"],
            estimated_impact="Low near-term risk of unexpected cost escalation.",
        )

        category = CostLLMReviewer(provider).review(self.request)

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
            CostLLMReviewer(provider).review(self.request)

    def test_provider_errors_are_wrapped_with_cost_context(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.side_effect = LLMProviderError("provider failed")

        with self.assertRaises(LLMProviderError) as ctx:
            CostLLMReviewer(provider).review(self.request)

        self.assertIn("Cost LLM review failed", str(ctx.exception))

    def test_cost_specific_instruction_is_passed_to_provider(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = CostReviewerLLMResult(
            score=7,
            summary="Cost concerns are present in growth scenarios.",
            engineering_reasoning=(
                "Cost telemetry is partial, and model call volume can increase quickly "
                "with traffic without stronger controls."
            ),
            risks=["Runaway spend risk under sudden traffic increases"],
            recommendations=["Add budget guardrails and per-request cost tracking"],
            estimated_impact="Higher-than-expected monthly spend and margin pressure.",
        )

        CostLLMReviewer(provider).review(self.request)

        provider.generate_structured.assert_called_once()
        kwargs = provider.generate_structured.call_args.kwargs
        self.assertEqual(kwargs["response_model"].__name__, "CostReviewerLLMResult")
        self.assertIn("model/API call costs", kwargs["system_instruction"])
        self.assertIn("theoretical cost concerns", kwargs["system_instruction"])


if __name__ == "__main__":
    unittest.main()
