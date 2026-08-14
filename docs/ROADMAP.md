# Roadmap — PreFlight AI

Engineering roadmap for agents. Not a marketing doc.

## Completed

- v1 Design Review Board MVP
- Five deterministic reviewers (Scalability, Observability, Security, Cost, Reliability)
- Review workflow UI (form, board animation, votes)
- Engineering report (executive summary, strengths/risks/quick wins, category detail)
- Example architectures gallery
- README / repository public launch
- **v1.0.0** release tag
- Phase 2 OpenAI-backed LLM provider foundation (`LLMProvider` + `OpenAIProvider`)
- Phase 2 shared LLM reviewer execution helper (`run_llm_category_review(...)`)
- Phase 2 Security LLM reviewer
- Phase 2 Scalability LLM reviewer
- Phase 2 Reliability LLM reviewer
- Phase 2 Observability LLM reviewer
- Phase 2 Cost LLM reviewer
- Phase 2 Review Orchestrator (concurrent execution + reviewer-level failure isolation)
- Phase 2 orchestration result contract (normalized complete/partial/failed outcomes)
- Phase 2 focused mocked/unit test coverage for provider, shared helper, all five LLM reviewers, and orchestrator

## Next (Phase 2)

- Board moderator / synthesis layer
- Evaluation of reviewer quality (consistency, usefulness, regression harness)
- Runtime integration of LLM review path with existing board/UI flow
- Production LLM observability and token/cost tracking

## Future modules

- Prompt Review
- RAG Review
- Agent Review
- Repository Review
- Broader Production AI Engineering Reviewer modules

## Notes

- Prefer extending `BaseReviewer` + `prompts/` over rewriting the board UX
- Keep deterministic reviewers available as baselines/fallbacks when LLMs arrive
- Do not treat future items as in-scope unless the current task says so
