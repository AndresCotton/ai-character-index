---
name: 4-sweep-spec-coverage
description: Stage 4 of a behaviour sweep (parallel track, independent of stages 1-3) -- score every passage of the local spec copies against one behaviour with the frontier LLM panel, build the citation set from the panel verdicts, assign per-spec verdict and depth, and stop at Gate 4.
---

# Sweep stage 4: spec coverage

Input: the behaviour (number, name, definition, facets). Independent of stages 1-3;
may run in parallel with them.
Output: `research/sweeps/NN-<slug>/4-spec-coverage.md` plus panel verdicts in the
run log consumed by `engine/panel/build_site_data.py`.
Read first: `engine/panel/README.md` (pipeline mechanics) and `specs/CITATION.md`
(locator format). Passages and locators come from `engine/spec-cite/cite.py` via the
panel pipeline; ground truth is the local mirrors under `specs/`.

Method: every passage of both specs is graded by a panel of three frontier models
(config: `engine/panel/panel-config.json`, panel `frontier_primary`; the wider
`frontier` list additionally admits the substitutes) on a 3-point scale --
2 core, 1 related, 0 neither. A passage's score is the sum across judges (max 6).
The run is a single logged command with every verdict banked per judge, so a
re-run against the same spec version is comparable cell by cell. Relevance is
judged against the behaviour's definition alone, and every kept passage carries
each judge's named verdict. Judges are not bit-deterministic;
treat rerun stability as an empirical check, not a guarantee.

## Mirror freshness (before any judging)

The claim is "scored against the latest published version of each spec as of the
run date". Refresh the mirrors with `engine/spec-watch/pull-latest.sh` (or verify
upstream directly), and record in `4-spec-coverage.md` the mirror versions and the
date confirmed. If a pull changes a mirror, all existing locators must re-resolve
before new work builds on the moved text, and the panel must re-run: verdicts are
pinned to `spec@version`.

## Panel run (per behaviour)

0. Keys: the env-var names are in `panel-config.json` under `providers`
   (OPENAI_API_KEY, ANTHROPIC_API_KEY, TOGETHER_API_KEY for the default panel);
   values live in the environment or a gitignored `engine/panel/.env`.
1. Add or check the behaviour's entry in `engine/panel/behaviours.json`: `label`,
   `query` (the definition exactly as supplied; a `query_v2` override exists only
   for definitions with a clause that cannot be judged per passage), optional
   `title`, `clarifications`, `boundary` (the Scope field). Blank optional fields
   render as "none provided"; the rubric tells judges to infer nothing from a
   blank. If the behaviour should appear on the site, also add its slug to
   `SLUGS` in `build_site_data.py` and to `display.behaviours` in
   `panel-config.json` -- without both, the run produces data the site never shows.
2. Dry-run first -- prints the exact call plan, what resume skips, and the cost
   estimate, and sends nothing. The canonical run log is
   `engine/panel/runlog-v3.jsonl` (the driver, `whole_doc.py`, and the builder all
   default to it; the shipped history exists only as an untracked file in a
   local working copy of `experiment/panel-judges`, committed to no branch):
   `python3 engine/panel/run_rollout.py --behaviours=<key>`
3. Execute with `--go`. Interrupting is safe: the run log is append-only and rerun
   skips completed cells. Never hold verdicts only in memory.
4. Failures print `PARSE FAILURE` with the `finish_reason`; the run log gets
   nothing (metrics are still recorded) and the call stays retryable. Known
   modes and their substitutes:
   - `finish_reason: content_filter` (seen: Fable on harm-dense cells) -- run
     `python3 engine/panel/whole_doc.py <behaviour> <spec> opus`.
   - `finish_reason: length` (seen: K3 spending the whole output budget on
     reasoning) -- run `python3 engine/panel/whole_doc.py <behaviour> <spec> kimi-k2`.
   The builder prefers the primary judge when both exist, so substitutes are safe
   to bank early. The substitute's name appears in each passage's rationale
   automatically; the data-level provenance note is NOT automatic -- when you
   substitute, update the `substitution` string in `build_site_data.py` to
   describe what happened and why.
