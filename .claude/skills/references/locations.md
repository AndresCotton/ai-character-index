# Fixed locations

Shared by all sweep stage skills. Update here, nowhere else.

| Thing | Where |
|---|---|
| Local spec copies (ground truth for all quotes) | `specs/claude-constitution/20260120-constitution.md` (2026-01-20), `specs/openai-model-spec/model_spec.md` (v2025.12.18); current versions are whatever `SPECS` in `cite.py` registers |
| Spec citation convention + resolver | `specs/CITATION.md`; `engine/spec-cite/cite.py` (`find` / `show` / `resolve`) -- every stored quote must be resolver output for a pinned locator |
| Canonical write-up per behaviour | `research/sweeps/NN-<slug>.md` |
| Sweep working record (stage artifacts + gate log) | `research/sweeps/NN-<slug>/` |
| Behaviour list (sweep input) | `research/core-behaviour-list.md` |
| Data seeds | `data/coverage.json`, `data/labs.json` |
| Reference sweep output (content templates) | `research/sweeps/01-no-sycophancy.md` (predates the staged layout; its content structure is still canonical) |
