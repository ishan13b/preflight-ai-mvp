"""Lightweight runner for deterministic vs LLM reviewer evaluation records."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.reviewers.base import BaseReviewer
from app.reviewers.cost import CostReviewer
from app.reviewers.cost_llm import CostLLMReviewer
from app.reviewers.observability import ObservabilityReviewer
from app.reviewers.observability_llm import ObservabilityLLMReviewer
from app.reviewers.reliability import ReliabilityReviewer
from app.reviewers.reliability_llm import ReliabilityLLMReviewer
from app.reviewers.scalability import ScalabilityReviewer
from app.reviewers.scalability_llm import ScalabilityLLMReviewer
from app.reviewers.security import SecurityReviewer
from app.reviewers.security_llm import SecurityLLMReviewer
from app.schemas.review import ArchitectureReviewRequest, CategoryReview
from app.services.llm.openai_provider import OpenAIProvider
from app.services.llm.provider import LLMProvider, LLMProviderError
from evaluation.models import (
    CategoryEvaluationRecord,
    EvaluationArtifact,
    EvaluationRunMetadata,
    NormalizedReviewerResult,
    ReferenceDataset,
    ReviewerStatus,
    ReviewerType,
    load_reference_dataset,
)

RUNNER_VERSION = "v0.1.0"

DEFAULT_DATASET_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "llm_reviewer_reference_dataset.json"
)
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output"


class LLMReviewerEvaluationRunner:
    """Execute deterministic and LLM reviewers over reference scenarios."""

    def __init__(
        self,
        *,
        dataset_path: str | Path = DEFAULT_DATASET_PATH,
        llm_provider: LLMProvider | None = None,
        include_llm: bool = True,
    ) -> None:
        self._dataset_path = Path(dataset_path)
        self._dataset: ReferenceDataset = load_reference_dataset(self._dataset_path)
        self._include_llm = include_llm

        self._deterministic_reviewers = self._build_deterministic_reviewers()
        self._llm_provider_error: str | None = None

        if not include_llm:
            self._llm_provider = None
            self._llm_reviewers = {}
        else:
            self._llm_provider = llm_provider
            if self._llm_provider is None:
                try:
                    self._llm_provider = OpenAIProvider()
                except Exception as exc:  # noqa: BLE001 - surface configuration issues.
                    self._llm_provider_error = str(exc)
                    self._llm_provider = None

            self._llm_reviewers = (
                self._build_llm_reviewers(self._llm_provider)
                if self._llm_provider is not None
                else {}
            )

    def run(self) -> EvaluationArtifact:
        """Execute evaluation and return normalized records."""
        run_id = str(uuid4())
        generated_at_utc = datetime.now(UTC).isoformat()
        records: list[CategoryEvaluationRecord] = []

        for scenario in self._dataset.scenarios:
            request = scenario.architecture
            for category in self._dataset.categories:
                deterministic_reviewer = self._deterministic_reviewers[category]
                deterministic_result = self._execute_reviewer(
                    reviewer=deterministic_reviewer,
                    request=request,
                    reviewer_type=ReviewerType.DETERMINISTIC,
                )

                llm_result = self._execute_llm_reviewer_for_category(
                    category=category,
                    request=request,
                )

                records.append(
                    CategoryEvaluationRecord(
                        scenario_id=scenario.scenario_id,
                        scenario_name=scenario.scenario_name,
                        architecture_source_id=scenario.architecture_source_id,
                        category=category,
                        deterministic_result=deterministic_result,
                        llm_result=llm_result,
                        reference_findings=scenario.category_expectations[
                            category
                        ].expected_findings,
                    )
                )

        metadata = EvaluationRunMetadata(
            run_id=run_id,
            generated_at_utc=generated_at_utc,
            runner_version=RUNNER_VERSION,
            llm_requested=self._include_llm,
            llm_provider="OpenAIProvider",
            llm_provider_available=self._llm_provider is not None,
            llm_provider_error=self._llm_provider_error,
            dataset_path=str(self._dataset_path),
            output_path=None,
        )

        return EvaluationArtifact(
            dataset_id=self._dataset.dataset_id,
            dataset_version=self._dataset.dataset_version,
            run_metadata=metadata,
            scenario_count=len(self._dataset.scenarios),
            category_count=len(self._dataset.categories),
            total_records=len(records),
            records=records,
        )

    def run_and_write(self, output_path: str | Path | None = None) -> Path:
        """Execute evaluation and persist a JSON artifact to disk."""
        artifact = self.run()

        resolved_output_path = Path(output_path) if output_path else _default_output_path()
        resolved_output_path.parent.mkdir(parents=True, exist_ok=True)

        artifact_dict = artifact.model_dump(mode="json")
        artifact_dict["run_metadata"]["output_path"] = str(resolved_output_path)

        with resolved_output_path.open("w", encoding="utf-8") as handle:
            json.dump(artifact_dict, handle, indent=2)
            handle.write("\n")

        return resolved_output_path

    @property
    def llm_provider_available(self) -> bool:
        return self._llm_provider is not None

    def _execute_llm_reviewer_for_category(
        self,
        *,
        category: str,
        request: ArchitectureReviewRequest,
    ) -> NormalizedReviewerResult:
        if not self._include_llm:
            return NormalizedReviewerResult(
                reviewer_type=ReviewerType.LLM,
                status=ReviewerStatus.SKIPPED,
                findings=[],
                recommendations=[],
                error_message="LLM evaluation skipped by runner configuration.",
            )

        if self._llm_provider is None:
            return NormalizedReviewerResult(
                reviewer_type=ReviewerType.LLM,
                status=ReviewerStatus.FAILED,
                findings=[],
                recommendations=[],
                error_type="LLMProviderUnavailable",
                error_message=self._llm_provider_error
                or "LLM provider is unavailable for this run.",
            )

        llm_reviewer = self._llm_reviewers[category]
        return self._execute_reviewer(
            reviewer=llm_reviewer,
            request=request,
            reviewer_type=ReviewerType.LLM,
        )

    @staticmethod
    def _execute_reviewer(
        *,
        reviewer: BaseReviewer,
        request: ArchitectureReviewRequest,
        reviewer_type: ReviewerType,
    ) -> NormalizedReviewerResult:
        try:
            category_result = reviewer.review(request)
        except Exception as exc:  # noqa: BLE001 - isolate reviewer failures.
            raw_result: dict[str, object] | None = None
            if reviewer_type == ReviewerType.LLM and isinstance(exc, LLMProviderError):
                diagnostics = getattr(exc, "diagnostics", None)
                if diagnostics:
                    raw_result = {"error_diagnostics": diagnostics}
            return NormalizedReviewerResult(
                reviewer_type=reviewer_type,
                status=ReviewerStatus.FAILED,
                findings=[],
                recommendations=[],
                raw_result=raw_result,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )

        return _normalize_category_review(
            reviewer_type=reviewer_type,
            result=category_result,
        )

    @staticmethod
    def _build_deterministic_reviewers() -> dict[str, BaseReviewer]:
        return {
            "Security": SecurityReviewer(),
            "Scalability": ScalabilityReviewer(),
            "Reliability": ReliabilityReviewer(),
            "Observability": ObservabilityReviewer(),
            "Cost": CostReviewer(),
        }

    @staticmethod
    def _build_llm_reviewers(provider: LLMProvider) -> dict[str, BaseReviewer]:
        return {
            "Security": SecurityLLMReviewer(provider),
            "Scalability": ScalabilityLLMReviewer(provider),
            "Reliability": ReliabilityLLMReviewer(provider),
            "Observability": ObservabilityLLMReviewer(provider),
            "Cost": CostLLMReviewer(provider),
        }


def _normalize_category_review(
    *,
    reviewer_type: ReviewerType,
    result: CategoryReview,
) -> NormalizedReviewerResult:
    raw_result = result.model_dump(mode="json")
    llm_structured_result = result.get_llm_structured_result()
    if reviewer_type == ReviewerType.LLM and llm_structured_result is not None:
        raw_result["llm_structured_result"] = llm_structured_result

    return NormalizedReviewerResult(
        reviewer_type=reviewer_type,
        status=ReviewerStatus.SUCCESS,
        score=result.score,
        vote=result.vote,
        severity=result.severity,
        summary=result.summary,
        engineering_reasoning=result.engineering_reasoning,
        findings=list(result.issues),
        recommendations=list(result.recommendations),
        raw_result=raw_result,
    )


def _default_output_path() -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return DEFAULT_OUTPUT_DIR / f"llm_reviewer_evaluation_{timestamp}.json"


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run deterministic and LLM reviewers against the Phase 2 reference dataset."
        )
    )
    parser.add_argument(
        "--dataset-path",
        default=str(DEFAULT_DATASET_PATH),
        help="Path to the reference dataset JSON.",
    )
    parser.add_argument(
        "--output-path",
        default=None,
        help="Path for the output artifact JSON. Defaults to evaluation/output/.",
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help=(
            "Skip LLM reviewer execution. Useful for fixture validation without "
            "OPENAI_API_KEY."
        ),
    )
    return parser


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()

    runner = LLMReviewerEvaluationRunner(
        dataset_path=args.dataset_path,
        include_llm=not args.skip_llm,
    )
    output_path = runner.run_and_write(output_path=args.output_path)

    print(f"Wrote evaluation artifact: {output_path}")
    if not args.skip_llm and not runner.llm_provider_available:
        print(
            "LLM provider unavailable. Set OPENAI_API_KEY to run LLM reviewers; "
            "deterministic records were still generated."
        )


if __name__ == "__main__":
    main()
