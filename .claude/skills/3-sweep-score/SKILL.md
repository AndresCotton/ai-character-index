---
name: 3-sweep-score
description: Stage 3 of a behaviour sweep -- score each curated eval 0-4 on Internal validity / External validity / Reproducibility with per-checklist-item verdicts and evidence tiers, extract per-lab adherence numbers with full provenance, and stop at Gate 3. Requires Gate 2 signed.
---

# Sweep stage 3: score

Input: the curated set + `1-dossiers.md`, with Gate 2 signed.
Output: `research/sweeps/NN-<slug>/3-scores.md`; register Used-downstream column
marked `scored` per eval.
Operationalization reference: `research/sweeps/01-no-sycophancy.md`, sections "Rubric
operationalization (v0)" and "Appendix A" -- follow their structure exactly. Rubric
source of truth: the Notion Evals Rubric (RAND, Paskov et al. 2025).

## Scoring

0-4 per dimension (I / E / R):

| Score | Meaning |
|---|---|
| 4 | Gold standard on essentially all applicable checklist items |
| 3 | Solid on core items, minor gaps (e.g. no power analysis) |
| 2 | Sound core design, one notable weakness (e.g. unvalidated judge, no uncertainty) |
| 1 | Demonstrative rather than rigorous |
| 0 | Criterion essentially absent |

- **A score with no named checklist items is invalid.** Each dimension score is
  justified by listing the items met and unmet (IDs D1-Do7 as defined in the
  reference write-up).
- **15-item verdict matrix** per eval. Verdict vocabulary: met / partial / not met /
  **not reported** (the paper is silent) / **not verified** (we did not check) /
  n/a. NR and NV are different claims and are never collapsed; every NV goes on the
  known-unknowns list with what checking it would take.
- **Evidence tier on every verdict:** verified-by-us / paper's-claim / third-party.
- **Per-dimension confidence** (high / medium / low), with the reason whenever it is
  not high.

## Adherence extraction

Only where a paper reports Anthropic/OpenAI results (decision by Andrés, 2026-07-12:
yes, extract).

- **In-scope slice only.** Never credit progressive corrections (flips toward the
  correct answer) as failures. If the headline metric bundles in-scope and
  out-of-scope behaviour, extract the slice and name it (behaviour-1 precedent:
  SycEval's regressive rate, ELEPHANT's moral + framing dimensions).
- **Per-model first.** Record every reported result for every Anthropic/OpenAI model
  the paper covers, as a per-model table in `3-scores.md` -- each row with its
  underlying number, exact model version (or "unpinned", stated as such), and date.
  Older-model results are kept and dated, never discarded: the date label, not
  deletion, is what stops a 2023 number being read as current (Andrés, 2026-07-14).
- **Lab-level band = most recent model measured.** The single per-lab band the
  surfaces display is the band of the most recent model version that eval measured
  for that lab -- never an average across model generations. The per-model table
  travels to the write-up so the aggregation can be re-derived. #TODO (2026-07-14):
  surface the per-model table on the site behind a click -- niche detail, not
  top-level.
- Map onto the 0-4 band (0 failing, 1 poor, 2 mixed, 3 good, 4 meets target) and
  **always give the underlying number** so the mapping can be re-derived.
- Never invent a number. Missing = `null` with a reason. Everything is labeled
  historical -- a per-paper snapshot, not a current-model verdict.

## `3-scores.md` contents

Per-eval blocks (scores + item justifications + verdict matrix + adherence +
limitations + "what would change the scores"), the adherence summary table, the
known-unknowns list, and cross-cutting observations the matrix makes legible.

## Gate 3 -- scores are auditable

Render with evidence, then STOP.

- [ ] Every dimension score names its checklist items. Human spot-audit: pick one
      eval x dimension and confirm the named items and their verdicts support the
      score.
- [ ] The verdict matrix is complete for every curated eval; every NV appears on
      the known-unknowns list.
- [ ] Every verdict carries an evidence tier.
- [ ] Every adherence band has complete provenance (paper, exact version or
      "unpinned" stated, date), its underlying number, and its in-scope slice named.
- [ ] The per-model table is complete (every reported Anthropic/OpenAI model result
      recorded), and each lab band matches its most recent model per the
      aggregation rule.
- [ ] No invented adherence numbers; all missing cells are `null` with reasons.
- [ ] Any cross-eval comparison carries a facet mapping.
- [ ] "What would change the scores" is present per eval.

## Pitfalls

- Constructs fragment: different evals can rank the same models in opposite order
  (behaviour 1: SycEval vs ELEPHANT on Gemini). Never present cross-eval aggregates
  without a facet mapping.
- The most-quoted numbers are often from obsolete models; model version + date
  travel with every number, everywhere it appears.
- Judge circularity (model X grading model X) and judge validation on tiny samples
  are the most common hidden Internal-validity weaknesses -- check them explicitly.
