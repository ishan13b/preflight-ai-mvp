import unittest
from unittest.mock import Mock

from pydantic import ValidationError

from app.reviewers.reliability_llm import ReliabilityLLMReviewer
from app.schemas.review import (
    ArchitectureReviewRequest,
    BoardVote,
    EvidenceBasis,
    LLMReviewerFinding,
    Severity,
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
            findings=[
                LLMReviewerFinding(
                    statement="Provider failures may trigger cascading timeouts",
                    evidence_basis=EvidenceBasis.INFERRED_RISK,
                    severity_hint=Severity.HIGH,
                )
            ],
            recommendations=["Define bounded retries and fallback responses"],
            estimated_impact="Intermittent outages can cause elevated error rates.",
            score_rationale="Inferred dependency-chain failure mode materially affects uptime.",
            severity_rationale="Likelihood and blast radius justify elevated severity hint.",
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
            findings=[
                LLMReviewerFinding(
                    statement="Replay policy for recovery is not fully specified.",
                    evidence_basis=EvidenceBasis.NOT_SPECIFIED,
                    severity_hint=Severity.LOW,
                )
            ],
            recommendations=["Keep failure-injection tests in CI"],
            estimated_impact="Low near-term risk of prolonged service disruption.",
            score_rationale="Reliability controls are mature with small documentation gaps.",
            severity_rationale="Unspecified replay detail has bounded production impact.",
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
            "findings": [],
            "recommendations": [],
            "estimated_impact": "invalid",
            "score_rationale": "invalid",
            "severity_rationale": "invalid",
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
            findings=[
                LLMReviewerFinding(
                    statement="Recovery behavior after provider outages is underspecified",
                    evidence_basis=EvidenceBasis.NOT_SPECIFIED,
                    severity_hint=Severity.MEDIUM,
                )
            ],
            recommendations=["Define replay and restoration procedures"],
            estimated_impact="Longer recovery times after upstream incidents.",
            score_rationale="Ambiguity in recovery path can increase MTTR under incident load.",
            severity_rationale="No confirmed outage mechanism, but impact is operationally meaningful.",
        )

        ReliabilityLLMReviewer(provider).review(self.request)

        provider.generate_structured.assert_called_once()
        kwargs = provider.generate_structured.call_args.kwargs
        self.assertEqual(kwargs["response_model"].__name__, "ReliabilityReviewerLLMResult")
        self.assertIn("single points of failure", kwargs["system_instruction"])
        self.assertIn("theoretically possible failures", kwargs["system_instruction"])
        self.assertIn(
            "Each finding statement must express exactly one evidence_basis",
            kwargs["system_instruction"],
        )


if __name__ == "__main__":
    unittest.main()
