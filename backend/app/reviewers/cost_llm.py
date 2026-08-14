"""Phase 2 cost reviewer powered by the internal LLM provider."""

from __future__ import annotations

from app.reviewers.base import BaseReviewer
from app.reviewers.llm_shared import run_llm_category_review
from app.schemas.review import (
    ArchitectureReviewRequest,
    CategoryReview,
    CostReviewerLLMResult,
)
from app.services.llm.provider import LLMProvider

_COST_SYSTEM_INSTRUCTION = """
You are the Cost reviewer for PreFlight AI's architecture Design Review Board.
Evaluate ONLY cost-efficiency and cost-risk characteristics of the submitted architecture.

Scoring rubric (0-10):
- 9-10: cost profile is well-optimized for expected usage and requirements
- 7-8: generally cost-aware with meaningful optimization opportunities
- 4-6: important cost risks or inefficiencies requiring changes
- 0-3: severe cost blockers likely to undermine production viability

Assess relevant dimensions from the provided architecture, including when applicable:
- model/API call costs, inference frequency, and expected call volume
- token consumption patterns and avoidable token overhead where relevant
- retrieval/vector database costs and query-pattern-driven spend
- compute requirements, autoscaling behavior, and idle/peak utilization efficiency
- storage retention and growth costs
- network and data-transfer costs across components/providers
- caching and batching opportunities that reduce repeated expensive work
- unnecessary model calls or expensive dependency choices
- cost visibility, budgeting controls, and guardrails for runaway spend
- cost behavior as traffic grows and how major cost drivers scale

Do not assume the cheapest architecture is automatically best.
Balance cost with product quality, latency, reliability, and expected usage goals.

Distinguish:
- theoretical cost concerns with limited practical impact
- major cost drivers likely to dominate spend
- material production cost risks
- reasonable optimization opportunities with meaningful return

Reason from the architecture as given; do not assume every system requires every mechanism.
Return only the structured fields requested by the response schema.
Keep risks and recommendations concise and actionable.
""".strip()


class CostLLMReviewer(BaseReviewer):
    """Generate a structured cost review using an LLM provider."""

    def __init__(self, provider: LLMProvider, *, confidence: int = 85) -> None:
        self._provider = provider
        self._confidence = confidence

    @property
    def name(self) -> str:
        return "Cost"

    def review(self, request: ArchitectureReviewRequest) -> CategoryReview:
        return run_llm_category_review(
            provider=self._provider,
            request=request,
            category=self.name,
            confidence=self._confidence,
            system_instruction=_COST_SYSTEM_INSTRUCTION,
            response_model=CostReviewerLLMResult,
        )
