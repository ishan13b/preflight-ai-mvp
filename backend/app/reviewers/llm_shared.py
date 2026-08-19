"""Shared execution helper for LLM-backed category reviewers."""

from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel

from app.reviewers.common import derive_severity, derive_vote
from app.schemas.review import ArchitectureReviewRequest, CategoryReview
from app.services.llm.provider import LLMProvider, LLMProviderError

StructuredResultT = TypeVar("StructuredResultT", bound=BaseModel)

_CALIBRATION_ADDENDUM = """
Calibration requirements (Phase 2.1):
- Evidence taxonomy:
  - OBSERVED: directly supported by the provided architecture fields.
  - NOT_SPECIFIED: architecture does not provide enough information to determine control presence or quality.
  - INFERRED_RISK: plausible production risk inferred from explicit architecture characteristics.
- Never convert NOT_SPECIFIED into a confirmed "missing" control claim. Phrase it as uncertainty plus validation need.
- Calibrate score and severity hints using:
  - evidence strength,
  - likelihood,
  - blast radius,
  - production impact,
  - compensating controls,
  - whether risk is confirmed (OBSERVED) or inferred.
- NOT_SPECIFIED alone should usually map to LOW or MEDIUM severity hints unless explicit compounding architecture signals justify higher severity.
- HIGH/CRITICAL severity hints must include explicit rationale linking likelihood, blast radius, and weak/absent compensating controls.

Structured output requirements:
- Provide findings as structured entries with:
  - statement
  - evidence_basis (OBSERVED | NOT_SPECIFIED | INFERRED_RISK)
  - severity_hint (LOW | MEDIUM | HIGH | CRITICAL)
  - confidence (optional integer 0-100)
  - category_relevance_note (optional, only when cross-category mention is needed)
- Include concise score_rationale and severity_rationale fields.
- Keep recommendations specific and testable.

Claim-construction requirements:
- For each finding, make statement wording match its evidence_basis.
- Each finding statement must express exactly one evidence_basis; do not combine NOT_SPECIFIED uncertainty and inferred impact in the same statement.
- Do not use consequence clauses ("which could", "creating", "leading to", "resulting in", "causing") inside a NOT_SPECIFIED finding. Start a new INFERRED_RISK finding instead.
- If evidence_basis is NOT_SPECIFIED:
  - explicitly state uncertainty ("not specified"/"cannot determine from provided architecture"),
  - do not convert unspecified detail into an asserted deficiency.
  - if a downstream risk is useful, express it conditionally as a separate finding and label that finding INFERRED_RISK.
- If evidence_basis is INFERRED_RISK:
  - use qualified/conditional language (e.g., "could", "may", "if ... then risk").
  - do not present inferred impact as an observed or established fact.
- If evidence_basis is OBSERVED:
  - factual wording is allowed when directly supported by provided architecture fields.

Examples:
- BAD: "Authorization is missing, creating an access-control vulnerability."
- BETTER (NOT_SPECIFIED): "Authorization controls are not specified in the provided material."
- CONDITIONAL INFERENCE (INFERRED_RISK): "If authorization controls are absent, this could create an access-control risk."
- SPLIT EXAMPLE (NOT_SPECIFIED): "The architecture does not specify controls to protect AI endpoints from abuse or excessive traffic."
- SPLIT EXAMPLE (INFERRED_RISK): "If such protections are absent or insufficient, endpoints could be exposed to exploitation or denial of service."
""".strip()


def build_calibrated_instruction(*, base_instruction: str, boundary_reminder: str) -> str:
    """Compose category prompt with shared calibration and boundary guardrails."""
    return (
        f"{base_instruction}\n\n"
        f"{_CALIBRATION_ADDENDUM}\n\n"
        "Category boundary discipline:\n"
        f"- {boundary_reminder}\n"
        "- Mention adjacent-category concerns only when they directly affect this category's assessment."
    )


def run_llm_category_review(
    *,
    provider: LLMProvider,
    request: ArchitectureReviewRequest,
    category: str,
    confidence: int,
    system_instruction: str,
    response_model: type[StructuredResultT],
    allow_legacy_risks: bool = False,
) -> CategoryReview:
    """Run a category review through the provider and map it to CategoryReview.

    This helper intentionally handles only shared mechanics:
    - architecture payload serialization
    - provider structured generation call
    - result validation at reviewer boundary
    - deterministic vote derivation from score
    - CategoryReview mapping

    Runtime modes:
    - Phase 2.1 default (`allow_legacy_risks=False`): requires structured findings.
    - Explicit legacy/test compatibility (`allow_legacy_risks=True`): allows risks-only payloads.
    """
    user_input = request.model_dump_json(indent=2)

    try:
        raw_result = provider.generate_structured(
            system_instruction=system_instruction,
            user_input=user_input,
            response_model=response_model,
        )
    except LLMProviderError as exc:
        raise LLMProviderError(
            f"{category} LLM review failed: {exc}",
            diagnostics=getattr(exc, "diagnostics", None),
        ) from exc

    # Re-validate output at reviewer boundary with explicit runtime mode.
    result_payload = (
        raw_result.model_dump(mode="json")
        if isinstance(raw_result, BaseModel)
        else raw_result
    )
    result = response_model.model_validate(
        result_payload,
        context={"require_structured_findings": not allow_legacy_risks},
    )

    score = result.score
    findings = list(getattr(result, "findings", []))
    if findings:
        risks = [finding.statement for finding in findings]
    elif allow_legacy_risks:
        risks = list(getattr(result, "risks", []) or [])
    else:  # Defensive guard; schema validation should fail first in strict mode.
        raise ValueError(
            "Structured findings are required in Phase 2.1 runtime; "
            "legacy risks-only payloads are not accepted."
        )
    severity = derive_severity(score, has_issues=len(risks) > 0)
    deterministic_vote = derive_vote(score)

    category_review = CategoryReview(
        category=category,
        score=score,
        confidence=confidence,
        severity=severity,
        vote=deterministic_vote,
        summary=result.summary,
        issues=risks,
        recommendations=list(result.recommendations),
        estimated_impact=result.estimated_impact,
        engineering_reasoning=result.engineering_reasoning,
    )
    # Preserve the full structured LLM output for evaluation/adjudication artifacts.
    category_review.attach_llm_structured_result(result.model_dump(mode="json"))
    return category_review
