# Pre-publication punch list

> Shared pre-publication checklist; lives next to the root README by design. Open items only — current state is documented in `SYSTEM.md` and the per-directory `OVERVIEW.md` files.
>
> **Scope decision (repo owner):** the deliverable is the **model spec reader only** — behaviour × model-spec coverage with cited passages. The eval-discovery/quality workflow is OUT: sweep stages 1–3, `data/evals.json`, `research/sources/`, the evidence-strength lens, eval-submission intake.

## 0. Scope consequences (need Andres ruling)

- [ ] Decide fate of out-of-scope material in the repo: delete, move to an archive area, or leave with a clear "not part of the deliverable" marker. Candidates: `data/evals.json`, `research/sources/`, sweep stages 1–3 artifacts, `site/index.html` evidence lens, `.github/ISSUE_TEMPLATE/submit-eval.yml`.
- [ ] Decide what "model spec reader" means for the site surfaces: keep `spec-reader/` + `llm-panel-review/` (+ test bench?), retire `index.html` prototype and `methodology.html` as-is, or rework them.
- [ ] `behaviours-for-adria/`: in or out? It feeds only the test bench, but it IS spec-coverage work.

## 1. Documentation

As-is documentation set: `SYSTEM.md` + per-directory `OVERVIEW.md` files + `experiments-branches.md` (proposed for main in this PR).

- [ ] Walk the as-is set with Andres; confirm the current-state claims before anything is rewritten.
- [ ] Kimi-K3 adversarial verification of all repo documentation → fixes land here as sub-items.
- [ ] Truthfulness fixes (no decisions needed, just stale prose):
  - [ ] `README.md` repo map: "evals/" label → sweeps; engine row missing `spec-cite/`, `panel/`, `publish-coverage.py`; Notion-sync described as operative (it's a `.gitkeep`).
  - [ ] `engine/README.md`: add `panel/` and `publish-coverage.py`; drop/qualify the "CI re-resolves every locator" claim.
  - [ ] `data/README.md`: "Empty until Phase 1" is false; schema/CI claim is false; `reader-test-coverage.json` also feeds `engine/panel/build_site_data.py`.
  - [ ] `site/README.md`: tab list missing `llm-panel-review/`; describes an Astro stack that does not exist (the site is vanilla HTML/JS, no build step).
  - [ ] `docs/onboarding-spec-coverage.md` §7: "CI is empty / no workflows" stale (deploy.yml exists); behaviour count (13 vs 12) unresolved.
  - [ ] 4 files cite the rubric at dead path `research/spec-coverage-depth-rubric.md` (it lives in `methodology/`).
- [ ] **PLAN.md ruling (Matt + Andres):** rewrite as living architecture doc, mark historical, or surgically update. It is the largest doc/reality gap in the repo.
- [ ] `site/methodology.html` + `methodology/site-copy-how-we-assess-coverage.md`: describe the term-list method while the operative procedure is the LLM panel; the panel method needs writing for the public page.

## 2. Engineering debt (from dual-model review — pending)

Qwen-3.8-Max + Kimi-K3 engineering reviews, cross-checked by each other. Findings land here ranked. Pre-seeded candidates from the as-is review:

- [ ] Behaviour-identity fragmentation: 6+ hand-synced copies AND `behaviour_id` reused across disjoint numbering spaces (`coverage.json` id 1 = No sycophancy vs `reader-test-coverage.json` id 1 = Helpfulness).
- [ ] `cite.py` untested (self-described trickiest code in repo; foundation of every chain).
- [ ] No CI validation of anything; `data/schema/` empty. Draft exists on parked branch `ci/fast-suite` + test suite on `tests/cite-suite` + gate hook on `hooks/fast-gate` — decide whether to land them.
- [ ] No Python packaging (importlib/`sys.path` wiring; config read at import time).
- [ ] Markdown-as-API seam: `publish-coverage.py` regex-scrapes stage-4 artifacts.
- [ ] Hand-maintained surfaces: `index.html` inline data (diverged from prototype source); hand-transcribed `reader-test-coverage.json`.
- [ ] Duplicated code: `coverage_payload()` across two builders; static-server harness across two verifiers; spec/behaviour registries in 4–6 places.

## 3. Deletions & cleanup

- [ ] `labs.json` / `evals.json`: zero code consumers — with the scope ruling, `evals.json` is out; decide `labs.json` (still feeds reader metadata? currently nothing reads it).
- [ ] `openai-model-spec/docs/*.html`: five 0-byte archives + malformed href in index.html — delete or re-pull.
- [ ] Behaviour 1 sweep gap: `research/sweeps/01-no-sycophancy/` lacks `4-spec-coverage.md`, so behaviour 1's published coverage records are currently unregenerable.
- [ ] `llm-panel-review/` orphan: link it from navs or fold it into the reader story.
- [ ] Parked local branches ruling: `backup/pre-final`, `backup/pre-linearize` (keep/delete), `feat/cite-sweep` suite home (land tests in main or abandon).

## 4. Provenance & reproducibility

- [ ] Canonical panel runlog lives only on the unmerged `experiment/panel-judges` branch — either land the runlog (or its hash + pointer) on main, or document the dependency explicitly in `engine/panel/README.md`.
- [ ] `site/index.html` update path ("re-copy the prototype") would regress live §1 data — fix the path or kill the prototype.

## 5. Publishing mechanics

- [ ] Decide public-name/domain (open in PLAN.md §7).
- [ ] Preview deploys for PRs do not exist (PLAN promised them); decide if wanted pre-publication.
- [ ] Turn on GitHub "automatically delete head branches" so merged branches stop accumulating.
