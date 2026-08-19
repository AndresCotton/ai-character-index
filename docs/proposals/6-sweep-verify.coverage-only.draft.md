> **Approved 2026-08-18** (repo-owner ruling, closeout list "Scope deletions" item: the `.claude/skills/` scope pass). The skills-pass PR promotes this file to `.claude/skills/6-sweep-verify/SKILL.md`.
> Rescoped replacement for `.claude/skills/6-sweep-verify/SKILL.md` under the model-spec-reader-only scope. Not a live skill until the skills-pass PR merges.
> Stage numbering (4/5/6) is kept for continuity with signed gate records in `research/sweeps/02-calibration/` and `03-action-honesty/`.

---
name: 6-sweep-verify
description: Stage 6 of a coverage sweep -- fresh-context audit of published coverage: locator re-resolution, payload identity, live render, gate-log completeness. Produces the final sign-off (Gate 6). Run in a new session or subagent that did not execute the sweep.
---

# Sweep stage 6: verify (coverage only)

Input: a behaviour whose stage-4 and stage-5 gates are signed.
Output: `research/sweeps/NN-<slug>/verify.md` -- findings, discrepancies, and their
resolution.

**Independence rule:** this stage is run by a context that did not produce the sweep
-- a fresh session or a subagent given only this skill and the behaviour number. The
auditor reads the repo and the live site; it does not read the sweeping session's
conversation. An auditor that watched the sweep shares its blind spots.

## Checks

1. **Quotes.** Every locator in `data/coverage.json` (and the stage-4 artifact)
   re-resolved with `engine/spec-cite/cite.py`; stored quotes byte-identical to
   resolver output. `publish-coverage.py --check` performs the same verification —
   re-run it here; an audit that trusts the publisher's earlier check without
   re-running it is not independent.
2. **Payload identity.** The behaviour's entries in
   `site/spec-reader/data/documents.json` match `data/coverage.json` exactly
   (verdict, depth, passage set). If the behaviour feeds the panel surface, its row
   in `site/llm-panel-review/data/behaviours.json` matches
   `data/reader-test-coverage.json`.
3. **Live render.** `node engine/verify-spec-reader.mjs` passes (and
   `engine/verify-reader-test.mjs` if the bench is affected): every passage anchors,
   no unresolved-anchor warnings, no console errors.
4. **Gate log.** The stage gates are signed with dates in `gates.md`; every open
   item accepted at a gate is recorded in the sweep record.

## Discrepancies

Each discrepancy is logged in `verify.md` with the owning stage. Fixes happen in
that stage's artifact first (noted in `gates.md`), then re-propagate through
publish. Re-run the affected checks after fixes; `verify.md` keeps both the finding
and its resolution -- a clean final report that hides a fixed discrepancy is a false
record.

## Gate 6 -- the sweep is done

- [ ] All four check sections ran; outputs pasted or linked in `verify.md`.
- [ ] Zero unresolved discrepancies; resolved ones documented with their fixes.
- [ ] Human signs the final line of `gates.md`: `sweep complete: <name>, <date>`.

## After Gate 6

Merge the sweep branch; the merge deploys the site automatically
(`.github/workflows/deploy.yml` fires on `site/**` changes — `pnpm deploy:site` is
the manual twin) and record the merge/deploy date in `gates.md` under Gate 6.

The behaviour's transparency chain is closed: every quote traces to a resolver call,
every published row to the gate-approved artifact, and every review step to a dated
sign-off.
