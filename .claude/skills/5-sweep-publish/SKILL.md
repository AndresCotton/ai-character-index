---
name: 5-sweep-publish
description: Stage 5 of a behaviour sweep -- transcribe the gate-approved stage artifacts to the three surfaces (Notion, repo data + canonical write-up, core-page prototype), verify each surface, and stop at Gate 5. Requires Gates 1-4 signed.
---

# Sweep stage 5: publish

Input: stage artifacts 1-4, all four gates signed in `gates.md`.
Outputs: the three surfaces + the canonical write-up `research/evals/NN-<slug>.md`.
IDs: `.claude/skills/behaviour-sweep/references/locations.md`.

**Nothing new is decided here.** Publish transcribes approved content. If
transcription surfaces an error in a stage artifact, fix the artifact first, note the
fix in `gates.md` under its gate, then re-transcribe. Divergence between a surface
and its artifact is always a bug.

## Surface A: repo

- **Canonical write-up** `research/evals/NN-<slug>.md`, assembled from the stage
  artifacts. Template: `research/evals/01-no-sycophancy.md` -- method (quoting the
  Gate 2 curation-decision line); rubric operationalization with the 15 item IDs;
  spec coverage excerpts; curated evals; rejected candidates table; adherence
  summary; cross-cutting findings; Appendix A verdict matrix; and the whole-sweep
  **epistemic status and provenance** section: evidence tiers, known unknowns
  (NV items + open items accepted at gates), and the conflict-of-interest note (the
  sweep is run by Claude, an Anthropic model).
- **`data/evals.json`:** one entry per curated eval (per-eval `sources` array with
  verification status per link, `notion_page`, `quality_confidence`, adherence with
  provenance strings) plus the rejected entries; update the top-level `assessment`
  block to reflect the gate log honestly -- link `research/evals/NN-<slug>/gates.md`
  as the review record and do not claim more review than the gates record (a gate
  spot-audit is not an item-by-item human review).
- **`data/coverage.json`:** the behaviour's rows with `locator` + `quote` citations
  (roles, `adjacent`/`example_block` flags), verdict, depth + note, spec version,
  verified date.
- **`research/core-behaviour-list.md`:** extend the behaviour's spec-coverage
  pointers if stage 4 found passages it missed.
- Register: mark Used-downstream for every row (surfaces reached, or where a
  context/watchlist item is cited).
- Commit only the sweep's files (conventional format, e.g. `feat(evals): behaviour
  NN <name> sweep`).

## Surface B: Notion

Read the enhanced-markdown spec resource before any write. **Gotchas:** pass content
with real newlines (literal `\n` escapes corrupt the page); in `update_content`,
match the existing tab indentation exactly in `old_str`.

1. **One "Evals by Behaviour" DB row per curated eval.** Properties: Name, Behaviour
   tag, Source/org, URL, Notes ("Assessed YYYY-MM-DD"), the three 0-4 scores. Page
   body = full analysis page (template: any behaviour-1 eval row, e.g. the
   SycophancyEval page): "How to read this page" callout; citation; sources table
   listing every link with verification status (gated or unverified sources say so);
   what it measures; facet mapping; rubric summary table (score + confidence + basis
   per dimension); the 15-row item-by-item table (item ID, verdict, what we found,
   evidence tier); adherence extraction; limitations and critiques; epistemic status
   and provenance block (produced-by + human-review status, what was verified
   directly / from the paper / from third parties, what remains open, what would
   change the scores).
2. **Behaviours page, inside the behaviour's toggle:** replace the pointer-style
   "Spec coverage" details with the verbatim excerpt set, and add an "Existing evals
   -- rubric-scored" details block: intro line (including the AI-assisted transparency
   note, now pointing at the gate record), table (eval mention-links, facets, I/E/R,
   one-liner with paper/code links), sweep-findings bullets, rejected-candidates line.
3. **"Spec Coverage by Behaviour" DB, the behaviour's two rows:** properties Verdict,
   "Depth (0-4)", Spec version, References (compact locators), "date:Verified against
   local copy:start"; replace the row page body with the excerpt set (template: the
   behaviour-1 rows -- callout stating the convention + resolver + run date, then per
   excerpt one bold role line + locator in code + blockquote).

## Surface C: prototype (`design/prototypes/core-page.html`)

Update `B[NN]`: real `cov` (depth + verbatim quote + note), `ins` (0-4 instrument
strength -- honest about facet gaps), `evals` with full display fields: name,
org+venue, `q:[I,E,R]`, `conf:[...]`, `qNotes:[...]` (one-line per-dimension basis),
`links:[{t,u,int?}]` (paper / code / data / port / analysis-record with `int:true`),
`adh:{A,O}` or nulls, one-line note. Set `verified:"YYYY-MM-DD"` on the clause (it
drives the rubric explainer); flip the "illustrative" flags so swept clauses are
labeled real.

## Gate 5 -- every surface is faithful to the artifacts

Render with evidence (command outputs, re-fetched pages), then STOP.

- [ ] Repo: `jq` validates both JSONs; scores identical between `3-scores.md`, the
      write-up, and `evals.json`; register dispositions match the rejected lists;
      `coverage.json` locators + quotes byte-match `4-spec-coverage.md`.
- [ ] Notion: every written page re-fetched; tables render; no literal `\n`
      anywhere; scores, quotes, and locators match the stage artifacts.
- [ ] Prototype: extract the script and `node --check` it; exercise `adhOf`/`adhAvg`;
      render `openPanel(NN)` through a DOM shim probing for links, explainer, and
      notes; illustrative flags flipped; `verified` date set.
- [ ] Register: every row's Used-downstream is filled or explains why not.
- [ ] Human: open the behaviour's Notion toggle and one eval row page in the app and
      confirm they read correctly (rendering can differ from a re-fetch).
