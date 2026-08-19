"""Architecture review request and response schemas."""

from enum import StrEnum
import re

from pydantic import (
    BaseModel,
    Field,
    PrivateAttr,
    ValidationInfo,
    field_validator,
    model_validator,
)


class Severity(StrEnum):
    """Consulting-style severity bands for category findings."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EvidenceBasis(StrEnum):
    """Evidence discipline marker for LLM reviewer findings."""

    OBSERVED = "OBSERVED"
    NOT_SPECIFIED = "NOT_SPECIFIED"
    INFERRED_RISK = "INFERRED_RISK"


class BoardVote(StrEnum):
    """Deterministic vote cast by a review-board member."""

    APPROVED = "APPROVED"
    APPROVED_WITH_CONCERNS = "APPROVED WITH CONCERNS"
    REQUIRES_CHANGES = "REQUIRES CHANGES"


class ArchitectureReviewRequest(BaseModel):
    """Inbound architecture description for deterministic review."""

    application_name: str = Field(min_length=1, max_length=200)
    frontend: str = Field(min_length=1, max_length=100)
    backend: str = Field(min_length=1, max_length=100)
    llm: str = Field(min_length=1, max_length=100)
    vector_db: str = Field(min_length=1, max_length=100)
    embeddings: str = Field(min_length=1, max_length=100)
    cache: str = Field(min_length=1, max_length=100)
    monitoring: str = Field(min_length=1, max_length=100)
    authentication: str = Field(min_length=1, max_length=100)
    traffic: int = Field(ge=0, description="Expected requests per unit time")

    @field_validator(
        "application_name",
        "frontend",
        "backend",
        "llm",
        "vector_db",
        "embeddings",
        "cache",
        "monitoring",
        "authentication",
        mode="before",
    )
    @classmethod
    def strip_strings(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class CategoryReview(BaseModel):
    """One category within an architecture review report."""

    category: str
    score: int = Field(ge=0, le=10)
    confidence: int = Field(ge=0, le=100)
    severity: Severity
    vote: BoardVote
    summary: str
    issues: list[str]
    recommendations: list[str]
    estimated_impact: str
    engineering_reasoning: str
    _llm_structured_result: dict[str, object] | None = PrivateAttr(default=None)

    def attach_llm_structured_result(self, payload: dict[str, object]) -> None:
        """Attach LLM structured payload for downstream diagnostics/evaluation."""
        self._llm_structured_result = payload

    def get_llm_structured_result(self) -> dict[str, object] | None:
        """Return attached LLM structured payload when available."""
        return self._llm_structured_result


class LLMReviewerFinding(BaseModel):
    """Structured finding produced by an LLM category reviewer."""

    statement: str = Field(min_length=1)
    evidence_basis: EvidenceBasis
    severity_hint: Severity
    confidence: int | None = Field(default=None, ge=0, le=100)
    category_relevance_note: str | None = None

    @model_validator(mode="after")
    def validate_statement_matches_evidence_basis(self) -> "LLMReviewerFinding":
        statement_lc = self.statement.lower()

        if self.evidence_basis == EvidenceBasis.NOT_SPECIFIED:
            # NOT_SPECIFIED is primarily declared by evidence_basis; deterministic
            # checks here focus on contradictions and obvious mixed-basis claims.

            assertive_absence_patterns = (
                r"\blacks?\b",
                r"\bis missing\b",
                r"\b(is|are)\s+absent\b",
                r"\bdoes not have\b",
                r"\b(has|have)\s+no\b.{0,40}\b(control|controls|policy|monitoring|auth|authentication|authorization|encryption|logging|retry|fallback|guardrail|guardrails)\b",
                r"\b(there is|there's)\s+no\s+(?!(information|specification|detail|details|mention)\b).{0,40}\b(control|controls|policy|monitoring|auth|authentication|authorization|encryption|logging|retry|fallback|guardrail|guardrails)\b",
                r"\bwithout\b.{0,40}\b(control|controls|policy|monitoring|auth|authorization|encryption|logging|retry|fallback|guardrail|guardrails)\b",
                r"\bno\b.{0,40}\b(implemented|in place|present|configured)\b",
            )
            if any(re.search(pattern, statement_lc) for pattern in assertive_absence_patterns):
                raise ValueError(
                    "NOT_SPECIFIED finding statements must not assert proven absence."
                )

            uncertainty_markers = (
                r"\bnot\s+specified\b",
                r"\bnot\s+detailed\b",
                r"\bdoes\s+not\s+specify\b",
                r"\bdoes\s+not\s+detail\b",
                r"\bno\s+explicit\s+mention\b",
                r"\bno\s+information\b.{0,80}\bprovided\b",
                r"\bwithout\s+stated\b",
            )
            inferred_impact_markers = (
                r"\bcreating\b",
                r"\bleading\s+to\b",
                r"\bresulting\s+in\b",
                r"\bcausing\b",
                r"\bwhich\s+could\b",
                r"\bcould\s+lead\b",
                r"\brisk\s+of\b",
            )
            has_uncertainty_marker = any(
                re.search(pattern, statement_lc) for pattern in uncertainty_markers
            )
            has_inferred_impact_marker = any(
                re.search(pattern, statement_lc) for pattern in inferred_impact_markers
            )
            if has_uncertainty_marker and has_inferred_impact_marker:
                raise ValueError(
                    "NOT_SPECIFIED finding statements must not combine uncertainty with inferred impact; use separate INFERRED_RISK finding."
                )

        if self.evidence_basis == EvidenceBasis.INFERRED_RISK:
            # Inferred risk findings should use qualified, conditional language.
            inference_cues = (
                "could",
                "may",
                "might",
                "can",
                "likely",
                "potential",
                "risk",
                "if ",
                "possible",
            )
            if not any(cue in statement_lc for cue in inference_cues):
                raise ValueError(
                    "INFERRED_RISK finding statements must include qualified/conditional language."
                )

        return self


class LLMReviewerResultBase(BaseModel):
    """Shared structured LLM output contract for category reviewers."""

    score: int = Field(ge=0, le=10)
    summary: str = Field(min_length=1)
    engineering_reasoning: str = Field(min_length=1)
    findings: list[LLMReviewerFinding] = Field(default_factory=list)
    # Backward compatibility for previously mocked responses that only emit string risks.
    risks: list[str] | None = None
    recommendations: list[str]
    estimated_impact: str = Field(min_length=1)
    score_rationale: str = Field(min_length=1)
    severity_rationale: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_findings_or_risks_present(
        self, info: ValidationInfo
    ) -> "LLMReviewerResultBase":
        require_structured_findings = bool(
            (info.context or {}).get("require_structured_findings")
        )
        if require_structured_findings and not self.findings:
            raise ValueError(
                "Phase 2.1 runtime requires structured findings; "
                "legacy risks-only payload is not allowed."
            )
        if not self.findings and not self.risks:
            raise ValueError("At least one finding or legacy risk is required.")
        return self


class SecurityReviewerLLMResult(LLMReviewerResultBase):
    """Structured LLM output contract for the Phase 2 security reviewer."""


class ScalabilityReviewerLLMResult(LLMReviewerResultBase):
    """Structured LLM output contract for the Phase 2 scalability reviewer."""


class ReliabilityReviewerLLMResult(LLMReviewerResultBase):
    """Structured LLM output contract for the Phase 2 reliability reviewer."""


class ObservabilityReviewerLLMResult(LLMReviewerResultBase):
    """Structured LLM output contract for the Phase 2 observability reviewer."""


class CostReviewerLLMResult(LLMReviewerResultBase):
    """Structured LLM output contract for the Phase 2 cost reviewer."""


class ReviewerVote(BaseModel):
    """Board-facing vote summary for a single reviewer."""

    reviewer: str
    score: int = Field(ge=0, le=10)
    vote: BoardVote


class ArchitectureReviewResponse(BaseModel):
    """Structured engineering review produced by rule-based reviewers."""

    overall_score: int = Field(ge=0, le=100)
    overall_status: str
    overall_summary: str
    final_decision: BoardVote
    board_summary: str
    reviewer_votes: list[ReviewerVote]
    strengths: list[str]
    critical_risks: list[str]
    quick_wins: list[str]
    categories: list[CategoryReview]
