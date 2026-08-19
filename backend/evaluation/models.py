"""Models for the Phase 2 LLM reviewer evaluation runner."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.review import (
    ArchitectureReviewRequest,
    BoardVote,
    CategoryReview,
    EvidenceBasis,
    Severity,
)


class ReferenceFinding(BaseModel):
    """Human-authored reference finding for one category in one scenario."""

    finding: str = Field(min_length=1)
    evidence_basis: EvidenceBasis
    expected_severity: Severity
    importance: Literal["MAJOR_ISSUE", "MINOR_ISSUE", "ACCEPTABLE"]
    why_it_matters: str = Field(min_length=1)
    recommendation_focus: str = Field(min_length=1)


class ReferenceCategoryExpectation(BaseModel):
    """Reference findings for a single reviewer category."""

    expected_findings: list[ReferenceFinding] = Field(min_length=1)


class ReferenceScenario(BaseModel):
    """One evaluation scenario from the reference dataset."""

    scenario_id: str = Field(min_length=1)
    scenario_name: str = Field(min_length=1)
    architecture_source_id: str = Field(min_length=1)
    architecture: ArchitectureReviewRequest
    category_expectations: dict[str, ReferenceCategoryExpectation]


class ReferenceDataset(BaseModel):
    """Top-level reference dataset contract."""

    dataset_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)
    description: str
    source: dict[str, str]
    categories: list[str] = Field(min_length=1)
    scenarios: list[ReferenceScenario] = Field(min_length=1)


class ReviewerType(StrEnum):
    """Source reviewer type for one normalized execution result."""

    DETERMINISTIC = "deterministic"
    LLM = "llm"


class ReviewerStatus(StrEnum):
    """Execution status for one reviewer invocation."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class NormalizedReviewerResult(BaseModel):
    """Normalized shape for deterministic and LLM reviewer outputs."""

    reviewer_type: ReviewerType
    status: ReviewerStatus
    score: int | None = None
    vote: BoardVote | None = None
    severity: Severity | None = None
    summary: str | None = None
    engineering_reasoning: str | None = None
    findings: list[str]
    recommendations: list[str]
    raw_result: dict[str, object] | None = None
    error_type: str | None = None
    error_message: str | None = None


class CategoryEvaluationRecord(BaseModel):
    """Evaluation record for one scenario/category pair."""

    scenario_id: str
    scenario_name: str
    architecture_source_id: str
    category: str
    deterministic_result: NormalizedReviewerResult
    llm_result: NormalizedReviewerResult
    reference_findings: list[ReferenceFinding]


class EvaluationRunMetadata(BaseModel):
    """Metadata describing one evaluation runner execution."""

    run_id: str
    generated_at_utc: str
    runner_version: str
    llm_requested: bool
    llm_provider: str
    llm_provider_available: bool
    llm_provider_error: str | None = None
    dataset_path: str
    output_path: str | None = None


class EvaluationArtifact(BaseModel):
    """Machine-readable output artifact for one full evaluation run."""

    dataset_id: str
    dataset_version: str
    run_metadata: EvaluationRunMetadata
    scenario_count: int = Field(ge=0)
    category_count: int = Field(ge=0)
    total_records: int = Field(ge=0)
    records: list[CategoryEvaluationRecord]


def load_reference_dataset(path: str | Path) -> ReferenceDataset:
    """Load and validate the reference fixture dataset from disk."""
    dataset_path = Path(path)
    with dataset_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return ReferenceDataset.model_validate(payload)

