"""Deterministic cost reviewer."""

from app.reviewers.base import BaseReviewer
from app.reviewers.common import ReviewFindings, build_category_review
from app.schemas.review import ArchitectureReviewRequest, CategoryReview
from app.utils.values import is_none_value


class CostReviewer(BaseReviewer):
    """Evaluates spend risk from repeated inference and retrieval paths."""

    @property
    def name(self) -> str:
        return "Cost"

    def review(self, request: ArchitectureReviewRequest) -> CategoryReview:
        findings = ReviewFindings(confidence=95)
        missing_cache = is_none_value(request.cache)
        high_traffic = request.traffic > 10_000
        mid_traffic = request.traffic >= 1_000

        if missing_cache and high_traffic:
            findings.issues.append("High traffic without caching will drive LLM spend.")
            findings.recommendations.append(
                "Cache frequent prompts and retrieval results before peak load."
            )
            findings.penalize(3)
            findings.set_confidence(96)
        elif missing_cache and mid_traffic:
            findings.issues.append("No cache to absorb repeated inference work.")
            findings.recommendations.append("Introduce Redis for hot query reuse.")
            findings.penalize(2)
            findings.set_confidence(94)
        elif missing_cache:
            findings.recommendations.append(
                "Add a cache early to keep unit economics predictable as usage grows."
            )
            findings.penalize(1)

        if high_traffic and not is_none_value(request.llm):
            findings.recommendations.append(
                "Set per-request token budgets and alerting on daily spend."
            )
            findings.penalize(1)
            findings.set_confidence(min(findings.confidence, 91))

        findings.summary = self._build_summary(findings)
        findings.estimated_impact = self._build_impact(
            missing_cache=missing_cache,
            traffic=request.traffic,
            llm=request.llm,
        )
        findings.engineering_reasoning = self._build_reasoning(
            missing_cache=missing_cache,
            request=request,
        )

        return build_category_review(self.name, findings)

    @staticmethod
    def _build_summary(findings: ReviewFindings) -> str:
        if findings.issues:
            return "Cost controls are weak relative to expected model-call volume."
        if findings.recommendations:
            return "Cost posture is acceptable with clear optimization opportunities."
        return "Current stack should keep near-term inference spend manageable."

    @staticmethod
    def _build_impact(*, missing_cache: bool, traffic: int, llm: str) -> str:
        if missing_cache:
            return (
                f"At ~{traffic:,} requests, uncached calls to {llm} and embeddings "
                "compound token and retrieval cost linearly with retries and duplicates."
            )
        return (
            f"Caching dampens repeated work against {llm}; continue tracking "
            "token burn as traffic approaches higher tiers."
        )

    @staticmethod
    def _build_reasoning(*, missing_cache: bool, request: ArchitectureReviewRequest) -> str:
        parts = [
            "Rule-based cost review inspected cache presence, traffic intensity, "
            f"and LLM choice ({request.llm})."
        ]
        if missing_cache:
            parts.append(
                "Missing cache is a primary cost amplifier for AI architectures "
                "because identical prompts and retrievals are recomputed."
            )
        else:
            parts.append(
                f"Cache is configured as '{request.cache}', which reduces duplicate spend."
            )
        return " ".join(parts)
