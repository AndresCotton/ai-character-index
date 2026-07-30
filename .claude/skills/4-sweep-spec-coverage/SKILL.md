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
(config: `engine/panel/panel-config.json`, panel `frontier`) on a 3-point scale --
2 core, 1 related, 0 neither. A passage's score is the sum across judges (max 6).
This replaced the manual term sweep: it is reproducible (same prompt, same spec,
same judges rerun to the same verdicts), it has no term-list recall ceiling, and
every kept passage carries each judge's named verdict.

## Mirror freshness (before any judging)

The claim is "scored against the latest published version of each spec as of the
run date". Refresh the mirrors with `engine/spec-watch/pull-latest.sh` (or verify
upstream directly), and record in `4-spec-coverage.md` the mirror versions and the
date confirmed. If a pull changes a mirror, all existing locators must re-resolve
before new work builds on the moved text, and the panel must re-run: verdicts are
pinned to `spec@version`.

## Panel run (per behaviour)

1. Add or check the behaviour's entry in `engine/panel/behaviours.json`: `label`,
   `query` (the definition exactly as supplied), optional `title`, `clarifications`,
   `boundary` (the Scope field). Blank optional fields render as "none provided";
   the rubric tells judges to infer nothing from a blank.
2. Dry-run first -- prints the exact call plan, what resume skips, and the cost
   estimate, and sends nothing:
   `python3 engine/panel/run_rollout.py --behaviours=<key> --runlog=<runlog>`
3. Execute with `--go`. Interrupting is safe: the run log is append-only and rerun
   skips completed cells. Never hold verdicts only in memory.
4. Failures print `PARSE FAILURE` and log nothing (the call stays retryable). Known
   modes and their substitutes:
   - `finish_reason: content_filter` (seen: Fable on harm-dense cells) -- run
     `python3 engine/panel/whole_doc.py <behaviour> <spec> opus`.
   - `finish_reason: length` (seen: K3 spending the whole output budget on
     reasoning) -- run `python3 engine/panel/whole_doc.py <behaviour> <spec> kimi-k2`.
   The builder prefers the primary judge when both exist, so substitutes are safe
   to bank early. Every substitution is named in the passage's rationale and the
   data's provenance block -- never silently.
5. Build: `python3 engine/panel/build_site_data.py --runlog=<runlog> --rubric=v3w
   --panel=frontier`.

## Verdict and depth (per spec)

The panel scores passages; the verdict and depth remain authored judgments made
FROM the panel's citation set. Verdict: covered / partial / not-in-spec. Depth 0-4
against `research/spec-coverage-depth-rubric.md` (0 absent / 1 named / 2 discussed /
3 prescribed / 4 demonstrated), with a one-line rationale naming what is present
and what is missing in the rubric's terms. Use the unanimous-core passages as the
spine of the assessment and the related band for the edges.

## Gate 4 -- verdicts are mechanical, not remembered

Record the run in `4-spec-coverage.md`, then STOP.

- [ ] Mirror freshness confirmed this run; versions and check date recorded.
- [ ] Panel provenance recorded: rubric tag, judges (and any substitutions with
      their cause), run date, spend, and the run-log location.
- [ ] Zero unparsed verdicts in the banked cells, or each exception listed.
- [ ] Every kept citation pins `spec@version`; spot-resolve a sample with
      `cite.py resolve` and diff against the stored quote -- zero mismatches.
- [ ] Score distribution sanity: unanimous-core count per spec stated; if a spec
      shows zero relevant passages, confirm it is a finding (the rubric licenses
      it) and not a failed or filtered call.
- [ ] Verdict + depth rationale present for each spec, grounded in cited passages.
- [ ] Human spot-read: the unanimous-core passages actually bear on the behaviour,
      and no passage the reviewer knows of is missing from the set.

## Pitfalls

- A judge returning an empty response is a provider fault, not a zero-coverage
  finding -- check `finish_reason` before concluding anything.
- Mid-word markup in spec source (one constitution passage bolds `conten**t`)
  breaks naive quote matching; the builder strips bold markers from quotes.
- Locators into an unpinned spec are meaningless after the next release; the
  version is mandatory in every stored citation, and a mirror update invalidates
  the panel verdicts along with the locators.
