"""Deterministic security reviewer."""

from app.reviewers.base import BaseReviewer
from app.reviewers.common import ReviewFindings, build_category_review
from app.schemas.review import ArchitectureReviewRequest, CategoryReview
from app.utils.values import is_none_value


class SecurityReviewer(BaseReviewer):
    """Evaluates authentication and access-control posture."""

    @property
    def name(self) -> str:
        return "Security"

    def review(self, request: ArchitectureReviewRequest) -> CategoryReview:
        findings = ReviewFindings(confidence=97)
        missing_auth = is_none_value(request.authentication)
        auth = request.authentication.strip().lower()
        weak_auth = auth in {"basic", "none", "password", "shared secret"}

        if missing_auth:
            findings.issues.append("No authentication mechanism configured.")
            findings.recommendations.append(
                "Require JWT or OAuth2/OIDC for all external API access."
            )
            findings.penalize(4)
            findings.set_confidence(96)
        elif weak_auth:
            findings.issues.append("Authentication approach appears weak for production.")
            findings.recommendations.append(
                "Upgrade to JWT or OAuth2/OIDC with short-lived tokens."
            )
            findings.penalize(3)
            findings.set_confidence(90)
        elif auth == "jwt":
            findings.recommendations.append(
                "Confirm JWT signing keys rotate and tokens are audience-scoped."
            )
        elif auth not in {"oauth2", "oauth 2.0", "oidc"}:
            findings.recommendations.append(
                "Document threat model and token lifecycle for the chosen auth scheme."
            )
            findings.penalize(1)
            findings.set_confidence(88)

        findings.summary = self._build_summary(
            missing_auth=missing_auth,
            weak_auth=weak_auth,
            score=findings.score,
        )
        findings.estimated_impact = self._build_impact(
            missing_auth=missing_auth,
            weak_auth=weak_auth,
            application_name=request.application_name,
        )
        findings.engineering_reasoning = self._build_reasoning(
            missing_auth=missing_auth,
            weak_auth=weak_auth,
            request=request,
        )

        return build_category_review(self.name, findings)

    @staticmethod
    def _build_summary(*, missing_auth: bool, weak_auth: bool, score: int) -> str:
        if missing_auth:
            return "Security blockers exist: unauthenticated surfaces are not acceptable."
        if weak_auth:
            return "Authentication is present but insufficient for a production AI API."
        if score >= 9:
            return "Authentication baseline looks appropriate for controlled exposure."
        return "Security is directionally sound with residual hardening recommendations."

    @staticmethod
    def _build_impact(
        *,
        missing_auth: bool,
        weak_auth: bool,
        application_name: str,
    ) -> str:
        if missing_auth:
            return (
                f"Without authentication, {application_name} can be abused for "
                "costly LLM/retrieval traffic and data exposure."
            )
        if weak_auth:
            return (
                "Weak credentials increase account takeover and lateral-abuse risk "
                "against model and vector endpoints."
            )
        return (
            "Authenticated access reduces misuse risk; remaining work is key rotation, "
            "authorization scope, and audit logging."
        )

    @staticmethod
    def _build_reasoning(
        *,
        missing_auth: bool,
        weak_auth: bool,
        request: ArchitectureReviewRequest,
    ) -> str:
        if missing_auth:
            return (
                "Authentication was reported as unset. AI services that front LLMs "
                "and vector indexes must enforce identity before invoking paid inference."
            )
        if weak_auth:
            return (
                f"Authentication is configured as '{request.authentication}', which "
                "is treated as weak for internet-facing AI workloads."
            )
        return (
            f"Authentication is configured as '{request.authentication}'. The board "
            "treats this as an acceptable baseline pending operational hardening."
        )
