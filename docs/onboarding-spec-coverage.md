# Onboarding: the spec-coverage tooling

Welcome. This document is the map for the part of the AI Character Index you'll
own: the **tools and process that turn a behaviour we want to track into a
coverage assessment**. It tells you where every moving part lives, walks the
pipeline end to end, and marks what is in scope for this collaboration and what
is not.

Read this first, then follow the "Suggested reading order" at the bottom -- it
sends you through the real files in the order they run.

---

## 1. What this project is (the 90-second version)

The index maps, for each frontier lab, three strata per behaviour:

```
  behaviour  →  spec coverage  →  strength of public evaluation evidence
```

- **Spec coverage** answers one question, per behaviour and per lab: *what does
  the lab's own published specification declare about this behaviour, and in
  what depth?* It is scored from the public documents alone.
- **Evidence strength** is a separate track about how well the behaviour is
  actually measured in the wild (papers, their quality, etc.).

**You work on the first one.** The public copy that states the coverage question
in plain language is `methodology/site-copy-how-we-assess-coverage.md` -- read it
once; it is the human-facing summary of everything below.

The wider system design (Notion → git → static site) is in `PLAN.md`. You rarely
need it, but §1 and §2 give the context.

---

## 2. Scope of this collaboration

**In scope -- the spec-coverage track (Stage 4 of a sweep + its publication):**

- `Skill 4` (`.claude/skills/4-sweep-spec-coverage/SKILL.md`) -- your primary
  procedure. It defines how a behaviour's spec passages are extracted.
- The citation resolver (`engine/spec-cite/cite.py`) and its convention
  (`specs/CITATION.md`).
- The depth rubric (`methodology/spec-coverage-depth-rubric.md`).
- The publish + verify tooling (`engine/publish-coverage.py`,
  `engine/build-spec-reader-data.py`, `engine/verify-spec-reader.mjs`).
- The coverage data (`data/coverage.json`) and the spec reader
  (`site/spec-reader/`).

**Out of scope (owner ruling) -- the evidence / evals track:**

- Finding pre-existing evals, judging paper quality, scoring the rubric,
  extracting lab adherence numbers. That is `Skills 1-3`
  (`1-sweep-discover`, `2-sweep-curate`, `3-sweep-score`). The
  staged-pipeline artifacts of that track (the stage 1-3 sweep files and
  `data/evals.json`) have been deleted under the owner's scope ruling --
  the deliverable is the model-spec reader only. (One pre-staged sweep
  write-up, `research/sweeps/01-no-sycophancy.md`, survives pending a
  separate owner ruling.) **You can ignore all of it.**

The two tracks are deliberately independent: Stage 4 runs in parallel with
Stages 1-3 and shares none of their data. So you can work on the whole coverage
pipeline without ever touching an eval.

**The goal of the initial collaboration** is a cleaner, better-structured, and --
above all -- **reproducible and well-documented** spec-coverage process: the same
behaviour run against the same specs should always yield the same coverage
assessment, and every step should be documented well enough that someone else can
re-run it and reproduce the result. Step 2 is the LLM panel
(§3 explains the method). This is about
cleaner process and code, not new features.

**This collaboration could be expanded** into building better tooling for
identifying contradictions in the model specs.

---

## 3. The pipeline: behaviour → coverage assessment

This is the heart of the job. Each step names the file(s) it touches.

```
 (1) BEHAVIOUR              research/core-behaviour-list.md   (id, name, definition, facets)
        │
        │  Skill 4  +  specs/CITATION.md  +  engine/spec-cite/cite.py
        ▼
 (2) SCORE PASSAGES         specs/*  (ground truth)  →  LLM panel, cite, author verdict
        │                   methodology/spec-coverage-depth-rubric.md  (score depth 0-4)
        ▼
 (3) STAGE-4 ARTIFACT       research/sweeps/NN-<slug>/4-spec-coverage.md
        │                   (verdict + depth + every excerpt, resolver-verbatim)
        │  Gate 4: human sign-off  →  gates.md
        ▼
 (4) PUBLISH DATA           engine/publish-coverage.py  →  data/coverage.json
        │
        ▼
 (5) BUILD READER PAYLOAD   engine/build-spec-reader-data.py
        │                     →  site/spec-reader/data/documents.json
        ▼
 (6) PRESENT + VERIFY       site/spec-reader/  (index.html, app.js, styles.css)
                            engine/verify-spec-reader.mjs  (headless render check)
```

### Step by step

1. **Input -- the behaviour.** The canonical list of behaviours (currently 12,
   grouped into 5 categories) lives in `research/core-behaviour-list.md`: each
   has an id, name, definition, and facets. That prose is the sole input to a
   coverage pass. (It is mirrored from a Notion page, but for your purposes the
   markdown file is the source.)
