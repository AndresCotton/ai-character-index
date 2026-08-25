---
name: sweep-publish
description: The publish stage of a coverage sweep -- publish the gate-approved coverage to the repo data layer and rebuild the reader payload; verify the publication and stop at the publish gate. Nothing is deployed publicly here. Requires the coverage gate signed.
---

# The publish stage of a sweep (coverage only)

Input: the coverage artifact `research/sweeps/NN-<slug>/spec-coverage.md`, the
coverage gate signed in `gates.md`.
Outputs: the behaviour's rows in `data/coverage.json` + a rebuilt reader payload.

**Nothing new is decided here.** Publish transcribes approved content. If
transcription surfaces an error in the coverage artifact, fix the artifact first,
note the fix in `gates.md` under its gate, then re-publish. Divergence between the
published rows and the artifact is always a bug.

**This stage is internal publication.** The public site updates when the payload
commit merges to main -- merges touching `site/**` deploy automatically via
`.github/workflows/deploy.yml` -- and that merge happens only after the verify
stage signs its gate.

## Repo

- **`data/coverage.json`:** the behaviour's rows with `locator` + `quote` citations
  (roles, `adjacent`/`example_block` flags), verdict, depth + note, spec version,
  verified date. Publish through `engine/publish-coverage.py
  research/sweeps/NN-<slug>` -- it re-resolves every quote through
  `engine/spec-cite/cite.py` before writing. Run `--check` first; write only on a
  clean check.
- **`research/core-behaviour-list.md`:** extend the behaviour's spec-coverage
  pointers if the coverage stage found passages the list missed.
- **Reader payload:** `python3 engine/build-spec-reader-data.py` rebuilds
  `site/spec-reader/data/documents.json` from `coverage.json` + the spec mirrors.
  (If the behaviour has rows in the committed panel runlog,
  `engine/panel/build_site_data.py` rebuilds the panel payload from it.)
- Commit only the sweep's files (conventional format, e.g. `feat(coverage):
  behaviour NN <name>`).

The sweep record is `spec-coverage.md` + `gates.md` (precedent: behaviours 2–3).

## The publish gate -- the publication is faithful to the artifact

Render with evidence (command outputs), then STOP.

- [ ] `publish-coverage.py --check` passes with zero mismatches.
- [ ] `jq` validates `coverage.json`; the new rows' locators + quotes byte-match
      `spec-coverage.md`.
- [ ] `build-spec-reader-data.py` succeeds and `node engine/verify-spec-reader.mjs`
      passes (every passage anchors, no console errors).
- [ ] Human: open the behaviour in a local reader and confirm the passages anchor
      and read correctly.
