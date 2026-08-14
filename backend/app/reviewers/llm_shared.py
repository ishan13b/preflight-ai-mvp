"""Shared execution helper for LLM-backed category reviewers."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from app.reviewers.common import derive_severity, derive_vote
from app.schemas.review import ArchitectureReviewRequest, CategoryReview
from app.services.llm.provider import LLMProvider, LLMProviderError

StructuredResultT = TypeVar("StructuredResultT", bound=BaseModel)


def run_llm_category_review(
    *,
    provider: LLMProvider,
    request: ArchitectureReviewRequest,
    category: str,
    confidence: int,
    system_instruction: str,
    response_model: type[StructuredResultT],
) -> CategoryReview:
    """Run a category review through the provider and map it to CategoryReview.

    This helper intentionally handles only shared mechanics:
    - architecture payload serialization
    - provider structured generation call
    - result validation at reviewer boundary
    - deterministic vote derivation from score
    - CategoryReview mapping
    """
    user_input = request.model_dump_json(indent=2)

    try:
        raw_result = provider.generate_structured(
            system_instruction=system_instruction,
            user_input=user_input,
            response_model=response_model,
        )
    except LLMProviderError as exc:
        raise LLMProviderError(f"{category} LLM review failed: {exc}") from exc

    # Re-validate output at reviewer boundary so invalid scores are rejected.
    result = response_model.model_validate(raw_result)

    score = result.score
    risks = list(result.risks)
    severity = derive_severity(score, has_issues=len(risks) > 0)
    deterministic_vote = derive_vote(score)

    return CategoryReview(
        category=category,
        score=score,
        confidence=confidence,
        severity=severity,
        vote=deterministic_vote,
        summary=result.summary,
        issues=risks,
        recommendations=list(result.recommendations),
        estimated_impact=result.estimated_impact,
        engineering_reasoning=result.engineering_reasoning,
    )
