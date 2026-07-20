---
name: 2-sweep-curate
description: Stage 2 of a behaviour sweep -- assign every discovered candidate a final disposition (curated-to-saturation / rejected / watchlist / context / port) against the pre-registered exclusion criteria, and stop at Gate 2, the sweep's editorial decision point. Requires Gate 1 signed.
---

# Sweep stage 2: curate

Input: `register.md` + `1-dossiers.md`, with Gate 1 signed in `gates.md`.
Output: `research/evals/NN-<slug>/2-curation.md`; register Disposition column finalized.
Read first: `.claude/skills/behaviour-sweep/references/exclusion-criteria.md`, in
full. Every disposition uses its vocabulary and codes. If a candidate fits no code,
flag the taxonomy gap to the human at the gate -- do not stretch a code.

## Decision rule

Curate every candidate that (a) **fits** the behaviour definition -- its facets, not
an adjacent construct -- and (b) clears the **rubric quality** bar. Fit is checked
first: a brilliant paper on a different construct is `rejected:X-CONSTRUCT`.

The set's size is an outcome, not a target (decision by Andrés, 2026-07-14,
superseding the "~5" target of 2026-07-12). Stop adding when the next-best candidate
is **saturated**: it would add no new facet coverage, no independent corroboration of
an already-covered facet, and no methodological diversity (a different metric type or
elicitation design). Record the saturation judgment for the first candidate left out
-- that line is what makes the cutoff auditable. Keep fewer when the evidence is
thin, and say so.

The curated set should cover the behaviour's facets as well as the available evidence
allows; remaining facet gaps are named explicitly in `2-curation.md` (they seed the
cross-cutting findings and research-handoff candidates).

## Partial use

When a curated eval's construct is broader than the behaviour, record exactly which
subtests or slices are in scope in both the register (`slices: ...`) and the curation
memo (behaviour-1 precedent: ELEPHANT curated on moral both-sides + framing only;
SycEval's regressive cell only). Later stages may use only the recorded slices.

## Vendor self-reports

The test is replicability, not authorship (Andrés, 2026-07-14). A vendor-built eval
that is public and independently re-runnable -- released dataset, rubric, and judge
details -- is eligible index evidence, scored like any other (SycophancyEval is
Anthropic-authored and curated). Numbers from internal evals that cannot be inspected
(e.g. model-card claims) are `X-INDEPENDENCE` -> `context`, never index evidence --
but keep them in the dossier: a large gap between a lab's own pre-release numbers and
independent public measurement is itself a finding.

## `2-curation.md` contents

- The curated set, one short rationale paragraph each (fit + quality).
- Every exclusion: one line + criterion code -- legible enough that a reader could
  reconstruct the decision from the dossier.
- Facet coverage map of the curated set, with named gaps.
- Watchlist with each item's promotion condition; context items with the finding
  they inform.

## Gate 2 -- curation is legible and the human owns it

This gate is editorial, not only audit: the human confirms or overrides the
disposition of every candidate. Render with evidence, then STOP.

- [ ] Every register row carries exactly one final disposition; none pending.
- [ ] Every non-curated row has a criterion code plus a one-line reason.
- [ ] Ports are linked to their parent instrument.
- [ ] Partial-use slices are recorded for every curated eval whose construct is
      broader than the behaviour.
- [ ] Facet coverage of the curated set is mapped; gaps are named, not implied.
- [ ] Watchlist items carry promotion conditions; context items name their finding.
- [ ] The human has read both the curated list and the full leave-out list and
      confirms the set. Record as: `curation decision: <name>, <date>` (this line is
      quoted in the canonical write-up's Method section).

## Pitfalls

- An instrument that repackages another eval's data is a port, not new evidence --
  even when actively maintained (UK AISI's inspect_evals port).
- The `X-STALE` two-year clock runs from the instrument's latest credible activity
  (dataset/code release, maintained port, independent re-run), not the paper's year.
  A maintained port contributes no new evidence (`X-EVIDENCE-DEP`) but does reset the
  parent's staleness clock -- SycophancyEval (2023) stays curated because the UK AISI
  port keeps it alive.
- Constructs that merely sound like the behaviour (delusion-validation vs factual
  claim-shifting) are `X-CONSTRUCT` regardless of paper quality.
- A rejected candidate can still be load-bearing as context or a design template
  (ELEPHANT's paired-perspective flip for facet 1.2) -- the disposition records the
  role, it does not erase the item.
