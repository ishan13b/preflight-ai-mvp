"""Architecture review endpoints."""

from fastapi import APIRouter

from app.schemas.review import ArchitectureReviewRequest, ArchitectureReviewResponse
from app.services.review import ReviewService

router = APIRouter(tags=["review"])
_review_service = ReviewService()


@router.post("/review", response_model=ArchitectureReviewResponse)
async def create_review(
    payload: ArchitectureReviewRequest,
) -> ArchitectureReviewResponse:
    """Run a deterministic architecture review and return a structured report."""
    return _review_service.review(payload)
