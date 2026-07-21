---
name: behaviour-sweep
description: Run a full evidence sweep for one behaviour of the AI Character Index as a staged pipeline with human-verified gates -- discover pre-existing evals, curate, score on the rubric, extract spec coverage, publish to Notion/repo/prototype, and audit. Use when asked to "sweep" a behaviour or complete its evidence/coverage sections.
---

# Behaviour sweep (orchestrator)

Staged pipeline established by the No Sycophancy sweep of 2026-07-12 and split into
stage skills on 2026-07-13. Argument: one behaviour from
`research/core-behaviour-list.md` (its number NN, name, definition, and facets).

Each stage is its own skill, produces a documented artifact, and ends at a **gate**:
a checklist the human verifies before the next stage may start. Read the stage skill
when you reach its stage -- this file only sequences them.

## Stages and gates

| # | Skill | Output artifact | Gate |
|---|---|---|---|
| 1 | `1-sweep-discover` | `register.md`, `1-dossiers.md` | G1: evidence base is real and complete |
| 2 | `2-sweep-curate` | `2-curation.md`, dispositions final | G2: curation is legible; the human owns the set |
| 3 | `3-sweep-score` | `3-scores.md` | G3: scores are auditable |
| 4 | `4-sweep-spec-coverage` | `4-spec-coverage.md` | G4: quotes are mechanical, not remembered |
| 5 | `5-sweep-publish` | three internal surfaces + `research/sweeps/NN-<slug>.md` | G5: internal publication faithful to the artifacts |
| 6 | `6-sweep-verify` | `verify.md` | G6: sweep complete (fresh-context audit) -> public site deploy |

Two independent tracks: **evidence** (1 -> 2 -> 3) and **spec** (4). Stage 4 may run
in parallel with 1-3; both tracks must be gated before stage 5. Stage 6 runs in a
fresh session or subagent that did not execute the sweep.

**Publication order** (Andrés, 2026-07-14): stage 5 is internal, preliminary
publication -- Notion, repo data, prototype. The public site is deployed
(`pnpm deploy:site`) only after Gate 6 signs the fresh-context audit: verified,
then public.

## Sweep directory

```
research/sweeps/NN-<slug>/     working record (committed with the sweep)
  register.md                 candidate register -- the spine; updated at every stage
  1-dossiers.md               discovery output
  2-curation.md               curation memo
  3-scores.md                 rubric scores + adherence extraction
  4-spec-coverage.md          excerpt sets, verdict, depth
  gates.md                    gate log: sign-offs, corrections, accepted open items
  verify.md                   stage-6 audit report
research/sweeps/NN-<slug>.md   canonical write-up, assembled at stage 5
```

The behaviour-1 sweep (`research/sweeps/01-no-sycophancy.md`) predates this layout;
its content structure remains the template for write-ups and Notion pages.

## Gate protocol (applies at every gate)

1. The stage skill finishes its artifact and renders its gate checklist in chat --
   each item with pointed evidence (fetch logs, command output, links into the
   artifact), never bare checkmarks.
2. **STOP.** Do not start the next stage. The human reviews the artifact against the
   checklist; the checklist tells them what to spot-check, not just what to accept.
3. Corrections loop within the stage; re-render the checklist after fixes.
4. On approval, append to `gates.md`: gate number, date, approver, corrections made,
   and any open items the human explicitly accepted.
5. An open item accepted at a gate is carried into the write-up's known-unknowns /
   epistemic-status section -- accepted never means dropped.
6. Gate N+1 work must not begin, even speculatively, before gate N is signed. The
   one exception is the stage-4 parallel track.

## Shared references

- Fixed IDs and file locations: `references/locations.md`
- Exclusion criteria, dispositions, register conventions: `references/exclusion-criteria.md`

## Transparency invariants (hold across all stages)

- Every candidate found is in the register with exactly one final disposition;
  leave-outs are documented, never deleted.
- Every stage's output is a committed artifact, not chat scroll.
- Every number carries model version + date; every quote carries a pinned locator;
  every claim carries an evidence tier.
- The gate log is the human-review record the epistemic-status blocks point to.
