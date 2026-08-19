import unittest
from unittest.mock import Mock

from pydantic import ValidationError

from app.reviewers.llm_shared import run_llm_category_review
from app.schemas.review import (
    ArchitectureReviewRequest,
    BoardVote,
    EvidenceBasis,
    LLMReviewerFinding,
    Severity,
    SecurityReviewerLLMResult,
)
from app.services.llm.provider import LLMProvider, LLMProviderError


class LLMReviewerSharedExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.request = ArchitectureReviewRequest(
            application_name="Customer Support Bot",
            frontend="React",
            backend="FastAPI",
            llm="GPT-5.5",
            vector_db="Pinecone",
            embeddings="BGE Large",
            cache="None",
            monitoring="None",
            authentication="JWT",
            traffic=1000,
        )

    def test_maps_structured_result_and_derives_vote(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = SecurityReviewerLLMResult(
            score=7,
            summary="Moderate security concerns.",
            engineering_reasoning="Auth exists but monitoring coverage is partial.",
            findings=[
                LLMReviewerFinding(
                    statement="Partial coverage for incident telemetry",
                    evidence_basis=EvidenceBasis.OBSERVED,
                    severity_hint=Severity.MEDIUM,
                )
            ],
            recommendations=["Add end-to-end security traces"],
            estimated_impact="Slower incident triage under active abuse.",
            score_rationale="One observed control gap with bounded blast radius.",
            severity_rationale="Observed detection gap creates medium production risk.",
        )

        category = run_llm_category_review(
            provider=provider,
            request=self.request,
            category="Security",
            confidence=85,
            system_instruction="security rubric",
            response_model=SecurityReviewerLLMResult,
        )

        self.assertEqual(category.score, 7)
        self.assertEqual(category.vote, BoardVote.APPROVED_WITH_CONCERNS)
        self.assertEqual(category.issues, ["Partial coverage for incident telemetry"])

    def test_maps_all_evidence_basis_variants(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = SecurityReviewerLLMResult(
            score=6,
            summary="Security posture has mixed evidence quality.",
            engineering_reasoning="Findings include observed, unspecified, and inferred risk.",
            findings=[
                LLMReviewerFinding(
                    statement="Authentication is explicitly set to None.",
                    evidence_basis=EvidenceBasis.OBSERVED,
                    severity_hint=Severity.CRITICAL,
                ),
                LLMReviewerFinding(
                    statement="Token rotation policy is not specified.",
                    evidence_basis=EvidenceBasis.NOT_SPECIFIED,
                    severity_hint=Severity.MEDIUM,
                ),
                LLMReviewerFinding(
                    statement="Multi-agent fan-out can increase abuse surface.",
                    evidence_basis=EvidenceBasis.INFERRED_RISK,
                    severity_hint=Severity.HIGH,
                ),
            ],
            recommendations=["Add auth controls and validate token lifecycle policy."],
            estimated_impact="Compounded attack surface and delayed containment.",
            score_rationale="One critical observed gap plus additional inferred risks.",
            severity_rationale="Observed exploitability and scale effects justify high concern.",
        )

        category = run_llm_category_review(
            provider=provider,
            request=self.request,
            category="Security",
            confidence=85,
            system_instruction="security rubric",
            response_model=SecurityReviewerLLMResult,
        )

        self.assertEqual(
            category.issues,
            [
                "Authentication is explicitly set to None.",
                "Token rotation policy is not specified.",
                "Multi-agent fan-out can increase abuse surface.",
            ],
        )

    def test_legacy_risks_field_remains_supported(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = SecurityReviewerLLMResult(
            score=7,
            summary="Moderate security concerns.",
            engineering_reasoning="Legacy payload uses risks only.",
            risks=["Legacy risk payload"],
            recommendations=["Migrate response to structured findings."],
            estimated_impact="Mapping still preserves issue statements.",
            score_rationale="Legacy-compatible score rationale.",
            severity_rationale="Legacy-compatible severity rationale.",
        )

        category = run_llm_category_review(
            provider=provider,
            request=self.request,
            category="Security",
            confidence=85,
            system_instruction="security rubric",
            response_model=SecurityReviewerLLMResult,
            allow_legacy_risks=True,
        )

        self.assertEqual(category.issues, ["Legacy risk payload"])

    def test_legacy_risks_only_payload_fails_in_phase21_runtime(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = {
            "score": 7,
            "summary": "Legacy-only payload.",
            "engineering_reasoning": "No structured findings included.",
            "risks": ["Legacy-only risk statement."],
            "recommendations": ["Return structured findings in Phase 2.1 mode."],
            "estimated_impact": "Evidence metadata cannot be evaluated.",
            "score_rationale": "Legacy payload rationale.",
            "severity_rationale": "Legacy payload rationale.",
        }

        with self.assertRaises(ValidationError) as ctx:
            run_llm_category_review(
                provider=provider,
                request=self.request,
                category="Security",
                confidence=85,
                system_instruction="security rubric",
                response_model=SecurityReviewerLLMResult,
            )

        self.assertIn(
            "requires structured findings",
            str(ctx.exception),
        )

    def test_no_metadata_is_synthesized_from_legacy_risks(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = {
            "score": 7,
            "summary": "Legacy-only payload.",
            "engineering_reasoning": "No finding metadata present.",
            "risks": ["Legacy risk without evidence basis."],
            "recommendations": ["Use structured findings output."],
            "estimated_impact": "Missing structured metadata blocks strict runtime.",
            "score_rationale": "Legacy rationale present.",
            "severity_rationale": "Legacy rationale present.",
        }

        with self.assertRaises(ValidationError):
            run_llm_category_review(
                provider=provider,
                request=self.request,
                category="Security",
                confidence=85,
                system_instruction="security rubric",
                response_model=SecurityReviewerLLMResult,
            )

    def test_invalid_score_is_rejected(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.return_value = {
            "score": 11,
            "summary": "invalid",
            "engineering_reasoning": "invalid",
            "findings": [],
            "recommendations": [],
            "estimated_impact": "invalid",
            "score_rationale": "invalid",
            "severity_rationale": "invalid",
        }

        with self.assertRaises(ValidationError):
            run_llm_category_review(
                provider=provider,
                request=self.request,
                category="Security",
                confidence=85,
                system_instruction="security rubric",
                response_model=SecurityReviewerLLMResult,
            )

    def test_invalid_evidence_basis_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            SecurityReviewerLLMResult(
                score=7,
                summary="Invalid evidence basis payload.",
                engineering_reasoning="Should fail schema validation.",
                findings=[
                    {
                        "statement": "Evidence basis is invalid.",
                        "evidence_basis": "UNKNOWN",
                        "severity_hint": "MEDIUM",
                    }
                ],
                recommendations=["Use supported enum values."],
                estimated_impact="Validation should fail before review mapping.",
                score_rationale="Invalid payload.",
                severity_rationale="Invalid payload.",
            )

    def test_invalid_severity_hint_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            SecurityReviewerLLMResult(
                score=7,
                summary="Invalid severity hint payload.",
                engineering_reasoning="Should fail schema validation.",
                findings=[
                    {
                        "statement": "Severity hint is invalid.",
                        "evidence_basis": "OBSERVED",
                        "severity_hint": "SEVERE",
                    }
                ],
                recommendations=["Use supported severity enum values."],
                estimated_impact="Validation should fail before review mapping.",
                score_rationale="Invalid payload.",
                severity_rationale="Invalid payload.",
            )

    def test_not_specified_finding_rejects_asserted_absence_wording(self) -> None:
        with self.assertRaises(ValidationError):
            SecurityReviewerLLMResult(
                score=7,
                summary="Invalid NOT_SPECIFIED wording.",
                engineering_reasoning="Should fail claim-construction validation.",
                findings=[
                    {
                        "statement": "The architecture lacks authorization controls.",
                        "evidence_basis": "NOT_SPECIFIED",
                        "severity_hint": "MEDIUM",
                    }
                ],
                recommendations=["Rephrase with uncertainty and validation guidance."],
                estimated_impact="Overstates confidence in absent controls.",
                score_rationale="Invalid claim construction.",
                severity_rationale="Invalid claim construction.",
            )

    def test_not_specified_existing_uncertainty_phrasing_still_passes(self) -> None:
        result = SecurityReviewerLLMResult(
            score=7,
            summary="Unspecified detail called out correctly.",
            engineering_reasoning="Uses explicit uncertainty wording.",
            findings=[
                {
                    "statement": "Token rotation policy is not specified.",
                    "evidence_basis": "NOT_SPECIFIED",
                    "severity_hint": "MEDIUM",
                }
            ],
            recommendations=["Document token rotation lifecycle controls."],
            estimated_impact="Moderate uncertainty around key security hygiene.",
            score_rationale="Unspecified but important control detail.",
            severity_rationale="Uncertainty is explicit and bounded.",
        )
        self.assertEqual(result.findings[0].evidence_basis, EvidenceBasis.NOT_SPECIFIED)

    def test_not_specified_accepts_no_details_are_provided_pattern(self) -> None:
        result = SecurityReviewerLLMResult(
            score=7,
            summary="Unspecified detail called out correctly.",
            engineering_reasoning="Uncertainty is explicit via no-details phrasing.",
            findings=[
                {
                    "statement": "No details on query optimization or cost controls are provided.",
                    "evidence_basis": "NOT_SPECIFIED",
                    "severity_hint": "MEDIUM",
                }
            ],
            recommendations=["Provide cost-control implementation details."],
            estimated_impact="Uncertain efficiency and spend controls.",
            score_rationale="Insufficient implementation detail in architecture input.",
            severity_rationale="Uncertainty is explicit and evidence-bounded.",
        )
        self.assertEqual(result.findings[0].evidence_basis, EvidenceBasis.NOT_SPECIFIED)

    def test_not_specified_accepts_equivalent_uncertainty_phrasing(self) -> None:
        accepted_statements = (
            "Authorization controls are not specified in the provided architecture.",
            "Details on authorization are not provided.",
            "Details on monitoring are not available.",
            "The architecture does not specify how this is handled.",
        )
        for statement in accepted_statements:
            result = SecurityReviewerLLMResult(
                score=7,
                summary="Equivalent uncertainty phrasing.",
                engineering_reasoning="All statements communicate insufficient evidence.",
                findings=[
                    {
                        "statement": statement,
                        "evidence_basis": "NOT_SPECIFIED",
                        "severity_hint": "MEDIUM",
                    }
                ],
                recommendations=["Document implementation specifics."],
                estimated_impact="Assessment confidence is limited by missing details.",
                score_rationale="Uncertainty is explicit in the finding statement.",
                severity_rationale="Unspecified controls imply bounded risk.",
            )
            self.assertEqual(result.findings[0].evidence_basis, EvidenceBasis.NOT_SPECIFIED)

    def test_not_specified_accepts_does_not_detail_pattern(self) -> None:
        result = SecurityReviewerLLMResult(
            score=7,
            summary="Unspecified detail called out correctly.",
            engineering_reasoning=(
                "Statement communicates missing architecture detail without asserting absence."
            ),
            findings=[
                {
                    "statement": "The architecture does not detail retry behavior.",
                    "evidence_basis": "NOT_SPECIFIED",
                    "severity_hint": "MEDIUM",
                }
            ],
            recommendations=["Document retry policy and failure-mode behavior."],
            estimated_impact="Retry reliability posture is uncertain from provided material.",
            score_rationale="Architecture omits concrete retry implementation details.",
            severity_rationale="Uncertainty is explicit and bounded.",
        )
        self.assertEqual(result.findings[0].evidence_basis, EvidenceBasis.NOT_SPECIFIED)

    def test_not_specified_accepts_single_points_of_failure_as_control_target(self) -> None:
        result = SecurityReviewerLLMResult(
            score=7,
            summary="Unspecified controls phrased with reliability target.",
            engineering_reasoning=(
                "Statement identifies unspecified controls and names their prevention target."
            ),
            findings=[
                {
                    "statement": (
                        "Reliability controls to prevent single points of failure are not "
                        "specified."
                    ),
                    "evidence_basis": "NOT_SPECIFIED",
                    "severity_hint": "MEDIUM",
                }
            ],
            recommendations=["Specify redundancy and failover controls."],
            estimated_impact="Reliability posture uncertainty remains unresolved.",
            score_rationale="Architecture omits reliability-control detail.",
            severity_rationale="Uncertainty is explicit without asserted consequence.",
        )
        self.assertEqual(result.findings[0].evidence_basis, EvidenceBasis.NOT_SPECIFIED)

    def test_not_specified_accepts_redundancy_and_failover_unspecified(self) -> None:
        result = SecurityReviewerLLMResult(
            score=7,
            summary="Unspecified detail called out correctly.",
            engineering_reasoning="Statement is a direct unspecified-control observation.",
            findings=[
                {
                    "statement": "Redundancy and failover strategies are not specified.",
                    "evidence_basis": "NOT_SPECIFIED",
                    "severity_hint": "MEDIUM",
                }
            ],
            recommendations=["Document failover and redundancy strategy."],
            estimated_impact="Resilience confidence is limited by missing specification.",
            score_rationale="Architecture detail is insufficient for reliability controls.",
            severity_rationale="Uncertainty is explicit and non-assertive.",
        )
        self.assertEqual(result.findings[0].evidence_basis, EvidenceBasis.NOT_SPECIFIED)

    def test_not_specified_accepts_no_information_or_specification_forms(self) -> None:
        accepted_statements = (
            "There is no information on security controls to protect AI endpoints from abuse or unauthorized access.",
            "There is no specification of timeout, retry, fallback, or circuit-breaking behavior for critical dependencies.",
            "There is no information about authentication controls.",
            "There is no specification of redundancy and failover strategies.",
        )
        for statement in accepted_statements:
            result = SecurityReviewerLLMResult(
                score=7,
                summary="Unspecified detail called out correctly.",
                engineering_reasoning=(
                    "Statement describes missing information/specification, not proven absence."
                ),
                findings=[
                    {
                        "statement": statement,
                        "evidence_basis": "NOT_SPECIFIED",
                        "severity_hint": "MEDIUM",
                    }
                ],
                recommendations=["Document the missing architecture details."],
                estimated_impact="Assessment confidence is bounded by missing specification detail.",
                score_rationale="Control detail cannot be confirmed from provided material.",
                severity_rationale="Uncertainty is explicit and non-assertive.",
            )
            self.assertEqual(result.findings[0].evidence_basis, EvidenceBasis.NOT_SPECIFIED)

    def test_not_specified_accepts_no_specification_on_pattern(self) -> None:
        result = SecurityReviewerLLMResult(
            score=7,
            summary="Unspecified detail called out correctly.",
            engineering_reasoning=(
                "Statement explicitly describes missing specification in provided material."
            ),
            findings=[
                {
                    "statement": (
                        "Monitoring is implemented with Langfuse, but there is no "
                        "specification on automated failure detection and recovery "
                        "or alerting workflows."
                    ),
                    "evidence_basis": "NOT_SPECIFIED",
                    "severity_hint": "LOW",
                }
            ],
            recommendations=["Document alerting and automated recovery workflow details."],
            estimated_impact="Reliability confidence is limited by unspecified operations detail.",
            score_rationale="Core control exists, but escalation and recovery details are unspecified.",
            severity_rationale="Uncertainty is explicit and scoped to missing specification detail.",
        )
        self.assertEqual(result.findings[0].evidence_basis, EvidenceBasis.NOT_SPECIFIED)

    def test_not_specified_accepts_no_detail_on_pattern(self) -> None:
        result = SecurityReviewerLLMResult(
            score=7,
            summary="Unspecified detail called out correctly.",
            engineering_reasoning="No-detail phrasing explicitly signals missing specification.",
            findings=[
                {
                    "statement": (
                        "Monitoring is provided via Langfuse, but there is no detail on "
                        "automated alerting, circuit breaking, or overload protection."
                    ),
                    "evidence_basis": "NOT_SPECIFIED",
                    "severity_hint": "MEDIUM",
                }
            ],
            recommendations=["Document resilience automation and overload controls."],
            estimated_impact="Unclear monitoring automation can delay failure containment.",
            score_rationale="Core monitoring exists but operational detail is unspecified.",
            severity_rationale="Statement is uncertainty-based and scoped to missing detail.",
        )
        self.assertEqual(result.findings[0].evidence_basis, EvidenceBasis.NOT_SPECIFIED)

    def test_not_specified_accepts_no_information_is_provided_about_pattern(self) -> None:
        result = SecurityReviewerLLMResult(
            score=7,
            summary="Unspecified detail called out correctly.",
            engineering_reasoning=(
                "No-information-provided phrasing clearly indicates uncertain evidence."
            ),
            findings=[
                {
                    "statement": (
                        "No information is provided about idempotency or duplicate-work safety "
                        "for retrying asynchronous operations or handling LLM failures."
                    ),
                    "evidence_basis": "NOT_SPECIFIED",
                    "severity_hint": "MEDIUM",
                }
            ],
            recommendations=["Specify idempotency and retry safety behavior for failure paths."],
            estimated_impact="Unclear retry semantics may hide reliability tradeoffs.",
            score_rationale="Control quality cannot be determined from provided architecture.",
            severity_rationale="Uncertainty remains explicit without asserting proven absence.",
        )
        self.assertEqual(result.findings[0].evidence_basis, EvidenceBasis.NOT_SPECIFIED)

    def test_not_specified_rejects_mixed_single_point_of_failure_assertion(self) -> None:
        with self.assertRaises(ValidationError):
            SecurityReviewerLLMResult(
                score=7,
                summary="Invalid NOT_SPECIFIED mixed assertion.",
                engineering_reasoning=(
                    "Statement asserts a concrete failure-mode conclusion while only partial "
                    "specification language is present."
                ),
                findings=[
                    {
                        "statement": (
                            "Cache (Redis) and Vector DB (Pinecone) redundancy is not "
                            "specified, creating potential single points of failure."
                        ),
                        "evidence_basis": "NOT_SPECIFIED",
                        "severity_hint": "HIGH",
                    }
                ],
                recommendations=["Split uncertainty and inferred-risk claims explicitly."],
                estimated_impact="Mixed claim structure overstates certainty for NOT_SPECIFIED.",
                score_rationale="Assertion should be expressed conditionally as inferred risk.",
                severity_rationale="Direct single-point-of-failure claim is not pure uncertainty.",
            )

    def test_not_specified_still_rejects_factual_absence_claims(self) -> None:
        factual_absence_statements = (
            "The system lacks access controls.",
            "The system is missing encryption.",
            "The architecture has no monitoring.",
            "Authentication is absent.",
            "There is no authentication.",
        )
        for statement in factual_absence_statements:
            with self.assertRaises(ValidationError):
                SecurityReviewerLLMResult(
                    score=7,
                    summary="Invalid NOT_SPECIFIED factual-absence claim.",
                    engineering_reasoning="Statement asserts proven absence.",
                    findings=[
                        {
                            "statement": statement,
                            "evidence_basis": "NOT_SPECIFIED",
                            "severity_hint": "MEDIUM",
                        }
                    ],
                    recommendations=["Rephrase with explicit uncertainty language."],
                    estimated_impact="Overstates confidence in absence claim.",
                    score_rationale="Claim-construction violation for NOT_SPECIFIED.",
                    severity_rationale="Assertive absence without proof is invalid.",
                )

    def test_not_specified_rejects_uncertainty_plus_inferred_impact_bundle(self) -> None:
        with self.assertRaises(ValidationError):
            SecurityReviewerLLMResult(
                score=7,
                summary="Invalid mixed-basis NOT_SPECIFIED statement.",
                engineering_reasoning=(
                    "Statement combines unspecified evidence with inferred reliability impact."
                ),
                findings=[
                    {
                        "statement": (
                            "There is no explicit mention of redundancy, creating potential "
                            "single points of failure."
                        ),
                        "evidence_basis": "NOT_SPECIFIED",
                        "severity_hint": "HIGH",
                    }
                ],
                recommendations=["Split uncertainty and inferred risk into separate findings."],
                estimated_impact="Mixed claim obscures evidence-basis semantics.",
                score_rationale="Evidence basis and impact inference are conflated.",
                severity_rationale="Claim must be separated across NOT_SPECIFIED and INFERRED_RISK.",
            )

    def test_not_specified_rejects_additional_explicit_mixed_consequence_patterns(self) -> None:
        mixed_statements = (
            "Redundancy and failover strategies are not specified, creating a risk of service failure.",
            "Redundancy is not specified, which could lead to service disruption.",
            "Token consumption patterns and management strategies are not specified, creating uncertainty about potential avoidable overhead in LLM usage costs.",
        )
        for statement in mixed_statements:
            with self.assertRaises(ValidationError):
                SecurityReviewerLLMResult(
                    score=7,
                    summary="Invalid mixed-basis NOT_SPECIFIED statement.",
                    engineering_reasoning=(
                        "Statement combines unspecified evidence with inferred consequence."
                    ),
                    findings=[
                        {
                            "statement": statement,
                            "evidence_basis": "NOT_SPECIFIED",
                            "severity_hint": "HIGH",
                        }
                    ],
                    recommendations=[
                        "Separate uncertainty from conditional risk in distinct findings."
                    ],
                    estimated_impact="Mixed statement violates evidence-basis separation.",
                    score_rationale="Evidence and consequence are conflated.",
                    severity_rationale="Conditional impact must be INFERRED_RISK.",
                )

    def test_inferred_risk_accepts_conditional_language(self) -> None:
        result = SecurityReviewerLLMResult(
            score=7,
            summary="Valid INFERRED_RISK claim construction.",
            engineering_reasoning="Conditional language expresses inferred consequence.",
            findings=[
                {
                    "statement": (
                        "If redundancy is absent, the service could experience broader "
                        "failure impact."
                    ),
                    "evidence_basis": "INFERRED_RISK",
                    "severity_hint": "HIGH",
                }
            ],
            recommendations=["Add redundancy and failover controls."],
            estimated_impact="Potential wider outage surface during dependency failures.",
            score_rationale="Conditional dependency risk is plausible and material.",
            severity_rationale="Inferred impact is qualified with explicit uncertainty.",
        )
        self.assertEqual(result.findings[0].evidence_basis, EvidenceBasis.INFERRED_RISK)

    def test_inferred_risk_rejects_unqualified_conclusion(self) -> None:
        with self.assertRaises(ValidationError):
            SecurityReviewerLLMResult(
                score=7,
                summary="Invalid INFERRED_RISK wording.",
                engineering_reasoning="Inference is presented as deterministic fact.",
                findings=[
                    {
                        "statement": "The service will experience broader failure impact.",
                        "evidence_basis": "INFERRED_RISK",
                        "severity_hint": "HIGH",
                    }
                ],
                recommendations=["Use conditional language for inferred claims."],
                estimated_impact="Overstates certainty of modeled risk behavior.",
                score_rationale="Risk statement lacks qualifying conditions.",
                severity_rationale="Unqualified certainty is invalid for inferred claims.",
            )

    def test_inferred_risk_requires_qualified_language(self) -> None:
        with self.assertRaises(ValidationError):
            SecurityReviewerLLMResult(
                score=7,
                summary="Invalid INFERRED_RISK wording.",
                engineering_reasoning="Should fail claim-construction validation.",
                findings=[
                    {
                        "statement": "Queue fan-out causes outage.",
                        "evidence_basis": "INFERRED_RISK",
                        "severity_hint": "HIGH",
                    }
                ],
                recommendations=["Use conditional language for inferred claims."],
                estimated_impact="Inference is expressed as guaranteed fact.",
                score_rationale="Invalid claim construction.",
                severity_rationale="Invalid claim construction.",
            )

    def test_observed_finding_permits_direct_factual_wording(self) -> None:
        result = SecurityReviewerLLMResult(
            score=6,
            summary="Observed control gap.",
            engineering_reasoning="Directly observed from architecture fields.",
            findings=[
                {
                    "statement": "Authentication is explicitly set to None.",
                    "evidence_basis": "OBSERVED",
                    "severity_hint": "CRITICAL",
                }
            ],
            recommendations=["Implement authentication before production launch."],
            estimated_impact="Unauthenticated access to enterprise search paths.",
            score_rationale="Observed explicit blocker in architecture input.",
            severity_rationale="Directly observed critical control gap.",
        )
        self.assertEqual(result.findings[0].evidence_basis, EvidenceBasis.OBSERVED)

    def test_provider_errors_are_wrapped_with_category_context(self) -> None:
        provider = Mock(spec=LLMProvider)
        provider.generate_structured.side_effect = LLMProviderError(
            "provider failed",
            diagnostics={"exception_class": "ValidationError"},
        )

        with self.assertRaises(LLMProviderError) as ctx:
            run_llm_category_review(
                provider=provider,
                request=self.request,
                category="Security",
                confidence=85,
                system_instruction="security rubric",
                response_model=SecurityReviewerLLMResult,
            )

        self.assertIn("Security LLM review failed", str(ctx.exception))
        self.assertEqual(
            getattr(ctx.exception, "diagnostics", None),
            {"exception_class": "ValidationError"},
        )


if __name__ == "__main__":
    unittest.main()
