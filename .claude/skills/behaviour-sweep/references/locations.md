# Fixed IDs and locations

Shared by all sweep stage skills. Update here, nowhere else.

| Thing | Where |
|---|---|
| Notion "Behaviours to track" page (per-behaviour toggles live here) | page `3983e0f9-3a80-8122-9a0a-fcdd70d1d1d2` |
| Notion "Evals by Behaviour" DB | data source `collection://834f8131-3166-4691-b191-52af08b9dde2` (has 0-4 number columns "Internal validity (0-4)", "External validity (0-4)", "Reproducibility (0-4)") |
| Notion "Evals Rubric" (RAND-based) | page `3963e0f9-3a80-8114-88a3-c25f4c0bacd4` |
| Notion "Spec Coverage by Behaviour" DB | data source `collection://c291b16b-f3d6-4522-8256-28e1e87b760c` -- one row per behaviour x spec; properties Verdict, "Depth (0-4)", References (compact locators), Spec version, Verified against local copy; row page body = verbatim excerpts |
| Local spec copies (ground truth for all quotes) | `specs/claude-constitution/20260120-constitution.md` (2026-01-20), `specs/openai-model-spec/model_spec.md` (v2025.12.18); current versions are whatever `SPECS` in `cite.py` registers |
| Spec citation convention + resolver | `specs/CITATION.md`; `engine/spec-cite/cite.py` (`find` / `show` / `resolve`) -- every stored quote must be resolver output for a pinned locator |
| Canonical write-up per behaviour | `research/sweeps/NN-<slug>.md` |
| Sweep working record (stage artifacts + gate log) | `research/sweeps/NN-<slug>/` (see the orchestrator skill for the layout) |
| Behaviour list (sweep input) | `research/core-behaviour-list.md` |
| Data seeds | `data/evals.json`, `data/coverage.json`, `data/labs.json` |
| Prototype | `design/prototypes/core-page.html` -- `B[NN]` object; 0-4 scales; `adh` may be `null` (rendering tolerates it) |
| Reference sweep output (content templates) | `research/sweeps/01-no-sycophancy.md` and the behaviour-1 Notion pages (predate the staged layout; their content structure is still canonical) |
