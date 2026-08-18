# Pre-publication punch list

> Shared pre-publication checklist; lives next to the root README by design. Open items only — current state is documented in `SYSTEM.md` and the per-directory `OVERVIEW.md` files.
>
> **Scope decision (repo owner):** the deliverable is the **model spec reader only** — behaviour × model-spec coverage with cited passages. The eval-discovery/quality workflow is OUT: sweep stages 1–3, `data/evals.json`, `research/sources/`, the evidence-strength lens, eval-submission intake.

## 0. Scope consequences (need Andres ruling)

- [ ] Decide fate of out-of-scope material in the repo: delete, move to an archive area, or leave with a clear "not part of the deliverable" marker. Candidates: `data/evals.json`, `research/sources/`, sweep stages 1–3 artifacts, `site/index.html` evidence lens, `.github/ISSUE_TEMPLATE/submit-eval.yml`.
- [ ] Decide what "model spec reader" means for the site surfaces: keep `spec-reader/` + `llm-panel-review/` (+ test bench?), retire `index.html` prototype and `methodology.html` as-is, or rework them.
- [ ] `behaviours-for-adria/`: in or out? It feeds the test bench and — via three transcribed rows — the panel surface, and it IS spec-coverage work.

## 1. Documentation

As-is documentation set: `SYSTEM.md` + per-directory `OVERVIEW.md` files + `experiments-branches.md` (proposed for main in this PR).

