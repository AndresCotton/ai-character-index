# engine/ — the automation layer: citation resolution, LLM panel judging, and site-payload builders

> Current-state doc: describes what exists now, not what should exist. Brought current with the Phase-2 stack (#28–#41).

## Purpose

Everything that keeps the index alive: resolves spec citations, runs LLM panel judging, transforms sweep artifacts and run logs into the JSON payloads the site renders, and verifies the rendered site end-to-end. No component here serves the public directly; outputs land in `data/`, `site/**/data/`, the `specs/` mirrors (spec-watch), and engine-local run artifacts (run logs, metrics, smoke samples, failure dumps).

## Contents

| Path | What it is |
|---|---|
| `spec-cite/cite.py` | Locator resolver/verifier (`outline`/`show`/`resolve`/`find`). Grammar defined by `specs/CITATION.md`; bundled specs (`BUNDLED_SPECS`) plus an optional user-spec manifest (`specs/user/specs.json`, gitignored; `SPEC_CITE_USER_SPECS` overrides) whose entries can carry `title`/`sourceUrl` rendering metadata (`spec_meta()`/`user_specs()`). Stdlib-only; CLI **and** imported library. Tests: `tests/test_cite.py`, `tests/test_cite_user_specs.py`. |
| `spec-watch/pull-latest.sh` | Pulls upstream OpenAI/Anthropic specs into `specs/` via `gh`. Manual today; no version pinning or diff detection. Known issue: the dated upstream HTML release archives exceed the contents API's 1 MB inline limit and are fetched as 0-byte files. |
| `panel/` | LLM panel pipeline: `harness.py` (library: lazy injectable config, frozen rubrics v1/v2/v3, explicit prompt composition, verdict parsing, resume), `whole_doc.py` (one API call per behaviour×spec×model), `run_rollout.py` (grid driver, dry-run default), `build_site_data.py` (runlog → site payload; behaviour metadata registry-driven from `data/behaviours.json`; parameterized via `--runlog=`/`--rubric=`/`--panel=`/`--behaviours=`/`--registry=`/`--run-date=`/`--out=`/`--threshold=`/`--solid-threshold=` for iteration and derived builds; with no `--out=`, a run writes timestamped `behaviours-<ts>.json` + `data/manifest.json`, latest-by-default), `select_strata.py` (validation sampler), `select_run.py` (pin → manifest-latest → shipped-fallback resolution, same order as the page), `verify_panel_provenance.py` (proves the shipped payload rebuilds byte-identically from the committed runlog), `test_panel.py` (92 offline tests), `test_verify_panel_provenance.py`, `panel-config.json`, `behaviours.json`, `runlog-v5.jsonl` (canonical runlog behind the shipped payload, documented in `runlog-v5.md`; the v3-era `runlog-v3.jsonl` stays committed with its record). |
| `generate_behaviour_constants.py` | Regenerates the derived behaviour constants from `data/behaviours.json` (the registry): `BEHAVIOURS` in `build-spec-reader-data.py`, and the `title` fields of `engine/panel/behaviours.json` (keys are registry slugs). `--check` exits 1 with a diff on drift; `tests/test_behaviour_registry.py` is the drift gate. |
| `build-spec-reader-data.py` | `data/coverage.json` + spec markdown → `site/spec-reader/data/documents.json`. Index behaviour list (`BEHAVIOURS`) generated from `data/behaviours.json` by `generate_behaviour_constants.py` (currently ids 1–3, the covered behaviours); `--user-manifest=PATH` folds user-registered specs in as extra documents (byte-identical output with no manifest — pinned by test). |
| `verify-reader-test.mjs` | Playwright E2E check of the reader (needs Chrome): walks its default resolution state (no pin, no manifest) and asserts every view anchors exactly the keep-set's passage counts (the client renders nothing below the related cut, so `behaviours-v5-reader.json` is the oracle), the nav must be present and every link resolve, the shipped fallback must return 200, no unexpected 404s, no console errors. Hardcodes site DOM selectors. |
| `verify-reader-features.mjs`, `stage_user_demo.py` | Site feature harness (needs Chrome): drives the reader against BOTH the bundled payload and a user-extended staging, pinning URL/DOM-state features (payload resolution, tier bands incl. the single-judge floor, N-document compare, export) and interactions (resizers, focus toggle, passage navigation, URL sync). `stage_user_demo.py` stages a clone/fork-style site into scratch (synthetic user spec + a `set:user` behaviour); the repo's own site data is restored exactly after. |
| `notion-sync/` | Empty placeholder (`.gitkeep`) — Phase 3 per PLAN.md; does not exist. |

## Relationships

- `cite.py` is the shared foundation: imported by `panel/harness.py`; `tests/test_coverage_json.py` re-resolves the frozen ledger's quotes against it in-process.
- Behaviour identity is registry-driven: `data/behaviours.json` → `generate_behaviour_constants.py` → the derived constants (reader-builder `BEHAVIOURS`, judge-prompt titles in `engine/panel/behaviours.json`); `tests/test_behaviour_registry.py` fails any drift.
- The panel chain: `run_rollout.py` drives `whole_doc.py` → runlogs (the canonical log behind the shipped payload is committed as `runlog-v5.jsonl`, documented in `runlog-v5.md`; the v3-era `runlog-v3.jsonl` stays committed with its record; other runlogs stay gitignored) → `build_site_data.py` → `site/spec-reader/data/`. The builder reads `data/behaviours.json` for behaviour metadata and `data/panel-cell-curation.json` for the per-lab cell rows (verdict/depth/verifiedDate); with no `--out=` it writes a timestamped payload + `data/manifest.json` (latest-by-default, both gitignored). A second committed payload, `behaviours-v5-reader.json` (built with `--threshold=4 --solid-threshold=6 --run-date=2026-08-17`), is the band keep-set — exactly what the reader can render, since the client shows nothing below the related cut; `verify-reader-test.mjs` holds the two together.
- The frozen chain: `data/coverage.json` (frozen ledger) → `build-spec-reader-data.py` → `site/spec-reader/data/documents.json` (user-registered specs fold in via `--user-manifest=`).
- `spec-watch` overwrites `specs/`, which `cite.py` and `build-spec-reader-data.py` consume.

## Dependency map

```mermaid
graph LR
  watch["spec-watch/pull-latest.sh"] -->|overwrites| specs["specs/ mirrors"]
  specs --> cite["spec-cite/cite.py"]
  specs --> bsr["build-spec-reader-data.py"]
  um["specs/user/specs.json (gitignored)"] -.->|user-manifest| cite
  um -.-> bsr
  cite --> harness["panel/harness.py"]
  rollout["panel/run_rollout.py"] --> wholedoc["panel/whole_doc.py"]
  harness --> wholedoc
  wholedoc --> runlog["runlog-v5.jsonl (committed canonical log; see runlog-v5.md)"]
  runlog --> bsd["panel/build_site_data.py"]
  reg["data/behaviours.json (registry)"] --> gbc["generate_behaviour_constants.py"]
  gbc -->|derived constants| bsr
  reg -->|behaviour metadata| bsd
  bsd --> panelpayload["site/spec-reader/data/ (behaviours payloads, timestamped runs + manifest)"]
  coverage["data/coverage.json (frozen ledger)"] --> bsr
  bsr --> docpayload["site/spec-reader/data/documents.json"]
  cur["data/panel-cell-curation.json"] --> bsd
  bsd -->|"--threshold=4 --solid-threshold=6"| readerpayload["behaviours-v5-reader.json (band keep-set)"]
  docpayload --> verify["verify-*.mjs (Playwright E2E)"]
  readerpayload --> verify
```

## As-is observations

- No Python package structure: no `__init__.py`/`pyproject.toml`; all cross-module wiring is `importlib` file-loading and a `sys.path` hack. Renames/moves break only at runtime.
- `cite.py` is the foundation of every chain — the trickiest code in the repo; its bundled + user-manifest contracts are pinned by `tests/test_cite.py` and `tests/test_cite_user_specs.py` (plus the corpus goldens in `tests/golden/`).
- Behaviour identity is registry-driven (`data/behaviours.json` → `generate_behaviour_constants.py`, drift-gated); spec identity still lives in `cite.py`'s bundled registry + `specs/CITATION.md` examples.
- Config loads lazily at use time and is injectable (`harness.load_config()`); the import-side-effect probe in `test_panel.py` pins that no panel module reads files at import.
- Runlog defaults disagree: `harness.RUNLOG` = `runlog.jsonl`, executors default to `runlog-v3.jsonl`; resume silently reads the wrong file if the override is forgotten.
- Locator separators: the panel chain and the frozen coverage ledger both carry `" > "`; `cite.py` also tolerates the grammar's display separator `" › "`.
- `threshold`/`solid_threshold` are both live: `threshold` sets `keeps_citation`'s score cut, `solid_threshold` bakes into the payload's `adjacent` flag (tier display is client-side), and `--threshold=`/`--solid-threshold=` override both for derived builds without touching the committed config.
- Rubric prompts compose explicitly from named slots (`harness.render_system_v3`), with frozen-prompt tests pinning byte-identity to the pre-refactor strings (replaced the former `str.replace`+`assert` coupling).
- `.github/workflows/ci.yml` runs the offline battery (panel/provenance/registry suites, data gate, byte-identity rebuilds, app.js harnesses) and the two browser walkers on every PR.
- Hygiene: `__pycache__/` + `*.pyc` are now gitignored (the committed `.pyc` was removed); `wholedoc-FAILED-*.txt` outputs are still not gitignored.