2. **Score the passages.** Against the two mirrored specs in `specs/`, every
   passage is graded for relevance to the behaviour by a **panel of three
   frontier LLMs** (2 core / 1 related / 0 neither per judge; a passage's score
   is the sum, max 6). The pipeline lives in `engine/panel/` and is run per
   behaviour with a dry-run-first driver; each kept passage carries a **locator**
   that pins the spec version and section, a quote produced by
   `engine/spec-cite/cite.py` (never typed by hand), and every judge's named verdict. The procedure is
   `Skill 4`; locator rules are `specs/CITATION.md`. Each spec then gets a
   **verdict** (covered / partial / not-in-spec) and a **depth 0-4** scored
   against `methodology/spec-coverage-depth-rubric.md` -- these remain authored
   judgments, made from the panel's citation set.
   *"The panel in detail" below covers the method's properties.*

3. **The Stage-4 artifact.** All of the above is written to
   `research/sweeps/NN-<slug>/4-spec-coverage.md`. This file is both the human
   record and a **machine-parsed contract** (see §5). It ends at **Gate 4**: a
   checklist the human verifies, then signs in `gates.md`. Nothing publishes
   before the gate is signed. The behaviour-2 artifact
   (`research/sweeps/02-calibration/4-spec-coverage.md`) is the canonical template
   -- copy its shape exactly.

4. **Publish to the canonical data.** `engine/publish-coverage.py
   research/sweeps/NN-<slug>` parses the artifact, **re-resolves every quote
   byte-for-byte** through `cite.py`, and rewrites that behaviour's records in
   `data/coverage.json`. That JSON file is the single source of truth the rest of
   the system renders from. `--check` mode re-verifies and diffs without writing.
5. **Build the reader payload.** `engine/build-spec-reader-data.py` reads
   `data/coverage.json`, joins it to the raw spec markdown and per-behaviour
   metadata, and emits the static blob `site/spec-reader/data/documents.json`.
   **Adding a newly-published behaviour requires adding it to the `BEHAVIOURS`
   list in this script** (id, slug, name, definition, category).
6. **Present and verify.** The public spec reader (`site/spec-reader/`) renders
   `documents.json`: it shows each spec with the behaviour's passages anchored in
   place. `engine/verify-spec-reader.mjs` drives it headlessly and asserts that
   every behaviour × spec view anchors exactly its published passage count with
   no console errors. This is the closest thing to an end-to-end test.

The **campaign wrapper** that runs steps 1-6 for one behaviour, with a git
commit at each step on a per-behaviour branch merged by PR, is the
`spec-coverage-pass` skill (`.claude/skills/spec-coverage-pass/SKILL.md`). Read
it to see the exact ordering, commit messages, and verification commands.

### The panel in detail (step 2)

Every passage of both specs is graded against the behaviour's definition by
three frontier models (`engine/panel/`); relevance is judged against the
definition alone, and a re-run against the same spec version is a single
logged, resumable command. The judgement inputs live in the behaviour's
definition fields (`behaviours.json`: definition, optional clarifications and
scope); the mechanics are a script with an append-only run log. Provider
failures are caught, named, and substituted openly -- see the failure modes and
substitution rules in `Skill 4`. Earlier methods and their artifacts are
preserved under `research/sweeps/` and `behaviours-for-adria/`, which also hold
the supplied definitions.

---

## 4. Where everything lives (reference map)

| Thing | Path | Role |
|---|---|---|
| **Behaviour list (input)** | `research/core-behaviour-list.md` | id, name, definition, facets per behaviour |
| **Spec mirrors (ground truth)** | `specs/claude-constitution/20260120-constitution.md`, `specs/openai-model-spec/model_spec.md` | the exact text all quotes resolve against |
| **Citation convention** | `specs/CITATION.md` | locator grammar, block/sentence rules, normalizations |
| **Resolver** | `engine/spec-cite/cite.py` | `outline` / `show` / `resolve` / `find`; every quote is its output |
| **Depth rubric** | `methodology/spec-coverage-depth-rubric.md` | anchors the 0-4 depth score + boundary tests + precedent |
| **Skill 4 (extraction procedure)** | `.claude/skills/4-sweep-spec-coverage/SKILL.md` | how a passage set is built and gated |
| **End-to-end campaign skill** | `.claude/skills/spec-coverage-pass/SKILL.md` | one behaviour, extract → publish → verify → PR |
| **Stage-4 artifact (per behaviour)** | `research/sweeps/NN-<slug>/4-spec-coverage.md` | the passage set + verdict + depth; a parsing contract |
| **Artifact template** | `research/sweeps/02-calibration/4-spec-coverage.md` | copy this shape |
| **Gate log (per behaviour)** | `research/sweeps/NN-<slug>/gates.md` | dated human sign-offs |
| **Publish script** | `engine/publish-coverage.py` | artifact → `data/coverage.json` (re-verifies quotes) |
| **Canonical coverage data** | `data/coverage.json` | single source of truth; site renders this |
| **Reader-payload builder** | `engine/build-spec-reader-data.py` | `coverage.json` + specs → `documents.json` |
| **Reader payload (generated)** | `site/spec-reader/data/documents.json` | minified static blob the reader loads |
| **Spec reader (front-end)** | `site/spec-reader/{index.html,app.js,styles.css}` | the public passage-anchored reader |
| **Reader verifier** | `engine/verify-spec-reader.mjs` | headless render check (needs Chrome) |
| **Mirror refresher** | `engine/spec-watch/pull-latest.sh` | pulls latest published specs into `specs/` |
| **Public methodology copy** | `methodology/site-copy-how-we-assess-coverage.md`, `site/methodology.html` | plain-language description of the method |
| **Fixed IDs / locations** | `.claude/skills/behaviour-sweep/references/locations.md` | canonical table of paths + Notion IDs |

