import unittest
from unittest.mock import Mock

from pydantic import ValidationError

from app.reviewers.llm_shared import run_llm_category_review
from app.schemas.review import (
    ArchitectureReviewRequest,
    BoardVote,
    SecurityReviewerLLMResult,
)
from app.services.llm.provider import LLMProvider, LLMProviderError


class LLMReviewerSharedExecutionTests(unittest.TestCase):
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

    def test_maps_structured_result_and_derives_vote(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = SecurityReviewerLLMResult(
            score=7,
            summary="Moderate security concerns.",
            engineering_reasoning="Auth exists but monitoring coverage is partial.",
            risks=["Partial coverage for incident telemetry"],
            recommendations=["Add end-to-end security traces"],
            estimated_impact="Slower incident triage under active abuse.",
        )

        category = run_llm_category_review(
            provider=provider,
            request=self.request,
            category="Security",
            confidence=85,
            system_instruction="security rubric",
            response_model=SecurityReviewerLLMResult,
        )

        self.assertEqual(category.score, 7)
        self.assertEqual(category.vote, BoardVote.APPROVED_WITH_CONCERNS)
        self.assertEqual(category.issues, ["Partial coverage for incident telemetry"])

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
            run_llm_category_review(
                provider=provider,
                request=self.request,
                category="Security",
                confidence=85,
                system_instruction="security rubric",
                response_model=SecurityReviewerLLMResult,
            )

    def test_provider_errors_are_wrapped_with_category_context(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.side_effect = LLMProviderError("provider failed")

        with self.assertRaises(LLMProviderError) as ctx:
            run_llm_category_review(
                provider=provider,
                request=self.request,
                category="Security",
                confidence=85,
                system_instruction="security rubric",
                response_model=SecurityReviewerLLMResult,
            )

        self.assertIn("Security LLM review failed", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
