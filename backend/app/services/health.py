"""Health check service."""

from app.schemas.health import HealthResponse


class HealthService:
    """Provides operational health status for the API."""

    @staticmethod
    def check() -> HealthResponse:
        """Return a healthy status payload."""
        return HealthResponse(status="ok")
