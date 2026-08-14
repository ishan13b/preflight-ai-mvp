"""Phase 2 security reviewer powered by the internal LLM provider."""

from __future__ import annotations

from app.reviewers.base import BaseReviewer
from app.reviewers.llm_shared import run_llm_category_review
from app.schemas.review import (
    ArchitectureReviewRequest,
    CategoryReview,
    SecurityReviewerLLMResult,
)
from app.services.llm.provider import LLMProvider

_SECURITY_SYSTEM_INSTRUCTION = """
You are the Security reviewer for PreFlight AI's architecture Design Review Board.
Evaluate ONLY security posture of the submitted architecture.

Scoring rubric (0-10):
- 9-10: strong production-ready controls
- 7-8: acceptable but with clear concerns
- 4-6: meaningful gaps requiring changes
- 0-3: critical blockers

Focus on:
- authentication and authorization posture
- exposure/abuse risk of AI endpoints
- secrets and key-handling risk in architecture choices
- security monitoring and incident response readiness

Return only the structured fields requested by the response schema.
Keep risks and recommendations concise and actionable.
""".strip()


class SecurityLLMReviewer(BaseReviewer):
    """Generate a structured security review using an LLM provider."""

    def __init__(self, provider: LLMProvider, *, confidence: int = 85) -> None:
        self._provider = provider
        self._confidence = confidence

    @property
    def name(self) -> str:
        return "Security"

    def review(self, request: ArchitectureReviewRequest) -> CategoryReview:
        return run_llm_category_review(
            provider=self._provider,
            request=request,
            category=self.name,
            confidence=self._confidence,
            system_instruction=_SECURITY_SYSTEM_INSTRUCTION,
            response_model=SecurityReviewerLLMResult,
        )
