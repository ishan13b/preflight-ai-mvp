import unittest

from pydantic import ValidationError

from app.schemas.review import (
    EvidenceBasis,
    LLMReviewerFinding,
    SecurityReviewerLLMResult,
    Severity,
)


class SecurityLLMResultValidationTests(unittest.TestCase):
    def test_valid_result_model(self) -> None:
        result = SecurityReviewerLLMResult(
            score=8,
            summary="Security posture is acceptable with risks.",
            engineering_reasoning="JWT is present but monitoring controls are limited.",
            findings=[
                LLMReviewerFinding(
                    statement="Insufficient incident tracing",
                    evidence_basis=EvidenceBasis.OBSERVED,
                    severity_hint=Severity.MEDIUM,
                )
            ],
            recommendations=["Add security event monitoring"],
            estimated_impact="Incidents may take longer to detect and contain.",
            score_rationale="Observed traceability gap with bounded impact.",
            severity_rationale="Likely slower detection but manageable blast radius.",
        )

        self.assertEqual(result.score, 8)

    def test_invalid_score_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            SecurityReviewerLLMResult(
                score=99,
                summary="bad",
                engineering_reasoning="bad",
                findings=[
                    LLMReviewerFinding(
                        statement="risk",
                        evidence_basis=EvidenceBasis.INFERRED_RISK,
                        severity_hint=Severity.HIGH,
                    )
                ],
                recommendations=["fix"],
                estimated_impact="impact",
                score_rationale="bad",
                severity_rationale="bad",
            )


if __name__ == "__main__":
    unittest.main()
