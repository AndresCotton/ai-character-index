# Scope deletions: remove out-of-scope eval-discovery material

**Ruling (repo owner, Andrés):** the deliverable of this repo is the **model-spec reader only** — behaviour × spec coverage with cited passages. The eval-discovery/quality workflow is outside the deliverable. This PR executes the scope-deletion ruling for the three items that are settled (see CLOSEOUT-LIST.md); it removes the material, unwires the machinery that existed only to serve it, and leaves every in-scope surface exactly as it was.

No new content, no behaviour changes to anything in scope — the sole exception is `PR-BODY.md` itself, process scaffolding for the assembly step (see the Meta note). Pure deletion + mechanical consequences otherwise.

> **Meta:** this file is the draft PR description, committed for the assembly step to consume verbatim. It pins repo state at review time and must not land on `main` — the assembly step is responsible for provably removing it (strip it before the PR opens, or drop it in the merge commit).

---

## What is removed, and why

### 1. `data/evals.json` + `data/schema/evals.schema.json` (13.4 KB + 5.6 KB)

The eval survey — 5 curated + 9 rejected sycophancy evals with rubric quality scores and per-lab adherence bands. It is the stage-5 transcription product of the eval-discovery workflow: **no code reads it (other than the validation-gate entry removed here) and no site surface renders it** (documented as such in `data/OVERVIEW.md` and `SYSTEM.md`). With the eval workflow out of scope, the file has no remaining purpose.

Consequences handled in the same commit:
- `engine/validate_data.py`: the `("evals.json", "evals.schema.json")` entry dropped from `CHECKS`.
- `engine/test_validate_data.py`: `TestEvalsSchema` removed (34 → 28 tests). The data-file ↔ schema bijection test is **kept** and now pins the reduced set — a future data file cannot land without a schema and a check entry. (One direction only, and pre-existing: an orphan schema with no data file would not be caught; unchanged by this PR.)
- `data/README.md`: `evals.json` inventory row removed; the **"no eval without a URL" rule is gone** — it existed only for this file.
- `engine/README.md`: the gate description no longer cites the removed rule or `evals.json`.

### 2. `research/sources/` (two tracked files, 6.8 KB)

Reference material for the eval workflow: the candidate-pool provenance for the behaviour long-list (Forethought *The Importance of AI Character*, Appendix 2 excerpt) and its README. Both tracked files removed; the directory is gone.

Deliberately untouched: the private PDF *Founding an AI Charter organisation.pdf* is **gitignored by design** and is not present on disk; its `.gitignore` entry stays as a privacy guard in case the file ever reappears at that path. Root `README.md` repo map: dead link to `research/sources/` removed.

### 3. Sweep stages 1–3 artifacts (42.4 KB)

The eval-discovery work products inside `research/sweeps/*/`:
- `research/sweeps/01-no-sycophancy/1-dossiers.md` — stage-1 discovery dossiers (36.5 KB)
- `research/sweeps/01-no-sycophancy/register.md` — candidate register, 32 candidates (5.9 KB)

Sweeps 02 and 03 never had stage 1–3 files (their gate logs record that stages 1–3 did not run for them).

## What is deliberately kept, and why

