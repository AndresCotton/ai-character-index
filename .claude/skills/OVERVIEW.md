# .claude/skills/ — retired procedure layer

> Current-state doc: describes what exists now, not what should exist. Brought current with the reader consolidation.

## Purpose

Former agent-executable playbook for the coverage workflow. The coverage-sweep pipeline it documented (the `sweep-coverage`, `sweep-publish`, `sweep-verify`, and `spec-coverage-pass` skills) is retired with the publish path; the coverage ledger (`data/coverage.json`) is frozen. The directory now holds only pointer documents.

## Contents

| Path | What it is |
|---|---|
| `README.md` | Pointer doc: no live skills here; where the procedures moved. |
| `references/locations.md` | Fixed locations: spec mirrors + pinned versions, the citation convention, the behaviour list, the data seeds. |

## Relationships

- Root `AGENTS.md` points here for the status of the procedure layer; the live procedures are `AGENTS.md` itself (clone/fork pathway), `engine/README.md` (user specs), and `engine/panel/README.md` (panel mechanics).
- `references/locations.md` restates facts whose sources are `engine/spec-cite/cite.py` (`SPECS` registry), `specs/CITATION.md`, `research/core-behaviour-list.md`, and `data/`.

## As-is observations

- The retired skills' gate records (signed `gates.md` files) went with the sweep directories they lived in; the coverage records they approved remain in the frozen `data/coverage.json`, machine-verified in CI by `tests/test_coverage_json.py`.
