"""Orchestrates deterministic architecture reviews."""

from app.reviewers import DEFAULT_REVIEWERS
from app.reviewers.base import BaseReviewer
from app.schemas.review import (
    ArchitectureReviewRequest,
    ArchitectureReviewResponse,
    CategoryReview,
)
from app.services.report_builder import (
    build_board_summary,
    build_overall_summary,
    build_reviewer_votes,
    collect_critical_risks,
    collect_quick_wins,
    collect_strengths,
    compute_overall_score,
    derive_final_decision,
    derive_overall_status,
)


class ReviewService:
    """Runs registered reviewers and assembles the executive report."""

    def __init__(self, reviewers: list[BaseReviewer] | None = None) -> None:
        self._reviewers = reviewers or list(DEFAULT_REVIEWERS)

    def review(self, request: ArchitectureReviewRequest) -> ArchitectureReviewResponse:
        categories: list[CategoryReview] = [
            reviewer.review(request) for reviewer in self._reviewers
        ]

        overall_score = compute_overall_score(request, categories)
        overall_status = derive_overall_status(overall_score)
        final_decision = derive_final_decision(categories)
        reviewer_votes = build_reviewer_votes(categories)
        board_summary = build_board_summary(
            request=request,
            final_decision=final_decision,
            overall_score=overall_score,
            reviewer_votes=reviewer_votes,
        )
        strengths = collect_strengths(request)
        critical_risks = collect_critical_risks(request, categories)
        quick_wins = collect_quick_wins(request)
        overall_summary = build_overall_summary(
            request=request,
            overall_score=overall_score,
            overall_status=overall_status,
            strengths=strengths,
            critical_risks=critical_risks,
        )

        return ArchitectureReviewResponse(
            overall_score=overall_score,
            overall_status=overall_status,
            overall_summary=overall_summary,
            final_decision=final_decision,
            board_summary=board_summary,
            reviewer_votes=reviewer_votes,
            strengths=strengths,
            critical_risks=critical_risks,
            quick_wins=quick_wins,
            categories=categories,
        )
