# `.claude/skills/` scope pass -- rescope to the coverage-only pipeline

Repo-owner ruling: the deliverable is the **model spec reader only** -- behaviour x
spec coverage with cited passages. The eval-discovery/quality workflow (sweep
stages 1-3) is outside the deliverable. This PR executes the approved scope pass
for `.claude/skills/` (CLOSEOUT-LIST, "Scope deletions" item): the out-of-scope
stage skills are deleted, the surviving stages are rescoped to coverage-only from
the reviewed drafts, the six-stage orchestrator is retired, and the entry-point
docs are aligned with the pipeline as it now is.

Sibling PR #23 carries the drafts this PR consumes (and the docs set); the draft
files under `docs/proposals/` are not modified here.

## Deletions

- **`.claude/skills/1-sweep-discover/`, `2-sweep-curate/`, `3-sweep-score/`** --
  the eval-discovery/quality stages (candidate discovery, curation against
  exclusion codes, rubric scoring). Out of scope under the ruling.
- **`.claude/skills/behaviour-sweep/references/exclusion-criteria.md`** --
  register/disposition conventions for the retired evidence track; its only
  consumers were stages 1-2.
- **`.claude/skills/behaviour-sweep/SKILL.md`** -- the six-stage orchestrator.
  Superseded by the coverage-only pipeline (stages 4-6) plus the
  `spec-coverage-pass/` campaign wrapper, which sequences them. The gate protocol
  and transparency-invariant language that survive the rescope are preserved in
  `.claude/skills/README.md`.

## Rescopes (drafts promoted)

- `.claude/skills/5-sweep-publish/SKILL.md` <- `docs/proposals/5-sweep-publish.coverage-only.draft.md`
- `.claude/skills/6-sweep-verify/SKILL.md` <- `docs/proposals/6-sweep-verify.coverage-only.draft.md`

Both are promoted **verbatim** apart from dropping the "DRAFT PROPOSAL --
awaiting ruling" banners (the ruling has landed) -- verified byte-for-byte with
`diff` against the drafts minus their banners. Stage 5 now publishes the
gate-approved stage-4 coverage to `data/coverage.json` and rebuilds the reader
payload; the Notion, prototype, and evals surfaces are gone. Stage 6 now audits
four coverage-only checks (quotes, payload identity, live render, gate log).

Stage numbering (4/5/6) is kept for continuity with the signed gate records in
`research/sweeps/02-calibration/` and `03-action-honesty/`; the continuity note
moves from the draft banners into `.claude/skills/README.md`.

## locations.md

Relocated `.claude/skills/behaviour-sweep/references/locations.md` ->
`.claude/skills/references/locations.md` (shared by the surviving skills; tracked
with `git mv`). All Notion page/DB IDs stripped (private; out of scope). The
canonical repo paths + spec versions are kept; the back-reference to the retired
orchestrator is dropped. The reference in `docs/onboarding-spec-coverage.md` is
repointed; `.claude/skills/README.md` lists it under References.

## Doc alignment (entailed by the deletions)

- `.claude/skills/README.md` rewritten: stage 4 (spec coverage, LLM panel) +
  rescoped stages 5/6 + the `spec-coverage-pass` wrapper; gate protocol preserved.
- Root `README.md`: how-it-works paragraph and repo-map row aligned (the
  six-stage sweep with eval/Notion/prototype surfaces no longer exists).
  Upstream's round-4 Contributing wording ("live on GitHub") is preserved.
- `docs/onboarding-spec-coverage.md`: deleted skill names removed from the
  out-of-scope description; locations.md row repointed and redescribed.

Note: `phase-1-cleanup` was rebased upstream mid-pass (round-4 review fixes);
this branch was rebased onto the current tip. One conflict (the skills README
"Where everything lands" block) was resolved in favour of the coverage-only map:
the rescoped pipeline does not produce the `research/sweeps/NN-<slug>.md`
canonical write-up (that belonged to the old full stage 5).

## Verification

Repo-wide grep for every deleted path and `exclusion-criteria` -- zero dangling
references in live files. Residual hits are in three intentionally untouched
files: `.claude/skills/OVERVIEW.md` + `ROOT.md` (as-is snapshot docs of
origin/main @ 72e2e6b; updates listed below, not made here) and
`CLOSEOUT-LIST.md:29` (the work order naming these deletions):

```
$ git grep -n -E "1-sweep-discover|2-sweep-curate|3-sweep-score|exclusion-criteria|behaviour-sweep" -- .
.claude/skills/OVERVIEW.md:14:| `behaviour-sweep/SKILL.md` | Orchestrator: ...
.claude/skills/OVERVIEW.md:15:| `1-sweep-discover/SKILL.md` | ...
.claude/skills/OVERVIEW.md:16:| `2-sweep-curate/SKILL.md` | ...
.claude/skills/OVERVIEW.md:17:| `3-sweep-score/SKILL.md` | ...
.claude/skills/OVERVIEW.md:22:| `behaviour-sweep/references/` | ...
CLOSEOUT-LIST.md:29:- [ ] **Scope deletions** ...
ROOT.md:41:- `deploy:site` is referenced in ... three skill files ...
```

All `locations.md` references resolve to the new path:

```
$ git grep -n "locations\.md" -- .
.claude/skills/OVERVIEW.md:19,22      (snapshot doc -- updates listed below)
.claude/skills/README.md:65: ... `references/locations.md`
CLOSEOUT-LIST.md:29:                  (work order)
docs/onboarding-spec-coverage.md:187: ... `.claude/skills/references/locations.md` ...
```

Skills README names no deleted stage; every path it names exists
(`spec-coverage-pass/SKILL.md`, `references/locations.md`, `N-sweep-*/SKILL.md`
= 4/5/6, `site/methodology.html` -- all checked OK).

Rescoped skills contain no draft/ruling wording, and both are byte-identical to
their drafts minus the banners:

```
$ grep -i -E "draft|awaiting|ruling|proposal" .claude/skills/{5-sweep-publish,6-sweep-verify}/SKILL.md
(no matches)
$ diff <(tail -n +5 docs/proposals/5-sweep-publish.coverage-only.draft.md) .claude/skills/5-sweep-publish/SKILL.md  # empty
$ diff <(tail -n +5 docs/proposals/6-sweep-verify.coverage-only.draft.md)  .claude/skills/6-sweep-verify/SKILL.md   # empty
```

Python suites green:

```
$ python3 engine/panel/test_panel.py
Ran 27 tests in 0.004s
OK
$ python3 -m unittest discover -s tests
Ran 28 tests in 31.018s
OK
```

## Known residue (not in this PR)

- As-is snapshot docs still describe the six-stage pipeline; needed updates:
  - `.claude/skills/OVERVIEW.md` -- contents rows for the orchestrator, stages
    1-3, and `behaviour-sweep/references/`; dependency map; observations.
  - `SYSTEM.md` -- conceptual six-stage descriptions (lines 9, 17, 42).
  - `ROOT.md:41` -- "`deploy:site` ... three skill files": after this pass the
    only live skill file still referencing it is `6-sweep-verify/SKILL.md`
    (`.claude/skills/README.md` no longer does; `behaviour-sweep/SKILL.md` is
    deleted).
- Content-level staleness in files this PR may only touch for references:
  `4-sweep-spec-coverage/SKILL.md` frontmatter ("parallel track, independent of
  stages 1-3") and `spec-coverage-pass/SKILL.md` ("the full stage 5 still
  requires Gates 1-3"). Neither references a deleted path.
