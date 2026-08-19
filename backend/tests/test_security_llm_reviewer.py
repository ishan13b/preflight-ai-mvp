import unittest
from unittest.mock import Mock

from pydantic import ValidationError

from app.reviewers.security_llm import SecurityLLMReviewer
from app.schemas.review import (
    ArchitectureReviewRequest,
    BoardVote,
    EvidenceBasis,
    LLMReviewerFinding,
    Severity,
    SecurityReviewerLLMResult,
)
from app.services.llm.provider import LLMProvider


class SecurityLLMReviewerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.request = ArchitectureReviewRequest(
            application_name="Customer Support Bot",
            frontend="React",
            backend="FastAPI",
            llm="GPT-5.5",
            vector_db="Pinecone",
            embeddings="BGE Large",
            cache="None",
            monitoring="None",
            authentication="JWT",
            traffic=1000,
        )

    def test_valid_llm_score_maps_to_deterministic_vote(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = SecurityReviewerLLMResult(
            score=8,
            summary="Security posture has concerns.",
            engineering_reasoning="Monitoring and auth hardening are incomplete.",
            findings=[
                LLMReviewerFinding(
                    statement="Weak incident visibility",
                    evidence_basis=EvidenceBasis.OBSERVED,
                    severity_hint=Severity.MEDIUM,
                )
            ],
            recommendations=["Add security telemetry"],
            estimated_impact="Delayed detection and higher abuse risk.",
            score_rationale="One observed visibility gap with moderate operational impact.",
            severity_rationale="Observed detection weakness elevates exploit dwell time.",
        )

        reviewer = SecurityLLMReviewer(provider, confidence=84)
        category = reviewer.review(self.request)

        self.assertEqual(category.category, "Security")
        self.assertEqual(category.score, 8)
        self.assertEqual(category.vote, BoardVote.APPROVED_WITH_CONCERNS)
        self.assertEqual(category.issues, ["Weak incident visibility"])
        self.assertEqual(category.recommendations[0], "Add security telemetry")
        self.assertEqual(category.confidence, 84)

        provider.generate_structured.assert_called_once()
        kwargs = provider.generate_structured.call_args.kwargs
        self.assertEqual(kwargs["response_model"].__name__, "SecurityReviewerLLMResult")
        self.assertIn('"application_name": "Customer Support Bot"', kwargs["user_input"])

    def test_final_vote_is_determined_solely_by_score(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = SecurityReviewerLLMResult(
            score=9,
            summary="Strong posture.",
            engineering_reasoning="Core controls are present.",
            findings=[
                LLMReviewerFinding(
                    statement="Token policy is not specified; validate rotation.",
                    evidence_basis=EvidenceBasis.NOT_SPECIFIED,
                    severity_hint=Severity.LOW,
                )
            ],
            recommendations=["Continue periodic reviews"],
            estimated_impact="Low near-term exploitability risk.",
            score_rationale="Mostly strong posture with only minor unspecified detail.",
            severity_rationale="Unspecified detail is low impact with compensating controls.",
        )

        category = SecurityLLMReviewer(provider).review(self.request)

        self.assertEqual(category.score, 9)
        self.assertEqual(category.vote, BoardVote.APPROVED)

    def test_invalid_score_is_rejected(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = {
            "score": 99,
            "summary": "bad",
            "engineering_reasoning": "bad",
            "findings": [
                {
                    "statement": "risk",
                    "evidence_basis": "OBSERVED",
                    "severity_hint": "MEDIUM",
                }
            ],
            "recommendations": ["fix"],
            "estimated_impact": "impact",
            "score_rationale": "bad",
            "severity_rationale": "bad",
        }

        with self.assertRaises(ValidationError):
            SecurityLLMReviewer(provider).review(self.request)


if __name__ == "__main__":
    unittest.main()
