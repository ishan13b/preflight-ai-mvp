"""Deterministic reliability reviewer."""

from app.reviewers.base import BaseReviewer
from app.reviewers.common import ReviewFindings, build_category_review
from app.schemas.review import ArchitectureReviewRequest, CategoryReview
from app.utils.values import is_none_value


class ReliabilityReviewer(BaseReviewer):
    """Evaluates failure detection and resilience under load."""

    @property
    def name(self) -> str:
        return "Reliability"

    def review(self, request: ArchitectureReviewRequest) -> CategoryReview:
        findings = ReviewFindings(confidence=96)
        missing_monitoring = is_none_value(request.monitoring)
        missing_cache = is_none_value(request.cache)
        high_traffic = request.traffic > 10_000

        if missing_monitoring:
            findings.issues.append("No monitoring to detect partial outages.")
            findings.recommendations.append(
                "Add OpenTelemetry traces and LLM-quality metrics before launch."
            )
            findings.penalize(3)
            findings.set_confidence(96)

        if high_traffic and missing_cache:
            findings.issues.append("Peak traffic can overload uncached dependency paths.")
            findings.recommendations.append(
                "Add retries with jitter and bulkheads around LLM/vector calls."
            )
            findings.penalize(2)
        elif request.traffic >= 1_000:
            findings.recommendations.append(
                "Add retry strategy with timeouts for LLM and vector database calls."
            )
            findings.penalize(1)
            findings.set_confidence(min(findings.confidence, 93))

        findings.summary = self._build_summary(findings)
        findings.estimated_impact = self._build_impact(
            missing_monitoring=missing_monitoring,
            missing_cache=missing_cache,
            traffic=request.traffic,
        )
        findings.engineering_reasoning = self._build_reasoning(
            missing_monitoring=missing_monitoring,
            missing_cache=missing_cache,
            request=request,
        )

        return build_category_review(self.name, findings)

    @staticmethod
    def _build_summary(findings: ReviewFindings) -> str:
        if findings.issues:
            return "Reliability gaps will delay incident detection and recovery."
        if findings.recommendations:
            return "Reliability is workable; resilience patterns should still be formalized."
        return "Operational signals look sufficient for the declared traffic profile."

    @staticmethod
    def _build_impact(
        *,
        missing_monitoring: bool,
        missing_cache: bool,
        traffic: int,
    ) -> str:
        if missing_monitoring and missing_cache:
            return (
                f"At ~{traffic:,} requests, silent failures and retry storms can "
                "compound without visibility or request absorption."
            )
        if missing_monitoring:
            return (
                "Outages and quality regressions will surface through user reports "
                "rather than SLO burn alerts."
            )
        return (
            "Monitoring provides a path to detect failure; continue investing in "
            "timeouts, retries, and degradation modes."
        )

    @staticmethod
    def _build_reasoning(
        *,
        missing_monitoring: bool,
        missing_cache: bool,
        request: ArchitectureReviewRequest,
    ) -> str:
        parts = [
            "Reliability review checked monitoring, caching, and traffic assumptions "
            f"({request.traffic:,} requests)."
        ]
        if missing_monitoring:
            parts.append(
                "Unset monitoring removes the feedback loop needed for graceful failure."
            )
        if missing_cache and request.traffic > 10_000:
            parts.append(
                "High traffic without cache increases cascade risk into LLM/vector backends."
            )
        if not missing_monitoring and not (missing_cache and request.traffic > 10_000):
            parts.append(
                "No critical reliability blockers were triggered by the current rule set."
            )
        return " ".join(parts)
