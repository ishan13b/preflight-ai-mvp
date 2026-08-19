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
- Phase 2.0 evaluation baseline frozen with adjudication + analysis artifacts
- Phase 2.1 calibration experiment completed (full 25-case run + human adjudication)
- Phase 2.1 validator robustness patch and passing test suite (`75` tests)
- Phase 2.2 evidence-basis intervention refinements:
  - validator robustness evolution for wording recognition and asserted-absence distinction
  - explicit mixed-clause split guidance in shared calibration addendum
- Phase 2.2 post-change checks: focused and full reviewer suites passing, lint clean
- Phase 2.2 clean live preflight gate (Security/Cost/Reliability all pass in a single controlled pass)
- Phase 2.2 controlled 25-case run completed (`25` attempted, `19` SUCCESS, `6` validation failures)
- Phase 2.2 partial adjudication artifact completed with frozen rubric (`19` adjudicated, `6` non-adjudicable validation failures)

## Next (Phase 2)

- Resolve Phase 2.2 methodology for official cross-phase reporting when adjudicable denominator is `19/25` instead of frozen `25/25`
- Decide methodologically valid path to complete apples-to-apples Phase 2.0 -> 2.1 -> 2.2 comparison without silently changing the frozen denominator assumptions
- Publish final Phase 2.2 interpretation only after the denominator/comparability decision is explicit
- Board moderator / synthesis layer
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
