---
name: behaviour-sweep
description: Run a full evidence sweep for one behaviour of the AI Character Index -- find pre-existing evals, score them on the rubric, complete the Notion page (evals block + verbatim spec-coverage excerpts), persist in the repo, and update the core-page prototype. Use when asked to "sweep" a behaviour or complete its evidence/coverage sections.
---

# Behaviour sweep

Repeatable procedure, established by the No Sycophancy sweep of 2026-07-12 (reference output: `research/evals/01-no-sycophancy.md`). Argument: one behaviour from `research/core-behaviour-list.md` (its number, name, definition, and facets).

## Fixed IDs and locations

| Thing | Where |
|---|---|
| Notion "Behaviours to track" page (per-behaviour toggles live here) | page `3983e0f9-3a80-8122-9a0a-fcdd70d1d1d2` |
| Notion "Evals by Behaviour" DB | data source `collection://834f8131-3166-4691-b191-52af08b9dde2` (has 0-4 number columns "Internal validity (0-4)", "External validity (0-4)", "Reproducibility (0-4)") |
| Notion "Evals Rubric" (RAND-based) | page `3963e0f9-3a80-8114-88a3-c25f4c0bacd4` |
| Local spec copies (ground truth for all quotes) | `specs/claude-constitution/20260120-constitution.md` (2026-01-20), `specs/openai-model-spec/model_spec.md` (v2025.12.18) |
| Canonical write-up per behaviour | `research/evals/NN-<slug>.md` |
| Data seeds | `data/evals.json`, `data/coverage.json`, `data/labs.json` |
| Prototype | `design/prototypes/core-page.html` -- `B[NN]` object; 0-4 scales; `adh` may be `null` (rendering tolerates it) |

## Procedure

1. **Research (parallel subagents).** Fan out 2-3 general-purpose agents over the eval literature for the behaviour: one per known-candidate cluster plus one broad sweep for 2024-current work. Require per eval: full citation; paper/code/data URLs each live-checked by actually fetching; metrics + dataset sizes; facet mapping against the behaviour's facets (and what falls outside the definition); rubric-relevant methodology facts (construct clarity, metric type, sample size, statistical uncertainty, sensitivity analyses, judge validation, release status, version pinning); per-model Claude/GPT results with exact versions; limitations and critiques from the literature.
2. **Curate.** Keep the top ~5 by (a) fit to the behaviour definition and (b) rubric quality (decision by Andrés 2026-07-12: curated ~5, not exhaustive). Every rejected candidate gets one line + reason -- curation must be legible. Instruments that merely repackage another eval's data are "ports", not new evidence.
3. **Score 0-4 on I/E/R** per the rubric operationalization in `research/evals/01-no-sycophancy.md` (4 = gold standard on essentially all applicable checklist items; 3 = minor gaps; 2 = one notable weakness, e.g. unvalidated judge or no uncertainty; 1 = demonstrative; 0 = absent). Justify each score by naming the checklist items met/unmet.
4. **Adherence extraction** (decision by Andrés 2026-07-12: yes, extract): where a paper reports Claude/GPT results, map the in-scope metric (never credit "progressive" corrections as failures) onto the 0-4 band with full provenance (paper, model version, date). Never invent a number; missing = `null`. Label everything historical, not a current-model verdict.
5. **Spec coverage excerpts.** Grep both local spec copies with behaviour-specific terms AND synonyms (for sycophancy: sycophan*, flatter*, "want to hear", "sounding board", placate...). Locate each hit's section heading (`awk` for the last `^#` heading before the line). Quote verbatim (keep original punctuation inside quotes; note any transcription), with section name, anchor, authority level, spec version, verified date. Assign verdict (covered / partial / not-in-spec) + 0-4 depth with a one-line depth rationale.
6. **Notion writes.** (a) One DB row per curated eval: properties = Name, Behaviour tag, Source/org, URL, Notes ("Assessed YYYY-MM-DD"), the three scores; page body = citation, links, what it measures, facet mapping, rubric table with justifications, adherence extraction, limitations. (b) On the Behaviours page, inside the behaviour's toggle: replace the pointer-style "Spec coverage" details with the verbatim excerpt set, and add an "Existing evals -- rubric-scored" details block: intro line, table (eval mention-links, facets, I/E/R, one-liner), sweep findings bullets, rejected-candidates line. Match existing tab indentation exactly in `update_content` old_str; read the enhanced-markdown spec resource first.
7. **Repo persistence.** Write `research/evals/NN-<slug>.md` (method, rubric operationalization, scored evals, rejected list, adherence table, spec excerpts, cross-cutting findings); update `data/evals.json` + `data/coverage.json`; extend `research/core-behaviour-list.md`'s spec-coverage pointers if the excerpt hunt found passages it missed. Commit only the sweep's files.
8. **Prototype.** Update `B[NN]` in `core-page.html`: real `cov` (depth + verbatim quote + note), `ins` (0-4 instrument strength -- be honest about facet gaps), `evals` (name, org+venue, `q:[I,E,R]`, `adh:{A,O}` or nulls, one-line note). Update the "illustrative" flags so swept clauses are labeled real. Syntax-check: extract the script and `node --check`; exercise `adhOf/adhAvg` on the new clause.
9. **Verify.** Every URL fetched live; every quote grep-verified against the local spec copies (match dash-free distinctive substrings; curly apostrophes differ from straight ones); re-fetch the Notion page and DB; `jq` the JSONs; confirm scores identical across research file, DB, evals.json, prototype.

## Learned pitfalls

- Sycophancy-style constructs fragment: different evals can rank the same models in opposite order. Never present cross-eval aggregates without a facet mapping.
- Headline metrics often bundle in-scope and out-of-scope behaviour (e.g. progressive flips); score and extract only the in-scope slice.
- Vendor self-reports (system cards, postmortems) are context for the independence-of-evidence finding, not index evidence.
- The most-quoted numbers are often from obsolete models; always carry model version + date next to any adherence number.
