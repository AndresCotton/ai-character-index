---
name: 4-sweep-spec-coverage
description: Stage 4 of a behaviour sweep (parallel track, independent of stages 1-3) -- extract every passage of the local spec copies bearing on one behaviour as pinned locators with resolver-verified verbatim quotes, assign per-spec verdict and depth, and stop at Gate 4.
---

# Sweep stage 4: spec coverage

Input: the behaviour (number, name, definition, facets). Independent of stages 1-3;
may run in parallel with them.
Output: `research/sweeps/NN-<slug>/4-spec-coverage.md`.
Read first: `specs/CITATION.md` -- the locator format, block/sentence rules, and
normalizations are all defined there. Resolver: `engine/spec-cite/cite.py`. Ground
truth: the local mirrors under `specs/` (versions per `SPECS` in `cite.py`).

## Mirror freshness (before the term sweep)

The sweep's claim is "checked against the latest published version of each spec as
of the sweep date" -- that claim depends on this step. Refresh the mirrors with
`engine/spec-watch/pull-latest.sh` (or verify upstream directly that they are
current), and record in `4-spec-coverage.md` the mirror versions and the date they
were confirmed latest. If a pull changes a mirror, flag it: existing locators in
`data/coverage.json` must re-resolve before new work builds on the moved text.

## Term sweep

- **Author the term list** (this is the judgement step -- do it before running
  anything): the behaviour's own words, synonyms, antonym-phrases, and spec-register
  phrasings (behaviour-1 precedent: sycophan, flatter, obsequi, placate, "want to
  hear", "sounding board", white lie, "doles out praise", "push back"). Each term is a
  case-insensitive **regex** -- a plain word is a literal (substring, so `calibrat`
  catches calibrated/calibration); use `\b` to word-bound an ambiguous short term
  (`\blie`, not inside "believe") and `|` for alternatives (`deceiv|decept`). Write
  phrases apostrophe- and dash-free (`t know` catches curly and straight "don't know").
- **Persist it** to `research/sweeps/NN-<slug>/terms.txt`: one term per line,
  everything from `#` to end-of-line ignored (use `#` for notes). This committed file
  is the sweep's input.
- **Run the sweep -- do not grep or count by hand:**
  `python3 engine/spec-cite/cite.py sweep research/sweeps/NN-<slug>/terms.txt`
  It prints the per-mirror hit-count table (zero-hit terms included). Paste that table
  into the artifact verbatim.
- **Check the tool's feedback before continuing:** on stderr it echoes `parsed N
  terms` -- confirm N matches what you wrote -- and warns on lines that look
  mis-formatted (list markers, unmatched quotes, prose, duplicates, unescaped regex
  metacharacters). Fix `terms.txt` and re-run until N is right and there are no warnings.
- **Read the enclosing section of every hit:** the operational content is often one
  paragraph away from the term hit. The hit table is a starting point, not the passage
  set.

## Excerpt workflow (per passage kept)

1. `cite.py find <spec> "<phrase>"` -- candidate locator.
2. `cite.py show "<spec> > <section>"` -- pick the exact ¶/sentence span from the
   tool's numbering. Never count blocks or sentences by hand.
3. `cite.py resolve "<locator>"` -- store the resolver's output as the quote,
   byte-for-byte. Never transcribe.

- Nothing is elided inside a quote; a discontinuous quotation is two locators.
- Example blocks are cited whole (the stored quote is the caption line; mark
  `example_block`).
- Smallest enclosing section; full heading path for constitution locators; stable
  `#anchors` for the Model Spec, noting each section's authority level (root/user/...)
  alongside the excerpt.
- Each excerpt gets a one-line **role** (why it is in the set). Adjacent/boundary
  passages are kept but marked `adjacent`, with the reason they sit outside the core
  construct (they define the construct's edges for eval designers).

## Verdict and depth (per spec)

Verdict: covered / partial / not-in-spec. Depth 0-4 scored against the anchored
rubric in `research/spec-coverage-depth-rubric.md` (0 absent / 1 named /
2 discussed / 3 prescribed / 4 demonstrated), with a one-line rationale naming
what is present and what is missing in the rubric's terms. The rubric's boundary
tests (the grading test for 2 vs 3; what counts as a worked example for 3 vs 4)
settle border calls; its precedent table records how behaviours 1-3 map onto it.

## Gate 4 -- quotes are mechanical, not remembered

Render with evidence, then STOP.

- [ ] Mirror freshness confirmed this sweep (spec-watch run or upstream checked);
      mirror versions and check date recorded in `4-spec-coverage.md`.
- [ ] Term list documented, including zero-hit terms.
- [ ] Mechanical re-check passes: every locator re-resolved in a scripted loop and
      diffed against its stored quote -- paste the loop's output; zero mismatches.
- [ ] Every locator pins `spec@version` and uses the smallest enclosing section,
      with the full heading path for constitution citations.
- [ ] No elided quotes; example blocks cited whole.
- [ ] Every excerpt has a role line; adjacent items are marked with reasons.
- [ ] Verdict + depth rationale present for each spec.
- [ ] Human spot-read: the kept passages actually bear on the behaviour, and no
      passage the reviewer knows of is missing from the set.

## Pitfalls

- Curly vs straight apostrophes (and em dashes) break naive greps: search dash-free,
  apostrophe-free distinctive substrings.
- The sweep matches **substrings** by default, so a short/ambiguous term can over-count by
  matching inside unrelated words (`lie` matches "believe"). For a genuinely short/ambiguous
  term, **word-bound it with `\b`** in the term file (e.g. `\blie` matches "lie" at a word
  boundary, not inside "believe"); plain stems like `calibrat` stay unbounded.
- Grepping only the behaviour's name finds the naming passages and misses the
  operational ones (behaviour 1: the invariance rule contains no sycophancy term).
- Locators into an unpinned spec are meaningless after the next release; the version
  is mandatory in every stored citation.
