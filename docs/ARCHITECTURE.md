# Architecture — PreFlight AI v1

Technical map of the shipped Design Review Board. Concise by design.

## Frontend (`frontend/`)

| Area | Role |
|------|------|
| `app/` | Next.js App Router pages/layout |
| `components/home/` | Page orchestration (`HomeExperience`) |
| `components/examples/` | Example architecture gallery |
| `components/review/` | Form, board animation, board summary, report cards |
| `components/ui/` | shadcn primitives |
| `lib/` | Constants, validation, board timing, example catalog, load helpers |
| `services/` | HTTP clients (`review`, `health`) — UI does not call `fetch` directly |
| `types/` | Contracts mirrored from backend schemas |

**UX flow:** load example / edit form → convene board → sequential reviewer cards (~3–5s) → board summary → detailed report.

## Backend (`backend/app/`)

| Area | Role |
|------|------|
| `main.py` | FastAPI app, CORS, router mount |
| `api/` | Thin HTTP routers (`health`, `review`) |
| `core/` | Settings (`app_name`, `app_version`, CORS) |
| `schemas/` | Pydantic request/response DTOs |
| `services/` | `ReviewService`, `report_builder` |
| `reviewers/` | Pluggable deterministic reviewers |
| `prompts/` | Reserved for future LLM prompts |
| `models/` | Reserved for persistence |
| `utils/` | Pure helpers (e.g. `is_none_value`) |

## Request flow

```
POST /review
  → api/review.py
  → ReviewService.review(request)
  → each BaseReviewer.review(request) → CategoryReview
  → report_builder (score, status, strengths, risks, quick wins, final_decision, board_summary)
  → ArchitectureReviewResponse
```

## API / schema boundary

- Inbound: `ArchitectureReviewRequest` (validated stack fields + traffic)
- Outbound: `ArchitectureReviewResponse` (overall fields + `reviewer_votes` + `categories`)
- Category payload includes score, confidence, severity, vote, summary, issues, recommendations, estimated_impact, engineering_reasoning
- Votes: `APPROVED` | `APPROVED WITH CONCERNS` | `REQUIRES CHANGES`
- Severity: `LOW` | `MEDIUM` | `HIGH` | `CRITICAL`

Pydantic schemas are the public contract; routers should not invent ad-hoc dict shapes.

## Reviewer strategy pattern

```
BaseReviewer
  ├── ScalabilityReviewer
  ├── ObservabilityReviewer
  ├── SecurityReviewer
  ├── CostReviewer
  └── ReliabilityReviewer
```

- `DEFAULT_REVIEWERS` registers the board order
- Each reviewer collects `ReviewFindings`, then `build_category_review()` normalizes severity + vote
- New dimensions = new reviewer module + register in `DEFAULT_REVIEWERS`

## Final board decision

1. Each category gets a vote from its score (`derive_vote`)
2. `derive_final_decision()` applies **worst-vote wins**
3. `build_board_summary()` narrates tally + decision
4. Overall score is separate (category blend + explicit cache/monitoring penalties)

Frontend board animation does not compute decisions; it displays API results after the timed sequence.

## Phase 2 — LLM review architecture (current)

### Implemented

| Component | Current state |
|---------|--------|
| `LLMProvider` | Implemented as a thin reviewer-facing abstraction (`services/llm/provider.py`) |
| `OpenAIProvider` | Implemented provider using OpenAI Responses structured parse (`services/llm/openai_provider.py`) |
| Shared reviewer execution | Implemented `run_llm_category_review(...)` for shared serialization, provider call, validation, deterministic vote derivation, and `CategoryReview` mapping |
| Structured reviewer result | Implemented Pydantic contracts for all five specialized LLM reviewer outputs |
| Specialized reviewers | `SecurityLLMReviewer`, `ScalabilityLLMReviewer`, `ReliabilityLLMReviewer`, `ObservabilityLLMReviewer`, `CostLLMReviewer` implemented |
| Review orchestration | Implemented concurrent `LLMReviewOrchestrator` service for five LLM reviewers (`services/review_orchestrator.py`) |
| Failure isolation | Implemented reviewer-level failure normalization (success/failure per category) so one reviewer failure does not crash the whole run |
| Orchestration result contract | Implemented focused orchestration schemas (`schemas/orchestration.py`) for complete/partial/failed outcomes and per-reviewer status |
| Deterministic vote policy | Implemented via existing score-to-vote derivation reused by shared helper |
| Test coverage | Focused mocked/unit tests for provider, shared helper, LLM reviewers, and orchestrator |

### Planned (not yet implemented)

| Component | Intent |
|---------|--------|
| Board moderator / synthesis | Synthesize cross-reviewer findings |
| Evaluation | Measure reviewer quality, consistency, and regressions |
| Runtime integration | Activate LLM reviewers in production board flow |
| Production LLM observability | Capture operational LLM telemetry in production |
| Token/cost tracking | Track LLM token usage and spend |
| Broader reviewer modules | Add additional Production AI Engineering Reviewer modules beyond the current five |

## Phase 2 — Review orchestration (implemented service)

```text
Architecture
    ↓
Review Orchestrator
    ↓
┌──────────────┬──────────────┬──────────────┐
Security    Scalability    Reliability
Observability     Cost
└──────────────┴──────────────┴──────────────┘
    ↓
Normalized reviewer results
    ↓
Board decision / future moderator
```

- Implemented orchestration role: invoke reviewers concurrently, normalize success/failure per reviewer, and return board-ready reviewer results.
- **Planned only:** moderator/synthesizer remains a later layer.
- Intended moderator role (later): interpret reviewer outputs and produce cross-category synthesis.

### Relationship to v1 deterministic reviewers

- v1 rule-based reviewers remain the **baseline** for Phase 2 evaluation and comparison
- Phase 2 should extend the board model, not throw away deterministic coverage
- LLM path is additive; details of final coexistence/activation policy are still open
