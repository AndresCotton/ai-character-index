# SYSTEM — global map of the AI Character Index repository

> Current-state doc, plus the branch/local territory documented in `experiments-branches.md`. Describes what exists now, not what should exist. Each directory has its own `OVERVIEW.md`; this file stitches them together. Brought current with the Phase-2 stack (#28–#34).

> **Scope (repo-owner decision):** the deliverable is the **model spec reader only** — behaviour × spec coverage with cited passages. The eval-discovery/quality workflow (sweep stages 1–3, `evals.json`, `sources/`, evidence-strength lens) is outside the deliverable and was deleted by the scope ruling (2026-08-19). This document maps the whole repo as-is; in/out rulings and removal tasks are tracked in [CLOSEOUT-LIST.md](CLOSEOUT-LIST.md).

## What the system is

An evidence-based index of AI character: **behaviours** (a canonical list) × **model-spec coverage** (cited verdicts against lab specs), published as a static site. Editing intent lives in sweep artifacts; git is the canonical gate (a merged PR is the push-to-production act); the site is committed static output deployed to Cloudflare Pages. An LLM-panel pipeline and a coverage-only, human-gated sweep procedure do the actual knowledge production. Behaviour identity is registry-driven (`data/behaviours.json`); users can register their own specs and behaviours locally (the clone/fork pathway — `specs/user/specs.json` + `set:user` registry entries, nothing pushed back).

## Global dependency map

```mermaid
graph TB
  upstream["lab spec repos (OpenAI, Anthropic)"] -->|"manual gh pull"| specs["specs/ mirrors + CITATION.md"]
  specs --> cite["engine/spec-cite/cite.py (bundled + user-spec manifest, test-pinned)"]
  um["specs/user/specs.json (gitignored)"] -.->|user-manifest| cite
  core["research/core-behaviour-list.md (12 behaviours)"] --> skills[".claude/skills/ coverage-only stages 4-6 + human gates"]
  skills --> sweeps["research/sweeps/NN-slug/ artifacts"]
  skills -->|"stage 4 drives"| panel["engine/panel/ (LLM judge APIs)"]
  sweeps -->|"stage-4 sidecar preferred, markdown fallback"| pub["engine/publish-coverage.py"]
  cite -->|"quote re-verification"| pub
  pub --> cov["data/coverage.json"]
  panel -->|"runlog-v3.jsonl (committed canonical log; provenance-verified)"| bsd["engine/panel/build_site_data.py"]
  reg["data/behaviours.json (registry)"] --> gbc["engine/generate_behaviour_constants.py (drift-gated)"]
  reg -->|behaviour metadata| bsd
  gbc -->|derived constants| bsr
  rtc["data/reader-test-coverage.json (hand-transcribed)"] --> bsd
  rtc --> brt["engine/build-reader-test-data.py"]
  cov --> bsr["engine/build-spec-reader-data.py"]
  um -.->|user docs| bsr
  specs -->|"full text inlined"| bsr
  bsr --> reader["site/spec-reader/"]
  brt --> bench["site/spec-reader-test/"]
  bsd --> panelview["site/llm-panel-review/ (unlinked)"]
  adria["behaviours-for-adria/ (reviewer batch)"] -->|"hand transcription"| rtc
  proto["site/index.html (inline hand-maintained data)"]
  meth["site/methodology.html (static page)"]
  reader & bench & panelview & proto & meth ==>|"deploy.yml on site/** changes"| cf["Cloudflare Pages"]
  notion["Notion DBs"] -.->|"planned sync -- engine/notion-sync/ is empty"| cov
```

## Component catalogue

| Directory | One-line role | Detail |
|---|---|---|
| `.claude/skills/` | LLM-facing procedure layer: coverage-only stages 4–6 with human gates (agent-neutral markdown; root `AGENTS.md` points here) | [.claude/skills/OVERVIEW.md](.claude/skills/OVERVIEW.md) |
| `engine/` | Automation: citation resolution, LLM panel judging, payload builders, E2E verifiers | [engine/OVERVIEW.md](engine/OVERVIEW.md) |
| `data/` | Canonical machine-readable data: behaviour registry, coverage ledgers, labs, schema/ | [data/OVERVIEW.md](data/OVERVIEW.md) |
| `specs/` | Version-pinned lab-spec mirrors + locator grammar | [specs/OVERVIEW.md](specs/OVERVIEW.md) |
| `research/` | Canonical behaviour list + per-behaviour sweep records | [research/OVERVIEW.md](research/OVERVIEW.md) |
| `behaviours-for-adria/` | Independent reviewer-batch stage-4 set (test bench, plus 3 rows feeding the panel surface) | [behaviours-for-adria/OVERVIEW.md](behaviours-for-adria/OVERVIEW.md) |
| `methodology/` | Depth rubric, public site copy, method-exploration findings | [methodology/OVERVIEW.md](methodology/OVERVIEW.md) |
| `site/` | Five static surfaces, no build step | [site/OVERVIEW.md](site/OVERVIEW.md) |
| `.github/` | One deploy workflow + two public intake forms | [.github/OVERVIEW.md](.github/OVERVIEW.md) |
| `docs/` | One onboarding document bridging both repo eras | [docs/OVERVIEW.md](docs/OVERVIEW.md) |
| `design/`, `vision/` | Settled-design log (Jul 2026) and the originating brief | [design/OVERVIEW.md](design/OVERVIEW.md), [vision/OVERVIEW.md](vision/OVERVIEW.md) |
| root files | PLAN.md, README.md, pnpm-for-wrangler setup | [ROOT.md](ROOT.md) |
| branch/local territory | Experiment branches, parked CI work, local-only branches | [experiments-branches.md](experiments-branches.md) |

## System-level contracts (the tissue between components)

1. **Locator grammar** — `specs/CITATION.md` defines the format; `cite.py` implements it (bundled specs + optional user manifest); every stored citation in `data/` and site payloads depends on byte-exact resolution. No CI re-resolves; only `publish-coverage.py` runs enforce it.
2. **Stage-4 artifact format** — prescribed by `.claude/skills/4-sweep-spec-coverage`: the structured `4-spec-coverage.json` sidecar (schema-checked) is preferred, with `engine/publish-coverage.py` falling back to regex-scraping the markdown. The artifact is simultaneously prose record, parser input, and gate evidence.
3. **Behaviour identity** — registry-driven since #28: `data/behaviours.json` is the source of truth; `engine/generate_behaviour_constants.py` regenerates the derived constants (`spec-reader/app.js GROUPS`, `build-spec-reader-data.py BEHAVIOURS`, panel slug lists), with `tests/test_behaviour_registry.py` as the drift gate. `behaviour_id` remains **file-local across disjoint numbering spaces** (id 1 = "No sycophancy" in `coverage.json`, "Helpfulness" in `reader-test-coverage.json`); the registry namespaces ids per set and slugs are the global key.
4. **Runlog convention** — JSONL rows keyed by rubric version; defaults still disagree between `harness.RUNLOG` and the executors. The canonical shipped runlog is committed (`engine/panel/runlog-v3.jsonl`, documented in `runlog-v3.md`) and `engine/panel/verify_panel_provenance.py` proves the shipped payload rebuilds from it byte-identically; other runlogs stay gitignored.
5. **Site payloads** — `spec-reader/data/documents.json` is shared by all three reader surfaces; panel citations carry `exampleBlock` flags anchoring example blocks. Panel runs emit timestamped payloads + `manifest.json` (latest-by-default, gitignored); the committed `behaviours.json` is the fresh-clone fallback.
6. **Deploy trigger** — pushes to main filtered to `site/**` and `.github/workflows/deploy.yml` (plus manual dispatch): data/engine changes are invisible to production until baked into committed payloads.

## Cross-cutting as-is risks (synthesized from all overviews)

1. **Nothing is verified automatically in CI.** No workflow runs tests, schema validation, or locator re-resolution — though the pieces now exist on main: schemas for every canonical `data/` file + the `validate_data.py` gate, the panel/provenance/cite/registry suites, and both `verify-*.mjs`. A draft `ci.yml` + pre-commit gate exist only on parked local branches (`ci/fast-suite`, `tests/cite-suite`, `hooks/fast-gate`).
2. **`cite.py` is the foundation** of every chain; docs call it the trickiest code in the repo. Its bundled + user-manifest contracts are now pinned by tests and corpus goldens.
3. **Behaviour metadata is registry-driven** (`data/behaviours.json` → derived constants, drift-gated); residual fragmentation: the reader's `BEHAVIOURS` list (ids 1–3) stays hardcoded in `build-spec-reader-data.py`, and the disjoint per-file id spaces persist (documented in the registry's per-set semantics).
4. **Documentation describes a system that half-exists**: PLAN.md promises Notion sync, four workflows, Astro, schemas; reality has one workflow, vanilla JS, and an empty `notion-sync/` — and this doc set now records the gap file-by-file.
5. **Hand-maintained surfaces**: `index.html` inline data (diverged from its prototype source) and hand-transcribed `reader-test-coverage.json`.
6. **Provenance is now committed and verified**: behaviour 1 publishes from a reconstructed sidecar; the shipped panel runlog is committed and byte-identity-verified. Residual: the substitution note in the payload is still a hand-edited string, and single-judge runs degenerate the tier cutoffs (display model assumes ≥2 judges).
7. **No Python packaging**: importlib/sys.path wiring persists (config is now lazy/injectable; dead code and the stale config comment are removed).
8. **Orphans and residue**: `llm-panel-review/` unlinked from all navs; `spec-watch`'s fetch still produces 0-byte release archives (the committed empty artifacts are gone; the fetch needs fixing); sweep records referencing the rubric at a stale path (annotated with its current `methodology/` location). Root agent-context now exists (`AGENTS.md`, added with the stack-reconciliation docs) pointing at the agent-neutral procedures under `.claude/skills/`.

## Reading order for a cold-start agent

`README.md` → this file → `docs/onboarding-spec-coverage.md` (coverage track) or `engine/panel/README.md` (panel track) → the `OVERVIEW.md` of the directory being touched → `.claude/skills/README.md` before running any sweep.
