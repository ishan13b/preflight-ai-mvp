"""Phase 2 orchestrator for concurrent LLM reviewer execution."""

from __future__ import annotations

import re
from concurrent.futures import Future, ThreadPoolExecutor, as_completed

from app.reviewers.base import BaseReviewer
from app.reviewers.cost_llm import CostLLMReviewer
from app.reviewers.observability_llm import ObservabilityLLMReviewer
from app.reviewers.reliability_llm import ReliabilityLLMReviewer
from app.reviewers.scalability_llm import ScalabilityLLMReviewer
from app.reviewers.security_llm import SecurityLLMReviewer
from app.schemas.orchestration import (
    LLMReviewOrchestrationResult,
    OrchestrationStatus,
    ReviewerExecutionResult,
    ReviewerFailureResult,
    ReviewerSuccessResult,
)
from app.schemas.review import ArchitectureReviewRequest
from app.services.llm.provider import LLMProvider


class LLMReviewOrchestrator:
    """Run LLM reviewers concurrently and normalize success/failure outcomes."""

    def __init__(self, reviewers: list[BaseReviewer]) -> None:
        self._reviewers = list(reviewers)

    @classmethod
    def from_provider(cls, provider: LLMProvider) -> LLMReviewOrchestrator:
        """Build the orchestrator with the five specialized LLM reviewers."""
        return cls(
            reviewers=[
                SecurityLLMReviewer(provider),
                ScalabilityLLMReviewer(provider),
                ReliabilityLLMReviewer(provider),
                ObservabilityLLMReviewer(provider),
                CostLLMReviewer(provider),
            ]
        )

    def review(self, request: ArchitectureReviewRequest) -> LLMReviewOrchestrationResult:
        if not self._reviewers:
            return LLMReviewOrchestrationResult(
                status=OrchestrationStatus.COMPLETE,
                is_complete=True,
                total_reviewers=0,
                successful_reviewers=0,
                failed_reviewers=0,
                reviewer_results=[],
            )

        ordered_results: list[ReviewerExecutionResult | None] = [None] * len(
            self._reviewers
        )

        with ThreadPoolExecutor(max_workers=len(self._reviewers)) as executor:
            futures: dict[Future[ReviewerExecutionResult], int] = {
                executor.submit(self._run_reviewer, reviewer, request): index
                for index, reviewer in enumerate(self._reviewers)
            }

            for future in as_completed(futures):
                index = futures[future]
                ordered_results[index] = future.result()

        reviewer_results = [result for result in ordered_results if result is not None]
        successful = sum(isinstance(result, ReviewerSuccessResult) for result in reviewer_results)
        failed = len(reviewer_results) - successful

        if failed == 0:
            status = OrchestrationStatus.COMPLETE
            is_complete = True
        elif successful == 0:
            status = OrchestrationStatus.FAILED
            is_complete = False
        else:
            status = OrchestrationStatus.PARTIAL
            is_complete = False

        return LLMReviewOrchestrationResult(
            status=status,
            is_complete=is_complete,
            total_reviewers=len(self._reviewers),
            successful_reviewers=successful,
            failed_reviewers=failed,
            reviewer_results=reviewer_results,
        )

    def _run_reviewer(
        self,
        reviewer: BaseReviewer,
        request: ArchitectureReviewRequest,
    ) -> ReviewerExecutionResult:
        category = reviewer.name
        try:
            review = reviewer.review(request)
            return ReviewerSuccessResult(category=category, review=review)
        except Exception as exc:  # noqa: BLE001 - orchestrator must isolate all failures.
            return ReviewerFailureResult(
                category=category,
                error_type=type(exc).__name__,
                error_message=self._sanitize_error_message(str(exc)),
            )

    @staticmethod
    def _sanitize_error_message(raw_message: str) -> str:
        message = raw_message.strip() or "Reviewer execution failed."

        # Redact potential key/token patterns from error text.
        message = re.sub(r"sk-[A-Za-z0-9\-_]+", "[REDACTED_KEY]", message)
        message = re.sub(
            r"(?i)(api[_-]?key\s*[:=]\s*)(\S+)",
            r"\1[REDACTED]",
            message,
        )
        message = re.sub(
            r"(?i)(authorization\s*[:=]\s*bearer\s+)(\S+)",
            r"\1[REDACTED]",
            message,
        )

        if len(message) > 400:
            return f"{message[:397]}..."
        return message
