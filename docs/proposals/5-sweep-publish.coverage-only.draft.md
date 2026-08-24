> **Approved 2026-08-18** (repo-owner ruling, closeout list "Scope deletions" item: the `.claude/skills/` scope pass). This banner is stripped on promotion; the skills-pass PR promotes this file to `.claude/skills/5-sweep-publish/SKILL.md`.
> Rescoped replacement for `.claude/skills/5-sweep-publish/SKILL.md` under the model-spec-reader-only scope. Not a live skill until the skills-pass PR merges.
> Stage numbering (4/5/6) is kept for continuity with signed gate records in `research/sweeps/02-calibration/` and `03-action-honesty/`.

---
name: 5-sweep-publish
description: Stage 5 of a coverage sweep -- publish the gate-approved stage-4 coverage to the repo data layer and rebuild the reader payload; verify the publication and stop at Gate 5. Nothing is deployed publicly here. Requires Gate 4 signed.
---

# Sweep stage 5: publish (coverage only)

Input: the stage-4 artifact `research/sweeps/NN-<slug>/4-spec-coverage.md`, Gate 4
signed in `gates.md`.
Outputs: the behaviour's rows in `data/coverage.json` + a rebuilt reader payload.

**Nothing new is decided here.** Publish transcribes approved content. If
transcription surfaces an error in the stage-4 artifact, fix the artifact first, note
the fix in `gates.md` under its gate, then re-publish. Divergence between the
published rows and the artifact is always a bug.

**This stage is internal publication.** The public site updates when the payload
commit merges to main — merges touching `site/**` deploy automatically via
`.github/workflows/deploy.yml` — and that merge happens only after stage 6 signs
Gate 6.

## Repo

- **`data/coverage.json`:** the behaviour's rows with `locator` + `quote` citations
  (roles, `adjacent`/`example_block` flags), verdict, depth + note, spec version,
  verified date. Publish through `engine/publish-coverage.py
  research/sweeps/NN-<slug>` — it re-resolves every quote through
  `engine/spec-cite/cite.py` before writing. Run `--check` first; write only on a
  clean check.
- **`research/core-behaviour-list.md`:** extend the behaviour's spec-coverage
  pointers if stage 4 found passages the list missed.
- **Reader payload:** `python3 engine/build-spec-reader-data.py` rebuilds
  `site/spec-reader/data/documents.json` from `coverage.json` + the spec mirrors.
  (If the behaviour is one of the panel-surface rows in
  `data/reader-test-coverage.json`, `engine/panel/build_site_data.py` rebuilds the
  panel payload from that ledger.)
- Commit only the sweep's files (conventional format, e.g. `feat(coverage):
  behaviour NN <name>`).

The sweep record is `4-spec-coverage.md` + `gates.md` (precedent: behaviours 2–3).
The full-sweep write-up and its eval sections belong to stages 1–3 and are out of
scope.

## Gate 5 -- the publication is faithful to the artifact

Render with evidence (command outputs), then STOP.

- [ ] `publish-coverage.py --check` passes with zero mismatches.
- [ ] `jq` validates `coverage.json`; the new rows' locators + quotes byte-match
      `4-spec-coverage.md`.
- [ ] `build-spec-reader-data.py` succeeds and `node engine/verify-spec-reader.mjs`
      passes (every passage anchors, no console errors).
- [ ] Human: open the behaviour in a local reader and confirm the passages anchor
      and read correctly.
