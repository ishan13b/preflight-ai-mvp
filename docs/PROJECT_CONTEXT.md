# Project Context — PreFlight AI

Canonical engineering snapshot for Cursor sessions. Keep this file short.

## Product purpose

PreFlight AI reviews AI system architectures **before production** by simulating a multi-reviewer Design Review Board and producing a structured engineering report.

## Current version

**v1.0.0 — v1 MVP** (deterministic / rule-based; no LLM reasoning in production path)

## Current v1 functionality

- Architecture input form + example architecture presets
- Sequential Design Review Board UX (Queued → Reviewing → Complete)
- Five reviewers: Scalability, Observability, Security, Cost, Reliability
- Per-reviewer score, confidence, severity, vote, issues, recommendations, impact, reasoning
- Board summary: final decision, overall score, vote tally
- Detailed engineering report (executive metrics, strengths, risks, quick wins, category cards)
- `GET /health`, `POST /review`

## Stacks

| Layer | Stack |
|-------|--------|
| Frontend | Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, Python 3.12, Pydantic / pydantic-settings |

## Repository structure

```
frontend/     # UI, types, API clients, example catalogs
backend/app/  # api, core, schemas, services, reviewers, prompts, models, utils
docs/         # Engineering context for developers/agents
assets/       # Marketing / README media
AGENTS.md     # Cursor onboarding entrypoint
```

## Reviewer architecture

- `BaseReviewer` strategy interface
- Concrete reviewers under `backend/app/reviewers/`
- Shared helpers in `reviewers/common.py` (findings → category review, severity, vote)
- `ReviewService` runs reviewers and assembles the response
- `report_builder.py` owns overall score, status, strengths/risks/quick wins, board decision text

## Scoring / decision approach

- Category score: 0–10 (rule penalties)
- Vote from score: ≥9 APPROVED, ≥7 APPROVED WITH CONCERNS, else REQUIRES CHANGES
- **Final board decision = worst vote** across reviewers
- Overall score: blended category average (×10) with cache/monitoring gap penalties

## Current limitations

- No authentication or persistence
- LLM reviewer path is partially implemented and not runtime-activated in the board flow
- LLM evaluation/benchmarking and LLM operational telemetry are not implemented
- Frontend board animation is UX-only; results come from FastAPI

## Phase 2 direction

Specialized LLM reviewers, orchestration/moderator synthesis, and evaluation of reviewer quality — without abandoning structured board + report UX.

## Phase 2 status

Implemented:
- OpenAI-backed `LLMProvider` path (`LLMProvider` + `OpenAIProvider`)
- Structured Pydantic LLM reviewer results
- Shared LLM reviewer execution helper (`run_llm_category_review(...)`)
- `SecurityLLMReviewer`
- `ScalabilityLLMReviewer`
- `ReliabilityLLMReviewer`
- `ObservabilityLLMReviewer`
- `CostLLMReviewer`
- Deterministic score-to-vote policy reused for LLM reviewer outputs
- Concurrent `LLMReviewOrchestrator` across all five specialized LLM reviewers
- Reviewer-level failure isolation with normalized success/failure outcomes
- Orchestration result contract for complete/partial/failed board evidence
- Focused mocked tests for provider, shared helper, and implemented reviewers
- Phase 2.0 frozen evaluation baseline artifacts (evaluation + adjudication + analysis)
- Phase 2.1 calibration experiment completion (25/25 evaluation success + adjudication)
- Phase 2.1 validator robustness fix and passing test suite (`75` tests)
- Phase 2.2 evidence-basis separation intervention and follow-on robustness clarifications (prompt + validator wording-recognition hardening)
- Phase 2.2 clean 3-case live preflight gate (Security/Cost/Reliability all SUCCESS with validator PASS)
- Phase 2.2 controlled 25-case run artifact recorded (`19` SUCCESS / `6` validation failures)
- Phase 2.2 partial human adjudication artifact recorded (`19` adjudicated / `6` non-adjudicable validation failures) with frozen rubric unchanged

Not yet implemented:
- LLM moderator/synthesizer
- Runtime activation of LLM reviewers in production board flow
- LLM evaluation/benchmarking
- Production LLM observability
- Token/cost tracking
- Broader Production AI Engineering Reviewer modules

v1 deterministic reviewers remain the Phase 2 evaluation baseline.

Current experimental interpretation:
- Phase 2.1 delivered a strong severity-calibration gain and slight category-relevance improvement with preserved alignment/usefulness, but evidence discipline remained mixed.
- Phase 2.2 has completed a controlled 25-case run, but only `19/25` cases are semantically adjudicable due to `6` deterministic validation failures.
- Do not treat Phase 2.2 as successful or failed yet; official apples-to-apples cross-phase percentage comparison is not established until methodology for incomplete adjudication denominator is resolved.

## Important constraints

- Do not add AI SDKs or databases unless the task explicitly requires Phase 2 work
- Preserve layered backend and frontend service boundaries
- Do not commit/push unless explicitly requested
- Prefer reading this file + targeted code over full-repo scans

## Development status

v1 Design Review Board MVP is released (`v1.0.0`). Phase 2 has OpenAI provider support, all five specialized LLM reviewers, and concurrent orchestration with reviewer-level failure isolation implemented. Moderator/synthesis, runtime activation in the current UI path, evaluation, and production LLM operational tracking are still pending. The deterministic v1 board remains the baseline path for comparison.
