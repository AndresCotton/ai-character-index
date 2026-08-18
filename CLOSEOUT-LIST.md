# Closeout list

> **Aim (repo-owner decision):** ship the **model spec reader** — behaviour × model-spec coverage with cited passages — as a small, honest, **fixed demo**, plus a **clear pathway for people to clone/fork the repo and run it on their own behaviours**. The eval-discovery/quality workflow is out of scope and gets stripped. The target is the reader + pathway (Phase 2 below), **timeboxed to this week and likely to land as an incompletely-tested end state**; on top of it, be **explicit about the limitations** so people can judge whether and how to build on it. The full modular platform (Phase 3) stays deferred. Current state is documented in `SYSTEM.md` and the per-directory `OVERVIEW.md` files.
>
> Three **cumulative** phases, ordered safest-first; each leaves the repo coherent and honest, and later phases build on earlier ones. **Phase 2 is the current target.**

## Phase 1 — Tier 3: honest, clean demo (bounded, behavior-preserving changes only)

> **Product if you stop here:** a read-only demo — visitors can read the example coverage (two lab specs × the example behaviours) and see what the project does, but cannot produce their own data without editing code; the only contribution route is the contact channel.
> **Risk: low.** Docs, bounded deletions/hygiene, and behavior-preserving code-quality work (tests, determinism, de-duplication); no interface or behavior changes. The main failure mode is cleanup scope-creep.

