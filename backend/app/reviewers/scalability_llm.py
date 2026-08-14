"""Phase 2 scalability reviewer powered by the internal LLM provider."""

from __future__ import annotations

from app.reviewers.base import BaseReviewer
from app.reviewers.llm_shared import run_llm_category_review
from app.schemas.review import (
    ArchitectureReviewRequest,
    CategoryReview,
    ScalabilityReviewerLLMResult,
)
from app.services.llm.provider import LLMProvider

_SCALABILITY_SYSTEM_INSTRUCTION = """
You are the Scalability reviewer for PreFlight AI's architecture Design Review Board.
Evaluate ONLY scalability characteristics of the submitted architecture.

Scoring rubric (0-10):
- 9-10: strong headroom and resilient scaling strategy under higher load
- 7-8: generally scalable with meaningful concerns to address
- 4-6: important scaling gaps requiring changes before growth
- 0-3: severe scalability blockers

Assess relevant dimensions from the provided architecture, including when applicable:
- traffic profile, concurrency, and throughput/latency under load
- horizontal and vertical scaling strategy, including bottlenecks
- state management, queueing, and backpressure behavior
- model inference capacity and saturation risk
- retrieval/vector database and cache scaling characteristics
- behavior under increased load and likely degradation modes

Reason from the architecture as given; do not assume every system requires every mechanism.
Return only the structured fields requested by the response schema.
Keep risks and recommendations concise and actionable.
""".strip()


class ScalabilityLLMReviewer(BaseReviewer):
    """Generate a structured scalability review using an LLM provider."""

    def __init__(self, provider: LLMProvider, *, confidence: int = 85) -> None:
        self._provider = provider
        self._confidence = confidence

    @property
    def name(self) -> str:
        return "Scalability"

    def review(self, request: ArchitectureReviewRequest) -> CategoryReview:
        return run_llm_category_review(
            provider=self._provider,
            request=request,
            category=self.name,
            confidence=self._confidence,
            system_instruction=_SCALABILITY_SYSTEM_INSTRUCTION,
            response_model=ScalabilityReviewerLLMResult,
        )
