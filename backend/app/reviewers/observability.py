"""Deterministic observability reviewer."""

from app.reviewers.base import BaseReviewer
from app.reviewers.common import ReviewFindings, build_category_review
from app.schemas.review import ArchitectureReviewRequest, CategoryReview
from app.utils.values import is_none_value


class ObservabilityReviewer(BaseReviewer):
    """Evaluates monitoring and tracing readiness."""

    @property
    def name(self) -> str:
        return "Observability"

    def review(self, request: ArchitectureReviewRequest) -> CategoryReview:
        findings = ReviewFindings(confidence=98)
        missing_monitoring = is_none_value(request.monitoring)

        if missing_monitoring:
            findings.issues.append("No monitoring or tracing configured.")
            findings.recommendations.append("Add Langfuse or OpenTelemetry.")
            findings.penalize(3)
            findings.set_confidence(96)

        findings.summary = self._build_summary(missing_monitoring=missing_monitoring)
        findings.estimated_impact = self._build_impact(
            missing_monitoring=missing_monitoring,
            application_name=request.application_name,
        )
        findings.engineering_reasoning = self._build_reasoning(
            missing_monitoring=missing_monitoring,
            request=request,
        )

        return build_category_review(self.name, findings)

    @staticmethod
    def _build_summary(*, missing_monitoring: bool) -> str:
        if missing_monitoring:
            return (
                "Observability is insufficient for production AI systems; "
                "instrumentation should be added."
            )
        return "Monitoring configuration looks present for operational visibility."

    @staticmethod
    def _build_impact(*, missing_monitoring: bool, application_name: str) -> str:
        if missing_monitoring:
            return (
                f"Without traces or LLM analytics for {application_name}, "
                "regressions in latency, cost, and answer quality will be detected "
                "late—usually by users rather than operators."
            )
        return (
            "Existing monitoring should support incident response and quality "
            "debugging once dashboards and alerts are wired to key paths."
        )

    @staticmethod
    def _build_reasoning(
        *,
        missing_monitoring: bool,
        request: ArchitectureReviewRequest,
    ) -> str:
        if missing_monitoring:
            return (
                "Monitoring was reported as unset. Production AI stacks need "
                "request tracing and prompt/completion telemetry (for example "
                "OpenTelemetry spans plus Langfuse or equivalent) to diagnose "
                f"failures in retrieval and generation for {request.llm}."
            )
        return (
            f"Monitoring is configured as '{request.monitoring}'. Treat this as a "
            "foundation and ensure traces cover embedding, retrieval, and LLM call "
            "boundaries."
        )
