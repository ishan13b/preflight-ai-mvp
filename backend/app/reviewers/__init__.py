"""Architecture review engines.

Each reviewer encapsulates a specialized analysis strategy.
Current reviewers are deterministic (rule-based) for workflow validation.
"""

from app.reviewers.base import BaseReviewer
from app.reviewers.observability import ObservabilityReviewer
from app.reviewers.scalability import ScalabilityReviewer

DEFAULT_REVIEWERS: list[BaseReviewer] = [
    ScalabilityReviewer(),
    ObservabilityReviewer(),
]

__all__ = [
    "BaseReviewer",
    "DEFAULT_REVIEWERS",
    "ObservabilityReviewer",
    "ScalabilityReviewer",
]
