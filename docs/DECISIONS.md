# Engineering Decisions — PreFlight AI

Record of durable choices for v1. Reasoning is brief on purpose.

## Deterministic / rule-based reviewers in v1

**Decision:** v1 reviewers are pure rule engines (no LLM calls).

**Why:** Validate end-to-end workflow, UX, and report quality with reproducible outputs before introducing model variance, cost, and prompt ops.

## LLM reviewers deferred to Phase 2

**Decision:** Do not add OpenAI/LangChain/etc. in the v1 path.

**Why:** Keeps MVP shippable and demoable; Phase 2 can plug into the existing `BaseReviewer` / `prompts/` extension points.

## Five specialized review dimensions

**Decision:** Board members are Scalability, Observability, Security, Cost, Reliability.

**Why:** Mirrors a real design review board: separate concerns, clearer votes, and room to deepen rules (or later LLMs) per discipline.

## Worst-vote board decision policy

**Decision:** Final decision escalates to the most severe vote (`REQUIRES CHANGES` > `APPROVED WITH CONCERNS` > `APPROVED`).

**Why:** Matches engineering review practice—one serious blocker should not be averaged away.

## Monorepo structure

**Decision:** `frontend/` and `backend/` live in one repository.

**Why:** Single product surface for demos and releases; shared docs/context; independent toolchains still allowed.

## Layered backend architecture

**Decision:** `api` → `services` → `reviewers` / `models`, with `schemas` as the DTO boundary.

**Why:** Keeps HTTP thin, business orchestration testable, and reviewer strategies swappable without rewriting routes.

## Frontend network calls in `services/`

**Decision:** Components/hooks call `frontend/services/*`; they do not own raw `fetch` URLs.

**Why:** Centralizes API base URL, error parsing, and future auth headers; keeps UI presentational.

## Manual Git commits / releases

**Decision:** Agents do not commit or push unless the user explicitly requests it; releases (e.g. `v1.0.0`) are manual.

**Why:** Preserves human control over history, tags, and public GitHub state.

## Phase 2 — LLM provider (OpenAI first)

**Decision:** Phase 2 will initially use OpenAI as the LLM provider.

**Why:** One well-supported provider reduces early integration surface area; other vendors can be considered later if needed.

## Phase 2 — Provider abstraction

**Decision:** Reviewers depend on a small internal `LLMProvider` abstraction, not the OpenAI SDK directly.

Conceptually:

```text
Reviewer
  → LLMProvider
  → OpenAIProvider
  → OpenAI API
```

**Why:** Keeps reviewer logic provider-agnostic and testable. The abstraction stays intentionally small — not a generic enterprise multi-cloud framework.

## Phase 2 — Structured outputs

**Decision:** LLM reviewers return validated structured results rather than free-form text or hand-parsed JSON strings.

**Why:** Preserves the existing board/report contract, reduces brittle parsing, and makes evaluation against the deterministic baseline feasible.

## Phase 2 — Shared reviewer execution helper (composition)

**Decision:** LLM category reviewers share execution through a composition helper (`run_llm_category_review(...)`) instead of introducing a new class hierarchy.

**Why:** Centralizes provider invocation, reviewer-boundary validation, deterministic score-to-vote derivation, and `CategoryReview` mapping while keeping category-specific logic in small reviewer modules.

## Phase 2 — Deterministic baseline retained

**Decision:** v1 rule-based reviewers remain the evaluation baseline in Phase 2; they are not discarded when LLM reviewers are introduced.

**Why:** Provides a reproducible reference for quality, regressions, and fallback comparisons while LLM behavior is still being tuned.

## Phase 2 — Parallel reviewer execution

**Decision:** Independent LLM reviewers should execute concurrently during a board run.

**Why:** Parallel execution reduces end-to-end review latency compared with sequential reviewer invocation.

## Phase 2 — Isolated reviewer failures

**Decision:** A timeout or provider failure in one reviewer should not crash the whole board review.

**Why:** The orchestrator should normalize reviewer-level failures into structured per-category results so the board can explicitly report incomplete evidence.

## Phase 2 — Orchestration result contract

**Decision:** Orchestration returns explicit per-reviewer success/failure outcomes plus overall completeness status (`COMPLETE` / `PARTIAL` / `FAILED`), instead of forcing failed reviewers into synthetic scores.

**Why:** Preserves evidence integrity, avoids misleading board outputs, and keeps synthesis/runtime integration free to handle incomplete reviewer evidence transparently.

## Phase 2 — Orchestration and synthesis are separate

**Decision:** Keep orchestration and moderator/synthesis responsibilities separate.

**Why:** The orchestrator should only invoke reviewers, manage concurrency, collect outcomes, and normalize success/failure. A future moderator/synthesizer should interpret reviewer outputs, identify cross-category themes, and produce board-level engineering synthesis.

## Phase 2 — LLM path remains separate during development

**Decision:** Keep the deterministic v1 board intact while developing Phase 2, with LLM review able to run as a separate path.

**Why:** This preserves the baseline and enables later quality/regression comparisons between deterministic and LLM review behavior.

## Phase 2.0 baseline is frozen for comparison

**Decision:** Treat Phase 2.0 evaluation, adjudication, and analysis artifacts as immutable baseline references.

**Why:** Phase-to-phase comparisons must remain reproducible and auditable against a fixed benchmark.

## Phase 2.1 outcome interpretation

**Decision:** Record Phase 2.1 as a mixed result with a strong positive component rather than an unconditional success.

**Why:** Adjudication shows major severity-calibration improvement and slight category-relevance improvement, but evidence discipline did not improve.

## Phase 2.2 starts as a minimal prompt-only intervention

**Decision:** Introduce Phase 2.2 evidence-basis separation through shared prompt guidance first, without schema/provider/runner redesign.

**Why:** This isolates one variable for the experiment and directly targets the dominant Phase 2.1 failure mode (unspecified detail -> asserted deficiency/risk).

## Phase 2.2 validator is an integrity layer, not a semantic scorer

**Decision:** Keep Phase 2.2 validator checks focused on evidence-basis contract integrity (asserted-absence contradiction checks and mixed-basis guardrails), not broad natural-language semantic grading.

**Why:** The experiment evaluates model behavior using structured outputs plus human adjudication. The deterministic validator should prevent obvious label/content mismatches without becoming a brittle second evaluator.

## Phase 2.2 partial adjudication is not official cross-phase metric output

**Decision:** Treat the Phase 2.2 partial adjudication set (`19` adjudicated / `6` non-adjudicable validation failures) as internal evidence, not as official apples-to-apples phase-level percentages.

**Why:** Frozen Phase 2.0/2.1 methodology assumes `25` adjudicated records and uses `25` as denominator for dimension distributions. Reporting official Phase 2.2 percentages on denominator `19` would break strict comparability unless methodology is explicitly revised.
