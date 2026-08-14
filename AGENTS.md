# AGENTS.md

Engineering onboarding for Cursor / AI agents working on **PreFlight AI**.

## What this is

PreFlight AI is a Design Review Board for AI system architectures. It evaluates stacks before production and returns structured engineering feedback.

**Current version:** `v1.0.0` (v1 MVP)

## Architecture (high level)

```
Next.js frontend  →  FastAPI backend  →  ReviewService  →  rule-based reviewers
                                                      →  board decision + report
```

Monorepo: `frontend/` + `backend/`.

## Implementation status

- **Shipped:** deterministic 5-reviewer board, vote + worst-vote decision, consultancy-style report, example architectures, animated board UX.
- **Phase 2 implemented:** OpenAI-backed `LLMProvider`/`OpenAIProvider`, structured Pydantic LLM result contracts, shared `run_llm_category_review(...)`, all five specialized LLM reviewers, deterministic score → vote policy, concurrent `LLMReviewOrchestrator`, reviewer-level failure isolation, orchestration result contract, focused mocked/unit tests.
- **Phase 2 not yet implemented:** board moderator/synthesis, runtime activation in the existing UI path, LLM evaluation/benchmarking, production LLM observability, token/cost tracking, broader Production AI Engineering Reviewer modules.
- **Not shipped (non-LLM platform):** auth, databases, LangChain, vector DB runtime deps.

## Engineering principles

- Prefer clean layered boundaries (`api` → `services` → `reviewers` / schemas).
- Keep frontend presentational; network I/O lives in `services/`.
- Keep v1 reviewers deterministic unless the task explicitly starts Phase 2 LLM work.
- Small, targeted changes; do not scan or rewrite the whole repo by default.

## How to use docs

1. **Always read first:** [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md)
2. Read other docs **only when relevant:**
   - [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — structure / data flow
   - [`docs/DECISIONS.md`](docs/DECISIONS.md) — why things are the way they are
   - [`docs/ROADMAP.md`](docs/ROADMAP.md) — what is next
3. **Do not** scan the entire repository unless the task requires it.
4. Public product copy lives in `README.md`; these docs are for engineering/agent context.

## Git

- **Do not commit or push** unless the user explicitly asks.
