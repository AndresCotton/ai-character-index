# research/ — the canonical behaviour list

> Current-state doc: describes what exists now, not what should exist. Brought current with the Phase-2 stack (#28–#34) and the reader consolidation.

## Purpose
Defines the behaviours the index measures (`core-behaviour-list.md`). The per-behaviour sweep records that used to live under `sweeps/` are retired with the publish path, and the coverage ledger they fed (`data/coverage.json`) is frozen. Candidate-pool provenance (`sources/`) and the evidence-discovery sweep stages 1–3 were retired by the scope ruling (2026-08-19).

## Contents
| Path | Holds |
|---|---|
| `core-behaviour-list.md` | Canonical list: 12 behaviours (10 Tier 1, 2 Tier 2) + parked table; inclusion criteria; per-behaviour spec-coverage blocks and eval facets; stated as kept in sync with the Notion "Behaviours to track" page |
| `archive/behaviours-to-track.md` | Earlier draft, superseded 2026-07-10; 13 rows with older numbering/titles |

## Relationships
`core-behaviour-list.md` is prose, not machine-parsed: its definitions and facets reach the system by being hand-synced into the behaviour registry (`data/behaviours.json`), which drives the panel judge prompts and the reader builder's derived constants. The quotes in the frozen `data/coverage.json` were taken from the `specs/` mirrors via `specs/CITATION.md` + `engine/spec-cite/cite.py`; CI keeps re-resolving them (`tests/test_coverage_json.py`). `site/index.html` renders hand-maintained inline data and reads nothing from `data/`. The preserved cross-spec strict-reading judgment (the only analysis of its kind in the repo) lives in the repo-root `archive/general-welfare-strict-reading/`.

## Dependency map
```mermaid
graph LR
  CBL["core-behaviour-list.md"] -->|hand-synced definitions + facets| REG["data/behaviours.json (registry)"]
  REG -->|judge prompts, derived constants| PANEL["engine/panel/ + site/"]
  SPECS["specs/ mirrors"] -->|verbatim quotes (frozen)| DATA["data/coverage.json"]
```

## As-is observations
- `data/coverage.json` covers only behaviours 1–3 (6 rows) and is frozen. Behaviour identity is registry-driven (`data/behaviours.json`); `data/evals.json` was retired by the scope ruling.
- `methodology/mentee-project-archetypes.md` states `core-behaviour-list.md` is stale vs Notion for rows 11–13 (Notion has an "Interaction with others" group absent here).
