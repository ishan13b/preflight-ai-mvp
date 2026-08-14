"""Schemas for Phase 2 LLM reviewer orchestration results."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.review import CategoryReview


class ReviewerExecutionStatus(StrEnum):
    """Normalized outcome status for one reviewer execution."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class OrchestrationStatus(StrEnum):
    """Overall orchestration completeness status."""

    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class ReviewerSuccessResult(BaseModel):
    """One reviewer completed successfully with a category review payload."""

    category: str
    status: Literal[ReviewerExecutionStatus.SUCCESS] = ReviewerExecutionStatus.SUCCESS
    review: CategoryReview


class ReviewerFailureResult(BaseModel):
    """One reviewer failed and returned safe, structured error metadata."""

    category: str
    status: Literal[ReviewerExecutionStatus.FAILED] = ReviewerExecutionStatus.FAILED
    error_type: str = Field(min_length=1)
    error_message: str = Field(min_length=1)


ReviewerExecutionResult = ReviewerSuccessResult | ReviewerFailureResult


class LLMReviewOrchestrationResult(BaseModel):
    """Normalized results for one full LLM reviewer orchestration run."""

    status: OrchestrationStatus
    is_complete: bool
    total_reviewers: int = Field(ge=0)
    successful_reviewers: int = Field(ge=0)
    failed_reviewers: int = Field(ge=0)
    reviewer_results: list[ReviewerExecutionResult]
