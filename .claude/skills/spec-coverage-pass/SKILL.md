---
name: spec-coverage-pass
description: Run one behaviour's spec-coverage pass -- stage-4 extraction by a fresh-context agent, Gate 4 sign-off, scoped publish to data/coverage.json and the spec reader, mechanical verification, Gate 5 sign-off -- with a commit pushed at every step on a per-behaviour branch whose PR merges only after the stage-6 audit signs Gate 6. Use when asked to do the next behaviour's spec coverage.
---

# Spec-coverage pass (one behaviour at a time)

The loop for the spec-coverage campaign: stage 4 of the behaviour sweep plus
stage 5 (publish the repo coverage data + rebuild the spec reader). It does NOT
publish to Notion and adds no eval data -- the eval-discovery stages (1-3)
are out of scope and no longer part of this pipeline. One behaviour per
pass; never batch.

The pass signs Gate 5, then opens the PR. The stage-6 audit
(`6-sweep-verify/SKILL.md`) runs next, in a fresh context, and the branch
merges -- which deploys the site -- only after Gate 6 is signed.

Precedent: behaviour 2 (Calibration), `research/sweeps/02-calibration/`. Its
artifact is both the format template and a parsing contract --
`engine/publish-coverage.py` reads the artifact mechanically (see its docstring
for the exact entry format). Deviating from the format breaks step 3.

## Step 0 -- Sync and branch

- `git checkout main && git pull --ff-only`
- `git checkout -b sweep/NN-<slug>`
- Mirror freshness: `bash engine/spec-watch/pull-latest.sh`, then
  `git status --porcelain specs/` must be empty. If a mirror moved: STOP.
  Re-run `engine/publish-coverage.py <dir> --check` for every published
  behaviour to find broken locators, and surface the situation to Andrés
  before any new extraction.

## Step 1 -- Stage 4 (fresh-context agent), commit, push, stop

- Spawn ONE fresh-context agent for the behaviour. Its instructions: follow
  `.claude/skills/4-sweep-spec-coverage/SKILL.md` exactly; behaviour definition
  and facets from `research/core-behaviour-list.md`; artifact format per the
  behaviour-2 template; write `research/sweeps/NN-<slug>/4-spec-coverage.md`
  and a `gates.md` stub; no publishing, no git. Tell it the mirror-freshness
  result from step 0 so it records rather than re-pulls.
- Orchestrator independently re-resolves a sample of locators with `cite.py`
  and greps the claimed authority levels before accepting the result.
- Commit: `feat(research): add stage-4 spec coverage for behaviour N (<slug>)`
- Push: `git push -u origin sweep/NN-<slug>`
- Render the per-spec verdicts, passage counts, and every judgment call in
  chat, then STOP for Gate 4.

## Step 2 -- Gate 4 (human sign-off)

Andrés spot-reads the artifact: the verdict table, the kept excerpts and their
roles, and "Considered and not kept". Corrections are applied and re-verified
before proceeding. On sign-off: tick the human spot-read checkbox, replace the
artifact's pending note with the signed date, and append the Gate 4 entry to
`gates.md` (date, approver, corrections, stage-4 artifact approved -- proceed
to stage 5; stage 5 publishes the coverage data and stops at its own Gate 5).

## Step 3 -- Publish, commit each surface, push

- `python3 engine/publish-coverage.py research/sweeps/NN-<slug>` -- parses the
  artifact, re-verifies every quote byte-for-byte against `cite.py`, rewrites
  `data/coverage.json`.
- Add the behaviour (id, slug, name, definition, category) to `BEHAVIOURS` in
  `engine/build-spec-reader-data.py`, then run it to rebuild
  `site/spec-reader/data/documents.json`.
- Commit A: `feat(data): publish <slug> spec coverage (behaviour N)` --
  coverage.json plus the gates.md entry and artifact sign-off tick. Push.
- Commit B: `feat(site): add <slug> to the spec reader` -- the build script
  entry and regenerated documents.json. Push.

## Step 4 -- Verify, then STOP for Gate 5

- `node engine/verify-spec-reader.mjs` -- every behaviour x spec view must
  PASS (this re-checks all previously published behaviours too).
- `python3 engine/publish-coverage.py research/sweeps/NN-<slug> --check` --
  must print CHECK OK.
- Local look for the human: `cd site && python3 -m http.server 8000`, then
  http://localhost:8000/spec-reader/?behavior=<slug>. Never open via file:// --
  module scripts are blocked there and the page renders as a dead shell.
- Render the Gate 5 checklist (`5-sweep-publish/SKILL.md`) with these command
  outputs, then STOP for sign-off; on approval append the Gate 5 entry to
  `gates.md` (date, approver, corrections).
- Commit the Gate 5 entry: `chore(gates): sign Gate 5 for behaviour N (<slug>)`,
  then push -- the gate record must reach the branch before the stage-6 audit.

## Step 5 -- PR; merge after Gate 6

- `gh pr create` on the branch: title `Behaviour N (<name>): spec coverage`;
  body lists verdict + depth per spec, citation counts, verification output,
  and links the gate log.
- The stage-6 audit (`6-sweep-verify/SKILL.md`) runs next, in a fresh context
  that did not execute this pass. Nothing merges before Gate 6 is signed.
- After Gate 6: Andrés merges -- the merge deploys the site. Then:
  `git checkout main && git pull --ff-only` and
  `git branch -d sweep/NN-<slug>`.

## Rules

- Conventional commits (`type(scope): subject`); no attribution lines of any
  kind in commits or PRs.
- Prose (roles, notes, rationales) uses " -- ", never em dashes; verbatim
  quotes keep the resolver's exact bytes, em dashes included.
- Quotes are never retyped: resolver output only, verified twice (the agent's
  scripted re-check inside the artifact, then publish-coverage.py at publish).
