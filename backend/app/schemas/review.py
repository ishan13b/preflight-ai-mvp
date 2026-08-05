"""Architecture review request and response schemas."""

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class Severity(StrEnum):
    """Consulting-style severity bands for category findings."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


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
    summary: str
    issues: list[str]
    recommendations: list[str]
    estimated_impact: str
    engineering_reasoning: str


class ArchitectureReviewResponse(BaseModel):
    """Structured engineering review produced by rule-based reviewers."""

    overall_score: int = Field(ge=0, le=100)
    overall_status: str
    overall_summary: str
    strengths: list[str]
    critical_risks: list[str]
    quick_wins: list[str]
    categories: list[CategoryReview]