---

## 5. The contracts you must not break

Three data shapes hold this pipeline together. Changing any one means changing
its readers too.

### a) The locator grammar (`specs/CITATION.md`)

```
<spec>@<version> > <section-ref> > ¶<n>[ s<a>[-<b>]]
```

- `spec` is `constitution` or `model-spec`; the version is **mandatory** in
  stored citations (a locator into an unpinned spec is meaningless after the next
  release). Registered versions are the `SPECS` dict in `cite.py`.
- `section-ref` is a `#anchor` for the Model Spec, or a full heading path for the
  constitution (no anchors exist there).
- `¶<n>` is a block within the section's direct span; `s<a>-<b>` an optional
  sentence range. `>` and `›` are interchangeable separators.
- Quotes are **verbatim** except for three mechanical normalizations applied by
  `cite.py` (footnote markers stripped, links reduced to visible text, whitespace
  and list markers collapsed). Nothing is ever elided inside a quote -- a
  discontinuous quotation is two locators.

### b) The Stage-4 artifact as a parsing contract (`4-spec-coverage.md`)

`publish-coverage.py` reads the artifact with strict regexes. Each excerpt is a
fixed four-line block:

```
- **Locator:** `<locator>`
  **Quote:** <one line, exact resolver output>
  **Role:** <one line>
  **Flags:** -- | adjacent ... | example_block ...
```

Per-spec sections are the headings `## Claude constitution ...` and
`## OpenAI Model Spec ...`; the score comes from a `## Verdict and depth` table
with one row per spec. Deviate from this shape and the publish step breaks.
(This tight coupling is one of the seams worth revisiting -- see §7.)

### c) The published record (`data/coverage.json`)

One record per behaviour × lab:

```json
{
  "behaviour_id": 1,
  "behaviour_name": "No sycophancy",
  "lab_id": "anthropic",
  "verdict": "covered",
  "depth_0_4": 3,
  "depth_note": "…one-line rationale…",
  "citations": [
    { "locator": "constitution@2026-01-20 › Being helpful › ¶2 s1-2",
      "quote": "…exact resolver text…",
      "role": "…" }
  ],
  "verified_against_version": "2026-01-20",
  "verified_date": "2026-07-13",
  "citation_format": "specs/CITATION.md; quotes are exact output of …"
}
```

`build-spec-reader-data.py` and the front-end read these field names directly.

---

## 6. Running the tools

Prereqs: Python 3, Node ≥ 22, `pnpm` (JS deps), and Chrome (for the reader
verifier). Deps install with `pnpm install`.

```sh
# Resolve / explore spec text (the resolver is the workhorse)
python3 engine/spec-cite/cite.py outline model-spec                       # section tree + anchors
python3 engine/spec-cite/cite.py show    "constitution > Being honest"     # numbered ¶ / sentences
python3 engine/spec-cite/cite.py resolve "model-spec@2025-12-18 > #avoid_sycophancy > ¶2 s1"
python3 engine/spec-cite/cite.py find    model-spec "some remembered phrase"

# Confirm the spec mirrors are the latest published versions (needs authenticated gh)
bash engine/spec-watch/pull-latest.sh        # then: git status --porcelain specs/  must be empty

# Publish a behaviour's coverage, or just check it against what's published
python3 engine/publish-coverage.py research/sweeps/02-calibration           # writes data/coverage.json
python3 engine/publish-coverage.py research/sweeps/02-calibration --check    # verify only, prints CHECK OK

# Rebuild the reader payload after coverage.json changes
python3 engine/build-spec-reader-data.py     # writes site/spec-reader/data/documents.json

# Verify the reader end to end (every behaviour × spec view)
node engine/verify-spec-reader.mjs           # PASS/FAIL per view; needs Chrome

# Look at the reader locally (never file:// -- module scripts are blocked there)
cd site && python3 -m http.server 8000
# → http://localhost:8000/spec-reader/?behavior=calibration&spec=openai
```

