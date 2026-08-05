"""Shared helpers for building consistent category reviews."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas.review import CategoryReview, Severity


@dataclass
class ReviewFindings:
    """Mutable findings collected while evaluating a category."""

    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    score: int = 10
    confidence: int = 98
    estimated_impact: str = ""
    engineering_reasoning: str = ""
    summary: str = ""

    def penalize(self, points: int) -> None:
        self.score = clamp_score(self.score - points)

    def set_confidence(self, value: int) -> None:
        self.confidence = clamp_confidence(value)


def clamp_score(score: int) -> int:
    return max(0, min(10, score))


def clamp_confidence(confidence: int) -> int:
    return max(0, min(100, confidence))


def derive_severity(score: int, *, has_issues: bool) -> Severity:
    """Map score and issue presence onto a consulting-style severity band."""
    if score <= 3:
        return Severity.CRITICAL
    if score <= 6 and has_issues:
        return Severity.HIGH
    if score <= 8 and has_issues:
        return Severity.HIGH
    if has_issues or score < 10:
        return Severity.MEDIUM
    return Severity.LOW


def build_category_review(category: str, findings: ReviewFindings) -> CategoryReview:
    """Normalize findings into the shared CategoryReview contract."""
    score = clamp_score(findings.score)
    has_issues = len(findings.issues) > 0
    severity = derive_severity(score, has_issues=has_issues)

    return CategoryReview(
        category=category,
        score=score,
        confidence=clamp_confidence(findings.confidence),
        severity=severity,
        summary=findings.summary,
        issues=list(findings.issues),
        recommendations=list(findings.recommendations),
        estimated_impact=findings.estimated_impact,
        engineering_reasoning=findings.engineering_reasoning,
    )
