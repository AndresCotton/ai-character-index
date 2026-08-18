# data/

The canonical machine-readable data the site renders from. **The dynamic site surfaces contain no data of their own** — the one exception is `site/index.html`, whose inline prototype data (`const B = {...}`) is hand-maintained and connected to nothing here; Notion is never read directly by the site. Changes arrive here via reviewed pull requests. The `coverage.json` records for behaviours 2–3 are published by `engine/publish-coverage.py` from gate-approved stage-4 sweep artifacts (`research/sweeps/NN-<slug>/4-spec-coverage.md`, or its structured sidecar `4-spec-coverage.json` when present); behaviour 1's records predate that pipeline and were written by hand (not regenerable today — see `data/OVERVIEW.md`). The other files are hand-maintained. `engine/notion-sync/` (the planned Notion → data/ sync) is a placeholder, not built.

Current files:

| File | One row per | Writer |
|---|---|---|
| `coverage.json` | behaviour × lab verdict, with citations | behaviours 2–3: `engine/publish-coverage.py` (re-verifies every quote via `engine/spec-cite/cite.py` before writing); behaviour 1: hand-written, predates the pipeline |
| `labs.json` | lab | hand-maintained (changes rarely); read by `engine/validate_data.py` (cross-file `lab_id` rule); no site code reads it |
| `evals.json` | eval, with rubric quality scores | hand-maintained (written before the staged pipeline existed); read by `engine/validate_data.py` (schema gate); no site code reads it |
| `reader-test-coverage.json` | see below | hand-transcribed from [`behaviours-for-adria/`](../behaviours-for-adria/README.md) |

Planned but absent: `behaviours.json` (the single behaviour registry — see the closeout list) and `meta.json` (site-wide metadata).

One file here is deliberately **not** index data: `reader-test-coverage.json`, the ledger behind the [reader test bench](../site/spec-reader-test/README.md). It holds an external reviewer's behaviour set -- definitions plus one coverage record per behaviour × lab, in the same record shape as `coverage.json` so a record can be lifted from a sweep unchanged. Consumers: `engine/build-reader-test-data.py` (the whole set → `site/spec-reader-test/`) and `engine/panel/build_site_data.py` (three rows — helpfulness, harm-avoidance-to-third-parties, avoiding-over-and-under-caution — carried through untouched into `site/llm-panel-review/`). Nothing in it is an index verdict, and nothing in it reaches `coverage.json` or the published `site/spec-reader/`.

`schema/` holds a JSON Schema per canonical file, plus `spec-coverage-sidecar.schema.json` for the stage-4 sidecar (`research/sweeps/NN-<slug>/4-spec-coverage.json`) — that one is deliberately not in this gate's CHECKS; `engine/publish-coverage.py` enforces it at publish time. `engine/validate_data.py` is the gate (uses the `jsonschema` package when installed, otherwise a built-in stdlib fallback, plus the cross-file rules below). It exits non-zero on any failure, so it can gate CI as-is, though no workflow runs it yet (the only workflow is `.github/workflows/deploy.yml`). Encoded rules: no **published** coverage verdict without at least one citation — the reader test bench deliberately differs, modelling an absence finding as a record whose citations are empty; no eval without a URL; no coverage record pointing at a lab `labs.json` doesn't define; no unknown behaviour IDs in `reader-test-coverage.json` (checked against its own behaviours list).

Derived views (evidence strength per cell, the gap list) are planned but computed nowhere today; the only evidence-strength display is hand-maintained inline data in `site/index.html`. When implemented they should be computed at render time and never stored here, so they can never go stale.
