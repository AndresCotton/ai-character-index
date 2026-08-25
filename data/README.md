# data/

The canonical machine-readable data the site renders from. **The dynamic site surfaces contain no data of their own** — the one exception is `site/index.html`, whose inline prototype data (`const B = {...}`) is hand-maintained and connected to nothing here; Notion is never read directly by the site. Changes arrive here via reviewed pull requests. `coverage.json` is a frozen ledger: the publish pipeline that wrote it is retired, nothing writes it any more, and CI keeps its citations machine-verified (every quote re-resolves through `engine/spec-cite/cite.py` in `tests/test_coverage_json.py`). The other files are hand-maintained. `engine/notion-sync/` (the planned Notion → data/ sync) is a placeholder, not built.

Current files:

| File | One row per | Writer |
|---|---|---|
| `behaviours.json` | behaviour, across every set (see below) | hand-maintained (the source of truth for behaviour identity; derived constants regenerate from it) |
| `coverage.json` | behaviour × lab verdict, with citations | frozen — nothing writes it; every quote is re-resolved through `engine/spec-cite/cite.py` in CI (`tests/test_coverage_json.py`) |
| `labs.json` | lab | hand-maintained (changes rarely); read by `engine/validate_data.py` (cross-file `lab_id` rule); no site code reads it |
| `panel-cell-curation.json` | see below | per-lab cell summaries (verdict/depth/verifiedDate) the panel builder ships beside its passages; read by `engine/panel/build_site_data.py` |

Planned but absent: `meta.json` (site-wide metadata).

`behaviours.json` is the single behaviour registry: one entry per behaviour in every set, keyed by slug — the global join key. Each entry carries `name`, `set` (`index` = the project's own list, `reader-test` = the panel-run set the reader renders, `user` = the clone/fork seam, empty for now), a per-set `numeric_id`, `group`, `definition`, and `facets`. Numeric ids are file-local and never renumbered: id 1 is "No sycophancy" in the index set (matching `coverage.json`); the reader-test set has its own numeric space starting at "Helpfulness". The derived constants — `BEHAVIOURS` in `engine/build-spec-reader-data.py`, and the `title` fields of `engine/panel/behaviours.json` (its keys are registry slugs — the panel runlogs are keyed by the same slugs) — regenerate from it via `engine/generate_behaviour_constants.py`, and `tests/test_behaviour_registry.py` fails any drift between the copies. `display.behaviours` in `engine/panel/panel-config.json` is curated configuration, validated against this registry by the panel payload builder at build time. Facets are empty until editorially synced from `research/core-behaviour-list.md` (prose, not machine-parsed), and the ten unpublished index rows carry empty definitions.

One file here is **not** index data: `panel-cell-curation.json` — the per-lab cell summaries (verdict/depth/verifiedDate) `engine/panel/build_site_data.py` ships beside the panel payload's passages. The same builder also cuts the band keep-set (`--threshold=4 --solid-threshold=6` against the committed v5 run), committed at `site/spec-reader/data/behaviours-v5-reader.json` — exactly what the reader can render, since the client shows nothing below the related cut. Nothing here is an index verdict, and nothing reaches `coverage.json`.

`schema/` holds a JSON Schema per canonical file. `engine/validate_data.py` is the gate (uses the `jsonschema` package when installed, otherwise a built-in stdlib fallback, plus the cross-file rules below). It exits non-zero on any failure and runs on every PR via `.github/workflows/ci.yml`. Encoded rules: no **published** coverage verdict without at least one citation; no coverage record pointing at a lab `labs.json` doesn't define; no coverage record reference to a behaviour id the registry's index set doesn't define.

Derived views (evidence strength per cell, the gap list) are planned but computed nowhere today; the only evidence-strength display is hand-maintained inline data in `site/index.html`. When implemented they should be computed at render time and never stored here, so they can never go stale.
