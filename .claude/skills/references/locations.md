# Fixed locations

Canonical table of repo paths + spec versions.

| Thing | Where |
|---|---|
| Local spec copies (ground truth for all quotes) | `specs/claude-constitution/20260120-constitution.md` (2026-01-20), `specs/openai-model-spec/model_spec.md` (v2025.12.18); current versions are whatever `SPECS` in `cite.py` registers |
| Spec citation convention + resolver | `specs/CITATION.md`; `engine/spec-cite/cite.py` (`find` / `show` / `resolve`) -- every stored quote must be resolver output for a pinned locator |
| Behaviour list | `research/core-behaviour-list.md` |
| Behaviour registry (identity source of truth) | `data/behaviours.json` |
| Data seeds | `data/coverage.json` (frozen ledger), `data/labs.json` |