- **Every `gates.md`** (all three sweep dirs): the gate logs — provenance records of human sign-offs, not stage work products. Deleting them would destroy the audit trail the in-scope coverage records depend on. (Sweeps 02 and 03 carry signed Gate 4 entries; sweep 01's log has **no gate signed yet** — it ends at the "Gate 1 pending sign-off" placeholder.) No gate log references the deleted `register.md` or `1-dossiers.md` (grep evidence below), so no signed record is left dangling by these deletions.
- **Every `4-spec-coverage.md`** (sweeps 02, 03): the source artifacts the published coverage is built from. `engine/publish-coverage.py` parses them and re-verifies every quote; `--check` remains green for behaviours 2 (45 locators) and 3 (23 locators).
- **`data/labs.json`**: separately deferred by owner ruling — not part of this PR.
- **`research/sweeps/01-no-sycophancy.md`** (top-level sweep record, kept — see "Uncertain" below).
- The `.gitignore` entry for the private PDF (see above).

Out of this PR's remit entirely: `site/index.html` (site-surfaces ruling deferred), `vision/`, `PLAN.md`, `.claude/skills/` (separate workstream), `behaviours-for-adria/` (kept by ruling).

## Uncertain — kept, flagged for the owner

**`research/sweeps/01-no-sycophancy.md`** (33 KB): the canonical record of the 2026-07-12 full eval sweep (predates the staged layout). It is arguably an eval-discovery work product and therefore out of scope. Kept because: (a) it does not match the stage 1–3 patterns this deletion covers; (b) the `gates.md` we are keeping explicitly references it ("its output is `../01-no-sycophancy.md` and remains the content template"), and deleting it would leave a dangling reference in a provenance record we are not rewriting. If the owner wants it gone, it should go in a follow-up that also annotates the gate log.

Gate-log dangling-reference check: sweep 01's log has no signed gate yet (nothing to dangle), and none of the three gate logs names either deleted file — that sweep-01 header reference to `../01-no-sycophancy.md` is the only file reference in any gate log:

```text
$ grep -rnEi 'register|dossier' research/sweeps/*/gates.md
# → zero hits, exit 1 (case-insensitive)
```

## Known surviving references (in documents this PR does not own)

Repo-wide greps for every deleted path are clean inside the files this PR may touch. Surviving mentions live in documents owned elsewhere and are listed here for follow-up:
- `SYSTEM.md`, `PLAN.md` (owner docs), `CLOSEOUT-LIST.md` (tracks this task itself)
- `data/OVERVIEW.md`, `research/OVERVIEW.md`, `design/OVERVIEW.md`, `design/interaction-model.md` (doc updates needed: inventory rows, diagrams, and the evals.json "data requirements" mention)
- `.claude/skills/*` — separate scope-pass workstream owns these
- `research/core-behaviour-list.md` lines 12/14: provenance links to the deleted `sources/` files — needs an owner-directed wording decision (the external forethought.org URLs survive in git history)
- `ROOT.md` line 16 mentions `research/sources/` only to describe the `.gitignore` entry, which stays — accurate as written.

Three surviving eval-workflow references sit in files this PR edits — **explicitly deferred, not oversights**; none matches the literal grep patterns below, which is why the grep audit does not surface them:
- `engine/README.md` §notion-sync still names the Notion **Evals by Behaviour** database as a future sync source. `engine/notion-sync/` is an unbuilt Phase-3 placeholder, and `PLAN.md` (owner doc, out of this PR's remit) still plans the evals sync for Phase 3 — rewriting those plans belongs to an owner-directed follow-up, not a deletion PR.
- Root `README.md` Contributing still invites "Submit an eval" via the issue form. The form itself (`.github/ISSUE_TEMPLATE/submit-eval.yml`) exists and is not deleted by the ruling — the ruling removes the eval data and machinery, not the contribution channel. Whether to retire the form and this README line is an owner decision and is deferred with the rest of the eval-workflow residue.
- Root `README.md` §"How it works" still says the full six-stage sweep "reserves the later gates for the eval, Notion, and prototype surfaces." Accurate as a description of the staged pipeline as designed, but it names eval surfaces the ruling shrank — same owner-deferred follow-up as the two items above.

## Verification (all on Python 3.10.6; branch `scope-delete` rebased onto `phase-1-cleanup` — the PR-BODY amend carrying this text changes no code or data)

```text
$ python3 engine/validate_data.py
OK: coverage.json, labs.json, reader-test-coverage.json validate against data/schema/ (backend: jsonschema 4.26.0)

$ python3 engine/validate_data.py --stdlib
OK: coverage.json, labs.json, reader-test-coverage.json validate against data/schema/ (backend: built-in stdlib validator)

$ python3 engine/test_validate_data.py
Ran 28 tests ... OK          (was 34; TestEvalsSchema's 6 tests removed with the file)

$ python3 -m unittest discover -s tests
Ran 28 tests ... OK          (same count as the engine suite above by coincidence: test_cite ×25, test_coverage_json ×1, test_publish_check ×2)

$ python3 engine/panel/test_panel.py
Ran 27 tests ... OK

$ python3 engine/test_coverage_payload.py
Ran 7 tests ... OK

$ python3 engine/publish-coverage.py research/sweeps/02-calibration --check
45 locators re-verified against cite.py, 0 mismatches
CHECK OK: behaviour 2 published records match the artifact

$ python3 engine/publish-coverage.py research/sweeps/03-action-honesty --check
23 locators re-verified against cite.py, 0 mismatches
CHECK OK: behaviour 3 published records match the artifact

$ git diff --exit-code -- site/                              # worktree check: exit 0, empty
$ git diff --stat phase-1-cleanup scope-delete -- site/     # branch-vs-base: empty
```

Pre-existing, not caused by this PR (identical failure on the base commit): `publish-coverage.py research/sweeps/01-no-sycophancy --check` exits 1 with `FileNotFoundError: 4-spec-coverage.md`. Sweep 01 has never had a stage-4 artifact on any branch (`git log --all` for that path is empty); `data/OVERVIEW.md` documents that behaviour 1's published records cannot currently be regenerated. The files this PR deletes there (`1-dossiers.md`, `register.md`) are not inputs to `publish-coverage.py`.

Repo-wide greps at branch tip (zero dangling in touchable files; survivors itemized above; "this PR's note" = this file plus the deletion note it writes into `docs/onboarding-spec-coverage.md` §2):

```text
$ grep -rn 'evals\.schema' . --exclude-dir=.git        # → only this PR's own note
$ grep -rn 'evals\.json' . --exclude-dir=.git          # → owner docs (SYSTEM, PLAN, CLOSEOUT-LIST) + OVERVIEW docs + design/interaction-model.md + .claude/skills/* + this PR's note
$ grep -rn 'research/sources' . --exclude-dir=.git     # → CLOSEOUT task text, ROOT.md's .gitignore description, .gitignore itself, this PR's note
$ grep -rnE 'sources/README|sources/forethought' …     # → research/OVERVIEW.md, core-behaviour-list.md provenance lines
$ grep -rn '1-dossiers' . --exclude-dir=.git           # → research/OVERVIEW.md + data/OVERVIEW.md + .claude/skills/* + this PR's note
$ grep -rn 'register\.md' . --exclude-dir=.git         # → research/OVERVIEW.md + data/OVERVIEW.md + .claude/skills/* + this PR's note
```

Stdlib-fallback `$ref` coverage after the deletion: `grep -l '\$ref' data/schema/*.json` → `coverage.schema.json` and `reader-test-coverage.schema.json`. Both surviving `$ref`-bearing schemas resolve every committed record through `$ref` at the record level, and every schema test runs on both backends (`BACKENDS` subtests in `engine/test_validate_data.py`), so the fallback's `$ref` path stays test-covered after `evals.schema.json` goes — the "28 tests OK" above is not hiding a coverage change.
