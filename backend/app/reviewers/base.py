"""Base contracts for architecture reviewers."""

from abc import ABC, abstractmethod

from app.schemas.review import ArchitectureReviewRequest, CategoryReview


class BaseReviewer(ABC):
    """Abstract interface for architecture review engines."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable category name returned in the report."""
        raise NotImplementedError

    @abstractmethod
    def review(self, request: ArchitectureReviewRequest) -> CategoryReview:
        """Produce a deterministic category review for the given architecture."""
        raise NotImplementedError
