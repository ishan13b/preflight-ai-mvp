import unittest
from unittest.mock import Mock

from pydantic import ValidationError

from app.reviewers.observability_llm import ObservabilityLLMReviewer
from app.schemas.review import (
    ArchitectureReviewRequest,
    BoardVote,
    EvidenceBasis,
    LLMReviewerFinding,
    Severity,
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
            findings=[
                LLMReviewerFinding(
                    statement="Cross-service root-cause analysis may be slow during incidents",
                    evidence_basis=EvidenceBasis.INFERRED_RISK,
                    severity_hint=Severity.MEDIUM,
                )
            ],
            recommendations=["Add distributed tracing with shared correlation IDs"],
            estimated_impact="Longer mean time to resolution during production failures.",
            score_rationale="Diagnosis gaps remain despite baseline telemetry coverage.",
            severity_rationale="Impact is meaningful but mitigated by existing metrics/logging.",
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
            findings=[
                LLMReviewerFinding(
                    statement="AI-specific retrieval telemetry coverage is not fully specified.",
                    evidence_basis=EvidenceBasis.NOT_SPECIFIED,
                    severity_hint=Severity.LOW,
                )
            ],
            recommendations=["Continuously tune alert quality and SLO coverage"],
            estimated_impact="Low near-term risk of blind spots during incidents.",
            score_rationale="Core observability controls are strong with minor unspecified depth.",
            severity_rationale="Unspecified telemetry depth appears low risk given compensating controls.",
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
            "findings": [],
            "recommendations": [],
            "estimated_impact": "invalid",
            "score_rationale": "invalid",
            "severity_rationale": "invalid",
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
            findings=[
                LLMReviewerFinding(
                    statement="Noisy telemetry obscures high-priority production signals",
                    evidence_basis=EvidenceBasis.OBSERVED,
                    severity_hint=Severity.MEDIUM,
                )
            ],
            recommendations=["Define high-value alerts and normalize log fields"],
            estimated_impact="Slower incident triage and delayed remediation.",
            score_rationale="Observed alert-noise problem slows diagnosis on critical paths.",
            severity_rationale="Clear operational drag with moderate blast radius.",
        )

        ObservabilityLLMReviewer(provider).review(self.request)

        provider.generate_structured.assert_called_once()
        kwargs = provider.generate_structured.call_args.kwargs
        self.assertEqual(kwargs["response_model"].__name__, "ObservabilityReviewerLLMResult")
        self.assertIn("distributed tracing", kwargs["system_instruction"])
        self.assertIn("noisy or low-value instrumentation", kwargs["system_instruction"])


if __name__ == "__main__":
    unittest.main()