---

## 7. Current state and the seams worth your attention

**What is real today.** Behaviours 1-3 (No sycophancy, Calibration, Honesty
about one's own actions) are published against 2 labs (Anthropic, OpenAI) =
6 coverage records. The two specs are `constitution@2026-01-20` and
`model-spec@2025-12-18`. The extraction procedure, resolver, publish/verify
scripts, and reader all work. Data is hand-maintained via reviewed PRs (Phase 1);
Notion sync is Phase 3 and not built.

**What is described but not yet built** (so it is a natural place for your work).
The first item is the headline objective of this collaboration; the rest are
secondary observations.

- **No validation CI.** `.github/workflows/` holds only `deploy.yml` (deploys
  `site/**` to Cloudflare Pages), and `data/schema/` holds no schemas -- yet
  `PLAN.md` describes CI that validates `data/*.json` against schemas and
  re-resolves every locator in `coverage.json` on each PR. Today that
  re-resolution only happens when someone runs `publish-coverage.py --check`
  by hand. Wiring this up would make the "coverage claims stay true" guarantee
  real rather than aspirational.
- **Behaviour metadata is duplicated in at least five places** that must be kept
  in sync by hand: `research/core-behaviour-list.md` (prose), the `BEHAVIOURS`
  list in `engine/build-spec-reader-data.py`, the `GROUPS` list in
  `site/spec-reader/app.js`, `engine/panel/behaviours.json`, and
  `panel-config.json` `display.behaviours`. Two data files additionally reuse `behaviour_id` across disjoint
  numbering spaces (`coverage.json` vs `reader-test-coverage.json`). A single
  source these derive from is an obvious
  cleanup.
- **The artifact is both prose and a parser input.** `publish-coverage.py` scrapes
  a human-written markdown file with regexes (§5b). It works, but the coupling is
  brittle -- small formatting drift breaks publication. Whether the artifact
  should emit a structured sidecar, or the parser should be more forgiving, is an
  open design question.
- **No unit tests for `cite.py`.** Its correctness is currently proven only
  indirectly, by the re-resolution in `publish-coverage.py` and by
  `verify-spec-reader.mjs`. The sentence splitter, block segmenter, and locator
  parser are the trickiest code in the repo and would benefit from direct tests.

Treat these as observations, not a backlog; confirm the direction with Andrés before large refactors. The whole point is *cleaner, reproducible* structure, so leave each
file at least as legible as you found it.

---

## 8. Conventions that apply to your commits

- **Conventional commits** (`type(scope): subject`): `feat`, `fix`, `docs`,
  `chore`, ... e.g. `feat(data): publish calibration spec coverage (behaviour 2)`.
- **No AI attribution** of any kind in commit messages or PR bodies.
- **Prose uses ` -- `, never em dashes.** The one exception: **verbatim spec
  quotes** keep the resolver's exact bytes, em dashes and all -- never retype a
  quote to "fix" its punctuation.
- **Quotes are never typed by hand.** Resolver output only, verified twice (the
  agent's scripted re-check inside the artifact, then `publish-coverage.py` at
  publish).
- **Work on a branch, merge by PR.** Production deploys happen from `main` only;
  `design/*` and `sweep/*` branches are unmerged explorations.

---

## 9. Suggested reading order (first day)

1. `methodology/site-copy-how-we-assess-coverage.md` -- what coverage *is*, in plain
   language, with a fully worked example (No sycophancy).
2. `specs/CITATION.md` -- the locator grammar. Then play with
   `engine/spec-cite/cite.py` (`outline`, `show`, `resolve`, `find`) against both
   specs until locators feel natural.
3. `.claude/skills/4-sweep-spec-coverage/SKILL.md` -- the extraction procedure
   you own.
4. `methodology/spec-coverage-depth-rubric.md` -- how the 0-4 depth score is decided.
5. `research/sweeps/02-calibration/4-spec-coverage.md` -- a real artifact, the
   template for the format.
6. `engine/publish-coverage.py` then `engine/build-spec-reader-data.py` then
   `engine/verify-spec-reader.mjs` -- read them in that order; it is the order
   they run.
7. `.claude/skills/spec-coverage-pass/SKILL.md` -- the wrapper that sequences it
   all for one behaviour.
8. Skim `PLAN.md` §1-2 only if you want the system-wide context.

Then, to feel the whole loop: check out a clean `main`, run
`python3 engine/publish-coverage.py research/sweeps/02-calibration --check`
(expect `CHECK OK`), `node engine/verify-spec-reader.mjs` (expect all views
verified), and open the reader locally. Once those three pass on your machine,
you understand the pipeline.
