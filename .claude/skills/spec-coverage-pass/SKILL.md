---
name: spec-coverage-pass
description: Run one behaviour's spec-coverage pass -- coverage extraction by a fresh-context agent, coverage-gate sign-off, scoped publish to data/coverage.json and the spec reader, mechanical verification, publish-gate sign-off -- with a commit pushed at every step on a per-behaviour branch whose PR merges only after the fresh-context verify audit signs the verify gate. Use when asked to do the next behaviour's spec coverage.
---

# Spec-coverage pass (one behaviour at a time)

The loop for the spec-coverage campaign: the coverage stage of a behaviour
sweep plus the publish stage (publish the repo coverage data + rebuild the
spec reader). One behaviour per pass; never batch.

The pass signs the publish gate, then opens the PR. The verify audit
(`sweep-verify/SKILL.md`) runs next, in a fresh context, and the branch
merges -- which deploys the site -- only after the verify gate is signed.

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

## Step 1 -- Coverage extraction (fresh-context agent), commit, push, stop

- Spawn ONE fresh-context agent for the behaviour. Its instructions: follow
  `.claude/skills/sweep-coverage/SKILL.md` exactly; behaviour definition
  and facets from `research/core-behaviour-list.md`; artifact format per the
  behaviour-2 template; write `research/sweeps/NN-<slug>/spec-coverage.md`
  and a `gates.md` stub; no publishing, no git. Tell it the mirror-freshness
  result from step 0 so it records rather than re-pulls.
- Orchestrator independently re-resolves a sample of locators with `cite.py`
  and greps the claimed authority levels before accepting the result.
- Commit: `feat(research): add spec coverage for behaviour N (<slug>)`
- Push: `git push -u origin sweep/NN-<slug>`
- Render the per-spec verdicts, passage counts, and every judgment call in
  chat, then STOP for the coverage gate.

## Step 2 -- The coverage gate (human sign-off)

Andrés spot-reads the artifact: the verdict table, the kept excerpts and their
roles, and "Considered and not kept". Corrections are applied and re-verified
before proceeding. On sign-off: tick the human spot-read checkbox, replace the
artifact's pending note with the signed date, and append the coverage-gate
entry to `gates.md` (date, approver, corrections, coverage artifact approved --
proceed to publish).

## Step 3 -- Publish, commit each surface, push

- `python3 engine/publish-coverage.py research/sweeps/NN-<slug>` -- parses the
  artifact, re-verifies every quote byte-for-byte against `cite.py`, rewrites
  `data/coverage.json`.
- The behaviour needs an entry (with its definition) in `data/behaviours.json`
  -- the registry is the single source of behaviour identity, and the builder
  refuses a covered id whose definition is empty. Add the entry if it is
  missing, then run `python3 engine/generate_behaviour_constants.py` to
  regenerate the derived constants (the reader's `GROUPS`, the builder's
  `BEHAVIOURS`), then `python3 engine/build-spec-reader-data.py` to rebuild
  `site/spec-reader/data/documents.json`.
- Commit A: `feat(data): publish <slug> spec coverage (behaviour N)` --
  coverage.json plus the gates.md entry and artifact sign-off tick. Push.
- Commit B: `feat(site): add <slug> to the spec reader` -- the registry entry
  and regenerated constants/documents.json. Push.

## Step 4 -- Verify, then STOP for the publish gate

- `node engine/verify-spec-reader.mjs` -- every behaviour x spec view must
  PASS (this re-checks all previously published behaviours too).
- `python3 engine/publish-coverage.py research/sweeps/NN-<slug> --check` --
  must print CHECK OK.
- Local look for the human: `cd site && python3 -m http.server 8000`, then
  http://localhost:8000/spec-reader/?behavior=<slug>. Never open via file:// --
  module scripts are blocked there and the page renders as a dead shell.
- Render the publish-gate checklist (`sweep-publish/SKILL.md`) with these
  command outputs, then STOP for sign-off; on approval append the publish-gate
  entry to `gates.md` (date, approver, corrections).
- Commit the publish-gate entry: `chore(gates): sign the publish gate for
  behaviour N (<slug>)`, then push -- the gate record must reach the branch
  before the verify audit.

## Step 5 -- PR; merge after the verify gate

- `gh pr create` on the branch: title `Behaviour N (<name>): spec coverage`;
  body lists verdict + depth per spec, citation counts, verification output,
  and links the gate log.
- The verify audit (`sweep-verify/SKILL.md`) runs next, in a fresh context
  that did not execute this pass. Nothing merges before the verify gate is
  signed.
- After the verify gate: Andrés merges -- the merge deploys the site. Then:
  `git checkout main && git pull --ff-only` and
  `git branch -d sweep/NN-<slug>`.

## Rules

- Conventional commits (`type(scope): subject`); no attribution lines of any
  kind in commits or PRs.
- Prose (roles, notes, rationales) uses " -- ", never em dashes; verbatim
  quotes keep the resolver's exact bytes, em dashes included.
- Quotes are never retyped: resolver output only, verified twice (the agent's
  scripted re-check inside the artifact, then publish-coverage.py at publish).