- [ ] Walk the as-is set with Andres; confirm the current-state claims before anything is rewritten.
- [x] Kimi-K3 adversarial verification of all repo documentation → findings fixed in this PR; remaining open items below.
- [x] Truthfulness fixes (no decisions needed, just stale prose) — landed in this PR:
  - [x] `README.md` repo map: "evals/" label → sweeps; engine row missing `spec-cite/`, `panel/`, `publish-coverage.py`; Notion-sync described as operative (it's a `.gitkeep`).
  - [x] `engine/README.md`: add `panel/` and `publish-coverage.py`; drop/qualify the "CI re-resolves every locator" claim.
  - [x] `data/README.md`: "Empty until Phase 1" is false; schema/CI claim is false; `reader-test-coverage.json` also feeds `engine/panel/build_site_data.py`.
  - [x] `site/README.md`: tab list missing `llm-panel-review/`; describes an Astro stack that does not exist (the site is vanilla HTML/JS, no build step).
  - [x] `docs/onboarding-spec-coverage.md` §7: "CI is empty / no workflows" stale (deploy.yml exists); behaviour count corrected to the repo list's 12 (the 13-row Notion version is noted as newer in `methodology/mentee-project-archetypes.md`).
  - [x] 3 files cited the rubric at dead path `research/spec-coverage-depth-rubric.md` (it lives in `methodology/`) — fixed/annotated.
- [ ] **PLAN.md ruling (Matt + Andres):** rewrite as living architecture doc, mark historical, or surgically update. It is the largest doc/reality gap in the repo. Confirmed specifics: §8 lists `outreach/` (gitignored, never on main); §2/§8 claim schema-enforced CI (none exists); §8's engine row omits `panel/` and the builders; §1.2 promises four workflows where one exists.
- [ ] `site/methodology.html` + `methodology/site-copy-how-we-assess-coverage.md`: describe the term-list method while the operative procedure is the LLM panel; the panel method needs writing for the public page.

## 2. Engineering debt (dual-model review, cross-checked)

Two independent engineering reviews (Qwen-3.8-Max and Kimi-K3, run as external OpenRouter API calls — not this repo's panel judges; the seated Qwen models are qwen-small in the cheap panel and qwen-big in the itest panel, and the shipped frontier panel is sol/fable/kimi) plus adversarial cross-checks by each model of the other's findings. The list below is the reconciled ranking; agreement on items 1–3 was unanimous, and each model caught real issues the other missed (marked ★). Scope note: the panel surface is judged at Severity 3 while its place in the deliverable is undecided (§0); items rise to 4 if it stays.

**Tier 1 — a single unnoticed change silently falsifies published claims:**

- [ ] **Land CI verification.** PR-time workflow running: `engine/panel/test_panel.py`, the cite.py golden suite, `publish-coverage.py --check` for every published behaviour, and both `verify-*.mjs`. Also make `spec-watch/pull-latest.sh` abort when upstream version ≠ `cite.py`'s registry (today it overwrites `specs/` in place, silently invalidating every locator). Note: `pull-latest.sh` still fetches the dated upstream HTML release archives although they exceed the contents API's 1 MB inline limit and arrive as 0-byte files — fixing that fetch (skip them, or use the blob API) belongs with this hardening; version detection needs its own signal regardless (a `docs/` listing or CHANGELOG diff). Most pieces already exist on parked branches `ci/fast-suite` / `tests/cite-suite` / `hooks/fast-gate`. *Sev 5 · M*
- [ ] **Behaviour-identity single source.** One slug-keyed `data/behaviours.json` registry (ids explicitly namespaced per set — `coverage.json` id 1 = No sycophancy vs `reader-test-coverage.json` id 1 = Helpfulness today); generate `GROUPS` in `spec-reader/app.js`, `BEHAVIOURS` in `build-spec-reader-data.py`, the issue-form dropdown, and panel `SLUGS` from it; kill the display-time renumbering in `build_site_data.py`. Copies to sync today: 12 / 13 / 3 / 11 / 3 / 12 across seven locations. *Sev 5 · M*
- [ ] **Structured stage-4 sidecar + behaviour-1 reconstruction.** Emit `4-spec-coverage.json` alongside the markdown and point `publish-coverage.py` at it (the current 4-line regex contract breaks on any prose drift). ★ Reconstruct `research/sweeps/01-no-sycophancy/4-spec-coverage.md` from its 20 published citations — a third of the deliverable's live coverage data currently has no regeneration or `--check` path. *Sev 4 · M*

**Tier 2 — correctness and provenance traps:**

- [ ] **Fix or retire `site/index.html`.** Verified divergence: behaviour 3 (Honesty about one's own actions) shows Anthropic depth 4 inline vs depth 3 in `data/coverage.json`; the documented "re-copy the prototype" update path would bake the error into production. *Sev 3 · S* (gated on §0)
- [ ] **Panel provenance on main.** Commit the canonical panel runlog (or a hash-pinned manifest) on main — published panel data's reproduction trail lives only on the unmerged `experiment/panel-judges` branch. Derive the substitution provenance text from the runlog instead of a hand-edited string. *Sev 3 · S*
- [ ] **Panel packaging + config injection.** Lazy config loading (no reads at import time), one `DEFAULT_RUNLOG` constant (defaults disagree today: forgetting `--runlog=` silently appends verdicts to the wrong file), delete dead symbols (`BATCH`, `user_msg()`, `VERDICT_WORD`, `batch_size`, `display.threshold`), replace the `str.replace`+`assert` rubric coupling with explicit template composition. *Sev 3 · S–M*
- [ ] **Unify reader anchoring + passage counting.** The three reader surfaces fork one code base (the published reader already lacks the forks' `passageFragments` matcher), and the two verifiers count passages differently (raw citations vs deduped blocks). Extract a shared reader-core module; generate `reader-test-coverage.json` from the sweep artifacts with a `--check` instead of hand transcription. *Sev 3 · M*
- [ ] **Single source for agent-facing procedures.** The sweep procedures exist only under `.claude/skills/` (a Claude-Code-specific path) and no root agent-context files exist (no AGENTS.md/QWEN.md/CLAUDE.md anywhere); making the procedures reachable from other agents must not duplicate the SKILL.md files — one canonical copy, everything else a pointer. Decide: (a) canonical location (stay at `.claude/skills/` vs move to a neutral path), (b) pointer mechanism (symlinks from agent-specific locations — fine on macOS/Linux, needs developer mode on Windows, some tools don't follow links — vs root AGENTS.md/QWEN.md pointer docs referencing the canonical path), (c) a CI sync check if copies are ever generated. *Sev 3 · S–M*
- [ ] **Decide `llm-panel-review/` production status.** ★ It is live on Cloudflare (deploy filters on `site/**`), unlinked from all navs, noindex but publicly reachable, rendering panel data whose provenance lives on an unmerged branch. Link it with a draft banner or exclude it from the deploy. *Sev 3 · S* (gated on §0)
- [ ] **Documentation truthfulness pass** — the items in §1 above. *Sev 3 · S*

**Tier 3 — hygiene:**

- [ ] `.gitignore` the panel runtime artifacts (`engine/panel/runlog*.jsonl`, `metrics.jsonl`, `wholedoc-FAILED-*.txt`); drop the committed `__pycache__/cite.cpython-312.pyc`; delete the five 0-byte `openai-model-spec/docs/*.html` archives (+ malformed href in `docs/index.html`); fix `build_site_data.py` stamping `date.today()` as `runDate`; fix the broken `../#methodology` / `../#about` nav anchors in `spec-reader/index.html`. *Sev 2 · S* (PR #22 carries the ignore rules plus the `.pyc` and archive removals.)

## 3. Deletions & cleanup

- [ ] `labs.json` / `evals.json`: zero code consumers — with the scope ruling, `evals.json` is out; decide `labs.json` (still feeds reader metadata? currently nothing reads it).
- [ ] `openai-model-spec/docs/*.html`: five 0-byte archives + malformed href in index.html — delete or re-pull (removal is in PR #22).
- [ ] Behaviour 1 sweep gap: `research/sweeps/01-no-sycophancy/` lacks `4-spec-coverage.md`, so behaviour 1's published coverage records are currently unregenerable.
- [ ] `llm-panel-review/` orphan: link it from navs or fold it into the reader story.
- [ ] Parked local branches ruling: `backup/pre-final`, `backup/pre-linearize` (keep/delete), `feat/cite-sweep` suite home (land tests in main or abandon).

## 4. Provenance & reproducibility

- [ ] Canonical panel runlog lives only on the unmerged `experiment/panel-judges` branch. `engine/panel/README.md` already documents that pointer; what is missing on main is the runlog itself (or a hash-pinned manifest).
- [ ] `site/index.html` update path ("re-copy the prototype") would regress live §1 data — fix the path or kill the prototype.

## 5. Publishing mechanics

- [ ] Decide public-name/domain (open in PLAN.md §7).
- [ ] Preview deploys for PRs do not exist (PLAN promised them); decide if wanted pre-publication.
- [ ] Turn on GitHub "automatically delete head branches" so merged branches stop accumulating.
