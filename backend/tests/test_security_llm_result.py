import unittest

from pydantic import ValidationError

from app.schemas.review import SecurityReviewerLLMResult


class SecurityLLMResultValidationTests(unittest.TestCase):
    def test_valid_result_model(self) -> None:
        result = SecurityReviewerLLMResult(
            score=8,
            summary="Security posture is acceptable with risks.",
            engineering_reasoning="JWT is present but monitoring controls are limited.",
            risks=["Insufficient incident tracing"],
            recommendations=["Add security event monitoring"],
            estimated_impact="Incidents may take longer to detect and contain.",
        )

        self.assertEqual(result.score, 8)

    def test_invalid_score_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            SecurityReviewerLLMResult(
                score=99,
                summary="bad",
                engineering_reasoning="bad",
                risks=["risk"],
                recommendations=["fix"],
                estimated_impact="impact",
            )


if __name__ == "__main__":
    unittest.main()
