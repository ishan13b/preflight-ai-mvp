"""Phase 2 reliability reviewer powered by the internal LLM provider."""

from __future__ import annotations

from app.reviewers.base import BaseReviewer
from app.reviewers.llm_shared import run_llm_category_review
from app.schemas.review import (
    ArchitectureReviewRequest,
    CategoryReview,
    ReliabilityReviewerLLMResult,
)
from app.services.llm.provider import LLMProvider

_RELIABILITY_SYSTEM_INSTRUCTION = """
You are the Reliability reviewer for PreFlight AI's architecture Design Review Board.
Evaluate ONLY reliability characteristics of the submitted architecture.

Scoring rubric (0-10):
- 9-10: strong operational resilience with robust failure handling
- 7-8: generally reliable with meaningful concerns to address
- 4-6: important reliability gaps requiring changes before production
- 0-3: severe reliability blockers

Assess relevant dimensions from the provided architecture, including when applicable:
- single points of failure and dependency failure modes
- timeout, retry, and fallback behavior across critical paths
- graceful degradation and blast-radius containment under partial outages
- idempotency and duplicate-work safety for retries and async processing
- circuit breaking, backoff, and overload protection behavior
- queue durability, ordering/at-least-once implications, and recovery paths
- model/provider failures and retrieval/data dependency failures
- recovery behavior: restart/replay, state consistency, and service restoration

Distinguish:
- theoretically possible failures that are unlikely or low-impact
- meaningful production risks with realistic trigger conditions
- missing mitigations that materially reduce reliability

Reason from the architecture as given; do not assume every system requires every mechanism.
Return only the structured fields requested by the response schema.
Keep risks and recommendations concise and actionable.
""".strip()


class ReliabilityLLMReviewer(BaseReviewer):
    """Generate a structured reliability review using an LLM provider."""

    def __init__(self, provider: LLMProvider, *, confidence: int = 85) -> None:
        self._provider = provider
        self._confidence = confidence

    @property
    def name(self) -> str:
        return "Reliability"

    def review(self, request: ArchitectureReviewRequest) -> CategoryReview:
        return run_llm_category_review(
            provider=self._provider,
            request=request,
            category=self.name,
            confidence=self._confidence,
            system_instruction=_RELIABILITY_SYSTEM_INSTRUCTION,
            response_model=ReliabilityReviewerLLMResult,
        )