5. Build: `python3 engine/panel/build_site_data.py --runlog=<runlog> --rubric=v3w
   --panel=frontier`.

## The stage-4 artifact (format is a parsing contract)

`4-spec-coverage.md` is read by `engine/publish-coverage.py`; keep the
behaviour-2 template's shape exactly (`research/sweeps/02-calibration/
4-spec-coverage.md`): the `- **Sweep date:**` header bullets, one `##` section
per spec, and one entry per kept excerpt with the four lines
`**Locator:** / **Quote:** / **Role:** / **Flags:**`. Build the entries FROM the
panel results: unanimous-core and majority-core passages are the core entries;
the related band becomes `adjacent` entries. Quotes come from `cite.py resolve`,
never typed. The **role** line is authored (one line on why the passage is in
the set -- the panel's per-judge verdicts inform it but do not replace it), and
Model Spec entries still note the section's authority level. Add a short
"Panel run" section recording provenance (rubric tag, judges, substitutions,
run date, spend, run-log location), and keep "Considered and not kept" for
passages the panel split on that you excluded.

## Verdict and depth (per spec)

The panel grades individual passages only. Each spec's two summary fields are
still written by whoever runs this stage, grounded in the panel's citations:

- **Verdict** -- covered / partial / not-in-spec.
- **Depth** -- 0-4 against `methodology/spec-coverage-depth-rubric.md`
  (0 absent, 1 named, 2 discussed, 3 prescribed, 4 demonstrated), with a
  one-line rationale saying which level the cited passages support and what
  would be needed for the next level.

Base both on the citation set: passages every judge marked core are the
strongest evidence; the related band shows where the behaviour's boundary
sits. Do not grade from memory of the spec.

## Gate 4 -- verdicts are mechanical, not remembered

Record the run in `4-spec-coverage.md`, then STOP.

- [ ] Mirror freshness confirmed this run; versions and check date recorded.
- [ ] Panel provenance recorded: rubric tag, judges (and any substitutions with
      their cause), run date, spend (token counts in `metrics.jsonl` times
      `price_per_mtok` in the config), and the run-log location.
- [ ] Zero unparsed verdicts in the banked cells, or each exception listed.
- [ ] Every kept citation pins `spec@version`; spot-resolve a sample with
      `cite.py resolve` and diff against the stored quote -- zero mismatches
      after allowing for the builder's two normalizations: it strips `**` from
      quotes, and for fenced example passages the stored quote is the caption
      line before the `~~~` fence (with `exampleBlock` extending the highlight);
      the resolver does neither.
- [ ] Score distribution sanity: unanimous-core count per spec stated; if a spec
      shows zero relevant passages, confirm it is a finding (the rubric licenses
      it) and not a failed or filtered call.
- [ ] Verdict + depth rationale present for each spec, grounded in cited passages.
- [ ] Human spot-read: the unanimous-core passages actually bear on the behaviour,
      and no passage the reviewer knows of is missing from the set.
- [ ] Site check: rebuild with `build_site_data.py`, load the page locally, and
      open a few "?" popups on the new behaviour's highlights.

## Pitfalls

- A judge returning an empty response is a provider fault, not a zero-coverage
  finding -- check `finish_reason` before concluding anything.
- Mid-word markup in spec source (one constitution passage bolds `conten**t`)
  breaks naive quote matching; the builder strips bold markers from quotes.
- Fenced example blocks (`~~~xml` dialogues) render as code the page matcher
  cannot see: the builder quotes only the caption line and sets `exampleBlock`
  so the highlight extends over the rendered block. A full-text quote for an
  example passage will never anchor.
- Locators into an unpinned spec are meaningless after the next release; the
  version is mandatory in every stored citation, and a mirror update invalidates
  the panel verdicts along with the locators.
