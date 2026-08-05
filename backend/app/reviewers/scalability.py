"""Deterministic scalability reviewer."""

from app.reviewers.base import BaseReviewer
from app.reviewers.common import ReviewFindings, build_category_review
from app.schemas.review import ArchitectureReviewRequest, CategoryReview
from app.utils.values import is_none_value


class ScalabilityReviewer(BaseReviewer):
    """Evaluates caching and traffic-handling characteristics."""

    @property
    def name(self) -> str:
        return "Scalability"

    def review(self, request: ArchitectureReviewRequest) -> CategoryReview:
        findings = ReviewFindings(confidence=97)
        missing_cache = is_none_value(request.cache)
        high_traffic_fastapi = (
            request.traffic > 10_000
            and request.backend.strip().lower() == "fastapi"
        )

        if missing_cache:
            findings.issues.append("No caching layer detected.")
            findings.recommendations.append("Consider Redis for repeated requests.")
            findings.penalize(2)
            findings.set_confidence(96)

        if high_traffic_fastapi:
            findings.recommendations.append("Evaluate horizontal scaling.")
            findings.penalize(1)
            findings.set_confidence(min(findings.confidence, 92))

        findings.summary = self._build_summary(findings)
        findings.estimated_impact = self._build_impact(
            missing_cache=missing_cache,
            high_traffic_fastapi=high_traffic_fastapi,
            traffic=request.traffic,
        )
        findings.engineering_reasoning = self._build_reasoning(
            missing_cache=missing_cache,
            high_traffic_fastapi=high_traffic_fastapi,
            request=request,
        )

        return build_category_review(self.name, findings)

    @staticmethod
    def _build_summary(findings: ReviewFindings) -> str:
        if not findings.issues and not findings.recommendations:
            return "Architecture appears adequately prepared for expected load."
        if findings.issues and findings.recommendations:
            return (
                "Scalability gaps were found; address caching and capacity "
                "before production traffic increases."
            )
        if findings.issues:
            return "Scalability issues detected that may limit throughput under load."
        return "No critical issues found; consider the capacity recommendations below."

    @staticmethod
    def _build_impact(
        *,
        missing_cache: bool,
        high_traffic_fastapi: bool,
        traffic: int,
    ) -> str:
        if missing_cache and high_traffic_fastapi:
            return (
                f"At ~{traffic:,} requests, repeated LLM/retrieval work without a cache "
                "will inflate latency and cost while a single FastAPI instance becomes "
                "a saturation point."
            )
        if missing_cache:
            return (
                "Repeated identical prompts and retrievals will recompute work, "
                "increasing p95 latency and token spend as traffic grows."
            )
        if high_traffic_fastapi:
            return (
                f"Traffic above 10,000 ({traffic:,}) on a single FastAPI deployment "
                "risks connection and CPU saturation without horizontal scale-out."
            )
        return (
            "Current scalability posture should absorb near-term load with limited "
            "operational risk."
        )

    @staticmethod
    def _build_reasoning(
        *,
        missing_cache: bool,
        high_traffic_fastapi: bool,
        request: ArchitectureReviewRequest,
    ) -> str:
        parts = [
            "Rule-based evaluation inspected cache configuration and "
            f"reported traffic ({request.traffic:,}) against the backend "
            f"({request.backend})."
        ]
        if missing_cache:
            parts.append(
                "Absence of a cache is a deterministic finding: AI paths that "
                "re-embed or re-query the same context benefit from a shared "
                "cache such as Redis."
            )
        if high_traffic_fastapi:
            parts.append(
                "Traffic exceeds the 10,000 threshold with FastAPI, so process "
                "isolation and replica count should be planned before peak load."
            )
        if not missing_cache and not high_traffic_fastapi:
            parts.append(
                "No caching gap or high-traffic FastAPI threshold was triggered."
            )
        return " ".join(parts)