- [ ] Merge the prep PRs: **#22** and **#24** merged; **#23** (docs + this list) open; **#25** (intake forms, split out of #23) open
- [ ] **Honest status note** (README or a top-level note): what this is (a spec reader + a toolkit to clone/fork), what works today vs. what is aspirational/unproven
- [ ] **PLAN.md ruling:** rewrite as a living architecture doc, mark historical, or surgically update — the largest doc/reality gap (§8 lists `outreach/` which is gitignored and never on main; §2/§8 claim schema-enforced CI that doesn't exist; §8's engine row omits `panel/` and the builders; §1.2 promises four workflows where one exists)
- [ ] **`site/methodology.html` + `methodology/site-copy-how-we-assess-coverage.md`:** describe the term-list method while the operative procedure is the LLM panel; the panel method needs writing for the public page
- [ ] **Bounded hygiene:** gitignore the panel runtime artifacts (`engine/panel/runlog*.jsonl`, `metrics.jsonl`, `wholedoc-FAILED-*.txt`). (The committed `.pyc` and the 0-byte archives are already removed by #22; the `runDate` and nav-anchor fixes live in the engineering items below.)
- [ ] **Turn on GitHub "automatically delete head branches"** so merged branches stop accumulating
- [ ] **Parked local branches ruling:** keep/delete `backup/pre-final`, `backup/pre-linearize`; `feat/cite-sweep` suite home (its tests land via W1 in **#26**)
- [ ] **Publishing decisions:** public name/domain; preview deploys for PRs (if wanted)
- [ ] **Phase-1 engineering** — parallel, behavior-preserving, test-driven; each in its own commit with an adversarial review (correctness + test-quality/mutation + Phase-1-goal-consistency):
  - [ ] **W1:** land the parked cite.py test suite (`tests/cite-suite`) on main + wire a runner; verify green against current `cite.py` (the foundation Phase 2 will generalize) — in **#26** (open)
  - [ ] **W2:** rescoped into the Phase-2 **timestamped run outputs** item: per-run timestamped files replace the fixed output destination; the `runDate` determinism piece survives there as content metadata
  - [ ] **W3:** fix the spec-reader nav anchors (`../#methodology`, `../#about`); make `verify-spec-reader.mjs` fail on unresolved anchors — in **#26** (open)
  - [ ] **W4:** JSON schemas + validation for `data/*.json` *(optional)* — in **#26** (open)
  - [ ] **W5:** de-duplicate `coverage_payload()` across `build-spec-reader-data.py` / `build-reader-test-data.py` — in **#26** (open)
  - [ ] **W6:** rescoped into the Phase-2 **timestamped run outputs** item: with one file per run, forgetting `--runlog=` can no longer append verdicts to the wrong run's file
  - [ ] **W7:** fix the stale "unused legacy" comment on `display.threshold` in `panel-config.json` (it is read by `build_site_data.py`) — **#27** merged 2026-08-18; the comment is still stale, so this is actionable again
- [ ] **Documentation: don't route demo users into the internal workflow** — ensure nothing tells a demo user to get data changes reviewed/pushed; the contribution route stays contact-only (the fuller "strip vision/review-workflow docs" is Phase 2)
- [ ] **Scope deletions** *(each needs an Andrés ruling)*: fate of out-of-scope material (`data/evals.json`, `research/sources/`, sweep stages 1–3 artifacts, `site/index.html` evidence lens) — delete, archive, or mark; `.claude/skills/` scope pass (delete `1-sweep-discover/`, `2-sweep-curate/`, `3-sweep-score/` + `references/exclusion-criteria.md`; rescope `5-sweep-publish/` and `6-sweep-verify/` to coverage-only — drafts in `docs/proposals/`; retire or rescope the `behaviour-sweep/` orchestrator; strip Notion IDs from `references/locations.md`); site-surfaces ruling (keep `spec-reader/` + `llm-panel-review/` + test bench? retire the `index.html` prototype? fix-or-retire `index.html` and its "re-copy the prototype" update path); `behaviours-for-adria/` in/out; `labs.json` (`evals.json` is already out)

## Phase 2 — Tier 2: decoupled single-user toolkit (adds to Phase 1)

> **Product if you stop here:** a user can supply their own spec + behaviours and run the pipeline to produce and view their own coverage data — no new code, nothing pushed back — but it is not yet a general extension platform.
> **Risk: medium.** The decoupling touches load-bearing code whose contract is pinned only for the two bundled specs (the cite.py golden suite lands in **#26**), and the seams get chosen without real users; real risk of breaking the working demo.

- [ ] **Generalize `cite.py`'s spec input** — accept an arbitrary user spec instead of the two hardcoded registry entries
- [ ] **Behaviour-identity single source:** one slug-keyed registry (ids namespaced per set — `coverage.json` id 1 = No sycophancy vs `reader-test-coverage.json` id 1 = Helpfulness today); generate `GROUPS` in `spec-reader/app.js`, `BEHAVIOURS` in `build-spec-reader-data.py`, and panel `SLUGS` from it; kill the display-time renumbering in `build_site_data.py`
- [ ] **Parameterize the builders** (`build-spec-reader-data.py`, `build-reader-test-data.py`) to drive from user-supplied behaviour + spec lists instead of hardcoded `BEHAVIOURS`/`DOCUMENTS`
- [ ] **Timestamped run outputs, latest-by-default** — each panel run emits its own timestamped data file (e.g. `behaviours-<timestamp>.json`); the UI shows the latest by default and can be pinned to a specific file (CLI argument now; UI picker deferred until its home is decided); with no timestamped files the UI falls back to the default data shipped with the repo. User-generated files stay local/gitignored (unpushed)
- [ ] **How-to: "run it on your own behaviours"** — the clone/fork pathway doc: define your behaviour, point it at your spec, run the pipeline, view the result locally (nothing pushed back)
- [ ] **Public page = small fixed demo + invitation** — the sample coverage stays a fixed demo that explicitly invites cloning/forking for one's own behaviours
- [ ] **Explicit limitations** — state what works vs. aspirational vs. unproven so people can judge whether/how to build on it (the endorsed part of option C)
- [ ] **Structured stage-4 sidecar:** emit `4-spec-coverage.json` alongside the markdown and point `publish-coverage.py` at it (the current 4-line regex contract breaks on any prose drift); reconstruct `research/sweeps/01-no-sycophancy/4-spec-coverage.md` from its 20 published citations — behaviour 1's records are currently unregenerable
- [ ] **Land CI verification:** PR-time workflow running `engine/panel/test_panel.py`, the cite.py golden suite, `publish-coverage.py --check` for every published behaviour, and both `verify-*.mjs`; make `spec-watch/pull-latest.sh` abort when upstream version ≠ `cite.py`'s registry (and fix its 0-byte archive fetch — skip them or use the blob API). Most pieces exist on parked branches `ci/fast-suite` / `tests/cite-suite` / `hooks/fast-gate`
- [ ] **Panel provenance on main:** commit the canonical panel runlog (or a hash-pinned manifest); derive the substitution provenance text from the runlog instead of a hand-edited string
- [ ] **Panel packaging + config injection:** lazy config loading (no reads at import time); replace the `str.replace`+`assert` rubric coupling with explicit template composition
- [ ] **Strip the vision/review-workflow documentation** that implies the internal authoring flow is the user path
- [ ] **Last decoupling item — convert the cite.py corpus goldens to hashes:** the full-corpus golden snapshots earn their repo weight while the contract is being refactored, because a failing golden is a reviewable byte-diff that shows exactly which locators a behavior change moves. Once the decoupling settles and the repo shifts from refactoring to maintenance, replace them with output hashes (a determinism/change-detection gate) and keep the locator re-resolution and corrupted-quote tests, which carry the published-citation contract independent of the goldens

## Phase 3 — Tier 1: extensible modular platform (adds to Phase 2)

> **Product if you stop here:** users bring their own specs/behaviours, produce coverage, and add local extensions — all without pushing back; the reader renders arbitrary user data.
> **Risk: high.** A redesign guessed without real users, executed on under-tested load-bearing code with no safety net — the most likely way to pick the wrong seams and break the demo. Strongly defer until there are real users to design the seams around.

- [ ] **Unify reader anchoring + passage counting:** the three reader surfaces fork one code base (the published reader already lacks the forks' `passageFragments` matcher) and the two verifiers count passages differently; extract a shared reader-core module; generate `reader-test-coverage.json` from the sweep artifacts with a `--check` instead of hand transcription
- [ ] **Single source for agent-facing procedures:** the sweep procedures exist only under `.claude/skills/` (a Claude-Code-specific path) and no root agent-context files exist; one canonical copy, everything else a pointer (decide canonical location, pointer mechanism incl. the Windows-symlink caveat, and a CI sync check if copies are ever generated)
- [ ] **Generalize the site/reader to load arbitrary user payloads** — the readers currently read fixed committed payloads
- [ ] **Support local extensions** — the "add your own extensions that don't get pushed" model
