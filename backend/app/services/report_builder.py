"""Assemble executive-level report sections from architecture inputs."""

from app.schemas.review import ArchitectureReviewRequest, CategoryReview
from app.utils.values import is_none_value


KNOWN_MODERN_BACKENDS = {"fastapi", "nestjs", "spring boot", "go", "gin", "echo"}
KNOWN_VECTOR_DBS = {
    "pinecone",
    "weaviate",
    "qdrant",
    "milvus",
    "chroma",
    "pgvector",
    "elasticsearch",
}


def compute_overall_score(request: ArchitectureReviewRequest) -> int:
    score = 100
    if is_none_value(request.cache):
        score -= 10
    if is_none_value(request.monitoring):
        score -= 15
    return max(0, min(100, score))


def derive_overall_status(overall_score: int) -> str:
    if overall_score >= 90:
        return "Production Ready"
    if overall_score >= 75:
        return "Needs Hardening"
    if overall_score >= 60:
        return "Significant Gaps"
    return "High Risk"


def collect_strengths(request: ArchitectureReviewRequest) -> list[str]:
    """Surface notable architecture choices suitable for an executive summary."""
    strengths: list[str] = []

    if request.backend.strip().lower() in KNOWN_MODERN_BACKENDS:
        strengths.append("Modern backend")

    if request.vector_db.strip().lower() in KNOWN_VECTOR_DBS:
        strengths.append("Good vector database")

    auth = request.authentication.strip().lower()
    if auth == "jwt":
        strengths.append("JWT authentication")
    elif auth in {"oauth2", "oauth 2.0", "oidc"}:
        strengths.append("Strong authentication")

    if not is_none_value(request.cache):
        strengths.append(f"Caching layer present ({request.cache})")

    if not is_none_value(request.monitoring):
        strengths.append(f"Monitoring configured ({request.monitoring})")

    return strengths


def collect_critical_risks(
    request: ArchitectureReviewRequest,
    categories: list[CategoryReview],
) -> list[str]:
    risks: list[str] = []

    if is_none_value(request.monitoring):
        risks.append("No monitoring")
    if is_none_value(request.cache):
        risks.append("No cache")

    for category in categories:
        if category.severity.value in {"CRITICAL", "HIGH"}:
            for issue in category.issues:
                label = _short_risk_label(issue)
                if label not in risks:
                    risks.append(label)

    return risks


def collect_quick_wins(request: ArchitectureReviewRequest) -> list[str]:
    wins: list[str] = []

    if is_none_value(request.cache):
        wins.append("Add Redis cache")
    if is_none_value(request.monitoring):
        wins.append("Add Langfuse")

    needs_resilience = (
        is_none_value(request.cache)
        or is_none_value(request.monitoring)
        or request.traffic >= 1_000
    )
    if needs_resilience and not is_none_value(request.llm):
        wins.append("Add retry strategy")

    if request.traffic > 10_000 and request.backend.strip().lower() == "fastapi":
        wins.append("Plan horizontal scaling")

    deduped: list[str] = []
    for item in wins:
        if item not in deduped:
            deduped.append(item)
    return deduped


def build_overall_summary(
    *,
    request: ArchitectureReviewRequest,
    overall_score: int,
    overall_status: str,
    strengths: list[str],
    critical_risks: list[str],
) -> str:
    strength_count = len(strengths)
    risk_count = len(critical_risks)

    if risk_count == 0:
        return (
            f"{request.application_name} scores {overall_score}/100 ({overall_status}). "
            f"{strength_count} strength{'s' if strength_count != 1 else ''} were identified "
            "and no critical operational gaps were flagged by the current rule set."
        )

    return (
        f"{request.application_name} scores {overall_score}/100 ({overall_status}). "
        f"The review found {strength_count} strength{'s' if strength_count != 1 else ''} "
        f"and {risk_count} critical risk{'s' if risk_count != 1 else ''} that should be "
        "addressed before broader production exposure."
    )


def _short_risk_label(issue: str) -> str:
    normalized = issue.strip().rstrip(".")
    mapping = {
        "No caching layer detected": "No cache",
        "No monitoring or tracing configured": "No monitoring",
    }
    return mapping.get(normalized, normalized)
