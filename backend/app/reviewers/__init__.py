"""Architecture review engines.

Each reviewer encapsulates a specialized analysis strategy.
Current reviewers are deterministic (rule-based) for workflow validation.
"""

from app.reviewers.base import BaseReviewer
from app.reviewers.cost import CostReviewer
from app.reviewers.observability import ObservabilityReviewer
from app.reviewers.reliability import ReliabilityReviewer
from app.reviewers.scalability import ScalabilityReviewer
from app.reviewers.security import SecurityReviewer

DEFAULT_REVIEWERS: list[BaseReviewer] = [
    ScalabilityReviewer(),
    ObservabilityReviewer(),
    SecurityReviewer(),
    CostReviewer(),
    ReliabilityReviewer(),
]

__all__ = [
    "BaseReviewer",
    "CostReviewer",
    "DEFAULT_REVIEWERS",
    "ObservabilityReviewer",
    "ReliabilityReviewer",
    "ScalabilityReviewer",
    "SecurityReviewer",
]
