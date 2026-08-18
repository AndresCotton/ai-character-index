# Closeout list

> **Closeout, not a roadmap.** The project is being paused. Scope (repo-owner decision): the deliverable is the **model spec reader only** — behaviour × model-spec coverage with cited passages; the eval-discovery/quality workflow is out of scope. Current state is documented in `SYSTEM.md` and the per-directory `OVERVIEW.md` files.
>
> Three **cumulative** phases, ordered safest-first. Each phase leaves the repo in a coherent, honest state, so it is fine to stop after any phase. Later phases add to earlier ones; nothing in a later phase is needed for an earlier phase to stand on its own.

## Phase 1 — Tier 3: honest, clean demo (bounded, behavior-preserving changes only)

> **Product if you stop here:** a read-only demo — visitors can read the example coverage (two lab specs × the example behaviours) and see what the project does, but cannot produce their own data without editing code; the only contribution route is the contact channel.
> **Risk: low.** Docs, bounded deletions/hygiene, and behavior-preserving code-quality work (tests, determinism, de-duplication); no interface or behavior changes. The main failure mode is cleanup scope-creep.

- [ ] Merge the prep PRs: **#22** (gitignore + cruft), **#23** (docs + this list + intake forms), **#24** (dead code)
- [ ] **Honest status note** (README or a top-level note): built with ambitions it hasn't reached; being paused; what works today vs. what is aspirational
- [ ] **PLAN.md ruling:** rewrite as a living architecture doc, mark historical, or surgically update — the largest doc/reality gap (§8 lists `outreach/` which is gitignored and never on main; §2/§8 claim schema-enforced CI that doesn't exist; §8's engine row omits `panel/` and the builders; §1.2 promises four workflows where one exists)
- [ ] **`site/methodology.html` + `methodology/site-copy-how-we-assess-coverage.md`:** describe the term-list method while the operative procedure is the LLM panel; the panel method needs writing for the public page
- [ ] **Bounded hygiene:** gitignore the panel runtime artifacts (`engine/panel/runlog*.jsonl`, `metrics.jsonl`, `wholedoc-FAILED-*.txt`). (The committed `.pyc` and the 0-byte archives are already removed by #22; the `runDate` and nav-anchor fixes live in the engineering items below.)
- [ ] **Turn on GitHub "automatically delete head branches"** so merged branches stop accumulating
- [ ] **Parked local branches ruling:** keep/delete `backup/pre-final`, `backup/pre-linearize`; `feat/cite-sweep` suite home (land the tests in main or abandon)
- [ ] **Publishing decisions:** public name/domain; preview deploys for PRs (if wanted)
- [ ] **Phase-1 engineering** — parallel, behavior-preserving, test-driven; each in its own commit with an adversarial review (correctness + test-quality/mutation + Phase-1-goal-consistency):
  - [ ] **W1:** land the parked cite.py test suite (`tests/cite-suite`) on main + wire a runner; verify green against current `cite.py` (the foundation Phase 2 will generalize)
  - [ ] **W2:** `build_site_data.py` determinism — derive `runDate` from the data instead of `date.today()` (non-deterministic output)
  - [ ] **W3:** fix the spec-reader nav anchors (`../#methodology`, `../#about`); make `verify-spec-reader.mjs` fail on unresolved anchors
  - [ ] **W4:** JSON schemas + validation for `data/*.json` *(optional)*
  - [ ] **W5:** de-duplicate `coverage_payload()` across `build-spec-reader-data.py` / `build-reader-test-data.py`
  - [ ] **W6:** `DEFAULT_RUNLOG` consistency — forgetting `--runlog=` currently appends verdicts to the wrong file
  - [ ] **W7:** fix the stale "unused legacy" comment on `display.threshold` in `panel-config.json` (it is read by `build_site_data.py`)
- [ ] **Documentation: don't route demo users into the internal workflow** — ensure nothing tells a demo user to get data changes reviewed/pushed; the contribution route stays contact-only (the fuller "strip vision/review-workflow docs" is Phase 2)
- [ ] **Scope deletions** *(each needs an Andrés ruling)*: fate of out-of-scope material (`data/evals.json`, `research/sources/`, sweep stages 1–3 artifacts, `site/index.html` evidence lens) — delete, archive, or mark; `.claude/skills/` scope pass (delete `1-sweep-discover/`, `2-sweep-curate/`, `3-sweep-score/` + `references/exclusion-criteria.md`; rescope `5-sweep-publish/` and `6-sweep-verify/` to coverage-only — drafts in `docs/proposals/`; retire or rescope the `behaviour-sweep/` orchestrator; strip Notion IDs from `references/locations.md`); site-surfaces ruling (keep `spec-reader/` + `llm-panel-review/` + test bench? retire the `index.html` prototype? fix-or-retire `index.html` and its "re-copy the prototype" update path); `behaviours-for-adria/` in/out; `labs.json` (`evals.json` is already out)

## Phase 2 — Tier 2: decoupled single-user toolkit (adds to Phase 1)

> **Product if you stop here:** a user can supply their own spec + behaviours and run the pipeline to produce and view their own coverage data — no new code, nothing pushed back — but it is not yet a general extension platform.
> **Risk: medium.** The decoupling touches load-bearing, under-tested code (`cite.py` has no tests) and the seams get chosen without real users; real risk of breaking the working demo.

- [ ] **Generalize `cite.py`'s spec input** — accept an arbitrary user spec instead of the two hardcoded registry entries
- [ ] **Behaviour-identity single source:** one slug-keyed registry (ids namespaced per set — `coverage.json` id 1 = No sycophancy vs `reader-test-coverage.json` id 1 = Helpfulness today); generate `GROUPS` in `spec-reader/app.js`, `BEHAVIOURS` in `build-spec-reader-data.py`, and panel `SLUGS` from it; kill the display-time renumbering in `build_site_data.py`
- [ ] **Parameterize the builders** (`build-spec-reader-data.py`, `build-reader-test-data.py`) to drive from user-supplied behaviour + spec lists instead of hardcoded `BEHAVIOURS`/`DOCUMENTS`
- [ ] **Local/gitignored output convention** — user-generated data lands somewhere unpushed
- [ ] **Structured stage-4 sidecar:** emit `4-spec-coverage.json` alongside the markdown and point `publish-coverage.py` at it (the current 4-line regex contract breaks on any prose drift); reconstruct `research/sweeps/01-no-sycophancy/4-spec-coverage.md` from its 20 published citations — behaviour 1's records are currently unregenerable
- [ ] **Land CI verification:** PR-time workflow running `engine/panel/test_panel.py`, the cite.py golden suite, `publish-coverage.py --check` for every published behaviour, and both `verify-*.mjs`; make `spec-watch/pull-latest.sh` abort when upstream version ≠ `cite.py`'s registry (and fix its 0-byte archive fetch — skip them or use the blob API). Most pieces exist on parked branches `ci/fast-suite` / `tests/cite-suite` / `hooks/fast-gate`
- [ ] **Panel provenance on main:** commit the canonical panel runlog (or a hash-pinned manifest); derive the substitution provenance text from the runlog instead of a hand-edited string
- [ ] **Panel packaging + config injection:** lazy config loading (no reads at import time); replace the `str.replace`+`assert` rubric coupling with explicit template composition (the `DEFAULT_RUNLOG` constant lands in Phase 1)
- [ ] **Strip the vision/review-workflow documentation** that implies the internal authoring flow is the user path

## Phase 3 — Tier 1: extensible modular platform (adds to Phase 2)

> **Product if you stop here:** users bring their own specs/behaviours, produce coverage, and add local extensions — all without pushing back; the reader renders arbitrary user data.
> **Risk: high.** A redesign guessed without real users, executed on under-tested load-bearing code with no safety net — the most likely way to pick the wrong seams and break the demo. Strongly defer until there are real users to design the seams around.

- [ ] **Unify reader anchoring + passage counting:** the three reader surfaces fork one code base (the published reader already lacks the forks' `passageFragments` matcher) and the two verifiers count passages differently; extract a shared reader-core module; generate `reader-test-coverage.json` from the sweep artifacts with a `--check` instead of hand transcription
- [ ] **Single source for agent-facing procedures:** the sweep procedures exist only under `.claude/skills/` (a Claude-Code-specific path) and no root agent-context files exist; one canonical copy, everything else a pointer (decide canonical location, pointer mechanism incl. the Windows-symlink caveat, and a CI sync check if copies are ever generated)
- [ ] **Generalize the site/reader to load arbitrary user payloads** — the readers currently read fixed committed payloads
- [ ] **Support local extensions** — the "add your own extensions that don't get pushed" model
