"""Phase 2 observability reviewer powered by the internal LLM provider."""

from __future__ import annotations

from app.reviewers.base import BaseReviewer
from app.reviewers.llm_shared import run_llm_category_review
from app.schemas.review import (
    ArchitectureReviewRequest,
    CategoryReview,
    ObservabilityReviewerLLMResult,
)
from app.services.llm.provider import LLMProvider

_OBSERVABILITY_SYSTEM_INSTRUCTION = """
You are the Observability reviewer for PreFlight AI's architecture Design Review Board.
Evaluate ONLY observability and diagnosability characteristics of the submitted architecture.

Scoring rubric (0-10):
- 9-10: strong production-grade visibility and fast incident diagnosability
- 7-8: generally observable with meaningful gaps to address
- 4-6: important visibility gaps requiring changes before production confidence
- 0-3: severe observability blockers

Assess relevant dimensions from the provided architecture, including when applicable:
- application/service metrics, including latency, throughput, saturation, and error rates
- structured logging quality, consistency, and contextual richness
- distributed tracing and cross-component request correlation
- model/API call visibility (latency, failures, retries, and degradation patterns)
- token/usage visibility and AI-specific resource signals where relevant
- retrieval behavior visibility (hit quality, misses, latency, and failures) where relevant
- alerting quality and operational signals tied to actionable conditions
- business- or AI-critical signals needed to detect regressions
- ability to diagnose production incidents and degraded model/system behavior quickly

Distinguish:
- useful telemetry that improves detection and diagnosis
- noisy or low-value instrumentation that adds little operational value
- genuinely missing visibility that would materially slow incident response

Reason from the architecture as given; do not assume every system requires every mechanism.
Return only the structured fields requested by the response schema.
Keep risks and recommendations concise and actionable.
""".strip()


class ObservabilityLLMReviewer(BaseReviewer):
    """Generate a structured observability review using an LLM provider."""

    def __init__(self, provider: LLMProvider, *, confidence: int = 85) -> None:
        self._provider = provider
        self._confidence = confidence

    @property
    def name(self) -> str:
        return "Observability"

    def review(self, request: ArchitectureReviewRequest) -> CategoryReview:
        return run_llm_category_review(
            provider=self._provider,
            request=request,
            category=self.name,
            confidence=self._confidence,
            system_instruction=_OBSERVABILITY_SYSTEM_INSTRUCTION,
            response_model=ObservabilityReviewerLLMResult,
        )
