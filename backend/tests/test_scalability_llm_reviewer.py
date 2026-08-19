import unittest
from unittest.mock import Mock

from pydantic import ValidationError

from app.reviewers.scalability_llm import ScalabilityLLMReviewer
from app.schemas.review import (
    ArchitectureReviewRequest,
    BoardVote,
    EvidenceBasis,
    LLMReviewerFinding,
    Severity,
    ScalabilityReviewerLLMResult,
)
from app.services.llm.provider import LLMProvider, LLMProviderError


class ScalabilityLLMReviewerTests(unittest.TestCase):
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

    def test_valid_structured_result_maps_to_scalability_category(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = ScalabilityReviewerLLMResult(
            score=8,
            summary="Architecture can scale with moderate risk under spikes.",
            engineering_reasoning=(
                "Redis and queueing reduce repeated work, but inference capacity can "
                "become a bottleneck during concurrent bursts."
            ),
            findings=[
                LLMReviewerFinding(
                    statement="Inference workers may saturate during traffic spikes",
                    evidence_basis=EvidenceBasis.INFERRED_RISK,
                    severity_hint=Severity.MEDIUM,
                )
            ],
            recommendations=["Add autoscaling based on queue depth and latency"],
            estimated_impact="Throughput plateaus and p95 latency rises under spikes.",
            score_rationale="Primary scaling risk is inferred from traffic and inference profile.",
            severity_rationale="Risk is credible but partially mitigated by cache and async backend.",
        )

        reviewer = ScalabilityLLMReviewer(provider, confidence=83)
        category = reviewer.review(self.request)

        self.assertEqual(category.category, "Scalability")
        self.assertEqual(category.score, 8)
        self.assertEqual(category.vote, BoardVote.APPROVED_WITH_CONCERNS)
        self.assertEqual(
            category.issues, ["Inference workers may saturate during traffic spikes"]
        )
        self.assertEqual(
            category.recommendations[0],
            "Add autoscaling based on queue depth and latency",
        )
        self.assertEqual(category.confidence, 83)

    def test_final_vote_is_derived_deterministically_from_score(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = ScalabilityReviewerLLMResult(
            score=9,
            summary="Strong scalability posture.",
            engineering_reasoning=(
                "Horizontal autoscaling, cache coverage, and async work partitioning "
                "provide healthy headroom."
            ),
            findings=[
                LLMReviewerFinding(
                    statement="Queue burst behavior is not specified; validate backpressure under peak load.",
                    evidence_basis=EvidenceBasis.NOT_SPECIFIED,
                    severity_hint=Severity.LOW,
                )
            ],
            recommendations=["Keep load testing as traffic grows"],
            estimated_impact="Low near-term risk of throughput collapse.",
            score_rationale="Current controls suggest strong headroom with minor unknowns.",
            severity_rationale="Unspecified burst controls are low impact pending validation.",
        )

        category = ScalabilityLLMReviewer(provider).review(self.request)

        self.assertEqual(category.score, 9)
        self.assertEqual(category.vote, BoardVote.APPROVED)

    def test_invalid_score_is_rejected(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = {
            "score": 11,
            "summary": "invalid",
            "engineering_reasoning": "invalid",
            "findings": [],
            "recommendations": [],
            "estimated_impact": "invalid",
            "score_rationale": "invalid",
            "severity_rationale": "invalid",
        }

        with self.assertRaises(ValidationError):
            ScalabilityLLMReviewer(provider).review(self.request)

    def test_provider_errors_are_wrapped_with_scalability_context(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.side_effect = LLMProviderError("provider failed")

        with self.assertRaises(LLMProviderError) as ctx:
            ScalabilityLLMReviewer(provider).review(self.request)

        self.assertIn("Scalability LLM review failed", str(ctx.exception))

    def test_scalability_specific_instruction_is_passed_to_provider(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = ScalabilityReviewerLLMResult(
            score=7,
            summary="Some scalability concerns are present.",
            engineering_reasoning="Queueing is present but backpressure behavior is unclear.",
            findings=[
                LLMReviewerFinding(
                    statement="Backpressure handling is underspecified",
                    evidence_basis=EvidenceBasis.NOT_SPECIFIED,
                    severity_hint=Severity.MEDIUM,
                )
            ],
            recommendations=["Define queue limits and failure behavior"],
            estimated_impact="Latency spikes under sustained concurrency.",
            score_rationale="Unknown queue behavior can degrade p95 at high concurrency.",
            severity_rationale="Risk is not confirmed but likely under burst traffic.",
        )

        ScalabilityLLMReviewer(provider).review(self.request)

        provider.generate_structured.assert_called_once()
        kwargs = provider.generate_structured.call_args.kwargs
        self.assertEqual(kwargs["response_model"].__name__, "ScalabilityReviewerLLMResult")
        self.assertIn("traffic profile, concurrency", kwargs["system_instruction"])
        self.assertIn("queueing, and backpressure behavior", kwargs["system_instruction"])


if __name__ == "__main__":
    unittest.main()
