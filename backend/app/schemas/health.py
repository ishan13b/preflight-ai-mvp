"""Health check response schemas."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Standard health check payload."""

    status: str = Field(description="Service health status", examples=["ok"])
