import threading
import unittest
from unittest.mock import Mock

from app.reviewers.base import BaseReviewer
from app.schemas.orchestration import (
    LLMReviewOrchestrationResult,
    OrchestrationStatus,
    ReviewerExecutionStatus,
)
from app.schemas.review import (
    ArchitectureReviewRequest,
    BoardVote,
    CategoryReview,
    Severity,
)
from app.services.llm.provider import LLMProvider
from app.services.review_orchestrator import LLMReviewOrchestrator


def _category_review(category: str, score: int = 8) -> CategoryReview:
    return CategoryReview(
        category=category,
        score=score,
        confidence=85,
        severity=Severity.MEDIUM,
        vote=BoardVote.APPROVED_WITH_CONCERNS if score < 9 else BoardVote.APPROVED,
        summary=f"{category} summary",
        issues=[],
        recommendations=[f"{category} recommendation"],
        estimated_impact=f"{category} impact",
        engineering_reasoning=f"{category} reasoning",
    )


class _SuccessReviewer(BaseReviewer):
    def __init__(self, category: str, score: int = 8) -> None:
        self._category = category
        self._score = score

    @property
    def name(self) -> str:
        return self._category

    def review(self, request: ArchitectureReviewRequest) -> CategoryReview:
        return _category_review(self._category, score=self._score)


class _FailingReviewer(BaseReviewer):
    def __init__(self, category: str, error_message: str) -> None:
        self._category = category
        self._error_message = error_message

    @property
    def name(self) -> str:
        return self._category

    def review(self, request: ArchitectureReviewRequest) -> CategoryReview:
        raise RuntimeError(self._error_message)


class _GateReviewer(BaseReviewer):
    def __init__(
        self,
        category: str,
        *,
        started_counter: dict[str, int],
        counter_lock: threading.Lock,
        all_started_event: threading.Event,
        release_event: threading.Event,
        total_reviewers: int,
    ) -> None:
        self._category = category
        self._started_counter = started_counter
        self._counter_lock = counter_lock
        self._all_started_event = all_started_event
        self._release_event = release_event
        self._total_reviewers = total_reviewers

    @property
    def name(self) -> str:
        return self._category

    def review(self, request: ArchitectureReviewRequest) -> CategoryReview:
        with self._counter_lock:
            self._started_counter["count"] += 1
            if self._started_counter["count"] == self._total_reviewers:
                self._all_started_event.set()

        released = self._release_event.wait(timeout=2.0)
        if not released:
            raise RuntimeError("release gate not opened")

        return _category_review(self._category, score=8)


class LLMReviewOrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.request = ArchitectureReviewRequest(
            application_name="Customer Support Bot",
            frontend="React",
            backend="FastAPI",
            llm="GPT-5.5",
            vector_db="Pinecone",
            embeddings="BGE Large",
            cache="Redis",
            monitoring="Datadog",
            authentication="JWT",
            traffic=30000,
        )

    def test_all_five_reviewers_succeed(self) -> None:
        reviewers = [
            _SuccessReviewer("Security"),
            _SuccessReviewer("Scalability"),
            _SuccessReviewer("Reliability"),
            _SuccessReviewer("Observability"),
            _SuccessReviewer("Cost"),
        ]

        result = LLMReviewOrchestrator(reviewers).review(self.request)

        self.assertEqual(result.status, OrchestrationStatus.COMPLETE)
        self.assertTrue(result.is_complete)
        self.assertEqual(result.total_reviewers, 5)
        self.assertEqual(result.successful_reviewers, 5)
        self.assertEqual(result.failed_reviewers, 0)
        self.assertTrue(
            all(
                item.status == ReviewerExecutionStatus.SUCCESS
                for item in result.reviewer_results
            )
        )

    def test_one_reviewer_failure_is_isolated(self) -> None:
        reviewers = [
            _SuccessReviewer("Security"),
            _SuccessReviewer("Scalability"),
            _FailingReviewer("Reliability", "provider timeout"),
            _SuccessReviewer("Observability"),
            _SuccessReviewer("Cost"),
        ]

        result = LLMReviewOrchestrator(reviewers).review(self.request)

        self.assertEqual(result.status, OrchestrationStatus.PARTIAL)
        self.assertFalse(result.is_complete)
        self.assertEqual(result.successful_reviewers, 4)
        self.assertEqual(result.failed_reviewers, 1)

        failure = next(
            item
            for item in result.reviewer_results
            if item.status == ReviewerExecutionStatus.FAILED
        )
        self.assertEqual(failure.category, "Reliability")
        self.assertEqual(failure.error_type, "RuntimeError")
        self.assertIn("provider timeout", failure.error_message)

    def test_multiple_reviewer_failures_are_isolated(self) -> None:
        reviewers = [
            _FailingReviewer("Security", "provider failed"),
            _SuccessReviewer("Scalability"),
            _FailingReviewer("Reliability", "timeout"),
            _SuccessReviewer("Observability"),
            _SuccessReviewer("Cost"),
        ]

        result = LLMReviewOrchestrator(reviewers).review(self.request)

        self.assertEqual(result.status, OrchestrationStatus.PARTIAL)
        self.assertEqual(result.successful_reviewers, 3)
        self.assertEqual(result.failed_reviewers, 2)

        failed_categories = {
            item.category
            for item in result.reviewer_results
            if item.status == ReviewerExecutionStatus.FAILED
        }
        self.assertEqual(failed_categories, {"Security", "Reliability"})

    def test_all_reviewers_failing_returns_failed_status(self) -> None:
        reviewers = [
            _FailingReviewer("Security", "provider failed"),
            _FailingReviewer("Scalability", "provider failed"),
            _FailingReviewer("Reliability", "provider failed"),
            _FailingReviewer("Observability", "provider failed"),
            _FailingReviewer("Cost", "provider failed"),
        ]

        result = LLMReviewOrchestrator(reviewers).review(self.request)

        self.assertEqual(result.status, OrchestrationStatus.FAILED)
        self.assertFalse(result.is_complete)
        self.assertEqual(result.successful_reviewers, 0)
        self.assertEqual(result.failed_reviewers, 5)

    def test_results_retain_category_identity(self) -> None:
        reviewers = [
            _SuccessReviewer("Security"),
            _SuccessReviewer("Scalability"),
            _SuccessReviewer("Reliability"),
            _SuccessReviewer("Observability"),
            _SuccessReviewer("Cost"),
        ]

        result = LLMReviewOrchestrator(reviewers).review(self.request)
        categories = [item.category for item in result.reviewer_results]

        self.assertEqual(
            categories,
            ["Security", "Scalability", "Reliability", "Observability", "Cost"],
        )

    def test_reviewers_execute_concurrently(self) -> None:
        all_started_event = threading.Event()
        release_event = threading.Event()
        counter_lock = threading.Lock()
        started_counter = {"count": 0}
        categories = ["Security", "Scalability", "Reliability", "Observability", "Cost"]

        reviewers = [
            _GateReviewer(
                category,
                started_counter=started_counter,
                counter_lock=counter_lock,
                all_started_event=all_started_event,
                release_event=release_event,
                total_reviewers=len(categories),
            )
            for category in categories
        ]

        orchestrator = LLMReviewOrchestrator(reviewers)
        holder: dict[str, object] = {}

        def _run_orchestration() -> None:
            holder["result"] = orchestrator.review(self.request)

        orchestration_thread = threading.Thread(target=_run_orchestration)
        orchestration_thread.start()

        self.assertTrue(
            all_started_event.wait(timeout=1.5),
            "Expected all reviewers to start before release, indicating concurrency.",
        )

        release_event.set()
        orchestration_thread.join(timeout=2.0)
        self.assertFalse(orchestration_thread.is_alive())

        result = holder["result"]
        self.assertIsInstance(result, LLMReviewOrchestrationResult)
        self.assertEqual(result.successful_reviewers, 5)

    def test_from_provider_runs_all_five_llm_reviewers_without_real_api_calls(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = {
            "score": 8,
            "summary": "Valid result",
            "engineering_reasoning": "Valid reasoning",
            "risks": [],
            "recommendations": ["Valid recommendation"],
            "estimated_impact": "Valid impact",
        }

        orchestrator = LLMReviewOrchestrator.from_provider(provider)
        result = orchestrator.review(self.request)

        self.assertEqual(result.total_reviewers, 5)
        self.assertEqual(result.successful_reviewers, 5)
        self.assertEqual(result.failed_reviewers, 0)
        self.assertEqual(provider.generate_structured.call_count, 5)


if __name__ == "__main__":
    unittest.main()
