---
name: 1-sweep-discover
description: Stage 1 of a behaviour sweep -- fan out research agents over the eval literature for one behaviour, build per-candidate dossiers and the candidate register, and stop at Gate 1. Invoked by behaviour-sweep, or directly when asked to find pre-existing evals for a behaviour.
---

# Sweep stage 1: discover

Input: one behaviour from `research/core-behaviour-list.md` (number NN, name, definition, facets).
Outputs: `research/evals/NN-<slug>/1-dossiers.md` and `research/evals/NN-<slug>/register.md`.
Read first: `.claude/skills/behaviour-sweep/references/exclusion-criteria.md` (register conventions) and `references/locations.md` in the same directory.

## Principle

Discovery is complete, not selective. Every instrument found enters the register --
including ones that will obviously be excluded. Exclusion is a documented decision at
Gate 2, never a silent omission during search: a candidate that never made the
register is invisible to every later check.

## Search protocol

1. **Seed list first.** Write down, before searching: candidates named in the
   behaviour's section of `core-behaviour-list.md`, candidates known from prior
   sweeps' watchlists, and anything the session already knows of. Each seed must be
   verified like any other candidate, not trusted.
2. **Fan out 2-3 parallel general-purpose agents:** one per known-candidate cluster,
   plus one broad sweep for 2024-current work (behaviour terms + "benchmark / eval /
   dataset"; venue programs; citation trails in both directions from the seeds).
3. **Search log.** Record per agent: scope, key queries, dates, and zero-result
   probes. A reader must be able to judge coverage from the log alone.

## Dossier requirements (one per candidate, no exceptions)

- Full citation (authors, year, venue, arXiv/DOI).
- Every URL (paper, published venue, OpenReview, code, data, ports, critiques,
  follow-ups) **fetched live during this sweep** with the result recorded. Dead or
  gated links are marked so -- never dropped.
- What it measures: metrics, dataset sizes, models covered.
- Facet mapping against the behaviour's facets, including what falls outside the
  definition ("maps to no facet" is a valid, required answer).
- Rubric-relevant methodology facts: construct clarity, metric type, sample size,
  statistical uncertainty, sensitivity analyses, judge validation, release status,
  version pinning.
- Last-activity date: the most recent of dataset/code release, maintained-port
  activity, or credible independent re-run, with its source (feeds the `X-STALE`
  two-year check at curation).
- Per-model Claude/GPT results with exact model versions, where reported.
- Limitations and critiques from the literature.
- An evidence tier on each fact: verified-by-us / paper's-claim / third-party.

No fact from model memory alone: every dossier claim traces to a source fetched this
sweep, or is explicitly marked `unverified`.

## Register

Create `register.md` per the conventions in `exclusion-criteria.md`. At this stage
fill only: candidate, primary source, found-by, and the prima facie facet-fit note
(in / borderline / out + candidate codes). Leave Disposition and Used-downstream
empty -- those belong to later stages.

## Gate 1 -- the evidence base is real and complete

Render this checklist in chat with pointed evidence per item (not bare checkmarks),
then STOP for sign-off per the behaviour-sweep gate protocol.

- [ ] Search log documents every agent's scope, queries, dates, and zero-result probes.
- [ ] Every seed-list item appears in the register (found, or explicitly marked no
      longer available / subsumed).
- [ ] Every register row has a dossier; missing dossier fields are marked missing,
      not silently absent.
- [ ] Every URL was fetched this sweep with its status recorded; dead and gated
      sources are marked, not dropped.
- [ ] No dossier fact rests on model memory alone.
- [ ] Every candidate has a facet mapping against the behaviour definition.
- [ ] Human spot-check: pick 2 candidates at random, open the primary source, and
      confirm the dossier's key numbers appear in it.

## Pitfalls

- The headline candidates are found by every search; the sweep's marginal value is
  the tail. Budget agent effort toward the broad 2024-current sweep, and treat "seed
  list confirmed, nothing new found" as a suspicious result worth one more probe.
- OpenReview and some publisher pages are Cloudflare-gated to fetchers: record
  "exists; gated -- not read" rather than guessing at contents.
